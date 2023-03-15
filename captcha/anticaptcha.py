import asyncio
import time

import aiohttp

from builder import get_variable
from builder import set_variable

__all__ = [
    'solve_anticaptcha',
]

from exceptions import StopWorkerException

STOP_ERRORS = [
    'ERROR_WRONG_USER_KEY',
    'ERROR_ZERO_BALANCE',
    'ERROR_KEY_DOES_NOT_EXIST',
]


async def solve_anticaptcha(session, api_key, site_key, url, user_agent, rqdata):
    '''Solve 2 captcha'''
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
        async with session.post(request_url, json=data) as res:
            if not res.ok:
                return None
            data = await res.json()
            if data['errorId'] > 0 and data['errorCode'] in STOP_ERRORS:
                raise StopWorkerException(reason=data['errorCode'])
            count = get_variable('captcha_usage_count') + 1
            set_variable('captcha_usage_count', count)
            task_id = data['taskId']
    except (aiohttp.ClientError, asyncio.TimeoutError):
        return None

    while True:
        data = {
            'clientKey': api_key,
            'taskId': task_id,
        }
        request_url = f'https://api.anti-captcha.com/getTaskResult'
        try:
            async with session.post(request_url, json=data) as res:
                if not res.ok:
                    return None
                data = await res.json()
                status = data['status']
                if status == 'processing':
                    time.sleep(10)
                    continue
                if status == 'ready':
                    return data['solution']
        except (aiohttp.ClientError, asyncio.TimeoutError):
            time.sleep(10)
            continue
