import os
import msgpack
from PIL import ImageQt
from PySide6 import QtWidgets, QtGui, QtCore
from pixoleros.dopesheet import DopeSheet
from pixoleros.io import get_icon, serialize_document
from pixoleros.imgutils import switch_colors
from pixoleros.library import LibraryTableView
from pixoleros.model import Document
from pixoleros.navigator import Navigator
from pixoleros.palette import Palettes
from pixoleros.viewport import ViewportMapper, zoom


def set_shortcut(keysequence, parent, method):
    shortcut = QtGui.QShortcut(QtGui.QKeySequence(keysequence), parent)
    shortcut.activated.connect(method)


class Pixoleros(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Pixoleros')
        self.mdi = QtWidgets.QMdiArea()
        self.setCentralWidget(self.mdi)

        self.mdi.subWindowActivated.connect(self.sub_window_changed)
        self.mdi.setViewMode(QtWidgets.QMdiArea.TabbedView)
        self.mdi.setTabsClosable(True)

        self.toolbar = MainToolbar()
        self.toolbar.new.triggered.connect(self.new)
        self.toolbar.open.triggered.connect(self.open)
        self.toolbar.save.triggered.connect(self.save)

        areas = (
            QtCore.Qt.TopDockWidgetArea |
            QtCore.Qt.BottomDockWidgetArea |
            QtCore.Qt.LeftDockWidgetArea |
            QtCore.Qt.RightDockWidgetArea)

        self.library = LibraryTableView()
        self.library_dock = QtWidgets.QDockWidget('Library', self)
        self.library_dock.setAllowedAreas(areas)
        self.library_dock.setWidget(self.library)

        self.parameters = CharacterParameters()
        title = 'Character parameters'
        self.parameters_dock = QtWidgets.QDockWidget(title, self)
        self.parameters_dock.setAllowedAreas(areas)
        self.parameters_dock.setWidget(self.parameters)

        self.dopesheet = DopeSheet()
        self.dopesheet.updated.connect(self.update)
        self.dopesheet_dock = QtWidgets.QDockWidget('Dopesheet', self)
        self.dopesheet_dock.setAllowedAreas(areas)
        self.dopesheet_dock.setWidget(self.dopesheet)

        self.palette = Palettes()
        self.palette.palette_changed.connect(self.repaint_canvas)
        self.palette_dock = QtWidgets.QDockWidget('Palette', self)
        self.palette_dock.setAllowedAreas(areas)
        self.palette_dock.setWidget(self.palette)

        self.addDockWidget(
            QtCore.Qt.BottomDockWidgetArea, self.dopesheet_dock)
        self.addDockWidget(
            QtCore.Qt.LeftDockWidgetArea, self.parameters_dock)
        self.addDockWidget(
            QtCore.Qt.LeftDockWidgetArea, self.palette_dock)
        self.addDockWidget(
            QtCore.Qt.LeftDockWidgetArea, self.library_dock)
        self.tabifyDockWidget(self.palette_dock, self.library_dock)

        self.setCorner(
            QtCore.Qt.BottomLeftCorner,
            QtCore.Qt.LeftDockWidgetArea)

        self.setCorner(
            QtCore.Qt.BottomRightCorner,
            QtCore.Qt.RightDockWidgetArea)

        self.addToolBar(QtCore.Qt.TopToolBarArea, self.toolbar)

        set_shortcut('CTRL+N', self, self.new)
        set_shortcut('CTRL+O', self, self.open)
        set_shortcut('CTRL+S', self, self.save)
        set_shortcut('RIGHT', self, self.next)
        set_shortcut('LEFT', self, self.prev)
        set_shortcut('F', self, self.focus)
        set_shortcut('DEL', self, self.delete)

    def save(self):
        if not self.current_document:
            return
        document = self.current_document
        if document.library:
            path = list(document.library.values())[0].path
            directory = os.path.dirname(os.path.dirname(path))
        else:
            directory = os.path.expanduser('~')
        path, result = QtWidgets.QFileDialog.getSaveFileName(
            self, 'Save as', directory, 'Pixoleros (*.pixo)')
        if not result:
            return
        with open(path, 'wb') as f:
            msgpack.dump(serialize_document(self.current_document), f)

    def delete(self):
        if not (document := self.current_document):
            return
        self.library.model().layoutAboutToBeChanged.emit()
        document.delete_frames(list(self.dopesheet.selection))
        self.library.model().layoutChanged.emit()
        self.repaint_canvas()
        self.dopesheet.repaint()

    @property
    def current_document(self):
        if not (window := self.mdi.currentSubWindow()):
            return
        if not (widget := window.widget()):
            return
        return widget.document

    def offset(self, value=1):
        window = self.mdi.currentSubWindow()
        if not window:
            return
        widget = window.widget()
        if not widget:
            return
        document = widget.document
        document.index += value
        self.dopesheet.repaint()
        widget.repaint()

    def next(self):
        self.offset()

    def prev(self):
        self.offset(-1)

    def update(self):
        self.mdi.currentSubWindow().repaint()
        self.dopesheet.repaint()

    def focus(self):
        window = self.mdi.currentSubWindow()
        if not window:
            return
        widget = window.widget()
        if not widget:
            return
        widget.focus()

    def new(self):
        document = Document()
        self.add_document(document, 'New character')

    def open(self):
        filepath, _ = QtWidgets.QFileDialog.getOpenFileName(
            parent=self,
            caption='Open file',
            dir='~',
            filter='Pixo file (*.pixo)')
        if not filepath:
            return
        self.open_filepath(filepath)

    def open_filepath(self, filepath):
        with open(filepath, 'rb') as f:
            data = msgpack.load(f)

        document = Document.load(data)
        self.add_document(document, filepath)

    def add_document(self, document, name):
        canvas = Canvas(document)
        canvas.updated.connect(self.update)
        window = self.mdi.addSubWindow(canvas)
        window.setWindowTitle(name)
        window.show()

    def sub_window_changed(self, window):
        document = window.widget().document if window else None
        self.dopesheet.set_document(document)
        self.palette.set_document(document)
        self.library.set_document(document)
        self.parameters.set_document(document)

    def repaint_canvas(self):
        if (widget := self.mdi.currentSubWindow().widget()):
            widget.repaint()


class PlayerToolbar(QtWidgets.QToolBar):
    def __init__(self):
        super().__init__()
        self.setIconSize(QtCore.QSize(16, 16))
        self.previous = QtGui.QAction(get_icon('previous.png'), '', self)
        self.stop = QtGui.QAction(get_icon('stop.png'), '', self)
        self.play = QtGui.QAction(get_icon('play.png'), '', self)
        self.pause = QtGui.QAction(get_icon('pause.png'), '', self)
        self.next = QtGui.QAction(get_icon('next.png'), '', self)
        spacer = QtWidgets.QWidget()
        spacer.setSizePolicy(*[QtWidgets.QSizePolicy.Expanding] * 2)
        self.addWidget(spacer)
        self.addAction(self.previous)
        self.addAction(self.stop)
        self.addAction(self.play)
        self.addAction(self.pause)
        self.addAction(self.next)
        spacer = QtWidgets.QWidget()
        spacer.setSizePolicy(*[QtWidgets.QSizePolicy.Expanding] * 2)
        self.addWidget(spacer)


class MainToolbar(QtWidgets.QToolBar):
    def __init__(self):
        super().__init__()
        self.new = QtGui.QAction(get_icon('new.png'), '', self)
        self.open = QtGui.QAction(get_icon('open.png'), '', self)
        self.save = QtGui.QAction(get_icon('save.png'), '', self)
        self.addAction(self.new)
        self.addAction(self.open)
        self.addAction(self.save)


class Canvas(QtWidgets.QWidget):

    def __init__(self, document):
        super().__init__()
        self.document = document
        self.canvas = CanvasView(document)
        self.focus = self.canvas.focus
        self.updated = self.canvas.updated
        self.toolbar = PlayerToolbar()
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.canvas)
        layout.addWidget(self.toolbar)


