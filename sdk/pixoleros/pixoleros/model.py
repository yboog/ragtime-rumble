import os
import msgpack
from copy import deepcopy
from pixoleros.template import EMPTY_ANIMDATA
from pixoleros.io import serialize_document, bytes_to_image


class Document:
    def __init__(self):
        self.data = deepcopy(EMPTY_ANIMDATA)
        self.library = {}
        self.animation = 'idle'
        self.side = 'face'
        self.hzoom = 1
        self._index = 0
        self.displayed_variants = {}
        self.displayed_palettes = []
        self.editing_color_index = ('', -1, -1)

    @staticmethod
    def load(data):
        document = Document()
        document.data = data['data']
        document.library = {k: PixoImage.load(v) for k, v in data['library'].items()}
        document.animation = data['animation']
        document.side = data['side']
        document.index = data['index']
        for animation in data['data']['animations']:
            for side in ('face', 'back'):
                images = document.data['animations'][animation]['images'][side]
                document.data['animations'][animation]['images'][side] = images
        return document

    @property
    def palettes(self):
        return self.data['palettes']

    def add_palette(self):
        self.data['palettes'].append({
            'name': f'palette-{len(self.palettes)}',
            'origins': [],
            'palettes': []})

    def add_palette_origins(self, index, color):
        self.data['palettes'][index]['origins'].append(color)
        for palette in self.data['palettes'][index]['palettes']:
            palette.append(color)

    def rename_palette(self, index, name):
        tmp = '{name}-{i}'
        basename = name
        i = 2
        while name in [p['name'] for p in self.palettes]:
            name = tmp.format(name=basename, i=i)
            i += 1
        palette = self.palettes[index]
        if palette['name'] in self.displayed_palettes:
            self.displayed_palettes.remove(palette['name'])
            self.displayed_palettes.append(name)
        if palette['name'] in self.displayed_variants:
            variant = self.displayed_variants[palette['name']]
            self.displayed_variants[name] = variant
            del(self.displayed_variants[palette['name']])
        palette['name'] = name

    @property
    def index(self):
        return max((0, min((self._index, sum(self.exposures) - 1))))

    @index.setter
    def index(self, n):
        self._index = max((0, min((n, sum(self.exposures) - 1))))

    @property
    def length(self):
        return max(
            sum(anim['exposures'])
            for anim in self.data['animations'].values())

    @property
    def exposures(self):
        return self.data['animations'][self.animation]['exposures']

    @property
    def current_image(self):
        try:
            i = frame_index_from_exposures(self.index, self.exposures)
            animation = self.animation
            id_ = self.data['animations'][animation]['images'][self.side][i]
            return self.library[id_]
        except IndexError:
            print(i, 'error')
            return None

    def get_display_palette(self, name):
        return self.display_palettes.get(name, 0)

    def image(self, animation, frame, side=None):
        return self.library[self.image_id(animation, frame, side)]

    def image_id(self, animation, frame, side=None):
        animation = self.data['animations'][animation]
        return animation['images'][side or self.side][frame]

    def animation_exposures(self, animation):
        return self.data['animations'][animation]['exposures']

    def exposure(self, animation, frame):
        return self.animation_exposures(animation)[frame]

    def save(self, filepath):
        data = serialize_document(self)
        with open(filepath, 'wb') as f:
            msgpack.dump(data, f)

    def switch_palette(self, palette_name):
        if palette_name in self.displayed_palettes:
            self.displayed_palettes.remove(palette_name)
        else:
            self.displayed_palettes.append(palette_name)

    def remove_sources(self, sources, destination=None):
        """
        Destination is a point in the dopesheet which is moved with the remove
        and need to be remapper. It does NOT affect the deletion.
        If not specified, the methods returns None
        """
        need_remap = (
            destination and
            (offset := any(
                (s[0] == destination[0] and s[1] < destination[1])
                for s in sources)))

        if need_remap:
            destination = destination[0], destination[1] - offset

        for source in sorted(sources, key=lambda x: x[1], reverse=True):
            animation = self.data['animations'][source[0]]
            del animation['images']['face'][source[1]]
            del animation['images']['back'][source[1]]
            del animation['exposures'][source[1]]

        return destination

    def internal_move(self, sources, destination, action='move'):
        similare = (destination[0], destination[1] - 1)
        if sources[0] in [destination, similare]:
            return sources

        items_to_insert = [{
            'face': self.image_id(src[0], src[1], 'face'),
            'back': self.image_id(src[0], src[1], 'back'),
            'exposure': self.exposure(src[0], src[1]),
        } for src in sorted(sources, key=lambda x: x[1], reverse=True)]

        if action == 'move':
            destination = self.remove_sources(sources, destination)

        anim = self.data['animations'][destination[0]]
        for item in items_to_insert:
            try:
                anim['images']['face'].insert(destination[1], item['face'])
                anim['images']['back'].insert(destination[1], item['back'])
                anim['exposures'].insert(destination[1], item['exposure'])
            except IndexError:  # at the end of the list.
                anim['images']['face'].append(item['face'])
                anim['images']['back'].append(item['back'])
                anim['exposures'].append(item['exposure'])
        # return new items infos
        return [
            (destination[0], destination[1] + i)
            for i in range(len(items_to_insert))]

    @property
    def palette_override(self):
        palettes = [
            p for p in self.palettes
            if self.displayed_variants.get(p['name'])]
        origins = []
        variants = []
        for palette in palettes:
            origins.extend(palette['origins'])
            index = self.displayed_variants[palette['name']] - 1
            variants.extend(palette['palettes'][index])
        return origins, variants


def frame_index_from_exposures(index, exposures):
    """
    frame indexes:
    0       1   2           3           4
    exposures indexes:
    0 - 1 - 2 - 3 - 4 - 5 - 6 - 7 - 8 - 9
    Return examples:
        index = 1 -> 2
        index = 3 -> 6
        index = 8 -> 3
    """
    loop = 0
    for i, d in enumerate(exposures):
        for _ in range(d):
            if index == loop:
                return i
            loop += 1
    return 0


class PixoImage:
    def __init__(self, image, path, ctime):
        self.image = image
        self.path = path
        self.ctime = ctime
        self._reference_exists = None
        self._file_modified = None

    @staticmethod
    def load(data):
        image = bytes_to_image(data['image'])
        return PixoImage(image, data['path'], data['ctime'])

    @property
    def reference_exists(self):
        if not self._reference_exists:
            self._reference_exists = os.path.exists(self.path)
        return self._reference_exists

    @property
    def file_modified(self):
        if not self.reference_exists:
            return False
        if not self._file_modified:
            self._file_modified = os.path.getctime(self.path) != self.ctime
        return self._file_modified

    def refresh(self):
        self._reference_exists = None
        self._file_modified = None
