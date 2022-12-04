
import pygame
from drunkparanoia.io import load_skins
from drunkparanoia.render import render_game
from drunkparanoia.scene import load_scene


pygame.init()
# screen = pygame.display.set_mode((640, 360), pygame.SCALED | pygame.FULLSCREEN)
screen = pygame.display.set_mode((640, 360), pygame.SCALED)
pygame.joystick.init()
load_skins()

scene = load_scene('resources/scenes/saloon.json')
joystick = pygame.joystick.Joystick(0)
joystick.init()
scene.assign_player(0, joystick)
scene.create_npcs()

from drunkparanoia.sprite import image_index_from_durations

clock = pygame.time.Clock()
while True:
    for event in pygame.event.get():
        if (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
                or event.type == pygame.QUIT):
            pygame.quit()
    next(scene)
    render_game(screen, scene)
    clock.tick(60)
    pygame.display.update()