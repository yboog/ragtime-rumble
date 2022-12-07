import math
import random
from PySide6 import QtWidgets, QtCore, QtGui


def distance(p1, p2):
    (ax, ay), (bx, by) = p1, p2
    return math.sqrt(
        (bx - ax)**2 +
        (by - ay)**2)


def shortest_path(orig, dst):
    """
    Create a path between an origin and a destination lock to height
    directions. Function can contains some random to decide the way to use.
            ORIG------------- OTHER WAY POSSIBLE
                \            \
                 \------------ DST
            INTERMEDIATE
    """
    dst = list(dst)[:]
    dst[0] = dst[0] if dst[0] is not None else orig[0]
    dst[1] = dst[1] if dst[1] is not None else orig[1]

    if orig[0] in dst or orig[1] in dst:
        return [orig, dst]

    reverse = random.choice([True, False])
    if reverse:
        orig, dst = dst, orig

    equi1 = dst[0], orig[1]
    equi2 = orig[0], dst[1]
    dist1 = distance(orig, equi1)
    dist2 = distance(orig, equi2)
    if dist1 > dist2:
        if dst[0] > orig[0]:
            intermediate = (equi2[0] + dist2, equi2[1])
        else:
            intermediate = (equi2[0] - dist2, equi2[1])
    else:
        if dst[1] > orig[1]:
            intermediate = (equi1[0], equi1[1] + dist1)
        else:
            intermediate = (equi1[0], equi1[1] - dist1)
    if reverse:
        orig, dst = dst, orig
    return [orig, intermediate, dst]


class TestWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.start = None
        self.end = None
        self.path = None

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.start = event.position().toPoint()
            self.path = None
        elif event.button() == QtCore.Qt.RightButton:
            self.end = event.position().toPoint()
            self.path = None
        self.repaint()

    def paintEvent(self, event):
        if not self.start or not self.end:
            return

        if not self.path:
            self.path = shortest_path(
                (self.start.x(), self.start.y()),
                (self.end.x(), self.end.y()))

        painter = QtGui.QPainter(self)
        if len(self.path) == 2:
            painter.drawLine(
                QtCore.QLine(
                    self.start.x(), self.start.y(),
                    self.end.x(), self.end.y()))

        start = None
        i = 1
        for point in self.path:
            if start is None:
                start = point
                continue
            painter.drawLine(QtCore.QLine(start[0], start[1], point[0], point[1]))
            painter.drawText(start[0], start[1], str(i))
            i += 1
            start = point

        painter.end()


app = QtWidgets.QApplication([])
wid = TestWidget()
wid.show()
app.exec()