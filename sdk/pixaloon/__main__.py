import sys
from functools import partial
sys.path.append('c:/perso/ragtime-rumble/sdk/')

from PySide6 import QtWidgets, QtCore, QtGui
from pixaloon.attributeeditor import AttributeEditor
from pixaloon.canvas.canvas import LevelCanvas
from pixaloon.dataeditor import DataEditor
from pixaloon.document import Document
from pixaloon.io import get_icon
from pixaloon.options import OptionsEditor
from pixaloon.selection import Selection
from pixaloon.sceneeditor import SceneEditor

from pixaloon.canvas.tools.fence import FenceTool
from pixaloon.canvas.tools.interaction import InteractionTool
from pixaloon.canvas.tools.overlays import OverlayTool
from pixaloon.canvas.tools.popspots import PopSpotTool
from pixaloon.canvas.tools.wall import WallTool


class Pixaloon(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.document = None
        self.canvas = LevelCanvas()

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

        self.attributeeditor = AttributeEditor(self.document)

        self.dataeditor = DataEditor(self.document)
        self.dataeditor.data_updated.connect(self.canvas.update)

        self.sceneeditor = SceneEditor(self.document)
        self.sceneeditor.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Fixed)

        self.optioneditor = OptionsEditor(self.document)
        self.optioneditor.option_set.connect(self.canvas.update)
        self.optioneditor.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Fixed)

        tools = QtGui.QActionGroup(self)
        tools.setExclusive(True)
        tools.addAction(self.navigate)
        tools.addAction(self.create)
        tools.addAction(self.edit)

        self.spot = QtGui.QAction(get_icon('spot.png'), '', self)
        self.spot.setToolTip('Pop spots')
        self.spot.element_type = 'popspots'
        self.spot.tool = PopSpotTool(self.canvas)
        self.spot.setCheckable(True)
        self.spot.setChecked(True)

        self.wall = QtGui.QAction(get_icon('wall.png'), '', self)
        self.wall.setToolTip('Walls')
        self.wall.element_type = 'walls'
        self.wall.setCheckable(True)
        self.wall.tool = WallTool(self.canvas)

        self.stair = QtGui.QAction(get_icon('stair.png'), '', self)
        self.stair.setToolTip('Stairs')
        self.stair.element_type = 'stairs'
        self.stair.setCheckable(True)

        self.fence = QtGui.QAction(get_icon('fence.png'), '', self)
        self.fence.setToolTip('Fences')
        self.fence.element_type = 'fences'
        self.fence.setCheckable(True)
        self.fence.tool = FenceTool(self.canvas)

        self.prop = QtGui.QAction(get_icon('prop.png'), '', self)
        self.prop.setToolTip('Props')
        self.prop.element_type = 'props'
        self.prop.setCheckable(True)
        self.interaction = QtGui.QAction(get_icon('interaction.png'), '', self)
        self.interaction.setToolTip('Interactive zones')
        self.interaction.element_type = 'interactions'
        self.interaction.setCheckable(True)
        self.interaction.tool = InteractionTool(self.canvas)

        self.switch = QtGui.QAction(get_icon('switch.png'), '', self)
        self.switch.setToolTip('Switch over/below')
        self.switch.element_type = 'switchs'
        self.switch.setCheckable(True)
        self.switch.tool = OverlayTool(self.canvas)

        self.startup = QtGui.QAction(get_icon('startup.png'), '', self)
        self.startup.setToolTip('Spawn spots')
        self.startup.element_type = 'startups'
        self.startup.setCheckable(True)

        self.path = QtGui.QAction(get_icon('path.png'), '', self)
        self.path.setToolTip('Path finding')
        self.path.element_type = 'paths'
        self.path.setCheckable(True)

        self.target = QtGui.QAction(get_icon('target.png'), '', self)
        self.target.setToolTip('Targets')
        self.target.element_type = 'targets'
        self.target.setCheckable(True)

        mode = QtGui.QActionGroup(self)
        mode.setExclusive(True)
        mode.addAction(self.spot)
        mode.addAction(self.wall)
        mode.addAction(self.stair)
        mode.addAction(self.fence)
        mode.addAction(self.prop)
        mode.addAction(self.interaction)
        mode.addAction(self.switch)
        mode.addAction(self.startup)
        mode.addAction(self.path)
        mode.addAction(self.target)
        mode.triggered.connect(self.mode_changed)

        self.tools_toolbar = QtWidgets.QToolBar()
        self.tools_toolbar.addAction(self.navigate)
        self.tools_toolbar.addAction(self.create)
        self.tools_toolbar.addAction(self.edit)

        self.modes_toolbar = QtWidgets.QToolBar()
        self.modes_toolbar.addAction(self.spot)
        self.modes_toolbar.addAction(self.wall)
        self.modes_toolbar.addAction(self.stair)
        self.modes_toolbar.addAction(self.fence)
        self.modes_toolbar.addAction(self.prop)
        self.modes_toolbar.addAction(self.interaction)
        self.modes_toolbar.addAction(self.switch)
        self.modes_toolbar.addAction(self.startup)
        self.modes_toolbar.addAction(self.path)
        self.modes_toolbar.addAction(self.target)


        self.option_dock = QtWidgets.QDockWidget()
        self.option_dock.setWindowTitle('Option')
        self.option_dock.setWidget(self.optioneditor)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.option_dock)

        self.scene_dock = QtWidgets.QDockWidget()
        self.scene_dock.setWindowTitle('Scene')
        self.scene_dock.setWidget(self.sceneeditor)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.scene_dock)

        self.data_dock = QtWidgets.QDockWidget()
        self.data_dock.setWindowTitle('Data Tables')
        self.data_dock.setWidget(self.dataeditor)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.data_dock)

        self.attributes_dock = QtWidgets.QDockWidget()
        self.attributes_dock.setWindowTitle('Attributes')
        self.attributes_dock.setWidget(self.attributeeditor)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.attributes_dock)

        self.addToolBar(QtCore.Qt.TopToolBarArea, self.tools_toolbar)
        self.addToolBar(QtCore.Qt.TopToolBarArea, self.modes_toolbar)
        self.setCentralWidget(self.canvas)

        self.resizeDocks([self.data_dock], [300], QtCore.Qt.Horizontal)
        self.register_actions()

    def set_tool_mode(self, mode):
        self.canvas.toolmode.mode = mode

    def sizeHint(self):
        return QtCore.QSize(1300, 800)

    def mode_changed(self, action):
        self.document.elements_to_render = [action.element_type]
        if hasattr(action, 'tool'):
            self.canvas.tool = action.tool
        else:
            from pixaloon.canvas.tools.basetool import NavigationTool
            self.canvas.tool = NavigationTool(self.canvas)
        self.dataeditor.set_element_type(action.element_type)
        self.canvas.repaint()

    def set_document(self, document):
        self.document = document
        self.canvas.set_document(document)
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
        if not self.document.selection:
            return
        if self.document.selection.tool == Selection.WALL:
            del self.document.data['walls'][self.document.selection.data]
        if self.document.selection.tool == Selection.NO_GO_ZONE:
            del self.document.data['no_go_zones'][self.document.selection.data]
        if self.document.selection.tool == Selection.INTERACTION:
            del self.document.data['interactions'][self.document.selection.data]
        if self.document.selection.tool == Selection.FENCE:
            del self.document.data['fences'][self.document.selection.data]
        if self.document.selection.tool == Selection.OVERLAY:
            del self.document.data['overlays'][self.document.selection.data]
            self.document.update_qimages()
        self.document.selection.clear()
        self.document.selection.changed.emit()
        self.document.edited.emit()

    def focus_canvas(self):
        self.canvas.focus()


if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    window = Pixaloon()
    document = Document.open(
        r'C:\perso\ragtime-rumble\ragtimerumble\resources\scenes\street.json')
    window.set_document(document)
    window.show()
    import os
    stylesheet_filepath = f'{os.path.dirname(__file__)}/css/dark.css'
    with open(stylesheet_filepath, 'r') as f:
        app.setStyleSheet(f.read())
    app.exec()
