
import math
import pygame
from ragtimerumble import debug
from ragtimerumble import preferences
from ragtimerumble.character import Character
from ragtimerumble.config import LOOP_STATUSES, DIRECTIONS
from ragtimerumble.gameloop import column_to_group, get_score_data
from ragtimerumble.io import (
    get_image, get_font, load_image, get_coin_stack, get_score_player_icon,
    get_round_image, get_build_name, get_button_text)
from ragtimerumble.menu import ControlMenuScreen, HotToPlayScreen
from ragtimerumble.pathfinding import distance, seg_to_vector
from ragtimerumble.pilot import SmoothPathPilot
from ragtimerumble.scene import Vfx


KILL_MESSAGE_SCREEN_PADDING = 10
KILL_MESSAGE_PADDING = 1
KILL_MESSAGE_MARGIN = 2
MESSAGE_FONT_SIZE = 8
MESSAGE_FONT_FILE = 'Pixel-Western.otf'
TEXT_FONT_FILE = 'Retro-Gaming.ttf'


def render_game(screen, loop):
    render_scene(screen, loop.scene)
    if loop.status == LOOP_STATUSES.MENU:
        return render_menu(screen, loop.menu)
    if loop.status == LOOP_STATUSES.SCORE:
        return render_score_screen(screen, loop.scores_screen)
    if loop.status == LOOP_STATUSES.LAST_KILL:
        render_last_kill(screen, loop)
        return
    if loop.status == LOOP_STATUSES.DISPATCHING:
        render_dispatching(screen, loop)
        render_players_ol_score(screen, loop.scene)
    render_messages(screen, loop.scene)


def render_menu(screen, menu):
    render_black_screen(screen, 180)
    bg = get_image(menu.bg)
    screen.blit(bg, (0, 0))
    if menu.subscreen:
        return SUBSCREEN_RENDERER[type(menu.subscreen)](screen, menu)
    render_element(screen, menu.title)
    render_build(screen, get_build_name())
    font = pygame.font.Font(get_font(TEXT_FONT_FILE), 11)
    for item in menu.items:
        highlighted = item.index == menu.index
        color = (255, 125, 0) if highlighted else (255, 255, 255)
        draw_text(
            surface=screen,
            text=item.label,
            pos=item.coordinates.position,
            font=font,
            color=color)


def render_build(screen, name):
    font = pygame.font.Font(get_font(TEXT_FONT_FILE), 11)
    draw_text(screen, name, (5, 350), color=(50, 50, 50), font=font)


def render_controls_screen(screen, menu):
    image = get_image(menu.subscreen.image)
    screen.blit(image, (0, 0))
    render_button(screen, menu.subscreen.button, (4, 335))


def render_how_to_play_screen(screen, menu):
    id_ = load_image('resources/ui/howtoplay/htp_ul.png')
    screen.blit(get_image(id_), (0, 0))
    image = get_image(menu.subscreen.image)
    screen.blit(image, (0, 0))
    render_button(screen, menu.subscreen.button, (4, 335))


def render_buttons(screen, buttons, pos):
    for button in buttons:
        right, _ = render_button(screen, button, pos)
        pos = right + 5, pos[1]


def render_button(screen, button, pos):
    color = (248, 213, 155)
    button_image = get_image(button.image)
    screen.blit(button_image, pos)
    text = get_button_text(button.key)
    font = pygame.font.Font(get_font(MESSAGE_FONT_FILE), 8)
    x = pos[0] + button_image.get_size()[0] + 3
    y = pos[1] + (button_image.get_size()[1] / 2)
    text = font.render(text, False, color)
    text_rect = text.get_rect(center=(x, y))
    text_rect.left += text_rect.width / 2

    screen.blit(text, text_rect)
    return text_rect.bottomright


def render_score_screen(screen, scores_screen):
    render_black_screen(screen, 180)
    image = get_image(scores_screen.background)
    screen.blit(image, (0, 0))
    winner = scores_screen.winner_index
    render_score_header(screen, scores_screen, winner)
    if scores_screen.page == 0:
        render_round_score_content(screen, scores_screen, winner)
    else:
        render_total_score_content(screen, scores_screen)
    render_buttons(screen, scores_screen.buttons, (4, 335))


