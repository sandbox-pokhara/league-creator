import asyncio

import aiohttp


def get_proxies(file_path):
    with open(file_path) as fp:
        return fp.read().splitlines()


async def get_proxy_counry(session, proxy):
    try:
        async with session.get('http://www.geoplugin.net/json.gp', proxy=proxy) as res:
            if not res.ok:
                return False, res.status
            res = await res.json()
            return True, res['geoplugin_countryCode']
    except (aiohttp.ClientError, asyncio.TimeoutError):
        return False, -1
