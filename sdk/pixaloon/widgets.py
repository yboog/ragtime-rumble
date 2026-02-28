
from PySide6 import QtCore, QtWidgets


class GameTypesSelector(QtWidgets.QListWidget):
    edited = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        for text in ['basic', 'advanced']:
            item = QtWidgets.QListWidgetItem()
            item.setText(text)
            item.setCheckState(QtCore.Qt.Checked)
            self.addItem(item)
        self.itemChanged.connect(lambda _: self.edited.emit())

    def game_types(self):
        return [
            self.item(r).text() for r in range(self.count()) if
            self.item(r).checkState() == QtCore.Qt.Checked]

    def set_game_types(self, game_types):
        for r in range(self.count()):
            self.item(r).setCheckState(
                QtCore.Qt.Checked
                if self.item(r).text() in game_types else
                QtCore.Qt.Unchecked)


class BoolCombo(QtWidgets.QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.addItems(['false', 'true'])

    def state(self):
        return bool(self.currentIndex())

    def set_state(self, state):
        self.setCurrentIndex(int(state))