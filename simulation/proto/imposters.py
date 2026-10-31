"""The five Imposters: who you are pretending to be, and what it is worth.

    python imposters.py           # every side, at Easy and at a hard rung

A COPY of finale.py carrying a HERO dial, in the manner of proto/bat.py and
proto/finale10.py. finale.py itself has no hero code: it pitches the finale
with no Imposter chosen, and a side is measured as a delta against that.

THE ROSTER AS IT SHIPS. 3000 finales a cell x 5 seeds, against 50.7% at
Easy and 22.4% at rung 13 (3/4/3/3 yellow/green/blue/purple exhausted).

  Imposter     side                 when            Easy  rung13  scales
  Archivist    Cross-Referenced     passive         +0.8    +0.8    -0.0
  Archivist    Precedent            once/Scenario   +2.5    +2.6    +0.1
  Understudy   Open Audition        once/Scenario   +4.0    +5.0    +1.0
  Understudy   Second Chair         twice/Scenario  +3.3    +5.1    +1.8
  Usher        Early Admittance     once/Scenario   +4.2    +2.2    -2.0
  Usher        Double Doors         once/Scenario   +4.3    +1.4    -2.9
  Porter       Sleight of Hand      once/session    +1.8    -0.3    -2.1
  Porter       Heavy Lifting        once/Scenario   +1.2    +2.7    +1.5
  Steward      Requisition          once/Scenario   +3.5    +5.4    +1.9
  Steward      Standing Order       once/Scenario   +3.1    +2.8    -0.3

TWO TESTS, AND A SIDE HAS TO PASS BOTH.

  LEVEL     worth about as much as every other side, so choosing an Imposter
            is a choice of how to play and not of how hard the finale is.
            The band has to be LOW: Easy already starts with nothing
            exhausted, so there is no handicap left to peg it back with.
  UNIFORM   worth about the same at Easy as at a handicapped rung. A side
            that scales is the only pick at Nobulous, which is the fault
            that sank every DICE-priced global Candidate job. Priced in
            attention instead, one does pass both tests - and it is
            Precedent, so it would cost the Archivist its B side. Raised,
            not shipped; see proto/candidates.py.

WHAT THE LADDER DOES with one chosen, 4000 x 5 seeds, against aims of
50 / 40 / 30 / 20:

                               Easy  Standard   Hard  Nobulous
  no Imposter                 50.6%     39.0%  30.6%     19.4%
  weakest  Cross-Referenced   51.8%     40.8%  31.9%     21.0%
  middling Standing Order     54.0%     42.9%  35.0%     23.2%
  strongest Double Doors      55.1%     40.9%  32.3%     19.5%

Two to four points hot, five at worst, and still inside the 47-57% band.
The ladder is NOT re-pegged for it: Easy is already zero dice exhausted, so
pegging it back to 50 would cost "Easy means nothing starts exhausted",
which is worth more than three points.

WHAT CANNOT BE ABILITY SPACE, measured rather than assumed:

  STR, REC, window width   finale.py prices a point of STR at 85 points, REC
            4 inverts the commit decision, and a third colour in the window
            reads 90%. A free third colour EVERY session was measured here
            anyway, as usher_c: +16.1. Double Doors is that same effect for
            one session only, which is +4.3.
  the wheel's PHASE        holding the attention for one session read +11.9.
            finale.py measures the clock's phase as a 27-point swing (8
            sessions 23.8%, 9 sessions 50.5%, 10 sessions 21.8%), so a card
            that re-phases it is a difficulty dial, not an ability.
  dice back, every session nine sessions of one recovered die IS the
            Nobulous handicap. Three sides were built this way and scaled
            +8.3, +15.1 and +18.1. All three were rebuilt as once per
            Scenario, or as a conversion that pays a die to get dice.
            The SIGN of the conversion decides it: Heavy Lifting pays 1 to
            get 2 and reads +1.2, while paying 1 to apply 1 out-of-colour
            die reads -10.1 even gated, because it nets a die DOWN.
  Damage and Health        both dead. Soaking 1 Damage a session read +0.0
            and moving successes between Exhibits read exactly +0.0 -
            successes are conserved, so all it buys is a card falling
            sooner. Under a sensible pace nothing is paid in Health, so
            nothing can be bought with it.
  Target points            not tunable: a point is worth about nothing below
            Target 5 and about +7 across it, because 5 is where an
            Exhibit's Damage doubles.
  giving an Exhibit back   putting one deployed Exhibit on the bottom of the
            Dossier read -25.0. finale.py measures 15 Exhibits at 50.1% and
            16 at 20.6%, so the nine-session clock has no slack: deferring
            one is very close to adding one.
  a card already standing  spending a retained card on an Exhibit deployed
            in an earlier session read -0.7 however it was gated. The pool
            is scarce enough that the card is always worth more held for a
            fresh Exhibit, so breaking that rule is not a gift.

AND ONE LESSON ABOUT MEASURING THEM. A side the model spends
unconditionally measures as its WORST case, not its best. Paying a die for
an out-of-colour die read -14.2 until it was gated on the session actually
needing it, and the Archivist's off-domain card read -3.4 ungated because
the model then spends the pool on small Exhibits and strands the big ones.
Where a real player would hold an ability back, the gate is the model's
stand-in for that judgement, and it is part of the ability.
"""
import collections
import math
import os
import random
import sys

# proto/ is one below simulation/, where dice.py lives.
sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))

from dice import COLORS, EV_REROLL, FACES, roll

GAMES = 6000

