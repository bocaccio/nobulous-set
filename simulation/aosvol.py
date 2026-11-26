"""What AoS ladder is reachable with Volatile at TWO rungs and Specialized free?

    python aosvol.py            # 1200 games per Technician per mix
    python aosvol.py 20000      # the published cell size, four rungs only

THE CONSTRAINT BEING RELEASED. The shipped ladder holds Specialized at 3 on
every rung and moves one card at a time from Routine to Unstable:

    Easy 4/3/3/0   Standard 2/3/5/0   Hard 0/3/7/0   Nobulous 0/3/5/2

so Volatile exists at one rung only, two cards of it, and the pin on
Specialized is why: with S fixed and R already at 0 by Hard, the only cards
Nobulous had left to spend were Unstable ones, and Unstable is capped at the
8 that are printed. Volatile was dealt at Nobulous alone because that was
the only rung with room for it, not because the class is a Nobulous idea.

Jon asked for 1 or 2 Volatile at Hard and 3 or 4 at Nobulous, with
Specialized free to move. That is a bigger space than the shipped ladder
could see: Specialized is the EASIER card - aosclass.txt measures 0/4/6 at
43.4% against 0/3/7 at 41.4%, so each Specialized traded for an Unstable is
worth about +1 - which means a rung can afford Volatile by paying for it in
Specialized rather than only by running out of cards.

WHAT THIS MEASURES, and what it does not. Composition only. Every card, every
printed Target and every rule stays exactly as it is; the only thing that
moves is how many of each class the ten-card deck is dealt from. Each class
has 8 printed cards, so no count above 8 is legal.

TWO TARGETS, because they are different questions and the answer differs:

  THE PUBLISHED LADDER, 62.4 / 52.5 / 44.7 / 36.6 (RESULTS.txt, 2026-11-25,
  20,000 games a cell). Holding this means Volatile reaches Hard without the
  rung getting harder, which it pays for in Specialized. A pure restructure.

  THE PEG, 63.7 / 52.8 / 37.8 / 25.8 - BAT's ladder, which rules/bat.html
  prints and which NAP was re-pegged to on 2026-11-25 (64.5 / 50.0 / 35.4 /
  25.7). AoS is the outlier of the three: Hard is 6.9 points easier than the
  peg and Nobulous 10.8. Hitting this is a re-pitch, not a restructure, and
  it is a design decision rather than a measurement.

Both are reported for every cell so the choice can be made on the numbers.
"""
import statistics
import sys

import aos

# ONE OWNER for the shipped ladder, the same reason aosmix.py derives it: a
# hand-copied mix labelled two rungs wrong for a fortnight after the
# 2026-11-05 re-pitch, and that script's whole job was comparing mixes.
CURRENT = {mix: name for name, mix in aos.LEVELS.items()}
NAMES = aos.LEVEL_NAMES

# RESULTS.txt, 2026-11-25, 20,000 games a cell, mean of the six Technicians.
PUBLISHED = {"Easy": 62.4, "Standard": 52.5, "Hard": 44.7, "Nobulous": 36.6}
# rules/bat.html's ladder, which NAP was re-pegged to the same day.
PEG = {"Easy": 63.7, "Standard": 52.8, "Hard": 37.8, "Nobulous": 25.8}

CARDS = 10          # the Program deck, since aosdeck.py chose ten
PRINTED = 8         # cards printed per class, so no count may exceed it


def candidates():
    """The mixes worth measuring, grouped by which rung they could serve.

    Routine is the easiest class, so a bottom rung carrying much of it is not
    a bottom rung; the Routine ceiling per group is what keeps this at about
    a hundred cells rather than the 286 splits of ten.
    """
    groups = [
        # (label, Volatile count, Routine ceiling)
        ("V0  Easy / Standard", 0, 5),
        ("V1  Hard", 1, 3),
        ("V2  Hard", 2, 3),
        ("V3  Nobulous", 3, 2),
        ("V4  Nobulous", 4, 2),
    ]
    out = []
    for label, v, rmax in groups:
        cells = []
        for r in range(0, rmax + 1):
            for s in range(0, PRINTED + 1):
                u = CARDS - v - r - s
                if 0 <= u <= PRINTED:
                    cells.append((r, s, u, v))
        out.append((label, sorted(cells, key=lambda m: (-m[0], -m[1]))))
    return out


def winrate(mix, games):
    """Mean of the six Technicians, the shape table.py and RESULTS.txt use."""
    aos.LEVELS["_probe"] = mix
    try:
        return 100 * statistics.mean(
            aos.run("_probe", games, tech=t) for t in aos.TECHS)
    finally:
        del aos.LEVELS["_probe"]


