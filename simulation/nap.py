"""Nobulous' Apprenticeship Program: work the Assignment row, then sit three
Final Exams.

Rules source: rules/nap.html. Card data is transcribed verbatim - the 26
Tasks, 6 Setbacks and 6 Opportunities from the NAP_TASKS / NAP_SETBACKS /
NAP_OPPS tables in playtest/dist/suite.js, the 12 Final Exams from the EXAMS
table in generator/build_nap.py.

Win condition (rules/nap.html:43, :194): earning 6 Credits does NOT win. It
ends the apprenticeship. You then sit three mandatory Final Exams and must
finish all three with at least 1 Health. Arriving short of 6 Credits does not
lose either - it costs dice and leaves the exam Targets unreduced.

FINF is the difficulty dial (rules/nap.html:143), Standard is -1.

WHAT IS NOT MODELED
  * Apprentice abilities. All six are 2 HP / 2 STR / 2 REC and "differ only
    in abilities", so the six are identical here by construction. Each now
    prints one ability instead of two; neither version is modeled.
  * Separate rows per Time Slot. One row is modeled, so a FINF card naming
    another slot is applied when that slot comes round, and a Reduce card
    reaches only the row in front of you.
  * Per-card Demand penalties. The rules say an Assignment left unresolved on
    its Demand side "inflicts its printed Demand penalty" every slot it
    survives; the penalties are card text. Modeled as a flat 1 Health.
  * Request effects, Opportunity effects, Setback text, subject-icon wilds.
"""
import random

from dice import COLORS, EV, roll

# (target, demand, recovery dot, skulls) for the 26 Tasks, deck order.
TASKS = [
    (2, 3, "Y", 0), (3, 5, "G", 1), (4, 5, "B", 1), (5, 7, "P", 2),
    (3, 4, "Y", 0), (3, 4, "G", 0), (3, 5, "B", 0), (5, 6, "P", 0),
    (4, 5, "G", 1), (4, 9, "B", 1), (4, 5, "B", 1), (4, 9, "P", 1),
    (5, 9, "P", 1), (6, 7, "P", 1), (3, 5, "Y", 1), (4, 9, "B", 2),
    (5, 7, "P", 2), (3, 4, "G", 0), (4, 9, "Y", 1), (4, 5, "G", 0),
    (3, 4, "Y", 0), (3, 4, "G", 0), (4, 5, "B", 0), (6, 8, "P", 1),
    (4, 9, "B", 1), (4, 5, "P", 0),
]

# Subject per Task; the last six are unmarked and earn no Credit.
SUBJECTS = ["Theory", "Anatomy", "Engineering", "Anatomy", "Procedure",
            "Theory", "Anatomy", "Engineering", "Engineering", "Engineering",
            "Engineering", "Procedure", "Procedure", "Anatomy", "Anatomy",
            "Theory", "Procedure", "Theory", "Procedure", "Theory",
            None, None, None, None, None, None]

# Printed Demand penalty per Task, applied at the end of every slot the Task
# survives on its Demand side. Transcribed from the last field of each entry
# in the TASKS table in generator/build_nap.py: 0 = exhaust 1 available die,
# -1 = lose 1 Health, 2 = exhaust 2 available dice.
DEMAND_PENALTY = [1, -1, 2, -1, 1, 1, -1, 1, -1, 1, 2, -1, 1, -1,
                  -1, 2, -1, 1, -1, 1, 1, 1, 1, -1, -1, 2]

# Setbacks print a single Target and no Demand side. Their standing cost is
# "At the start of this Time Slot, if this Setback has no stored dice, exhaust
# 1 available die", and while one is on the row "No other Assignment may be
# worked until this Setback is resolved."
SETBACKS = [(6, "Y"), (6, "G"), (7, "G"), (7, "B"), (8, "B"), (8, "P")]
OPPORTUNITIES = [(3, "Y"), (3, "Y"), (4, "Y"), (4, "Y"), (3, "G"), (4, "G")]

# (subject, recovery dot, base Target) for the 12 Final Exams, 3 per subject.
EXAMS = [
    ("Anatomy", "B", 5), ("Anatomy", "Y", 6), ("Anatomy", "P", 6),
    ("Theory", "G", 5), ("Theory", "P", 6), ("Theory", "Y", 7),
    ("Engineering", "G", 5), ("Engineering", "B", 6), ("Engineering", "B", 6),
    ("Procedure", "Y", 6), ("Procedure", "P", 7), ("Procedure", "G", 7),
]

SUBJECT_LIST = ["Anatomy", "Engineering", "Procedure", "Theory"]
DOT_COLOR = {"P": "purple", "B": "blue", "G": "green", "Y": "yellow"}

# All six begin at 2/2/2 and differ only in abilities (rules/nap.html:33).
APPRENTICES = ["Prodigy", "Slacker", "Technician",
               "Savant", "Opportunist", "Lab Rat"]

# FINF settings. Standard difficulty is -1. Negative numbers are uses of the
# removal power; positive numbers add Assignments to later Time Slots.
FINF_SETTINGS = ["+3", "+2", "+1", "-1", "-2", "-3"]

# ---------------------------------------------------------------------------
# NRJ overlay tiers. Each tier includes the ones before it.
#   I   - 3 of the 4 Following Setbacks replace 3 base Setbacks
#   II  - 4 Impostor Tasks, one per subject, each replacing a Credit Task
#   III - 6 Devious Opportunities replace the 6 Opportunities
# Card data from the FOLLOWING / IMPOSTOR / DEVIOUS tables in build_nrj.py.
# ---------------------------------------------------------------------------

