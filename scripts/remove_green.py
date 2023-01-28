
import os
import itertools
from PIL import Image


GREEN = (0, 255, 0, 255)
BG = (0, 0, 0, 0)


repo_root = os.path.dirname(os.path.dirname(__file__))
files = (
    # f"{repo_root}/drunkparanoia/resources/skins/smith_face.png",
    # f"{repo_root}/drunkparanoia/resources/skins/smith_back.png",
    f"{repo_root}/drunkparanoia/resources/skins/janet_face.png",
    f"{repo_root}/drunkparanoia/resources/skins/janet_back.png",
    f"{repo_root}/drunkparanoia/resources/skins/barman.png",)
for file in files:
    img = Image.open(file)
    img = img.convert("RGBA")

    pixdata = img.load()
    for y, x in itertools.product(range(img.size[1]), range(img.size[0])):
        if pixdata[x, y] == GREEN:
            pixdata[x, y] = BG

    img.save(file)
