# -*- coding: utf-8 -*-
"""THE ONE OWNER of the difficulty target the three games are tuned against.

    python peg.py        # the target, every family against it, provenance

WHY THIS FILE EXISTS. From 2026-11-12 to 2026-11-26 the target was the four
numbers 63.7 / 52.8 / 37.8 / 25.8, typed by hand into eight files and
described in most of them as "the pegged ladder in rules/bat.html, the one
ladder in the set aimed at the community band on purpose". THREE SEPARATE
THINGS ABOUT THAT SENTENCE WERE FALSE AT THE SAME TIME.

  rules/bat.html PRINTS NO PERCENTAGE AT ALL. Not that one, not any: the
  file contains zero "%" characters and always has. Four files cited a
  rulebook for a figure no rulebook has ever carried.

  NO BAT RUN EVER PRODUCED THOSE FOUR NUMBERS TOGETHER. It is a composite
  of four cells from four configurations, assembled by hand:

    Easy      63.7  supply.txt's BANKING table, whose Standard reads 56.1
    Standard  52.8  batrev_batch.txt, GRAFT_REVEAL 2, DECKS 12/13/14/15
    Hard      37.8  batrev.py's lab-quality table, and its attrition run
    Nobulous  25.8  the HP sweep's deck-15 / HP-9 cell, which batrev.py's
                    own docstring warns to "read as DECK SIZE ONLY"

  CARD_MANIFEST.txt attributed the same four numbers to a THIRD scheme
  again - "Easy 5/9, Standard 6/10, Hard 7/12, Nobulous 8/14... at 3000
  games" - so the composite had been carried across at least three
  difficulty schemes without being re-measured once.

  AND IT WAS THE WRONG COLUMN. On 2026-11-20 BAT adopted the
  scavenged-Tyrant design and its BRIEF changed with it. HANDOFF.md says so
  in as many words: "Standard's great third, 46.5%, is the figure the
  design is pegged to... Do not read the overall column against the old
  band: that band was set for an overall win rate and this ladder is not
  one." BAT is judged on its games split into thirds by the Prototyrant's
  total graft Value at Wake-Up, because a GREAT lab should still be a fight
  and a POOR one close to hopeless. Its OVERALL column is about 23% at
  Standard, which is not a figure anything should be pegged to - and NAP
  and AoS spent six days pegged to a stale reading of exactly that column.

NOTHING CAUGHT ANY OF IT BECAUSE NOTHING WAS ASKED TO. There was no owner
and no check: eight copies of a number cannot disagree with each other.
check_app_sync.py now pins this file, and the predicate is that every
ladder's four figures must be FINDABLE IN THE OUTPUT FILE IT NAMES. A
comment cannot satisfy that and neither can a rename.

-----------------------------------------------------------------------
WHAT THE TARGET IS
-----------------------------------------------------------------------

THE ANCHOR IS THE BAND, and it is the only part that was never in doubt:
the 20 Strong community's own reported win rate, 47-57%, mean 53.0%. It is
external to this repository, so it cannot go stale when a model changes -
which is exactly the property the composite lacked.

THE LADDER IS BAT'S, re-measured 2026-11-26 on the column BAT's brief
names: the GREAT third, on the games where the old Tyrant woke NORMALLY.
Jon pegs difficulty mostly to the normal wake (2026-11-26), and the early
wake is 4-5% of games and wins almost none of them at the top two rungs.

MIND WHAT THE SAMPLES MEAN, because the two grids do not agree on it.
NAP's 20,004 is the TOTAL for a cell - napgrid.py divides it by the six
Apprentices - and AoS's 20,000 is PER TECHNICIAN, so an AoS cell is 120,000
games and a NAP cell is 20,004. Both files used to say "20,000 games a cell"
about samples six times apart.

MIND WHAT KIND OF NUMBER IT IS. BAT's great third is a CONDITIONAL win rate
- given a good lab - while NAP's and AoS's columns are unconditional. They
are not the same quantity and this file does not pretend they are. The
great third is used because it is the figure BAT's own design is pegged to
and the only BAT column with a band-sized value in it; comparing the other
two games' overall columns against it is the closest the set can get, and
the gap it reports is a guide and not an equivalence.

AND IT NEEDS THE BIG SAMPLE. A third of the games is a third of the
sample, so the great third at 20,000 games a rung is about 6,700 games a
cell. The 2,000-game pilot of the same measurement read 71.6 / 47.8 / 35.6
/ 24.1 against the 70.5 / 50.4 / 38.5 / 21.2 below - up to 3 points out.
Do not re-peg off a quick run.
"""
import io
import os
import sys

LEVELS = ("Easy", "Standard", "Hard", "Nobulous")

# THE EXTERNAL ANCHOR. Not measured here and not ours to move.
BAND = (47.0, 57.0)
BAND_MEAN = 53.0

# Which family's ladder is the target, and WHICH COLUMN OF IT - because
# getting the column wrong is the mistake this file was written to end.
PEG_FAMILY = "BAT"
PEG_COLUMN = "great third, normal wake"

