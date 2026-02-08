
from PySide6 import QtWidgets, QtCore
from pixaloon.selection import Selection
from pixaloon.tablemodel import (
    PopspotsModel, WallsModel, InteractionModel, StairModel, OverlaysModel,
    PathsModel, FencesModel, PropsModel, UnassignedSpotModel, GroupsListModel,
    GroupAttributesModel, OriginModel, DestinationsModel)


class DataEditor(QtWidgets.QWidget):
    data_updated = QtCore.Signal()

    def __init__(self, document=None, parent=None):
        super().__init__(parent)
        self.document = document

        selection_mode = QtWidgets.QAbstractItemView.ExtendedSelection
        self.popspotsmodel = PopspotsModel(self.document)
        self.popspotsmodel.changed.connect(self.data_updated.emit)
        self.popspots = QtWidgets.QListView()
        self.popspots.setSelectionMode(selection_mode)
        self.popspots.setModel(self.popspotsmodel)

        selection_behavior = QtWidgets.QAbstractItemView.SelectRows
        selection_mode = QtWidgets.QAbstractItemView.SingleSelection
        self.walls_model = WallsModel(self.document)
        self.walls_model.changed.connect(self.data_updated.emit)
        self.walls = QtWidgets.QTableView()
        self.walls.setSelectionMode(selection_mode)
        self.walls.setSelectionBehavior(selection_behavior)
        self.walls.setModel(self.walls_model)
        self.walls.selectionModel().selectionChanged.connect(
            self.wall_selected)

        self.interactions_model = InteractionModel(self.document)
        self.interactions_model.changed.connect(self.data_updated.emit)
        self.interactions = QtWidgets.QTableView()
        self.interactions.setSelectionMode(selection_mode)
        self.interactions.setSelectionBehavior(selection_behavior)
        self.interactions.setModel(self.interactions_model)

        self.stairs_model = StairModel(self.document)
        self.stairs_model.changed.connect(self.data_updated.emit)
        self.stairs = QtWidgets.QTableView()
        self.stairs.setSelectionMode(selection_mode)
        self.stairs.setSelectionBehavior(selection_behavior)
        self.stairs.setModel(self.stairs_model)

        self.targets = OriginDestinations(self.document)
        self.targets.data_updated.connect(self.data_updated.emit)

        selection_mode = QtWidgets.QAbstractItemView.SingleSelection
        selection_behavior = QtWidgets.QAbstractItemView.SelectRows
        self.overlays_model = OverlaysModel(self.document)
        self.overlays_model.changed.connect(self.data_updated.emit)
        self.overlays = QtWidgets.QTableView()
        self.overlays.setModel(self.overlays_model)
        self.overlays.setSelectionMode(selection_mode)
        self.overlays.setSelectionBehavior(selection_behavior)
        self.overlays.selectionModel().selectionChanged.connect(
            self.overlay_selected)

        self.paths_model = PathsModel(self.document)
        self.paths_model.changed.connect(self.data_updated.emit)
        self.paths = QtWidgets.QTableView()
        self.paths.setWordWrap(True)
        self.paths.setModel(self.paths_model)

        selection_mode = QtWidgets.QAbstractItemView.SingleSelection
        self.fences_model = FencesModel(self.document)
        self.fences_model.changed.connect(self.data_updated.emit)
        self.fences = QtWidgets.QListView()
        self.fences.setSelectionMode(selection_mode)
        self.fences.setModel(self.fences_model)
        self.fences.selectionModel().selectionChanged.connect(
            self.fence_selected)

        self.props_model = PropsModel(self.document)
        self.props_model.changed.connect(self.data_updated.emit)
        self.props = QtWidgets.QTableView()
        self.props.setModel(self.props_model)

        self.startups = Startups(self.document)
        self.startups.data_updated.connect(self.data_updated.emit)

        self.tab = QtWidgets.QTabWidget()
        self.tab.addTab(self.popspots, 'Pop spots')
        self.tab.addTab(self.walls, 'Walls')
        self.tab.addTab(self.interactions, 'Interactions')
        self.tab.addTab(self.stairs, 'Stairs')
        self.tab.addTab(self.targets, 'Origin/Targets')
        self.tab.addTab(self.props, 'Props')
        self.tab.addTab(self.fences, 'Fences')
        self.tab.addTab(self.paths, 'NPC Paths')
        self.tab.addTab(self.overlays, 'OL / Switches')
        self.tab.addTab(self.startups, 'Startups')

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.tab)

    def set_element_type(self, element_type):
        element_types = [
            'popspots',
            'walls',
            'interactions',
            'stairs',
            'targets',
            'props',
            'fences',
            'paths',
            'switchs',
            'startups']
        if element_type not in element_types:
            return
        index = element_types.index(element_type)
        self.tab.setCurrentIndex(index)

    def set_document(self, document):
        self.document = document
        self.document.selection.changed.connect(self.selection_changed)
        self.startups.set_document(document)
        self.targets.set_document(document)
        self.popspotsmodel.set_document(document)
        self.walls_model.set_document(document)
        self.stairs_model.set_document(document)
        self.overlays_model.set_document(document)
        self.fences_model.set_document(document)
        self.props_model.set_document(document)

    def fence_selected(self):
        row = next((idx.row() for idx in self.fences.selectedIndexes()), None)
        if row is None:
            return self.clear_selection()
        self.document.selection.data = row
        self.document.selection.tool = Selection.FENCE
        self.data_updated.emit()

    def overlay_selected(self):
        row = next((i.row() for i in self.overlays.selectedIndexes()), None)
        if row is None:
            return self.clear_selection()
        self.document.selection.data = row
        self.document.selection.tool = Selection.OVERLAY
        self.data_updated.emit()

    def wall_selected(self):
        row = next((idx.row() for idx in self.walls.selectedIndexes()), None)
        if row is None:
            return self.clear_selection()
        if row >= len(self.document.data['no_go_zones']):
            row -= len(self.document.data['no_go_zones'])
            self.document.selection.data = row
            self.document.selection.tool = Selection.WALL
        else:
            self.document.selection.data = row
            self.document.selection.tool = Selection.NO_GO_ZONES
        self.data_updated.emit()

    def clear_selection(self):
        self.startups.clear_selection()
        self.targets.clear_selection()
        tables = (
            self.popspots,
            self.walls,
            self.stairs,
            self.overlays,
            self.fences,
            self.props)
        for table in tables:
            selection_model: QtCore.QItemSelectionModel = table.selectionModel()
            selection_model.clear()

    def selection_changed(self):
        self.clear_selection()
        match self.document.selection.tool:
            case Selection.WALL:
                row = len(self.document.data['no_go_zones'])
                row +=  self.document.selection.data
                self.walls.selectRow(row)
            case Selection.NO_GO_ZONES:
                row = self.document.selection.data
                self.walls.selectRow(row)
            case Selection.FENCE:
                row = self.document.selection.data
                index = self.fences_model.index(row, 0)
                self.fences.setCurrentIndex(index)
            case Selection.OVERLAY:
                row = self.document.selection.data
                self.overlays.selectRow(row)


