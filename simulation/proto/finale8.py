"""PROTOTYPE: finale6's one rule, plus one clause per domain that changes
WHICH DICE are good - not how the check resolves.

    python proto/finale8.py

Exploratory. The brief, from Jon:

    "The previous design was much more targeted... I want the imposter
    scenario to be a fun offshoot. It should be playable quickly, but offer
    enough of a puzzle that people would want to keep coming back to it."

finale7 answered the wrong question. It gave each domain its own RESOLUTION
PROCEDURE - a queue that backs up, a track that hits back, an allocation
phase with its own failure threshold - and measured a 64.8-point gap on the
Tyrant track. A 64.8-point gap is not depth, it is a tutorial: one line
dominates so completely that you learn it in a single play and the
encounter is solved forever. Worse, because a standing track was an instant
loss, the track pre-empted the other two - every die was owed to it first -
which is why all three wanted the same hedge. Three mechanisms, one
strategy, triple the rules.

So this prototype keeps finale6 EXACTLY - one council deck of 18 cards, one
shroud flip per attempt, Target = base + Suspicion + the flipped card's
value + MATCH_BONUS if its domain matches the gate - and adds one clause per
domain, each a single sentence, each touching only how the committed dice
SCORE:

    Physical   you get no Strategy reroll. The Tyrant does not let you take
               a swing back.
    Knowledge  name a colour before you commit; those dice are rerolled
               until they hit. You study a subject until you have it.
    Cover-Up   split your committed dice into three Elements; at most one
               may come up empty, or the alibi comes apart.

WHY THIS SHOULD BE A PUZZLE AND finale6 WAS NOT. finale6's nine attempts all
asked the same question in the same currency - how many expected hits do I
need - and more dice always answered it, so one hedge solved the scenario.
These three clauses reorder the pool, and Physical's order is the EXACT
INVERSION of Knowledge's:

    Physical   (plain EV, no reroll)   red 1.17 purple 1.00 blue .83 green .67 yellow .50
    Knowledge  (reroll until it hits)  yellow 1.50 green 1.33 blue 1.25 purple 1.20 red 1.17
    Cover-Up   (P[Element not empty])  red 1.00 purple .97 blue .89 green .75 yellow .56

Red never shows a blank, so it is the best die when you cannot reroll and
the WORST die when you may reroll freely. Yellow is the reverse. Cover-Up
wants the same reliable dice as Physical but only THREE of them - one per
Element - and is indifferent after that.

So nine gates draw on one 14-die pool that refills at REC, and they want
different dice from it. The decision is which colours to spend now and which
to hold for a domain still to come.

WHAT WAS MEASURED, AND WHAT THE ANSWER WAS. 10000 finales a cell, at
base 1 / match +1 unless a row says otherwise.

WHAT WORKED. The clauses buy a large skill layer. Playing the finale
finale6's way - best dice first at every gate, strongest dice back at REC,
nothing held in reserve - wins 35.9%. Playing it as these clauses ask wins
59.9%. That +24.0 is the policy gap, against about +3.7 for the same
measurement with all three clauses switched off, which is finale6's own
residual. Where it comes from, by removing one clause at a time:

    Knowledge's grind      13.2 of the 24.0
    Cover-Up's Elements     9.1
    Physical's no-reroll    1.4

Naming the colour is the sharpest single moment in the design, and it is a
trap with a lesson in it. The clause rewards the blank-prone dice, so the
instinct every 20 Strong player has - name your best colour - is the worst
line on the board: naming red wins 41.9%, naming purple 43.0%, and naming
by what the clause actually buys you wins 59.9%. An 18-point lesson that
you learn once and never forget, which is exactly the right shape for a
short scenario.

And the thing finale7 could not do: the hedge differs by clause. Pin one
domain's hedge and leave the others adaptive, and Knowledge and Physical
both peak at q0.75 while Cover-Up climbs to q1.00 - and Physical falls off
a CLIFF at q1.00, 58.4% to 48.1%. Pushing more dice at a gate where you
cannot reroll does not buy reliability, it just drains the pool for the
gates after it. finale7's version of this table picked q1.00 in every row.
That cliff is why Physical's clause is worth keeping even though it carries
only 1.4 of the skill gap: the gap measures how much better a good player
does, and the cliff measures how much a single bad decision costs. They are
not the same thing and this clause scores on the second.

WHAT DID NOT WORK, kept because it is the finding. Neither of the two
candidate state-dependent decisions is state-dependent:

    reservation  holding another domain's colours back is worth +7.6, but
                 no conditional rule beats flat "always hold three back".
                 `safe`, `early`, `makeable` and `flush` all read the board
                 and all tie it or lose. A procedure, not a puzzle.
    recovery     board-reading at REC wins 59.9% and the best fixed colour
                 priority - red, purple, blue, green, yellow - wins 59.6%.
                 A tie. Which fixed order you pick is worth 4.0 points, so
                 the rule matters; reading the board on top of it does not.

So every decision in this finale is a static policy. Learn "route by the
clause, name by what the clause buys, hold three back, take reds first,
and never hedge a Physical gate to the top" and you have solved the
scenario's strategy. What differs between plays is the INPUTS - the deck
the campaign built and the order the gates come in - not the policy.
Whether that is enough to bring people back is a design judgement and not
something these runs can settle.

THE CALIBRATION PROBLEM. The council deck is whatever the campaign
produced, and its mix swings the result 19.1 points: a Physical-heavy deck
wins 48.5% and a Knowledge-heavy one 67.6%, same player, same dice. Good
for variety, bad for pitching the thing to a single number. That has to be
solved - most likely by scaling the base Target to the mix - before the
rate below means anything.

    pitch: base 0 / match +3 wins 57.0% on an even deck (20000 games),
    inside the published 47-57% community band - but 44.4% on a
    Physical-heavy deck and 74.5% on a Knowledge-heavy one, so the swing
    is WIDER at this pitch than at the one measured above, not narrower.

ONE MEASUREMENT LIMITATION. GRIND_CAP is not monotonic at intermediate
values - one reroll 43.4%, three rerolls 39.4%, unlimited 59.9% - which no
mechanic can be, since extra free rerolls cannot hurt a player. It is the
policy: it values a named die by expectation alone, and at a middling cap a
named yellow still blanks about a fifth of the time, so the policy commits
too few of them. The rule worth printing is the unlimited one anyway, and
it is also the shortest: reroll that colour until it hits. Read the
GRIND_CAP rows in section 9 as a property of this harness, not of the
design.

SIMPLIFICATIONS: core economy only - no Scenario texts, no colour clauses,
no avoid rule. Read the gaps, not the absolute rates.
"""
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import finale6
from dice import COLORS, EV, EV_REROLL, FACES, roll

