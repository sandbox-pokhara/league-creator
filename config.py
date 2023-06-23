import json
import os
from tkinter import messagebox

from builder import get_variable

file_name = 'config.json'

BASE_PATH = os.path.realpath('.')


def load_config():
    # read from file
    try:
        with open(file_name) as fp:
            config = json.load(fp)
    except (OSError, json.JSONDecodeError):
        config = {}
     # set default values
    config['is_use_proxies'] = config.get('is_use_proxies', False)
    config['accounts_count'] = config.get('accounts_count', 10)
    config['workers'] = config.get('workers', 10)
    config['captcha_type'] = config.get('captcha_type', 'anti-captcha')
    config['captcha_key'] = config.get('captcha_key', '')
    config['region'] = config.get('region', 'EUW')
    config['write_format'] = config.get('write_format', 'username:password')
    config['proxies_file_path'] = config.get('proxies_file_path', '')
    config['email_host'] = config.get('email_host', 'gmail.com')
    config['account_write_path'] = config.get('account_write_path', BASE_PATH)
    config['min_delay'] = config.get('min_delay', 0)
    config['max_delay'] = config.get('max_delay', 0)
    return config


error_messages = {
    'accounts_count': 'Error: Accounts Count cannot be empty',
    'workers': 'Error: Workers cannot be empty',
    'captcha_type': 'Error: Captcha Type cannot be empty',
    'captcha_key': 'Error: Captcha Key cannot be empty',
    'region': 'Error: At least one region must be selected',
    'write_format': 'Error: Output Format cannot be empty',
    'proxies_file_path': 'Error: Proxies File Path cannot be empty',
    'email_host': 'Error: Email Host cannot be empty',
    'account_write_path': 'Error: Output Folder cannot be empty',
    'min_delay': 'Error: Min Delay cannot be empty',
    'max_delay': 'Error: Max Delay cannot be empty',
}


def dump_config():
    config = {
        'accounts_count': get_variable('accounts_count'),
        'captcha_type': get_variable('captcha_type'),
        'captcha_key': get_variable('captcha_key'),
        'workers': get_variable('workers'),
        'region': get_variable('region'),
        'write_format': get_variable('write_format'),
        'is_use_proxies': get_variable('is_use_proxies'),
        'proxies_file_path': get_variable('proxies_file_path'),
        'email_host': get_variable('email_host'),
        'account_write_path': get_variable('account_write_path'),
        'min_delay': get_variable('min_delay'),
        'max_delay': get_variable('max_delay'),
    }
    try:
        with open(file_name, 'w') as fp:
            json.dump(config, fp, indent=2)
            return config

    except OSError:
        pass


def show_error_popup(message):
    messagebox.showerror('Error', message)


def validate_config(config):
    for key, item in config.items():
        if item == '':
            if key == 'proxies_file_path' and not config.get('is_use_proxies', False):
                continue
            show_error_popup(error_messages[key])
            return False
    return True