def render_score_header(screen, scores_screen, winner):
    image = get_round_image(scores_screen.scores['round'])
    screen.blit(get_image(image), (0, 0))
    for player in scores_screen.players:
        # Draw character avatar.
        palette = player.character.palette
        direction = DIRECTIONS.RIGHT
        id_ = player.character.spritesheet.image(direction, palette)
        image = get_image(id_)
        position = scores_screen.characters_coordinates[player.index].position
        screen.blit(image, position)
        # Draw character avatar dead filter
        if player.index != winner:
            image = image.copy()
            image.fill((60, 60, 60), special_flags=pygame.BLEND_MULT)
            image.set_alpha(150)
            screen.blit(image, position)
        # Draw Player number
        id_ = get_score_player_icon(player.index, player.index == winner)
        image = get_image(id_)
        left = scores_screen.columns[player.index][0]
        top = 121 - image.get_size()[0]
        screen.blit(image, (left, top))


def render_total_score_content(screen, scores_screen):
    image = get_image(load_image('resources/ui/scores/separator-2.png'))
    screen.blit(image, (0, 0))
    font = pygame.font.Font(get_font(TEXT_FONT_FILE), 11)
    margin = 8
    for player in scores_screen.players:
        score = scores_screen.scores[f'player {player.index + 1}']
        column = scores_screen.columns[player.index]

        top = scores_screen.lines['tot_wins']
        draw_text(
            surface=screen,
            text='Wins :',
            pos=(column[0] + margin, top),
            color=(255, 255, 255),
            font=font)
        draw_text(
            surface=screen,
            text=f'{score["victory"]}',
            pos=(column[1] - margin, top),
            font=font,
            color=(255, 255, 255),
            align='right')
        top = scores_screen.lines['tot_death']
        draw_text(
            surface=screen,
            text='Deaths :',
            pos=(column[0] + margin, top),
            color=(255, 255, 255),
            font=font)
        draw_text(
            surface=screen,
            text=f'{score["deaths"]}',
            pos=(column[1] - margin, top),
            font=font,
            color=(255, 255, 255),
            align='right')
        opponents = [
            p for p in scores_screen.players
            if p.index != player.index]

        for i, opponent in enumerate(opponents):
            top = scores_screen.lines['tot_kills'][i]
            text = f'Killed P{opponent.index + 1} :'
            draw_text(
                surface=screen,
                text=text,
                pos=(column[0] + margin, top),
                font=font,
                color=(255, 255, 255))
            kills = score[f'player {opponent.index + 1}'][0]
            draw_text(
                surface=screen,
                text=f'{kills}',
                pos=(column[1] - margin, top),
                font=font,
                color=(255, 255, 255),
                align='right')
        top = scores_screen.lines['tot_money']
        draw_text(
            surface=screen,
            text='Bank :',
            pos=(column[0] + margin, top),
            color=(255, 255, 255),
            font=font)
        draw_text(
            surface=screen,
            text=f'{score["money_earned"]}$',
            pos=(column[1] - margin, top),
            font=font,
            color=(255, 255, 255),
            align='right')
        top = scores_screen.lines['tot_npc_killed']
        draw_text(
            surface=screen,
            text='Npcs killed :',
            pos=(column[0] + margin, top),
            color=(255, 255, 255),
            font=font)
        draw_text(
            surface=screen,
            text=f'{score["civilians"]}',
            pos=(column[1] - margin, top),
            font=font,
            color=(255, 255, 255),
            align='right')
        top = scores_screen.lines['tot_score']
        draw_text(
            surface=screen,
            text='Score :',
            pos=(column[0] + margin, top),
            color=(255, 255, 255),
            font=font)
        draw_text(
            surface=screen,
            text='XXX',
            pos=(column[1] - margin, top),
            font=font,
            color=(255, 255, 255),
            align='right')


