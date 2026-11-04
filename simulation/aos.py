"""Automaton of Shale: allocate dice to Elements before rolling.

Rules source: rules/aos.html; Program targets and Element counts are lifted
verbatim from playtest/dist/app.js, which carries the canonical tables.

A Program shows several Elements, each with a printed Target. Dice are
allocated to Elements up front, then each Element is rolled. An Element that
misses its Target fails; two failed Elements in one Program is a Catastrophic
Failure and costs 1 HP. Reach the end of Advanced Programming with HP left
to win.
"""
import random

from dice import COLORS, EV, policy_value, roll

ELEMENT_COUNTS = {
    "Routine": [3, 3, 3, 3, 3, 4, 3, 4],
    "Specialized": [3, 4, 3, 4, 3, 4, 4, 4],
    "Unstable": [4, 4, 4, 4, 4, 4, 4, 4],
    "Advanced": [5, 4, 5, 4, 5, 4, 5, 5],
}

PROGRAM_TARGETS = {
    "Routine": {
        "front": [[2,3,2],[3,2,2],[2,2,3],[2,3,2],[3,2,2],[2,2,2,2],[2,3,2],[2,2,2,3]],
        "back":  [[3,3,2],[3,3,2],[3,2,3],[2,4,2],[3,2,3],[2,3,2,2],[2,3,3],[2,2,3,3]],
    },
    "Specialized": {
        "front": [[3,2,3],[2,3,2,2],[3,3,2],[2,3,2,3],[3,2,3],[3,2,3,2],[2,3,3,2],[3,2,2,3]],
        "back":  [[3,3,3],[3,3,2,2],[3,4,2],[2,3,2,4],[4,2,3],[3,2,4,2],[2,4,3,2],[3,2,3,3]],
    },
    "Unstable": {
        "front": [[3,2,3,2],[2,3,2,3],[3,2,3,2],[2,3,3,2],[3,2,2,3],[2,3,2,3],[3,3,2,3],[3,2,3,2]],
        "back":  [[4,2,3,2],[2,3,2,4],[3,2,4,2],[2,4,3,2],[4,2,2,3],[2,3,2,4],[3,4,2,3],[3,3,3,2]],
    },
    "Advanced": {
        "front": [[2,3,3,3,2],[3,3,3,3],[2,3,3,3,3],[3,3,3,2],[3,2,3,2,3],[3,3,3,3],[2,3,3,3,2],[3,3,3,3,3]],
        "back":  [[2,3,4,3,2],[3,4,3,3],[2,3,3,4,3],[4,3,3,2],[3,2,4,2,3],[3,3,4,3],[2,4,3,3,2],[3,3,4,3,3]],
    },
}

# Reward earned for completing a Program with no failed Element.
# Required-colour dots, element by element, GENERATED from
# generator/aos.py's REQ_MAP - the authoritative card data. One entry
# per element, a colour name or None, and the same dots on both faces
# of a card. check_app_sync.py holds this against the generator.
#
# Dot counts are NOT uniform per deck, whatever rules/aos.html says:
# Routine and Unstable carry 1 each, Specialized carry 2 except Carry
# a Moving Load which carries 4, and Advanced carry 2 except Rapid
# Approach and Unobserved Entry which carry 3.
PROGRAM_REQS = {
    "Routine": [
        ["green", None, None],                       # Maintain Balance
        ["purple", None, None],                      # Lift a Heavy Object
        [None, None, "yellow"],                      # Climb an Incline
        [None, "blue", None],                        # Move at Speed
        ["green", None, None],                       # Navigate a Passage
        [None, None, "purple", None],                # Cross Uneven Ground
        ["yellow", None, None],                      # Manipulate an Object
        [None, None, "blue", None],                  # Detect an Obstacle
    ],
    "Specialized": [
        ["purple", None, "yellow"],                  # Traverse Difficult Terrain
        ["green", None, "blue", None],               # Move Without Detection
        [None, "yellow", "purple"],                  # Track a Moving Subject
        ["blue", None, None, "green"],               # Climb a Vertical Surface
        ["purple", "yellow", None],                  # Clear an Obstacle
        [None, "green", None, "blue"],               # Operate in Low Light
        ["yellow", None, "purple", None],            # Maintain a Pursuit
        ["yellow", "purple", "blue", "green"],       # Carry a Moving Load
    ],
    "Unstable": [
        ["purple", None, None, None],                # Navigate Without Guidance
        [None, None, "yellow", None],                # Evade Observation
        [None, "blue", None, None],                  # Overcome a Barrier
        [None, None, "green", None],                 # Intercept a Moving Subject
        ["yellow", None, None, None],                # Maintain Control of a Load
        [None, None, None, "purple"],                # Adapt to Changing Terrain
        [None, "green", None, None],                 # Execute a Complex Route
        [None, None, "blue", None],                  # Operate Autonomously
    ],
    "Advanced": [
        ["purple", None, "green", "yellow", None],   # Rapid Approach
        ["yellow", "green", None, "blue"],           # Unobserved Entry
        ["yellow", None, None, "purple", None],      # Subject Acquisition
        [None, "blue", None, "green"],               # Difficult Extraction
        ["green", None, None, "yellow", None],       # Autonomous Infiltration
        [None, "purple", None, "blue"],              # Controlled Restraint
        ["blue", None, None, "green", None],         # Adaptive Pursuit
        ["yellow", None, "purple", None, None],      # Council Extraction Protocol
    ],
}

# Every element must receive at least this many dice, so an element cannot
# be given up for nothing. 0 is the printed rule, under which a bare element
# "simply fails" and exhausts no dice - which is what makes deliberate
# single-element sacrifice worth 10 to 27 points. 1 prices that triage in
# dice without touching the negate rule, the escalation rule or any Target.
#
# PRINTED 2026-11-03, so 1 is now the rule: rules/aos.html, "Allocation floor
# and cap". It cuts the sacrifice edge from +26.9 to +8.0, makes
# indiscriminate sacrifice actively bad at Easy and Standard, RAISES honest
# play 4.4 to 6.2 - the naive policy had been leaving late elements bare when
# dice ran dry, and spreading is simply better - and keeps 28.7 points of
# ladder spread against 13.9 under the exploit. The playtest lab had always
# enforced it (rollElement: "Allocate at least one die first"), so the
# rulebook was the odd one out. 0 is the old printed rule.
MIN_DICE_PER_ELEMENT = 1

# Required-colour dots are now modelled. False reproduces every AoS figure
# published before 2026-11-03, all of which were taken without them.
REQUIRED_COLORS = True
# Programs begun, and Programs that could not be executed because a required
# colour was not available. The second over the first is how often the new
# "lose 1 Health and move on" branch actually fires.
REQ_TRIED = [0]
REQ_SHORT = [0]

