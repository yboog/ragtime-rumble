import os
from PySide6 import QtWidgets, QtCore, QtGui


FRAME_OUT_DATE_COLOR = (200, 100, 0)
FRAME_NOT_FOUND_COLOR = (200, 50, 50)
FRAME_UP_TO_DATE_COLOR = (50, 200, 50)


class LibraryTableView(QtWidgets.QTableView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.delegate = StatusDelegate()
        self.setItemDelegateForColumn(0, self.delegate)
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

    def set_document(self, model):
        model = LibraryTableModel(model)
        self.setModel(model)
        self.delegate.model = model
        self.horizontalHeader().resizeSection(0, 10)


class StatusDelegate(QtWidgets.QStyledItemDelegate):

    def __init__(self):
        super().__init__()
        self.model = None

    def paint(self, painter, option, index):
        if not self.model:
            return
        image = self.model.data(index, QtCore.Qt.UserRole)
        color = self.get_frame_color(image)
        painter.setBrush(color)
        painter.setPen(QtCore.Qt.NoPen)
        painter.drawEllipse(option.rect.center(), 7, 7)

    def get_frame_color(self, image):
        if not image.reference_exists:
            return QtGui.QColor(*FRAME_NOT_FOUND_COLOR)
        if image.file_modified:
            return QtGui.QColor(*FRAME_OUT_DATE_COLOR)
        return QtGui.QColor(*FRAME_UP_TO_DATE_COLOR)


class LibraryTableModel(QtCore.QAbstractTableModel):
    HEADERS = '', 'File', 'Directory'

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

    def data(self, index, role=QtCore.Qt.UserRole):
        if role == QtCore.Qt.UserRole:
            return list(self.model.library.values())[index.row()]

        if role != QtCore.Qt.DisplayRole:
            return
        path = list(self.model.library.values())[index.row()].path
        if index.column() == 1:
            return os.path.basename(path)
        if index.column() == 2:
            return os.path.dirname(path)
