import json
import os
from tkinter import messagebox

file_name = 'config.json'

BASE_PATH = os.path.realpath('.')


def load_config():
    try:
        with open(file_name) as fp:
            config = json.load(fp)
            # set default values
            config['is_use_proxies'] = config.get('is_use_proxies', False)
            config['accounts_count'] = config.get('accounts_count', 10)
            config['captcha_key'] = config.get('captcha_key', '')
            config['region'] = config.get('region', 'EUW')
            config['write_format'] = config.get('write_format', 'username:password')
            config['proxies_file_path'] = config.get('proxies_file_path', '')
            config['email_host'] = config.get('email_host', 'gmail.com')
            config['account_write_path'] = config.get('account_write_path', BASE_PATH)
            return config
    except (OSError, json.JSONDecodeError):
        return {}


def dump_config(builder):
    config = {
        'accounts_count': builder.get_variable('accounts_count').get(),
        'captcha_key': builder.get_variable('captcha_key').get(),
        'region': builder.get_variable('region').get(),
        'write_format': builder.get_variable('write_format').get(),
        'is_use_proxies': builder.get_variable('is_use_proxies').get(),
        'proxies_file_path': builder.get_variable('proxies_file_path').get(),
        'email_host': builder.get_variable('email_host').get(),
        'account_write_path': builder.get_variable('account_write_path').get(),
    }
    try:
        with open(file_name, 'w') as fp:
            return json.dump(config, fp, indent=2)
    except OSError:
        pass


def validate_config(config):
    for key, item in config.items():
        if item == '':
            if key == 'proxies_file_path' and not config.get('is_use_proxies', False):
                continue
            messagebox.showerror('Error', f'{key} cannot be empty')
            return False
    return True