# figures, the output file they must be findable in, how they were measured
LADDERS = {
    "BAT": ((70.5, 50.4, 38.5, 21.2), "simulation/batpeg.txt",
            "20,000 games a rung, seed 20, great third on the normal wake"),
    "NAP": ((64.5, 50.0, 35.4, 21.8), "simulation/napgrid.txt",
            "20,004 games a cell TOTAL - 3,334 an Apprentice - overall"),
    "AoS": ((66.4, 52.3, 38.2, 24.6), "simulation/aosgrid.txt",
            "20,000 games a TECHNICIAN a cell - six of them, so 120,000 "
            "games - overall"),
}

# BAT's OVERALL column, recorded so that the two can never be confused
# again - and asserted to differ from the pegged column, because the whole
# failure was one being read as the other.
BAT_OVERALL = (40.4, 23.3, 15.4, 7.6)

# DERIVED, NEVER TYPED. This is the structural half of the fix: there is
# nothing here for a hand to copy out of step.
HOUSE = dict(zip(LEVELS, LADDERS[PEG_FAMILY][0]))


def house_tuple():
    """The target in LEVELS order, for callers that want a row."""
    return tuple(HOUSE[lvl] for lvl in LEVELS)


def off(figures):
    """A family's ladder against the target, in LEVELS order."""
    return tuple(f - HOUSE[lvl] for f, lvl in zip(figures, LEVELS))


def ladder_steps(figures):
    """The three gaps between rungs - the SHAPE, as against the level.

    Worth printing beside the target because the two ends are chased on it.
    BAT's great third steps 20.1 / 11.9 / 17.3 where NAP steps 14.5 / 14.6 /
    9.7 and AoS 10.1 / 14.1 / 9.1: BAT's rungs are set by the ROUND LIMIT
    (12/10/9/8) and a round is not worth the same at every rung, so the
    ladder it hands the other two to copy is an irregular one. Pegging a
    LEVEL to it is a different proposition from pegging a SHAPE to it.
    """
    return tuple(a - b for a, b in zip(figures, figures[1:]))


def in_band(pct):
    """Where one win rate sits against the community band."""
    lo, hi = BAND
    if pct < lo:
        return "%.1f below" % (lo - pct)
    if pct > hi:
        return "%.1f above" % (pct - hi)
    return "in band"


def provenance():
    """Every ladder's figures must be findable in the file it names.

    This is what check_app_sync.py asserts, and it is the reason a stale
    figure cannot hide here: re-measure and the output file changes, so
    the claim fails until the claim is updated too.
    """
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    bad = []
    for name, (figs, rel, _how) in sorted(LADDERS.items()):
        path = os.path.join(root, rel.replace("/", os.sep))
        if not os.path.exists(path):
            bad.append("%s: %s is missing" % (name, rel))
            continue
        with io.open(path, encoding="utf-8", errors="replace") as f:
            src = f.read()
        missing = [("%.1f" % v) for v in figs if ("%.1f" % v) not in src]
        if missing:
            bad.append("%s: %s does not contain %s"
                       % (name, rel, ", ".join(missing)))
    return bad


def main():
    print("THE TARGET - %s's %s, owned here." % (PEG_FAMILY, PEG_COLUMN))
    print("The community band is %.0f-%.0f%%, mean %.1f%%, and it is what "
          "the target" % (BAND[0], BAND[1], BAND_MEAN))
    print("is anchored on. Standard is in it; the hard end is outside it on "
          "purpose.")
    print("")
    print("%-8s %7s %8s %7s %8s   %s"
          % ("", "Easy", "Standard", "Hard", "Nobulous", "measured in"))
    print("-" * 78)
    for name in (PEG_FAMILY,) + tuple(n for n in sorted(LADDERS)
                                      if n != PEG_FAMILY):
        figs, rel, how = LADDERS[name]
        tag = name + (" *" if name == PEG_FAMILY else "  ")
        print("%-8s %6.1f%% %7.1f%% %6.1f%% %7.1f%%   %s"
              % ((tag,) + figs + (rel,)))
        if name != PEG_FAMILY:
            print("%-8s %+6.1f  %+7.1f  %+6.1f  %+7.1f    %s"
                  % (("",) + off(figs) + (how,)))
        else:
            print("%-8s %-33s %s" % ("", "the target itself", how))
        print("%-8s steps of %4.1f / %4.1f / %4.1f"
              % (("",) + ladder_steps(figs)))
    print("")
    print("* the target. BAT's OVERALL column, which is NOT it, reads "
          "%s" % " / ".join("%.1f" % v for v in BAT_OVERALL))
    print("  - 23.7 points under the band at Standard. Read the great third "
          "against")
    print("  the band and the overall column against nothing: the band was "
          "set for")
    print("  an overall rate, but not for a game split into thirds.")
    print("")
    print("Standard against the band: " + ", ".join(
        "%s %.1f%% (%s)" % (n, LADDERS[n][0][1], in_band(LADDERS[n][0][1]))
        for n in (PEG_FAMILY,) + tuple(sorted(set(LADDERS) - {PEG_FAMILY}))))
    bad = provenance()
    print("")
    if bad:
        print("PROVENANCE BROKEN:")
        for b in bad:
            print("  " + b)
        return 1
    print("Provenance checked: every figure above was found in the file it "
          "names.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
