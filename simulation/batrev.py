# -*- coding: utf-8 -*-
"""Revised standalone Build-a-Tyrant: the scavenged-Tyrant redesign.

    python3 batrev.py one           # one complete seeded playthrough, named cards
    python3 batrev.py batch [n]     # seeded batch at all four difficulties
    python3 batrev.py assumptions   # the ruling log alone
    python3 batrev.py diagnose      # WHY each forced pass happened
    python3 batrev.py ladder        # the first proposal's 10/12/14/16
    python3 batrev.py graft         # reveal 1 graft vs 2
    python3 batrev.py attrition     # is running out of grafts the loss?
    python3 batrev.py directed      # R22, directing the attack, priced
    python3 batrev.py weak          # R22 vs R23 vs R24 for weak builds
    python3 batrev.py lab           # win rate by how well the lab went
    python3 batrev.py shape         # R25/R26, lowering the ceiling only
    python3 batrev.py hp            # pooled Rat Health, tuned

THIS IS NOT bat.py. bat.py models the PRINTED game and its figures are
calibrated; nothing here touches it. Card data is imported from it, because
those tables are the ones check_app_sync.py holds against
generator/build_bat.py.

PREMISE. The four Lab Rats scavenge an abandoned Tyrant that failed because
it could not be controlled, and build a Prototyrant they can direct. Each
Experiment gives the Prototyrant one part and the old Tyrant reclaims the
other. Eventually the old Tyrant wakes up.

WHAT THE REVISION CHANGES, STRUCTURALLY
  * EVERY Experiment grafts a part and reclaims a part, win or lose. Success
    only decides WHO CHOOSES. That makes the lab phase's stake "which parts"
    rather than "how many", which is the point of the redesign.
  * The clock is the Experiment deck, not the Splice count. Six dealt cards
    then a three-card packet holding the Wake-Up gives 6, 7 or 8 resolved
    Experiments at equal odds.
  * The old Tyrant's wall is its STARTING PARTS MINUS THE GRAFTS, so its size
    is set by difficulty and its composition by how the lab went.
  * In the battle a graft's Value CAPS the dice the Rats may commit and a
    Splice's Value is the damage Target. So losing an Experiment hands the
    Rats a smaller cap and the Tyrant a higher threshold - one roll, two
    penalties.

CARD SOURCE. generator/build_bat.py, via bat.py's transcribed tables. The
Experiment numbers there are ALREADY 3/4/5, matching the November 12
print-and-play; the "older generator has 2/3/4" warning in the handoff does
not apply to this tree, so there is nothing to reconcile.

-----------------------------------------------------------------------
THE CONFIGURATION THESE FIGURES ARE MEASURED THROUGH
-----------------------------------------------------------------------

    Experiment phase   dice stay PER-RAT; Red held by one Rat, set aside
                       after use, handed to a non-active Rat. Unchanged.
    Battle             dice POOLED; one PROTOTYRANT Health track
                       (SHARED_HP_START 12); an active Rat chosen every
                       round; Red on its own Experiment-phase rule, not
                       drawn from the pool, but EXHAUSTING when committed
                       rather than set aside (R21).
    PARTS_AT_SETUP is now 12/13/14/15, not the handoff's 10/14/18/22, and
    GRAFT_REVEAL is 2, not the handoff's 1. Both are measured below.

THE LADDER AS IT SHIPS, 2000 games a rung, Proto HP 12, decks 12/13/14/15:

                    Easy  Standard   Hard  Nobulous
    GRAFT_REVEAL 1  64.7%    48.9%   36.5%    22.8%
    GRAFT_REVEAL 2  64.2%    52.8%   37.9%    25.1%
    BAT, printed    60%      52%     39%      27%

Reveal 2 is the closer fit and lands Standard and Hard almost exactly;
Easy runs four points generous and Nobulous two light. Walls are 5/6/7/8
Splices against 7.0 grafts, so the Prototyrant outnumbers what is left of
the old Tyrant on every rung - the lab is now the bigger half of the game.

How the deck size was found, HP swept against it on the Standard rung,
1500 games an arm, GRAFT_REVEAL 2:

    Proto HP   deck 11  deck 12  deck 13  deck 14  deck 15  deck 16
       9         73.9%    63.1%    48.7%    37.7%    25.8%    15.9%
      12         74.7%    63.4%    53.0%    38.8%    29.6%    19.5%
      15         75.2%    66.4%    51.2%    39.7%    29.8%    21.3%
      18         77.1%    64.3%    52.5%    39.5%    30.1%    19.9%

HP saturates by 12: Health sets the LEVEL, the deck builds the LADDER at
10-14 points a Splice. Read that sweep as DECK SIZE ONLY - it moves the
Standard rung's deck and leaves its Specimen pool at 6, so it understates
the real upper rungs, which carry 7 and 8 Specimens and therefore higher
Splice VALUES. The sweep says 29.6% for a 15-card deck; the Nobulous rung,
with its own mix, measures 25.1%. The four-rung batch is the authority.

-----------------------------------------------------------------------
WHAT ACTUALLY DECIDES THE BATTLE: GRAFT ATTRITION, NOT HEALTH
-----------------------------------------------------------------------

A destroyed graft leaves the Prototyrant for good (R15), so its seven
parts are spent at about one a round against a battle that runs twelve.
Run `batrev.py attrition`; 2000 games a rung, decks 12/13/14/15:

    rung        win%   naked%  atRound  win|naked  win|clad  rounds
    Easy       65.5%    37.0%     11.9       6.8%     99.8%   10.55
    Standard   52.7%    49.6%     12.3       5.1%     99.6%   12.16
    Hard       37.8%    63.7%     12.8       3.3%     98.3%   13.67
    Nobulous   24.9%    76.6%     13.5       2.8%     97.2%   14.66

RUNNING OUT OF GRAFTS IS THE LOSS CONDITION. A game that keeps one graft
to the end wins 97-100% of the time; a game that runs out wins 3-7%. The
whole ladder is the naked% column read backwards, and the Rats' Health is
a two-round epilogue once the last graft dies - which is exactly why the
HP dial saturated: Health is not what they are spending.

The experience that falls out of it is the one the brief asked for. The
question at Wake-Up is not "can I out-damage it" but "have I got enough
parts to outlast its wall", and the card that kills you is whichever
Specimen a failed Experiment handed over - in the seeded playthrough, a
Value-5 Splice that stood for eight rounds and was still standing when
the grafts ran out. The lab phase is where that is decided.

It also says where the remaining dials are. Graft COUNT is the lab's
length; graft SURVIVAL is its thresholds against the Tyrant's attack
sizes; and whether a destroyed graft can ever be recovered is an open
rules question, not a tuning one. The Health track's value was removing
the dice spiral, not being a resource.

-----------------------------------------------------------------------
WHERE THE FIRST ROUND OF TUNING LANDED
-----------------------------------------------------------------------

The forced passes were never the graft cap. Logging a cause for each one
gives colour 0.0%, cap 8.4%, pool 91.6% - they would still be forced with
no cap and no colour rule at all. The Rats fight with 3.69 available dice
against a Splice Target averaging 3.74 needed in ONE blow, and 2.62 dice a
round sit banished behind knocked-out Rats. Health and the dice pool were
the same resource, so a knockout cost four dice and bought the next one.

One Prototyrant Health track fixes it: banished dice 2.54 -> 0.02,
available 3.38 -> 4.68, rounds opening with nothing to roll 24% -> 18%,
forced passes 3.04 -> 1.85. At equal total Health it is roughly a wash on
win rate - pooling also recovers the overkill a per-Rat track wastes - so
the gain is in restored agency, not in survivability.

RED WAS MISSING FROM THE BATTLE ENTIRELY, against the handoff's "Red
counts toward the cap": all_dice() returned only each Rat's four personal
dice, so Red worked all through the lab and vanished at Wake-Up. What it
is worth depends entirely on whether it comes back by itself. Standard,
Proto HP 12, GRAFT_REVEAL 2, 2500 games an arm:

    arm                       deck 12  deck 13  deck 14  deck 15  deck 16
    Red set aside               68.0%    59.0%    44.8%    35.0%    23.8%
    Red exhausts (default)      63.0%    51.9%    39.8%    29.1%    19.5%
    Red absent                  60.7%    48.2%    35.6%    24.2%    17.7%

SET ASIDE, Red is worth about one whole Splice (+9.2 at deck 14) because
it is then the one die that never runs out: usable in 100% of rounds, and
forced passes fall 2.65 -> 1.63. EXHAUSTING, it is worth +4.2, usable in
67% of rounds and committed in 29% - a die with real downtime, which is
the point of the change. Folded into the shared pool instead of keeping
its own rule it was worth only +4.1, and for a worse reason: the pool can
spend it on any round, so no decision attaches to it.

NOTE FOR THE DESIGNER: the active-Rat choice is free and the sort prefers
whoever holds Red, so the HOLDER is activated every round regardless. The
handover rule therefore restricts nothing by itself - under the set-aside
reading Red was simply always in play. It is exhaustion, not the handover,
that gives Red downtime: the third of rounds it is unusable are rounds it
sits in the exhausted pool waiting for a recovery, and a recovery spent
getting Red back is a real choice against the dice it could have bought.
The handover still matters to the Experiment phase, where it stops one Rat
working every Experiment.

WHERE THE FORCED PASSES ENDED UP, deck 13, Proto HP 12, GRAFT_REVEAL 2:
    passes 5.72/game, forced 1.99, voluntary 3.73
    forced = 34.8% of passes and 16.3% of all rounds (from 44.2% / 21.5%)
    cause: colour 0.0%, cap 12.5%, pool 87.5%
    deck 14 reads 6.38 / 2.35 / 4.03 and 36.9% / 17.5%, same causes
17% of rounds still open with no available dice, so the pool is still the
binding constraint - but it is now a reason to pass, not a round with no
move in it. An exhausting Red costs 0.7 forced passes a game against the
set-aside reading: that is the price of giving it downtime.

The HP dial SATURATES near 9: deck 12 reads 51.7 / 55.6 / 58.6 / 60.7 at
HP 6/7/8/9 and then only 59.9 / 60.5 / 61.4 at 10/11/12. Above 9 the Rats'
problem is no longer survival, so Health sets the LEVEL and cannot build
the ladder. The ladder has to come from the deck, where one Splice is worth
13-15 points.

    pooled HP 12, starting decks 12/13/14/15, two grafts revealed:
        no Red at all:      62.1% / 48.5% / 38.3% / 26.8%
        Red, exhausting:    63.4% / 53.0% / 38.8% / 29.6%
    BAT's printed ladder, for comparison:
        60%   / 52%   / 39%   / 27%

An exhausting Red is worth about four points, which the SAME deck sizes
absorb - the set-aside reading was worth nine and moved every rung a whole
deck. Standard and Hard land on the printed ladder; Easy and Nobulous run
a few points generous, and the Specimen mix - held at 6 throughout these
sweeps - is the fine dial for that, since it moves Splice VALUES while the
deck size moves COUNTS. The first proposal moved both together, which
charged every rung twice.

-----------------------------------------------------------------------
RULINGS. Every one of these is a choice this module made, not printed text.
-----------------------------------------------------------------------

SETUP AND CLOCK
  R1  Tyrant's starting parts are sampled from 16 regular Upgrades plus
      5/6/7/8 randomly chosen Specimens (Easy..Nobulous), then the deck size
      10/14/18/22 is drawn from that pool. Reported as the regular/Specimen
      mix per difficulty.
  R2  Target = (combined Value of the two revealed parts) - (printed
      Experiment number), floored at 1. The old blanket Specimen surcharge is
      replaced by this, not stacked with it.
  R3  Cards that DISCARD or REPLACE Experiments (Performance Trial,
      Load-Bearing Trial's redraw, Controlled Failure) draw from the twelve
      Experiments not dealt, so the resolved-Experiment window stays 6-8 and
      the Wake-Up packet is never touched. Without this the clock moves and
      the window the handoff asks to preserve is lost.
  R4  The Tyrant's discard reshuffles into its deck on demand. If one card
      remains it is drawn first, then the discard is reshuffled for the
      second - so a part never fails to be revealed.

PART ASSIGNMENT
  R5  Success: the Rats choose the graft; the old Tyrant reclaims the other.
      Failure or a zero-dice pass: the old Tyrant takes the HIGHER-Value
      part, the Prototyrant gets the other. Ties go to the player.
  R6  Structural Stress Trial reveals a third part. The TARGET uses the two
      highest Values. On resolution one part is grafted, the old Tyrant
      reclaims the highest of the rest, and the leftover goes to the Tyrant's
      discard - so conservation holds (starting parts = wall + grafts).
  R7  Rapid Response Trial with no Green discards the stronger part before
      the Target is computed, so the Target is the single remaining part's
      Value minus the Experiment number. The discard is the Tyrant's.
  R8  Methodological Optimization: Target to 0, and the Prototyrant takes the
      WEAKER part while the Tyrant reclaims the stronger. That is the price.
  R9  Field Retrofit Trial swaps one of the PROTOTYRANT's grafts (no Rat owns
      parts any more) with a revealed part; Specimens cannot be swapped; the
      displaced graft goes to the Tyrant's discard.

LEGACY OWNERSHIP
  R10 The borrow restriction keyed to "Upgrades held by the active Rat" now
      reads the PROTOTYRANT's graft count, which is shared. The escalation
      shape is preserved; the per-Rat distinction cannot be.
  R11 Mottle's Specimen Adaptation counts the Prototyrant's Specimens.
      Experimental Subject needs only a Specimen REVEALED and is unchanged.
  R12 Degraded Tissue Study's "reduce the Prototyrant's Health dial by 2" is
      a DOCUMENTED OMISSION: the revision has no Health dial. The card
      resolves as a plain Experiment number 5.

BATTLE
  R13 The Tyrant's six-die bag (2 Purple, 2 Blue, 1 Green, 1 Yellow) is
      carved out of the Rats' 16 before the shared pool is built, as the
      printed game does - the box holds 17 dice. Shortages substitute the
      next-strongest colour available.
  R14 Opening transition: available dice stay available, exhausted stay
      exhausted, then recover OPENING_RECOVERY (2) dice.
  R15 A revealed graft DEFENDS the incoming attack whether or not it breaks:
      it is discarded when the attack meets or exceeds its Value and survives
      otherwise. A Rat's Health is only reached when no graft is revealed, or
      by damage a card says cannot be absorbed.
  R16 Predatory Instinct targeted "the Rat holding the greatest total Upgrade
      Value", which no Rat now does. It targets the Rat with the most
      AVAILABLE dice - the nearest reading of "your finest work has attracted
      professional interest". Ties to the player.
  R17 Unstable Growth's second attack arrives with no fresh reveal, so if the
      first destroyed the exposed graft the second lands on the Rat.
  R18 Crushing Blow's 1 unabsorbable damage reaches the Rat past a graft; the
      remainder is put against the graft threshold as usual.
  R19 Banishment on breaking a Splice is OFF for the main run, per the
      handoff. BANISH_ON_BREAK turns it on.
  R20 A destroyed Splice still sets the counterattack's dice count, and its
      printed effect does NOT fire. A recovery pass still pays out when the
      graft survives.
  R23 PARTIAL DAMAGE (PARTIAL_DAMAGE, off). A blow that falls short stays
      on the exposed Splice and the Rats need only the remainder next time.
      The handoff says no partial damage, so this contradicts it on
      purpose. The retaliation still reads the Splice's printed Value.
  R24 SPEND THE GRAFT (SPEND_GRAFT, off). The active Rat may destroy the
      exposed graft to add its Value to the blow, closing a gap the dice
      could not. The part is gone for good and cannot defend that round's
      retaliation, so it is attrition the Rats choose rather than suffer.
  R25 CAP FLOOR (CAP_FLOOR, off). The dice cap is max(graft Value, floor),
      so a Value-2 graft stops meaning a two-dice round.
  R26 FLAT RETALIATION (SPLICE_ATTACK_DICE, off). The Tyrant rolls a fixed
      number of dice instead of the exposed Splice's Value, so a high-Value
      Splice is a harder TARGET without also being a bigger HITTER.

      R25 and R26 exist because a part's Value does THREE jobs at once -
      the Rats' dice cap, the Target they must meet in one blow, and the
      Tyrant's attack dice - so one lost Experiment charges them three
      times. Both dials are worth most to the weakest build.
  R22 DIRECT THE ATTACK. Before rolling, with a graft exposed, the active
      Rat may forgo that graft's ability and commit up to DIRECT_CAP (4)
      dice whatever the graft's Value, setting aside DIRECT_COST (1) further
      available die. The graft stays exposed and defends at its printed
      Value, with its soak text forgone. The tied-up die reaches the
      exhausted pool after this round's recovery, so only a later recovery
      pass reclaims it; attacks pay no recovery here, so that ordering is
      only future-proofing. Because the ability is forgone the hand is
      scored with no graft at all, which also frees Red from the printed
      either/or. A round that PASSES directs nothing: nothing is forgone
      and no die is tied up. DIRECT_ATTACK turns the whole rule off.
  R21 Red works in the battle as it does in the Experiment phase - only the
      active Rat commits it, only while that Rat holds it, it counts toward
      the graft's dice cap, and it then moves to a non-active Rat - with ONE
      difference: in the battle it EXHAUSTS rather than being set aside, so
      it has to be recovered like any other die. It is still never drawn
      from the shared pool, and shared_exhausted() reaches it so a recovery
      can return it. RED_SET_ASIDE_IN_BATTLE restores the lab reading.

OMITTED CARD TEXT, declared rather than quietly dropped
  * Per-card battle effects for grafts and Splices beyond the flat damage
    and damage-reduction table in GRAFT_DAMAGE / SPLICE_DAMAGE. The
    conditional ones (colour-contingent damage, reroll and recovery riders,
    "remove a success from the opponent's next attack") are not modelled.
  * Diagnostic Trial's look at the next Experiment: the policy has no
    lookahead to spend it on, as in bat.py.
  * Containment Failure's optional Target reduction is declined always.
  * Baseline Calibration's side flip: all Rats use Side A and the flip is a
    no-op. Side B abilities are therefore unmodelled.
  * Rat abilities modelled: Jury-Rig, Self-Sufficient, Prepared,
    Experimental Subject, Specimen Adaptation (per R11), Careful Borrower.
"""
import collections
import random
import sys

