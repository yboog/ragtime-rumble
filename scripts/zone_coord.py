import os
import json
import subprocess

import numpy as np
from PIL import Image, ImageQt
from PySide6 import QtWidgets, QtCore, QtGui


def get_stair_line(rect, inclination):
    mult = rect.width()
    x = rect.left()
    y = rect.center().y() - (mult * (inclination / 2))
    p1 = QtCore.QPointF(x, y)
    x = rect.right()
    y = rect.center().y() - (mult * (-inclination / 2))
    p2 = QtCore.QPointF(x, y)
    line = QtCore.QLineF(p1, p2)
    offset = rect.center().y() - line.center().y()
    line.setP1(QtCore.QPointF(rect.left(), p1.y() + offset))
    line.setP2(QtCore.QPointF(rect.right(), p2.y() + offset))
    return line


class UnassignedSpotModel(QtCore.QAbstractListModel):
    changed = QtCore.Signal()

    def __init__(self, model):
        super().__init__()
        self.model = model

    def rowCount(self, *_):
        return len(self.model.data['startups']['unassigned'])

    def setData(self, index, value, role):
        try:
            data = json.loads(value)
        except BaseException:
            return False
        if not is_point(data):
            return False
        self.model.data['startups']['unassigned'][index.row()] = data
        self.changed.emit()
        return True

    def flags(self, index):
        return super().flags(index) | QtCore.Qt.ItemIsEditable

    def data(self, index, role):
        if not index.isValid():
            return

        if role in (QtCore.Qt.DisplayRole, QtCore.Qt.EditRole):
            return str(self.model.data['startups']['unassigned'][index.row()])


class GroupAttributesModel(QtCore.QAbstractTableModel):
    changed = QtCore.Signal()

    def __init__(self, model, parent=None):
        super().__init__(parent)
        self.model = model

    def rowCount(self, *_):
        return 8 if self.model.selected_group is not None else 0

    def columnCount(self, *_):
        return 2

    def flags(self, index):
        flags = super().flags(index)
        if index.column() > 0:
            flags |= QtCore.Qt.ItemIsEditable
        return flags

    def setData(self, index, value, role):
        if not index.isValid():
            return False
        try:
            data = json.loads(value)
        except BaseException:
            return False
        if not is_point(data):
            return
        group_index = self.model.selected_group
        group = self.model.data['startups']['groups'][group_index]
        self.layoutAboutToBeChanged.emit()
        if index.row() < 4:
            d = ("left", "right", "up", "down")[index.row()]
            group['popspots'][d] = data
        else:
            group['assigned'][index.row() - 4] = data
        self.layoutChanged.emit()
        self.changed.emit()

    def data(self, index, role):
        if not index.isValid():
            return
        if role not in (QtCore.Qt.DisplayRole, QtCore.Qt.EditRole):
            return
        row = index.row()
        keys = ("left", "right", "up", "down", "pos1", "pos2", "pos3", "pos4")
        if index.column() == 0:
            return keys[row]
        groups = self.model.data['startups']['groups']
        group = self.model.selected_group
        if row < 4:
            return str(groups[group]['popspots'][keys[row]])
        return str(groups[group]['assigned'][row - 4])


class GroupsListModel(QtCore.QAbstractListModel):
    def __init__(self, model, parent=None):
        super().__init__(parent)
        self.model = model

    def rowCount(self, *_):
        return len(self.model.data['startups']['groups'])

    def data(self, index, role):
        if role == QtCore.Qt.DisplayRole:
            return str(index.row() + 1)


class Startups(QtWidgets.QWidget):
    changed = QtCore.Signal()

    def __init__(self, model, parent=None):
        super().__init__(parent)
        self.model = model
        self.unassigned_label = QtWidgets.QLabel('Unassigned Gamepad positions')
        self.unassigned_model = UnassignedSpotModel(self.model)
        self.unassigned_model.changed.connect(self.changed.emit)
        self.unassigned_stops = QtWidgets.QListView()
        self.unassigned_stops.setModel(self.unassigned_model)

        unnasighed_layout = QtWidgets.QVBoxLayout()
        unnasighed_layout.addWidget(self.unassigned_label)
        unnasighed_layout.addWidget(self.unassigned_stops)

        self.groups_model = GroupsListModel(self.model)
        self.groups = QtWidgets.QListView()
        self.groups.setModel(self.groups_model)
        self.groups.selectionModel().selectionChanged.connect(self.set_group)

        self.groups_attributes_model = GroupAttributesModel(self.model)
        self.groups_attributes_model.changed.connect(self.changed.emit)
        self.groups_attributes = QtWidgets.QTableView()
        self.groups_attributes.setModel(self.groups_attributes_model)
        self.groups_attributes.verticalHeader().hide()
        self.groups_attributes.horizontalHeader().hide()

        layout = QtWidgets.QHBoxLayout(self)
        layout.addLayout(unnasighed_layout)
        layout.addWidget(self.groups)
        layout.addWidget(self.groups_attributes)

    def set_group(self, *_):
        indexes = self.groups.selectionModel().selectedIndexes()
        self.groups_attributes_model.layoutAboutToBeChanged.emit()
        self.model.selected_group = indexes[0].row() if indexes else None
        self.groups_attributes_model.layoutChanged.emit()
        self.changed.emit()
        return


