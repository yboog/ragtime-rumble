from PySide6 import QtWidgets, QtCore


class IntArrayListEditor(QtWidgets.QWidget):
    values_changed = QtCore.Signal()
    row_selected = QtCore.Signal(int)

    def values(self):
        return self.model.values()

    def __init__(
            self,
            values=None,
            resizable=False,
            array_lenght=2,
            parent=None):
        super().__init__(parent)

        self.model = IntArrayListModel(values or [])
        self.model.values_changed.connect(self.values_changed.emit)

        self.view = QtWidgets.QListView()
        self.view.setModel(self.model)
        self.view.setItemDelegate(IntArrayDelegate(array_lenght=array_lenght))
        self.view.setSelectionMode(QtWidgets.QListView.SingleSelection)
        self.view.setEditTriggers(
            QtWidgets.QListView.DoubleClicked |
            QtWidgets.QListView.EditKeyPressed |
            QtWidgets.QListView.SelectedClicked)
        self.view.selectionModel().selectionChanged.connect(self.point_selected)

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

    def point_selected(self, selected, _):
        row = next(iter(selected.indexes()), None)
        if row is None:
            return
        self.row_selected.emit(row.row())

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


class IntArrayListModel(QtCore.QAbstractListModel):
    values_changed = QtCore.Signal()

    def __init__(self, values=None, parent=None):
        super().__init__(parent)
        self._values = values or []

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self._values)

    def set_values(self, values):
        self.beginResetModel()
        self._values = values
        self.endResetModel()
        self.values_changed.emit()

    def data(self, index, role):
        if not index.isValid():
            return None
        values = self._values[index.row()]
        if role == QtCore.Qt.DisplayRole:
            return f"({', '.join([str(v) for v in values])})"

        if role == QtCore.Qt.EditRole:
            return values

        return None

    def setData(self, index, value, role):
        if role != QtCore.Qt.EditRole:
            return False

        self._values[index.row()] = tuple(value)
        self.dataChanged.emit(index, index, [
            QtCore.Qt.DisplayRole,
            QtCore.Qt.EditRole])
        self.values_changed.emit()
        return True

    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.ItemIsEnabled

        return (
            QtCore.Qt.ItemIsEnabled |
            QtCore.Qt.ItemIsSelectable |
            QtCore.Qt.ItemIsEditable
        )

    def insertRows(self, row, count, parent=QtCore.QModelIndex()):
        self.beginInsertRows(parent, row, row + count - 1)
        for _ in range(count):
            self._values.insert(row, (0, 0))
        self.endInsertRows()
        self.values_changed.emit()
        return True

    def removeRows(self, row, count, parent=QtCore.QModelIndex()):
        self.beginRemoveRows(parent, row, row + count - 1)
        del self._values[row:row + count]
        self.endRemoveRows()
        self.values_changed.emit()
        return True

    def supportedDropActions(self):
        return QtCore.Qt.MoveAction

    def values(self):
        return self._values


class IntArrayEditor(QtWidgets.QWidget):
    value_changed = QtCore.Signal()

    def __init__(
            self,
            minimum=-1_000_000,
            maximum=1_000_000,
            array_lenght=2,
            parent=None):

        super().__init__(parent)
        self.minimum = minimum
        self.maximum = maximum
        self.spins = []
        for _ in range(array_lenght):
            spin = QtWidgets.QSpinBox()
            spin.valueChanged.connect(lambda _: self.value_changed.emit())
            spin.setRange(self.minimum, self.maximum)
            spin.setFrame(False)
            self.spins.append(spin)

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        for spin in self.spins:
            layout.addWidget(spin)

    def value(self):
        return [spin.value() for spin in self.spins]

    def set_value(self, values):
        for spin, value in zip(self.spins, values):
            spin.setValue(value)


class IntArrayDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(
            self, minimum=-1_000_000, maximum=1_000_000,
            array_lenght=2, parent=None):
        super().__init__(parent)
        self.array_lenght = array_lenght
        self.minimum = minimum
        self.maximum = maximum

    def createEditor(self, parent, option, index):
        widget = QtWidgets.QWidget(parent)

        spins = []
        for _ in range(self.array_lenght):
            spin = QtWidgets.QSpinBox()
            spin.setRange(self.minimum, self.maximum)
            spin.setFrame(False)
            spins.append(spin)

        layout = QtWidgets.QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        for spin in spins:
            layout.addWidget(spin)

        widget.spins = spins
        return widget

    def setEditorData(self, editor, index):
        values = index.data(QtCore.Qt.EditRole)
        for spin, value in zip(editor.spins, values):
            spin.setValue(value)

    def setModelData(self, editor, model, index):
        value = [spin.value() for spin in editor.spins]
        model.setData(index, value, QtCore.Qt.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)

    editor = IntArrayListEditor(
        values=[(10, 20), (42, -3), (1337, 9001)],
        resizable=True
    )
    editor.resize(300, 300)
    editor.values_changed.connect(
        lambda: print("Values:", editor.values())
    )
    editor.show()

    sys.exit(app.exec())
