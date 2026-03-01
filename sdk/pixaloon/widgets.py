
from PySide6 import QtCore, QtWidgets, QtGui
from pixaloon.io import list_tiles, get_tile


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


class TileSelector(QtWidgets.QWidget):
    edited = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tiles = QtWidgets.QComboBox()
        self.tiles.addItem('Color (No tile)')
        self.tiles.addItems(list_tiles())
        self.tiles.currentIndexChanged.connect(self.set_current_tile)
        self.tiles.currentIndexChanged.connect(lambda _: self.edited.emit())
        self.display = QtWidgets.QLabel()
        self.display.setFixedSize(QtCore.QSize(64, 64))

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.tiles, alignment=QtCore.Qt.AlignTop)
        layout.addWidget(self.display)

        self.set_current_tile()

    def set_current_tile(self):
        if self.tiles.currentIndex() == 0:
            pixmap = QtGui.QPixmap(QtCore.QSize(50, 50))
            pixmap.fill(QtGui.QColor('purple'))
            self.display.setPixmap(pixmap)
            return
        tile = self.tiles.currentText()
        self.display.setPixmap(QtGui.QPixmap.fromImage(get_tile(tile)))

    def set_tile(self, tile):
        self.blockSignals(True)
        if tile is None:
            self.tiles.setCurrentIndex(0)
            return
        self.tiles.setCurrentText(tile)
        self.blockSignals(False)

    def tile(self):
        if self.tiles.currentIndex() == 0:
            return None
        return self.tiles.currentText()