# --- the components ---------------------------------------------------------
# Every domain of the Council Test library prints this Target spread, and the
# Exhibit's Target is the printed one minus TARGET_OFFSET.
PRINTED = [8, 8, 8, 9, 9, 9, 10, 10]
TARGET_OFFSET = 5          # printed 8/9/10 -> Exhibit Target 3/4/5
DEAL = 5                   # Exhibits per domain; a 3-tuple deals unevenly
SESSIONS = 9               # the clock. Chosen for its phase: see the header
HEALTH = 5
STRAT = 2                  # Strategy phases per session
# REC 3 rather than 4: the five Reward cards hand back dice for burying
# the right evidence, so the extra recovery is earned instead of given.
# At REC 4 with the Rewards on, throwing every allowed die beat holding
# any back by 8.4 points and the commit decision disappeared.
REC_BASE = 3
BIG = 5                    # an Exhibit at this Target or above deals 2 Damage
CARRY = True               # damage on a standing Exhibit carries over
RESEARCH = True            # the campaign's retained Tier III cards
# How many cards each game carries, NAP / BAT / AoS. The printed cap is 3 a
# game, but AoS's own limit of 2 claims a game binds first, so 8 is the most
# any campaign can carry and the standalone rule deals the same.
# NAP 3, BAT 2, AoS 2. With one value the pool is just a count, and seven
# cards is the count that reads 50.6%. The caps match the economics: a NAP
# Opportunity is worked like an Assignment and apprentices finish about 2.5
# of them, a second BAT Note already costs that game 9 points, and AoS
# limits itself to 2 claims.
RETAIN = (3, 2, 2)
CARD_VALUE = 2             # what one retained card takes off an Exhibit
# Each game lays 6 Tier III cards out, so what you did not claim comes to
# the finale as Candidates. They answer nothing, but this many of them
# discarded buys back one exhausted die, once a session. Uncapped on
# purpose: the COUNT is the limit, and the count is the complement of what
# you claimed. 0 switches the job off.
LAID_OUT = 6
CANDIDATE_COST = 0
# "die"    - discard CANDIDATE_COST Candidates, recover 1 exhausted die
# "target" - discard CANDIDATE_COST Candidates, -1 off a just-deployed Exhibit
# "colour" - discard CANDIDATE_COST Candidates, apply 1 die the attention
#            forbids. Priced in ATTENTION rather than in dice: the wheel is
#            the one scarcity the difficulty ladder does not also spend.
# "reroll" - discard CANDIDATE_COST Candidates, reroll one committed die
#            that applied nothing. Adds no die, so it is bounded by how many
#            you were able to commit in the first place.
# "soak"   - discard CANDIDATE_COST Candidates, prevent 1 Damage
# "cheap"  - discard CANDIDATE_COST Candidates, cheapest of the top 3 of the
#            Dossier to the top
# "front"  - the same, dearest to the top
# "none"   - Candidates do nothing (as it shipped)
CANDIDATE_JOB = "none"
# HOW OFTEN the job may be done in a whole Scenario. 0 is uncapped, which
# is how all six rejected prices were measured - nine sessions, nine uses.
# The cap is the dial those six never varied.
CANDIDATE_USES = 0
# THE IMPOSTER YOU CHOSE. Five two-sided cards, one lever each, and every
# side prints the finale's own 5 HP / 2 STR / 3 REC - the house rule across
# the set is that heroes differ only in ability text (simulation/cards.py).
# None of them touches STR, REC or the width of the attention window: a
# point of STR is worth 85 points, REC 4 inverts the commit decision and a
# three-colour window reads 90%, so those three are not ability space.
HERO = None
ARCHIVIST_USES = 2         # how often Cross-Referenced answers off-domain
HEROES = ("archivist_a", "archivist_b", "understudy_a", "understudy_b",
          "usher_a", "usher_b", "porter_a", "porter_b",
          "steward_a", "steward_b")


def cand_cost(g):
    return CANDIDATE_COST
# THE IMPOSTER STARTS TIRED, and how tired is the difficulty. These dice
# begin exhausted; they return through ordinary recovery, so the handicap
# costs tempo rather than dice and bites hardest early, when the Dossier is
# full. The RULES name them, so there is no player choice here for this
# module to model badly - an earlier version let the model pick the dice and
# picked worse than random at the hard end.
#
# The counts are deliberately SPREAD across the four colours rather than
# taking whole ones, because whole colours collide with the attention wheel.
# The wheel opens on Yellow with a Yellow+Green window, so "4 yellow, 4
# green" empties the only colours sessions 1 and 2 may apply and reads 28.7%
# against 38.4% for the same eight dice taken off the purple end - a
# ten-point swing decided by the wheel's phase rather than by the handicap.
# Spread, the curve is smooth and the two stay independent.
#
# The single red is never exhausted: session 5 allows only Red and Yellow,
# and there is one red die.
#
#   level      y  g  b  p     n    win     aim
#   Easy       0  0  0  0     0   50.6%   +0.6
#   Standard   3  2  2  2     9   39.2%   -0.8
#   Hard       3  3  3  2    11   30.6%   +0.6
#   Nobulous   3  3  4  4    14   19.4%   -0.6
TIRED_COLOURS = ("yellow", "green", "blue", "purple")
LADDER = {"easy": (0, 0, 0, 0), "standard": (3, 2, 2, 2),
          "hard": (3, 3, 3, 2), "nobulous": (3, 3, 4, 4)}
START_TIRED = LADDER["easy"]

DOMAINS = ("Knowledge", "Physical", "Cover-Up")

# THE FIVE REWARD CARDS. Eight of the 24 Council Tests are printed as
# Rewards; these five pay on success in a currency this finale still has,
# and "if you succeed" reads as "when the Exhibit falls". The other three
# (An Unwelcome Embrace, The Night Watchman's Account, Across the Chamber)
# modify an attempt that no longer exists as a unit, and are not restored.
# Measured at +1.3 points, which is why they cost nothing to put back.
REWARDS = {
    "The Chamber Mechanism": ("dice", 2),       # recover 2 exhausted dice
    "The Sedative Ledger": ("dice", 3),         # recover 3
    "The Vote": ("colour", 1),                  # all exhausted of one colour
    "Tracks in the Yard": ("spread", 2),        # 1 each of two colours
    "The Narrow Stair": ("discount", 1),        # next Exhibit deployed: -1
}
PAY_REWARDS = True
# Which game's retained cards answer which domain. Mirrors the category match
# of the superseded finale, scaled from Targets of 8-10 to Targets of 3-5.
ANSWERS = {"Knowledge": "NAP", "Physical": "BAT", "Cover-Up": "AoS"}

