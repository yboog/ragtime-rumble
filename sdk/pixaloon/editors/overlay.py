from PySide6 import QtWidgets
from pixaloon.path import relative_normpath
from pixaloon.selection import Selection
from pixaloon.intarrayeditor import IntArrayEditor
from pixaloon.filewidget import FileLineEdit
from pixaloon.editors.base import BaseEditor


class OverlayEditor(BaseEditor):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.document = None

        self.image_filepath = FileLineEdit(self.document, '*.png')
        self.position = IntArrayEditor()
        self.position.value_changed.connect(self.values_changed)
        self.switch = QtWidgets.QSpinBox()
        self.switch.setMaximum(1_000_000_000)
        self.switch.setMinimum(-1_000_000_000)
        self.switch.valueChanged.connect(self.values_changed)
        self.image_filepath.edited.connect(self.values_changed)

        self.add_row('Position', self.position)
        self.add_row('Y switch', self.switch)
        self.add_row('Image', self.image_filepath)

    def selection_changed(self):
        selection = self.document.selection
        if selection.tool != Selection.OVERLAY or selection.data is None:
            return
        self.image_filepath.document = self.document
        index = self.document.selection.data
        ol = self.document.data['overlays'][index]
        self.block_signals(True)
        self.position.set_value(ol['position'])
        fp = relative_normpath(ol["file"], self.document)
        self.image_filepath.set_file(fp)
        self.switch.setValue(ol['y'])
        self.block_signals(False)

    def values_changed(self, *_):
        if self.document.selection.tool != Selection.OVERLAY:
            return
        index = self.document.selection.data
        ol = self.document.data['overlays'][index]
        ol.update(self.data())
        self.document.edited.emit()

    def data(self):
        fp = relative_normpath(self.image_filepath.filepath(), self.document)
        return {
            'type': 'props',
            'file': fp,
            'y': self.switch.value(),
            'position': self.position.value()}