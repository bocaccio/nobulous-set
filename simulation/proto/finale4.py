"""PROTOTYPE: reveal, then pay. The council's dossier as a chaos bag.

    python proto/finale4.py

Exploratory. The structure, from Jon, after Arkham Horror LCG:

    "The scenario is revealed, you have to commit and roll dice and then a
    council upgrade is revealed similar to the chaos bag. If you didn't have
    enough hits, you can choose to play a card to get a success."

So the order of play becomes:

    1. reveal the Scenario           its Target, plus the Suspicion row
    2. commit dice and roll          blind to what the council will produce
    3. reveal one council card       the dossier, one card per attempt
    4. choose to pay the shortfall   each card played buys successes AND
                                     adds to the Suspicion row

This is strictly a better decision than every earlier prototype, for one
reason: you pay with INFORMATION. finale2 and finale3 both make you spend
before the roll, so evidence is either wasted on a check you would have
passed or sunk into one you then lose anyway. Here you know the exact
shortfall, so the only question is the one that should be interesting - is
this check worth the exposure?

It also gives the council's 9 Candidates a job. Nine council cards, nine
attempts, one revealed each time: the dossier IS the randomiser, so the
cards each game leaves behind decide how the finale swings.

The two decisions this creates, and both are measured below:

    how many dice to commit    the council card lands after you commit, so
                               extra dice are insurance - and dice come back
                               at REC, which the Suspicion row is cutting
    whether to pay             with full information, against a cost that
                               compounds for the rest of the finale

SIMPLIFICATIONS: core economy only - no Scenario texts, no colour clauses,
no avoid rule. Read the POLICY GAP, not the absolute rates.
"""
import collections
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dice import COLORS, EV_REROLL, roll

GAMES = 20000
DOMAINS = ("Knowledge", "Physical", "Cover-Up")
DOMAIN_OF = {"NAP": "Knowledge", "BAT": "Physical", "AoS": "Cover-Up"}

# ---------------------------------------------------------------- the dials
BASE_TARGET = 5
HEALTH = 5
REC_BASE = 3
ATTEMPTS = 9
SUSPICION_PER_CARD = 1     # playing evidence exposes you
COMMIT_MARGIN = 1          # expected successes committed over the Target
GATED = True               # may a card only answer its own domain?
RANDOM_PAY = False         # must the card played be drawn at random?
BASE_FOR_REPORT = 4        # the pitch the sections below run at

# What one played card buys, in successes. These are the levers.
NAP_SUCCESS = 1
UPGRADE_SUCCESS = 1
SPECIMEN_SUCCESS = 2       # BAT's lever
STABLE_SUCCESS = 2         # AoS's lever
OVERHEATED_SUCCESS = 1

# The council's dossier, drawn one card per attempt. Each entry is how many
# successes it takes away (negative gives one back), with a weight.
DOSSIER = ((0, 3), (1, 3), (2, 2), (-1, 1))


def fresh():
    # 20 Strong's pool is 4 each of purple, blue, green and yellow plus a
    # SINGLE red - 17 unit dice (General Rules, p.7). Earlier prototypes used
    # 3 each plus two reds, which made red twice as common as it is and the
    # cheap colours scarcer; both matter here, because the design turns on
    # which colours you hold.
    return [c for c in COLORS for _ in range(4)] + ["red"]


class Card(object):
    __slots__ = ("game", "buys")

    def __init__(self, game, buys):
        self.game, self.buys = game, buys


def deal(rng):
    mine = [Card("NAP", NAP_SUCCESS) for _ in range(3)]
    specimen = rng.random() < 0.5
    for i in range(3):
        mine.append(Card("BAT", SPECIMEN_SUCCESS if (specimen and i == 0)
                         else UPGRADE_SUCCESS))
    for _ in range(3):
        mine.append(Card("AoS", STABLE_SUCCESS if rng.random() < 0.65
                         else OVERHEATED_SUCCESS))
    bag = []
    for penalty, weight in DOSSIER:
        bag += [penalty] * weight
    council = [rng.choice(bag) for _ in range(ATTEMPTS)]
    return mine, council


def play(rng, policy):
    mine, council = deal(rng)
    available, exhausted = fresh(), []
    hp, suspicion, spent = HEALTH, 0, 0
    order = [d for d in DOMAINS for _ in range(3)]
    rng.shuffle(order)

    for attempt in range(ATTEMPTS):
        domain = order[attempt]
        target = BASE_TARGET + suspicion

        # ---- commit dice, blind to what the council will produce
        available.sort(key=lambda c: -EV_REROLL[c])
        take, got = [], 0.0
        for c in available:
            if got >= target + COMMIT_MARGIN:
                break
            take.append(c)
            got += EV_REROLL[c]
        values = [roll(c, rng) for c in take]
        hits = sum(values)
        if hits < target:                        # STR 2: one Strategy reroll
            again = [take[i] for i, v in enumerate(values) if v == 0]
            hits += sum(roll(c, rng) for c in again)
        for c in take:
            available.remove(c)
            exhausted.append(c)

        # ---- the council produces a card
        hits -= council[attempt]

        # ---- pay the shortfall, with full information
        short = target - hits
        if short > 0:
            usable = [c for c in mine
                      if not GATED or DOMAIN_OF[c.game] == domain]
            usable.sort(key=lambda c: -c.buys)
            afford = sum(c.buys for c in usable) >= short
            pay = False
            if policy == "always":
                pay = afford
            elif policy == "cheap":
                pay = afford and short <= 2
            elif policy == "desperate":
                pay = afford and (hp <= 2 or short <= 1)
            elif policy == "never":
                pay = False
            if pay:
                # Chosen: spend the strongest first, so the shortfall costs
                # the fewest cards. Random: you reach into the hand and take
                # what comes, so a weak draw costs another card and another
                # point of Suspicion.
                while short > 0 and usable:
                    c = (usable.pop(rng.randrange(len(usable))) if RANDOM_PAY
                         else usable.pop(0))
                    short -= c.buys
                    mine.remove(c)
                    spent += 1
                    suspicion += SUSPICION_PER_CARD

        if short > 0:
            suspicion += 1
            hp -= 1
            if hp <= 0:
                return False, spent
        rec = max(0, REC_BASE - suspicion)
        exhausted.sort(key=lambda c: EV_REROLL[c])
        for _ in range(min(rec, len(exhausted))):
            available.append(exhausted.pop())
    return hp >= 1, spent


