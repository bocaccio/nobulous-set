# -*- coding: utf-8 -*-
"""WHAT IT WOULD COST TO PUT NAP'S TWO ENDS ON THE PEG.

    python napends.py            # the surface, 3000 games a cell
    python napends.py 6000       # slower, tighter

Re-pegging on 2026-11-26 (simulation/peg.py) found the middle of NAP's
ladder landing and the two ends out, in the opposite directions from what
the retired composite peg had said:

    rung       shipped   target   off
    Easy         64.5     70.5   -6.0     six points TOO HARD
    Standard     50.0     50.4   -0.4     lands
    Hard         35.4     38.5   -3.1     close
    Nobulous     25.7     21.2   +4.5     four and a half TOO EASY

This sizes the two ends and nothing else.  Standard and Hard are not
candidates here: they land, and the lesson of 2026-11-12 is that moving one
rung on its own is what inverts a ladder.

WHAT SHIPPED, 2026-11-27: BOTH ENDS, AND THE CREDIT GOAL AT EACH.  Nobulous
went to 7 Credits and 5 Setbacks and Easy to 2 and 2, in two runs an hour
apart; the table above is the ladder as it stood when this file was written.
On the published sample they read 21.8% (+0.6) and 72.5% (+2.0), and
simulation/napgrid.txt is the run.  THE 3,000-GAME ROWS WERE RIGHT TO A
TENTH AT BOTH ENDS - this file read 21.7 and 72.5 - because its candidate
ladders are the mean of six Apprentices at 3,000 games each, 18,000 a cell,
against a published 20,004.  The SURFACE below is Prodigy alone and is not
that; do not quote a surface cell as a figure.
  THE CREDIT WON AT BOTH ENDS AND THE SETBACK AT NEITHER, which this file
sized but could not decide.  At Nobulous 6/6 was +0.8 against 7/5's +0.6 and
would have spent the last printed Setback.  At Easy, 3/1 was NEARER the
target - -1.7 against 2/2's +2.0 - and lost anyway, because Tier I swaps one
base Setback out per Following card in and floors at none: 3/1's campaign
columns are byte for byte the old rung's, so it buys SOLO Easy alone and
takes Tier I's bite at Easy from 5.7 points to 9.9.  2/2 reaches the
campaign because nothing swaps a Credit goal - Easy's three NRJ cells came
up +10.4 / +12.5 / +12.5 and the bite fell to 3.3.
  SO THE LESSON OF THIS FILE IS NOT ITS "off" COLUMN.  On the soft half the
Setback count does nothing from Tier I upward, so a cell that is nearer the
target can still be the worse rung.  Read the campaign columns beside it.

TWO HARD LIMITS, both printed, and they bound the whole question:

  SIX SETBACK CARDS EXIST.  build_nap.py's SETBACKS has six entries, so
  SETBACKS_IN_DECK cannot exceed 6 - and Nobulous already runs 5.  There is
  exactly ONE Setback left in the game to spend on the hard end.

  EVERY RUNG MUST CARRY AT LEAST ONE.  That is what the 2026-11-25 step
  bought and it is not a preference: Tier I swaps one base Setback out per
  Following Setback in, floored at none, so a rung with none simply GAINS
  three cards - it cost Easy 21 points and Nobulous 2 when Easy had nothing
  to swap.  Easy is at 2, so there is exactly ONE Setback to spend on the
  soft end too.

So each end has two single steps available and they are the whole menu:
one Setback, or one Credit.

THE SURFACE IS PRODIGY, THE CANDIDATES ARE ALL SIX.  A one-Apprentice
surface is a hundred times cheaper and Prodigy tracks the mean closely at
Standard (50.1 against 50.0 on the 20,004-game run), but the published
ladder is the mean of six and a candidate has to be confirmed on it.
Prodigy reads about a point high at the soft end, which is reported.
"""
import collections
import statistics
import sys

import nap
import peg

GOALS = (1, 2, 3, 4, 5, 6, 7, 8)
SETBACKS = (0, 1, 2, 3, 4, 5, 6)
PRINTED_SETBACKS = 6      # build_nap.py's SETBACKS, and the check pins it
MIN_SETBACKS = 1          # Tier I has to have one to swap out
# DERIVED FROM nap.LEVELS, NOT TYPED.  nap_ladder.py typed its own copy of
# the shipped ladder and was two re-pegs stale - 4/1, 5/2, 6/3, 7/4 - so
# `nap_ladder.py confirm` had been confirming a ladder that has not shipped
# since 2026-11-25, with nothing to say so.  Same failure as the peg, one
# file over.
SHIPPED = dict(nap.LEVELS)
ENDS = ("Easy", "Nobulous")


def cell(goal, sb, tier="none", apprentice="Prodigy", games=3000):
    """One cell, with the dials put back - this module is imported."""
    old = nap.CREDITS_TO_LEAVE, nap.SETBACKS_IN_DECK
    nap.CREDITS_TO_LEAVE, nap.SETBACKS_IN_DECK = goal, sb
    try:
        return 100.0 * nap.run(apprentice=apprentice, games=games, seed=20,
                               tier=tier)
    finally:
        nap.CREDITS_TO_LEAVE, nap.SETBACKS_IN_DECK = old


def mean_cell(goal, sb, tier="none", games=3000):
    """The published shape: the mean of the six Apprentices."""
    return statistics.mean(cell(goal, sb, tier=tier, apprentice=a,
                                games=games)
                           for a in nap.APPRENTICES)


