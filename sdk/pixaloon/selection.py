
from PySide6 import QtCore

class Selection(QtCore.QObject):
    changed = QtCore.Signal(object)

    POPSPOT = 'popspots'
    PATH = 'path'
    PROP = 'prop'
    NO_GO_ZONE = 'no_go_zones'
    STARTUP = 'startup'
    WALL = 'wall'
    FENCE = 'fences'
    INTERACTION = 'interaction'
    OVERLAY = 'overlay'
    TARGET = 'origin_targets'
    BACKGROUND = 'background'
    STAIR = 'stair'

    def __init__(self):
        super().__init__()
        self.tool = None
        self.data = None

    def __repr__(self):
        return str((self.tool, self.data))

    def __bool__(self):
        return self.data is not None

    def clear(self):
        self.tool = None
        self.data = None
