import os
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


def serialize_image(image):
    return {
        'path': image.path,
        'ctime': image.ctime,
        'image': qimage_to_bytes(image.image)}


def serialize_animdata(data):
    data = deepcopy(data)
    for animation in data['animation']:
        for side in ('face', 'back'):
            images = data[animation]['images'][side]
            data[animation]['images'][side] = [
                serialize_image(img) for img in images]
    return data


def serialize_model(model):
    return {
        'data': serialize_animdata(model.data),
        'library': [serialize_image(img) for img in model.library],
        'animation': model.animation,
        'side': model.side,
        'index': model.index
    }