def surface(games):
    print("THE SURFACE, Prodigy, %d games a cell. '-' is illegal: more "
          "Setbacks than" % games)
    print("the six printed, or none at all for Tier I to swap out.")
    print("%-6s" % "goal" + "".join("%9s" % ("%d sb" % s) for s in SETBACKS))
    table = {}
    for g in GOALS:
        row = []
        for s in SETBACKS:
            if s < MIN_SETBACKS or s > PRINTED_SETBACKS:
                row.append("%9s" % "-")
                continue
            v = cell(g, s, games=games)
            table[(g, s)] = v
            here = [n for n, gs in SHIPPED.items() if gs == (g, s)]
            row.append("%8.1f%s" % (v, here[0][0] if here else " "))
        print("%-6d" % g + "".join(row), flush=True)
    print("")
    print("The letter beside a cell is the rung that ships it.")
    return table


def steps(table, games):
    """The single steps available from each end, and what each one buys."""
    print("")
    print("=" * 72)
    print("THE SINGLE STEPS FROM EACH END - one Setback, or one Credit")
    print("=" * 72)
    print("%-10s %-10s %8s %8s %8s   %s"
          % ("rung", "goal/sb", "Prodigy", "six", "target", "off"))
    print("-" * 72)
    out = {}
    for rung in ENDS:
        g, s = SHIPPED[rung]
        want = peg.HOUSE[rung]
        # The direction that helps: Easy wants EASIER, Nobulous HARDER.
        cands = [(g, s)]
        if rung == "Easy":
            cands += [(g, s - 1), (g - 1, s), (g - 1, s - 1)]
        else:
            cands += [(g, s + 1), (g + 1, s), (g + 1, s + 1)]
        for cg, cs in cands:
            if cs < MIN_SETBACKS or cs > PRINTED_SETBACKS or cg < 1:
                continue
            p = table.get((cg, cs))
            if p is None:
                p = cell(cg, cs, games=games)
            m = mean_cell(cg, cs, games=games)
            out[(rung, cg, cs)] = m
            tag = "   SHIPPED" if (cg, cs) == (g, s) else ""
            print("%-10s %-10s %7.1f%% %7.1f%% %7.1f%%   %+5.1f%s"
                  % (rung, "%d / %d" % (cg, cs), p, m, want, m - want, tag),
                  flush=True)
        print("")
    return out


def confirm(ladder, games):
    """A whole ladder at every tier, six Apprentices - the published shape."""
    print("%-10s %-9s" % ("level", "goal/sb")
          + "".join("%10s" % ("tier " + t) for t in ("0", "I", "II", "III")))
    rows = {}
    for name, (g, s) in ladder:
        cells = [mean_cell(g, s, tier=t, games=games)
                 for t in ("none", "I", "II", "III")]
        rows[name] = cells
        print("%-10s %-9s" % (name, "%d / %d" % (g, s))
              + "".join("%9.1f%%" % v for v in cells), flush=True)
    return rows


def verdict(rows, label):
    """The three shapes a NAP ladder must have, checked rather than eyeballed."""
    names = ["Easy", "Standard", "Hard", "Nobulous"]
    solo = [rows[n][0] for n in names]
    bad = []
    if any(a <= b for a, b in zip(solo, solo[1:])):
        bad.append("the solo ladder is not monotone: %s"
                   % " > ".join("%.1f" % v for v in solo))
    for n in names:
        if rows[n][3] >= rows[n][0]:
            bad.append("%s Tier III (%.1f) is not below its solo cell (%.1f)"
                       % (n, rows[n][3], rows[n][0]))
    off = [rows[n][0] - peg.HOUSE[n] for n in names]
    print("")
    print("%-22s %s" % (label, "  ".join("%+5.1f" % v for v in off))
          + "   against the target")
    print("%-22s %s" % ("", "  ".join("%5.1f" % v for v in
                                      [solo[i] - solo[i + 1]
                                       for i in range(3)] + [0.0]))
          + "   the three ladder steps")
    lo, hi = peg.BAND
    print("%-22s Standard %.1f%% (%s)"
          % ("", solo[1], peg.in_band(solo[1])))
    if bad:
        print("  SHAPE BROKEN:")
        for b in bad:
            print("    - " + b)
    else:
        print("  shape holds: monotone, and Tier III below solo at every rung.")
    return not bad


def main():
    games = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
    print("NAP'S TWO ENDS AGAINST THE PEG - %s, %s" % (peg.PEG_FAMILY,
                                                       peg.PEG_COLUMN))
    print("Target %s.  Shipped %s."
          % (" / ".join("%.1f" % peg.HOUSE[n]
                        for n in ("Easy", "Standard", "Hard", "Nobulous")),
             " / ".join("%d/%d" % SHIPPED[n]
                        for n in ("Easy", "Standard", "Hard", "Nobulous"))))
    print("")
    table = surface(games)
    found = steps(table, games)

    print("=" * 72)
    print("THE LADDERS, %d games a cell, six Apprentices averaged" % games)
    print("=" * 72)
    print("")
    print("AS IT SHIPS")
    base = confirm([(n, SHIPPED[n]) for n in
                    ("Easy", "Standard", "Hard", "Nobulous")], games)
    verdict(base, "shipped")

    # The two candidate ladders: spend the Setback at each end, or the Credit.
    for label, easy, nob in (
            ("BOTH SETBACKS", (3, 1), (6, 6)),
            ("BOTH CREDITS", (2, 2), (7, 5)),
            ("SETBACK AT EASY, CREDIT AT NOBULOUS", (3, 1), (7, 5)),
            ("CREDIT AT EASY, SETBACK AT NOBULOUS", (2, 2), (6, 6))):
        print("")
        print(label)
        rows = confirm([("Easy", easy), ("Standard", SHIPPED["Standard"]),
                        ("Hard", SHIPPED["Hard"]), ("Nobulous", nob)], games)
        verdict(rows, label.lower())
    return 0


if __name__ == "__main__":
    sys.exit(main())
