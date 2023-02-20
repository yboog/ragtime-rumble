
import msgpack
from PySide6 import QtWidgets, QtGui, QtCore
from pixoleros.io import get_icon
from pixoleros.navigator import Navigator
from pixoleros.viewport import ViewportMapper, zoom
from pixoleros.model import UiModel


class SpritesheetEditor(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Pixoleros')
        self.mdi = QtWidgets.QMdiArea()
        self.setCentralWidget(self.mdi)

        self.mdi.subWindowActivated.connect(self.sub_window_changed)
        self.mdi.setViewMode(QtWidgets.QMdiArea.TabbedView)
        self.mdi.setTabsClosable(True)

        self.toolbar = MainToolbar()
        self.toolbar.open.triggered.connect(self.open_file)

        self.addToolBar(QtCore.Qt.TopToolBarArea, self.toolbar)

    def open_file(self):
        filepath, _ = QtWidgets.QFileDialog.getOpenFileName(
            parent=self,
            caption='Open file',
            dir='~',
            filter='Pixo file (*.pixo)')
        if not filepath:
            return
        with open(filepath, 'rb') as f:
            data = msgpack.load(f)

        model = UiModel.load(data)
        canvas = Canvas(model)
        window = self.mdi.addSubWindow(canvas)
        window.setWindowTitle(filepath)
        window.show()

    def sub_window_changed(self, *_):
        return


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
    def __init__(self, model):
        super().__init__()
        self.model = model
        self.viewportmapper = ViewportMapper()
        self.navigator = Navigator()

    def paintEvent(self, _):
        painter = QtGui.QPainter(self)
        image = self.model.image
        rect = QtCore.QRectF(0, 0, image.size().width(), image.size().height())
        rect = self.viewportmapper.to_viewport_rect(rect)
        image = image.scaled(
            rect.size().toSize(),
            QtCore.Qt.KeepAspectRatio,
            QtCore.Qt.FastTransformation)
        painter.drawImage(rect, image)

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
                self.model.index += 1
            elif offset and offset.x() < -0.5:
                self.model.index -= 1
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
