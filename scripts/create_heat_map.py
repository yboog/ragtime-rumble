import os
import json
from PySide2 import QtWidgets, QtCore, QtGui

app = QtGui.QGuiApplication()
image = QtGui.QPixmap(QtCore.QSize(640, 360))
painter = QtGui.QPainter(image)

filepath = f'{os.path.dirname(__file__)}/../refs/coord.json'
with open(filepath, 'r') as f:
    points = json.load(f)

image.fill(QtCore.Qt.white)

color = QtGui.QColor(QtCore.Qt.black)
color.setAlpha(2)
painter.setBrush(color)
painter.setPen(color)

for point in points:
    point = QtCore.QPointF(*point)
    painter.drawEllipse(point, 4, 4)

filepath = f'{os.path.dirname(__file__)}/../refs/coord.png'
image = image.toImage()
image.save(filepath)