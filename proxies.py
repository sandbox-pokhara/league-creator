
import httpx


def get_proxies(file_path):
    with open(file_path) as fp:
        return fp.read().splitlines()


async def get_proxy_counry(client):
    try:
        res = await client.get('http://www.geoplugin.net/json.gp')
        if res.status_code != 200:
            return False, res.status_code
        res = res.json()
        return True, res['geoplugin_countryCode']
    except (httpx.ConnectError, httpx.ConnectTimeout, httpx.RemoteProtocolError):
        return False, -1
