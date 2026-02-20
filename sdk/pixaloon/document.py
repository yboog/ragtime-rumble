import os
import json
from PySide6 import QtGui, QtCore
from pixaloon.canvas.navigator import Navigator
from pixaloon.canvas.viewport import ViewportMapper
from pixaloon.imgutils import remove_key_color
from pixaloon.selection import Selection


class Document(QtCore.QObject):
    edited = QtCore.Signal()

    def __init__(self, gameroot, data=None, filepath=None):
        super().__init__()
        self.filepath = filepath
        self.data = data
        self.viewportmapper: ViewportMapper = ViewportMapper()
        self.selection: Selection = Selection()
        self.navigator: Navigator = Navigator()
        self.gameroot = gameroot
        self.elements_to_render = ['popspots',]

        self.veil_alpha = 10
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
        return Document(gameroot, data, filepath)

    def update_qimages(self):
        self.overlays = []
        self.props = []
        self.backgrounds = []
        self.scores = {}

        for background in self.data['backgrounds']:
            img = QtGui.QImage(f'{self.gameroot}/{background["file"]}')
            self.backgrounds.append(img)

        for overlay in self.data['overlays']:
            img = remove_key_color(f'{self.gameroot}/{overlay["file"]}')
            self.overlays.append(img)

        for prop in self.data['props']:
            img = remove_key_color(f'{self.gameroot}/{prop["file"]}')
            self.props.append(img)

        path = f'{self.gameroot}/{self.data["score"]["ol"]["file"]}'
        self.scores['overlay'] = remove_key_color(path)
        path = f'{self.gameroot}/resources/ui/coin-stack/coin-stack-05.png'
        self.scores['coin-stack'] = remove_key_color(path)
        for i in range(1, 5):
            p = f'player{i}'
            self.scores[p] = {}
            path = f'{self.gameroot}/{self.data["score"][p]["life"]["file2"]}'
            self.scores[p]['life'] = remove_key_color(path)
            path = f'{self.gameroot}/{self.data["score"][p]["bullet"]["on"]}'
            self.scores[p]['bullet'] = remove_key_color(path)

    def delete_selection(self):
        if not self.selection:
            return
        match self.selection.tool:
            case Selection.POPSPOT:
                for row in sorted(self.selection.data, reverse=True):
                    del self.data['popspots'][row]
            case Selection.PATH:
                index = self.selection.data[0]
                del self.data['paths'][index]
            case Selection.WALL:
                del self.data['walls'][self.selection.data]
            case Selection.TARGET:
                target, destination = self.selection.data
                if destination is None:
                    del self.data['targets'][target]
                else:
                    target = self.data['targets'][target]
                    del target['destinations'][destination]
            case Selection.NO_GO_ZONE:
                index = self.selection.data
                del self.data['no_go_zones'][index]
            case Selection.INTERACTION:
                index = self.selection.data
                del self.data['interactions'][index]
            case Selection.FENCE:
                del self.data['fences'][self.selection.data]
            case Selection.OVERLAY:
                index = self.selection.data
                del self.data['overlays'][index]
                self.update_qimages()
        self.selection.clear()
        self.selection.changed.emit(None)
        self.edited.emit()
