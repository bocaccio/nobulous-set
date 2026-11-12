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
  * Nothing in the FINAL EXAM column: all 12 restrictions are modelled.
    Eleven went in on 2026-11-06 - EXAMS carries each card's printed
    restriction and exam_commit honours it - and that also made Definitely
    Curriculum-Approved payable for the first time. The twelfth, Neural
    Response Screening, was reworded on 2026-11-08 out of Assignment
    language into the exam's own idiom and went in with the rewording; see
    the note on EXAMS.
  * The six Setbacks' individual text. The one printed rule they share -
    the row locks until the Setback is resolved - IS modeled.
  * 24 of the 26 DEMAND-side restrictions - the store caps, the per-attempt
    commit minimums, the "+1 Target per other unresolved Assignment" clauses
    and the Crit repricings. Two are modelled, as TASK_EFFECT. This is not
    new: those clauses have been printed and unmodelled throughout, and the
    2026-11-12 revision reworded only two of them. What that revision DID
    put in the model is the Demand COMPLETION REWARD, all 26 of them - see
    DEMAND_REWARD - which is the half that changes whether a flip is a
    decision.
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
# value. One more success on every check did: MEASURED THAT DAY, Standard
# landed at 51.1% and 49.5%, all six Apprentices were in band on both axes,
# the two axes converged (the printed 9.3-point gap became -1.6) because
# raising the Exam Targets is what the no-NRJ game actually leans on, and the
# per-Apprentice spread narrowed 10.8 to 8.4 at Tier III.
#
# THAT PARAGRAPH IS HISTORY, AND HALF OF ITS BAND CLAIM IS NO LONGER TRUE.
# Re-read 2026-11-08 at 12,000 games an Apprentice: Standard is 49.7% solo
# with ALL SIX Apprentices in band (49.9 / 48.6 / 53.4 / 47.1 / 51.0 / 48.3)
# and 41.6% at Tier III with NONE of them in it (39.4 at the bottom). Three things landed in between - the colour rule enforced on
# SUCCESSES (about -5 points everywhere), the Setback re-peg, and the twelfth
# exam restriction - and the Tier III axis went out of band with the first of
# them, not with the last. The sentence sat unchallenged because nothing
# checks a calibration claim: coverage.py holds predicates over printed
# EFFECTS, and a win rate in a comment has no predicate at all. Date any
# figure written here, and distrust the date first.
#
# TARGET_DELTA below is still a dial on top of these numbers, and still 0.
#
# SIX DEMAND TARGETS CAME DOWN FROM 9 TO 6 ON 2026-11-12, and Suture's Request
# rose 5 to 6. Those six - indices 9, 11, 12, 15, 18, 24 - are the whole of
# the "4 x5 and 3 x1" tail of the Request-to-Demand gap census the 2026-10-28
# Target rise left behind, and a Demand Target 4 above the Request is not a
# Target, it is a card you have written off. The same revision printed a
# COMPLETION REWARD on every Demand face, and a reward on a face nobody clears
# is dead text; DEMAND_REWARD below is what required these six to come within
# reach. The widest gap in the deck is now 1.
TASKS = [
    (3, 3, "Y", 0), (4, 5, "G", 1), (5, 5, "B", 1), (6, 7, "P", 2),
    (4, 4, "Y", 0), (4, 4, "G", 0), (4, 5, "B", 0), (6, 6, "P", 0),
    (5, 5, "G", 1), (5, 6, "B", 1), (5, 5, "B", 1), (5, 6, "P", 1),
    (6, 6, "P", 1), (7, 7, "P", 1), (4, 5, "Y", 1), (5, 6, "B", 2),
    (6, 7, "P", 2), (4, 4, "G", 0), (6, 6, "Y", 1), (5, 5, "G", 0),
    (4, 4, "Y", 0), (4, 4, "G", 0), (5, 5, "B", 0), (7, 8, "P", 1),
    (5, 6, "B", 1), (5, 5, "P", 0),
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

# What a Crit scores on Neural Response Screening, the one exam that reprices
# every colour's Crit: 1 as of 2026-11-08, when the card was reworded into the
# exam's own idiom. 2 is NO repricing, which is the clause modelled as nothing
# - what every NAP figure published before that day was measured through, so
# this is the dial that reproduces them. EXAM_CRIT_GATE below is a third
# reading, the printed wording the rewording replaced.
EXAM_CRIT_VALUE = 1

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
#             instead of the usual 2, and the colour "any" is every colour
#
# THE TWELFTH CLAUSE WAS A CARD-TEXT PROBLEM AND THE CARD WAS REWORDED,
# 2026-11-08. Neural Response Screening printed "At least 1 Crit must
# contribute to COMPLETE THIS ASSIGNMENT" - Assignment language, where
# completion is binary. A Final Exam has no completion: you lose 1 Health per
# success short and pass by surviving. So no reading of that clause said
# anything a player could act on. MEASURED: as a gate ("no Crit, no
# successes") it dealt the card's whole Target in 23% of the sittings it got,
# -3.9 points of win rate across the solo column on one card of twelve, which
# no other single exam comes near - the dot colours are weak and every colour
# crits on exactly one face. As a commit rule it said nothing at all, for the
# same reason: there is no way to commit FOR a Crit.
#
# IT NOW PRINTS "Each Crit counts as 1 success instead of 2", which is the
# idiom its own subject's other two Crit cards already use - "A Red Crit
# counts as 1 success", "One Yellow Crit counts as 3 successes" - and the
# only one of the three that applies to every colour. That last part matters:
# a single-colour repricing on a weak colour would be the same defect again,
# because the commit policy takes the strongest dice first and may never
# commit a Green at all. A Crit contributes to 78% of sittings, so this
# clause bites nearly every time the card is drawn where the gate bit 23% of
# the time, and it costs less: -1.7 points across the solo column. A player
# can also answer it, by committing another die. EXAM_CRIT_GATE restores the
# printed gate reading, and the "crit" key on the card below is what it
# attaches to - inert on its own.
#
# AND THE CARD'S BASE TARGET CAME DOWN TO 5 THE SAME DAY, which is the other
# half of the same decision. A restriction has to be priced against the
# Target on the card that prints it, and this one was not: the clause cost
# 1 to 3 points across the ladder and left three of six Apprentices below the
# 47% band floor at Standard. The two levers in LEVELS - the Credit goal and
# the Setback count - are worth 4 to 6 points each, so either would have
# overshot a 1-to-3-point problem; the Target is worth about 2 and is on the
# card doing the damage. At 5 the grid sits within 0.7 of the pre-clause
# column in all sixteen cells and all six Apprentices are back in band at
# Standard. It is the only Target-5 exam of the twelve, which is what a card
# that reprices every Crit should look like.
EXAMS = [
    ("Anatomy", "B", 6, {"colors": 3}),
    ("Anatomy", "Y", 7, {"need": ("yellow", "blue")}),
    ("Anatomy", "P", 7, {"among": (2, ("blue", "purple"))}),
    ("Theory", "G", 6, {"no_red": True, "colors": 3}),
    ("Theory", "P", 7, {"need": ("blue", "purple")}),
    ("Theory", "Y", 8, {"colors": 4, "crit_val": {"red": 1}}),
    ("Engineering", "G", 5,
     {"crit_val": {"any": EXAM_CRIT_VALUE}, "crit": True}),
    ("Engineering", "B", 7, {"dice": 4, "crit_val": {"yellow": 3}}),
    ("Engineering", "B", 7, {"no_red": True, "need": ("purple",)}),
    ("Procedure", "Y", 7, {"no_red": True, "colors": 3}),
    ("Procedure", "P", 8, {"dice": 4, "colors": 3}),
    ("Procedure", "G", 8, {"dice": 5, "colors": 3}),
]
# Restores Neural Response Screening's pre-2026-11-08 clause, read as a gate:
# the card marked "crit" scores nothing without one, and its own scoring
# clause does not apply. False is the card as it prints now.
EXAM_CRIT_GATE = False
# THE EXAM POOL, 2026-11-12: False is one card per subject chosen at random,
# shuffled, three of the four drawn. True restores the Credit-weighted pool -
# 1 card of a subject at 0-1 Credits, 2 at 2-3, 3 at 4+ - and is the dial that
# reproduces every NAP figure published before that date.
#
# THE OLD POOL WAS NOT JUST WEIGHTED, IT WAS SORTED. It took
# `subject_exams[:n]`, the first cards of each subject in EXAMS order, and
# those happen to be the cheapest: Targets 6, 6, 5 and 7 at one card each
# against subject means of 6.7, 7.0, 6.3 and 7.7. So the old rule sat three
# of the four EASIEST exams in front of you, and the new one is a real
# difficulty rise on top of being a fairer draw. That is most of the
# difference the revision measures; see rules/RULES_CHANGELOG.txt.
EXAM_POOL_BY_CREDITS = False
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
#   work_first   one die must go here before any other Assignment on each
#                ROLL - per Time Slot until 2026-11-12, which one die paid
#                off for good
#   upkeep       1 available die at the end of every slot it survives
#   no_special   Special Recovery leaves 1 die of the queued colour behind.
#                It printed "one die committed here cannot be recovered by
#                Special Recovery" until 2026-11-12, which named a die that
#                was already ineligible: a die committed here is STORED on
#                the card, and Special Recovery takes from the exhausted pool
FOLLOWING = [(7, 'Y', "dot_first"), (7, 'G', "work_first"),
             (8, 'B', "upkeep"), (8, 'P', "no_special")]
# Switch the four printed effects off and restore the flat upkeep every
# figure published before 2026-11-06 was measured through.
FOLLOWING_EFFECTS = True
# False is the rule, in all four owners, as of 2026-11-07: one base Setback
# leaves for each Following Setback that arrives, so the deck keeps the count
# the difficulty asks for and 3 of those Setbacks are nastier.
#
# True is what rules/nrj.html printed and what the lab played until then -
# the 6 base Setbacks set aside entirely and exactly 3 Following ones in
# their place, "never both kinds together". That reading INVERTED THE TIER on
# the two hard rungs, because it hands a Setback back: at Hard and Nobulous,
# which carry 4 and 5, Tier I measured EASIER than no module at all. This
# model has mixed them since the counts stopped being 3 everywhere and was
# the only owner that was right; the other three moved to it rather than the
# reverse, so NO PUBLISHED NAP FIGURE CHANGES. The two readings agree at Easy
# and Standard either way, where the count is 3.
#
# True is kept to reproduce the printed reading; see simulation/RESULTS.txt
# and rules/RULES_CHANGELOG.txt, 2026-11-07.
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
#                  2026-11-06: eleven of the twelve restrictions went into
#                  exam_commit then and the twelfth on 2026-11-08, so this
#                  card - Definitely Curriculum-Approved - has something to
#                  ignore. Before that it was earned in 153 of 6000 Tier III
#                  games and its printed reward fired in 0 of them.
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


def crit_worth(rule):
    """What one Crit scores on an exam printing this restriction.

    2 everywhere in the set except where a card reprices every colour's Crit,
    which is Neural Response Screening alone. A single-colour repricing is
    applied per die at scoring time instead, since it does not move what the
    other dice are worth. Under EXAM_CRIT_GATE the card is read as it printed
    before 2026-11-08, which carried no scoring clause at all.
    """
    if EXAM_CRIT_GATE and rule.get("crit"):
        return 2
    if (rule.get("crit_val") or {}).get("any") is None:
        return 2
    # EXAM_CRIT_VALUE and not the table entry, so the dial still answers when
    # it is set after import - which is how every other dial here is used.
    # The table is written from the same name, so the two cannot drift.
    return EXAM_CRIT_VALUE


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
    # Every colour crits on exactly one face, so a card that reprices Crits
    # for EVERY colour takes the same sixth off every die's expected
    # successes, and a player who can count commits accordingly.
    drop = (2 - crit_worth(rule)) / 6.0
    used, got, i = [], 0.0, 0
    while i < len(order) and got < target:
        used.append(order[i])
        got += EV[order[i]] - drop
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

# Request-side reward per Task, by deck order.
#
# REWRITTEN 2026-11-12, AND THE CONDITIONS ARE WHAT WENT. Fifteen of these
# entries carried a second field - "exact", "few_dice", "three_dice",
# "four_dice", "one_attempt", "no_stored", "no_crit", "crit" - because the
# cards printed "If Exact", "If completed using exactly 3 dice", "If
# completed with exactly 2 successes across all committed dice this strategy
# phase". A reward conditioned on how the dice fell is a reward the player
# reconstructs after the dice are swept, and reward_fires() below is the
# model's record of how much machinery that took. Every surviving entry now
# fires on completion.
#
# AND THE PAYOUT NAMES A COLOUR. "recover_committed" took one of the dice
# just committed, which is whatever happened to be left; the cards name a
# colour, and name one OTHER than the card's own dot, because the dot is what
# the Primary already queues for the next slot. That is a real change in the
# model, not a rewording: recovering a named colour is worth more than
# recovering an arbitrary one and strictly more than recovering the colour the
# next Special Recovery was going to sweep anyway.
#
#   colors      recover 1 exhausted die of any of these colors
#   colors2     recover 2, one of EACH listed color
#   colors_n    recover up to n of one named color
#   hp_primary  +1 Health if the card came in as the Primary
#   rec / str   +1, permanently
#   roll        +1 Strategy roll this Time Slot
#   pick_dot    choose the color the next Special Recovery queues
#   peek3       look at the top 3 and reorder them
#   bonus       counts as +1 success while resolving (applied at roll)
#   None/absent no completion reward on this face
#
# SIX ENTRIES ARE GONE RATHER THAN CHANGED, and they are the six whose printed
# Request clause is not a completion reward at all: 2, 7 and 11 reprice a
# Crit (CRIT_COLOR below), and 3, 5 and 15 add a success while you work the
# card ("bonus"). Those apply during the attempt, so they stay where the
# attempt can see them.
REQUEST_REWARD = {
    0: ("colors", ("green",)),
    1: ("colors", ("yellow",)),
    3: ("bonus", "three_colors"),
    4: ("colors", ("blue",)),
    5: ("bonus", "primary"),
    6: ("hp_primary", None),
    8: ("pick_dot", None),
    9: ("roll", None),
    10: ("exchange", "blue"),
    12: ("colors_n", ("blue", 2)),
    13: ("rec", None),
    14: ("colors", ("green",)),
    15: ("bonus", "three_colors"),
    16: ("colors2", ("green", "blue")),
    17: ("move_setback", None),
    18: ("colors", ("green",)),
    19: ("peek3", None),
    20: ("from_discard", None),
    21: ("colors", ("yellow", "blue")),
    22: ("colors", ("purple",)),
    23: ("str", None),
    24: ("drop_demand", None),
    25: ("add_die", "yellow"),
}
# Demand-side reward per Task, by deck order - ALL 26, which is the point of
# it. Until 2026-11-12 a Demand face was pure downside: a harsher printed
# rule, a penalty one slot later, and nothing at all for clearing it, so the
# model's only reason to let a card flip was that it had run out of dice.
# Now clearing a Demand pays, which makes a deliberate flip a decision. Some
# of these match the card's own dot on purpose: that is the die you just spent
# clearing it.
#
# ONE ENTRY IS NOT A DIE. Decode Nobulous' Lecture Notes pays in deck order on
# both faces - the top 3 reordered on its Request, one card peeked and
# optionally buried on its Demand.
DEMAND_REWARD = {
    0: ("colors", ("yellow",)), 1: ("colors", ("green",)),
    2: ("colors", ("blue",)), 3: ("colors", ("purple",)),
    4: ("colors", ("yellow",)), 5: ("colors", ("yellow",)),
    6: ("colors", ("green",)), 7: ("colors", ("purple",)),
    8: ("colors", ("blue",)), 9: ("colors", ("blue",)),
    10: ("colors", ("blue",)), 11: ("colors", ("purple",)),
    12: ("colors", ("blue",)), 13: ("colors", ("purple",)),
    14: ("colors", ("green",)), 15: ("colors", ("purple",)),
    16: ("colors", ("green",)), 17: ("colors", ("yellow",)),
    18: ("colors", ("green",)), 19: ("peek1", None),
    20: ("colors", ("yellow",)), 21: ("colors", ("yellow",)),
    22: ("colors", ("blue",)), 23: ("colors", ("blue",)),
    24: ("colors", ("green",)), 25: ("colors", ("purple",)),
}
# The four Imposter Tasks' rewards, (Request, Demand), in IMPOSTER_TASKS
# order. Mandatory and worth no Credit is the whole point of these cards, but
# a mandatory card that pays nothing on either face is upkeep wearing a name.
IMPOSTER_REWARD = [
    (("green", "blue"), ("green",)),
    (("purple", "green"), ("blue",)),
    (("green", "blue"), ("green",)),
    (("purple", "yellow"), ("yellow",)),
]
# THE TABLE AS IT PRINTED BEFORE 2026-11-12, kept because a dial that only
# switches rewards OFF prices the wrong thing - it measures no rewards at all
# against the new ones, and the question is what the revision changed.
# Setting TASK_REWARDS_2026_11_12 False restores these entries, their
# conditions in reward_fires and the old payout kinds, pays nothing on a
# Demand face and nothing on an Imposter Task: together, the game every NAP
# figure published before that date was measured through.
#   recover_committed  take one of the dice just committed back
#   recover_any        take one exhausted die back, any colour
#   hp                 +1 Health
#   peek1              look at the top card, bury it if it is a Setback
REQUEST_REWARD_PRE_2026_11_12 = {
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
TASK_REWARDS_2026_11_12 = True
# The six Demand Targets the same revision brought down from 9 to 6, as they
# printed before it, with Suture's Request still at 5. Setting DEMAND_TARGETS_9
# True restores them, which is the other half of reproducing an old figure.
PRE_2026_11_12_TARGETS = {9: (5, 9), 11: (5, 9), 12: (6, 9),
                          15: (5, 9), 18: (5, 9), 24: (5, 9)}
DEMAND_TARGETS_9 = False
# The two Tasks that pay in DECK ORDER rather than in dice. The model draws
# with deck.pop(), so the end of the list is the top of the deck and ordering
# it is a real decision once there is a preference to order by.
#
# THEY SWAPPED FACES ON 2026-11-12. Decode Nobulous' Lecture Notes reorders
# the top 3 on its REQUEST and peeks at one on its DEMAND; Update Nobulous'
# Lab Notes now reaches into the DISCARD on its Request instead of peeking at
# the deck. So peek3 and peek1 are both Decode's, and from_discard is Update's.
#
# TASK_EFFECT is the Demand clauses that RESTRICT how the card may be worked
# rather than penalise you for leaving it - the only two of the 26 that do,
# and still the only two.
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
# THE COUNT IS PRINTED, so FIVE sources carry it and all five have to move:
# this table, the difficulty table in rules/nap.html and the setup step above
# it, NAP_SETBACK_COUNT in playtest/dist/suite.js, NAP_DIFF in tts/lua.lua and
# the NAP quick reference in tts/build_mod.py. check_app_sync.py compares the
# first three, which nothing did before - the same gap that let the
# End-of-Day burn sit unplayed in this file for weeks while the other two
# sources played it.
#
# RETUNED ON BOTH DIALS, 2026-11-12, and this is the first time they have
# been swept together. Each had only ever been moved on its own, against a
# column measured with the other held still - which is how the ladder came to
# invert earlier the same day, Standard at 2 Setbacks overtaking Easy at 3.
# simulation/nap_ladder.py prints the surface.
#
# THE GOAL RISES BY ONE AND THE SETBACK COUNT RISES WITH IT: 5/0, 6/1, 7/2,
# 8/4. Measured 62.2 / 53.0 / 38.6 / 23.7 (Prodigy, solo), against BAT's
# pegged ladder of 63.7 / 52.8 / 37.8 / 25.8 - the one ladder in the set
# deliberately pitched at the 20 Strong community band, with Standard inside
# 47-57 and the hard end outside it on purpose.
#
# EASY HAS NO SETBACKS AND THAT IS FORCED, not a flourish. A Setback is worth
# 5 to 7 points and a Credit about 4, so Standard can only reach 53% at 1
# Setback (6/1 = 53.0; 6/2 = 45.3 is below the floor). Easy then cannot also
# be 1 - 5/1 is 55.1, a 2.1-point step that is no rung at all - so Easy is 0.
# They still meet Setbacks in the campaign: Tier I deals 3 Following ones
# whatever the difficulty says.
#
# NOBULOUS SKIPS 3 FOR 4, which is the one place the column is not +1 a rung.
# 8/3 reads 29.8 and 8/4 reads 23.7 against BAT's 25.8, so 4 is nearer - and
# 4 is where Tier I's swap finally bites, so Nobulous is the only rung whose
# CAMPAIGN axis still moves with the Setback count.
LEVELS = {"Easy": (5, 0), "Standard": (6, 1), "Hard": (7, 2), "Nobulous": (8, 4)}
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

# ----------------------------------------------------------------------
# THE 2026-11-11 RULES REVISION. Jon rewrote rules/nap.html and five of
# the edits changed rules this file implements. Each gets a dial, True
# being the printed rule and False the behaviour every NAP figure
# published before 2026-11-11 was measured through.
#
# ONE ROW PER TIME SLOT. "Assignments placed in a given Time Slot stay
# there until completed or discarded; they do not follow you into the
# next Time Slot." The page used to say the opposite in as many words -
# "the row is THE SAME ROW all game" - and this model kept one list.
#
# It is the largest of the five and it drags three others with it, which
# is why they have no dials of their own:
#   - a Setback's upkeep bills when its own slot is active, so once a
#     day rather than three times;
#   - a rotated Opportunity gets its last chance when that slot comes
#     round again, which is the next DAY, exactly as the page now says;
#   - a Task that flipped to Demand bills on its slot's next visit.
SLOT_ROWS = True
# A DEMAND-SIDE ASSIGNMENT BILLS ONCE. "...inflicts its printed Demand
# penalty and is then discarded." It used to bill again at the end of
# every slot it survived, which with SLOT_ROWS off was every slot.
DEMAND_ONCE = True
# REC RECOVERS AT END OF DAY, not at the top of every Time Slot. "Note,
# REC only occurs at the end of the day. Dice can only be recovered
# during the day via the Special Recovery or from card-specific
# effects." This is three recoveries a day becoming one and is the
# heaviest of the five on its own.
REC_AT_END_OF_DAY = True
# TWO SETBACKS REVEALED: TAKE THE HIGHER TARGET. "If two Setbacks are
# revealed, take the one with the higher Target." The model took
# whichever came off the deck first, which is not a rule, just an
# artefact of the order they were drawn in.
SETBACK_PICK_HIGHER = True
# ----------------------------------------------------------------------
# TWO PRINTED RULES THE MODEL NEVER PLAYED. Neither is new on
# 2026-11-11; both were found while reading the page against the code
# and both live in draw_into_row, which returned silently whenever the
# row was full.
#
# A BLOCKED SKULL STILL COSTS YOU. "If a Skull would add an Assignment
# while the slot already holds 4, do not add a card - instead rotate the
# Skull-generating Assignment to its Demand side once." The lab plays
# it; this file did nothing at all. Rotating early is worth more than it
# looks: the free end-of-slot flip is spent, so the card bills a real
# Demand penalty at the end of the slot instead of merely turning over.
SKULL_BLOCKED_DEMAND = True
# THE SLACKER'S ROW HOLDS 3. reveal() honoured the card and
# draw_into_row did not, so a Skull or a FINF card could push the one
# Apprentice whose printed ability is a smaller row up to four.
SMALL_ROW_CAPS_ADDS = True


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
        # One row per Time Slot under SLOT_ROWS, and `self.row` is
        # whichever of them is active; `_row` is the single all-game row
        # the model kept before 2026-11-11. Everything below goes on
        # using `self.row`, which is why this is a property and not a
        # rename of twenty call sites.
        self.rows = [[], [], []]
        self._row = []
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
        # THE DISCARD PILE, added 2026-11-12 for Update Nobulous' Lab Notes:
        # "Return 1 discarded, uncompleted Assignment to the top of the deck."
        # Only uncompleted cards are put here - the card cannot take a
        # completed one, and that holds by construction rather than by a flag.
        self.discard = []

        # Assignment deck: 26 Tasks + 6 Opportunities + 3 of the 6 Setbacks.
        deck = []
        for i, (t, d, dot, sk) in enumerate(TASKS):
            if DEMAND_TARGETS_9 and i in PRE_2026_11_12_TARGETS:
                t, d = PRE_2026_11_12_TARGETS[i]
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
        # and Nobulous carried 4 and 5, turning a tier ON made them EASIER.
        following = 3 if tier in ("I", "II", "III") else 0
        # HOW MANY BASE SETBACKS SURVIVE A TIER. All four owners agree on this
        # as of 2026-11-07 - the card footer, rules/nrj.html, this line and
        # playtest/dist/suite.js - and until then three of them swept the base
        # Setbacks out entirely for exactly 3 Following cards. This model was
        # the only one that was right, so the fix moved the other three and no
        # published NAP figure changes; see FOLLOWING_REPLACE_ALL above.
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
    def recover(self, n, distinct=0):
        """Recover n exhausted dice.

        `distinct` is how many of them may not repeat a colour, counted from
        the END of the run. rules/nap.html gives the Final Exam's Preparation
        one free die "plus 1 further exhausted die per Credit above your
        Credit goal", and then: "Excess-Credit recovery may not pick the same
        color twice." Unmodelled until 2026-11-06 - recover() popped off the
        end of the pile and happily took three of one colour.
        """
        free = max(0, n - distinct)
        for _ in range(min(free, len(self.exhausted))):
            self.available.append(self.exhausted.pop())
        seen = set()
        for _ in range(max(0, n - free)):
            pick = None
            for c in reversed(self.exhausted):
                if c not in seen:
                    pick = c
                    break
            if pick is None:
                break
            seen.add(pick)
            self.exhausted.remove(pick)
            self.available.append(pick)

    NEIGHBOURS = {"purple": ("yellow", "blue"), "blue": ("purple", "green"),
                  "green": ("blue", "yellow"), "yellow": ("green", "purple")}

    def recover_color(self, color):
        """Special Recovery: recover ALL exhausted dice of one color."""
        # WHERE DID I PUT THAT?, as reworded 2026-11-12: "While unresolved,
        # Special Recovery at the start of each Time Slot leaves 1 die of the
        # queued color exhausted."
        #
        # It used to print "one die committed here cannot be recovered by
        # Special Recovery", and that named a die that was already ineligible:
        # a die committed here is STORED on the card, locked to it, and so is
        # not in `exhausted` for Special Recovery to reach. The model guessed
        # at the intent and charged one die of the queued colour - but only
        # while the card held stored dice, which is the premise the card no
        # longer has. The clause is unconditional now, so the test is.
        held = None
        if any(c.kind == "setback" and c.effect == "no_special"
               and not c.ignored for c in self.row):
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
    @property
    def row(self):
        """The Assignments you can work right now."""
        if not SLOT_ROWS:
            return self._row
        return self.rows[self.slot if self.slot >= 0 else 0]

    @row.setter
    def row(self, cards):
        if not SLOT_ROWS:
            self._row = cards
        else:
            self.rows[self.slot if self.slot >= 0 else 0] = cards

    def all_rows(self):
        """Every row there is, for the ends of things."""
        return self.rows if SLOT_ROWS else [self._row]

    def row_cap(self):
        """How many unresolved Assignments this slot may hold."""
        if SMALL_ROW_CAPS_ADDS and self.ability == "small_row":
            return 3
        return ROW_MAX

    def unresolved(self):
        return len(self.row)

    def draw_into_row(self, free=True, source=None):
        """Add the top card to the row. `source` is the card whose Skull
        called for it, and is what pays when the slot is full."""
        if self.unresolved() >= self.row_cap():
            # "If a Skull would add an Assignment while the slot already
            # holds 4, do not add a card - instead rotate the
            # Skull-generating Assignment to its Demand side once."
            # `not source.on_demand` is the "once": a second blocked
            # Skull finds it already turned and does nothing.
            if (SKULL_BLOCKED_DEMAND and source is not None
                    and source.kind == "task" and not source.on_demand):
                source.on_demand = True
            return
        if not self.deck:
            # Out of deck is not a full slot, and the penalty is printed
            # for a full slot. Nothing is owed.
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
    # RE-KEYED 2026-11-12 to the reward kinds the cards now print. The old
    # keys - recover_any, recover_dot, recover_committed - no longer exist, so
    # every entry in this table was dead and card_worth added 0.0 for every
    # reward in the deck. A NAMED COLOUR IS WORTH MORE THAN AN ARBITRARY ONE,
    # which is why "colors" is above the 0.25 the old committed-die reward
    # carried, and the two-dice forms are worth about double.
    REWARD_WORTH = {"str": 0.5, "rec": 0.5, "roll": 0.4, "hp_primary": 0.3,
                    "colors": 0.3, "colors2": 0.6, "colors_n": 0.5,
                    "pick_dot": 0.4, "exchange": 0.3, "add_die": 0.3,
                    "drop_demand": 0.4, "move_setback": 0.1,
                    "from_discard": 0.3, "peek3": 0.2, "peek1": 0.1,
                    "bonus": 0.25}

    # AND THE TABLE THAT WENT WITH THE OLD CARDS, exactly as it was - the two
    # peek kinds are absent from it, which is not an oversight to tidy up but
    # the policy the published figures were measured through. A dial that
    # restores a card table and not the policy that reads it does not
    # reproduce anything: with the new weights in place, "all old" measured
    # 2 points off the game at HEAD, and a baseline that is not the baseline
    # is worse than no baseline at all.
    REWARD_WORTH_PRE_2026_11_12 = {
        "str": 0.5, "rec": 0.5, "hp": 0.3, "recover_any": 0.3,
        "recover_dot": 0.3, "recover_committed": 0.25, "bonus": 0.25}

    def card_worth(self, card):
        """Higher is better: what it pays, less what it costs."""
        worth = -float(card.target)
        if card.kind == "task" and card.subject:
            worth += 2.0                      # a Credit is the win condition
        if card.kind == "opportunity":
            worth += 1.0                      # coupons are banked for later
        table, worths = ((REQUEST_REWARD, self.REWARD_WORTH)
                         if TASK_REWARDS_2026_11_12
                         else (REQUEST_REWARD_PRE_2026_11_12,
                               self.REWARD_WORTH_PRE_2026_11_12))
        entry = table.get(getattr(card, "index", None))
        if entry and card.kind == "task":
            worth += worths.get(entry[0], 0.0)
        worth -= 0.6 * getattr(card, "skulls", 0)
        return worth

    def reveal(self):
        """Reveal 2, take one as Primary, discard the other."""
        row_max = 3 if self.ability == "small_row" else ROW_MAX
        if self.unresolved() >= row_max:
            # "if the row is already full when you reveal, discard both
            # revealed cards and take nothing"
            self.discard += self.deck[-2:]
            del self.deck[-2:]
            return None
        drawn = []
        while len(drawn) < 2 and self.deck:
            card = self.deck.pop()
            if card.kind == "finf":
                # The card adds an Assignment to its own Time Slot,
                # which may be this one. A card for another slot waits
                # until that slot comes round, which under SLOT_ROWS is
                # also where the Assignment lands.
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
        if forced:
            # "If two Setbacks are revealed, take the one with the higher
            # Target." Only Setbacks: an Imposter Task is Mandatory for a
            # reason of its own and keeps the old precedence.
            _sb = [c for c in forced if c.kind == "setback"]
            if SETBACK_PICK_HIGHER and len(_sb) > 1:
                primary = max(_sb, key=lambda c: c.target)
            else:
                primary = forced[0]
        else:
            primary = max(drawn, key=self.card_worth)
        self.row.append(primary)
        # "Discard the other Assignment." It is retrievable: see from_discard.
        self.discard += [c for c in drawn if c is not primary]
        self.queued = primary.dot
        # Skulls resolve only on the Assignment you chose.
        for _ in range(primary.skulls):
            self.draw_into_row(free=True, source=primary)
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
        # UNSCHEDULED DEMONSTRATION IS PER ROLL as of 2026-11-12: "commit at
        # least one die here before committing dice elsewhere on each roll".
        # It printed "in this Time Slot", which one die paid off for the whole
        # slot and which made it the mildest of the four Following Setbacks by
        # a wide margin. `fed` exists only for this clause, so clearing it
        # here is the whole of the change.
        self.fed = set()
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
                    if card.kind in ("task", "impostor"):
                        # BOTH FACES PAY. This was gated on
                        # `not card.on_demand` until 2026-11-12, when the
                        # Demand side gained a completion reward of its own.
                        if card.kind == "task":
                            self.apply_task_reward(card.index, card, take,
                                                   got, crit)
                        else:
                            self.apply_imposter_reward(card.index, card)
                        # The Opportunist's card says "on its Request side",
                        # so that one keeps the gate.
                        if not card.on_demand and self.ability == "dot_recovery":
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
        """Does the printed condition on a Request effect hold?

        TWO OF THESE ARE LIVE AND SEVEN ARE HISTORY. Fifteen Request effects
        used to be conditioned on how the dice happened to fall - "If Exact",
        "If completed using exactly 3 dice", "If completed with exactly 2
        successes across all committed dice this strategy phase" - and the
        2026-11-12 revision removed every one of those conditions from the
        cards. What a shipping card still asks is the two clauses that add a
        success WHILE you work it: 3 colours contributing, and the card being
        your Primary. The rest are reached only through
        REQUEST_REWARD_PRE_2026_11_12, and the length of this list is the
        model's record of what those conditions cost to play.
        """
        if cond == "always":
            return True
        if cond == "primary":
            return not card.free
        if cond == "three_colors":
            return len(set(take + card.stored_dice)) >= 3
        if cond == "exact":
            return got == card.remaining()
        if cond == "few_dice":
            return len(take) <= 3
        if cond == "three_dice":
            return len(take) == 3
        if cond == "four_dice":
            return len(take) == 4
        if cond in ("one_attempt", "no_stored"):
            return not card.stored_dice
        if cond == "no_crit":
            return not crit
        if cond == "crit":
            return crit
        return False

    def pay_colors(self, colors, count=1, distinct=False):
        """Recover `count` exhausted dice from among `colors`.

        The printed form of nearly every reward in the deck as of 2026-11-12.
        rules/nap.html: it takes any exhausted die of that colour, including
        one the card has just exhausted - which is why this is called after
        the card's dice have gone to the pile - and "if no die of that color
        is exhausted, skip that recovery", so a miss pays nothing rather than
        substituting something else.
        """
        taken = 0
        used = set()
        for _ in range(count):
            for c in colors:
                if distinct and c in used:
                    continue
                if self.recover_one(c):
                    used.add(c)
                    taken += 1
                    break
        return taken

    def apply_task_reward(self, index, card, take, got, crit):
        """The completion reward printed on the face a Task was finished on.

        BOTH FACES PAY AS OF 2026-11-12. This was apply_request_reward and the
        call site was gated on `not card.on_demand`, because a Demand face
        printed no reward at all - it was a harsher rule, a penalty one slot
        later, and nothing for clearing it. The model's only reason to let a
        card flip was running out of dice.
        """
        if TASK_REWARDS_2026_11_12:
            table = DEMAND_REWARD if card.on_demand else REQUEST_REWARD
        elif card.on_demand:
            return          # a Demand face printed no reward before 11-12
        else:
            table = REQUEST_REWARD_PRE_2026_11_12
        entry = table.get(index)
        if not entry:
            return
        kind, arg = entry
        if kind == "bonus":
            return          # applied at the roll, not on completion
        if not TASK_REWARDS_2026_11_12:
            # The old table's second field is a CONDITION, and seven of the
            # nine in reward_fires exist only for this branch.
            if not self.reward_fires(arg, card, take, got, crit):
                return
            if kind == "recover_committed":
                if take:
                    self.available.append(take[0])
                    if take[0] in self.exhausted:
                        self.exhausted.remove(take[0])
            elif kind == "recover_any":
                self.recover(1)
            elif kind == "hp":
                self.hp = min(3, self.hp + 1)
            elif kind == "rec":
                self.rec += 1
            elif kind == "str":
                self.str_ += 1
            elif kind in ("peek3", "peek1"):
                self.reorder_top(kind)
            return
        if kind == "colors":
            self.pay_colors(arg)
        elif kind == "colors2":
            self.pay_colors(arg, count=2, distinct=True)
        elif kind == "colors_n":
            color, count = arg
            self.pay_colors((color,), count=count)
        elif kind == "hp_primary":
            # "If this is the Primary, gain 1 Health." `free` is set on a card
            # that arrived by Skull or FINF rather than being chosen.
            if not card.free:
                self.hp = min(3, self.hp + 1)
        elif kind == "rec":
            self.rec += 1
        elif kind == "str":
            self.str_ += 1
        elif kind == "roll":
            # "You may take 1 additional Strategy roll this Time Slot." The
            # allowance rises even if STR is already spent, so it is added to
            # the rolls left in the slot and not to the stat.
            self.rolls_left += 1
        elif kind == "pick_dot":
            # "Choose the next Special Recovery color (not Red)." The colour
            # the Primary queued is overridden; take the colour that has the
            # most dice in the pile, which is what the sweep is worth.
            if self.exhausted:
                self.queued = max(
                    "PBGY", key=lambda d: self.exhausted.count(DOT_COLOR[d]))
        elif kind == "exchange":
            # THE CEREBRAL COUPLER: "Exchange 1 available die for 2 exhausted
            # dice of its color." Optional, and it needs two of that colour
            # already in the pile before the available die is paid - so it is
            # a net gain of one die, never a loss.
            for c in (arg,) + tuple(DOT_COLOR[d] for d in "PBGY"):
                if c in self.available and self.exhausted.count(c) >= 2:
                    self.available.remove(c)
                    self.exhausted.append(c)
                    self.pay_colors((c,), count=2)
                    break
        elif kind == "add_die":
            # SHARPEN THE SURGICAL IMPLEMENTS: "Add 1 Yellow die as a hit to
            # another Task here with stored progress." It needs a Task already
            # holding progress, because that is what satisfies the colour rule.
            others = [c for c in self.row
                      if c is not card and c.kind in ("task", "impostor")
                      and c.stored_dice]
            if others and arg in self.available:
                self.available.remove(arg)
                best = min(others, key=lambda c: c.remaining())
                best.stored += 1
                self.exhausted.append(arg)
        elif kind == "drop_demand":
            # DISPOSE OF FAILED SAMPLES: "You may discard another unresolved
            # Demand here without penalty." Its stored dice exhaust; it pays
            # no penalty and earns no Credit.
            victims = [c for c in self.row
                       if c is not card and c.on_demand
                       and c.kind in ("task", "impostor")]
            if victims:
                worst = max(victims, key=lambda c: (c.remaining(), -c.penalty))
                self.exhausted += worst.stored_dice
                self.row.remove(worst)
                self.discard.append(worst)
        elif kind == "move_setback":
            # DOCUMENT THE PROCEDURE: "You may move a Setback to a different
            # Time Slot with room." The model has one row, so a move is
            # `away` slots spent elsewhere, the same convention the Devious
            # move uses. IT RARELY FIRES, and that is the card: a base Setback
            # locks the row, so you cannot work this Task while one is on it,
            # and what is left to move is a Following Setback or nothing.
            live = [c for c in self.row if c.kind == "setback"
                    and not c.away and not c.ignored]
            if live:
                max(live, key=lambda c: (c.upkeep, c.remaining())).away = 1
        elif kind == "from_discard":
            # UPDATE NOBULOUS' LAB NOTES: "Return 1 discarded, uncompleted
            # Assignment to the top of the deck." A retrieved Task comes back
            # as a fresh Request, so its rotation and progress reset. Completed
            # cards never enter self.discard, so they cannot be taken.
            if self.discard:
                best = max(self.discard, key=self.card_worth)
                self.discard.remove(best)
                best.on_demand = False
                best.rotated = False
                best.stored = 0
                best.stored_dice = []
                self.deck.append(best)
        elif kind in ("peek3", "peek1"):
            self.reorder_top(kind)

    def reorder_top(self, kind):
        """Decode Nobulous' Lecture Notes, on either face.

        deck.pop() draws from the END, so the end of the list is the top of
        the deck. A Setback is the card worth moving; after that, a Task with
        a subject is a Credit and the rest is not.
        """
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

    def apply_imposter_reward(self, index, card):
        """An Imposter Task's recovery, on whichever face cleared it."""
        if not TASK_REWARDS_2026_11_12:
            return
        if index is None or index >= len(IMPOSTER_REWARD):
            return
        self.pay_colors(IMPOSTER_REWARD[index][1 if card.on_demand else 0])

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
                    self.discard.append(card)   # discarded, no penalty
                    continue
                card.rotated = True
                survivors.append(card)
            elif card.kind == "setback":
                survivors.append(card)      # no printed Demand side
            elif card.on_demand:
                self.demand_penalty(card)
                if DEMAND_ONCE:
                    # "...and is then discarded." Its stored dice are
                    # locked to it, so they exhaust as the card leaves,
                    # the same way final_exam releases them.
                    self.exhausted += card.stored_dice
                    self.discard.append(card)
                    continue
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
        self.fed = set()                    # spend_roll clears it per roll
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
        if not REC_AT_END_OF_DAY:
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
        if not self.deck and not any(self.all_rows()):
            return False
        self.reveal()
        self.work()
        self.end_of_slot()
        if REC_AT_END_OF_DAY and self.slot == 2:
            # End of Day, and BEFORE the Opportunity bonuses below come
            # back off: a card that paid "+1 REC next slot" into the
            # Evening has to be worth something when the Day settles.
            # The book puts this after the deck burn; the burn touches
            # the deck and not the dice, so the two do not interact.
            self.recover(self.rec)
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
        for _row in self.all_rows():
            for card in _row:
                self.exhausted += card.stored_dice
            del _row[:]
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
        # Preparation: 1 die, plus 1 per Credit above the goal, plus the
        # queued recovery. "Excess-Credit recovery may not pick the same
        # color twice" - so only the first die is a free choice.
        extra = max(0, self.credit_total - CREDITS_TO_LEAVE)
        self.recover(1 + extra, distinct=extra)
        if self.queued:
            self.recover_color(DOT_COLOR[self.queued])

        # BUILD THE EXAM POOL: 1 card chosen at random from EACH of the four
        # subjects, shuffled, three drawn. Every subject has a 75% chance to
        # appear and can appear at most once; Credits only reduce Targets.
        #
        # REPLACED 2026-11-12. The old rule put 1 card of a subject in the
        # pool at 0-1 Credits, 2 at 2-3 and 3 at 4+, which stacked the pool
        # with the subjects you had already studied - so the exams you were
        # best prepared for were the likeliest to come up, and the Credit
        # ladder was pulling in the same direction as the Target reduction it
        # already pays for. It also took `subject_exams[:n]`, the FIRST cards
        # of each subject in table order, so eight of the twelve printed exams
        # could not be drawn at all at 0-1 Credits in their subject - which is
        # why eleven printed restrictions could go unmodelled for weeks
        # without the ladder noticing.
        pool = []
        for s in SUBJECT_LIST:
            subject_exams = [e for e in EXAMS if e[0] == s]
            if not subject_exams:
                continue
            if EXAM_POOL_BY_CREDITS:
                n = (1 if self.credits[s] <= 1
                     else (2 if self.credits[s] <= 3 else 3))
                pool += subject_exams[:n]
            else:
                pool.append(self.rng.choice(subject_exams))
        self.rng.shuffle(pool)
        for subject, dot, base, printed in pool[:3]:
            target = max(1, base - self.credits[subject])
            rule = printed if EXAM_RESTRICTIONS else {}
            # "Ignore one Final Exam's printed restriction." Spent on the
            # exams whose restriction costs the most - the ones that forbid
            # Red, because Red is the best die in the box, the ones that
            # demand dice or colours a bare Target would not have needed, and
            # the one that reprices every Crit, which costs about as much.
            if rule and "exam_ignore" in self.devious_coupons and (
                    rule.get("no_red") or rule.get("dice", 0) >= 4
                    or rule.get("colors", 0) >= 4 or crit_worth(rule) < 2):
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
            # 3 successes"; "Each Crit counts as 1 success instead of 2",
            # which is the colour key "any". A Crit is 2 everywhere else.
            had_crit = 2 in values
            gate = EXAM_CRIT_GATE and rule.get("crit")
            if not gate:
                for col_, worth in (rule.get("crit_val") or {}).items():
                    if col_ == "any":
                        worth = crit_worth(rule)
                    values = [worth if (v == 2 and col_ in ("any", c)) else v
                              for c, v in zip(used, values)]
            total = sum(values)
            # The pre-2026-11-08 wording, "At least 1 Crit must contribute to
            # complete this Assignment", read as a gate. OFF by default; the
            # Crit is counted before any repricing, so the two readings cannot
            # interfere - see the note on EXAMS.
            if gate and not had_crit:
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
