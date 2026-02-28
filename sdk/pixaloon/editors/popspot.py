from pixaloon.selection import Selection

from pixaloon.editors.base import BaseEditor
from pixaloon.widgets import GameTypesSelector


class PopspotEditor(BaseEditor):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.gametypes = GameTypesSelector()
        self.gametypes.edited.connect(self.values_changed)
        self.add_row('Game types', self.gametypes)

    def selection_changed(self):
        selection = self.document.selection
        if selection.tool != Selection.POPSPOT or not selection.data:
            return
        self.block_signals(True)
        popspot = self.document.data['popspots'][selection.data[-1]]
        self.gametypes.set_game_types(popspot["gametypes"])

        self.block_signals(False)

    def values_changed(self, *_):
        if self.document.selection.tool != Selection.POPSPOT:
            return
        for index in self.document.selection.data:
            popspot = self.document.data['popspots'][index]
            popspot['gametypes'] = self.gametypes.game_types()
        self.document.edited.emit()