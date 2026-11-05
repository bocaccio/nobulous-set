"""What win rate does each AoS deck mix produce?

    python aosmix.py            # 900 games per Technician per mix

Difficulty in AoS is the mix of the three Program decks - (Routine,
Specialized, Unstable) - summing to the 8 Programs you cycle. Each deck
holds 8 cards, so any split of 8 is legal.

Every mix is reported as the mean of the six Technicians, the way table.py
reports the ladder, so the numbers are directly comparable to RESULTS.txt.
"""
import statistics
import sys

import aos

# ONE OWNER: the ladder is aos.LEVELS, never a copy. This dict was written by
# hand and still read Easy 5/3/0, Standard 4/3/1 after the 2026-11-03 retune
# moved every rung - so the one script whose entire job is comparing mixes was
# labelling them a rung wrong, and the 2026-11-05 re-pitch would have left it
# two rungs wrong. Derived, it cannot drift.
CURRENT = {mix: name for name, mix in aos.LEVELS.items()}


def mixes():
    """Every split of 8 across the three decks, hardest-last."""
    out = []
    for u in range(0, 9):
        for s in range(0, 9 - u):
            r = 8 - u - s
            out.append((r, s, u))
    # Unstable count dominates difficulty, then Specialized.
    return sorted(out, key=lambda m: (m[2], m[1]))


def winrate(mix, games):
    aos.LEVELS["_probe"] = mix
    try:
        return 100 * statistics.mean(
            aos.run("_probe", games, tech=t) for t in aos.TECHS)
    finally:
        del aos.LEVELS["_probe"]


def main(games=900):
    print("AoS deck mixes, mean of the six Technicians, %d games each." % games)
    print("(Routine, Specialized, Unstable); each deck holds 8 cards.")
    print()
    print("%-18s %8s   %s" % ("mix", "win", "currently"))
    print("-" * 46)
    for m in mixes():
        if m[2] > 6:
            continue                     # beyond anything playable
        w = winrate(m, games)
        print("%-18s %7.1f%%   %s"
              % ("%d / %d / %d" % m, w, CURRENT.get(m, "")), flush=True)


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 900)
