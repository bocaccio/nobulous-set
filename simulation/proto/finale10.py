"""PROTOTYPE: the Council's attention rotates, and you choose the pace.

    python proto/finale10.py

Exploratory. Two mechanics lifted from published 20 Strong decks, on Jon's
instruction to use them as inspiration rather than to replicate them.

THE DIAL, from Tainted Grail. Its rule is one sentence: "you can only apply
dice that are the same color as the dial's current color. Dice that do not
match the dial color can still be committed and rolled, but they cannot be
applied." Each round the dial advances one colour. Here the dial is the
Council's ATTENTION - what part of you they are looking at this session -
and it runs yellow, green, blue, purple, red and round again.

Why this is the right core rule, measured rather than guessed. finale8 put
three one-line clauses on the three domains to make different dice valuable
and measured a +20.3 skill gap from routing the pool by them - twelve times
anything information or card-counting could produce. The dial buys the same
decision for a fifth of the rules, and it buys something finale8 could not:
because the dial is PUBLIC and advances predictably, you can see next
session's colour coming, so holding dice back and recovering the right ones
becomes a plan rather than a heuristic. finale8's recovery lever was worth
+2.9 because nothing made a colour matter next round. Here it should be the
spine of the game.

THE PACING, from Tanglewoods: Rose. "You can deploy as many or as few
enemies as you want each round. Deploying fewer gives you a respite, but
deploying too few each round will make it difficult for you to defeat them
all before the day tracker reaches zero." Each Exhibit you deploy pays a
reward at once; every Exhibit still standing hurts you every session; and
you must clear the whole Dossier before the clock runs out.

This is the engine finale7, finale8 and finale9 all lacked. Their decisions
were static policies - learn five rules and the scenario is solved. A
player-set pace against a hard clock cannot be solved that way, because the
right number to deploy depends on Health, the pool, the colour coming up and
how many Exhibits are left against how many sessions remain. That is the
property that decides whether anyone replays it.

THE SHAPE OF A SESSION

    1  DEPLOY   choose how many Exhibits to take from the Dossier. Each one
                pays a reward as it lands: recover dice, mend Health, or
                bend the dial for this session.
    2  STRATEGY commit dice, roll, apply hits - but only dice the dial
                allows. Repeat up to STR times, re-rolling what missed.
    3  RESOLVE  every Exhibit still standing deals its Damage. Dice applied
                to a standing Exhibit are NOT exhausted and their damage
                carries over, which is the published rule in Victorum,
                Cloudspire and Baba Yaga. Then recover, advance the dial,
                and tick the clock.

    WIN   the Dossier is empty and nothing is standing.
    LOSE  the clock runs out with Exhibits left, or Health falls below 1.

WHAT WAS MEASURED. 20000 finales a cell.

THE STRICT DIAL DOES NOT SURVIVE CONTACT. Applying only the attention
colour wins 4.0% over 9 sessions: four dice a session, one on a red
session, against twelve Exhibits. Tainted Grail can afford the strict rule
because it ships 32 combat cards whose whole job is bending it. The honest
simplification is a THREE-COLOUR WINDOW that rotates - the attention covers
your colour and the two beside it - which still locks about 40% of the pool
every session and still rotates predictably. That is DIAL_MODE "adjacent",
and everything below is measured there.

THE SKILL LAYER IS THE LARGEST OF ANY PROTOTYPE HERE, at 15 Exhibits over
9 sessions:

    played as the earlier prototypes played          8.9%
    + stop committing dice you do not need          44.1%   +35.1
    + recover the colour coming up next             56.8%   +12.7
    + keep pace with the clock                      75.7%   +18.9

Three separate levers, all large, all reading public state, none of them
asking the player to remember anything. Compare finale8's +20.3 for its
whole skill layer and finale9's +2.4 ceiling on deck knowledge.

PACING IS THE DOMINANT DECISION and no fixed number survives: deploying one
an session wins 0.0%, two 75.8%, three 60.5%, everything at once 0.0%, and
keeping pace with the clock 93.9%. The rule that wins is remaining Exhibits
over remaining sessions, less whatever is already on the table.

AND YOU CANNOT BUY SAFETY BY SLOWING DOWN. Throttling the pace when Health
is short LOSES 2.1 points, and throttling on a red session loses more. The
clock kills you more reliably than the Exhibits do, which is exactly the
tension Tanglewoods: Rose is built on.

SMALLER FINDINGS. Carry-over is worth +23.6, so the published rule that
damage on a standing enemy persists is load-bearing rather than a courtesy.
Recovery should look ONE session ahead, not two - "next" beats "horizon"
86.8% to 83.2%. And the deploy reward should simply be a recovered die:
paying Health instead wins 57.1% and banking a dial-bend 26.1%, against
85.0% for dice.

THE HONEST LIMIT. The winning pacing rule is one formula. It has to be
recomputed from the board every session, which is more than finale8's
static colour priorities ever asked, but it is still a single rule once
learned. The depth here is in execution rather than in choice.

PITCH: 15 Exhibits over 8 sessions wins 56.7%, inside the published 47-57%
community band.

SIMPLIFICATIONS: core economy only - no Scenario texts, no avoid rule, and
Suspicion is folded into Damage rather than tracked separately (it would
read as a second Health track here). Read the gaps, not the absolute rates.
"""
import collections
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dice import COLORS, EV, EV_REROLL, FACES, roll

