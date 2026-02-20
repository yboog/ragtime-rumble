

from PySide6 import QtWidgets, QtCore


class OptionsEditor(QtWidgets.QWidget):
    option_set = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.document = None
        self.veil_alpha = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.veil_alpha.valueChanged.connect(self.set_veil_alpha)
        self.veil_alpha.setMinimum(0)
        self.veil_alpha.setMaximum(255)
        layout = QtWidgets.QFormLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addRow('Veil', self.veil_alpha)

    def set_veil_alpha(self, value):
        self.document.veil_alpha = value
        self.option_set.emit()

    def set_document(self, document):
        self.document = document
        self.veil_alpha.setValue(document.veil_alpha)
