from ragtimerumble.coordinates import Coordinates
from ragtimerumble.io import load_data
from ragtimerumble.pathfinding import point_in_rectangle
from ragtimerumble.sprite import SpriteSheet
from ragtimerumble.sniperreticle import SniperReticle


class Sniper:
    def __init__(
            self, scene=None, file=None,
            startposition=None, zone=None,
            interaction_zone=None, **_):
        self.data = load_data(file)
        self.spritesheet = SpriteSheet(self.data, 'idle')
        self.coordinates = Coordinates((startposition))
        self.reticle = SniperReticle(zone, scene)
        self.interaction_zone = interaction_zone
        self.scene = scene
        self.price = 1
        self.zone = zone
        scene.sniperreticles.append(self.reticle)

    def create_coin_vfx(self):
        position = list(self.coordinates.position)
        position[0] += 25
        self.scene.create_vfx('coin-alert', position)

    def corruption_attempt(self, player):
        if self.spritesheet.animation == 'gunshot-goback':
            return False
        if self.price > player.coins:
            return False
        if player == self.reticle.player:
            return False
        player.coins -= self.price
        self.price += 1
        if self.spritesheet.animation == 'idle':
            self.spritesheet.animation = 'go-aim'
            self.spritesheet.index = 0
        self.reticle.player = player
        self.create_coin_vfx()
        return True

    def meet(self, position):
        return point_in_rectangle(position, *self.interaction_zone)

    @property
    def render_position(self):
        return self.coordinates.position

    @property
    def switch(self):
        return 2000

    def __next__(self):
        next(self.reticle)
        if not self.spritesheet.animation_is_done:
            next(self.spritesheet)
            return

        match self.spritesheet.animation:
            case 'idle':
                self.spritesheet.index = 0
            case 'aim-idle':
                self.spritesheet.index = 0
            case 'go-aim':
                self.spritesheet.animation = 'aim-idle'
                self.spritesheet.index = 0
            case 'gunshot-goback':
                self.spritesheet.animation = 'idle'
                self.spritesheet.index = 0

    def shoot(self):
        self.price = 1
        self.reticle.shoot()
        self.spritesheet.animation = 'gunshot-goback'
        self.spritesheet.index = 0

    @property
    def image(self):
        return self.spritesheet.image()

