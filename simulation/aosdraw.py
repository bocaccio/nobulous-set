# -*- coding: utf-8 -*-
"""Two proposed changes to how the next AoS Program is chosen.

Both are about INFORMATION. A Program deck face down on the table
leaks its top card, and its LAST card is known by elimination, so a
player who wants to can plan the cycle's end from its beginning.

  1. "At the start of the turn, shuffle the Program deck and select a
     random Program."                                     DRAW_RANDOM

  2. "Do not complete the last Program in the deck. If there is only
     one Program left in the deck at the start of the turn, shuffle
     the discard pile to create a new deck and proceed to the next
     cycle or the Advanced Programming phase."            KEEP_LAST

The first cannot change the odds and the point of measuring it is to
SHOW that, not to assert it: consuming a uniformly random permutation
in order is the same experiment as drawing a uniform card from what is
left each turn, and the player in aos.py never reads the queue, so
there is no lookahead to take away either. If this column moves by
more than its own noise, something in the model is reading the order.

The second really does change the game - about one Program a cycle
that you never face - and a Program is both a risk and a reward, so
the direction is the question.

Figures are win rate over SEEDS independent runs of GAMES each; the
+/- is the standard error across those runs, so a difference smaller
than about two of them is noise.
"""
import sys
import math
import random

import aos

GAMES = 6000
SEEDS = 5
LEVELS = ["Easy", "Standard", "Hard", "Nobulous"]
VARIANTS = [("printed", False, False),
            ("random draw", True, False),
            ("keep last", False, True),
            ("both", True, True)]


def measure(level, tier, draw_random, keep_last, games=GAMES, seeds=SEEDS):
    """Win rate, and what the deck actually put in front of the player."""
    aos.DRAW_RANDOM, aos.KEEP_LAST = draw_random, keep_last
    rates, faced, adv = [], [], []
    comp = aos.LEVELS.get(level)
    source = level if comp is None else "Specialized"
    for s in range(seeds):
        rng = random.Random(20 + s)
        wins = runs = reached = 0
        for _ in range(games):
            g = aos.Game(source, rng, tier, composition=comp)
            won = g.play()
            wins += 1 if won else 0
            runs += g.ran
            reached += 1 if g.advanced_done else 0
        rates.append(wins / float(games))
        faced.append(runs / float(games))
        adv.append(reached / float(games))
    aos.DRAW_RANDOM = aos.KEEP_LAST = False
    return (mean(rates), stderr(rates), mean(faced), mean(adv))


def mean(xs):
    return sum(xs) / float(len(xs))


def stderr(xs):
    m = mean(xs)
    if len(xs) < 2:
        return 0.0
    v = sum((x - m) ** 2 for x in xs) / float(len(xs) - 1)
    return math.sqrt(v / len(xs))


def table(tier, levels=LEVELS):
    print("\nTier %s -- win rate, Programs faced, and how often Advanced"
          " Programming is reached" % tier)
    print("%-10s %-14s %16s %9s %9s" %
          ("level", "variant", "win rate", "faced", "reached"))
    for level in levels:
        base = None
        for name, dr, kl in VARIANTS:
            w, e, f, a = measure(level, tier, dr, kl)
            delta = "" if base is None else "  %+5.1f" % (100 * (w - base))
            if base is None:
                base = w
            print("%-10s %-14s %7.1f%% +/-%4.1f%-6s %9.2f %8.1f%%"
                  % (level, name, 100 * w, 100 * e, delta, f, 100 * a))


if __name__ == "__main__":
    tiers = sys.argv[1:] or ["none", "III"]
    print(__doc__)
    print("%d games x %d seeds per cell" % (GAMES, SEEDS))
    for t in tiers:
        table(t)
