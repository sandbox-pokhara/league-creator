import asyncio
import time
import traceback
from contextlib import contextmanager
from datetime import datetime
from random import choice
from random import randint

import httpx
from cachetools import TTLCache

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
from ips import add_ip
from proxies import get_proxy_details

proxy_details = TTLCache(maxsize=100_000, ttl=5 * 60)  # 5 minutes
proxy_ratelimits = TTLCache(maxsize=100_000, ttl=15 * 60)  # 15 minutes
proxy_soft_ratelimits = TTLCache(maxsize=100_000, ttl=2 * 60)  # 2 minutes
# soft_ratelimit rate limits proxies that
# sucessfully created accounts to avoid rate limit from riot

disabled_proxies = {}


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
        'token': f'hcaptcha {token}',
    }


@contextmanager
def account_manager(accounts, region, email_host):
    try:
        account = generate_accounts(region=region, email_host=email_host)[0]
        accounts.append(account['username'])
        yield account
    finally:
        accounts.remove(account['username'])


async def get_valid_proxy(
    name, proxies, proxies_len, logger, assigned_proxies=None, bad_ips=None
):
    if assigned_proxies is None:
        assigned_proxies = {}
    if bad_ips is None:
        bad_ips = set()
    if proxies is None:
        return None
    i = 0
    while True:
        proxy = next(proxies)
        i += 1
        if i % proxies_len == 0:
            logger.info(
                f'{name}: No proxy available. Sleeping for 1 minutes...')
            await asyncio.sleep(randint(50, 70))
            continue

        # Check if proxy is disabled
        is_disabled = disabled_proxies.get(proxy, -1) > time.time()
        if is_disabled:
            continue

        # check if proxy is already assigned
        is_assigned = False
        for worker in assigned_proxies:
            if worker != name and proxy == assigned_proxies[worker]:
                is_assigned = True
                break
        if is_assigned:
            continue

        if proxy in proxy_details:
            proxy_ip = proxy_details[proxy]['geoplugin_request']
            # check if proxy is banned
            if proxy_ip in bad_ips:
                continue
            # check if proxy is rate limited
            if proxy_ip in proxy_ratelimits:
                continue
            if proxy_ip in proxy_soft_ratelimits:
                continue
        return proxy


def disable_proxy(proxy, min_delay, max_delay, logger):
    proxy_disabled_duration = randint(min_delay, max_delay)
    logger.info(f'Disabling {proxy} for {proxy_disabled_duration} secs.')
    disabled_proxies[proxy] = time.time() + proxy_disabled_duration


