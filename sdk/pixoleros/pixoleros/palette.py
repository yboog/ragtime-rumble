from PySide6 import QtWidgets, QtGui, QtCore
from pixoleros.colorwheel import ColorWheel

ROW_HEIGHT = 22
CELL_WIDTH = 22
VERTICAL_HEADER_WIDTH = 120
PALETTE_NAME_LEFT_MARGIN = 5
CELL_MARGIN = 2

PALETTE_MARGINS = 12
COLOR_RECT_SIZE = 22
COLOR_RECT_SPACING = 5


def grow_rect(rect, value):
    if not rect:
        return None
    return QtCore.QRectF(
        rect.left() - value,
        rect.top() - value,
        rect.width() + (value * 2),
        rect.height() + (value * 2))


class Palette(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.document = None
        self.palette_table = PaletteDisplayTable()
        self.palette = PaletteColors()
        self.palette_table.updated.connect(self.palette.update_size)
        self.color_wheel = ColorWheel()
        splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        splitter.setContentsMargins(0, 0, 0, 0)
        splitter.addWidget(self.palette_table)
        splitter.addWidget(self.palette)
        splitter.addWidget(self.color_wheel)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(splitter)

    def set_document(self, document):
        self.document = document
        self.palette_table.set_document(document)
        self.palette.set_document(document)
        self.repaint()


class PaletteListToolBar(QtWidgets.QToolBar):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.addAction('+')
        self.addAction('-')


class PaletteDisplayTable(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.rows = PaletteDisplayRow()
        self.rows.resized.connect(self.row_resized)
        self.updated = self.rows.updated
        self.set_document = self.rows.set_document
        self.scroll = QtWidgets.QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self.rows)
        self.scroll.sizeHint = lambda: QtCore.QSize(300, 400)
        self.scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.scroll)
        layout.addWidget(PaletteListToolBar())

    def row_resized(self, size):
        width = size.width() + self.scroll.verticalScrollBar().width() + 2
        self.scroll.setMinimumWidth(width)


class PaletteDisplayRow(QtWidgets.QWidget):
    resized = QtCore.Signal(QtCore.QSize)
    updated = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.document = None

    def mouseReleaseEvent(self, event):
        if event.button() != QtCore.Qt.LeftButton:
            return
        for row in self.rows:
            palette = self.document.palettes[row.index]['name']
            for i, rect in enumerate(row.palettes_rects):
                if rect.contains(event.pos()):
                    self.document.display_palettes[palette] = i
                    self.repaint()
                    self.updated.emit()
                    return
            if row.rect(self.width()).contains(event.pos()):
                self.document.selected_palette = palette
                self.repaint()
                self.updated.emit()
                return

    @property
    def rows(self):
        return [
            _Row(self.document, index=i)
            for i in range(len(self.document.palettes))]

    def paintEvent(self, event):
        if self.document is None:
            return

        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        color = QtGui.QColor(QtCore.Qt.black)
        color.setAlpha(20)
        painter.setBrush(color)
        painter.setPen(QtCore.Qt.NoPen)
        painter.drawRect(0, 0, VERTICAL_HEADER_WIDTH, event.rect().height())

        for row in self.rows:
            top = ROW_HEIGHT * row.index
            palette = self.document.palettes[row.index]
            if palette['name'] == self.document.selected_palette:
                color = QtGui.QColor(QtCore.Qt.yellow)
                color.setAlpha(20)
                painter.setPen(QtCore.Qt.NoPen)
                painter.setBrush(color)
                rect = QtCore.QRect(0, top, event.rect().width(), ROW_HEIGHT)
                painter.drawRect(rect)
            elif row.index % 2 == 0:
                color = QtGui.QColor(QtCore.Qt.black)
                color.setAlpha(20)
                painter.setPen(QtCore.Qt.NoPen)
                painter.setBrush(color)
                rect = QtCore.QRect(0, top, event.rect().width(), ROW_HEIGHT)
                painter.drawRect(rect)
            painter.setPen(QtGui.QColor(200, 200, 200))
            y = top - (ROW_HEIGHT / 4)
            painter.drawText(PALETTE_NAME_LEFT_MARGIN, y, palette['name'])
            painter.setBrush(QtCore.Qt.NoBrush)

            for i, rect in enumerate(row.palettes_rects):
                painter.setPen(QtGui.QColor(25, 25, 25))
                painter.setBrush(QtCore.Qt.NoBrush)
                painter.drawRoundedRect(grow_rect(rect, -CELL_MARGIN), 3, 3)
                if self.document.get_display_palette(palette['name']) == i:
                    painter.setPen(QtCore.Qt.NoPen)
                    painter.setBrush(QtGui.QColor(25, 25, 25))
                    painter.drawEllipse(grow_rect(rect, -CELL_MARGIN * 3))

    def update_size(self):
        if not self.document:
            self.resize(VERTICAL_HEADER_WIDTH, 50)
            self.repaint()
            return
        palettes = self.document.palettes
        cell_number = max(len(p['palettes']) for p in palettes)
        width = VERTICAL_HEADER_WIDTH + (CELL_WIDTH * cell_number)
        height = ROW_HEIGHT * (len(palettes) - 1)
        self.setMinimumWidth(width)
        self.setFixedHeight(height)
        self.resized.emit(QtCore.QSize(width, height))
        self.repaint()

    def set_document(self, document):
        self.document = document
        self.update_size()
        self.repaint()