def sweep(games):
    print("AoS deck mixes with Specialized FREE and Volatile at two rungs.")
    print("%d games per Technician per cell, mean of the six, seed 20." % games)
    print("Ten cards dealt from four classes of 8 printed each.")
    print()
    print("Shipped ladder: " + "   ".join(
        "%s %d/%d/%d/%d" % ((n,) + aos.LEVELS[n]) for n in NAMES))
    print("Published      " + "  ".join("%s %.1f" % (n, PUBLISHED[n])
                                        for n in NAMES))
    print("Peg (BAT)      " + "  ".join("%s %.1f" % (n, PEG[n])
                                        for n in NAMES))
    print()
    best = {}
    for label, cells in candidates():
        print("=" * 62)
        print(label)
        print("%-14s %8s  %8s  %8s   %s"
              % ("R/S/U/V", "win", "vs pub", "vs peg", "shipped"))
        print("-" * 62)
        for m in cells:
            w = winrate(m, games)
            # Score each cell against whichever rung its Volatile count is
            # for, so the two columns mean something per group rather than
            # against a ladder position this cell could not take.
            rungs = {0: ("Easy", "Standard"), 1: ("Hard",), 2: ("Hard",),
                     3: ("Nobulous",), 4: ("Nobulous",)}[m[3]]
            pub = min((abs(w - PUBLISHED[r]), r) for r in rungs)
            peg = min((abs(w - PEG[r]), r) for r in rungs)
            print("%-14s %7.1f%%  %+7.1f  %+7.1f   %s"
                  % ("%d/%d/%d/%d" % m, w, w - PUBLISHED[pub[1]],
                     w - PEG[peg[1]], CURRENT.get(m, "")), flush=True)
            for r in rungs:
                for tag, want in (("pub", PUBLISHED), ("peg", PEG)):
                    k = (tag, r)
                    d = abs(w - want[r])
                    if k not in best or d < best[k][0]:
                        best[k] = (d, m, w)
        print()
    print("=" * 62)
    print("CLOSEST CELL PER RUNG, both targets")
    print("-" * 62)
    for tag, want in (("pub", PUBLISHED), ("peg", PEG)):
        print(" against the %s ladder:" % ("published" if tag == "pub"
                                           else "peg"))
        for r in NAMES:
            if (tag, r) in best:
                d, m, w = best[(tag, r)]
                print("   %-10s %-10s %6.1f%%  want %.1f  off %+.1f"
                      % (r, "%d/%d/%d/%d" % m, w, want[r], w - want[r]))
        print()


def confirm(games):
    """The four shipped rungs at the published cell size, as a control."""
    print("CONTROL: the shipped ladder at %d games per Technician." % games)
    for n in NAMES:
        w = winrate(aos.LEVELS[n], games)
        print("  %-10s %-10s %6.1f%%  published %.1f  off %+.1f"
              % (n, "%d/%d/%d/%d" % aos.LEVELS[n], w, PUBLISHED[n],
                 w - PUBLISHED[n]), flush=True)


# THE SHORTLIST THE SWEEP PRODUCED, at 1200 games a cell, re-measured at the
# published size because 1200 carries about a point either way - the control
# above read the four shipped rungs 0.1 to 0.9 LOW at that size, all four in
# the same direction, so the sweep's own figures are not safe to publish.
#
# Each entry is (rung it would serve, mix, why it is on the list).
FINALS = [
    ("Easy", (4, 3, 3, 0), "shipped, unchanged - the control"),
    ("Easy", (4, 4, 2, 0), "closest to the peg, one Unstable traded for a "
                           "Specialized"),
    ("Standard", (2, 3, 5, 0), "shipped, and already on the peg - no "
                               "candidate beat it"),
    ("Hard", (0, 4, 4, 2), "the peg ladder: Volatile 2, paid for in Unstable"),
    ("Hard", (2, 3, 3, 2), "the published ladder: Volatile 2, paid for in "
                           "Routine"),
    ("Nobulous", (0, 2, 4, 4), "the peg ladder, Specialized 2 so the mod can "
                               "still deal it"),
    ("Nobulous", (0, 3, 3, 4), "the same one Specialized milder"),
    ("Nobulous", (0, 1, 5, 4), "the sweep's floor, and Specialized 1 - see "
                               "tts/lua.lua"),
    ("Nobulous", (2, 2, 2, 4), "the published ladder: Volatile 4, paid for in "
                               "Routine"),
]


def finals(games):
    print("THE SHORTLIST at %d games per Technician, mean of the six." % games)
    print("Published  " + "  ".join("%s %.1f" % (n, PUBLISHED[n])
                                    for n in NAMES))
    print("Peg (BAT)  " + "  ".join("%s %.1f" % (n, PEG[n]) for n in NAMES))
    print()
    print("%-10s %-10s %8s %8s %8s   %s"
          % ("rung", "R/S/U/V", "win", "vs pub", "vs peg", "why"))
    print("-" * 96)
    for rung, mix, why in FINALS:
        w = winrate(mix, games)
        print("%-10s %-10s %7.1f%% %+8.1f %+8.1f   %s"
              % (rung, "%d/%d/%d/%d" % mix, w, w - PUBLISHED[rung],
                 w - PEG[rung], why), flush=True)


if __name__ == "__main__":
    g = int(sys.argv[1]) if len(sys.argv) > 1 else 1200
    if "--control" in sys.argv:
        confirm(g)
    elif "--finals" in sys.argv:
        finals(g)
    else:
        sweep(g)
