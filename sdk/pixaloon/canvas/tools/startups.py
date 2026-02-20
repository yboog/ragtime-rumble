from PySide6 import QtGui, QtCore
from pixaloon.selection import Selection
from pixaloon.canvas.tools.basetool import NavigationTool
from pixaloon.toolmode import ToolMode
from pixaloon.mathutils import distance


class StartupTool(NavigationTool):

    def __init__(self, canvas=None):
        super().__init__(canvas)
        self.edited_element = None
        self.hovered_element = None

    def mousePressEvent(self, event):
        if self.toolmode.mode != ToolMode.EDIT:
            return
        if self.edited_element is not None:
            return
        if event.button() != QtCore.Qt.LeftButton:
            return
        self.edited_element = self.get_interaction(event.pos())

    def mouseMoveEvent(self, event):
        if super().mouseMoveEvent(event):
            return
        if self.toolmode.mode != ToolMode.EDIT:
            return
        if not self.edited_element:
            self.hovered_element = self.get_interaction(event.pos())
            return False
        action, data = self.edited_element
        pos = self.viewportmapper.to_units_coords(event.pos()).toPoint()
        pos = pos.toTuple()
        startups = self.document.data['startups']
        match action:
            case 'unassigned':
                startups['unassigned'][data] = pos
                return
            case 'assigned':
                i, j = data
                startups['groups'][i]['assigned'][j] = pos
            case 'popspot':
                i, direction = data
                startups['groups'][i]['popspots'][direction] = pos
        return super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.edited_element = None
        return super().mouseReleaseEvent(event)

    def get_interaction(self, position):
        qpoint = self.document.viewportmapper.to_units_coords(position)
        qpoint = qpoint.toPoint()
        cursor_point = qpoint.toTuple()
        unassigned = self.document.data['startups']['unassigned']
        for i, point in enumerate(unassigned):
            if distance(cursor_point, point) < 3:
                return 'unassigned', i
        for i, group in enumerate(self.document.data['startups']['groups']):
            for j, assignation_spot in enumerate(group['assigned']):
                if distance(cursor_point, assignation_spot) < 3:
                    return 'assigned', (i, j)
            for direction, spot in group['popspots'].items():
                if distance(cursor_point, spot) < 3:
                    return 'popspot', (i, direction)

    def window_cursor_override(self):
        if self.toolmode.mode == ToolMode.CREATE:
            return QtCore.Qt.CursorShape.ForbiddenCursor

    def get_interaction_position(self, interaction):
        action, data = interaction
        startups = self.document.data['startups']
        match action:
            case 'unassigned':
                return startups['unassigned'][data]
            case 'assigned':
                i, j = data
                return startups['groups'][i]['assigned'][j]
            case 'popspot':
                i, direction = data
                return startups['groups'][i]['popspots'][direction]

    def draw(self, painter):
        interaction = (
            self.edited_element if self.edited_element
            else self.hovered_element)
        if not interaction:
            return
        position = self.get_interaction_position(interaction)
        p = self.viewportmapper.to_viewport_coords(QtCore.QPointF(*position))
        painter.setPen(QtCore.Qt.NoPen)
        color = QtGui.QColor(QtCore.Qt.yellow)
        color.setAlpha(150)
        painter.setBrush(color)
        painter.drawEllipse(p, 7, 7)