def render_round_score_content(screen, scores_screen, winner):
    image = get_image(load_image('resources/ui/scores/separator-1.png'))
    screen.blit(image, (0, 0))
    font = pygame.font.Font(get_font(TEXT_FONT_FILE), 11)
    font_name = pygame.font.Font(get_font(MESSAGE_FONT_FILE), 8)

    for player in scores_screen.players:
        # Draw player name
        left = scores_screen.columns[player.index][0]
        color = (255, 232, 152) if player.index == winner else (115, 98, 90)
        top = scores_screen.lines['name']
        text = player.character.display_name
        draw_text(screen, text, (left, top), color=color, font=font_name)

        top = scores_screen.lines['money']
        column = scores_screen.columns[player.index]
        draw_text(
            screen,
            text='Money :',
            pos=(column[0], top),
            font=font,
            color=(255, 255, 255))

        draw_text(
            screen,
            text=f'{player.coins}$',
            pos=(column[1], top),
            font=font,
            color=(255, 255, 255),
            align='right')

        top = scores_screen.lines['npc_killed']
        kill = 'kill' if player.npc_killed < 2 else 'kills'
        draw_text(
            screen,
            text=f'{player.npc_killed} Npc {kill} :',
            pos=(column[0], top),
            font=font,
            color=(255, 255, 255))

        draw_text(
            screen,
            text=f'- {player.npc_killed * 2}$',
            pos=(column[1], top),
            font=font,
            color=(255, 255, 255),
            align='right')

        killed = [p for p in scores_screen.players if p.killer == player.index]
        for i, killed_player in enumerate(killed):
            top = scores_screen.lines['player_killed'][i]
            draw_text(
                screen,
                text=f'Killed P{killed_player.index + 1} :',
                pos=(column[0], top),
                font=font,
                color=(255, 255, 255))
            draw_text(
                screen,
                text='+ 2$',
                pos=(column[1], top),
                font=font,
                color=(255, 255, 255),
                align='right')

        if player.index == winner:
            top = scores_screen.lines['victory']
            draw_text(
                screen,
                text='Victory :',
                pos=(column[0], top),
                font=font,
                color=(255, 255, 255))
            draw_text(
                screen,
                text='+ 3$',
                pos=(column[1], top),
                font=font,
                color=(255, 255, 255),
                align='right')

        total = (
            player.coins +
            (2 * len(killed)) +
            (3 if player.index == winner else 0) -
            (player.npc_killed * 2))

        top = scores_screen.lines['total']
        draw_text(
            screen,
            text='Total :',
            pos=(column[0], top),
            font=font,
            color=(255, 255, 255))
        draw_text(
            screen,
            text=f'{total}$',
            pos=(column[1], top),
            font=font,
            color=(255, 255, 255),
            align='right')


SUBSCREEN_RENDERER = {
    ControlMenuScreen: render_controls_screen,
    HotToPlayScreen: render_how_to_play_screen
}

CELL_WIDTH = 55
CELL_HEIGHT = 35
COL_COUNT = 7
ROW_COUNT = 4


def render_score(screen, loop):
    screen.fill((0, 0, 0))
    for row in range(ROW_COUNT):
        player = f'player {row + 1}'
        pos = get_player_pos(screen, row)
        draw_text(screen, player, pos, color=(200, 200, 200))
        for col in range(COL_COUNT):
            rect = get_cell_rect(screen, row, col)
            pygame.draw.rect(screen, (30, 30, 30), rect, width=1)
            data = get_score_data(loop.scores, row, col)
            draw_score_data(screen, rect, data)

    headers = 'p1', 'p2', 'p3', 'p4', 'tot', 'npc', 'win'
    for col in range(COL_COUNT):
        text = headers[col]
        rect = get_header_rect(screen, col)
        draw_text(screen, text, rect.center, color=(200, 200, 200))

    x = screen.get_size()[0] / 2
    y = get_cell_rect(screen, ROW_COUNT + 1, 0).centery
    draw_text(screen, 'Press "a" button to restart', (x, y))


