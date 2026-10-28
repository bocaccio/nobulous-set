"""PROTOTYPE: three ENCOUNTERS that play like the games they came from.

    python proto/finale7.py

Exploratory. The objection this answers, from Jon:

    "Other than a council card being related to a skill in one of the games,
    the associated 'task' is still somewhat generic. I want the knowledge
    tasks to feel like something I would do in NAP, or a physical task like
    fighting the tyrant in BAT."

finale6 is guilty as charged. Every check there is the same arithmetic -
beat one number - and the domain label only decides whether the shroud gets
its match bonus. So the finale asks one question nine times.

The fix is not three flavours of check. It is three ENCOUNTERS, interleaved
across the nine attempts, each built out of the mechanic that makes its game
what it is. The three attempts of a domain are the same encounter, continued:

  Knowledge, after NAP's Assignment row (nap.py, rules/nap.html)
      Three Inquiries queue up and you work the FRONT one. Successes STORE
      on it rather than resolving it, and the dice you store LOCK to the
      card - no REC until the question is answered. A question you leave
      open inflicts its Demand every attempt it survives (exhaust 1 die)
      and takes another council card onto its Target, so an unfinished
      answer is scrutinised harder the longer you sit on it. Worst of all
      it BLOCKS THE QUEUE: carry one and the question behind it is never
      asked, and you walk out with it unanswered.
      The NAP decision: answer now and risk it, or store and back the row up.

  Physical, after BAT's Tyrant track (bat.py, rules/bat.html)
      ONE track of three segments, face down. Damage CHEWS LEFT TO RIGHT
      AND CARRIES OVER, and carry-over reveals the next segment - so a big
      swing can take two at once and end the fight early, and overkill is
      never wasted. Between blows it REPLIES, and the reply's severity is
      the largest segment still standing, exactly as the Tyrant draws dice
      equal to its best surviving Splice. Chew it down and it hits softer.
      The BAT decision: one big swing, or chip at it and eat the replies.

  Cover-Up, after AoS's Programs (aos.py, rules/aos.html)
      Three independent Programs, because that is what AoS is. Each shows
      several Elements with their own small Targets, ALLOCATED BEFORE
      ROLLING. One failed Element is free; two is a Catastrophic Failure.
      Landing exactly on an Element's Target hands a die back. The council
      card lands on ONE Element at random, after you have allocated.
      The AoS decision: pad every Element against the flip, or aim tight
      and let the hardest one go.

So the three encounters differ in STRUCTURE, not just in arithmetic: a queue
that backs up, a track chewed down once, and three independent allocations.

WHAT WAS MEASURED, AND WHAT THE ANSWER WAS. The hypothesis was that the
three shapes would want OPPOSITE play - that overcommitting locks dice away
in the Knowledge encounter, is nearly free in the Physical one because the
excess carries down the track, and is impossible in the Cover-Up one where
you only distribute. If one hedge served all three, the shaping would be
cosmetic.

That hypothesis is FALSIFIED at the recommended pitch, and section 4 shows
it: once the Tyrant has to be put down, Knowledge and Physical both want the
hedge at q1.00. One rule - "commit for the worst card the council can still
flip" - serves both. The shapes change WHAT you do; they do not yet change
HOW MUCH you commit.

What did hold:

  * BAT's track PORTS, and hard. Chipping at it and walking away scores 1.1%
    against 66.0% for committing to put it down: a 64.9-point tactical gap.
    It is a real encounter, not a label.
  * AoS's Program PORTS. 8.4 points separate the allocation policies, and
    the winning one is a genuine AoS reading - allocate THIN and take the
    one free Element failure, rather than padding every Element (-1.5) or
    deliberately abandoning the hardest (-8.4).
  * NAP's row DOES NOT PORT. Six variants were measured. Among the options
    that are actually competitive the spread never cleared 2.5 points - the
    queue answered at once (2.5), the parallel Assignment row (0.4), that
    row with a reward for answering (0.1), the row with printed subject dots
    (1.1). The wide gaps that do appear are storing being strictly worse:
    overstore 51.9% against declare 66.0%, and the split/pace storing
    policies 14 to 30 points down. So there is no decision in it, only a
    trap. The reason is structural and it is the useful
    finding here - see below.

LOCAL MECHANICS PORT; GAME-SPANNING ECONOMIES DO NOT. BAT's track and AoS's
Programs each resolve completely inside one confrontation or one Program, so
lifting the mechanic lifts its decision with it. NAP's Assignment row is an
economy that spans a whole game: which Assignment you work matters because
of Credits, subjects, recovery dots and the Final Exams waiting at the end.
Compress it into three attempts with nothing downstream and every Inquiry is
interchangeable, so "which one" has nothing to bite on, and storing
successes becomes pure cost-spreading that buys nothing.

WHERE THE DEPTH WOULD HAVE TO COME FROM, untested. The three encounters
currently compete for one pool in the same currency - expected hits - which
is why one hedge serves them. They would want different play if they wanted
different DICE: the Tyrant wants raw volume, an alibi's Elements want many
cheap dice because each needs only 2 hits, and an Inquiry wants the one
colour its subject dot doubles. Then the decision is which encounter gets
which dice, and no single hedge can express it. Measuring that needs a
policy that RESERVES colours across encounters, which this harness does not
have: `commit` always takes the best dice available.

SIMPLIFICATIONS: core economy only - no Scenario texts, no colour clauses,
no avoid rule. Read the gaps, not the absolute rates.
"""
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import nap
from dice import COLORS, EV_REROLL, roll

