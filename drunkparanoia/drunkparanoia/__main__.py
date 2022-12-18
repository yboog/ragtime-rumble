
import sys
import pickle
import pygame

from drunkparanoia.io import load_skins
from drunkparanoia.render import render_game
from drunkparanoia.scene import load_scene

pygame.init()
screen = pygame.display.set_mode((640, 360), pygame.SCALED | pygame.FULLSCREEN)
# screen = pygame.display.set_mode((640, 360), pygame.SCALED)
# screen = pygame.display.set_mode((640, 360))
pygame.joystick.init()
load_skins()

scene = load_scene('resources/scenes/saloon.json')
joystick = pygame.joystick.Joystick(0)
joystick.init()
scene.assign_player(0, joystick)
scene.create_npcs()

replay = []
clock = pygame.time.Clock()
continue_ = True
while continue_:
    for event in pygame.event.get():
        end = (
            event.type == pygame.KEYDOWN and
            event.key == pygame.K_ESCAPE or
            event.type == pygame.QUIT)
        if end:
            continue_ = False

    next(scene)
    # replay.append(pickle.dumps(scene))
    render_game(screen, scene)
    clock.tick(60)
    pygame.display.update()
sys.exit(0)
