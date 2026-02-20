import json
import codecs
from PySide6 import QtWidgets, QtGui, QtCore
from pixoleros.template import ANIMATIONS


TOP_MARGIN = 0
LEFT_MARGIN = 10
SEPARATION_SPACE = 5
COLLAPSED_ROW_HEIGHT = 24
EXPANDED_ROW_HEIGHT = 50
FRAME_WIDTH = 10
FRAME_SPACING = 6
FRAME_VPADDING = 3
LEFT_COLUMN_WIDTH = 95
DROP_RECT_WIDTH = 2
HEADER_HIGHT = 40

HEADER_COLOR = (25, 25, 25)
FRAME_COLOR = (75, 125, 145)


class DopeSheet(QtWidgets.QWidget):
    updated = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.document = None
        self.header = DopeSheetHeader()
        self.header.setFixedHeight(HEADER_HIGHT)
        self.header.updated.connect(self.updated.emit)
        self.exposures = DopeSheetExposures()
        self.exposures.updated.connect(self.updated.emit)

        self.header_scroll = QtWidgets.QScrollArea()
        self.header_scroll.setStyleSheet('border-width : 0')
        self.header_scroll.setFixedHeight(HEADER_HIGHT)
        self.header_scroll.setWidgetResizable(True)
        self.header_scroll.setWidget(self.header)
        policy = QtCore.Qt.ScrollBarAlwaysOff
        self.header_scroll.setHorizontalScrollBarPolicy(policy)
        self.header_scroll.setVerticalScrollBarPolicy(policy)
        scrollbar1 = self.header_scroll.horizontalScrollBar()
        self.exposures_scroll = QtWidgets.QScrollArea()
        self.exposures_scroll.setStyleSheet('border-width : 0')
        self.exposures_scroll.setWidgetResizable(True)
        self.exposures_scroll.setWidget(self.exposures)
        scrollbar2 = self.exposures_scroll.horizontalScrollBar()
        scrollbar2.valueChanged.connect(scrollbar1.setValue)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.header_scroll)
        layout.addWidget(self.exposures_scroll)

    def wheelEvent(self, event):
        if not self.document:
            return
        factor = .1 if event.angleDelta().y() > 0 else -.1
        offset = self.document.hzoom * abs(factor)
        offset = offset if factor < 0 else -offset
        zoom = self.document.hzoom + offset
        self.document.hzoom = max((0.33, min((10, zoom))))
        self.repaint()

    def set_document(self, document):
        self.document = document
        self.exposures.set_document(document)
        self.header.set_document(document)

    def repaint(self):
        super().repaint()

    @property
    def selection(self):
        return self.exposures.selection


class DopeSheetHeader(QtWidgets.QWidget):
    updated = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.document = None
        self.setFixedHeight(HEADER_HIGHT)

    def set_document(self, document):
        self.document = document
        self.repaint()

    def mousePressEvent(self, event):
        if event.button() != QtCore.Qt.LeftButton:
            return
        self.left_clicked = True
        self.set_index_from_point(event.pos())
        self.updated.emit()
        self.repaint()

    def mouseMoveEvent(self, event):
        if self.left_clicked:
            self.set_index_from_point(event.pos())
            self.updated.emit()
            self.repaint()

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.left_clicked = False

    def set_index_from_point(self, pos):
        left = LEFT_COLUMN_WIDTH
        if pos.x() < left:
            return
        i = 0
        width = dopesheet_width(self.document)
        offset = FRAME_WIDTH * self.document.hzoom
        while left < width:
            if left <= pos.x() <= left + offset:
                self.document.index = i
                return
            i += 1
            left += offset

    def get_frame_rect(self):
        left = LEFT_COLUMN_WIDTH
        left += (FRAME_WIDTH * self.document.index) * self.document.hzoom
        width = FRAME_WIDTH * self.document.hzoom
        return QtCore.QRectF(left, 0, width, self.rect().height())

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        if not self.document:
            painter.setBrush(QtGui.QColor(35, 35, 35))
            painter.setPen(QtCore.Qt.NoPen)
            painter.drawRect(self.rect())
            return
        painter.setBrush(QtGui.QColor(*HEADER_COLOR))
        pen = painter.pen()
        painter.setPen(QtCore.Qt.NoPen)
        painter.drawRect(self.rect())
        painter.setPen(pen)
        left = LEFT_COLUMN_WIDTH
        width = dopesheet_width(self.document)
        width = max((width, self.parent().width()))
        i = 0
        self.setFixedWidth(width)
        offset = FRAME_WIDTH * self.document.hzoom

        while left < width:
            top = HEADER_HIGHT / 2
            top += 0 if i % 5 == 0 else top / 3
            p1 = QtCore.QPoint(left, top)
            p2 = QtCore.QPoint(left, event.rect().height())
            painter.drawLine(p1, p2)
            if i % 5 == 0:
                painter.drawText(left - offset / 2, top / 1.4, str(i + 1))
            left += offset
            i += 1

        painter.setBrush(QtCore.Qt.yellow)
        painter.setPen(QtCore.Qt.NoPen)
        radius = (FRAME_WIDTH / 2) * 0.95
        x = self.get_frame_rect().center().x()
        y = HEADER_HIGHT * 0.75
        painter.drawEllipse(QtCore.QPoint(x, y), radius, radius)

        painter.end()


