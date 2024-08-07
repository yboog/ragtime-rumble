
import sys
import json
from PySide6 import QtGui, QtCore
import PIL.Image
import math
import os


ORDER = (
    'idle-a',
    'idle-b',
    'idle-c',
    'idle-d',
    'idle-e',
    'idle-f',
    'idle-g',
    'idle-h',
    'idle-i',
    'runcycle',
    'runjump',
    'scratch',
    'walkcycle',
)


repo_root = os.path.dirname(os.path.dirname(__file__))
ref_root = f'{repo_root}/refs/frames/paulette'
relative_output = 'resources/skins/paulette.png'
output = f'{repo_root}/ragtimerumble/{relative_output}'
gamedata_output_path = f'{repo_root}/ragtimerumble/resources/animdata/paulette.json'


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
    'name': 'paulette',
    'type': 'chicken',
    'y': -1000,
    'framesize': (64, 64),
    'filepath': "resources/skins/paulette.png",
    'animations': {}
}


animations = {
    anim: [f'{ref_root}/{anim}/{f}' for f in os.listdir(f'{ref_root}/{anim}')]
    for anim in ORDER}
images = [image for images in animations.values() for image in images]
width, height = PIL.Image.open(images[0]).size
images = [QtGui.QImage(image) for image in images]
print(images[0].format())
column_lenght = math.ceil(math.sqrt(len(images)))

start = 0
for anim in ORDER:
    data['animations'][anim] = {
        'exposures': [6 for _ in range(len(animations[anim]))],
        'startframe': start}
    print(anim, len(animations[anim]), start)
    start += len(animations[anim])

with open(gamedata_output_path, 'w') as f:
    json.dump(data, f, indent=2)

canvas_size = get_canvas_size(len(images), column_lenght, width, height)
canvas = QtGui.QImage(canvas_size, QtGui.QImage.Format_ARGB32)
fill_canvas(canvas, images, column_lenght, width, height)
canvas.save(output, "png")
print(os.path.exists(os.path.dirname(output)))
print(output, canvas.isNull())
print(len(images))