# The 12 Final Exams, from nap.EXAMS: their base Targets and their subject
# dots. NAP prints a recovery dot on every Exam and every Assignment, and
# working to the dot is the game's constant small decision.
EXAM_TARGETS = [t for _, _, t in nap.EXAMS]
EXAM_DOTS = [nap.DOT_COLOR[d] for _, d, _ in nap.EXAMS]

GAMES = 20000

# ---------------------------------------------------------------- the dials
BASE_TARGET = 0           # finale6's recommended pitch: no printed Target
MATCH_BONUS = 1           # the council card's bonus when it matches the gate
HEALTH = 5
REC_BASE = 3
ATTEMPTS = 9
BANISH = 2                # dice paid for a failure, when dice can be paid
INQUIRIES = 2             # Inquiries queued against 3 Knowledge slots. NAP's
                          # Assignment row has slack - more Time Slots than
                          # Assignments - and without slack here a carried
                          # question always costs an unanswered one, so
                          # storing can never pay. Swept in section 6.
SEGMENTS = 3              # the Tyrant track's length
REPLY = "splice"          # how hard the track hits back:
                          #   "flat"   2 dice, 1 once it is chewed small
                          #   "splice" dice equal to its biggest surviving
                          #            segment, as the Tyrant draws dice equal
                          #            to its best remaining Splice (max 6)
TIER3 = True              # Tier III puts Modifications at 4-5 in BAT's deck
# Two dials that decide whether each encounter's SIGNATURE mechanic is live.
# Measured in section 6: with the track merely costing 1 Health at the end,
# chipping at the Tyrant and walking away beats fighting it; with a wrong
# answer costing no more than a Demand, storing on an Inquiry is never worth
# it. Both make the shape cosmetic, so both are swept rather than assumed.
SUBJECT = True            # an Inquiry prints a subject dot and dice of that
                          # colour count double on it, as NAP prints a dot on
                          # every Exam. This is a LOCAL mechanic - it resolves
                          # inside the one check - which is why it ports where
                          # the Assignment row's economy does not.
REWARD = "discard"        # what ANSWERING an Inquiry buys you:
                          #   "none"      nothing - the cost axis only
                          #   "discard"   strike the worst card still in the
                          #               council deck, one per 3 Target, as
                          #               NAP's Credits cut the Exam Targets
                          #   "suspicion" clear 1 Suspicion
ROW = False               # Inquiries sit on a ROW, all open at once, the
                          # way NAP's Assignments do - rather than queuing
                          # one at a time. Measured in section 6: the queue
                          # kills storing outright, because spreading an
                          # answer over two slots buys nothing when there
                          # is no second card to park dice on meanwhile.
