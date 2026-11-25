"""SHOULD AoS PRINT A FOURTH PROGRAM CLASS? Measured 2026-11-25.

aosdeck.py settled the deck SIZE at ten cards and left one thing unresolved:
the bottom rung. Ten cards reads 60.8 / 52.9 / 44.9 / 42.2 against the AoS
this replaces at 59.1 / 50.7 / 42.5 / 34.9, so Nobulous lands about six
points too easy and nothing in the composition can pull it down. This file
is the measurement of why, and of what the smallest fix costs.

THE COMPOSITION LEVER DID NOT JUST RUN OUT - IT LOST RANGE. The old AoS
spanned 24.2 points from the same Routine/Specialized/Unstable mix. Under
the Assembly rules ten cards span 18.6. What binds now is the three-round
deadline, and the deadline counts how many Programs you get THROUGH, which
the deck size sets, rather than how hard each one is, which the mix sets.
So the mix has less to push against than it did, and the bottom rung is
where the shortfall shows.

AND EIGHT CARDS IS NOT THE WAY BACK. Eight reads 48.1 / 40.8 / 36.8 / 34.1:
the bottom rung is right and Standard is six points below the set's 47-57%
band. There is no deck size that puts both in band, which is the finding
that makes a new card worth pricing at all.

WHAT A NEW CLASS MUST NOT DO is move the other three rungs. That rules out
raising Unstable's own Targets, the obvious cheap fix: Unstable deals at
every rung, so hardening it lowers all four. A class that deals ONLY at
Nobulous moves only Nobulous, which is the shape wanted and the reason this
is a new card rather than an edit to an old one.

Run under INSTALL_REQUIRES = "nocat" throughout. Under "clean" no deck size
and no card class reaches a playable game - see aosdeck.py - so every figure
here is conditional on that reading, which was still open when this was
written.
"""
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import aos

aos.INSTALL_REQUIRES = "nocat"
aos.OFFER_SIZE = 6
aos.COLOR_FLOOR = 2

COLORS = ("purple", "blue", "green", "yellow")
LEVELS = ("Easy", "Standard", "Hard", "Nobulous")
# The AoS this replaces, 20,000 games a cell, RESULTS.txt of 2026-11-12.
WANT = (59.1, 50.7, 42.5, 34.9)
NEW = "Degraded"


def bump(front, k):
    """The Overheated back: one element's Target raised, as every deck prints."""
    back = list(front)
    back[k % len(front)] = min(4, back[k % len(front)] + 1)
    return back


def install(front, dots):
    """Register a candidate fourth class of 8 cards with this profile.

    Eight cards, because that is what the other three classes print and
    what Game.__init__ samples from. A class that printed fewer would be
    dealt with less variety and would need re-measuring - see the note on
    the decomposition below, which is where the deal size shows up.
    """
    n = len(front)
    aos.ELEMENT_COUNTS[NEW] = [n] * 8
    aos.PROGRAM_TARGETS[NEW] = {
        "front": [list(front) for _ in range(8)],
        "back": [bump(front, i) for i in range(8)],
    }
    reqs = []
    for i in range(8):
        row = [None] * n
        for d in range(dots):
            row[(i + d * 2) % n] = COLORS[(i + d) % 4]
        reqs.append(row)
    aos.PROGRAM_REQS[NEW] = reqs
    aos.PROGRAM_REWARDS[NEW] = list(aos.PROGRAM_REWARDS["Unstable"])
    if NEW not in aos.DECKS:
        aos.DECKS.append(NEW)


def clone_unstable():
    """A fourth class that IS Unstable, card for card.

    Not a null case: a Nobulous deck of 5 Unstable + 2 of these deals
    5-of-8 from the Unstable deck where 0/3/7 deals 7-of-8, so it stops
    being nearly certain to include any particular Unstable card and its
    Reward. That is a real consequence of splitting the hard cards across
    two decks, and it has to be separated from what the new Targets do, or
    the new card gets credit for it.
    """
    aos.ELEMENT_COUNTS[NEW] = list(aos.ELEMENT_COUNTS["Unstable"])
    aos.PROGRAM_REWARDS[NEW] = list(aos.PROGRAM_REWARDS["Unstable"])
    aos.PROGRAM_TARGETS[NEW] = {
        k: [list(r) for r in v]
        for k, v in aos.PROGRAM_TARGETS["Unstable"].items()}
    aos.PROGRAM_REQS[NEW] = [list(r) for r in aos.PROGRAM_REQS["Unstable"]]
    if NEW not in aos.DECKS:
        aos.DECKS.append(NEW)


def win(comp, games=6000, seed=9):
    rng = random.Random(seed)
    won = 0
    for _ in range(games):
        if aos.Game("Specialized", rng, "none", composition=comp).play():
            won += 1
    return 100.0 * won / games


