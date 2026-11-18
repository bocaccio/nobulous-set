# -*- coding: utf-8 -*-
"""How the four Buff HP values in bat.DIFFICULTY were chosen.

    python3 price_buff_ladder.py [games]          # the grid, then the ladder

BUFF HP SHIPPED AT 0 ON EVERY RUNG until 2026-11-18, so rules/bat.html
printed a column of four zeros - a table that reads as one nobody filled in,
and a card that did nothing in any game anyone played. Jon asked for real
numbers and for the measurement to pick them.

THE MEASUREMENT CANNOT PICK THEM ON ITS OWN. Buff HP in front of the printed
core makes every rung much harder, and the core ladder is pegged to the 20
Strong community band at Standard, so the question is what to hold fixed.
What this script holds fixed is the WIN RATES: for each rung it sweeps core
Health against Buff HP and then prints the pair whose win rate matches what
the zero column was measured at. The ladder it chose:

    Easy      9 core / 0 buff  60.7%  ->   8 / 1  59.8%
    Standard 10 core / 0 buff  52.0%  ->   9 / 1  51.6%
    Hard     12 core / 0 buff  38.6%  ->   9 / 2  39.2%
    Nobulous 14 core / 0 buff  26.0%  ->  11 / 2  27.5%

AND WHY THE SHIPPED COLUMN IS NOT STEEPER - WHICH IS A CHOICE AND NOT A
LIMIT. Under one constraint, that the core column keeps laddering near the
numbers it printed, 1/2/3/4 cannot be paid for: holding the rates at Buff HP
3 wants a Hard core near 7 and a Nobulous core near 9, and at Buff HP 2 it
wants a Standard core of 6 - LOWER than Easy's. The core needed stops
laddering before the wall column gets interesting.

DROP THAT CONSTRAINT AND A STEEP COLUMN IS AFFORDABLE. With the core flat at
its floor of 3, the walls below hold every rung's rate - a wall ladder
instead of a core ladder, which is what the 15-space track was drawn for.
The first version of this docstring said a steeper column "cannot be paid
for" full stop; that was the constraint talking, not the grid.

THE CORE CANNOT GO BELOW 3, and this is measured, not assumed. Degraded
Tissue Study prints "if successful, reduce the Prototyrant's Health dial by
2", and the Tyrant is dead the moment the dial reads 0 - before the wall or
a single Splice is touched. So a core of 1 or 2 hands the Rats the game
outright whenever that Experiment comes up and succeeds. At Easy with a
wall of 6, 6000 games a cell, turning that one card off is worth:

    core 1   66.0% -> 58.2%   -7.8      the card is an instant win
    core 2   61.0% -> 54.5%   -6.5      so is this
    core 3   51.8% -> 52.1%   +0.3      noise: it leaves the dial at 1
    core 4   50.6% -> 49.6%   -1.0      noise

That is also why a core x wall grid has a cliff between its 3 and 2 rows
that is twice what a point of core is worth anywhere else. Read a row above
3 as a free win and not as a tuning.

AND AT THE FLOOR THE WALL CAN BE MUCH BIGGER, which is the ladder the
15-space track was drawn for. Holding each rung's rate with core 3:

    Easy      core 3 / wall 3   61.7%   against a target of 60.7%
    Standard  core 3 / wall 4   52.1%   against 52.0%
    Hard      core 3 / wall 6   42.5%   against 38.6% - wall 7 is the fit
    Nobulous  core 3 / wall 6   40.2%   against 26.0% - far more fits

Nobulous wants a wall somewhere past 6 at core 3; big_wall measured core 3 /
wall 10 at 21.2%, so its fit is between. A flat core of 3 with the ladder
carried on the card is the OLD design - HANDOFF section 9a00000000: Buff HP
existed because the Health chip only reads to 20, and the bulk lived on the
card. What shipped on 2026-11-18 is the opposite, a core ladder with a small
wall, because it was the change that moved no published figure.

Pass a game count. 6000 a cell is enough to read the grid; the ladder at the
bottom is reprinted at 20000, which puts the standard error on a difference
near half a point.
"""
import sys

import bat

LEVELS = ("Easy", "Standard", "Hard", "Nobulous")
BUFFS = (0, 1, 2, 3)

# What the zero column was measured at, 20000 games a cell, tier none, on
# the code of 2026-11-18 - which is after FIRST_ATTACK_FREE, so these are
# half a point under the figures published before it.
WAS = {"Easy": (5, 9, 0), "Standard": (6, 10, 0),
       "Hard": (7, 12, 0), "Nobulous": (8, 14, 0)}


def grid(games):
    """Core Health against Buff HP, one rung at a time."""
    print("%d games a cell, tier none, every other dial shipping.\n" % games)
    for name in LEVELS:
        spec, core, _ = WAS[name]
        print("%s  (the zero column shipped %d core)" % (name, core))
        print("%-8s %s" % ("core", "  ".join("%7s" % ("buff %d" % b)
                                             for b in BUFFS)))
        for c in range(core - 4, core + 1):
            cells = []
            for b in BUFFS:
                bat.DIFFICULTY[name] = (spec, c, b)
                cells.append(100 * bat.run(name, games, tier="none"))
            print("%-8d %s" % (c, "  ".join("%6.1f%%" % v for v in cells)))
        print()
        sys.stdout.flush()


def ladder(games):
    """The chosen pairs against the zero column, side by side."""
    print("%d games a cell. The zero column, then what ships now.\n" % games)
    print("%-10s %16s %16s %8s" % ("rung", "was", "now", "delta"))
    for name in LEVELS:
        spec, core, buff = bat.DIFFICULTY[name]
        bat.DIFFICULTY[name] = WAS[name]
        was = 100 * bat.run(name, games, tier="none")
        bat.DIFFICULTY[name] = (spec, core, buff)
        now = 100 * bat.run(name, games, tier="none")
        print("%-10s %6s %8.1f%% %6s %8.1f%% %+7.1f"
              % (name, "%d/%d" % (WAS[name][1], WAS[name][2]), was,
                 "%d/%d" % (core, buff), now, now - was))
        sys.stdout.flush()


def main():
    games = int(sys.argv[1]) if len(sys.argv) > 1 else 6000
    base = dict(bat.DIFFICULTY)
    try:
        grid(games)
        bat.DIFFICULTY.update(base)
        print("-" * 56)
        ladder(max(games, 20000))
    finally:
        bat.DIFFICULTY.update(base)


if __name__ == "__main__":
    main()
