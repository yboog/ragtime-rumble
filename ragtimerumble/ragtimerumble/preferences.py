

preferences = {
    'language': 'english'
}


def get(key):
    return preferences[key]


def set(key, value):
    preferences[key] = value