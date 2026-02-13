
from PySide6 import QtCore

class Selection(QtCore.QObject):
    changed = QtCore.Signal()

    POPSPOT = 'popspots'
    NO_GO_ZONE = 'no_go_zones'
    WALL = 'wall'
    FENCE = 'fences'
    INTERACTION = 'interaction'
    OVERLAY = 'overlay'

    def __init__(self):
        super().__init__()
        self.tool = None
        self.data = None

    def __bool__(self):
        return self.data is not None

    def clear(self):
        self.tool = None
        self.data = None
