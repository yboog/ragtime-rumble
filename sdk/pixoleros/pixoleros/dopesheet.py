import json
import codecs
from PySide6 import QtWidgets, QtGui, QtCore
from pixoleros.template import ANIMATIONS


TOP_MARGIN = 15
LEFT_MARGIN = 10
SEPARATION_SPACE = 5
COLLAPSED_ROW_HEIGHT = 24
EXPANDED_ROW_HEIGHT = 50
FRAME_WIDTH = 10
FRAME_SPACING = 6
FRAME_VPADDING = 3
LEFT_COLUMN_WIDTH = 85
DROP_RECT_WIDTH = 2

FRAME_COLOR = (75, 100, 220)
FRAME_OUT_DATE_COLOR = (200, 100, 0)
FRAME_NOT_FOUND_COLOR = (200, 50, 50)


class DopeSheet(QtWidgets.QWidget):
    updated = QtCore.Signal()

    def __init__(self, model=None, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setMouseTracking(True)
        self.model = model
        self.hzoom = 1
        self.hovered_handler = None
        self.hovered_frame = None
        self.clicked_frame = None
        self.drop_rect = None
        self.handler = None
        self.dropping = False
        self.selection = Selection()

    def selected(self, animation, frame):
        for info in self.selection:
            if info == (animation, frame):
                return True
        return False

    def check_hovered_handler(self, event):
        for row in self.rows:
            for rect in row.handlers:
                if rect.contains(event.pos()):
                    return rect

    def check_hovered_frame(self, event):
        for row in self.rows:
            for rect in row.frame_rects:
                if rect.contains(event.pos()):
                    return rect

    def check_drop_rect(self, event):
        for row in self.rows:
            rect = row.drop_rect(event.pos())
            if rect:
                return rect

    def mouseMoveEvent(self, event):
        self.drop_rect = self.check_drop_rect(event)
        if self.handler:
            self.handler.mouse_move(event.pos())
            self.repaint()
            return

        if self.clicked_frame:
            row, frame = self.clicked_frame
            rect = row.frame_rects[frame]
            self.handler = DragAndDropFrameHandler(
                rect, self.model, row, frame)
            self.dropping = True
            mime = QtCore.QMimeData()
            frame = json.dumps(frame).encode()
            mime.setData('frame', QtCore.QByteArray(frame))
            mime.setData('animation', QtCore.QByteArray(row.animation))
            mime.setParent(self)
            drag = QtGui.QDrag(self)
            drag.setMimeData(mime)
            drag.exec_(QtCore.Qt.MoveAction)
            self.clicked_frame = None
            print('create mime data')
            return self.clear_hovered_items()

        self.hovered_handler = self.check_hovered_handler(event)
        self.hovered_frame = self.check_hovered_frame(event)
        self.repaint()

    def mousePressEvent(self, event):
        if event.button() != QtCore.Qt.LeftButton and self.hovered_handler:
            return
        for row in self.rows:
            for i, rect in enumerate(row.handlers):
                if rect.contains(event.pos()):
                    anchor = row.frame_rects[i].topLeft()
                    anchor.setX(anchor.x() - (FRAME_SPACING / 2))
                    self.handler = ExposureHandler(
                        self.model, anchor, row, i,
                        self.hzoom)
                    return self.clear_hovered_items()
            for i, rect in enumerate(row.frame_rects):
                if rect.contains(event.pos()):
                    self.clicked_frame = (row, i)

    def dragEnterEvent(self, event):
        if event.mimeData().parent() == self:
            return event.accept()

    def dragLeaveEvent(self, _):
        self.hovered_handler = None
        self.hovered_frame = None
        self.repaint()

    def dragMoveEvent(self, event):
        self.drop_rect = self.check_drop_rect(event)
        if self.handler:
            self.handler.mouse_move(event.pos())
            self.repaint()
            return
        self.hovered_handler = self.check_hovered_handler(event)
        self.hovered_frame = self.check_hovered_frame(event)
        self.repaint()

    def clear_hovered_items(self):
        self.hovered_handler = None
        self.hovered_frame = None

    def get_drop_infos(self, pos):
        for row in self.rows:
            index = row.drop_index(pos)
            if index is not None:
                return row.animation, index

    def dropEvent(self, event):
        self.dropping = False
        self.handler = None
        destination = self.get_drop_infos(event.pos())
        if not destination:
            return
        if event.mimeData().parent() == self:
            index = event.mimeData().data('frame').toInt()[0]
            data = bytes(event.mimeData().data('animation'))
            animation = codecs.decode(data)
            origin = (animation, index)
            selection = self.model.internal_move(
                self.selection.items or [origin], destination, action='move')
            self.selection.set(selection)
        self.repaint()

    def mouseReleaseEvent(self, event):
        if not self.clicked_frame:
            if not self.handler:
                self.selection.clear()
        else:
            row, frame = self.clicked_frame
            if not shift_pressed() and not ctrl_pressed():
                self.selection.set([(row.animation, frame)])
            elif not ctrl_pressed():
                self.selection.to((row.animation, frame))
            else:
                self.selection.add([(row.animation, frame)])
        self.handler = None
        self.hovered_handler = self.check_hovered_handler(event)
        self.hovered_frame = self.check_hovered_frame(event)
        self.clicked_frame = None
        if event.button() == QtCore.Qt.LeftButton:
            for row in self.rows:
                if row.text_rect.contains(event.pos()):
                    self.model.animation = row.animation
                    self.updated.emit()
                    self.repaint()
                    return
        self.repaint()

    def sizeHint(self):
        return QtCore.QSize(300, 300)

    def set_model(self, model):
        self.model = model
        self.repaint()

    def get_full_height(self):
        return (
            COLLAPSED_ROW_HEIGHT * len(ANIMATIONS) - 1) + EXPANDED_ROW_HEIGHT

    def get_full_width(self):
        width = (
            LEFT_COLUMN_WIDTH +
            SEPARATION_SPACE +
            (self.model.length * (FRAME_WIDTH * self.hzoom)))
        if width != self.width():
            self.setFixedWidth(width)
        return width

    def get_rows_rect(self):
        t = TOP_MARGIN
        left = LEFT_COLUMN_WIDTH
        width = self.get_full_width() - left
        rects = []
        for animation in ANIMATIONS:
            height = (
                COLLAPSED_ROW_HEIGHT
                if animation != self.model.animation
                else EXPANDED_ROW_HEIGHT)
            rects.append(QtCore.QRectF(left, t, width, height))
            t += height
        self.setFixedHeight(t)
        return rects

    def get_frame_rect(self):
        left = LEFT_COLUMN_WIDTH
        left = left + (FRAME_WIDTH * self.model.index)
        return QtCore.QRectF(left, 0, FRAME_WIDTH, self.rect().height())

    @property
    def rows(self):
        if self.model is None:
            return []
        return [
            Row(self.model, anim, rect, self.hzoom)
            for anim, rect in zip(ANIMATIONS, self.get_rows_rect())]

    def get_frame_color(self, animation, frame):
        image = self.model.image(animation, frame)
        if self.selected(animation, frame):
            return QtGui.QColor('white')
        if not image.reference_exists:
            return QtGui.QColor(*FRAME_NOT_FOUND_COLOR)
        if image.file_modified:
            return QtGui.QColor(*FRAME_OUT_DATE_COLOR)
        return QtGui.QColor(*FRAME_COLOR)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        if self.model is None:
            painter.setBrush(QtCore.Qt.darkGray)
            painter.drawRect(event.rect())
            return

        for i, row in enumerate(self.rows):
            if not i % 2:
                color = QtGui.QColor('black')
                color.setAlpha(25)
                painter.setPen(QtCore.Qt.NoPen)
                painter.setBrush(color)
                painter.drawRect(row.rect)
            if row.expanded:
                painter.setPen(QtCore.Qt.NoPen)
                color = QtGui.QColor(QtCore.Qt.lightGray)
                color.setAlpha(80)
                painter.setBrush(color)
                rect = QtCore.QRectF(row.rect)
                rect.setLeft(0)
                painter.drawRect(rect)
            painter.setBrush(QtGui.QBrush())
            painter.setPen(QtCore.Qt.white)
            flags = QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight
            font = QtGui.QFont()
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(row.text_rect, flags, row.animation)
            painter.setPen(QtCore.Qt.NoPen)
            for frame, rect in enumerate(row.frame_rects):
                color = self.get_frame_color(row.animation, frame)
                painter.setBrush(color)
                painter.drawRoundedRect(rect, 5, 5)
                if rect == self.hovered_frame and not self.hovered_handler:
                    painter.setBrush(QtGui.QColor(255, 255, 255, 50))
                    painter.drawRoundedRect(rect, 5, 5)

        if self.hovered_handler:
            painter.setPen(QtCore.Qt.NoPen)
            color = QtGui.QColor('white')
            color.setAlpha(75)
            painter.setBrush(color)
            painter.drawEllipse(self.hovered_handler.center(), 5, 5)

        if self.handler:
            painter.setPen(QtCore.Qt.NoPen)
            color = QtGui.QColor('white')
            painter.setBrush(color)
            painter.drawRoundedRect(self.handler.rect, 5, 5)

        if self.drop_rect and self.dropping:
            painter.setPen(QtCore.Qt.NoPen)
            color = QtGui.QColor('red')
            painter.setBrush(color)
            painter.drawRect(self.drop_rect)

        color = QtGui.QColor('yellow')
        color.setAlpha(75)
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(color)
        rect = self.get_frame_rect()
        painter.drawRect(rect)

        painter.end()


class Row:
    def __init__(self, model, animation, rect, hzoom):
        self.model = model
        self.animation = animation
        self.rect = rect
        self.hzoom = hzoom

    @property
    def expanded(self):
        return self.animation == self.model.animation

    @property
    def text_rect(self):
        return QtCore.QRectF(
            LEFT_MARGIN,
            self.rect.top(),
            self.rect.left() - LEFT_MARGIN,
            self.rect.height()).toRect()

    @property
    def handlers(self):
        left = self.rect.left()
        rects = []
        exposures = self.model.data['animations'][self.animation]['exposures']
        for exposure in exposures:
            width = (FRAME_WIDTH * self.hzoom * exposure)
            rect = QtCore.QRectF(
                left + width - (FRAME_SPACING / 2) - (FRAME_WIDTH * self.hzoom),
                self.rect.top() + (FRAME_VPADDING * 2),
                FRAME_SPACING + (FRAME_WIDTH * self.hzoom),
                self.rect.height() - (FRAME_VPADDING * 4))
            left += width
            rects.append(rect)
        return rects

    @property
    def frame_rects(self):
        left = self.rect.left()
        rects = []
        exposures = self.model.data['animations'][self.animation]['exposures']
        for exposure in exposures:
            width = (FRAME_WIDTH * self.hzoom * exposure)
            rect = QtCore.QRectF(
                (FRAME_SPACING / 2) + left,
                self.rect.top() + FRAME_VPADDING,
                width - FRAME_SPACING,
                self.rect.height() - (FRAME_VPADDING * 2))
            left += width
            rects.append(rect)
        return rects

    def drop_rect(self, pos):
        if not self.rect.contains(pos):
            return None
        exposures = self.model.data['animations'][self.animation]['exposures']
        left = self.rect.left()
        for exposure in exposures:
            width = (FRAME_WIDTH * self.hzoom * exposure)
            rect = QtCore.QRectF(
                left, self.rect.top(), width, self.rect.height())
            if rect.contains(pos):
                if pos.x() < rect.center().x():
                    return QtCore.QRectF(
                        rect.left() - (DROP_RECT_WIDTH / 2),
                        rect.top(), DROP_RECT_WIDTH, rect.height())
                return QtCore.QRectF(
                    rect.right() - (DROP_RECT_WIDTH / 2),
                    rect.top(), DROP_RECT_WIDTH, rect.height())
            left += width

    def drop_index(self, pos):
        if not self.rect.contains(pos):
            return None
        exposures = self.model.data['animations'][self.animation]['exposures']
        left = self.rect.left()
        for i, exposure in enumerate(exposures):
            width = (FRAME_WIDTH * self.hzoom * exposure)
            rect = QtCore.QRectF(
                left, self.rect.top(), width, self.rect.height())
            if rect.contains(pos):
                return i if pos.x() < rect.center().x() else i + 1
            left += width


class DragAndDropFrameHandler:
    def __init__(self, rect, model, row, frame):
        self.model = model
        self.row = row
        self.rect = rect

    def mouse_move(self, pos):
        ...


class ExposureHandler:
    def __init__(self, model, anchor, row, frame, zoom):
        self.model = model
        self.anchor = anchor
        self.row = row
        self.frame = frame
        self.zoom = zoom

    def mouse_move(self, pos):
        exposure = (pos.x() - self.anchor.x()) / (FRAME_WIDTH * self.zoom)
        exposure = max((1, round(exposure)))
        animation = self.model.data['animations'][self.row.animation]
        animation['exposures'][self.frame] = exposure

    @property
    def rect(self):
        return self.row.handlers[self.frame]


def shift_pressed():
    modifiers = QtWidgets.QApplication.keyboardModifiers()
    return modifiers == (modifiers | QtCore.Qt.ShiftModifier)


def ctrl_pressed():
    modifiers = QtWidgets.QApplication.keyboardModifiers()
    return modifiers == (modifiers | QtCore.Qt.ControlModifier)


class Selection:
    def __init__(self):
        self.items = []

    def clear(self):
        self.items = []

    def set(self, items):
        self.items = items

    def to(self, item):
        if not self.items:
            return self.set([item])
        items = self.items + [item]
        if len({item[0] for item in items}) != 1 or not self.items:
            self.set([item])
            return
        frames = [item[1], self.items[-1][1]]
        start, end = min(frames), max(frames)
        items = [(items[0][0], i) for i in range(start, end + 1)]
        self.add(items)

    def add(self, items):
        if not self.items:
            return self.set(items)

        if len({item[0] for item in items}) != 1:
            return

        if len({item[0] for item in items + self.items}) != 1:
            self.clear()
        additions = []
        for item in items:
            already = any(item == item2 for item2 in self.items)
            if not already:
                additions.append(item)
        self.items.extend(additions)

    def __iter__(self):
        return sorted(self.items, key=lambda x: x[1]).__iter__()
