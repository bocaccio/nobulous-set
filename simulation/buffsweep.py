import bat, sys
GAMES = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
SPEC = {"Easy": 5, "Standard": 6, "Hard": 7, "Nobulous": 8}
TARGET = {"Easy": 50, "Standard": 43, "Hard": 32, "Nobulous": 21}
print("Buff HP sweep, in the SAME configuration table.py uses for the published")
print("ladder: card effects on, random Rat sides. Specimen count is held at each")
print("difficulty's value while Buff HP is swept. %d games per cell." % GAMES)
print()
print("%-10s" % "Buff HP" + "".join("%7d" % b for b in range(0, 16)))
for name in ("Easy", "Standard", "Hard", "Nobulous"):
    row = []
    for buff in range(0, 16):
        bat.DIFFICULTY[name] = (SPEC[name], buff)
        # Must match table.py:95 or the targets below mean nothing.
        row.append(100 * bat.run(name, GAMES, card_effects=True, sides="random"))
    print("%-10s" % name + "".join("%6.1f%%" % v for v in row), flush=True)
    best = min(range(len(row)), key=lambda b: abs(row[b] - TARGET[name]))
    print("%-10s  target %d%% -> closest Buff HP %d (%.1f%%)"
          % ("", TARGET[name], best, row[best]), flush=True)