PROGRAM_REWARDS = {
    "Routine": ["hp", "recover", "rec", "unheat", "str", "banish", "recover", "unheat"],
    "Specialized": ["hp", "str", "recover", "rec", "unheat", "banish", "recover", "unheat"],
    "Unstable": ["hp", "rec", "unheat", "str", "recover", "banish", "recover", "unheat"],
}

DECKS = ["Routine", "Specialized", "Unstable"]

# Difficulty is the mix of the three decks, not a choice of one: (Routine,
# Specialized, Unstable), summing to the 8 Programs you cycle.
# ---- dice-economy levers, all defaulting to the printed rules ----------
# AoS's pool never runs short: a Program costs 0.45 dice net. These exist to
# measure what would change that. See dicetension.py.
OVERKILL_SCALE = False   # True: burn 1 die per point above Target+1
RECOVERY_DELTA = 0       # added to the REC recovered each Program
OPTIMAL_BONUS = 2        # dice back for landing exactly on Target
RECOVERY_ON_CLEAN = False  # base REC only recovers on a Program with no
                           # failed element, so a bad Program compounds
ELEMENT_COST = 0         # dice exhausted per resolved element, win or lose:
                         # makes allocating dice into SPENDING them, which
                         # the printed rules explicitly say it is not


# (Routine, Specialized, Unstable), summing to the 8 Programs you cycle.
# Specialized is held at 3 and each step up trades one Routine Program for
# one Unstable, so the ladder is a single substitution repeated.
# Retuned 2026-11-03, one rung harder across the board. AoS read 63.1% solo
# at Standard against BAT's 53.2 and NAP's 48.2, because every earlier pitch
# was made against a model with no required colours and a free abandon. The
# mix is AoS's difficulty dial and the steps are an even ~9 points:
#   5/3/0 72.7   4/3/1 63.1   3/3/2 52.5   2/3/3 44.0   1/3/4 35.6   0/3/5 28.1
# Specialized stays at 3 and each rung trades one Routine for one Unstable,
# which is what rules/aos.html prints.
LEVELS = {
    "Easy": (4, 3, 1),
    "Standard": (3, 3, 2),
    "Hard": (2, 3, 3),
    "Nobulous": (1, 3, 4),
}
LEVEL_NAMES = ["Easy", "Standard", "Hard", "Nobulous"]

# ---------------------------------------------------------------------------
# NRJ overlay tiers. Each tier includes the ones before it.
#   I   - draw 1 of 6 Nobulous Interference cards at setup
#   II  - 6 Corrupted Limitations shuffled into the Limitation deck
#   III - 6 Backdoor Routines, at most 2 claimed per game
# Card text from the INTF / CORRUPT / BACKDOOR tables in generator/build_nrj.py.
# ---------------------------------------------------------------------------
INTERFERENCE = [
    "all_overheated",   # I Don't Have Time for This
    "banish_one",       # Legacy Hardware: banish 1 non-Red die at setup
    "flip_two",         # Nobulous Was Here: 2 Programs start Overheated
    "cap_first",        # Undocumented Dependencies: element 1 gets 1..Target
    "crit_shift",       # Works on My Machine
    "memory_leak",      # over-allocation costs 1 extra exhausted die
]

# Base Limitations are not modeled, so Tier II is modeled as the chance of
# drawing a Corrupted one: 6 corrupted cards added to a 6-card deck, so half
# the Programs face one. A Corrupted Limitation withholds 2 dice of a randomly
# selected color, on top of a printed allocation corruption that is not
# modeled.
# The 6 Limitations, in deck order. 0-3 are colour shortages, 4 is the
# Diversity Protocol and 5 is the Red Quarantine.
LIMITATIONS = ["yellow", "green", "blue", "purple", "diversity", "red"]

# The six Experimental Technicians. One ability each, once per Program unless
# the card says otherwise.
#   architect  move up to 2 allocated dice between unresolved elements
#   debugger   after missing by exactly 1, reroll 1 die on that element
#   optimizer  Target + 1 may count as Optimal Implementation
#   engineer   the safe threshold is Target + 2 on up to 2 elements
#   operator   a colour shortage may withhold 1 die as another non-Red colour
#   compiler   an extra STR roll rerolls only the dice that missed
TECHS = ["architect", "debugger", "optimizer", "engineer", "operator", "compiler"]

# The Compiler's printed ability - an extra STR roll rerolls only the misses -
# is the exception to REROLL_MODE "element", where everyone else throws the
# whole element and takes the new result. Under REROLL_MODE "select" it
# restates the base Strategy phase and does nothing, which is what these
# candidates were drafted for:
#   compile      the printed card, kept for comparison
#   optimize     one element's Target is 1 lower
#   link         carry 1 surplus success from a cleared element to a later one
#   cache        the first element resolved exhausts no dice
#   analyse      reroll one whole element and keep the better total
COMPILER_ABILITY = "compile"

# An extra STR roll rerolls the dice you pick and keeps the rest. With this
# False the model throws the whole element again, which is how it behaved
# before the base Strategy phase was modelled properly.
PUSH_REROLL = True
# Dice held back from each element. Target + 1 is a RULES cap and cannot be
# exceeded, so this only ever fills less: 0 is the calibrated policy.
FILL_MARGIN = 0

# ---------------------------------------------------------------------------
# PLAYER MODEL. simulation/players.py sets these to approximate kinds of
# human player. The defaults are the calibrated policy every other tool in
# this package runs on, so leaving them alone changes nothing.
#   DICE_ORDER    "strongest" take the best die first - the tuned policy
#                 "weakest"   save the good dice for later, a common error
#                 "random"    no ordering at all
#   COMMIT_MARGIN how many expected successes to throw past the requirement
# ---------------------------------------------------------------------------
DICE_ORDER = "strongest"


def pick_order(seq, rng=None):
    """The order a player takes dice in, per DICE_ORDER."""
    if DICE_ORDER == "random" and rng is not None:
        out = list(seq)
        rng.shuffle(out)
        return out
    return sorted(seq, key=lambda c: EV[c], reverse=DICE_ORDER != "weakest")

# How an extra Strategy roll works. "element" is the AoS rule, printed at
# rules/aos.html:117 and implemented in playtest/dist/app.js: the whole
# element is thrown again and the new result replaces the old one, better or
# worse. Allocation therefore has to be right the first time, which is the
# point of it. "select" is the base 20 Strong procedure - choose which dice
# go back in the cup - and is kept only so the difference can be measured.
REROLL_MODE = "element"
# Counts how often each resolution branch fires, for working out which rules
# earn their place in the rulebook. Off unless a caller clears it.
FIRINGS = None

