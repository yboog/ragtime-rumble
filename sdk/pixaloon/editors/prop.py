from pixaloon.selection import Selection

from pixaloon.path import relative_normpath
from pixaloon.filewidget import FileLineEdit
from pixaloon.intlisteditor import IntListEditor
from pixaloon.intarrayeditor import IntArrayEditor
from pixaloon.editors.base import BaseEditor
from pixaloon.widgets import GameTypesSelector, BoolCombo, BlendmodeSelector


class PropEditor(BaseEditor):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.blendmode = BlendmodeSelector()
        self.blendmode.currentIndexChanged.connect(self.values_changed)

        self.gametypes = GameTypesSelector()
        self.gametypes.edited.connect(self.values_changed)

        self.visible_at_dispatch = BoolCombo()
        self.visible_at_dispatch.currentIndexChanged.connect(
            self.values_changed)

        self.image_filepath = FileLineEdit(self.document, '*.png')

        self.position = IntArrayEditor()
        self.position.value_changed.connect(self.values_changed)

        self.center = IntArrayEditor()
        self.center.value_changed.connect(self.values_changed)

        self.box = IntListEditor()
        self.box.values_changed.connect(self.values_changed)

        self.add_row('Game types', self.gametypes)
        self.add_row('Image', self.image_filepath)
        self.add_row('Blend mode', self.blendmode)
        self.add_row('Visible at dispatch', self.visible_at_dispatch)
        self.add_separator()
        self.add_row('Position', self.position)
        self.add_row('Center', self.center)
        self.add_row('Hitbox', self.box)

    def selection_changed(self):
        selection = self.document.selection
        if selection.tool != Selection.PROP or selection.data is None:
            return
        self.image_filepath.document = self.document
        index = self.document.selection.data
        prop = self.document.data['props'][index]
        self.block_signals(True)

        self.blendmode.set_blendmode(prop['blendmode'])
        self.box.set_values(prop['box'])
        self.gametypes.set_game_types(prop['gametypes'])
        self.position.set_value(prop['position'])
        self.center.set_value(prop['center'])
        fp = relative_normpath(prop["file"], self.document)
        self.image_filepath.set_file(fp)
        self.visible_at_dispatch.set_state(prop["visible_at_dispatch"])

        self.block_signals(False)

    def values_changed(self, *_):
        if self.document.selection.tool != Selection.PROP:
            return
        index = self.document.selection.data
        prop = self.document.data['props'][index]
        prop.update(self.data())
        self.document.edited.emit()

    def data(self):
        fp = relative_normpath(self.image_filepath.filepath(), self.document)
        return {
            'gametypes': self.gametypes.game_types(),
            'blendmode': self.blendmode.blendmode(),
            'visible_at_dispatch': self.visible_at_dispatch.state(),
            'file': fp,
            'center': self.center.value(),
            'position': self.position.value(),
            'box': self.box.values()}