"""NRJ Imposter Scenario: survive nine Council attempts.

Rules source: rules/nrj.html. The 24 Council Test Scenarios - name, domain,
category and printed Target - are transcribed from the SCENARIOS table in
playtest/dist/suite.js.

Structure (rules/nrj.html:108):
  * Deal 4 Knowledge, 4 Physical and 4 Cover-Up Scenarios into a 12-card deck.
  * The Imposter begins at 5 HP / 2 STR / 3 REC with all 17 dice, and REC
    falls by 1 for every card in the Suspicion row.
  * Attempt Scenarios until 9 have been attempted; avoided ones do not count.
  * Win with at least 1 Health. Reaching 0 Health at any point loses.

Suspicion is uncapped: every failed Scenario in the Suspicion row adds +1
Target to every later Scenario.

THE RESEARCH POOL - what the earlier version of this file got wrong
-------------------------------------------------------------------
The pool is 18 cards but only 9 of them reduce anything. 9 are retained and
9 are Candidates, and "Candidate or damaged card" is worth 0. Retained values
depend on a category match (rules/nrj.html:133):

    Matching retained - NAP      -2
    Matching retained - BAT      -3   (Specimen -5)
    Matching retained - AoS      Stable -4, Overheated -2
    Retained, wrong category     -2
    Candidate or damaged         0

So the whole campaign is worth on the order of 25-30 Target reduction spread
across nine attempts against Targets of 8-10 plus accumulating Suspicion.
The previous model treated all 18 cards as spendable at a flat -3, roughly
double the real budget, which bought every Target into range and pinned the
win rate at 100%. That figure was an artifact and is gone.

SCENARIO TEXT: 23 of the 24 Council Tests now have their printed effect
modelled - the Suspicion clauses, the recovery clauses, the Research-card
clauses, the avoid clauses, the Crit clause, and the six that restrict which
dice may contribute. The exception is Across the Chamber, "look at the next
Scenario before rolling": the policy has no lookahead to spend that on, the
same case as BAT's Diagnostic Trial.

NOT MODELED: Research card effects beyond Target reduction.
"""
import random

from dice import COLORS, EV, EV_REROLL, roll

ATTEMPTS = 9
START_HP = 5
START_STR = 2
START_REC = 3

# ---------------------------------------------------------------------------
# Policy dials. None of these is a printed rule - each is a choice this model
# makes on the player's behalf, and each was an accident of list order until
# imposter.py measured it. Defaults are the behaviour as written.
#
#   RECOVER_PICK   "last" pops the end of the exhausted pile, which commit()
#                  filled strongest-first, so REC hands back the three WORST
#                  dice every attempt. "best" takes the strongest, and makes
#                  The Vote recover the most valuable color rather than the
#                  commonest.
#   BANISH_PICK    "last" pops the end of the available list, which begins
#                  [purple x4 ... yellow x4, red] - so the first banish
#                  throws away Red, the best die in the game. "weakest"
#                  takes the worst.
#   BANISH_FLOOR   dice-plus-pile at or below which a failure cannot be paid
#                  in dice. The printed rule is only "if you cannot banish 2
#                  available dice", so anything above 2 is this model's own
#                  caution; at 8 it withholds the trade from attempt 3 on,
#                  which is every attempt where a player would want it.
#   COMMIT_HOPELESS  whether to commit dice at a Target the pool cannot
#                  reach. Throwing them loses them for nothing, and because
#                  REC is capped by the size of the exhausted pile, a
#                  zero-commit attempt is the only way the pool climbs back.
# ---------------------------------------------------------------------------
# Measured over 4,000 finales each: recovering the strongest dice instead of
# the last-appended ones is worth +20.4 points, from 29.9% to 50.3%. It was
# the single largest distortion anywhere in the Imposter model. Banishing the
# weakest and lowering the floor to the printed condition are both worth 0.0,
# for a reason worth keeping: see imposter.py. Committing at an unreachable
# Target was tested and KEPT - holding the dice back costs 1.1 points,
# because "expected successes below the Target" is not the same as
# impossible, and a long throw can still crit its way home.
# ---------------------------------------------------------------------------
# CANDIDATE REPAIRS. All five default to the printed rules; proto/fix.py
# measures them. See imposter.py for the diagnosis they answer.
# ---------------------------------------------------------------------------
PARTIAL_PAY = 0            # banish 1 die per missing success, up to this many
BANISH_EXHAUSTED = False   # the failure trade may banish exhausted dice too
RECOVER_ON_PASS = 0        # extra dice recovered after a success
TARGET_SHIFT = 0           # flat shift on all 24 printed Targets
SUSPICION_CAP = None       # ceiling on Suspicion, None for uncapped
# APPLIED. "Your REC is 3 minus the number of cards in the Suspicion row."
# The pool used to collapse to exactly REC by the fourth attempt and sit
# there, so it could not run out and running out was never a worry. With the
# floor falling, the finale shows 35% of commit decisions at 2 dice or fewer
# and 13.5% with none at all - it leads the set on five of dicetension.py's
# six columns, every one that measures running out, though NAP's mean pool is
# lower - and lands at about 50.5% with 5 starting Health (50.3% in
# imposter.py's own pass, 50.9% in the cross-tab). proto/fix.py has the alternatives
# that were measured and rejected; the short version is that nothing which
# leaves the recovery floor fixed can create dice tension at all.
REC_PER_SUSPICION = 1      # REC falls 1 per this many Suspicion cards
REC_FLOOR = 0              # however far it falls, never below this
FAIL_BANISHES = 0          # dice committed to a failure that are banished

