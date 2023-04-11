from PySide6 import QtWidgets, QtGui, QtCore
from pixoleros.colorwheel import ColorWheel
from pixoleros.imgutils import list_rgb_colors


HEADER_HEIGHT = 22
CELL_WIDTH = 22
HEADER_TEXT_WIDTH = 120
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


class Palettes(QtWidgets.QWidget):
    palette_changed = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.document = None
        self.palettetable = PaletteTable()
        self.palettetable.display_changed.connect(self.send_update_signal)
        self.palettetable.color_selected.connect(self.color_index_changed)
        self.colorwheel = ColorWheel()
        self.colorwheel.currentColorChanged.connect(self.set_color)
        self.colorwheel.currentColorChanged.connect(self.send_update_signal)

        scroll = QtWidgets.QScrollArea()
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.palettetable)

        splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        splitter.addWidget(scroll)
        splitter.addWidget(self.colorwheel)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(splitter)

    def send_update_signal(self, *_):
        self.palette_changed.emit()

    def color_index_changed(self, rgb):
        if rgb is not None:
            self.colorwheel.set_rgb255(*rgb)
            return

        name, i, j = self.document.editing_color_index
        for palette in self.document.palettes:
            if palette['name'] != name:
                continue
            color = palette['palettes'][i][j]
            self.colorwheel.set_rgb255(*color)
            return

    def set_color(self, rgb):
        name, i, j = self.document.editing_color_index
        for palette in self.document.palettes:
            if palette['name'] != name:
                continue
            rgb = [int(round(n * 255)) for n in rgb]
            palette['palettes'][i][j] = rgb
            self.palettetable.repaint()
            return

    def sizeHint(self):
        return QtCore.QSize(300, 600)

    def set_document(self, document):
        self.document = document
        self.palettetable.set_document(document)
        self.repaint()