def draw_score_data(screen, rect, data):
    if data is None:
        pygame.draw.rect(screen, (100, 100, 100), rect)
        return

    if isinstance(data, int):
        draw_text(screen, str(data), rect.center, color=(255, 255, 0))
        return

    if isinstance(data, list):
        rect1 = pygame.Rect(
            rect.left, rect.top, rect.width / 2, rect.height / 2)
        draw_text(screen, str(data[0]), rect1.center, color=(0, 255, 0))
        rect2 = pygame.Rect(
            rect.centerx, rect.centery, rect.width / 2, rect.height / 2)
        draw_text(screen, str(data[1]), rect2.center, color=(255, 0, 0))
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
        font = pygame.font.Font(get_font(TEXT_FONT_FILE), 11)
        x, y = player.character.coordinates.position
        y += 15
        draw_text(screen, f'player {player.index + 1}', (x, y), font=font)


def draw_text(
        surface, text, pos, size=15, font=None, color=None, align='left'):
    color = color or (255, 255, 255)
    font = font or pygame.font.SysFont('Consolas', size)
    text = font.render(text, False, color)
    text_rect = text.get_rect(center=pos)
    if align == 'left':
        text_rect.left += text_rect.width / 2
    else:
        text_rect.right -= text_rect.width / 2
    surface.blit(text, text_rect)


def render_black_screen(surface, alpha):
    temp = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    temp.fill((0, 0, 0))
    temp.set_alpha(alpha)
    surface.blit(temp, (0, 0))


def render_dispatching(screen, loop):
    render_black_screen(screen, 180)
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
        font = pygame.font.Font(get_font(TEXT_FONT_FILE), 8)
        draw_text(screen, str(i + 1), (x, y), font=font)
        column_counts[column] += 1


def render_no_player(screen):
    color = 255, 255, 255
    font = pygame.font.Font(get_font(MESSAGE_FONT_FILE), 30)
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
    done = []
    for character1, character2 in scene.possible_duels:
        draw_line = [character2, character1] not in done
        draw_possible_duel(duel_surface, character1, character2, draw_line)
        done.append([character1, character2])
    screen.blit(duel_surface, (0, 0))
    # Sniper
    render_sniper_reticles(screen, scene)
    characters = {
        character for reticle in scene.sniperreticles
        for character in reticle.target_characters}
    for character in characters:
        image = get_image(character.image).copy()
        image.fill((255, 255, 255), special_flags=pygame.BLEND_ADD)
        image.set_alpha(50)
        screen.blit(image, character.render_position)
    # Scores.
    render_players_ol_score(screen, scene)

    if not debug.active:
        return

    # RENDER ZONE
    for rect in scene.no_go_zones:
        draw_rect(screen, rect, 125)
    for interaction_zone in scene.interaction_zones:
        draw_rect(screen, interaction_zone.zone, 15)
    for zone in scene.interactive_props:
        draw_rect(screen, zone.zone, 50)
        draw_rect(screen, zone.attraction, 25)

    # TEST FOR HIGHLIGHT RENDER CHARACER
    for character in scene.characters:
        image = get_image(character.image).copy()
        image.fill((255, 255, 255), special_flags=pygame.BLEND_ADD)
        image.set_alpha(50)
        screen.blit(image, character.render_position)


def render_players_ol_score(screen, scene):
    image = get_image(scene.score_ol.image)
    screen.blit(image, scene.score_ol.render_position)
    for player in scene.players:
        image = get_image(scene.life_image(player.index, player.life))
        position = scene.life_positions[player.index]
        screen.blit(image, position)
    for player in scene.players:
        on = player.bullet_cooldown == 0
        image = get_image(scene.bullet_image(player.index, on))
        position = scene.bullet_positions[player.index]
        screen.blit(image, position)
        position = scene.coins_position(player.index)
        if preferences.get('gametype') == 'advanced':
            image = get_coin_stack(player.coins)
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


def point_on_segment(segment, distance_from_p1):
    x1, y1 = segment[0]
    x2, y2 = segment[1]
    segment_length = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    ratio = distance_from_p1 / segment_length
    x = x1 + ratio * (x2 - x1)
    y = y1 + ratio * (y2 - y1)
    return (x, y)