class PropsModel(QtCore.QAbstractTableModel):
    changed = QtCore.Signal()

    def __init__(self, model):
        super().__init__()
        self.model = model

    def rowCount(self, *_):
        return len(self.model.data['props'])

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
        prop = self.model.data['props'][index.row()]
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
            return str(self.model.data['props'][index.row()][key])
        except IndexError:
            print('fail', index)


class OverlaysModel(QtCore.QAbstractTableModel):
    changed = QtCore.Signal()

    def __init__(self, model):
        super().__init__()
        self.model = model

    def rowCount(self, *_):
        return len(self.model.data['overlays'])

    def columnCount(self, *_):
        return 2

    def headerData(self, section, orientation, role):
        if role != QtCore.Qt.DisplayRole:
            return
        if orientation != QtCore.Qt.Horizontal:
            return
        return ('file', 'switch')[section]

    def flags(self, index):
        flags = super().flags(index)
        if index.column() == 1:
            flags |= QtCore.Qt.ItemIsEditable
        return flags

    def setData(self, index, value, _):
        if not index.isValid() or not index.column():
            return False
        self.model.data['overlays'][index.row()]['y'] = value
        self.changed.emit()
        return True

    def data(self, index, role):
        if not index.isValid():
            return
        if role not in (QtCore.Qt.DisplayRole, QtCore.Qt.EditRole):
            return
        if index.column() == 0:
            return self.model.data['overlays'][index.row()]['file']
        return self.model.data['overlays'][index.row()]['y']


class StairModel(QtCore.QAbstractTableModel):
    changed = QtCore.Signal()

    def __init__(self, model):
        super().__init__()
        self.model = model

    def rowCount(self, *_):
        return len(self.model.data['stairs'])

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
            self.model.data['stairs'][index.row()]['zone'] = data
            self.changed.emit()
            return True
        if index.column() == 1:
            if not isinstance(value, (int, float)):
                return False
            self.model.data['stairs'][index.row()]['inclination'] = float(data)
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
        stair = self.model.data['stairs'][row]
        if col == 0:
            return str(stair['zone'])
        if col == 1:
            return str(stair['inclination'])


class InteractionModel(QtCore.QAbstractTableModel):
    changed = QtCore.Signal()

    def __init__(self, model):
        super().__init__()
        self.model = model

    def rowCount(self, *_):
        return len(self.model.data['interactions'])

    def columnCount(self, *_):
        return 5

    def flags(self, index):
        flags = super().flags(index)
        flags |= QtCore.Qt.ItemIsEditable
        return flags

    def setData(self, index, value, _):
        row, col = index.row(), index.column()

        if col == 0:
            if value not in ['poker', 'piano', 'bet', 'rob', 'balcony']:
                return False
            self.model.data['interactions'][row]['action'] = value
            self.changed.emit()
            return True

        elif col in (3, 4):
            try:
                data = json.loads(value)
                if not is_zone(data):
                    raise TypeError()
                key = 'zone' if col == 3 else 'attraction'
                self.model.data['interactions'][row][key] = data
                self.changed.emit()
                return True
            except TypeError:
                return False

        elif col == 1:
            try:
                data = [v.strip(" ") for v in value.strip('[]').split(',')]
                data = [
                    int(data[0]) if data[0] != 'None' else None,
                    int(data[1]) if data[1] != 'None' else None]
                self.model.data['interactions'][row]['target'] = data
                self.changed.emit()
                return True
            except BaseException as e:
                print(e)
                return False

        elif col == 2:
            directions = ['left', 'right', 'up', 'down']
            if value not in directions:
                return False
            self.model.data['interactions'][row]['direction'] = value
            self.changed.emit()
            return True

    def headerData(self, section, orientation, role):
        if orientation != QtCore.Qt.Horizontal or role != QtCore.Qt.DisplayRole:
            return
        return ["Action", "Target", "Direction", "Zone", "Attraction"][section]

    def data(self, index, role):
        if not index.isValid():
            return

        if role not in (QtCore.Qt.DisplayRole, QtCore.Qt.EditRole):
            return

        interaction = self.model.data['interactions'][index.row()]
        col = index.column()
        k = ["action", "target", "direction", "zone", "attraction"][col]
        return str(interaction[k])


def is_zone(data):
    return False if len(data) != 4 else all(isinstance(n, int) for n in data)


def is_point(data):
    if len(data) != 2:
        return False
    return all(isinstance(n, (int, float)) for n in data)


class FencesModel(QtCore.QAbstractListModel):
    changed = QtCore.Signal()

    def __init__(self, model):
        super().__init__()
        self.model = model

    def rowCount(self, *_):
        return len(self.model.data['fences'])

    def flags(self, index):
        return super().flags(index) | QtCore.Qt.ItemIsEditable

    def setData(self, index, value, role):
        try:
            data = json.loads(value)
        except TypeError:
            return False
        if not is_zone(data):
            return False
        self.model.data['fences'][index.row()] = data
        self.changed.emit()
        return True

    def data(self, index, role):
        if not index.isValid():
            return

        if role in (QtCore.Qt.DisplayRole, QtCore.Qt.EditRole):
            return str(self.model.data['fences'][index.row()])


