import asyncio
import atexit
import os
import tkinter as tk
import traceback
from collections import deque
from itertools import cycle
from threading import Thread
from tkinter import messagebox

import pygubu

from builder import builder
from builder import get_variable
from builder import set_attribute
from builder import set_variable
from config import dump_config
from config import load_config
from config import show_error_popup
from config import validate_config
from constants import CAPTCHAS
from constants import REGION_CHOICES
from constants import WRITE_FORMATS
from ips import get_ips
from logger import logger
from logger import tk_handler
from proxies import get_proxies
from user_agents import get_user_agents
from utils import TkList
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
        self.region_configs = {region: [0] for region in REGION_CHOICES}

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
        set_variable('min_delay', config['min_delay'])
        set_variable('max_delay', config['max_delay'])

        self.set_is_use_proxies()

    # called when is_use_proxies is changed
    def set_is_use_proxies(self):
        is_use_proxies = get_variable('is_use_proxies')
        if not is_use_proxies:
            set_attribute('proxy_pathchooser', 'state', 'disabled')
        else:
            set_attribute('proxy_pathchooser', 'state', 'normal')

    def get_account_basket_data(self):

        for values in self.region_configs.values():
            if len(values) > 1:
                break
        else:
            return

        return sum([i[0] for i in self.region_configs.values()])

    def on_start(self):
        total_count = (self.get_account_basket_data())

        if not total_count:
            show_error_popup("Error: Select at least one region.")
            return

        def task():
            try:
                config = dump_config()

                if not validate_config(config):
                    return

                builder.set_attribute('start', 'state', 'disabled')
                builder.set_attribute('region_config_clear_button', 'state', 'disabled')

                captcha_type = get_variable('captcha_type')
                captcha_key = get_variable('captcha_key')
                workers = get_variable('workers')
                # write_format = get_variable('write_format')
                is_use_proxies = get_variable('is_use_proxies')
                proxies_file_path = get_variable('proxies_file_path')
                email_host = get_variable('email_host')
                account_write_path = get_variable('account_write_path')
                min_delay = get_variable('min_delay')
                max_delay = get_variable('max_delay')

                proxies = get_proxies(proxies_file_path) if is_use_proxies else None
                proxy_cycle = cycle(proxies) if proxies is not None else None
                proxy_count = 0 if proxies is None else len(proxies)
                user_agents = get_user_agents()
                bad_ips = get_ips('bad_ips.txt')
                set_variable('progress', 0)
                set_variable('proxy_count', proxy_count)
                set_variable('remaining_count', total_count)
                set_variable('completed_count', 0)
                creating = TkList('current_count', [])
                created = []
                errors = deque(maxlen=10)
                assigned_proixes = {}
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                accounts_state = []

                def yield_regions():
                    for region, items in self.region_configs.items():
                        for _ in range(items[0]):
                            yield region

                accounts_state = yield_regions()

                worker_count = min(total_count, workers)
                tasks = [
                    (run_worker(
                        name=f'worker{i}',
                        region=next(accounts_state),
                        accounts_state=accounts_state,
                        to_create=total_count,
                        email_host=email_host,
                        creating=creating,
                        completed=created,
                        errors=errors,
                        assigned_proixes=assigned_proixes,
                        captcha_type=captcha_type,
                        captcha_key=captcha_key,
                        proxies=proxy_cycle,
                        proxies_len=len(proxies) if proxies is not None else 0,
                        bad_ips=bad_ips,
                        user_agents=user_agents,
                        min_delay=min_delay,
                        max_delay=max_delay,
                        account_write_path=account_write_path,
                    )) for i in range(worker_count)]
                asyncio.run(asyncio.wait(tasks))
                logger.info('Completed.')

            except Exception:
                logger.debug(traceback.format_exc())
                messagebox.showerror('Unhandled Exception', traceback.format_exc())
            finally:
                builder.set_attribute('start', 'state', 'normal')

        Thread(target=task, daemon=True).start()

    def remove_region_button_callback(self, e):
        region = e.widget['text'].split('-')[0]
        self.region_configs[region][0] = 0
        self.region_configs[region].pop()
        e.widget.destroy()

    def clear_accounts_basket(self, *args):
        for i in self.region_configs.values():
            i[0] = 0
            if len(i) > 1:
                i[1].destroy()
            i.pop()
        self.region_configs = {region: [0] for region in REGION_CHOICES}

    def add_region_callback(self, event):
        region, count = get_variable('region'), get_variable('accounts_count')
        region_configs = self.builder.get_object('accounts_basket')

        if not (self.region_configs[region][0]):
            button = tk.Button(region_configs, text=f'{region}-{count}')
            button.bind('<Button-1>', self.remove_region_button_callback)

            self.region_configs[region].append(button)

            num_widgets = len(region_configs.grid_slaves())

            row = num_widgets // 4
            column = num_widgets % 4

            button.grid(row=row, column=column,)
            for c in range(column + 1):
                region_configs.grid_columnconfigure(c, weight=1)

        self.region_configs[region][0] = count
        self.region_configs[region][1].config(text=f'{region}-{self.region_configs[region][0]}')

    def run(self):
        atexit.register(dump_config)
        self.mainwindow.mainloop()


if __name__ == '__main__':
    app = App()
    app.run()
