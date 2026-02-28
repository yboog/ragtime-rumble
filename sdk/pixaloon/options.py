

from PySide6 import QtWidgets, QtCore
from pixaloon.widgets import GameTypesSelector
from pixaloon.document import Document


class OptionsEditor(QtWidgets.QWidget):
    option_set = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.document: Document = None
        self.veil_alpha = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.veil_alpha.valueChanged.connect(self.set_veil_alpha)
        self.veil_alpha.setMinimum(0)
        self.veil_alpha.setMaximum(255)
        self.gametypes_display = GameTypesSelector()
        self.gametypes_display.edited.connect(self.gametypes_display_changed)

        layout = QtWidgets.QFormLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addRow('Veil', self.veil_alpha)
        layout.addRow('Gametypes display', self.gametypes_display)

    def gametypes_display_changed(self):
        gametypes = self.gametypes_display.game_types()
        self.document.gametypes_display_filters = gametypes
        self.option_set.emit()

    def set_veil_alpha(self, value):
        self.document.veil_alpha = value
        self.option_set.emit()

    def set_document(self, document):
        self.document = document
        self.veil_alpha.setValue(document.veil_alpha)
        self.gametypes_display.set_game_types(
            document.gametypes_display_filters)
