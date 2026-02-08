import json
from PySide6 import QtCore
from pixaloon.data import is_point, is_zone


class PathsModel(QtCore.QAbstractTableModel):
    changed = QtCore.Signal()

    def __init__(self, document):
        super().__init__()
        self.document = document

    def set_document(self, document):
        self.layoutAboutToBeChanged.emit()
        self.document = document
        self.document.edited.connect(self.layoutChanged.emit)
        self.layoutChanged.emit()

    def headerData(self, section, orientation, role):
        if role != QtCore.Qt.DisplayRole:
            return
        if orientation != QtCore.Qt.Horizontal:
            return
        return ('Hard', 'Path')[section]

    def rowCount(self, *_):
        if not self.document:
            return 0
        return len(self.document.data['paths'])

    def columnCount(self, *_):
        return 2

    def setData(self, index, value, role):
        try:
            data = json.loads(value)
        except BaseException as e:
            return False

        row, col = index.row(), index.column()
        if col == 0:
            self.document.data['paths'][row]['hard'] = bool(data)
        else:
            if not all(isinstance(n, int) for p in data for n in p):
                return False
            self.document.data['paths'][row]['points'] = data
        self.changed.emit()
        return True

    def flags(self, index):
        return super().flags(index) | QtCore.Qt.ItemIsEditable

    def data(self, index, role):
        if not index.isValid():
            return

        if role not in (QtCore.Qt.DisplayRole, QtCore.Qt.EditRole):
            return
        if index.column() == 0:
            return str(self.document.data['paths'][index.row()]['hard'])
        if index.column() == 1:
            return str(self.document.data['paths'][index.row()]['points'])


class UnassignedSpotModel(QtCore.QAbstractListModel):
    changed = QtCore.Signal()

    def __init__(self, document):
        super().__init__()
        self.document = document

    def set_document(self, document):
        self.layoutAboutToBeChanged.emit()
        self.document = document
        self.document.edited.connect(self.layoutChanged.emit)
        self.layoutChanged.emit()

    def rowCount(self, *_):
        return len(self.document.data['startups']['unassigned'])

    def setData(self, index, value, role):
        try:
            data = json.loads(value)
        except BaseException:
            return False
        if not is_point(data):
            return False
        self.document.data['startups']['unassigned'][index.row()] = data
        self.changed.emit()
        return True

    def flags(self, index):
        return super().flags(index) | QtCore.Qt.ItemIsEditable

    def data(self, index, role):
        if not index.isValid():
            return

        if role in (QtCore.Qt.DisplayRole, QtCore.Qt.EditRole):
            return str(self.document.data['startups']['unassigned'][index.row()])


class GroupAttributesModel(QtCore.QAbstractTableModel):
    changed = QtCore.Signal()

    def __init__(self, document, parent=None):
        super().__init__(parent)
        self.document = document

    def rowCount(self, *_):
        print("TODO: document selected group")
        return 0
        return 8 if self.document.selected_group is not None else 0

    def columnCount(self, *_):
        return 3

    def set_document(self, document):
        self.layoutAboutToBeChanged.emit()
        self.document = document
        self.document.edited.connect(self.layoutChanged.emit)
        self.layoutChanged.emit()

    def flags(self, index):
        flags = super().flags(index)
        if index.column() > 0:
            flags |= QtCore.Qt.ItemIsEditable
        return flags

    def setData(self, index, value, role):
        if not index.isValid():
            return False
        col = index.column()
        if col == 1:
            try:
                data = json.loads(value)
            except BaseException:
                return False
        else:
            data = value

        group_index = self.document.selected_group
        group = self.document.data['startups']['groups'][group_index]
        if index.row() < 4:
            if col == 0:
                return False
            d = ("left", "right", "up", "down")[index.row()]
            if col == 1:
                if not is_point(data):
                    return False
                group['popspots'][d] = data
            else:
                group['interactions'][d] = data
            return True

        if col != 1 or not is_point(data):
            return False
        group['assigned'][index.row() - 4] = data
        return True

    def data(self, index, role):
        if not index.isValid():
            return
        if role not in (QtCore.Qt.DisplayRole, QtCore.Qt.EditRole):
            return
        row, col = index.row(), index.column()
        keys = ("left", "right", "up", "down", "pos1", "pos2", "pos3", "pos4")
        if index.column() == 0:
            return keys[row]
        groups = self.document.data['startups']['groups']
        group = self.document.selected_group
        if row < 4:
            if col == 2:
                return groups[group]['interactions'][keys[row]]
            return str(groups[group]['popspots'][keys[row]])
        if col < 2:
            return str(groups[group]['assigned'][row - 4])
        return ' --- '


