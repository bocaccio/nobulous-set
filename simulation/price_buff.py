# -*- coding: utf-8 -*-
"""What a point of the Tyrant's outer layer costs the Rats.

    python3 price_buff.py [games]

THE FOUR LAYER VALUES IN bat.DIFFICULTY CANNOT BE PICKED BY EYE. The core
Health ladder is pegged to the 20 Strong community band - Standard sits at
52.8%, and CARD_MANIFEST rev 28 put it there on purpose after finding it 25
points above the band - so any layer added in front of that core moves a
number somebody measured. This prints the price list so the choice is made
against it.

A point of LAYER is not a point of CORE. While the layer stands, the five
Splices shelter behind it at full strength: the Tyrant keeps its largest
Splice Value, and the number of dice that Value draws, for the whole time
the Rats spend stripping it. The last column says how many points of core
Health the same win-rate drop would have cost, which is the honest exchange
rate between the two stats.
"""
import sys

import bat

LEVELS = ("Easy", "Standard", "Hard", "Nobulous")
LAYERS = (0, 1, 2, 3, 4, 6)


def sweep(games):
    base = dict(bat.DIFFICULTY)
    out = {}
    for name in LEVELS:
        spec, core, _ = base[name]
        row = {}
        for layer in LAYERS:
            bat.DIFFICULTY[name] = (spec, core, layer)
            row[layer] = 100 * bat.run(name, games, tier="none")
        # ...AND THE SAME DROP BOUGHT WITH CORE HEALTH INSTEAD, so the two
        # stats can be compared in the only unit that matters. Measured the
        # same way rather than assumed linear.
        core_rows = {}
        for extra in (1, 2, 3, 4, 6):
            bat.DIFFICULTY[name] = (spec, core + extra, 0)
            core_rows[extra] = 100 * bat.run(name, games, tier="none")
        bat.DIFFICULTY[name] = base[name]
        out[name] = (row, core_rows)
    return out


def main():
    games = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
    res = sweep(games)
    print("%d games a cell, every other dial at its shipping value.\n" % games)
    head = "  ".join("%6s" % ("L%d" % l) for l in LAYERS)
    print("%-10s %s" % ("core+layer", head))
    for name in LEVELS:
        row = res[name][0]
        print("%-10s %s" % (name, "  ".join("%5.1f%%" % row[l]
                                            for l in LAYERS)))
    print("\nWHAT A POINT OF LAYER COSTS, against the same rung at layer 0:")
    for name in LEVELS:
        row = res[name][0]
        print("%-10s %s" % (name, "  ".join(
            "%+5.1f" % (row[l] - row[0]) for l in LAYERS)))
    print("\nAND THE SAME POINTS SPENT ON CORE HEALTH INSTEAD:")
    head = "  ".join("%6s" % ("+%d" % e) for e in (1, 2, 3, 4, 6))
    print("%-10s %s" % ("", head))
    for name in LEVELS:
        base_v = res[name][0][0]
        cr = res[name][1]
        print("%-10s %s" % (name, "  ".join(
            "%+5.1f" % (cr[e] - base_v) for e in (1, 2, 3, 4, 6))))


if __name__ == "__main__":
    main()
