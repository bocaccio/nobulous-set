# -*- coding: utf-8 -*-
"""WHAT IT WOULD COST TO PUT AoS'S TWO ENDS ON THE PEG.

    python aosends.py            # 1500 games per Technician per cell
    python aosends.py 4000       # slower, tighter

Re-pegging on 2026-11-26 (simulation/peg.py) found AoS's middle landing and
its two ends out. THIS IS THE LADDER AS IT STOOD THAT DAY, which is what the
sweep below was run against; the two ends stepped on 2026-11-27 and the note
after the table says to what, so do not read this as the shipped mix.

    rung       shipped mix   win    target   off
    Easy        4/3/3/0     62.4     70.5   -8.1    eight points TOO HARD
    Standard    2/3/5/0     52.3     50.4   +1.9    lands
    Hard        0/4/4/2     38.2     38.5   -0.3    lands
    Nobulous    0/3/3/4     29.1     21.2   +7.9    eight points TOO EASY

WHAT SHIPPED, 2026-11-27, AND IT IS NOT WHAT THIS FILE FOUND. The sweep's
answers were Easy 4/6/0/0 at +0.0 and Nobulous 0/3/0/7 at +0.6, both of them
re-dealing LESS often than the rungs they would replace. Neither shipped:
each builds a rung from two classes and deals no Unstable Program at all,
and Jon ruled that Specialized and Unstable must appear at all four rungs.
The shipped ends are the nearest cells in the tables below that carry every
class - Easy 5/2/3/0 and Nobulous 0/2/3/5 - and they are FURTHER from the
target than the cells that do not, and re-deal MORE often, because
Specialized is the colour carrier and holding Unstable at three leaves it as
the only card either end has left to spend. simulation/aosgrid.py measures
what shipped at the published sample; this file is the sizing it was chosen
from.

AoS's only ladder dial is COMPOSITION: which ten of the thirty-two printed
Programs the rung is dealt from, eight per class and no count above eight.
Every printed Target and every rule is the same on all four rungs.  So the
question is not "what should move" but "is the target REACHABLE AT ALL by
dealing a different ten cards", and at the Nobulous end that has already
been answered no once: the floor over every four-Volatile mix was 27.5%
against a target then believed to be 25.8.  The target is now 21.2.

THE SECOND COLUMN IS THE DEAL-AGAIN RATE AND IT IS NOT A FOOTNOTE.
COLOR_FLOOR re-deals any setup leaving a colour on fewer than two of the
ten Programs, and Specialized carries TWO required-colour dots where the
other three classes carry one (Carry a Moving Load four).  So difficulty is
NON-MONOTONIC in Specialized, and every mix that buys difficulty by cutting
it buys re-deals as well.  A rung that re-deals one setup in three is not a
rung, whatever its win rate says.  Measured here by replaying the first
deal analytically, which is cheap and exact - 200,000 deals a mix.

The Easy end has the mirror of the same problem: Routine is the easiest
class, so the way to make Easy easier is more Routine, and the cards it
displaces are the ones carrying the colours.
"""
import random
import statistics
import sys

import aos
import peg

CARDS = 10
PRINTED = 8
COLORS = ("purple", "blue", "green", "yellow")
DEALS = 200000

# DERIVED FROM aos.LEVELS, NOT TYPED - see the note in napends.py for the
# file that typed its own copy and went two re-pegs stale.
SHIPPED = dict(aos.LEVELS)

# EASY HAS TWO CANDIDATE LEVERS AND THE SWEEP IS NOT ALLOWED TO ASSUME
# WHICH.  Routine is the easiest class, so the obvious move is more of it at
# Unstable's expense.  But SPECIALIZED IS THE NON-MONOTONIC ONE - two
# required-colour dots a card, which makes each card harder and the SETUP
# easier, because it is what satisfies the colour floor - so an S-heavy Easy
# could read easier than an R-heavy one while re-dealing half as often.  A
# 60-game smoke run put 4/4/2/0 three points above the shipped 4/3/3/0 at
# half the deal-again rate, which is inside the noise at that sample and
# exactly the reason to measure both arms properly.  The shipped mix is
# first so the column has a control in it.
EASY = [(4, 3, 3, 0),
        # the Routine arm
        (5, 3, 2, 0), (5, 2, 3, 0), (6, 3, 1, 0), (6, 2, 2, 0),
        (7, 3, 0, 0), (7, 2, 1, 0), (8, 2, 0, 0), (8, 1, 1, 0),
        # the Specialized arm
        (4, 4, 2, 0), (5, 4, 1, 0), (6, 4, 0, 0), (4, 5, 1, 0),
        (3, 5, 2, 0), (5, 5, 0, 0), (4, 6, 0, 0), (3, 6, 1, 0),
        (2, 6, 2, 0), (3, 4, 3, 0), (2, 5, 3, 0)]

