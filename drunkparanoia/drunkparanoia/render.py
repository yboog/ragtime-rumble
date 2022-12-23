import numpy
import math
import pygame
from drunkparanoia.io import get_image
from drunkparanoia.config import COUNTDOWNS
from drunkparanoia.character import Character


def render_no_player(screen):
    color = 255, 255, 255
    font = pygame.font.SysFont('Consolas', 30)
    text = font.render('no pad detected', True, color)
    x, y = screen.get_size()
    text_rect = text.get_rect(center=(x / 2, y / 2))
    screen.blit(text, text_rect)


def render_game(screen, scene):
    # Background Color.
    if scene.black_screen_countdown:
        render_death_screen(screen, scene)
        return
    # Background.
    for background in scene.backgrounds:
        screen.blit(get_image(background.image), background.position)
    duel_surface = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    # Duel.
    duel_surface.set_alpha(50)
    for character in scene.characters:
        if character.duel_target:
            pos1 = character.coordinates.position
            pos2 = character.duel_target.coordinates.position
            pygame.draw.line(duel_surface, (255, 0, 0), pos1, pos2, 3)
    screen.blit(duel_surface, (0, 0))
    # Background.
    elements = sorted(scene.elements, key=lambda elt: elt.switch)
    for element in elements:
        render_element(screen, element)
    # Possible duel.
    duel_surface = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    duel_surface.set_alpha(50)
    for character1, character2 in scene.possible_duels:
        draw_possible_duel(duel_surface, character1, character2)
    screen.blit(duel_surface, (0, 0))
    # Scores.
    image = get_image(scene.score_ol.image)
    screen.blit(image, scene.score_ol.render_position)
    for player in scene.players:
        image = get_image(scene.score_image(player.index, player.life))
        position = scene.score_positions[player.index]
        screen.blit(image, position)
    # for rect in scene.no_go_zones:
    #     draw_rect(screen, rect, 125)
    # for interaction_zone in scene.interaction_zones:
    #     draw_rect(screen, interaction_zone.zone, 15)


def render_death_screen(screen, scene):
    if scene.black_screen_countdown >= COUNTDOWNS.BLACK_SCREEN_COUNT_DOWN - 5:
        screen.fill((255, 255, 255))
        print('white')
    else:
        screen.fill((0, 0, 0))
    for character in scene.dying_characters:
        render_element(screen, character)


def draw_possible_duel(screen, char1, char2):
    p1 = char1.coordinates.x, char1.coordinates.y - 30
    p2 = char2.coordinates.x, char2.coordinates.y - 30
    draw_dashed_line(screen, 'white', p1, p2)


def render_element(screen, element):
    img = element.image
    screen.blit(get_image(img), element.render_position)
    # if isinstance(element, Character):
    #     # screen.blit(get_image(img), element.render_position)
    #     if element.path:
    #         last = None
    #         for point in [element.coordinates.position] + element.path:
    #             draw_rect(screen, (point[0], point[1], 2, 2))
    #             if last:
    #                 pygame.draw.line(screen, (255, 255, 0), last, point, 2)
    #             last = point

    # from drunkparanoia.character import Character
        # draw_rect(screen, element.screen_box, alpha=125)


def draw_rect(surface, box, alpha=255):
    x, y, width, height = box
    color = 'red'
    temp = pygame.Surface((width, height), pygame.SRCALPHA)
    pygame.draw.rect(temp, color, [0, 0, width, height])
    temp.set_alpha(alpha)
    surface.blit(temp, (x, y))


def draw_dashed_line(surf, color, start_pos, end_pos, width=1, dash_length=4):
    """
    https://codereview.stackexchange.com/questions/70143/drawing-a-dashed-line-with-pygame
    """
    x1, y1 = (int(n) for n in start_pos)
    x2, y2 = (int(n) for n in end_pos)
    dl = dash_length

    if x1 == x2:
        ycoords = list(range(y1, y2, dl if y1 < y2 else -dl))
        xcoords = [x1] * len(ycoords)
    elif y1 == y2:
        try:
            xcoords = list(range(x1, x2, dl if x1 < x2 else -dl))
            ycoords = [y1] * len(xcoords)
        except TypeError as e:
            print(x1, x2, -dl)
            raise TypeError from e
    else:
        a = abs(x2 - x1)
        b = abs(y2 - y1)
        c = round(math.sqrt(a**2 + b**2))
        dx = dl * a / c
        dy = dl * b / c

        xcoords = list(numpy.arange(x1, x2, dx if x1 < x2 else -dx))
        ycoords = list(numpy.arange(y1, y2, dy if y1 < y2 else -dy))

    next_coords = list(zip(xcoords[1::2], ycoords[1::2]))
    last_coords = list(zip(xcoords[::2], ycoords[::2]))
    for (x1, y1), (x2, y2) in zip(next_coords, last_coords):
        start = (round(x1), round(y1))
        end = (round(x2), round(y2))
        pygame.draw.line(surf, color, start, end, width)