class PaletteTable(QtWidgets.QWidget):
    color_selected = QtCore.Signal(object)
    display_changed = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.document = None

    def sizeHint(self):
        return QtCore.QSize(300, 600)

    def set_document(self, document):
        self.document = document
        self.repaint()

    def draw_header(self, painter, header, extended):
        brush = painter.brush()
        pen = painter.pen()
        painter.setBrush(QtGui.QColor(0, 0, 0, 150))
        painter.setPen(QtCore.Qt.NoPen)
        painter.drawRect(header.rect(self.width()))
        painter.setBrush(brush)
        painter.setPen(pen)
        f = QtCore.Qt.AlignVCenter
        painter.drawText(header.text_rect, f, f'   {header.palette_name}')
        rect = grow_rect(header.expand_rect, -4)
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(pen.color())
        painter.drawRoundedRect(rect, 2, 2)
        font = QtGui.QFont()
        font.setBold(True)
        painter.setFont(font)
        f = QtCore.Qt.AlignCenter
        painter.setBrush(QtCore.Qt.NoBrush)
        painter.setPen(QtGui.QColor(25, 25, 25))
        painter.drawText(rect, f, '-' if extended else '+')
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(pen.color())
        rect = header.delete_rect(self.width())
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.drawEllipse(rect.center(), 8, 8)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, False)
        painter.setBrush(QtCore.Qt.NoBrush)
        painter.setPen(QtGui.QColor(25, 25, 25))
        painter.drawText(rect, f, 'X')
        painter.setFont(QtGui.QFont())
        rects = header.variants_rects
        painter.setPen(pen)
        painter.setBrush(brush)
        for i, rect in enumerate(rects):
            painter.drawRect(grow_rect(rect, -2))
            v = self.document.displayed_variants.get(header.palette_name, 0)
            if i == v:
                brush = painter.brush()
                color = painter.pen().color()
                painter.setBrush(color)
                painter.drawEllipse(rect.center(), 6, 6)
                painter.setBrush(brush)

        painter.drawText(rects[-1], QtCore.Qt.AlignCenter, '+')

    @property
    def rows(self):
        if not self.document:
            return
        top = 0
        for i, palette in enumerate(self.document.palettes):
            expanded = palette['name'] in self.document.displayed_palettes
            header = _Header(self.document, palette['name'], i, top)
            top += HEADER_HEIGHT
            if not expanded:
                yield header, None, top
                continue
            colors = _Colors(self.document, palette['name'], i, top)
            top += colors.height
            yield header, colors, top

    def mouseReleaseEvent(self, event):
        bottom = 0
        for header, colors, bottom in self.rows:
            palette = self.document.palettes[header.index]
            if colors:
                column = colors.column(0)
                if len(column) > 1:
                    for i, rect in enumerate(column):
                        if rect.contains(event.pos()):
                            self.document.editing_color_index = ('', -1, -1)
                            c = self.document.palettes[colors.index]['origins']
                            if i < len(c):
                                self.color_selected.emit(c[i])
                                self.repaint()
                                return
                # Add Origins color.
                if column[-1].contains(event.pos()):
                    if not self.document.current_image:
                        return
                    rgbs = list_rgb_colors(self.document.current_image.image)
                    dialog = ColorSelection(rgbs)
                    point = self.mapToGlobal(column[-1].topLeft())
                    result = dialog.exec(point)
                    if result == QtWidgets.QDialog.Accepted:
                        self.document.add_palette_origins(
                            colors.index, dialog.color)
                        self.repaint()
                    return
                i = 0
                for i in range(len(palette['palettes'])):
                    column = colors.column(i + 1)
                    for j, rect in enumerate(column[:-1]):
                        if rect.contains(event.pos()):
                            infos = header.palette_name, i, j
                            self.document.editing_color_index = infos
                            self.repaint()
                            self.color_selected.emit(None)
                            return
                    if column[-1].contains(event.pos()):
                        del palette['palettes'][i]
                        infos = palette['name'], i
                        infos2 = self.document.editing_color_index[:2]
                        if infos2 == infos:
                            self.document.editing_color_index = ('', -1, -1)
                        self.display_changed.emit()
                        self.repaint()
                        return
                column = colors.column(i + 2)
                for j, rect in enumerate(column[:-1]):
                    if rect.contains(event.pos()):
                        infos = self.document.editing_color_index[0]
                        if infos == palette['name']:
                            self.document.editing_color_index = ('', -1, -1)
                        del palette['origins'][j]
                        for p in palette['palettes']:
                            del p[j]
                        self.display_changed.emit()
                        self.repaint()
                        return

            if not header.rect(self.width()).contains(event.pos()):
                continue

            if header.text_rect.contains(event.pos()):
                self.rename(header)
                return

            if header.delete_rect(self.width()).contains(event.pos()):
                del self.document.palettes[header.index]
                if palette['name'] == self.document.editing_color_index[0]:
                    self.document.editing_color_index = ('', -1, -1)
                self.repaint()
                return

            if header.expand_rect.contains(event.pos()):
                self.document.switch_palette(header.palette_name)
                self.repaint()
                return

            else:
                rects = header.variants_rects
                for i, rect in enumerate(rects[:-1]):
                    if rect.contains(event.pos()):
                        self.document.displayed_variants[header.palette_name] = i
                        self.display_changed.emit()
                        self.repaint()
                        return
                if rects[-1].contains(event.pos()):
                    palette['palettes'].append(palette['origins'][:])
                    self.repaint()
                    return
        rect = self.plus_rect(bottom)
        if rect.contains(event.pos()):
            self.document.add_palette()
            self.repaint()

    def rename(self, header):
        dialog = RenameDialog(header, self)
        rect = header.text_rect
        point = self.mapToGlobal(rect.topLeft())
        dialog.exec_(point, rect.size())

    def draw_colors(self, painter, colors):
        palette = self.document.palettes[colors.index]
        pen = painter.pen()
        painter.setPen(QtCore.Qt.NoPen)
        selected = self.document.editing_color_index
        i = 0
        for i, rgbs in enumerate(palette['palettes']):
            column = colors.column(i + 1)
            font = QtGui.QFont()
            font.setBold(True)
            painter.setFont(font)
            for j, (rect, rgb) in enumerate(zip(column[:-1], rgbs)):
                if selected == (colors.palette_name, i, j):
                    painter.setPen(QtCore.Qt.yellow)
                else:
                    painter.setPen(QtCore.Qt.NoPen)
                painter.setBrush(QtGui.QColor(*rgb))
                painter.drawRect(grow_rect(rect, -2))
            painter.setBrush(QtGui.QColor(255, 255, 255, 20))
            painter.setPen(QtCore.Qt.NoPen)
            painter.drawRect(grow_rect(column[-1], -2))
            painter.setPen(pen)
            painter.drawText(column[-1], QtCore.Qt.AlignCenter, '-')

        column = colors.column(i + 2)
        for rect in column[:-1]:
            painter.setBrush(QtGui.QColor(255, 255, 255, 20))
            painter.setPen(QtCore.Qt.NoPen)
            painter.drawRect(grow_rect(rect, -2))
            painter.setPen(pen)
            painter.drawText(rect, QtCore.Qt.AlignCenter, '-')

        painter.setFont(QtGui.QFont())
        column = colors.column(0)
        painter.setPen(QtCore.Qt.NoPen)
        for rect, rgb in zip(column[:-1], palette['origins']):
            painter.setBrush(QtGui.QColor(*rgb))
            painter.drawRect(grow_rect(rect, -2))
        painter.setBrush(QtCore.Qt.NoBrush)
        painter.setPen(pen)
        painter.drawText(grow_rect(column[-1], -2), QtCore.Qt.AlignCenter, '+')
        painter.drawRect(grow_rect(column[-1], -2))

    def plus_rect(self, top):
        top = max((
            top + CELL_MARGIN * 2,
            self.parent().rect().bottom() - HEADER_HEIGHT * 1.5))
        return QtCore.QRect(0, top, self.width(), HEADER_HEIGHT * 1.5)

    def paintEvent(self, _):
        if not self.document:
            return
        painter = QtGui.QPainter(self)
        pen = painter.pen()
        brush = painter.brush()
        painter.setPen(QtCore.Qt.NoPen)
        color = QtGui.QColor('black')
        color.setAlpha(100)
        painter.setBrush(color)
        painter.drawRect(
            0, 0,
            HEADER_HEIGHT + HEADER_TEXT_WIDTH + CELL_WIDTH + (CELL_MARGIN / 2),
            self.rect().height())
        painter.setPen(pen)
        painter.setBrush(brush)
        bottom = 0
        for header, colors, bottom in self.rows:
            self.draw_header(painter, header, bool(colors))
            if not colors:
                continue
            self.draw_colors(painter, colors)
        rect = self.plus_rect(bottom)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setBrush(QtGui.QColor(15, 15, 15))
        painter.setPen(QtCore.Qt.NoPen)
        painter.drawRoundedRect(grow_rect(rect, -4), 4, 4)
        painter.setBrush(QtCore.Qt.NoBrush)
        painter.setPen(pen)
        font = QtGui.QFont()
        font.setBold(True)
        font.setPixelSize(25)
        painter.setFont(font)
        painter.drawText(rect, QtCore.Qt.AlignCenter, '+')
        painter.end()
        self.setFixedHeight(rect.bottom())
        return


