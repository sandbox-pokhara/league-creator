from .anticaptcha import solve_anticaptcha
from .twocaptcha import solve_2captcha


def solve(service, client, api_key, site_key, url, user_agent, rqdata, worker_name, logger, proxy=None, proxy_ip=None):
    if service == '2captcha':
        return solve_2captcha(client, api_key, site_key, url, user_agent, rqdata, logger, worker_name)
    if service == 'anti-captcha':
        return solve_anticaptcha(client, api_key, site_key, url, user_agent, rqdata = rqdata, logger=logger, proxy = proxy, proxy_ip = proxy_ip, worker_name = worker_name)
    raise NotImplementedError(f'{service} captcha service is not implemented.')