# The attention runs weakest to strongest and round again, as Tainted Grail's
# dial does, and starts on yellow. WINDOW is how many colours it covers: the
# colour it points to plus the next one clockwise. Two is the shipped rule.
# One is unplayable at 0.4%, and three inverts the recovery lever, because a
# window that wide makes raw strength beat reading the wheel (90.3%, with
# `best` recovery then ahead of `next`).
WHEEL = ["yellow", "green", "blue", "purple", "red"]
WINDOW = 2


def deck_cards():
    """(name, domain, kind, printed Target) for the 24 Council Tests, read
    from generator/build_nrj.py so the model cannot drift from the cards."""
    import ast
    src = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))), "generator", "build_nrj.py")
    with io.open(src, encoding="utf-8") as f:
        tree = ast.parse(f.read())
    for node in tree.body:
        if (isinstance(node, ast.Assign) and len(node.targets) == 1
                and getattr(node.targets[0], "id", "") == "SCEN"):
            out = []
            for row in node.value.elts:
                v = [e.value for e in row.elts[:4] if isinstance(e, ast.Constant)]
                out.append((v[0], v[1], v[2].split(" - ")[-1], v[3]))
            return out
    raise RuntimeError("SCEN not found in generator/build_nrj.py")


import io                                    # noqa: E402  (deck_cards needs it)

DECK = deck_cards()
BY_DOMAIN = {d: [c for c in DECK if c[1] == d] for d in DOMAINS}


def fresh():
    """4 each of purple, blue, green and yellow plus a SINGLE red: 17 unit
    dice (General Rules of Play, p.7)."""
    return [c for c in COLORS for _ in range(4)] + ["red"]


def window(dial):
    i = WHEEL.index(dial)
    out = [dial]
    for step in (1, -1, 2, -2):
        if len(out) >= WINDOW:
            break
        out.append(WHEEL[(i + step) % 5])
    return set(out)


class Exhibit(object):
    __slots__ = ("domain", "target", "dealt", "locked", "name", "kind")

    def __init__(self, domain, target, name="", kind=""):
        self.domain = domain
        self.name = name
        self.kind = kind
        self.target = target
        self.dealt = 0          # successes carried over from past sessions
        self.locked = []        # dice held on the card, neither side of the pool

    @property
    def damage(self):
        return 2 if self.target >= BIG else 1

    @property
    def left(self):
        return max(0, self.target - self.dealt)


class Card(object):
    """A retained card in the Research Pool."""
    __slots__ = ("game", "value")

    def __init__(self, game, value):
        self.game = game
        self.value = value


def research(rng):
    """The retained Tier III cards, as rules/nrj.html deals them.

    Retained or not, and every retained card is worth the same. The earlier
    scheme paid 2 for a card never spent in its own game and 1 for one that
    was; it was dropped on 2026-10-30 because nothing on the table records
    which a card is, and a campaign can sit for weeks between games.
    """
    if not RESEARCH:
        return []
    out = []
    for game, n in zip(("NAP", "BAT", "AoS"), RETAIN):
        out += [Card(game, CARD_VALUE) for _ in range(n)]
    return out


def dossier(rng):
    """DEAL Exhibits per domain, Targets dealt from the printed spread.

    The counts are fixed so the finale can be pitched to one number; what the
    campaign varies is the Research Pool. finale9 measured a 30-point
    difficulty swing when the campaign set the counts as well, which is a
    scenario nobody can tune.
    """
    out = []
    per = DEAL if isinstance(DEAL, tuple) else (DEAL,) * 3
    for d, n in zip(DOMAINS, per):
        for name, _, kind, p in rng.sample(BY_DOMAIN[d], min(n, len(BY_DOMAIN[d]))):
            out.append(Exhibit(d, p - TARGET_OFFSET, name, kind))
    rng.shuffle(out)
    return out