class _Header:
    def __init__(self, document, palette_name, index, top):
        self.document = document
        self.palette_name = palette_name
        self.top = top
        self.index = index

    def rect(self, width):
        return QtCore.QRect(0, self.top, width, HEADER_HEIGHT)

    @property
    def variants_rects(self):
        return [
            QtCore.QRect(
                (
                    HEADER_HEIGHT + HEADER_TEXT_WIDTH +
                    ((CELL_WIDTH + CELL_MARGIN) * i)
                ),
                self.top,
                CELL_WIDTH,
                CELL_WIDTH)
            for i in range(
                len(self.document.palettes[self.index]['palettes']) + 2)]

    @property
    def expand_rect(self):
        return QtCore.QRect(0, self.top, HEADER_HEIGHT, HEADER_HEIGHT)

    def delete_rect(self, width):
        return QtCore.QRect(
            width - HEADER_HEIGHT, self.top, HEADER_HEIGHT, HEADER_HEIGHT)

    @property
    def text_rect(self):
        return QtCore.QRect(
            HEADER_HEIGHT, self.top, HEADER_TEXT_WIDTH, HEADER_HEIGHT)


class _Colors:
    def __init__(self, document, palette_name, index, top):
        self.document = document
        self.palette_name = palette_name
        self.index = index
        self.top = top

    def column(self, i):
        left = HEADER_HEIGHT + HEADER_TEXT_WIDTH
        left += i * (CELL_WIDTH + CELL_MARGIN)
        top = self.top
        cells = []
        it = len(self.document.palettes[self.index]['origins']) + 1
        for _ in range(it):
            cells.append(QtCore.QRect(left, top, CELL_WIDTH, CELL_WIDTH))
            top += CELL_WIDTH + CELL_MARGIN
        return cells

    @property
    def height(self):
        return self.column(0)[-1].bottom() - self.top + (CELL_MARGIN * 2)


