

preferences = {
    'language': 'english',
    'gametype': 'advanced'
}


def get(key):
    return preferences[key]


def set(key, value):
    preferences[key] = value