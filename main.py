import asyncio
import atexit
import os
import traceback
from collections import deque
from datetime import datetime
from itertools import cycle
from threading import Thread
from tkinter import messagebox
from tkinter.filedialog import askdirectory
from tkinter.filedialog import askopenfilename

import pygubu

from builder import builder
from builder import get_variable
from builder import set_attribute
from builder import set_variable
from config import dump_config
from config import load_config
from constants import CAPTCHAS
from constants import REGION_CHOICES
from constants import WRITE_FORMATS
from logger import logger
from logger import tk_handler
from proxies import get_proxies
from user_agents import get_user_agents
from worker import run_worker

BASE_PATH = os.path.realpath('.')


class App:
    def __init__(self):
        self.builder = pygubu.Builder()
        self.builder.add_from_file('app.ui')
        self.mainwindow = self.builder.get_object('main_window')
        self.builder.connect_callbacks(self)
        builder.pygubu_builder = self.builder
        tk_handler.text = self.builder.get_object('console')
        self.initialize_gui_values()

    def initialize_gui_values(self):
        set_attribute('region_widget', 'values', REGION_CHOICES)
        set_attribute('write_format_widget', 'values', WRITE_FORMATS)
        set_attribute('captcha_type_widget', 'values', CAPTCHAS)

        # Load saved config
        config = load_config()
        set_variable('is_use_proxies', config['is_use_proxies'])
        set_variable('accounts_count', config['accounts_count'])
        set_variable('captcha_type', config['captcha_type'])
        set_variable('captcha_key', config['captcha_key'])
        set_variable('workers', config['workers'])
        set_variable('region', config['region'])
        set_variable('write_format', config['write_format'])
        set_variable('proxies_file_path', config['proxies_file_path'])
        set_variable('email_host', config['email_host'])
        set_variable('account_write_path', config['account_write_path'])

        self.set_is_use_proxies()

    # called when is_use_proxies is changed
    def set_is_use_proxies(self):
        is_use_proxies = get_variable('is_use_proxies')
        if not is_use_proxies:
            set_attribute('proxy_pathchooser', 'state', 'disabled')
        else:
            set_attribute('proxy_pathchooser', 'state', 'normal')

    def set_proxies_path(self):
        path = os.path.realpath(askopenfilename(title=f'Choose proxies path'))
        set_variable('proxies_file_path', path)

    def set_accounts_write_path(self):
        path = os.path.realpath(askdirectory(title=f'Choose account write path'))
        set_variable('account_write_path', path)

    def on_start(self):
        def task():
            try:
                dump_config()
                builder.set_attribute('start', 'state', 'disabled')

                # get data from gui
                accounts_count = get_variable('accounts_count')
                captcha_type = get_variable('captcha_type')
                captcha_key = get_variable('captcha_key')
                workers = get_variable('workers')
                region = get_variable('region')
                write_format = get_variable('write_format')
                is_use_proxies = get_variable('is_use_proxies')
                proxies_file_path = get_variable('proxies_file_path')
                email_host = get_variable('email_host')
                account_write_path = get_variable('account_write_path')

                # TODO
                # if not validate_config(config):
                #     return

                # initialize vars before task
                now = datetime.now().strftime("%Y-%b-%d %H-%M-%S").lower()
                output_file = f'output_{region}_{now}.txt'
                output_file = os.path.join(account_write_path, output_file)
                proxies = get_proxies(proxies_file_path) if is_use_proxies else None
                proxy_cycle = cycle(proxies) if proxies is not None else None
                proxy_count = 0 if proxies is None else len(proxies)
                user_agents = get_user_agents()
                set_variable('proxy_count', proxy_count)
                set_variable('remaining_count', accounts_count)
                creating = []
                created = []
                errors = deque(maxlen=10)
                proxy_rate_limits = {}
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                worker_count = min(accounts_count, workers)
                logger.info(f'Worker Count: {worker_count}')

                tasks = [run_worker(
                    name=f'worker{i}',
                    output_file=output_file,
                    to_create=accounts_count,
                    region=region,
                    email_host=email_host,
                    creating=creating,
                    completed=created,
                    errors=errors,
                    proxy_rate_limits=proxy_rate_limits,
                    captcha_type=captcha_type,
                    captcha_key=captcha_key,
                    proxies=proxy_cycle,
                    user_agents=user_agents,
                ) for i in range(worker_count)]
                loop.run_until_complete(asyncio.gather(*tasks))
                logger.info('Completed.')

            except Exception:
                logger.debug(traceback.format_exc())
                messagebox.showerror('Unhandled Exception', traceback.format_exc())
            finally:
                builder.set_attribute('start', 'state', 'normal')

        Thread(target=task, daemon=True).start()

    def run(self):
        atexit.register(dump_config)
        self.mainwindow.mainloop()


if __name__ == '__main__':
    app = App()
    app.run()
