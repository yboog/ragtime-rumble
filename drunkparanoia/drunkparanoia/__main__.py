import pygame

pygame.init()
screen = pygame.display.set_mode((640, 360), pygame.SCALED)
pygame.joystick.init()

from drunkparanoia.io import load_skins
load_skins()

import json
from drunkparanoia.config import GAMEROOT
from drunkparanoia.character import Player, Character
from drunkparanoia.render import render_game
from drunkparanoia.sprite import SpriteSheet

sheet_path = f'{GAMEROOT}/resources/animdata/smith.json'
with open(sheet_path, 'r') as f:
    data = json.load(f)

spritesheet = SpriteSheet(data)
character = Character((150, 150), spritesheet)
joystick = pygame.joystick.Joystick(0)
joystick.init()
player = Player(character, joystick)

clock = pygame.time.Clock()
while True:
    for event in pygame.event.get():
        if (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
                or event.type == pygame.QUIT):
            pygame.quit()
    next(player)
    render_game(screen, [character])
    clock.tick(60)
    pygame.display.update()