EXAM_SIZED = False        # an Inquiry prints a NAP Final Exam Target (5-7),
                          # which is more than one attempt's dice - the whole
                          # reason NAP's row stores successes at all
TRACK_MUST_FALL = True    # BAT: you do not get to walk away from the Tyrant
WRONG_SUSPICION = 2       # what answering an Inquiry wrongly costs
SHAPED = True             # False = finale6's flat check, as the control
DOMAINS = ("Knowledge", "Physical", "Cover-Up")

# How hard each encounter hedges: a quantile of what the council could flip,
# "adaptive" for finale6's state-aware rule, or "reckless" for none.
Q = {"Knowledge": "adaptive", "Physical": "adaptive", "Cover-Up": "adaptive"}


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


class Finale(object):
    """17 dice, 5 Health, no cards. The council holds everything."""

    def __init__(self, rng):
        self.rng = rng
        self.deck = council_deck(rng)
        self.available = fresh()
        self.exhausted = []
        self.locked = []          # dice stored on the open Inquiry
        self.hp = HEALTH
        self.suspicion = 0
        # the three encounters
        # [Target, stored, Demand] per Inquiry. The Demand is drawn from
        # nap.DEMAND_PENALTY, the printed penalties an Assignment inflicts
        # for every Time Slot it survives on its Demand side: 1 or 2 means
        # exhaust that many dice, -1 means lose 1 Health.
        self.queue = [[0, 0, rng.choice(nap.DEMAND_PENALTY)]
                      for _ in range(INQUIRIES)]
        self.open = False         # is the front Inquiry already under way?
        # [Target, stored, Demand, locked dice] per Inquiry on the row.
        self.row = [[0, 0, rng.choice(nap.DEMAND_PENALTY), [],
                     rng.choice(EXAM_DOTS)] for _ in range(INQUIRIES)]
        self.know_left = 3        # Knowledge attempts still to come
        self.revealed = []        # remainders of flipped segments, in order
        self.face_down = SEGMENTS
        self.left = ATTEMPTS

    # -- the council ------------------------------------------------------
    def flip(self, domain):
        if not self.deck:
            return 2
        d, v = self.deck.pop()
        return v + (MATCH_BONUS if d == domain else 0)

    def hedge(self, domain):
        """How much to pad the commitment, by policy.

        `adaptive` is finale6's measured rule, which reduced to two clauses
        worth ~6 points: hedge hard while the game is long, and never hedge
        with dice you cannot spare.
        """
        q = Q[domain]
        if q == "reckless" or not self.deck:
            return 0.0
        vals = [v + (MATCH_BONUS if d == domain else 0) for d, v in self.deck]
        if q != "adaptive":
            return quantile(vals, q)
        qq = 0.50
        if self.left >= 6:
            qq += 0.20
        if self.left <= 2:
            qq -= 0.25
        if self.hp <= 2:
            qq += 0.20
        if len(self.available) <= 6:
            qq -= 0.30
        return quantile(vals, min(1.0, max(0.0, qq)))

    # -- the dice ---------------------------------------------------------
    def commit(self, want, double=None):
        """Take dice by descending EV until the expected total reaches `want`,
        roll, and reroll the misses once (STR 2). The dice leave `available`;
        the caller decides whether they exhaust or lock."""
        def worth(c):
            # A die on the Inquiry's subject counts double, so the subject
            # decides which dice are the right ones to spend here - and
            # spending them here is spending them away from the Tyrant.
            return EV_REROLL[c] * (2 if c == double else 1)

        self.available.sort(key=lambda c: -worth(c))
        take, got = [], 0.0
        for c in self.available:
            if got >= want:
                break
            take.append(c)
            got += worth(c)
        values = [roll(c, self.rng) * (2 if c == double else 1) for c in take]
        hits = sum(values)
        if hits < want:
            again = [take[i] for i, v in enumerate(values) if v == 0]
            hits += sum(roll(c, self.rng) for c in again)
        for c in take:
            self.available.remove(c)
        return hits, take

    def pay(self, dice=BANISH, suspicion=1):
        """A failure: Suspicion, then dice if there are dice, else Health.
        finale5 measured dice-first as worth 9-13 points over Health."""
        self.suspicion += suspicion
        if len(self.available) >= dice:
            self.available.sort(key=lambda c: EV_REROLL[c])
            for _ in range(dice):
                self.available.pop(0)
        else:
            self.hp -= 1

    def knowledge_slots(self):
        """Knowledge attempts still to come, this one included."""
        return max(1, self.know_left)

    def hit(self, dice):
        """A blow that is not a failure: exhaust dice, or lose Health if
        there are no dice left to take. The Tyrant's attacks and NAP's
        Demands both land here - neither is a Suspicion event, because
        neither is the council catching you out."""
        self.available.sort(key=lambda c: EV_REROLL[c])
        if len(self.available) >= dice:
            for _ in range(dice):
                self.exhausted.append(self.available.pop(0))
        else:
            self.hp -= 1

    def recover(self):
        rec = max(0, REC_BASE - self.suspicion)
        self.exhausted.sort(key=lambda c: EV_REROLL[c])
        for _ in range(min(rec, len(self.exhausted))):
            self.available.append(self.exhausted.pop())


