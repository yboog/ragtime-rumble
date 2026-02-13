
from pixaloon.selection import Selection
from pixaloon.intlisteditor import IntListEditor
from pixaloon.vec2deditor import IntVec2DListEditor
from pixaloon.editors.base import BaseEditor


class NoGoZoneEditor(BaseEditor):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.document = None
        self.rect = IntListEditor()
        self.rect.values_changed.connect(self.values_changed)
        self.add_row('Rect', self.rect)

    def selection_changed(self):
        if self.document.selection.tool != Selection.NO_GO_ZONE:
            return self.rect.clear()
        index = self.document.selection.data
        values = self.document.data['no_go_zones'][index]
        self.rect.set_values(values)


class WallsEditor(BaseEditor):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.document = None
        self.polygon = IntVec2DListEditor(resizable=True)
        self.polygon.values_changed.connect(self.values_changed)
        self.add_row('Polygon', self.polygon)

    def values_changed(self):
        if not self.document:
            return
        self.document.edited.emit()

    def selection_changed(self):
        if self.document.selection.tool != Selection.WALL:
            return self.polygon.clear()
        index = self.document.selection.data
        values = self.document.data['walls'][index]
        self.polygon.set_values(values)


class FenceEditor(BaseEditor):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.document = None
        self.rect = IntListEditor()
        self.rect.values_changed.connect(self.values_changed)
        self.add_row('Rect', self.rect)

    def selection_changed(self):
        if self.document.selection.tool != Selection.FENCE:
            return self.rect.clear()
        index = self.document.selection.data
        values = self.document.data['fences'][index]
        self.rect.set_values(values)

