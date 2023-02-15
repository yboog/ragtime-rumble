import os
import json
from drunkparanoia.config import CHARACTER_STATUSES

active = False
render_path = False
log_coordinates = False

coordinates_log = []


def log_npc_coordinates(scene):
    for npc in scene.npcs:
        if npc.character.status != CHARACTER_STATUSES.OUT:
            if npc.character.speed:
                coordinates_log.append(npc.character.coordinates.position)


def close():
    if active is False:
        return
    statpath = f'{os.path.dirname(__file__)}/../../refs/coord.json'
    with open(statpath, 'w') as f:
        json.dump(coordinates_log, f)