GAMES = 10000
BASE_TARGET = 1
MATCH_BONUS = 1
HEALTH = 5
REC_BASE = 3
ATTEMPTS = 9
BANISH = 2
TIER3 = True
MIX = None             # None = finale6's even 6/6/6 deck; else (K, P, C) counts
FLIPS = 1              # shroud cards turned over per attempt
FLIP_MODE = 'sum'      # 'sum' = every flip adds; 'mean' = the average of
                       # them, which holds difficulty fixed while the deck
                       # is consumed faster - the control that isolates
                       # INFORMATION from DIFFICULTY
SPIKY = False          # a mostly-cheap deck with a few disasters, same mean
DOMAINS = ("Knowledge", "Physical", "Cover-Up")

GRIND_CAP = 20         # rerolls of a named die; 20 is "until it hits"
GROUPS = 3             # Cover-Up's Elements
MIN_HITS = 2           # hits an Element needs to hold up
EMPTY_ALLOWED = 1      # ...and this many Elements may fall short anyway
NO_REROLL = True       # Physical's clause
GRIND = True           # Knowledge's clause
SPLIT = True           # Cover-Up's clause
NEED = 2               # dice of a class held back per domain still to come

# Expected value of a named die, which is rerolled while it shows a blank.
# This MUST follow GRIND_CAP: at cap 3 a yellow is worth 1.20, not 1.50, so a
# policy reading the uncapped 1.50 commits too few dice and loses to playing
# blind. That was the first measurement this prototype produced.
HIT_EV = {c: sum(v for v in FACES[c] if v) / float(len([v for v in FACES[c] if v]))
          for c in FACES}
