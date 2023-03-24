import asyncio
import time
import traceback
from random import choice
from random import randint

import httpx

from builder import get_variable
from builder import set_variable
from captcha.solver import solve
from constants import BANNED_COUNTRIES
from constants import CONFIG_URL
from constants import LOCALES
from constants import REGIONS
from constants import SIGNUP_URL
from constants import SITE_KEY
from constants import URLS
from exceptions import StopWorkerException
from export import export_account
from generator import generate_accounts
from logger import logger
from proxies import get_proxy_counry


def get_sign_up_body(account, token):
    return {
        'username': account['username'],
        'password': account['password'],
        'confirm_password': account['password'],
        'date_of_birth': account['dob'],
        'email': account['email'],
        'tou_agree': True,
        'newsletter': False,
        'region': REGIONS[account['region']],
        'campaign': 'league_of_legends',
        'locale': LOCALES[account['region']],
        'token': f'hcaptcha {token}'
    }


async def run_worker(name,
                     output_file,
                     to_create,
                     region,
                     email_host,
                     creating,
                     completed,
                     errors,
                     proxy_rate_limits,
                     captcha_type,
                     captcha_key,
                     proxies,
                     user_agents,
                     min_delay=0,
                     max_delay=0,
                     ):
    def _get_log_message(message):
        return f'{name} | {proxy_country}: {message}'

    try:
        while len(creating) + len(completed) < to_create:
            logger.debug(errors)
            if len(errors) >= 10 and all(e == 'InvalidToken' for e in errors):
                logger.info(
                    f'Found InvalidToken in last 10 requests. Pausing {name} for 15 mins...')
                await asyncio.sleep(15 * 60)
                errors.clear()

            account = generate_accounts(region=region, email_host=email_host)[0]
            creating.append(account['username'])
            proxy = next(proxies) if proxies is not None else None

            proxy_rate_limit_until = proxy_rate_limits.get('proxy')
            if proxy_rate_limit_until is not None and time.now() <= proxy_rate_limit_until:
                logger.info(f'{name}: Proxy {proxy} is rate limited.')
                continue

            proxy_country = None
            logger.info(f'{name}: Using proxy: {proxy}')
            user_agent = choice(user_agents)
            headers = {'user-agent': user_agent}

            async with httpx.AsyncClient(headers=headers, timeout=120, proxies=proxy) as client:

                if proxy is not None:
                    logger.info(f'{name}: Checking proxy country...')
                    success, output = await get_proxy_counry(client)
                    logger.info(f'{name}: Proxy country: {output}')
                    if not success and output == 407:
                        logger.error(f'{name}: Proxy authentication error.')
                    if not success and output == -1:
                        logger.error(f'{name}: Invalid proxy.')
                        creating.remove(account['username'])
                        continue
                    if output in BANNED_COUNTRIES:
                        logger.error(f'{name}: Bad region found in proxy.')
                        creating.remove(account['username'])
                        continue
                    proxy_country = output

                # Extract rq data and cookies
                logger.info(_get_log_message(f'Extracting rq data and cookies...'))
                try:
                    res = await client.get(CONFIG_URL)
                    if res.status_code != 200:
                        logger.error(_get_log_message('Error parsing rqdata.'))
                        creating.remove(account['username'])
                        continue
                    res = res.json()
                    rqdata = res['captcha']['hcaptcha']['rqdata']
                except (httpx.ConnectError, httpx.ConnectTimeout, httpx.RemoteProtocolError):
                    logger.error(_get_log_message(f'Error parsing rqdata.'))
                    logger.debug(_get_log_message(traceback.format_exc()))
                    creating.remove(account['username'])
                    continue

                website_url = URLS[account['region']]
                logger.info(_get_log_message(f'Solving catpcha...'))
                captcha_result = await solve(captcha_type, client, captcha_key, SITE_KEY, website_url, user_agent, rqdata, name)
                if captcha_result is None:
                    creating.remove(account['username'])
                    logger.error(_get_log_message('Can not solve captcha.'))
                    continue

                body = get_sign_up_body(account, captcha_result)
                logger.info(_get_log_message(f'Signing up...'))

                try:
                    res = await client.post(SIGNUP_URL, json=body)
                    text = res.text
                    if res.status_code != 200:
                        logger.error(_get_log_message(
                            f'Error signing up: {text}, Status: {res.status_code}'))
                        if res.status_code == 429:
                            # Disable proxy for 15 mins
                            proxy_rate_limits[proxy] = time.now() + 900
                            continue
                        if 'InvalidToken' in text:
                            count = get_variable('invalid_token_count') + 1
                            set_variable('invalid_token_count', count)
                            errors.append('InvalidToken')
                            duration = randint(min_delay, max_delay)
                            if duration > 0:
                                logger.info(f'Sleeping for {duration} seconds...')
                                await asyncio.sleep(duration)
                        if 'ValueNotUnique' in text:
                            count = get_variable('value_not_unique_count') + 1
                            set_variable('value_not_unique_count', count)
                            errors.append('ValueNotUnique')
                        if 'UnsupportedCountry' in text:
                            count = get_variable('unsupported_country_count') + 1
                            set_variable('unsupported_country_count', count)
                            errors.append('UnsupportedCountry')
                        creating.remove(account['username'])
                        continue
                    errors.append(None)
                    logger.info(_get_log_message(f'Success.'))
                    export_account(account, output_file)
                    completed.append(account['username'])
                    creating.remove(account['username'])
                    set_variable('remaining_count', to_create - len(completed))
                    set_variable('signed_up_count', len(completed))
                    set_variable('progress', int(len(completed) * 100 / to_create))
                    duration = randint(min_delay, max_delay)
                    if duration > 0:
                        logger.info(f'Sleeping for {duration} seconds...')
                        await asyncio.sleep(duration)
                except (httpx.ConnectError, httpx.ConnectTimeout, httpx.RemoteProtocolError):
                    logger.error(_get_log_message('Error signing up.'))
                    creating.remove(account['username'])
                    continue
    except StopWorkerException as e:
        logger.info(f'{name}: Stopping worker. Reason: {e.reason}...')
        return
    except Exception:
        logger.info(f'{name}: Unexpected excpetion occured. Check logs.')
        logger.debug(traceback.format_exc())
        return