class Game(object):
    def __init__(self, rng):
        self.rng = rng
        self.deck = dossier(rng)
        self.pool = research(rng)
        self.active = []
        self.available, self.exhausted = fresh(), []
        self.candidates = sum(LAID_OUT - n for n in RETAIN) if RESEARCH else 0
        self.start_tired()
        self.hp = HEALTH
        self.dial = 0
        self.at = 0
        self.discount = 0          # The Narrow Stair, owed to the next deploy
        self.hero = HERO
        self.once = collections.Counter()    # uses this finale
        self.sess = collections.Counter()    # uses this session

    def start_tired(self):
        """The dice rules/nrj.html names for the chosen difficulty."""
        for colour, n in zip(TIRED_COLOURS, START_TIRED):
            for _ in range(n):
                if colour not in self.available:
                    break
                self.available.remove(colour)
                self.exhausted.append(colour)

    # -- the state a policy may read. All of it is face-up on the table ----
    def colour(self):
        return WHEEL[self.dial % 5]

    def next_colour(self, ahead=1):
        return WHEEL[(self.dial + ahead) % 5]

    def sessions_left(self):
        return SESSIONS - self.at

    def pressure(self):
        """Exhibits left to bury per session remaining. Above 1 means the
        clock is winning and you have to take on more."""
        left = len(self.deck) + len(self.active)
        return left / float(max(1, self.sessions_left()))

    # -- the economy ------------------------------------------------------
    def recover(self, policy, n=None):
        rec = REC_BASE if n is None else n
        if not rec or not self.exhausted:
            return
        if policy == "next":                   # the colour coming up
            nxt = self.next_colour()
            key = {c: (10.0 if c == nxt else EV_REROLL[c]) for c in FACES}
        elif policy == "horizon":              # the next two
            a, b = self.next_colour(1), self.next_colour(2)
            key = {c: EV_REROLL[c] for c in FACES}
            key[a] += 20.0
            key[b] += 10.0
        elif policy == "now":
            cur = self.colour()
            key = {c: (10.0 if c == cur else EV_REROLL[c]) for c in FACES}
        else:                                  # "best": the naive rule
            key = {c: EV_REROLL[c] for c in FACES}
        self.exhausted.sort(key=lambda c: key[c])
        for _ in range(min(rec, len(self.exhausted))):
            self.available.append(self.exhausted.pop())

    def pay_reward(self, e):
        """A Reward Exhibit pays as it falls. Rules: rules/nrj.html, "What
        the Council lets slip"."""
        if not PAY_REWARDS:
            return
        pay = REWARDS.get(e.name)
        if not pay:
            return
        how, n = pay
        if how in ("colour", "spread") and not self.exhausted:
            return                 # nothing exhausted: the Reward pays nothing
        if how == "dice":
            self.recover("next", n)
        elif how == "discount":
            self.discount += n
        elif how == "colour":
            # All exhausted dice of ONE colour: take the colour the next
            # session wants, falling back to whichever there is most of.
            want = self.next_colour()
            if want not in self.exhausted:
                want = max(set(self.exhausted), key=self.exhausted.count)
            for c in [c for c in self.exhausted if c == want]:
                self.exhausted.remove(c)
                self.available.append(c)
        elif how == "spread":
            # One die of each of two colours: the next two on the wheel.
            for want in (self.next_colour(1), self.next_colour(2)):
                if want in self.exhausted:
                    self.exhausted.remove(want)
                    self.available.append(want)

    def reward(self, policy):
        """Rose pays for every enemy you deploy, which is what makes taking
        on more than the clock demands worth considering. Measured against
        the alternatives in the prototype: a die 85.0%, Health 57.1%.
        """
        if policy == "health":
            self.hp = min(HEALTH, self.hp + 1)
            return
        if self.exhausted:
            self.recover("next", 1)
        else:
            self.hp = min(HEALTH, self.hp + 1)

    def spend_research(self, fresh_exhibits, policy):
        """A retained card removes 1 from an Exhibit of its own domain, or 2
        if it was never spent in its own game. Only just-deployed Exhibits
        can be answered: once the Council has heard the evidence, producing
        your credentials is too late.
        """
        if policy == "none" or not self.pool:
            return
        for e in sorted(fresh_exhibits, key=lambda e: -e.target):
            while e.target > 1:
                want = ANSWERS[e.domain]
                cands = [c for c in self.pool if c.game == want]
                # The Archivist, Cross-Referenced: a retained card answers an
                # Exhibit of ANY domain, this many times a finale.
                # Gated to the Target 5s, and the gate is load-bearing:
                # ungated this side read -3.4, because the model then spends
                # the pool off-domain on small Exhibits and strands the big
                # ones. No use limit - a Dossier holds about four 5s, so a
                # limit never bound and the card reads shorter without one.
                if (not cands and self.hero == "archivist_a"
                        and e.target >= BIG):
                    cands = list(self.pool)
                if not cands:
                    break
                if policy == "big" and e.target < BIG:
                    break          # hoard everything for the Target 5s
                # Spend the smallest card that still helps, so a 2 is kept
                # for a Target-5 Exhibit of the same domain.
                cards = sorted(cands, key=lambda c: c.value)
                if policy == "big":
                    cards = sorted(cands, key=lambda c: -c.value)
                c = cards[0]
                cut = c.value
                e.target = max(1, e.target - cut)
                self.pool.remove(c)
                if policy != "dump":
                    break          # one card an Exhibit unless told otherwise


def how_many(g, pace):
    """Rose's decision: how many Exhibits to take on this session."""
    room = len(g.deck)
    if not room:
        return 0
    if pace in ("one", "two", "three"):
        return min(room, {"one": 1, "two": 2, "three": 3}[pace])
    if pace == "all":
        return room
    # "ceil" never leaves more behind than the sessions that are left can
    # clear. "clock" rounds the same quantity instead, which looks equivalent
    # and is not - at a pressure just over 1 it deploys one a session, falls
    # quietly behind, and meets the whole remainder in the last session. That
    # made the win rate fall as the clock got LONGER, which is how the
    # rounding was caught; proto/finale10.py's pacing figures carry it.
    if pace == "ceil":
        n = int(math.ceil(len(g.deck) / float(max(1, g.sessions_left()))))
        n -= len(g.active)
    else:
        n = int(round(g.pressure() - len(g.active)))
    if pace == "throttle":
        if g.hp <= 2 and n > 1:
            n -= 1
        if g.hp >= HEALTH and not g.active and room:
            n += 1
    return min(room, max(0, n))


def want_dice(g, pool, policy):
    """How many of the usable dice to commit. An allowed die you commit and
    do not need is simply burned, so this is a lever in its own right - and
    the reason to hold dice back is that next session's colour is already
    visible on the wheel."""
    pool = sorted(pool, key=lambda c: -EV_REROLL[c])
    if policy == "all":
        return pool
    need = sum(e.left for e in g.active)
    margin = 1.0 if (policy == "adaptive" and g.hp <= 2) else 0.0
    out, got = [], 0.0
    for c in pool:
        if got >= need + margin:
            break
        out.append(c)
        got += EV_REROLL[c]
    return out


