
import sys
import json
from PySide6 import QtGui, QtCore
import PIL.Image
import math
import os


repo_root = os.path.dirname(os.path.dirname(__file__))
ref_root = f'{repo_root}/refs/frames/title-screen/titre-anim'
relative_output = 'resources/ui/title.png'
output = f'{repo_root}/ragtimerumble/{relative_output}'


def fill_canvas(canvas, images, column_lenght, frame_width, frame_height):
    painter = QtGui.QPainter(canvas)
    row, column = 0, 0
    for image in images:
        painter.drawImage(frame_width * column, frame_height * row, image)
        column += 1
        if column >= column_lenght:
            column = 0
            row += 1


def get_canvas_size(frame_count, column_lenght, frame_width, frame_height):
    row, column = 1, 0
    for _ in range(frame_count):
        column += 1
        if column >= column_lenght:
            column = 0
            row += 1
    return QtCore.QSize(frame_width * column_lenght, frame_height * row)


data = {
    'name': 'diego',
    'type': 'dog',
    'center': (32, 54),
    'framesize': (64, 64),
    'filepath': "resources/skins/diego.png",
    'animations': {}
}


images = [f'{ref_root}/{file}' for file in os.listdir(ref_root)]
width, height = PIL.Image.open(images[0]).size
images = [QtGui.QImage(image) for image in images]
column_lenght = math.ceil(math.sqrt(len(images)))

canvas_size = get_canvas_size(len(images), column_lenght, width, height)
canvas = QtGui.QImage(canvas_size, QtGui.QImage.Format_ARGB32)
fill_canvas(canvas, images, column_lenght, width, height)
canvas.save(output, "png")
print(os.path.exists(os.path.dirname(output)))
print(output, canvas.isNull())
print(len(images))
