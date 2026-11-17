# -*- coding: utf-8 -*-
"""What the Rats' free first attack costs them.

    python3 price_first_attack.py [games]

NOTHING IS FLIPPED OUT OF THE ATTACK DECK AT SETUP. A card used to be turned
face-up to start the discard and seed the first commit color; it also showed
the table one of the seven bad things waiting for it, so Jon dropped it on
2026-11-17. The price is that the Rats' opening attack honors no color at
all, and that is a rule change on a ladder somebody measured - so it gets
measured too.

bat.FIRST_ATTACK_FREE is the dial. True is the printed game; False is the
seeded color every figure published before 2026-11-17 was measured through.

THE TWO ARMS ARE NOT PAIRED and cannot be: the first attack is where the
Rats' choices diverge, so the random streams part there whatever this does
about the one draw the seed used to consume. That is what the game count is
for - 20000 a cell puts the standard error on a difference near half a
point, and only Easy moves further than that.
"""
import sys

import bat

LEVELS = ("Easy", "Standard", "Hard", "Nobulous")


def main():
    games = int(sys.argv[1]) if len(sys.argv) > 1 else 20000
    print("%d games a cell, tier none, every other dial shipping." % games)
    print()
    print("%-10s %8s %8s %7s" % ("rung", "seeded", "free", "delta"))
    was_dial = bat.FIRST_ATTACK_FREE
    try:
        for name in LEVELS:
            bat.FIRST_ATTACK_FREE = False
            was = 100 * bat.run(name, games, tier="none")
            bat.FIRST_ATTACK_FREE = True
            now = 100 * bat.run(name, games, tier="none")
            print("%-10s %7.1f%% %7.1f%% %+6.1f" % (name, was, now, now - was))
    finally:
        bat.FIRST_ATTACK_FREE = was_dial


if __name__ == "__main__":
    main()
