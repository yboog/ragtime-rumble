
from PySide6 import QtWidgets
from pixaloon.editors.base import BaseEditor
from pixaloon.selection import Selection
from pixaloon.intarrayeditor import IntArrayListEditor


class PathEditor(BaseEditor):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.points = IntArrayListEditor(resizable=True)
        self.points.row_selected.connect(self._point_selected)
        self.points.values_changed.connect(self.values_changed)

        self.hard = QtWidgets.QComboBox()
        self.hard.addItems(['false', 'true'])
        self.hard.currentIndexChanged.connect(self.values_changed)
        self.hard.currentIndexChanged.connect(self.values_changed)

        self.add_row('Hard', self.hard)
        self.add_row('Points', self.points)
        self.old_selection = None

    def selection_changed(self):
        selection = self.document.selection
        skip = (
            selection.tool != Selection.PATH or
            selection.data is None or
            self.old_selection == selection.data or
            selection.data[0] is None)
        if skip:
            return
        self.old_selection = selection.data
        self.block_signals(True)
        path = self.document.data['paths'][selection.data[0]]
        self.points.set_values(path['points'])
        self.hard.setCurrentIndex(int(path['hard']))
        self.block_signals(False)

    def point_selected(self, row):
        self._point_selected(row)

    def _point_selected(self, row):
        if self.document.selection.tool != Selection.PATH:
            return
        if self.document.selection.data:
            self.document.selection.data = self.document.selection.data[0], row
            self.document.selection.changed.emit(self.parent())

    def values_changed(self, *_):
        if self.document.selection.tool != Selection.PATH:
            return
        index = self.document.selection.data[0]
        ol = self.document.data['paths'][index]
        ol.update(self.data())
        self.document.edited.emit()

    def data(self):
        return {
            'hard': bool(self.hard.currentIndex()),
            'points': self.points.values()}
