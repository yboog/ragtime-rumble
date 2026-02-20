
from PySide6 import QtWidgets, QtCore
from pixaloon.filewidget import FilesList
from pixaloon.path import relative_normpath


class SceneEditor(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.character_number = QtWidgets.QSpinBox()
        self.characters = FilesList('characters', filters='*.json')
        self.ambiance = AmbianceEdit()
        self.musics = FilesList('musics', filters='*.ogg')
        self.backgrounds = FilesList('backgrounds', filters='*.png')

        form = QtWidgets.QFormLayout(self)
        form.setContentsMargins(0, 0, 0, 0)
        form.addRow('Number of character', self.character_number)
        form.addRow('Characters', self.characters)
        form.addRow('Ambiance', self.ambiance)
        form.addRow('Musics', self.musics)

    def set_document(self, document):
        self.character_number.setValue(document.data['character_number'])
        self.ambiance.set_document(document)
        self.musics.set_document(document)
        self.characters.set_document(document)


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


