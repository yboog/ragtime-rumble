from PySide6 import QtCore
from pixaloon.canvas.viewport import zoom
from pixaloon.toolmode import ToolMode


class BaseTool:
    """
    This baseclass is only there to avoid reimplement unused method in each
    children. This is NOT doing anything.
    """

    def __init__(self, canvas=None, document=None):
        self.canvas = canvas
        self.document = document
        self.is_dirty = False

    @property
    def navigator(self):
        if not self.document:
            return None
        return self.document.navigator

    @property
    def selection(self):
        return self.document.selection

    @property
    def toolmode(self):
        return self.canvas.toolmode

    @property
    def viewportmapper(self):
        return self.document.viewportmapper

    def set_document(self, document):
        self.document = document

    def keyPressEvent(self, event):
        ...

    def keyReleaseEvent(self, event):
        ...

    def mousePressEvent(self, event):
        ...

    def mouseMoveEvent(self, event):
        ...

    def mouseReleaseEvent(self, event) -> bool:
        "Record an undo state if it returns True."
        ...

    def mouseWheelEvent(self, event):
        ...

    def tabletMoveEvent(self, event):
        ...

    def wheelEvent(self, event):
        ...

    def draw(self, painter):
        ...

    def window_cursor_visible(self):
        return True

    def window_cursor_override(self):
        return


class NavigationTool(BaseTool):
    """
    This is the main tool to navigate in scene. This can be subclassed for
    advanced tools which would keep the navigation features.
    """

    def mouseMoveEvent(self, event):
        zooming = self.navigator.shift_pressed and self.navigator.alt_pressed
        if zooming:
            offset = self.navigator.mouse_offset(event.pos())
            if offset is not None and self.navigator.zoom_anchor:
                factor = (offset.x() + offset.y()) / 10
                self.zoom(factor, self.navigator.zoom_anchor)
                return True
        navigate = (
            self.navigator.left_pressed and self.navigator.space_pressed or
            self.navigator.center_pressed)
        if navigate:
            offset = self.navigator.mouse_offset(event.pos())
            if offset is not None:
                self.viewportmapper.origin = (
                    self.viewportmapper.origin - offset)
            return True
        return False

    def wheelEvent(self, event):
        factor = .25 if event.angleDelta().y() > 0 else -.25
        zoom(self.viewportmapper, factor, event.position())

    def mouseReleaseEvent(self, event):
        return False

    def tabletMoveEvent(self, event):
        return self.mouseMoveEvent(event)

    def window_cursor_visible(self):
        return True

    def window_cursor_override(self):
        space = self.navigator.space_pressed
        left = self.navigator.left_pressed
        center = self.navigator.center_pressed
        if center:
            return QtCore.Qt.ClosedHandCursor
        if space and not left:
            return QtCore.Qt.OpenHandCursor
        if space and left:
            return QtCore.Qt.ClosedHandCursor
