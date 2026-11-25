"""HOW BIG SHOULD THE AoS PROGRAM DECK BE?

Eight cards was the right size for the old AoS, where a Program was run and
set aside and the deck only had to outlast you. The Assembly rules ask it to
do something else: supply six to nine CLEAN runs in three rounds, in four
specific colours, out of a pool that shrinks every time one lands. Eight
cards cannot, and the two symptoms are the same shortage seen from
different ends.

  * FEASIBILITY. Eight Programs leave some colour on fewer than two cards
    a third of the time, and a colour nothing prints kills every Assembly
    that asks for it. That is the 15.2% of Standard deals with no buildable
    trio - see aosbuild.py, and the worked example in it.
  * THE DEADLINE. Three rounds of eight cards yield about three installs
    where six to nine are wanted - see aosdeadline.py.

Six Assemblies offered rather than five was a workaround for the first:
picking three of six gives twenty candidate trios against ten, so twice the
chance that one of them matches the colours the deck happens to print. It
treats the symptom. A deck that covers the colours treats the cause, and
then five offered is fine again.

DIFFICULTY STAYS IN THE COMPOSITION, which is the constraint this sweep is
written to respect: the deck size is one number for every difficulty, and
the four rungs are the Routine/Specialized/Unstable mix exactly as they
have always been. mix() below reproduces the shipped 3/3/2, 2/3/3, 1/3/4,
0/3/5 exactly at eight cards, so the ladder is being rescaled rather than
redesigned.
"""
import collections
import random
import sys

sys.path.insert(0, ".")
import aos
import aosbuild as AB

LEVELS = ("Easy", "Standard", "Hard", "Nobulous")


def mix(n):
    """The four difficulty rungs for a deck of `n` cards.

    The shipped ladder holds Specialized at three of eight and trades one
    Routine for one Unstable per rung. Both parts are kept as proportions:
    Specialized at three eighths, and Routine running from 60% of what is
    left down to none across the four rungs. At n = 8 this returns the
    printed table unchanged, which is the test that it is the same ladder.

    Each deck holds only eight cards, so Unstable is capped there and the
    remainder goes back to Routine - which is why the top rung stops being
    all-Unstable somewhere above twelve.
    """
    spec = max(1, int(round(3 * n / 8.0)))
    rest = n - spec
    out = []
    for k in range(4):
        routine = int(round(rest * (0.6 - 0.2 * k)))
        unstable = min(rest - routine, 8)
        routine = min(rest - unstable, 8)
        out.append((routine, spec, unstable))
    return out


def dead_rate(n, offer, floor, games=6000, seed=4):
    """Setups with no buildable trio, at this deck size."""
    worst = 0.0
    for level, comp in zip(LEVELS, mix(n)):
        rng = random.Random(seed)
        dead = 0
        for _ in range(games):
            progs, _ = AB.draw_deck(comp, rng, floor)
            pool = AB.RECIPES
            got = rng.sample(pool, offer)
            if not AB.buildable(got, progs, n):
                dead += 1
        worst = max(worst, 100.0 * dead / games)
    return worst


def ladder(n, games=1200, seed=9, **dials):
    old = {k: getattr(aos, k) for k in dials}
    for k, v in dials.items():
        setattr(aos, k, v)
    try:
        out, installs = [], []
        for comp in mix(n):
            rng = random.Random(seed)
            won = inst = 0
            for _ in range(games):
                g = aos.Game("Specialized", rng, "none", composition=comp)
                if g.play():
                    won += 1
                inst += g.installed
            out.append(100.0 * won / games)
            installs.append(inst / float(games))
        return out, installs
    finally:
        for k, v in old.items():
            setattr(aos, k, v)


def main():
    sizes = (8, 9, 10, 11, 12, 13, 14)
    print("AoS Program deck size - difficulty stays in the composition")
    print()
    print("the four rungs at each size (Routine / Specialized / Unstable):")
    print("%-6s %-12s %-12s %-12s %-12s" % ("deck", *LEVELS))
    for n in sizes:
        print("%-6d %s" % (n, " ".join("%-12s" % ("%d/%d/%d" % c) for c in mix(n))))

    print()
    print("setups with NO buildable trio, worst difficulty of the four.")
    print("SIX OFFERED is settled; five is kept here only to show what the")
    print("deck size alone is worth, and whether the colour-floor setup")
    print("rule can be dropped once the deck covers its own colours.")
    print("%-6s %10s %10s %10s %10s"
          % ("deck", "5, no chk", "5 + floor", "6, no chk", "6 + floor"))
    for n in sizes:
        print("%-6d %9.2f%% %9.2f%% %9.2f%% %9.2f%%"
              % (n, dead_rate(n, 5, 0), dead_rate(n, 5, 2),
                 dead_rate(n, 6, 0), dead_rate(n, 6, 2)))

    for req in ("clean", "nocat"):
        print()
        what = ("installing needs a CLEAN run (no failed element)"
                if req == "clean"
                else "installing needs NO CATASTROPHIC FAILURE (<=1 failed)")
        print("win rate - %s" % what)
        print("%-6s %8s %8s %8s %8s   %s"
              % ("deck", *LEVELS, "installs/game at Standard"))
        for n in sizes:
            row, inst = ladder(n, **{"INSTALL_REQUIRES": req})
            print("%-6d %s   %.2f"
                  % (n, " ".join("%7.1f%%" % x for x in row), inst[1]))

    print()
    print("For reference, the AoS this replaces measured 60.6 / 52.0 / 43.6 /")
    print("35.6, and the rest of the set sits near 50% at Standard.")


if __name__ == "__main__":
    main()
