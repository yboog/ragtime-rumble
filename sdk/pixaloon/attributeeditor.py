

from PySide6 import QtWidgets
from pixaloon.editors.walls import NoGoZoneEditor, WallsEditor, FenceEditor
from pixaloon.editors.interaction import InterationEditor
from pixaloon.selection import Selection


class AttributeEditor(QtWidgets.QWidget):
    def __init__(self, document=None, parent=None):
        super().__init__(parent)
        self.document = document
        self.current_editor = QtWidgets.QWidget()
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.current_editor)

    def set_document(self, document):
        self.document = document
        self.document.selection.changed.connect(self.selection_changed)
        self.selection_changed()

    def selection_changed(self):
        cls = {
            Selection.NO_GO_ZONE: NoGoZoneEditor,
            Selection.FENCE: FenceEditor,
            Selection.INTERACTION: InterationEditor,
            Selection.WALL: WallsEditor}.get(
                self.document.selection.tool, QtWidgets.QWidget)
        if type(self.current_editor) == cls:
            if hasattr(self.current_editor, 'selection_changed'):
                self.current_editor.selection_changed()
            return
        if self.current_editor is not None:
            self.layout.removeWidget(self.current_editor)
            self.current_editor.deleteLater()

        self.current_editor = cls()
        if hasattr(self.current_editor, 'set_document'):
            self.current_editor.set_document(self.document)
            self.current_editor.selection_changed()
        self.layout.addWidget(self.current_editor)
