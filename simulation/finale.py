"""The Imposter finale: the Council's attention rotates, and you set the pace.

    python finale.py              # the pitch, the skill layer and the dials

Rules source: rules/nrj.html. This module is the calibrated simulator for the
finale that SHIPS. `nrj.py` models the superseded nine-attempt Suspicion
finale and is kept only as the record of it - read the note at the top of that
file before quoting any figure from it.

WHERE THIS CAME FROM. proto/finale10.py measured the design against two
mechanics taken from published 20 Strong decks: Tainted Grail's colour dial,
and Tanglewoods: Rose's player-set pace against a hard clock. It beat every
earlier prototype on the only thing that decides whether a scenario gets
replayed - the gap between playing it badly and playing it well - and it did
it without asking the player to remember anything, because every input is
face-up on the table. The prototype measured a bare economy with invented
Exhibit values. This module is the same design on the REAL components, and
the numbers moved enough that three of its claims did not survive. They are
recorded in THE PROTOTYPE'S ERRATA at the bottom of the report.

WHAT THE COMPONENTS SUPPLY

  1 THE EXHIBITS ARE THE PRINTED COUNCIL TESTS. The 24-card library already
    sorts into 8 Knowledge, 8 Physical and 8 Cover-Up, and every domain
    prints the same Target spread, 8 8 8 9 9 9 10 10. An Exhibit's Target is
    its printed Target MINUS 5, so the deck supplies 3s, 4s and 5s with not
    one card reprinted - three 3s, three 4s and two 5s per domain.
    check_components() asserts that spread against build_nrj.py.
  2 THE RESEARCH POOL IS THE TIER III CARDS. Each game lays 6 out - 6
    Research Notes, 6 Devious Opportunities, 6 Backdoor Routines - so the
    18-card Pool needs no other box. A card you claimed is retained and a
    card you never claimed is a Candidate, worth nothing. A retained card
    spent as you deploy removes 1 from that Exhibit's Target, or 2 if you
    never spent it in its own game: the campaign's challenge is to finish
    each game using as little of its own Tier III help as possible. It
    answers only its own domain - NAP to Knowledge, BAT to Physical, AoS to
    Cover-Up - which is the old category match, and the only thing that
    makes the three domains mean anything once the dial carries the colour
    layer. A card is RETAINED or it is not and every retained one is worth
    2: the spent/unspent split was dropped on 2026-10-30 because nothing on
    the table records which a card is. At most 7 retained against 15
    Exhibits - NAP 3, BAT 2, AoS 2 - which is the count that reads 50%.
  3 THE AVOID RULE IS GONE, because choosing your pace replaces it. So is
    Suspicion, the uncapped Target tax: standing Exhibits deal Damage every
    session, which is the same pressure paid in Health instead of arithmetic.

THE PITCH: 50.5% at EASY, which is the Easy rung of the 50/40/30/20 ladder
and also sits in the old 47-57% community band. Measured over five seeds,
because one is not a pitch: 50.1 50.4 50.1 50.6 51.0. Every figure below is
at that setting, with no dice exhausted at setup.

  pace       clock 50.1   against every fixed pace: two 31.9, three 1.2,
             one and all 0.0, and the throttled variant 47.4
  recovery   horizon 50.1 and next 51.3, against best 45.6 and now 8.4 -
             reading the wheel pays, and grabbing this session's colour is
             far too late. next edges horizon on one seed and loses to it
             over five, 50.0 against 50.5 - which is the whole reason this
             file pitches on five.
  commit     adaptive 50.1 against 37.5 for throwing every allowed die
  Research   spending it 50.1 against 8.7 for ignoring it, with hoarding
             for the Target 5s at 42.1 and dumping it at 37.5 - WHICH card
             on WHICH Exhibit is the decision, not whether to spend
  Rewards    50.5 against 42.7 with the five Reward cards switched off
  carry-over 50.1 against 31.1 when progress resets, so the published rule
             that damage on a standing enemy persists is load-bearing
  blind play 0.5% - a player using none of the levers does not finish

  Every figure above is the BEST cell of the 224-cell policy grid, and the
  policy this module models IS that cell - clock / horizon / adaptive /
  small. This project has mis-pitched a game once by measuring it against a
  weaker policy than the one a player would find; the grid search is the
  guard against doing it twice.

THE LADDER IS CUT WITH DICE, not with a dial - see START_TIRED. Easy none,
Standard 3/2/2/2, Hard 3/3/3/2, Nobulous 3/3/4/4 yellow/green/blue/purple,
reading 50.6 / 39.2 / 30.6 / 19.4. The rungs still reward play, which is why
this dial was chosen over REC or the Dossier: the RECOVERY decision pays
+4.8 at Easy and +14.1 at Hard, so the harder tiers are more rewarding of
good play rather than less.

WHAT 2026-10-30 MOVED, in three corrections. research() was still dealing the
pool the Tier III rework replaced the day before - a NAP card always worth 1,
a BAT card worth 2 only on a 1-in-4 Specimen, an AoS card worth 2 on a coin
flip. Then the spent/unspent split went, because a campaign played over
several evenings cannot track it, and with one card value the pool became a
count that had to be re-derived: eight cards worth 1.5 beat six worth 2 on
the same total reduction, since spreading across more Exhibits and more
domains pays better than concentrating. And the Council Tests were reprinted
as Exhibits, Target and Damage on the face. Through all of it the pitch moved
about a point, and the COMMIT lever got stronger rather than weaker - 12.3
against 7.7 - because a pool that lowers Targets makes committing exactly
enough pay more.

THE FIVE REWARD CARDS ARE WHY REC IS 3. Eight of the 24 Council Tests are
printed as Rewards and five of them still pay something this finale has;
restoring them is worth +7.8 points. At REC 4 that tips the economy over,
and the commit decision does not merely die, it INVERTS: throwing every
allowed die beats holding any back by 12.0 points and the best available
policy wins 65.9%, out of band. The commit gap reads +23.8 at REC 2, +12.3
at REC 3, -12.0 at REC 4 and -13.2 at REC 5. REC 3 is the last rung where
committing is a decision. The Rewards are the fourth point of recovery, and
they have to be earned.

THE CLOCK IS NOT MONOTONIC, and that is a property rather than a bug. The
window is two colours wide and the wheel is five long, so the length of the
clock decides which colour the LAST session lands on. Nine sessions puts the
red session - one die, the hard one - exactly in the middle at session 5, and
ends on purple, the strongest. Eight sessions reads 23.8% and ten 21.8%,
because ten ENDS on red with the whole remainder still on the table. The
nine-session clock is chosen for its phase on the wheel, not its length.

WHAT IS STEEP, and where the edges are. REC is the usable dial and it is
not gentle: 2 / 3 / 4 / 5 read 28.2 / 50.5 / 53.9 / 54.1, and that last
pair is not a typo - past REC 3 the modelled policy stops being the best
one, exactly as described above. A point of STR is worth 85.4%.

THE DOSSIER SITS ONE EXHIBIT ABOVE A CLIFF. At REC 3 the deck reads
12 / 13 / 14 / 15 / 16 / 18 Exhibits = 76.7 / 69.8 / 64.8 / 50.1 / 20.6 /
0.2%. It is a workable seven-points-an-Exhibit dial on the easy side and
falls off entirely past the shipped 15, so a sixteenth Exhibit is not a
difficulty step, it is a different game. Health, by contrast, saturates
and is a buffer rather than a dial: 3 / 4 / 5 / 6 read 43.5 / 50.3 / 50.1
/ 50.0.
"""
import collections
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dice import COLORS, EV_REROLL, FACES, roll

