
import random
import re

import httpx


def get_proxies(file_path, shuffle=True):
    with open(file_path) as fp:
        proxies = fp.read().splitlines()
        if shuffle:
            random.shuffle(proxies)
        return proxies


def get_proxy_parts(proxy):
    if proxy is None:
        return None
    proxy = re.search('(http)://(.+):(.+)@(.+):([0-9]+)', proxy)
    return {
        'type': proxy.group(1),
        'username': proxy.group(2),
        'password': proxy.group(3),
        'address': proxy.group(4),
        'port': int(proxy.group(5)),
    }


async def get_proxy_details(client):
    try:
        res = await client.get('http://www.geoplugin.net/json.gp')
        if res.status_code != 200:
            return False, res.status_code
        res = res.json()
        return True, res
    except (httpx.ConnectError, httpx.ConnectTimeout, httpx.RemoteProtocolError):
        return False, -1
