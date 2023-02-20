
import sys
import json
from PySide6 import QtGui, QtCore
import PIL.Image
import math
import os


*_, char, side = sys.argv
repo_root = os.path.dirname(os.path.dirname(__file__))
ref_root = f'{repo_root}/refs/frames/{char}/{side}'
relative_output = f'resources/skins/{char}_{side}.png'
variation_path = f'{repo_root}/refs/variants/{char}.json'
output = f'{repo_root}/drunkparanoia/{relative_output}'
gamedata_output_path = f'{repo_root}/drunkparanoia/resources/animdata/{char}.json'


MALES = "smith"


ORDER = [
    'bet',
    'balcony',
    'call',
    'coma',
    'death',
    'drink',
    'gunshot',
    'idle',
    'order',
    'poker',
    'smoke',
    'suspicious',
    'vomit',
    'walk',
]


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


animations = {
    anim: [f'{ref_root}/{anim}/{f}' for f in os.listdir(f'{ref_root}/{anim}')]
    for anim in ORDER}
images = [image for images in animations.values() for image in images]
width, height = PIL.Image.open(images[0]).size
images = [QtGui.QImage(image) for image in images]
column_lenght = math.ceil(math.sqrt(len(images)))
with open(variation_path, 'rb') as f:
    variants = json.load(f)


data = {
    'name': char,
    'gender': 'man' if char in MALES else 'woman',
    'framesize': (64, 64),
    'center': (32, 56),
    'box': (-10, -8, 20, 10),
    'hitbox': (-10, -40, 20, 40),
    'variants': variants,
    'sheets': {
        'face': f'resources/skins/{char}_face.png',
        'back': f'resources/skins/{char}_back.png'},
    'animations': {}
}

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
