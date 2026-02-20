from PySide6 import QtGui, QtCore
from pixaloon.selection import Selection
from pixaloon.canvas.tools.basetool import NavigationTool
from pixaloon.toolmode import ToolMode
from pixaloon.mathutils import distance, start_end_to_rect_data


class TargetTool(NavigationTool):
    def __init__(self, canvas=None):
        super().__init__(canvas)
        self.editing_index = None
        self.new_shape_data = None

    def mousePressEvent(self, event):
        if self.toolmode.mode == ToolMode.SELECTION:
            return self.mouse_press_selection(event)
        if self.toolmode.mode == ToolMode.CREATE:
            return self.mouse_press_create(event)

    def mouse_press_create(self, event):
        qpoint = self.document.viewportmapper.to_units_coords(event.pos())
        qpoint = qpoint.toPoint()
        point = [int(v) for v in qpoint.toTuple()]
        if self.new_shape_data is not None:
            return

        shape_type = (
            'destination'
            if self.document.navigator.shift_pressed and
            self.document.selection.data else
            'origin')

        tl_bl = [point, [point[0] + 1, point[1] + 1]]
        self.new_shape_data = shape_type, tl_bl

    def mouseMoveEvent(self, event):
        if super().mouseMoveEvent(event):
            return
        qpoint = self.document.viewportmapper.to_units_coords(event.pos())
        qpoint = qpoint.toPoint()
        point = [int(v) for v in qpoint.toTuple()]
        if self.toolmode.mode == ToolMode.CREATE and self.new_shape_data:
            self.new_shape_data[1][1] = point

    def mouseReleaseEvent(self, event):
        return_conditions = (
            self.toolmode.mode != ToolMode.CREATE or
            not self.new_shape_data)
        if return_conditions:
            return
        rect = start_end_to_rect_data(*self.new_shape_data[1])
        if self.new_shape_data[0] == 'origin':
            data = {'origin': rect, 'weight': 3, 'destinations': []}
            self.document.data['targets'].append(data)
            self.selection.tool = Selection.TARGET
            self.selection.data = len(self.document.data['targets']) - 1, None
        else:
            index = self.document.selection.data[0]
            self.document.data['targets'][index]['destinations'].append(rect)
            i = len(self.document.data['targets'][index]['destinations']) - 1
            self.selection.data = index, i
        self.new_shape_data = None
        self.selection.changed.emit(self)
        self.document.edited.emit()
        return super().mouseReleaseEvent(event)

    def mouse_press_selection(self, event):
        qpoint = self.document.viewportmapper.to_units_coords(event.pos())
        qpoint = qpoint.toPoint()
        for i, target in enumerate(self.document.data['targets']):
            rect = QtCore.QRect(*target['origin'])
            if rect.contains(qpoint):
                self.selection.tool = Selection.TARGET
                self.selection.data = [i, None]
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
        data = start_end_to_rect_data(*self.new_shape_data[1])
        rect = QtCore.QRectF(*data)
        painter.drawRect(self.viewportmapper.to_viewport_rect(rect))