TARGET_DELTA = 0   # flat rise on every printed element Target

CORRUPT_CHANCE = 0.5
CORRUPT_WITHHOLD = 2
# A Corrupted Limitation draws its withheld colour from the ones this
# Program does NOT require. False is the printed rule - "withhold 2 dice of
# a randomly selected color" - under which the withheld colour may be one a
# dot needs, and the Program then cannot be executed at all: 1 Health, no
# roll, no decision. That compounding is what dropped Tier II and III by 20
# points when required colours were implemented.
# PRINTED 2026-11-03, so True is now the rule: a Corrupted Limitation draws
# its colour from the ones the Program does not require. It lifts Tier II
# and III about 8 points and, more to the point, restores their shape - the
# drop from the pre-required-colour figures becomes near-uniform across the
# three tiers instead of twice as deep at II and III.
CORRUPT_AVOID_REQUIRED = True

# Backdoor Routines: at most 2 claimed per game. The two modeled are the ones
# whose rewards change an outcome rather than an allocation choice - "treat one
# failed element as successful" and "recover 2 exhausted dice".
BACKDOOR_CLAIMS = 2

# THE SIX CLAIM CONDITIONS. Each Backdoor Routine prints a condition as well
# as a later one-shot use, and the NRJ campaign retains the Routines you
# claimed - so what the finale inherits from AoS is how many conditions you
# met, capped at the 2 claims a game allows. The conditions below are the
# printed ones from the BACKDOOR table in generator/build_nrj.py, read
# against rules/aos.html: the allocation cap is Target + 1, an element FAILS
# when it misses its Target, and OPTIMAL IMPLEMENTATION is landing exactly
# on it.
#
#   Diagnostic Port       no element over-allocated - every element held at
#                         most its Target in dice
#   Privilege Escalation  an Overheated Program completed with no element
#                         failed
#   Resource Fork         total dice committed no more than the summed
#                         Targets plus 1
#   Packet Sniffer        Crits on at least two different elements
#   Garbage Collection    completed while at least 4 dice were exhausted
#   Root Access           Optimal Implementation on at least two elements
#
# This is OBSERVATION ONLY. Nothing recorded here changes how a Program
# resolves, so the win rates are untouched and the calibration holds; the
# model still grants the 2 Root Access uses at setup as it always did.
BACKDOOR_NAMES = ("Diagnostic Port", "Privilege Escalation", "Resource Fork",
                  "Packet Sniffer", "Garbage Collection", "Root Access")

# WHEN TO SPEND ONE. The NRJ campaign retains a claimed Routine either way,
# but a Routine still HELD at the end is worth more to the finale than one
# cashed in - the campaign's challenge is to win each game using as few of
# these buffs as it can. So spending is a policy, not a reflex:
#
#   greedy   negate every Catastrophic Failure you can. The shipped model,
#            and the default, so the calibrated win rates do not move.
#   last     negate only when the Health it costs would end the game.
#   hoard    never negate; carry both Routines into the finale.
BACKDOOR_POLICY = "greedy"

# CLAIMING BY WORKING IT, the proposed replacement for the printed claim
# conditions. Measured 2026-10-29: five of the six conditions fire in 76-100%
# of games, so claiming costs nothing and the whole AoS carryover rests on the
# spend decision. NAP does not have that problem, because a Devious
# Opportunity has to be WORKED like an Assignment before it is yours.
#
# The same idiom here: a Backdoor Routine prints a claim Target, and during a
# Program you may put dice on the ROUTINE instead of on an element. Dice spent
# claiming are dice not spent on the Program, which is the trade the printed
# conditions never asked for.
#
# PRICED IN DICE IT DOES NOT WORK. Diverting dice to the Routine costs 8
# points of AoS win rate for ONE die and 21 for three, because exhaustion is
# the whole game here - the dice economy cannot spare them. Measured
# 2026-10-29: Target 1 / 1 die / 2 tries reads 40.4% against a baseline of
# 48.6%, and Target 3 / 3 dice / 3 tries reads 19.8%.
#
# SO THE CLAIM FORKS THE REWARD INSTEAD. A Program completed with no failed
# element claims its printed Program Reward; you may claim a Backdoor Routine
# INSTEAD. That is NAP's shape exactly - a Devious Opportunity is worked in
# place of a Credit Task, giving up the game's own progress to bank a card -
# and it needs no new cost, because two of the Program Rewards are the
# permanent +1 REC and +1 STR.
#
# CLAIM_INSTEAD is how many rewards the policy will trade away. 0 is off, so
# the calibrated win rates do not move.
CLAIM_INSTEAD = 0


