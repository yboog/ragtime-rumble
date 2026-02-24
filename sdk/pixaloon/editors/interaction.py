from PySide6 import QtWidgets, QtCore
from pixaloon.editors.base import BaseEditor
from pixaloon.intlisteditor import IntListEditor
from pixaloon.filewidget import FileLineEdit
from pixaloon.selection import Selection
from pixaloon.intarrayeditor import IntArrayEditor


class InteractionEditor(BaseEditor):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.play_once = QtWidgets.QComboBox()
        self.play_once.addItems(['false', 'true'])
        self.play_once.currentIndexChanged.connect(self.data_edited)

        self.busy = QtWidgets.QComboBox()
        self.busy.addItems(['false', 'true'])
        self.busy.currentIndexChanged.connect(self.data_edited)

        self.lockable = QtWidgets.QComboBox()
        self.lockable.addItems(['false', 'true'])
        self.lockable.currentIndexChanged.connect(self.data_edited)

        self.action = QtWidgets.QComboBox()
        self.action.addItems(['bet', 'balcony', 'order','poker', 'startup'])
        self.action.currentIndexChanged.connect(self.data_edited)

        self.target = IntArrayEditor()
        self.target.value_changed.connect(self.data_edited)

        self.attraction = IntListEditor()
        self.attraction.values_changed.connect(self.data_edited)

        self.zone = IntListEditor()
        self.zone.values_changed.connect(self.data_edited)

        self.direction = QtWidgets.QComboBox()
        self.direction.addItems(['left', 'right', 'up', 'down'])
        self.direction.currentIndexChanged.connect(self.data_edited)

        self.id = QtWidgets.QLineEdit()
        self.id.textEdited.connect(self.data_edited)

        self.insound = FileLineEdit(self.document, '*.wav')
        self.insound.edited.connect(self.data_edited)
        self.outsound = FileLineEdit(self.document, '*.wav')
        self.outsound.edited.connect(self.data_edited)

        self.gametypes = GameTypesSelector()
        self.gametypes.edited.connect(self.data_edited)

        self.add_row('Game types', self.gametypes)
        self.add_row('ID', self.id)
        self.add_row('Action', self.action)
        self.add_row('Target', self.target)
        self.add_row('Direction', self.direction)
        self.add_row('Interaction zone', self.zone)
        self.add_row('NPC attraction zone', self.attraction)
        self.add_separator()
        self.add_row('Start sound', self.insound)
        self.add_row('Leave sourd', self.outsound)
        self.add_separator()
        self.add_row('Play once', self.play_once)
        self.add_row('Busy', self.busy)
        self.add_row('Lockable', self.lockable)

    def selection_changed(self):
        selection = self.document.selection
        if selection.tool != Selection.INTERACTION or selection.data is None:
            return
        data = self.document.data['interactions'][self.document.selection.data]
        self.block_signals(True)
        self.id.setText(data['id'])
        self.target.set_value(data['target'])
        self.action.setCurrentText(data['action'])
        self.attraction.set_values(data['attraction'])
        self.zone.set_values(data['zone'])
        self.direction.setCurrentText(data['direction'])

        self.play_once.setCurrentIndex(int(data['play_once']))
        self.busy.setCurrentIndex(int(data['busy']))
        self.lockable.setCurrentIndex(int(data['lockable']))

        self.insound.set_file(data['insound'])
        self.outsound.set_file(data['outsound'])
        self.gametypes.set_game_types(data['gametypes'])

        self.block_signals(False)

    def data_edited(self, *_):
        if self.document.selection.tool != Selection.INTERACTION:
            return
        data = self.document.data['interactions'][self.document.selection.data]
        data.update(self.data())
        self.document.edited.emit()

    def data(self):
        return {
            'id': self.id.text(),
            'action': self.action.currentText(),
            'target': self.target.value(),
            'attraction': self.attraction.values(),
            'zone': self.zone.values(),
            'direction': self.direction.currentText(),
            'play_once': bool(self.play_once.currentIndex()),
            'busy': bool(self.busy.currentIndex()),
            'insound': self.insound.filepath(),
            'outsound': self.outsound.filepath(),
            'lockable': bool(self.lockable.currentIndex()),
            'gametypes': self.gametypes.game_types()}


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