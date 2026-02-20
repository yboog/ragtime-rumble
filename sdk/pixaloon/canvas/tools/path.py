from PySide6 import QtGui, QtCore
from pixaloon.mathutils import distance
from pixaloon.canvas.tools.basetool import NavigationTool
from pixaloon.selection import Selection
from pixaloon.toolmode import ToolMode


class PathTool(NavigationTool):
    def __init__(self, canvas=None):
        super().__init__(canvas)
        self.path_data = None

    def mousePressEvent(self, event):
        if self.toolmode.mode != ToolMode.CREATE:
            return
        point = self.viewportmapper.to_units_coords(event.pos())
        if self.path_data is None:
            self.path_data = [point]
            return
        if distance(self.path_data[-1].toTuple(), point.toTuple()) < 2:
            return
        self.path_data.append(point)

    def mouseMoveEvent(self, event):
        if super().mouseMoveEvent(event):
            return True

    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        if event.key() != QtCore.Qt.Key.Key_Return or self.path_data is None:
            return
        self.document.data['paths'].append({
            'points': [[int(p.x()), int(p.y())] for p in self.path_data],
            'hard': True})
        self.document.edited.emit()
        self.selection.data = [len(self.document.data['paths']) - 1, None]
        self.selection.tool = Selection.PATH
        self.selection.changed.emit(self.canvas)
        self.path_data = None

    def draw(self, painter):
        if self.path_data is None:
            return
        pen = QtGui.QPen(QtCore.Qt.cyan)
        pen.setWidth(4)
        pen.setStyle(QtCore.Qt.SolidLine)
        painter.setPen(pen)
        points = [
            self.viewportmapper.to_viewport_coords(p)
            for p in self.path_data]
        points.append(self.canvas.mapFromGlobal(QtGui.QCursor.pos()))

        start = None
        for end in points:
            if start is None:
                start = end
                continue
            painter.drawLine(start, end)
            start = end

        painter.setPen(QtCore.Qt.green)
        painter.drawEllipse(points[0], 2, 2)
        painter.setPen(QtCore.Qt.red)
        painter.drawEllipse(points[-1], 1, 1)


