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
from proxies import get_proxy_details


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


async def get_valid_proxy(name, proxies, proxies_len, proxy_rate_limits, assigned_proxies):
    if proxies is None:
        return None
    i = 0
    while True:
        proxy = next(proxies)
        i += 1
        if i % proxies_len == 0:
            logger.info(f'{name}: No proxy available. Sleeping for 5 minutes...')
            await asyncio.sleep(300)
            continue
        proxy_rate_limit_until = proxy_rate_limits.get(proxy)
        if proxy_rate_limit_until is not None and time.time() <= proxy_rate_limit_until:
            continue
        for assigned in assigned_proxies.values():
            if proxy == assigned:
                continue
        return proxy


async def check_proxy(client):
    try:
        params = {
            'client_id': 'play-valorant-web-prod',
            'nonce': '1',
            'redirect_uri': 'https://playvalorant.com/opt_in',
            'response_type': 'token id_token',
            'scope': 'account openid',
        }
        res = await client.get('https://auth.riotgames.com/authorize', params=params)
        return res.status_code == 303
    except (httpx.ConnectError, httpx.ConnectTimeout, httpx.RemoteProtocolError):
        return False


async def run_worker(name,
                     output_file,
                     to_create,
                     region,
                     email_host,
                     creating,
                     completed,
                     errors,
                     proxy_rate_limits,
                     assigned_proixes,
                     captcha_type,
                     captcha_key,
                     proxies,
                     proxies_len,
                     user_agents,
                     min_delay=0,
                     max_delay=0,
                     ):
    def _get_log_message(message):
        return f'{name} | {proxy_country}: {message}'

    try:
        while len(creating) + len(completed) < to_create:
            account = generate_accounts(region=region, email_host=email_host)[0]
            creating.append(account['username'])

            proxy = await get_valid_proxy(name, proxies, proxies_len, proxy_rate_limits, assigned_proixes)

            proxy_country = None
            logger.info(f'{name}: Using proxy: {proxy}')
            assigned_proixes[name] = proxy
            user_agent = choice(user_agents)
            headers = {'user-agent': user_agent}

            async with httpx.AsyncClient(headers=headers, timeout=120, proxies=proxy) as client:

                if proxy is not None:
                    logger.info(f'{name}: Checking if proxy is not banned...')
                    if not await check_proxy(client):
                        logger.info(f'{name}: Proxy is probably banned.')
                        proxy_rate_limits[proxy] = time.time() + 900
                        creating.remove(account['username'])
                        continue
                    logger.info(f'{name}: Checking proxy country...')
                    success, output = await get_proxy_details(client)
                    logger.info(f'{name}: Proxy country: {output["geoplugin_countryCode"]}')
                    if not success and output == 407:
                        logger.error(f'{name}: Proxy authentication error.')
                    if not success and output == -1:
                        logger.error(f'{name}: Invalid proxy.')
                        creating.remove(account['username'])
                        continue
                    if output['geoplugin_countryCode'] in BANNED_COUNTRIES:
                        logger.error(f'{name}: Bad region found in proxy.')
                        creating.remove(account['username'])
                        continue
                    proxy_country = output['geoplugin_countryCode']

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
                            count = get_variable('ratelimited_count') + 1
                            set_variable('ratelimited_count', count)
                            proxy_rate_limits[proxy] = time.time() + 900
                            creating.remove(account['username'])
                            continue
                        if 'InvalidToken' in text:
                            count = get_variable('invalid_token_count') + 1
                            set_variable('invalid_token_count', count)
                            proxy_rate_limits[proxy] = time.time() + 900
                            creating.remove(account['username'])
                            errors.append('InvalidToken')
                            continue
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