from dice import COLORS, EV, FACES, roll
import bat
from bat import (EXPERIMENT_TARGETS, EXPERIMENT_EFFECT, UPGRADE_VALUES,
                 UPGRADE_NAMES, UPGRADE_CATS, SPECIMEN_NAMES, SPECIMEN_CATS,
                 SPECIMEN_VALUE, RAT_HP, RAT_REC, pick_order)

# ---------------------------------------------------------------- dials
# PARTS_AT_SETUP is the old Tyrant's starting deck, and the ladder's coarse
# dial: one Splice on the wall is worth 10-14 points. The handoff proposed
# 10/14/18/22, which is a cliff - 84 / 39 / 6 / 0 measured. 12/13/14/15 is
# what the sweeps landed on, because the Rats' capacity to BREAK Splices is
# near constant (4.7 a game) while the spec scaled the requirement 2 -> 15.
PARTS_AT_SETUP = {"Easy": 12, "Standard": 13, "Hard": 14, "Nobulous": 15}
SPECIMENS_IN_POOL = {"Easy": 5, "Standard": 6, "Hard": 7, "Nobulous": 8}
LEVELS = ("Easy", "Standard", "Hard", "Nobulous")

EXPERIMENTS_DEALT = 8      # six, then a three-card packet with the Wake-Up
WAKEUP_PACKET = 3
TARGET_FLOOR = 1
STR_PHASES = 2
OPENING_RECOVERY = 2       # dice recovered once at the transition
PASS_RECOVERY_BONUS = 2    # a recovery pass pays REC + 2
NO_GRAFT_CAP = 3           # dice cap with no graft revealed

# R22: DIRECT THE ATTACK. Without it the exposed graft's Value is a hard
# ceiling on the Rats' OWN dice, so a Value-2 graft against a Value-5
# Splice is not a decision, it is a lost round - and attrition() shows
# running out of grafts is the loss condition. Directing lets the active
# Rat forgo the graft's ability and commit up to DIRECT_CAP dice whatever
# the graft's Value, paying DIRECT_COST available dice that are tied up
# until a later recovery. The graft stays exposed and defends at its
# printed Value, so a fragile graft is being risked to force a break.
# DIRECT_MARGIN is the expected damage the directed route must BEAT the
# graft route by: 0.0 makes the policy greedy, which is the harshest test
# of whether the price is too low.
# Measured OFF: rescue 0.09 a round against luxury 1.08, and a point of win
# rate lost. R22 raises the dice CAP, and only 12% of forced passes are
# cap-caused. `batrev.py directed` reproduces that.
DIRECT_ATTACK = False
DIRECT_CAP = 4
DIRECT_COST = 1
DIRECT_MARGIN = 0.0

# TWO MORE WAYS A WEAK BUILD MIGHT GET THROUGH, both OFF by default and
# both aimed at the constraint R22 turns out to miss. R22 raises the DICE
# CAP, but only 12% of forced passes are cap-caused; 88% are the pool.
#
# PARTIAL_DAMAGE (R23) lets a blow that falls short stay on the exposed
# Splice, so several small blows can do what the Rats cannot do in one.
# That is what a weak build produces. The handoff says no partial damage,
# so this contradicts it on purpose and stays off until chosen.
#
# SPEND_GRAFT (R24) lets the active Rat destroy the exposed graft to add
# its Value to the blow, taking the retaliation bare. It hands graft
# attrition - which attrition() shows IS the loss condition - to the Rats
# as something they spend on purpose rather than something done to them.
PARTIAL_DAMAGE = False
SPEND_GRAFT = False

