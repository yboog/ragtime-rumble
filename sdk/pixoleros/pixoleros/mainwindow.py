
import msgpack
from PIL import ImageQt
from PySide6 import QtWidgets, QtGui, QtCore
from pixoleros.dopesheet import DopeSheet
from pixoleros.io import get_icon
from pixoleros.imgutils import switch_colors
from pixoleros.library import LibraryTableView
from pixoleros.model import Document
from pixoleros.navigator import Navigator
from pixoleros.palette import Palettes
from pixoleros.viewport import ViewportMapper, zoom


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

        areas = (
            QtCore.Qt.TopDockWidgetArea |
            QtCore.Qt.BottomDockWidgetArea |
            QtCore.Qt.LeftDockWidgetArea |
            QtCore.Qt.RightDockWidgetArea)

        self.library = LibraryTableView()
        self.library_dock = QtWidgets.QDockWidget('Library', self)
        self.library_dock.setAllowedAreas(areas)
        self.library_dock.setWidget(self.library)

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
            QtCore.Qt.BottomDockWidgetArea, self.library_dock)
        self.addDockWidget(
            QtCore.Qt.LeftDockWidgetArea, self.palette_dock)

        self.setCorner(
            QtCore.Qt.BottomLeftCorner,
            QtCore.Qt.BottomDockWidgetArea)

        self.setCorner(
            QtCore.Qt.BottomRightCorner,
            QtCore.Qt.RightDockWidgetArea)

        self.addToolBar(QtCore.Qt.TopToolBarArea, self.toolbar)

    def update(self):
        self.mdi.currentSubWindow().repaint()
        self.dopesheet.repaint()

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
        self.viewportmapper.viewsize = event.size()
        size = (event.size() - event.oldSize()) / 2
        offset = QtCore.QPointF(size.width(), size.height())
        self.viewportmapper.origin -= offset
        self.repaint()

    def wheelEvent(self, event):
        factor = .25 if event.angleDelta().y() > 0 else -.25
        zoom(self.viewportmapper, factor, event.position())
        self.repaint()