BLANK = {c: FACES[c].count(0) / 6.0 for c in FACES}


def grind_ev(c):
    return (1.0 - BLANK[c] ** (GRIND_CAP + 1)) * HIT_EV[c]


# P(a lone die of this colour leaves its Element non-empty), with one reroll.
ANCHOR = {c: 1.0 - (FACES[c].count(0) / 6.0) ** 2 for c in FACES}

# Which colours a domain competes for, and so which a future gate wants
# held back. Cover-Up wants the anchors too - it needs three reliable dice -
# so it shares Physical's claim rather than being squeezed from both sides.
CLAIM = {"Physical": ("red", "purple"),
         "Cover-Up": ("red", "purple"),
         "Knowledge": ("yellow", "green")}


def mixed_deck(rng, k, p, c):
    """finale6's deck builder with the counts opened up. A campaign that
    went badly in one game hands the council more of that game's cards, so
    the finale the player walks into is not the same finale every time."""
    deck = [("Knowledge", 2)] * k
    pool = [2, 3, 3, 4, 2, 2, 3, 3, 2, 3, 3, 2, 4]
    if TIER3:
        pool += [4, 4, 5, 4, 5, 4]
    deck += [("Physical", rng.choice(pool + [5])) for _ in range(p)]
    deck += [("Cover-Up", 4 if rng.random() < 0.65 else 2) for _ in range(c)]
    rng.shuffle(deck)
    return deck


def fresh():
    # 20 Strong's pool is 4 each of purple, blue, green and yellow plus a
    # SINGLE red - 17 unit dice (General Rules, p.7). Earlier prototypes used
    # 3 each plus two reds, which made red twice as common as it is and the
    # cheap colours scarcer; both matter here, because the design turns on
    # which colours you hold.
    return [c for c in COLORS for _ in range(4)] + ["red"]


def quantile(vals, q):
    vals = sorted(vals)
    if not vals:
        return 0.0
    return float(vals[int(round(q * (len(vals) - 1)))])


