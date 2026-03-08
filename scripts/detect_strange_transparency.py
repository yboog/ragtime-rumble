
import os
import itertools
from PIL import Image


GREEN = (0, 255, 0, 255)
BG = (0, 0, 0, 0)
pixels = set()

repo_root = os.path.dirname(os.path.dirname(__file__))
files = [r'C:\perso\ragtime-rumble\refs\frames\ghost\walk\ghost-walk-001.png']
for file in files:
    img = Image.open(file)
    # img = img.convert("RGBA")

    pixdata = img.load()
    for y, x in itertools.product(range(img.size[1]), range(img.size[0])):
        pixels.add(pixdata[x, y])
        # if pixdata[x, y] == GREEN:
        #     pixdata[x, y] = BG

def fill_canvas(canvas, images, column_lenght, frame_width, frame_height):
    painter = QtGui.QPainter(canvas)
    row, column = 0, 0
    for image in images:
        painter.drawImage(frame_width * column, frame_height * row, image)
        column += 1
        if column >= column_lenght:
            column = 0
            row += 1
    # img.save(file)

from PySide6 import QtGui, QtCore
image = QtGui.QImage(files[0])
canvas = QtGui.QImage(QtCore.QSize(64, 64), QtGui.QImage.Format.Format_ARGB32)
painter = QtGui.QPainter(canvas)
painter.drawImage(QtCore.QRect(0, 0, 64, 64), image)
canvas.save(files[0] + '.copy.png')

import pprint
print('LEN', len(pixels))
pprint.pprint(pixels)