# TWO DIALS THAT LIFT THE FLOOR WITHOUT LIFTING THE CEILING. A part's Value
# currently does THREE jobs at once, and losing one Experiment charges the
# Rats for all three: the part they keep caps their dice, the part the old
# Tyrant takes sets the Target they must meet in one blow, AND sets how many
# dice it rolls back at them. These unhook the first and the third, so they
# are worth something to a Value-2 graft and nothing to a Value-5 one -
# which is what makes them compress the spread rather than raise it.
#
# CAP_FLOOR (R25): the dice cap is max(graft Value, CAP_FLOOR). 0 is off.
# SPLICE_ATTACK_DICE (R26): the Tyrant rolls this many dice instead of the
# exposed Splice's Value, so a high-Value Splice is a harder TARGET without
# also being a bigger HITTER. 0 is off.
CAP_FLOOR = 0
SPLICE_ATTACK_DICE = 0
BANISH_ON_BREAK = False    # R19: off for the main run
TYRANT_BAG = ["purple", "purple", "blue", "blue", "green", "yellow"]
ROUND_GUARD = 300          # genuine stalls are reported, not won or lost
COMMIT_MARGIN = 0.0        # extra expected damage the policy wants

# How many of the Prototyrant's grafts are revealed each battle round. 1 is
# the handoff's rule. 2 reveals two, uses and exposes one and sets the other
# aside until the pile reshuffles - so the card held back cannot be destroyed
# that round. 2 is the default because it is the closer fit to BAT's printed
# ladder (64/53/38/25 against 60/52/39/27, where 1 reads 65/49/37/23) and
# because it is the round's only real decision: which graft to spend and
# which to protect. Set it to 1 for the handoff's rule.
GRAFT_REVEAL = 2

# THE RATS' HEALTH, POOLED. In the battle the dice are already a shared pool,
# but Health is still per-Rat - so a knockout costs four dice as well as a
# Rat, and that is what turns one knockout into the next. 2.62 dice a round
# are sitting banished behind downed Rats, against 3.69 available.
# SHARED_HP pools Health the way the dice already pool: damage comes off one
# track, nobody goes down until it is empty, and every die stays in the pool
# for the whole battle. The printed total is sum(RAT_HP) = 6, so 6 is the
# neutral setting and the dial is what the simulation tunes.
# Note this makes the retargeting Attack cards - Adaptive Strike, Predatory
# Instinct - cosmetic, since all damage lands on the same track.
# JON, 2026-11-19: "Keep the separate dice pools during the experiment
# phase, but pool the dice and the hp during the battle... think of it as the
# base HP for the prototyrant." So this is not pooled RAT Health - it is the
# PROTOTYRANT's Health track, and the Rats ride it. The Experiment phase is
# untouched either way: nothing there damages Health, and lab dice stay
# per-Rat through self.available(rat).
# False restores the handoff's per-Rat 1/1/2/2 and every figure measured
# before this. 12 is where the sweep landed; the printed total is 6, and
# pooling also recovers the overkill a per-Rat track wastes.
SHARED_HP = True
SHARED_HP_START = 12

# RED IN THE BATTLE, WORKED AS IN THE EXPERIMENT PHASE. The handoff says
# "Red counts toward the cap", but
# Rats' four personal dice were the only thing all_dice() returned, so Red
# was used all through the lab and then vanished at Wake-Up. It is the
# strongest die in the game - EV 1.17 against Purple's 1.00 - and the battle
# pool averages under five available dice, so this was a material omission
# rather than a rounding one.
# RED_OR_ABILITY is the printed either/or: "the printed choice of Red or the
# graft ability", so committing Red forgoes the graft's damage text.
# Red keeps its own rule rather than joining the pool:
#   * only the ACTIVE RAT may commit it, and only while that Rat holds it
#   * it counts toward the graft's dice cap, so taking it costs a pooled die
#   * it EXHAUSTS when committed, like every other die, and has to be
#     recovered before its holder can commit it again
#   * afterwards it moves to a non-active Rat, as rules/bat.html has it
RED_IN_BATTLE = True
RED_OR_ABILITY = True
# RED_SET_ASIDE_IN_BATTLE. In the Experiment phase Red is SET ASIDE
# after use and is back the next turn. Carrying that into the battle,
# where every other die exhausts and recovery is the scarce resource,
# made Red the one die that never runs out - most of the +9.0 points it
# was worth. Off, Red EXHAUSTS like any other committed die and has to
# be recovered, so it is a resource with real downtime. True reproduces
# the figures measured before 2026-11-19.
RED_SET_ASIDE_IN_BATTLE = False

# Experiment titles, in the order generator/build_bat.py prints them,
# so the seeded playthrough can name its cards.
EXPERIMENT_NAMES = [
    "Baseline Calibration", "Fine Motor Trial",
    "Structural Stress Trial", "Contaminated Tissue",
    "Performance Trial", "Load-Bearing Trial",
    "Diagnostic Trial", "Rapid Response Trial",
    "Full-Spectrum Trial", "Workspace Efficiency Study",
    "Restricted Materials Trial", "Independent Performance Trial",
    "Resource Depletion Study", "Reliability Trial",
    "Reagent Exclusion Trial", "Containment Failure",
    "Endurance Trial", "Field Retrofit Trial",
    "Methodological Optimization", "Degraded Tissue Study",
]

RAT_NAMES = ["Rummage", "Fidget", "Whiz", "Mottle"]
# Side A only (see the omission log).
RAT_ABILITY = ["careful_borrower", "jury_rig", "self_sufficient",
               "experimental"]

# Flat, unconditional battle damage a graft adds when the Rats attack with
# it revealed. Everything not named here is modelled as Value only.
GRAFT_DAMAGE = {
    "Titanium-Toothed Mole": 3,
    "Voltaic Mantis": 2,
    "Piercing Horn": 2,
    "Reinforced Jaw": 2,       # printed "if a Purple hit is applied"
    "Serrated Claws": 1,
}
# The same, for a SURVIVING Splice's effect against the Rats (R20).
SPLICE_DAMAGE = {
    "Titanium-Toothed Mole": 3,
    "Voltaic Mantis": 2,
    "Piercing Horn": 2,
    "Reinforced Jaw": 2,
    "Serrated Claws": 1,
}
# Damage the graft subtracts from an incoming attack before the threshold
# check. Defence cards only.
GRAFT_SOAK = {
    "Ironback Beetle": 3,
    "Layered Carapace": 2,
    "Thickened Hide": 1,
}
# A graft worth taking for its text even a point down on Value.
GRAFT_EFFECT_BONUS = dict((n, 1) for n in
                          list(GRAFT_DAMAGE) + list(GRAFT_SOAK))

ATTACK_NAMES = ["Overwhelming Mass", "Adaptive Strike", "Predatory Instinct",
                "Spliced Reflexes", "Terrifying Roar", "Crushing Blow",
                "Unstable Growth"]
ATTACK_COLORS = bat.ATTACK_COLORS


# ------------------------------------------------------------ card helpers
def part_value(card):
    return SPECIMEN_VALUE if card[0] == "s" else UPGRADE_VALUES[card[1]]


def part_name(card):
    return SPECIMEN_NAMES[card[1]] if card[0] == "s" else UPGRADE_NAMES[card[1]]


def part_cat(card):
    return SPECIMEN_CATS[card[1]] if card[0] == "s" else UPGRADE_CATS[card[1]]


def is_specimen(card):
    return card[0] == "s"


def graft_score(card):
    """Policy value of a part as a GRAFT: its dice cap plus a nod to text."""
    return part_value(card) + GRAFT_EFFECT_BONUS.get(part_name(card), 0)


class Die(object):
    __slots__ = ("color", "zone")

    def __init__(self, color):
        self.color = color
        self.zone = "available"


class Rat(object):
    def __init__(self, i):
        self.i = i
        self.name = RAT_NAMES[i]
        self.hp = RAT_HP[i]
        self.str_ = 2
        self.rec = RAT_REC[i]
        self.ability = RAT_ABILITY[i]
        self.dice = [Die(c) for c in COLORS]
        self.down = False


class Part(object):
    """A part once it is installed or reclaimed: Value plus identity."""
    __slots__ = ("value", "name", "cat", "card", "dmg")

    def __init__(self, card):
        self.dmg = 0          # R23: damage standing on an exposed Splice
        self.value = part_value(card)
        self.name = part_name(card)
        self.cat = part_cat(card)
        self.card = card


