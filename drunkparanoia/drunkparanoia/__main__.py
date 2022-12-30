
import sys
# import pickle
import pygame

from drunkparanoia.io import load_skins, load_main_resources
from drunkparanoia.render import render_game
from drunkparanoia.scene import load_scene, GameLoop

pygame.init()
screen = pygame.display.set_mode((640, 360), pygame.SCALED | pygame.FULLSCREEN)
# screen = pygame.display.set_mode((640, 360), pygame.SCALED)
screen = pygame.display.set_mode((640, 360))
pygame.joystick.init()
load_skins()
load_main_resources()

scene = load_scene('resources/scenes/saloon.json')
loop = GameLoop()
loop.start_scene(scene)
replay = []
while not loop.done:
    next(loop)
    # replay.append(pickle.dumps(scene))
    render_game(screen, loop)
    pygame.display.update()
sys.exit(0)