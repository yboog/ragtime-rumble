import io
import os
import sys
import json
import uuid
import msgpack
import numpy as np
from PIL import Image


*_, char = sys.argv
repo_root = os.path.dirname(os.path.dirname(__file__))
ref_root = f'{repo_root}/refs/frames/{char}/'
palette_path = f'{repo_root}/refs/palettes/{char}.json'
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


with open(palette_path, 'r') as f:
    palettes = json.load(f)


data = {
    'name': 'character',
    'genre': 'woman',
    'framesize': [64, 64],
    'center': [32, 56],
    'box': [-10, -8, 20, 10],
    'hitbox': [-10, -40, 20, 40],
    'palettes': palettes,
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


pixo = {
    'library': {},
    'animation': 'idle',
    'side': 'face',
    'index': 0
}


def remove_key_color(filename):
    orig_color = 0, 255, 0, 255
    replacement_color = 0, 0, 0, 0
    image = Image.open(filename).convert('RGBA')
    data = np.array(image)
    data[(data == orig_color).all(axis=-1)] = replacement_color
    return Image.fromarray(data, mode='RGBA')


def image_to_byte(image):
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    return img_byte_arr.getvalue()


for anim in ORDER:
    for side in ['face', 'back']:
        root = f'{ref_root}/{side}/{anim}'
        for file in os.listdir(root):
            filepath = f'{root}/{file}'
            image = {
                'image': image_to_byte(remove_key_color(filepath)),
                'path': filepath,
                'ctime': os.path.getctime(filepath)}
            id_ = str(uuid.uuid1())
            pixo['library'][id_] = image
            data['animations'][anim]['images'][side].append(id_)
    lenght = len(data['animations'][anim]['images'][side])
    data['animations'][anim]['exposures'] = [6] * lenght

pixo['data'] = data


with open(output, 'wb') as f:
    msgpack.dump(pixo, f)