# NOBULOUS WANTS MORE VOLATILE, and four is what ships.  Five was measured
# on 2026-11-26 at 26.2%; this goes to the printed ceiling of eight, which
# is the whole of the remaining room.
NOBULOUS = [(0, 3, 3, 4), (0, 4, 1, 5), (0, 3, 2, 5), (0, 2, 3, 5),
            (0, 4, 0, 6), (0, 3, 1, 6), (0, 2, 2, 6),
            (0, 3, 0, 7), (0, 2, 1, 7), (0, 1, 2, 7),
            (0, 2, 0, 8), (0, 1, 1, 8), (0, 0, 2, 8)]


def legal(mix):
    return (sum(mix) == CARDS and all(0 <= n <= PRINTED for n in mix))


def dealagain(mix, deals=DEALS, seed=20):
    """Share of FIRST deals the printed colour floor throws away.

    Replays aos.Game.__init__'s own deal (aos.py:1237-1251) rather than
    running games, because the rate is a property of the deal alone.
    """
    rng = random.Random(seed)
    bad = 0
    for _ in range(deals):
        have = dict.fromkeys(COLORS, 0)
        for name, n in zip(aos.DECKS, mix):
            for i in rng.sample(range(PRINTED), min(n, PRINTED)):
                for c in aos.program_colors(name, i):
                    have[c] += 1
        if min(have.values()) < aos.COLOR_FLOOR:
            bad += 1
    return 100.0 * bad / deals


def winrate(mix, games, tier="none"):
    """Mean of the six Technicians - the shape RESULTS.txt publishes."""
    aos.LEVELS["_probe"] = mix
    try:
        return 100 * statistics.mean(
            aos.run("_probe", games, tier=tier, tech=t) for t in aos.TECHS)
    finally:
        aos.LEVELS.pop("_probe", None)


def sweep(label, rung, mixes, games):
    want = peg.HOUSE[rung]
    print("=" * 72)
    print(label)
    print("target %.1f%%, shipped %d/%d/%d/%d"
          % ((want,) + SHIPPED[rung]))
    print("=" * 72)
    print("%-12s %8s %8s   %10s  %s"
          % ("R/S/U/V", "win", "vs target", "deal-again", ""))
    print("-" * 72)
    rows = []
    for m in mixes:
        assert legal(m), m
        w = winrate(m, games)
        d = dealagain(m)
        rows.append((m, w, d))
        tag = ("   SHIPPED %s" % rung) if m == SHIPPED[rung] else ""
        print("%-12s %7.1f%% %+8.1f   %9.1f%%%s"
              % ("%d/%d/%d/%d" % m, w, w - want, d, tag), flush=True)
    print("")
    return rows