class PopspotsModel(QtCore.QAbstractListModel):
    changed = QtCore.Signal()

    def __init__(self, model):
        super().__init__()
        self.model = model

    def rowCount(self, *_):
        return len(self.model.data['popspots'])

    def setData(self, index, value, role):
        try:
            data = json.loads(value)
        except BaseException:
            return False
        if not is_point(data):
            return False
        self.model.data['popspots'][index.row()] = data
        self.changed.emit()
        return True

    def flags(self, index):
        return super().flags(index) | QtCore.Qt.ItemIsEditable

    def data(self, index, role):
        if not index.isValid():
            return

        if role in (QtCore.Qt.DisplayRole, QtCore.Qt.EditRole):
            return str(self.model.data['popspots'][index.row()])


class WallsModel(QtCore.QAbstractTableModel):
    changed = QtCore.Signal()

    def __init__(self, model):
        super().__init__()
        self.model = model

    def rowCount(self, *_):
        return (
            len(self.model.data['no_go_zones']) +
            len(self.model.data['walls']))

    def columnCount(self, *_):
        return 2

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
            self.model.data['no_go_zones'][index.row()] = data
            self.changed.emit()
            return True
        if len(data) < 3:
            return False
        if not all(len(p) == 2 for p in data):
            return False
        if not all(isinstance(n, int) for p in data for n in p):
            return False
        row = index.row() - (len(self.model.data['no_go_zones']))
        self.model.data['walls'][row] = data
        self.changed.emit()
        return True

    def type(self, row):
        zones = self.model.data['no_go_zones']
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
        item = (self.model.data['no_go_zones'] + self.model.data['walls'])[row]
        return str(item)


def remove_key_color(filename, key_color):
    orig_color = tuple(key_color + [255])
    replacement_color = (0, 0, 0, 0)
    image = Image.open(filename).convert('RGBA')
    data = np.array(image)
    data[(data == orig_color).all(axis=-1)] = replacement_color
    return ImageQt.ImageQt(Image.fromarray(data, mode='RGBA'))


class LevelCanvasModel:
    def __init__(self, gameroot, data):
        self.data = data
        self.backgrounds = []

        for background in data['backgrounds']:
            img = QtGui.QImage(f'{gameroot}/{background["file"]}')
            self.backgrounds.append(img)

        self.overlays = []
        color = [0, 255, 0]
        for overlay in data['overlays']:
            img = remove_key_color(f'{gameroot}/{overlay["file"]}', color)
            self.overlays.append(img)

        self.props = []
        color = [0, 255, 0]
        for prop in data['props']:
            img = remove_key_color(f'{gameroot}/{prop["file"]}', color)
            self.props.append(img)

        self.filter = True
        self.walls = True
        self.popspots = False
        self.interactions = False
        self.display_props = True
        self.stairs = False
        self.targets = False
        self.switches = False
        self.fences = False
        self.startups = True

        self.selected_target = None
        self.selected_group = None
        self.selected_interaction = None
        self.wall_selected_rows = []

    def size(self):
        w = max(b.size().width() for b in self.backgrounds)
        h = max(b.size().height() for b in self.backgrounds)
        return QtCore.QSize(w, h)


