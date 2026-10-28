"""PROTOTYPE: the player keeps nothing. The council keeps everything.

    python proto/finale5.py

Exploratory. The structure, from Jon, after Arkham Horror LCG - and with
the clarification that settles the shape of it:

    "Create a mix of cards that are given to the council. You have some
    notion of what the council holds, but you have to allocate and roll
    dice to mitigate against whatever might come from the 'shroud' card
    flip."

    "To be clear, the player would not retain any cards going into the
    finale."

So the Imposter walks in with nothing but dice, Health and nerve. Every
card the three games produced goes to the COUNCIL, and the council's deck
is what the campaign hands forward: you know roughly what is in it, because
you lived it, but not the order it comes out in. One card flips per attempt
and takes successes away.

WHY THIS IS A BETTER SHAPE THAN THE EARLIER PROTOTYPES. Each of them put
the campaign's influence in the player's hand, and each ran into the same
wall - measured, not guessed:

    finale2  cards gated to their domain      policy gap 0.4 - 2.9, rote
    finale3  spending cards costs Suspicion   good gap, but Candidates and
                                              card identity stayed inert
    finale4  reveal the flip, then pay        gap 34 - 42, but WHICH card
                                              you played was worth ~2 points
                                              and a random draw ~2 more

The pattern is that card identity never mattered, because a payment was
only ever one or two cards. Moving the whole hand to the council's side of
the table stops pretending otherwise: the campaign sets the DECK, and the
player's decisions are the ones dice games are good at.

THE TWO DECISIONS, both measured below:

    allocation  how many dice to commit against a known distribution, when
                dice only come back at REC and the Suspicion row is cutting
                REC every time something goes wrong
    the failure choice  "lose 1 Health or banish 2 available dice" - a real
                decision once dice are the only currency

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
BASE_TARGET = 4
HEALTH = 5
REC_BASE = 3
ATTEMPTS = 9
DECK_SIZE = 18            # the council holds everything the games produced
BANISH_COST = 2           # dice banished instead of losing 1 Health

# The council's deck, as a mix of "successes taken away" values. Nine of
# these flip, one per attempt, so with 18 cards you know the mix but see
# only half of it.
COUNCIL = {0: 7, 1: 6, 2: 3, -1: 2}


def fresh():
    # 20 Strong's pool is 4 each of purple, blue, green and yellow plus a
    # SINGLE red - 17 unit dice (General Rules, p.7). Earlier prototypes used
    # 3 each plus two reds, which made red twice as common as it is and the
    # cheap colours scarcer; both matter here, because the design turns on
    # which colours you hold.
    return [c for c in COLORS for _ in range(4)] + ["red"]


def build_deck(rng, size):
    weights = [v for v, n in COUNCIL.items() for _ in range(n)]
    deck = [rng.choice(weights) for _ in range(size)]
    rng.shuffle(deck)
    return deck


def hedge(policy, deck):
    """How much the player pads the commitment, by policy."""
    if policy == "reckless":
        return 0.0
    if not deck:
        return 0.0
    if policy == "cautious":
        return float(max(deck))
    if policy == "counting":
        return sum(deck) / float(len(deck))
    whole = [v for v, n in COUNCIL.items() for _ in range(n)]
    return sum(whole) / float(len(whole))          # "average"


def play(rng, policy, failure="smart"):
    deck = build_deck(rng, DECK_SIZE)
    available, exhausted, banished = fresh(), [], []
    hp, suspicion = HEALTH, 0

    for attempt in range(ATTEMPTS):
        target = BASE_TARGET + suspicion
        want = target + hedge(policy, deck)

        available.sort(key=lambda c: -EV_REROLL[c])
        take, got = [], 0.0
        for c in available:
            if got >= want:
                break
            take.append(c)
            got += EV_REROLL[c]
        values = [roll(c, rng) for c in take]
        hits = sum(values)
        if hits < want:                       # STR 2: one Strategy reroll
            again = [take[i] for i, v in enumerate(values) if v == 0]
            hits += sum(roll(c, rng) for c in again)
        for c in take:
            available.remove(c)
            exhausted.append(c)

        hits -= deck.pop()                    # the council flips

        if hits < target:
            suspicion += 1
            # "Lose 1 Health or banish 2 available dice."
            can_banish = len(available) >= BANISH_COST
            if failure == "dice" and can_banish:
                pay_dice = True
            elif failure == "health":
                pay_dice = False
            else:
                # Dice are the only currency now, so spend Health while it
                # is plentiful and dice once Health is short.
                pay_dice = can_banish and hp <= 2
            if pay_dice:
                available.sort(key=lambda c: EV_REROLL[c])
                for _ in range(BANISH_COST):
                    banished.append(available.pop(0))
            else:
                hp -= 1
                if hp <= 0:
                    return False
        rec = max(0, REC_BASE - suspicion)
        exhausted.sort(key=lambda c: EV_REROLL[c])
        for _ in range(min(rec, len(exhausted))):
            available.append(exhausted.pop())
    return hp >= 1


def run(policy, failure="smart", games=GAMES, seed=11, **over):
    saved = {k: globals()[k] for k in over}
    globals().update(over)
    rng = random.Random(seed)
    try:
        return 100.0 * sum(1 for _ in range(games)
                           if play(rng, policy, failure)) / games
    finally:
        globals().update(saved)


if __name__ == "__main__":
    POLICIES = ("reckless", "average", "counting", "cautious")
    print("PROTOTYPE - the player keeps nothing")
    print("=" * 74)
    print("%d finales a cell. The council holds %d cards and flips one per"
          % (GAMES, DECK_SIZE))
    print("attempt; the player has 17 dice, 5 Health and no cards at all.")

    print()
    print("1. IS THERE A DECISION IN ALLOCATING DICE?")
    print("   %-16s" % "base Target"
          + "".join("%12s" % p for p in POLICIES) + "%8s" % "gap")
    for base in (3, 4, 5, 6):
        ws = [run(p, BASE_TARGET=base) for p in POLICIES]
        print("   %-16s" % base + "".join("%11.1f%%" % w for w in ws)
              + "%7.1f" % (max(ws) - min(ws)))
        sys.stdout.flush()

    print()
    print("2. THE FAILURE CHOICE - lose Health or banish 2 dice?")
    print("   %-16s %11s %11s %11s %8s"
          % ("policy", "always HP", "always dice", "smart", "gap"))
    for p in POLICIES:
        ws = [run(p, failure=f) for f in ("health", "dice", "smart")]
        print("   %-16s %10.1f%% %10.1f%% %10.1f%% %7.1f"
              % (p, ws[0], ws[1], ws[2], max(ws) - min(ws)))
        sys.stdout.flush()

    print()
    print("3. DOES COUNTING BEAT KNOWING? by how the deck is built")
    print("   %-30s %9s %9s %7s" % ("council deck", "average", "counting",
                                    "delta"))
    for label, deck in (
            ("as above  0x7,1x6,2x3,-1x2", COUNCIL),
            ("mild      0x12,1x6", {0: 12, 1: 6}),
            ("spiky     0x14,3x4", {0: 14, 3: 4}),
            ("one bomb  0x17,5x1", {0: 17, 5: 1}),
            ("harsh     1x8,2x6,3x4", {1: 8, 2: 6, 3: 4})):
        a = run("average", COUNCIL=deck)
        c = run("counting", COUNCIL=deck)
        print("   %-30s %8.1f%% %8.1f%% %+6.1f" % (label, a, c, c - a))
        sys.stdout.flush()

    print()
    print("4. THE CAMPAIGN'S DIAL - deck size, and how much the council got")
    print("   %-30s %9s" % ("council deck", "win (counting)"))
    for size in (9, 12, 18, 24):
        print("   %-30s %8.1f%%" % ("%d cards, 9 flipped" % size,
                                    run("counting", DECK_SIZE=size)))
        sys.stdout.flush()
