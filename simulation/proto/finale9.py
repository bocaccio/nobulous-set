"""PROTOTYPE: the Dossier, the Exhibit deck, and a likeness you flip for.

    python proto/finale9.py

Exploratory. The structure is Jon's, across three messages. Each attempt:

    1  flip the top EXHIBIT. This is the DEMAND - you see it, and its type
       tells you what you must do before anything else.
    2  resolve the demand:

         Knowledge   commit COMBO dice of the colour it names, in addition
                     to nothing - they count toward the check - and take a
                     point of Suspicion if you cannot supply them all.
         Physical    the test is LIKENESS, not strength: flip Exhibits
                     until one matches the Target on your Dossier. The
                     NUMBER of cards flipped is the shroud value.
         Cover-Up    remove the top Exhibit face down, without looking,
                     then shuffle the discarded Exhibits back into a new
                     deck.

    3  commit dice against what you expect.
    4  the shroud resolves. Target = base + Suspicion + shroud. Miss it and
       Suspicion rises and you banish dice, or lose Health if you cannot.

WHY THIS IS THE FIRST VERSION WHERE COUNTING CAN PAY. finale8 measured the
value of counting the deck at zero, and the reason was mechanical: counting
changed the dice committed on only 13.5% of attempts, and when it did the
change was one die. Information is worth nothing when the only lever it
moves is a scalar quantised to whole dice.

Flip-until-match breaks that. Drawing without replacement until the first
match, with K matching cards among N, runs (N+1)/(K+1) cards long. With
twelve Exhibits that is about 1.9 flips if your likeness is common and 6.5
if it is rare - and if the last matching Exhibit has been burned it is the
whole deck. So knowing what is left does not adjust your commitment by a
die, it tells you whether the next Physical test costs you two successes or
nine. That is a decision with teeth, and it is the thing the Cover-Up
effect can then attack.

And the burn is what makes that attack stick. A plain reshuffle only resets
memory, which a player rebuilds. Removing a card FACE DOWN puts permanent
uncertainty into the deck, and it can quietly take away the last Exhibit
that matches your Dossier - after which every Physical test is a crawl and
nothing you can observe tells you why.

WHAT IS MEASURED HERE:

    1  the shroud the likeness actually produces, against the printed 2-5
       values it replaces
    2  DOES COUNTING PAY NOW - a perfect counter against one who never
       counts, by likeness. This is the whole point of the prototype.
    3  what the burn costs, separately from the reshuffle
    4  whether the Knowledge combination creates a real decision about
       keeping a spread of colours available
    5  the pitch, and how much the likeness swings it

SIMPLIFICATIONS: core economy only - no Scenario texts, no avoid rule, and
none of finale8's per-domain dice clauses, which are orthogonal to this and
can be layered back on. Read the gaps, not the absolute rates.
"""
import collections
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dice import COLORS, EV_REROLL, roll

GAMES = 20000
BASE_TARGET = 0
HEALTH = 5
REC_BASE = 3
ATTEMPTS = 9
BANISH = 2
DECK = (4, 4, 4)          # Exhibits per type: Knowledge, Physical, Cover-Up
TIER3 = True
BURN = True               # Cover-Up removes a card face down before shuffling
RESHUFFLE = True          # ...and then shuffles the discards back in
COMBO = 3                 # dice a Knowledge demand requires
COMBO_PENALTY = 1         # Suspicion for failing to supply them
LIKENESS = "random"       # "common" | "mid" | "rare" | "random"
CAP = 0                   # 0 = the run is bounded only by the deck; else
                          # the council gives up after this many Exhibits
EXPOSED = 0               # Suspicion if a likeness run finds NO match at
                          # all - the council goes through every Exhibit and
                          # none of them looks like you. The burn can remove
                          # the last matching Exhibit, so this is the
                          # disaster that deck knowledge would warn you of.
CHOICE = 1                # Exhibits laid face up for the player to pick
                          # among. 1 is the design as Jon described it;
                          # more than 1 gives information a SECOND lever,
                          # which is the thing being tested
TYPES = ("Knowledge", "Physical", "Cover-Up")

# The colour a Knowledge Exhibit names as its subject, by the card's value.
SUBJECT = {2: "yellow", 3: "green", 4: "blue", 5: "purple"}


def fresh():
    # 20 Strong's pool is 4 each of purple, blue, green and yellow plus a
    # SINGLE red - 17 unit dice (General Rules, p.7). Earlier prototypes used
    # 3 each plus two reds, which made red twice as common as it is and the
    # cheap colours scarcer; both matter here, because the design turns on
    # which colours you hold.
    return [c for c in COLORS for _ in range(4)] + ["red"]


