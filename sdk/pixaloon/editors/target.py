from PySide6 import QtWidgets
from pixaloon.selection import Selection
from pixaloon.intlisteditor import IntListEditor
from pixaloon.intarrayeditor import IntArrayListEditor
from pixaloon.editors.base import BaseEditor


class TargetEditor(BaseEditor):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.weight = QtWidgets.QSpinBox()
        self.weight.setMaximum(1_000_000_000)

        self.origin = IntListEditor()
        self.origin.values_changed.connect(self.values_changed)

        self.destinations = IntArrayListEditor(resizable=True, array_lenght=4)
        self.destinations.row_selected.connect(self.destination_selected)
        self.destinations.values_changed.connect(self.values_changed)

        self.add_row('Weight', self.weight)
        self.add_row('Origin', self.origin)
        self.add_row('Destinations', self.destinations)
        self.old_selection = None

    def destination_selected(self, row):
        selection = self.document.selection
        if selection.tool != Selection.TARGET or selection.data is None:
            return
        if selection.data:
            selection.data = selection.data[0], row
            selection.changed.emit(self.parent())

    def selection_changed(self):
        selection = self.document.selection
        skip = (
            selection.tool != Selection.TARGET or
            selection.data is None or
            self.old_selection == selection.data or
            selection.data[0] is None)
        if skip:
            return
        self.old_selection = self.document.selection.data
        self.block_signals(True)
        index = self.document.selection.data[0]
        target = self.document.data['targets'][index]
        self.weight.setValue(target['weight'])
        self.origin.set_values(target['origin'])
        self.destinations.set_values(target['destinations'])
        self.block_signals(False)

    def values_changed(self):
        index = self.document.selection.data[0]
        target = self.document.data['targets'][index]
        target.update({
            'origin': self.origin.values(),
            'weight': self.weight.value()})
        self.document.edited.emit()