import numpy
import math
import pygame
from drunkparanoia.io import get_image, get_font
from drunkparanoia.config import LOOP_STATUSES
from drunkparanoia.scene import column_to_group, get_score_data
from drunkparanoia.character import Character


KILL_MESSAGE_SCREEN_PADDING = 10
KILL_MESSAGE_PADDING = 1
KILL_MESSAGE_MARGIN = 2



def render_game(screen, loop):
    if loop.status == LOOP_STATUSES.SCORE:
        return render_score(screen, loop)
    render_scene(screen, loop.scene)
    if loop.status == LOOP_STATUSES.LAST_KILL:
        render_last_kill(screen, loop)
        return
    if loop.status == LOOP_STATUSES.DISPATCHING:
        render_dispatching(screen, loop)
        render_players_ol_score(screen, loop.scene)
    render_messages(screen, loop.scene)


CELL_WIDTH = 55
CELL_HEIGHT = 35
COL_COUNT = 7
ROW_COUNT = 4


def render_score(screen, loop):
    screen.fill((0, 0, 0))
    for row in range(ROW_COUNT):
        player = f'player {row + 1}'
        pos = get_player_pos(screen, row)
        draw_text(screen, player, pos, (200, 200, 200))
        for col in range(COL_COUNT):
            rect = get_cell_rect(screen, row, col)
            pygame.draw.rect(screen, (30, 30, 30), rect, width=1)
            data = get_score_data(loop.scores, row, col)
            draw_score_data(screen, rect, data)

    headers = 'p1', 'p2', 'p3', 'p4', 'tot', 'npc', 'win'
    for col in range(COL_COUNT):
        text = headers[col]
        rect = get_header_rect(screen, col)
        draw_text(screen, text, rect.center, (200, 200, 200))

    x = screen.get_size()[0] / 2
    y = get_cell_rect(screen, ROW_COUNT + 1, 0).centery
    draw_text(screen, 'Press "a" button to restart', (x, y))


def draw_score_data(screen, rect, data):
    if data is None:
        pygame.draw.rect(screen, (100, 100, 100), rect)
        return

    if isinstance(data, int):
        draw_text(screen, str(data), rect.center, (255, 255, 0))
        return

    if isinstance(data, list):
        rect1 = pygame.Rect(
            rect.left, rect.top, rect.width / 2, rect.height / 2)
        draw_text(screen, str(data[0]), rect1.center, (0, 255, 0))
        rect2 = pygame.Rect(
            rect.centerx, rect.centery, rect.width / 2, rect.height / 2)
        draw_text(screen, str(data[1]), rect2.center, (255, 0, 0))
        pygame.draw.line(
            screen, (255, 255, 255), rect.topright, rect.bottomleft, 1)


def get_header_rect(screen, col):
    return get_cell_rect(screen, -1, col)


def get_player_pos(screen, row):
    rect = get_cell_rect(screen, row, 0)
    x, y = rect.midleft
    x -= 39
    return x, y


def get_cell_rect(screen, row, col):
    x = (screen.get_size()[0] / 2)
    x -= CELL_WIDTH * (COL_COUNT / 2)
    x += CELL_WIDTH * col
    y = screen.get_size()[1] / 2
    y -= CELL_HEIGHT * (ROW_COUNT / 2)
    y += CELL_HEIGHT * row
    return pygame.Rect(x, y, CELL_WIDTH, CELL_HEIGHT)


def render_last_kill(screen, loop):
    if loop.scene.white_screen_countdown:
        screen.fill((255, 255, 255))
    else:
        temp = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        temp.fill((0, 0, 0))
        temp.set_alpha(180)
        screen.blit(temp, (0, 0))
    for player in loop.scene.players:
        render_element(screen, player.character)
        x, y = player.character.coordinates.position
        y += 15
        draw_text(screen, f'player {player.index + 1}', (x, y))


def draw_text(surface, text, pos, color=None):
    color = color or (255, 255, 255)
    font = pygame.font.SysFont('Consolas', 15)
    text = font.render(text, True, color)
    text_rect = text.get_rect(center=pos)
    surface.blit(text, text_rect)


