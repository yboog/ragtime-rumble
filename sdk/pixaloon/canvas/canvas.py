

from PySide6 import QtWidgets, QtGui, QtCore
from pixaloon.canvas.paint import (
    paint_canvas_popspots, paint_canvas_base, paint_canvas_fences,
    paint_canvas_interactions, paint_canvas_paths, paint_canvas_props,
    paint_canvas_stairs, paint_canvas_startups, paint_canvas_switchs,
    paint_scores, paint_canvas_target, paint_canvas_walls, paint_npc,
    paint_canvas_shadow_zones, paint_canvas_selection,
    paint_background_placeholder)
from pixaloon.canvas.tools.basetool import NavigationTool
from pixaloon.toolmode import ToolMode


def zoom(viewportmapper, factor, reference):
    abspoint = viewportmapper.to_units_coords(reference)
    if factor > 0:
        viewportmapper.zoomin(abs(factor))
    else:
        viewportmapper.zoomout(abs(factor))
    relcursor = viewportmapper.to_viewport_coords(abspoint)
    vector = relcursor - reference
    viewportmapper.origin = viewportmapper.origin + vector


class LevelCanvas(QtWidgets.QWidget):
    def __init__(self, document=None, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.toolmode: ToolMode = ToolMode()
        self.tool = NavigationTool(self)
        self.document = None
        self.set_document(document)

    def showEvent(self, event):
        QtCore.QTimer.singleShot(1, self.focus)
        return super().showEvent(event)

    def sizeHint(self):
        return QtCore.QSize(900, 750)

    def set_document(self, document):
        self.document = document
        self.document.edited.connect(self.update)
        self.document.selection.changed.connect(lambda _: self.update())
        self.update()

    def focus(self):
        self.document.viewportmapper.focus(QtCore.QRect(0, 0, 640, 360))

        self.update()

    def wheelEvent(self, event):
        factor = .25 if event.angleDelta().y() > 0 else -.25
        zoom(self.document.viewportmapper, factor, event.position())
        self.update()

    def resizeEvent(self, event):
        self.document.viewportmapper.viewsize = event.size()
        size = (event.size() - event.oldSize()) / 2
        offset = QtCore.QPointF(size.width(), size.height())
        self.document.viewportmapper.origin -= offset
        self.update()

    def enterEvent(self, _):
        self.update_cursor()

    def leaveEvent(self, _):
        QtWidgets.QApplication.restoreOverrideCursor()

    def mouseMoveEvent(self, event):
        self.tool.mouseMoveEvent(event)
        self.update_cursor()
        self.update()

    def mousePressEvent(self, event):
        self.setFocus(QtCore.Qt.MouseFocusReason)
        self.document.navigator.update(event, pressed=True)
        result = self.tool.mousePressEvent(event)
        self.update_cursor()
        if result:
            self.update()

    def mouseReleaseEvent(self, event):
        self.document.navigator.update(event, pressed=False)
        self.tool.mouseReleaseEvent(event)
        self.update_cursor()
        self.update()

    def keyPressEvent(self, event):
        if event.isAutoRepeat():
            return
        self.document.navigator.update(event, pressed=True)
        self.tool.keyPressEvent(event)
        self.update_cursor()
        self.update()

    def keyReleaseEvent(self, event):
        if event.isAutoRepeat():
            return
        self.document.navigator.update(event, pressed=False)
        self.tool.keyReleaseEvent(event)
        self.update_cursor()
        self.update()

    def paintEvent(self, event):
        if not self.document:
            return
        painter = QtGui.QPainter(self)
        paint_canvas_base(
            painter, self.document,
            self.document.viewportmapper,
            event.rect())

        rect = QtCore.QRect(
            self.rect().left(), self.rect().top(),
            self.rect().width() - 1, self.rect().height() - 1)
        color = QtGui.QColor('black')
        color.setAlpha(10)
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(color)
        painter.drawRect(rect)
        paint_scores(painter, self.document, self.document.viewportmapper)

        try:
            if 'switchs' in self.document.elements_to_render:
                paint_canvas_switchs(
                    painter, self.document, self.document.viewportmapper,
                    event.rect().left(), event.rect().right())
        except BaseException as e:
            print('fail, switchs', e)

        try:
            if 'popspots' in self.document.elements_to_render:
                paint_canvas_popspots(
                    painter, self.document, self.document.viewportmapper)
        except BaseException as e:
            print('popspot', e)
            raise

        try:
            if 'props' in self.document.elements_to_render:
                paint_canvas_props(
                    painter, self.document, self.document.viewportmapper)
        except BaseException:
            print('props')

        try:
            if 'walls' in self.document.elements_to_render:
                paint_canvas_walls(
                    painter, self.document, self.document.viewportmapper)
        except BaseException as e:
            print('walls', e)

        try:
            if 'shadows' in self.document.elements_to_render:
                paint_canvas_shadow_zones(
                    painter, self.document, self.document.viewportmapper)
        except BaseException as e:
            print('shadows', str(e))

        try:
            if 'stairs' in self.document.elements_to_render:
                paint_canvas_stairs(
                    painter, self.document, self.document.viewportmapper)
        except BaseException:
            print('stairs')

        try:
            if 'targets' in self.document.elements_to_render:
                filters = self.document.gametypes_display_filters
                for target in self.document.data['targets']:
                    if not any(gt in filters for gt in target['gametypes']):
                        continue
                    paint_canvas_target(
                        painter=painter,
                        target=target,
                        viewportmapper=self.document.viewportmapper)
        except BaseException as e:
            print('targets', e)

        try:
            if 'fences' in self.document.elements_to_render:
                paint_canvas_fences(painter, self.document, self.document.viewportmapper)
        except BaseException:
            print('fences')

        try:
            if 'interactions' in self.document.elements_to_render:
                paint_canvas_interactions(
                    painter, self.document, self.document.viewportmapper)
        except BaseException:
            print('interactions')

        try:
            if 'startups' in self.document.elements_to_render:
                paint_canvas_startups(
                    painter, self.document, self.document.viewportmapper)
        except BaseException as e:
            print('startups', str(e))

        try:
            if 'bgph' in self.document.elements_to_render:
                d = self.document.data['edit_data']['background_placeholders']
                for bgph in d:
                    paint_background_placeholder(
                        painter, bgph, self.document.viewportmapper)
        except BaseException as e:
            print('bgphs', str(e))
            raise

        try:
            if 'npcs' in self.document.elements_to_render:
                for npc in self.document.data['npcs']:
                    paint_npc(painter, npc, self.document.viewportmapper)
        except BaseException as e:
            print('npcs', str(e))
            raise

        try:
            if 'paths' in self.document.elements_to_render:
                painter.setOpacity(.3)
                paint_canvas_walls(
                    painter, self.document, self.document.viewportmapper)
                painter.setOpacity(1)
                paint_canvas_paths(
                    painter, self.document, self.document.viewportmapper)
        except BaseException:
            print('paths')

        paint_canvas_selection(
            painter,
            self.document,
            self.document.viewportmapper)
        self.tool.draw(painter)
        painter.end()

    def update_cursor(self):
        if not self.tool.window_cursor_visible():
            override = QtCore.Qt.BlankCursor
        else:
            override = self.tool.window_cursor_override()

        override = override or QtCore.Qt.ArrowCursor
        current_override = QtWidgets.QApplication.overrideCursor()

        if not current_override:
            QtWidgets.QApplication.setOverrideCursor(override)
            return

        if current_override and current_override.shape() != override:
            # Need to restore override because overrides can be nested.
            QtWidgets.QApplication.restoreOverrideCursor()
            QtWidgets.QApplication.setOverrideCursor(override)