class LevelCanvas(QtWidgets.QWidget):
    rect_drawn = QtCore.Signal(object)
    point_set = QtCore.Signal(object)
    polygon_drawn = QtCore.Signal(object)

    def __init__(self, model):
        super().__init__()
        self.model = model
        self.setFixedSize(self.sizeHint())
        self.rect_ = None
        self.point = None
        self.polygon = None
        self.mode = 'None'

    def sizeHint(self):
        return self.model.size()

    def mousePressEvent(self, event):
        if self.mode == 'None':
            return
        if self.mode == 'rectangle':
            self.polygon = None
            self.point = None
            self.rect_ = QtCore.QRect(
                event.position().toPoint(),
                event.position().toPoint())
        elif self.mode == 'point':
            self.rect_ = None
            self.point = None
            self.point = event.position().toPoint()
        elif self.mode == 'polygon' and not self.polygon:
            self.polygon = QtGui.QPolygon([event.position().toPoint()])
            self.point = None
            self.rect_ = None
        elif self.mode == 'polygon':
            self.polygon << event.position().toPoint()
        self.repaint()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Return and self.polygon:
            self.polygon_drawn.emit(self.polygon)
            self.polygon = None
            self.repaint()

    def mouseMoveEvent(self, event):
        if self.mode == 'point':
            self.point = event.position().toPoint()
        elif self.mode == 'rectangle':
            self.rect_.setBottomRight(event.position().toPoint())
        elif self.mode == 'polygon':
            self.polygon[-1] = event.position().toPoint()
        self.repaint()

    def mouseReleaseEvent(self, event):
        if self.mode == 'point':
            self.point_set.emit(self.point)
        elif self.mode == 'rectangle':
            self.rect_drawn.emit(self.rect_)
        self.point = None
        self.rect_ = None
        self.repaint()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        positions = [bg['position'] for bg in self.model.data['backgrounds']]
        for pos, image in zip(positions, self.model.backgrounds):
            painter.drawImage(QtCore.QPoint(*pos), image)
        positions = [ol['position'] for ol in self.model.data['overlays']]
        for pos, image in zip(positions, self.model.overlays):
            painter.drawImage(QtCore.QPoint(*pos), image)
        for prop, image in zip(self.model.data['props'], self.model.props):
            x = prop['position'][0] - prop['center'][0]
            y = prop['position'][1] - prop['center'][1]
            painter.drawImage(x, y, image)
        if self.model.filter:
            color = QtGui.QColor(QtCore.Qt.white)
            color.setAlpha(100)
            painter.setBrush(color)
            painter.setPen(color)
            painter.drawRect(event.rect())
        if self.model.switches:
            for ol in self.model.data['overlays']:
                c = event.rect().left(), ol['y'], event.rect().right(), ol['y']
                line = QtCore.QLine(*c)
                painter.setPen(QtCore.Qt.white)
                painter.drawLine(line)
        if self.model.popspots:
            painter.setPen(QtCore.Qt.yellow)
            painter.setBrush(QtCore.Qt.yellow)
            for x, y in self.model.data['popspots']:
                painter.drawEllipse(x, y, 2, 2)
        if self.model.display_props:
            for prop in self.model.data['props']:
                x = prop['position'][0] + prop['center'][0]
                y = prop['position'][1] + prop['center'][1]
                left = prop['position'][0] + prop['box'][0]
                top = prop['position'][1] + prop['box'][1]
                color = QtGui.QColor('pink')
                painter.setPen(color)
                color.setAlpha(50)
                painter.setBrush(color)
                painter.drawRect(left, top, prop['box'][2], prop['box'][3])
                painter.setPen(QtCore.Qt.white)
                painter.setBrush(QtCore.Qt.white)
                painter.drawEllipse(prop['position'][0], prop['position'][1], 2, 2)
        if self.model.walls:
            i = 0
            for rect in self.model.data['no_go_zones']:
                if i in self.model.wall_selected_rows:
                    pen = QtGui.QPen(QtCore.Qt.white)
                    pen.setWidth(3)
                    painter.setPen(pen)
                    color = QtGui.QColor(QtCore.Qt.white)
                    color.setAlpha(50)
                    painter.setBrush(color)
                else:
                    pen = QtGui.QPen(QtCore.Qt.red)
                    pen.setWidth(1)
                    painter.setPen(pen)
                    color = QtGui.QColor(QtCore.Qt.red)
                    color.setAlpha(50)
                    painter.setBrush(color)
                painter.drawRect(*rect)
                i += 1
            for polygon in self.model.data['walls']:
                if i in self.model.wall_selected_rows:
                    pen = QtGui.QPen(QtCore.Qt.white)
                    pen.setWidth(3)
                    painter.setPen(pen)
                    color = QtGui.QColor(QtCore.Qt.white)
                    color.setAlpha(50)
                    painter.setBrush(color)
                else:
                    pen = QtGui.QPen(QtCore.Qt.red)
                    pen.setWidth(1)
                    painter.setPen(pen)
                    color = QtGui.QColor(QtCore.Qt.red)
                    color.setAlpha(50)
                    painter.setBrush(color)
                polygon = QtGui.QPolygon([QtCore.QPoint(*p) for p in polygon])
                painter.drawPolygon(polygon)
                i += 1
        if self.model.stairs:
            for stair in self.model.data['stairs']:
                color = QtGui.QColor("#DEABDE")
                painter.setPen(color)
                color.setAlpha(50)
                painter.setBrush(color)
                rect = QtCore.QRect(*stair['zone'])
                painter.drawRect(rect)
                painter.setPen(QtCore.Qt.white)
                line = get_stair_line(rect, stair['inclination'])
                painter.drawLine(line)
        if self.model.targets:
            for i, origin_dsts in enumerate(self.model.data['targets']):
                sel = self.model.selected_target
                if sel is not None and i != sel:
                    continue
                color = QtGui.QColor('#FF00FF')
                painter.setPen(color)
                color.setAlpha(50)
                painter.setBrush(color)
                origin = QtCore.QRect(*origin_dsts['origin'])
                painter.drawRect(origin)
                for dst in origin_dsts['destinations']:
                    color = QtGui.QColor('#FFFF00')
                    painter.setPen(color)
                    color.setAlpha(50)
                    painter.setBrush(color)
                    dst = QtCore.QRect(*dst)
                    painter.drawRect(dst)
                    painter.setPen(QtCore.Qt.white)
                    painter.setBrush(QtCore.Qt.NoBrush)
                    painter.drawLine(origin.center(), dst.center())
        if self.model.fences:
            color = QtGui.QColor(QtCore.Qt.cyan)
            painter.setPen(color)
            color.setAlpha(50)
            painter.setBrush(color)
            for fence in self.model.data['fences']:
                painter.drawRect(*fence)
        if self.model.interactions:
            color = QtGui.QColor(QtCore.Qt.green)
            color.setAlpha(50)
            painter.setBrush(color)
            align = QtCore.Qt.AlignCenter
            for i, interaction in enumerate(self.model.data['interactions']):
                selection = self.model.selected_interaction
                if i == selection and selection is not None:
                    painter.setPen(QtCore.Qt.white)
                else:
                    painter.setPen(QtCore.Qt.green)
                color.setAlpha(50)
                painter.setBrush(color)
                painter.setBrush(color)
                rect = QtCore.QRect(*interaction['zone'])
                painter.drawRect(rect)
                text = get_interaction_text(interaction)
                painter.drawText(rect, align, text)
                color.setAlpha(25)
                painter.setBrush(color)
                painter.setPen(QtCore.Qt.NoPen)
                painter.drawRect(*interaction['attraction'])
                painter.setPen(QtCore.Qt.white)
                painter.setBrush(QtCore.Qt.white)
                if None not in interaction['target']:
                    painter.drawEllipse(*interaction['target'], 2, 2)
                elif interaction['target'][0] is None:
                    y = interaction['target'][1]
                    p1 = QtCore.QPoint(interaction['zone'][0], y)
                    x = interaction['zone'][0] + interaction['zone'][2]
                    p2 = QtCore.QPoint(x, y)
                    painter.drawLine(p1, p2)
                elif interaction['target'][1] is None:
                    x = interaction['target'][0]
                    p1 = QtCore.QPoint(x, interaction['zone'][1])
                    y = interaction['zone'][1] + interaction['zone'][3]
                    p2 = QtCore.QPoint(x, y)
                    painter.drawLine(p1, p2)

        if self.model.startups:
            painter.setBrush(QtCore.Qt.green)
            painter.setPen(QtCore.Qt.blue)
            for point in self.model.data['startups']['unassigned']:
                painter.drawEllipse(point[0], point[1], 4, 4)
            for i, group in enumerate(self.model.data['startups']['groups']):
                painter.setBrush(QtCore.Qt.green)
                painter.setPen(QtCore.Qt.blue)
                for point in group['assigned']:
                    painter.drawEllipse(point[0], point[1], 4, 4)
                directions = 'left', 'up', 'right', 'down'
                points = [
                    QtCore.QPoint(*group['popspots'][d]) for d in directions]
                if i == self.model.selected_group:
                    color = QtCore.Qt.white
                else:
                    color = QtCore.Qt.magenta
                color = QtGui.QColor(color)
                painter.setPen(color)
                color.setAlpha(50)
                painter.setBrush(color)
                polygon = QtGui.QPolygon(points)
                painter.drawPolygon(polygon)
                painter.setBrush(QtCore.Qt.black)
                painter.setPen(QtCore.Qt.black)
                for direction in directions:
                    painter.drawText(
                        QtCore.QPoint(*group['popspots'][direction]),
                        direction)

        if self.rect_ and self.mode == 'rectangle':
            painter.setPen(QtCore.Qt.white)
            painter.setBrush(QtCore.Qt.NoBrush)
            painter.drawRect(self.rect_)
        elif self.point and self.mode == 'point':
            painter.setPen(QtCore.Qt.red)
            painter.setBrush(QtCore.Qt.red)
            painter.drawEllipse(self.point, 2, 2)
        elif self.polygon and self.mode == 'polygon':
            painter.setPen(QtCore.Qt.yellow)
            color = QtGui.QColor(QtCore.Qt.yellow)
            color.setAlpha(100)
            painter.drawPolygon(self.polygon)

        painter.end()


