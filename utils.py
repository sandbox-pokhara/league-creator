from builder import set_variable


class TkList(list):
    # Custom list that maps it's length to tk variable

    def __init__(self, label, initial):
        self.label = label
        super().__init__(initial)

    def append(self, value):
        super().append(value)
        set_variable(self.label, len(self))

    def remove(self, value):
        super().remove(value)
        set_variable(self.label, len(self))
