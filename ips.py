
import os


def get_ips(file_path):
    try:
        with open(file_path) as fp:
            proxies = fp.read().splitlines()
            return set(proxies)
    except OSError:
        return set()


def add_ip(file_path, ip):
    try:
        dirname = os.path.dirname(file_path)
        if dirname:
            os.makedirs(dirname, exist_ok=True)
        with open(file_path, 'a') as fp:
            proxies = fp.write(ip + '\n')
            return proxies
    except OSError:
        pass