def get_interaction_text(interaction):
    if interaction['direction'] == 'left':
        return f"<- {interaction['action']}"
    if interaction['direction'] == 'right':
        return f"{interaction['action']} ->"
    if interaction['direction'] == 'up':
        return f"^\n{interaction['action']}"
    if interaction['direction'] == 'down':
        return f"{interaction['action']}\nv"


class Editor(QtWidgets.QWidget):
    def __init__(self, gameroot, filename):
        super().__init__()
        self.setMinimumWidth(1100)
        self.filename = filename
        with open(filename, 'r') as f:
            data = json.load(f)
        self.model = LevelCanvasModel(gameroot, data)
        self.canvas = LevelCanvas(self.model)
        self.canvas.point_set.connect(self.add_point)
        self.canvas.rect_drawn.connect(self.add_rectangle)
        self.canvas.polygon_drawn.connect(self.add_polygon)
        self.visibilities = Visibilities(self.model)
        self.visibilities.update_visibilities.connect(self.change_visibilities)

        selection_mode = QtWidgets.QAbstractItemView.ExtendedSelection
        self.popspotsmodel = PopspotsModel(self.model)
        self.popspotsmodel.changed.connect(self.canvas.repaint)
        self.popspots = QtWidgets.QListView()
        self.popspots.setSelectionMode(selection_mode)
        self.popspots.setModel(self.popspotsmodel)

        selection_behavior = QtWidgets.QAbstractItemView.SelectRows
        self.walls_model = WallsModel(self.model)
        self.walls_model.changed.connect(self.canvas.repaint)
        self.walls = QtWidgets.QTableView()
        self.walls.setSelectionMode(selection_mode)
        self.walls.setSelectionBehavior(selection_behavior)
        self.walls.setModel(self.walls_model)
        method = self.walls_selected
        self.walls.selectionModel().selectionChanged.connect(method)

        self.interactions_model = InteractionModel(self.model)
        self.interactions_model.changed.connect(self.canvas.repaint)
        self.interactions = QtWidgets.QTableView()
        self.interactions.setSelectionMode(selection_mode)
        self.interactions.setSelectionBehavior(selection_behavior)
        self.interactions.setModel(self.interactions_model)
        method = self.interaction_selected
        self.interactions.selectionModel().selectionChanged.connect(method)

        self.stairs_model = StairModel(self.model)
        self.stairs_model.changed.connect(self.canvas.repaint)
        self.stairs = QtWidgets.QTableView()
        self.stairs.setSelectionMode(selection_mode)
        self.stairs.setSelectionBehavior(selection_behavior)
        self.stairs.setModel(self.stairs_model)

        self.targets = OriginDestinations(self.model)
        self.targets.changed.connect(self.canvas.repaint)

        self.overlays_model = OverlaysModel(self.model)
        self.overlays_model.changed.connect(self.canvas.repaint)
        self.overlays = QtWidgets.QTableView()
        self.overlays.setModel(self.overlays_model)

        self.fences_model = FencesModel(self.model)
        self.fences_model.changed.connect(self.canvas.repaint)
        self.fences = QtWidgets.QListView()
        self.fences.setModel(self.fences_model)

        self.props_model = PropsModel(self.model)
        self.props_model.changed.connect(self.canvas.repaint)
        self.props = QtWidgets.QTableView()
        self.props.setModel(self.props_model)

        self.startups = Startups(self.model)
        self.startups.changed.connect(self.canvas.repaint)

        self.tab = QtWidgets.QTabWidget()
        self.tab.currentChanged.connect(self.tab_changed)
        self.tab.addTab(self.popspots, 'Pop spots')
        self.tab.addTab(self.walls, 'Walls')
        self.tab.addTab(self.interactions, 'Interactions')
        self.tab.addTab(self.stairs, 'Stairs')
        self.tab.addTab(self.targets, 'Origin/Targets')
        self.tab.addTab(self.props, 'Props')
        self.tab.addTab(self.fences, 'Fences')
        self.tab.addTab(self.overlays, 'OL / Switches')
        self.tab.addTab(self.startups, 'Startups')

        self.rect_wall = QtWidgets.QPushButton('Create rect wall')
        self.rect_wall.setCheckable(True)
        self.rect_wall.setChecked(True)
        self.poly_wall = QtWidgets.QPushButton('Create polygonal wall')
        self.poly_wall.setCheckable(True)
        self.poly_wall.setChecked(True)
        self.create_interaction = QtWidgets.QPushButton('Create interaction')
        self.create_interaction.setCheckable(True)
        self.create_interaction.setChecked(True)
        self.create_stair = QtWidgets.QPushButton('Create stair')
        self.create_stair.setCheckable(True)
        self.create_stair.setChecked(True)
        self.add_popspots = QtWidgets.QPushButton('Create pop spot')
        self.add_popspots.setCheckable(True)
        self.create_origin = QtWidgets.QPushButton('Create origin zone')
        self.create_origin.setCheckable(True)
        self.create_destination = QtWidgets.QPushButton('Create destination zone')
        self.create_destination.setCheckable(True)
        self.create_fence = QtWidgets.QPushButton('Create fence')
        self.create_fence.setCheckable(True)

        self.group = QtWidgets.QButtonGroup()
        self.group.addButton(self.rect_wall, 0)
        self.group.addButton(self.poly_wall, 1)
        self.group.addButton(self.add_popspots, 2)
        self.group.addButton(self.create_interaction, 3)
        self.group.addButton(self.create_stair, 4)
        self.group.addButton(self.create_origin, 5)
        self.group.addButton(self.create_destination, 6)
        self.group.addButton(self.create_fence, 7)
        self.group.idReleased.connect(self.mode_changed)
        self.group.setExclusive(True)

        self.delete = QtWidgets.QPushButton('delete')

        action1 = QtGui.QAction('💾', self)
        action1.triggered.connect(self.save)
        action2 = QtGui.QAction('📁', self)
        action2.triggered.connect(self.open)
        action3 = QtGui.QAction('play', self)
        action3.triggered.connect(self.play)
        self.toolbar = QtWidgets.QToolBar()
        self.toolbar.addAction(action1)
        self.toolbar.addAction(action2)
        self.toolbar.addAction(action3)

        buttons = QtWidgets.QGridLayout()
        buttons.setSpacing(2)
        buttons.addWidget(self.rect_wall, 0, 0)
        buttons.addWidget(self.poly_wall, 1, 0)
        buttons.addWidget(self.add_popspots, 2, 0)
        buttons.addWidget(self.create_interaction, 3, 0)
        buttons.addWidget(self.create_stair, 0, 1)
        buttons.addWidget(self.create_origin, 1, 1)
        buttons.addWidget(self.create_destination, 2, 1)
        buttons.addWidget(self.create_fence, 3, 1)

        buttons_spacing = QtWidgets.QVBoxLayout()
        buttons_spacing.addLayout(buttons)
        buttons_spacing.addWidget(self.visibilities)
        buttons_spacing.addSpacing(1)

        right = QtWidgets.QVBoxLayout()
        right.addWidget(self.tab)
        right.addWidget(self.delete)

        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(self.canvas)
        hlayout.addLayout(buttons_spacing)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.toolbar)
        layout.addLayout(hlayout)
        layout.addLayout(right)

    def tab_changed(self, *_):
        for table in (self.walls, self.interactions):
            table.horizontalHeader().resizeSections(
                QtWidgets.QHeaderView.ResizeToContents)

    def mode_changed(self, index):
        self.canvas.mode = (
            'rectangle', 'polygon', 'point', 'rectangle',
            'rectangle', 'rectangle', 'rectangle', 'rectangle')[index]
        self.canvas.repaint()

    def add_point(self, point):
        if self.group.checkedId() == 2:
            self.popspotsmodel.layoutAboutToBeChanged.emit()
            self.model.data['popspots'].append([point.x(), point.y()])
            self.popspotsmodel.layoutChanged.emit()
            self.canvas.repaint()

    def add_rectangle(self, rect):
        if self.group.checkedId() == 0:
            self.walls_model.layoutAboutToBeChanged.emit()
            rect = [rect.left(), rect.top(), rect.width(), rect.height()]
            self.model.data['no_go_zones'].append(rect)
            self.walls_model.layoutChanged.emit()
        if self.group.checkedId() == 3:
            self.interactions_model.layoutAboutToBeChanged.emit()
            target = [rect.center().x(), rect.center().y()]
            rect = [rect.left(), rect.top(), rect.width(), rect.height()]
            interaction = {
                "action": "poker",
                "direction": "right",
                "zone": rect,
                "target": target}
            self.model.data['interactions'].append(interaction)
            self.interactions_model.layoutChanged.emit()
        if self.group.checkedId() == 4:
            self.stairs_model.layoutAboutToBeChanged.emit()
            rect = [rect.left(), rect.top(), rect.width(), rect.height()]
            stair = {
                "zone": rect,
                "inclination": 1.5}
            self.model.data['stairs'].append(stair)
            self.stairs_model.layoutChanged.emit()
        if self.group.checkedId() == 5:
            self.targets.origin_model.layoutAboutToBeChanged.emit()
            rect = [rect.left(), rect.top(), rect.width(), rect.height()]
            target = {
                "origin": rect,
                "weight": 3,
                "destinations": []}
            self.model.data['targets'].append(target)
            self.targets.origin_model.layoutChanged.emit()
            self.targets.select_last()
        if self.group.checkedId() == 6:
            if self.model.selected_target is None:
                return
            self.targets.destinations_model.layoutAboutToBeChanged.emit()
            rect = [rect.left(), rect.top(), rect.width(), rect.height()]
            self.model.data['targets'][self.model.selected_target]['destinations'].append(rect)
            self.targets.destinations_model.layoutChanged.emit()
        if self.group.checkedId() == 7:
            self.fences_model.layoutAboutToBeChanged.emit()
            rect = [rect.left(), rect.top(), rect.width(), rect.height()]
            self.model.data['fences'].append(rect)
            self.fences_model.layoutChanged.emit()

    def add_polygon(self, polygon):
        self.walls_model.layoutAboutToBeChanged.emit()
        data = [(p.x(), p.y()) for p in polygon]
        self.model.data['walls'].append(data)
        self.repaint()
        self.walls_model.layoutChanged.emit()

    def keyPressEvent(self, event):
        self.canvas.keyPressEvent(event)

    def change_visibilities(self):
        self.model.filter = self.visibilities.filter.isChecked()
        self.model.walls = self.visibilities.walls.isChecked()
        self.model.popspots = self.visibilities.popspots.isChecked()
        self.model.interactions = self.visibilities.interactions.isChecked()
        self.model.display_props = self.visibilities.props.isChecked()
        self.model.stairs = self.visibilities.stairs.isChecked()
        self.model.targets = self.visibilities.targets.isChecked()
        self.model.switches = self.visibilities.switches.isChecked()
        self.model.fences = self.visibilities.fences.isChecked()
        self.model.startups = self.visibilities.startups.isChecked()
        self.repaint()

    def interaction_selected(self, *_):
        indexes = self.interactions.selectionModel().selectedIndexes()
        if not indexes:
            self.model.selected_interaction = None
            self.repaint()
            return
        rows = list({index.row() for index in indexes})
        self.model.selected_interaction = rows[0]
        self.repaint()

    def walls_selected(self, *_):
        indexes = self.walls.selectedIndexes()
        rows = list({index.row() for index in indexes})
        self.model.wall_selected_rows = rows
        self.repaint()

    def open(self):
        ...

    def save(self):
        with open(self.filename, 'w') as f:
            json.dump(self.model.data, f, indent=2)

    def play(self):
        here = os.path.dirname(__file__)
        subprocess.Popen(f'{here}/../launcher.bat')