# ------------------------------------------------------------ the encounters
def flat(g, domain):
    """The control: finale6's single number, nine times."""
    base = BASE_TARGET + g.suspicion
    hits, take = g.commit(base + g.hedge(domain))
    g.exhausted += take
    if hits < base + g.flip(domain):
        g.pay()


def knowledge(g, policy):
    """NAP's Assignment row: store successes, lock the dice, pay the Demand
    for every slot the question survives - and block the queue behind it."""
    if not g.queue:
        return                             # every Inquiry answered: a clear slot
    inq = g.queue[0]
    if not g.open:
        # An Inquiry prints a Target the way NAP's Final Exams do - 5 to 7,
        # from nap.EXAMS - and that is the point of the shape: it is more
        # than one attempt's worth of dice, so the successes have to be
        # STORED across slots before the question can be answered.
        inq[0] = (EXAM_TARGETS[g.rng.randrange(len(EXAM_TARGETS))]
                  if EXAM_SIZED else BASE_TARGET) + g.suspicion
        g.open = True
    need = max(0.0, inq[0] - inq[1])
    want = need + g.hedge("Knowledge")
    if policy == "overstore":
        # Store against the scrutiny a carried question will attract.
        want += g.hedge("Knowledge")
    elif policy in ("split", "pace"):
        # Work the question the way NAP's row is worked: put part of the
        # answer together this slot and finish it in the next, rather than
        # emptying the pool to close it in one.
        slots = 2 if policy == "split" else max(1, g.knowledge_slots())
        want = need / float(slots) + g.hedge("Knowledge") / float(slots)
    hits, take = g.commit(want)
    inq[1] += hits
    g.locked += take                       # the dice lock to the card
    inq[0] += g.flip("Knowledge")          # the council reads your answer

    if inq[1] >= inq[0]:                   # answered
        g.queue.pop(0)
        g.open = False
        g.exhausted += g.locked
        g.locked = []
        return
    carry = policy in ("carry", "overstore", "split", "pace") and g.left > 1
    if policy == "judge":
        # Carry only when carrying is cheap and nearly done: the Demand is
        # not a Health loss, the answer is within one more attempt, and there
        # is a Knowledge slot spare to finish it in.
        carry = (g.left > 2 and inq[2] >= 0
                 and inq[0] - inq[1] <= 3 and len(g.queue) < INQUIRIES + 1)
    if carry:
        return                             # left open: it will cost a die a slot
    g.pay(suspicion=WRONG_SUSPICION)       # you answer anyway, and it is wrong
    g.queue.pop(0)
    g.open = False
    g.exhausted += g.locked
    g.locked = []