RECOVER_PICK = "best"
BANISH_PICK = "weakest"
BANISH_FLOOR = 2
COMMIT_HOPELESS = True

# (name, domain, category, printed Target) for the 24 Council Test Scenarios.
SCENARIOS = [
    ("The Physician's Greeting", "Knowledge", "Anatomy", 8),
    ("An Old Injury", "Knowledge", "Anatomy", 9),
    ("The Chamber Mechanism", "Knowledge", "Engineering", 8),
    ("Failed Apparatus", "Knowledge", "Engineering", 10),
    ("Order of Precedence", "Knowledge", "Procedure", 9),
    ("The Vote", "Knowledge", "Procedure", 8),
    ("A Disputed Citation", "Knowledge", "Theory", 9),
    ("The Long Argument", "Knowledge", "Theory", 10),
    ("The Ceremonial Seal", "Physical", "Power", 8),
    ("An Unwelcome Embrace", "Physical", "Power", 9),
    ("The Narrow Stair", "Physical", "Mobility", 8),
    ("A Sudden Fall", "Physical", "Mobility", 10),
    ("The Long Session", "Physical", "Defense", 9),
    ("Tainted Wine", "Physical", "Defense", 10),
    ("Across the Chamber", "Physical", "Senses", 8),
    ("The Darkened Corridor", "Physical", "Senses", 9),
    ("Tracks in the Yard", "Cover-Up", "Approach", 8),
    ("The Night Watchman's Account", "Cover-Up", "Approach", 9),
    ("An Open Window", "Cover-Up", "Concealment", 8),
    ("Someone Was Seen", "Cover-Up", "Concealment", 10),
    ("Rope Burns", "Cover-Up", "Restraint", 9),
    ("The Sedative Ledger", "Cover-Up", "Restraint", 9),
    ("The Missing Hours", "Cover-Up", "Extraction", 10),
    ("A Second Search", "Cover-Up", "Extraction", 8),
]

# Each game's cards carry one of its domain's four categories.
CATEGORIES = {
    "Knowledge": ["Anatomy", "Engineering", "Procedure", "Theory"],
    "Physical": ["Power", "Mobility", "Defense", "Senses"],
    "Cover-Up": ["Approach", "Concealment", "Restraint", "Extraction"],
}

POOL_MODES = ["standalone", "campaign"]

# Scenario effects that move the dice economy or the Suspicion count, and so
# change the outcome rather than just the flavor. Transcribed from the
# SCENARIOS table. The remaining effects - color and count restrictions on
# which dice may contribute, and the look-ahead effects - are not modeled.
RECOVER_ON_SUCCESS = {
    "The Chamber Mechanism": 2,        # "Success: recover 2 exhausted dice."
    "The Sedative Ledger": 3,          # "Success: recover 3 exhausted dice."
    "Tracks in the Yard": 2,           # one die of each of two colors
}
RECOVER_COLOR_ON_SUCCESS = "The Vote"  # recover all exhausted of one color
REMOVE_SUSPICION_ON_REVEAL = "A Second Search"
EXTRA_STR = "An Unwelcome Embrace"     # "+1 STR for this Scenario."
DISCARD_RESEARCH_ON_REVEAL = "Rope Burns"
ONE_NAP_CARD_ONLY = "The Long Argument"