# (Target, extra cost per slot unresolved). All four are harsher than the base
# Setbacks they displace and carry into the next Time Slot.
FOLLOWING = [(7, 1), (7, 1), (8, 1), (8, 1)]

# (subject, Request Target, Demand Target). Mandatory, and they grant no
# Credits - "You still have to clear them; clearing them advances nothing."
IMPOSTOR = [("Anatomy", 5, 6), ("Engineering", 4, 5),
            ("Procedure", 4, 5), ("Theory", 4, 5)]

# (Target, payout). Two resolve on completion; the other four are kept and
# spent during the Final Exam, which is where NAP actually kills you.
#   free_task      exhaust 2 dice to finish a cheap non-Credit Task now
#   credit         1 Credit now
#   exam_recover   recover 3 dice before one exam
#   exam_reroll    reroll the misses on one exam
#   exam_target    one exam's Target drops by 3
#   exam_ignore    ignore one exam's printed restriction (unmodeled here)
DEVIOUS = [(3, "free_task"), (3, "exam_recover"), (3, "credit"),
           (3, "exam_reroll"), (4, "exam_target"), (3, "exam_ignore")]

TIERS = ["none", "I", "II", "III"]

# An earlier draft of rules/nap.html said STR also capped completions in a
# slot. It never did, and the rulebook no longer claims it. The knob stays so
# the old behaviour can be reproduced. It binds
# only when stored progress lets one roll finish several cards, which needs
# SPLIT_ROLLS below; measured at about 0.1% of slots, worth under 0.5 points
# of win rate.
# A Strategy roll may be spent rerolling the dice just thrown instead of
# committing a fresh batch. Rerolling a miss is free; rerolling a hit is only
# worth it when a Crit is the one thing that still finishes the card.
PUSH_REROLL = True
TARGET_DELTA = 0   # flat rise on every printed Assignment Target

STR_CAPS_COMPLETIONS = False
# A roll's dice may be applied to more than one Assignment, so a slot can
# finish several cards that already hold stored progress. With this False the
# model commits each roll to a single card and the cap above cannot bind.
SPLIT_ROLLS = True
# How many cards one roll may be spread over; beyond 4 the row runs out anyway.
CARDS_PER_ROLL = 4
# Play the printed card text: Request rewards, Opportunity payouts and the
# Apprentice ability. False reproduces the older, card-text-free model.
PLAY_THE_CARDS = True
# How many dice the policy refuses to spend. 3 is cautious; a player chasing a
# finish will go lower.
DICE_RESERVE = 2
# Reduce variant: with this True a FINF card is not tied to its number - any
# held card removes any non-Final-Exam card from the ACTIVE Time Slot.
FINF_REDUCE_ANY_CARD = False
# Deck composition, fixed by the rules: 3 of the 6 Setbacks and all 6
# Opportunities. Exposed so the lever can be measured.
SETBACKS_IN_DECK = 3
OPPORTUNITIES_IN_DECK = 6

# Opportunity levers, all printed-card changes:
OPP_TARGET_DELTA = 0      # cheaper to finish
OPP_STORES = False        # progress banks like a Task instead of being lost
OPP_DICE_RETURN = False   # dice spent on one come back available, not exhausted
OPP_RETURN_ON_WIN = True  # with the above: do the dice come back on a finish too,
                          # or only when the attempt falls short?
OPP_REWARD_PLUS = 0       # pay more: +N dice recovered, bonuses last the Day
# A Devious exam coupon may be discarded during the apprenticeship to recover
# 2 exhausted dice, so holding one is never a dead card.
DEVIOUS_CASH_EARLY = False
# Spend a Devious coupon to ignore one Setback's restrictions: it stops
# billing upkeep, stops demanding to be worked first, and - for a base
# Setback - stops locking the row. The card stays in the row unresolved.
DEVIOUS_IGNORE_SETBACK = True
# Spend a coupon to move a Setback to another Time Slot. The model has one
# row, so this counts only the distance bought: that many slots dormant.
DEVIOUS_MOVE_SLOTS = 0

OPP_COUPONS = True        # a finished Opportunity is KEPT and spent later on an
                          # Assignment, instead of paying out on the spot

# One coupon per Opportunity, in deck order, keeping each card's own fiction:
#   soak      cancel one Health loss             Take an Unauthorized Break
#   wild      one die counts as any color        Raid the Supply Closet
#   boost     +1 success on a roll              Borrow Better Instruments
#   shortcut  -2 from one Assignment's need     Study Nobulous' Notes
#   assist    +2 successes, no roll             Salvage Useful Components
#   crit3     one Crit counts as 3              Practice on a Spare Brain
COUPON = ["soak", "wild", "boost", "shortcut", "assist", "crit3"]

