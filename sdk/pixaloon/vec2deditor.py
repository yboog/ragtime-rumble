from PySide6 import QtWidgets, QtCore


class IntVec2DListEditor(QtWidgets.QWidget):
    values_changed = QtCore.Signal()

    def values(self):
        return self.model.values()

    def __init__(self, values=None, resizable=False, parent=None):
        super().__init__(parent)

        self.model = IntVec2DListModel(values or [])
        self.model.values_changed.connect(self.values_changed.emit)

        self.view = QtWidgets.QListView()
        self.view.setModel(self.model)
        self.view.setItemDelegate(IntVec2DDelegate())
        self.view.setSelectionMode(QtWidgets.QListView.SingleSelection)
        self.view.setDragDropMode(QtWidgets.QListView.InternalMove)
        self.view.setDefaultDropAction(QtCore.Qt.MoveAction)
        self.view.setEditTriggers(
            QtWidgets.QListView.DoubleClicked |
            QtWidgets.QListView.EditKeyPressed |
            QtWidgets.QListView.SelectedClicked)

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


class IntVec2DListModel(QtCore.QAbstractListModel):
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

        x, y = self._values[index.row()]

        if role == QtCore.Qt.DisplayRole:
            return f"({x}, {y})"

        if role == QtCore.Qt.EditRole:
            return (x, y)

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
        return (
            QtCore.Qt.ItemIsEnabled |
            QtCore.Qt.ItemIsSelectable |
            QtCore.Qt.ItemIsEditable |
            QtCore.Qt.ItemIsDragEnabled |
            QtCore.Qt.ItemIsDropEnabled)

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


class Vec2DEditor(QtWidgets.QWidget):
    value_changed = QtCore.Signal()

    def __init__(self, minimum=-1_000_000, maximum=1_000_000, parent=None):
        super().__init__(parent)
        self.minimum = minimum
        self.maximum = maximum
        self.x_spin = QtWidgets.QSpinBox()
        self.y_spin = QtWidgets.QSpinBox()
        self.x_spin.valueChanged.connect(lambda _: self.value_changed.emit())
        self.y_spin.valueChanged.connect(lambda _: self.value_changed.emit())

        for spin in (self.x_spin, self.y_spin):
            spin.setRange(self.minimum, self.maximum)
            spin.setFrame(False)

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.x_spin)
        layout.addWidget(self.y_spin)

    def value(self):
        return self.x_spin.value(), self.y_spin.value()

    def set_value(self, vec):
        self.x_spin.setValue(vec[0])
        self.y_spin.setValue(vec[1])


class IntVec2DDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, minimum=-1_000_000, maximum=1_000_000, parent=None):
        super().__init__(parent)
        self.minimum = minimum
        self.maximum = maximum

    def createEditor(self, parent, option, index):
        widget = QtWidgets.QWidget(parent)

        x_spin = QtWidgets.QSpinBox(widget)
        y_spin = QtWidgets.QSpinBox(widget)

        for spin in (x_spin, y_spin):
            spin.setRange(self.minimum, self.maximum)
            spin.setFrame(False)

        layout = QtWidgets.QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(x_spin)
        layout.addWidget(y_spin)

        widget.x_spin = x_spin
        widget.y_spin = y_spin
        return widget

    def setEditorData(self, editor, index):
        x, y = index.data(QtCore.Qt.EditRole)
        editor.x_spin.setValue(x)
        editor.y_spin.setValue(y)

    def setModelData(self, editor, model, index):
        value = editor.x_spin.value(), editor.y_spin.value()
        model.setData(index, value, QtCore.Qt.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)

    editor = IntVec2DListEditor(
        values=[(10, 20), (42, -3), (1337, 9001)],
        resizable=True
    )
    editor.resize(300, 300)
    editor.values_changed.connect(
        lambda: print("Values:", editor.values())
    )
    editor.show()

    sys.exit(app.exec())