GAMES = 20000
DOSSIER = (4, 4, 4)       # Exhibits per type: Knowledge, Physical, Cover-Up
SESSIONS = 9              # the clock
HEALTH = 5
STRAT = 2                 # Strategy phases per session
REC_BASE = 3
TIER3 = True
DIAL_MODE = "strict"      # strict | plus_red | adjacent
BEND = True               # a deploy reward may bend the dial for a session
CARRY = True              # damage on a standing Exhibit carries over
DAMAGE_BIG = 2            # Damage of an Exhibit worth 4 or more

# The attention runs weakest to strongest and round again, as Tainted Grail's
# dial does. Red is a single die, so a red session is the hard one unless you
# have banked a bend.
WHEEL = ["yellow", "green", "blue", "purple", "red"]
TYPES = ("Knowledge", "Physical", "Cover-Up")


def fresh():
    # 4 each of purple, blue, green and yellow plus a SINGLE red: 17 unit
    # dice (General Rules of Play, p.7).
    return [c for c in COLORS for _ in range(4)] + ["red"]


class Exhibit(object):
    __slots__ = ("kind", "hp", "dealt", "locked")

    def __init__(self, kind, value):
        self.kind = kind
        self.hp = value                 # the Target you must meet to bury it
        self.dealt = 0                  # damage carried over from past rounds
        self.locked = []                # dice held on the card, not exhausted

    @property
    def damage(self):
        return DAMAGE_BIG if self.hp >= 4 else 1

    @property
    def left(self):
        return max(0, self.hp - self.dealt)


def dossier(rng):
    """The Exhibits the campaign produced. Counts are fixed at four per type
    so the finale can be pitched to one number; the campaign sets the
    VALUES, which keeps the deck personal without the 30-point difficulty
    swing finale9 measured when the campaign set the counts too."""
    k, p, c = DOSSIER
    out = [Exhibit("Knowledge", 2) for _ in range(k)]
    pool = [2, 3, 3, 4, 2, 2, 3, 3, 2, 3, 3, 2, 4]
    if TIER3:
        pool += [4, 4, 5, 4, 5, 4]
    out += [Exhibit("Physical", rng.choice(pool + [5])) for _ in range(p)]
    out += [Exhibit("Cover-Up", 4 if rng.random() < 0.65 else 2)
            for _ in range(c)]
    rng.shuffle(out)
    return out


def allowed(dial, bent):
    """Which colours may be APPLIED this session."""
    ok = {dial}
    if bent:
        ok |= set(bent)
    if DIAL_MODE == "plus_red":
        ok.add("red")
    elif DIAL_MODE == "adjacent":
        i = WHEEL.index(dial)
        ok.add(WHEEL[(i + 1) % 5])
        ok.add(WHEEL[(i - 1) % 5])
    return ok


