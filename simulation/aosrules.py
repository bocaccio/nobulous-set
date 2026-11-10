# -*- coding: utf-8 -*-
"""AoS under both proposed draw rules, against the printed ones.

  1. Shuffle the Program deck and take a Program at random each turn.
  2. Do not run the last Program in the deck: one left at the start of
     a turn ends the cycle, and that Program goes back in for the next.

The first cannot change the odds - see aosdraw.py, which measures that
rather than asserting it - so everything below is the second one. It
is here as the pair because the pair is what would be printed.

THE WHOLE GRID, because the question a rules change raises is what it
does to the LADDER, not what it does to one cell. The four levels are
a difficulty ladder and the four tiers are a campaign; a change worth
+2 at Easy and +4 at Nobulous has flattened the ladder even though
both numbers are small.

Figures are win rate over SEEDS independent runs of GAMES each; the
+/- is the standard error across those runs, so a difference smaller
than about two of them is noise.
"""
import sys

import aosdraw

GAMES = 6000
SEEDS = 5
LEVELS = ["Easy", "Standard", "Hard", "Nobulous"]
TIERS = ["none", "I", "II", "III"]


def grid():
    print(__doc__)
    print("%d games x %d seeds per cell\n" % (GAMES, SEEDS))
    aosdraw.GAMES, aosdraw.SEEDS = GAMES, SEEDS
    rows = {}
    for tier in TIERS:
        for level in LEVELS:
            was = aosdraw.measure(level, tier, False, False)
            now = aosdraw.measure(level, tier, True, True)
            rows[(tier, level)] = (was, now)
            print("  measured tier %-4s %-9s %.1f%% -> %.1f%%"
                  % (tier, level, 100 * was[0], 100 * now[0]))
    print("\nWIN RATE, printed rules -> both new rules\n")
    print("%-10s %22s %22s %22s %22s"
          % ("level", "tier none", "tier I", "tier II", "tier III"))
    for level in LEVELS:
        cells = []
        for tier in TIERS:
            was, now = rows[(tier, level)]
            cells.append("%5.1f%% -> %5.1f%%  %+4.1f"
                         % (100 * was[0], 100 * now[0],
                            100 * (now[0] - was[0])))
        print("%-10s %s" % (level, " ".join("%22s" % c for c in cells)))
    print("\nSTANDARD ERROR on each figure, for reading the +/- above\n")
    for level in LEVELS:
        cells = ["%.1f / %.1f" % (100 * rows[(t, level)][0][1],
                                  100 * rows[(t, level)][1][1])
                 for t in TIERS]
        print("%-10s %s" % (level, " ".join("%22s" % c for c in cells)))
    print("\nPROGRAMS FACED, printed -> both\n")
    for level in LEVELS:
        cells = ["%.2f -> %.2f" % (rows[(t, level)][0][2],
                                   rows[(t, level)][1][2])
                 for t in TIERS]
        print("%-10s %s" % (level, " ".join("%22s" % c for c in cells)))
    print("\nREACHED ADVANCED PROGRAMMING, printed -> both\n")
    for level in LEVELS:
        cells = ["%.1f%% -> %.1f%%" % (100 * rows[(t, level)][0][3],
                                       100 * rows[(t, level)][1][3])
                 for t in TIERS]
        print("%-10s %s" % (level, " ".join("%22s" % c for c in cells)))
    # THE LADDER ITSELF. The steps between levels are what a difficulty
    # ladder IS, so they are reported rather than left to be subtracted
    # out of the table by eye.
    print("\nTHE LADDER: step between levels, printed -> both\n")
    for tier in TIERS:
        steps = []
        for a, b in zip(LEVELS, LEVELS[1:]):
            steps.append("%4.1f -> %4.1f"
                         % (100 * (rows[(tier, a)][0][0]
                                   - rows[(tier, b)][0][0]),
                            100 * (rows[(tier, a)][1][0]
                                   - rows[(tier, b)][1][0])))
        print("tier %-5s %s" % (tier, "   ".join(steps)))


if __name__ == "__main__":
    sys.exit(grid())
