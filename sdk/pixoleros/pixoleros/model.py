import os
import msgpack
import platform
import uuid
from copy import deepcopy
from pixoleros.io import serialize_document, bytes_to_image
from pixoleros.imgutils import remove_key_color
from pixoleros.template import EMPTY_ANIMDATA


class Document:
    def __init__(self):
        self.data = deepcopy(EMPTY_ANIMDATA)
        self.library = {}
        self.animation = 'idle'
        self.hzoom = 1
        self._index = 0
        self.displayed_variants = {}
        self.displayed_palettes = []
        self.editing_color_index = ('', -1, -1)

    @staticmethod
    def load(data):
        document = Document()
        document.data = data['data']
        document.library = {
            k: PixoImage.load(v) for k, v in data['library'].items()}
        document.animation = data['animation']
        document.index = data['index']
        for animation in data['data']['animations']:
            images = document.data['animations'][animation]['images']
            document.data['animations'][animation]['images'] = images
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
            id_ = self.data['animations'][animation]['images'][i]
            return self.library[id_]
        except IndexError:
            # No imported images yet for current animation.
            return None

    def get_display_palette(self, name):
        return self.display_palettes.get(name, 0)

    def image(self, animation, frame):
        return self.library[self.image_id(animation, frame)]

    def image_id(self, animation, frame):
        animation = self.data['animations'][animation]
        return animation['images'][frame]

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
            del animation['images'][source[1]]
            del animation['exposures'][source[1]]

        return destination

    def delete_frames(self, frames):
        frames = sorted(frames, key=lambda x: x[1], reverse=True)
        ids = []
        for frame in frames:
            animation = self.data['animations'][frame[0]]
            ids.append(animation['images'][frame[1]])
            del animation['images'][frame[1]]
            del animation['exposures'][frame[1]]

        used_images = {
            img for animation in self.data['animations'].values()
            for img in animation['images']}
        for id_ in ids:
            if id_ in used_images:
                continue
            del self.library[id_]

    def import_images_at(self, paths, destination):
        if platform.platform().startswith('Win'):
            paths = [path.lstrip('/') for path in paths]
        images = [remove_key_color(path) for path in paths]
        for image in images:
            if image.size != (64, 64):
                raise ValueError('Image size must be 64px on 64px')
        images = [
            PixoImage(img, path, os.path.getctime(path))
            for img, path in zip(images, paths)]
        ids = [self.add_to_library(img) for img in images]
        anim = self.data['animations'][destination[0]]
        for id_ in reversed(ids):
            anim['images'].insert(destination[1], id_)
            anim['exposures'].insert(destination[1], 6)

    def add_to_library(self, image):
        while (id_ := str(uuid.uuid1())) in self.library:
            continue
        self.library[id_] = image
        return id_

    def internal_move(self, sources, destination, action='move'):
        similare = (destination[0], destination[1] - 1)
        if sources[0] in [destination, similare]:
            return sources

        items_to_insert = [{
            'image': self.image_id(src[0], src[1]),
            'exposure': self.exposure(src[0], src[1]),
        } for src in sorted(sources, key=lambda x: x[1], reverse=True)]

        if action == 'move':
            destination = self.remove_sources(sources, destination)

        anim = self.data['animations'][destination[0]]
        for item in items_to_insert:
            try:
                anim['images'].insert(destination[1], item['image'])
                anim['exposures'].insert(destination[1], item['exposure'])
            except IndexError:  # at the end of the list.
                anim['images'].append(item['image'])
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
