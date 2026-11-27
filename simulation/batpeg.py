# -*- coding: utf-8 -*-
"""THE PEG, RE-MEASURED FROM BAT AS IT SHIPS - AND ON THE RIGHT COLUMN.

TWO THINGS WERE WRONG WITH 63.7 / 52.8 / 37.8 / 25.8, not one.

IT IS A COMPOSITE, not a measurement.  No BAT output file in the repository
contains those four numbers as a row:

  Easy      63.7  supply.txt's BANKING table, whose Standard reads 56.1
  Standard  52.8  batrev_batch.txt, GRAFT_REVEAL 2, DECKS 12/13/14/15
  Hard      37.8  batrev.py's own lab-quality table, and its attrition run
  Nobulous  25.8  the HP sweep's deck-15 / HP-9 cell, which batrev.py's
                  docstring itself warns to "read as DECK SIZE ONLY"

AND IT IS THE WRONG COLUMN.  On 2026-11-20 BAT adopted the scavenged-Tyrant
design and its BRIEF changed with it: the game stopped being judged on an
overall win rate at all.  HANDOFF.md says so in as many words - "Standard's
great third, 46.5%, is the figure the design is pegged to... Do not read the
overall column against the old band: that band was set for an overall win
rate and this ladder is not one."  The figures are split into thirds by the
Prototyrant's total graft Value at Wake-Up, because a GREAT lab should still
be a fight and a POOR one close to hopeless.

So NAP and AoS have spent six days pegged to BAT's OVERALL column, measured
under a difficulty scheme BAT replaced, while BAT's own design pegs itself to
its GREAT third.  That is a category error and not a drift: the two columns
are not the same quantity, and BAT's overall column today is around 22% at
Standard - which is not a number anything should be pegged to.

THE COMPARABLE COLUMN IS THE GREAT THIRD, because it is the one BAT's brief
names and the only one with a band-sized value in it.  Both are printed here
so the choice stays visible, and both are split by which wake ended the lab:
difficulty is pegged mostly to the NORMAL wake (Jon, 2026-11-26).

Conservation is asserted on every game: starting parts = wall + grafts.
"""
import collections
import random
import sys

import batrev

G = int(sys.argv[1]) if len(sys.argv) > 1 else 3000

# Everything that would reproduce an older reading has to be ON, i.e. at its
# shipped value, or this measures a game nobody plays.  Asserted rather than
# assumed, because every one of these is a dial whose whole purpose is to be
# turned off, and the file this replaces was measured through four of them.
SHIPPED = dict(RETAIN_NO_RESHUFFLE=True, BOTTOM_ON_SUCCESS=True,
               ZERO_DICE_NO_GRAFT=True, BORROW_BANDS=True,
               CLOCK_AWARE_PASS=True, ROUND_LIMIT=0)
for k, v in sorted(SHIPPED.items()):
    got = getattr(batrev, k)
    assert got == v, "%s is %r, not the shipped %r" % (k, got, v)

print("THE PEG RE-MEASURED - %d games a rung, seed 20, batch() shape." % G)
print("batrev.py as it ships: PARTS_AT_SETUP %s, SPECIMENS_IN_POOL %s,"
      % (sorted(set(batrev.PARTS_AT_SETUP.values())),
         [batrev.SPECIMENS_IN_POOL[l] for l in batrev.LEVELS]))
print("ROUNDS %s, GRAFT_REVEAL %d, WAKEUP_PACKET %d.  Thirds are split by "
      "graft Value" % ([batrev.ROUND_LIMITS[l] for l in batrev.LEVELS],
                       batrev.GRAFT_REVEAL, batrev.WAKEUP_PACKET))
print("at Wake-Up, by batrev.thirds_of, which is how BAT's own brief reads "
      "the game.")
print("")
print("%-10s %7s %7s %7s %7s %8s %7s %6s %6s"
      % ("rung", "overall", "poor", "mid", "GREAT", "GREAT|nml", "early%",
         "rnds", "wall"))
print("-" * 76)

great, overall, great_nml = {}, {}, {}
for lvl in batrev.LEVELS:
    rng = random.Random(20)
    rows, rows_nml = [], []
    n = collections.Counter()
    bad = 0
    for _ in range(G):
        g = batrev.Game(lvl, rng)
        res = g.play()
        if sum(g.setup_mix) != g.gate["splices"] + g.gate["grafts"]:
            bad += 1
        won = res == "win"
        rows.append((g.gate["graft_value"], won))
        if not g.early_wake:
            rows_nml.append((g.gate["graft_value"], won))
        else:
            n["early"] += 1
        n["win"] += bool(won)
        n["rounds"] += g.rounds
        n["wall"] += g.gate["splices"]
    assert not bad, "%s: conservation broken in %d games" % (lvl, bad)
    poor, mid, grt = batrev.thirds_of(rows)
    grt_n = batrev.thirds_of(rows_nml)[2]
    great[lvl], overall[lvl], great_nml[lvl] = grt, 100.0 * n["win"] / G, grt_n
    print("%-10s %6.1f%% %6.1f%% %6.1f%% %6.1f%% %7.1f%% %6.1f%% %5.2f %5.2f"
          % (lvl, overall[lvl], poor, mid, grt, grt_n,
             100.0 * n["early"] / G, float(n["rounds"]) / G,
             float(n["wall"]) / G))

OLD = (63.7, 52.8, 37.8, 25.8)
print("")
print("BAT's GREAT third, normal wake: %s"
      % " / ".join("%.1f" % great_nml[l] for l in batrev.LEVELS))
print("BAT's GREAT third, all games:   %s"
      % " / ".join("%.1f" % great[l] for l in batrev.LEVELS))
print("BAT's OVERALL column:           %s"
      % " / ".join("%.1f" % overall[l] for l in batrev.LEVELS))
print("The composite this replaces:    %s"
      % " / ".join("%.1f" % v for v in OLD))
print("")
print("THE 20 STRONG COMMUNITY BAND is 47-57%, mean 53.0%, and it was set "
      "for an")
print("OVERALL win rate.  Standard reads:")
for label, col in (("great third, normal wake", great_nml),
                   ("great third, all games", great),
                   ("overall", overall)):
    v = col["Standard"]
    where = ("inside" if 47.0 <= v <= 57.0
             else "%.1f below" % (47.0 - v) if v < 47.0
             else "%.1f above" % (v - 57.0))
    print("  %-26s %5.1f%%   %s the band" % (label, v, where))
print("")
print("THE SET'S OTHER TWO LADDERS, both overall win rates at 20,000 games:")
print("  NAP  64.5 / 50.0 / 35.4 / 25.7   napgrid.txt, six Apprentices")
print("  AoS  62.4 / 52.3 / 38.2 / 29.1   RESULTS.txt, six Technicians")