class GroupsListModel(QtCore.QAbstractListModel):
    def __init__(self, document, parent=None):
        super().__init__(parent)
        self.document = document

    def set_document(self, document):
        self.layoutAboutToBeChanged.emit()
        self.document = document
        self.document.edited.connect(self.layoutChanged.emit)
        self.layoutChanged.emit()

    def rowCount(self, *_):
        return len(self.document.data['startups']['groups'])

    def data(self, index, role):
        if role == QtCore.Qt.DisplayRole:
            return str(index.row() + 1)


class PropsModel(QtCore.QAbstractTableModel):
    changed = QtCore.Signal()

    def __init__(self, document):
        super().__init__()
        self.document = document

    def set_document(self, document):
        self.layoutAboutToBeChanged.emit()
        self.document = document
        self.document.edited.connect(self.layoutChanged.emit)
        self.layoutChanged.emit()

    def rowCount(self, *_):
        if not self.document:
            return 0
        return len(self.document.data['props'])

    def columnCount(self, *_):
        return 5

    def headerData(self, section, orientation, role):
        if role != QtCore.Qt.DisplayRole:
            return
        if orientation != QtCore.Qt.Horizontal:
            return
        return (
            'file', 'position', 'center', 'box',
            'visible at dispatch')[section]

    def flags(self, index):
        flags = super().flags(index)
        if index.column() != 0:
            flags |= QtCore.Qt.ItemIsEditable
        return flags

    def setData(self, index, value, _):
        if not index.isValid() or not index.column():
            return False
        prop = self.document.data['props'][index.row()]
        if index.column() != 4:
            try:
                data = json.loads(value)
                data = [int(n) for n in data]
            except BaseException:
                return False
        match index.column():
            case 0:
                return False
            case 1:
                if not is_point(data):
                    return False
                prop['position'] = data
            case 2:
                if not is_point(data):
                    return False
                prop['center'] = data
            case 3:
                if not is_zone(data):
                    return False
                prop['box'] = data
            case 4:
                if value.lower() not in ('true', 'false'):
                    return False
                prop['visible_at_dispatch'] = value.lower() == 'true'
        self.changed.emit()
        return True

    def data(self, index, role):
        if not index.isValid():
            return
        if role not in (QtCore.Qt.DisplayRole, QtCore.Qt.EditRole):
            return
        try:
            key = (
                'file', 'position', 'center', 'box',
                'visible_at_dispatch')[index.column()]
            return str(self.document.data['props'][index.row()][key])
        except IndexError:
            print('fail', index)


class OverlaysModel(QtCore.QAbstractTableModel):
    changed = QtCore.Signal()

    def __init__(self, document):
        super().__init__()
        self.document = document

    def set_document(self, document):
        self.layoutAboutToBeChanged.emit()
        self.document = document
        self.document.edited.connect(self.layoutChanged.emit)
        self.layoutChanged.emit()

    def rowCount(self, *_):
        if not self.document:
            return 0
        return len(self.document.data['overlays'])

    def columnCount(self, *_):
        return 2

    def headerData(self, section, orientation, role):
        if role != QtCore.Qt.DisplayRole:
            return
        if orientation != QtCore.Qt.Horizontal:
            return
        return ('File', 'Switch Y')[section]

    def flags(self, index):
        flags = super().flags(index)
        if index.column() == 1:
            flags |= QtCore.Qt.ItemIsEditable
        return flags

    def setData(self, index, value, _):
        if not index.isValid() or not index.column():
            return False
        self.document.data['overlays'][index.row()]['y'] = value
        self.changed.emit()
        return True

    def data(self, index, role):
        if not index.isValid():
            return
        if role not in (QtCore.Qt.DisplayRole, QtCore.Qt.EditRole):
            return
        if index.column() == 0:
            return self.document.data['overlays'][index.row()]['file']
        return self.document.data['overlays'][index.row()]['y']


class StairModel(QtCore.QAbstractTableModel):
    changed = QtCore.Signal()

    def __init__(self, document):
        super().__init__()
        self.document = document

    def set_document(self, document):
        self.layoutAboutToBeChanged.emit()
        self.document = document
        self.document.edited.connect(self.layoutChanged.emit)
        self.layoutChanged.emit()

    def rowCount(self, *_):
        if not self.document:
            return 0
        return len(self.document.data['stairs'])

    def columnCount(self, *_):
        return 2

    def headerData(self, section, orientation, role):
        if role != QtCore.Qt.DisplayRole:
            return
        if orientation != QtCore.Qt.Horizontal:
            return
        return ('Zone', 'Inclination')[section]

    def setData(self, index, value, role):
        try:
            data = json.loads(value)
        except ValueError:
            return False
        if index.column() == 0:
            if not is_zone(data):
                return False
            self.document.data['stairs'][index.row()]['zone'] = data
            self.changed.emit()
            return True
        if index.column() == 1:
            if not isinstance(value, (int, float)):
                return False
            self.document.data['stairs'][index.row()]['inclination'] = float(data)
            self.changed.emit()
            return True
        return False

    def flags(self, index):
        flags = super().flags(index)
        flags |= QtCore.Qt.ItemIsEditable
        return flags

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


