
from PySide6 import QtWidgets, QtCore
from pixaloon.selection import Selection
from pixaloon.tablemodel import (
    PopspotsModel, WallsModel, InteractionModel, StairModel, OverlaysModel,
    PathsModel, FencesModel, PropsModel, StartupsModel, TargetsModel,
    BackgroundsModel)


class TableView(QtWidgets.QTableView):
    def __init__(self, parent=None):
        super().__init__(parent)
        selection_behavior = QtWidgets.QAbstractItemView.SelectRows
        self.setSelectionBehavior(selection_behavior)
        self.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeToContents)
        self.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.setHorizontalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)

    def select_row(self, row):
        rows = [i.row() for i in self.selectedIndexes()]
        if row not in rows:
            self.selectRow(row)

    def setModel(self, model):
        super().setModel(model)
        self.setSelectionMode(model.SELECTION_MODE)


class ObjectsList(QtWidgets.QWidget):
    data_updated = QtCore.Signal()

    def __init__(self, document=None, parent=None):
        super().__init__(parent)
        self.document = document

        self.popspotsmodel = PopspotsModel(self.document)
        self.walls_model = WallsModel(self.document)
        self.backgrounds_model = BackgroundsModel(self.document)
        self.interactions_model = InteractionModel(self.document)
        self.stairs_model = StairModel(self.document)
        self.startups_model = StartupsModel(self.document)
        self.overlays_model = OverlaysModel(self.document)
        self.paths_model = PathsModel(self.document)
        self.fences_model = FencesModel(self.document)
        self.props_model = PropsModel(self.document)
        self.targets_model = TargetsModel(self.document)

        self.table = TableView()
        self.table.setModel(self.popspotsmodel)
        self.table.selectionModel().selectionChanged.connect(
            self.table_selection_changed)

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.table)

    def set_document(self, document):
        self.document = document
        self.document.selection.changed.connect(self.selection_changed)
        self.popspotsmodel.set_document(document)
        self.startups_model.set_document(document)
        self.walls_model.set_document(document)
        self.stairs_model.set_document(document)
        self.backgrounds_model.set_document(document)
        self.overlays_model.set_document(document)
        self.fences_model.set_document(document)
        self.props_model.set_document(document)
        self.paths_model.set_document(document)
        self.targets_model.set_document(document)
        self.interactions_model.set_document(document)

    def set_element_type(self, element_type):
        self.clear_selection()
        types_and_models = {
            'popspots': self.popspotsmodel,
            'walls': self.walls_model,
            'backgrounds': self.backgrounds_model,
            'interactions': self.interactions_model,
            'startups': self.startups_model,
            'stairs': self.stairs_model,
            'overlays': self.overlays_model,
            'props': self.props_model,
            'fences': self.fences_model,
            'targets': self.targets_model,
            'paths': self.paths_model}
        model = types_and_models.get(element_type)
        self.table.setModel(model)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.selectionModel().selectionChanged.connect(
            self.table_selection_changed)

    def table_selection_changed(self):
        model = self.table.model()
        selection_mode = QtWidgets.QAbstractItemView.SingleSelection
        if model.SELECTION_TOOL == Selection.WALL:
            return self.wall_selected()
        elif model.SELECTION_TOOL == Selection.STARTUP:
            return # TODO
        elif model.SELECTION_TOOL in (Selection.TARGET, Selection.PATH):
            iterator = (idx.row() for idx in self.table.selectedIndexes())
            data = next(iterator, None)
            data = [data, None]
        elif model.SELECTION_MODE == selection_mode:
            data = next((idx.row() for idx in self.table.selectedIndexes()), None)
        else:
            data = sorted(set(i.row() for i in self.table.selectedIndexes()))
        self.document.selection.data = data
        self.document.selection.tool = model.SELECTION_TOOL
        self.document.selection.changed.emit(self)

    def wall_selected(self):
        row = next((idx.row() for idx in self.table.selectedIndexes()), None)
        if row is None:
            return self.clear_selection()
        if row >= len(self.document.data['no_go_zones']):
            row -= len(self.document.data['no_go_zones'])
            self.document.selection.data = row
            self.document.selection.tool = Selection.WALL
        else:
            self.document.selection.data = row
            self.document.selection.tool = Selection.NO_GO_ZONE
        self.document.selection.changed.emit(self)

    def clear_selection(self):
        self.table.selectionModel().clear()
        self.document.selection.clear()
        self.document.selection.changed.emit(self)

    def selection_changed(self, qobject_source):
        if qobject_source == self:
            return
        seldata = self.document.selection.data
        match self.document.selection.tool:
            case Selection.WALL:
                row = len(self.document.data['no_go_zones'])
                self.table.select_row(row + seldata)
            case Selection.TARGET:
                self.table.select_row(seldata[0])
            case Selection.NO_GO_ZONE:
                self.table.select_row(seldata)
            case Selection.INTERACTION:
                self.table.select_row(seldata)
            case Selection.STAIR:
                self.table.select_row(seldata)
            case Selection.FENCE:
                index = self.fences_model.index(seldata, 0)
                self.table.setCurrentIndex(index)
            case Selection.OVERLAY:
                self.table.select_row(seldata)
            case _:
                return
        self.document.selection.changed.emit(self)
