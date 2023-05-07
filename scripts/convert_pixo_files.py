import msgpack

smith_names = [ "José Delgado", "Pat' la fauche", "El Gringo", "Paul Regret", "Bud le soifard", "Willy the kid", "Swearingen", "Bill sans visage", "Jo la mite", "Sam le vautour", "Avrell Dalton", "Jo l'indien", "Personne", "Lucky Lyke", "Kiyan Lebreton", "Jijo", "Buffalo Bill", "John Wolf", "Biggy Bob", "Dick la prime", "Johnny Veinard", "Gravedigger Greg", "Doc Holiday", "Kit Carlson", "Bart Cassidy", "Black Jack", "Sean Mallory", "Jesse Jones", "Slab Le flingueur", "Avenger Chuck", "Pedro Ramirez", "Sam the vulture", "Sid Ketchum", "Handy Francky", "John Mitcell ", "Igor Terror", "Jackson Samuelson", "Kevin Kleetus Killer", "Gustave Pourrave", "Chuck Novice", "Eustache Long Mustach"]
janet_names = ["Mallory Knockx", "Belle Star", "Calamity Jane", "Elena Fuente", "Molly stark", "Vera Custer", "Rose Doolan", "Suzy Lafayette", "Bossy Alice", "Holy Mary", "Clem and Tine", "Nat Ginger", "Joyce Burkle", "Freaky gun Zoey", "Frida Stabyourback", "Tally Paris", "Georgia Ofmimind", "Mae Noman", "Fatty Lucy", "Ella Singzeblues", "Betsy Pullman", "Charlotte la crotte", "Nora Norak", "Pearl Beurkingsson", "Hope la choppe", "Carence Clarence", "Claire qui blaire", "Delilah Choke'O'La", "Eleanor Mc Gregor", "Cate Blood'Blade", "Caroline the Whale", "Maya Crapsoft", "Maori Fluffy", "Tora Jarmusch", "Jesse Horseteeth", "Tela Tientoala"]
kate_names = ["rania simple choix", "toto sifredy", "marion colt blond"],

filename = r"C:\Users\Lionel\Downloads\pixos-update-1(3)\pixos-sources_modified\smith.pixo"
with open(filename, 'rb') as f:
    data = msgpack.load(f)
data['data']['names'] = smith_names
del data['data']['gender']
data['data']['animations']['victory'] = {'images': [], 'exposures': []}
data['data']['animations']['defeat'] = {'images': [], 'exposures': []}
with open(filename, 'wb') as f:
    data = msgpack.dump(data, f)


filename = r"C:\Users\Lionel\Downloads\pixos-update-1(3)\pixos-sources_modified\janet.pixo"
with open(filename, 'rb') as f:
    data = msgpack.load(f)
data['data']['names'] = janet_names
del data['data']['gender']
data['data']['animations']['victory'] = {'images': [], 'exposures': []}
data['data']['animations']['defeat'] = {'images': [], 'exposures': []}
with open(filename, 'wb') as f:
    data = msgpack.dump(data, f)

filename = r"C:\Users\Lionel\Downloads\pixos-update-1(3)\pixos-sources_modified\kate.pixo"
with open(filename, 'rb') as f:
    data = msgpack.load(f)
data['data']['names'] = kate_names
del data['data']['gender']
data['data']['animations']['victory'] = {'images': [], 'exposures': []}
data['data']['animations']['defeat'] = {'images': [], 'exposures': []}
with open(filename, 'wb') as f:
    data = msgpack.dump(data, f)
