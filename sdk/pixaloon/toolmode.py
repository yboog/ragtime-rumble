

class ToolMode:
    SELECTION = 0
    CREATE = 1
    EDIT = 2

    def __init__(self):
        self.mode = self.SELECTION

    def set_mode(self, mode):
        if mode not in (0, 1, 2):
            raise ValueError('Wrong tool mode: {mode} (0, 1, 2 supported)')
