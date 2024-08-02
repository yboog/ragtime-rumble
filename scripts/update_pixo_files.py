import os
import msgpack
pixos = [
    r"C:\Users\Lionel\Downloads\janet(2).pixo",
    r"C:\Users\Lionel\Downloads\smith(1).pixo",
    r"C:\Users\Lionel\Downloads\kate(1).pixo",
    r"C:\Users\Lionel\Downloads\jo(2).pixo",
]

for pixo in pixos:
    with open(pixo, 'rb') as f:
        data = msgpack.load(f)

    import pprint
    pprint.pprint(data['data']['animations'])
    new_anims = (
        'startup',
        'sweating',
        'water')
    for anim in new_anims:
        data['data']['animations'][anim] = {'exposures': [], 'images': []}
    with open(f'{os.path.splitext(pixo)[0]}-fixed.pixo', 'wb') as f:
        msgpack.dump(data, f)
