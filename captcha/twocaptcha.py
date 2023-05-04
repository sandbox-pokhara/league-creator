import asyncio
import traceback

import httpx

from builder import get_variable
from builder import set_variable

__all__ = [
    'solve_2captcha',
    'get_2captcha_id_future',
    'get_2captcha_token_future',
]

STOP_ERRORS = [
    'ERROR_WRONG_USER_KEY',
    'ERROR_ZERO_BALANCE',
    'ERROR_KEY_DOES_NOT_EXIST',
]


async def solve_2captcha(client, api_key, site_key, url, user_agent, rqdata, logger, worker_name='worker'):
    # Request to solve captcha
    try:
        url = f'http://2captcha.com/in.php?key={api_key}&method=hcaptcha&sitekey={site_key}&pageurl={url}&invisible=1&data={rqdata}&userAgent={user_agent}'
        res = await client.post(url, timeout=300)
        if res.status_code != 200:
            return None
        if 'ERROR' in res.text:
            return None
        count = int(get_variable('captcha_usage_count')) + 1
        set_variable('captcha_usage_count', count)
        captcha_data = res.text.split('|')
        captcha_id = captcha_data[1]
    except httpx.HTTPError:
        return None

    # Get solved captcha token using captcha id
    url = f'http://2captcha.com/res.php?key={api_key}&action=get&id={captcha_id}'
    while True:
        try:
            res = await client.get(url)
            if res.text == 'CAPCHA_NOT_READY':
                logger.info(f'{worker_name}: Captcha not ready. Retrying after 5 secs...')
                await asyncio.sleep(5)
                continue
            if 'ERROR' in res.text:
                return None
            logger.info(f'{worker_name}: Captcha ready.')
            if '|' in res.text:
                return res.text.split('|')[1]
            return res.text
        except httpx.HTTPError:
            logger.debug(f'{worker_name}: Exception when solving captcha.')
            logger.debug(traceback.format_exc())
            await asyncio.sleep(10)
            continue
