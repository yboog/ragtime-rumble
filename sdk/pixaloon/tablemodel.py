import os
import json
from PySide6 import QtCore, QtWidgets
from pixaloon.data import is_zone
from pixaloon.selection import Selection


V = '✔'
X = '✘'


class AbstractTableModel(QtCore.QAbstractTableModel):
    HEADERS = []
    DATAKEY = ''
    SELECTION_TOOL = None
    SELECTION_MODE = QtWidgets.QAbstractItemView.SingleSelection

    def __init__(self, document):
        super().__init__()
        self.document = document

    def set_document(self, document):
        self.layoutAboutToBeChanged.emit()
        self.document = document
        self.document.edited.connect(self.layoutChanged.emit)
        self.layoutChanged.emit()

    def headerData(self, section, orientation, role):
        if role == QtCore.Qt.TextAlignmentRole:
            if orientation == QtCore.Qt.Horizontal:
                return QtCore.Qt.AlignCenter
            return QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
        if role != QtCore.Qt.DisplayRole:
            return
        if orientation != QtCore.Qt.Horizontal:
            return str(section)
        return self.HEADERS[section]

    def rowCount(self, *_):
        if not self.document:
            return 0
        return len(self.document.data[self.DATAKEY])

    def columnCount(self, *_):
        return len(self.HEADERS)


class StartupsModel(AbstractTableModel):
    HEADERS = 'Player',
    SELECTION_TOOL = Selection.STARTUP

    def rowCount(self, *_):
        return 5

    def data(self, index, role):
        if not index.isValid():
            return
        if role == QtCore.Qt.DisplayRole:
            if not index.row():
                return 'Unassigned spot positions'
            return f'Player {index.row()}'


class BackgroundPlaceHolderModel(AbstractTableModel):
    HEADERS = 'Type', 'Color'
    SELECTION_TOOL = Selection.BGPH

    def rowCount(self, *_):
        return len(self.document.data['edit_data']['background_placeholders'])

    def data(self, index, role):
        if not index.isValid():
            return
        if role == QtCore.Qt.DisplayRole:
            ph = self.document.data['edit_data']['background_placeholders']
            if index.column() == 0:
                return ph[index.row()]['type']
            if index.column() == 1:
                return str(ph[index.row()]['color'])


class ShadowModel(AbstractTableModel):
    HEADERS = 'Player',
    DATAKEY = 'shadow_zones'
    SELECTION_TOOL = Selection.SHADOW

    def data(self, index, role):
        if not index.isValid():
            return
        if role == QtCore.Qt.DisplayRole:
            return str(self.document.data[self.DATAKEY][index.row()]['polygon'])


class PathsModel(AbstractTableModel):
    HEADERS = 'Hard', 'Path'
    DATAKEY = 'paths'
    SELECTION_TOOL = Selection.PATH

    def data(self, index, role):
        if not index.isValid():
            return

        if role == QtCore.Qt.TextAlignmentRole and index.column() == 0:
            return QtCore.Qt.AlignmentFlag.AlignCenter
        if role not in (QtCore.Qt.DisplayRole, QtCore.Qt.EditRole):
            return
        if index.column() == 0:
            return V if self.document.data['paths'][index.row()]['hard'] else ''
        if index.column() == 1:
            return str(self.document.data['paths'][index.row()]['points'])


class PropsModel(AbstractTableModel):
    HEADERS = ('File', 'Position', 'Center')
    DATAKEY = 'props'
    SELECTION_TOOL = Selection.PROP

    def data(self, index, role):
        if not index.isValid():
            return
        if role not in (QtCore.Qt.DisplayRole, QtCore.Qt.EditRole):
            return
        try:
            key = ('file', 'position', 'center')[index.column()]
            return str(self.document.data[self.DATAKEY][index.row()][key])
        except IndexError:
            print('fail', index)


class OverlaysModel(AbstractTableModel):
    HEADERS = ('File', 'Position', 'Switch Y')
    DATAKEY = 'overlays'
    SELECTION_TOOL = Selection.OVERLAY

    def data(self, index, role):
        if not index.isValid():
            return
        if role not in (QtCore.Qt.DisplayRole, QtCore.Qt.EditRole):
            return
        if index.column() == 0:
            return self.document.data['overlays'][index.row()]['file']
        if index.column() == 1:
            return str(self.document.data['overlays'][index.row()]['position'])
        return self.document.data['overlays'][index.row()]['y']


class StairModel(AbstractTableModel):
    HEADERS = ('Zone', 'Inclination')
    DATAKEY = 'stairs'
    SELECTION_TOOL = Selection.STAIR

    def data(self, index, role):
        if not index.isValid():
            return
        if role not in (QtCore.Qt.DisplayRole, QtCore.Qt.EditRole):
            return
        row, col = index.row(), index.column()
        stair = self.document.data['stairs'][row]
        if col == 0:
            return str(stair['zone'])
        if col == 1:
            return str(stair['inclination'])


