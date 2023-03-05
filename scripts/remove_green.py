
import os
import itertools
from PIL import Image


GREEN = (0, 255, 0, 255)
BG = (0, 0, 0, 0)


repo_root = os.path.dirname(os.path.dirname(__file__))
files = (
    f"{repo_root}/ragtimerumble/resources/skins/smith.png",
    f"{repo_root}/ragtimerumble/resources/skins/janet.png",
    f"{repo_root}/ragtimerumble/resources/skins/sniper.png",
    f"{repo_root}/ragtimerumble/resources/skins/barman.png",
    f"{repo_root}/ragtimerumble/resources/vfx/coin-alert.png")
for file in files:
    img = Image.open(file)
    img = img.convert("RGBA")

    pixdata = img.load()
    for y, x in itertools.product(range(img.size[1]), range(img.size[0])):
        if pixdata[x, y] == GREEN:
            pixdata[x, y] = BG

    img.save(file)