class OriginModel(QtCore.QAbstractTableModel):
    changed = QtCore.Signal()

    def __init__(self, model):
        super().__init__()
        self.model = model

    def rowCount(self, *_):
        return len(self.model.data['targets'])

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
                self.model.data['targets'][index.row()]['origin'] = data
                self.layoutChanged.emit()
                self.changed.emit()
                return True
            return False
        if not isinstance(data, int):
            return False
        self.layoutAboutToBeChanged.emit()
        self.model.data['targets'][index]['weight'] = data
        self.changed.emit()
        self.layoutChanged.emit()
        return True

    def data(self, index, role):
        if not index.isValid():
            return
        if role not in (QtCore.Qt.DisplayRole, QtCore.Qt.EditRole):
            return
        row, col = index.row(), index.column()
        target = self.model.data['targets'][row]
        return str(target['weight']) if col == 0 else str(target['origin'])


class DestinationsModel(QtCore.QAbstractListModel):
    changed = QtCore.Signal()

    def __init__(self, model):
        super().__init__()
        self.model = model

    def rowCount(self, _):
        if self.model.selected_target is None:
            return 0
        index = self.model.selected_target
        return len(self.model.data['targets'][index]['destinations'])

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
        target = self.model.data['targets'][self.model.selected_target]
        target['destinations'][row] = data
        self.layoutChanged.emit()
        self.changed.emit()
        return True

    def data(self, index, role):
        roles = QtCore.Qt.DisplayRole, QtCore.Qt.EditRole
        if not index.isValid() or role not in roles:
            return

        row = index.row()
        target = self.model.data['targets'][self.model.selected_target]
        return str(target['destinations'][row])