class Game(object):
    """One finale. The council deck and the Suspicion row are finale6's."""

    def __init__(self, rng):
        self.rng = rng
        finale6.TIER3 = TIER3        # the deck builder lives in finale6
        self.deck = (finale6.council_deck(rng) if MIX is None
                     else mixed_deck(rng, *MIX))
        self.discard = []
        if SPIKY:
            self.spike()
        self.available, self.exhausted = fresh(), []
        self.hp, self.suspicion = HEALTH, 0
        self.order = [d for d in DOMAINS for _ in range(3)]
        rng.shuffle(self.order)
        self.at = 0

    def left_total(self):
        return ATTEMPTS - self.at - 1

    def spike(self):
        """Re-shape the deck at the same mean. The printed values average
        about 3.1, so 1s with a few 7s holds the mean while giving a
        counter something worth knowing."""
        out = []
        for d, v in self.deck:
            out.append((d, v))
        total = sum(v for _, v in out)
        hi = max(1, int(round(total / 7.0)))
        vals = [7] * hi + [1] * (len(out) - hi)
        self.rng.shuffle(vals)
        self.deck = [(d, vals[i]) for i, (d, _) in enumerate(out)]

    def left(self, domain):
        """Gates of this domain still to come. Always public knowledge -
        three of each, and you can see which ones you have walked."""
        return self.order[self.at + 1:].count(domain)

    def hedge(self, domain, policy="adaptive"):
        """finale6's hedge, unchanged: a quantile of what the council could
        still flip at this gate, moved by the state."""
        vals = [v + (MATCH_BONUS if d == domain else 0) for d, v in self.deck]
        if not vals:
            return 0.0
        if isinstance(policy, dict):
            policy = policy.get(domain, "adaptive")
        if policy != "adaptive":
            return quantile(vals, float(policy))
        q, rest = 0.50, ATTEMPTS - self.at
        if rest >= 6:
            q += 0.20
        if rest <= 2:
            q -= 0.25
        if self.hp <= 2:
            q += 0.20
        if len(self.available) <= 6:
            q -= 0.30
        return quantile(vals, min(1.0, max(0.0, q)))

    def recover(self, policy="best"):
        """REC already makes the player choose which exhausted dice come
        back. finale6 always took the strongest. With the three clauses in
        play the right answer depends on which gates are still ahead - which
        is the one decision here that cannot be memorised, because it reads
        the board every turn."""
        rec = max(0, REC_BASE - self.suspicion)
        if not rec or not self.exhausted:
            return
        rest = self.order[self.at + 1:]
        if policy == "best":                    # finale6's rule
            key = EV_REROLL
        elif policy == "cheap":
            key = {c: -EV_REROLL[c] for c in FACES}
        elif policy == "next":                  # what the very next gate wants
            key = want_key(rest[0]) if rest else EV_REROLL
        elif policy == "demand":                # what every gate left wants
            key = {c: 0.0 for c in FACES}
            for d in DOMAINS:
                k = normed(want_key(d))
                for c in key:
                    key[c] += rest.count(d) * k[c]
            if not rest:
                key = EV_REROLL
        elif isinstance(policy, (tuple, list)):
            # A fixed colour priority - the strongest thing a player can do
            # without reading the board. Board-reading has to beat the BEST
            # of these, not just finale6's "strongest dice first".
            key = {c: -i for i, c in enumerate(policy)}
        else:
            key = EV_REROLL
        self.exhausted.sort(key=lambda c: key[c])
        for _ in range(min(rec, len(self.exhausted))):
            self.available.append(self.exhausted.pop())


def name_colour(pool, rule):
    """Which colour the player declares as the subject of the Inquiry."""
    if not pool:
        return None
    if rule == "grind":
        # What the clause is worth is (gain per die) x (dice you hold of
        # that colour). Valuing it per die names a scarce colour and makes
        # the player worse as the clause gets MORE generous, which is how
        # this was found.
        return max(set(pool), key=lambda c:
                   pool.count(c) * (grind_ev(c) - EV_REROLL[c]))
    if rule == "best_ev":               # the naive read: the strongest die
        return max(set(pool), key=lambda c: EV_REROLL[c])
    if rule == "abundant":
        return max(set(pool), key=lambda c: pool.count(c))
    return rule                         # a fixed colour


def want_key(domain):
    """What a die of each colour is worth AT a gate of this domain. This is
    the whole design in one function: Physical reads plain EV because it
    cannot reroll, Knowledge reads the ground value because it rerolls
    freely, Cover-Up reads the chance a lone die keeps an Element alive."""
    if domain == "Physical" and NO_REROLL:
        return EV
    if domain == "Knowledge" and GRIND:
        return {c: grind_ev(c) for c in FACES}
    if domain == "Cover-Up" and SPLIT:
        return ANCHOR
    return EV_REROLL


def normed(key):
    lo, hi = min(key.values()), max(key.values())
    span = (hi - lo) or 1.0
    return {c: (v - lo) / span for c, v in key.items()}