# Request-side reward per Task, by deck order. The condition is what the model
# can actually check; effects that only reorder the deck are left out.
#   recover_committed  take one of the dice just committed back
#   recover_any        take one exhausted die back
#   recover_dot        take back an exhausted die of the card's dot color
#   hp / rec / str     +1, permanently for rec and str
#   bonus              counts as +1 success while resolving (applied at roll)
REQUEST_REWARD = {
    0: ("recover_committed", "exact"), 1: ("recover_committed", "few_dice"),
    3: ("bonus", "three_colors"), 4: ("recover_committed", "no_crit"),
    5: ("bonus", "primary"), 6: ("hp", "exact"),
    8: ("recover_committed", "exact"), 9: ("recover_committed", "exact"),
    10: ("recover_committed", "exact"), 12: ("recover_committed", "three_dice"),
    13: ("rec", "always"), 14: ("recover_committed", "one_attempt"),
    15: ("bonus", "three_colors"), 16: ("recover_committed", "no_stored"),
    17: ("recover_committed", "primary"), 18: ("recover_committed", "four_dice"),
    21: ("recover_any", "always"), 22: ("recover_committed", "few_dice"),
    23: ("str", "always"), 24: ("recover_any", "one_attempt"),
    25: ("recover_committed", "crit"),
}
# Crits of one color count as 3 successes on these Tasks.
CRIT_COLOR = {2: "blue", 7: "purple", 11: "purple"}

# Opportunity payouts, in deck order, matching generator/build_nap.py.
OPPORTUNITY_REWARD = ["hp", "recover2", "str_next", "rec_next", "recover3", "crit_next"]

# One ability per Apprentice. Prodigy's wild rule needs per-die color matching
# the model does not do, so it plays as no ability.
# Candidate Slacker abilities. "discard" is the printed one.
#   discard          once per Day, drop the worst Assignment in this slot
#   morning_discard  the same, but only during a Morning - the Time Slot card
#                    is the tracker, so nothing extra is written down
#   dodge_setback    passive: a revealed Setback need not be taken as Primary
#   small_row        passive: the row holds 3 Assignments instead of 4
SLACKER_ABILITY = "small_row"

# Technician candidates.
#   setback_window  printed: a Setback holding a die lets you work one other
#                   Assignment. Dead once Following Setbacks stop blocking.
#   repair_bonus    the first die committed to a Setback each Time Slot
#                   counts as 2 successes
#   repair_reward   completing a Setback recovers 2 exhausted dice
#   exempt          B: a Setback holding a die stops restricting you
TECHNICIAN_ABILITY = "repair_reward"

ABILITIES = {"Prodigy": None, "Slacker": "discard", "Technician": "setback_window",
             "Savant": "wide_recovery", "Opportunist": "dot_recovery",
             "Lab Rat": "soak"}

CREDITS_TO_LEAVE = 6      # Easy 5, Standard 6, Hard 7, Nobulous 8
ROW_MAX = 4
SLOTS_PER_DAY = 3


def fresh_dice():
    return [c for c in COLORS for _ in range(4)] + ["red"]


class Card(object):
    __slots__ = ("kind", "subject", "target", "demand", "dot", "skulls",
                 "on_demand", "rotated", "free", "stored", "stored_dice",
                 "penalty", "upkeep", "devious", "slot", "index", "ignored",
                 "away")

    def __init__(self, kind, target, demand, dot, skulls=0, subject=None,
                 penalty=1):
        self.kind = kind            # task | setback | opportunity | finf
        self.slot = None            # FINF only: the Time Slot it names
        self.index = None           # position in its printed deck
        self.subject = subject
        self.target = target
        self.demand = demand
        self.dot = dot
        self.skulls = skulls
        self.on_demand = False
        self.rotated = False        # Opportunities get one extra slot
        self.free = False           # added by FINF/skull: Skulls ignored
        self.stored = 0             # successes banked on the card
        self.stored_dice = []       # locked to the card until it resolves
        self.penalty = penalty      # printed Demand penalty; -1 = 1 Health
        self.upkeep = 0             # Following Setback: dice per slot
        self.ignored = False        # a Devious coupon was spent on it
        self.away = 0               # Time Slots spent in another row
        self.devious = None         # Devious Opportunity: (recover, credit)

    def need(self):
        return self.demand if self.on_demand else self.target

    def remaining(self):
        """Successes still wanted. Opportunities store no progress."""
        if self.kind == "opportunity":
            return self.need()
        return max(0, self.need() - self.stored)


