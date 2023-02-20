
import os
import sys
import json
import msgpack
from PySide6 import QtGui, QtCore


*_, char = sys.argv
repo_root = os.path.dirname(os.path.dirname(__file__))
ref_root = f'{repo_root}/refs/frames/{char}/'
variation_path = f'{repo_root}/refs/variants/{char}.json'
output = f'{repo_root}/refs/pixoleros/{char}.pixo'


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


def get_canvas_size(frame_count, column_lenght, frame_width, frame_height):
    row, column = 1, 0
    for _ in range(frame_count):
        column += 1
        if column >= column_lenght:
            column = 0
            row += 1
    return QtCore.QSize(frame_width * column_lenght, frame_height * row)


with open(variation_path, 'r') as f:
    variants = json.load(f)


data = {
    'name': 'character',
    'genre': 'woman',
    'framesize': [64, 64],
    'center': [32, 56],
    'box': [-10, -8, 20, 10],
    'hitbox': [-10, -40, 20, 40],
    'variants': variants,
    'animations': {
        'bet': {'images': {'face': [], 'back': []}, 'exposures': []},
        'balcony': {'images': {'face': [], 'back': []}, 'exposures': []},
        'call': {'images': {'face': [], 'back': []}, 'exposures': []},
        'coma': {'images': {'face': [], 'back': []}, 'exposures': []},
        'death': {'images': {'face': [], 'back': []}, 'exposures': []},
        'drink': {'images': {'face': [], 'back': []}, 'exposures': []},
        'gunshot': {'images': {'face': [], 'back': []}, 'exposures': []},
        'idle': {'images': {'face': [], 'back': []}, 'exposures': []},
        'order': {'images': {'face': [], 'back': []}, 'exposures': []},
        'poker': {'images': {'face': [], 'back': []}, 'exposures': []},
        'smoke': {'images': {'face': [], 'back': []}, 'exposures': []},
        'suspicious': {'images': {'face': [], 'back': []}, 'exposures': []},
        'vomit': {'images': {'face': [], 'back': []}, 'exposures': []},
        'walk': {'images': {'face': [], 'back': []}, 'exposures': []},
    }
}


def qimage_to_bytes(image):
    ba = QtCore.QByteArray()
    buff = QtCore.QBuffer(ba)
    buff.open(QtCore.QIODevice.WriteOnly)
    image.save(buff, 'PNG')
    return ba.data()


for anim in ORDER:
    for side in ['face', 'back']:
        root = f'{ref_root}/{side}/{anim}'
        for file in os.listdir(root):
            filepath = f'{root}/{file}'
            image = {
                'image': qimage_to_bytes(QtGui.QImage(filepath)),
                'path': filepath,
                'ctime': os.path.getctime(filepath)}
            data['animations'][anim]['images'][side].append(image)
    lenght = len(data['animations'][anim]['images'][side])
    data['animations'][anim]['exposures'] = [6] * lenght


pixo = {
    'data': data,
    'library': [],
    'animation': 'idle',
    'side': 'face',
    'index': 0
}


with open(output, 'wb') as f:
    msgpack.dump(pixo, f)
