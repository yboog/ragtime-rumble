

EMPTY_ANIMDATA = {
    'barman' : {
        'name': 'eustache',
        'type': 'barman',
        'palettes': [],
        'framesize': [64, 64],
        'animations': {
            'idle': {'images': [], 'exposures': []},
            'towel': {'images': [], 'exposures': []},
            'towel-end': {'images': [], 'exposures': []},
            'towel-start': {'images': [], 'exposures': []},
            'walk': {'images': [], 'exposures': []}}
        },
    'chicken' : {
        'name': 'chicken',
        'type': 'chicken',
        'framesize': [64, 64],
        'y': -0,
        'center': [32, 55],
        'box': [-10, -8, 20, 10],
        'hitbox': [-10, -40, 20, 40],
        'palettes': [],
        'animations': {
            'idle-a': {'exposures': [], 'images':[]},
            'idle-b': {'exposures': [], 'images':[]},
            'idle-c': {'exposures': [], 'images':[]},
            'idle-d': {'exposures': [], 'images':[]},
            'idle-e': {'exposures': [], 'images':[]},
            'idle-f': {'exposures': [], 'images':[]},
            'idle-g': {'exposures': [], 'images':[]},
            'idle-h': {'exposures': [], 'images':[]},
            'idle-i': {'exposures': [], 'images':[]},
            'runcycle': {'exposures': [], 'images':[]},
            'runjump': {'exposures': [], 'images':[]},
            'scratch': {'exposures': [], 'images':[]},
            'walkcycle': {'exposures': [], 'images':[]},
            },
        },
    'dog': {
        'name': 'diego',
        'type': 'dog',
        'framesize': [64, 64],
        'center': [40, 58],
        'hitbox': [-10, -40, 20, 40],
        'palettes': [],
        'animations': {
            'bark': {'images': [], 'exposures': []},
            'growl': {'images': [], 'exposures': []},
            'idle': {'images': [], 'exposures': []},
            'siderun': {'images': [], 'exposures': []},
            'sit': {'images': [], 'exposures': []}}
        },
    'loop' : {
        'name': 'bob',
        'type': 'loop',
        'palettes': [],
        'framesize': [32, 32],
        'animations': {'loop': {'images': [], 'exposures': []}}
        },
    'pianist' : {
        'name': 'petrucciani',
        'type': 'pianist',
        'y': -1000,
        'palettes': [],
        'framesize': [64, 64],
        'palettes': [],
        'animations': {
            'fast1': {'images': [], 'exposures': []},
            'fast2': {'images': [], 'exposures': []},
            'fast3': {'images': [], 'exposures': []},
            'fast4': {'images': [], 'exposures': []},
            'slow1': {'images': [], 'exposures': []},
            'slow2': {'images': [], 'exposures': []},
            'slow3': {'images': [], 'exposures': []},
            'slow4': {'images': [], 'exposures': []}}
        },
    'playable' : {
        'name': 'character',
        'type': 'playable',
        'names': ['characher1'],
        'framesize': [64, 64],
        'center': [32, 56],
        'box': [-10, -8, 20, 10],
        'hitbox': [-10, -40, 20, 40],
        'palettes': [],
        'animations': {
            'bet': {'images': [], 'exposures': []},
            'balcony': {'images': [], 'exposures': []},
            'call': {'images': [], 'exposures': []},
            'coma': {'images': [], 'exposures': []},
            'death': {'images': [], 'exposures': []},
            'defeat': {'images': [], 'exposures': []},
            'drink': {'images': [], 'exposures': []},
            'gunshot': {'images': [], 'exposures': []},
            'idle': {'images': [], 'exposures': []},
            'order': {'images': [], 'exposures': []},
            'poker': {'images': [], 'exposures': []},
            'smoke': {'images': [], 'exposures': []},
            'suspicious': {'images': [], 'exposures': []},
            'startup': {'images': [], 'exposures': []},
            'sweating': {'images': [], 'exposures': []},
            'vomit': {'images': [], 'exposures': []},
            'victory': {'images': [], 'exposures': []},
            'walk': {'images': [], 'exposures': []},
            'water': {'images': [], 'exposures': []},
            'walk-back': {'images': [], 'exposures': []},
        }
    }
}

SIZE_LOCK_SHEET_TYPES = ('playable',)