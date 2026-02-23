from pixaloon.canvas.tools.interaction import InteractionTool
from pixaloon.canvas.tools.overlays import OverlayTool
from pixaloon.canvas.tools.path import PathTool
from pixaloon.canvas.tools.popspots import PopSpotTool
from pixaloon.canvas.tools.square import FenceTool, StairTool
from pixaloon.canvas.tools.score import ScoreTool
from pixaloon.canvas.tools.shadow import ShadowTool
from pixaloon.canvas.tools.startups import StartupTool
from pixaloon.canvas.tools.target import TargetTool
from pixaloon.canvas.tools.wall import WallTool


TOOL_ACTIONS = [
    {
        'icon': 'background.png',
        'tooltip': 'Backgrounds',
        'element_type': 'backgrounds',
        'tool_cls': None,
        'checkable': True,
    },
    {
        'icon': 'spot.png',
        'tooltip': 'Pop spots',
        'element_type': 'popspots',
        'tool_cls': PopSpotTool,
        'checkable': True,
    },
    {
        'icon': 'startup.png',
        'tooltip': 'Spawn spots',
        'tool_cls': None,
        'element_type': 'startups',
        'tool_cls': StartupTool,
        'checkable': True,
    },
    {
        'icon': 'wall.png',
        'tooltip': 'Walls',
        'element_type': 'walls',
        'checkable': True,
        'tool_cls': WallTool,
    },
    {
        'icon': 'stair.png',
        'tooltip': 'Stairs',
        'element_type': 'stairs',
        'checkable': True,
        'tool_cls': StairTool,
    },
    {
        'icon': 'fence.png',
        'tooltip': 'Fences',
        'element_type': 'fences',
        'checkable': True,
        'tool_cls': FenceTool,
    },
    {
        'icon': 'shadow.png',
        'tooltip': 'Shadow zone',
        'element_type': 'shadows',
        'checkable': True,
        'tool_cls': ShadowTool,
    },
    {
        'icon': 'prop.png',
        'tooltip': 'Props',
        'element_type': 'props',
        'checkable': True,
    },
    {
        'icon': 'interaction.png',
        'tooltip': 'Interactive zones',
        'element_type': 'interactions',
        'checkable': True,
        'tool_cls': InteractionTool,
    },
    {
        'icon': 'switch.png',
        'tooltip': 'Switch over/below',
        'element_type': 'overlays',
        'checkable': True,
        'tool_cls': OverlayTool,
    },
    {
        'icon': 'path.png',
        'tooltip': 'Path finding',
        'element_type': 'paths',
        'tool_cls': PathTool,
        'checkable': True,
    },
    {
        'icon': 'target.png',
        'tooltip': 'Targets',
        'element_type': 'targets',
        'tool_cls': TargetTool,
        'checkable': True,
    },
    {
        'icon': 'coin.png',
        'tooltip': 'Coin',
        'element_type': 'score',
        'tool_cls': ScoreTool,
        'checkable': True,
    }]