def exhibit_deck(rng):
    """The Exhibits the campaign produced, as (type, value). Counts are
    fixed so the finale can be pitched; the campaign sets the VALUES, which
    is what keeps the deck personal without swinging difficulty 30 points -
    the calibration problem finale8 ran into."""
    k, p, c = DECK
    deck = [("Knowledge", 2)] * k
    pool = [2, 3, 3, 4, 2, 2, 3, 3, 2, 3, 3, 2, 4]
    if TIER3:
        pool += [4, 4, 5, 4, 5, 4]
    deck += [("Physical", rng.choice(pool + [5])) for _ in range(p)]
    deck += [("Cover-Up", 4 if rng.random() < 0.65 else 2) for _ in range(c)]
    rng.shuffle(deck)
    return deck


def pick_dossier(deck, rng):
    """The Target on your Dossier - who you are pretending to be. How many
    Exhibits share it IS your likeness: a common value means you resemble
    the member and the council finds a match quickly."""
    counts = collections.Counter(v for _, v in deck)
    order = sorted(counts, key=lambda v: -counts[v])
    if LIKENESS == "common":
        return order[0]
    if LIKENESS == "rare":
        return order[-1]
    if LIKENESS == "mid":
        return order[len(order) // 2]
    return rng.choice(sorted(counts))


class Game(object):
    def __init__(self, rng, counts=True):
        self.rng = rng
        self.deck = exhibit_deck(rng)
        self.origin = collections.Counter(self.deck)
        self.seen = collections.Counter()       # Exhibits the player saw
        self.discard = []
        self.dossier = pick_dossier(self.deck, rng)
        self.exposed = False
        self.available, self.exhausted = fresh(), []
        self.hp, self.suspicion = HEALTH, 0
        self.counts = counts
        self.at = 0

    # -- what the player believes is still in the deck ------------------
    def believed(self):
        """A perfect counter knows the opening composition and everything
        flipped, so it knows what is left - except for cards burned face
        down, which it can only account for by scaling. Someone who never
        counts just reasons from the opening composition all game."""
        if not self.counts:
            return collections.Counter(self.origin)
        left = collections.Counter(self.origin)
        left.subtract(self.seen)
        left = +left                            # drop zero and negative
        return left or collections.Counter(self.origin)

    def match_odds(self):
        """Expected Exhibits flipped before one matches the Dossier, drawing
        without replacement: (N+1)/(K+1). The counter's K is scaled by what
        it believes is left, to account for burned cards it cannot see."""
        left = self.believed()
        k = sum(c for (_, v), c in left.items() if v == self.dossier)
        if self.counts:
            # Scale by the real deck size: cards burned face down are gone
            # but cannot be identified, so they dilute what is believed.
            believed = max(1, sum(left.values()))
            n = max(1, len(self.deck))
            k = k * float(n) / believed
        else:
            n = max(1, sum(left.values()))
        return (n + 1.0) / (k + 1.0)

    def expected_value(self):
        """What a plain Exhibit flip is worth, by belief."""
        src = self.believed()
        tot = max(1, sum(src.values()))
        return sum(v * c for (_, v), c in src.items()) / float(tot)

    # -- deck handling --------------------------------------------------
    def refill(self):
        if not self.deck and self.discard:
            self.deck, self.discard = self.discard, []
            self.rng.shuffle(self.deck)

    def flip(self):
        self.refill()
        if not self.deck:
            return None
        card = self.deck.pop()
        self.seen[card] += 1
        self.discard.append(card)
        return card

    def cover_up(self):
        """Remove the top Exhibit face down, then shuffle the discards back
        into a new deck. The burned card is never seen by anyone."""
        if BURN:
            self.refill()
            if self.deck:
                self.deck.pop()                 # gone, and unseen
        if RESHUFFLE:
            self.deck += self.discard
            self.discard = []
            self.rng.shuffle(self.deck)
            self.seen = collections.Counter()   # the count is worthless now

    def likeness_run(self):
        """Flip until an Exhibit matches the Dossier. The COUNT is the
        shroud. One pass at most, so it is bounded by the deck."""
        flipped, found = 0, False
        limit = len(self.deck) + len(self.discard)
        if CAP:
            limit = min(limit, CAP)
        while flipped < max(1, limit):
            card = self.flip()
            if card is None:
                break
            flipped += 1
            if card[1] == self.dossier:
                found = True
                break
        self.exposed = not found
        return flipped

    def recover(self):
        rec = max(0, REC_BASE - self.suspicion)
        self.exhausted.sort(key=lambda c: EV_REROLL[c])
        for _ in range(min(rec, len(self.exhausted))):
            self.available.append(self.exhausted.pop())


def take(pool, want, order=None):
    """Commit dice until expected hits cover `want`."""
    seq = sorted(pool, key=lambda c: -EV_REROLL[c]) if order is None else order
    got, chosen = 0.0, []
    for c in seq:
        if got >= want:
            break
        chosen.append(c)
        got += EV_REROLL[c]
    return chosen


def resolve(chosen, want, rng):
    vals = [roll(c, rng) for c in chosen]
    hits = sum(vals)
    if hits < want:                             # STR 2: one reroll of misses
        hits += sum(roll(chosen[i], rng)
                    for i, v in enumerate(vals) if v == 0)
    return hits


def play(rng, counts=True, pad=1.0, hoard="off"):
    g = Game(rng, counts)
    for g.at in range(ATTEMPTS):
        if CHOICE > 1:
            # Lay several Exhibits face up and take the one whose demand
            # looks cheapest from what you believe is left. The ones you
            # pass over go to the bottom of the deck.
            up = [g.flip() for _ in range(CHOICE)]
            up = [c for c in up if c is not None]
            if not up:
                break
            cost = {}
            for card in up:
                cost[card] = (g.match_odds() if card[0] == "Physical"
                              else g.expected_value())
                if card[0] == "Knowledge":
                    col = SUBJECT.get(card[1], "yellow")
                    short = max(0, COMBO - g.available.count(col))
                    cost[card] += short * COMBO_PENALTY
            demand = min(up, key=lambda c: cost[c])
            for card in up:
                if card is not demand:
                    g.deck.insert(0, card)
                    if card in g.discard:       # a refill may have moved it
                        g.discard.remove(card)
        else:
            demand = g.flip()
        if demand is None:
            break
        base = BASE_TARGET + g.suspicion
        chosen = []

        if demand[0] == "Cover-Up":
            g.cover_up()

        if demand[0] == "Knowledge":
            # The demand names a subject colour and wants COMBO of them.
            colour = SUBJECT.get(demand[1], "yellow")
            have = [c for c in g.available if c == colour][:COMBO]
            chosen += have
            if len(have) < COMBO:
                g.suspicion += COMBO_PENALTY
                base = BASE_TARGET + g.suspicion

        # What the player expects the shroud to be, from what they believe
        # is left in the deck.
        if demand[0] == "Physical":
            expect = g.match_odds()
        else:
            expect = g.expected_value()
        want = base + pad * expect

        spare = [c for c in g.available if c not in chosen]
        if hoard != "off":
            # Hold back dice of the colours a Knowledge demand could still
            # call for, so the combination can be supplied later.
            need = set(SUBJECT.values())
            keep, rest = [], []
            for c in sorted(spare, key=lambda c: -EV_REROLL[c]):
                if c in need and keep.count(c) < COMBO and hoard == "on":
                    keep.append(c)
                else:
                    rest.append(c)
            order = rest + keep
        else:
            order = sorted(spare, key=lambda c: -EV_REROLL[c])

        got = sum(EV_REROLL[c] for c in chosen)
        chosen += take(spare, max(0.0, want - got), order)

        hits = resolve(chosen, want, rng)
        for c in chosen:
            g.available.remove(c)
            g.exhausted.append(c)

        g.exposed = False
        shroud = (g.likeness_run() if demand[0] == "Physical"
                  else (g.flip() or ("", 0))[1])
        target = base + shroud
        if g.exposed and EXPOSED:
            g.suspicion += EXPOSED      # nothing in the file looks like you

        if hits < target:
            g.suspicion += 1
            if len(g.available) >= BANISH:
                g.available.sort(key=lambda c: EV_REROLL[c])
                for _ in range(BANISH):
                    g.available.pop(0)
            else:
                g.hp -= 1
                if g.hp <= 0:
                    return False
        g.recover()
    return g.hp >= 1


KW = ("counts", "pad", "hoard")


def run(games=GAMES, seed=11, **over):
    kw = {k: over.pop(k) for k in list(over) if k in KW}
    saved = {k: globals()[k] for k in over}
    globals().update(over)
    rng = random.Random(seed)
    try:
        return 100.0 * sum(1 for _ in range(games) if play(rng, **kw)) / games
    finally:
        globals().update(saved)


def shroud_sample(games=8000, seed=3, **over):
    """What the likeness run actually produces, as a distribution."""
    saved = {k: globals()[k] for k in over}
    globals().update(over)
    rng = random.Random(seed)
    out = []
    try:
        for _ in range(games):
            g = Game(rng)
            for g.at in range(ATTEMPTS):
                if g.flip() is None:
                    break
                out.append(g.likeness_run())
                g.recover()
        return out
    finally:
        globals().update(saved)


if __name__ == "__main__":
    print("PROTOTYPE - the Dossier, the Exhibit deck, and the likeness run")
    print("=" * 76)
    print("%d finales a cell. %d Exhibits, %d per type, 9 attempts."
          % (GAMES, sum(DECK), DECK[0]))

    print()
    print("1. WHAT THE LIKENESS RUN PRODUCES")
    print("   It replaces a printed shroud of 2-5, so it has to land in")
    print("   roughly that range or the economy needs rescaling.")
    print("   %-18s %7s %7s %7s %7s %9s"
          % ("likeness", "mean", "p25", "p75", "worst", "share >5"))
    for lab in ("common", "mid", "rare", "random"):
        s = sorted(shroud_sample(LIKENESS=lab))
        q = lambda f: s[int(f * (len(s) - 1))]
        print("   %-18s %7.2f %7d %7d %7d %8.1f%%"
              % (lab, sum(s) / float(len(s)), q(.25), q(.75), s[-1],
                 100.0 * sum(1 for x in s if x > 5) / len(s)))
        sys.stdout.flush()

    print()
    print("2. DOES COUNTING PAY NOW? - the point of the prototype")
    print("   finale8's answer was +1.0 at best, which was noise. A counter")
    print("   here knows what is left and so knows whether the next")
    print("   likeness run is short or ruinous.")
    print("   %-18s %10s %10s %8s"
          % ("likeness", "counts", "never", "worth"))
    for lab in ("common", "mid", "rare", "random"):
        a = run(LIKENESS=lab, counts=True)
        b = run(LIKENESS=lab, counts=False)
        print("   %-18s %9.1f%% %9.1f%% %+7.1f" % (lab, a, b, a - b))
        sys.stdout.flush()

    print()
    print("3. WHAT THE COVER-UP EFFECT COSTS")
    print("   Burning a card face down and reshuffling are separable. A")
    print("   reshuffle only resets memory; the burn puts uncertainty into")
    print("   the deck that no amount of attention recovers.")
    print("   %-28s %10s %10s %8s"
          % ("Cover-Up does", "counts", "never", "worth"))
    for lab, over in (("nothing", {"BURN": False, "RESHUFFLE": False}),
                      ("reshuffles only", {"BURN": False,
                                           "RESHUFFLE": True}),
                      ("burns only", {"BURN": True, "RESHUFFLE": False}),
                      ("burns and reshuffles", {"BURN": True,
                                                "RESHUFFLE": True})):
        a = run(counts=True, **over)
        b = run(counts=False, **over)
        print("   %-28s %9.1f%% %9.1f%% %+7.1f" % (lab, a, b, a - b))
        sys.stdout.flush()

    print()
    print("4. THE KNOWLEDGE COMBINATION")
    print("   The demand wants %d dice of one colour. `hoard` keeps a" % COMBO)
    print("   spread available against that; `off` spends whatever is best.")
    print("   If hoarding pays, the demand has created a real decision")
    print("   about pool composition rather than pool size.")
    print("   %-22s %10s %10s %8s"
          % ("dice demanded", "spend best", "hoard", "delta"))
    for n in (0, 2, 3, 4):
        a = run(COMBO=n, hoard="off")
        b = run(COMBO=n, hoard="on")
        print("   %-22s %9.1f%% %9.1f%% %+7.1f"
              % ("%d dice" % n, a, b, b - a))
        sys.stdout.flush()

    print()
    print("5. THE PITCH, and how much the likeness swings it")
    print("   %-26s %9s %9s %9s %9s"
          % ("pitch", "common", "mid", "rare", "swing"))
    for base in (0, 1, 2):
        for p in (1.0, 1.25):
            ws = [run(BASE_TARGET=base, pad=p, LIKENESS=l)
                  for l in ("common", "mid", "rare")]
            print("   %-26s %8.1f%% %8.1f%% %8.1f%% %8.1f"
                  % ("base %d, pad x%.2f" % (base, p), ws[0], ws[1], ws[2],
                     max(ws) - min(ws)))
            sys.stdout.flush()

    print()
    print("6. THE DIALS")
    print("   %-30s %9s" % ("dial", "win"))
    for label, over in (("as built", {}),
                        ("16 Exhibits, 5/5/6", {"DECK": (5, 5, 6)}),
                        ("9 Exhibits, 3/3/3", {"DECK": (3, 3, 3)}),
                        ("no Tier III values", {"TIER3": False}),
                        ("REC 2 not 3", {"REC_BASE": 2}),
                        ("4 Health not 5", {"HEALTH": 4}),
                        ("6 Health not 5", {"HEALTH": 6}),
                        ("combination costs 2 Suspicion",
                         {"COMBO_PENALTY": 2})):
        print("   %-30s %8.1f%%" % (label, run(**over)))
        sys.stdout.flush()
