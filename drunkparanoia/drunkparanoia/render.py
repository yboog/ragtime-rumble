from drunkparanoia.io import get_image


def render_game(screen, characters):
    screen.fill((60, 0, 18))
    for player in characters:
        render_characters(screen, player)


def render_characters(screen, character):
    img = character.image
    screen.blit(get_image(img), character.render_position)