def session(g, pace, recov, rew, commit, res):
    # Candidates, before anything else: a die bought back now is a die that
    # can be committed this session.
    g.sess.clear()
    # The Usher, Order of Business: once a finale, look at the top three of
    # the Dossier and put them back in any order. The cheapest Exhibits go
    # on top, so the session you spend it on is the one you can finish.

    if (CANDIDATE_JOB == "die" and CANDIDATE_COST and g.exhausted
            and g.candidates >= cand_cost(g)
            and (not CANDIDATE_USES or g.once["cand"] < CANDIDATE_USES)):
        g.once["cand"] += 1
        g.candidates -= cand_cost(g)
        g.recover(recov, 1)
    if (CANDIDATE_JOB in ("cheap", "front") and CANDIDATE_COST
            and len(g.deck) >= 2 and g.candidates >= cand_cost(g)
            and (not CANDIDATE_USES or g.once["cand"] < CANDIDATE_USES)):
        g.once["cand"] += 1
        g.candidates -= cand_cost(g)
        top = g.deck[-3:]
        del g.deck[-3:]
        top.sort(key=lambda e: e.target,
                 reverse=CANDIDATE_JOB == "cheap")
        g.deck += top                 # the end of the list is the top
    taken = []
    for _ in range(how_many(g, pace)):
        e = g.deck.pop()
        if g.discount:                      # The Narrow Stair, if one is owed
            e.target = max(1, e.target - g.discount)
            g.discount = 0
        taken.append(e)
        g.active.append(e)
        g.reward(rew)
        # The Orderly, Second Pair of Hands: the first Exhibit you deploy
        # each session pays twice.
        pass
    g.spend_research(taken, res)
    # The decoupled job: Candidates pay in Target, not in dice, so the job
    # does not fight the exhausted-dice ladder over the same currency.
    if (CANDIDATE_JOB == "target" and CANDIDATE_COST and taken
            and g.candidates >= cand_cost(g)
            and (not CANDIDATE_USES or g.once["cand"] < CANDIDATE_USES)):
        cands = [e for e in taken if e.left > 1]
        if cands:
            e = max(cands, key=lambda e: (e.target >= BIG, e.left))
            e.target -= 1
            g.candidates -= cand_cost(g)
            g.once["cand"] += 1

    ok = window(g.colour())
    # The Usher, Early Admittance: once a finale the window reaches one
    # colour further round the wheel, spent on a session where the dice the
    # window allows cannot cover what is on the table.
    outside = 0
    # The Usher, Double Doors: once a Scenario the window covers a third
    # colour for one session.
    if g.hero == "usher_b" and not g.once["dd"] and g.active:
        if (sum(EV_REROLL[c] for c in g.available if c in ok)
                < sum(e.left for e in g.active)):
            g.once["dd"] = 1
            ok = ok | {g.next_colour(WINDOW)}
    if g.hero == "usher_a" and not g.once["adm"] and g.active:
        need = sum(e.left for e in g.active)
        have = sum(EV_REROLL[c] for c in g.available if c in ok)
        if have < need:
            g.once["adm"] = 1
            outside = 1
    phases = STRAT
    # The Steward, Standing Order: once a finale, a third Strategy phase,
    # spent on the same test - a session the window alone cannot cover.
    if g.hero == "steward_b" and not g.once["str"] and g.active:
        need = sum(e.left for e in g.active)
        have = sum(EV_REROLL[c] for c in g.available if c in ok)
        if have < need:
            g.once["str"] = 1
            phases += 1
    spent = collections.Counter()       # committed from the pool this session
    applied = collections.Counter()     # ...of which these landed on a card
    unapplied = []

    for _ in range(phases):
        if not g.active or all(e.left <= 0 for e in g.active):
            break
        usable = [c for c in g.available if c in ok]
        take = want_dice(g, usable, commit)
        for c in take:
            g.available.remove(c)
            spent[c] += 1
        # The Steward, Requisition: once a session, commit one EXHAUSTED die
        # the window allows. It is already exhausted, so it stays that way -
        # `spent` carries it so the bookkeeping below returns it.
        # The Usher, Early Admittance: up to two dice from outside the
        # window, once a finale.
        # usher_c: the same colour override as Early Admittance, but free
        # and every session instead of once a Scenario.
        if g.hero == "usher_c" and not g.sess["inv"]:
            soon = g.next_colour(WINDOW)
            got = [c for c in g.available if c == soon]
            if got:
                g.sess["inv"] = 1
                c = got[0]
                g.available.remove(c)
                spent[c] += 1
                take = take + [c]
        if (CANDIDATE_JOB == "colour" and CANDIDATE_COST
                and g.candidates >= cand_cost(g)
                and (not CANDIDATE_USES or g.once["cand"] < CANDIDATE_USES)
                and sum(EV_REROLL[c] for c in g.available if c in ok)
                < sum(e.left for e in g.active)):
            pick = [c for c in g.available if c not in ok]
            if pick:
                g.once["cand"] += 1
                g.candidates -= cand_cost(g)
                c = max(pick, key=lambda c: EV_REROLL[c])
                g.available.remove(c)
                spent[c] += 1
                take = take + [c]
        if g.hero == "archivist_b" and not g.once["prec"]:
            pick = [c for c in g.available if c not in ok]
            if pick:
                g.once["prec"] = 1
                c = max(pick, key=lambda c: EV_REROLL[c])
                g.available.remove(c)
                spent[c] += 1
                take = take + [c]
        if outside:
            # Not a free choice of colour: the one the attention reaches
            # next, which is the one the player can see coming.
            soon = g.next_colour(WINDOW)
            extra = [c for c in g.available if c == soon][:outside]
            for c in extra:
                g.available.remove(c)
                spent[c] += 1
            take = take + extra
            outside = 0
        if (g.hero == "steward_a" and not g.once["req"]
                and sum(EV_REROLL[c] for c in g.available if c in ok)
                < sum(e.left for e in g.active)):
            pick = [c for c in g.exhausted if c in ok]
            if pick:
                c = max(pick, key=lambda c: EV_REROLL[c])
                g.exhausted.remove(c)
                spent[c] += 1
                take = take + [c]
                g.once["req"] = 1
        rolling = unapplied + take
        if not rolling:
            break
        unapplied = []
        hits = []
        for c in rolling:
            v = roll(c, g.rng)
            if v:
                hits.append((c, v))
            else:
                unapplied.append(c)
        if (CANDIDATE_JOB == "reroll" and CANDIDATE_COST and unapplied
                and g.candidates >= cand_cost(g)
                and (not CANDIDATE_USES or g.once["cand"] < CANDIDATE_USES)):
            g.once["cand"] += 1
            g.candidates -= cand_cost(g)
            c = max(unapplied, key=lambda c: EV_REROLL[c])
            unapplied.remove(c)
            v = roll(c, g.rng)
            if v:
                hits.append((c, v))
            else:
                unapplied.append(c)
        # The Understudy, Open Audition: once a Scenario, four Candidates
        # reroll EVERY die that applied nothing this Strategy phase.
        if (g.hero == "understudy_a" and not g.once["aud"]
                and len(unapplied) >= 2 and g.candidates >= 4):
            g.candidates -= 4
            g.once["aud"] = 1
            again, unapplied = unapplied, []
            for c in again:
                v = roll(c, g.rng)
                if v:
                    hits.append((c, v))
                else:
                    unapplied.append(c)
        # The Understudy, Second Chair: twice a Scenario, discard 2
        # Candidates to reroll one die that missed.
        if (g.hero == "understudy_b" and g.once["chair"] < 2
                and unapplied and g.candidates >= 2):
            g.candidates -= 2
            g.once["chair"] += 1
            c = max(unapplied, key=lambda c: EV_REROLL[c])
            unapplied.remove(c)
            v = roll(c, g.rng)
            if v:
                hits.append((c, v))
            else:
                unapplied.append(c)
        # Spend the biggest results on whatever is closest to falling, so a
        # Crit is not stranded on a card that needed one success.
        for c, v in sorted(hits, key=lambda x: -x[1]):
            tgt = None
            for e in sorted(g.active, key=lambda e: e.left):
                if e.left > 0:
                    tgt = e
                    break
            if tgt is None:
                unapplied.append(c)
                continue
            tgt.dealt += v
            tgt.locked.append(c)
            applied[c] += 1

    # Every Exhibit still standing deals its Damage.
    hit = sum(e.damage for e in g.active if e.left > 0)
    while (CANDIDATE_JOB == "soak" and CANDIDATE_COST and hit > 0
           and g.candidates >= cand_cost(g)
           and (not CANDIDATE_USES or g.once["cand"] < CANDIDATE_USES)):
        g.once["cand"] += 1
        g.candidates -= cand_cost(g)
        hit -= 1
    g.hp -= hit
    if g.hp <= 0:
        return False

    # Exhaust committed dice that did not land, plus every die held on an
    # Exhibit that has now fallen. Dice on something still standing are
    # neither exhausted nor available - the published rule.
    for c in (spent - applied).elements():
        g.exhausted.append(c)
    buried = [e for e in g.active if e.left <= 0]
    g.active = [e for e in g.active if e.left > 0]
    for e in buried:
        g.exhausted += e.locked
        e.locked = []
    # Rewards pay AFTER the dice come back, so "recover 2" can take the
    # very dice that just buried the card.
    for e in buried:
        g.pay_reward(e)
    # The Porter, Heavy Lifting: once a Scenario, recover 2 exhausted dice -
    # the same wording The Chamber Mechanism already prints. Moving
    # SUCCESSES between Exhibits was measured here first and read exactly
    # 0.0: successes are conserved, so all it buys is a card falling sooner,
    # and Damage does not bind under a sensible pace. Triage died of the
    # same fact.
    if (g.hero == "porter_b" and not g.once["lift"]
            and len(g.exhausted) >= 2 and g.available):
        g.once["lift"] = 1
        drop = min(g.available, key=lambda c: EV_REROLL[c])
        g.available.remove(drop)
        g.exhausted.append(drop)
        g.recover(recov, 2)
    # The Porter, Sleight of Hand: once a session, one die stranded on a
    # standing Exhibit comes back exhausted. The Exhibit keeps its
    # successes, and the die is in time for this session's recovery.
    if g.hero == "porter_a":
        for e in g.active:
            if e.locked:
                g.exhausted.append(e.locked.pop())
                break
    if not CARRY:
        for e in g.active:                  # the control: progress resets
            g.exhausted += e.locked
            e.locked = []
            e.dealt = 0

    g.recover(recov)
    g.dial += 1
    g.at += 1
    return True