# ---------------------------------------------------------------------------
# The clauses that constrain the dice themselves. Six restrict which dice may
# contribute and one changes what they are worth; none was modelled, and they
# are the Scenario text most likely to squeeze a pool that sits at REC from
# attempt 4 onward. SCENARIO_DICE gates the lot so the effect is measurable.
#
# A requirement that cannot be met has no printed resolution. Treated here as
# an attempt that fails - the Scenario is still avoidable beforehand, which
# is what a player would reach for.
# ---------------------------------------------------------------------------
SCENARIO_DICE = True
NEED_COLORS = {
    "An Old Injury": (("purple", "blue"), 2),       # 2 from this set
    "The Ceremonial Seal": (("purple",), 1),
}
NEED_DISTINCT = {"Order of Precedence": 3, "An Open Window": 3}
NEED_COUNT = {"The Long Session": 6}
FORBID_COLOR = {"The Darkened Corridor": "yellow"}
BIG_CRIT = "The Night Watchman's Account"      # a Crit counts as 3
SPECIAL_RECOVERY = "The Physician's Greeting"
AVOID_TO_TOP = "Someone Was Seen"


def fresh_dice():
    return [c for c in COLORS for _ in range(4)] + ["red"]


class Research(object):
    """One Research Pool card."""
    __slots__ = ("game", "category", "match", "off", "retained",
                 "can_avoid", "dot")

    def __init__(self, game, category, match, retained, can_avoid=False,
                 dot=None):
        self.game = game            # NAP | BAT | AoS
        self.category = category
        # NAP cards are the Final Exams actually faced, and an exam card
        # carries a recovery-color dot. Only The Physician's Greeting reads
        # it, but it reads it off the card that was spent.
        self.dot = dot
        self.match = match          # reduction on a category match
        self.off = 2 if retained else 0   # retained, wrong category
        self.retained = retained
        self.can_avoid = can_avoid

    def value_for(self, category):
        if not self.retained:
            return 0
        return self.match if self.category == category else self.off


# Each game contributes exactly 6 cards: its retained cards, then Candidates
# to fill. rules/{bat,nap,aos}.html, "Carrying X forward".
PER_GAME = 6
DOMAIN = {"NAP": "Knowledge", "BAT": "Physical", "AoS": "Cover-Up"}


def build_pool(rng, mode="standalone", bat_cards=None, aos_cards=None):
    """Six cards from each game: its retained cards, then Candidates.

    Standalone mode (rules/nrj.html, "Standalone Imposter mode") draws 3
    retained and 3 Candidates per game at random, so it always banks the
    maximum. A real campaign may bank less, and `bat_cards` / `aos_cards`
    take what the three games actually produced - supply.py measures that
    from the games themselves and reports what the difference is worth.

    NAP is the same either way: it faces exactly 3 Final Exams out of 12 and
    retains those 3, so it always contributes 3 retained and 3 Candidates.
    """
    pool = []

    def candidates(game, n):
        for _ in range(n):
            # Candidates reduce nothing; the AoS ones can still buy an avoid.
            pool.append(Research(game, rng.choice(CATEGORIES[DOMAIN[game]]),
                                 0, False, can_avoid=(game == "AoS")))

    # NAP: the 3 Final Exams faced, each with its own recovery-color dot.
    for _ in range(3):
        pool.append(Research("NAP", rng.choice(CATEGORIES["Knowledge"]), 2,
                             True, dot=rng.choice(COLORS)))
    candidates("NAP", PER_GAME - 3)

    # BAT: up to 3 Upgrades the Rats held when the battle began, at most 1 a
    # Specimen (-5 against an Upgrade's -3). Tyrant Splices fill the rest.
    if bat_cards is None:
        specimen = rng.random() < 0.5
        bat_cards = [5 if (specimen and i == 0) else 3 for i in range(3)]
    for value in bat_cards:
        pool.append(Research("BAT", rng.choice(CATEGORIES["Physical"]),
                             value, True))
    candidates("BAT", PER_GAME - len(bat_cards))

    # AoS: the 3 Advanced Programs faced, Stable or Overheated as faced.
    # Stable is pure reduction and cannot avoid; Overheated is weaker and can.
    if aos_cards is None:
        aos_cards = [rng.random() < 0.5 for _ in range(3)]
    for stable in aos_cards:
        pool.append(Research("AoS", rng.choice(CATEGORIES["Cover-Up"]),
                             4 if stable else 2, True,
                             can_avoid=not stable))
    candidates("AoS", PER_GAME - len(aos_cards))
    return pool


