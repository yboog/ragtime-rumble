from PySide6 import QtWidgets
from pixaloon.selection import Selection
from pixaloon.intlisteditor import IntListEditor
from pixaloon.intarrayeditor import IntArrayListEditor
from pixaloon.editors.base import BaseEditor


class NoGoZoneEditor(BaseEditor):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.rect = IntListEditor()
        self.rect.values_changed.connect(self.values_changed)
        self.add_row('Rect', self.rect)

    def selection_changed(self):
        selection = self.document.selection
        if selection.tool != Selection.NO_GO_ZONE or selection.data is None:
            return self.rect.clear()
        index = self.document.selection.data
        values = self.document.data['no_go_zones'][index]
        self.rect.set_values(values)


class WallsEditor(BaseEditor):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.polygon = IntArrayListEditor(resizable=True)
        self.polygon.values_changed.connect(self.values_changed)
        self.add_row('Polygon', self.polygon)

    def values_changed(self):
        if not self.document:
            return
        self.document.edited.emit()

    def selection_changed(self):
        selection = self.document.selection
        if selection.tool != Selection.WALL or selection.data is None:
            return self.polygon.clear()
        index = self.document.selection.data
        values = self.document.data['walls'][index]
        self.polygon.set_values(values)


class FenceEditor(BaseEditor):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.rect = IntListEditor()
        self.rect.values_changed.connect(self.values_changed)
        self.add_row('Rect', self.rect)

    def selection_changed(self):
        selection = self.document.selection
        if selection.tool != Selection.FENCE or selection.data is None:
            return self.rect.clear()
        index = self.document.selection.data
        values = self.document.data['fences'][index]
        self.rect.set_values(values)


class StairEditor(BaseEditor):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.inclination = QtWidgets.QDoubleSpinBox()
        self.inclination.setRange(-1, 1)
        self.inclination.valueChanged.connect(self.values_changed)

        self.rect = IntListEditor()
        self.rect.values_changed.connect(self.values_changed)

        self.add_row('Inclination', self.inclination)
        self.add_row('Rect', self.rect)

    def selection_changed(self):
        selection = self.document.selection
        if selection.tool != Selection.STAIR or selection.data is None:
            return self.rect.clear()

        self.block_signals(True)
        index = self.document.selection.data
        stair = self.document.data['stairs'][index]
        self.inclination.setValue(stair['inclination'])
        self.rect.set_values(stair['zone'])
        self.block_signals(False)

    def values_changed(self, *_):
        index = self.document.selection.data
        stair = self.document.data['stairs'][index]
        stair.update({
            'zone': self.rect.values(),
            'inclination': self.inclination.value()})
        self.document.edited.emit()
