import os
import json
import msgpack
import subprocess

from PIL import ImageQt
from PySide6 import QtWidgets, QtGui, QtCore

from pixoleros.dopesheet import DopeSheet
from pixoleros.io import get_icon, serialize_document, export_anim_data
from pixoleros.imgutils import switch_colors, build_sprite_sheet
from pixoleros.library import LibraryTableView
from pixoleros.model import Document
from pixoleros.navigator import Navigator
from pixoleros.palette import Palettes
from pixoleros.viewport import ViewportMapper, zoom


def set_shortcut(keysequence, parent, method):
    shortcut = QtGui.QShortcut(QtGui.QKeySequence(keysequence), parent)
    shortcut.activated.connect(method)


class Pixoleros(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        self.play_state = False

        self.setWindowTitle('Pixoleros')
        self.mdi = QtWidgets.QMdiArea()
        self.setCentralWidget(self.mdi)

        self.mdi.subWindowActivated.connect(self.sub_window_changed)
        self.mdi.setViewMode(QtWidgets.QMdiArea.TabbedView)
        self.mdi.setTabsClosable(True)

        self.toolbar = MainToolbar()
        self.toolbar.new.triggered.connect(self.new)
        self.toolbar.open.triggered.connect(self.open)
        self.toolbar.save.triggered.connect(self.save)
        self.toolbar.export.triggered.connect(self.export)
        self.toolbar.assign.triggered.connect(self.assign)
        self.toolbar.play.triggered.connect(self.play)

        areas = (
            QtCore.Qt.TopDockWidgetArea |
            QtCore.Qt.BottomDockWidgetArea |
            QtCore.Qt.LeftDockWidgetArea |
            QtCore.Qt.RightDockWidgetArea)

        self.library = LibraryTableView()
        self.library_dock = QtWidgets.QDockWidget('Library', self)
        self.library_dock.setAllowedAreas(areas)
        self.library_dock.setWidget(self.library)

        self.parameters = CharacterParameters()
        title = 'Character parameters'
        self.parameters_dock = QtWidgets.QDockWidget(title, self)
        self.parameters_dock.setAllowedAreas(areas)
        self.parameters_dock.setWidget(self.parameters)

        self.dopesheet = DopeSheet()
        self.dopesheet.updated.connect(self.update)
        self.dopesheet_dock = QtWidgets.QDockWidget('Dopesheet', self)
        self.dopesheet_dock.setAllowedAreas(areas)
        self.dopesheet_dock.setWidget(self.dopesheet)

        self.palette = Palettes()
        self.palette.palette_changed.connect(self.repaint_canvas)
        self.palette_dock = QtWidgets.QDockWidget('Palette', self)
        self.palette_dock.setAllowedAreas(areas)
        self.palette_dock.setWidget(self.palette)

        self.addDockWidget(
            QtCore.Qt.BottomDockWidgetArea, self.dopesheet_dock)
        self.addDockWidget(
            QtCore.Qt.LeftDockWidgetArea, self.parameters_dock)
        self.addDockWidget(
            QtCore.Qt.LeftDockWidgetArea, self.palette_dock)
        self.addDockWidget(
            QtCore.Qt.LeftDockWidgetArea, self.library_dock)
        self.tabifyDockWidget(self.palette_dock, self.library_dock)

        self.setCorner(
            QtCore.Qt.BottomLeftCorner,
            QtCore.Qt.LeftDockWidgetArea)

        self.setCorner(
            QtCore.Qt.BottomRightCorner,
            QtCore.Qt.RightDockWidgetArea)

        self.addToolBar(QtCore.Qt.TopToolBarArea, self.toolbar)

        set_shortcut('CTRL+N', self, self.new)
        set_shortcut('CTRL+O', self, self.open)
        set_shortcut('CTRL+S', self, self.save)
        set_shortcut('RIGHT', self, self.next)
        set_shortcut('LEFT', self, self.prev)
        set_shortcut('F', self, self.focus)
        set_shortcut('DEL', self, self.delete)
        set_shortcut('CTRL+E', self, self.export)
        set_shortcut('CTRL+A', self, self.assign)

    def assign(self):
        CharacterAssignment(self).exec()

    def save(self):
        if not self.current_document:
            return
        document = self.current_document
        if document.filepath:
            directory = os.path.dirname(document.filepath)
        elif document.library:
            path = list(document.library.values())[0].path
            directory = os.path.dirname(os.path.dirname(path))
        else:
            directory = os.path.expanduser('~')
        path, result = QtWidgets.QFileDialog.getSaveFileName(
            self, 'Save as', directory, 'Pixoleros (*.pixo)')
        if not result:
            return
        document.filepath = path
        with open(path, 'wb') as f:
            msgpack.dump(serialize_document(self.current_document), f)

    def export(self):
        if not self.current_document:
            return
        images = build_sprite_sheet(self.current_document)
        data = export_anim_data(self.current_document)
        dialog = Exporter(images, data, self.current_document)
        dialog.exec()

    def delete(self):
        if not (document := self.current_document):
            return
        self.library.model().layoutAboutToBeChanged.emit()
        document.delete_frames(list(self.dopesheet.selection))
        self.library.model().layoutChanged.emit()
        self.repaint_canvas()
        self.dopesheet.repaint()

    @property
    def current_document(self):
        if not (window := self.mdi.currentSubWindow()):
            return
        if not (widget := window.widget()):
            return
        return widget.document

    def offset(self, value=1):
        window = self.mdi.currentSubWindow()
        if not window:
            return
        widget = window.widget()
        if not widget:
            return
        document = widget.document
        document.index += value
        self.dopesheet.repaint()
        widget.repaint()

    def next(self):
        self.offset()

    def prev(self):
        self.offset(-1)

    def update(self):
        self.mdi.currentSubWindow().repaint()
        self.dopesheet.repaint()

    def focus(self):
        window = self.mdi.currentSubWindow()
        if not window:
            return
        widget = window.widget()
        if not widget:
            return
        widget.focus()

    def new(self):
        document = Document()
        self.add_document(document, 'New character')

    def open(self):
        directory = os.path.expanduser(os.path.expanduser('~'))
        if self.current_document and self.current_document.filepath:
            directory = os.path.dirname(self.current_document.filepath)
        filepath, _ = QtWidgets.QFileDialog.getOpenFileName(
            parent=self,
            caption='Open file',
            dir=directory,
            filter='Pixo file (*.pixo)')
        if not filepath:
            return
        self.open_filepath(filepath)

    def open_filepath(self, filepath):
        with open(filepath, 'rb') as f:
            data = msgpack.load(f)

        document = Document.load(data)
        document.filepath = filepath
        self.add_document(document, filepath)

    def add_document(self, document, name):
        canvas = Canvas(document)
        canvas.updated.connect(self.update)
        window = self.mdi.addSubWindow(canvas)
        window.setWindowTitle(name)
        window.show()

    def sub_window_changed(self, window):
        document = window.widget().document if window else None
        self.dopesheet.set_document(document)
        self.palette.set_document(document)
        self.library.set_document(document)
        self.parameters.set_document(document)

    def repaint_canvas(self):
        if (widget := self.mdi.currentSubWindow().widget()):
            widget.repaint()

    def play(self):
        if not self.current_document:
            return
        if not self.current_document.gamedirectory:
            directory = QtWidgets.QFileDialog.getExistingDirectory(
                parent=self,
                caption='Select output folder',
                dir=os.path.expanduser('~'))
            if not directory:
                return
            self.current_document.gamedirectory = directory
        gamepath = f'{self.current_document.gamedirectory}/ragtime.exe'
        try:
            subprocess.call(gamepath)
        except BaseException as e:
            print(e)
            self.current_document.gamedirectory = None


class PlayerToolbar(QtWidgets.QToolBar):
    def __init__(self):
        super().__init__()
        self.setIconSize(QtCore.QSize(16, 16))
        self.previous = QtGui.QAction(get_icon('previous.png'), '', self)
        self.stop = QtGui.QAction(get_icon('stop.png'), '', self)
        self.play = QtGui.QAction(get_icon('play.png'), '', self)
        self.pause = QtGui.QAction(get_icon('pause.png'), '', self)
        self.next = QtGui.QAction(get_icon('next.png'), '', self)
        spacer = QtWidgets.QWidget()
        spacer.setSizePolicy(*[QtWidgets.QSizePolicy.Expanding] * 2)
        self.addWidget(spacer)
        self.addAction(self.previous)
        self.addAction(self.stop)
        self.addAction(self.play)
        self.addAction(self.pause)
        self.addAction(self.next)
        spacer = QtWidgets.QWidget()
        spacer.setSizePolicy(*[QtWidgets.QSizePolicy.Expanding] * 2)
        self.addWidget(spacer)


class MainToolbar(QtWidgets.QToolBar):
    def __init__(self):
        super().__init__()
        self.new = QtGui.QAction(get_icon('new.png'), '', self)
        self.open = QtGui.QAction(get_icon('open.png'), '', self)
        self.save = QtGui.QAction(get_icon('save.png'), '', self)
        self.export = QtGui.QAction(get_icon('export.png'), '', self)
        self.assign = QtGui.QAction(get_icon('assign.png'), '', self)
        self.play = QtGui.QAction(get_icon('play.png'), '', self)
        self.addAction(self.new)
        self.addAction(self.open)
        self.addAction(self.save)
        self.addSeparator()
        self.addAction(self.export)
        self.addAction(self.assign)
        self.addSeparator()
        self.addAction(self.play)


class Canvas(QtWidgets.QWidget):

    def __init__(self, document):
        super().__init__()
        self.document = document
        self.canvas = CanvasView(document)
        self.focus = self.canvas.focus
        self.updated = self.canvas.updated
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.canvas)


