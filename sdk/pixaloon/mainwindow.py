import os
import json
import shutil
from functools import partial

from PySide6 import QtWidgets, QtCore, QtGui
from pixaloon.actions import TOOL_ACTIONS
from pixaloon.attributeeditor import AttributeEditor
from pixaloon.canvas.canvas import LevelCanvas
from pixaloon.canvas.paint import render_placeholder_image
from pixaloon.document import Document
from pixaloon.io import get_icon
from pixaloon.heatmap import HeatmapDisplayWidget
from pixaloon.options import OptionsEditor
from pixaloon.path import relative_normpath
from pixaloon.pop import run_game
from pixaloon.objectlist import ObjectsList
from pixaloon.sceneeditor import SceneEditor
from pixaloon.canvas.tools.basetool import NavigationTool


PIXALOON = 'Pixaloon'


class Pixaloon(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(PIXALOON)

        self.mdi = QtWidgets.QMdiArea()
        self.setCentralWidget(self.mdi)
        self.mdi.subWindowActivated.connect(self.sub_window_changed)
        self.mdi.setViewMode(QtWidgets.QMdiArea.TabbedView)
        self.mdi.setTabsClosable(True)

        self.tools_windows = []

        self.actions = []
        self.navigate = QtGui.QAction(get_icon('navigate.png'), '', self)
        self.navigate.triggered.connect(partial(self.set_tool_mode, 0))
        self.navigate.setChecked(True)
        self.navigate.setCheckable(True)
        self.create = QtGui.QAction(get_icon('add.png'), '', self)
        self.create.triggered.connect(partial(self.set_tool_mode, 1))
        self.create.setCheckable(True)
        self.edit = QtGui.QAction(get_icon('edit.png'), '', self)
        self.edit.triggered.connect(partial(self.set_tool_mode, 2))
        self.edit.setCheckable(True)

        self.attributeeditor = AttributeEditor()

        self.dataeditor = ObjectsList()
        self.dataeditor.data_updated.connect(
            lambda: self.current_canvas().update())

        self.sceneeditor = SceneEditor()
        self.sceneeditor.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Fixed)

        self.optioneditor = OptionsEditor()
        self.optioneditor.option_set.connect(
            lambda: self.current_canvas().update())
        self.optioneditor.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Fixed)

        tools = QtGui.QActionGroup(self)
        tools.setExclusive(True)
        tools.addAction(self.navigate)
        tools.addAction(self.create)
        tools.addAction(self.edit)

        tools = QtGui.QActionGroup(self)
        tools.setExclusive(True)
        tools.triggered.connect(self.tool_changed)

        self.tools_actions = []
        for data in TOOL_ACTIONS:
            action = QtGui.QAction(get_icon(data['icon']), '', self)
            action.setToolTip(data['tooltip'])
            action.element_type = data['element_type']
            cls = data.get('tool_cls')
            action.tool = cls() if cls else NavigationTool()
            action.setCheckable(True)
            self.tools_actions.append(action)
            tools.addAction(action)
        self.tools_actions[0].setChecked(True)

        self.modes_toolbar = QtWidgets.QToolBar()
        self.modes_toolbar.addAction(self.navigate)
        self.modes_toolbar.addAction(self.create)
        self.modes_toolbar.addAction(self.edit)

        self.tools_toolbar = QtWidgets.QToolBar()
        self.tools_toolbar.addActions(self.tools_actions)

        self.option_dock = QtWidgets.QDockWidget()
        self.option_dock.setWindowTitle('Option')
        self.option_dock.setWidget(self.optioneditor)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.option_dock)

        self.scene_dock = QtWidgets.QDockWidget()
        self.scene_dock.setWindowTitle('Scene')
        self.scene_dock.setWidget(self.sceneeditor)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.scene_dock)

        self.data_dock = QtWidgets.QDockWidget()
        self.data_dock.setWindowTitle('Objects')
        self.data_dock.setWidget(self.dataeditor)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.data_dock)

        self.attributes_dock = QtWidgets.QDockWidget()
        self.attributes_dock.setWindowTitle('Attributes')
        self.attributes_dock.setWidget(self.attributeeditor)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.attributes_dock)

        self.addToolBar(QtCore.Qt.TopToolBarArea, self.modes_toolbar)
        self.addToolBar(QtCore.Qt.TopToolBarArea, self.tools_toolbar)
        self.setCentralWidget(self.mdi)

        self.resizeDocks([self.data_dock], [300], QtCore.Qt.Horizontal)
        self.register_actions()
        self.create_menu()

    def create_menu(self):
        new = QtGui.QAction('New', self)
        new.triggered.connect(self.create_new)
        open_ = QtGui.QAction('Open', self)
        open_.triggered.connect(self.open_document_prompt)
        save = QtGui.QAction('Save', self)
        save.triggered.connect(self.save_current_document)
        save_as = QtGui.QAction('Save as', self)
        save_as.triggered.connect(self.save_current_document_as)
        exit_action = QtGui.QAction('Exit', self)
        exit_action.triggered.connect(self.close)

        filemenu = QtWidgets.QMenu('File', self)
        filemenu.addAction(new)
        filemenu.addAction(open_)
        filemenu.addAction(save)
        filemenu.addAction(save_as)
        filemenu.addSeparator()
        filemenu.addAction(exit_action)

        self.menuBar().addMenu(filemenu)

        import_prop = QtGui.QAction('Prop', self)
        import_prop.triggered.connect(self.import_prop)

        import_menu = QtWidgets.QMenu('Import')
        import_menu.addAction(import_prop)

        self.menuBar().addMenu(import_menu)

        run_game = QtGui.QAction('Run game', self)
        run_game.triggered.connect(
            lambda: RunGameDialog(self.current_canvas().document).exec())
        heatmap_analytics = QtGui.QAction('Heat map analytics', self)
        heatmap_analytics.triggered.connect(self.open_hitmap_display)
        txt = 'Render placeholder background'
        render_placeholder = QtGui.QAction(txt, self)
        render_placeholder.triggered.connect(self.render_placeholders)

        tools_menu = QtWidgets.QMenu('Tools')
        tools_menu.addAction(run_game)
        tools_menu.addAction(heatmap_analytics)
        tools_menu.addAction(render_placeholder)

        self.menuBar().addMenu(tools_menu)

    def import_prop(self):
        document = self.current_canvas().document
        filepath, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, 'Import prop',
            document.gameroot, '*.png')
        if not filepath:
            return
        image = QtGui.QImage(filepath)

        if not filepath.replace('\\', '/').startswith(document.gameroot):
            dst = f'{document.gameroot}/props/{os.path.basename(filepath)}'
            shutil.copy(filepath, dst)
            filepath = relative_normpath(dst, document)
        else:
            filepath = relative_normpath(filepath, document)

        document.data['props'].append({
            'gametypes': ['advanced', 'basic'],
            'visible_at_dispatch': True,
            'file': filepath,
            'center': [0, 0],
            'position': [0, 0],
            'box': [0, 0, *image.size().toTuple()]})
        document.update_qimages()
        document.edited.emit()

    def sub_window_changed(self, window):
        canvas = window.widget() if window else None
        if not canvas:
            return
        for action in self.tools_actions:
            action.tool.canvas = canvas
        self.set_document(canvas.document)
        self.update_window_title()

    def set_tool_mode(self, mode):
        for window in self.mdi.subWindowList():
            window.widget().toolmode.mode = mode

    def sizeHint(self):
        return QtCore.QSize(1300, 800)

    def tool_changed(self, action):
        for window in self.mdi.subWindowList():
            window.widget().tool = action.tool
            window.widget().update()
            window.widget().document.elements_to_render = [action.element_type]
        self.dataeditor.set_element_type(action.element_type)

    def set_document(self, document):
        self.dataeditor.set_document(document)
        self.sceneeditor.set_document(document)
        self.optioneditor.set_document(document)
        self.attributeeditor.set_document(document)

    def register_actions(self):
        action = QtGui.QAction('Focus', self)
        action.triggered.connect(self.focus_canvas)
        action.setShortcut(QtGui.QKeySequence('F'))
        self.actions.append(action)
        self.addAction(action)

        action = QtGui.QAction('Delete selection', self)
        action.triggered.connect(self.delete_selection)
        action.setShortcut(QtGui.QKeySequence('DEL'))
        self.actions.append(action)
        self.addAction(action)

    def delete_selection(self):
        canvas = self.current_canvas()
        if canvas:
            canvas.document.delete_selection()

    def focus_canvas(self):
        self.current_canvas().focus()

    def open_document(self, filepath):
        document = Document.open(filepath)
        name = os.path.basename(filepath)
        self.create_sub_window(document, name)

    def open_document_prompt(self):
        filepaths, _ = QtWidgets.QFileDialog.getOpenFileNames(
            self, 'Open levels', filter='*.json')
        if not filepaths:
            return
        for filepath in filepaths:
            self.open_document(filepath)
        self.update_window_title()

    def create_sub_window(self, document, name):
        canvas = LevelCanvas(document, self)
        canvas.setWindowTitle(name)
        self.mdi.addSubWindow(canvas)
        self.set_document(document)
        self.update_window_title()

    def save_current_document(self):
        document = self.current_canvas().document
        if not document.filepath:
            return self.save_current_document_as(self)
        with open(document.filepath, 'w') as f:
            import pprint
            pprint.pprint(document.data)
            json.dump(document.data, f, indent=2)

    def save_current_document_as(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, 'Save as', filter='*json')
        if not path:
            return
        self.current_canvas().document.filepath = path
        self.save_current_document()
        self.update_window_title()

    def update_window_title(self):
        fp = self.current_canvas().document.filepath
        if not fp:
            self.setWindowTitle(PIXALOON)
            return
        self.setWindowTitle(f'{PIXALOON} - {fp}')

    def create_new(self):
        fp = f'{os.path.dirname(__file__)}/resources/emptylevel.json'
        with open(fp, 'r') as f:
            data = json.load(f)
        r = QtWidgets.QFileDialog.getExistingDirectory(self, 'Select GameRoot')
        if not r:
            return
        document = Document(gameroot=r, data=data)
        self.create_sub_window(document, 'Untitled')

    def current_canvas(self):
        return self.mdi.currentSubWindow().widget()

    def open_hitmap_display(self):
        filepath, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, 'Open heat map file', filter='*.pkl')
        if not filepath:
            return
        window = HeatmapDisplayWidget(filepath, self)
        self.tools_windows.append(window)
        window.show()

    def render_placeholders(self):
        document = self.current_canvas().document
        image = render_placeholder_image(document)
        image.save(f'{document.gameroot}/{document.get_placeholder_path()}')
        document.update_placeholder()


