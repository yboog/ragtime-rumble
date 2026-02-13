from PySide6 import QtCore, QtWidgets, QtGui
from pixaloon.selection import Selection
from pixaloon.canvas.tools.basetool import NavigationTool
from pixaloon.toolmode import ToolMode
from pixaloon.mathutils import start_end_to_rect_data


class OverlayTool(NavigationTool):

    def mousePressEvent(self, event):
        if self.toolmode.mode == ToolMode.SELECTION:
            return self.mouse_press_selection(event)
        if self.toolmode.mode == ToolMode.CREATE:
            return self.mouse_press_create(event)

    def mouse_press_create(self, event):
        qpoint = self.document.viewportmapper.to_units_coords(event.pos())
        qpoint = qpoint.toPoint()
        point = [int(v) for v in qpoint.toTuple()]
        print('TODO')

    def mouse_press_selection(self, event):
        if event.button() != QtCore.Qt.LeftButton:
            return
        qpoint = self.document.viewportmapper.to_units_coords(event.pos())
        qpoint = qpoint.toPoint()
        for i, overlay in enumerate(self.document.data['overlays']):
            image = self.document.overlays[i]
            pos = overlay['position']
            rect = QtCore.QRect(QtCore.QPoint(*pos), image.size())
            if rect.contains(qpoint):
                self.selection.tool = Selection.OVERLAY
                self.selection.data = i
                self.selection.changed.emit()
                return

            self.selection.clear()
            self.selection.changed.emit()

    def draw(self, painter):
        painter.setBrush(QtCore.Qt.transparent)
        pen = QtGui.QPen(QtCore.Qt.black)
        pen.setStyle(QtCore.Qt.DashLine)
        painter.setPen(pen)
        for i, overlay_data in enumerate(self.document.data['overlays']):
            image = self.document.overlays[i]
            size = image.size().toTuple()
            rect = QtCore.QRectF(*overlay_data['position'], *size)
            rect = self.viewportmapper.to_viewport_rect(rect)
            painter.drawRect(rect)

    def draw_create(self, painter):
        if self.new_shape_data is None:
            return
        data = start_end_to_rect_data(*self.new_shape_data)
        rect = QtCore.QRectF(*data)
        painter.drawRect(self.viewportmapper.to_viewport_rect(rect))
