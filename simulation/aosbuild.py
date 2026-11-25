"""CAN THE DEAL EVEN BE BUILT? The AoS Assembly setup gate.

A Program fills ONE Build slot and counts as ONE colour, chosen at
installation from its printed required-colour dots. So "can I build three of
the Assemblies I was offered" is a bipartite matching: the chosen trio's
slots on one side, distinct Programs on the other, an edge wherever the
Program prints that slot's colour. Nothing here rolls a die - this is the
question of whether a setup is winnable AT ALL, which is the one failure a
player cannot see coming and cannot play around.

MEASURED 2026-11-24, five offered and no deck check, the spec as handed over:

    Easy 15.6%  Standard 15.4%  Hard 12.8%  Nobulous 9.5%

of setups had no buildable trio before a single die was rolled - an
invisible loss dealt at setup. Two findings made that worth fixing at the
setup rather than on the cards:

  * IT IS ENTIRELY COLOUR SUPPLY, NOT SLOT COUNT. Of 3144 dead Standard
    deals, 3144 had a trio inside the slot budget and none could colour it.
    The binding case is a colour that only one Program in the deck can
    serve, which happens to some colour in roughly one deal in ten.
  * A DOUBLED COLOUR IS THE FLEXIBLE RECIPE, NOT THE DEMANDING ONE.
    Respeccing the four three-slot recipes to ask three DISTINCT colours
    made it worse, 23.4% at Standard, because three colours is three chances
    to be blocked where two is two. The handed-over recipes were right.

So the fix is two lines of setup, and no card changes:

    six Assemblies offered instead of five  ..........  15.4% -> 4.7%
    + every colour on >=2 of the 8 Programs  .........  15.4% -> 0.6%

The deck check costs about half a reshuffle per setup and a player does it
by counting dots, which is why it is preferred to redrawing the offer: a
player cannot eyeball a bipartite matching, but anyone can count to two.

The slot budget is how many Programs a player can realistically get
installed - every install needs a clean run - so 8 is the optimistic bound
and 7 the planning figure. Both are reported.
"""
import collections
import itertools
import random
import sys

sys.path.insert(0, "../generator")
sys.path.insert(0, "generator")
from aos import ALL_ASSEMBLIES, ASSEMBLIES, COVERT, REQ_MAP, ROUTINE, SPECIALIZED, UNSTABLE

DECKS = {"Routine": ROUTINE, "Specialized": SPECIALIZED, "Unstable": UNSTABLE}
# A Program's Build eligibility is exactly its printed required-colour dots.
COLORS_OF = lambda name: frozenset(c for c in REQ_MAP[name] if c)
POOL = {d: [(n, COLORS_OF(n)) for n, *_ in cards] for d, cards in DECKS.items()}

# rules/aos.html's difficulty table, as (Routine, Specialized, Unstable).
MIX = {"Easy": (3, 3, 2), "Standard": (2, 3, 3), "Hard": (1, 3, 4), "Nobulous": (0, 3, 5)}

RECIPES = [(n, rec) for n, rec, _, _ in ASSEMBLIES]
# Tier III swaps the Covert Sensor Array in for the standard Sensor Array and
# guarantees it a place in the offer.
TIER3 = [(n, rec) for n, rec, _, _ in ASSEMBLIES if n != "Sensor Array"]
COVERT_RECIPE = (COVERT[0], COVERT[1])

# PRINTED 2026-11-24: six offered, and every colour on at least two Programs.
OFFER = 6
COLOR_FLOOR = 2


def matches(slots, programs):
    """Is there a perfect matching of slots to distinct Programs?"""
    pairing = {}
    def augment(si, seen):
        for pi, (_, cs) in enumerate(programs):
            if slots[si] in cs and pi not in seen:
                seen.add(pi)
                if pi not in pairing or augment(pairing[pi], seen):
                    pairing[pi] = si
                    return True
        return False
    return all(augment(si, set()) for si in range(len(slots)))


def supply(programs):
    return {c: sum(1 for _, cs in programs if c in cs) for c in "PYBG"}