def draw_possible_duel(screen, char1, char2, line=True):
    p1 = char1.coordinates.x, char1.coordinates.y - 30
    p2 = char2.coordinates.x, char2.coordinates.y - 30
    pp1 = point_on_segment((p1, p2), 13)
    pp2 = point_on_segment((p2, p1), 13)
    # pygame.draw.line(screen, (255, 255, 255), p1, p2, width=2)
    draw_arrow(screen, 'white', pp1, pp2, headwidth=5)
    if line:
        draw_dashed_line(screen, 'white', pp1, pp2)


def render_element(screen, element):
    try:
        img = element.image
        screen.blit(get_image(img), element.render_position)
        if hasattr(element, 'shorn') and element.shorn:
            image = get_image(element.image).copy()
            image.fill((0, 0, 0), special_flags=pygame.BLEND_MULT)
            image.set_alpha(150)
            screen.blit(image, element.render_position)
    except TypeError:
        print(img, get_image(img))
        raise
    if debug.render_path:
        condition = (
            isinstance(element, Character) and
            element.pilot and
            element.pilot.path)
        if condition:
            if isinstance(element.pilot, SmoothPathPilot):
                color = (255, 255, 0)
            else:
                color = (0, 0, 255)
            last = None
            for point in [element.coordinates.position] + element.pilot.path:
                draw_rect(screen, (point[0], point[1], 2, 2))
                if last:
                    pygame.draw.line(screen, color, last, point, 2)
                last = point

    if debug.active:
        # COLLIDER
        if hasattr(element, 'screen_box'):
            draw_rect(screen, element.screen_box, alpha=125)
        # HITBOX
        if hasattr(element, 'hitbox'):
            draw_rect(screen, element.hitbox, alpha=125)
        if hasattr(element, 'zone'):
            draw_rect(screen, element.zone, color='blue', alpha=125)
        if hasattr(element, 'interaction_zone'):
            draw_rect(
                screen, element.interaction_zone, color='green', alpha=125)


def draw_rect(surface, box, color=None, alpha=255):
    color = color or [255, 0, 0]
    x, y, width, height = box
    temp = pygame.Surface((width, height), pygame.SRCALPHA)
    pygame.draw.rect(temp, color, [0, 0, width, height])
    temp.set_alpha(alpha)
    surface.blit(temp, (x, y))


def draw_arrow(surface, color, p1, p2, headwidth=2):
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]

    length = math.sqrt(dx**2 + dy**2)
    if length == 0:
        return

    theta = math.acos(dx / length)
    if dy < 0:
        theta = 2 * math.pi - theta

    angle1 = theta + math.pi / 6
    angle2 = theta - math.pi / 6
    x1 = p2[0] - headwidth * math.cos(angle1)
    y1 = p2[1] - headwidth * math.sin(angle1)
    x2 = p2[0] - headwidth * math.cos(angle2)
    y2 = p2[1] - headwidth * math.sin(angle2)

    pygame.draw.polygon(surface, color, [(p2[0], p2[1]), (x1, y1), (x2, y2)])


def draw_dashed_line(surface, color, p1, p2, width=1, dash_length=4):
    dist = distance(p1, p2)
    if dist < dash_length:
        pygame.draw.line(surface, color, p1, p2, width)
        return

    vector = [n * dash_length for n in seg_to_vector(p1, p2)]
    start_point = p1
    draw = True
    while True:
        end_point = start_point[0] + vector[0], start_point[1] + vector[1]
        if distance(p1, end_point) > dist:
            return
        if draw:
            pygame.draw.line(surface, color, start_point, end_point, width)
        draw = not draw
        start_point = end_point


def render_messages(screen, scene):
    for i, (text, alpha) in enumerate(scene.messenger.data):
        font = pygame.font.Font(get_font(MESSAGE_FONT_FILE), MESSAGE_FONT_SIZE)
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


def render_sniper_reticles(screen, scene):
    for reticle in scene.sniperreticles:
        if reticle.player is None:
            continue
        img = get_image(load_image('resources/ui/sniper_reticle.png'))
        position = list(reticle.coordinates.position)
        position[0] -= img.get_size()[0] / 2
        position[1] -= img.get_size()[1] / 2
        surface = pygame.Surface(img.get_size(), pygame.SRCALPHA)
        surface.blit(img, (0, 0))
        surface.set_alpha(100)
        screen.blit(surface, position)
