from PySide6 import QtWidgets, QtCore


class RactListEditor(QtWidgets.QWidget):
    values_changed = QtCore.Signal()

    def values(self):
        return self.model.values()

    def __init__(self, values=None, resizable=False, parent=None):
        super().__init__(parent)

        self.model = IntListModel(values)
        self.model.values_changed.connect(self.values_changed.emit)

        self.view = QtWidgets.QListView()
        self.view.setModel(self.model)
        self.view.setItemDelegate(IntSpinBoxDelegate())
        self.view.setEditTriggers(
            QtWidgets.QListView.DoubleClicked |
            QtWidgets.QListView.EditKeyPressed)
        self.view.setDragDropMode(QtWidgets.QListView.InternalMove)
        self.view.setDefaultDropAction(QtCore.Qt.MoveAction)
        self.view.setSelectionMode(QtWidgets.QListView.SingleSelection)
        self.view.setEditTriggers(
            QtWidgets.QListView.CurrentChanged |
            QtWidgets.QListView.SelectedClicked |
            QtWidgets.QListView.EditKeyPressed)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.view)

        if not resizable:
            return
        self.add_btn = QtWidgets.QPushButton("➕ Add")
        self.remove_btn = QtWidgets.QPushButton("❌ Delete")

        btns = QtWidgets.QHBoxLayout()
        btns.addWidget(self.add_btn)
        btns.addWidget(self.remove_btn)
        btns.addStretch()
        layout.addLayout(btns)

        self.add_btn.clicked.connect(self.add_item)
        self.remove_btn.clicked.connect(self.remove_item)

    def clear(self):
        self.model.set_values([])

    def set_values(self, values):
        self.model.set_values(values)

    def add_item(self):
        row = self.model.rowCount()
        self.model.insertRows(row, 1)
        index = self.model.index(row)
        self.view.setCurrentIndex(index)
        self.view.edit(index)

    def remove_item(self):
        index = self.view.currentIndex()
        if index.isValid():
            self.model.removeRows(index.row(), 1)


class IntListModel(QtCore.QAbstractListModel):
    values_changed = QtCore.Signal()

    def __init__(self, values=None, parent=None):
        super().__init__(parent)
        self._values = values

    def rowCount(self, *_):
        if self._values is None:
            return 0
        return len(self._values)

    def set_values(self, values):
        self.layoutAboutToBeChanged.emit()
        self._values = values
        self.layoutChanged.emit()

    def data(self, index, role):
        if not index.isValid():
            return None

        if role in (QtCore.Qt.DisplayRole, QtCore.Qt.EditRole):
            return self._values[index.row()]

        return None

    def setData(self, index, value, role):
        if role != QtCore.Qt.EditRole:
            return False
        self._values[index.row()] = int(value)
        roles = [QtCore.Qt.DisplayRole, QtCore.Qt.EditRole]
        self.dataChanged.emit(index, index, roles)
        self.values_changed.emit()
        return True

    def flags(self, _):
        return (
            QtCore.Qt.ItemIsEnabled |
            QtCore.Qt.ItemIsSelectable |
            QtCore.Qt.ItemIsEditable |
            QtCore.Qt.ItemIsDragEnabled |
            QtCore.Qt.ItemIsDropEnabled)

    def insertRows(self, row, count, parent):
        self.beginInsertRows(parent, row, row + count - 1)
        for _ in range(count):
            self._values.insert(row, 0)
        self.endInsertRows()
        self.values_changed.emit()
        return True

    def removeRows(self, row, count, parent):
        self.beginRemoveRows(parent, row, row + count - 1)
        del self._values[row:row + count]
        self.endRemoveRows()
        self.values_changed.emit()
        return True

    def supportedDropActions(self):
        return QtCore.Qt.MoveAction

    def values(self):
        return self._values


class IntSpinBoxDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, minimum=-1_000_000, maximum=1_000_000, parent=None):
        super().__init__(parent)
        self.minimum = minimum
        self.maximum = maximum

    def createEditor(self, parent, option, index):
        editor = QtWidgets.QSpinBox(parent)
        editor.setRange(self.minimum, self.maximum)
        editor.setFrame(False)
        return editor

    def setEditorData(self, editor, index):
        editor.setValue(index.data(QtCore.Qt.EditRole))

    def setModelData(self, editor, model, index):
        model.setData(index, editor.value(), QtCore.Qt.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)

    editor = IntListEditor([10, 20, 42, 1337])
    editor.resize(300, 300)
    editor.values_changed.connect(lambda: print("Values:", editor.model.values()))
    editor.show()

    sys.exit(app.exec())