# "On a Catastrophic Failure you may exhaust 2 misses on failed Elements to
# negate the Health loss." Agreed with Jon 2026-10-28, after Cloudspire,
# where misses loaded on a spire absorb damage. Note the dice on a failed
# Element were exhausting anyway, so this costs nothing beyond the misses
# being there - which is why it fires on 68% of Catastrophic Failures. Set
# to 0 to recover the rule as printed before 2026-10-28.
MISSES_TO_NEGATE = 2
# How many Catastrophic Failures ONE CYCLE of the Program deck may negate,
# with Advanced Programming getting its own allowance. 0 is unlimited - the
# shipped rule. Jon's 2026-11-03 proposal is 1, and the reason is the line
# above: negating is free in dice, so nothing stops a player from failing
# on purpose, over and over, to burn the deck down to Advanced Programming
# (which an empty deck reaches, and which is won by surviving rather than
# by succeeding). A cap is the cheapest thing that makes deliberate failure
# cost Health again without touching a single printed Target.
#
# MEASURED 2026-11-03 AND NOT ADOPTED. A cap of 1 per cycle costs honest
# play 13.7 / 16.6 / 17.2 / 18.3 points across the four difficulties, which
# is a re-pitch of the whole ladder, not a patch: honest play wants the
# saving throw about 3.2 times a game and a cap of 1 denies 39% of them. A
# cap of 2 costs 3.2 / 5.3 / 5.8 / 6.7. And it buys nothing, because
# deliberate failure is not a winning line to begin with - see ALLOC_MODE.
NEGATES_PER_CYCLE = 0
# DELIBERATE FAILURE. "dump" abandons every element but one, which fails the
# Program on purpose: two failures is one Catastrophic Failure costing 1
# Health, and the negate rule above may wipe even that. The point of failing
# is that it SHORTENS THE DECK - a Stable Program flips to Overheated and an
# Overheated one is set aside - and an empty deck goes straight to Advanced
# Programming, which is won by surviving three Programs rather than by
# completing them. DUMP_DICE is how many dice are left on the one element
# that is still played, which is the only place the misses needed to negate
# can come from. "honest" is the shipped policy.
#   honest     the shipped policy: fund every element
#   dump       abandon every element but one, every Program
#   dump_hard  dump only Programs from the DUMP_DECKS list, play the rest
#              honestly - the mixed line, which keeps the Program Rewards
#              (the only way Health is ever regained) while still burning
#              the costly Programs out of the deck
#   sacrifice  write off the single most expensive element and fund the rest
#              properly. One failed element costs NO Health, and an element
#              with no dice on it exhausts none, so the only price is the
#              Program Reward. This is deliberate triage, not dumping.
#   sacrifice_short  the same, but only when the pool cannot fill every
#              element anyway - triage when short, reward-seeking when rich
#
# RE-MEASURED 2026-11-04, 12000 games a cell, on this model as it now stands
# - required colours on, the allocation floor at 1, the corruption exclusion
# on, and the retuned mix. Deliberate failure LOSES, monotonically in how much
# of it you do, and the conclusion is STRONGER than it was: at Standard 3/3/2,
# 52.7% honest, 34.8% dumping Unstable (-18.0), 6.7% dumping Specialized too
# (-46.0), 0.1% dumping everything (-52.7). The premise never comes off.
#
# The figures this block used to carry - 70.8 / 64.1 / 18.9 / 0.2 - were taken
# earlier the same day, BEFORE required colours, the floor and the exclusion
# went in and before the retune, so 70.8% honest is a number this model cannot
# produce any more. The conclusion survived the re-measurement; the numbers did
# not, which is why they are dated.
#
# THE BRAKE IS NOT THE NEGATE RULE, it is that Health is only ever regained
# through a Program Reward and a Reward needs ZERO failed elements. Failing
# on purpose forfeits the only healing in the game, from a start of 2 HP,
# with roughly 16 failures needed to burn the deck down and negation only a
# ~68% saving throw. So the route the rules appear to leave open is already
# shut by the economy, and no cap is needed to shut it.
#
# What IS wrong is the wording: "Complete all three with Health remaining"
# and "face three Advanced Programs" never say the Advanced Programs must
# be completed, so the route reads as open on paper. That is a rulebook
# fix, not a mechanical one.
ALLOC_MODE = "honest"
DUMP_DICE = 3
DUMP_DECKS = ("Unstable",)
# A Catastrophic Failure sets the Program ASIDE at once, instead of a Stable
# card flipping to Overheated and only the second failure retiring it. This
# halves the cost of burning the deck down - 8 failures rather than 16 - so
# it is the lever that decides whether deliberate failure can be a real
# option instead of a trap. It is not dumping-only: an honest player's
# Catastrophic Failures retire their Programs too, and with them the Program
# Rewards those Programs would have paid.
#
# MEASURED 2026-11-03 AND NOT ADOPTED. It does not mainly discount dumping,
# it DELETES THE ESCALATION PENALTY: today a bad failure makes a Program
# harder next time, and under this it makes the Program go away. So honest
# play gains (+3.4 / +2.9 / +4.4 / +7.5) and gains most at Nobulous, where
# the Unstable cards that escalate are thickest - the ladder flattens,
# which is the wrong direction for a difficulty dial. It also makes dumping
# the BEST line at Standard, 74.9% against 73.7% honest: the one thing it
# was meant to prevent.
CF_SETS_ASIDE = False
# A DECLARED abandon: take the Program out of the deck for a fixed price in
# Health, before anything is rolled. Never available on an Advanced Program.
#   none   no such action - the shipped rules
#   broke  abandon only a Program the pool cannot fund (the release valve)
#   hard   abandon the costly decks, per ABANDON_DECKS
#   all    abandon every Program in the deck (the degenerate line)
#
# MEASURED 2026-11-03 AND NOT ADOPTED - a DEAD BUTTON. Every policy at every
# price is strictly worse than not having it: broke -6.1/-8.3/-8.9/-8.3 at
# 1 HP, hard down to -14.2, all down to -34.4. The reason is the negate rule
# above: abandoning pays 1 Health CERTAINLY, where attempting the Program
# and failing pays 1 Health with a ~68% saving throw and leaves the chance
# the dice come good. A Health price can never compete with that, so no
# rational player presses this. Pricing an abandon in DICE rather than
# Health is the untested variant - dice are what AoS is actually short of.
ABANDON_MODE = "none"
ABANDON_COST = 1               # Health per abandon
ABANDON_DECKS = ("Unstable",)
# A failed Program is played again immediately, on its new Overheated face,
# with dumping and abandoning both forbidden on that retry. Failing the
# retry sets the card aside exactly as now, so the card still costs two
# failures - they just happen back to back, and the second one has to be a
# real attempt. This is the lever that takes away what dumping BUYS.
#
# MEASURED 2026-11-03 AND NOT ADOPTED, though it is the best behaved of the
# three: dumping stays strictly dominated at every difficulty (at Standard,
# honest 63.6% against 61.2% / 30.0% / 2.9%), the ladder keeps its shape - a
# flat -6 to -8 rather than a flattening - and it adds almost no table time,
# honest runs going 20.57 to 20.70 Programs at Standard.
#
# It is still not worth printing, and the numbers say why in a way worth
# keeping: IT IMPROVES THE DUMPING LINES. Dump Specialized+Unstable gains
# +8 to +11 and dump-everything +2 to +3, because forcing a real retry drags
# a dumper back toward playing properly, which is better for them. The rule
# does not punish the bad strategy, it CONFISCATES THE CHOICE - and the only
# player who actually pays for it is the honest one, at about 7 points.
RETRY_IMMEDIATE = False
SAVES = None          # set to a list to record saves per game
# How often the saving throw was WANTED versus taken: with a cap in place
# the gap between them is exactly what the cap costs an honest player.
NEG_WANTED = [0]
NEG_USED = [0]
# Instrumentation, like FIRINGS below: set to a Counter to record how many
# misses were sitting on the failed Elements each time a Program reaches
# Catastrophic Failure. That distribution is what decides whether the
# negate rule fires often enough to be worth printing.
NEGATE_STATS = None


def fresh_dice():
    return [c for c in COLORS for _ in range(4)] + ["red"]