class CanvasView(QtWidgets.QWidget):
    updated = QtCore.Signal()

    def __init__(self, document):
        super().__init__()
        self.document = document
        self.viewportmapper = ViewportMapper()
        self.navigator = Navigator()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QtGui.QColor(25, 25, 25))
        painter.drawRect(event.rect())
        if self.document.current_image:
            image = self.document.current_image.image
            origins, overrides = self.document.palette_override
            if origins:
                image = switch_colors(image, origins, overrides)
            qimage = ImageQt.ImageQt(image)
            rect = QtCore.QRectF(
                0, 0, qimage.size().width(), qimage.size().height())
            rect = self.viewportmapper.to_viewport_rect(rect)
            qimage = qimage.scaled(
                rect.size().toSize(),
                QtCore.Qt.KeepAspectRatio,
                QtCore.Qt.FastTransformation)
            painter.drawImage(rect, qimage)
            painter.setBrush(QtCore.Qt.NoBrush)
            painter.setPen(QtCore.Qt.black)
            painter.drawRect(rect)
        painter.end()

    def mouseReleaseEvent(self, event):
        self.navigator.update(event, pressed=False)

    def mousePressEvent(self, event):
        self.setFocus(QtCore.Qt.MouseFocusReason)
        self.navigator.update(event, pressed=True)

    def keyPressEvent(self, event):
        self.navigator.update(event, pressed=True)
        self.repaint()

    def keyReleaseEvent(self, event):
        if event.isAutoRepeat():
            return
        self.navigator.update(event, pressed=False)
        self.repaint()

    def mouseMoveEvent(self, event):
        zooming = self.navigator.shift_pressed and self.navigator.alt_pressed
        if zooming:
            offset = self.navigator.mouse_offset(event.pos())
            if offset is not None and self.navigator.zoom_anchor:
                factor = (offset.x() + offset.y()) / 10
                self.zoom(factor, self.navigator.zoom_anchor)
                return self.repaint()
        if self.navigator.left_pressed and self.navigator.space_pressed:
            offset = self.navigator.mouse_offset(event.pos())
            if offset is not None:
                self.viewportmapper.origin = (
                    self.viewportmapper.origin - offset)
        elif self.navigator.left_pressed:
            offset = self.navigator.mouse_offset(event.pos())
            if offset and offset.x() > 0.5:
                self.document.index += 1
                self.updated.emit()
            elif offset and offset.x() < -0.5:
                self.document.index -= 1
                self.updated.emit()
        self.repaint()

    def resizeEvent(self, event):
        check = (
            event.size().width(), event.size().height(),
            event.oldSize().height(), event.oldSize().width())
        if 0 in check or -1 in check:
            return
        self.viewportmapper.viewsize = event.size()
        size = (event.size() - event.oldSize()) / 2
        offset = QtCore.QPointF(size.width(), size.height())
        self.viewportmapper.origin -= offset
        self.repaint()

    def focus(self):
        if not self.document.current_image:
            return
        self.viewportmapper.viewsize = self.size()
        size = self.document.current_image.image.size
        rect = QtCore.QRect(0, 0, size[0], size[1])
        self.viewportmapper.focus(rect)
        self.repaint()

    def wheelEvent(self, event):
        factor = .25 if event.angleDelta().y() > 0 else -.25
        zoom(self.viewportmapper, factor, event.position())
        self.repaint()