class Game(object):
    def __init__(self, rng):
        self.rng = rng
        self.deck = dossier(rng)
        self.active = []
        self.available, self.exhausted = fresh(), []
        self.hp = HEALTH
        self.dial = 0
        self.at = 0
        self.bent = set()

    # -- the state a policy is allowed to read; all of it is public --------
    def colour(self):
        return WHEEL[self.dial % 5]

    def next_colour(self, ahead=1):
        return WHEEL[(self.dial + ahead) % 5]

    def sessions_left(self):
        return SESSIONS - self.at

    def pressure(self):
        """Exhibits still to bury per session remaining. Above 1.0 means the
        clock is losing and you have to take on more."""
        left = len(self.deck) + len(self.active)
        return left / float(max(1, self.sessions_left()))

    # -- the economy ------------------------------------------------------
    def recover(self, policy):
        rec = REC_BASE
        if not rec or not self.exhausted:
            return
        if policy == "best":                       # the naive rule
            key = {c: EV_REROLL[c] for c in FACES}
        elif policy == "next":                     # the colour coming up
            nxt = self.next_colour()
            key = {c: (10.0 if c == nxt else EV_REROLL[c]) for c in FACES}
        elif policy == "horizon":                  # the next two colours
            a, b = self.next_colour(1), self.next_colour(2)
            key = {c: EV_REROLL[c] for c in FACES}
            key[a] += 20.0
            key[b] += 10.0
        elif policy == "now":                       # this session's colour
            cur = self.colour()
            key = {c: (10.0 if c == cur else EV_REROLL[c]) for c in FACES}
        else:
            key = {c: EV_REROLL[c] for c in FACES}
        self.exhausted.sort(key=lambda c: key[c])
        for _ in range(min(rec, len(self.exhausted))):
            self.available.append(self.exhausted.pop())

    def reward(self, policy):
        """Rose pays a reward for each Exhibit you deploy - that is what
        makes taking on more than you must worth considering."""
        if policy == "health":
            self.hp = min(HEALTH, self.hp + 1)
            return
        if policy == "bend" and BEND:
            for c in WHEEL:                 # bank the scarcest useful colour
                if c not in self.bent:
                    self.bent.add(c)
                    return
            return
        if policy == "adaptive":
            if self.hp <= 2:
                self.hp = min(HEALTH, self.hp + 1)
                return
            if BEND and self.colour() == "red" and not self.bent:
                self.bent.add("purple")
                return
        if self.exhausted:                  # default: dice back
            nxt = self.next_colour()
            self.exhausted.sort(
                key=lambda c: (10.0 if c == nxt else EV_REROLL[c]))
            self.available.append(self.exhausted.pop())
        else:
            self.hp = min(HEALTH, self.hp + 1)


def how_many(g, pace):
    """Rose's decision: how many Exhibits to take this session."""
    room = len(g.deck)
    if not room:
        return 0
    if pace in ("one", "two", "three"):
        return min(room, {"one": 1, "two": 2, "three": 3}[pace])
    if pace == "all":
        return room
    if pace == "clock":
        # Exactly enough to stay on schedule, and nothing more.
        return min(room, max(0, int(round(g.pressure() - len(g.active)))))
    if pace == "adaptive":
        # Start from the schedule - remaining work over remaining sessions,
        # less whatever is already on the table - because the first pass of
        # this prototype measured every FIXED pace losing to that rule by
        # 18 to 94 points. Then throttle only where the board says to.
        n = max(0, int(round(g.pressure() - len(g.active))))
        if g.hp <= 2 and n > 1:
            n -= 1                      # cannot afford another Damage source
        if g.hp >= HEALTH and not g.active and room:
            n += 1                      # a free session is wasted schedule
        return min(room, max(0, n))
    return min(room, 1)


def want_dice(g, pool, policy):
    """How many of the usable dice to commit. Under the dial an applicable
    die you commit and do not need is simply burned, so this is a lever in
    its own right - and the reason to leave dice ready is that next
    session's colour is already visible on the wheel."""
    pool = sorted(pool, key=lambda c: -EV_REROLL[c])
    if policy == "all":
        return pool
    need = sum(e.left for e in g.active)
    if policy == "enough":
        out, got = [], 0.0
        for c in pool:
            if got >= need:
                break
            out.append(c)
            got += EV_REROLL[c]
        return out
    # adaptive: cover what is standing, with a margin while Health is thin,
    # and never spend a die the next session will want if this one is safe.
    margin = 1.0 if g.hp <= 2 else 0.0
    out, got = [], 0.0
    for c in pool:
        if got >= need + margin:
            break
        out.append(c)
        got += EV_REROLL[c]
    return out


