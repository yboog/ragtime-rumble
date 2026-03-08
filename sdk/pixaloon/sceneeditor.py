
from PySide6 import QtWidgets, QtCore
from pixaloon.filewidget import FilesList
from pixaloon.path import relative_normpath
from pixaloon.editors.base import BaseEditor


class SceneEditor(BaseEditor):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.character_number = QtWidgets.QSpinBox()
        self.character_number.valueChanged.connect(self.data_edited)
        self.characters = FilesList('characters', filters='*.json')
        self.ambiance = AmbianceEdit()
        self.musics = FilesList('musics', filters='*.ogg')

        self.add_row('Number of character', self.character_number)
        self.add_row('Characters', self.characters)
        self.add_row('Ambiance', self.ambiance)
        self.add_row('Musics', self.musics)

    def selection_changed(self):
        return

    def set_document(self, document):
        super().set_document(document)
        self.block_signals(True)
        self.character_number.setValue(document.data['character_number'])
        self.ambiance.set_document(document)
        self.musics.set_document(document)
        self.characters.set_document(document)
        self.block_signals(False)

    def data_edited(self, _):
        self.document.data['character_number'] = self.character_number.value()


class AmbianceEdit(QtWidgets.QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.model = AmbianceModel()
        self.mapper = QtWidgets.QDataWidgetMapper()
        self.mapper.setModel(self.model)
        self.mapper.addMapping(self, 0)
        self.mapper.setSubmitPolicy(QtWidgets.QDataWidgetMapper.AutoSubmit)
        self.mapper.toFirst()

    def set_document(self, document):
        self.model.layoutAboutToBeChanged.emit()
        self.model.document = document
        self.mapper.toFirst()
        self.model.layoutChanged.emit()


class AmbianceModel(QtCore.QAbstractTableModel):
    def __init__(self):
        super().__init__()
        self.document = None

    def set_document(self, document):
        self.layoutAboutToBeChanged.emit()
        self.document = document
        self.layoutChanged.emit()

    def rowCount(self, *_):
        return 1

    def columnCount(self, *_):
        return 1

    def data(self, _, role):
        if role in (QtCore.Qt.DisplayRole, QtCore.Qt.EditRole):
            if self.document is None:
                return ''
            return self.document.data['ambiance']

    def setData(self, index, value, role):
        if role != QtCore.Qt.EditRole or self.document is None:
            return False

        path = relative_normpath(value, self.document)
        self.document.data['ambiance'] = path
        self.document.edited.emit()
        self.dataChanged.emit(index, index, [QtCore.Qt.EditRole])
        return True