class Game(object):
    def __init__(self, mode="standalone", rng=None, bat_cards=None,
                 aos_cards=None):
        self.rng = rng or random.Random()
        self.hp = START_HP
        self.str_ = START_STR
        self.rec = START_REC
        self.suspicion = 0
        self.attempts = 0
        self.available = fresh_dice()
        self.exhausted = []
        self.banished = []
        self.pool = build_pool(self.rng, mode, bat_cards, aos_cards)

        # 4 Scenarios from each domain, shuffled into a 12-card deck.
        deck = []
        for domain in ("Knowledge", "Physical", "Cover-Up"):
            ids = [i for i, s in enumerate(SCENARIOS) if s[1] == domain]
            deck += self.rng.sample(ids, 4)
        self.rng.shuffle(deck)
        self.deck = deck
        self.next_discount = 0
        self.special_dot = None    # color dot of the first NAP card spent

    # ------------------------------------------------------------------
    def expected(self, dice):
        """Expected successes with STR 2 - one roll plus a reroll of misses."""
        return sum(EV_REROLL[c] for c in dice)

    def target_for(self, sid):
        name, domain, category, base = SCENARIOS[sid]
        target = base + TARGET_SHIFT
        susp = self.suspicion
        if SUSPICION_CAP is not None:
            susp = min(susp, SUSPICION_CAP)
        if name != "A Disputed Citation":      # its text ignores Suspicion
            target += susp
        if name == "The Missing Hours":        # +1 Target per Suspicion again
            target += susp
        return max(0, target - self.next_discount)

    def spend(self, sid, target):
        """Spend Research cards to bring the Target within reach.

        Reach is measured against the dice actually available. The policy
        rations the pool across the attempts still to come and prefers
        category matches, which are worth more than the flat wrong-category 2.
        """
        name, _, category, _ = SCENARIOS[sid]
        reach = self.expected(self.available)
        usable = [c for c in self.pool if c.value_for(category) > 0]
        if name == ONE_NAP_CARD_ONLY:      # "Spend at most one NAP card."
            nap_cards = [c for c in usable if c.game == "NAP"]
            for c in nap_cards[1:]:
                usable.remove(c)
        if not usable:
            return target
        usable.sort(key=lambda c: -c.value_for(category))
        # Spend whatever it takes to bring this Target inside the dice reach,
        # and nothing beyond that. Rationing the pool to an even per-attempt
        # share loses: the budget only wins attempts it fully closes, so it is
        # better to buy six Scenarios outright than to under-buy all nine.
        for card in list(usable):
            if reach >= target:
                break
            target -= card.value_for(category)
            self.pool.remove(card)
            if card.game == "NAP" and self.special_dot is None:
                self.special_dot = card.dot
        return max(0, target)

    def legal_pool(self, name):
        """The dice this Scenario allows to contribute."""
        banned = FORBID_COLOR.get(name) if SCENARIO_DICE else None
        return [c for c in self.available if c != banned]

    def can_attempt(self, name):
        """Whether the Scenario's dice requirement can be met at all."""
        if not SCENARIO_DICE:
            return True
        pool = self.legal_pool(name)
        if len(pool) < NEED_COUNT.get(name, 0):
            return False
        want = NEED_COLORS.get(name)
        if want and sum(1 for c in pool if c in want[0]) < want[1]:
            return False
        if len(set(pool)) < NEED_DISTINCT.get(name, 0):
            return False
        return True

    def commit(self, target, name=None):
        pool = sorted(self.legal_pool(name), key=lambda c: -EV[c])
        if not COMMIT_HOPELESS and \
                sum(EV_REROLL[c] for c in pool) < target:
            # The attempt fails whether or not dice are thrown at it, so keep
            # them. It also leaves the exhausted pile intact for REC, which
            # is the only way the pool climbs back up.
            return []
        take = []

        def grab(color):
            pool.remove(color)
            take.append(color)

        if SCENARIO_DICE:
            # Pay the requirement first, strongest qualifying dice first,
            # then fill toward the Target as usual.
            want = NEED_COLORS.get(name)
            if want:
                for c in [x for x in pool if x in want[0]][:want[1]]:
                    grab(c)
            if name in NEED_DISTINCT:
                for color in sorted(set(pool), key=lambda c: -EV[c]):
                    if len(set(take)) >= NEED_DISTINCT[name]:
                        break
                    if color not in take:
                        grab(color)
            while len(take) < NEED_COUNT.get(name, 0) and pool:
                grab(pool[0])
        got = sum(EV_REROLL[c] for c in take)
        while got < target and pool:
            got += EV_REROLL[pool[0]]
            grab(pool[0])
        return take

    def try_avoid(self, sid):
        """Discard an eligible AoS card to push the Scenario to the bottom."""
        if SCENARIOS[sid][0] == "A Sudden Fall":
            return False               # cannot be avoided with an AoS card
        eligible = [c for c in self.pool if c.can_avoid]
        if not eligible:
            return False
        # Prefer to give up a Candidate, which reduces nothing anyway.
        eligible.sort(key=lambda c: c.retained)
        self.pool.remove(eligible[0])
        if SCENARIOS[sid][0] == AVOID_TO_TOP:
            # "If avoided, put it on top instead of bottom." Avoiding it
            # buys one reveal, not a trip through the deck.
            self.deck.insert(0, sid)
        else:
            self.deck.append(sid)
        return True

    def attempt(self):
        if not self.deck:
            return False
        sid = self.deck.pop(0)
        name = SCENARIOS[sid][0]

        # Reveal text.
        if name == REMOVE_SUSPICION_ON_REVEAL:
            self.suspicion = max(0, self.suspicion - 1)
        elif name == DISCARD_RESEARCH_ON_REVEAL and self.pool:
            self.pool.pop(self.rng.randrange(len(self.pool)))

        target = self.target_for(sid)

        # Avoid only when the attempt looks hopeless even after spending.
        if self.expected(self.available) + 6 < target and self.try_avoid(sid):
            return self.hp > 0

        forced_fail = False
        if SCENARIO_DICE and not self.can_attempt(name):
            # "Commit at least 6 dice" with 3 in the pool, or a required
            # color the pool no longer holds. There is no printed resolution
            # for a requirement that cannot be met: avoid if an AoS card is
            # left, and otherwise take the failure without throwing anything
            # and without spending Research on it.
            if self.try_avoid(sid):
                return self.hp > 0
            forced_fail = True

        if not forced_fail:
            self.special_dot = None
            target = self.spend(sid, target)
            if name == SPECIAL_RECOVERY and self.special_dot:
                # "The first NAP card spent also performs Special Recovery":
                # recover all exhausted dice of that card's color dot. It
                # resolves at the spend step, so it feeds this attempt.
                keep = []
                for c in self.exhausted:
                    (self.available if c == self.special_dot
                     else keep).append(c)
                self.exhausted = keep
        take = [] if forced_fail else self.commit(target, name)
        for c in take:
            self.available.remove(c)
        values = [roll(c, self.rng) for c in take]
        if SCENARIO_DICE and name == BIG_CRIT:
            # "A Crit counts as 3 successes."
            values = [3 if v == 2 else v for v in values]
        rerolls = self.str_ + (1 if name == EXTRA_STR else 0) - 1
        for _ in range(max(0, rerolls)):
            total = sum(values)
            if total >= target:
                break
            # One throw. Misses cost nothing to rethrow; further available
            # dice may join them; and all of it is chosen beforehand.
            again = [k for k, v in enumerate(values) if v == 0]
            hits = [k for k, v in enumerate(values) if v == 1]
            add = []
            expected = total + sum(EV[take[k]] for k in again)
            for c in sorted(self.legal_pool(name), key=lambda c: -EV[c]):
                if expected >= target:
                    break
                if add.count(c) < self.legal_pool(name).count(c):
                    add.append(c)
                    expected += EV[c]
            # A thrown die comes back as at most a Crit. If even that falls
            # short, trading basic hits is the only way to find one, and only
            # worth it when trading enough of them gets there.
            ceiling = (total + sum(2 - values[k] for k in again)
                       + 2 * len(add))
            if ceiling < target:
                for k in hits:
                    again.append(k)
                    ceiling += 1
                    if ceiling >= target:
                        break
                else:
                    again = [k for k in again if values[k] == 0]
            if not again and not add:
                break
            for c in add:
                self.available.remove(c)
            again += range(len(values), len(values) + len(add))
            take = take + add
            values = values + [0] * len(add)
            for k in again:
                values[k] = roll(take[k], self.rng)
                if SCENARIO_DICE and name == BIG_CRIT and values[k] == 2:
                    values[k] = 3
        total = sum(values)
        self.exhausted += take

        if PARTIAL_PAY and total < target:
            # "If you fall short, you may banish 1 available or exhausted die
            # per missing success to succeed anyway." Paid out of the dice
            # just thrown, so it is payable; and the banished dice never come
            # back, so the pool - and the REC floor with it - really falls.
            short = target - total
            if short <= PARTIAL_PAY:
                payable = self.exhausted + self.available
                if len(payable) >= short:
                    payable.sort(key=lambda c: EV[c])
                    for c in payable[:short]:
                        if c in self.exhausted:
                            self.exhausted.remove(c)
                        else:
                            self.available.remove(c)
                        self.banished.append(c)
                    total = target

        if total < target and FAIL_BANISHES and take:
            # "Dice committed to a failed Scenario are banished instead of
            # exhausted." A drain failure drives, so the pool declines over
            # the finale instead of sitting on the REC floor.
            self.exhausted.sort(key=lambda c: -EV[c])
            for _ in range(min(FAIL_BANISHES, len(self.exhausted))):
                self.banished.append(self.exhausted.pop())

        if total < target:
            self.suspicion += 2 if name == "Failed Apparatus" else 1
            # Lose 1 Health or banish 2 available dice. Keep Health while the
            # dice can pay, but not once the pool is too thin to attempt with.
            payable = len(self.available)
            if BANISH_EXHAUSTED:
                payable += len(self.exhausted)
            can_banish = payable >= 2 and name != "Tainted Wine"
            if can_banish and \
                    len(self.available) + len(self.exhausted) > BANISH_FLOOR:
                for _ in range(2):
                    if self.available and (not BANISH_EXHAUSTED
                                           or not self.exhausted):
                        if BANISH_PICK == "weakest":
                            self.available.sort(key=lambda c: -EV[c])
                        self.banished.append(self.available.pop())
                    else:
                        # Spend the worst of what was just thrown first: an
                        # exhausted die is only worth what REC would give back.
                        self.exhausted.sort(key=lambda c: -EV[c])
                        self.banished.append(self.exhausted.pop())
            else:
                self.hp -= 1
            self.next_discount = 0
        else:
            self.next_discount = 1 if name == "The Narrow Stair" else 0
            # Success text that restores dice - the finale's real engine.
            extra = RECOVER_ON_SUCCESS.get(name, 0) + RECOVER_ON_PASS
            if RECOVER_PICK == "best":
                self.exhausted.sort(key=lambda c: EV[c])
            for _ in range(min(extra, len(self.exhausted))):
                self.available.append(self.exhausted.pop())
            if name == RECOVER_COLOR_ON_SUCCESS and self.exhausted:
                if RECOVER_PICK == "best":
                    # "Recover all exhausted dice of one color" - worth the
                    # most total EV, not simply the commonest color.
                    best = max(COLORS + ["red"],
                               key=lambda c: self.exhausted.count(c) * EV[c])
                else:
                    best = max(COLORS + ["red"], key=self.exhausted.count)
                keep = []
                for c in self.exhausted:
                    (self.available if c == best else keep).append(c)
                self.exhausted = keep

        if RECOVER_PICK == "best":
            # Weakest-first, so pop() hands back the strongest.
            self.exhausted.sort(key=lambda c: EV[c])
        rec = self.rec
        if REC_PER_SUSPICION:
            # "Your REC is reduced by 1 for every N cards in the Suspicion
            # row." The pool's floor stops being fixed, so a bad run costs
            # dice as well as Health.
            rec = max(REC_FLOOR, rec - self.suspicion // REC_PER_SUSPICION)
        for _ in range(min(rec, len(self.exhausted))):
            self.available.append(self.exhausted.pop())
        self.attempts += 1
        return self.hp > 0

    def play(self):
        guard = 0
        while self.attempts < ATTEMPTS and guard < 60:
            guard += 1
            if not self.attempt():
                return False
        return self.hp > 0 and self.attempts >= ATTEMPTS


def run(mode="standalone", games=20000, seed=20, bat_cards=None,
        aos_cards=None):
    rng = random.Random(seed)
    wins = 0
    for _ in range(games):
        if Game(mode, rng, bat_cards, aos_cards).play():
            wins += 1
    return wins / float(games)


if __name__ == "__main__":
    for m in POOL_MODES:
        print("%-11s %.1f%%" % (m, 100 * run(m, 5000)))
