from PySide6 import QtGui, QtCore
from pixaloon.selection import Selection
from pixaloon.canvas.tools.basetool import NavigationTool
from pixaloon.toolmode import ToolMode
from pixaloon.mathutils import distance, start_end_to_rect_data


class WallTool(NavigationTool):
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
            return self.create_new_shape(point)
        if self.new_shape_data[0] == 'shape':
            if not self.close_new_shape:
                self.new_shape_data[1].append(point)
                return
            self.document.data['walls'].append(self.new_shape_data[1])
            self.document.edited.emit()
            self.selection.tool = Selection.WALL
            self.selection.data = len(self.document.data['walls']) - 1
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
            if self.new_shape_data[0] == 'shape':
                data = self.new_shape_data[1]
                if len(data) < 3:
                    self.close_new_shape = False
                    return
                self.close_new_shape = distance(point, data[0]) < 3
                return True
            self.new_shape_data[1][1] = point

    def mouseReleaseEvent(self, event):
        return_conditions = (
            self.toolmode.mode != ToolMode.CREATE or
            not self.new_shape_data or
            self.new_shape_data[0] != 'rect')
        if return_conditions:
            return
        rect = start_end_to_rect_data(*self.new_shape_data[1])
        self.document.data['no_go_zones'].append(rect)
        self.selection.tool = Selection.NO_GO_ZONE
        self.selection.data = len(self.document.data['no_go_zones']) - 1
        self.new_shape_data = None
        self.document.edited.emit()
        self.selection.changed.emit(self)
        return super().mouseReleaseEvent(event)

    def create_new_shape(self, point):
        if self.document.navigator.shift_pressed:
            self.new_shape_data = 'shape', [point]
            return
        tl_bl = [point, [point[0] + 1, point[1] + 1]]
        self.new_shape_data = 'rect', tl_bl

    def mouse_press_selection(self, event):
        qpoint = self.document.viewportmapper.to_units_coords(event.pos())
        qpoint = qpoint.toPoint()
        # point = [int(v) for v in qpoint.toTuple()]
        for i, zone in enumerate(self.document.data['no_go_zones']):
            rect = QtCore.QRect(*zone)
            if rect.contains(qpoint):
                self.selection.tool = Selection.NO_GO_ZONE
                self.selection.data = i
                self.selection.changed.emit(self)
                return

        for i, wall in enumerate(self.document.data['walls']):
            points = [QtCore.QPointF(*p) for p in wall]
            polygon = QtGui.QPolygonF(points)
            if polygon.containsPoint(qpoint, QtCore.Qt.OddEvenFill):
                self.selection.tool = Selection.WALL
                self.selection.data = i
                self.selection.changed.emit(self)
                return

            self.selection.clear()
            self.selection.changed.emit(self)

    def draw(self, painter):
        match self.toolmode.mode:
            case ToolMode.EDIT:
                return
            case ToolMode.CREATE:
                self.draw_create(painter)

    def draw_create(self, painter):
        if self.new_shape_data is None:
            return
        if self.new_shape_data[0] == 'rect':
            self.draw_rect(painter)
        if self.new_shape_data[0] == 'shape':
            self.draw_shape(painter)

    def draw_rect(self, painter):
        data = start_end_to_rect_data(*self.new_shape_data[1])
        rect = QtCore.QRectF(*data)
        painter.drawRect(self.viewportmapper.to_viewport_rect(rect))

    def draw_shape(self, painter):
        data = self.new_shape_data[1]
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

