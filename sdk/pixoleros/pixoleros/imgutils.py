import math
import colorsys
import numpy as np
from PIL import Image, ImageQt
from collections import Counter
from PySide6 import QtGui, QtCore


def remove_key_color(filename):
    orig_color = [0, 255, 0, 255]
    replacement_color = (0, 0, 0, 0)
    image = Image.open(filename).convert('RGBA')
    data = np.array(image)
    data[(data == orig_color).all(axis=-1)] = replacement_color
    return Image.fromarray(data, mode='RGBA')


def switch_colors(image, palette1, palette2):
    data = np.array(image)
    # Temporarily unpack the bands for readability
    red, green, blue, _ = data.T
    for color1, color2 in zip(palette1, palette2):
        if color1 == color2:
            continue
        # Replace white with red... (leaves alpha values alone...)
        areas = (red == color1[0]) & (blue == color1[2]) & (green == color1[1])
        data[..., :-1][areas.T] = color2  # Transpose back needed
        # data[(data == color1).all(axis=-1)] = color2
    return Image.fromarray(data, mode='RGBA')


def list_rgb_colors(image):
    return sorted(
        list(Counter(image.convert('RGB').getdata())),
        key=lambda rgb: colorsys.rgb_to_hls(*rgb))


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


def build_sprite_sheet(document):
    image_ids = [
        image for anim in document.data['animations'].values()
        for image in anim['images']]
    images = [ImageQt.ImageQt(document.library[id_].image) for id_ in image_ids]
    column_lenght = math.ceil(math.sqrt(len(images)))
    canvas_size = get_canvas_size(len(images), column_lenght, 64, 64)
    base = QtGui.QImage(canvas_size, QtGui.QImage.Format_ARGB32)
    fill_canvas(base, images, column_lenght, 64, 64)
    image = Image.fromqimage(base)
    images = []
    for indexes in document.iter_all_possible_overrides():
        origins = []
        overrides = []
        for i, j in enumerate(indexes):
            origins.extend(document.palettes[i]['origins'])
            overrides.extend(document.palettes[i]['palettes'][j])
        images.append(switch_colors(image, origins, overrides))
    return images