class Game(object):
    def __init__(self, deck="Specialized", rng=None, tier="none",
                 composition=None, tech=None):
        """`deck` runs all 8 Programs from one deck, the published setup.

        `composition` is (routine, specialized, unstable) summing to 8 and
        builds a mixed Program set instead - the variant being explored, where
        difficulty is tuned by how many cards come from each deck rather than
        by picking one deck outright.
        """
        self.rng = rng or random.Random()
        if tech == "compiler" and COMPILER_ABILITY != "compile":
            tech = COMPILER_ABILITY
        self.tech = tech
        self.deck = deck
        self.tier = tier
        self.hp = 2
        self.str_ = 2
        self.rec = 3
        self.cycle = 1
        self.available = fresh_dice()
        self.exhausted = []
        if composition is None:
            picks = [(deck, i) for i in range(8)]
        else:
            picks = []
            for name, n in zip(DECKS, composition):
                picks += [(name, i) for i in
                          self.rng.sample(range(8), min(n, 8))]
            self.rng.shuffle(picks)
        self.composition = composition
        self.programs = [{"id": i, "deck": d, "pid": p, "status": "stable"}
                         for i, (d, p) in enumerate(picks)]
        self.queue = [p["id"] for p in self.programs]
        self.rng.shuffle(self.queue)
        self.advanced_done = 0
        self.completed = 0
        # -1 is unlimited; see NEGATES_PER_CYCLE.
        self.negates_left = NEGATES_PER_CYCLE or -1
        self.lim_queue = list(LIMITATIONS)
        self.rng.shuffle(self.lim_queue)

        # --- NRJ overlay ---
        self.intf = None
        self.corrupt = False
        self.backdoors = 0
        self.met = set()       # claim conditions met, observation only
        self.worked = 0        # ...and how many were claimed
        if tier in ("I", "II", "III"):
            self.intf = self.rng.choice(INTERFERENCE)
            if self.intf == "banish_one":
                self.available.remove(self.rng.choice(COLORS))
            elif self.intf == "flip_two":
                for p in self.rng.sample(self.programs, 2):
                    p["status"] = "overheated"
            elif self.intf == "all_overheated":
                for p in self.programs:
                    p["status"] = "overheated"
        if tier in ("II", "III"):
            self.corrupt = True
        if tier == "III":
            self.backdoors = BACKDOOR_CLAIMS

    def targets_for(self, deck, pid, face):
        return PROGRAM_TARGETS[deck][face][pid]

    def withhold_for(self, lim):
        """Dice the revealed Limitation takes out of play for this Program."""
        held = []
        if lim == "diversity":
            # "Withhold 2 non-Red dice of different colours."
            seen = set()
            order = sorted(set(self.available),
                           key=lambda c: (-self.available.count(c), EV[c]))
            for c in order:
                if c == "red" or c in seen or len(held) >= 2:
                    continue
                seen.add(c)
                self.available.remove(c)
                held.append(c)
            return held
        if lim == "red":
            if "red" in self.available:
                self.available.remove("red")
                held.append("red")
            return held
        # A colour shortage: 2 of that colour, or as many as are in play.
        need = min(2, self.available.count(lim))
        swapped = False
        for _ in range(need):
            if lim in self.available:
                self.available.remove(lim)
                held.append(lim)
        # Workaround: one of those dice may be withheld as another non-Red
        # colour instead, which keeps a scarce colour on the table.
        if self.tech == "operator" and len(held) == 2 and not swapped:
            spare = [c for c in self.available if c != "red" and c != lim]
            if spare:
    # Keep the better dice: withhold the weakest colour instead.
                best = min(set(spare), key=lambda c: EV[c])
                self.available.remove(best)
                self.available.append(held.pop())
                held.append(best)
        return held

    def seed_minimum(self, plan, targets, pool):
        """Put the minimum on every element before anything is filled.

        Takes from the WEAKEST end of the pool, because a player forced to
        put a die somewhere they expect to lose spends their worst one. The
        cap still binds, and if the pool runs out the remaining elements go
        without - "place what you have".
        """
        if not MIN_DICE_PER_ELEMENT:
            return
        for i, t in enumerate(targets):
            cap = t if (i == 0 and self.intf == "cap_first") else t + 1
            want = min(MIN_DICE_PER_ELEMENT, cap)
            while pool and len(plan[i]) < want:
                plan[i].append(pool.pop())

    def allocate(self, targets, locked=None):
        """Fill each element to its cap.

        Target + 1 is a hard cap in the rules, raised to Target + 2 on up to
        two elements by the Engineer. It used to be a soft threshold you
        could exceed by paying exhausted dice; that penalty fired zero times
        in 266,000 element resolutions across all six Technicians, because
        going past it is never worth the dice, so it became a limit.
        """
        pool = pick_order(self.available, self.rng)
        # Required-colour dice are already on their elements and count
        # toward both the Target and the Target + 1 cap.
        plan = [list(x) for x in locked] if locked else [[] for _ in targets]
        self.seed_minimum(plan, targets, pool)
        # Redundancy: the two biggest Targets get the wider threshold.
        self.wide = set()
        if self.tech == "engineer":
            spare = len(self.available) - (sum(targets) + len(targets))
            # Redundancy is worth a die only on an element big enough to miss
            # at the normal threshold, and only when the pool can spare it.
            hard = [i for i, t in enumerate(targets) if t >= 3]
            if spare >= 2 and hard:
                order = sorted(hard, key=lambda i: -targets[i])
                self.wide = set(order[:min(2, spare // 2)])
        # The cap is Target + 1, and the loop below cannot exceed it.
        for i, t in enumerate(targets):
            # Undocumented Dependencies caps the first element at its Target,
            # taking away the free Target + 1 die there.
            cap = t if (i == 0 and self.intf == "cap_first") else t + 1
            if i in getattr(self, "wide", set()):
                cap = t + 2
            cap = max(1, cap + policy_value(FILL_MARGIN, self))
            while pool and len(plan[i]) < cap:
                plan[i].append(pool.pop(0))
        return plan

    def want_abandon(self, deck, targets):
        """Would this player declare the Program abandoned?

        Never on an Advanced Program: those must be faced. Never at 1 Health
        either, since paying the price would simply end the game - abandoning
        is meant to buy tempo, not to be a way of losing.
        """
        if ABANDON_MODE == "none" or deck == "Advanced":
            return False
        if self.hp <= ABANDON_COST:
            return False
        if ABANDON_MODE == "all":
            return True
        if ABANDON_MODE == "hard":
            return deck in ABANDON_DECKS
        if ABANDON_MODE == "broke":
            # Fewer dice than the Program needs successes: most elements are
            # going to fail however they are arranged, so the Program is
            # already lost and the only question is what it costs.
            return len(self.available) < sum(targets)
        return False

    def sacrifice_allocate(self, targets, locked=None):
        """Give up one element deliberately and spend its dice elsewhere.

        The victim is the highest Target: the element that costs most to
        reach and is likeliest to fail anyway. It gets NO dice, so it
        exhausts none when it fails, and failing exactly one element costs
        no Health. Everything saved goes into the elements that are left,
        which is the point - the same pool, concentrated.

        Forfeits the Program Reward, since that needs every element to land.
        """
        if len(targets) <= 1:
            return self.allocate(targets, locked)
        pool = pick_order(self.available, self.rng)
        # Filling every element to its cap costs this much.
        need = sum(t + 1 for t in targets)
        if ALLOC_MODE == "sacrifice_short" and len(pool) >= need:
            return self.allocate(targets, locked)
        self.wide = set()           # allocate() owns the Engineer's widening
        plan = [list(x) for x in locked] if locked else [[] for _ in targets]
        # A REQUIRED-COLOUR DOT CANNOT BE ABANDONED: its die is already on
        # that element, so the cheapest element to give up is the dearest one
        # carrying NO dot. If every element carries one, nothing can be left
        # bare and the sacrifice is only partial - the victim keeps its
        # required die and gets nothing more. This is the constraint the
        # model was missing when the sacrifice measured +10 to +30.
        free = [i for i in range(len(targets)) if not plan[i]]
        victim = max(free or list(range(len(targets))),
                     key=lambda i: targets[i])
        # The minimum lands on the victim too - that is the whole point of
        # it. The victim is still given up, it just is not given up free.
        self.seed_minimum(plan, targets, pool)
        for i, t in enumerate(targets):
            if i == victim:
                continue
            cap = t if (i == 0 and self.intf == "cap_first") else t + 1
            while pool and len(plan[i]) < cap:
                plan[i].append(pool.pop(0))
        return plan

    def dump_allocate(self, targets, locked=None):
        """Fail the Program on purpose, as cheaply as possible.

        Every element but one is left bare, so it fails for nothing. The one
        exception carries DUMP_DICE of the WEAKEST dice available: weakest
        because those dice are going to be exhausted whatever happens, and
        because misses are the currency the negate rule spends. It goes on
        the hardest element, which is the one least likely to spoil the plan
        by succeeding.
        """
        if not targets:
            return []
        # The required dice are already committed and cannot be taken back.
        plan = [list(x) for x in locked] if locked else [[] for _ in targets]
        pool = sorted(self.available, key=lambda c: EV[c])
        pool.reverse()          # seed_minimum pops the weakest off the end
        self.seed_minimum(plan, targets, pool)
        pool.reverse()
        i = max(range(len(targets)), key=lambda k: targets[k])
        plan[i] = plan[i] + pool[:DUMP_DICE]
        return plan

    def element_values(self, index, dice):
        """Roll one element, honoring Works on My Machine if it is in play."""
        values = [roll(c, self.rng) for c in dice]
        if self.intf == "crit_shift":
            # A Crit on the second element counts as 3 successes; Crits on
            # every other element count as basic successes.
            values = [(3 if index == 1 else 1) if v == 2 else v for v in values]
        return values

    def element_total(self, index, dice):
        return sum(self.element_values(index, dice))

    def run_program(self, deck, pid, face, slot=None, allow_dump=True):
        targets = [t + TARGET_DELTA for t in self.targets_for(deck, pid, face)]

        if allow_dump and self.want_abandon(deck, targets):
            # Declared before the roll: pay in Health, and the card is gone.
            # -1 tells play() to retire it rather than flip it Overheated.
            self.hp -= ABANDON_COST
            self.completed += 1
            return -1

        # A Corrupted Limitation withholds 2 dice of a randomly selected
        # color before allocation; they come back once the Program resolves.
        withheld = []
        if not self.lim_queue:
            self.lim_queue = list(LIMITATIONS)
            self.rng.shuffle(self.lim_queue)
        withheld += self.withhold_for(self.lim_queue.pop())
        if self.corrupt and self.rng.random() < CORRUPT_CHANCE:
            choices = COLORS
            if CORRUPT_AVOID_REQUIRED and REQUIRED_COLORS:
                need = set(c for c in PROGRAM_REQS[deck][pid] if c)
                # If a Program requires every colour there is nothing safe
                # to take, so the corruption falls back to any of them.
                choices = [c for c in COLORS if c not in need] or COLORS
            color = self.rng.choice(list(choices))
            for _ in range(CORRUPT_WITHHOLD):
                if color in self.available:
                    self.available.remove(color)
                    withheld.append(color)

        # "Commit required-color dice. Every colored dot beside an element
        # requires one available die of that color to be placed on that
        # element now. These dice are locked there." Red can never satisfy a
        # dot, and nor can a withheld die - it is not available, which is
        # exactly what "not even for a required color" means.
        locked = [[] for _ in targets]
        if REQUIRED_COLORS:
            REQ_TRIED[0] += 1
            dots = PROGRAM_REQS[deck][pid]
            missing = False
            for i, color in enumerate(dots[:len(targets)]):
                if not color:
                    continue
                if color in self.available:
                    self.available.remove(color)
                    locked[i].append(color)
                else:
                    missing = True
                    break
            if missing:
                # "Do not execute the Program. Lose 1 Health. Return any
                # withheld dice, discard the Limitation, and treat the
                # Program as failed for Stable/Overheated progression."
                for held in locked:
                    self.available += held
                self.available += withheld
                self.hp -= 1
                self.completed += 1
                REQ_SHORT[0] += 1
                return 1        # one failure: flips Stable, no Catastrophic

        if self.tech == "optimize" and targets:
            worst = max(range(len(targets)), key=lambda i: targets[i])
            if targets[worst] > 1:
                targets = list(targets)
                targets[worst] -= 1
        dumping = allow_dump and (
            ALLOC_MODE == "dump"
            or (ALLOC_MODE == "dump_hard" and deck in DUMP_DECKS))
        if dumping:
            plan = self.dump_allocate(targets, locked)
        elif ALLOC_MODE in ("sacrifice", "sacrifice_short"):
            # Triage is a legal way to play a Program, not a way of ducking
            # it, so it is NOT gated on allow_dump.
            plan = self.sacrifice_allocate(targets, locked)
        else:
            plan = self.allocate(targets, locked)
        # The required dice were taken out of `available` so no allocator
        # could spend them twice. Put them back now the plan is fixed: the
        # resolution loop below removes every die in the plan from
        # `available`, and these are in the plan, so leaving them out here
        # would charge for each of them twice over.
        for held in locked:
            self.available += held
        rerolls = max(0, self.str_ - 1)
        failed = 0
        misses_on_failed = 0   # misses available to negate a Catastrophic
        leaked = 0
        recovery = max(0, self.rec + RECOVERY_DELTA)   # plus the Optimal bonus
        used_debug = used_optimize = False
        carry = 0              # link: a surplus success held for a later element
        link_spent = cache_spent = analyse_spent = False
        # Reconfigure: up to 2 dice move from an element that is over its
        # Target to one the pool left short of its Target.
        if self.tech == "architect":
            moved = 0
            while moved < 2:
                short = [i for i, t in enumerate(targets) if len(plan[i]) < t]
                rich = [i for i, t in enumerate(targets) if len(plan[i]) > t]
                if not short or not rich:
                    break
                give = max(rich, key=lambda i: len(plan[i]) - targets[i])
                take = min(short, key=lambda i: len(plan[i]) - targets[i])
                plan[take].append(plan[give].pop())
                moved += 1
        seen = []              # per element: (dice, Target, total, crit, miss)
        for i, t in enumerate(targets):
            dice = plan[i]
            for c in dice:
                if c in self.available:
                    self.available.remove(c)
            values = self.element_values(i, dice)
            total = sum(values)
            # link: spend a success banked from an element that overshot.
            if self.tech in ("link","link2") and carry and total < t:
                total += carry
                carry = 0
            # analyse: throw the whole element again and keep the better run.
            if ((self.tech == "analyse" or (self.tech == "analyse_last" and i == len(targets)-1)) and not analyse_spent and total < t):
                analyse_spent = True
                again = self.element_values(i, dice)
                if sum(again) > total:
                    values, total = again, sum(again)
            used_reroll = False
            if total < t and rerolls > 0:  # spend an extra STR roll
                rerolls -= 1
                used_reroll = True
                if REROLL_MODE == "element" and self.tech != "compiler":
                    # The printed AoS rule: pick the element up and throw all
                    # of it. The new result stands even if it is worse. The
                    # Compiler is the exception and keeps what landed.
                    values = self.element_values(i, dice)
                    total = sum(values)
                elif PUSH_REROLL or self.tech == "compiler":
                    # One roll: the dice are chosen before any is thrown.
                    again = [k for k, v in enumerate(values) if v == 0]
                    hits = [k for k, v in enumerate(values) if v == 1]
                    # A thrown die comes back as at most a Crit, so each one
                    # in the cup raises the ceiling by 2 less what it scored.
                    ceiling = total + sum(2 - values[k] for k in again)
                    if ceiling < t:
                        # The misses alone cannot reach the Target. Trading a
                        # basic hit is the only way left to find a Crit, but
                        # only if trading enough of them actually gets there.
                        for k in hits:
                            again.append(k)
                            ceiling += 1
                            if ceiling >= t:
                                break
                        else:
                            again = [k for k in again if values[k] == 0]
                    fresh = self.element_values(i, [dice[k] for k in again])
                    values = list(values)
                    for pos, k in enumerate(again):
                        values[k] = fresh[pos]
                    total = sum(values)
                else:
                    total = self.element_total(i, dice)
            # Debug: once per Program, after missing by exactly 1, reroll one die.
            if (self.tech == "debugger" and not used_debug and total == t - 1):
                misses = [c for c, v in zip(dice, values) if v == 0]
                if misses:
                    used_debug = True
                    total += sum(self.element_values(i, misses[:1]))
            miss = total < t
            seen.append((len(dice), t, total,
                         any(v >= 2 for v in values), miss))
            if FIRINGS is not None:
                safe_n = t + (2 if i in getattr(self, "wide", set()) else 1)
                FIRINGS["elements"] += 1
                if miss:
                    FIRINGS["fail (burn all)"] += 1
                else:
                    if used_reroll:
                        FIRINGS["used an extra roll"] += 1
                        if total == t:
                            FIRINGS["extra roll AND exactly on Target"] += 1
                    if total == t:
                        FIRINGS["exactly on Target (Optimal, +2)"] += 1
                    elif total == t + 1:
                        FIRINGS["beat by exactly 1 (no penalty)"] += 1
                    else:
                        FIRINGS["beat by 2+ (burn 1)"] += 1
                    if len(dice) > safe_n:
                        FIRINGS["allocated past Target+1"] += 1
                        if total >= t + 2:
                            FIRINGS["  both over-rules at once"] += 1
            if miss:
                failed += 1
                misses_on_failed += values.count(0)
            if used_reroll or miss:
                self.exhausted += dice          # the whole Element exhausts
            else:
                # Allocation is capped, so there is never an excess to burn;
                # only overshooting the Target itself costs a die.
                excess = 0
                over = max(0, total - (t + 1))     # points past the safe band
                overkill = over if OVERKILL_SCALE else (1 if over else 0)
                if excess or overkill:
                    leaked += 1                 # this element over-allocated
                burn = min(len(dice), excess + overkill + ELEMENT_COST)
                # allocate() hands these out strongest-first, so dice[:burn]
                # used to burn the BEST dice on the element. A player gives up
                # the worst.
                order = sorted(dice, key=lambda c: EV[c])
                self.exhausted += order[:burn]
                self.available += order[burn:]  # the rest come straight back
                # link: bank one success from an element that cleared with room.
                if self.tech in ("link","link2") and not link_spent and total >= t + (2 if self.tech=="link2" else 1):
                    link_spent = True
                    carry = 1
                # cache: the first element to resolve gives its dice straight
                # back instead of exhausting any of them.
                if self.tech == "cache" and not cache_spent:
                    cache_spent = True
                    self.available += self.exhausted[-burn:] if burn else []
                    if burn:
                        del self.exhausted[-burn:]
                if total == t:                  # Optimal Implementation
                    recovery += OPTIMAL_BONUS
                elif (self.tech == "optimizer" and not used_optimize
                      and total == t + 1):
                    used_optimize = True        # Optimize: Target + 1 counts
                    recovery += OPTIMAL_BONUS

        # Which Backdoor Routines this Program could have been claimed off.
        # Measured before Root Access negates anything, so "without failing
        # an element" means the element really held.
        if seen:
            if all(n <= t2 for n, t2, _tot, _c, _m in seen):
                self.met.add("Diagnostic Port")
            if face == "back" and not failed:
                self.met.add("Privilege Escalation")
            if sum(n for n, _t, _tot, _c, _m in seen) <= sum(targets) + 1:
                self.met.add("Resource Fork")
            if sum(1 for _n, _t, _tot, c, _m in seen if c) >= 2:
                self.met.add("Packet Sniffer")
            if len(self.exhausted) >= 4:
                self.met.add("Garbage Collection")
            if sum(1 for _n, t2, tot, _c, _m in seen if tot == t2) >= 2:
                self.met.add("Root Access")

        # Root Access: treat one failed element as successful. Spent to save a
        # Program from Catastrophic Failure, which is the only thing that costs
        # Health.
        if failed >= 2 and self.backdoors > 0 and self.spend_backdoor():
            self.backdoors -= 1
            failed -= 1

        self.available += withheld
        if self.intf == "memory_leak":
            for _ in range(min(leaked, len(self.available))):
                # The weakest die, not the last in the list - which was Red.
                worst = min(self.available, key=lambda c: EV[c])
                self.available.remove(worst)
                self.exhausted.append(worst)
        if RECOVERY_ON_CLEAN and failed:
            # The flat REC refill is what keeps the pool in equilibrium; gate
            # it on a clean Program and a bad one leaves you short for the
            # next, which is how scarcity compounds instead of just biting.
            recovery = max(0, recovery - self.rec)
        for _ in range(min(recovery, len(self.exhausted))):
            self.available.append(self.exhausted.pop())
        if failed >= 2:
            if NEGATE_STATS is not None:
                NEGATE_STATS[min(misses_on_failed, 9)] += 1
            if (MISSES_TO_NEGATE
                    and misses_on_failed >= MISSES_TO_NEGATE):
                NEG_WANTED[0] += 1
            if (MISSES_TO_NEGATE
                    and misses_on_failed >= MISSES_TO_NEGATE
                    and self.negates_left != 0):
                misses_on_failed -= MISSES_TO_NEGATE
                if self.negates_left > 0:
                    self.negates_left -= 1
                NEG_USED[0] += 1
                if SAVES is not None:
                    SAVES[-1] += 1
            else:
                self.hp -= 1
        elif failed == 0 and deck in PROGRAM_REWARDS:
            # The fork: bank a Backdoor Routine instead of taking the reward.
            if (self.worked < CLAIM_INSTEAD
                    and self.worked < BACKDOOR_CLAIMS):
                self.worked += 1
            else:
                self.reward(PROGRAM_REWARDS[deck][pid], slot)
        self.completed += 1
        return failed

    def spend_backdoor(self):
        """Root Access is about to save 1 Health. Is it worth a Routine?"""
        if BACKDOOR_POLICY == "hoard":
            return False
        if BACKDOOR_POLICY == "last":
            return self.hp <= 1        # the Health loss would end the game
        return True

    def retire(self, pid):
        """The card leaves the deck for good, shortening later cycles."""
        if pid is None:
            return
        self.programs[pid]["status"] = "removed"
        self.queue = [q for q in self.queue if q != pid]

    def reward(self, kind, pid=None):
        if kind == "hp":
            self.hp = min(6, self.hp + 1)
        elif kind == "rec":
            # "+1 REC; remove this Program - the bonus is permanent and the
            # card leaves the deck", which also shortens every later cycle.
            self.rec += 1
            self.retire(pid)
        elif kind == "str":
            self.str_ += 1
            self.retire(pid)
        elif kind == "recover":
            for _ in range(min(3, len(self.exhausted))):
                self.available.append(self.exhausted.pop())
        elif kind == "unheat":
            for p in self.programs:
                if p["status"] == "overheated":
                    p["status"] = "stable"
                    break

    def play(self):
        guard = 0
        while self.hp > 0 and guard < 200:
            guard += 1
            if not self.queue:
                active = [p for p in self.programs
                          if p["status"] not in ("aside", "removed")]
                if self.cycle < 3 and active:
                    self.cycle += 1
                    self.negates_left = NEGATES_PER_CYCLE or -1
                    self.queue = [p["id"] for p in active]
                    self.rng.shuffle(self.queue)
                else:
                    break  # into Advanced Programming
            pid = self.queue.pop(0)
            prog = self.programs[pid]
            face = "back" if prog["status"] == "overheated" else "front"
            failed = self.run_program(prog["deck"], prog["pid"], face,
                                      slot=pid)
            retry = False
            if failed < 0:
                # A declared abandon. Under RETRY_IMMEDIATE it buys nothing
                # either: the card heats up and comes back at once.
                if RETRY_IMMEDIATE:
                    prog["status"] = "overheated"
                    retry = True
                else:
                    prog["status"] = "aside"
            elif failed > 0:
                if failed >= 2 and CF_SETS_ASIDE:
                    # Catastrophic: retired on the spot, Stable or not.
                    prog["status"] = "aside"
                elif prog["status"] == "stable":
                    prog["status"] = "overheated"
                    retry = RETRY_IMMEDIATE
                elif self.intf == "all_overheated":
                    # "cycle it to the bottom of its deck instead of setting
                    # it aside" - the Program keeps coming back.
                    self.queue.append(pid)
                else:
                    prog["status"] = "aside"
            if retry and self.hp > 0:
                # Straight back at you, on the harder face, and this time it
                # has to be played. Fail it again and it is set aside, as a
                # second failure always has.
                again = self.run_program(prog["deck"], prog["pid"], "back",
                                         slot=pid, allow_dump=False)
                if again > 0:
                    prog["status"] = "aside"
        if self.hp <= 0:
            return False
        # "Select 3 Advanced Programs." Eight are shuffled and set aside at
        # setup, but only three are ever faced - running all eight made the
        # finale nearly three times as long as the rules call for.
        adv = self.rng.sample(range(8), 3)
        # Advanced Programming is its own stretch, so it gets its own
        # allowance rather than inheriting whatever the third cycle left.
        self.negates_left = NEGATES_PER_CYCLE or -1
        overheated = False
        for pid in adv:
            if self.hp <= 0:
                return False
            failed = self.run_program("Advanced", pid, "back" if overheated else "front")
            overheated = failed >= 2
            self.advanced_done += 1
        return self.hp > 0


def run(deck="Standard", games=20000, seed=20, tier="none", tech=None):
    """`deck` names a difficulty level, or one of the three decks to run whole."""
    rng = random.Random(seed)
    composition = LEVELS.get(deck)
    source = deck if composition is None else "Specialized"
    wins = 0
    for _ in range(games):
        if Game(source, rng, tier, composition=composition, tech=tech).play():
            wins += 1
    return wins / float(games)


if __name__ == "__main__":
    print("%-14s %8s %8s %8s %8s" % ("deck", "none", "I", "II", "III"))
    for d in DECKS:
        row = ["%7.1f%%" % (100 * run(d, 4000, tier=t))
               for t in ("none", "I", "II", "III")]
        print("%-14s %s" % (d, " ".join(row)))
