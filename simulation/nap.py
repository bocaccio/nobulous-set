"""Nobulous Apprenticeship Program: work the Assignment row, then sit three
Final Exams.

Rules source: rules/nap.html. Card data is transcribed verbatim - the 26
Tasks, 6 Setbacks and 6 Opportunities from the NAP_TASKS / NAP_SETBACKS /
NAP_OPPS tables in playtest/dist/suite.js, the 12 Final Exams from the EXAMS
table in generator/build_nap.py.

Win condition (rules/nap.html:43, :194): earning 6 Credits does NOT win. It
ends the apprenticeship. You then sit three mandatory Final Exams and must
finish all three with at least 1 Health. Arriving short of 6 Credits does not
lose either - it costs dice and leaves the exam Targets unreduced.

Difficulty is the Credit goal. FINF is a SECOND, independent dial - the
three cards numbered 1 Morning, 2 Afternoon, 3 Evening - and Standard is
Reduce 1. The "+2" / "-1" setting strings below are shorthand for Increase
or Reduce N, meaning N of those three cards.

WHAT IS NOT MODELED
  This block was wrong in three places on 2026-11-06 - it denied Apprentice
  abilities, Request effects and Opportunity effects, all of which are
  modeled below. coverage.py now derives the list from the live module, so
  read it there and treat this as prose.
  * ONE of the 12 FINAL EXAM restrictions. The other eleven went in on
    2026-11-06 - EXAMS now carries each card's printed restriction and
    exam_commit honours it - and that also made Definitely
    Curriculum-Approved payable for the first time. The one left is Neural
    Response Screening's "at least 1 Crit must contribute to complete this
    Assignment", which is Assignment language a Final Exam has no
    completion step for; see the note on EXAMS.
  * The 4 IMPOSTER TASK effects and the 4 FOLLOWING SETBACK effects.
    IMPOSTER_TASKS and FOLLOWING carry Targets and a flat upkeep, so the
    four Following cards are interchangeable in the model.
  * Two of the 26 Request effects - Decode Nobulous' Lecture Notes and
    Update Nobulous' Lab Notes. The other 24 carry a CRIT_COLOR or a
    REQUEST_REWARD entry.
  * The six Setbacks' individual text. The one printed rule they share -
    the row locks until the Setback is resolved - IS modeled.
  * Prodigy's ability, alone of the six: ABILITIES maps it to None. Prodigy
    is also the default in run() and in audit.py.
  * Separate rows per Time Slot. One row is modeled, so a FINF card naming
    another slot is applied when that slot comes round, and a Reduce card
    reaches only the row in front of you.
  * Per-card Demand penalties. The rules say an Assignment left unresolved on
    its Demand side "inflicts its printed Demand penalty" every slot it
    survives; the penalties are card text. Modeled as a flat 1 Health.
  * Subject-icon wilds.
"""
import collections
import random

from dice import COLORS, EV, policy_value, roll

