# -*- coding: utf-8 -*-
"""The four rungs for the candidates that land near the 47-57% band.

napharder.txt sized every lever at Standard. Four survive: one moves
the deck, one moves the Credit goal, one prices the unmeetable exam
clause, and one is the exam decision already on the table. This is
each of them across all four rungs, solo and Tier III - the two axes
the set band-checks.
"""
import time

import nap

GAMES = 20004
APPS = nap.APPRENTICES
RUNGS = ("Easy", "Standard", "Hard", "Nobulous")


def cell(tier):
    each = GAMES // len(APPS)
    return 100.0 * sum(nap.run(a, "-1", each, tier=tier) for a in APPS) / len(APPS)


def grid(label, levels, **dials):
    old = {k: getattr(nap, k) for k in dials}
    for k, v in dials.items():
        setattr(nap, k, v)
    print("  %s" % label)
    for r in RUNGS:
        nap.CREDITS_TO_LEAVE, nap.SETBACKS_IN_DECK = levels[r]
        solo, t3 = cell("none"), cell("III")
        print("    %-12s %d Cr / %d Sb   %6.1f%% %8.1f%%"
              % (r, levels[r][0], levels[r][1], solo, t3))
    nap.CREDITS_TO_LEAVE, nap.SETBACKS_IN_DECK = nap.LEVELS["Standard"]
    for k, v in old.items():
        setattr(nap, k, v)
    print()


# DERIVED FROM nap.LEVELS, NOT TYPED, as of 2026-11-27.  This dict read
#   {"Easy": (3, 1), "Standard": (4, 2), "Hard": (5, 3), "Nobulous": (6, 4)}
# and was TWO re-pegs stale: the Setback counts went up one on 2026-11-25
# and Nobulous's Credit goal went up one on 2026-11-27, so a grid headed
# "AS SHIPPED" described a ladder nobody had played for a fortnight.
#   THE SAME BUG WAS FOUND AND PINNED IN nap_ladder.py ON 2026-11-26 - the
# two file names differ by one underscore, the check written that day names
# the other one, and this file was not looked at.  It is in the check now.
SHIPPED = dict(nap.LEVELS)
# The two dated candidate ladders of 2026-11-25, kept exactly as they were
# measured, because napladder.txt is that day's record and is cited as such.
# Their labels below name each ladder outright rather than describing it as
# a step away from SHIPPED, which is no longer the ladder they were a step
# away from.
DECK_UP = {"Easy": (3, 2), "Standard": (4, 3), "Hard": (5, 4),
           "Nobulous": (6, 5)}
PRE_A = {"Easy": (4, 1), "Standard": (5, 2), "Hard": (6, 3),
         "Nobulous": (7, 4)}


def main():
    started = time.time()
    print("NAP ladders, %d games a rung, mean of the six Apprentices," % GAMES)
    print("FINF Reduce 1. Band is 47-57% on the solo column.")
    print()
    print("    %-12s %-12s %6s %9s" % ("", "", "no NRJ", "Tier III"))
    grid("AS SHIPPED, for the step sizes", SHIPPED)
    grid("1. THE 2026-11-25 LADDER, 3/2 4/3 5/4 6/5 - one Setback a rung "
         "up on what shipped that day", DECK_UP)
    grid("2. THE PRE-A CREDIT GOALS back, 4/1 5/2 6/3 7/4", PRE_A)
    grid("3. AN UNMEETABLE CONTRIBUTION CLAUSE COSTS 1 HEALTH",
         SHIPPED, EXAM_WAIVER_COST=1)
    grid("4. CONTRIBUTE = SUCCEED, the decision already open",
         SHIPPED, EXAM_NEED="success")
    grid("5. ONE MORE SETBACK *and* contribute = succeed",
         DECK_UP, EXAM_NEED="success")
    print("  Finished in %.0fs." % (time.time() - started))


if __name__ == "__main__":
    main()
