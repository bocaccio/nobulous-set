"""PROTOTYPE: one council deck, one shroud flip, +1 if it matches the gate.

    python proto/finale6.py

Exploratory. The structure, from Jon:

    "What if the council combines all the cards and reveals one as the
    'shroud' - if it matches the gate (i.e., an NAP card for a knowledge
    check), the target increases +1 beyond the boost from the NAP target
    value."

So all 18 cards from the three games go into one council deck. Each attempt
flips one:

    Target = base + Suspicion + the flipped card's value
             + 1 more if that card's domain matches the check's domain

The player keeps nothing and commits dice before the flip.

WHY THIS IS THE FIRST VERSION WITH A PER-CHECK DECISION. finale5 gave the
player one global hedge, and at any single pitch one hedge dominated - the
decision was solved once learned. Here the risk differs BY CHECK, because
the domains do not hold cards of equal value: BAT's deck runs 2-5 with
Specimens at 5 and Modifications at 4-5, AoS runs 2 or 4, NAP is a flat 2.
So a Physical check is the dangerous one, the player can see that from the
deck they just built by playing, and the right hedge changes from check to
check.

The measurement that matters is therefore whether reading the deck BY
DOMAIN beats reading it in aggregate. If it does, the domain-match rule has
bought a real skill layer for one line of text.

Card values are the printed ones: UPGRADE_VALUES is [2,3,3,4,2,2,3,3,2,3,
3,4,2,3,2,4] with Specimens at 5, NAP exams at 2, AoS Stable 4 and
Overheated 2.

SIMPLIFICATIONS: core economy only - no Scenario texts, no colour clauses,
no avoid rule. Read the gaps, not the absolute rates.
"""
import collections
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dice import COLORS, EV_REROLL, roll

GAMES = 20000
BASE_TARGET = 1
HEALTH = 5
REC_BASE = 3
ATTEMPTS = 9
MATCH_BONUS = 1           # the +1 when the shroud matches the gate
DOMAINS = ("Knowledge", "Physical", "Cover-Up")
TIER3 = True              # Tier III puts Modifications at 4-5 in BAT's deck


def fresh():
    # 20 Strong's pool is 4 each of purple, blue, green and yellow plus a
    # SINGLE red - 17 unit dice (General Rules, p.7). Earlier prototypes used
    # 3 each plus two reds, which made red twice as common as it is and the
    # cheap colours scarcer; both matter here, because the design turns on
    # which colours you hold.
    return [c for c in COLORS for _ in range(4)] + ["red"]


def council_deck(rng):
    """All 18 cards the three games produced, as (domain, value)."""
    deck = []
    for _ in range(6):                      # NAP: exams, flat 2
        deck.append(("Knowledge", 2))
    # BAT: the Upgrades and Splices that came out of the battle.
    pool = [2, 3, 3, 4, 2, 2, 3, 3, 2, 3, 3, 2, 4]
    if TIER3:
        pool += [4, 4, 5, 4, 5, 4]          # the 6 Modifications
    for _ in range(6):
        deck.append(("Physical", rng.choice(pool + [5])))   # 5 = a Specimen
    for _ in range(6):                      # AoS: Stable 4 / Overheated 2
        deck.append(("Cover-Up", 4 if rng.random() < 0.65 else 2))
    rng.shuffle(deck)
    return deck


def quantile(vals, q):
    vals = sorted(vals)
    if not vals:
        return 0.0
    i = int(round(q * (len(vals) - 1)))
    return float(vals[i])


def hedge(policy, deck, domain, hp=None, left=None, dice=None):
    """How much the player pads the commitment, by policy.

    The fixed policies name a quantile of what the council could still
    flip. `adaptive` moves that quantile with the state, on the reasoning
    the earlier prototypes made measurable: a failure costs a point of
    Suspicion, which cuts REC for every attempt still to come - so failing
    EARLY is dear and failing on the last attempt is nearly free. Hedge
    hard while the game is long, stop paying for insurance at the end, and
    never hedge with dice you cannot spare.
    """
    if policy == "reckless" or not deck:
        return 0.0
    vals = [v + (MATCH_BONUS if d == domain else 0) for d, v in deck]
    if policy == "cautious":
        return float(max(vals))
    if policy == "q25":
        return quantile(vals, 0.25)
    if policy == "q50":
        return quantile(vals, 0.50)
    if policy == "q75":
        return quantile(vals, 0.75)
    if policy == "by_domain":
        return sum(vals) / float(len(vals))
    if policy == "counting":
        return sum(v for _, v in deck) / float(len(deck))
    if policy == "adaptive":
        q = 0.50
        if left is not None and left >= 6:
            q += 0.20                 # a failure now poisons six more checks
        if left is not None and left <= 2:
            q -= 0.25                 # almost nothing left to poison
        if hp is not None and hp <= 2:
            q += 0.20                 # cannot afford the Health
        if dice is not None and dice <= 6:
            q -= 0.30                 # no dice to insure with
        return quantile(vals, min(1.0, max(0.0, q)))
    return 3.0                        # "average": a fixed estimate


