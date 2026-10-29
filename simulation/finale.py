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
  2 THE RESEARCH POOL SURVIVES, with one job instead of three. The campaign
    still carries 18 cards, 9 retained and 9 Candidates, and a retained card
    spent as you deploy removes 1 from that Exhibit's Target - 2 for a BAT
    Specimen or a Stable Advanced Program. It answers only its own domain:
    NAP to Knowledge, BAT to Physical, AoS to Cover-Up. That is the old
    category match, and it is the only thing that makes the three domains
    mean anything once the dial is carrying the colour layer.
  3 THE AVOID RULE IS GONE, because choosing your pace replaces it. So is
    Suspicion, the uncapped Target tax: standing Exhibits deal Damage every
    session, which is the same pressure paid in Health instead of arithmetic.

THE PITCH: 53.1%, against a community band of 47-57% and a mean of 53.0%
across 955 recorded games. Every lever below is measured at that setting.

  pace       clock 53.1   against every fixed pace: two 34.2, three 0.4,
             one and all 0.0, and the throttled variant 41.2
  recovery   next 53.1 and horizon 54.0, against best 47.2 and now 4.8 -
             reading the wheel pays, and grabbing this session's colour is
             far too late
  Research   spending it 53.1 against 9.3 for ignoring it, with hoarding for
             the Target 5s at 32.0 and dumping it at 33.6 - WHICH card on
             WHICH Exhibit is the decision, not whether to spend
  carry-over 53.1 against 36.2 when progress resets, so the published rule
             that damage on a standing enemy persists is load-bearing
  blind play 0.3% - a player using none of the levers does not finish

  The three levers, each measured as it is added to blind play: spending the
  Research Pool +13.1, keeping pace with the clock +20.3, recovering for the
  colour coming up +19.5. Committing only what you need, which was the
  prototype's biggest lever, is worth 0.0 - see the errata.

THE CLOCK IS NOT MONOTONIC, and that is a property rather than a bug. The
window is two colours wide and the wheel is five long, so the length of the
clock decides which colour the LAST session lands on. Nine sessions puts the
red session - one die, the hard one - exactly in the middle at session 5, and
ends on purple, the strongest. Eight sessions reads 24.6% and ten 18.1%,
because ten ENDS on red with the whole remainder still on the table. The
nine-session clock is chosen for its phase on the wheel, not its length.

WHAT IS STILL STEEP. One point of REC is worth about 20 points of win rate
(REC 3 reads 33.0%) and a point of STR 88.5%. That is the same binomial knife
edge imposter.py diagnosed in the superseded finale: a short race of pass/fail
sessions amplifies any dial that changes income. The Dossier is the gentler
dial at about 10 points an Exhibit, and the three settings measured in band -
12 Exhibits at REC 2, 14 at REC 3, 15 at REC 4 - are a real choice rather
than a knife edge. Health is a buffer and saturates: 3 / 4 / 5 / 6 Health
read 47.4 / 52.1 / 53.1 / 54.0.
"""
import collections
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

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
REC_BASE = 4
BIG = 5                    # an Exhibit at this Target or above deals 2 Damage
CARRY = True               # damage on a standing Exhibit carries over
RESEARCH = True            # the campaign's 9 retained cards

DOMAINS = ("Knowledge", "Physical", "Cover-Up")
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
    __slots__ = ("domain", "target", "dealt", "locked")

    def __init__(self, domain, target):
        self.domain = domain
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
    """The 9 retained cards, 3 per game, as the standalone rules deal them.

    BAT keeps at most 1 Specimen and AoS randomises Stable against
    Overheated, both per rules/nrj.html's standalone mode - so the pool's
    strength varies between finales exactly as a campaign's would.
    """
    if not RESEARCH:
        return []
    out = [Card("NAP", 1) for _ in range(3)]
    specimen = rng.randrange(4) == 0          # at most 1, and not always
    out += [Card("BAT", 2 if specimen and i == 0 else 1) for i in range(3)]
    out += [Card("AoS", 2 if rng.random() < 0.5 else 1) for _ in range(3)]
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
        for p in rng.sample(PRINTED, n):
            out.append(Exhibit(d, p - TARGET_OFFSET))
    rng.shuffle(out)
    return out


class Game(object):
    def __init__(self, rng):
        self.rng = rng
        self.deck = dossier(rng)
        self.pool = research(rng)
        self.active = []
        self.available, self.exhausted = fresh(), []
        self.hp = HEALTH
        self.dial = 0
        self.at = 0

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
        for a Specimen or a Stable Program. Only just-deployed Exhibits can
        be answered: once the Council has heard the evidence, producing your
        credentials is too late.
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
        taken.append(g.deck.pop())
        g.active.append(taken[-1])
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
    if not CARRY:
        for e in g.active:                  # the control: progress resets
            g.exhausted += e.locked
            e.locked = []
            e.dealt = 0

    g.recover(recov)
    g.dial += 1
    g.at += 1
    return True


def play(rng, pace="clock", recov="next", rew="dice", commit="adaptive",
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
         "RESEARCH", "TARGET_OFFSET", "WINDOW")


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
    for lab, over in (("as it ships", {}),
                      ("without the Research Pool", {"RESEARCH": False}),
                      ("played blind", dict(recov="best", pace="two",
                                            commit="all", res="none"))):
        w = run(**over)
        print("   %-32s %7.1f%%%s" % (lab, w, band(w)))
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
                      ("18 Exhibits, 6 per domain", {"DEAL": 6}),
                      ("3 Health", {"HEALTH": 3}),
                      ("4 Health", {"HEALTH": 4}),
                      ("6 Health", {"HEALTH": 6}),
                      ("REC 3", {"REC_BASE": 3}),
                      ("REC 5", {"REC_BASE": 5}),
                      ("STR 3", {"STRAT": 3}),
                      ("one-colour attention", {"WINDOW": 1}),
                      ("three-colour attention", {"WINDOW": 3}),
                      ("Targets 2/3/4", {"TARGET_OFFSET": 6}),
                      ("Damage 2 at Target 4+", {"BIG": 4}),
                      ("damage resets each session", {"CARRY": False})):
        w = run(**over)
        print("   %-32s %7.1f%%%s" % (lab, w, band(w)))
        sys.stdout.flush()

    print()
    print("THE PROTOTYPE'S ERRATA - three finale10 claims that the real")
    print("components did not support:")
    print("  1 'the pace cannot be memorised'. The schedule rule IS the")
    print("    winning pace and it is one formula, so the depth is in")
    print("    execution. finale10 said as much in its honest-limit note;")
    print("    what is new is that its own throttled variant measures WORSE")
    print("    than the plain schedule here, 41.2% against 53.1%.")
    print("  2 'a three-colour window'. At three colours raw strength beats")
    print("    reading the wheel and the finale reads 90.6%. The window has")
    print("    to be TWO for the dial's central decision to pay at all.")
    print("  3 its pacing figures. `clock` rounds the schedule and so falls")
    print("    quietly behind at a pressure just over 1 - see how_many().")
    print("  4 'commit only the dice you need', its LARGEST lever at +35.1.")
    print("    Worth 0.0 here: at REC 4 against Targets of 3 to 5 there is")
    print("    no pool shortage to be disciplined about, so throwing every")
    print("    allowed die measures exactly as well. Three levers carry")
    print("    this finale, not four.")
