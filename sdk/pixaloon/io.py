import io
import os
from PIL import Image
from copy import deepcopy
from PySide6 import QtCore, QtGui


def get_icon(filename):
    here = os.path.dirname(__file__)
    return QtGui.QIcon(f'{here}/icons/{filename}')


def qimage_to_bytes(image):
    ba = QtCore.QByteArray()
    buff = QtCore.QBuffer(ba)
    buff.open(QtCore.QIODevice.WriteOnly)
    image.save(buff, 'PNG')
    return ba.data()


def bytes_to_qimage(image_bytes):
    ba = QtCore.QByteArray(image_bytes)
    image = QtGui.QImage()
    image.loadFromData(ba, 'PNG')
    return image


def bytes_to_image(image_bytes):
    return Image.open(io.BytesIO(image_bytes))
