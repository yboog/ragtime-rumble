
from PySide6 import QtCore

class Selection(QtCore.QObject):
    changed = QtCore.Signal(object)

    BACKGROUND = 'background'
    FENCE = 'fences'
    INTERACTION = 'interaction'
    NO_GO_ZONE = 'no_go_zones'
    NPC = 'npc'
    PATH = 'path'
    POPSPOT = 'popspots'
    PROP = 'prop'
    OVERLAY = 'overlay'
    SHADOW = 'Shadow'
    STARTUP = 'startup'
    STAIR = 'stair'
    TARGET = 'origin_targets'
    WALL = 'wall'
    BGPH = 'bgph'

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