# (target, demand, recovery dot, skulls) for the 26 Tasks, deck order.
#
# EVERY PRINTED TARGET ROSE BY 1 ON 2026-10-28, agreed with Jon: the 26 Task
# Requests here, the 6 Opportunities and the 12 Final Exam base Targets. Task
# DEMAND targets did not move. NAP read well above the 47-57% community band
# at every rung of its printed Credit ladder - Standard was 66.7% at Tier III
# and 76.0% with no NRJ - and the Credit goal could not fix both axes at any
# value. One more success on every check does: Standard lands at 51.1% and
# 49.5%, all six Apprentices land in band on both axes, and the two axes
# converge (the printed 9.3-point gap becomes -1.6) because raising the Exam
# Targets is what the no-NRJ game actually leans on. The per-Apprentice
# spread also narrows, 10.8 to 8.4 at Tier III.
#
# TARGET_DELTA below is still a dial on top of these numbers, and still 0.
TASKS = [
    (3, 3, "Y", 0), (4, 5, "G", 1), (5, 5, "B", 1), (6, 7, "P", 2),
    (4, 4, "Y", 0), (4, 4, "G", 0), (4, 5, "B", 0), (6, 6, "P", 0),
    (5, 5, "G", 1), (5, 9, "B", 1), (5, 5, "B", 1), (5, 9, "P", 1),
    (6, 9, "P", 1), (7, 7, "P", 1), (4, 5, "Y", 1), (5, 9, "B", 2),
    (6, 7, "P", 2), (4, 4, "G", 0), (5, 9, "Y", 1), (5, 5, "G", 0),
    (4, 4, "Y", 0), (4, 4, "G", 0), (5, 5, "B", 0), (7, 8, "P", 1),
    (5, 9, "B", 1), (5, 5, "P", 0),
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
OPPORTUNITIES = [(4, "Y"), (4, "Y"), (5, "Y"), (5, "Y"), (4, "G"), (5, "G")]

# (subject, recovery dot, base Target, printed restriction) for the 12 Final
# Exams, 3 per subject, in generator/build_nap.py's EXAMS order.
#
# THE RESTRICTION COLUMN WAS ADDED 2026-11-06. Until then every row was
# (subject, dot, Target) and all twelve printed restrictions were unmodelled
# - which also left Definitely Curriculum-Approved, whose entire reward is to
# ignore one of them, unable to pay out at all: it was earned in 153 of 6000
# Tier III games and its printed reward fired in 0 of them.
#
# A RESTRICTION IS A CONSTRAINT ON WHAT YOU COMMIT, which is what
# rules/nap.html asks for - "Roll against the modified Target, honoring the
# exam's printed restriction. Lose 1 Health for each success below the
# modified Target." There is no pass/fail: a Yellow you had to throw for a
# colour requirement and which missed is simply a success you did not get,
# and the Health rule already prices that. So these are modelled in
# exam_commit, not as a second failure condition the cards do not print.
#
#   no_red    Red cannot be committed
#   colors    at least this many DISTINCT colours must be committed
#   need      each of these colours must be committed at least once
#   among     (n, colours) - at least n dice from this set
#   dice      at least this many dice must be committed
#   crit_val  {colour: successes} - a Crit of that colour scores this
#             instead of the usual 2
#
# ONE CLAUSE IS NOT MODELLED AND CANNOT BE, and it is a card-text problem
# rather than a model gap. Neural Response Screening prints "At least 1 Crit
# must contribute to COMPLETE THIS ASSIGNMENT" - Assignment language, where
# completion is binary. A Final Exam has no completion: you lose 1 Health per
# success short and pass by surviving. MEASURED 2026-11-06: read as a gate
# ("no Crit, no successes") it deals its whole Target in 23% of the sittings
# it gets - the dot colours are weak and every colour crits on exactly one
# face - and costs 3.8 points of win rate on its own, which no other single
# exam comes near. Read as a commit rule it says nothing at all, for the same
# reason: there is no way to commit FOR a Crit. RAISED, not papered over: the
# clause wants rewording into the exam's own idiom. EXAM_CRIT_GATE models the
# gate reading for whoever decides it.
EXAMS = [
    ("Anatomy", "B", 6, {"colors": 3}),
    ("Anatomy", "Y", 7, {"need": ("yellow", "blue")}),
    ("Anatomy", "P", 7, {"among": (2, ("blue", "purple"))}),
    ("Theory", "G", 6, {"no_red": True, "colors": 3}),
    ("Theory", "P", 7, {"need": ("blue", "purple")}),
    ("Theory", "Y", 8, {"colors": 4, "crit_val": {"red": 1}}),
    ("Engineering", "G", 6, {"crit": True}),
    ("Engineering", "B", 7, {"dice": 4, "crit_val": {"yellow": 3}}),
    ("Engineering", "B", 7, {"no_red": True, "need": ("purple",)}),
    ("Procedure", "Y", 7, {"no_red": True, "colors": 3}),
    ("Procedure", "P", 8, {"dice": 4, "colors": 3}),
    ("Procedure", "G", 8, {"dice": 5, "colors": 3}),
]
# See the "crit" note above: False is the shipped reading.
EXAM_CRIT_GATE = False
# Switch the whole restriction column off to reproduce the pre-2026-11-06
# model, which is also the control the restrictions are priced against.
EXAM_RESTRICTIONS = True

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
#   II  - 4 Imposter Tasks, one per subject, each replacing a Credit Task
#   III - 6 Devious Opportunities replace the 6 Opportunities
# Card data from the FOLLOWING / IMPOSTER_TASKS / DEVIOUS tables in build_nrj.py.
# ---------------------------------------------------------------------------

# (Target, printed dot, printed effect) for the 4 Following Setbacks, in
# build_nrj.py's FOLLOWING order. All four are Mandatory and carry into the
# next Time Slot.
#
# MODELLED SINCE 2026-11-06. Until then this was [(7,1),(7,1),(8,1),(8,1)] -
# a Target and a flat 1-die upkeep every slot - and that was wrong in three
# ways at once. ONLY ONE of the four prints an upkeep (Minor Laboratory
# Fire), so the other three were being charged a die a slot for text they do
# not carry; the four printed effects were interchangeable in the model, so
# Tier I was two Targets wearing four names; and the dot was drawn at random
# from PBGY when all four print one.
#
# A Following Setback does NOT print the base Setback's text. build_nrj.py
# gives it its own effect line and a footer - "Mandatory. Follows into the
# next Time Slot if unresolved" - and nothing else, so the base card's row
# lock and conditional upkeep are not on it. Unscheduled Demonstration
# prints a weaker version of the lock and is the only one of the four that
# has any.
#
#   dot_first    the first die committed to ANOTHER Assignment each Time
#                Slot must match that Assignment's own dot
#   work_first   one die must go here before any other Assignment this slot
#   upkeep       1 available die at the end of every slot it survives
#   no_special   one die committed here is not returned by Special Recovery
FOLLOWING = [(7, 'Y', "dot_first"), (7, 'G', "work_first"),
             (8, 'B', "upkeep"), (8, 'P', "no_special")]
# Switch the four printed effects off and restore the flat upkeep every
# figure published before 2026-11-06 was measured through.
FOLLOWING_EFFECTS = True
# True is what rules/nrj.html prints and what the lab plays: the 6 base
# Setbacks are set aside entirely and exactly 3 Following ones take their
# place, "never both kinds together". False is what this model has done
# since the counts stopped being 3 everywhere - 3 Following PLUS whatever
# the difficulty's count leaves over - on the argument that otherwise
# turning a tier ON makes Hard and Nobulous EASIER. The two agree at Easy
# and Standard since the 2026-11-06 re-peg. RAISED, not decided, so this
# ships as the model has had it.
FOLLOWING_REPLACE_ALL = False

# (subject, Request Target, Demand Target). Mandatory, and they grant no
# Credits - "You still have to clear them; clearing them advances nothing."
# subject, printed dot, Request Target, Demand Target. The dot is printed
# on the card as of 2026-10-30; before that this model inherited the dot of
# the Credit Task each Imposter Task replaced, which was never on any card.
#
# THE FOURTH COLUMN IS THE PRINTED EFFECT, modelled since 2026-11-06; before
# that the four cards were a subject, a dot and two raised Targets, and so
# were interchangeable.
#
#   lock_day     "One die committed here remains locked until the end of the
#                Day even if completed" - it does not even exhaust, so it is
#                out of the pool until the Day turns over
#   same_color   "At least 2 applied successes must come from the same
#                color" - a roll where no colour supplies two successes
#                applies nothing
#   commit2      "Before rolling, commit at least 2 dice initially"
#   demand_burn  "If unresolved, exhaust 1 available die before flipping it
#                to Demand"
IMPOSTER_TASKS = [("Anatomy", 'P', 5, 6, "lock_day"),
                  ("Engineering", 'B', 4, 5, "same_color"),
                  ("Procedure", 'Y', 4, 5, "commit2"),
                  ("Theory", 'G', 4, 5, "demand_burn")]
IMPOSTER_EFFECTS = True

# (Target, payout). Two resolve on completion; the other four are kept and
# spent during the Final Exam, which is where NAP actually kills you.
#   free_task      exhaust 2 dice to finish a cheap non-Credit Task now
#   credit         1 Credit now
#   exam_recover   recover 3 dice before one exam
#   exam_reroll    reroll the misses on one exam
#   exam_target    one exam's Target drops by 3
#   exam_ignore    ignore one exam's printed restriction. PAYABLE SINCE
#                  2026-11-06: eleven of the twelve restrictions are now
#                  modelled in exam_commit, so this card - Definitely
#                  Curriculum-Approved - has something to ignore. Before
#                  that it was earned in 153 of 6000 Tier III games and its
#                  printed reward fired in 0 of them.
# TARGETS RAISED 2026-11-06 from 3/3/3/3/4/3 to 4/4/5/5/4/5 - what the six
# base OPPORTUNITIES these replace cost. Tier III was handing out six cards
# that were both stronger and cheaper than the ones they displaced, and it
# showed: Tier III read ABOVE the no-tier column at every rung (Standard
# 52.3% against 48.8% solo, and 121.9% of solo at Nobulous), where BAT sits
# at 81-85% of its own solo cell. At the base Targets it reads 85.6% of solo
# at Standard and 86-88% across the ladder.
DEVIOUS = [(4, "free_task"), (4, "exam_recover"), (5, "credit"),
           (5, "exam_reroll"), (4, "exam_target"), (5, "exam_ignore")]

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
# How many expected successes to throw past an Assignment's requirement.
# RETUNED 2026-10-27 from 1 to -1, which is worth +33.5 points at Standard
# and +31 to +35 at every difficulty. The old value was reasoned from "a
# roll that falls short locks its dice onto the card as stored progress",
# which is true and is the argument for the OPPOSITE policy: stored progress
# is carried, so a shortfall costs only the upkeep while the card sits,
# while every success past the requirement is simply lost. Deliberately
# under-throwing by one is the cheapest way to buy progress. The sweep has
# a clear interior peak - 42.5 / 57.8 / 65.2 / 55.3 / 44.0% at +1 / 0 / -1 /
# -2 / -3 - so this is not "commit nothing" winning by degenerate means.
COMMIT_MARGIN = -1

# ---------------------------------------------------------------------------
# PLAYER MODEL. simulation/players.py sets these to approximate kinds of
# human player. The defaults are the calibrated policy every other tool in
# this package runs on, so leaving them alone changes nothing.
#   DICE_ORDER    "strongest" take the best die first - the tuned policy
#                 "weakest"   save the good dice for later, a common error
#                 "random"    no ordering at all
#   COMMIT_MARGIN how many expected successes to throw past the requirement
# ---------------------------------------------------------------------------
# RETUNED 2026-10-27 to "weakest", worth +8.9 points on its own and +33.5
# together with the commit margin. NAP charges nothing for a short roll, so
# the strong dice are better kept for the Assignments that need them; BAT is
# the mirror image, where a wall must fall in one blow and taking the
# strongest dice is worth +25.8.
DICE_ORDER = "weakest"


def exam_commit(available, target, rule, rng):
    """The dice a Final Exam's printed restriction makes you commit.

    Strongest first up to the Target as before, then whatever the restriction
    still demands out of what is left - and Red taken out of consideration
    entirely where the card forbids it. Anything the pool cannot supply is
    simply not supplied: the exam is still sat, and the successes that do not
    arrive are what rules/nap.html charges in Health.

    The cost of a restriction is therefore real but indirect. "Red cannot be
    committed" takes away the best die in the box; "commit at least 5 dice
    from at least 3 colours" makes you throw dice a bare Target would not
    have needed, and a Yellow thrown only to satisfy a colour count misses
    half the time.
    """
    pool = [c for c in available
            if not (rule.get("no_red") and c == "red")]
    order = pick_order(pool, rng)
    used, got, i = [], 0.0, 0
    while i < len(order) and got < target:
        used.append(order[i])
        got += EV[order[i]]
        i += 1
    spare = order[i:]

    def grab(pred):
        for j, c in enumerate(spare):
            if pred(c):
                return spare.pop(j)
        return None

    for want in rule.get("need", ()):
        if want not in used:
            c = grab(lambda x, w=want: x == w)
            if c:
                used.append(c)
    count, cols = rule.get("among", (0, ()))
    while sum(1 for c in used if c in cols) < count:
        c = grab(lambda x: x in cols)
        if c is None:
            break
        used.append(c)
    while len(set(used)) < rule.get("colors", 0):
        c = grab(lambda x: x not in used)
        if c is None:
            break
        used.append(c)
    while len(used) < rule.get("dice", 0) and spare:
        used.append(spare.pop(0))
    return used


def pick_order(seq, rng=None):
    """The order a player takes dice in, per DICE_ORDER."""
    if DICE_ORDER == "random" and rng is not None:
        out = list(seq)
        rng.shuffle(out)
        return out
    return sorted(seq, key=lambda c: EV[c], reverse=DICE_ORDER != "weakest")

TARGET_DELTA = 0   # flat rise on every printed Assignment Target

STR_CAPS_COMPLETIONS = False
# A roll's dice may be applied to more than one Assignment, so a slot can
# finish several cards that already hold stored progress. With this False the
# model commits each roll to a single card and the cap above cannot bind.
SPLIT_ROLLS = True
# How many cards one roll may be spread over; beyond 4 the row runs out anyway.
CARDS_PER_ROLL = 4
# A second difficulty lever, and it flattens out: at 4 Setbacks the goal runs
# 76.3% at 6 Credits, 65.8% at 8, 55.6% at 10, then only 52.4 / 50.1 / 48.0%
# at 12 / 14 / 16. Raising the goal is the obvious dial for re-pitching NAP
# after the retune, and on its own it cannot get below about 48%. The shortfall penalty is bounded by the dice you still
# have - past about 10 Credits you are always fully drained and further
# shortfall is nearly free. Raising the Final Exam Targets is not bounded
# that way.
# Play the printed card text: Request rewards, Opportunity payouts and the
# Apprentice ability. False reproduces the older, card-text-free model.
PLAY_THE_CARDS = True
# How many dice the policy refuses to spend. 3 is cautious; a player chasing a
# finish will go lower.
DICE_RESERVE = 2
# Reduce variant: with this True a FINF card is not tied to its number - any
# held card removes any non-Final-Exam card from the ACTIVE Time Slot. The
# printed rule ties it to the number (rules/nap.html, "Reduce"), which is
# why this is False; an earlier draft of the rulebook described the loose
# version and has been removed.
FINF_REDUCE_ANY_CARD = False
# Deck composition, fixed by the rules: 3 of the 6 Setbacks and all 6
# Opportunities. Exposed so the lever can be measured.
# Half of NAP's difficulty. The Credit goal cannot carry it alone: the
# shortfall penalty is never paid, Credits discount the Final Exam one for
# one so demanding more refunds itself, and above about 8 the Credits earned
# flatline because the deck runs out. The deck is the other half, which is
# what BAT (Specimens added) and AoS (deck mix) already use.
#   Easy 3, Standard 3, Hard 4, Nobulous 5 - see LEVELS below
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
# 2 exhausted dice, so holding one is never a dead card. No card prints it,
# so this is a tuple of names too - see DEVIOUS_IGNORE_SETBACK below.
DEVIOUS_CASH_EARLY = ()
# WHICH COUPONS MAY PAY FOR AN OFF-CARD POWER, by name. Empty is the printed
# cards, and the printed cards are what ships.
#
# THIS WAS THE THIRD FUNGIBLE-TOKEN DEFECT IN THE SET, and it ran the other
# way. AoS's Backdoor Routines and BAT's Research Notes each had six cards
# sharing one counter and under-delivered; here devious_coupons IS a list of
# named payouts, but until 2026-11-06 ignore_setback() and move_setback()
# called .pop(), which takes whichever coupon is on the END. So a coupon
# earned by any of the six bought "ignore a Setback" - an ability NONE OF THE
# SIX PRINTS - and 27% of every coupon earned left the hand that way. The
# pool OVER-delivered. Measured at -0.7 points even so, because the policy
# was spending on a Setback a coupon worth more at an exam.
#
# These are tuples rather than booleans on purpose: a lever that consumes a
# coupon now has to NAME the card paying for it, so the fungible form cannot
# be written again by accident. To reproduce the old model, set
# DEVIOUS_IGNORE_SETBACK = EXAM_COUPONS.
#
# Ignoring a Setback stops it billing upkeep, stops it demanding to be worked
# first and - for a base Setback - stops it locking the row. Moving one sends
# it to another Time Slot; the model has one row, so DEVIOUS_MOVE_SLOTS
# counts only the distance bought.
EXAM_COUPONS = ("exam_recover", "exam_reroll", "exam_target", "exam_ignore")
DEVIOUS_IGNORE_SETBACK = ()
DEVIOUS_MOVE_SETBACK = ()
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
    19: ("peek3", "always"), 20: ("peek1", "always"),
    21: ("recover_any", "always"), 22: ("recover_committed", "few_dice"),
    23: ("str", "always"), 24: ("recover_any", "one_attempt"),
    25: ("recover_committed", "crit"),
}
# 19 and 20 went in on 2026-11-06 and were the last two Tasks with no
# modelled text. Both pay in DECK ORDER rather than in dice, which is why
# they sat out: the model draws with deck.pop(), so the next card is the end
# of the list, and ordering it is a real decision once there is a preference
# to order by. Decode Nobulous' Lecture Notes looks at the next three and
# returns them in any order; Update Nobulous' Lab Notes looks at one and
# sends it to the top or the bottom.
#
# THE DEMAND SIDES of the same two cards are the other half, and they are
# the only two Demand clauses in the deck that are not a penalty - they are
# restrictions on how the card may be worked, so they go on the card as
# TASK_EFFECT rather than in this table.
#   three_colors  Decode, on Demand: at least 3 different die colours
#   store_one     Update, on Demand: no more than 1 die may be stored here
TASK_EFFECT = {19: "three_colors", 20: "store_one"}
# Crits of one color count as 3 successes on these Tasks.
CRIT_COLOR = {2: "blue", 7: "purple", 11: "purple"}

