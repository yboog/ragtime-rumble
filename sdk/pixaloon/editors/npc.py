from PySide6 import QtWidgets
from pixaloon.editors.base import BaseEditor
from pixaloon.intarrayeditor import IntArrayEditor, IntArrayListEditor
from pixaloon.intlisteditor import IntListEditor
from pixaloon.selection import Selection
from pixaloon.widgets import GameTypesSelector


class NPCEditor(BaseEditor):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.npc_type = QtWidgets.QLabel()
        self.gametypes = GameTypesSelector()
        self.gametypes.edited.connect(self.data_edited)
        self.subeditor = None
        self.add_row('Type', self.npc_type)
        self.add_row('Game types', self.gametypes)
        self.add_separator()

    def selection_changed(self):
        selection = self.document.selection
        if selection.tool != Selection.NPC or selection.data is None:
            return
        self.block_signals(True)
        npc = self.document.data['npcs'][selection.data]
        self.npc_type.setText(npc["type"])
        self.gametypes.set_game_types(npc["gametypes"])
        cls = SUBEDITORS_BY_TYPES.get(npc['type'], NotEditableNpc)
        if self.subeditor:
            self.layout.removeWidget(self.subeditor)
            self.subeditor.deleteLater()
        self.subeditor = cls()
        self.layout.addWidget(self.subeditor)
        self.subeditor.set_npc(npc)
        self.subeditor.changed.connect(self.data_edited)
        self.block_signals(False)

    def data_edited(self):
        if self.document.selection.tool != Selection.NPC:
            return
        npc = self.document.data['npcs'][self.document.selection.data]
        npc.update({'gametypes': self.gametypes.game_types()})
        npc.update(self.subeditor.data())
        self.document.edited.emit()


class NotEditableNpc(BaseEditor):
    def set_npc(self, npc):
        ...

    def data(self):
        return {}


class SaloonDoorEditor(BaseEditor):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.position = IntArrayEditor()
        self.position.value_changed.connect(self.values_changed)
        self.switch = QtWidgets.QSpinBox()
        self.switch.setMaximum(1_000_000_000)
        self.switch.setMinimum(-1_000_000_000)
        self.switch.valueChanged.connect(self.values_changed)
        self.zone = IntListEditor()
        self.zone.values_changed.connect(self.values_changed)

        self.add_row('Position', self.position)
        self.add_row('Switch', self.switch)
        self.add_row('Zone', self.zone)

    def values_changed(self, *_):
        self.changed.emit()

    def set_npc(self, npc):
        self.block_signals(True)
        self.position.set_value(npc['position'])
        self.zone.set_values(npc['zone'])
        self.switch.setValue(npc['switch'])
        self.block_signals(False)

    def data(self):
        return {
            "zone": self.zone.values(),
            "switch": self.switch.value(),
            "position": self.position.value()}


class PositionEditor(BaseEditor):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.startposition = IntArrayEditor()
        self.startposition.value_changed.connect(self.values_changed)
        self.add_row('Start position', self.startposition)

    def data(self):
        return {
            "startposition": self.startposition.value()}

    def values_changed(self, *_):
        self.changed.emit()

    def set_npc(self, npc):
        self.block_signals(True)
        self.startposition.set_value(npc['startposition'])
        self.block_signals(False)


class LoopEditor(BaseEditor):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.position = IntArrayEditor()
        self.position.value_changed.connect(self.values_changed)
        self.switch = QtWidgets.QSpinBox()
        self.switch.setMaximum(1_000_000_000)
        self.switch.setMinimum(-1_000_000_000)
        self.switch.valueChanged.connect(self.values_changed)

        self.add_row('Position', self.position)
        self.add_row('Switch', self.switch)

    def values_changed(self, *_):
        self.changed.emit()

    def set_npc(self, npc):
        self.block_signals(True)
        self.position.set_value(npc['position'])
        self.switch.setValue(npc['switch'])
        self.block_signals(False)

    def data(self):
        return {
            "switch": self.switch.value(),
            "position": self.position.value()}


class ChickenEditor(BaseEditor):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.startposition = IntArrayEditor()
        self.startposition.value_changed.connect(self.values_changed)
        self.zone = IntListEditor()
        self.zone.values_changed.connect(self.values_changed)
        self.radius = QtWidgets.QSpinBox()
        self.radius.setMaximum(200)
        self.radius.setMinimum(10)
        self.radius.valueChanged.connect(self.values_changed)
        self.add_row('Start position', self.startposition)
        self.add_row('Picking zone', self.zone)
        self.add_row('Flee radius', self.radius)

    def data(self):
        return {
            "zone": self.zone.values(),
            "run_radius": self.radius.value(),
            "startposition": self.startposition.value()}

    def values_changed(self, *_):
        self.changed.emit()

    def set_npc(self, npc):
        self.block_signals(True)
        self.startposition.set_value(npc['startposition'])
        self.zone.set_values(npc['zone'])
        self.radius.setValue(npc['run_radius'])
        self.block_signals(False)


class BarmanEditor(BaseEditor):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.startposition = IntArrayEditor()
        self.startposition.value_changed.connect(self.values_changed)
        self.path = IntArrayListEditor(resizable=True)
        self.path.values_changed.connect(self.values_changed)
        self.direction = QtWidgets.QComboBox()
        self.direction.addItems(['left', 'right'])
        self.direction.currentIndexChanged.connect(self.values_changed)

        self.add_row('Start position', self.startposition)
        self.add_row('Path', self.path)
        self.add_row('Direction', self.direction)

    def data(self):
        return {
            "startposition": self.startposition.value(),
            "direction": self.direction.currentText(),
            "path": self.path.values()}

    def values_changed(self, *_):
        self.changed.emit()

    def set_npc(self, npc):
        self.block_signals(True)
        self.startposition.set_value(npc['startposition'])
        self.direction.setCurrentText(npc['direction'])
        self.path.set_values(npc['path'])
        self.block_signals(False)


class SniperEditor(BaseEditor):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.startposition = IntArrayEditor()
        self.startposition.value_changed.connect(self.values_changed)
        self.switch = QtWidgets.QSpinBox()
        self.switch.setMaximum(1_000_000_000)
        self.switch.setMinimum(-1_000_000_000)
        self.switch.valueChanged.connect(self.values_changed)
        self.zone = IntListEditor()
        self.zone.values_changed.connect(self.values_changed)
        self.interaction_zone = IntListEditor()
        self.interaction_zone.values_changed.connect(self.values_changed)
        self.add_row('Start position', self.startposition)
        self.add_row('Switch', self.switch)
        self.add_row('Aiming zone', self.zone)
        self.add_row('Interaction zone', self.interaction_zone)

    def data(self):
        return {
            "zone": self.zone.values(),
            "interaction_zone": self.interaction_zone.values(),
            "y": self.switch.value(),
            "startposition": self.startposition.value()}

    def values_changed(self, *_):
        self.changed.emit()

    def set_npc(self, npc):
        self.block_signals(True)
        self.startposition.set_value(npc['startposition'])
        self.zone.set_values(npc['zone'])
        self.interaction_zone.set_values(npc['interaction_zone'])
        self.switch.setValue(npc['y'])
        self.block_signals(False)


SUBEDITORS_BY_TYPES = {
    'chicken': ChickenEditor,
    'pianist': PositionEditor,
    'saloon-door': SaloonDoorEditor,
    'barman': BarmanEditor,
    'dog': BarmanEditor,
    'sniper': SniperEditor,
    'loop': LoopEditor,
}