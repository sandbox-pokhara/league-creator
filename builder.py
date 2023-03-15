
class PygubuBuilder:
    '''A wrapper class around the pygubu builder for easy gui building'''

    def __init__(self, pygubu_builder=None):
        self.pygubu_builder = pygubu_builder
        self.mappings = {}

    def set_mappings(self, mappings):
        '''Sets label entry mappings'''
        for i, label in enumerate(mappings):
            self.set_variable(f'label_{i+1}', label)
        self.mappings = {name: f'entry_{i+1}' for i, name in enumerate(mappings)}

    def set_variable(self, name, value):
        '''Sets a tk variable'''
        if self.pygubu_builder is None:
            return
        if name in self.pygubu_builder.tkvariables:
            self.pygubu_builder.tkvariables[name].set(value)

    def get_variable(self, name):
        '''Returns a tk variable'''
        if self.pygubu_builder is None or name not in self.pygubu_builder.tkvariables:
            return None
        return self.pygubu_builder.tkvariables[name].get()

    def set_attribute(self, name, attribute, value):
        '''Set attribute of tkinter object'''
        if self.pygubu_builder is None:
            return
        if name in self.pygubu_builder.objects:
            self.pygubu_builder.get_object(name).configure(**{attribute: value})

    def clear_status(self):
        '''Clears status after some time'''
        self.set_variable('status', '')

    def set_status(self, value):
        '''Helper method to set status'''
        self.set_variable('status', value)

    def get_all_children(self, widget, list_=None):
        '''Returns every child widgets recursively'''
        if not list_:
            list_ = []
        for item in widget.winfo_children():
            list_.append(item)
            self.get_all_children(item, list_)
        return list_

    def disable_all(self, widget):
        '''Disables all children '''
        for my_widget in self.get_all_children(widget):
            if my_widget.winfo_class() in ['Entry', 'Button', 'Label', 'Spinbox', 'Checkbutton', 'TCombobox']:
                my_widget['state'] = 'disabled'

    def enable_all(self, widget):
        '''Enables all children '''
        for my_widget in self.get_all_children(widget):
            if my_widget.winfo_class() in ['Entry', 'Button', 'Label', 'Spinbox', 'Checkbutton', ]:
                my_widget['state'] = 'normal'


builder = PygubuBuilder()
set_mappings = builder.set_mappings
set_variable = builder.set_variable
get_variable = builder.get_variable
set_status = builder.set_status
set_attribute = builder.set_attribute