def session(g, pace, recov, rew, commit):
    g.bent = set()
    for _ in range(how_many(g, pace)):
        g.active.append(g.deck.pop())
        g.reward(rew)

    ok = allowed(g.colour(), g.bent)
    spent = collections.Counter()      # committed from the pool this session
    applied = collections.Counter()    # ...of which these landed on a card
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
        # crit is not stranded on a card that needed one hit.
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

    # Suffer Damage: everything still standing hits you.
    g.hp -= sum(e.damage for e in g.active if e.left > 0)
    if g.hp <= 0:
        return False

    # Exhaust: committed dice that did not land, plus every die held on an
    # Exhibit that has now fallen. Dice held on something still standing are
    # neither exhausted nor available - the published rule.
    for c in (spent - applied).elements():
        g.exhausted.append(c)
    buried = [e for e in g.active if e.left <= 0]
    g.active = [e for e in g.active if e.left > 0]
    for e in buried:
        g.exhausted += e.locked
        e.locked = []
    if not CARRY:
        for e in g.active:                 # the control: progress resets
            g.exhausted += e.locked
            e.locked = []
            e.dealt = 0

    g.recover(recov)
    g.dial += 1
    g.at += 1
    return True


def play(rng, pace="adaptive", recov="next", rew="adaptive",
         commit="adaptive"):
    g = Game(rng)
    for _ in range(SESSIONS):
        if not g.deck and not g.active:
            return True
        if not session(g, pace, recov, rew, commit):
            return False
    return not g.deck and not g.active


KW = ("pace", "recov", "rew", "commit")


def run(games=GAMES, seed=11, **over):
    kw = {k: over.pop(k) for k in list(over) if k in KW}
    saved = {k: globals()[k] for k in over}
    globals().update(over)
    rng = random.Random(seed)
    try:
        return 100.0 * sum(1 for _ in range(games) if play(rng, **kw)) / games
    finally:
        globals().update(saved)


PACES = ("one", "two", "three", "all", "clock", "adaptive")
RECOVS = ("best", "now", "next", "horizon")
COMMITS = ("all", "enough", "adaptive")


