import pickle
from PySide6 import QtWidgets, QtCore, QtGui


STATUS_COLORS = {
    'autopilot': 'red',
    'duel_origin': 'yellon',
    'duel_target': 'yellow',
    'interacting': 'orange',
    'out': 'black',
    'free': 'green',
    'stuck': 'white',
}


class HeatmapDisplayWidget(QtWidgets.QWidget):
    def __init__(self, heatmap_path, parent=None):
        super().__init__(parent, QtCore.Qt.Tool)
        with open(heatmap_path, 'rb') as f:
            self.heatmap_data = pickle.load(f)

        self.heatmap_display = HeatmapDisplay(self.heatmap_data)

        self.timeline = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.timeline.setMaximum(len(self.heatmap_data) - 1)
        self.timeline.valueChanged.connect(self.set_frame)

        self.all = QtWidgets.QCheckBox('All')
        self.all.toggled.connect(self.check_all)

        self.isolate = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.isolate.setRange(-1, len(self.heatmap_data[0]) - 1)
        self.isolate.setValue(-1)
        self.isolate.valueChanged.connect(self.isolate_character)

        layout1 = QtWidgets.QHBoxLayout()
        layout1.setContentsMargins(0, 0, 0, 0)
        layout1.addWidget(self.timeline)
        layout1.addWidget(self.all)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.heatmap_display)
        layout.addLayout(layout1)
        layout.addWidget(self.isolate)

    def check_all(self, state):
        self.heatmap_display.all_frames = state
        self.heatmap_display.update()

    def set_frame(self, frame):
        self.heatmap_display.frame = frame
        self.heatmap_display.update()

    def isolate_character(self, value):
        self.heatmap_display.isolated_index = value
        self.heatmap_display.update()


class HeatmapDisplay(QtWidgets.QWidget):
    def __init__(self, heatmap_data, parent=None):
        super().__init__(parent=parent)
        self.data = heatmap_data
        self.frame = 0
        self.all_frames = False
        self.npc_path_pixmaps = {}
        self.isolated_index = -1
        self.heatmap_pixmap = None
        self.setFixedSize(640, 360)

    def get_heatmap_pixmap(self):
        if self.heatmap_pixmap is None:
            self.heatmap_pixmap = QtGui.QPixmap(QtCore.QSize(640, 360))
            self.heatmap_pixmap.fill(QtCore.Qt.white)
            painter = QtGui.QPainter(self.heatmap_pixmap)
            painter.setPen(QtCore.Qt.NoPen)
            color = QtGui.QColor(255, 0, 0, 5)
            painter.setBrush(color)
            for positions in self.data:
                for position, status, _ in positions:
                    if status == 'out':
                        continue
                    position = QtCore.QPoint(*position)
                    painter.drawEllipse(position, 5, 5)
            painter.end()
        return self.heatmap_pixmap

    def get_npc_paths_pixmap(self, index):
        pixmap = self.npc_path_pixmaps.get(index)
        if pixmap:
            return pixmap
        pixmap = QtGui.QPixmap(QtCore.QSize(640, 360))
        pixmap.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(pixmap)
        painter.setPen(QtCore.Qt.NoPen)
        last_point = None
        for positions in self.data:
            position, status, freepilot = positions[index]
            if status == 'out':
                continue
            point = QtCore.QPoint(*position)
            if last_point is None:
                last_point = point
                continue
            color = QtGui.QColor(STATUS_COLORS[status] if freepilot else 'blue')
            painter.setPen(color)
            painter.drawLine(last_point, point)
            last_point = point
        painter.end()
        self.npc_path_pixmaps[index] = pixmap
        return pixmap

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.drawRect(self.rect())
        if self.all_frames and self.isolated_index == -1:
            painter.drawPixmap(self.rect(), self.get_heatmap_pixmap())
            return
        elif self.all_frames:
            pixmap = self.get_npc_paths_pixmap(self.isolated_index)
            painter.drawPixmap(self.rect(), pixmap)
        else:
            positions = self.data[self.frame]
            for position, status, freepilot in positions:
                color = QtGui.QColor(
                    (STATUS_COLORS[status] if freepilot else 'blue'))
                painter.setPen(color)
                point = QtCore.QPoint(*position)
                painter.drawEllipse(point, 2, 2)
        painter.end()
        return super().paintEvent(event)