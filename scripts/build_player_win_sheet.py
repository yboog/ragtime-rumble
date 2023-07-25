
import json
from PySide6 import QtGui, QtCore
import PIL.Image
import math
import os


repo_root = os.path.dirname(os.path.dirname(__file__))
ref_root = f'{repo_root}/refs/UI/win-animations'
relative_output = 'resources/ui/scores/win-animations'
output_folder = f'{repo_root}/ragtimerumble/{relative_output}'
gamedata_output_folder = f'{repo_root}/ragtimerumble/resources/animdata'


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


for folder in os.listdir(ref_root):
    filenames = os.listdir(f'{ref_root}/{folder}')
    images = [f'{ref_root}/{folder}/{f}' for f in filenames]
    width, height = PIL.Image.open(images[0]).size
    images = [QtGui.QImage(image) for image in images]
    column_lenght = math.ceil(math.sqrt(len(images)))
    output_file = f'{output_folder}/{folder}.png'
    anim_data = {
        'name': folder,
        'type': 'fx',
        'framesize': (width, height),
        'filepath': output_file,
        'animations': {
            'loop': {
                'exposures': [6 for _ in range(len(images))],
                'startframe': 0
            }
        }
    }
    data_filepath = f'{gamedata_output_folder}/{folder}-win-animation.json'
    with open(data_filepath, 'w') as f:
        json.dump(anim_data, f, indent=2)

    canvas_size = get_canvas_size(len(images), column_lenght, width, height)
    canvas = QtGui.QImage(canvas_size, QtGui.QImage.Format_ARGB32)
    fill_canvas(canvas, images, column_lenght, width, height)
    canvas.save(output_file, 'png')
    print(output_file, 'and', data_filepath, 'generated')
