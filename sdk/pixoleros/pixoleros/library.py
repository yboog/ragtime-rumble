import os
from PySide6 import QtWidgets, QtCore


class LibraryTableView(QtWidgets.QTableView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setShowGrid(False)
        self.setWordWrap(False)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        scrollmode = QtWidgets.QAbstractItemView.ScrollPerPixel
        self.setVerticalScrollMode(scrollmode)
        self.setHorizontalScrollMode(scrollmode)
        mode = QtWidgets.QHeaderView.ResizeToContents
        self.verticalHeader().setSectionResizeMode(mode)
        self.verticalHeader().hide()
        self.horizontalHeader().setStretchLastSection(True)
        self.setEditTriggers(QtWidgets.QAbstractItemView.AllEditTriggers)

    def set_model(self, model):
        self.setModel(LibraryTableModel(model))


class LibraryTableModel(QtCore.QAbstractTableModel):
    HEADERS = 'File', 'Directory'

    def __init__(self, model):
        super().__init__()
        self.model = model

    def columnCount(self, _):
        return len(self.HEADERS) if self.model else 0

    def rowCount(self, _):
        return len(self.model.library) if self.model else 0

    def headerData(self, section, orientation, role):
        skip = (
            orientation != QtCore.Qt.Horizontal or
            role != QtCore.Qt.DisplayRole)
        if skip:
            return
        return self.HEADERS[section]

    def data(self, index, role):
        if role != QtCore.Qt.DisplayRole:
            return
        path = list(self.model.library.values())[index.row()].path
        if index.column() == 0:
            return os.path.basename(path)
        if index.column() == 1:
            return os.path.dirname(path)