GAMES = 6000
# The pitch is a FIVE-SEED mean: one 6000-game cell lands about a point
# either side of it, so a single seed is not a pitch. Module-level because
# table.py reads these rather than copying them - a copied seed set gives a
# different mean and the two files then disagree about what the finale reads.
SEEDS = (11, 23, 47, 101, 7)

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
    src = os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "generator", "build_nrj.py")
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
        self.start_tired()
        self.hp = HEALTH
        self.dial = 0
        self.at = 0
        self.discount = 0          # The Narrow Stair, owed to the next deploy

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
                e.target = max(1, e.target - c.value)
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
    taken = []
    for _ in range(how_many(g, pace)):
        e = g.deck.pop()
        if g.discount:                      # The Narrow Stair, if one is owed
            e.target = max(1, e.target - g.discount)
            g.discount = 0
        taken.append(e)
        g.active.append(e)
        g.reward(rew)
    g.spend_research(taken, res)

    ok = window(g.colour())
    spent = collections.Counter()       # committed from the pool this session
    applied = collections.Counter()     # ...of which these landed on a card
    unapplied = []

    for _ in range(STRAT):
        if not g.active or all(e.left <= 0 for e in g.active):
            break
        usable = [c for c in g.available if c in ok]
        take = want_dice(g, usable, commit)
        for c in take:
            g.available.remove(c)
            spent[c] += 1
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
    g.hp -= sum(e.damage for e in g.active if e.left > 0)
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
         "RESEARCH", "RETAIN", "CARD_VALUE", "START_TIRED",
         "TARGET_OFFSET", "WINDOW", "PAY_REWARDS")


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
    src = os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "generator", "build_nrj.py")
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
    seeds = SEEDS
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