class RunGameDialog(QtWidgets.QDialog):
    def __init__(self, document, parent=None):
        super().__init__(parent)

        self.document = document
        self.default_scene = QtWidgets.QCheckBox('Test with current scene')
        self.default_scene.setChecked(True)
        self.loop_on_default_scene = QtWidgets.QCheckBox('Loop on current scene')
        self.loop_on_default_scene.setChecked(True)


        self.windowed = QtWidgets.QCheckBox('Windowed')
        self.windowed.setChecked(True)

        self.record_replay = QtWidgets.QCheckBox('Record replay')
        self.record_replay.setChecked(True)

        self.replay_path = QtWidgets.QLineEdit()
        self.replay_path.setReadOnly(True)

        self.replay_browse = QtWidgets.QPushButton()
        self.replay_browse.setIcon(get_icon('open.png'))
        self.replay_browse.setFixedWidth(30)
        self.replay_browse.released.connect(self.select_file)
        self.clear_replay = QtWidgets.QPushButton('X')
        self.clear_replay.setFixedWidth(30)
        self.clear_replay.released.connect(
            lambda: self.replay_browse.setText(''))

        run = QtWidgets.QPushButton('Run')
        run.released.connect(self.accept)

        replay_layout = QtWidgets.QHBoxLayout()
        replay_layout.setContentsMargins(0, 0, 0, 0)
        replay_layout.setSpacing(0)
        replay_layout.addWidget(self.replay_path)
        replay_layout.addWidget(self.replay_browse)
        replay_layout.addWidget(self.clear_replay)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.default_scene)
        layout.addWidget(self.loop_on_default_scene)
        layout.addWidget(self.windowed)
        layout.addWidget(self.record_replay)
        layout.addLayout(replay_layout)
        layout.addWidget(run)

    def select_file(self):
        filepath, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, 'Record path', self.document.gameroot, filter='*.pkl')
        if not filepath:
            return
        self.replay_path.setText(filepath)

    def accept(self):
        try:
            replay_path = self.replay_path.text() or None
            replay_path = replay_path if self.record_replay.isChecked() else None
            run_game(
                document=self.document,
                loop_on_default_scene=self.loop_on_default_scene.isChecked(),
                windowed=self.windowed.isChecked(),
                use_document_as_default_scene=self.default_scene.isChecked(),
                record_replay_filepath=replay_path)
            super().accept()
        except BaseException as e:
            QtWidgets.QMessageBox.critical(self, 'Error', str(e))