class Game(object):
    def __init__(self, apprentice="Prodigy", finf="-1", rng=None, tier="none"):
        self.rng = rng or random.Random()
        self.apprentice = apprentice
        self.tier = tier
        self.hp = 2
        self.str_ = 2
        self.rec = 2
        self.credits = dict((s, 0) for s in SUBJECT_LIST)
        self.credit_total = 0
        self.available = fresh_dice()
        self.exhausted = []
        self.row = []
        self.queued = None          # color dot queued for Special Recovery

        # FINF: three cards numbered for the Time Slots (0 Morning .. 2 Evening).
        # The setting is how many of them you take, at random.
        level = int(finf[1])
        self.finf_increase = level if finf[0] == "+" else 0
        self.finf_uses = level if finf[0] == "-" else 0
        self.finf_cards = sorted(self.rng.sample(range(3), level))
        self.finf_spent = set()     # Reduce: slots already used
        self.finf_due = [0, 0, 0]   # Increase: Assignments owed per slot
        self.slot = -1              # the Time Slot about to be played
        self.day = 1
        self.done_this_slot = 0     # Assignments completed in this slot
        self.ability = ABILITIES.get(apprentice) if PLAY_THE_CARDS else None
        if self.ability == "discard":
            self.ability = SLACKER_ABILITY
        if self.ability == "setback_window":
            self.ability = TECHNICIAN_ABILITY
        self.ability_day = None     # once-per-day abilities: the day last used
        self.setback_window = False  # Technician: one card worked past a Setback
        self.repaired_this_slot = False
        self.next_slot = {"str": 0, "rec": 0, "crit": 0}   # Opportunity carry
        self.crit_bonus = 0         # a Crit counts as 3 this slot
        self.coupons = []           # finished Opportunities held for later
        self.devious_coupons = []   # Tier III: kept for the Final Exam

        # Assignment deck: 26 Tasks + 6 Opportunities + 3 of the 6 Setbacks.
        deck = []
        for i, (t, d, dot, sk) in enumerate(TASKS):
            t, d = t + TARGET_DELTA, d + TARGET_DELTA
            card = Card("task", t, d, dot, sk, SUBJECTS[i], DEMAND_PENALTY[i])
            card.index = i
            deck.append(card)

        # Tier II: each Impostor Task replaces a Credit Task of its subject.
        if tier in ("II", "III"):
            for subject, rt, dt in IMPOSTOR:
                same = [c for c in deck
                        if c.kind == "task" and c.subject == subject]
                victim = self.rng.choice(same)
                deck.remove(victim)
                imp = Card("impostor", rt, dt, victim.dot, 0, None,
                           victim.penalty)
                imp.index = None
                deck.append(imp)

        # Tier III: Devious Opportunities replace the base Opportunities.
        if tier == "III":
            for i, (t, payout) in enumerate(DEVIOUS):
                card = Card("opportunity", t, t, OPPORTUNITIES[i][1])
                card.devious = payout
                card.index = i
                deck.append(card)
        else:
            for i, (t, dot) in enumerate(OPPORTUNITIES[:OPPORTUNITIES_IN_DECK]):
                t = max(2, t + OPP_TARGET_DELTA)
                card = Card("opportunity", t, t, dot)
                card.index = i
                deck.append(card)

        # Tier I: 3 of the 4 Following Setbacks stand in for 3 base Setbacks.
        if tier in ("I", "II", "III"):
            for i in self.rng.sample(range(4), 3):
                t, upkeep = FOLLOWING[i]
                card = Card("setback", t, t, self.rng.choice("PBGY"))
                card.upkeep = upkeep
                deck.append(card)
        else:
            for i in self.rng.sample(range(6), min(6, SETBACKS_IN_DECK)):
                t, dot = SETBACKS[i]
                deck.append(Card("setback", t, t, dot))
        if self.finf_increase:
            # Increase shuffles the dealt FINF cards into the Assignment deck.
            for slot in self.finf_cards:
                card = Card("finf", 0, 0, "Y")
                card.slot = slot
                deck.append(card)
        self.rng.shuffle(deck)
        self.deck = deck

    # ------------------------------------------------------------------
    # dice
    # ------------------------------------------------------------------
    def recover(self, n):
        for _ in range(min(n, len(self.exhausted))):
            self.available.append(self.exhausted.pop())

    NEIGHBOURS = {"purple": ("yellow", "blue"), "blue": ("purple", "green"),
                  "green": ("blue", "yellow"), "yellow": ("green", "purple")}

    def recover_color(self, color):
        """Special Recovery: recover ALL exhausted dice of one color."""
        keep = []
        for c in self.exhausted:
            if c == color:
                self.available.append(c)
            else:
                keep.append(c)
        self.exhausted = keep
        if self.ability == "wide_recovery":      # Savant
            # all but one of the color, plus one of a neighbouring color
            if color in self.available:
                self.available.remove(color)
                self.exhausted.append(color)
            for near in self.NEIGHBOURS[color]:
                if self.recover_one(near):
                    break

    def commit_for(self, card):
        """Pick dice for one Assignment, honoring the color rule.

        To complete or store, the successes must include a die matching the
        card's dot, Red as wild, or two dice of one other color. The policy
        leads with a matching die when it holds one.
        """
        want = DOT_COLOR[card.dot]
        pool = sorted(self.available, key=lambda c: -EV[c])
        take = []
        if want in pool:
            take.append(want)
            pool.remove(want)
        elif "red" in pool:
            take.append("red")
            pool.remove("red")
        else:
            # two of one other color
            for c in COLORS:
                if pool.count(c) >= 2:
                    take += [c, c]
                    pool.remove(c)
                    pool.remove(c)
                    break
            else:
                # "One die counts as any color" - take the best single die.
                if not (pool and self.spend_coupon("wild")):
                    return []
                take.append(pool.pop(0))
        # Aim one expected success past the requirement. Committing to exactly
        # the remaining need finishes only about half the time, and a roll that
        # falls short locks its dice onto the card as stored progress - so
        # under-committing drains the pool far faster than over-committing.
        expected = sum(EV[c] for c in take)
        want = card.remaining() + 1
        for c in pool:
            if expected >= want:
                break
            take.append(c)
            expected += EV[c]
        return take

    # ------------------------------------------------------------------
    # a Time Slot
    # ------------------------------------------------------------------
    def unresolved(self):
        return len(self.row)

    def draw_into_row(self, free=True):
        if not self.deck or self.unresolved() >= ROW_MAX:
            return
        card = self.deck.pop()
        card.free = free
        self.row.append(card)

    def reveal(self):
        """Reveal 2, take one as Primary, discard the other."""
        row_max = 3 if self.ability == "small_row" else ROW_MAX
        if self.unresolved() >= row_max:
            # "if the row is already full when you reveal, discard both
            # revealed cards and take nothing"
            del self.deck[-2:]
            return None
        drawn = []
        while len(drawn) < 2 and self.deck:
            card = self.deck.pop()
            if card.kind == "finf":
                # The card adds an Assignment to its own Time Slot, which may be
                # this one. The model keeps a single row, so a card for another
                # slot waits until that slot comes round.
                if card.slot == self.slot:
                    self.draw_into_row(free=True)
                else:
                    self.finf_due[card.slot] += 1
                continue
            drawn.append(card)
        if not drawn:
            return None
        # A Setback among the two must be the one you take, and Impostor Tasks
        # are Mandatory, so they are forced in the same way.
        forced = [c for c in drawn if c.kind in ("setback", "impostor")]
        if self.ability == "dodge_setback" and len(drawn) > 1:
            # The Slacker may leave a revealed Setback behind; an Impostor Task
            # is still Mandatory.
            forced = [c for c in forced if c.kind == "impostor"]
            drawn = [c for c in drawn if c.kind != "setback"] or drawn
        primary = forced[0] if forced else min(drawn, key=lambda c: c.target)
        self.row.append(primary)
        self.queued = primary.dot
        # Skulls resolve only on the Assignment you chose.
        for _ in range(primary.skulls):
            self.draw_into_row(free=True)
        return primary

    def work(self):
        """Up to STR rolls this slot, each spread over one or more cards."""
        self.done_this_slot = 0
        self.rolls_left = self.str_
        while self.rolls_left > 0:                     # Strategy rolls
            self.rolls_left -= 1
            if self.capped():
                break
            if self.spend_roll() is False:
                break

    def capped(self):
        return STR_CAPS_COMPLETIONS and self.done_this_slot >= self.str_

    def spend_roll(self):
        """One Strategy roll, spread over up to CARDS_PER_ROLL Assignments.

        False when the slot cannot continue (no dice, nothing workable).
        """
        for _ in range(CARDS_PER_ROLL if SPLIT_ROLLS else 1):
            if self.capped():
                return True
            # Keep a reserve: Setback upkeep and Demand penalties are paid in
            # available dice, and spending the pool to zero converts them into
            # Health loss. A player would hold something back.
            if len(self.available) < DICE_RESERVE:
                return False
            # "No other Assignment may be worked until this Setback is
            # resolved" - a Setback on the row blocks everything else.
            setbacks = [c for c in self.row
                        if c.kind == "setback" and not c.upkeep
                        and not c.ignored and not c.away
                        and not (self.ability == "exempt" and c.stored_dice)]
            if (setbacks and self.ability == "setback_window"
                    and not self.setback_window
                    and any(c.stored_dice for c in setbacks)):
                self.setback_window = True      # work one other Assignment
                setbacks = []
            if setbacks:
                card = min(setbacks, key=lambda c: c.remaining())
            else:
                # Base Opportunities are optional and, with their rewards
                # unmodeled, worth nothing - so they are left alone. Devious
                # Opportunities pay out, so they are worth working.
                # Impostor Tasks are Mandatory and come first among Tasks;
                # otherwise chase Credits, nearest-to-done next.
                workable = [c for c in self.row
                            if c.kind in ("task", "impostor")
                            or (c.kind == "setback" and c.upkeep
                                and not c.ignored and not c.away)
                            or (c.kind == "opportunity"
                                and (c.devious or PLAY_THE_CARDS))]
                if not workable:
                    return False
                # A Following Setback is worked first - its printed text asks
                # for a die before anything else - then Impostor Tasks.
                card = min(workable, key=lambda c: (not (c.kind == "setback" and c.upkeep),
                                                    c.kind != "impostor",
                                                    c.subject is None,
                                                    c.remaining()))
            if (OPP_COUPONS and card.remaining() >= 4
                    and card.kind != "opportunity"
                    and self.spend_coupon("shortcut")):
                card.stored += 2        # "Study Nobulous' Notes"
            take = self.commit_for(card)
            if not take:
                return False
            for c in take:
                self.available.remove(c)
            results = [roll(c, self.rng) for c in take]
            # Each further STR roll is one throw. It may add available dice
            # and re-throw the committed dice that are not yet assigned to
            # the card, and both are decided before anything is thrown.
            while (PUSH_REROLL and getattr(self, "rolls_left", 0) > 0
                   and sum(results) < card.remaining()):
                need = card.remaining()
                again = [i for i, v in enumerate(results) if v == 0]
                hits = [i for i, v in enumerate(results) if v == 1]
                # Bring in fresh dice alongside them, strongest first, until
                # the throw is expected to cover what is still missing.
                add = []
                expected = sum(results) + sum(EV[take[i]] for i in again)
                for c in sorted(self.available, key=lambda c: -EV[c]):
                    if expected >= need:
                        break
                    add.append(c)
                    expected += EV[c]
                ceiling = (sum(results) + sum(2 - results[i] for i in again)
                           + 2 * len(add))
                if ceiling < need:
                    # Nothing on the table can finish the card except a Crit
                    # off a basic hit. This card keeps partial progress, so
                    # only trade hits away if enough of them can get there.
                    for i in hits:
                        again.append(i)
                        ceiling += 1
                        if ceiling >= need:
                            break
                    else:
                        again = [i for i in again if results[i] == 0]
                if not again and not add:
                    break
                self.rolls_left -= 1
                for c in add:
                    self.available.remove(c)
                again += range(len(results), len(results) + len(add))
                take = take + add
                results = results + [0] * len(add)
                for i in again:
                    results[i] = roll(take[i], self.rng)
            got = sum(results)
            crit = any(v >= 2 for v in results)
            if (self.ability == "repair_bonus" and card.kind == "setback"
                    and not self.repaired_this_slot and results):
                got += 1                     # one die counts double
                self.repaired_this_slot = True
            if PLAY_THE_CARDS and card.kind == "task":
                index = card.index
                # "A Crit of this color counts as 3 successes."
                colour = CRIT_COLOR.get(index)
                if colour:
                    got += sum(1 for c, v in zip(take, results)
                               if c == colour and v >= 2)
                if self.crit_bonus and crit:
                    got += 1
                    self.crit_bonus -= 1
                entry = REQUEST_REWARD.get(index)
                if (entry and entry[0] == "bonus" and not card.on_demand
                        and self.reward_fires(entry[1], card, take, got, crit)):
                    got += 1
            if OPP_COUPONS and self.coupons and got < card.remaining():
                # A roll that falls just short is what a coupon is for.
                short = card.remaining() - got
                if short == 1 and crit and self.spend_coupon("crit3"):
                    got += 1
                elif short == 1 and self.spend_coupon("boost"):
                    got += 1
                elif short <= 2 and self.spend_coupon("assist"):
                    got += 2
            if got >= card.remaining():
                # Resolved: its committed and stored dice all exhaust.
                if OPP_DICE_RETURN and OPP_RETURN_ON_WIN and card.kind == "opportunity":
                    self.available += take + card.stored_dice
                else:
                    self.exhausted += take + card.stored_dice
                self.row.remove(card)
                self.done_this_slot += 1
                if self.ability == "repair_reward" and card.kind == "setback":
                    self.recover(2)
                if PLAY_THE_CARDS:
                    if card.kind in ("task", "impostor") and not card.on_demand:
                        if card.kind == "task":
                            self.apply_request_reward(card.index, card, take, got, crit)
                        if self.ability == "dot_recovery":      # Opportunist
                            self.recover_one(DOT_COLOR[card.dot])
                    elif card.kind == "opportunity":
                        self.apply_opportunity(card.index)
                if card.kind == "task" and card.subject:
                    self.credits[card.subject] += 1
                    self.credit_total += 1
                elif card.devious:
                    self.apply_devious(card.devious)
            elif card.kind == "opportunity":
                if OPP_STORES:
                    card.stored += got
                    card.stored_dice += take
                elif OPP_DICE_RETURN:
                    self.available += take      # a free attempt
                else:
                    self.exhausted += take      # printed: no progress stored
            else:
                # Store the successes as progress; the dice lock to the card.
                card.stored += got
                card.stored_dice += take
                if (self.finf_uses > 0 and card.on_demand
                        and (FINF_REDUCE_ANY_CARD
                             or (self.slot in self.finf_cards
                                 and self.slot not in self.finf_spent))
                        and card.kind != "setback"):   # Setbacks never flip to Demand here
                    # Reduce: this slot's card removes a card from this slot.
                    if not FINF_REDUCE_ANY_CARD:
                        self.finf_spent.add(self.slot)
                    self.finf_uses -= 1
                    self.exhausted += card.stored_dice
                    self.row.remove(card)
        return True

    # ------------------------------------------------------------------
    # printed card text
    # ------------------------------------------------------------------
    def reward_fires(self, cond, card, take, got, crit):
        if cond == "always":
            return True
        if cond == "exact":
            return got == card.remaining()
        if cond == "few_dice":
            return len(take) <= 3
        if cond == "three_dice":
            return len(take) == 3
        if cond == "four_dice":
            return len(take) == 4
        if cond == "one_attempt":
            return not card.stored_dice
        if cond == "no_stored":
            return not card.stored_dice
        if cond == "no_crit":
            return not crit
        if cond == "crit":
            return crit
        if cond == "primary":
            return not card.free
        if cond == "three_colors":
            return len(set(take + card.stored_dice)) >= 3
        return False

    def apply_request_reward(self, index, card, take, got, crit):
        """The Request effect printed on a Task, when its condition holds."""
        entry = REQUEST_REWARD.get(index)
        if not entry:
            return
        kind, cond = entry
        if not self.reward_fires(cond, card, take, got, crit):
            return
        if kind == "recover_committed":
            if take:
                self.available.append(take[0])
                if take[0] in self.exhausted:
                    self.exhausted.remove(take[0])
        elif kind == "recover_any":
            self.recover(1)
        elif kind == "recover_dot":
            self.recover_one(DOT_COLOR[card.dot])
        elif kind == "hp":
            self.hp = min(3, self.hp + 1)
        elif kind == "rec":
            self.rec += 1
        elif kind == "str":
            self.str_ += 1

    def spend_coupon(self, kind):
        """Cash in a held Opportunity. One use, then it is discarded."""
        if OPP_COUPONS and kind in self.coupons:
            self.coupons.remove(kind)
            return True
        return False

    def recover_one(self, color):
        if color in self.exhausted:
            self.exhausted.remove(color)
            self.available.append(color)
            return True
        return False

    def apply_devious(self, payout):
        """A Devious Opportunity: two pay now, four are kept for the exams."""
        if payout == "credit":
            s = self.rng.choice(SUBJECT_LIST)
            self.credits[s] += 1
            self.credit_total += 1
        elif payout == "free_task":
            # Exhaust 2 available dice to clear a cheap non-Credit Task.
            for _ in range(2):
                if self.available:
                    self.exhausted.append(self.available.pop())
            cheap = [c for c in self.row
                     if c.kind == "task" and not c.subject and c.remaining() <= 3]
            if cheap:
                victim = min(cheap, key=lambda c: c.remaining())
                self.exhausted += victim.stored_dice
                self.row.remove(victim)
        else:
            self.devious_coupons.append(payout)

    def apply_opportunity(self, index):
        """What an Opportunity pays when you finish it."""
        if OPP_COUPONS:
            self.coupons.append(COUPON[index % len(COUPON)])
            return
        kind = OPPORTUNITY_REWARD[index % len(OPPORTUNITY_REWARD)]
        bonus = OPP_REWARD_PLUS
        if kind == "hp":
            self.hp = min(3, self.hp + 1)
            self.recover(bonus)
        elif kind == "recover2":
            self.recover(2 + bonus)
        elif kind == "recover3":
            self.recover(3 + bonus)
        elif kind == "str_next":
            self.next_slot["str"] += 1 + bonus
        elif kind == "rec_next":
            self.next_slot["rec"] += 1 + bonus
        elif kind == "crit_next":
            self.next_slot["crit"] += 1 + bonus

    def use_daily_ability(self):
        """Slacker's discard: drop the card that is furthest from done."""
        if self.ability == "morning_discard" and self.slot != 0:
            return                      # Mornings only; the Time Slot tracks it
        if self.ability not in ("discard", "morning_discard") or self.ability_day == self.day:
            return
        workable = [c for c in self.row if c.kind != "setback"]
        if not workable:
            return
        worst = max(workable, key=lambda c: c.remaining())
        self.exhausted += worst.stored_dice
        self.row.remove(worst)
        self.ability_day = self.day

    def soak(self):
        """Lab Rat: once a day, exhaust a die instead of losing 1 Health."""
        if self.ability != "soak" or self.ability_day == self.day or not self.available:
            return False
        self.exhausted.append(self.available.pop())
        self.ability_day = self.day
        return True

    def demand_penalty(self, card):
        """Apply a Task's printed Demand penalty.

        11 of the 26 Tasks bill 1 Health; the other 15 exhaust 1 or 2
        available dice. Exhausting when nothing is available does nothing -
        the penalty is not convertible to Health.
        """
        if card.penalty < 0:
            if not self.soak() and not self.spend_coupon("soak"):
                self.hp -= 1             # Lab Rat, or a held Break, pays instead
            return
        for _ in range(card.penalty):
            if not self.available:
                break
            self.exhausted.append(self.available.pop())

    def move_setback(self):
        """Spend a coupon to send a Setback to a different Time Slot."""
        if not (DEVIOUS_MOVE_SLOTS and self.devious_coupons):
            return
        live = [c for c in self.row
                if c.kind == "setback" and not c.away and not c.ignored]
        if not live:
            return
        worst = max(live, key=lambda c: (c.upkeep, c.remaining()))
        worst.away = DEVIOUS_MOVE_SLOTS
        self.devious_coupons.pop()

    def ignore_setback(self):
        """Spend a coupon on the Setback that is costing the most."""
        if not (DEVIOUS_IGNORE_SETBACK and self.devious_coupons):
            return
        live = [c for c in self.row if c.kind == "setback" and not c.ignored]
        if not live:
            return
        worst = max(live, key=lambda c: (c.upkeep, c.remaining()))
        worst.ignored = True
        self.devious_coupons.pop()

    def cash_devious(self):
        """Discard a Final Exam coupon for 2 dice rather than never spend it."""
        if not (DEVIOUS_CASH_EARLY and self.devious_coupons):
            return
        if len(self.available) <= 1 and len(self.exhausted) >= 2:
            self.devious_coupons.pop()
            self.recover(2)

    def end_of_slot(self):
        self.move_setback()
        self.ignore_setback()
        self.cash_devious()
        survivors = []
        for card in self.row:
            if card.kind == "opportunity":
                if card.rotated:
                    continue            # discarded, no penalty
                card.rotated = True
                survivors.append(card)
            elif card.kind == "setback":
                survivors.append(card)      # no printed Demand side
            elif card.on_demand:
                self.demand_penalty(card)
                survivors.append(card)
            else:
                card.on_demand = True
                survivors.append(card)
        self.repaired_this_slot = False
        self.row = survivors

    def time_slot(self):
        self.slot = (self.slot + 1) % 3     # Morning, Afternoon, Evening
        if self.slot == 0:
            self.day += 1
        # Opportunities paid into the coming slot.
        self.str_ += self.next_slot["str"]
        self.rec += self.next_slot["rec"]
        self.crit_bonus = self.next_slot["crit"]
        carried = dict(self.next_slot)
        self.next_slot = {"str": 0, "rec": 0, "crit": 0}
        if self.ability in ("discard", "morning_discard"):
            self.use_daily_ability()
        if self.queued:
            self.recover_color(DOT_COLOR[self.queued])
        self.recover(self.rec)
        # A Setback with no stored dice exhausts 1 available die each slot.
        for card in self.row:
            if card.kind != "setback":
                continue
            # Base Setback: 1 die if it holds no stored dice. A Following
            # Setback bills its own upkeep every slot regardless.
            if card.ignored:
                continue
            if card.away:
                card.away -= 1      # it is sitting in another Time Slot
                continue
            cost = card.upkeep or (0 if card.stored_dice else 1)
            for _ in range(cost):
                if self.available:
                    self.exhausted.append(self.available.pop())
        while self.finf_due[self.slot] > 0:
            self.finf_due[self.slot] -= 1
            self.draw_into_row(free=True)   # Skulls ignored on FINF cards
        if PLAY_THE_CARDS and FINF_REDUCE_ANY_CARD and self.finf_uses > 0:
            setbacks = [c for c in self.row if c.kind == "setback"]
            if setbacks:                      # it blocks everything else
                worst = max(setbacks, key=lambda c: c.remaining())
                self.exhausted += worst.stored_dice
                self.row.remove(worst)
                self.finf_uses -= 1
        if not self.deck and not self.row:
            return False
        self.reveal()
        self.work()
        self.end_of_slot()
        self.str_ -= carried["str"]
        self.rec -= carried["rec"]
        self.crit_bonus = 0
        self.setback_window = False
        return self.hp > 0

    # ------------------------------------------------------------------
    # Final Exam
    # ------------------------------------------------------------------
    def final_exam(self):
        # Leaving the apprenticeship: discard unresolved Assignments and
        # exhaust their stored dice.
        for card in self.row:
            self.exhausted += card.stored_dice
        self.row = []
        missing = max(0, CREDITS_TO_LEAVE - self.credit_total)
        order = ["red", "purple", "blue", "green", "yellow"]
        i = 0
        while missing > 0 and self.available:
            c = order[i % len(order)]
            if c in self.available:
                self.available.remove(c)
                self.exhausted.append(c)
                missing -= 1
            i += 1
            if i > 40:
                break
        # Preparation: 1 die, plus 1 per Credit above 6, plus queued recovery.
        self.recover(1 + max(0, self.credit_total - CREDITS_TO_LEAVE))
        if self.queued:
            self.recover_color(DOT_COLOR[self.queued])

        # Build the exam pool: per subject, 1 card at 0-1 Credits, 2 at 2-3,
        # 3 at 4+. Then draw three.
        pool = []
        for s in SUBJECT_LIST:
            n = 1 if self.credits[s] <= 1 else (2 if self.credits[s] <= 3 else 3)
            subject_exams = [e for e in EXAMS if e[0] == s]
            pool += subject_exams[:n]
        self.rng.shuffle(pool)
        for subject, dot, base in pool[:3]:
            target = max(1, base - self.credits[subject])
            # "Reduce one exam's Target by 3" - spend it on the worst exam.
            if "exam_target" in self.devious_coupons and target >= 3:
                self.devious_coupons.remove("exam_target")
                target = max(1, target - 3)
            # "Recover 3 exhausted dice of different colors before any exam."
            if "exam_recover" in self.devious_coupons and len(self.available) < target:
                self.devious_coupons.remove("exam_recover")
                seen = set()
                for c in list(self.exhausted):
                    if c not in seen and len(seen) < 3:
                        self.exhausted.remove(c)
                        self.available.append(c)
                        seen.add(c)
            take = sorted(self.available, key=lambda c: -EV[c])
            got, used = 0.0, []
            for c in take:
                if got >= target:
                    break
                used.append(c)
                got += EV[c]
            for c in used:
                self.available.remove(c)
            values = [roll(c, self.rng) for c in used]
            # STR 2: one roll plus one chance to reroll the misses.
            values = [roll(c, self.rng) if v == 0 else v
                      for c, v in zip(used, values)]
            # "After rolling one exam, reroll any number of failed dice."
            if sum(values) < target and "exam_reroll" in self.devious_coupons:
                self.devious_coupons.remove("exam_reroll")
                values = [roll(c, self.rng) if v == 0 else v
                          for c, v in zip(used, values)]
            total = sum(values)
            self.exhausted += used
            if total < target:
                loss = target - total
                while loss > 0 and self.spend_coupon("soak"):
                    loss -= 1
                self.hp -= loss
                if self.hp <= 0:
                    return False
            self.recover_color(DOT_COLOR[dot])
            self.recover(self.rec)
        return self.hp > 0

    def play(self):
        guard = 0
        while self.hp > 0 and guard < 60:
            guard += 1
            if self.credit_total >= CREDITS_TO_LEAVE or not self.deck:
                break
            if not self.time_slot():
                return False
        if self.hp <= 0:
            return False
        return self.final_exam()


def run(apprentice="Prodigy", finf="-1", games=20000, seed=20, tier="none"):
    rng = random.Random(seed)
    wins = 0
    for _ in range(games):
        if Game(apprentice, finf, rng, tier).play():
            wins += 1
    return wins / float(games)


if __name__ == "__main__":
    print("%-14s %8s %8s %8s %8s" % ("FINF", "none", "I", "II", "III"))
    for f in FINF_SETTINGS:
        row = ["%7.1f%%" % (100 * run("Prodigy", f, 4000, tier=t))
               for t in TIERS]
        print("%-14s %s" % (f, " ".join(row)))
