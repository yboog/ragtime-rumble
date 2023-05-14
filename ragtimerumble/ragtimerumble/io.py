
import os
import json
import pygame
import random
import itertools
from ragtimerumble import preferences
from ragtimerumble.config import GAMEROOT, PALLETTES_COUNT
from ragtimerumble.joystick import get_current_commands


_ambiance_channel = None
_animation_store = {}
_image_store = {}
_name_generators = {}
_death_sentences_generators = {}
_kill_sentences_generators = {}
_palettes = {}
_sounds = {}
_dispatcher_music = None
_scene_music = None
_menu_texts = {}
_buttons_texts = {}


def play_coin_sound():
    play_sound(random.choice((
        'resources/sounds/coins_3.wav',
        'resources/sounds/coins_1.wav',
        'resources/sounds/coins_2.wav')))


def play_scene_music(sounds):
    sound = random.choice(sounds)
    global _scene_music
    if _scene_music:
        stop_scene_music()
    _scene_music = load_sound(sound)
    _scene_music.play(-1)


def stop_scene_music():
    global _scene_music
    if not _scene_music:
        return
    _scene_music.stop()
    _scene_music = None


def get_build_name():
    version_filepath = f'{GAMEROOT}/resources/version'
    if not os.path.exists(version_filepath):
        return 'Python Interactive'
    with open(version_filepath, 'r') as f:
        return f'build: {f.read()}'


def get_how_to_play_image(page):
    language = {'french': 'fr', 'english': 'en'}.get(
        preferences.get('language'), 'en')
    return load_image(f'resources/ui/howtoplay/page{page}-{language}.png')


def play_dispatcher_music():
    sounds = (
        'resources/sounds/dispatcher_1_sound.ogg',
        'resources/sounds/dispatcher_2_ErikVargas_TonkyMyHonky.ogg',
        'resources/sounds/dispatcher_3_JakeSchneider_HonkyTonkSaloon.ogg')
    sound = random.choice(sounds)
    global _dispatcher_music
    if _dispatcher_music:
        stop_dispatcher_music()
    _dispatcher_music = load_sound(sound)
    _dispatcher_music.play(-1)


def get_touch_button_image(button):
    return load_image(f'resources/ui/touch-button/{button.lower()}.png')


def get_icon():
    return get_image(load_image('/resources/ragtime.ico'))


def stop_dispatcher_music():
    global _dispatcher_music
    if not _dispatcher_music:
        return
    _dispatcher_music.stop()
    _dispatcher_music = None


def get_coin_stack(n):
    path = f'resources/ui/coin-stack/coin-stack-{n:02}.png'
    return get_image(load_image(path))


def choice_display_name(data):
    if not _name_generators.get(data["name"]):
        names = data["names"]
        random.shuffle(names)
        _name_generators[data["name"]] = itertools.cycle(names)
    return next(_name_generators[data["name"]])


def build_random_palette(palettes):
    indexes = list(range(len(palettes)))
    palettes = [palettes[i] for i in indexes[:len(palettes)]]
    palette_source = [c for v in palettes for c in v['origins']]
    palette_dest = []
    ids = []
    for palette in palettes:
        index = random.randrange(0, len(palette['palettes']))
        ids.append([palette['name'], index])
        palette_dest.extend(palette['palettes'][index])
    id_ = '-'.join(f'{id_[0]}.{id_[1]}' for id_ in ids)
    return id_, palette_source, palette_dest


def get_menu_text(key):
    language = preferences.get('language')
    if not _menu_texts:
        filepath = f'{GAMEROOT}/resources/texts/menu.json'
        with open(filepath, 'rb') as f:
            _menu_texts.update(json.load(f))
    if key not in _menu_texts:  # Thing does not need to be translated
        return key
    return _menu_texts[key][language]


def choice_death_sentence():
    if not _death_sentences_generators:
        filepath = f'{GAMEROOT}/resources/texts/darwinaward.json'
        with open(filepath, 'rb') as f:
            data = json.load(f)
        for key in data:
            array = data[key]
            random.shuffle(array)
            _death_sentences_generators[key] = itertools.cycle(array)
    language = preferences.get('language')
    return next(_death_sentences_generators[language])


def choice_kill_sentence():
    if not _kill_sentences_generators:
        filepath = f'{GAMEROOT}/resources/texts/kills.json'
        with open(filepath, 'rb') as f:
            data = json.load(f)
        for key in data:
            array = data[key]
            random.shuffle(array)
            _kill_sentences_generators[key] = itertools.cycle(array)
    language = preferences.get('language')
    return next(_kill_sentences_generators[language])


def get_round_image(n):
    path = f'resources/ui/scores/round-sources/round{n:02d}.png'
    return load_image(path)


def load_main_resources():
    load_image('resources/ui/gamepad.png', (0, 255, 0))


def quit_event():
    return any((
        event.type == pygame.KEYDOWN and
        event.key == pygame.K_ESCAPE or
        event.type == pygame.QUIT)
        for event in pygame.event.get())


def list_joysticks():
    pygame.joystick.quit()
    pygame.joystick.init()
    pygame.joystick.get_count()
    joysticks = []
    for i in range(pygame.joystick.get_count()):
        try:
            joystick = pygame.joystick.Joystick(i)
            joystick.init()
            joysticks.append(joystick)
        except BaseException:
            print(f'Unsupported joystick {joystick.get_name()}')
            raise
    return joysticks[:4]


