
from PySide6 import QtWidgets, QtCore
from pixaloon.path import relative_normpath


class FileLineEdit(QtWidgets.QWidget):
    edited = QtCore.Signal()

    def __init__(self, filters, document=None, parent=None):
        super().__init__(parent)
        self.document = document
        self.filters = filters

        self.file = QtWidgets.QLineEdit()
        self.file.textEdited.connect(self.edited.emit)
        self.browse = QtWidgets.QPushButton('📁')
        self.browse.released.connect(self.call_browse)

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.file)
        layout.addWidget(self.browse)

    def call_browse(self):
        filepath, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, 'Open file', None, filter=self.filters)
        if filepath is None:
            return
        self.file.setText(relative_normpath(filepath))
        self.edited.emit()

    def set_document(self, document):
        self.document = document

    def filepath(self):
        return self.file.text() or None

    def set_file(self, filepath):
        self.file.setText(filepath)


class FilesList(QtWidgets.QWidget):
    def __init__(self, key, filters, parent=None):
        super().__init__(parent)
        self.filters = filters
        self.model = RessourceFilesListModel(key)
        self.list = QtWidgets.QListView()
        self.list.setModel(self.model)
        self.add = QtWidgets.QPushButton('+')
        self.add.released.connect(self.add_files)
        self.remove = QtWidgets.QPushButton('🗑')
        self.remove.released.connect(self.remove_selection)
        toolbar = QtWidgets.QToolBar()
        toolbar.addWidget(self.add)
        toolbar.addWidget(self.remove)
        tb_layout = QtWidgets.QHBoxLayout()
        tb_layout.setContentsMargins(0, 0, 0, 0)
        tb_layout.addStretch()
        tb_layout.addWidget(toolbar)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.list)
        layout.addLayout(tb_layout)

    def remove_selection(self):
        rows = [i.row() for i in self.list.selectedIndexes()]
        rows.sort(reverse=True)
        self.model.layoutAboutToBeChanged.emit()
        for row in rows:
            del self.model.document.data[self.model.key][row]
        self.model.layoutChanged.emit()

    def add_files(self):
        files, _ = QtWidgets.QFileDialog.getOpenFileNames(
            self, caption='Open', filter=self.filters)
        if not files:
            return
        files = [relative_normpath(f, self.model.document) for f in files]
        self.model.layoutAboutToBeChanged.emit()
        self.model.document.data[self.model.key].extend(files)
        self.model.layoutChanged.emit()

    def set_document(self, document):
        self.model.layoutAboutToBeChanged.emit()
        self.model.document = document
        self.model.layoutChanged.emit()


class RessourceFilesListModel(QtCore.QAbstractListModel):
    def __init__(self, key):
        super().__init__()
        self.key = key
        self.document = None

    def rowCount(self, *_):
        if self.document is None:
            return 0
        return len(self.document.data[self.key])

    def data(self, index, role):
        if not index.isValid():
            return
        if role == QtCore.Qt.DisplayRole:
            return self.document.data[self.key][index.row()]