import os
import json
from functools import partial

from PySide6 import QtWidgets, QtCore, QtGui

from pixaloon.actions import TOOL_ACTIONS
from pixaloon.attributeeditor import AttributeEditor
from pixaloon.canvas.canvas import LevelCanvas
from pixaloon.document import Document
from pixaloon.io import get_icon
from pixaloon.options import OptionsEditor
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
        save = QtGui.QAction('Save', self)
        save.triggered.connect(self.save_current_document)
        save_as = QtGui.QAction('Save as', self)
        save_as.triggered.connect(self.save_current_document_as)
        exit_action = QtGui.QAction('Exit', self)
        exit_action.triggered.connect(self.close)

        filemenu = QtWidgets.QMenu('File', self)
        filemenu.addAction(QtGui.QAction('New', self))
        filemenu.addAction(QtGui.QAction('Open', self))
        filemenu.addAction(save)
        filemenu.addAction(save_as)
        filemenu.addSeparator()
        filemenu.addAction(exit_action)

        self.menuBar().addMenu(filemenu)

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
        canvas = LevelCanvas(document, self)
        canvas.setWindowTitle(os.path.basename(filepath))
        self.mdi.addSubWindow(canvas)
        self.set_document(document)
        self.update_window_title()

    def save_current_document(self):
        document = self.current_canvas().document
        if not document.filepath:
            return self.save_current_document_as(self)
        with open(document.filepath, 'r') as f:
            json.dump(document.data, f, indent=2)

    def save_current_document_as(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, 'Save as', filter='*json')
        if not path:
            return
        self.current_canvas().document.filepath = path
        self.save_current_document()

    def update_window_title(self):
        fp = self.current_canvas().document.filepath
        if not fp:
            self.setWindowTitle(PIXALOON)
            return
        self.setWindowTitle(f'{PIXALOON} - {fp}')

    def current_canvas(self):
        return self.mdi.currentSubWindow().widget()

