from copy import deepcopy
from PySide6 import QtGui, QtCore, QtWidgets
from pixaloon.canvas.tools.basetool import NavigationTool
from pixaloon.selection import Selection
from pixaloon.toolmode import ToolMode


NPC_TYPES = {
    'barman': {
        "type": "barman",
        "file": "resources/animdata/barman.json",
        "gametypes": ["advanced"],
        "startposition": [0, 0],
        "direction": "left",
        "blendmode": "normal",
        "path": [[0, 0], [0, 50]]},
    'chicken': {
        "type": "chicken",
        "file": "resources/animdata/chicken.json",
        "gametypes": ["basic", "advanced"],
        "startposition": [0, 0],
        "zone": [0, 0, 50, 50],
        "blendmode": "normal",
        "run_radius": 50},
    'dog': {
        "type": "dog",
        "file": "resources/animdata/diego.json",
        "gametypes": ["basic", "advanced"],
        "startposition": [0, 107],
        "direction": "right",
        "blendmode": "normal",
        "path": [[0, 0], [0, 50]]},
    'ghost': {
        "type": "ghost",
        "file": "resources/animdata/ghost.json",
        "gametypes": ["basic", "advanced"],
        "startposition": [0, 107],
        "direction": "right",
        "blendmode": "normal",
        "zone": [0, 0, 640, 360]},
    'loop': {
        "type": "loop",
        "file": "resources/animdata/banjo.json",
        "gametypes": ["basic", "advanced"],
        "position": [0, 0],
        "blendmode": "normal",
        "switch": 243},
    'pianist': {
        "type": "pianist",
        "file": "resources/animdata/pianist.json",
        "gametypes": ["basic", "advanced"],
        "blendmode": "normal",
        "startposition": [0, 0]},
    'sniper': {
        "type": "sniper",
        "file": "resources/animdata/sniper.json",
        "gametypes": ["advanced"],
        "startposition": [0, 0],
        "y": 400,
        "zone": [0, 0, 150, 150],
        "blendmode": "normal",
        "interaction_zone": [-50, -50, 60, 60]},
    'saloon-door': {
        "file": "resources/animdata/saloon-door-a.json",
        "gametypes": ["basic", "advanced"],
        "type": "saloon-door",
        "position": [0, 0],
        "switch": 94,
        "zone": [95, 83, 47, 9],
        "blendmode": "normal",
    }
}


class NpcTool(NavigationTool):
    def mouseReleaseEvent(self, event):
        conditions = (
            self.toolmode.mode != ToolMode.CREATE or
            event.button() != QtCore.Qt.LeftButton)
        if conditions:
            return
        menu = QtWidgets.QMenu(self.canvas)
        menu.addActions([QtGui.QAction(t, self.canvas) for t in NPC_TYPES])
        action = menu.exec_(self.canvas.mapToGlobal(event.pos()))
        point = self.viewportmapper.to_units_coords(event.pos()).toPoint()
        x, y = point.toTuple()
        data = deepcopy(NPC_TYPES[action.text()])
        data['gametypes'] = self.document.gametypes_display_filters
        if 'startposition' in data:
            data['startposition'] = [x, y]
        if 'position' in data:
            data['position'] = [x, y]
        if 'path' in data:
            for point in data['path']:
                point[0] = point[0] + x
                point[1] = point[1] + y
        if data['type'] == 'loop':
            data['switch'] += y
        if data['type'] == 'chicken':
            data['zone'][0] = x
            data['zone'][1] = y
        if data['type'] == 'sniper':
            data['zone'][0] = x
            data['zone'][1] = y
            data['interaction_zone'][0] += x
            data['interaction_zone'][1] += y
        if data['type'] == 'saloon':
            data['zone'][0] += x
            data['zone'][1] += y
        self.document.data['npcs'].append(data)
        self.selection.tool = Selection.NPC
        self.selection.data = len(self.document.data['npcs']) - 1
        self.selection.changed.emit(self.canvas)
        self.document.edited.emit()
