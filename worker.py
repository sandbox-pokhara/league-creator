import asyncio
from random import choice

import aiohttp

from builder import get_variable
from builder import set_variable
from captcha.anticaptcha import solve_anticaptcha
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


async def run_worker(name, output_file, to_create, region, email_host, creating, completed, captcha_key, proxies, user_agents):
    try:
        while len(creating) + len(completed) < to_create:
            account = generate_accounts(region=region, email_host=email_host)[0]
            creating.append(account['username'])
            proxy = next(proxies) if proxies is not None else None
            logger.info(f'{name}: Using proxy: {proxy}')
            timeout = aiohttp.ClientTimeout(total=30)
            user_agent = choice(user_agents)
            print(user_agent)
            headers = {'user-agent': user_agent}
            async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
                if proxy is not None:
                    logger.info(f'{name}: Checking proxy country...')
                    success, output = await get_proxy_counry(session, proxy)
                    if not success and output == 407:
                        logger.error(f'{name}: Proxy authentication error.')
                    logger.info(f'{name}: Proxy country: {output}')
                    if output in BANNED_COUNTRIES:
                        logger.error(f'{name}: Bad region found in proxy.')
                        creating.remove(account['username'])
                        continue

                # Extract rq data and cookies
                logger.info(f'{name}: Extracting rq data and cookies...')
                try:
                    async with session.get(CONFIG_URL) as res:
                        if not res.ok:
                            logger.error('Error parsing rqdata.')
                            creating.remove(account['username'])
                            continue
                        res = await res.json()
                        rqdata = res['captcha']['hcaptcha']['rqdata']
                except (aiohttp.ClientError, asyncio.TimeoutError):
                    logger.error('Error parsing rqdata.')
                    creating.remove(account['username'])
                    continue

                website_url = URLS[account['region']]
                logger.info(f'{name}: Solving catpcha...')
                captcha_result = await solve_anticaptcha(session, captcha_key, SITE_KEY, website_url, user_agent, rqdata)
                if captcha_result is None:
                    creating.remove(account['username'])
                    logger.error('can not solve captcha: anticaptcha')
                    continue

                body = get_sign_up_body(account, captcha_result['gRecaptchaResponse'])
                logger.info(f'{name}: Signing up...')

                try:
                    async with session.post(SIGNUP_URL, json=body) as res:
                        text = await res.text()
                        if not res.ok:
                            if res.status == 429:
                                # TODO rate limit proxy
                                pass
                            if 'InvalidToken' in text:
                                count = get_variable('invalid_token_count') + 1
                                set_variable('invalid_token_count', count)
                            if 'ValueNotUnique' in text:
                                count = get_variable('value_not_unique_count') + 1
                                set_variable('value_not_unique_count', count)
                            if 'UnsupportedCountry' in text:
                                count = get_variable('unsupported_country_count') + 1
                                set_variable('unsupported_country_count', count)
                            logger.error(f'Error signing up: {text}, Status: {res.status}')
                            creating.remove(account['username'])
                            continue
                        logger.info('Success.')
                        export_account(account, output_file)
                        completed.append(account['username'])
                        creating.remove(account['username'])
                        set_variable('remaining_count', to_create - len(completed))
                        set_variable('signed_up_count', len(completed))
                except (aiohttp.ClientError, asyncio.TimeoutError):
                    logger.error('Error signing up.')
                    creating.remove(account['username'])
                    continue
    except StopWorkerException as e:
        logger.info(f'{name}: Stopping worker. Reason: {e.reason}...')
        return