class OriginDestinations(QtWidgets.QWidget):
    changed = QtCore.Signal()

    def __init__(self, model):
        super().__init__()
        self.model = model
        self.origin_model = OriginModel(self.model)
        self.origin_model.changed.connect(self.changed.emit)
        self.origin = QtWidgets.QTableView()
        behavior = QtWidgets.QAbstractItemView.SelectRows
        self.origin.setSelectionBehavior(behavior)
        self.origin.setModel(self.origin_model)
        method = self.selection_changed
        self.origin.selectionModel().selectionChanged.connect(method)
        self.destinations_model = DestinationsModel(self.model)
        self.destinations_model.changed.connect(self.changed.emit)
        self.destinations = QtWidgets.QListView()
        self.destinations.setSelectionBehavior(behavior)
        self.destinations.setModel(self.destinations_model)
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.origin)
        layout.addWidget(self.destinations)

    def selection_changed(self, *_):
        indexes = self.origin.selectionModel().selectedIndexes()
        self.destinations_model.layoutAboutToBeChanged.emit()
        if not indexes:
            self.model.selected_target = None
            self.changed.emit()
            return
        self.model.selected_target = indexes[0].row()
        self.changed.emit()
        self.destinations_model.layoutChanged.emit()

    def select_last(self):
        self.origin.selectionModel().clear()
        last_row = self.origin.model().rowCount() - 1
        index = self.origin.model().index(last_row, 0)
        self.origin.selectionModel().select(
            index, QtCore.QItemSelectionModel.Select)