class _Row:
    def __init__(self, document, index):
        self.document = document
        self.index = index

    def rect(self, width):
        return QtCore.QRect(0, self.top, width, ROW_HEIGHT)

    @property
    def top(self):
        return ROW_HEIGHT * self.index

    @property
    def palettes_rects(self):
        return [
            QtCore.QRect(
                VERTICAL_HEADER_WIDTH + (CELL_WIDTH * i),
                self.top,
                CELL_WIDTH,
                CELL_WIDTH)
            for i in range(
                len(self.document.palettes[self.index]['palettes']))]


class PaletteColors(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.document = None

    @property
    def palette(self):
        if self.document is None:
            return None
        return next((
            p for p in self.document.palettes
            if p['name'] == self.document.selected_palette), None)

    def set_document(self, document):
        self.document = document
        self.update_size()
        self.repaint()

    def update_size(self):
        if not self.palette:
            return
        self.setMinimumHeight(self.column(0).height)
        column_count = len(self.palette['palettes']) + 3
        width = PALETTE_MARGINS * 2
        width += (COLOR_RECT_SIZE + COLOR_RECT_SPACING) * column_count
        self.setMinimumWidth(width)
        self.repaint()

    def column(self, index):
        left = PALETTE_MARGINS
        left += (COLOR_RECT_SIZE + COLOR_RECT_SPACING) * index
        return _Column(self.document, left)

    def paintEvent(self, event):
        palette = self.palette
        if self.document is None or palette is None:
            return
        painter = QtGui.QPainter(self)
        column = self.column(0)
        pen = QtGui.QPen(QtGui.QColor(35, 35, 35))
        pen.setWidth(2)
        painter.setPen(pen)
        for color, rect in zip(palette['origins'], column.rects):
            painter.setBrush(QtGui.QColor(*color))
            painter.drawRoundedRect(rect, 3, 3)
        for rect in self.column(1).rects:
            painter.drawText(rect.center(), '-')
        for rect in self.column(2).rects:
            painter.drawText(rect.center(), '>')
        for i, overrive in enumerate(palette['palettes']):
            column = self.column(i + 3)
            if i == self.document.get_display_palette(palette['name']):
                color = QtGui.QColor(QtCore.Qt.yellow)
                color.setAlpha(25)
                painter.setBrush(color)
                painter.setPen(QtCore.Qt.NoPen)
                rect = column.rect
                rect.setHeight(event.rect().height())
                painter.drawRect(rect)
            pen = QtGui.QPen(QtGui.QColor(35, 35, 35))
            pen.setWidth(2)
            painter.setPen(pen)
            for color, rect in zip(overrive, column.rects):
                painter.setBrush(QtGui.QColor(*color))
                painter.drawRoundedRect(rect, 3, 3)


class _Column:
    def __init__(self, document, left):
        self.document = document
        self.left = left

    @property
    def height(self):
        palette = self.palette
        if not palette:
            return 150
        height = PALETTE_MARGINS * 2
        height += COLOR_RECT_SIZE * len(palette['origins'])
        height += COLOR_RECT_SPACING * len(palette['origins'])
        return height

    @property
    def rect(self):
        return QtCore.QRectF(
            self.left - (COLOR_RECT_SPACING / 2), 0,
            COLOR_RECT_SIZE + COLOR_RECT_SPACING, self.height)

    @property
    def palette(self):
        if self.document is None:
            return
        return next((
            p for p in self.document.palettes
            if p['name'] == self.document.selected_palette), None)

    @property
    def rects(self):
        palette = self.palette
        if not palette:
            return []

        rects = []
        top = PALETTE_MARGINS
        for _ in palette['origins']:
            rect = QtCore.QRect(
                self.left, top, COLOR_RECT_SIZE, COLOR_RECT_SIZE)
            rects.append(rect)
            top += COLOR_RECT_SIZE + COLOR_RECT_SPACING
        return rects