class DopeSheetExposures(QtWidgets.QWidget):
    updated = QtCore.Signal()

    def __init__(self, document=None, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setMouseTracking(True)
        self.document = document
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
            self.handler = DragAndDropFrameHandler(rect, self.document, row)
            self.dropping = True
            mime = QtCore.QMimeData()
            frame = json.dumps(frame).encode()
            mime.setData('frame', QtCore.QByteArray(frame))
            mime.setData('animation', QtCore.QByteArray(row.animation))
            mime.setData('internal_move', b'1')
            mime.setParent(self)
            drag = QtGui.QDrag(self)
            drag.setMimeData(mime)
            drag.exec_(QtCore.Qt.MoveAction)
            self.clicked_frame = None
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
                        self.document, anchor, row, i)
                    return self.clear_hovered_items()
            for i, rect in enumerate(row.frame_rects):
                if rect.contains(event.pos()):
                    self.clicked_frame = (row, i)

    def dragEnterEvent(self, event):
        # Cannot rely on event.mimeData().parent() because this call provoke a
        # crash in case of data coming from external parent (WIN11)
        if event.mimeData().data('internal_move').toInt()[0] == 1:
            return event.accept()

        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if not url.path().endswith('.png'):
                    return
            self.dropping = True
            self.handler = DragAndDropImportHandler()
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
        # Cannot rely on event.mimeData().parent() because this call provoke a
        # crash in case of data coming from external parent (WIN11)
        if event.mimeData().data('internal_move').toInt()[0] == 1:
            index = event.mimeData().data('frame').toInt()[0]
            data = bytes(event.mimeData().data('animation'))
            animation = codecs.decode(data)
            origin = (animation, index)
            action = 'copy' if ctrl_pressed else 'move'
            selection = self.document.internal_move(
                self.selection.items or [origin], destination, action=action)
            self.selection.set(selection)
        else:
            paths = [url.path() for url in event.mimeData().urls()]
            self.document.import_images_at(paths, destination)
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
                    self.document.animation = row.animation
                    self.updated.emit()
                    self.repaint()
                    return
        self.repaint()

    def sizeHint(self):
        return QtCore.QSize(300, 300)

    def set_document(self, document):
        self.document = document
        self.repaint()

    def get_full_height(self):
        return (
            COLLAPSED_ROW_HEIGHT * len(ANIMATIONS) - 1) + EXPANDED_ROW_HEIGHT

    def get_full_width(self):
        width = dopesheet_width(self.document)
        width = max((width, self.parent().rect().width()))
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
                if animation != self.document.animation
                else EXPANDED_ROW_HEIGHT)
            rects.append(QtCore.QRectF(left, t, width, height))
            t += height
        self.setFixedHeight(t)
        return rects

    def get_frame_rect(self):
        left = LEFT_COLUMN_WIDTH
        left += (FRAME_WIDTH * self.document.index) * self.document.hzoom
        width = FRAME_WIDTH * self.document.hzoom
        return QtCore.QRectF(left, 0, width, self.rect().height())

    @property
    def rows(self):
        if self.document is None:
            return []
        return [
            _Row(self.document, anim, rect, self.document.hzoom)
            for anim, rect in zip(ANIMATIONS, self.get_rows_rect())]

    def get_frame_color(self, animation, frame):
        if self.selected(animation, frame):
            return QtGui.QColor('white')
        return QtGui.QColor(*FRAME_COLOR)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        if self.document is None:
            painter.setBrush(QtCore.Qt.darkGray)
            painter.drawRect(self.rect())
            return

        painter.setPen(QtCore.Qt.NoPen)
        color = QtGui.QColor(*HEADER_COLOR)
        color.setAlpha(150)
        painter.setBrush(color)
        painter.drawRect(0, 0, LEFT_COLUMN_WIDTH, self.rect().height())

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

        if self.handler and self.handler.rect:
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


