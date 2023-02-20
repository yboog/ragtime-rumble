
import sys
# import pickle
import pygame

from ragtimerumble.io import load_skins, load_main_resources
from ragtimerumble.render import render_game
from ragtimerumble.scene import GameLoop
from ragtimerumble import debug

pygame.init()
screen = pygame.display.set_mode((640, 360), pygame.SCALED | pygame.FULLSCREEN)
# screen = pygame.display.set_mode((640, 360), pygame.SCALED)
# screen = pygame.display.set_mode((640, 360))
pygame.joystick.init()
load_skins()
load_main_resources()
scene = 'resources/scenes/saloon.json'
loop = GameLoop()
loop.set_scene(scene)
loop.start_scene()
replay = []
while not loop.done:
    next(loop)
    # replay.append(pickle.dumps(scene))
    render_game(screen, loop)
    pygame.display.update()
    if debug.log_coordinates:
        debug.log_npc_coordinates(loop.scene)

debug.close()
sys.exit(0)