class InteractionModel(QtCore.QAbstractTableModel):
    changed = QtCore.Signal()

    def __init__(self, document):
        super().__init__()
        self.document = document

    def set_document(self, document):
        self.layoutAboutToBeChanged.emit()
        self.document = document
        self.document.edited.connect(self.layoutChanged.emit)
        self.layoutChanged.emit()

    def rowCount(self, *_):
        if not self.document:
            return 0
        return len(self.document.data['interactions'])

    def columnCount(self, *_):
        return 9

    def flags(self, index):
        flags = super().flags(index)
        flags |= QtCore.Qt.ItemIsEditable
        return flags

    def setData(self, index, value, _):
        row, col = index.row(), index.column()

        if col == 0:
            if value not in ['poker', 'piano', 'bet', 'rob', 'balcony', 'startup']:
                return False
            self.document.data['interactions'][row]['action'] = value
            self.changed.emit()
            return True

        elif col in (4, 5):
            try:
                data = json.loads(value)
                if not is_zone(data):
                    raise TypeError()
                key = 'zone' if col == 3 else 'attraction'
                self.document.data['interactions'][row][key] = data
                self.changed.emit()
                return True
            except TypeError:
                return False

        elif col == 2:
            try:
                data = [v.strip(" ") for v in value.strip('[]').split(',')]
                data = [
                    int(data[0]) if data[0] != 'None' else None,
                    int(data[1]) if data[1] != 'None' else None]
                self.document.data['interactions'][row]['target'] = data
                self.changed.emit()
                return True
            except BaseException as e:
                print(e)
                return False

        elif col == 3:
            directions = ['left', 'right', 'up', 'down']
            if value not in directions:
                return False
            self.document.data['interactions'][row]['direction'] = value
            self.changed.emit()
            return True

        elif col == 6:
            if value.lower() not in ["0", "1", "true", "false"]:
                return False
            value = value.lower() in ["1", "true"]
            self.document.data['interactions'][row]['busy'] = value
            return True

        elif col == 7:
            if value.lower() not in ["0", "1", "true", "false"]:
                return False
            value = value.lower() in ["1", "true"]
            self.document.data['interactions'][row]['lockable'] = value
            return True

        elif col == 1:
            if value.lower() not in ["0", "1", "true", "false"]:
                return False
            value = value.lower() in ["1", "true"]
            self.document.data['interactions'][row]['play_once'] = value
            return True

        elif col == 8:
            existing_ids = [
                self.document.data['interactions'][r]["id"]
                for r in range(self.rowCount()) if r != row]
            if value in existing_ids:
                return False
            self.document.data['interactions'][row]['id'] = value
            return True

    def headerData(self, section, orientation, role):
        if orientation != QtCore.Qt.Horizontal or role != QtCore.Qt.DisplayRole:
            return
        h = [
            "Action", "Play Once", "Target", "Direction",
            "Zone", "Attraction", "Busy", "Lockable", "Id"]
        return h[section]

    def data(self, index, role):
        if not index.isValid():
            return

        if role not in (QtCore.Qt.DisplayRole, QtCore.Qt.EditRole):
            return

        interaction = self.document.data['interactions'][index.row()]
        col = index.column()
        keys = [
            "action", "play_once", "target", "direction", "zone",
            "attraction", "busy", "lockable", "id"]
        return str(interaction.get(keys[col]))


class FencesModel(QtCore.QAbstractListModel):
    changed = QtCore.Signal()

    def __init__(self, document):
        super().__init__()
        self.document = document

    def set_document(self, document):
        self.layoutAboutToBeChanged.emit()
        self.document = document
        self.document.edited.connect(self.layoutChanged.emit)
        self.layoutChanged.emit()

    def rowCount(self, *_):
        return len(self.document.data['fences'])

    def flags(self, index):
        return super().flags(index) | QtCore.Qt.ItemIsEditable

    def setData(self, index, value, role):
        try:
            data = json.loads(value)
        except TypeError:
            return False
        if not is_zone(data):
            return False
        self.document.data['fences'][index.row()] = data
        self.changed.emit()
        return True

    def data(self, index, role):
        if not index.isValid():
            return
        if index.row() >= len(self.document.data['fences']):
            return
        if role in (QtCore.Qt.DisplayRole, QtCore.Qt.EditRole):
            return str(self.document.data['fences'][index.row()])


