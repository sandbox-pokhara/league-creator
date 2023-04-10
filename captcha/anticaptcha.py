import asyncio
import re
import traceback

import httpx

from builder import get_variable
from builder import set_variable
from exceptions import StopWorkerException
from logger import logger
from proxies import get_proxy_parts

__all__ = [
    'solve_anticaptcha',
]


STOP_ERRORS = [
    'ERROR_WRONG_USER_KEY',
    'ERROR_ZERO_BALANCE',
    'ERROR_KEY_DOES_NOT_EXIST',
]


async def solve_anticaptcha(client, api_key, site_key, url, user_agent, rqdata, proxy=None, proxy_ip=None, worker_name='worker'):
    logger.info(f'{worker_name}: Initiating captcha task..')
    parts = get_proxy_parts(proxy)
    data = {
        'clientKey': api_key,
        'task': {
            'type': 'HCaptchaTaskProxyless',
            'websiteURL': url,
            'websiteKey': site_key,
            'isInvisible': True,
            'userAgent': user_agent,
            'enterprisePayload': {
                'rqdata': rqdata,
            }
        }
    }
    if proxy is not None and proxy_ip is not None and parts is not None:
        data['task']['type'] = 'HCaptchaTask'
        data['task']['proxyType'] = parts['type']
        data['task']['proxyAddress'] = proxy_ip
        data['task']['proxyPort'] = parts['port']
        if 'username' in parts:
            data['task']['proxyLogin'] = parts['username']
        if 'password' in parts:
            data['task']['proxyPassword'] = parts['password']

    request_url = 'https://api.anti-captcha.com/createTask'
    try:
        res = await client.post(request_url, json=data, timeout=300)
        if res.status_code != 200:
            return None
        data = res.json()
        if data['errorId'] > 0 and data['errorCode'] in STOP_ERRORS:
            raise StopWorkerException(reason=data['errorCode'])
        if 'taskId' not in data:
            logger.debug(data)
            return None
        count = int(get_variable('captcha_usage_count')) + 1
        set_variable('captcha_usage_count', count)
        task_id = data['taskId']
    except httpx.HTTPError:
        return None

    while True:
        data = {
            'clientKey': api_key,
            'taskId': task_id,
        }
        request_url = f'https://api.anti-captcha.com/getTaskResult'
        try:
            res = await client.post(request_url, json=data, timeout=300)
            if res.status_code != 200:
                return None
            data = res.json()
            if data['errorId'] > 0:
                if data['errorCode'] in STOP_ERRORS:
                    raise StopWorkerException(reason=data['errorCode'])
                logger.info(f'{worker_name}: Unhandled Error: {data["errorCode"]}')
                return None

            status = data['status']
            if status == 'processing':
                logger.info(f'{worker_name}: Captcha not ready...')
                await asyncio.sleep(10)
                continue
            if status == 'ready':
                logger.info(f'{worker_name}: Captcha ready.')
                return data['solution']['gRecaptchaResponse']
        except httpx.HTTPError:
            logger.debug(f'Exception when solving captcha.')
            logger.debug(traceback.format_exc())
            await asyncio.sleep(10)
            continue