def play(rng, policy, failure="dice"):
    deck = council_deck(rng)
    available, exhausted = fresh(), []
    hp, suspicion = HEALTH, 0
    order = [d for d in DOMAINS for _ in range(3)]
    rng.shuffle(order)

    for attempt in range(ATTEMPTS):
        domain = order[attempt]
        base = BASE_TARGET + suspicion
        want = base + hedge(policy, deck, domain, hp=hp,
                            left=ATTEMPTS - attempt, dice=len(available))

        available.sort(key=lambda c: -EV_REROLL[c])
        take, got = [], 0.0
        for c in available:
            if got >= want:
                break
            take.append(c)
            got += EV_REROLL[c]
        values = [roll(c, rng) for c in take]
        hits = sum(values)
        if hits < want:                     # STR 2: one Strategy reroll
            again = [take[i] for i, v in enumerate(values) if v == 0]
            hits += sum(roll(c, rng) for c in again)
        for c in take:
            available.remove(c)
            exhausted.append(c)

        shroud_domain, shroud_value = deck.pop()
        target = base + shroud_value
        if shroud_domain == domain:
            target += MATCH_BONUS

        if hits < target:
            suspicion += 1
            can_banish = len(available) >= 2
            # finale5 measured dice-first as worth 9-13 points over Health.
            if failure == "dice" and can_banish:
                available.sort(key=lambda c: EV_REROLL[c])
                for _ in range(2):
                    available.pop(0)
            else:
                hp -= 1
                if hp <= 0:
                    return False
        rec = max(0, REC_BASE - suspicion)
        exhausted.sort(key=lambda c: EV_REROLL[c])
        for _ in range(min(rec, len(exhausted))):
            available.append(exhausted.pop())
    return hp >= 1


def run(policy, failure="dice", games=GAMES, seed=11, **over):
    saved = {k: globals()[k] for k in over}
    globals().update(over)
    rng = random.Random(seed)
    try:
        return 100.0 * sum(1 for _ in range(games)
                           if play(rng, policy, failure)) / games
    finally:
        globals().update(saved)


if __name__ == "__main__":
    FIXED = ("reckless", "q25", "q50", "by_domain", "q75", "cautious")
    print("PROTOTYPE - base 0 with match +2, and an adaptive hedge")
    print("=" * 76)
    print("%d finales a cell. The adaptive policy has to beat the BEST fixed"
          % GAMES)
    print("one, not the average one, or it is not buying anything.")

    for base, bonus in ((0, 2), (1, 1), (0, 3), (1, 2)):
        print()
        print("  base %d, match +%d" % (base, bonus))
        print("   %-12s" % "policy" + "".join("%11s" % p for p in FIXED)
              + "%11s" % "adaptive")
        ws = [run(p, BASE_TARGET=base, MATCH_BONUS=bonus) for p in FIXED]
        ad = run("adaptive", BASE_TARGET=base, MATCH_BONUS=bonus)
        print("   %-12s" % "win" + "".join("%10.1f%%" % w for w in ws)
              + "%10.1f%%" % ad)
        best = max(ws)
        print("   %-12s best fixed %.1f%%, adaptive %.1f%%  ->  %+.1f"
              % ("", best, ad, ad - best))
        sys.stdout.flush()

    print()
    print("  WHICH PART OF THE ADAPTIVE RULE EARNS ITS KEEP?")
    print("  base 0, match +2. Each row drops one clause.")
    import re
    src = open(__file__).read() if False else None
    print("   %-34s %9s" % ("rule", "win"))
    full = run("adaptive", BASE_TARGET=0, MATCH_BONUS=2)
    print("   %-34s %8.1f%%" % ("the whole rule", full))
    for label, patch in (("without the early-game clause", "left_hi"),
                         ("without the endgame clause", "left_lo"),
                         ("without the low-Health clause", "hp"),
                         ("without the few-dice clause", "dice")):
        # Re-run with that clause neutralised by passing None for its input.
        real = hedge

        def patched(policy, deck, domain, hp=None, left=None, dice=None,
                    _p=patch, _r=real):
            if _p == "hp":
                hp = 5
            elif _p == "dice":
                dice = 99
            elif _p == "left_hi":
                left = min(left or 0, 5)
            elif _p == "left_lo":
                left = max(left or 0, 3)
            return _r(policy, deck, domain, hp, left, dice)

        globals()["hedge"] = patched
        try:
            w = run("adaptive", BASE_TARGET=0, MATCH_BONUS=2)
        finally:
            globals()["hedge"] = real
        print("   %-34s %8.1f%%  %+5.1f" % (label, w, w - full))
        sys.stdout.flush()
