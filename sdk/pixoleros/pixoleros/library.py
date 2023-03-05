import time
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
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.call_context_menu)
        self.context_menu = None
        self.timer = QtCore.QBasicTimer()
        self.timer.start(1000, self)
        self.time = time.time()

    def timerEvent(self, _):
        if not self.model() or not self.model().document:
            return
        self.model().layoutAboutToBeChanged.emit()
        for image in self.model().document.library.values():
            image.refresh()
        self.model().layoutChanged.emit()

    def set_document(self, model):
        model = LibraryTableModel(model)
        self.setModel(model)
        self.delegate.model = model
        self.horizontalHeader().resizeSection(0, 10)

    def call_context_menu(self, point):
        indexes = self.selectionModel().selectedRows()
        all_images = list(self.model().document.library.values())
        images = [all_images[i.row()] for i in indexes]
        self.context_menu = _ContextMenu(images, all_images)
        self.context_menu.exec(self.mapToGlobal(point))


class _ContextMenu(QtWidgets.QMenu):
    def __init__(self, images, all_images, parent=None):
        super().__init__(parent=parent)
        self.images = images
        self.all_images = all_images
        self.reload = QtGui.QAction('Reload', self)
        self.reload.triggered.connect(self.call_reload)
        self.repath = QtGui.QAction('Repath', self)
        self.repath.triggered.connect(self.call_repath)
        self.reload_all = QtGui.QAction('Reload all', self)
        self.reload_all.triggered.connect(self.call_reload_all)
        self.repath_all = QtGui.QAction('Repath all', self)
        self.repath_all.triggered.connect(self.call_repath_all)
        self.addAction(self.reload)
        self.addAction(self.repath)
        self.addSeparator()
        self.addAction(self.reload_all)
        self.addAction(self.repath_all)

    def call_reload(self):
        for image in self.images:
            image.reload()

    def call_repath(self):
        self.dialog = RepathDialog(self.images)
        self.dialog.exec()

    def call_reload_all(self):
        for image in self.all_images:
            image.reload()

    def call_repath_all(self):
        self.dialog = RepathDialog(self.all_images)
        self.dialog.exec()


def _split_path(path):
    items = []
    path, item = os.path.split(path)
    while item:
        items.append(item.strip('/\\'))
        path, item = os.path.split(path)
    items.append(path)
    return list(reversed(items))


def _common_hierarchy(splitted_paths):
    result = []
    for elements in zip(*splitted_paths):
        if len(set(elements)) != 1:
            break
        result.append(elements[0])
    return result


def _uncommon_directories(root, splitted_paths):
    result = []
    for splitted_path in splitted_paths:
        if splitted_path[len(root):] not in result and splitted_path[len(root):]:
            result.append(splitted_path[len(root):])
    return result


class RepathDialog(QtWidgets.QDialog):
    def __init__(self, images, parent=None):
        super().__init__(parent=parent)
        self.setWindowTitle('Change multiple images path')
        self.images = images
        self.splitted_paths = [
            _split_path(os.path.dirname(img.path)) for img in images]
        layout = QtWidgets.QVBoxLayout(self)

        self.common_hierarchy = _common_hierarchy(self.splitted_paths)
        if not self.common_hierarchy:
            layout.addWidget(QtWidgets.QLabel('No common root found'))
            button = QtWidgets.QPushButton('Cancel')
            button.released.connect(self.reject)
            layout.addWidget(layout)
            layout.addWidget(button)

        layout.addWidget(QtWidgets.QLabel('Common root'))
        self.root = QtWidgets.QLineEdit(os.path.join(*self.common_hierarchy))
        layout.addWidget(self.root)

        directories = _uncommon_directories(
            self.common_hierarchy, self.splitted_paths)
        self.lineedits = []

        if directories:
            layout.addWidget(QtWidgets.QLabel('Sub roots found'))
            for folders in directories:
                lineedit = QtWidgets.QLineEdit(os.path.join(*folders))
                lineedit.folders = folders
                layout.addWidget(lineedit)
                self.lineedits.append(lineedit)

        ok = QtWidgets.QPushButton('Apply')
        ok.released.connect(self.repath)
        cancel = QtWidgets.QPushButton('Cancel')
        cancel.released.connect(self.reject)

        layout.addStretch()
        buttons_layout = QtWidgets.QHBoxLayout()
        buttons_layout.addStretch()
        buttons_layout.addWidget(ok)
        buttons_layout.addWidget(cancel)
        layout.addLayout(buttons_layout)

    def repath(self):
        if not self.lineedits:
            for image in self.images:
                filename = os.path.basename(image.path)
                image.path = os.path.join(self.root.text(), filename)
                image.refresh()
            return self.accept()

        for image, folders in zip(self.images, self.splitted_paths):
            for lineedit in self.lineedits:
                if folders[-len(lineedit.folders):] == lineedit.folders:
                    filename = os.path.basename(image.path)
                    end = lineedit.folders + [filename]
                    image.path = os.path.join(self.root.text(), *end)
                    image.refresh()
        self.accept()


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

    def __init__(self, document):
        super().__init__()
        self.document = document

    def columnCount(self, _):
        return len(self.HEADERS) if self.document else 0

    def rowCount(self, _):
        return len(self.document.library) if self.document else 0

    def headerData(self, section, orientation, role):
        skip = (
            orientation != QtCore.Qt.Horizontal or
            role != QtCore.Qt.DisplayRole)
        if skip:
            return
        return self.HEADERS[section]

    def data(self, index, role=QtCore.Qt.UserRole):
        if role == QtCore.Qt.UserRole:
            return list(self.document.library.values())[index.row()]

        if role != QtCore.Qt.DisplayRole:
            return
        path = list(self.document.library.values())[index.row()].path
        if index.column() == 1:
            return os.path.basename(path)
        if index.column() == 2:
            return os.path.dirname(path)