def report(rung, rows, games):
    """Is the target reachable, and what is the NEAREST mix that reaches it?

    THE PICK IS BY DISTANCE, NOT BY DEAL-AGAIN.  The first version of this
    function chose the lowest deal-again rate among every cell that crossed
    the target, which is not a ladder question at all: at the Easy end it
    answered 8/2/0/0, fourteen points PAST the target, because a mix that is
    eight-tenths Routine satisfies the colour floor every time.  "Reaches
    the target" and "is the target" are different things and the second one
    is what a rung has to be.

    The deal-again rate is a CONSTRAINT, not the objective, so the nearest
    cell is reported and then separately the nearest cell that does not make
    setup worse than the rung already is.  A mix that lands on the win rate
    and re-deals one setup in five has not solved the rung.
    """
    want = peg.HOUSE[rung]
    ship = [r for r in rows if r[0] == SHIPPED[rung]][0]
    if rung == "Easy":
        # Easy wants the HIGHEST win rate the composition can reach.
        edge = max(rows, key=lambda r: r[1])
        reached = edge[1] >= want
        word = "ceiling"
    else:
        edge = min(rows, key=lambda r: r[1])
        reached = edge[1] <= want
        word = "floor"
    print("THE %s OVER EVERY MIX MEASURED: %d/%d/%d/%d at %.1f%%, "
          "deal-again %.1f%%."
          % ((word.upper(),) + edge[0] + (edge[1], edge[2])))
    if reached:
        near = min(rows, key=lambda r: abs(r[1] - want))
        print("THE TARGET IS REACHABLE, and the NEAREST cell is "
              "%d/%d/%d/%d at %.1f%%" % (near[0] + (near[1],)))
        print("(%+.1f), deal-again %.1f%% against the shipped rung's %.1f%% "
              "and %.1f%%."
              % (near[1] - want, near[2], ship[1], ship[2]))
        kept = [r for r in rows if r[2] <= ship[2]]
        best = min(kept, key=lambda r: abs(r[1] - want))
        if best[0] != near[0]:
            print("IT RE-DEALS MORE OFTEN THAN THE RUNG ALREADY DOES.  The "
                  "nearest cell that")
            print("does not is %d/%d/%d/%d at %.1f%% (%+.1f) and %.1f%%."
                  % (best[0] + (best[1], best[1] - want, best[2])))
        else:
            print("IT ALSO RE-DEALS NO MORE OFTEN than the rung already "
                  "does, so it costs")
            print("nothing at setup - %.1f%% against %.1f%%."
                  % (best[2], ship[2]))
        return best
    print("THE TARGET IS NOT REACHABLE BY COMPOSITION.  The %s is %.1f "
          "points %s %.1f%%,"
          % (word, abs(edge[1] - want),
             "short of" if rung == "Easy" else "above", want))
    print("and that is the whole of the printed room: no legal ten cards "
          "reach it.")
    print("Closing it needs a RULE or a harder card, which is not a dial "
          "this file has.")
    return edge


def tiers(rung, mix, games):
    print("")
    print("%s %d/%d/%d/%d ON THE CAMPAIGN AXIS, %d games a Technician:"
          % ((rung,) + mix + (games,)))
    cells = [winrate(mix, games, tier=t) for t in ("none", "I", "II", "III")]
    print("  tier none %.1f%%   I %.1f%%   II %.1f%%   III %.1f%%"
          % tuple(cells))
    if max(cells[1:]) >= cells[0]:
        print("  A TIER MAKES IT EASIER, which is the one shape a tier must "
              "not have.")
    else:
        print("  every tier is below the solo cell, which is the shape a "
              "tier must have.")
    return cells


def main():
    games = int(sys.argv[1]) if len(sys.argv) > 1 else 1500
    print("AoS'S TWO ENDS AGAINST THE PEG - %s's %s"
          % (peg.PEG_FAMILY, peg.PEG_COLUMN))
    print("%d games per Technician per cell, mean of the six, seed 20.  "
          "Deal-again is" % games)
    print("%d analytic deals a mix.  COLOR_FLOOR = %d over %d Programs."
          % (DEALS, aos.COLOR_FLOOR, CARDS))
    print("")
    print("Shipped: " + "   ".join("%s %d/%d/%d/%d" % ((n,) + SHIPPED[n])
                                   for n in ("Easy", "Standard", "Hard",
                                             "Nobulous")))
    print("Target:  " + "   ".join(
        "%s %.1f" % (n, peg.HOUSE[n])
        for n in ("Easy", "Standard", "Hard", "Nobulous")))
    print("")
    picks = {}
    for rung, mixes, label in (
            ("Easy", EASY,
             "THE EASY END - the Routine arm and the Specialized arm"),
            ("Nobulous", NOBULOUS,
             "THE NOBULOUS END - more Volatile, to the printed ceiling")):
        rows = sweep(label, rung, mixes, games)
        picks[rung] = report(rung, rows, games)
        print("")
    for rung in ("Easy", "Nobulous"):
        tiers(rung, picks[rung][0], games)
    return 0


if __name__ == "__main__":
    sys.exit(main())