# Opportunity payouts, in deck order, matching generator/build_nap.py.
OPPORTUNITY_REWARD = ["hp", "recover2", "str_next", "rec_next", "recover3", "crit_next"]

# One ability per Apprentice. All six are modelled; Prodigy's needed the
# colour rule to be enforced on successes first - see COLOR_RULE_ON_SUCCESS.
# Candidate Slacker abilities. "small_row" is the PRINTED one as of the
# 2026-10-31 rewording; ABILITIES still maps Slacker to "discard" and
# __init__ redirects it through SLACKER_ABILITY, so this constant is the
# one switch that decides what Slacker does.
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

ABILITIES = {"Prodigy": "wild_one", "Slacker": "discard",
             "Technician": "setback_window",
             "Savant": "wide_recovery", "Opportunist": "dot_recovery",
             "Lab Rat": "soak"}

# THE COLOUR RULE, ON SUCCESSES - and this is what Prodigy was waiting for.
# rules/nap.html: to complete or store an Assignment the successes must
# include "a successful die matching its color dot, Red as wild, or two
# SUCCESSFUL dice of the same other color". Until 2026-11-06 this model
# enforced the rule on the COMMIT instead - commit_for leads with a matching
# die, or Red, or a pair - and never asked whether those dice succeeded,
# which is strictly more generous than the cards.
#
# It is also why Prodigy had no ability for the whole life of this file.
# "When using two dice of the same color as wild, only one of those dice
# must roll a success" relaxes a requirement the model did not have, so
# ABILITIES mapped Prodigy to None and the default Apprentice - in run(),
# in audit.py and in every hand-run cell - was the one with nothing to do.
# A card cannot be modelled by itself: this one needed the rule it modifies.
#
# False restores the commit-only rule every figure published before
# 2026-11-06 was measured through.
COLOR_RULE_ON_SUCCESS = True

