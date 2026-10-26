"""NRJ Imposter Scenario: survive nine Council attempts.

Rules source: rules/nrj.html. The 24 Council Test Scenarios - name, domain,
category and printed Target - are transcribed from the SCENARIOS table in
playtest/dist/suite.js.

Structure (rules/nrj.html:108):
  * Deal 4 Knowledge, 4 Physical and 4 Cover-Up Scenarios into a 12-card deck.
  * The Imposter begins at 4 HP / 2 STR / 3 REC with all 17 dice.
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

NOT MODELED: the per-Scenario reveal/success/failure text (the two Scenarios
whose text changes how Suspicion applies are implemented; the other 22 effects
are not), and Research card effects beyond Target reduction.
"""
import random

from dice import COLORS, EV, EV_REROLL, roll

ATTEMPTS = 9
START_HP = 4
START_STR = 2
START_REC = 3

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


def fresh_dice():
    return [c for c in COLORS for _ in range(4)] + ["red"]


class Research(object):
    """One Research Pool card."""
    __slots__ = ("game", "category", "match", "off", "retained", "can_avoid")

    def __init__(self, game, category, match, retained, can_avoid=False):
        self.game = game            # NAP | BAT | AoS
        self.category = category
        self.match = match          # reduction on a category match
        self.off = 2 if retained else 0   # retained, wrong category
        self.retained = retained
        self.can_avoid = can_avoid

    def value_for(self, category):
        if not self.retained:
            return 0
        return self.match if self.category == category else self.off


def build_pool(rng, mode="standalone", bat_cards=None):
    """9 retained cards plus 9 Candidates.

    Standalone mode (rules/nrj.html:176) randomizes the selection, including
    Stable versus Overheated for the retained AoS Advanced Programs, and keeps
    BAT to at most 1 Specimen. Campaign mode is modeled as the same draw -
    the model has no cross-game state to carry - so the two match here.
    """
    pool = []
    for _ in range(3):
        pool.append(Research("NAP", rng.choice(CATEGORIES["Knowledge"]), 2, True))
    if bat_cards is None:
        specimen = rng.random() < 0.5  # at most 1 Specimen may be retained
        bat_cards = [5 if (specimen and i == 0) else 3 for i in range(3)]
    # Only the Upgrades that survived on living Rats are retained; anything
    # short of three is simply not banked, and buys nothing in the finale.
    for value in bat_cards:
        pool.append(Research("BAT", rng.choice(CATEGORIES["Physical"]),
                             value, True))
    for _ in range(3):
        cat = rng.choice(CATEGORIES["Cover-Up"])
        stable = rng.random() < 0.5
        # Retained Stable Programs are pure reduction and cannot avoid;
        # retained Overheated ones may be discarded to avoid.
        pool.append(Research("AoS", cat, 4 if stable else 2, True,
                             can_avoid=not stable))
    for game in ("NAP", "BAT", "AoS"):
        domain = {"NAP": "Knowledge", "BAT": "Physical",
                  "AoS": "Cover-Up"}[game]
        for _ in range(3):
            # Candidates reduce nothing; the AoS ones can still buy an avoid.
            pool.append(Research(game, rng.choice(CATEGORIES[domain]), 0,
                                 False, can_avoid=(game == "AoS")))
    return pool


class Game(object):
    def __init__(self, mode="standalone", rng=None, bat_cards=None):
        self.rng = rng or random.Random()
        self.hp = START_HP
        self.str_ = START_STR
        self.rec = START_REC
        self.suspicion = 0
        self.attempts = 0
        self.available = fresh_dice()
        self.exhausted = []
        self.banished = []
        self.pool = build_pool(self.rng, mode, bat_cards)

        # 4 Scenarios from each domain, shuffled into a 12-card deck.
        deck = []
        for domain in ("Knowledge", "Physical", "Cover-Up"):
            ids = [i for i, s in enumerate(SCENARIOS) if s[1] == domain]
            deck += self.rng.sample(ids, 4)
        self.rng.shuffle(deck)
        self.deck = deck
        self.next_discount = 0

    # ------------------------------------------------------------------
    def expected(self, dice):
        """Expected successes with STR 2 - one roll plus a reroll of misses."""
        return sum(EV_REROLL[c] for c in dice)

    def target_for(self, sid):
        name, domain, category, base = SCENARIOS[sid]
        target = base
        if name != "A Disputed Citation":      # its text ignores Suspicion
            target += self.suspicion
        if name == "The Missing Hours":        # +1 Target per Suspicion again
            target += self.suspicion
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
        return max(0, target)

    def commit(self, target):
        pool = sorted(self.available, key=lambda c: -EV[c])
        take, got = [], 0.0
        for c in pool:
            if got >= target:
                break
            take.append(c)
            got += EV_REROLL[c]
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

        target = self.spend(sid, target)
        take = self.commit(target)
        for c in take:
            self.available.remove(c)
        values = [roll(c, self.rng) for c in take]
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
            for c in sorted(self.available, key=lambda c: -EV[c]):
                if expected >= target:
                    break
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
        total = sum(values)
        self.exhausted += take

        if total < target:
            self.suspicion += 2 if name == "Failed Apparatus" else 1
            # Lose 1 Health or banish 2 available dice. Keep Health while the
            # dice can pay, but not once the pool is too thin to attempt with.
            can_banish = len(self.available) >= 2 and name != "Tainted Wine"
            if can_banish and len(self.available) + len(self.exhausted) > 8:
                for _ in range(2):
                    self.banished.append(self.available.pop())
            else:
                self.hp -= 1
            self.next_discount = 0
        else:
            self.next_discount = 1 if name == "The Narrow Stair" else 0
            # Success text that restores dice - the finale's real engine.
            extra = RECOVER_ON_SUCCESS.get(name, 0)
            for _ in range(min(extra, len(self.exhausted))):
                self.available.append(self.exhausted.pop())
            if name == RECOVER_COLOR_ON_SUCCESS and self.exhausted:
                best = max(COLORS + ["red"], key=self.exhausted.count)
                keep = []
                for c in self.exhausted:
                    (self.available if c == best else keep).append(c)
                self.exhausted = keep

        for _ in range(min(self.rec, len(self.exhausted))):
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


def run(mode="standalone", games=20000, seed=20, bat_cards=None):
    rng = random.Random(seed)
    wins = 0
    for _ in range(games):
        if Game(mode, rng, bat_cards).play():
            wins += 1
    return wins / float(games)


if __name__ == "__main__":
    for m in POOL_MODES:
        print("%-11s %.1f%%" % (m, 100 * run(m, 5000)))