class CanvasView(QtWidgets.QWidget):
    updated = QtCore.Signal()

    def __init__(self, document):
        super().__init__()
        self.document = document
        self.viewportmapper = ViewportMapper()
        self.navigator = Navigator()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QtGui.QColor(25, 25, 25))
        painter.drawRect(event.rect())
        if self.document.current_image:
            image = self.document.current_image.image
            origins, overrides = self.document.palette_override
            if origins:
                image = switch_colors(image, origins, overrides)
            qimage = ImageQt.ImageQt(image)
            rect = QtCore.QRectF(
                0, 0, qimage.size().width(), qimage.size().height())
            rect = self.viewportmapper.to_viewport_rect(rect)
            qimage = qimage.scaled(
                rect.size().toSize(),
                QtCore.Qt.KeepAspectRatio,
                QtCore.Qt.FastTransformation)
            painter.drawImage(rect, qimage)
            painter.setBrush(QtCore.Qt.NoBrush)
            painter.setPen(QtCore.Qt.black)
            painter.drawRect(rect)
        painter.end()

    def mouseReleaseEvent(self, event):
        self.navigator.update(event, pressed=False)

    def mousePressEvent(self, event):
        self.setFocus(QtCore.Qt.MouseFocusReason)
        self.navigator.update(event, pressed=True)

    def keyPressEvent(self, event):
        self.navigator.update(event, pressed=True)
        self.repaint()

    def keyReleaseEvent(self, event):
        if event.isAutoRepeat():
            return
        self.navigator.update(event, pressed=False)
        self.repaint()

    def mouseMoveEvent(self, event):
        zooming = self.navigator.shift_pressed and self.navigator.alt_pressed
        if zooming:
            offset = self.navigator.mouse_offset(event.pos())
            if offset is not None and self.navigator.zoom_anchor:
                factor = (offset.x() + offset.y()) / 10
                self.zoom(factor, self.navigator.zoom_anchor)
                return self.repaint()
        if self.navigator.left_pressed and self.navigator.space_pressed:
            offset = self.navigator.mouse_offset(event.pos())
            if offset is not None:
                self.viewportmapper.origin = (
                    self.viewportmapper.origin - offset)
        elif self.navigator.left_pressed:
            offset = self.navigator.mouse_offset(event.pos())
            if offset and offset.x() > 0.5:
                self.document.index += 1
                self.updated.emit()
            elif offset and offset.x() < -0.5:
                self.document.index -= 1
                self.updated.emit()
        self.repaint()

    def resizeEvent(self, event):
        check = (
            event.size().width(), event.size().height(),
            event.oldSize().height(), event.oldSize().width())
        if 0 in check or -1 in check:
            return
        self.viewportmapper.viewsize = event.size()
        size = (event.size() - event.oldSize()) / 2
        offset = QtCore.QPointF(size.width(), size.height())
        self.viewportmapper.origin -= offset
        self.repaint()

    def focus(self):
        if not self.document.current_image:
            return
        self.viewportmapper.viewsize = self.size()
        size = self.document.current_image.image.size
        rect = QtCore.QRect(0, 0, size[0], size[1])
        self.viewportmapper.focus(rect)
        self.repaint()

    def wheelEvent(self, event):
        factor = .25 if event.angleDelta().y() > 0 else -.25
        zoom(self.viewportmapper, factor, event.position())
        self.repaint()


class CharacterParameters(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.document = None
        self.gender = QtWidgets.QComboBox()
        self.gender.addItems(['male', 'female', 'undefined'])
        self.gender.currentIndexChanged.connect(self.update)
        self.name = QtWidgets.QLineEdit()
        self.name.textEdited.connect(self.update)
        layout = QtWidgets.QFormLayout(self)
        layout.addRow('Name', self.name)
        layout.addRow('Gender', self.gender)

    def set_document(self, document):
        if not document:
            return
        self.document = document
        self.gender.setCurrentText(self.document.data['gender'])
        self.name.setText(self.document.data['name'])

    def update(self):
        if not self.document:
            return
        self.document.data['name'] = self.name.text()
        self.document.data['gender'] = self.gender.currentText()