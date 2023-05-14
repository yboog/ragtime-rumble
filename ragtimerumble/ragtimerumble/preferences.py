

preferences = {
    'language': 'english',
    'gametype': 'advanced',
    'rounds': 10,
}


def get(key):
    return preferences[key]


def set(key, value):
    preferences[key] = value