def keys(domain, routed, named):
    """(order_key, value) for this gate. order_key ranks the pool; value is
    what a die is expected to be worth here, for deciding when to stop."""
    if not routed:                      # finale6's one rule for every gate
        return EV_REROLL, EV_REROLL
    if domain == "Physical" and NO_REROLL:
        return EV, EV
    if domain == "Knowledge" and GRIND:
        v = dict(EV_REROLL)
        if named:
            v[named] = grind_ev(named)
        return v, v
    if domain == "Cover-Up" and SPLIT:
        return ANCHOR, EV_REROLL        # rank by reliability, count in hits
    return EV_REROLL, EV_REROLL


def take_dice(pool, want, order_key, value, caps=None, min_dice=0):
    """Greedily commit dice until the expected hits cover `want`. `caps`
    limits how many dice of a reserved colour this gate may touch."""
    caps = dict(caps or {})
    order = sorted(pool, key=lambda c: (-order_key[c], -value[c]))
    take, got = [], 0.0
    for c in order:
        if got >= want and len(take) >= min_dice:
            break
        if c in caps:
            if caps[c] <= 0:
                continue
            caps[c] -= 1
        take.append(c)
        got += value[c]
    return take, got


def reserve_caps(g, domain, pool):
    """How many dice of each colour this gate may spend, given that other
    domains are still to come and want colours of their own."""
    caps = {}
    mine = CLAIM.get(domain, ())
    for other, colours in CLAIM.items():
        if other == domain or not g.left(other):
            continue
        colours = tuple(c for c in colours if c not in mine)
        if not colours:
            continue                    # this gate has the same claim
        have = sum(pool.count(c) for c in colours)
        budget = max(0, have - NEED)    # spend the class down to NEED, no further
        for c in colours:
            caps[c] = min(caps.get(c, budget), budget)
    return caps


def elements(take):
    """One reliable anchor per Element, then the rest spread round-robin."""
    order = sorted(take, key=lambda c: -ANCHOR[c])
    grps = [[] for _ in range(GROUPS)]
    for i, c in enumerate(order):
        grps[i % GROUPS].append(c)
    return grps


def resolve(g, domain, take, want, named):
    """Roll the committed dice under this gate's clause. -1 means the clause
    itself failed, whatever the Target turns out to be."""
    rng = g.rng
    if domain == "Knowledge" and GRIND:
        vals = []
        for c in take:
            v = roll(c, rng)
            if c == named:
                for _ in range(GRIND_CAP):
                    if v:
                        break
                    v = roll(c, rng)
            vals.append(v)
        hits = sum(vals)
        if hits < want:                 # STR 2, on the dice not being ground
            for i, v in enumerate(vals):
                if v == 0 and take[i] != named:
                    hits += roll(take[i], rng)
        return hits
    if domain == "Physical" and NO_REROLL:
        return sum(roll(c, rng) for c in take)
    if domain == "Cover-Up" and SPLIT:
        grps = elements(take)
        vals = [[roll(c, rng) for c in grp] for grp in grps]
        short = lambda: sum(1 for v in vals if sum(v) < MIN_HITS)
        if sum(sum(v) for v in vals) < want or short() > EMPTY_ALLOWED:
            for gi, grp in enumerate(grps):
                for di, c in enumerate(grp):
                    if vals[gi][di] == 0:
                        vals[gi][di] = roll(c, rng)
        if short() > EMPTY_ALLOWED:
            return -1                   # the alibi came apart
        return sum(sum(v) for v in vals)
    vals = [roll(c, rng) for c in take]
    hits = sum(vals)
    if hits < want:
        hits += sum(roll(take[i], rng) for i, v in enumerate(vals) if v == 0)
    return hits