# Candidates, mildest first. Unstable prints 4 elements with two 3s and one
# colour dot, so each of these is one step harder in exactly one respect.
PROFILES = [
    ("Unstable Targets, a 2nd colour dot", (3, 2, 3, 2), 2),
    ("4 elements [3,3,3,2], 1 dot", (3, 3, 3, 2), 1),
    ("4 elements [3,3,3,2], 2 dots", (3, 3, 3, 2), 2),
    ("5 elements [3,2,3,2,2], 1 dot", (3, 2, 3, 2, 2), 1),
    ("4 elements [3,3,3,3], 1 dot", (3, 3, 3, 3), 1),
]


def main():
    print("A FOURTH AoS PROGRAM CLASS - is it needed, and how small can it be?")
    print("6000 games a cell, INSTALL_REQUIRES = nocat, 6 Assemblies offered.")
    print("Target is the AoS this replaces: %s."
          % " / ".join("%.1f" % w for w in WANT))
    print()

    print("1. THE FLOOR WITH NO NEW CARDS, at ten cards.")
    print("   Earlier sweeps held Specialized at 3 because the shipped ladder")
    print("   does. Nothing requires it at the bottom, and Specialized is the")
    print("   easier card, so the hardest ten-card deck is as much Unstable as")
    print("   is printed - the cap is 8 - and the rest Specialized.")
    print("   %-14s %8s" % ("R/S/U", "win"))
    for comp in ((5, 3, 2), (4, 3, 3), (3, 3, 4), (2, 3, 5), (1, 3, 6),
                 (0, 3, 7), (0, 2, 8), (0, 4, 6)):
        print("   %-14s %7.1f%%" % ("%d/%d/%d" % comp, win(comp)))
    print("   0/3/7 and 0/2/8 BOTH read the floor, from either side of it.")
    print("   Easy, Standard and Hard are all reachable from this table.")
    print("   Nobulous is 6.5 points above target and there is no cell left.")
    print()

    print("2. WHAT THE RESTRUCTURE IS WORTH ON ITS OWN, before any new")
    print("   Targets: a fourth class that is Unstable card for card.")
    clone_unstable()
    ctl = [win((0, 3, 7 - d, d)) for d in (0, 1, 2, 3)]
    print("   %-38s %6s %6s %6s %6s" % ("", "+0", "+1", "+2", "+3"))
    print("   %-38s %5.1f%% %5.1f%% %5.1f%% %5.1f%%"
          % ("a 4th class that IS Unstable", *ctl))
    print("   Three points of the drop are this and not the new card: with")
    print("   two decks of hard cards the deal stops seeing nearly all of")
    print("   either one. Real, but it is the deck structure paying, so the")
    print("   figures in 3 are decomposed against this row and not against")
    print("   41.4.")
    print()

    print("3. HOW MILD CAN THE NEW CLASS BE? Nobulous, by how many of the")
    print("   seven hard cards are the new class.")
    print("   %-38s %6s %6s %6s %6s   %s"
          % ("", "+0", "+1", "+2", "+3", "own effect at +2"))
    for label, front, dots in PROFILES:
        install(front, dots)
        cells = [win((0, 3, 7 - d, d)) for d in (0, 1, 2, 3)]
        print("   %-38s %5.1f%% %5.1f%% %5.1f%% %5.1f%%   %+5.1f"
              % (label, *cells, cells[2] - ctl[2]))
    print("   Two cards of the second profile land the rung. The first is")
    print("   too mild to matter - an extra colour dot is nearly free, which")
    print("   is worth knowing on its own - and the last three overshoot.")
    print()

    print("4. THE WHOLE LADDER on the second profile, new class at the")
    print("   bottom rung only so the other three are untouched.")
    install((3, 3, 3, 2), 1)
    fit = ((4, 3, 3, 0), (2, 3, 5, 0), (0, 3, 7, 0), (0, 3, 5, 2))
    print("   %-10s %-12s %8s %8s %7s" % ("rung", "mix", "win", "want", "off"))
    got = []
    for lvl, comp, want in zip(LEVELS, fit, WANT):
        w = win(comp)
        got.append(w)
        print("   %-10s %-12s %7.1f%% %7.1f%% %+6.1f"
              % (lvl, "%d/%d/%d/%d" % comp, w, want, w - want))
    print("   spread %.1f against the published %.1f"
          % (got[0] - got[-1], WANT[0] - WANT[-1]))
    print()
    print("   The deck CONTAINS two of the new class, at one rung. How many")
    print("   get PRINTED is a separate question this does not answer: the")
    print("   model samples 2 of 8, so printing fewer than 8 would deal them")
    print("   with less variety and wants re-measuring before anything goes")
    print("   to art.")


if __name__ == "__main__":
    main()
