import os
import json
import pygame
import itertools
import numpy as np
from PIL import Image

from drunkparanoia.config import GAMEROOT


_animation_store = {}
_image_store = {}


def swap_colors(surface, palette1, palette2):
    """ THX Chat GPT:"""
    swapped_surface = pygame.Surface(surface.get_size())
    original_pixels = pygame.PixelArray(surface)
    swapped_pixels = pygame.PixelArray(swapped_surface)
    for x in range(original_pixels.shape[0]):
        for y in range(original_pixels.shape[1]):
            color = original_pixels[x, y]
            # Transform a bit pixel into a list comparable with palette data.
            check = [color >> 16, color >> 8 & 0xff, color & 0xff]
            if check in palette1:
                index = palette1.index(check)
                color = palette2[index]
                swapped_color = color[0] << 16 | color[1] << 8 | color[2]
            else:
                swapped_color = color
            swapped_pixels[x, y] = swapped_color
    # PixelArray is expensive for memory, then we force an immediate delete.
    # In case of the garbage collector would delay the memory clear to later.
    del original_pixels
    del swapped_pixels
    return swapped_surface


def load_skins():
    d = f'{GAMEROOT}/resources/animdata'
    skins = [f'{d}/{f}' for f in os.listdir(d)]
    for skin in skins:
        with open(skin, 'r') as f:
            data = json.load(f)
        for filepath in data['sheets'].values():
            frames = load_frames(filepath, data['framesize'], (0, 255, 0))
            for frame in frames:
                image_mirror(frame, horizontal=True)


def load_skin(data):
    size = data['framesize']
    sheets = data["sheets"]
    # Build original colors skin.
    result = [{
        side: load_frames(sheets[side], size, (0, 255, 0))
        for side in ('face', 'back')}]
    # Build color variations
    for i, variation in enumerate(data['variations']):
        palette1 = [colors[0] for colors in variation]
        palette2 = [colors[1] for colors in variation]
        skin = {}
        for side in ('face', 'back'):
            image = load_frames(
                sheets[side], size, (0, 255, 0), palette1, palette2, i)
            skin[side] = image
        result.append(skin)
    return result


def load_frames(
        filepath, frame_size, key_color,
        palette1=None, palette2=None, variation=None):
    """
    Split a huge sheet in memory.
    """
    filepath = filename_id = f'{GAMEROOT}/{filepath}'
    if variation is not None:
        filename_id = f'{GAMEROOT}/{filepath}.{variation}'
    if _animation_store.get(filename_id):
        return _animation_store.get(filename_id, [])

    sheet = pygame.image.load(filepath).convert()
    if palette1 and palette2:
        sheet = swap_colors(sheet, palette1, palette2)
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
        id_ = f'{filename_id}[{i}.{j}]'
        _image_store[id_] = image
        ids.append(id_)
    _animation_store[filename_id] = ids
    return ids


def get_image(image_id):
    return _image_store.get(image_id)


def load_image(filename, key_color=None):
    if _image_store.get(filename):
        return filename

    filepath = f'{GAMEROOT}/{filename}'
    image = pygame.image.load(filepath).convert_alpha()
    if key_color is not None:
        image.set_colorkey(key_color)
    _image_store[filename] = image
    return filename


def load_data(filename):
    filepath = f'{GAMEROOT}/{filename}'
    with open(filepath, 'r') as f:
        return json.load(f)


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