class RenameDialog(QtWidgets.QWidget):
    def __init__(self, header, parent=None):
        super().__init__(parent)
        self.header = header
        self.setWindowFlag(QtCore.Qt.FramelessWindowHint)
        self.setWindowFlag(QtCore.Qt.Popup)
        self.text = QtWidgets.QLineEdit(header.palette_name)
        self.text.focusOutEvent = self.focusOutEvent
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.text)
        self.text.returnPressed.connect(self.close)

    def closeEvent(self, _):
        text = self.text.text()
        if self.header.palette_name == text:
            return
        self.header.document.rename_palette(self.header.index, text)
        self.parent().repaint()

    def exec_(self, point, size):
        self.move(point)
        self.resize(size)
        self.show()
        self.text.setFocus(QtCore.Qt.MouseFocusReason)
        self.text.selectAll()


class ColorSelection(QtWidgets.QDialog):
    COLORSIZE = 30
    COLCOUNT = 5

    def __init__(self, colors, parent=None):
        super().__init__(parent=parent)
        self.setMouseTracking(True)
        self.colors = colors
        self.color = None
        self.setModal(True)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        width = self.COLORSIZE * self.COLCOUNT
        height = self.COLORSIZE * (len(self.colors) // self.COLCOUNT)
        self.resize(width, height)

    def mouseMoveEvent(self, _):
        self.repaint()

    def exec(self, point):
        self.move(point)
        return super().exec()

    def mouseReleaseEvent(self, event):
        if event.button() != QtCore.Qt.LeftButton:
            return
        row = event.pos().y() // self.COLORSIZE
        col = event.pos().x() // self.COLORSIZE
        index = (row * self.COLCOUNT) + col
        try:
            self.color = self.colors[index]
            self.accept()
        except IndexError:
            ...

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        left, top = 0, 0
        pen = QtGui.QPen()
        pen.setWidth(3)
        for color in self.colors:
            if left >= self.rect().width():
                left = 0
                top += self.COLORSIZE
            rect = QtCore.QRect(left, top, self.COLORSIZE, self.COLORSIZE)
            if color == self.color:
                pencolor = QtCore.Qt.red
            elif rect.contains(self.mapFromGlobal(QtGui.QCursor.pos())):
                pencolor = QtCore.Qt.white
            else:
                pencolor = QtCore.Qt.transparent
            pen.setColor(pencolor)
            painter.setPen(pen)
            painter.setBrush(QtGui.QColor(*color))
            painter.drawRect(rect)
            left += self.COLORSIZE