class Visibilities(QtWidgets.QWidget):
    update_visibilities = QtCore.Signal()

    def __init__(self, model):
        super().__init__()
        self.model = model
        self.filter = QtWidgets.QCheckBox('Filter', checked=model.filter)
        self.filter.released.connect(self.update_visibilities.emit)
        self.walls = QtWidgets.QCheckBox('Walls', checked=model.walls)
        self.walls.released.connect(self.update_visibilities.emit)
        s = model.popspots
        self.popspots = QtWidgets.QCheckBox('Pop Spots', checked=s)
        self.popspots.released.connect(self.update_visibilities.emit)
        s = model.interactions
        self.interactions = QtWidgets.QCheckBox('Interactions', checked=s)
        self.interactions.released.connect(self.update_visibilities.emit)
        self.props = QtWidgets.QCheckBox('Props', checked=model.display_props)
        self.props.released.connect(self.update_visibilities.emit)
        self.stairs = QtWidgets.QCheckBox('Stairs', checked=model.stairs)
        self.stairs.released.connect(self.update_visibilities.emit)
        s = model.targets
        self.targets = QtWidgets.QCheckBox('Origin -> Destinations', checked=s)
        self.targets.released.connect(self.update_visibilities.emit)
        self.switches = QtWidgets.QCheckBox('Switches', checked=model.switches)
        self.switches.released.connect(self.update_visibilities.emit)
        self.fences = QtWidgets.QCheckBox('Fences', checked=s)
        self.fences.released.connect(self.update_visibilities.emit)
        self.startups = QtWidgets.QCheckBox('Startups', checked=model.startups)
        self.startups.released.connect(self.update_visibilities.emit)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.filter)
        layout.addWidget(self.walls)
        layout.addWidget(self.popspots)
        layout.addWidget(self.interactions)
        layout.addWidget(self.props)
        layout.addWidget(self.stairs)
        layout.addWidget(self.targets)
        layout.addWidget(self.switches)
        layout.addWidget(self.fences)
        layout.addWidget(self.startups)
        layout.addStretch(1)


app = QtWidgets.QApplication([])
gameroot = 'C:/perso/drunk-paranoia/drunkparanoia'
scene = 'C:/perso/drunk-paranoia/drunkparanoia/resources/scenes/saloon.json'
editor = Editor(gameroot, scene)
editor.show()
app.exec()
