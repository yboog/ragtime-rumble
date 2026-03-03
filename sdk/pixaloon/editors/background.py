from pixaloon.path import relative_normpath
from pixaloon.selection import Selection
from pixaloon.intarrayeditor import IntArrayEditor
from pixaloon.filewidget import FileLineEdit
from pixaloon.editors.base import BaseEditor
from pixaloon.widgets import BlendmodeSelector

class BackgroundEditor(BaseEditor):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.document = None

        self.blendmode = BlendmodeSelector()
        self.blendmode.currentIndexChanged.connect(self.values_changed)

        self.image_filepath = FileLineEdit(self.document, '*.png')
        self.image_filepath.edited.connect(self.values_changed)

        self.position = IntArrayEditor()
        self.position.value_changed.connect(self.values_changed)

        self.add_row('Position', self.position)
        self.add_row('Image', self.image_filepath)
        self.add_row('Blend mode', self.blendmode)

    def selection_changed(self):
        selection = self.document.selection
        if selection.tool != Selection.BACKGROUND or selection.data is None:
            return
        self.image_filepath.document = self.document
        index = self.document.selection.data
        bg = self.document.data['backgrounds'][index]
        self.block_signals(True)
        self.position.set_value(bg['position'])
        fp = relative_normpath(bg["file"], self.document)
        self.image_filepath.set_file(fp)
        self.blendmode.set_blendmode(bg['blendmode'])
        self.block_signals(False)

    def values_changed(self, *_):
        if self.document.selection.tool != Selection.BACKGROUND:
            return
        index = self.document.selection.data
        ol = self.document.data['backgrounds'][index]
        ol.update(self.data())
        self.document.edited.emit()

    def data(self):
        fp = relative_normpath(self.image_filepath.filepath(), self.document)
        return {
            'file': fp,
            'blendmode': self.blendmode.blendmode(),
            'position': self.position.value()}