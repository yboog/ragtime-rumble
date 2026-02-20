from PySide6 import QtWidgets, QtCore
from pixaloon.qtutils import get_separator


class BaseEditor(QtWidgets.QWidget):
    changed = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.document = None
        self.editors = []

        self.current_form = QtWidgets.QFormLayout()
        self.current_form.setSpacing(0)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addLayout(self.current_form)

    def adjust_form_label_size(self):
        margins = QtWidgets.QLabel().contentsMargins()
        margins.setRight(8)
        alignment = QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
        for label in self.findChildren(QtWidgets.QLabel):
            if isinstance(label, QtWidgets.QLabel):
                label.setAlignment(alignment)
                label.setContentsMargins(margins)
                label.setFixedWidth(100)

    def block_signals(self, state):
        for editor in self.editors:
            editor.blockSignals(state)

    def set_document(self, document):
        self.document = document
        self.document.selection.changed.connect(self.selection_changed)

    def selection_changed(self):
        """To implement in subclasses"""
        raise NotImplementedError()

    def values_changed(self):
        if not self.document:
            return
        self.document.edited.emit()

    def add_stretch(self):
        self.layout.addStretch()

    def add_row(self, name, widget):
        self.current_form.addRow(f'{name}  ', widget)
        self.editors.append(widget)

    def add_separator(self):
        self.current_form = QtWidgets.QFormLayout()
        self.current_form.setSpacing(0)

        self.layout.addWidget(get_separator())
        self.layout.addLayout(self.current_form)