def draw_deck(mix, rng, floor=COLOR_FLOOR):
    """The 8-card Program deck, redrawn until the colour floor holds.
    Returns (programs, redraws)."""
    r, s, u = mix
    redraws = 0
    while True:
        progs = (rng.sample(POOL["Routine"], r) + rng.sample(POOL["Specialized"], s)
                 + rng.sample(POOL["Unstable"], u))
        if not floor or min(supply(progs).values()) >= floor:
            return progs, redraws
        redraws += 1


def buildable(offer, programs, budget):
    """Every trio of the offer that can actually be built."""
    out = []
    for trio in itertools.combinations(offer, 3):
        slots = [c for _, rec in trio for c in rec]
        if len(slots) <= budget and matches(slots, programs):
            out.append(tuple(n for n, _ in trio))
    return out


def survey(mix, recipes, offer_n, budget, floor, n=20000, seed=1234, forced=None):
    rng = random.Random(seed)
    dead = redraws = 0
    trios = []
    for _ in range(n):
        progs, rd = draw_deck(mix, rng, floor)
        redraws += rd
        pool = [r for r in recipes if r != forced]
        offer = rng.sample(pool, offer_n - (1 if forced else 0))
        if forced:
            offer = [forced] + offer
        found = buildable(offer, progs, budget)
        trios.append(len(found))
        if not found:
            dead += 1
    return 100.0 * dead / n, sum(trios) / float(n), redraws / float(n)


def main():
    levels = ("Easy", "Standard", "Hard", "Nobulous")
    print("AoS Assembly setup gate - %% of setups with NO buildable trio" % ())
    print("(no dice rolled; this is winnable-at-all, not win rate)")
    for budget in (8, 7):
        print()
        print("slot budget %d - the Programs a player can get installed clean" % budget)
        print("%-44s %8s %8s %8s %8s" % ("", *levels))
        for label, offer_n, floor in (
                ("as handed over: 5 offered, no deck check", 5, 0),
                ("6 offered", 6, 0),
                ("5 offered + colour floor 2", 5, 2),
                ("PRINTED: 6 offered + colour floor 2", 6, 2)):
            row = [survey(MIX[l], RECIPES, offer_n, budget, floor)[0] for l in levels]
            print("%-44s %7.2f%% %7.2f%% %7.2f%% %7.2f%%" % (label, *row))
    print()
    print("cost of the colour floor, in reshuffles per setup:")
    for l in levels:
        print("   %-9s %.3f" % (l, survey(MIX[l], RECIPES, OFFER, 8, COLOR_FLOOR)[2]))
    print()
    print("choice left on the table - mean buildable trios of the %d offered:"
          % (OFFER * (OFFER - 1) * (OFFER - 2) // 6))
    for l in levels:
        d, t, _ = survey(MIX[l], RECIPES, OFFER, 8, COLOR_FLOOR)
        print("   %-9s %.2f" % (l, t))
    print()
    print("Tier III, Covert Sensor Array guaranteed a place in the offer:")
    for l in levels:
        d, t, _ = survey(MIX[l], TIER3 + [COVERT_RECIPE], OFFER, 8, COLOR_FLOOR,
                         forced=COVERT_RECIPE)
        print("   %-9s dead %5.2f%%  mean buildable trios %.2f" % (l, d, t))
    print()
    print("how often each Assembly can be part of a buildable trio, Standard:")
    rng = random.Random(99)
    tally, offered = collections.Counter(), collections.Counter()
    for _ in range(20000):
        progs, _ = draw_deck(MIX["Standard"], rng)
        offer = rng.sample(RECIPES, OFFER)
        for n, _ in offer:
            offered[n] += 1
        for trio in buildable(offer, progs, 8):
            for n in trio:
                tally[n] += 1
    for n, rec in RECIPES:
        print("   %-18s %d slots  %.2f buildable trios per offer"
              % (n, len(rec), tally[n] / float(offered[n])))


if __name__ == "__main__":
    main()