CREDITS_TO_LEAVE = 6      # Easy 5, Standard 6, Hard 7, Nobulous 8
# Difficulty is the pair (Credit goal, Setbacks in the deck).
#
# RE-PEGGED 2026-11-06, one Setback off every rung: 4/4/5/6 became 3/3/4/5.
# The Credit goals did not move. This is the ladder catching up with a MODEL
# FIX, not a difficulty decision: the colour rule is now enforced on the
# SUCCESSES rather than on the commit, which is what rules/nap.html prints,
# and the old model was more generous than the cards by about 5 points of win
# rate at every rung. One Setback is worth about the same 5, so the solo
# column lands back where it was published - 56.2 / 48.8 / 38.1 / 29.4
# against the old 55.5 / 48.8 / 37.5 / 29.7 - and NAP is pitched against the
# printed game for the first time.
#
# THE COUNT IS PRINTED, so three sources carry it and all three had to move:
# this table, the difficulty table in rules/nap.html, and NAP_SETBACK_COUNT
# in playtest/dist/suite.js. check_app_sync.py now compares them, which
# nothing did before - the same gap that let the End-of-Day burn sit unplayed
# in this file for weeks while the other two sources played it.
LEVELS = {"Easy": (5, 3), "Standard": (6, 3), "Hard": (7, 4), "Nobulous": (8, 5)}
# End of Day burns one card off the Assignment deck, text ignored.
# rules/nap.html prints it under "End of Day" - "Reveal and discard the top
# card of the Assignment deck. Ignore all of its text, effects and Skulls" -
# and the lab has always done it (playtest/dist/suite.js, at the day
# rollover: n.discard.push(n.deck.pop())). This model shipped False, so until
# 2026-11-05 every published NAP figure described a game missing a printed
# rule: two sources out of three played it and the one that published the
# numbers did not.
#
# True is now the rule. MEASURED 2026-11-05, 20,000 games a cell, six
# Apprentices averaged: turning it on is worth +0.1 / +0.6 / +1.3 / +2.4 solo
# across the four levels and up to +2.7 at Tier III. It helps, and it helps
# MORE the harder the level, which tracks the Setbacks in the deck (4/4/5/6
# as the table stood that day; see the 2026-11-06 re-peg at LEVELS) -
# a burned card is likeliest to have been one of those. Standard moves
# 48.2 -> 48.8 and stays inside the 47-57% band, so this is a correctness fix
# and not a re-pitch of the ladder.
#
# False is kept because every NAP figure published before 2026-11-05 was
# measured with it. check_app_sync.py now holds the model, the lab and the
# rulebook together on this; nothing compared them before, which is why it
# sat.
END_OF_DAY_BURN = True
# Reaching the Credit goal ends the apprenticeship at the end of that DAY,
# not of that Time Slot: decided 2026-11-03 and printed in rules/nap.html
# under "How the apprenticeship ends". True is now the rule. False is the
# older end-of-slot reading, kept because every NAP figure published before
# 2026-11-03 was measured with it; the change costs 1.8 / 1.0 / 1.1 / 0.3
# points across the four levels.
LEAVE_AT_END_OF_DAY = True
ROW_MAX = 4
SLOTS_PER_DAY = 3