def dopesheet_width(document):
    return (
        LEFT_COLUMN_WIDTH +
        SEPARATION_SPACE +
        (document.length * (FRAME_WIDTH * document.hzoom)))


class _Row:
    def __init__(self, document, animation, rect, hzoom):
        self.document = document
        self.animation = animation
        self.rect = rect
        self.document.hzoom = hzoom

    @property
    def expanded(self):
        return self.animation == self.document.animation

    @property
    def text_rect(self):
        return QtCore.QRectF(
            LEFT_MARGIN,
            self.rect.top(),
            self.rect.left() - (LEFT_MARGIN * 2),
            self.rect.height()).toRect()

    @property
    def handlers(self):
        left = self.rect.left()
        rects = []
        exposures = self.document.animation_exposures(self.animation)
        for exposure in exposures:
            width = (FRAME_WIDTH * self.document.hzoom * exposure)
            hleft = (
                (left + width) -
                (FRAME_SPACING / 2) -
                (FRAME_WIDTH * self.document.hzoom))
            rect = QtCore.QRectF(
                hleft,
                self.rect.top() + (FRAME_VPADDING * 2),
                FRAME_SPACING + (FRAME_WIDTH * self.document.hzoom),
                self.rect.height() - (FRAME_VPADDING * 4))
            left += width
            rects.append(rect)
        return rects

    @property
    def frame_rects(self):
        left = self.rect.left()
        rects = []
        exposures = self.document.animation_exposures(self.animation)
        for exposure in exposures:
            width = (FRAME_WIDTH * self.document.hzoom * exposure)
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
        exposures = self.document.animation_exposures(self.animation)
        if not exposures:
            return QtCore.QRectF(
                0, self.rect.top(), DROP_RECT_WIDTH / 2, self.rect.height())
        left = self.rect.left()
        for exposure in exposures:
            width = (FRAME_WIDTH * self.document.hzoom * exposure)
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
        return QtCore.QRectF(
            rect.right() - (DROP_RECT_WIDTH / 2),
            rect.top(), DROP_RECT_WIDTH, rect.height())

    def drop_index(self, pos):
        if not self.rect.contains(pos):
            return None
        exposures = self.document.animation_exposures(self.animation)
        left = self.rect.left()
        for i, exposure in enumerate(exposures):
            width = (FRAME_WIDTH * self.document.hzoom * exposure)
            rect = QtCore.QRectF(
                left, self.rect.top(), width, self.rect.height())
            if rect.contains(pos):
                return i if pos.x() < rect.center().x() else i + 1
            left += width
        return len(exposures)


class DragAndDropFrameHandler:
    def __init__(self, rect, document, row):
        self.document = document
        self.row = row
        self.rect = rect

    def mouse_move(self, pos):
        ...


class DragAndDropImportHandler:
    def __init__(self):
        self.rect = None

    def mouse_move(self, pos):
        ...


class ExposureHandler:
    def __init__(self, document, anchor, row, frame):
        self.document = document
        self.anchor = anchor
        self.row = row
        self.frame = frame

    def mouse_move(self, pos):
        exposure = (pos.x() - self.anchor.x())
        exposure = exposure / (FRAME_WIDTH * self.document.hzoom)
        exposure = max((1, round(exposure)))
        animation = self.document.data['animations'][self.row.animation]
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