class Game(object):
    def __init__(self, difficulty="Standard", rng=None, log=None):
        self.diff = difficulty
        self.rng = rng or random.Random()
        self.log = log if log is not None else None
        self.stalled = False

        self.rats = [Rat(i) for i in range(4)]
        self.red = Die("red")
        self.red_holder = self.rng.choice(self.rats)
        self.red_aside = False

        # ---- R1: the old Tyrant's starting parts
        specs = self.rng.sample(range(8), SPECIMENS_IN_POOL[difficulty])
        pool = [("u", i) for i in range(16)] + [("s", i) for i in specs]
        n = PARTS_AT_SETUP[difficulty]
        self.tyrant_deck = self.rng.sample(pool, min(n, len(pool)))
        self.rng.shuffle(self.tyrant_deck)
        self.setup_mix = (sum(1 for c in self.tyrant_deck if c[0] == "u"),
                          sum(1 for c in self.tyrant_deck if c[0] == "s"))
        self.tyrant_discard = []
        # R4: a reclaimed part goes to the old Tyrant's DISCARD and
        # recirculates. Holding them aside starved the 10-card Easy deck
        # and ended the lab early - it showed up as a Wake-Up at 5.00
        # Experiments instead of the 6-8 window, and as 0.15 of a part
        # missing from the conservation check.
        self.reclaimed = 0         # count only, for reporting
        self.grafts = []           # the Prototyrant's installed parts

        # ---- the Experiment clock
        deal = self.rng.sample(range(20), EXPERIMENTS_DEALT)
        packet = deal[EXPERIMENTS_DEALT - (WAKEUP_PACKET - 1):] + [None]
        self.rng.shuffle(packet)
        self.exp_deck = deal[:EXPERIMENTS_DEALT - (WAKEUP_PACKET - 1)] + packet
        self.exp_reserve = [i for i in range(20) if i not in deal]   # R3
        self.rng.shuffle(self.exp_reserve)
        self.wakeup_at = None
        self.experiments = 0

        self.last_active = None
        self.banished = 0
        self.shared_hp = SHARED_HP_START
        self.in_battle = False
        self.red_commits = 0
        self.red_rounds = 0        # battle rounds where Red was usable
        self.naked_round = None    # first round with no graft left to use
        self.directed_rescue = 0   # R22 used where the graft could not win
        self.directed_luxury = 0   # R22 used though the graft route was live
        self.direct_fee = 0        # dice tied up paying for R22
        self.grafts_spent = 0      # R24: grafts cashed in for damage
        self.avail_sum = 0         # pooled dice available, summed
        self.no_dice_rounds = 0    # rounds that opened with nothing
        self.notes = []            # verbose playthrough lines

    # ------------------------------------------------------------- logging
    def say(self, fmt, *a):
        if self.log is not None:
            self.log.append(fmt % a if a else fmt)

    # ------------------------------------------------------- dice plumbing
    def available(self, rat):
        return [d for d in rat.dice if d.zone == "available"]

    def exhausted(self, rat):
        return [d for d in rat.dice if d.zone == "exhausted"]

    def all_dice(self):
        """The shared battle pool. RED IS NOT IN IT: it belongs to
        whichever Rat holds it and is committed by the active Rat under the
        Experiment phase's own rule, never drawn from the pool."""
        return [d for r in self.rats if not r.down for d in r.dice]

    def shared_available(self):
        return [d for d in self.all_dice() if d.zone == "available"]

    def shared_exhausted(self):
        ex = [d for d in self.all_dice() if d.zone == "exhausted"]
        # A Red that EXHAUSTS in the battle must be recoverable like
        # any other die, and it is not in all_dice() because it belongs
        # to its holder and not to the pool. It still never appears in
        # shared_available(): the holder commits it, nobody draws it.
        if (self.in_battle and not RED_SET_ASIDE_IN_BATTLE
                and self.red.zone == "exhausted"):
            ex.append(self.red)
        return ex

    def draw_part(self):
        """R4: never fail to reveal a part."""
        if not self.tyrant_deck:
            if not self.tyrant_discard:
                return None
            self.tyrant_deck = self.tyrant_discard
            self.tyrant_discard = []
            self.rng.shuffle(self.tyrant_deck)
        return self.tyrant_deck.pop()

    def next_experiment(self):
        """R3: replacements come from the undealt twelve."""
        if self.exp_reserve:
            return self.exp_reserve.pop()
        return None

    # =====================================================================
    # LAB PHASE
    # =====================================================================
    def lab_turn(self):
        """One Experiment. False once the Wake-Up card is turned."""
        if not self.exp_deck:
            return False
        exp = self.exp_deck.pop(0)
        if exp is None:                       # the Wake-Up card
            self.wakeup_at = self.experiments
            self.say("  Wake-Up turned after %d Experiments.", self.experiments)
            return False

        eff = EXPERIMENT_EFFECT.get(exp)
        name = EXPERIMENT_NAMES[exp]
        number = EXPERIMENT_TARGETS[exp]

        # ---- reveal parts
        count = 3 if eff == "extra_upgrade" else 2        # R6
        parts = [p for p in (self.draw_part() for _ in range(count))
                 if p is not None]
        if len(parts) < 2:
            return False
        if eff == "rereveal":                             # Contaminated Tissue
            self.tyrant_discard += parts
            parts = [p for p in (self.draw_part() for _ in range(count))
                     if p is not None]
            if len(parts) < 2:
                return False

        rat = self.choose_rat()
        if rat is None:
            return False

        # Rapid Response Trial with no Green: R7
        dropped = None
        if eff == "need_green" and not any(
                d.color == "green" for d in self.available(rat)):
            dropped = max(parts, key=part_value)
            parts = [p for p in parts if p is not dropped]
            self.tyrant_discard.append(dropped)

        # ---- R2 / R6: the Target
        if len(parts) >= 2:
            pair = sorted(parts, key=part_value, reverse=True)[:2]
            combined = sum(part_value(p) for p in pair)
        else:
            combined = part_value(parts[0])
        target = max(TARGET_FLOOR, combined - number)
        if eff == "methodology":                          # R8
            target = 0

        self.experiments += 1
        self.say("Experiment %d: %s (number %d)", self.experiments, name, number)
        self.say("  parts revealed: %s", ", ".join(
            "%s [%d]" % (part_name(p), part_value(p)) for p in parts))
        if dropped is not None:
            self.say("  no Green available - %s discarded before the Target (R7)",
                     part_name(dropped))
        self.say("  Target = %d combined - %d = %d%s", combined, number, target,
                 "  (Methodological Optimization reduces it to 0)"
                 if eff == "methodology" else "")
        self.say("  active Rat: %s  (available %s)", rat.name,
                 "/".join(d.color[0].upper() for d in self.available(rat))
                 or "none")

        ok = self.attempt(rat, target, eff, parts)
        self.say("  -> %s", "SUCCESS" if ok else "FAILURE")
        self.assign(parts, ok, eff)
        self.recover(rat, parts)
        self.last_active = rat
        # rules/bat.html: the Red die goes on a NON-ACTIVE Rat. Leaving it
        # pinned made the holder win the active-Rat sort every turn, so one
        # Rat worked all seven Experiments into exhaustion while the other
        # three stayed fresh - visible in the playthrough log as 'active
        # Rat: Rummage' seven times running.
        others = [r for r in self.rats if r is not rat and not r.down]
        if others:
            self.red_holder = max(others, key=lambda r: (
                len(self.available(r)),
                sum(EV[d.color] for d in self.available(r))))
        return True

    def choose_rat(self):
        up = [r for r in self.rats if not r.down]
        if not up:
            return None
        return max(up, key=lambda r: (
            r is self.red_holder and not self.red_aside,
            len(self.available(r)),
            sum(EV[d.color] for d in self.available(r))))

    def borrow_row(self):
        """R10: the restriction reads the Prototyrant's graft count."""
        return min(3, len(self.grafts))

    def borrow_for(self, rat, need):
        allowed = bat.BORROWABLE[self.borrow_row()]
        pool = [(o, d) for o in self.rats if o is not rat and not o.down
                for d in self.available(o) if d.color in allowed]
        if not pool:
            return None
        lender, die = max(pool, key=lambda od: EV[od[1].color])
        if EV[die.color] < need:
            return None
        return lender, die

    def attempt(self, rat, target, eff, parts):
        """Commit, roll, accumulate across Strategy phases."""
        if target <= 0:
            return True
        avail = pick_order(self.available(rat), self.rng)

        cap = 2 if eff == "max_two" else 99
        if eff == "exclude_die" and avail:
            avail = avail[1:] if len(avail) > 1 else []

        phases = STR_PHASES
        if eff == "str_one" or eff == "no_phase_two":
            phases = 1
        if rat.ability == "experimental" and any(is_specimen(p) for p in parts):
            phases += 1                                   # Echo of +1 STR

        # Self-Sufficient: no borrow, no Red, Target -1
        solo = rat.ability == "self_sufficient"
        if solo:
            target = max(1, target - 1)

        used_red = False
        borrowed = None
        successes = 0
        committed = []

        for phase in range(phases):
            if successes >= target:
                break
            take = avail[:cap] if phase == 0 else avail[:1]
            avail = avail[len(take):]
            # colour requirements
            if phase == 0 and eff == "need_yellow" and not any(
                    d.color == "yellow" for d in take):
                target += 1
            if phase == 0 and eff == "three_colors":
                want = set()
                for d in take:
                    want.add(d.color)
                if len(want) < 3:
                    extra = [d for d in avail if d.color not in want]
                    take += extra[:3 - len(want)]
                    avail = [d for d in avail if d not in take]
            for d in take:
                d.zone = "exhausted"
                committed.append(d)
                v = roll(d.color, self.rng)
                if eff == "reroll_pb" and phase == 0 \
                        and d.color in ("purple", "blue") and v:
                    v = roll(d.color, self.rng)
                successes += v
            if phase == 0 and not solo and eff != "no_red" \
                    and self.red_holder is rat and not self.red_aside \
                    and successes < target:
                used_red = True
                self.red_aside = True
                successes += roll("red", self.rng)
            if phase == 0 and not solo and eff != "no_borrow" \
                    and successes < target:
                got = self.borrow_for(rat, target - successes)
                if got is not None:
                    borrowed = got
                    got[1].zone = "exhausted"
                    successes += roll(got[1].color, self.rng)

        if rat.ability == "jury_rig" and successes < target:
            successes += roll(committed[0].color, self.rng) if committed else 0

        if borrowed is not None:
            self.resolve_borrow(*borrowed, rat=rat)
        self.say("    committed %d dice%s%s -> %d successes vs %d",
                 len(committed), " + Red" if used_red else "",
                 " + borrow" if borrowed else "", successes, target)
        return successes >= target

    def resolve_borrow(self, lender, die, rat):
        miss = FACES[die.color].count(0) / 6.0
        bad = self.rng.random() < miss
        if bad and rat.ability == "careful_borrower":
            bad = self.rng.random() < miss
        if bad:
            die.zone = "banished"
            self.banished += 1

    def assign(self, parts, ok, eff):
        """R5/R6/R8/R9: one graft, one reclaim, leftovers to the discard."""
        if not parts:
            return
        order = sorted(parts, key=part_value, reverse=True)
        if eff == "methodology":                           # R8
            graft = order[-1]
        elif ok:
            graft = max(parts, key=graft_score)            # Rats choose
        else:
            graft = order[-1]                              # Tyrant takes best
        rest = [p for p in parts if p is not graft]

        self.grafts.append(Part(graft))
        if rest:
            claim = max(rest, key=part_value)
            self.reclaimed += 1
            self.tyrant_discard.append(claim)
            for p in rest:
                if p is not claim:
                    self.tyrant_discard.append(p)          # R6 leftover
        self.say("    graft -> Prototyrant: %s [%d]%s", part_name(graft),
                 part_value(graft),
                 ("   reclaimed by the old Tyrant: %s [%d]"
                  % (part_name(max(rest, key=part_value)),
                     part_value(max(rest, key=part_value)))) if rest else "")

        if eff == "retrofit" and ok:                       # R9
            mine = [g for g in self.grafts[:-1] if not is_specimen(g.card)]
            offer = [p for p in rest if not is_specimen(p)]
            if mine and offer:
                worst = min(mine, key=lambda g: g.value)
                best = max(offer, key=part_value)
                if part_value(best) > worst.value:
                    self.grafts.remove(worst)
                    self.grafts.append(Part(best))
                    self.tyrant_discard.append(worst.card)
                    # The swapped-IN part was already placed above -
                    # reclaimed or discarded - so it has to leave
                    # there or the card is duplicated and the wall
                    # gains 0.08 of a Splice a game.
                    if best in self.tyrant_discard:
                        self.tyrant_discard.remove(best)
                    else:
                        self.reclaimed -= 1
                    self.say("    Field Retrofit: %s swapped out for %s (R9)",
                             worst.name, part_name(best))

    def recover(self, rat, parts):
        n = rat.rec
        if rat.ability == "experimental" and any(is_specimen(p) for p in parts):
            n += 1
        if rat.ability == "specimen_adapt":
            n += sum(1 for g in self.grafts if is_specimen(g.card))   # R11
        if rat.ability == "prepared" and self.last_active is not rat:
            n += 1
        ex = self.exhausted(rat)
        for d in pick_order(ex, self.rng)[:n]:
            d.zone = "available"
        self.red_aside = False

    # =====================================================================
    # BATTLE
    # =====================================================================
    def start_battle(self):
        """R13/R14. The wall is starting parts minus grafts."""
        # Red joins the shared pool, available, before the opening recovery.
        self.in_battle = True
        self.red.zone = "available"
        # Carve the Tyrant's bag out of the Rats' dice.
        self.bag = []
        for want in TYRANT_BAG:
            pick = None
            for r in self.rats:
                for d in r.dice:
                    if d.color == want and d.zone != "banished" \
                            and d not in self.bag:
                        pick = d
                        break
                if pick:
                    break
            if pick is None:                      # printed shortage procedure
                left = [d for r in self.rats for d in r.dice
                        if d.zone != "banished" and d not in self.bag]
                if not left:
                    continue
                pick = max(left, key=lambda d: EV[d.color])
            self.bag.append(pick)
        for d in self.bag:
            d.zone = "tyrant"

        # R14: recover once at the transition.
        for d in pick_order(self.shared_exhausted(), self.rng)[:OPENING_RECOVERY]:
            d.zone = "available"
        self.opening_dice = len(self.shared_available())

        # The wall: undrawn parts plus everything reclaimed.
        wall = [Part(c) for c in self.tyrant_deck + self.tyrant_discard]
        self.rng.shuffle(wall)
        self.splices = wall
        self.graft_pile = list(self.grafts)
        self.rng.shuffle(self.graft_pile)
        self.attack_deck = list(range(7))
        self.rng.shuffle(self.attack_deck)
        self.attack_color = ATTACK_COLORS[self.attack_deck[-1]]   # seed
        self.rounds = 0
        self.passes = 0
        self.forced_passes = 0
        self.regained = 0
        self.pass_graft_lived = 0
        self.unbreakable = 0
        # WHY a forced pass happened. Three problems wear the same face:
        #   "colour" the commit-colour rule cost them the reaching dice
        #   "cap"    the graft Value capped them, though the pool had enough
        #   "pool"   not enough dice existed at all, cap or no cap
        self.forced_why = collections.Counter()
        self.forced_unmodelled = 0
        self.graft_aside = []
        self.graft_picked = collections.Counter()
        self.gate = dict(
            grafts=len(self.grafts),
            graft_value=sum(g.value for g in self.grafts),
            splices=len(self.splices),
            splice_value=sum(s.value for s in self.splices),
            worst=max([s.value for s in self.splices] or [0]),
            dice=self.opening_dice)
        self.say("")
        self.say("WAKE-UP. Prototyrant holds %d grafts (total Value %d); "
                 "the old Tyrant holds %d Splices (total Value %d, biggest %d).",
                 self.gate["grafts"], self.gate["graft_value"],
                 self.gate["splices"], self.gate["splice_value"],
                 self.gate["worst"])
        self.say("Rats enter with %d available dice; commit colour seeded %s.",
                 self.opening_dice, self.attack_color)

    def draw_attack(self):
        if not self.attack_deck:
            self.attack_deck = list(range(7))
            self.rng.shuffle(self.attack_deck)
        return self.attack_deck.pop()

    def commit_dice(self, cap, allow_red=True):
        """Up to `cap` dice honouring the commit colour (one of it, or two of
        one other colour)."""
        avail = pick_order(self.shared_available(), self.rng)
        if not allow_red:
            avail = [d for d in avail if d.color != "red"]
        pick = avail[:cap]
        if not self.attack_color or any(d.color == self.attack_color
                                        for d in pick):
            return pick
        swap = [d for d in avail if d.color == self.attack_color]
        if swap and pick:
            pick = pick[:-1] + swap[:1]
            return pick
        by = collections.Counter(d.color for d in pick)
        if any(v >= 2 for v in by.values()):
            return pick
        for c in COLORS:
            pair = [d for d in avail if d.color == c][:2]
            if len(pair) == 2:
                return (pick[:max(0, cap - 2)] + pair)[:cap]
        return pick

    def ceiling(self, dice, graft):
        """Most damage this exact set of dice could possibly roll.

        Prices the Red either/or, or the policy believes in a blow it cannot
        assemble and the forced-pass count goes soft.
        """
        return self._score(dice, graft, lambda c: max(FACES[c]))

    def expected(self, dice, graft):
        """Mean damage, with the same either/or applied."""
        return self._score(dice, graft, lambda c: EV[c])

    def _score(self, dice, graft, per_die):
        top = sum(per_die(d.color) for d in dice)
        if graft is None:
            return top
        if RED_OR_ABILITY and any(d.color == "red" for d in dice):
            return top
        return top + GRAFT_DAMAGE.get(graft.name, 0)

    def may_use_red(self, rat):
        """The Experiment phase's rule, unchanged: the active Rat commits Red
        only while it holds it and it is neither set aside nor spent.
        The zone test covers both readings - set aside leaves Red
        available, exhausting it does not."""
        return (RED_IN_BATTLE and self.red_holder is rat
                and not self.red_aside and self.red.zone == "available")

    def best_commit(self, cap, graft, target, rat):
        """THE RED CHOICE, made rather than stumbled into.

        Red counts toward the cap, so taking it costs a pooled die, and under
        RED_OR_ABILITY it also forfeits the graft's text - worth up to 3. A
        policy that simply grabbed its strongest dice committed Red every
        round it held it and LOST 7 points doing so, which would have read as
        "Red hurts the Rats" when the truth was that no choice was being
        made. So price both hands and keep the better: viability first, then
        mean damage.
        """
        best = None
        for use_red in ((False, True) if self.may_use_red(rat) else (False,)):
            pk = self.commit_dice(cap - 1 if use_red else cap)
            hand = list(pk) + ([self.red] if use_red else [])
            key = (self.ceiling(hand, graft) >= target,
                   self.expected(hand, graft))
            if best is None or key > best[0]:
                best = (key, hand)
        return best[1]

    def direct_option(self, avail, graft, need, rat):
        """R22. The directed attack: (pick, fee), or (None, None).

        Only with a graft exposed - directing is a way of using a graft
        BADLY, not of fighting without one - and only while the Rats can
        still set aside DIRECT_COST dice they did not commit. The graft's
        ability is forgone, which is why the hand is scored with no graft
        at all; that also frees Red from the printed either/or.
        """
        if not DIRECT_ATTACK or graft is None:
            return None, None
        pick = self.best_commit(DIRECT_CAP, None, need, rat)
        spare = [d for d in avail if d not in pick]
        if len(spare) < DIRECT_COST:
            return None, None
        return pick, spare[-DIRECT_COST:]

    def choose_graft(self, options, splice, rat):
        """Which revealed graft to use and expose.

        A graft does two jobs: its Value CAPS the dice the Rats may commit,
        and it is the threshold an incoming attack must meet to destroy it.
        A high Value is better at both, so the only reason to expose a low
        one is to keep the better card out of harm - worth doing exactly
        when the cheap one already gets the job done, because the card set
        aside cannot be destroyed this round.

        If no graft makes the blow viable the Rats are passing anyway and
        the cap is irrelevant, so expose whichever DEFENDS best - the
        highest threshold.
        """
        scored = []
        for g in options:
            pick = self.best_commit(g.value, g, splice.value, rat)
            ok = self.ceiling(pick, g) >= splice.value
            likely = self.expected(pick, g) >= splice.value
            scored.append((ok, likely, -g.value, g))
        if any(t[0] for t in scored):
            scored.sort(key=lambda t: (t[0], t[1], t[2]), reverse=True)
        else:
            # -t[2] is the graft's Value: highest threshold first.
            scored.sort(key=lambda t: -t[2], reverse=True)
        use = scored[0][3]
        return use, [g for g in options if g is not use]

    def battle_round(self):
        self.rounds += 1
        # A destroyed graft never returns, so the Prototyrant's parts are a
        # ONE-WAY clock. Record the round it runs out: see attrition().
        if not self.grafts and self.naked_round is None:
            self.naked_round = self.rounds
        splice = self.splices[0]
        # R23: with partial damage the Rats need only the REMAINDER. Every
        # decision below reads `need`; the retaliation still reads the
        # Splice's printed Value, which sets its attack dice.
        need = splice.value - splice.dmg if PARTIAL_DAMAGE else splice.value
        # AN ACTIVE RAT EACH BATTLE TURN, chosen exactly as in the Experiment
        # phase - the sort prefers whoever holds Red, which is why Red moves
        # to a NON-ACTIVE Rat at the end of the round. This has to happen
        # before the graft decision: whether Red is available changes which
        # graft is worth exposing.
        rat = self.choose_rat()
        if rat is None:
            return False
        if len(self.graft_pile) < GRAFT_REVEAL:
            self.graft_pile += [g for g in self.grafts
                                if g not in self.graft_pile]
            self.graft_aside = []
            self.rng.shuffle(self.graft_pile)
        shown = []
        while self.graft_pile and len(shown) < GRAFT_REVEAL:
            shown.append(self.graft_pile.pop(0))
        if len(shown) > 1:
            graft, rest = self.choose_graft(shown, splice, rat)
            low = min(g.value for g in shown)
            self.graft_picked["low" if graft.value == low else "high"] += 1
            self.graft_aside += rest
            self.say("  revealed %s -> using %s [%d], %s set aside",
                     ", ".join("%s [%d]" % (g.name, g.value) for g in shown),
                     graft.name, graft.value,
                     ", ".join(g.name for g in rest))
        else:
            graft = shown[0] if shown else None

        cap = graft.value if graft is not None else NO_GRAFT_CAP
        if CAP_FLOOR and graft is not None:
            cap = max(cap, CAP_FLOOR)                              # R25
        avail = pick_order(self.shared_available(), self.rng)
        self.avail_sum += len(avail)
        if not avail:
            self.no_dice_rounds += 1
        if self.may_use_red(rat):
            self.red_rounds += 1
        pick = self.best_commit(cap, graft, need, rat)
        ceiling = self.ceiling(pick, graft)
        viable = ceiling >= need
        expect = self.expected(pick, graft)

        # R22. Price the directed attack against the graft route and keep
        # the better: can it break at all first, then mean damage.
        dpick, dfee = self.direct_option(avail, graft, need, rat)
        use_direct = False
        if dpick is not None:
            dceil = self.ceiling(dpick, None)
            dexp = self.expected(dpick, None)
            if ((dceil >= need, dexp - DIRECT_MARGIN)
                    > (viable, expect)):
                use_direct = True
                graft_viable = viable
                pick = dpick
                ceiling = dceil
                viable = dceil >= need
                expect = dexp
        if not use_direct:
            dfee = []

        if not viable:
            self.unbreakable += 1
            cls_cap = DIRECT_CAP if use_direct else cap
            if self.ceiling(avail[:cls_cap], graft) >= need:
                why = "colour"
            elif self.ceiling(avail, graft) >= need:
                why = "cap"
            else:
                why = "pool"
            self.forced_why[why] += 1
            if graft is not None and graft.name not in GRAFT_DAMAGE \
                    and graft.name not in GRAFT_SOAK:
                # The card has printed battle text this module does not
                # model, so the real game might have resolved the round.
                self.forced_unmodelled += 1
        want_pass = (graft is not None
                     and (not viable
                          or expect < need - COMMIT_MARGIN)
                     and len(self.shared_exhausted()) > 0)
        if want_pass and use_direct:
            # R22 is paid for on the attack. A round that passes directs
            # nothing, forgoes nothing and ties up no die.
            use_direct = False
            dfee = []
        self.say("")
        self.say("Round %d: graft %s [%d] / Splice %s [%d]  (colour %s)",
                 self.rounds, graft.name if graft else "none",
                 graft.value if graft is not None else cap,
                 splice.name, splice.value, self.attack_color)

        broke = False
        if want_pass:
            self.passes += 1
            if not viable:
                self.forced_passes += 1
            self.say("  RECOVERY PASS (%s): ceiling %d vs Target %d",
                     "no legal break" if not viable else "rational",
                     ceiling, need)
        else:
            dmg = 0
            if use_direct:
                if graft_viable:
                    self.directed_luxury += 1   # chosen with a live graft
                else:
                    self.directed_rescue += 1   # a forced pass, rescued
            used_red = any(d.color == "red" for d in pick)
            if used_red:
                self.red_commits += 1
            for d in pick:
                if d is self.red and RED_SET_ASIDE_IN_BATTLE:
                    self.red_aside = True     # set aside, not exhausted
                else:
                    d.zone = "exhausted"
                dmg += roll(d.color, self.rng)
            if (graft is not None and not use_direct
                    and not (used_red and RED_OR_ABILITY)):
                dmg += GRAFT_DAMAGE.get(graft.name, 0)
            for d in dfee:
                d.zone = "aside"      # invisible to both pools this round
                self.direct_fee += 1
            # R24: cash the exposed graft in when the blow falls short and
            # its Value closes the gap. The part is gone and cannot defend.
            spent = None
            gname = graft.name if graft is not None else "no graft"
            if (SPEND_GRAFT and graft is not None and dmg < need
                    and dmg + graft.value >= need):
                spent = graft
                dmg += graft.value
                self.grafts = [g for g in self.grafts if g is not graft]
                self.grafts_spent += 1
                self.say("  SPEND %s [%d] for the break - the part is gone.",
                         graft.name, graft.value)
                graft = None
            self.say("  %s %d dice -> %d damage vs Target %d%s",
                     "DIRECT" if use_direct else "commit",
                     len(pick), dmg, need,
                     ("  (forgoing %s, %d die tied up)"
                      % (gname, len(dfee))) if use_direct else "")
            if PARTIAL_DAMAGE:
                splice.dmg += dmg
                dmg = splice.dmg
                if dmg < splice.value:
                    self.say("  %s holds at %d of %d.",
                             splice.name, dmg, splice.value)
            if dmg >= splice.value:
                broke = True
                self.splices.pop(0)
                self.say("  %s BREAKS.", splice.name)
                if BANISH_ON_BREAK:
                    av = self.shared_available() or self.shared_exhausted()
                    if av:
                        av[0].zone = "banished"
                        self.banished += 1
                if not self.splices:
                    self.say("  The last Splice is down. The Rats win.")
                    return "win"

        # ---- counterattack. R20: a destroyed Splice still sets the count.
        card = self.draw_attack()
        draws = min(SPLICE_ATTACK_DICE or splice.value, len(self.bag))
        hits = sum(roll(d.color, self.rng) for d in self.bag[:draws])
        if not broke:
            hits += SPLICE_DAMAGE.get(splice.name, 0)
        direct = 0
        target = rat
        if card == 0:
            hits += 3
        elif card == 1:
            up = [r for r in self.rats if not r.down]
            target = up[(up.index(rat) + 1) % len(up)]
            self.say("  Adaptive Strike retargets %s.", target.name)
        elif card == 2:
            up = [r for r in self.rats if not r.down]
            target = max(up, key=lambda r: len(self.available(r)))   # R16
            self.say("  Predatory Instinct retargets %s (most dice, R16).",
                     target.name)
        elif card == 3:
            hits += len(self.splices)
        elif card == 4:
            hits = 0
            av = self.shared_available()
            if av:
                av[-1].zone = "exhausted"
            self.say("  Terrifying Roar: no damage, one die exhausted.")
        elif card == 5:
            direct = 1
            hits = max(0, hits - 1)                                   # R18
        self.say("  Attack card: %s   incoming %d%s",
                 ATTACK_NAMES[card], hits,
                 " (+1 direct)" if direct else "")

        self.apply_attack(target, hits, graft, direct, passed=want_pass,
                          no_ability=use_direct)

        if card == 6 and not target.down:                             # R17
            second = sum(roll(d.color, self.rng) for d in self.bag[:2])
            self.say("  Unstable Growth attacks again for %d.", second)
            self.apply_attack(target, second, None, 0, passed=want_pass)

        # ---- recovery pass payout (R20)
        if want_pass:
            n = rat.rec + PASS_RECOVERY_BONUS
            got = pick_order(self.shared_exhausted(), self.rng)[:n]
            for d in got:
                d.zone = "available"
            self.regained += len(got)
            self.say("  recovered %d dice (REC %d + %d).",
                     len(got), rat.rec, PASS_RECOVERY_BONUS)

        # R22: the die tied up by a directed attack joins the EXHAUSTED
        # pool after this round's recovery, so it cannot be reclaimed until
        # a later recovery pass. Attacks pay no recovery in this model, so
        # the ordering only matters if that ever changes.
        for d in dfee:
            d.zone = "exhausted"

        # rules/bat.html: Red goes to a NON-ACTIVE Rat, and a Red that was
        # set aside comes back. In the Experiment phase recover() does this;
        # the battle has no recover(), so it happens here. Under the
        # default an exhausted Red does NOT come back here: it waits in
        # the exhausted pool for a recovery like every other die.
        self.red_aside = False
        others = [r for r in self.rats if r is not rat and not r.down]
        if others:
            self.red_holder = max(others, key=lambda r: (
                len(self.available(r)),
                sum(EV[d.color] for d in self.available(r))))

        if self.rats_beaten():
            return "loss"
        if not self.splices:
            return "win"
        return True

    def hurt(self, rat, n):
        """Put n damage on the Rats, pooled or per-Rat."""
        if not n:
            return
        if SHARED_HP:
            self.shared_hp -= n
        else:
            rat.hp -= n

    def rats_beaten(self):
        if SHARED_HP:
            return self.shared_hp <= 0
        return all(r.down for r in self.rats)

    def apply_attack(self, rat, hits, graft, direct, passed,
                     no_ability=False):
        """R15: a revealed graft defends; a Rat is only reached without one.

        no_ability is R22: the Rats directed the attack, so the graft keeps
        its printed Value as a threshold but its soak text is forgone.
        """
        if direct:
            self.hurt(rat, direct)
        if graft is not None:
            if not no_ability:
                hits = max(0, hits - GRAFT_SOAK.get(graft.name, 0))
            if hits >= graft.value:
                self.grafts = [g for g in self.grafts if g is not graft]
                self.say("  graft %s destroyed (took %d vs threshold %d).",
                         graft.name, hits, graft.value)
            else:
                self.graft_pile.append(graft)
                if passed:
                    self.pass_graft_lived += 1
                self.say("  graft %s holds (%d < %d).",
                         graft.name, hits, graft.value)
        else:
            self.hurt(rat, hits)
            if hits:
                self.say("  no graft: %d to Health%s.", hits,
                         " (pool now %d)" % self.shared_hp if SHARED_HP
                         else " on " + rat.name)
        if SHARED_HP:
            return
        if rat.hp <= 0 and not rat.down:
            rat.down = True
            for d in rat.dice:
                if d.zone not in ("tyrant", "banished"):
                    d.zone = "banished"
            self.say("  %s is KNOCKED OUT.", rat.name)

    # =====================================================================
    def play(self):
        guard = 0
        while guard < 60:
            guard += 1
            if not self.lab_turn():
                break
        if self.wakeup_at is None:
            self.wakeup_at = self.experiments
        self.start_battle()
        if not self.splices:
            return "win"
        for _ in range(ROUND_GUARD):
            out = self.battle_round()
            if out in ("win", "loss"):
                return out
            if out is False:
                return "loss"
        self.stalled = True
        return "stall"