def play(rng, pace="clock", recov="horizon", rew="dice", commit="adaptive",
         res="small"):
    g = Game(rng)
    for _ in range(SESSIONS):
        if not g.deck and not g.active:
            return True
        if not session(g, pace, recov, rew, commit, res):
            return False
    return not g.deck and not g.active


KW = ("pace", "recov", "rew", "commit", "res")
DIALS = ("SESSIONS", "DEAL", "HEALTH", "STRAT", "REC_BASE", "BIG", "CARRY",
         "RESEARCH", "RETAIN", "CARD_VALUE", "LAID_OUT",
         "CANDIDATE_COST", "CANDIDATE_JOB", "CANDIDATE_USES",
         "HERO", "ARCHIVIST_USES",
         "START_TIRED", "TARGET_OFFSET", "WINDOW",
         "PAY_REWARDS")


def run(games=GAMES, seed=11, **over):
    kw = {k: over.pop(k) for k in list(over) if k in KW}
    bad = [k for k in over if k not in DIALS]
    if bad:
        raise TypeError("unknown dial(s): %s" % ", ".join(bad))
    saved = {k: globals()[k] for k in over}
    globals().update(over)
    rng = random.Random(seed)
    try:
        return 100.0 * sum(1 for _ in range(games) if play(rng, **kw)) / games
    finally:
        globals().update(saved)


