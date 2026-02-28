from PySide6 import QtGui, QtCore
from pixaloon.mathutils import distance
from pixaloon.canvas.tools.basetool import NavigationTool
from pixaloon.selection import Selection
from pixaloon.toolmode import ToolMode


class NpcTool(NavigationTool):
    def __init__(self, canvas=None):
        super().__init__(canvas)
        self.path_data = None
