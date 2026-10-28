"""PROTOTYPE: evidence, not currency. Spending a card exposes you.

    python proto/finale3.py

Exploratory. The concept, from Jon:

    "I almost want it to be that players do not want to use their cards. If
    they do, this does more to expose them. The puzzle then is figuring out
    how to appease the council without revealing your hand."

    "Perhaps the 3 cards that are selected randomly go to the council
    instead of the imposter."

So the finale inverts. A Research card still reduces a Target, but spending
one adds a card to the Suspicion row - which raises every later Target and
cuts REC, exactly the machinery the shipped finale already uses for
failure. Evidence you produce incriminates you. The 3 Candidates each game
banks become the COUNCIL's dossier, setting how hard that domain's checks
are, which is where the "veracity of the council" framing lands.

WHY THIS IS WORTH TESTING. The gated prototype (finale2.py) measured a
policy gap of under 3 points - playing cleverly scored the same as playing
blindly, because spending was free and only one kind of card was legal per
check, so there was no decision in it. The metric here is that gap. If
"spend reluctantly" beats "spend freely" by a wide margin, the design has
a puzzle in it; if not, it is another gauntlet.

SIMPLIFICATIONS, and they matter for reading the numbers: this is the core
economy only. None of the 24 Scenarios' printed texts are here, nor the
colour clauses, nor the avoid rule. Absolute win rates are indicative; the
POLICY GAP is the measurement that survives the simplification.
"""
import collections
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dice import COLORS, EV_REROLL, roll

GAMES = 20000
DOMAINS = ("Knowledge", "Physical", "Cover-Up")

# ---------------------------------------------------------------- the dials
BASE_TARGET = 6           # before the council's dossier and Suspicion
HEALTH = 5
REC_BASE = 3
ATTEMPTS = 9
SUSPICION_PER_CARD = 1    # what producing evidence costs you
SCRUTINY_PER_COUNCIL = 1  # +Target per council card in that domain
CARD_VALUES = {"NAP": 3, "BAT": 3, "AoS": 3}
SPECIMEN = 5              # BAT's lever
STABLE = 4                # AoS's lever: pure reduction
OVERHEATED = 2            # weaker, but see finale2 - avoid is not modelled here


def fresh():
    # 20 Strong's pool is 4 each of purple, blue, green and yellow plus a
    # SINGLE red - 17 unit dice (General Rules, p.7). Earlier prototypes used
    # 3 each plus two reds, which made red twice as common as it is and the
    # cheap colours scarcer; both matter here, because the design turns on
    # which colours you hold.
    return [c for c in COLORS for _ in range(4)] + ["red"]


class Card(object):
    __slots__ = ("game", "value")

    def __init__(self, game, value):
        self.game, self.value = game, value


def deal(rng):
    """Your 9 retained cards, and the council's 9."""
    mine, council = [], collections.Counter()
    for _ in range(3):
        mine.append(Card("NAP", CARD_VALUES["NAP"]))
    specimen = rng.random() < 0.5
    for i in range(3):
        mine.append(Card("BAT", SPECIMEN if (specimen and i == 0)
                         else CARD_VALUES["BAT"]))
    for _ in range(3):
        mine.append(Card("AoS", STABLE if rng.random() < 0.65 else OVERHEATED))
    # The 3 Candidates from each game go to the council as its dossier.
    for domain in DOMAINS:
        council[domain] = 3
    return mine, council


DOMAIN_OF = {"NAP": "Knowledge", "BAT": "Physical", "AoS": "Cover-Up"}


