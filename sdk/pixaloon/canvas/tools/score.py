from PySide6 import QtGui, QtCore
from pixaloon.canvas.tools.basetool import NavigationTool
from pixaloon.toolmode import ToolMode
from pixaloon.mathutils import distance


class ScoreTool(NavigationTool):

    def __init__(self, canvas=None):
        super().__init__(canvas)
        self.edited_element = None
        self.hovered_element = None
        self.mouse_offset = None

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
        action, player, offset = self.edited_element
        pos = self.viewportmapper.to_units_coords(event.pos() - offset)
        pos = pos.toTuple()
        # pos = (pos - offset).toTuple()

        match action:
            case 'overlay':
                self.document.data['score']['ol']['position'] = pos
            case 'life':
                p = f'player{player + 1}'
                self.document.data['score'][p]['life']['position'] = pos
            case 'bullet':
                p = f'player{player + 1}'
                self.document.data['score'][p]['bullet']['position'] = pos
            case 'coin':
                p = f'player{player + 1}'
                self.document.data['score'][p]['coins_position'] = pos

    def mouseReleaseEvent(self, event):
        self.edited_element = None
        return super().mouseReleaseEvent(event)

    def window_cursor_override(self):
        if self.toolmode.mode == ToolMode.CREATE:
            return QtCore.Qt.CursorShape.ForbiddenCursor

    def get_interaction(self, pos):
        for r in range(4):
            p = f'player{r + 1}'
            # P1 P2 P3
            image = self.document.scores[p]['life']
            position = self.document.data['score'][p]['life']['position']
            rect = QtCore.QRectF(QtCore.QPoint(*position), image.size())
            rect = self.viewportmapper.to_viewport_rect(rect)
            if rect.contains(pos):
                return 'life', r, pos - rect.topLeft().toPoint()
            # Bullet image
            image = self.document.scores[p]['bullet']
            position = self.document.data['score'][p]['bullet']['position']
            rect = QtCore.QRectF(QtCore.QPoint(*position), image.size())
            rect = self.viewportmapper.to_viewport_rect(rect)
            if rect.contains(pos):
                return 'bullet', r, pos - rect.topLeft().toPoint()
            # Coin
            image = self.document.scores['coin-stack']
            position = self.document.data['score'][p]['coins_position']
            rect = QtCore.QRectF(QtCore.QPoint(*position), image.size())
            rect = self.viewportmapper.to_viewport_rect(rect)
            if rect.contains(pos):
                return 'coin', r, pos - rect.topLeft().toPoint()
        image = self.document.scores['overlay']
        position = self.document.data['score']['ol']['position']
        rect = QtCore.QRectF(QtCore.QPoint(*position), image.size())
        rect = self.viewportmapper.to_viewport_rect(rect)
        if rect.contains(pos):
            return 'overlay', None, pos - rect.topLeft().toPoint()

    def get_interaction_rect(self, interaction):
        action, player, _ = interaction
        p = f'player{player + 1}' if player is not None else ''
        match action:
            case 'life':
                image = self.document.scores[p]['life']
                position = self.document.data['score'][p]['life']['position']
                rect = QtCore.QRectF(QtCore.QPoint(*position), image.size())
                return self.viewportmapper.to_viewport_rect(rect)
            case 'bullet':
                image = self.document.scores[p]['bullet']
                position = self.document.data['score'][p]['bullet']['position']
                rect = QtCore.QRectF(QtCore.QPoint(*position), image.size())
                return self.viewportmapper.to_viewport_rect(rect)
            case 'coin':
                image = self.document.scores['coin-stack']
                position = self.document.data['score'][p]['coins_position']
                rect = QtCore.QRectF(QtCore.QPoint(*position), image.size())
                return self.viewportmapper.to_viewport_rect(rect)
            case 'overlay':
                image = self.document.scores['overlay']
                position = self.document.data['score']['ol']['position']
                rect = QtCore.QRectF(QtCore.QPoint(*position), image.size())
                return self.viewportmapper.to_viewport_rect(rect)

    def get_interaction_label(self, interaction):
        action, player, _ = interaction
        if player is None:
            return 'Overlay'
        return f'{action.capitalize()} - Player {player + 1}'

    def draw(self, painter):
        interaction = (
            self.edited_element if self.edited_element
            else self.hovered_element)
        if not interaction:
            return
        rect = self.get_interaction_rect(interaction)
        painter.setBrush(QtCore.Qt.NoBrush)
        pen = QtGui.QPen(QtCore.Qt.white)
        pen.setWidth(3)
        painter.setPen(pen)
        painter.drawRect(rect)
        label = self.get_interaction_label(interaction)
        painter.drawText(rect.bottomLeft() + QtCore.QPoint(0, 15), label)