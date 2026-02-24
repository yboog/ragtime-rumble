from PySide6 import QtGui, QtCore
from pixaloon.selection import Selection
from pixaloon.canvas.tools.basetool import NavigationTool
from pixaloon.toolmode import ToolMode
from pixaloon.mathutils import start_end_to_rect_data


DEFAULT_INTERACTION = {
    "gametypes": ["advanced", "basic"],
    "play_once": False,
    "action": "poker",
    "id": "poker-4-up",
    "busy": False,
    "lockable": True,
    "direction": "left",
    "insound": None,
    "outsound": None,
    "zone": [25, 25, 50, 50],
    "target": [50, 50],
    "attraction": [0, 0, 75, 75],
}


class InteractionTool(NavigationTool):
    def __init__(self, canvas=None):
        super().__init__(canvas)
        self.editing_index = None
        self.new_shape_data = None
        self.close_new_shape = False
        self.mouse_offsets = None

    def mousePressEvent(self, event):
        if event.button() != QtCore.Qt.LeftButton:
            return
        if self.toolmode.mode == ToolMode.SELECTION:
            return self.mouse_press_selection(event)
        if self.toolmode.mode == ToolMode.CREATE:
            return self.mouse_press_create(event)
        if self.toolmode.mode == ToolMode.EDIT:
            return self.mouse_press_edit(event)

    def mouse_press_selection(self, event):
        qpoint = self.document.viewportmapper.to_units_coords(event.pos())
        qpoint = qpoint.toPoint()
        for i, interaction in enumerate(self.document.data['interactions']):
            rect = QtCore.QRect(*interaction['attraction'])
            if rect.contains(qpoint):
                self.selection.tool = Selection.INTERACTION
                self.selection.data = i
                self.selection.changed.emit(self)
                return

            self.selection.clear()
            self.selection.changed.emit(self)

    def mouse_press_edit(self, event):
        self.mouse_press_selection(event)
        if not self.selection:
            self.mouse_offsets = None
            return

        interaction = self.document.data['interactions'][self.selection.data]
        cursor = self.viewportmapper.to_units_coords(event.pos())
        self.mouse_offsets = {
            'zone': cursor - QtCore.QPointF(*interaction['zone'][:2]),
            'attraction': cursor - QtCore.QPointF(*interaction['attraction'][:2]),
            'target': cursor - QtCore.QPointF(*interaction['target'][:2])}

    def mouse_press_create(self, event):
        qpoint = self.document.viewportmapper.to_units_coords(event.pos())
        qpoint = qpoint.toPoint()
        point = [int(v) for v in qpoint.toTuple()]
        if self.new_shape_data is None:
            return self.create_new_shape(point)

    def mouseMoveEvent(self, event):
        if super().mouseMoveEvent(event):
            return
        qpoint = self.document.viewportmapper.to_units_coords(event.pos())

        if self.toolmode.mode == ToolMode.EDIT and self.selection:
            if not self.navigator.left_pressed:
                return
            # Offset attraction
            inter = self.document.data['interactions'][self.selection.data]
            tl = (qpoint - self.mouse_offsets['attraction']).toTuple()
            attraction = inter['attraction']
            attraction = [int(v) for v in [*tl, *inter['attraction'][2:]]]
            inter['attraction'] = attraction
            # Offset zone
            tl = (qpoint - self.mouse_offsets['zone']).toTuple()
            zone = inter['zone']
            zone = [int(v) for v in [*tl, *inter['zone'][2:]]]
            inter['zone'] = zone
            # Offset Target
            target = (qpoint - self.mouse_offsets['target']).toTuple()
            inter['target'] = target
            # Update data
            self.document.data['interactions'][self.selection.data] = inter
            self.document.edited.emit()
            self.selection.changed.emit(self)
        if self.toolmode.mode == ToolMode.CREATE and self.new_shape_data:
            qpoint = qpoint.toPoint()
            point = [int(v) for v in qpoint.toTuple()]
            self.new_shape_data[1] = point

    def mouseReleaseEvent(self, event):
        return_conditions = (
            self.toolmode.mode != ToolMode.CREATE or
            not self.new_shape_data)
        if return_conditions:
            return
        rect = start_end_to_rect_data(*self.new_shape_data)
        interaction = DEFAULT_INTERACTION.copy()
        interaction['zone'] = rect
        interaction['attraction'] = rect
        x = int(rect[0] + (rect[2] / 2))
        y = int(rect[1] + (rect[3] / 2))
        interaction['position'] = x, y
        self.document.data['interactions'].append(interaction)
        self.selection.tool = Selection.INTERACTION
        self.selection.data = len(self.document.data['interactions']) - 1
        self.new_shape_data = None
        self.document.edited.emit()
        self.selection.changed.emit(self)
        return super().mouseReleaseEvent(event)

    def create_new_shape(self, point):
        tl_bl = [point, [point[0] + 1, point[1] + 1]]
        self.new_shape_data = tl_bl

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

    def draw_shape(self, painter):
        if not self.new_shape_data:
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