def play(rng, policy):
    mine, council = deal(rng)
    available, exhausted = fresh(), []
    hp, suspicion = HEALTH, 0
    order = [d for d in DOMAINS for _ in range(3)]
    rng.shuffle(order)

    for attempt in range(ATTEMPTS):
        domain = order[attempt]
        target = (BASE_TARGET + SCRUTINY_PER_COUNCIL * council[domain]
                  + suspicion)
        usable = [c for c in mine if DOMAIN_OF[c.game] == domain]

        # Commit dice: everything that gets the expected total to target.
        available.sort(key=lambda c: -EV_REROLL[c])
        take, got = [], 0.0
        for c in available:
            if got >= target:
                break
            take.append(c)
            got += EV_REROLL[c]

        # ---- the decision: produce evidence, or risk the check?
        spend = []
        short = target - got
        if usable and short > 0:
            if policy == "free":
                spend = sorted(usable, key=lambda c: -c.value)
            elif policy == "reluctant":
                # Only enough to make the check reachable, and only if it
                # actually can be made reachable.
                if sum(c.value for c in usable) >= short:
                    for c in sorted(usable, key=lambda c: c.value):
                        if short <= 0:
                            break
                        spend.append(c)
                        short -= c.value
            elif policy == "late":
                # Same, but hold everything until the last three checks:
                # evidence produced late incriminates you for fewer rounds.
                if attempt >= ATTEMPTS - 3 and \
                        sum(c.value for c in usable) >= short:
                    for c in sorted(usable, key=lambda c: c.value):
                        if short <= 0:
                            break
                        spend.append(c)
                        short -= c.value
            elif policy == "never":
                spend = []
        for c in spend:
            mine.remove(c)
            target -= c.value
            suspicion += SUSPICION_PER_CARD      # producing it exposes you

        # ---- resolve
        values = [roll(c, rng) for c in take]
        total = sum(values)
        if total < target:                       # one Strategy reroll (STR 2)
            again = [take[i] for i, v in enumerate(values) if v == 0]
            total += sum(roll(c, rng) for c in again)
        for c in take:
            available.remove(c)
            exhausted.append(c)

        if total < target:
            suspicion += 1
            hp -= 1
            if hp <= 0:
                return False
        rec = max(0, REC_BASE - suspicion)
        exhausted.sort(key=lambda c: EV_REROLL[c])
        for _ in range(min(rec, len(exhausted))):
            available.append(exhausted.pop())
    return hp >= 1


def run(policy, games=GAMES, seed=11, **over):
    saved = {k: globals()[k] for k in over}
    globals().update(over)
    rng = random.Random(seed)
    try:
        return 100.0 * sum(1 for _ in range(games)
                           if play(rng, policy)) / games
    finally:
        globals().update(saved)


if __name__ == "__main__":
    POLICIES = ("never", "free", "reluctant", "late")
    print("PROTOTYPE - evidence, not currency")
    print("=" * 70)
    print("%d finales a cell. Spending a card adds %d to Suspicion, which"
          % (GAMES, SUSPICION_PER_CARD))
    print("raises every later Target and cuts REC. The council's dossier is")
    print("the 3 Candidates each game banks.")

    print()
    print("1. FINDING THE PITCH, and the policy gap at each one")
    print("   %-26s" % "base Target"
          + "".join("%11s" % p for p in POLICIES) + "%8s" % "gap")
    for base in (4, 5, 6, 7, 8):
        ws = [run(p, BASE_TARGET=base) for p in POLICIES]
        print("   %-26s" % base + "".join("%10.1f%%" % w for w in ws)
              + "%7.1f" % (max(ws) - min(ws)))
        sys.stdout.flush()

    print()
    print("2. WHAT EXPOSURE SHOULD COST - Suspicion added per card spent")
    print("   %-26s" % "per card"
          + "".join("%11s" % p for p in POLICIES) + "%8s" % "gap")
    for cost in (0, 1, 2, 3):
        ws = [run(p, SUSPICION_PER_CARD=cost) for p in POLICIES]
        print("   %-26s" % cost + "".join("%10.1f%%" % w for w in ws)
              + "%7.1f" % (max(ws) - min(ws)))
        sys.stdout.flush()

    print()
    print("3. THE COUNCIL'S DOSSIER - scrutiny per card it holds")
    print("   %-26s" % "per council card"
          + "".join("%11s" % p for p in POLICIES) + "%8s" % "gap")
    for s in (0, 1, 2):
        ws = [run(p, SCRUTINY_PER_COUNCIL=s) for p in POLICIES]
        print("   %-26s" % s + "".join("%10.1f%%" % w for w in ws)
              + "%7.1f" % (max(ws) - min(ws)))
        sys.stdout.flush()
