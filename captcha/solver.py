from .anticaptcha import solve_anticaptcha
from .twocaptcha import solve_2captcha


def solve(service, client, api_key, site_key, url, user_agent, rqdata, worker_name, proxy=None, proxy_ip=None):
    if service == '2captcha':
        return solve_2captcha(client, api_key, site_key, url, user_agent, rqdata, worker_name)
    if service == 'anti-captcha':
        return solve_anticaptcha(client, api_key, site_key, url, user_agent, rqdata, proxy, proxy_ip, worker_name)
    raise NotImplementedError(f'{service} captcha service is not implemented.')
