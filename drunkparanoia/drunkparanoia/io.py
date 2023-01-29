
import os
import json
import pygame
import random
import itertools
from drunkparanoia.config import GAMEROOT, VARIANTS_COUNT
from drunkparanoia.joystick import get_current_commands


_animation_store = {}
_image_store = {}
_name_generators = {}
_death_sentences_generators = {}
_kill_sentences_generators = {}
_variants = {}


def choice_random_name(gender):
    global _name_generators
    if not _name_generators:
        filepath = f'{GAMEROOT}/resources/texts/names.json'
        with open(filepath, 'rb') as f:
            data = json.load(f)

        man = data['man']
        random.shuffle(man)
        _name_generators['man'] = itertools.cycle(man)

        woman = data['woman']
        random.shuffle(woman)
        _name_generators['woman'] = itertools.cycle(woman)
    return next(_name_generators[gender])


def build_random_variant(variants):
    indexes = list(range(len(variants)))
    random.shuffle(indexes)
    length = random.randrange(1, len(variants))
    variants = [variants[i] for i in indexes[:length]]
    palette_source = [c for v in variants for c in v['origins']]
    palette_dest = []
    ids = []
    for variant in variants:
        index = random.randrange(0, len(variant['variants']))
        ids.append([variant['name'], index])
        palette_dest.extend(variant['variants'][index])
    id_ = '-'.join(f'{id_[0]}.{id_[1]}' for id_ in ids)
    return id_, palette_source, palette_dest


def choice_death_sentence(language):
    if not _death_sentences_generators:
        filepath = f'{GAMEROOT}/resources/texts/darwinaward.json'
        with open(filepath, 'rb') as f:
            data = json.load(f)
        for key in data:
            array = data[key]
            random.shuffle(array)
            _death_sentences_generators[key] = itertools.cycle(array)
    return next(_death_sentences_generators[language])


def choice_kill_sentence(language):
    if not _kill_sentences_generators:
        filepath = f'{GAMEROOT}/resources/texts/kills.json'
        with open(filepath, 'rb') as f:
            data = json.load(f)
        for key in data:
            array = data[key]
            random.shuffle(array)
            _kill_sentences_generators[key] = itertools.cycle(array)
    return next(_kill_sentences_generators[language])


def load_main_resources():
    load_image('resources/ui/gamepad.png', (0, 255, 0))


def quit_event():
    return any((
        event.type == pygame.KEYDOWN and
        event.key == pygame.K_ESCAPE or
        event.type == pygame.QUIT)
        for event in pygame.event.get())


def list_joysticks():
    pygame.joystick.init()
    pygame.joystick.get_count()
    joysticks = []
    for i in range(pygame.joystick.get_count()):
        try:
            joystick = pygame.joystick.Joystick(i)
            joystick.init()
            get_current_commands(joystick)
            joysticks.append(joystick)
        except BaseException:
            print(f'Unsupported joystick {joystick.get_name()}')
            raise
    return joysticks[:4]


def swap_colors(surface, palette1, palette2):
    """ THX Chat GPT:"""
    swapped_surface = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    original_pixels = pygame.PixelArray(surface)
    swapped_pixels = pygame.PixelArray(swapped_surface)
    for x in range(original_pixels.shape[0]):
        for y in range(original_pixels.shape[1]):
            color = original_pixels[x, y]
            # Transform a bit pixel into a list comparable with palette data.
            check = [color >> 24, color >> 16 & 0xff, color >> 8 & 0xff, color & 0xff]
            if check[-3:] in palette1:
                index = palette1.index(check[-3:])
                color = palette2[index]
                swapped_color = check[0] << 24 | color[0] << 16 | color[1] << 8 | color[2]
            else:
                swapped_color = color
            swapped_pixels[x, y] = swapped_color
    # PixelArray is expensive for memory, then we force an immediate delete.
    # In case of the garbage collector would delay the memory clear to later.
    del original_pixels
    del swapped_pixels
    return swapped_surface


def load_skins():
    directory = f'{GAMEROOT}/resources/animdata'
    skins = [f'{directory}/{file}' for file in os.listdir(directory)]
    for skin in skins:
        with open(skin, 'r') as f:
            data = json.load(f)
        load_skin(data)


def get_font(filename):
    return f'{GAMEROOT}/resources/fonts/{filename}'


def get_character_variant_ids(data):
    result = _variants.setdefault(data["name"], [])
    if result:
        return result
    for _ in range(VARIANTS_COUNT):
        result.append(build_random_variant(data['variants']))
    _variants[data["name"]] = result
    return result


def load_skin(data):
    size = data['framesize']
    sheets = data["sheets"]
    # Build original colors skin.
    result = [{
        side: load_frames(sheets[side], size, (0, 255, 0))
        for side in ('face', 'back')}]
    # Build color variants
    variants = get_character_variant_ids(data) if data.get('variants') else []
    for id_, palette1, palette2 in variants:
        skin = {}
        for side in ('face', 'back'):
            images = load_frames(
                sheets[side], size, (0, 255, 0), palette1, palette2, id_)
            skin[side] = images
        result.append(skin)
    return result


def load_frames(
        filepath, frame_size, key_color,
        palette1=None, palette2=None, variation=0):
    """
    Split a huge sheet in memory.
    """
    filepath = f'{GAMEROOT}/{filepath}'
    filename_id = f'{GAMEROOT}/{filepath}.{variation}'
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