def knowledge_row(g, policy):
    """NAP's Assignment row proper: every Inquiry is open at once, each with
    its own stored successes, its own locked dice and its own Demand. One is
    worked per slot and the rest bite. The decision is WHICH to work - and
    that is the decision NAP actually asks."""
    if not g.row:
        return
    for c in g.row:                        # a Target is printed when it lands
        if c[0] == 0:
            c[0] = (EXAM_TARGETS[g.rng.randrange(len(EXAM_TARGETS))]
                    if EXAM_SIZED else BASE_TARGET) + g.suspicion

    if policy == "closest":                # finish what is nearly done
        inq = min(g.row, key=lambda c: c[0] - c[1])
    elif policy == "biggest":              # start the hard one while rich
        inq = max(g.row, key=lambda c: c[0] - c[1])
    elif policy == "silence":
        # Clear the one whose Demand costs Health first, nearest among those:
        # the row bleeds you every slot, so shutting the painful card up is
        # worth more than the progress.
        inq = min(g.row, key=lambda c: (c[2] >= 0, c[0] - c[1]))
    elif policy == "subject":
        # Work the question your pool is actually stocked for.
        inq = max(g.row, key=lambda c: sum(1 for d in g.available
                                           if d == c[4]))
    else:                                  # "rote": left to right
        inq = g.row[0]

    want = max(0.0, inq[0] - inq[1]) + g.hedge("Knowledge")
    # "subject" leads with the dice the Inquiry's dot doubles; "rote" leads
    # with raw expectation and takes the doubling only by accident.
    hits, take = g.commit(want, double=inq[4] if SUBJECT else None)
    inq[1] += hits
    inq[3] += take                         # the dice lock to THIS card
    inq[0] += g.flip("Knowledge")          # the council reads your answer
    if inq[1] >= inq[0]:                   # answered: its dice come free
        g.row.remove(inq)
        g.exhausted += inq[3]
        # A solid answer narrows what the council can still produce - and the
        # harder the question, the bigger the concession. This is the reward
        # axis NAP's row has and a bare queue of Inquiries does not: it is
        # what makes WHICH question you answer first worth thinking about.
        if REWARD == "discard":
            for _ in range(max(1, inq[0] // 3)):
                if g.deck:
                    worst = max(range(len(g.deck)),
                                key=lambda i: g.deck[i][1])
                    g.deck.pop(worst)
        elif REWARD == "suspicion":
            g.suspicion = max(0, g.suspicion - 1)
    for c in g.row:                        # NAP's Demands, one per open card
        if c[2] < 0:
            g.hp -= 1
        else:
            g.hit(c[2])


def physical(g, policy):
    """BAT's Tyrant track: one track, damage carries left to right and the
    carry-over reveals the next segment, and what still stands replies as
    hard as its biggest surviving piece."""
    if not g.revealed and not g.face_down:
        return                             # the Tyrant is down
    known = float(sum(g.revealed))
    if not g.revealed:                     # nothing visible: the next segment
        known = float(BASE_TARGET + g.suspicion)
    if policy == "chip":
        want = float(g.revealed[0]) if g.revealed else known
    elif policy == "swing":
        want = known + g.hedge("Physical")
    elif policy == "finish":
        # Chip while the fight is young, then swing to put it down - leaving
        # it standing is what actually costs you.
        want = (known + g.hedge("Physical") if g.face_down <= 1
                else float(g.revealed[0]) if g.revealed else known)
    else:
        # adaptive: swing while the reply is dear, chip once what is left in
        # front of you cannot hit hard any more.
        want = (known + g.hedge("Physical")
                if (not g.revealed or max(g.revealed) > 2)
                else float(g.revealed[0]))
    hits, take = g.commit(want)
    g.exhausted += take

    track = list(g.revealed)
    if not track and g.face_down:          # the next Splice steps forward
        track.append(g.flip("Physical"))
        g.face_down -= 1
    i = 0
    while i < len(track):
        if hits >= track[i]:               # destroyed, and the rest carries on
            hits -= track[i]
            track[i] = 0
            i += 1
            if i == len(track) and hits > 0 and g.face_down:
                track.append(g.flip("Physical"))   # carry-over reveals it
                g.face_down -= 1
        else:
            track[i] -= hits
            break
    g.revealed = [s for s in track if s > 0]

    if g.revealed or g.face_down:
        # It is still standing, so it hits back - and the blow is as hard as
        # its biggest surviving segment, exactly as the Tyrant draws dice
        # equal to its best remaining Splice. This is NOT a Suspicion event:
        # trading blows with the thing is the encounter, not a slip.
        if REPLY == "splice":
            g.hit(min(6, max(g.revealed) if g.revealed else 2))
        else:
            g.hit(2 if (g.revealed and max(g.revealed) > 2) else 1)


def cover(g, policy):
    """AoS's Programs: allocate to Elements before rolling, one failure free
    - and allocation is NOT spending. An Element that passes hands its dice
    straight back; only a failed Element's dice exhaust. aos.py: ELEMENT_COST
    is 0 because "the printed rules explicitly say it is not". The council
    card lands on one Element after you have allocated."""
    n = g.rng.choice((3, 4, 4, 5))         # Advanced Programs show 4-5
    elems = [g.rng.choice((2, 2, 3)) + BASE_TARGET for _ in range(n)]
    for i in range(g.suspicion):           # scrutiny, spread over the alibi
        elems[i % n] += 1

    pad = g.hedge("Cover-Up") / float(n)
    order = sorted(range(n), key=lambda i: elems[i])   # cheapest first
    if policy == "triage" and n > 2:
        order = order[:-1]                 # take the free failure deliberately
    mean = sum(elems) / float(n)
    wants = {}
    for i in order:
        if policy == "thin":
            wants[i] = float(elems[i])     # the naive play: EV on the nose
        elif policy == "spread":
            wants[i] = mean + 1.0          # ignores the printed Targets
        elif policy == "robust":
            wants[i] = elems[i] + pad      # pad every Element against the flip
        else:                              # precise / triage: one die of margin
            wants[i] = elems[i] + 1.0

    g.available.sort(key=lambda c: -EV_REROLL[c])
    pool = list(g.available)
    alloc = dict((i, []) for i in range(n))
    for i in order:
        got = 0.0
        while pool and got < wants[i]:
            c = pool.pop(0)
            alloc[i].append(c)
            got += EV_REROLL[c]
    for i in alloc:
        for c in alloc[i]:
            g.available.remove(c)

    hit = g.rng.randrange(n)               # the council card, after allocation
    elems[hit] += g.flip("Cover-Up")

    fails = 0
    for i in range(n):
        if not alloc[i]:
            fails += 1                     # no dice left to cover it
            continue
        values = [roll(c, g.rng) for c in alloc[i]]
        tot = sum(values)
        if tot < elems[i]:                 # STR 2: one reroll of the misses
            tot += sum(roll(alloc[i][k], g.rng)
                       for k, v in enumerate(values) if v == 0)
        if tot < elems[i]:
            fails += 1
            g.exhausted += alloc[i]        # a failed Element burns its dice
        else:
            g.available += alloc[i]        # allocation is not spending
            if tot == elems[i] and g.exhausted:
                g.exhausted.sort(key=lambda c: EV_REROLL[c])
                g.available.append(g.exhausted.pop())   # AoS's optimal bonus
    if fails >= 2:                         # Catastrophic Failure
        g.pay()


# ---------------------------------------------------------------- the finale
def play(rng, know="declare", phys="swing", cov="thin"):
    g = Finale(rng)
    order = [d for d in DOMAINS for _ in range(3)]
    rng.shuffle(order)

    for attempt in range(ATTEMPTS):
        g.left = ATTEMPTS - attempt
        domain = order[attempt]
        if not ROW and g.open and g.queue:
            # NAP's Demand: the open question inflicts its printed penalty
            # for every slot it survives.
            d = g.queue[0][2]
            if d < 0:
                g.hp -= 1
                if g.hp <= 0:
                    return False
            else:
                g.hit(d)
        if not SHAPED:
            flat(g, domain)
        elif domain == "Knowledge":
            g.know_left = sum(1 for d in order[attempt:] if d == "Knowledge")
            (knowledge_row if ROW else knowledge)(g, know)
        elif domain == "Physical":
            physical(g, phys)
        else:
            cover(g, cov)
        if g.hp <= 0:
            return False
        g.recover()

    if SHAPED:
        # questions you never answered
        g.hp -= len(g.row) if ROW else len(g.queue)
        if g.revealed or g.face_down:      # and something still standing
            if TRACK_MUST_FALL:
                return False               # BAT: the Tyrant has to go down
            g.hp -= 1
    return g.hp >= 1


def run(games=GAMES, seed=11, know="declare", phys="swing", cov="thin",
        **over):
    saved = {k: globals()[k] for k in over}
    globals().update(over)
    rng = random.Random(seed)
    try:
        return 100.0 * sum(1 for _ in range(games)
                           if play(rng, know, phys, cov)) / games
    finally:
        globals().update(saved)


def q(domain, value):
    """A Q override: q("Physical", 0.75) keeps the other two adaptive."""
    d = dict(Q)
    d[domain] = value
    return d


def mono(domain, games=4000, seed=11, know="declare", phys="swing",
         cov="thin", **over):
    """One encounter, nine attempts of it, to price each shape on its own."""
    saved = {k: globals()[k] for k in over}
    globals().update(over)
    rng = random.Random(seed)
    try:
        wins = 0
        for _ in range(games):
            g = Finale(rng)
            alive = True
            for attempt in range(ATTEMPTS):
                g.left = ATTEMPTS - attempt
                # Three encounters of the same domain, not one nine long:
                # the encounters are 3 attempts by design.
                if not g.queue:
                    g.queue = [[0, 0, rng.choice(nap.DEMAND_PENALTY)]
                               for _ in range(INQUIRIES)]
                if not g.revealed and not g.face_down:
                    g.face_down = SEGMENTS
                if g.open and g.queue:
                    d = g.queue[0][2]
                    if d < 0:
                        g.hp -= 1
                    else:
                        g.hit(d)
                    if g.hp <= 0:
                        alive = False
                        break
                if domain == "flat":
                    flat(g, "Knowledge")
                elif domain == "Knowledge":
                    g.know_left = ATTEMPTS - attempt
                    if ROW and not g.row:
                        g.row = [[0, 0, rng.choice(nap.DEMAND_PENALTY), [],
                                  rng.choice(EXAM_DOTS)]
                                 for _ in range(INQUIRIES)]
                    (knowledge_row if ROW else knowledge)(g, know)
                elif domain == "Physical":
                    physical(g, phys)
                else:
                    cover(g, cov)
                if g.hp <= 0:
                    alive = False
                    break
                g.recover()
            wins += alive and g.hp >= 1
        return 100.0 * wins / games
    finally:
        globals().update(saved)


if __name__ == "__main__":
    print("PROTOTYPE - three encounters, each shaped like its own game")
    print("=" * 76)
    print("%d finales a cell. Knowledge is a queue that backs up (NAP),"
          % GAMES)
    print("Physical is one track chewed down that hits back (BAT), Cover-Up")
    print("is three allocations that tolerate one failure each (AoS).")

    print()
    print("1. WHAT THE SHAPING COSTS IN DIFFICULTY")
    print("   The flat control is finale6's single number, same deck, same")
    print("   dice, same Suspicion row. The shapes carry their own costs -")
    print("   Demands, replies, Catastrophic Failures - so the pitch moves.")
    print("   %-20s %10s %12s %12s"
          % ("pitch", "flat", "shaped/flat", "shaped/splice"))
    for base, bonus in ((0, 1), (0, 2), (0, 3), (1, 2)):
        a = run(SHAPED=False, BASE_TARGET=base, MATCH_BONUS=bonus)
        b = run(BASE_TARGET=base, MATCH_BONUS=bonus, REPLY="flat")
        c = run(BASE_TARGET=base, MATCH_BONUS=bonus, REPLY="splice")
        print("   base %d, match +%-9d %9.1f%% %11.1f%% %12.1f%%"
              % (base, bonus, a, b, c))
        sys.stdout.flush()

    print()
    print("2. EACH SHAPE PRICED ON ITS OWN")
    print("   Nine attempts of one domain - three encounters of it, since an")
    print("   encounter is three attempts long.")
    print("   %-26s %11s" % ("all nine attempts are", "win"))
    for d in ("flat", "Knowledge", "Physical", "Cover-Up"):
        print("   %-26s %10.1f%%" % (d, mono(d, games=8000)))
        sys.stdout.flush()

    print()
    print("3. IS THERE A DECISION IN EACH SHAPE?")
    print("   Each row sweeps one encounter's own tactic, the other two held.")
    print("   A gap near zero means that shape is decoration.")
    for label, key, options in (
            ("Knowledge (NAP)", "know", ("declare", "carry", "overstore")),
            ("Physical (BAT)", "phys", ("swing", "chip", "adaptive")),
            ("Cover-Up (AoS)", "cov",
             ("thin", "spread", "precise", "robust", "triage"))):
        ws = [run(**{key: opt}) for opt in options]
        print("   %-18s" % label
              + "  ".join("%s %.1f%%" % (o, w) for o, w in zip(options, ws))
              + "   gap %.1f" % (max(ws) - min(ws)))
        sys.stdout.flush()

    print()
    print("4. DO THE SHAPES WANT DIFFERENT PLAY? the hedge, per encounter")
    print("   One encounter's hedge is pinned to a fixed quantile; the other")
    print("   two stay adaptive. If the best column differed by row, one rule")
    print("   could not serve all three. It does not differ: this is the")
    print("   measurement that falsified the premise. Cover-Up's row is flat")
    print("   because the winning allocation (thin) ignores the pad entirely.")
    QS = (0.25, 0.5, 0.75, 1.0)
    print("   %-16s" % "pinned"
          + "".join("%10s" % ("q%.2f" % x) for x in QS)
          + "%11s %12s" % ("adaptive", "best"))
    for domain in DOMAINS:
        ws = [run(Q=q(domain, x)) for x in QS]
        base = run()
        print("   %-16s" % domain + "".join("%9.1f%%" % w for w in ws)
              + "%10.1f%%" % base + "%12s" % ("q%.2f" % QS[ws.index(max(ws))]))
        sys.stdout.flush()

    print()
    print("5. NAP'S ROW, SIX WAYS - the negative result, kept because it is")
    print("   the finding. Among the options that are actually competitive")
    print("   the spread is under 2.5 points; the big gaps below are storing")
    print("   being strictly WORSE, not a live decision.")
    print("   %-38s %9s %8s" % ("variant", "best", "gap"))
    for label, kw, key, opts in (
            ("queue, answer or carry", dict(ROW=False, EXAM_SIZED=False),
             "know", ("declare", "carry", "judge")),
            ("queue, storing policies", dict(ROW=False, EXAM_SIZED=True),
             "know", ("declare", "split", "pace")),
            ("the parallel row", dict(ROW=True, EXAM_SIZED=False,
                                      REWARD="none", SUBJECT=False),
             "know", ("rote", "closest", "biggest", "silence")),
            ("the row, with a reward for answering",
             dict(ROW=True, EXAM_SIZED=False, REWARD="discard", SUBJECT=False),
             "know", ("rote", "closest", "biggest", "silence")),
            ("the row, with printed subject dots",
             dict(ROW=True, EXAM_SIZED=False, REWARD="none", SUBJECT=True),
             "know", ("rote", "closest", "silence", "subject"))):
        ws = [run(phys="swing", cov="thin", MATCH_BONUS=1,
                  **dict(kw, **{key: o})) for o in opts]
        print("   %-38s %8.1f%% %7.1f"
              % (label, max(ws), max(ws) - min(ws)))
        sys.stdout.flush()

    print()
    print("6. DOES THE CAMPAIGN STILL REACH THE FINALE?")
    print("   %-34s %10s" % ("council deck", "win"))
    for label, kw in (("Tier III, as built", dict(TIER3=True)),
                      ("no tier module", dict(TIER3=False))):
        print("   %-34s %9.1f%%" % (label, run(**kw)))
        sys.stdout.flush()
    print()
    print("   And the Tyrant track's length, which is the one structural dial")
    print("   the Physical encounter has:")
    for segs in (2, 3, 4):
        print("   %-34s %9.1f%%" % ("%d segments" % segs, run(SEGMENTS=segs)))
        sys.stdout.flush()
