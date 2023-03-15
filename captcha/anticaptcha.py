import asyncio
import traceback

import httpx

from builder import get_variable
from builder import set_variable
from exceptions import StopWorkerException
from logger import logger

__all__ = [
    'solve_anticaptcha',
]


STOP_ERRORS = [
    'ERROR_WRONG_USER_KEY',
    'ERROR_ZERO_BALANCE',
    'ERROR_KEY_DOES_NOT_EXIST',
]


async def solve_anticaptcha(client, api_key, site_key, url, user_agent, rqdata, worker_name='worker'):
    '''Solve 2 captcha'''
    logger.info(f'{worker_name}: Initiating captcha task..')
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
    request_url = 'https://api.anti-captcha.com/createTask'
    try:
        res = await client.post(request_url, json=data, timeout=300)
        if res.status_code != 200:
            return None
        data = res.json()
        if data['errorId'] > 0 and data['errorCode'] in STOP_ERRORS:
            raise StopWorkerException(reason=data['errorCode'])
        count = int(get_variable('captcha_usage_count')) + 1
        set_variable('captcha_usage_count', count)
        task_id = data['taskId']
    except (httpx.ConnectError, httpx.ConnectTimeout, httpx.RemoteProtocolError):
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
                return data['solution']
        except (httpx.ConnectError, httpx.Connectasyncioout, httpx.RemoteProtocolError):
            logger.debug(f'Exception when solving captcha.')
            logger.debug(traceback.format_exc())
            await asyncio.sleep(10)
            continue