def render_dispatching(screen, loop):
    temp = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    temp.fill((0, 0, 0))
    temp.set_alpha(180)
    screen.blit(temp, (0, 0))
    elements = [p for p in loop.scene.props if p.visible_at_dispatch]
    elements += loop.scene.characters
    for element in sorted(elements, key=lambda elt: elt.switch):
        render_element(screen, element)
    gamepad_image = get_image('resources/ui/gamepad.png')
    offset_x = gamepad_image.get_size()[0] / 2
    offset_y = gamepad_image.get_size()[1] / 2
    column_counts = [0, 0, 0, 0, 0]
    for i, _ in enumerate(loop.dispatcher.joysticks):
        column = loop.dispatcher.joysticks_column[i]
        row = column_counts[column]
        startups = loop.scene.startups
        if column == 2:  # Unassigned
            position = startups['unassigned'][row]
        else:
            group = startups['groups'][column_to_group(column)]
            position = group['assigned'][row]
        x = position[0] - offset_x
        y = position[1] - offset_y
        screen.blit(gamepad_image, (x, y))
        x = position[0] + gamepad_image.get_size()[0]
        y = position[1]
        draw_text(screen, str(i + 1), (x, y))
        column_counts[column] += 1


def render_no_player(screen):
    color = 255, 255, 255
    font = pygame.font.SysFont('Consolas', 30)
    text = font.render('no pad detected', True, color)
    x, y = screen.get_size()
    text_rect = text.get_rect(center=(x / 2, y / 2))
    screen.blit(text, text_rect)


def render_scene(screen, scene):
    # Background Color.
    if scene.black_screen_countdown or scene.white_screen_countdown:
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
            pygame.draw.line(duel_surface, (255, 255, 0), pos1, pos2, 6)
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
    render_players_ol_score(screen, scene)
    # for rect in scene.no_go_zones:
    #     draw_rect(screen, rect, 125)
    # for interaction_zone in scene.interaction_zones:
    #     draw_rect(screen, interaction_zone.zone, 15)


def render_players_ol_score(screen, scene):
    image = get_image(scene.score_ol.image)
    screen.blit(image, scene.score_ol.render_position)
    for player in scene.players:
        image = get_image(scene.life_image(player.index, player.life))
        position = scene.life_positions[player.index]
        screen.blit(image, position)
        on = player.bullet_cooldown == 0
        image = get_image(scene.bullet_image(player.index, on))
        position = scene.bullet_positions[player.index]
        screen.blit(image, position)


def render_death_screen(screen, scene):
    if scene.white_screen_countdown:
        screen.fill((255, 255, 255))
        if scene.killer:
            render_element(screen, scene.killer)
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
    ### RENDER PATHS
    # if isinstance(element, Character):
    #     if element.path:
    #         last = None
    #         for point in [element.coordinates.position] + element.path:
    #             draw_rect(screen, (point[0], point[1], 2, 2))
    #             if last:
    #                 pygame.draw.line(screen, (255, 255, 0), last, point, 2)
    #             last = point

    #     draw_rect(screen, element.screen_box, alpha=125)


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


def render_messages(screen, scene):
    for i, (text, alpha) in enumerate(scene.messager.data):
        font = pygame.font.Font(get_font('Pixel-Western.TTF'), 8)
        text_surface = font.render(text, False, (0, 0, 0))
        text_surface.set_alpha(alpha)
        text_rect = text_surface.get_rect()
        top = (
            i * (
                text_rect.height +
                (KILL_MESSAGE_MARGIN * 2) +
                KILL_MESSAGE_PADDING))
        text_rect.topright = (screen.get_width(), top)
        text_rect.top += KILL_MESSAGE_SCREEN_PADDING
        text_rect.right -= KILL_MESSAGE_SCREEN_PADDING
        bg_surface = pygame.Surface((
            text_rect.width + (KILL_MESSAGE_MARGIN * 2),
            text_rect.height + (KILL_MESSAGE_MARGIN * 2)))
        bg_surface.fill((248, 213, 155))
        bg_surface.set_alpha(alpha)
        bg_rect = bg_surface.get_rect()
        bg_rect.top = text_rect.top - KILL_MESSAGE_MARGIN
        bg_rect.left = text_rect.left - KILL_MESSAGE_MARGIN
        screen.blit(bg_surface, bg_rect)
        screen.blit(text_surface, text_rect)
