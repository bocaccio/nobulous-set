"""Tune the Tyrant's Health against a target ladder.

    python healthsweep.py            # 4000 games per cell
    python healthsweep.py 8000

Difficulty is Specimens / Tyrant Health. Specimen count is held at each
difficulty's published value and only Health is swept, in the same
configuration table.py uses for the ladder: card effects on, random Rat
sides, and the commit policy that plays the threshold rules.

This replaces buffsweep.py. The dial used to be Buff HP on its own card,
because the Health chip only reads to 20 and the Tyrant's bulk had to live
somewhere; with the Splices carrying the fight those points fit on the dial
and the card left standard setup.

Two candidate ladders are printed, because the full table is more useful
than an argmin: the shape of a row says how much a point of Health is worth
at that difficulty, which is what you need when moving one.
"""
import sys

import bat

SPEC = {"Easy": 5, "Standard": 6, "Hard": 7, "Nobulous": 8}
LADDERS = {
    "CURRENT 50/41/29/19": {"Easy": 50, "Standard": 41, "Hard": 29,
                            "Nobulous": 19},
    "EVEN    50/40/30/20": {"Easy": 50, "Standard": 40, "Hard": 30,
                            "Nobulous": 20},
}
TRACK = range(5, 19)


def main(games=4000):
    print("Tyrant Health sweep. Card effects on, random Rat sides,")
    print("threshold commit policy. %d games per cell." % games)
    print()
    print("%-10s" % "Health" + "".join("%7d" % h for h in TRACK))

    rows = {}
    for name in ("Easy", "Standard", "Hard", "Nobulous"):
        row = []
        for hp in TRACK:
            bat.DIFFICULTY[name] = (SPEC[name], hp)
            row.append(100 * bat.run(name, games, card_effects=True,
                                     sides="random"))
        rows[name] = row
        print("%-10s" % name + "".join("%6.1f%%" % v for v in row), flush=True)

    for label, target in sorted(LADDERS.items()):
        print()
        print(label)
        prev = None
        for name in ("Easy", "Standard", "Hard", "Nobulous"):
            row = rows[name]
            best = min(range(len(row)), key=lambda b: abs(row[b] - target[name]))
            step = "" if prev is None else "  (%+.1f)" % (row[best] - prev)
            prev = row[best]
            print("  %-10s target %2d%% -> Health %2d  (%.1f%%)%s"
                  % (name, target[name], list(TRACK)[best], row[best], step))


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 4000)