def check_components():
    """The printed Targets this module assumes are the ones on the cards."""
    import ast
    import io
    src = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))), "generator", "build_nrj.py")
    with io.open(src, encoding="utf-8") as f:
        tree = ast.parse(f.read())
    scen = None
    for node in tree.body:
        if (isinstance(node, ast.Assign) and len(node.targets) == 1
                and getattr(node.targets[0], "id", "") == "SCEN"):
            scen = [[e.value for e in row.elts[:4]
                     if isinstance(e, ast.Constant)] for row in node.value.elts]
    if scen is None:
        return "SCEN not found in generator/build_nrj.py"
    by = collections.defaultdict(list)
    for row in scen:
        by[row[1]].append(row[3])
    out = []
    for d in DOMAINS:
        got = sorted(by[d])
        out.append("%s %s" % (d, "ok" if got == PRINTED else "MISMATCH %s" % got))
    return "; ".join(out)


PACES = ("one", "two", "three", "all", "clock", "ceil", "throttle")
RECOVS = ("best", "now", "next", "horizon")
COMMITS = ("all", "adaptive")
RESES = ("none", "small", "big", "dump")


if __name__ == "__main__":
    def band(w):
        return "*" if 47.0 <= w <= 57.0 else " "

    total = sum(DEAL) if isinstance(DEAL, tuple) else DEAL * 3
    print("THE IMPOSTER FINALE - the attention rotates, and you set the pace")
    print("=" * 74)
    print("%d finales a cell. %d Exhibits, %d sessions, 17 dice, "
          "Targets %d/%d/%d." % (GAMES, total, SESSIONS, 8 - TARGET_OFFSET,
                                 9 - TARGET_OFFSET, 10 - TARGET_OFFSET))
    print("printed Targets: %s" % check_components())
    print("* marks the 47-57% community band, whose mean is 53.0%.")

    print()
    print("1. THE PITCH")
    print("   Five seeds, because one is not a pitch: a single %d-game cell"
          % GAMES)
    print("   lands about a point either side of the mean.")
    seeds = (11, 23, 47, 101, 7)
    for lab, over in (("as it ships", {}),
                      ("without the five Reward cards", {"PAY_REWARDS": False}),
                      ("without the Research Pool", {"RESEARCH": False}),
                      ("played blind", dict(recov="best", pace="two",
                                            commit="all", res="none"))):
        ws = [run(seed=sd, **over) for sd in seeds]
        mean = sum(ws) / len(ws)
        print("   %-32s %6.1f%%%s  [%s]"
              % (lab, mean, band(mean),
                 " ".join("%.1f" % w for w in ws)))
        sys.stdout.flush()

    print()
    print("2. THE SKILL LAYER - every input face-up, none of it remembered")
    prev = None
    for lab, kw in (("played as the old finale was", dict(
                         recov="best", pace="two", commit="all", res="none")),
                    ("+ spend the Research Pool", dict(
                         recov="best", pace="two", commit="all", res="small")),
                    ("+ keep pace with the clock", dict(
                         recov="best", pace="clock", commit="all",
                         res="small")),
                    ("+ recover the colour coming up", dict(
                         recov="next", pace="clock", commit="all",
                         res="small")),
                    ("+ commit only what you need", dict(
                         recov="next", pace="clock", commit="adaptive",
                         res="small"))):
        w = run(**kw)
        print("   %-32s %7.1f%%%s%s"
              % (lab, w, band(w),
                 "" if prev is None else "  %+.1f" % (w - prev)))
        prev = w
        sys.stdout.flush()

    print()
    print("3. IS THE PACE A LIVE DECISION? the replay question.")
    print("   A fixed pace is what a solved scenario looks like.")
    for p in PACES:
        w = run(pace=p)
        print("   %-32s %7.1f%%%s" % ("pace: " + p, w, band(w)))
        sys.stdout.flush()

    print()
    print("4. THE OTHER THREE DECISIONS")
    for lab, key, vals in (("recover", "recov", RECOVS),
                           ("commit", "commit", COMMITS),
                           ("Research", "res", RESES)):
        ws = [run(**{key: v}) for v in vals]
        print("   %-10s" % lab + "  ".join("%s %.1f%%" % (v, w)
                                           for v, w in zip(vals, ws))
              + "   gap %.1f" % (max(ws) - min(ws)))
        sys.stdout.flush()

    print()
    print("5. THE DIALS - one step each")
    for lab, over in (("as it ships", {}),
                      ("8 sessions (ends on blue)", {"SESSIONS": 8}),
                      ("10 sessions (ENDS ON RED)", {"SESSIONS": 10}),
                      ("12 Exhibits, 4 per domain", {"DEAL": 4}),
                      ("13 Exhibits (5/4/4)", {"DEAL": (5, 4, 4)}),
                      ("14 Exhibits (5/5/4)", {"DEAL": (5, 5, 4)}),
                      ("16 Exhibits (6/5/5)", {"DEAL": (6, 5, 5)}),
                      ("18 Exhibits, 6 per domain", {"DEAL": 6}),
                      ("3 Health", {"HEALTH": 3}),
                      ("4 Health", {"HEALTH": 4}),
                      ("6 Health", {"HEALTH": 6}),
                      ("REC 2", {"REC_BASE": 2}),
                      ("REC 4", {"REC_BASE": 4}),
                      ("REC 5", {"REC_BASE": 5}),
                      ("STR 3", {"STRAT": 3}),
                      ("one-colour attention", {"WINDOW": 1}),
                      ("three-colour attention", {"WINDOW": 3}),
                      ("Targets 2/3/4", {"TARGET_OFFSET": 6}),
                      ("Damage 2 at Target 4+", {"BIG": 4}),
                      ("damage resets each session", {"CARRY": False}),
                      ("no Reward cards", {"PAY_REWARDS": False})):
        w = run(**over)
        print("   %-32s %7.1f%%%s" % (lab, w, band(w)))
        sys.stdout.flush()

    print()
    print("6. THE RESEARCH POOL")
    print("   A card is retained or it is not, and every retained card takes")
    print("   %d off one Exhibit's Target. The spent/unspent split was dropped"
          % CARD_VALUE)
    print("   on 2026-10-30: nothing on the table records which a card is,")
    print("   and a campaign can sit for weeks between games. So the pool is")
    print("   now just a COUNT, and seven is the count that reads 50%.")
    print("   %-26s %8s %8s" % ("NAP/BAT/AoS retained", "worth 1", "worth 2"))
    for r in ((1, 1, 1), (2, 2, 1), (2, 2, 2), (3, 2, 2), (3, 3, 2),
              (3, 3, 3)):
        a = sum(run(seed=sd, RETAIN=r, CARD_VALUE=1)
                for sd in seeds) / len(seeds)
        b = sum(run(seed=sd, RETAIN=r, CARD_VALUE=2)
                for sd in seeds) / len(seeds)
        print("   %-26s %7.1f%% %7.1f%%%s"
              % ("%d/%d/%d" % r, a, b,
                 "   <- shipped" if r == RETAIN else ""))
        sys.stdout.flush()
    w0 = sum(run(seed=sd, RESEARCH=False) for sd in seeds) / len(seeds)
    print("   %-26s %7s  %7.1f%%" % ("no retained cards", "", w0))
    print()
    print("   Eight cards worth 1.5 each beat six worth 2, on the same total")
    print("   reduction: spreading across more Exhibits pays better than")
    print("   concentrating, and more cards cover the three domains better.")
    print("   That is why dropping to one value needed the COUNTS re-derived")
    print("   rather than the values doubled.")

    print()
    print("7. THE DIFFICULTY LADDER - dice exhausted at setup")
    print("   The rules name the dice, so there is no choice to model. The")
    print("   counts are spread across the colours on purpose: taking whole")
    print("   ones collides with the wheel, which opens Yellow+Green, and")
    print("   '4 yellow 4 green' reads 28.7% against 38.4% for the same")
    print("   eight dice taken off the purple end. The red is never taken.")
    print("   %-10s %-14s %4s %8s %7s" % ("level", "y  g  b  p", "n",
                                          "win", "aim"))
    aims = {"easy": 50, "standard": 40, "hard": 30, "nobulous": 20}
    for lab in ("easy", "standard", "hard", "nobulous"):
        c = LADDER[lab]
        x = sum(run(seed=sd, START_TIRED=c) for sd in seeds) / len(seeds)
        print("   %-10s %-14s %4d %7.1f%%%s  %3d%%  %+.1f"
              % (lab.title(), "%d  %d  %d  %d" % c, sum(c), x, band(x),
                 aims[lab], x - aims[lab]))
        sys.stdout.flush()
    print()
    print("   AND WHETHER THE RUNGS ARE STILL GAMES OF SKILL. A tier where")
    print("   no policy beats another is not a harder puzzle, it is a worse")
    print("   one, so every rung is measured with its own gaps. This is the")
    print("   property that chose this dial: the RECOVERY decision, which is")
    print("   what the attention wheel exists to create, pays MORE as the")
    print("   ladder gets harder.")
    for lab in ("easy", "standard", "hard", "nobulous"):
        c = LADDER[lab]

        def g(**kw):
            return sum(run(seed=sd, START_TIRED=c, **kw)
                       for sd in seeds) / len(seeds)
        base = g()
        print("   %-10s %5.1f%%   pace %+5.1f   recover %+5.1f   commit %+5.1f"
              % (lab.title(), base, base - g(pace="two"),
                 base - g(recov="best"), base - g(commit="all")))
        sys.stdout.flush()
    print()
    print("   AND WHETHER COMMITTING IS STILL A DECISION. The pool lowers")
    print("   Targets, so it could have done what REC 4 does and made")
    print("   throwing every allowed die simply correct. It did the")
    print("   opposite - the gap is wider than it was on the old pool.")
    for rec in (2, 3, 4, 5):
        a = sum(run(seed=sd, REC_BASE=rec, commit="adaptive")
                for sd in seeds) / len(seeds)
        b = sum(run(seed=sd, REC_BASE=rec, commit="all")
                for sd in seeds) / len(seeds)
        print("   REC %d  adaptive %5.1f%%  all %5.1f%%   gap %+5.1f%s"
              % (rec, a, b, a - b,
                 "   <- shipped" if rec == REC_BASE else ""))
        sys.stdout.flush()

    print()
    print("THE PROTOTYPE'S ERRATA - three finale10 claims that the real")
    print("components did not support:")
    print("  1 'the pace cannot be memorised'. The schedule rule IS the")
    print("    winning pace and it is one formula, so the depth is in")
    print("    execution. finale10 said as much in its honest-limit note;")
    print("    what is new is that its own throttled variant measures WORSE")
    print("    than the plain schedule here, 40.1% against 51.4%.")
    print("  2 'a three-colour window'. At three colours raw strength beats")
    print("    reading the wheel and the finale reads 79.2%. The window has")
    print("    to be TWO for the dial's central decision to pay at all.")
    print("  3 its pacing figures. `clock` rounds the schedule and so falls")
    print("    quietly behind at a pressure just over 1 - see how_many().")
    print("  4 'commit only the dice you need', its LARGEST lever at +35.1.")
    print("    Worth +11.8 here, a third of that - and it is the lever")
    print("    most sensitive to the recovery economy. At REC 4 with the")
    print("    five Reward cards paying dice back it INVERTS, and")
    print("    throwing every allowed die wins by 10.0, which is why")
    print("    REC is 3: the Rewards ARE the fourth point of recovery, and")
    print("    they have to be earned.")
