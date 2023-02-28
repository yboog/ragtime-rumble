import colorsys
import numpy as np
from PIL import Image
from collections import Counter


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