class NamesModel(QtCore.QAbstractListModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.document = None

    def rowCount(self, *_):
        if self.document is None:
            return 0
        return len(self.document.data.get('names', []))

    def set_document(self, document):
        self.layoutAboutToBeChanged.emit()
        self.document = document
        self.layoutChanged.emit()

    def data(self, index, role):
        if role == QtCore.Qt.DisplayRole:
            return self.document.data.get('names', [])[index.row()]


class CharacterParameters(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.document = None
        self.name = QtWidgets.QLineEdit()
        self.name.textEdited.connect(self.update)

        self.names = QtWidgets.QListView()
        mode = QtWidgets.QAbstractItemView.ExtendedSelection
        self.names.setSelectionMode(mode)
        self.names_model = NamesModel()
        self.names.setModel(self.names_model)
        add = QtWidgets.QPushButton('Add')
        add.released.connect(self.add_names)
        remove = QtWidgets.QPushButton('Remove')
        remove.released.connect(self.remove_names)

        names = QtWidgets.QWidget()
        buttons = QtWidgets.QHBoxLayout()
        buttons.setContentsMargins(0, 0, 0, 0)
        buttons.addWidget(add)
        buttons.addWidget(remove)
        names_layout = QtWidgets.QVBoxLayout(names)
        names_layout.setContentsMargins(0, 0, 0, 0)
        names_layout.addWidget(self.names)
        names_layout.addLayout(buttons)

        layout = QtWidgets.QFormLayout(self)
        layout.addRow('Name', self.name)
        layout.addRow('Diplay names', names)

    def set_document(self, document):
        if not document:
            return
        self.document = document
        self.name.blockSignals(True)
        self.name.setText(self.document.data['name'])
        self.name.blockSignals(False)
        self.names_model.set_document(document)

    def update(self):
        if not self.document:
            return
        self.document.data['name'] = self.name.text()

    def add_names(self):
        names, _ = QtWidgets.QInputDialog.getText(
            self, 'Names', 'Enter names, split names with a coma')
        if not names:
            return
        names = [n.strip(' ') for n in names.split(',')]
        self.names_model.layoutAboutToBeChanged.emit()
        data = self.document.data.setdefault('names', [])
        data.extend(names)
        self.names_model.layoutChanged.emit()

    def remove_names(self):
        rows = self.names.selectionModel().selectedRows()
        if not rows:
            return
        self.names_model.layoutAboutToBeChanged.emit()
        for row in sorted(rows, reverse=True):
            self.document.data['names'].pop(row.row())
        self.names_model.layoutChanged.emit()


class CharacterAssignment(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setWindowTitle('Assign to scenes')
        self.directory = QtWidgets.QLineEdit()
        self.directory.textEdited.connect(self.directory_set)
        self.select_directory = QtWidgets.QPushButton('Browse')
        self.select_directory.released.connect(self.call_select_directory)

        directory_layout = QtWidgets.QHBoxLayout()
        directory_layout.setContentsMargins(0, 0, 0, 0)
        directory_layout.addWidget(self.directory)
        directory_layout.addWidget(self.select_directory)

        self.scenes = QtWidgets.QComboBox()
        self.scenes.currentTextChanged.connect(self.update_scene)
        self.characters = QtWidgets.QListWidget()
        self.characters.itemChanged.connect(self.item_changed)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addLayout(directory_layout)
        layout.addWidget(self.scenes)
        layout.addWidget(self.characters)
        self.directory_set('')

    def item_changed(self, item):
        if not item:
            return
        characters = []
        for row in range(self.characters.count()):
            item = self.characters.item(row)
            if item.checkState() == QtCore.Qt.Checked:
                characters.append(f'resources/animdata/{item.text()}')
        scene = self.scenes.currentText()
        ressources_directory = f'{self.directory.text()}/lib/resources'
        scene_directory = f'{ressources_directory}/scenes'
        with open(f'{scene_directory}/{scene}', 'r') as f:
            data = json.load(f)
        data['characters'] = characters
        with open(f'{scene_directory}/{scene}', 'w') as f:
            json.dump(data, f, indent=2)

    def call_select_directory(self):
        directory = QtWidgets.QFileDialog.getExistingDirectory()
        if not directory:
            return
        self.directory.setText(directory)
        self.directory_set(directory)

    def directory_set(self, directory):
        ressources_directory = f'{directory}/lib/resources'
        skins_directory = f'{ressources_directory}/skins'
        data_directory = f'{ressources_directory}/animdata'
        directories = skins_directory, data_directory
        enabled = all(os.path.exists(d) for d in directories)
        self.scenes.setEnabled(enabled)
        self.characters.setEnabled(enabled)
        if not enabled:
            return
        scene_directory = f'{ressources_directory}/scenes'
        scenes = [
            f for f in os.listdir(scene_directory)
            if os.path.splitext(f)[-1].lower() == '.json']
        self.scenes.clear()
        self.scenes.addItems(scenes)
        characters_directory = f'{ressources_directory}/animdata'
        characters = list_playable_characters(characters_directory)
        self.characters.clear()
        for character in characters:
            item = QtWidgets.QListWidgetItem()
            item.setText(character)
            item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
            item.setCheckState(QtCore.Qt.Unchecked)
            self.characters.addItem(item)
        self.update_scene()

    def update_scene(self, *_):
        if not self.scenes.isEnabled():
            return
        scene = self.scenes.currentText()
        ressources_directory = f'{self.directory.text()}/lib/resources'
        scene_directory = f'{ressources_directory}/scenes'
        with open(f'{scene_directory}/{scene}', 'r') as f:
            data = json.load(f)
        for row in range(self.characters.count()):
            item = self.characters.item(row)
            path_in_data = f'resources/animdata/{item.text()}'
            if path_in_data in data['characters']:
                item.setCheckState(QtCore.Qt.Checked)
            else:
                item.setCheckState(QtCore.Qt.Unchecked)


class Exporter(QtWidgets.QDialog):
    def __init__(self, image, data, document, parent=None):
        super().__init__(parent=parent)
        self.image = image
        self.document = document
        self.data = data
        self.label = QtWidgets.QLabel()
        self.label.setPixmap(QtGui.QPixmap.fromImage(self.image))
        self.label.setFixedSize(self.image.size())
        self.package = QtWidgets.QPushButton('Export package')
        self.package.released.connect(self.call_export_package)
        self.togame = QtWidgets.QPushButton('Import in game')
        self.togame.released.connect(self.call_import_in_game)
        layout = QtWidgets.QHBoxLayout()
        layout.addStretch()
        layout.addWidget(self.package)
        layout.addWidget(self.togame)
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addWidget(self.label)
        self.layout.addLayout(layout)

    def call_export_package(self):
        directory = QtWidgets.QFileDialog.getExistingDirectory(
            parent=self,
            caption='Select output folder',
            dir=os.path.expanduser('~'))
        if not directory:
            return

        directory = f'{directory}/{self.data["name"]}'
        data_filename = f'{directory}/{self.data["name"]}.json'
        spritesheet_filename = f'{directory}/{self.data["name"]}.png'
        filenames = (data_filename, spritesheet_filename)
        if any(os.path.exists(f) for f in filenames):
            result = QtWidgets.QMessageBox.question(
                parent=self,
                title='Overwrite files',
                text=(
                    f'{filenames} already exists.'
                    'Would you like to overwrite them ?'),
                button0=QtWidgets.QMessageBox.Yes,
                button1=QtWidgets.QMessageBox.No,
                defaultButton=QtWidgets.QMessageBox.No)
            if result == QtWidgets.QMessageBox.No:
                return

        if not os.path.exists(directory):
            os.makedirs(directory)
        with open(data_filename, 'w') as f:
            json.dump(self.data, f, indent=2)
        self.image.save(spritesheet_filename, 'PNG')
        self.accept()

    def call_import_in_game(self):
        directory = QtWidgets.QFileDialog.getExistingDirectory(
            parent=self,
            caption='Select output folder',
            dir=self.document.gamedirectory or '')
        if not directory:
            return
        self.document.gamedirectory = directory
        ressources_directory = f'{directory}/lib/resources'
        skins_directory = f'{ressources_directory}/skins'
        data_directory = f'{ressources_directory}/animdata'
        directories = skins_directory, data_directory
        if not all(os.path.exists(d) for d in directories):
            m = f'"{directory}" is not a valid Ragtime-Rumble game directory'
            return QtWidgets.QMessageBox.critical(
                parent=self,
                title='Wrong directory',
                text=m)
        data_filename = f'{data_directory}/{self.data["name"]}.json'
        spritesheet_filename = f'{skins_directory}/{self.data["name"]}.png'
        with open(data_filename, 'w') as f:
            json.dump(self.data, f, indent=2)
        self.image.save(spritesheet_filename, 'PNG')


def list_playable_characters(directory):
    result = []
    for character in os.listdir(directory):
        if os.path.splitext(character)[-1].lower() != '.json':
            continue
        try:
            with open(f'{directory}/{character}', 'r') as f:
                if json.load(f).get('type') == 'playable':
                    result.append(character)
        except Exception:
            print('failed', character)
            continue
    return result
