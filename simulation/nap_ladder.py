"""NAP's difficulty surface: Credit goal against Setback count.

    python3 nap_ladder.py              # the grid, 3000 games a cell
    python3 nap_ladder.py 8000         # slower, tighter
    python3 nap_ladder.py 8000 confirm # a named ladder at every tier,
                                       #   six Apprentices

LEVELS has two dials and they have never been swept together. The Credit
goal is what rules/nap.html calls the difficulty, and the Setback count was
added as a second axis; each has only ever been moved on its own, against a
column measured with the other held still. That is how the ladder came to
invert on 2026-11-12 - Standard 3 -> 2 Setbacks is worth more than Easy's
extra Credit, so Standard overtook Easy.

TWO THINGS MAKE THIS A SURFACE AND NOT TWO LINES.

  A SETBACK IS WORTH MORE THAN A CREDIT, about 4.2-6.3 points against 4.2-5.2,
  and the gap widens in the middle of the ladder where there are enough dice
  to work a Setback but not enough to ignore one.

  AND BELOW 4 SETBACKS THE COUNT DOES NOTHING FROM TIER I UPWARD. Tier I
  swaps one base Setback out per Following Setback in, floored at none, so
  0, 1, 2 and 3 all give 3 Following and 0 base - the same deck. The Credit
  goal is the ONLY lever that moves the campaign axis on the soft half of
  the ladder, and a ladder tuned on the solo column alone will be flat at
  Tier III wherever it leans on Setbacks.

The house style to aim at is BAT's, which is the one ladder in the set that
was pegged against the 20 Strong community band deliberately: Easy 63.7,
Standard 52.8, Hard 37.8, Nobulous 25.8. Standard inside 47-57 and the hard
end outside it on purpose.
"""
import sys

sys.path.insert(0, '.')
import nap  # noqa: E402

GOALS = (4, 5, 6, 7, 8)
SETBACKS = (0, 1, 2, 3, 4, 5)
TARGET = {"Easy": 63.0, "Standard": 53.0, "Hard": 38.0, "Nobulous": 26.0}


def cell(goal, sb, tier="none", apprentice="Prodigy", games=3000):
    nap.CREDITS_TO_LEAVE, nap.SETBACKS_IN_DECK = goal, sb
    return 100.0 * nap.run(apprentice=apprentice, games=games, seed=20,
                           tier=tier)


def grid(games):
    print("SOLO, Prodigy, FINF -1, %d games a cell" % games)
    print("%-6s" % "goal" + "".join("%9s" % ("%d sb" % s) for s in SETBACKS))
    table = {}
    for g in GOALS:
        row = []
        for s in SETBACKS:
            v = cell(g, s, games=games)
            table[(g, s)] = v
            row.append("%8.1f%%" % v)
        print("%-6d" % g + "".join(row))
    print()
    print("TIER III, same cells - note the soft half is flat across "
          "0-3 Setbacks")
    print("%-6s" % "goal" + "".join("%9s" % ("%d sb" % s) for s in SETBACKS))
    for g in GOALS:
        row = []
        for s in SETBACKS:
            row.append("%8.1f%%" % cell(g, s, tier="III", games=games))
        print("%-6d" % g + "".join(row))
    print()
    print("NEAREST CELL TO THE HOUSE STYLE (BAT's pegged ladder)")
    for name in ("Easy", "Standard", "Hard", "Nobulous"):
        want = TARGET[name]
        best = sorted(table.items(), key=lambda kv: abs(kv[1] - want))[:3]
        print("  %-9s want %4.1f%%  ->  %s"
              % (name, want,
                 "   ".join("%d Cr / %d sb %5.1f%%" % (g, s, v)
                            for (g, s), v in best)))
    return table


def confirm(ladder, games):
    """A named ladder at every tier, six Apprentices averaged."""
    print()
    print("THE PROPOSED LADDER, %d games a cell, six Apprentices averaged"
          % games)
    print("%-10s %-9s" % ("level", "goal/sb")
          + "".join("%10s" % ("tier " + t) for t in ("0", "I", "II", "III")))
    for name, (g, s) in ladder:
        cells = []
        for tier in ("none", "I", "II", "III"):
            vals = [cell(g, s, tier=tier, apprentice=a, games=games)
                    for a in nap.APPRENTICES]
            cells.append(sum(vals) / len(vals))
        print("%-10s %-9s" % (name, "%d / %d" % (g, s))
              + "".join("%9.1f%%" % v for v in cells))


if __name__ == "__main__":
    _games = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
    _t = grid(_games)
