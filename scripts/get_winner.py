import random


VIRGIN_SCORES = {
    'round': 0,
    'player 1': {
        'player 2': [3, 0],
        'player 3': [0, 0],
        'player 4': [3, 0],
        'civilians': 0,
        'deaths': 0,
        'victory': 3,
        'dranked_beers': 1,
        'money_earned': 0,
        'poker_balance': 0,
        'looted_bodies': 0
    },
    'player 2': {
        'player 1': [2, 0],
        'player 3': [0, 0],
        'player 4': [4, 0],
        'civilians': 0,
        'deaths': 0,
        'victory': 3,
        'dranked_beers': 0,
        'money_earned': 0,
        'poker_balance': 0,
        'looted_bodies': 0
    },
    'player 3': {
        'player 1': [1, 0],
        'player 2': [1, 0],
        'player 4': [1, 0],
        'civilians': 0,
        'deaths': 0,
        'victory': 2,
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
        return formated.index(max(formated)) + 1
    tie_players = [i for i, s in enumerate(formated) if s == max(formated)]
    formated = [
        f - s['deaths'] - (s['civilians'] / 10) - (s['dranked_beers'] / 100) -
        (s['looted_bodies'] / 1000) for f, s in zip(formated, scores)]
    only_tie = [formated[p] for p in tie_players]
    if only_tie.count(max(only_tie)) == 1:
        for i in tie_players:
            if formated[i] == max(only_tie):
                return i + 1
    only_tie = [i for i in only_tie if formated[i] == max(only_tie)]
    return random.choice(only_tie) + 1


print(get_final_winner_index(VIRGIN_SCORES))