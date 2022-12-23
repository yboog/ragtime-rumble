
import sys
# import pickle
import pygame

from drunkparanoia.io import load_skins
from drunkparanoia.render import render_game, render_no_player
from drunkparanoia.scene import load_scene

pygame.init()
screen = pygame.display.set_mode((640, 360), pygame.SCALED | pygame.FULLSCREEN)
# screen = pygame.display.set_mode((640, 360), pygame.SCALED)
# screen = pygame.display.set_mode((640, 360))
pygame.joystick.init()
load_skins()

scene = load_scene('resources/scenes/saloon.json')
for i in range(min(4, pygame.joystick.get_count())):
    joystick = pygame.joystick.Joystick(i)
    joystick.init()
    scene.create_player(joystick)

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
    # if not scene.players:
    #     render_no_player(screen)
    #     clock.tick(60)
    #     pygame.display.update()
    #     continue
    next(scene)
    # replay.append(pickle.dumps(scene))
    render_game(screen, scene)
    clock.tick(60)
    pygame.display.update()
sys.exit(0)