if __name__ == "__main__":
    print("PROTOTYPE - the Council's attention rotates, and you set the pace")
    print("=" * 76)
    print("%d finales a cell. %d Exhibits, %d sessions, 17 dice."
          % (GAMES, sum(DOSSIER), SESSIONS))

    print()
    print("1. IS IT PLAYABLE AT ALL? the dial is a hard restriction")
    print("   strict = only the attention colour may be applied, which on a")
    print("   red session is one die. The looser modes are what card text")
    print("   would buy you in a real deck.")
    print("   %-16s %10s %10s %9s" % ("dial", "9 sessions", "11", "13"))
    for mode in ("strict", "plus_red", "adjacent"):
        ws = [run(DIAL_MODE=mode, SESSIONS=s) for s in (9, 11, 13)]
        print("   %-16s %9.1f%% %9.1f%% %8.1f%%" % (mode, ws[0], ws[1], ws[2]))
        sys.stdout.flush()

    print()
    print("2. DOES THE PUBLIC DIAL MAKE RECOVERY A PLAN?")
    print("   `best` is finale6's rule - take the strongest dice back.")
    print("   `now` grabs this session's colour, which is too late to help.")
    print("   `next` and `horizon` read the wheel and stock what is coming.")
    print("   %-18s" % "recover" + "".join("%11s" % r for r in RECOVS)
          + "%9s" % "gap")
    for mode in ("strict", "plus_red", "adjacent"):
        ws = [run(DIAL_MODE=mode, recov=r) for r in RECOVS]
        print("   %-18s" % mode + "".join("%10.1f%%" % w for w in ws)
              + "%8.1f" % (max(ws) - min(ws)))
        sys.stdout.flush()

    print()
    print("3. IS THE PACE A LIVE DECISION? - the replay question")
    print("   The fixed paces are what a solved strategy looks like. If")
    print("   `adaptive` - which reads Health, the pool, the colour and the")
    print("   clock - beats every one of them, the right number to deploy")
    print("   depends on the board and cannot be memorised.")
    print("   %-14s" % "pace" + "".join("%10s" % p for p in PACES))
    for mode in ("strict", "plus_red", "adjacent"):
        ws = [run(DIAL_MODE=mode, pace=p) for p in PACES]
        best = max(ws[:-1])
        print("   %-14s" % mode + "".join("%9.1f%%" % w for w in ws)
              + "   adaptive %+.1f over the best fixed" % (ws[-1] - best))
        sys.stdout.flush()

    print()
    print("4. WHAT THE DEPLOY REWARD SHOULD BE")
    print("   Rose pays you for every Exhibit you take on. What it pays")
    print("   decides whether taking more is ever right.")
    print("   %-20s %10s %10s %10s %10s"
          % ("reward", "dice", "health", "bend", "adaptive"))
    for mode in ("strict", "adjacent"):
        ws = [run(DIAL_MODE=mode, rew=r)
              for r in ("dice", "health", "bend", "adaptive")]
        print("   %-20s %9.1f%% %9.1f%% %9.1f%% %9.1f%%"
              % (mode, ws[0], ws[1], ws[2], ws[3]))
        sys.stdout.flush()

    print()
    print("5. DOES CARRY-OVER MATTER? the published rule says damage on a")
    print("   standing enemy persists and its dice are not exhausted.")
    print("   %-28s %10s %10s" % ("", "carries", "resets"))
    for mode in ("strict", "adjacent"):
        a = run(DIAL_MODE=mode, CARRY=True)
        b = run(DIAL_MODE=mode, CARRY=False)
        print("   %-28s %9.1f%% %9.1f%%  %+.1f" % (mode, a, b, a - b))
        sys.stdout.flush()

    print()
    print("6. THE WHOLE SKILL LAYER")
    print("   Playing it the way the earlier prototypes played - strongest")
    print("   dice back, a fixed pace - against reading the wheel and the")
    print("   clock.")
    print("   %-28s %10s %10s %9s" % ("dial", "blind", "skilled", "gap"))
    for mode in ("strict", "plus_red", "adjacent"):
        b = run(DIAL_MODE=mode, recov="best", pace="two", rew="dice",
                commit="all")
        s = run(DIAL_MODE=mode, recov="horizon", pace="adaptive",
                rew="adaptive", commit="adaptive")
        print("   %-28s %9.1f%% %9.1f%% %+8.1f" % (mode, b, s, s - b))
        sys.stdout.flush()

    print()
    print("7. IS COMMITMENT A LEVER UNDER THE DIAL?")
    print("   `all` throws every usable die at the table, which burns dice")
    print("   the next colour wanted. `enough` covers what is standing.")
    print("   %-18s" % "commit" + "".join("%11s" % c for c in COMMITS)
          + "%9s" % "gap")
    for mode in ("strict", "plus_red", "adjacent"):
        ws = [run(DIAL_MODE=mode, commit=c) for c in COMMITS]
        print("   %-18s" % mode + "".join("%10.1f%%" % w for w in ws)
              + "%8.1f" % (max(ws) - min(ws)))
        sys.stdout.flush()

    print()
    print("8. THE DIALS, at adjacent / adaptive / horizon")
    base = dict(DIAL_MODE="adjacent", recov="horizon", pace="adaptive",
                rew="adaptive", commit="adaptive")
    print("   %-30s %9s" % ("dial", "win"))
    for label, over in (("as built", {}),
                        ("8 sessions", {"SESSIONS": 8}),
                        ("10 sessions", {"SESSIONS": 10}),
                        ("9 Exhibits, 3 per type", {"DOSSIER": (3, 3, 3)}),
                        ("15 Exhibits, 5 per type", {"DOSSIER": (5, 5, 5)}),
                        ("4 Health", {"HEALTH": 4}),
                        ("6 Health", {"HEALTH": 6}),
                        ("REC 2", {"REC_BASE": 2}),
                        ("REC 4", {"REC_BASE": 4}),
                        ("STR 3", {"STRAT": 3}),
                        ("no dial bending", {"BEND": False}),
                        ("big Exhibits deal 1", {"DAMAGE_BIG": 1}),
                        ("no tier module", {"TIER3": False})):
        print("   %-30s %8.1f%%" % (label, run(**dict(base, **over))))
        sys.stdout.flush()
