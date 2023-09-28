import random


VIRGIN_SCORES = {
    'round': 0,
    'player 1': {
        'player 2': [0, 0],
        'player 3': [0, 0],
        'player 4': [0, 0],
        'civilians': 0,
        'deaths': 0,
        'victory': 0,
        'cigarets': 0,
        'dranked_beers': 0,
        'money_earned': 0,
        'poker_balance': 0,
        'looted_bodies': 0
    },
    'player 2': {
        'player 1': [0, 0],
        'player 3': [0, 0],
        'player 4': [0, 0],
        'civilians': 0,
        'deaths': 0,
        'cigarets': 0,
        'victory': 0,
        'dranked_beers': 0,
        'money_earned': 0,
        'poker_balance': 0,
        'looted_bodies': 0
    },
    'player 3': {
        'player 1': [0, 0],
        'player 2': [0, 0],
        'player 4': [0, 0],
        'civilians': 0,
        'deaths': 0,
        'victory': 0,
        'cigarets': 0,
        'dranked_beers': 0,
        'money_earned': 0,
        'poker_balance': 0,
        'looted_bodies': 0
    },
    'player 4': {
        'player 1': [0, 0],
        'player 2': [0, 0],
        'player 3': [0, 0],
        'civilians': 0,
        'deaths': 0,
        'victory': 0,
        'cigarets': 0,
        'dranked_beers': 0,
        'money_earned': 0,
        'poker_balance': 0,
        'looted_bodies': 0
    }
}


def get_final_winner_index(scores):
    scores = [scores[p] for p in (f'player {n}' for n in range(1, 5))]
    for score in scores:
        score['kills'] = sum(
            score.get(p, [0, 0])[0]
            for p in (f'player {n}' for n in range(1, 5)))
    formated = [
        s['victory'] + (s['money_earned'] / 10) + (s['kills']) / 100
        for s in scores]
    if formated.count(max(formated)) == 1:
        return formated.index(max(formated))
    tie_players = [i for i, s in enumerate(formated) if s == max(formated)]
    print(tie_players)
    formated = [
        f - s['deaths'] - (s['civilians'] / 10) - (s['dranked_beers'] / 100) -
        (s['looted_bodies'] / 1000) for f, s in zip(formated, scores)]
    only_tie = [formated[p] for p in tie_players]
    print(tie_players)
    if only_tie.count(max(only_tie)) == 1:
        for i in tie_players:
            if formated[i] == max(only_tie):
                return i
    print(only_tie, formated, tie_players)
    tie_players = [i for i, s in enumerate(formated) if s == max(formated)]
    return random.choice(tie_players)


def get_most(scores, key):
    scores = [scores[p] for p in (f'player {n}' for n in range(1, 5))]
    if key == 'alcoholic':
        high = max(p['dranked_beers'] for p in scores)
        if high == 0:
            return []
        return [i for i in range(4) if scores[i]['dranked_beers'] == high]
    if key == 'guilty':
        high = max(p['civilians'] for p in scores)
        if high == 0:
            return []
        return [i for i in range(4) if scores[i]['civilians'] == high]
    if key == 'rich':
        high = min(p['money_earned'] for p in scores)
        if high == 0:
            return []
        return [i for i in range(4) if scores[i]['money_earned'] == high]
    if key == 'poor':
        high = min(p['money_earned'] for p in scores)
        if high == 0:
            return []
        return [i for i in range(4) if scores[i]['money_earned'] == high]
    if key == 'smoker':
        high = max(p['cigarets'] for p in scores)
        if high == 0:
            return []
        return [i for i in range(4) if scores[i]['cigarets'] == high]
    if key == 'vulture':
        high = max(p['looted_bodies'] for p in scores)
        if high == 0:
            return []
        return [i for i in range(4) if scores[i]['looted_bodies'] == high]
    if key == 'lucky':
        high = max(p['poker_balance'] for p in scores)
        if high == 0:
            return []
        return [i for i in range(4) if scores[i]['poker_balance'] == high]
    if key == 'loser':
        high = min(p['poker_balance'] for p in scores)
        if high == 0:
            return []
        return [i for i in range(4) if scores[i]['poker_balance'] == high]


MOST_KEYS = [
    'alcoholic',
    'guilty',
    'rich',
    'poor',
    'smoker',
    'vulture',
    'lucky',
    'loser'
]


def get_most_sheet(scores):
    player_recaps = [[], [], [], []]
    for key in MOST_KEYS:
        players = get_most(scores, key)
        for i, player_recap in enumerate(player_recaps):
            if i in players:
                player_recap.append(key)
    return player_recaps


def get_score_data(scores, row, col):
    row_keys = list(VIRGIN_SCORES)
    col_keys = (
        'player 1',
        'player 2',
        'player 3',
        'player 4',
        'total',
        'civilians',
        'victory')
    if col_keys[col] == 'total':
        data = [scores[row_keys[row]].get(col_keys[i]) for i in range(4)]
        data = [d for d in data if d is not None]
        return [sum(d[0] for d in data), sum(d[1] for d in data)]
    return scores[row_keys[row]].get(col_keys[col])
