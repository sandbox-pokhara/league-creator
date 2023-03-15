import logging
import tkinter as tk

MAX_HISTORY = 2000


class TkinterHandler(logging.Handler):
    def __init__(self, text=None):
        logging.Handler.__init__(self, )
        self.text = text
        self.history = []
        self.history_size = 0

    def emit(self, record):
        '''Writes the message'''
        try:
            msg = self.format(record) + '\n'
            if self.history_size >= MAX_HISTORY:
                self.text.delete('1.0', '1.end+1c')
                self.history.pop(0)
                self.history_size -= 1
            self.history_size += 1
            self.history.append(msg)
            if self.text is None:
                return
            self.text.insert(tk.END, msg)
            self.text.see('end')
        except RuntimeError:
            pass