def hold(g, reserve, want, pool, order_key, value, min_dice, domain):
    """Do you hold the other domains' colours back at this gate, or strip
    the pool to make this one? The pure rules are `off` and `always`; the
    rest read the board, and whether any of them beats both pure rules is
    the measurement that decides whether this is a puzzle or a procedure."""
    if reserve == "off":
        return False
    if reserve == "always":
        return True
    if reserve == "early":              # protect the pool while it still pays
        return g.left_total() >= 4
    if reserve == "late":               # the control: the other way round
        return g.left_total() < 4
    if reserve == "safe":               # stop insuring once Health is short
        return g.hp > 2
    if reserve == "makeable":
        # Hold back only if this gate can still be made without them.
        _, got = take_dice(pool, want, order_key, value,
                           reserve_caps(g, domain, pool), min_dice)
        return got >= want
    if reserve == "flush":
        # Read both: protect the pool early, and never insure a gate you
        # cannot pay for anyway.
        if g.hp <= 2:
            return False
        return g.left_total() >= 3 and len(pool) >= 5
    return False


def play(rng, routed=True, reserve="always", named_rule="grind",
         hedging="adaptive", recov="demand"):
    g = Game(rng)
    for g.at in range(ATTEMPTS):
        domain = g.order[g.at]
        base = BASE_TARGET + g.suspicion
        want = base + g.hedge(domain, hedging)
        pool = g.available

        named = name_colour(pool, named_rule) if domain == "Knowledge" else None
        order_key, value = keys(domain, routed, named)
        min_dice = (GROUPS * MIN_HITS) if (domain == "Cover-Up" and SPLIT) \
            else 0

        caps = None
        if hold(g, reserve, want, pool, order_key, value, min_dice, domain):
            caps = reserve_caps(g, domain, pool)
        take, _ = take_dice(pool, want, order_key, value, caps, min_dice)

        hits = resolve(g, domain, take, want, named)
        for c in take:
            g.available.remove(c)
            g.exhausted.append(c)

        target, shown = base, []
        for _ in range(FLIPS):
            if not g.deck:                  # the council shuffles and goes on
                g.deck, g.discard = g.discard, []
                g.rng.shuffle(g.deck)
            if not g.deck:
                break
            card = g.deck.pop()
            g.discard.append(card)
            shown.append(card[1] + (MATCH_BONUS if card[0] == domain else 0))
        if shown:
            target += (sum(shown) if FLIP_MODE == 'sum'
                       else int(round(float(sum(shown)) / len(shown))))

        if hits < 0 or hits < target:
            g.suspicion += 1
            if len(g.available) >= BANISH:     # dice first, worth 9-13 pts
                g.available.sort(key=lambda c: EV_REROLL[c])
                for _ in range(BANISH):
                    g.available.pop(0)
            else:
                g.hp -= 1
                if g.hp <= 0:
                    return False
        g.recover(recov)
    return g.hp >= 1


KW = ("routed", "reserve", "named_rule", "hedging", "recov")


def run(games=GAMES, seed=11, **over):
    kw = {k: over.pop(k) for k in list(over) if k in KW}
    saved = {k: globals()[k] for k in over}
    globals().update(over)
    rng = random.Random(seed)
    try:
        return 100.0 * sum(1 for _ in range(games) if play(rng, **kw)) / games
    finally:
        globals().update(saved)


def control(base, bonus, games=GAMES, seed=11):
    """finale6 itself, at the same pitch, as the control."""
    return finale6.run("adaptive", games=games, seed=seed,
                       BASE_TARGET=base, MATCH_BONUS=bonus)


