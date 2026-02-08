
from PySide6 import QtCore


class Selection(QtCore.QObject):
    changed = QtCore.Signal()

    POPSPOTS = 'popspots'
    NO_GO_ZONES = 'no_go_zones'
    WALL = 'wall'
    FENCE = 'fences'
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
