
import sys
import pygame

from ragtimerumble.io import load_skins, load_main_resources
from ragtimerumble.config import DISPLAY_MODES
from ragtimerumble.display import set_screen_display_mode, get_screen
from ragtimerumble.gameloop import GameLoop
from ragtimerumble.render import render_game
from ragtimerumble import debug


pygame.init()
set_screen_display_mode(DISPLAY_MODES.FULSCREEN)
pygame.joystick.init()
load_skins()
load_main_resources()
scene = 'resources/scenes/saloon.json'
loop = GameLoop()
loop.set_scene(scene)
replay = []
while not loop.done:
    next(loop)
    # replay.append(pickle.dumps(scene))
    render_game(get_screen(), loop)
    pygame.display.update()
    if debug.log_coordinates:
        debug.log_npc_coordinates(loop.scene)

debug.close()
sys.exit(0)
