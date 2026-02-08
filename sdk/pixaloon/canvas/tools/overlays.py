from PySide6 import QtCore, QtWidgets
from pixaloon.selection import Selection
from pixaloon.canvas.tools.basetool import NavigationTool
from pixaloon.toolmode import ToolMode
from pixaloon.mathutils import start_end_to_rect_data


class OverlayTool(NavigationTool):
    def __init__(self, canvas=None, document=None):
        super().__init__(canvas, document)
        self.editing_index = None

    def mousePressEvent(self, event):
        if self.toolmode.mode == ToolMode.SELECTION:
            return self.mouse_press_selection(event)
        if self.toolmode.mode == ToolMode.CREATE:
            return self.mouse_press_create(event)

    def mouse_press_create(self, event):
        qpoint = self.document.viewportmapper.to_units_coords(event.pos())
        qpoint = qpoint.toPoint()
        point = [int(v) for v in qpoint.toTuple()]
        if self.new_shape_data is None:
            self.new_shape_data = [point, [point[0] + 1, point[1] + 1]]

    def mouseMoveEvent(self, event):
        if super().mouseMoveEvent(event):
            return
        qpoint = self.document.viewportmapper.to_units_coords(event.pos())
        qpoint = qpoint.toPoint()
        point = [int(v) for v in qpoint.toTuple()]
        if self.toolmode.mode == ToolMode.CREATE and self.new_shape_data:
            self.new_shape_data[1] = point

    def mouseReleaseEvent(self, event):
        return_conditions = (
            self.toolmode.mode != ToolMode.CREATE or
            not self.new_shape_data)
        if return_conditions:
            return
        rect = start_end_to_rect_data(*self.new_shape_data)
        self.document.data['fences'].append(rect)
        self.selection.tool = Selection.FENCE
        self.selection.data = len(self.document.data['fences']) - 1
        self.new_shape_data = None
        self.document.edited.emit()
        self.selection.changed.emit()
        return super().mouseReleaseEvent(event)

    def mouse_press_selection(self, event):
        qpoint = self.document.viewportmapper.to_units_coords(event.pos())
        qpoint = qpoint.toPoint()
        for i, overlay in enumerate(self.document.data['overlays']):
            image = self.document.overlays[i]
            pos = overlay['position']
            rect = QtCore.QRect(QtCore.QPoint(*pos), image.size())
            if rect.contains(qpoint):
                self.selection.tool = Selection.OVERLAY
                self.selection.data = i
                self.selection.changed.emit()
                return

            self.selection.clear()
            self.selection.changed.emit()

    def draw(self, painter):
        match self.toolmode.mode:
            case ToolMode.EDIT:
                return
            case ToolMode.CREATE:
                self.draw_create(painter)

    def draw_create(self, painter):
        if self.new_shape_data is None:
            return
        data = start_end_to_rect_data(*self.new_shape_data)
        rect = QtCore.QRectF(*data)
        painter.drawRect(self.viewportmapper.to_viewport_rect(rect))
