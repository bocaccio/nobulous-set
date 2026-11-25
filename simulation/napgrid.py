# -*- coding: utf-8 -*-
"""The NAP grid alone, at the shape and sample size table.py uses.

table.py cannot be run whole: it measures BAT with simulation/bat.py,
retired on 2026-11-20 in favour of batrev.py, which still reads 87% at
Standard against a published 53.2%. Running it would overwrite a third
of RESULTS.txt with figures for a game that no longer exists. So the
NAP third is regenerated here, cell for cell the way table.py builds
it - the mean of the six Apprentices at FINF Reduce 1, four tiers -
and pasted in, with the BAT third left standing and marked.

Run from simulation/ so `import nap` resolves. The ladder is read from
nap.LEVELS, so this cannot measure a table the model does not play.
"""
import sys
import time

import nap

GAMES = 20004
APPS = nap.APPRENTICES
TIERS = nap.TIERS   # ("none", "I", "II", "III")
LEVELS = nap.LEVELS
ORDER = ("Easy", "Standard", "Hard", "Nobulous")


def cell(tier):
    each = GAMES // len(APPS)
    return 100.0 * sum(nap.run(a, "-1", each, tier=tier) for a in APPS) / len(APPS)


def main():
    started = time.time()
    print("  difficulty = the Credit goal and the Setbacks in the deck")
    print()
    print("%-29s %6s %9s %9s %9s"
          % ("", "no NRJ", "Tier I", "Tier II", "Tier III"))
    rows = {}
    for level in ORDER:
        nap.CREDITS_TO_LEAVE, nap.SETBACKS_IN_DECK = LEVELS[level]
        rows[level] = [cell(t) for t in TIERS]
        print("  %-27s %s"
              % ("%s  %d Cr / %d Sb" % ((level,) + LEVELS[level]),
                 " ".join("%8.1f%%" % x for x in rows[level])))
        sys.stdout.flush()
    print()
    solo = [rows[l][0] for l in ORDER]
    print("  solo steps  %s"
          % "  ".join("%.1f" % (solo[i] - solo[i + 1]) for i in range(3)))
    print()
    print("  EVERY APPRENTICE AT STANDARD, %d games each - the"
          % GAMES)
    print("  per-Apprentice band check the set applies.")
    nap.CREDITS_TO_LEAVE, nap.SETBACKS_IN_DECK = LEVELS["Standard"]
    each = GAMES
    vals = []
    for a in APPS:
        v = 100.0 * nap.run(a, "-1", each)
        vals.append(v)
        print("    %-16s %5.1f%%   %s"
              % (a, v, "in band" if 47 <= v <= 57
                 else ("ABOVE the band" if v > 57 else "BELOW the band")))
        sys.stdout.flush()
    print("    %-16s %5.1f    spread, %.1f to %.1f"
          % ("", max(vals) - min(vals), min(vals), max(vals)))
    print()
    print("  Mean of the six Apprentices, FINF Reduce 1.")
    print("  %d games a cell. Finished in %.0fs."
          % (GAMES, time.time() - started))


if __name__ == "__main__":
    main()
