from PySide6 import QtGui, QtCore
from pixaloon.selection import Selection
from pixaloon.canvas.tools.basetool import NavigationTool
from pixaloon.toolmode import ToolMode
from pixaloon.mathutils import distance


class ShadowTool(NavigationTool):
    def __init__(self, canvas=None):
        super().__init__(canvas)
        self.editing_index = None
        self.new_shape_data = None
        self.close_new_shape = False

    def mousePressEvent(self, event):
        if event.button() != QtCore.Qt.LeftButton:
            return
        if self.toolmode.mode == ToolMode.SELECTION:
            return self.mouse_press_selection(event)
        if self.toolmode.mode == ToolMode.CREATE:
            return self.mouse_press_create(event)

    def mouse_press_create(self, event):
        qpoint = self.document.viewportmapper.to_units_coords(event.pos())
        qpoint = qpoint.toPoint()
        point = [int(v) for v in qpoint.toTuple()]
        if self.new_shape_data is None:
            self.new_shape_data = [point]
            return
        if not self.close_new_shape:
            self.new_shape_data.append(point)
            return
        data = {'color': (0, 0, 0, 100), 'polygon': self.new_shape_data}
        self.document.data['shadow_zones'].append(data)
        self.document.edited.emit()
        self.selection.tool = Selection.SHADOW
        self.selection.data = len(self.document.data['shadow_zones']) - 1
        self.selection.changed.emit(self)
        self.new_shape_data = None
        return

    def mouseMoveEvent(self, event):
        if super().mouseMoveEvent(event):
            return
        qpoint = self.document.viewportmapper.to_units_coords(event.pos())
        qpoint = qpoint.toPoint()
        point = [int(v) for v in qpoint.toTuple()]
        if self.toolmode.mode == ToolMode.CREATE and self.new_shape_data:
            polygon = self.new_shape_data
            if len(polygon) < 3:
                self.close_new_shape = False
                return
            self.close_new_shape = distance(point, polygon[0]) < 3
            return True

    def mouse_press_selection(self, event):
        qpoint = self.document.viewportmapper.to_units_coords(event.pos())
        qpoint = qpoint.toPoint()
        for i, data in enumerate(self.document.data['shadow_zones']):
            points = [QtCore.QPointF(*p) for p in data['polygon']]
            polygon = QtGui.QPolygonF(points)
            if polygon.containsPoint(qpoint, QtCore.Qt.OddEvenFill):
                self.selection.tool = Selection.SHADOW
                self.selection.data = i
                self.selection.changed.emit(self)
                return

            self.selection.clear()
            self.selection.changed.emit(self)

    def draw(self, painter):
        if self.toolmode.mode != ToolMode.CREATE or not self.new_shape_data:
            return
        data = self.new_shape_data
        painter.setPen(QtCore.Qt.yellow)
        painter.setBrush(QtCore.Qt.yellow)
        wh = self.viewportmapper.to_viewport(1)
        for point in data:
            p = QtCore.QPoint(*point)
            p = self.viewportmapper.to_viewport_coords(p)
            painter.drawRect(p.x(), p.y(), wh, wh)
        if len(data) == 1:
            return
        color = QtGui.QColor(QtCore.Qt.yellow)
        color.setAlpha(100)
        painter.setBrush(color)
        polygon = QtGui.QPolygonF([
            self.viewportmapper.to_viewport_coords(QtCore.QPoint(*p))
            for p in data])
        painter.drawPolygon(polygon)
        if self.close_new_shape:
            pen = QtGui.QPen(color)
            radius = self.viewportmapper.to_viewport(3)
            painter.setPen(pen)
            p = QtCore.QPoint(*data[0])
            p = self.viewportmapper.to_viewport_coords(p)
            p.setX(p.x() + self.viewportmapper.to_viewport(0.5))
            p.setY(p.y() + self.viewportmapper.to_viewport(0.5))
            painter.drawEllipse(p, radius, radius)

