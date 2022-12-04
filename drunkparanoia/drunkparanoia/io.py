import os
import json
import itertools
import pygame
from drunkparanoia.config import GAMEROOT


_animation_store = {}
_image_store = {}


def load_skins():
    d = f'{GAMEROOT}/resources/animdata'
    skins = [f'{d}/{f}' for f in os.listdir(d)]
    for skin in skins:
        with open(skin, 'r') as f:
            data = json.load(f)
        for side, filepath in data['sheets'].items():
            frames = load_frames(filepath, data['framesize'], (0, 255, 0))
            if side == 'side':
                for frame in frames:
                    image_mirror(frame, horizontal=True)

def load_skin(data):
    return {
        side: load_frames(data["sheets"][side], data['framesize'], (0, 255, 0))
        for side in ('face', 'side', 'back')}


def load_frames(filepath, frame_size, key_color):
    """
    Split a huge sheet in memory.
    """
    filepath = f'{GAMEROOT}/{filepath}'
    if _animation_store.get(filepath):
        return _animation_store.get(filepath, [])

    sheet = pygame.image.load(filepath).convert()
    width, height = frame_size
    row = sheet.get_height() / height
    col = sheet.get_width() / width
    if row != int(row) or col != int(col):
        message = (
            f"the sprite sheet file {filepath} size doesn't "
            "match with his block size")
        raise ValueError(message)
    ids = []

    for j, i in itertools.product(range(int(row)), range(int(col))):
        image = pygame.Surface([width, height]).convert()
        x, y = i * width, j * height
        image.blit(sheet, (0, 0), (x, y, width, height))
        image.set_colorkey(key_color)
        id_ = f'{filepath}[{i}.{j}]'
        _image_store[id_] = image
        ids.append(id_)
    _animation_store[filepath] = ids
    return ids


def get_image(image_id):
    return _image_store.get(image_id)


def load_image(filename, key_color=None):
    if _image_store.get(filename):
        return filename
    image = pygame.image.load(filename).convert()
    if key_color is not None:
        image.set_colorkey(key_color)
    _image_store[filename] = image
    return filename


def image_mirror(id_, horizontal=True, vertical=False):
    if not _image_store.get(id_):
        raise ValueError(f'Unknown image id {id_}. Cannot generate a mirror.')
    flip_id = f'{id_}['
    if horizontal:
        flip_id += 'h'
    if vertical:
        flip_id += 'v'
    flip_id += ']'
    if not _image_store.get(flip_id):
        image = _image_store[id_]
        mirror = pygame.transform.flip(image, horizontal, vertical)
        _image_store[flip_id] = mirror
    return flip_id
