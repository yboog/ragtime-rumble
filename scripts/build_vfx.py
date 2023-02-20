
import sys
import json
from PySide6 import QtGui, QtCore
import PIL.Image
import math
import os

vfx = sys.argv[-1]

repo_root = os.path.dirname(os.path.dirname(__file__))
ref_root = f'{repo_root}/refs/frames/{vfx}'
relative_output = f'resources/vfx/{vfx}.png'
output = f'{repo_root}/drunkparanoia/{relative_output}'
gamedata_output_path = f'{repo_root}/drunkparanoia/resources/vfx/{vfx}.json'


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


frames = [f'{ref_root}/{f}' for f in os.listdir(ref_root)]
width, height = PIL.Image.open(frames[0]).size
images = [QtGui.QImage(image) for image in frames]
print(images[0].format())
column_lenght = math.ceil(math.sqrt(len(images)))


data = {
    'name': vfx,
    'type': 'vfx',
    'framesize': (width, height),
    'sheet': relative_output,
    'exposures': [6 for _ in range(len(frames))]
}


with open(gamedata_output_path, 'w') as f:
    json.dump(data, f, indent=2)

canvas_size = get_canvas_size(len(images), column_lenght, width, height)
canvas = QtGui.QImage(canvas_size, QtGui.QImage.Format_ARGB32)
fill_canvas(canvas, images, column_lenght, width, height)
canvas.save(output, "png")
print(os.path.exists(os.path.dirname(output)))
print(output, canvas.isNull())
print(len(images))
