import os
import msgpack
from copy import deepcopy
from PySide6 import QtGui
from pixoleros.template import EMPTY_ANIMDATA
from pixoleros.io import serialize_model, bytes_to_qimage


class UiModel:
    def __init__(self):
        self.data = deepcopy(EMPTY_ANIMDATA)
        self.library = []
        self.animation = 'idle'
        self.side = 'face'
        self._index = 0

    @staticmethod
    def load(data):
        model = UiModel()
        model.data = data['data']
        model.library = [Image.load(image) for image in data['library']]
        model.animation = data['animation']
        model.side = data['side']
        model.index = data['index']
        for animation in data['data']['animations']:
            for side in ('face', 'back'):
                images = model.data['animations'][animation]['images'][side]
                model.data['animations'][animation]['images'][side] = [
                    Image.load(img) for img in images]
        return model

    @property
    def index(self):
        return max((0, min((self._index, sum(self.exposures)))))

    @index.setter
    def index(self, n):
        self._index = max((0, min((n, sum(self.exposures)))))

    @property
    def images(self):
        img = self.data['animations'][self.animation]['images'].get(self.side)
        return img or self.data['animations'][self.animation]['images']['face']

    @property
    def exposures(self):
        return self.data['animations'][self.animation]['exposures']

    @property
    def image(self):
        try:
            index = frame_index_from_exposures(self.index, self.exposures)
            return self.images[index].image
        except IndexError:
            print(index, 'error')
            return None

    def save(self, filepath):
        data = serialize_model(self)
        with open(filepath, 'wb') as f:
            msgpack.dump(data, f)


def frame_index_from_exposures(index, exposures):
    """
    frame indexes:
    0       1   2           3           4
    exposures indexes:
    0 - 1 - 2 - 3 - 4 - 5 - 6 - 7 - 8 - 9
    Return examples:
        index = 1 -> 2
        index = 3 -> 6
        index = 8 -> 3
    """
    loop = 0
    for i, d in enumerate(exposures):
        for _ in range(d):
            if index == loop:
                return i
            loop += 1
    return 0


class Image:
    def __init__(self, qimage, path, ctime):
        self.image = qimage
        self.path = path
        self.ctime = ctime

    @staticmethod
    def load(data):
        qimage = bytes_to_qimage(data['image'])
        return Image(qimage, data['path'], data['ctime'])

    @property
    def reference_exists(self):
        return os.path.exists(self.path)

    @property
    def file_modified(self):
        if not self.reference_exists:
            return False
        return os.path.getctime(self.path) == self.ctime

    def update(self):
        if not self.reference_exists:
            return
        self.image = QtGui.QImage(self.path)
