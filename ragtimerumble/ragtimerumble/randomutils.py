import random


def choose(items):
    '''
    this method is an utils to choose an element with a coefficient.
    :items: is a dict {'item1': coefficien as int}
    return a random key with a chance coefficient as value
    '''
    return random.choice([
        t for k, v in items.items()
        for t in tuple([k] * v) if v])