if __name__ == "__main__":
    FULL = dict(reserve="always", recov="demand", NEED=3)
    BAR = "=" * 76

    print("PROTOTYPE - finale6 plus one clause per domain, on the dice")
    print(BAR)
    print("%d finales a cell. Same council deck, same 14 dice, same"
          % GAMES)
    print("Suspicion row as finale6. The only change is how dice score.")

    print()
    print("1. WHAT THE CLAUSES COST IN DIFFICULTY")
    print("   finale6 is the control - literally the same module, called.")
    print("   %-22s %10s %10s %9s" % ("pitch", "finale6", "finale8",
                                      "delta"))
    for base, bonus in ((0, 1), (1, 1), (0, 2), (1, 2), (0, 3), (1, 3)):
        c = control(base, bonus)
        w = run(BASE_TARGET=base, MATCH_BONUS=bonus, **FULL)
        print("   base %d, match +%-12d %9.1f%% %9.1f%% %+8.1f"
              % (base, bonus, c, w, w - c))
        sys.stdout.flush()

    print()
    print("2. IS THERE A ROUTING DECISION, AND DOES IT COMPOUND?")
    print("   blind uses finale6's single rule - best dice first, every")
    print("   gate. routed reads the pool by the gate's own clause. The")
    print("   columns are the other lever: what you take back at REC.")
    print("   %-26s %13s %15s %8s"
          % ("", "REC: strongest", "REC: reads ahead", "delta"))
    for label, routed in (("spend blind", False), ("spend routed", True)):
        x = run(routed=routed, recov="best", reserve="always", NEED=3)
        y = run(routed=routed, recov="demand", reserve="always", NEED=3)
        print("   %-26s %12.1f%% %14.1f%% %+7.1f"
              % (label, x, y, y - x))
        sys.stdout.flush()
    lo = run(routed=False, recov="best", reserve="off")
    hi = run(routed=True, **FULL)
    print("   finale6's way %.1f%%, this way %.1f%%  ->  the whole skill"
          % (lo, hi))
    print("   layer is worth %+.1f points" % (hi - lo))

    print()
    print("3. DOES EACH CLAUSE EARN ITS KEEP?")
    print("   Each row removes one clause and re-measures the gap between")
    print("   blind and skilled play. A clause whose removal leaves the")
    print("   gap alone is dead weight.")
    print("   %-30s %9s %9s %8s"
          % ("clauses in play", "blind", "skilled", "gap"))
    for label, off in (("all three", {}),
                       ("without Physical no-reroll",
                        {"NO_REROLL": False}),
                       ("without Knowledge grind", {"GRIND": False}),
                       ("without Cover-Up Elements", {"SPLIT": False}),
                       ("none - finale6 by another road",
                        {"NO_REROLL": False, "GRIND": False,
                         "SPLIT": False})):
        b = run(routed=False, recov="best", reserve="off", **off)
        r = run(routed=True, **dict(FULL, **off))
        print("   %-30s %8.1f%% %8.1f%% %+7.1f" % (label, b, r, r - b))
        sys.stdout.flush()

    print()
    print("4. IS NAMING THE COLOUR A DECISION?")
    print("   The clause rewards the blank-prone dice, which is the")
    print("   opposite of what a 20 Strong player's instincts say.")
    print("   %-24s %9s" % ("names", "win"))
    for rule in ("grind", "abundant", "best_ev", "yellow", "green",
                 "blue", "purple", "red"):
        print("   %-24s %8.1f%%" % (rule, run(named_rule=rule, **FULL)))
        sys.stdout.flush()

    print()
    print("5. DO THE CLAUSES WANT DIFFERENT PLAY? - the headline")
    print("   One domain's hedge is pinned to a quantile of what the")
    print("   council could flip; the other two stay adaptive. finale7")
    print("   ran this and every row picked q1.00 - three mechanisms and")
    print("   one strategy. Watch Physical's top column here.")
    QS = ("0.25", "0.50", "0.75", "1.00")
    print("   %-12s" % "pinned" + "".join("%9s" % q for q in QS)
          + "%11s %9s" % ("adaptive", "best"))
    ad = run(**FULL)
    for d in DOMAINS:
        row = [run(hedging={d: q}, **FULL) for q in QS]
        print("   %-12s" % d + "".join("%8.1f%%" % w for w in row)
              + "%10.1f%%" % ad
              + "%9s" % ("q" + QS[row.index(max(row))]))
        sys.stdout.flush()

    print()
    print("6. RESERVATION - a real lever, but a flat rule, not a puzzle")
    print("   Hold N dice of another domain's colours back while that")
    print("   domain still has a gate. off and always are the pure rules;")
    print("   the rest read the board. If none beats always, this is")
    print("   something you learn once and then simply do.")
    MODES = ("off", "always", "early", "late", "safe", "makeable",
             "flush")
    print("   %-12s" % "hold back" + "".join("%10s" % m for m in MODES))
    for nd in (2, 3, 4):
        row = [run(reserve=m, recov="demand", NEED=nd) for m in MODES]
        print("   %-12s" % ("%d dice" % nd)
              + "".join("%9.1f%%" % w for w in row))
        sys.stdout.flush()

    ORDERS = (("red>pur>blu>grn>yel",
               ("red", "purple", "blue", "green", "yellow")),
              ("yel>grn>blu>pur>red",
               ("yellow", "green", "blue", "purple", "red")),
              ("pur>red>blu>grn>yel",
               ("purple", "red", "blue", "green", "yellow")),
              ("finale6: strongest", "best"),
              ("reads the next gate", "next"),
              ("reads every gate left", "demand"))
    print()
    print("7. RECOVERY - which dice you take back at REC")
    print("   REC already makes the player choose; finale6 always took")
    print("   the strongest. A fixed colour priority is the best a player")
    print("   can do without reading the board, so board-reading has to")
    print("   beat the BEST of those, not just finale6's rule.")
    print("   %-24s %9s" % ("rule", "win"))
    for label, o in ORDERS:
        print("   %-24s %8.1f%%"
              % (label, run(recov=o, reserve="always", NEED=3)))
        sys.stdout.flush()

    print()
    print("8. DOES THE CAMPAIGN CHANGE THE PUZZLE? - the replay question")
    print("   The council deck is whatever the campaign produced. If the")
    print("   best rule changes with the mix, every campaign hands you a")
    print("   different finale. Watch the win numbers too: the mix swings")
    print("   difficulty hard, which is a calibration problem.")
    MIXES = (("even 6/6/6", (6, 6, 6)),
             ("Physical-heavy 3/12/3", (3, 12, 3)),
             ("Knowledge-heavy 12/3/3", (12, 3, 3)),
             ("Cover-Up-heavy 3/3/12", (3, 3, 12)),
             ("Physical-light 8/2/8", (8, 2, 8)))
    CAND = list(ORDERS[:3]) + [("reads every gate left", "demand")]
    print("   %-24s" % "deck"
          + "".join("%12s" % l[:11] for l, _ in CAND) + "   best rule")
    for ml, mx in MIXES:
        row = [run(MIX=mx, recov=o, reserve="always", NEED=3)
               for _, o in CAND]
        print("   %-24s" % ml + "".join("%11.1f%%" % w for w in row)
              + "   %s" % CAND[row.index(max(row))][0])
        sys.stdout.flush()

    print()
    print("9. THE DIALS, at the full-skill line")
    print("   %-30s %9s" % ("dial", "win"))
    for label, over in (("as built", {}),
                        ("Cover-Up: 2 Elements", {"GROUPS": 2}),
                        ("Cover-Up: 4 Elements", {"GROUPS": 4}),
                        ("Knowledge: 1 reroll only", {"GRIND_CAP": 1}),
                        ("Knowledge: 3 rerolls", {"GRIND_CAP": 3}),
                        ("Cover-Up: 1 hit an Element", {"MIN_HITS": 1}),
                        ("Cover-Up: 3 hits an Element", {"MIN_HITS": 3}),
                        ("Cover-Up: none may fall short",
                         {"EMPTY_ALLOWED": 0}),
                        ("REC 2 not 3", {"REC_BASE": 2}),
                        ("4 Health not 5", {"HEALTH": 4}),
                        ("6 Health not 5", {"HEALTH": 6}),
                        ("no tier module", {"TIER3": False})):
        print("   %-30s %8.1f%%" % (label, run(**dict(FULL, **over))))
        sys.stdout.flush()