class PopspotsModel(QtCore.QAbstractListModel):
    changed = QtCore.Signal()

    def __init__(self, document):
        super().__init__()
        self.document = document

    def set_document(self, document):
        self.layoutAboutToBeChanged.emit()
        self.document = document
        self.document.edited.connect(self.layoutChanged.emit)
        self.layoutChanged.emit()

    def rowCount(self, *_):
        # return 0
        return len(self.document.data['popspots'])

    def setData(self, index, value, role):
        try:
            data = json.loads(value)
        except BaseException:
            return False
        if not is_point(data):
            return False
        self.document.data['popspots'][index.row()] = data
        self.changed.emit()
        return True

    def flags(self, index):
        return super().flags(index) | QtCore.Qt.ItemIsEditable

    def data(self, index, role):
        if not index.isValid():
            return

        if role in (QtCore.Qt.DisplayRole, QtCore.Qt.EditRole):
            return str(self.document.data['popspots'][index.row()])


class WallsModel(QtCore.QAbstractTableModel):
    changed = QtCore.Signal()
    HEADERS = 'Shape', 'Coordinates'

    def __init__(self, document):
        super().__init__()
        self.document = document

    def set_document(self, document):
        self.layoutAboutToBeChanged.emit()
        self.document = document
        self.document.edited.connect(self.layoutChanged.emit)
        self.layoutChanged.emit()

    def rowCount(self, *_):
        if not self.document:
            return 0
        return (
            len(self.document.data['no_go_zones']) +
            len(self.document.data['walls']))

    def columnCount(self, *_):
        return 2

    def headerData(self, section, orientation, role):
        if role != QtCore.Qt.DisplayRole:
            return
        if orientation != QtCore.Qt.Vertical:
            return self.HEADERS[section]
        return str(section)

    def flags(self, index):
        flags = super().flags(index)
        if index.column() == 1:
            flags |= QtCore.Qt.ItemIsEditable
        return flags

    def setData(self, index, data, role):
        try:
            data = json.loads(data)
        except TypeError:
            return False
        if self.type(index.row()) == 'rectangle':
            if not is_zone(data):
                return False
            self.document.data['no_go_zones'][index.row()] = data
            self.changed.emit()
            return True
        if len(data) < 3:
            return False
        if not all(len(p) == 2 for p in data):
            return False
        if not all(isinstance(n, int) for p in data for n in p):
            return False
        row = index.row() - (len(self.document.data['no_go_zones']))
        self.document.data['walls'][row] = data
        self.changed.emit()
        return True

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


class OriginModel(QtCore.QAbstractTableModel):
    changed = QtCore.Signal()

    def __init__(self, document):
        super().__init__()
        self.document = document

    def set_document(self, document):
        self.layoutAboutToBeChanged.emit()
        self.document = document
        self.document.edited.connect(self.layoutChanged.emit)
        self.layoutChanged.emit()

    def rowCount(self, *_):
        if not self.document:
            return 0
        return len(self.document.data['targets'])

    def columnCount(self, _):
        return 2

    def headerData(self, section, orientation, role):
        if orientation != QtCore.Qt.Horizontal or role != QtCore.Qt.DisplayRole:
            return
        return ('Origin', 'Weight')[section]

    def flags(self, index):
        flags = super().flags(index)
        flags |= QtCore.Qt.ItemIsEditable
        return flags

    def setData(self, index, value, _):
        if not index.isValid():
            return
        try:
            data = json.loads(value)
        except TypeError:
            return False
        if index.column() == 0:
            if is_zone(data):
                self.layoutAboutToBeChanged.emit()
                self.document.data['targets'][index.row()]['origin'] = data
                self.layoutChanged.emit()
                self.changed.emit()
                return True
            return False
        if not isinstance(data, int):
            return False
        self.layoutAboutToBeChanged.emit()
        self.document.data['targets'][index]['weight'] = data
        self.changed.emit()
        self.layoutChanged.emit()
        return True

    def data(self, index, role):
        if not index.isValid():
            return
        if role not in (QtCore.Qt.DisplayRole, QtCore.Qt.EditRole):
            return
        row, col = index.row(), index.column()
        target = self.document.data['targets'][row]
        return str(target['weight']) if col == 0 else str(target['origin'])


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
