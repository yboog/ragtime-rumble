from PySide6 import QtCore
from pixaloon.selection import Selection
from pixaloon.canvas.tools.basetool import NavigationTool
from pixaloon.toolmode import ToolMode
from pixaloon.mathutils import start_end_to_rect_data


class AbstractSquareTool(NavigationTool):
    DATA_KEY: str = ''
    SELECTION_TOOL: str = '' # Selection.TOOL

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


class FenceTool(AbstractSquareTool):
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
        self.selection.changed.emit(self)
        return super().mouseReleaseEvent(event)

    def mouse_press_selection(self, event):
        qpoint = self.document.viewportmapper.to_units_coords(event.pos())
        qpoint = qpoint.toPoint()
        # point = [int(v) for v in qpoint.toTuple()]
        for i, zone in enumerate(self.document.data['fences']):
            rect = QtCore.QRect(*zone)
            if rect.contains(qpoint):
                self.selection.tool = Selection.FENCE
                self.selection.data = i
                self.selection.changed.emit(self)
                return

            self.selection.clear()
            self.selection.changed.emit(self)

class StairTool(AbstractSquareTool):
    def mouseReleaseEvent(self, event):
        return_conditions = (
            self.toolmode.mode != ToolMode.CREATE or
            not self.new_shape_data)
        if return_conditions:
            return
        rect = start_end_to_rect_data(*self.new_shape_data)
        data = {'zone': rect, 'inclination': 0.5}
        self.document.data['stairs'].append(data)
        self.selection.tool = Selection.STAIR
        self.selection.data = len(self.document.data['stairs']) - 1
        self.new_shape_data = None
        self.document.edited.emit()
        self.selection.changed.emit(self)
        return super().mouseReleaseEvent(event)

    def mouse_press_selection(self, event):
        qpoint = self.document.viewportmapper.to_units_coords(event.pos())
        qpoint = qpoint.toPoint()
        # point = [int(v) for v in qpoint.toTuple()]
        for i, stair in enumerate(self.document.data['stairs']):
            rect = QtCore.QRect(*stair['zone'])
            if rect.contains(qpoint):
                self.selection.tool = Selection.STAIR
                self.selection.data = i
                self.selection.changed.emit(self)
                return

            self.selection.clear()
            self.selection.changed.emit(self)