# ---------------------------------------------------------------- runners
def one(difficulty="Standard", seed=20):
    lines = []
    g = Game(difficulty, random.Random(seed), log=lines)
    print("=" * 72)
    print("ONE SEEDED PLAYTHROUGH - %s, seed %d" % (difficulty, seed))
    print("=" * 72)
    print("Old Tyrant's starting parts: %d  (%d regular / %d Specimen)"
          % (sum(g.setup_mix), g.setup_mix[0], g.setup_mix[1]))
    print("")
    out = g.play()
    for l in lines:
        print(l)
    print("")
    print("OUTCOME: %s after %d battle rounds" % (out.upper(), g.rounds))
    print("conservation check: starting parts %d = wall %d + grafts %d -> %s"
          % (sum(g.setup_mix), g.gate["splices"], g.gate["grafts"],
             "OK" if sum(g.setup_mix) == g.gate["splices"] + g.gate["grafts"]
             else "MISMATCH"))
    return out


def batch(games=4000, seed=20):
    print("REVISED STANDALONE BAT - seeded batch, %d games a difficulty\n"
          % games)
    print("%-10s %6s %6s %6s  %5s %5s  %5s %5s %5s %5s  %5s %5s %5s %5s"
          % ("rung", "win%", "KO%", "stall", "mix", "wake",
             "graft", "gV", "splic", "sV", "rnds", "pass%", "regn", "unbr"))
    for lvl in LEVELS:
        rng = random.Random(seed)
        n = collections.Counter()
        acc = collections.Counter()
        rounds, mixes = [], []
        for _ in range(games):
            g = Game(lvl, rng)
            out = g.play()
            n[out] += 1
            rounds.append(g.rounds)
            mixes.append(g.setup_mix[1])
            for k, v in g.gate.items():
                acc[k] += v
            acc["rounds"] += g.rounds
            acc["passes"] += g.passes
            acc["forced"] += g.forced_passes
            acc["regained"] += g.regained
            acc["unbreak"] += g.unbreakable
            acc["wake"] += g.wakeup_at
            acc["pass_lived"] += g.pass_graft_lived
        f = float(games)
        rs = sorted(rounds)
        print("%-10s %5.1f%% %5.1f%% %5.1f%%  %5.1f %5.2f  %5.2f %5.1f %5.2f "
              "%5.1f  %5.1f %5.1f%% %5.2f %5.2f"
              % (lvl, 100*n["win"]/f, 100*n["loss"]/f, 100*n["stall"]/f,
                 sum(mixes)/f, acc["wake"]/f,
                 acc["grafts"]/f, acc["graft_value"]/f,
                 acc["splices"]/f, acc["splice_value"]/f,
                 acc["rounds"]/f,
                 100*acc["passes"]/max(1.0, acc["rounds"]),
                 acc["regained"]/f, acc["unbreak"]/f))
        print("%-10s battle length p10/p50/p90 = %d/%d/%d  max %d   "
              "forced passes %.2f/game   graft survived a pass %.2f/game"
              % ("", rs[len(rs)//10], rs[len(rs)//2], rs[(9*len(rs))//10],
                 rs[-1], acc["forced"]/f, acc["pass_lived"]/f))
    print("\nmix = Specimens among the Tyrant's starting parts; wake = "
          "Experiments resolved before Wake-Up.")
    print("gV/sV = total graft and Splice Value at the gate; unbr = rounds "
          "where no legal commit could reach the exposed Splice.")



# ---------------------------------------------------------------- analyses
def sample(lvl, games, seed=11, parts=None, reveal=None):
    """Run one arm and return the aggregates these reports need."""
    global GRAFT_REVEAL
    old_parts, old_reveal = PARTS_AT_SETUP.get(lvl), GRAFT_REVEAL
    if parts is not None:
        PARTS_AT_SETUP[lvl] = parts
    if reveal is not None:
        GRAFT_REVEAL = reveal
    try:
        rng = random.Random(seed)
        a = collections.Counter()
        rounds, wins = [], 0
        for _ in range(games):
            g = Game(lvl, rng)
            out = g.play()
            wins += out == "win"
            a["stall"] += out == "stall"
            rounds.append(g.rounds)
            a["rounds"] += g.rounds
            a["passes"] += g.passes
            a["forced"] += g.forced_passes
            a["vol"] += g.passes - g.forced_passes
            a["attacks"] += g.rounds - g.passes
            a["splices"] += g.gate["splices"]
            a["broken"] += g.gate["splices"] - len(g.splices)
            a["unmodelled"] += g.forced_unmodelled
            a["red_rounds"] += g.red_rounds
            a["d_rescue"] += g.directed_rescue
            a["d_luxury"] += g.directed_luxury
            a["d_fee"] += g.direct_fee
            if g.naked_round is not None:
                a["naked"] += 1
                a["naked_round"] += g.naked_round
                a["win_naked"] += out == "win"
            a["red_commits"] += g.red_commits
            a["avail"] += g.avail_sum
            a["no_dice"] += g.no_dice_rounds
            for k, v in g.forced_why.items():
                a["why_" + k] += v
            for k, v in g.graft_picked.items():
                a["pick_" + k] += v
    finally:
        if old_parts is not None:
            PARTS_AT_SETUP[lvl] = old_parts
        GRAFT_REVEAL = old_reveal
    a["games"], a["wins"] = games, wins
    a["p50"] = sorted(rounds)[len(rounds) // 2]
    return a


def pass_line(a):
    f = float(a["games"])
    rnd = max(1.0, float(a["rounds"]))
    pas = max(1.0, float(a["passes"]))
    return ("%5.2f %5.2f %5.2f  %5.1f%% %5.1f%%"
            % (a["passes"] / f, a["forced"] / f, a["vol"] / f,
               100 * a["forced"] / pas, 100 * a["forced"] / rnd))


HEAD = "pass/g forced volun  %ofpas %ofrnd"


def diagnose(games=3000):
    print("WHY EACH FORCED PASS HAPPENED. Three problems wear one face:")
    print("  colour = the commit-colour rule cost them the reaching dice")
    print("  cap    = the graft Value capped them, though the pool had enough")
    print("  pool   = not enough dice existed at all, cap or no cap")
    print("%d games a rung, current rules, decks %s."
          % (games, "/".join(str(PARTS_AT_SETUP[l]) for l in LEVELS)))
    print("")
    print("%-10s %-34s %7s %6s %6s %7s"
          % ("rung", HEAD, "colour", "cap", "pool", "unmodl"))
    for lvl in LEVELS:
        a = sample(lvl, games)
        tot = max(1.0, float(a["why_colour"] + a["why_cap"] + a["why_pool"]))
        print("%-10s %-34s %6.1f%% %5.1f%% %5.1f%% %6.1f%%"
              % (lvl, pass_line(a),
                 100 * a["why_colour"] / tot, 100 * a["why_cap"] / tot,
                 100 * a["why_pool"] / tot,
                 100 * a["unmodelled"] / max(1.0, float(a["forced"]))))
    print("")
    print("Every ratio is accumulated per game, not got by dividing means.")
    print("unmodl = forced passes whose exposed graft has printed battle text")
    print("         this module does not model, so the real game might have")
    print("         resolved the round.")


def ladder(games=3000):
    print("TIGHTER LADDER: starting decks 10/12/14/16, combat unchanged.")
    print("This is the FIRST proposal, kept as a comparison arm; the dials")
    print("now ship at %s."
          % "/".join(str(PARTS_AT_SETUP[l]) for l in LEVELS))
    print("%d games an arm." % games)
    print("")
    print("%-12s %5s %7s %7s %7s %7s  %s"
          % ("rung (deck)", "wall", "win%", "attacks", "broken", "rounds",
             HEAD))
    for lvl, parts in zip(LEVELS, (10, 12, 14, 16)):
        a = sample(lvl, games, parts=parts)
        f = float(a["games"])
        print("%-12s %5.2f %6.1f%% %7.2f %7.2f %7.2f  %s"
              % ("%s (%d)" % (lvl, parts), a["splices"] / f,
                 100 * a["wins"] / f, a["attacks"] / f, a["broken"] / f,
                 a["rounds"] / f, pass_line(a)))
    print("")
    print("wall = Splices at Wake-Up. The questions: is a 5-Splice wall a")
    print("good Standard, and is 9 still too much for Nobulous?")


def hp_tune(games=2500):
    global SHARED_HP, SHARED_HP_START
    print("POOLED RAT HEALTH, TUNED. Two grafts revealed. %d games an arm."
          % games)
    print("Per-Rat 1/1/2/2 = 6 is the printed total. Pooling also recovers")
    print("the overkill a per-Rat track wastes, so 6 pooled is not 6 kinder.")
    print("")
    decks = (11, 12, 13, 14, 15)
    print("%6s  " % "HP" + "".join("%9s" % ("deck %d" % d) for d in decks)
          + "   forced")
    SHARED_HP = True
    try:
        for hp in (6, 8, 9, 10, 12):
            SHARED_HP_START = hp
            row, forced = [], 0.0
            for d in decks:
                a = sample("Standard", games, parts=d, reveal=2)
                row.append(100.0 * a["wins"] / a["games"])
                if d == 13:
                    forced = a["forced"] / float(games)
            print("%6d  " % hp + "".join("%8.1f%%" % v for v in row)
                  + "   %6.2f" % forced)
    finally:
        SHARED_HP = False
    row = []
    for d in decks:
        a = sample("Standard", games, parts=d, reveal=2)
        row.append(100.0 * a["wins"] / a["games"])
    print("%6s  " % "1122" + "".join("%8.1f%%" % v for v in row))
    print("")
    print("The dial saturates near 9: Health sets the LEVEL, the deck builds")
    print("the LADDER. With Red exhausting (R21), HP 12 and decks 12/13/14/15")
    print("read 63/53/39/30 against BAT's printed 60/52/39/27.")


def attrition(games=2000):
    """Is graft attrition the real battle clock, rather than Health?

    A destroyed graft leaves self.grafts for good (R15), so the
    Prototyrant's seven parts are spent at roughly one a round against a
    battle that runs twelve. Once they are gone there is no defender and
    the dice cap falls to NO_GRAFT_CAP.
    """
    print("GRAFT ATTRITION AS THE REAL BATTLE CLOCK.")
    print("A destroyed graft never comes back, so the Prototyrant's parts")
    print("are a one-way resource. This asks how often the Rats end the")
    print("fight naked: no graft to defend with, and a dice cap of %d."
          % NO_GRAFT_CAP)
    print("Decks %s, Proto HP %d, GRAFT_REVEAL %d, %d games a rung."
          % ("/".join(str(PARTS_AT_SETUP[l]) for l in LEVELS),
             SHARED_HP_START, GRAFT_REVEAL, games))
    print("")
    print("%-10s %7s %8s %9s %10s %9s %8s"
          % ("rung", "win%", "naked%", "atRound", "win|naked", "win|clad",
             "rounds"))
    for lvl in LEVELS:
        a = sample(lvl, games)
        f = float(a["games"])
        nk = max(1, a["naked"])
        cl = max(1, a["games"] - a["naked"])
        print("%-10s %6.1f%% %7.1f%% %9.1f %9.1f%% %8.1f%% %8.2f"
              % (lvl, 100.0 * a["wins"] / f, 100.0 * a["naked"] / f,
                 a["naked_round"] / float(nk),
                 100.0 * a["win_naked"] / nk,
                 100.0 * (a["wins"] - a["win_naked"]) / cl,
                 a["rounds"] / f))
    print("")
    print("naked% = games reaching a round with no surviving graft;")
    print("atRound = when it first happens; win|naked vs win|clad = the")
    print("win rate for games that do and do not get there.")


def directed(games=2000):
    """R22: can the Rats push a WEAK Prototyrant through a bad matchup?

    Without R22 the exposed graft's Value caps the Rats' own dice, so the
    build they assembled in the lab is the build they fight with. The
    questions the rule has to answer are whether a previously forced pass
    becomes a directed attack, whether weak builds win through that route,
    and whether directing becomes the DEFAULT - which would mean the price
    of one tied-up die is too low.
    """
    global DIRECT_ATTACK, DIRECT_MARGIN
    was_on, was_margin = DIRECT_ATTACK, DIRECT_MARGIN
    weak_at = 24          # gate graft Value; the mean is about 25.5
    print("R22, DIRECTING THE ATTACK. Standard, deck %d, Proto HP %d,"
          % (PARTS_AT_SETUP["Standard"], SHARED_HP_START))
    print("GRAFT_REVEAL %d, %d games an arm. weak = gate graft Value <= %d."
          % (GRAFT_REVEAL, games, weak_at))
    print("")
    print("%-20s %6s %7s %8s %8s %8s %7s %7s %7s"
          % ("arm", "win%", "win|wk", "win|str", "direct/g", "rescue",
             "luxury", "naked%", "rounds"))
    try:
        for name, on, margin in (("R22 off", False, 0.0),
                                 ("on, greedy", True, 0.0),
                                 ("on, margin 0.5", True, 0.5),
                                 ("on, margin 1.0", True, 1.0),
                                 ("on, margin 2.0", True, 2.0)):
            DIRECT_ATTACK, DIRECT_MARGIN = on, margin
            rng = random.Random(11)
            a = collections.Counter()
            for _ in range(games):
                g = Game("Standard", rng)
                out = g.play()
                won = out == "win"
                weak = g.gate["graft_value"] <= weak_at
                a["win"] += won
                a["weak"] += weak
                a["win_weak"] += won and weak
                a["rescue"] += g.directed_rescue
                a["luxury"] += g.directed_luxury
                a["naked"] += g.naked_round is not None
                a["rounds"] += g.rounds
            f = float(games)
            wk = max(1, a["weak"])
            st = max(1, games - a["weak"])
            print("%-20s %5.1f%% %6.1f%% %7.1f%% %8.2f %8.2f %7.2f %6.1f%%"
                  " %7.2f"
                  % (name, 100.0 * a["win"] / f, 100.0 * a["win_weak"] / wk,
                     100.0 * (a["win"] - a["win_weak"]) / st,
                     (a["rescue"] + a["luxury"]) / f, a["rescue"] / f,
                     a["luxury"] / f, 100.0 * a["naked"] / f,
                     a["rounds"] / f))
    finally:
        DIRECT_ATTACK, DIRECT_MARGIN = was_on, was_margin
    print("")
    print("rescue = directed where the graft route could not reach the")
    print("Splice at all, i.e. a round that would have been a forced pass.")
    print("luxury = directed although the graft route COULD have broken it;")
    print("if that dominates, one tied-up die is too cheap a price.")


def shape(games=2000):
    """Can the GREAT third sit at 40-50% without the poor third at 2%?

    Deck size moves every third together and hits the poor one hardest, so
    on its own it buys the target rate at the cost of a hopeless floor. The
    floor dials (R25, R26) are worth most to the weakest build, so the two
    together should be able to lower the ceiling and lift the floor at once.
    """
    global CAP_FLOOR, SPLICE_ATTACK_DICE
    was = (CAP_FLOOR, SPLICE_ATTACK_DICE, PARTS_AT_SETUP["Standard"])
    print("SHAPING THE SPREAD. Standard rung, Proto HP %d, GRAFT_REVEAL %d,"
          % (SHARED_HP_START, GRAFT_REVEAL))
    print("%d games an arm. Thirds are by graft Value at Wake-Up." % games)
    print("")
    print("%-26s %7s %9s %9s %9s %8s"
          % ("arm", "win%", "poor 3rd", "mid 3rd", "great 3rd", "rounds"))
    arms = (("plain", 0, 0),
            ("cap floor 4", 4, 0),
            ("flat attack 3", 0, 3),
            ("flat attack 4", 0, 4),
            ("floor 4 + flat 3", 4, 3))
    try:
        for deck in (15, 16, 17, 18):
            PARTS_AT_SETUP["Standard"] = deck
            for name, floor, flat in arms:
                CAP_FLOOR, SPLICE_ATTACK_DICE = floor, flat
                rng = random.Random(11)
                rows, rounds = [], 0
                for _ in range(games):
                    g = Game("Standard", rng)
                    out = g.play()
                    rows.append((g.gate["graft_value"], out == "win"))
                    rounds += g.rounds
                rows.sort(key=lambda t: t[0])
                n = len(rows)
                cut = n // 3
                thirds = (rows[:cut], rows[cut:n - cut], rows[n - cut:])
                r = [100.0 * sum(1 for _, w in t if w) / max(1, len(t))
                     for t in thirds]
                print("%-26s %6.1f%% %8.1f%% %8.1f%% %8.1f%% %8.2f"
                      % ("deck %d, %s" % (deck, name),
                         100.0 * sum(1 for _, w in rows if w) / n,
                         r[0], r[1], r[2], rounds / float(n)))
            print("")
    finally:
        CAP_FLOOR, SPLICE_ATTACK_DICE, PARTS_AT_SETUP["Standard"] = was
    print("Read the great-3rd column against 40-50%, then the poor 3rd for")
    print("how hopeless a bad lab is. A dial that lifts the poor third more")
    print("than the great one is doing what the brief asks.")


def lab(games=2000):
    """Does the lab's outcome set the battle's difficulty, and where?

    The target: a GREAT lab should still be a challenge - 40-50% at
    Standard - and a POOR lab should be close to hopeless. So the number
    to tune against is not the overall win rate but the TOP THIRD's.

    Lab quality is the Prototyrant's total graft Value at Wake-Up. That one
    number carries both sides of every Experiment, because conservation
    makes the old Tyrant's wall the complement of it: parts taken plus
    parts reclaimed is the starting deck.
    """
    old = PARTS_AT_SETUP["Standard"]
    print("DID THE LAB DECIDE IT? Standard rung, Proto HP %d, GRAFT_REVEAL"
          % SHARED_HP_START)
    print("%d, %d games a deck. Games are split into thirds by the"
          % (GRAFT_REVEAL, games))
    print("Prototyrant's total graft Value at Wake-Up.")
    print("")
    print("%6s %7s %9s %9s %9s %9s %8s"
          % ("deck", "win%", "poor 3rd", "mid 3rd", "great 3rd", "cuts",
             "rounds"))
    try:
        for deck in (13, 14, 15, 16, 17):
            PARTS_AT_SETUP["Standard"] = deck
            rng = random.Random(11)
            rows, rounds = [], 0
            for _ in range(games):
                g = Game("Standard", rng)
                out = g.play()
                rows.append((g.gate["graft_value"], out == "win"))
                rounds += g.rounds
            rows.sort(key=lambda t: t[0])
            n = len(rows)
            cut = n // 3
            thirds = (rows[:cut], rows[cut:n - cut], rows[n - cut:])
            rates = [100.0 * sum(1 for _, w in t if w) / max(1, len(t))
                     for t in thirds]
            lo = thirds[0][-1][0] if thirds[0] else 0
            hi = thirds[2][0][0] if thirds[2] else 0
            print("%6d %6.1f%% %8.1f%% %8.1f%% %8.1f%% %5d/%-3d %8.2f"
                  % (deck, 100.0 * sum(1 for _, w in rows if w) / n,
                     rates[0], rates[1], rates[2], lo, hi,
                     rounds / float(n)))
    finally:
        PARTS_AT_SETUP["Standard"] = old
    print("")
    print("cuts = the graft-Value boundaries of the poor and great thirds.")
    print("The dial to read is the GREAT third: the brief wants it at 40-50%,")
    print("with the poor third far below it.")


def weak(games=2000):
    """Can a WEAK Prototyrant win, and by which mechanism?

    attrition() shows the loss condition is running out of grafts, and
    diagnose() shows 88% of forced passes are the dice POOL rather than the
    graft cap. So a rule that raises the cap (R22) is aimed at the 12%.
    These are the three candidates, priced against the same baseline and
    split by how good a build the lab produced.
    """
    global DIRECT_ATTACK, PARTIAL_DAMAGE, SPEND_GRAFT
    was = (DIRECT_ATTACK, PARTIAL_DAMAGE, SPEND_GRAFT)
    weak_at = 24          # gate graft Value; the mean is about 25.5
    print("WAYS A WEAK BUILD MIGHT GET THROUGH. Standard, deck %d, Proto"
          % PARTS_AT_SETUP["Standard"])
    print("HP %d, GRAFT_REVEAL %d, %d games an arm. weak = gate graft"
          % (SHARED_HP_START, GRAFT_REVEAL, games))
    print("Value <= %d, which is a bit under half of all games." % weak_at)
    print("")
    print("%-22s %6s %7s %8s %6s %7s %7s %7s"
          % ("arm", "win%", "win|wk", "win|str", "gap", "spent/g",
             "naked%", "rounds"))
    arms = (("baseline, none of it", False, False, False),
            ("R22 direct only", True, False, False),
            ("R23 partial only", False, True, False),
            ("R24 spend only", False, False, True),
            ("R22 + R23", True, True, False),
            ("R22 + R24", True, False, True),
            ("all three", True, True, True))
    try:
        for name, d, pa, sp in arms:
            DIRECT_ATTACK, PARTIAL_DAMAGE, SPEND_GRAFT = d, pa, sp
            rng = random.Random(11)
            a = collections.Counter()
            for _ in range(games):
                g = Game("Standard", rng)
                out = g.play()
                won = out == "win"
                wk = g.gate["graft_value"] <= weak_at
                a["win"] += won
                a["weak"] += wk
                a["win_weak"] += won and wk
                a["spent"] += g.grafts_spent
                a["naked"] += g.naked_round is not None
                a["rounds"] += g.rounds
            f = float(games)
            nw = max(1, a["weak"])
            ns = max(1, games - a["weak"])
            pw = 100.0 * a["win_weak"] / nw
            ps = 100.0 * (a["win"] - a["win_weak"]) / ns
            print("%-22s %5.1f%% %6.1f%% %7.1f%% %5.1f %7.2f %6.1f%% %7.2f"
                  % (name, 100.0 * a["win"] / f, pw, ps, ps - pw,
                     a["spent"] / f, 100.0 * a["naked"] / f,
                     a["rounds"] / f))
    finally:
        DIRECT_ATTACK, PARTIAL_DAMAGE, SPEND_GRAFT = was
    print("")
    print("gap = how much better a strong build does than a weak one. That")
    print("is the number the brief is about: a mechanism that lets a weak")
    print("Prototyrant win should SHRINK it without lifting the ceiling.")


def graft_choice(games=3000):
    print("GRAFT CHOICE: deck 14 on every rung, reveal 1 graft versus 2.")
    print("%d games an arm." % games)
    print("")
    print("%-14s %7s %7s %7s  %-34s %s"
          % ("arm", "win%", "attacks", "broken", HEAD, "low-Value chosen"))
    for lvl in LEVELS:
        for reveal in (1, 2):
            a = sample(lvl, games, parts=14, reveal=reveal)
            f = float(a["games"])
            tp = float(a["pick_low"] + a["pick_high"]) or 1.0
            extra = ("%5.1f%%" % (100 * a["pick_low"] / tp)) if reveal == 2                 else "     -"
            print("%-14s %6.1f%% %7.2f %7.2f  %-34s %s"
                  % ("%s, reveal %d" % (lvl[:8], reveal),
                     100 * a["wins"] / f, a["attacks"] / f,
                     a["broken"] / f, pass_line(a), extra))
    print("")
    print("Reveal 2: use and expose one graft, set the other aside until the")
    print("pile reshuffles - the card held back cannot be destroyed.")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "batch"
    if mode == "one":
        lvl = sys.argv[2] if len(sys.argv) > 2 else "Standard"
        one(lvl, int(sys.argv[3]) if len(sys.argv) > 3 else 20)
    elif mode == "assumptions":
        print(__doc__)
    elif mode == "diagnose":
        diagnose(int(sys.argv[2]) if len(sys.argv) > 2 else 3000)
    elif mode == "ladder":
        ladder(int(sys.argv[2]) if len(sys.argv) > 2 else 3000)
    elif mode == "shape":
        shape(int(sys.argv[2]) if len(sys.argv) > 2 else 2000)
    elif mode == "lab":
        lab(int(sys.argv[2]) if len(sys.argv) > 2 else 2000)
    elif mode == "weak":
        weak(int(sys.argv[2]) if len(sys.argv) > 2 else 2000)
    elif mode == "directed":
        directed(int(sys.argv[2]) if len(sys.argv) > 2 else 2000)
    elif mode == "attrition":
        attrition(int(sys.argv[2]) if len(sys.argv) > 2 else 2000)
    elif mode == "graft":
        graft_choice(int(sys.argv[2]) if len(sys.argv) > 2 else 3000)
    elif mode == "hp":
        hp_tune(int(sys.argv[2]) if len(sys.argv) > 2 else 2500)
    else:
        batch(int(sys.argv[2]) if len(sys.argv) > 2 else 4000)