async def run_worker(
    name,
    output_file,
    to_create,
    region,
    email_host,
    creating,
    completed,
    errors,
    assigned_proixes,
    captcha_type,
    captcha_key,
    proxies,
    proxies_len,
    bad_ips,
    user_agents,
    logger,
    min_delay=0,
    max_delay=0,
    use_bad_ips=True,  # wheather to use ips that are in bad_ips.txt
):
    def _get_log_message(message):
        return f'{name} | {proxy_country}: {message}'

    try:
        while len(creating) + len(completed) < to_create:
            with account_manager(creating, region, email_host) as account:
                proxy = await get_valid_proxy(
                    name,
                    proxies,
                    proxies_len,
                    logger=logger,
                    assigned_proxies=assigned_proixes,
                    bad_ips=bad_ips,
                )
                proxy_country = None
                logger.info(f'{name}: Using proxy: {proxy}')
                assigned_proixes[name] = proxy
                user_agent = choice(user_agents)
                headers = {'user-agent': user_agent}

                async with httpx.AsyncClient(
                    headers=headers, timeout=120, proxies=proxy
                ) as client:
                    logger.info(f'{name}: Checking proxy country...')
                    if proxy not in proxy_details:  # if not found in cache
                        success, output = await get_proxy_details(client)
                        if success:
                            proxy_details[proxy] = output
                        else:
                            if output == 407:
                                logger.error(
                                    f'{name}: Proxy authentication error.')
                                disable_proxy(proxy, min_delay,
                                              max_delay, logger)
                                continue
                            if output == -1:
                                logger.error(f'{name}: Invalid proxy.')
                                disable_proxy(proxy, min_delay,
                                              max_delay, logger)
                                continue
                            continue

                    details = proxy_details[proxy]
                    logger.info(
                        f'{name}: Proxy country: {details["geoplugin_countryCode"]}'
                    )
                    if details['geoplugin_countryCode'] in BANNED_COUNTRIES:
                        logger.error(f'{name}: Bad region found in proxy.')
                        continue
                    proxy_country = details['geoplugin_countryCode']
                    proxy_ip = details['geoplugin_request']
                    if not use_bad_ips and proxy_ip in bad_ips:
                        logger.info(
                            'Proxy ip found in bad ips list. Skipping...')
                        continue

                    # Extract rq data and cookies
                    logger.info(_get_log_message(
                        f'Extracting rq data and cookies...'))
                    try:
                        res = await client.get(CONFIG_URL)
                        if res.status_code != 200:
                            logger.error(_get_log_message(
                                'Error parsing rqdata.'))
                            continue
                        res = res.json()
                        rqdata = res['captcha']['hcaptcha']['rqdata']
                    except httpx.HTTPError:
                        logger.error(_get_log_message(
                            f'Error parsing rqdata.'))
                        logger.debug(_get_log_message(traceback.format_exc()))
                        continue

                    website_url = URLS[account['region']]
                    logger.info(_get_log_message(f'Solving catpcha...'))
                    captcha_result = await solve(
                        captcha_type,
                        client,
                        captcha_key,
                        SITE_KEY,
                        website_url,
                        user_agent=user_agent,
                        logger=logger,
                        rqdata=rqdata,
                        worker_name=name,
                    )
                    if captcha_result is None:
                        logger.error(_get_log_message(
                            'Can not solve captcha.'))
                        continue

                    body = get_sign_up_body(account, captcha_result)
                    logger.info(_get_log_message(f'Signing up...'))

                    try:
                        res = await client.post(SIGNUP_URL, json=body)
                        text = res.text
                        if res.status_code != 200:
                            logger.error(
                                _get_log_message(
                                    f'Error signing up: {text}, Status: {res.status_code}'
                                )
                            )
                            if res.status_code == 429:
                                count = get_variable('ratelimited_count') + 1
                                set_variable('ratelimited_count', count)
                                proxy_ratelimits[proxy_ip] = True
                                disable_proxy(proxy, min_delay,
                                              max_delay, logger)
                                continue
                            if 'InvalidToken' in text:
                                count = get_variable('invalid_token_count') + 1
                                set_variable('invalid_token_count', count)
                                errors.append('InvalidToken')
                                bad_ips.add(proxy_ip)
                                add_ip('bad_ips.txt', proxy_ip)
                                proxy_soft_ratelimits[proxy_ip] = True
                                disable_proxy(proxy, min_delay,
                                              max_delay, logger)
                                continue
                            if 'ValueNotUnique' in text:
                                count = get_variable(
                                    'value_not_unique_count') + 1
                                set_variable('value_not_unique_count', count)
                                errors.append('ValueNotUnique')
                            if 'UnsupportedCountry' in text:
                                count = get_variable(
                                    'unsupported_country_count') + 1
                                set_variable(
                                    'unsupported_country_count', count)
                                errors.append('UnsupportedCountry')
                            continue
                        errors.append(None)
                        logger.info(_get_log_message(f'Success.'))
                        proxy_soft_ratelimits[proxy_ip] = True
                        account['creation_date'] = str(datetime.utcnow())
                        account['ip_address'] = proxy_ip
                        account['country'] = details['geoplugin_countryName']
                        account['city'] = details['geoplugin_city']
                        export_account(account, output_file)
                        add_ip('good_ips.txt', proxy_ip)
                        completed.append(account['username'])
                        set_variable('remaining_count',
                                     to_create - len(completed))
                        set_variable('signed_up_count', len(completed))
                        set_variable('progress', int(
                            len(completed) * 100 / to_create))
                        disable_proxy(proxy, min_delay, max_delay, logger)
                    except httpx.HTTPError:
                        logger.error(_get_log_message('Error signing up.'))
                        continue
    except StopWorkerException as e:
        logger.info(f'{name}: Stopping worker. Reason: {e.reason}...')
        return
    except Exception as e:
        logger.info(f'{name}: Unexpected excpetion occured. {e} Check logs.')
        logger.debug(traceback.format_exc())
        return