def run(policy, games=GAMES, seed=11, **over):
    saved = {k: globals()[k] for k in over}
    globals().update(over)
    rng = random.Random(seed)
    try:
        wins, spent = 0, 0
        for _ in range(games):
            won, used = play(rng, policy)
            wins += won
            spent += used
        return 100.0 * wins / games, spent / float(games)
    finally:
        globals().update(saved)


if __name__ == "__main__":
    POLICIES = ("never", "always", "cheap", "desperate")
    B = BASE_FOR_REPORT
    print("PROTOTYPE - reveal, then pay")
    print("=" * 74)
    print("%d finales a cell, base Target %d - the pitch that lands in band."
          % (GAMES, B))
    print("Dice commit blind; the council produces a card after the roll;")
    print("evidence is paid against a known shortfall.")

    print()
    print("1. CHOSEN AGAINST RANDOM - may you pick which card you play?")
    print("   %-24s" % "" + "".join("%12s" % p for p in POLICIES)
          + "%8s" % "gap")
    for label, rp in (("you choose the card", False),
                      ("drawn at random", True)):
        ws = [run(p, BASE_TARGET=B, RANDOM_PAY=rp)[0] for p in POLICIES]
        print("   %-24s" % label + "".join("%11.1f%%" % w for w in ws)
              + "%7.1f" % (max(ws) - min(ws)))
        sys.stdout.flush()

    print()
    print("2. THE FRONTIER - win rate against evidence produced")
    print("   %-28s %8s %14s" % ("", "win", "cards played"))
    for label, rp in (("chosen", False), ("random", True)):
        for p in POLICIES:
            w, s = run(p, BASE_TARGET=B, RANDOM_PAY=rp)
            print("   %-28s %7.1f%% %13.1f" % ("%s, %s" % (label, p), w, s))
            sys.stdout.flush()

    print()
    print("3. DOES WHAT YOU BANKED MATTER NOW? the BAT and AoS levers")
    print("   %-34s %10s %10s" % ("", "chosen", "random"))
    for label, kw in (
            ("as dealt", {}),
            ("BAT: no Specimen (all buy 1)", dict(SPECIMEN_SUCCESS=1)),
            ("BAT: Specimen buys 3", dict(SPECIMEN_SUCCESS=3)),
            ("AoS: all Stable (all buy 2)", dict(OVERHEATED_SUCCESS=2)),
            ("AoS: all Overheated (all buy 1)", dict(STABLE_SUCCESS=1))):
        a = run("cheap", BASE_TARGET=B, RANDOM_PAY=False, **kw)[0]
        b = run("cheap", BASE_TARGET=B, RANDOM_PAY=True, **kw)[0]
        print("   %-34s %9.1f%% %9.1f%%" % (label, a, b))
        sys.stdout.flush()

    print()
    print("4. CAN THE DICE MEDIATE IT? dice committed over the Target")
    print("   %-16s %12s %12s %12s"
          % ("margin", "chosen cheap", "random cheap", "random always"))
    for margin in (0, 1, 2, 3):
        a = run("cheap", BASE_TARGET=B, COMMIT_MARGIN=margin)[0]
        b = run("cheap", BASE_TARGET=B, COMMIT_MARGIN=margin,
                RANDOM_PAY=True)[0]
        c = run("always", BASE_TARGET=B, COMMIT_MARGIN=margin,
                RANDOM_PAY=True)[0]
        print("   %-16s %11.1f%% %11.1f%% %11.1f%%" % (margin, a, b, c))
        sys.stdout.flush()

    print()
    print("5. HOW NASTY SHOULD THE DOSSIER BE? (random pay)")
    print("   %-26s" % "council cards" + "".join("%12s" % p for p in POLICIES))
    for label, bag in (
            ("benign  0/0/+1", ((0, 2), (1, 1))),
            ("middling 0/+1/+2/-1", DOSSIER),
            ("harsh   +1/+2/+3", ((1, 2), (2, 2), (3, 1))),
            ("swingy  -2/0/+3", ((-2, 1), (0, 2), (3, 2)))):
        ws = [run(p, BASE_TARGET=B, DOSSIER=bag, RANDOM_PAY=True)[0]
              for p in POLICIES]
        print("   %-26s" % label + "".join("%11.1f%%" % w for w in ws))
        sys.stdout.flush()