class Startups(QtWidgets.QWidget):
    data_updated = QtCore.Signal()

    def __init__(self, document, parent=None):
        super().__init__(parent)
        self.document = document
        self.unassigned_label = QtWidgets.QLabel('Unassigned Gamepad positions')
        self.unassigned_model = UnassignedSpotModel(self.document)
        self.unassigned_model.changed.connect(self.data_updated.emit)
        self.unassigned_stops = QtWidgets.QListView()
        self.unassigned_stops.setModel(self.unassigned_model)

        unnasighed_layout = QtWidgets.QVBoxLayout()
        unnasighed_layout.addWidget(self.unassigned_label)
        unnasighed_layout.addWidget(self.unassigned_stops)

        self.groups_model = GroupsListModel(self.document)
        self.groups = QtWidgets.QListView()
        self.groups.setModel(self.groups_model)
        self.groups.selectionModel().selectionChanged.connect(self.set_group)

        self.groups_attributes_model = GroupAttributesModel(self.document)
        self.groups_attributes_model.changed.connect(self.data_updated.emit)
        self.groups_attributes = QtWidgets.QTableView()
        self.groups_attributes.setModel(self.groups_attributes_model)
        self.groups_attributes.verticalHeader().hide()
        self.groups_attributes.horizontalHeader().hide()

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(unnasighed_layout)
        layout.addWidget(self.groups)
        layout.addWidget(self.groups_attributes)

    def clear_selection(self):
        self.groups.selectionModel().clear()
        self.groups_attributes.selectionModel().clear()

    def set_group(self, *_):
        indexes = self.groups.selectionModel().selectedIndexes()
        self.groups_attributes_model.layoutAboutToBeChanged.emit()
        self.document.selected_group = indexes[0].row() if indexes else None
        self.groups_attributes_model.layoutChanged.emit()
        self.data_updated.emit()
        return

    def set_document(self, document):
        self.document = document
        self.groups_attributes_model.document = document
        self.groups_model.document = document
        self.unassigned_model.document = document


class OriginDestinations(QtWidgets.QWidget):
    data_updated = QtCore.Signal()

    def __init__(self, document):
        super().__init__()
        self.document = document
        self.origin_model = OriginModel(self.document)
        self.origin_model.changed.connect(self.data_updated.emit)
        self.origin = QtWidgets.QTableView()
        behavior = QtWidgets.QAbstractItemView.SelectRows
        self.origin.setSelectionBehavior(behavior)
        self.origin.setModel(self.origin_model)
        method = self.selection_changed
        self.origin.selectionModel().selectionChanged.connect(method)
        self.destinations_model = DestinationsModel(self.document)
        self.destinations_model.changed.connect(self.data_updated.emit)
        self.destinations = QtWidgets.QListView()
        self.destinations.setSelectionBehavior(behavior)
        self.destinations.setModel(self.destinations_model)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.origin)
        layout.addWidget(self.destinations)

    def clear_selection(self):
        self.origin.selectionModel().clear()
        self.destinations.selectionModel().clear()

    def set_document(self, document):
        self.document = document
        self.origin_model.document = document
        self.destinations_model.document = document

    def selection_changed(self, *_):
        indexes = self.origin.selectionModel().selectedIndexes()
        self.destinations_model.layoutAboutToBeChanged.emit()
        if not indexes:
            self.document.selected_target = None
            self.data_updated.emit()
            return
        self.document.selected_target = indexes[0].row()
        self.data_updated.emit()
        self.destinations_model.layoutChanged.emit()

    def select_last(self):
        self.origin.selectionModel().clear()
        last_row = self.origin.model().rowCount() - 1
        index = self.origin.model().index(last_row, 0)
        self.origin.selectionModel().select(
            index, QtCore.QItemSelectionModel.Select)

