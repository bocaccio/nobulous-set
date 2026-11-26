"""What win rate does each AoS deck mix produce?

    python aosmix.py            # 900 games per Technician per mix

Difficulty in AoS is the mix of the FOUR Program decks - (Routine,
Specialized, Unstable, Volatile) - summing to the 10 Programs you cycle.
Each deck holds 8 cards, so any split of 10 with no part above 8 is legal.

BOTH NUMBERS WERE WRONG HERE UNTIL 2026-11-25. This still enumerated splits
of 8 across three decks a fortnight after the deck grew to ten and a fourth
class was printed, so every mix it offered was one the model cannot deal and
CURRENT below matched nothing - the one script whose whole job is comparing
mixes had stopped being able to name the shipped ladder at all. It is fixed
rather than retired because its question is still a good one, but the sweep
that chose the current rungs is simulation/aosvol.py, which groups the space
by Volatile count and scores each cell against both the published ladder and
BAT's peg. Prefer that one for a retune; this is the flat table.

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
    """Every legal split of 10 across the four decks, hardest-last.

    No part above 8, because 8 is what each class prints - a split that
    asks for 9 Unstable is a deal nobody can make.
    """
    out = []
    for v in range(0, 9):
        for u in range(0, 9):
            for s in range(0, 9):
                r = 10 - v - u - s
                if 0 <= r <= 8:
                    out.append((r, s, u, v))
    # Volatile is the hardest class and Unstable the next, so order by
    # those two, then Specialized. NOT A DIFFICULTY ORDER, only a reading
    # order: Specialized carries two required-colour dots where the other
    # three carry one, so it is the harder card on colour supply and the
    # easier one on Targets, and the two cross over. See the note on
    # aos.LEVELS, and aosvol.txt for where it turns round.
    return sorted(out, key=lambda m: (m[3], m[2], m[1]))


def winrate(mix, games):
    aos.LEVELS["_probe"] = mix
    try:
        return 100 * statistics.mean(
            aos.run("_probe", games, tech=t) for t in aos.TECHS)
    finally:
        del aos.LEVELS["_probe"]


def main(games=900):
    print("AoS deck mixes, mean of the six Technicians, %d games each." % games)
    print("(Routine, Specialized, Unstable, Volatile); each deck holds 8.")
    print()
    print("%-18s %8s   %s" % ("mix", "win", "currently"))
    print("-" * 46)
    for m in mixes():
        # THE SKIP IS ON THE TWO HARD CLASSES TOGETHER, not on Unstable
        # alone. It used to read "if m[2] > 6", which with Volatile in the
        # tuple would have printed every one of the hardest cells and cut
        # mild ones instead.
        if m[2] + m[3] > 8:
            continue                     # beyond anything playable
        w = winrate(m, games)
        print("%-18s %7.1f%%   %s"
              % ("%d / %d / %d / %d" % m, w, CURRENT.get(m, "")), flush=True)


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 900)