def fresh_dice():
    return [c for c in COLORS for _ in range(4)] + ["red"]


class Card(object):
    __slots__ = ("kind", "subject", "target", "demand", "dot", "skulls",
                 "on_demand", "rotated", "free", "stored", "stored_dice",
                 "penalty", "upkeep", "devious", "slot", "index", "ignored",
                 "away", "effect")

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
        # The card's own printed effect, for the decks that print one per
        # card: a Following Setback or an Imposter Task. None means the card
        # prints no effect of its own - which for a Setback is what makes it
        # a BASE Setback, carrying build_nap.SB_TEXT's row lock instead. The
        # row-lock test used to read `not c.upkeep`, which worked only while
        # every Following Setback had an upkeep and no base one did.
        self.effect = None
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
        # Per-slot and per-Day state the Tier I and II decks need.
        self.wild_used = False      # the wild coupon paid for this commit
        self.fed = set()            # cards given a die this Time Slot
        self.dot_first_used = False  # Nobulous Needs This Now, this slot
        self.locked_day = []        # Neural Extraction Practicum: off the
        #                             table until the Day turns over

        # Assignment deck: 26 Tasks + 6 Opportunities + 3 of the 6 Setbacks.
        deck = []
        for i, (t, d, dot, sk) in enumerate(TASKS):
            t, d = t + TARGET_DELTA, d + TARGET_DELTA
            card = Card("task", t, d, dot, sk, SUBJECTS[i], DEMAND_PENALTY[i])
            card.effect = TASK_EFFECT.get(i)
            card.index = i
            deck.append(card)

        # Tier II: each Imposter Task replaces a Credit Task of its subject.
        if tier in ("II", "III"):
            for i, (subject, dot, rt, dt, eff) in enumerate(IMPOSTER_TASKS):
                same = [c for c in deck
                        if c.kind == "task" and c.subject == subject]
                victim = self.rng.choice(same)
                deck.remove(victim)
                imp = Card("impostor", rt, dt, dot, 0, None,
                           victim.penalty)
                imp.index = i
                imp.effect = eff if IMPOSTER_EFFECTS else None
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

        # Tier I: 3 of the 4 Following Setbacks REPLACE 3 base Setbacks - the
        # deck keeps the same number of Setbacks, three of them nastier. It
        # used to drop every base Setback for exactly 3 Following ones, which
        # was only equivalent while SETBACKS_IN_DECK was always 3; once Hard
        # and Nobulous carried 4 and 6, turning a tier ON made them EASIER.
        following = 3 if tier in ("I", "II", "III") else 0
        # HOW MANY BASE SETBACKS SURVIVE A TIER, and the three sources do not
        # agree. rules/nrj.html: "Set the 6 base Setbacks ASIDE and shuffle
        # in 3 of the 4 Following Setbacks chosen at random, exactly where
        # the 3 base Setbacks would have gone. NEVER USE BOTH KINDS
        # TOGETHER." The lab plays that. This model mixes them, on the
        # argument recorded below - which is a real argument and still
        # contradicts the printed rule.
        #
        # With the 2026-11-06 re-peg the two readings AGREE at Easy and
        # Standard, where SETBACKS_IN_DECK is 3, and differ only at Hard (1
        # base card) and Nobulous (2). RAISED, not decided: see RESULTS.txt.
        if FOLLOWING_REPLACE_ALL and following:
            base = 0
        else:
            base = max(0, SETBACKS_IN_DECK - following)
        for i in self.rng.sample(range(4), following):
            t, dot, eff = FOLLOWING[i]
            card = Card("setback", t, t, dot)
            card.effect = eff if FOLLOWING_EFFECTS else "upkeep"
            card.upkeep = 1 if card.effect == "upkeep" else 0
            card.index = i          # Following Setback i, so it is identifiable
            deck.append(card)
        for i in self.rng.sample(range(6), min(6, base)):
            t, dot = SETBACKS[i]
            card = Card("setback", t, t, dot)
            card.index = i          # base Setback i; the six were anonymous
            deck.append(card)
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
        # WHERE DID I PUT THAT?: "While unresolved, one die committed here
        # cannot be recovered by Special Recovery." Its stored dice are
        # locked to the card and so are not in `exhausted` to begin with;
        # what the card really costs is one die of this colour held back when
        # the Special Recovery lands, which is where it bites.
        held = None
        if any(c.kind == "setback" and c.effect == "no_special"
               and not c.ignored and c.stored_dice for c in self.row):
            if color in self.exhausted:
                self.exhausted.remove(color)
                held = color
        keep = []
        for c in self.exhausted:
            if c == color:
                self.available.append(c)
            else:
                keep.append(c)
        self.exhausted = keep
        if held is not None:
            self.exhausted.append(held)
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
        pool = pick_order(self.available, self.rng)
        take = []
        # "One die counts as any color": when the coupon below pays for the
        # commit it satisfies the colour rule on its own, so the check after
        # the roll must not ask again.
        self.wild_used = False
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
                self.wild_used = True
                take.append(pool.pop(0))
        # Aim one expected success past the requirement. Committing to exactly
        # the remaining need finishes only about half the time, and a roll that
        # falls short locks its dice onto the card as stored progress - so
        # under-committing drains the pool far faster than over-committing.
        expected = sum(EV[c] for c in take)
        want = card.remaining() + policy_value(COMMIT_MARGIN, self)
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

    # What a revealed Assignment is worth, in Targets. The old policy took
    # the cheaper card and ignored the reward entirely, which declined every
    # permanent upgrade in the deck: Task 23 is Target 6 for a PERMANENT +1
    # STR and was taken in 8% of games.
    # Deliberately small. Sweeping these showed the gain comes almost
    # entirely from valuing the CREDIT, not the upgrade: the old policy would
    # take a cheap no-Credit Task over a slightly dearer Credit one, working
    # against the win condition. Weighting permanent upgrades heavily made
    # the model play WORSE at Hard and Nobulous, where a failed expensive
    # Task costs more than the bonus returns.
    REWARD_WORTH = {"str": 0.5, "rec": 0.5, "hp": 0.3, "recover_any": 0.3,
                    "recover_dot": 0.3, "recover_committed": 0.25,
                    "bonus": 0.25}

    def card_worth(self, card):
        """Higher is better: what it pays, less what it costs."""
        worth = -float(card.target)
        if card.kind == "task" and card.subject:
            worth += 2.0                      # a Credit is the win condition
        if card.kind == "opportunity":
            worth += 1.0                      # coupons are banked for later
        entry = REQUEST_REWARD.get(getattr(card, "index", None))
        if entry and card.kind == "task":
            worth += self.REWARD_WORTH.get(entry[0], 0.0)
        worth -= 0.6 * getattr(card, "skulls", 0)
        return worth

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
        # A Setback among the two must be the one you take, and Imposter Tasks
        # are Mandatory, so they are forced in the same way.
        forced = [c for c in drawn if c.kind in ("setback", "impostor")]
        if self.ability == "dodge_setback" and len(drawn) > 1:
            # The Slacker may leave a revealed Setback behind; an Imposter Task
            # is still Mandatory.
            forced = [c for c in forced if c.kind == "impostor"]
            drawn = [c for c in drawn if c.kind != "setback"] or drawn
        primary = forced[0] if forced else max(drawn, key=self.card_worth)
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
            # A BASE Setback locks the row - it is the only Setback that
            # prints "No other Assignment may be worked until this Setback is
            # resolved" - and a base Setback is one with no printed effect of
            # its own. Unscheduled Demonstration prints the weaker version,
            # "one die here before committing dice to another Assignment in
            # this Time Slot", and joins the lock until it has been fed.
            setbacks = [c for c in self.row
                        if c.kind == "setback" and not c.ignored
                        and not c.away
                        and (c.effect is None
                             or (c.effect == "work_first"
                                 and id(c) not in self.fed))
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
                # Imposter Tasks are Mandatory and come first among Tasks;
                # otherwise chase Credits, nearest-to-done next.
                workable = [c for c in self.row
                            if c.kind in ("task", "impostor")
                            or (c.kind == "setback" and c.effect
                                and not c.ignored and not c.away)
                            or (c.kind == "opportunity"
                                and (c.devious or PLAY_THE_CARDS))]
                if not workable:
                    return False
                # A Following Setback is Mandatory and worked first, then
                # Imposter Tasks, which are Mandatory too.
                card = min(workable, key=lambda c: (not (c.kind == "setback"
                                                         and c.effect),
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
            # NOBULOUS NEEDS THIS NOW: "the first die you commit to another
            # Assignment each Time Slot must match that Assignment's
            # recovery-color dot." commit_for already leads with the dot when
            # it holds one, so this bites exactly when it does not - and then
            # the commit is illegal and the Assignment cannot be worked.
            if (not self.dot_first_used
                    and any(c.kind == "setback" and c.effect == "dot_first"
                            and not c.ignored and not c.away
                            for c in self.row)
                    and not (card.kind == "setback"
                             and card.effect == "dot_first")):
                self.dot_first_used = True
                if take[0] != DOT_COLOR[card.dot]:
                    if DOT_COLOR[card.dot] not in self.available:
                        return False
                    swap = DOT_COLOR[card.dot]
                    self.available.remove(swap)
                    self.available.append(take[0])
                    take = [swap] + take[1:]
            # EMERGENCY SPECIMEN HANDLING: "Before rolling, commit at least 2
            # dice initially."
            if card.effect == "commit2" and len(take) < 2:
                spare = [c for c in self.available if c not in take]
                if not spare:
                    return False
                take = take + [pick_order(spare, self.rng)[0]]
            # CONTRADICTIONS EVERYWHERE, Decode Nobulous' Lecture Notes on
            # its Demand side: "Requires at least 3 different die colors."
            if card.effect == "three_colors" and card.on_demand:
                while len(set(take)) < 3:
                    spare = [c for c in pick_order(self.available, self.rng)
                             if c not in take]
                    if not spare:
                        return False
                    take = take + [spare[0]]
            self.fed.add(id(card))
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
                for c in pick_order(self.available, self.rng):
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
            # THE COLOUR RULE, on the successes rather than on the commit -
            # see COLOR_RULE_ON_SUCCESS. A roll whose successes do not carry
            # the card's colour applies nothing; the dice still lock to it as
            # stored progress, exactly as a roll that falls short does.
            if COLOR_RULE_ON_SUCCESS and got and not self.wild_used:
                want = DOT_COLOR[card.dot]
                hit = collections.Counter()
                for c, v in zip(take, results):
                    if v:
                        hit[c] += 1
                if not (hit[want] or hit["red"]):
                    # PRODIGY: "When using two dice of the same color as
                    # wild, only one of those dice must roll a success."
                    need = 1 if self.ability == "wild_one" else 2
                    if not any(take.count(c) >= 2 and hit[c] >= need
                               for c in COLORS if c != want):
                        got = 0
                        crit = False
            # LOAD-BEARING PROSTHETICS: "At least 2 applied successes must
            # come from the same color." A roll where no single colour
            # supplies two successes applies nothing at all - the dice still
            # lock to the card as they always do when a roll falls short.
            if card.effect == "same_color" and got:
                by = collections.Counter()
                for c, v in zip(take, results):
                    by[c] += v
                if max(by.values()) < 2:
                    got = 0
                    crit = False
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
                spent = take + card.stored_dice
                # NEURAL EXTRACTION PRACTICUM: "One die committed here
                # remains locked until the end of the Day even if completed."
                # Locked is not exhausted - it is off the table entirely, so
                # no recovery reaches it until the Day turns over.
                if card.effect == "lock_day" and spent:
                    self.locked_day.append(spent.pop())
                if OPP_DICE_RETURN and OPP_RETURN_ON_WIN and card.kind == "opportunity":
                    self.available += spent
                else:
                    self.exhausted += spent
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
                # NOBULOUS WANTS DETAILS, Update Nobulous' Lab Notes on its
                # Demand side: "You may store no more than 1 die here." The
                # rest exhaust instead of locking, so the progress they
                # bought is kept and the dice are not.
                if (card.effect == "store_one" and card.on_demand
                        and len(card.stored_dice) > 1):
                    self.exhausted += card.stored_dice[1:]
                    del card.stored_dice[1:]
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
        elif kind in ("peek3", "peek1"):
            # deck.pop() draws from the END, so the end of the list is the
            # top of the deck. A Setback is the card worth moving; after
            # that, a Task with a subject is a Credit and the rest is not.
            def welcome(c):
                if c.kind == "setback":
                    return -1
                return 1 if c.subject else 0
            if kind == "peek3":
                top = self.deck[-3:]
                if len(top) > 1:
                    del self.deck[-len(top):]
                    self.deck += sorted(top, key=welcome)
            elif self.deck and welcome(self.deck[-1]) < 0:
                self.deck.insert(0, self.deck.pop())

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
                self.spend_die()
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

    def spend_die(self, color=None):
        """Exhaust one available die.

        The card's recovery dot names the colour, and that die goes if the
        Apprentice holds one; otherwise the weakest does, so being out of
        the named colour is not a free pass. Before this, the pool was a
        flat list popped from the end, which handed over the RED die first.
        """
        if not self.available:
            return None
        if color and color in self.available:
            pick = color
        else:
            pick = min(self.available, key=lambda c: EV[c])
        self.available.remove(pick)
        self.exhausted.append(pick)
        return pick

    def soak(self):
        """Lab Rat: once a day, exhaust a die instead of losing 1 Health."""
        if self.ability != "soak" or self.ability_day == self.day or not self.available:
            return False
        self.spend_die()
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
            self.spend_die(DOT_COLOR.get(card.dot))

    def spend_devious(self, names):
        """Discard one Devious coupon BY NAME, in the order given, or refuse.

        The hand is six named cards and not a counter. The three levers below
        used to call devious_coupons.pop(), which takes whichever coupon is on
        the END of the list, so a coupon earned by any of the six paid for an
        ability none of them prints - see DEVIOUS_IGNORE_SETBACK. Now a lever
        has to name the cards entitled to pay for it, and the shipped answer
        for all three is: none of them.
        """
        for want in names:
            if want in self.devious_coupons:
                self.devious_coupons.remove(want)
                return want
        return None

    def move_setback(self):
        """Spend a coupon to send a Setback to a different Time Slot."""
        if not (DEVIOUS_MOVE_SLOTS and DEVIOUS_MOVE_SETBACK):
            return
        live = [c for c in self.row
                if c.kind == "setback" and not c.away and not c.ignored]
        if not live:
            return
        if not self.spend_devious(DEVIOUS_MOVE_SETBACK):
            return
        worst = max(live, key=lambda c: (c.upkeep, c.remaining()))
        worst.away = DEVIOUS_MOVE_SLOTS

    def ignore_setback(self):
        """Spend a coupon on the Setback that is costing the most."""
        if not DEVIOUS_IGNORE_SETBACK:
            return
        live = [c for c in self.row if c.kind == "setback" and not c.ignored]
        if not live:
            return
        if not self.spend_devious(DEVIOUS_IGNORE_SETBACK):
            return
        worst = max(live, key=lambda c: (c.upkeep, c.remaining()))
        worst.ignored = True

    def cash_devious(self):
        """Discard a Final Exam coupon for 2 dice rather than never spend it."""
        if not DEVIOUS_CASH_EARLY:
            return
        if len(self.available) <= 1 and len(self.exhausted) >= 2:
            if self.spend_devious(DEVIOUS_CASH_EARLY):
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
                # CONTAINMENT DRILL: "If unresolved, exhaust 1 available die
                # before flipping it to Demand."
                if card.effect == "demand_burn":
                    self.spend_die(DOT_COLOR.get(card.dot))
                card.on_demand = True
                survivors.append(card)
        self.repaired_this_slot = False
        self.row = survivors

    def time_slot(self):
        self.slot = (self.slot + 1) % 3     # Morning, Afternoon, Evening
        self.fed = set()
        self.dot_first_used = False
        if self.slot == 0:
            self.day += 1
            # "remains locked until the end of the Day" - the Day has turned
            # over, so the dice come back exhausted and recovery can reach
            # them again.
            self.exhausted += self.locked_day
            self.locked_day = []
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
            # A BASE Setback prints "if this Setback has no stored dice,
            # exhaust 1 available die". A Following Setback does not print
            # that clause at all; only Minor Laboratory Fire prints an
            # upkeep of its own, and it is unconditional.
            if card.effect:
                cost = card.upkeep
            else:
                cost = 0 if card.stored_dice else 1
            for _ in range(cost):
                self.spend_die(DOT_COLOR.get(card.dot))
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
        if END_OF_DAY_BURN and self.slot == 2 and self.deck:
            # "After Evening, resolve End of Day ... Reveal and discard the
            # top card of the Assignment deck. Ignore all of its text,
            # effects and Skulls."
            self.deck.pop()
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
        # You arrive at the exam having spent everything, so the clause above
        # was never once paid - measured 0.0 dice at every difficulty, which
        # made being short of the goal free and left NAP's Nobulous tier
        # columns running backwards. What cannot be paid in available dice is
        # taken from the exhausted pile and BANISHED, so Preparation below
        # cannot recover it.
        i = 0
        while missing > 0 and self.exhausted and i <= 40:
            c = order[i % len(order)]
            if c in self.exhausted:
                self.exhausted.remove(c)
                missing -= 1
            i += 1
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
        for subject, dot, base, printed in pool[:3]:
            target = max(1, base - self.credits[subject])
            rule = printed if EXAM_RESTRICTIONS else {}
            # "Ignore one Final Exam's printed restriction." Spent on the
            # exams whose restriction costs the most - the ones that forbid
            # Red, because Red is the best die in the box, and the ones that
            # demand dice or colours a bare Target would not have needed.
            if rule and "exam_ignore" in self.devious_coupons and (
                    rule.get("no_red") or rule.get("dice", 0) >= 4
                    or rule.get("colors", 0) >= 4):
                self.devious_coupons.remove("exam_ignore")
                rule = {}
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
            used = exam_commit(self.available, target, rule, self.rng)
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
            # "A Red Crit counts as 1 success"; "One Yellow Crit counts as
            # 3 successes." A Crit is 2 everywhere else in the set.
            for col_, worth in (rule.get("crit_val") or {}).items():
                values = [worth if (c == col_ and v == 2) else v
                          for c, v in zip(used, values)]
            total = sum(values)
            # "At least 1 Crit must contribute to complete this Assignment",
            # read as a gate. OFF by default - see the note on EXAMS.
            if EXAM_CRIT_GATE and rule.get("crit") and 2 not in values:
                total = 0
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
            if not self.deck:
                break
            if self.credit_total >= CREDITS_TO_LEAVE and (
                    not LEAVE_AT_END_OF_DAY or self.slot == 2):
                # self.slot is the slot just played, so slot 2 means the
                # Evening is done and the Day is complete.
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