def swap_colors(surface, palette1, palette2):
    arr = pygame.surfarray.pixels3d(surface)
    red, green, blue = arr.T
    for color1, color2 in zip(palette1, palette2):
        if color1 == color2:
            continue
        areas = (red == color1[0]) & (blue == color1[2]) & (green == color1[1])
        arr[..., ][areas.T] = color2
    new_surface = pygame.surfarray.make_surface(arr).convert_alpha()
    alpha_array = pygame.surfarray.pixels_alpha(surface)
    pygame.surfarray.pixels_alpha(new_surface)[:] = alpha_array[:]
    return new_surface


def load_skins():
    directory = f'{GAMEROOT}/resources/animdata'
    skins = [f'{directory}/{file}' for file in os.listdir(directory)]
    for skin in skins:
        with open(skin, 'r') as f:
            data = json.load(f)
        load_skin(data)


def get_font(filename):
    return f'{GAMEROOT}/resources/fonts/{filename}'


def get_character_palette_ids(data):
    result = _palettes.setdefault(data["name"], [])
    if result:
        return result
    for _ in range(PALLETTES_COUNT):
        result.append(build_random_palette(data['palettes']))
    _palettes[data["name"]] = result
    return result


def load_skin(data):
    size = data['framesize']
    path = data["filepath"]
    if not data.get('palettes'):
        # Build original colors skin.
        return [load_frames(path, size, (0, 255, 0))]
    # Build color palettes
    result = []
    palettes = get_character_palette_ids(data) if data.get('palettes') else []
    for id_, palette1, palette2 in palettes:
        variant = load_frames(path, size, (0, 255, 0), palette1, palette2, id_)
        result.append(variant)
    return result


def load_frames(
        filepath, frame_size, key_color,
        palette1=None, palette2=None, palette=0):
    """
    Split a huge sheet in memory.
    """
    filepath = f'{GAMEROOT}/{filepath}'
    filename_id = f'{GAMEROOT}/{filepath}.{palette}'
    if _animation_store.get(filename_id):
        return _animation_store.get(filename_id, [])

    sheet = pygame.image.load(filepath).convert_alpha()
    if palette1 and palette2:
        sheet = swap_colors(sheet, palette1, palette2)
    width, height = frame_size
    row = sheet.get_height() / height
    col = sheet.get_width() / width
    if row != int(row) or col != int(col):
        message = (
            f"the sprite sheet file {filepath} size doesn't "
            "match with his block size")
        raise ValueError(message)
    ids = []

    for j, i in itertools.product(range(int(row)), range(int(col))):
        image = pygame.Surface([width, height], pygame.SRCALPHA)
        x, y = i * width, j * height
        image.blit(sheet, (0, 0), (x, y, width, height))
        # image.set_colorkey((0, 0, 0, 0))
        id_ = f'{filename_id}[{i}.{j}]'
        _image_store[id_] = image
        ids.append(id_)
    _animation_store[filename_id] = ids
    return ids


def get_score_player_icon(index, is_winner):
    return load_image(
        'resources/ui/scores/'
        f'p{index + 1}-{"win" if is_winner else "lose"}.png')


def get_image(image_id):
    return _image_store.get(image_id)


def load_image(filename, key_color=None, flipped=False):
    if _image_store.get(filename) and flipped is False:
        return filename
    filepath = f'{GAMEROOT}/{filename}'
    image = pygame.image.load(filepath).convert_alpha()
    if key_color is not None:
        image.set_colorkey(key_color)
    _image_store[filename] = image
    return filename


def load_data(filename):
    filepath = f'{GAMEROOT}/{filename}'
    with open(filepath, 'r') as f:
        return json.load(f)


def load_sound(filename):
    if sound := _sounds.get(filename):
        return sound
    try:
        filepath = f'{GAMEROOT}/{filename}'
        _sounds[filename] = pygame.mixer.Sound(filepath)
        return _sounds[filename]
    except FileNotFoundError as e:
        msg = f"No such file or directory: {filepath}"
        raise FileNotFoundError(msg) from e


def play_music(filename):
    pygame.mixer.music.load(f'{GAMEROOT}/{filename}')
    pygame.mixer.music.play()


def stop_music():
    pygame.mixer.music.stop()
    pygame.mixer.music.unload()


def play_ambiance(filename):
    global _ambiance_channel
    if not _ambiance_channel:
        _ambiance_channel = pygame.mixer.find_channel()
    _ambiance_channel.play(load_sound(filename))


def stop_ambiance():
    if not _ambiance_channel:
        return
    _ambiance_channel.stop()


def play_sound(filename, loop=0):
    load_sound(filename).play(loop)


def stop_sound(filename):
    if (sound := _sounds.get(filename)):
        sound.stop()


def image_mirror(id_, horizontal=True, vertical=False):
    if not _image_store.get(id_):
        raise ValueError(f'Unknown image id {id_}. Cannot generate a mirror.')
    flip_id = f'{id_}['
    if horizontal:
        flip_id += 'h'
    if vertical:
        flip_id += 'v'
    flip_id += ']'
    if not _image_store.get(flip_id):
        image = _image_store[id_]
        mirror = pygame.transform.flip(image, horizontal, vertical)
        _image_store[flip_id] = mirror
    return flip_id
