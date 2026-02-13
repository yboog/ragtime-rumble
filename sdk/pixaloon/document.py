import os
import json
from PySide6 import QtGui, QtCore
from pixaloon.canvas.navigator import Navigator
from pixaloon.canvas.viewport import ViewportMapper
from pixaloon.imgutils import remove_key_color
from pixaloon.selection import Selection


class Document(QtCore.QObject):
    edited = QtCore.Signal()

    def __init__(self, gameroot, data=None):
        super().__init__()
        self.data = data
        self.viewportmapper: ViewportMapper = ViewportMapper()
        self.selection: Selection = Selection()
        self.navigator: Navigator = Navigator()
        self.gameroot = gameroot
        self.elements_to_render = [
            'popspots',
            'props',
            'walls',
            'stairs',
            'targets',
            'fences',
            'interactions',
            'startups',
            'paths']

        self.veil_alpha = 100
        self.overlays = []
        self.props = []
        self.backgrounds = []
        self.selected_target = 0
        self.update_qimages()

    def set_gameroot(self, gameroot):
        self.gameroot = gameroot
        self.update_qimages()

    @staticmethod
    def open(filepath, gameroot=None):
        gameroot = (
            gameroot or
            os.path.dirname(os.path.dirname(os.path.dirname(filepath))))
        with open(filepath, 'r') as f:
            data = json.load(f)
        return Document(gameroot, data)

    def update_qimages(self):
        self.overlays = []
        self.props = []
        self.backgrounds = []

        for background in self.data['backgrounds']:
            img = QtGui.QImage(f'{self.gameroot}/{background["file"]}')
            self.backgrounds.append(img)

        for overlay in self.data['overlays']:
            img = remove_key_color(f'{self.gameroot}/{overlay["file"]}')
            self.overlays.append(img)

        for prop in self.data['props']:
            img = remove_key_color(f'{self.gameroot}/{prop["file"]}')
            self.props.append(img)