class InteractionModel(AbstractTableModel):
    HEADERS = ["Action", "Id", "Direction", "Play Once"]
    DATAKEY = 'interactions'
    SELECTION_TOOL = Selection.INTERACTION

    def data(self, index, role):
        if not index.isValid():
            return

        if role == QtCore.Qt.TextAlignmentRole:
            return QtCore.Qt.AlignmentFlag.AlignCenter
        if role not in (QtCore.Qt.DisplayRole, QtCore.Qt.EditRole):
            return

        interaction = self.document.data['interactions'][index.row()]
        col = index.column()
        key = ["action", "id", "direction", "play_once"][col]
        if key == 'play_once':
            return V if interaction.get(col) else ''

        return str(interaction.get(key))


class FencesModel(AbstractTableModel):
    HEADERS = 'Coords',
    DATAKEY = 'fences'
    SELECTION_TOOL = Selection.FENCE

    def data(self, index, role):
        if not index.isValid():
            return
        if index.row() >= len(self.document.data['fences']):
            return
        if role in (QtCore.Qt.DisplayRole, QtCore.Qt.EditRole):
            return str(self.document.data['fences'][index.row()])


class PopspotsModel(AbstractTableModel):
    HEADERS = 'Position',
    DATAKEY = 'popspots'
    SELECTION_MODE = QtWidgets.QAbstractItemView.ExtendedSelection
    SELECTION_TOOL = Selection.POPSPOT

    def data(self, index, role):
        if not index.isValid():
            return

        if role in (QtCore.Qt.DisplayRole, QtCore.Qt.EditRole):
            return str(self.document.data['popspots'][index.row()]['position'])


class BackgroundsModel(AbstractTableModel):
    HEADERS = 'File',
    DATAKEY = 'backgrounds'
    SELECTION_TOOL = Selection.BACKGROUND

    def data(self, index, role):
        if not index.isValid():
            return

        if role in (QtCore.Qt.DisplayRole, QtCore.Qt.EditRole):
            return self.document.data['backgrounds'][index.row()]['file']


class NpcsModel(AbstractTableModel):
    HEADERS = 'Name', 'Type'
    DATAKEY = 'npcs'
    SELECTION_TOOL = Selection.NPC

    def data(self, index, role):
        if not index.isValid():
            return

        if role in (QtCore.Qt.DisplayRole, QtCore.Qt.EditRole):
            npc =  self.document.data['npcs'][index.row()]
            if index.column() == 0:
                return os.path.basename(npc['file'])
            if index.column() == 1:
                return npc['type']


class WallsModel(AbstractTableModel):
    HEADERS = 'Shape', 'Coordinates'
    SELECTION_TOOL = Selection.WALL

    def rowCount(self, *_):
        if not self.document:
            return 0
        return (
            len(self.document.data['no_go_zones']) +
            len(self.document.data['walls']))

    def type(self, row):
        zones = self.document.data['no_go_zones']
        return 'rectangle' if row < len(zones) else 'polygon'

    def data(self, index, role):
        if not index.isValid():
            return
        row, col = index.row(), index.column()
        if role not in (QtCore.Qt.DisplayRole, QtCore.Qt.EditRole):
            return
        type_ = self.type(row)
        if col == 0:
            return type_
        item = (self.document.data['no_go_zones'] + self.document.data['walls'])[row]
        return str(item)


class TargetsModel(AbstractTableModel):
    HEADERS = ['Origin', 'Weight', 'Destinations']
    DATAKEY = 'targets'
    SELECTION_TOOL = Selection.TARGET

    def data(self, index, role):
        if not index.isValid():
            return
        row, col = index.row(), index.column()
        if role == QtCore.Qt.TextAlignmentRole:
            if col:
                return QtCore.Qt.AlignCenter
        if role not in (QtCore.Qt.DisplayRole, QtCore.Qt.EditRole):
            return
        target = self.document.data['targets'][row]
        if col == 0:
            return str(target['origin'])
        if col == 1:
            return str(target['weight'])
        if col == 2:
            return str(len(target['destinations']))


class DestinationsModel(QtCore.QAbstractListModel):
    changed = QtCore.Signal()

    def __init__(self, document):
        super().__init__()
        self.document = document

    def set_document(self, document):
        self.layoutAboutToBeChanged.emit()
        self.document = document
        self.document.edited.connect(self.layoutChanged.emit)
        self.layoutChanged.emit()

    def rowCount(self, _):
        if self.document.selected_target is None:
            return 0
        index = self.document.selected_target
        return len(self.document.data['targets'][index]['destinations'])

    def flags(self, index):
        return super().flags(index) | QtCore.Qt.ItemIsEditable

    def setData(self, index, value, role):
        if not index.isValid():
            return
        try:
            data = json.loads(value)
        except TypeError:
            return False
        if not is_zone(data):
            return False
        row = index.row()
        self.layoutAboutToBeChanged.emit()
        target = self.document.data['targets'][self.document.selected_target]
        target['destinations'][row] = data
        self.layoutChanged.emit()
        self.changed.emit()
        return True

    def data(self, index, role):
        roles = QtCore.Qt.DisplayRole, QtCore.Qt.EditRole
        if not index.isValid() or role not in roles:
            return

        row = index.row()
        target = self.document.data['targets'][self.document.selected_target]
        return str(target['destinations'][row])
