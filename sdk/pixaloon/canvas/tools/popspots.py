from PySide6 import QtGui, QtCore
from pixaloon.toolmode import ToolMode
from pixaloon.canvas.tools.basetool import NavigationTool
from pixaloon.mathutils import distance


class PopSpotTool(NavigationTool):
    def __init__(self, canvas=None):
        super().__init__(canvas)
        self.editing_index = None

    def mousePressEvent(self, event):
        if self.toolmode.mode == ToolMode.SELECTION:
            return
        qpoint = self.document.viewportmapper.to_units_coords(event.pos())
        point = [int(v) for v in qpoint.toTuple()]
        if self.toolmode.mode == ToolMode.EDIT:
            for i, point2 in enumerate(self.document.data['popspots']):
                if distance(point, point2) < 2:
                    self.editing_index = i
                    return
            return
        self.document.data['popspots'].append(point)
        self.document.edited.emit()
        self.editing_index = -1

    def mouseMoveEvent(self, event):
        if super().mouseMoveEvent(event):
            return True
        conditions = (
            self.toolmode.mode == ToolMode.SELECTION or
            self.editing_index is None)
        if conditions:
            return True
        qpoint = self.document.viewportmapper.to_units_coords(event.pos())
        point = [int(v) for v in qpoint.toTuple()]
        self.document.data['popspots'][self.editing_index] = point
        self.document.edited.emit()
        return True

    def mouseReleaseEvent(self, event):
        if self.editing_index is None:
            return super().mouseReleaseEvent(event)
        qpoint = self.viewportmapper.to_units_coords(event.pos())
        point = [int(v) for v in qpoint.toTuple()]
        self.document.data['popspots'][self.editing_index] = point
        self.document.edited.emit()
        self.editing_index = None
        return super().mouseReleaseEvent(event)

    def draw(self, painter):
        if self.toolmode.mode != ToolMode.EDIT:
            return
        qpoint = self.canvas.mapFromGlobal(QtGui.QCursor.pos())
        point = self.document.viewportmapper.to_units_coords(qpoint)
        point = [int(v) for v in point.toTuple()]
        for point2 in self.document.data['popspots']:
            distance(point, point2)
            if distance(point, point2) < 2:
                pen = QtGui.QPen(QtGui.QColor(255, 255, 0, 50))
                pen.setWidth(3)
                painter.setPen(pen)
                painter.setBrush(QtCore.Qt.NoBrush)
                p = QtCore.QPoint(*point2)
                p = self.viewportmapper.to_viewport_coords(p)
                painter.drawEllipse(p, 7, 7)
                return
