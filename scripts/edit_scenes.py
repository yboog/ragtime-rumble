
import os
import json


directory = f"{os.path.dirname(__file__)}/../ragtimerumble/resources/scenes"
files = [f'{directory}/{f}' for f in os.listdir(directory)]
for file in files:
    with open(file, 'r') as f:
        data = json.load(f)

    # for path in data['paths']:
    #     path['gametypes'] = ['advanced', 'basic']

    # for target in data['targets']:
    #     target['gametypes'] = ['advanced', 'basic']

    # popspots = [{'gametypes': ['advanced', 'basic'], 'position': p} for p in data['popspots']]
    # data['popspots'] = popspots
    if not 'edit_data' in data:
        data['edit_data'] = {'background_placeholders': []}
    for bgph in data['edit_data']['background_placeholders']:
        bgph['tile'] = None

    with open(file, 'w') as f:
        json.dump(data, f, indent=2)