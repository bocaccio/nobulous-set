# -*- coding: utf-8 -*-
"""THE AoS GRID, whole, at the shape and sample RESULTS.txt publishes.

    python aosgrid.py            # 20,000 games a Technician a cell
    python aosgrid.py 2000       # a pilot; do not publish one

WHY THIS FILE EXISTS. table.py cannot be run whole - it measures BAT with
simulation/bat.py, retired 2026-11-20 for batrev.py, which still reads 87%
at Standard against a published 53.2% - so the AoS third of RESULTS.txt was
assembled from TWO runs with a hand-written note saying which cells came
from which: Hard and Nobulous from aosvol.py on 2026-11-25, Easy and
Standard's Tier columns carried over from 2026-11-12, and their solo cells
re-measured as a control. That note was correct and it was also four
paragraphs of bookkeeping that had to be rewritten every time a rung moved.
This measures all sixteen cells in one run, so there is nothing to track.

THE LADDER IS READ FROM aos.LEVELS, so this cannot measure a table the
model does not play - the failure nap_ladder.py spent a fortnight in, with
a typed copy of a ladder that had stepped twice.

THE SAMPLE IS PER TECHNICIAN, which is the one thing easy to get wrong
here. aosvol_finals.txt's own header says "THE SHORTLIST at 20000 games per
Technician, mean of the six", so a published AoS cell is 120,000 games, not
20,000. NAP's grid is the other way round - napgrid.py's 20,004 is the
total, 3,334 an Apprentice - and the two files say "20,000 games a cell"
about samples six times apart.

AND THE DEAL-AGAIN RATE IS PUBLISHED BESIDE THE WIN RATE, from 2026-11-27,
because it is now a cost the ladder pays on purpose. COLOR_FLOOR re-deals
any setup leaving a colour on fewer than two of the ten Programs, and
Specialized carries TWO required-colour dots where the other three classes
carry one - so it is the colour carrier, and a rung that buys difficulty by
cutting it buys re-deals with the same card. Holding Unstable at three on
every rung (Jon, 2026-11-27) leaves Specialized as the only thing the two
ends have left to spend, and both ends now re-deal about one setup in four.
A figure that drives a design decision belongs in the published table and
not in a sweep nobody reruns.
"""
import statistics
import sys
import time

import aos
import aosends   # dealagain() lives there; one owner, not a second copy
import peg

# The four NRJ tiers aos.run accepts, in the order RESULTS.txt prints them.
TIERS = ("none", "I", "II", "III")
ORDER = tuple(aos.LEVEL_NAMES)
DEFAULT_GAMES = 20000


def cell(level, tier, games):
    """One published cell: the mean of the six Technicians."""
    return 100.0 * statistics.mean(
        aos.run(level, games, tier=tier, tech=t) for t in aos.TECHS)


def grid(games):
    print("  difficulty = the Routine/Specialized/Unstable/Volatile mix")
    print("")
    print("%-28s %8s %9s %9s %9s %11s"
          % ("", "no NRJ", "Tier I", "Tier II", "Tier III", "deal-again"))
    rows = {}
    for level in ORDER:
        mix = aos.LEVELS[level]
        rows[level] = [cell(level, t, games) for t in TIERS]
        print("  %-26s %s %10.1f%%"
              % ("%s  %d/%d/%d/%d" % ((level,) + mix),
                 " ".join("%8.1f%%" % v for v in rows[level]),
                 aosends.dealagain(mix)),
              flush=True)
    return rows


def against_target(rows):
    solo = [rows[l][0] for l in ORDER]
    print("")
    print("  target      %s   simulation/peg.py, %s's %s"
          % (" ".join("%8.1f%%" % peg.HOUSE[l] for l in ORDER),
             peg.PEG_FAMILY, peg.PEG_COLUMN))
    print("  off         %s"
          % " ".join("%+8.1f " % v for v in peg.off(solo)))
    print("  steps       %s   target steps %s"
          % (" ".join("%8.1f " % v for v in peg.ladder_steps(solo)),
             " / ".join("%.1f" % v
                        for v in peg.ladder_steps(peg.house_tuple()))))
    print("  Standard against the community band: %.1f%% (%s)"
          % (solo[1], peg.in_band(solo[1])))
    if [(a, b) for a, b in zip(solo, solo[1:]) if a <= b]:
        print("  THE SOLO LADDER IS NOT MONOTONE: %s"
              % " > ".join("%.1f" % v for v in solo))
    else:
        print("  the solo ladder is monotone, which is the one shape it "
              "must have.")
    for level in ORDER:
        if rows[level][3] >= rows[level][0]:
            print("  %s TIER III (%.1f) IS NOT BELOW ITS SOLO CELL (%.1f)."
                  % (level, rows[level][3], rows[level][0]))
    return solo


def spread(games):
    """Every Technician at Standard - the per-character band check."""
    print("")
    print("  EVERY TECHNICIAN AT STANDARD, %d games each." % games)
    vals = []
    lo, hi = peg.BAND
    for t in aos.TECHS:
        v = 100.0 * aos.run("Standard", games, tech=t)
        vals.append(v)
        print("    %-12s %5.1f%%   %s" % (t, v, peg.in_band(v)), flush=True)
    print("    %-12s %5.1f    spread, %.1f to %.1f"
          % ("", max(vals) - min(vals), min(vals), max(vals)))
    return vals


def main():
    games = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_GAMES
    started = time.time()
    print("AoS  Automaton of Shale - the whole grid, one run.")
    print("%d games per Technician per cell, mean of the six, seed 20 - so "
          "%d games" % (games, games * len(aos.TECHS)))
    print("a cell. Deal-again is %d analytic replays of the first deal, "
          "COLOR_FLOOR = %d." % (aosends.DEALS, aos.COLOR_FLOOR))
    if games != DEFAULT_GAMES:
        print("THIS IS NOT THE PUBLISHED SAMPLE (%d). Do not paste it into "
              "RESULTS.txt." % DEFAULT_GAMES)
    print("")
    rows = grid(games)
    against_target(rows)
    spread(games)
    print("")
    print("  Finished in %.0fs." % (time.time() - started))
    return 0


if __name__ == "__main__":
    sys.exit(main())
