"""Build-a-Tyrant: Splice Phase, then the Tyrant Battle.

Rules source: rules/bat.html plus the card data in generator/build_bat.py.

Verified against rules/bat.html and the core 20-Strong_Rulebook.pdf.

Only 17 dice exist in the physical box, so the Tyrant's six - 2 Purple,
2 Blue, 1 Green, 1 Yellow - MUST be taken out of the Rats' own 16 personal
dice. There is no separate Tyrant pool. rules/bat.html reads as though the
Tyrant brings its own ("those six dice never exhaust"), which is not
physically possible and should be reworded. tyrant_takes_rat_dice=False
models the impossible version and exists only to measure what the dice tax
costs: about 15 points at Standard.

Modeled as printed:
  * Value is printed and never weakens - damage marked on a Splice does not
    reduce the dice the Tyrant draws
  * the Tyrant draws dice equal to the highest Value among Splices it still
    holds, minimum 2, maximum 6
  * the track is Buff HP, then the five Splices in RANDOM order, then the
    Health dial; damage chews left to right, and the leftmost surviving
    Splice supplies its effect until it is destroyed and the next takes over
  * the damage asymmetry, which is what makes the battle work: the RATS'
    damage carries over freely along the Tyrant's track (Buff HP, then the
    five Splices left to right, then Health), while a TYRANT attack destroys
    at most ONE of a Rat's Upgrades and carries over nothing - if it cannot
    meet any held Upgrade's Value the Rat keeps it, and either way nothing
    reaches Health unless the Rat holds no Upgrades at all.
    rules/bat.html currently words this the other way round ("the rest carries
    on to the next Upgrade under the same test, then to Health"), which
    contradicts the intended rule and should be corrected there.
  * a Rat may tap ONE Upgrade per attack instead of committing Red - it is
    never obliged to - and by default a tapped Upgrade cannot soak the
    Tyrant's reply; it untaps at the start of the next round
  * commit up to 6, reroll each miss once (STR 2), recover REC + 2
  * Lab Rat abilities are silent during the battle
  * Red belongs to one Rat at a time. Only the active Rat may commit it, and
    only if it is holding it; after use it is set aside and placed on a
    NON-active Rat next turn, so it is available every other turn at best
  * borrowing: one non-Red die from another Rat, the colors allowed
    narrowing as the borrower's Upgrade count rises, then rolled by itself
    afterwards - a miss banishes it from the game permanently, which
    permanently shrinks the shared battle pool
  * Splicing Machine Malfunction tops the Tyrant up from unused Upgrades;
    running out of Upgrades reshuffles the discard instead

The printed tap effects ARE implemented, but behind `card_effects=True`, which
is OFF by default. That switch turns on the leftmost Splice firing free on
every Tyrant attack, and the Rats tapping one Upgrade per attack. At Standard,
15,000 games: effects off 71.4%, on 40.1%, on with tapped_defends 58.9% -
against a published ~63%. No setting reproduces the ladder exactly; off
overshoots and on undershoots. That is an unresolved discrepancy rather than a
settled answer; see README.md.

Design variants, all switchable, for testing rule changes:
  dice_rule        "six" (current) or "highest_upgrade" - the attacking Rat
                   commits dice up to its best Upgrade's Value, minimum 2
  tapped_defends   whether a tapped Upgrade still soaks the Tyrant's reply
  tap_bonus        "none", "mobility_senses", "all", or "free" - ways to make
                   the weak tap effects worth using
  attacker_policy  "healthiest" or "best_roller" - who leads the attack

The 7 Tyrant Attack cards ARE implemented, behind `attack_cards=True`. Two
carry deliberate changes agreed in testing, so they no longer match the text
in generator/build_bat.py:
  * Terrifying Roar exhausts 1 die, not 2 - at 2 it ended 86% of games by
    itself against a pool that starts at only 8.6 dice
  * Adaptive Strike now hits the next Lab Rat clockwise (wrapping) instead of
    bypassing an Upgrade, which was killing its target 87% of the time
Crushing Blow is left as printed: it is meant to be the worst card.

The 20 Experiment effects are not implemented.
"""
import random

from dice import COLORS, EV, EV_REROLL, roll

RAT_HP = [1, 1, 2, 2]
RAT_REC = [2, 2, 1, 1]
STR_PHASES = 2

# Upgrade Values and categories in deck order, from build_bat.py UPGRADES.
UPGRADE_VALUES = [2, 3, 3, 4, 2, 2, 3, 3, 2, 3, 3, 4, 2, 3, 2, 4]
UPGRADE_CATS = ["Power", "Power", "Power", "Power",
                "Mobility", "Mobility", "Mobility", "Mobility",
                "Defense", "Defense", "Defense", "Defense",
                "Senses", "Senses", "Senses", "Senses"]
UPGRADE_NAMES = ["Serrated Claws", "Reinforced Jaw", "Capacitor Muscles",
                 "Piercing Horn", "Spring-Loaded Legs", "Prehensile Tail",
                 "Tripwire Tendons", "Evasive Reflexes", "Thickened Hide",
                 "Layered Carapace", "Chromatic Plating", "Reactive Shell",
                 "Acute Hearing", "Predatory Focus", "Rapid Metabolism",
                 "Neural Overclock"]
SPECIMEN_NAMES = ["Titanium-Toothed Mole", "Voltaic Mantis", "Blink Hare",
                  "Ghost Gecko", "Ironback Beetle", "Prismatic Tortoise",
                  "Echo Bat", "Regenerator Newt"]
MOD_NAMES = ["Extra Limbs", "Secondary Brain", "Adrenal Gland",
             "Bone Plating", "Redundant Organs", "Hypermetabolism"]

SPECIMEN_VALUE = 5
SPECIMEN_CATS = ["Power", "Power", "Mobility", "Mobility",
                 "Defense", "Defense", "Senses", "Senses"]

# Printed Targets of the 20 Experiments.
EXPERIMENT_TARGETS = [2, 2, 3, 3, 4, 3, 3, 4, 3, 3, 4, 4, 3, 4, 4, 3, 4, 5, 4, 5]

# difficulty -> (Specimens shuffled into the Upgrade deck, Buff HP)
# (Specimens shuffled into the Upgrade deck, the Tyrant's starting Buff HP).
# Re-tuned once the eight Rat side abilities were modelled, which moved the
# whole ladder up by roughly 13 points. The dial is exhausted at Nobulous:
# there are only 8 Specimen cards; the Buff HP track was extended to 15
# spaces so the bottom two rungs could separate.
DIFFICULTY = {
    "Easy": (5, 3),
    "Standard": (6, 4),
    "Hard": (7, 7),
    "Nobulous": (8, 11),
}

TYRANT_NEED = [("purple", 2), ("blue", 2), ("green", 1), ("yellow", 1)]

# Borrowing: "The active Rat may borrow one available non-Red die from another
# Rat. The more Upgrades the borrower already holds, the worse the die it is
# allowed to take." After the Experiment resolves the borrowed die is rolled by
# itself; on a miss it is BANISHED - removed from the game permanently - and on
# a hit it returns to its owner exhausted. The printed banish risks (17/33/50/
# 67%) are exactly the miss chances of the best die each row allows.
# The 7 Tyrant Attack cards, revealed one per Tyrant attack and discarded;
# reshuffle the discard when the deck runs out. Text from build_bat.py ATTACKS.
OVERWHELMING_MASS = 0   # +3 damage
ADAPTIVE_STRIKE = 1     # hits the next Lab Rat clockwise, wrapping
PREDATORY_INSTINCT = 2  # hits the Rat with the greatest total Upgrade Value
SPLICED_REFLEXES = 3    # +1 damage per Splice the Tyrant still holds
TERRIFYING_ROAR = 4     # no damage; exhausts dice from the shared pool
TERRIFYING_ROAR_DICE = 1  # printed 2; see the note in resolve_attack
CRUSHING_BLOW = 5       # 1 damage straight to Health, unabsorbable
UNSTABLE_GROWTH = 6     # if the target survives, attack again with 2 dice
ATTACK_COUNT = 7
# Proposed color dot on each Attack card, in the order above. The most
# recently revealed card sets the color for Buff HP and the Tyrant's Health,
# which have none of their own; one card is flipped at the start of the battle
# to supply it before the Tyrant has attacked. No Red: Red is never wild.
ATTACK_COLORS = ["green", "blue", "yellow", "green", "yellow", "green", "yellow"]
# Mass, Reflexes and Crushing Blow are Green; Predatory Instinct, Roar and
# Unstable Growth are Yellow; Adaptive Strike is the lone Blue.

BORROWABLE = {
    0: ["purple", "blue", "green", "yellow"],
    1: ["blue", "green", "yellow"],
    2: ["green", "yellow"],
    3: ["yellow"],
}

# ---------------------------------------------------------------------------
# NRJ overlay tiers. Each tier includes the ones before it.
#   I   - draw 1 of 6 Experimental Protocols at setup
#   II  - 6 Unauthorized Modifications shuffled into the Upgrade deck
#   III - 6 Research Notes, claimed on condition for a one-shot reward
# Card data from the PROTOCOLS / MODS / NOTES tables in generator/build_nrj.py.
# ---------------------------------------------------------------------------
# Accelerated Trials, as printed: -1 Target at printed Target 4+, and 2 of the
# active Rat's available dice exhausted after completing one. The two knobs
# below exist to test a narrower, costlier version of the card.
ACCEL_FLOOR = 5          # printed Target at which the -1 applies
ACCEL_COST_ALWAYS = True   # bill the 2 dice on every attempt, not just a win
INDEP_ON_WIN = True        # Independent Funding pays only on a completed Experiment
# Questionable Methodology: splice the stronger Upgrade into the Tyrant for a
# replacement reveal. The printed card charged +1 Target for the privilege, so
# nobody took it; -1 makes it a bargain paid for in Tyrant strength.
METHODOLOGY_DELTA = -1
METHODOLOGY_FLOOR = 5      # the policy only takes the bargain on hard Experiments

# Which module each tier adds. The printed campaign is protocol, mods, notes;
# permuting this answers whether a different order would give BAT the dip at
# Tier II that NAP and AoS have.
TIER_ORDER = ["protocol", "mods", "notes"]

# Candidate fixes for BAT's tier ladder, which currently rises where NAP's and
# AoS's dip. Both mirror what those two games already do:
#   TIER1_EXTRA_SPECIMEN - Tier I carries a flat handicap, the way Following
#       Setbacks and Nobulous Interference do, instead of only a Protocol.
#   MODS_REPLACE - the 6 Modifications REPLACE 6 ordinary Upgrades rather than
#       being added alongside, the way Impostor Tasks replace Credit Tasks.
# All of these are OFF: each tier should be one deck to swap in or add, not a
# card plus a side instruction. They remain so the measurements reproduce.
TIER1_EXTRA_SPECIMEN = False  # superseded by TIER1_BANISH
TIER1_BANISH = False       # Tier I banishes 1 non-Red die, as AoS Legacy Hardware does
TIER2_BANISH = False       # Tier II banishes a second one. Unlike Specimens this
                           # has no ceiling: there are only 8 Specimen cards, so
                           # a Specimen-based tier rule does nothing at Hard
                           # and Nobulous, which already use 7 and 8 of them.
TIER2_EXTRA_SPECIMEN = 0   # further Specimens once the Modifications arrive
MODS_REPLACE = False
TIER_INDEX = {"none": 0, "I": 1, "II": 2, "III": 3}


def module_active(name, tier):
    """True when `tier` has reached the tier this module is assigned to."""
    return TIER_INDEX.get(tier, 0) >= TIER_ORDER.index(name) + 1


# Each Rat is double-sided and one side is chosen at setup, so BAT's hero
# axis is four choices rather than one. Index = Rat, [front, back].
#   careful_borrower  reroll the banishment check on a die you borrowed
#   tool_keeper       a die lent out and not banished comes back available
#   jury_rig          once per Experiment, reroll one miss
#   fine_tuning       once per Experiment, reroll a basic hit, keeping it on a miss
#   self_sufficient   no borrow and no Red this Experiment: Target -1
#   prepared          recover 1 if a different Rat was active last turn
#   experimental      a revealed Specimen gives +1 STR and +1 recovery
#   adaptation        completing recovers 1 extra die per Specimen held
RAT_SIDES = [
    ["careful_borrower", "tool_keeper"],
    ["jury_rig", "fine_tuning"],
    ["self_sufficient", "prepared"],
    ["experimental", "adaptation"],
]

PROTOCOLS = [
    "cross_contamination",      # a banished borrowed die Splices an Upgrade
    "shared_equipment",         # 2 dice into a common Equipment pool
    "accelerated_trials",       # Target 4+ gets -1, then exhaust 2 dice
    "questionable_procurement",  # +1 Specimen; first one is over the limit
    "independent_funding",      # the lender recovers 1 die
    "questionable_methodology",  # Splice the stronger Upgrade for -1 Target
]

# Unauthorized Modifications, in deck order: (Value, drawback while held).
# Either a Rat or the Tyrant may hold them. The drawbacks are the reason the
# cards are a mixed blessing, so each is modeled as printed rather than
# flattened into one generic penalty.
#   no_borrow  Extra Limbs        - may not borrow dice (borrowing unmodeled)
#   no_red     Secondary Brain    - may not use the Red die
#   less_hp    Adrenal Gland      - 1 less Health, minimum 1
#   less_rec   Bone Plating       - -1 REC, minimum 1 (also blocks 2 damage)
#   no_streak  Redundant Organs   - cannot be active on consecutive turns
#   burn_die   Hypermetabolism    - exhaust 1 die per Experiment attempted
MODS = [
    (3, "no_borrow"),
    (3, "no_red"),
    (4, "less_hp"),
    (3, "less_rec"),
    (4, "no_streak"),
    (3, "burn_die"),
]
# Lower the Modification bodies so the drawback is the point of the card.
MOD_VALUE_DELTA = 0

# What the second Strategy phase does.
#   extra_die        commit one further die (what the model has always done)
#   reroll_misses    reroll the dice that missed, keeping the hits
#   reroll_unbanked  also reroll a basic hit when the die is worth more than
#                    the 1 it scored - only Red (EV 1.17) and Purple (EV 1.0)
#                    qualify, and only while short of the Target
#   push             the printed rule: reroll misses, commit more dice, and
#                    reroll hits when only a Crit can still close the gap
PHASE2_POLICY = "push"
# A flat rise on every printed Experiment Target. Needs no new components -
# it is 20 numbers on 20 cards - so it is the cheapest way to move the whole
# ladder once the dice-side dial is exhausted.
TARGET_DELTA = 1
MOD_VALUES = [v for v, _ in MODS]
MOD_CATS = ["Mobility", "Senses", "Power", "Defense", "Defense", "Senses"]

# Research Notes print restrictive claim conditions and are earned during
# play, not granted at setup - see Game.claim_notes.

# ---------------------------------------------------------------------------
# The frontmost-Splice effect.
#
#   "The Tyrant holds Spliced Upgrades differently. It never taps: the
#    frontmost Splice in its row applies its effect on every attack, free,
#    for as long as that card survives - so a Splice is armor and a weapon at
#    the same time, and killing it is how you switch off both."
#
# Every Upgrade and Specimen prints a tap effect, so whichever card sits at the
# front of the Tyrant's row fires that effect on every single attack. Because
# damage runs Buff HP, then DEFENSE Splices, then the rest, the frontmost card
# is usually one of the damage-reducers - which is exactly the point.
#
# Each entry is (damage added to the Tyrant's attack, damage soaked off the
# Rats' attack, successes removed from the Rats' attack, Rat dice exhausted,
# dice a RAT recovers by tapping this card). The last field only matters on the
# Rat side: effects that recover dice do nothing for a Tyrant whose six dice
# never exhaust, but dice are the Rats' binding constraint, so for them these
# are far from inert.
# ---------------------------------------------------------------------------
UPGRADE_EFFECTS = [
    (1, 0, 0, 0, 0),   # Serrated Claws     +1 per Blue/Green basic hit
    (2, 0, 0, 0, 0),   # Reinforced Jaw     +2 with a Purple hit
    (1, 0, 0, 0, 0),   # Capacitor Muscles  commits an extra die
    (2, 0, 0, 0, 0),   # Piercing Horn      +2, bypasses a Defense Upgrade
    (1, 0, 0, 0, 0),   # Spring-Loaded Legs rolls an extra Green
    (1, 0, 0, 0, 0),   # Prehensile Tail    rolls an extra Yellow
    (0, 0, 0, 1, 0),   # Tripwire Tendons   opponent exhausts a die
    (0, 0, 1, 0, 0),   # Evasive Reflexes   removes 1 success
    (0, 1, 0, 0, 0),   # Thickened Hide     reduce incoming by 1
    (0, 2, 0, 0, 0),   # Layered Carapace   reduce incoming by 2
    (0, 2, 0, 0, 0),   # Chromatic Plating  Blue and Green -1 each
    (0, 2, 0, 0, 0),   # Reactive Shell     Purple and Yellow -1 each
    (1, 0, 0, 0, 0),   # Acute Hearing      +1 STR next turn
    (1, 0, 0, 0, 0),   # Predatory Focus    +1 STR this attack
    (0, 0, 0, 0, 1),   # Rapid Metabolism   recovery only
    (0, 0, 0, 0, 2),   # Neural Overclock   recovery only
]

SPECIMEN_EFFECTS = [
    (3, 0, 0, 0, 0),   # Titanium-Toothed Mole  +3 damage
    (3, 0, 0, 0, 0),   # Voltaic Mantis         +2, and +2 more on a Crit
    (2, 0, 0, 0, 0),   # Blink Hare             rolls up to 2 extra dice
    (0, 0, 2, 0, 0),   # Ghost Gecko            removes 2 successes
    (0, 3, 0, 0, 0),   # Ironback Beetle        reduce incoming by 3
    (0, 2, 0, 0, 0),   # Prismatic Tortoise     two colors -1 per die
    (1, 0, 0, 0, 1),   # Echo Bat               +1 STR
    (0, 0, 0, 0, 3),   # Regenerator Newt       recovery only
]

MOD_EFFECTS = [
    (1, 0, 0, 0, 0),   # Extra Limbs        rolls an exhausted Green or Yellow
    (1, 0, 0, 0, 0),   # Secondary Brain    +1 STR
    (3, 0, 0, 0, 0),   # Adrenal Gland      +3 damage
    (0, 2, 0, 0, 0),   # Bone Plating       reduce incoming by 2
    (0, 0, 0, 0, 0),   # Redundant Organs   survives a knockout
    (0, 0, 0, 0, 2),   # Hypermetabolism    recovery only
]

NO_EFFECT = (0, 0, 0, 0, 0)


def splice_effect(card):
    kind, idx = card
    if kind == "s":
        return SPECIMEN_EFFECTS[idx % len(SPECIMEN_EFFECTS)]
    if kind == "m":
        return MOD_EFFECTS[idx]
    return UPGRADE_EFFECTS[idx]


class Die(object):
    __slots__ = ("color", "zone")

    def __init__(self, color):
        self.color = color
        self.zone = "available"  # available | exhausted | banished | tyrant


class Upgrade(object):
    """An Upgrade held by a Rat. A Rat may tap one per attack, instead of
    committing Red, for its printed effect; "the card cannot absorb damage
    until it untaps"."""
    __slots__ = ("value", "effect", "tapped", "name", "cat")

    def __init__(self, value, effect, name="", cat=""):
        self.value = value
        self.effect = effect
        self.tapped = False
        self.name = name
        self.cat = cat


class Rat(object):
    def __init__(self, i):
        self.i = i
        self.hp = RAT_HP[i]
        self.rec = RAT_REC[i]
        self.upgrades = []  # Upgrade objects
        self.dice = [Die(c) for c in COLORS]
        self.down = False
        self.mod_ids = []   # indices of held Unauthorized Modifications
        self.side = 0       # 0 = front, 1 = back
        self.specimens = 0  # Specimens this Rat holds

    @property
    def ability(self):
        # side 2 is a control with no ability, for measuring the other two.
        if self.side > 1:
            return None
        return RAT_SIDES[self.i][self.side]

    def has(self, drawback):
        return any(MODS[i][1] == drawback for i in self.mod_ids)

    @property
    def mods(self):
        return len(self.mod_ids)

    def take_mod(self, idx):
        self.mod_ids.append(idx)
        if MODS[idx][1] == "less_hp":
            self.hp = max(1, self.hp - 1)

    def drop_mod(self, value):
        for i in list(self.mod_ids):
            if MODS[i][0] == value:
                self.mod_ids.remove(i)
                return

    def effective_rec(self):
        return max(1, self.rec - (1 if self.has("less_rec") else 0))


def splice_value(card):
    if card[0] == "m" and MOD_VALUE_DELTA:
        return max(1, MOD_VALUES[card[1]] + MOD_VALUE_DELTA)
    kind, idx = card
    if kind == "s":
        return SPECIMEN_VALUE
    if kind == "m":
        return MOD_VALUES[idx]
    return UPGRADE_VALUES[idx]


def splice_name(card):
    kind, idx = card
    if kind == "s":
        return SPECIMEN_NAMES[idx % len(SPECIMEN_NAMES)]
    if kind == "m":
        return MOD_NAMES[idx]
    return UPGRADE_NAMES[idx]


def splice_cat(card):
    kind, idx = card
    if kind == "s":
        return SPECIMEN_CATS[idx % len(SPECIMEN_CATS)]
    if kind == "m":
        return MOD_CATS[idx]
    return UPGRADE_CATS[idx]


# ---------------------------------------------------------------------------
# Color commitment (proposed). Each Upgrade category has a color; while a
# Splice is leftmost, the attacking Rat must commit at least one die of its
# color, or - if it has none available - two dice of one other color as a
# wild. Specimens carry two colors and need BOTH. Red is not wild: it can
# never satisfy a color requirement.
#
# Weaker dice are tied to the more powerful Upgrades, so beating a strong
# Splice means spending dice you would otherwise leave in the pool.
# ---------------------------------------------------------------------------
CAT_COLOR = {"Power": "green", "Mobility": "blue",
             "Defense": "yellow", "Senses": "purple"}
# Each Specimen keeps its own category's color and adds one more, spread so
# every color appears as a second color exactly twice.
SPECIMEN_COLORS = [("green", "purple"), ("green", "yellow"),
                   ("blue", "purple"), ("blue", "yellow"),
                   ("yellow", "blue"), ("yellow", "green"),
                   ("purple", "blue"), ("purple", "green")]


def splice_colors(card):
    kind, idx = card
    if kind == "s":
        return SPECIMEN_COLORS[idx % len(SPECIMEN_COLORS)]
    cat = MOD_CATS[idx] if kind == "m" else UPGRADE_CATS[idx]
    return (CAT_COLOR[cat],)


class Splice(object):
    """One card on the Tyrant track.

    Value is printed and never weakens: "it uses the card's printed Value -
    damage already marked on that card does not weaken it" (rules/bat.html).
    Damage marked on it is tracked separately.
    """
    __slots__ = ("value", "cat", "damage", "effect", "colors")

    def __init__(self, value, cat, effect=NO_EFFECT, colors=()):
        self.value = value
        self.cat = cat
        self.damage = 0
        self.colors = colors
        self.effect = effect

    @property
    def alive(self):
        return self.damage < self.value

    def soak(self, dmg):
        """Absorb up to the remaining Value; return what carries through."""
        room = self.value - self.damage
        hit = min(room, dmg)
        self.damage += hit
        return dmg - hit


class Game(object):
    def __init__(self, difficulty="Standard", rng=None, tyrant_takes_rat_dice=True,
                 tier="none", card_effects=False, dice_rule="six",
                 attacker_policy="healthiest", tapped_defends=False,
                 tap_bonus="none", attack_cards=True, tyrant_pool=6,
                 battle_rec_bonus=2, battle_rec="flat", rec_rule="strongest",
                 color_rule="attack_only", commit_policy="conserve",
                 sides=None):
        self.rng = rng or random.Random()
        self.tyrant_takes_rat_dice = tyrant_takes_rat_dice
        self.specimens, self.buff_max = DIFFICULTY[difficulty]
        self.tier = tier
        # The printed tap effects on Upgrades and Specimens: the Tyrant's
        # frontmost Splice firing free on every attack, and the Rats tapping
        # one Upgrade per attack instead of Red. OFF by default - see the
        # note in run().
        self.card_effects = card_effects
        self.dice_rule = dice_rule
        self.attacker_policy = attacker_policy
        # Variant: a tapped Upgrade still soaks the Tyrant's reply, so tapping
        # costs nothing defensively.
        self.tapped_defends = tapped_defends
        # Proposed structural fixes for the dead tap effects:
        #   "mobility_senses" - a tapped Mobility or Senses Upgrade also
        #                       deals +1 damage, on top of its printed effect
        #   "all"             - every tap deals +1 damage
        #   "free"            - a Rat may tap AND commit Red, so tapping
        #                       carries no opportunity cost at all
        self.tap_bonus = tap_bonus
        # The 7 Tyrant Attack cards are base content and are ON by default.
        # They were unplayable at REC + 1 (under 1%); REC + 2 plus the
        # Terrifying Roar cap makes them land where the ladder wants them.
        self.attack_cards = attack_cards
        # Only 17 dice exist in the box, so the Tyrant's dice MUST be taken
        # out of the Rats' 16 personal dice - there is no separate pool. How
        # many it takes is therefore a real balance lever.
        self.tyrant_pool = tyrant_pool
        # The attacking Rat returns REC + this many of the dice it committed.
        #   "flat"     - REC + battle_rec_bonus; the rule is now +2, raised
        #                from +1 because the Rats bleed 3-4 dice a round out
        #                of a pool that starts at only 8.6
        #   "upgrades" - REC + the number of Upgrades the Rat holds, so the
        #                Splice phase pays for the battle's dice economy
        self.battle_rec_bonus = battle_rec_bonus
        self.battle_rec = battle_rec
        self.rec_rule = rec_rule
        # "off", "either" (Specimens accept either color) or "both"
        # (Specimens need one die of each of their two colors).
        self.color_rule = color_rule
        # "max": commit up to the cap every attack. "conserve": commit only as
        # many as REC + 2 will return, spending no dice permanently.
        self.commit_policy = commit_policy

        # --- NRJ overlay ---
        self.protocol = None
        self.notes = 0
        if module_active("protocol", tier):
            self.protocol = self.rng.choice(PROTOCOLS)
            if TIER1_EXTRA_SPECIMEN:
                self.specimens += 1
            self.tier1_banish = TIER1_BANISH
            if self.protocol == "questionable_procurement":
                self.specimens += 1

        self.rats = [Rat(i) for i in range(4)]
        for i, r in enumerate(self.rats):
            if sides == "random":
                r.side = self.rng.randint(0, 1)
            else:
                r.side = (sides[i] if sides else 0)
        # "Place the Red die on a randomly selected Lab Rat." Only the active
        # Rat may commit Red, and only if it is the Rat holding it.
        # "At setup, randomly select 2 personal dice from different Rats and
        # place them in a common Equipment pool." Those two Rats are a die
        # short all game; the exchange is modeled as the +1 recovery below.
        self.equipment_pool = 0
        if self.protocol == "shared_equipment":
            for donor in self.rng.sample(self.rats, 2):
                if donor.dice:
                    donor.dice.pop()
                    self.equipment_pool += 1
        if TIER2_BANISH and module_active("mods", tier):
            victim = self.rng.choice(self.rats)
            if victim.dice:
                victim.dice.pop()
        if getattr(self, "tier1_banish", False):
            # "At setup, banish 1 non-Red die." A flat handicap that works at
            # every difficulty, unlike an extra Specimen.
            victim = self.rng.choice(self.rats)
            if victim.dice:
                victim.dice.pop()
        self.red_holder = self.rng.choice(self.rats)
        self.red_aside = False
        self.deck = list(range(20))
        self.rng.shuffle(self.deck)
        plain = 16 - (len(MOD_VALUES) if (MODS_REPLACE and module_active("mods", tier)) else 0)
        self.upgrade_deck = [("u", i) for i in
                             self.rng.sample(range(16), plain)]
        # "Shuffle that many RANDOM Specimens in with the 16 regular
        # Upgrades." Taking the first N would mean the last few Specimens
        # never appeared below Nobulous.
        # Specimen count may exceed the 8 printed cards when exploring what a
        # bigger Specimen pool would do. Extras are modelled as further cards
        # of the same profile: Value 5, and +1 Target when revealed.
        _pool = list(range(len(SPECIMEN_NAMES)))
        _picks = self.rng.sample(_pool, min(self.specimens, len(_pool)))
        while len(_picks) < self.specimens:
            _picks.append(self.rng.choice(_pool))
        self.upgrade_deck += [("s", i) for i in _picks]
        if module_active("mods", tier):
            self.upgrade_deck += [("m", i) for i in range(len(MOD_VALUES))]
            for _ in range(TIER2_EXTRA_SPECIMEN):
                pool=[i for i in range(len(SPECIMEN_NAMES))]
                self.upgrade_deck.append(("s", self.rng.choice(pool)))
        self.rng.shuffle(self.upgrade_deck)
        self.notes = 0         # Research Notes claimed and not yet spent
        self.claimed = set()   # which Notes have been claimed
        self.recent = []       # outcomes of the last four Experiments
        self.freeborrow = set()
        self.lender = None
        self.attack_deck = []  # the 7 Tyrant Attack cards, shuffled on use
        self.discard = []      # revealed Upgrades that were not kept
        self.splices = []
        self.splice_mods = 0   # Unauthorized Modifications the Tyrant holds
        self.tyrant_taps = 0
        self.last_destroyed = ()
        self.attack_color = None
        self.health = 20
        self.buff = self.buff_max
        self.experiments = 0
        self.last_active = None
        self.tyrant_dice = []

    # ------------------------------------------------------------------
    # Splice Phase
    # ------------------------------------------------------------------
    def available(self, rat):
        return [d for d in rat.dice if d.zone == "available"]

    def claim_notes(self, rat, success, committed, used_red):
        """Tier III Research Notes are earned, not granted.

        Each prints a claim condition and can be claimed only once. Handing
        the player a flat allowance was the single biggest distortion in the
        BAT tier column, so the conditions are checked as printed. The three
        modeled here are the ones whose conditions this model can actually
        observe; the other three turn on tapping, on zero-dice turns the
        policy never takes, and on a battle-only reward.
        """
        if not module_active("notes", self.tier):
            return
        self.recent.append(success)
        self.recent = self.recent[-4:]

        # Unexpected Resilience: completed without committing Purple or Red.
        if "resilience" not in self.claimed and success and not used_red and \
                not any(d.color == "purple" for d in committed):
            self.claimed.add("resilience")
            self.notes += 1
        # Successful Integration: a single Rat holds 2 Specimens.
        if "integration" not in self.claimed and \
                sum(1 for u in rat.upgrades if u.value == SPECIMEN_VALUE) >= 2:
            self.claimed.add("integration")
            self.notes += 1
        # Acceptable Losses: 3 Experiments failed in the same four-Rat rotation.
        if "losses" not in self.claimed and len(self.recent) == 4 and \
                self.recent.count(False) >= 3:
            self.claimed.add("losses")
            self.notes += 1

    def borrow_for(self, rat):
        """Take the best die the borrower's Upgrade count still allows."""
        allowed = BORROWABLE[min(3, len(rat.upgrades))]
        # Cross-Contamination: "The first time each Rat borrows a die, it may
        # borrow any color regardless of Upgrade count."
        if self.protocol == "cross_contamination" and rat.i not in self.freeborrow:
            self.freeborrow.add(rat.i)
            allowed = BORROWABLE[0]
        pool = [(other, d) for other in self.rats if other is not rat
                for d in self.available(other) if d.color in allowed]
        if not pool:
            return None
        lender, die = max(pool, key=lambda od: EV[od[1].color])
        die.zone = "borrowed"
        self.lender = lender
        return die

    def resolve_borrowed(self, die, rat):
        """"Roll the borrowed die by itself. On a miss it is banished -
        removed from the game permanently. On a hit or Crit it returns to its
        owner exhausted." """
        if die is None:
            return
        banished = roll(die.color, self.rng) == 0
        if banished and rat is not None and rat.ability == "careful_borrower":
            banished = roll(die.color, self.rng) == 0      # one reroll
        die.zone = "banished" if banished else "exhausted"
        lender = self.lender
        if not banished and lender is not None and lender.ability == "tool_keeper":
            die.zone = "available"
        self.lender = None
        if banished and self.protocol == "cross_contamination" and self.upgrade_deck:
            # "If that die is banished, reveal the top Upgrade and Splice it
            # into the Tyrant."
            extra = self.upgrade_deck.pop()
            self.splices.append(Splice(splice_value(extra), splice_cat(extra), splice_effect(extra), splice_colors(extra)))
            if extra[0] == "m":
                self.splice_mods += 1
        if not banished and self.protocol == "independent_funding" and \
                lender is not None and len(lender.upgrades) > len(rat.upgrades):
            # "when a Rat has lent a die to a Rat holding fewer Upgrades, the
            # lender recovers 1 die."
            if INDEP_ON_WIN:
                self.pending_funding = lender   # paid only if the Experiment lands
            else:
                for d in lender.dice:
                    if d.zone == "exhausted":
                        d.zone = "available"
                        break

    def splice_turn(self):
        """Resolve one Experiment. Returns True while the phase continues."""
        if not self.deck:
            return False
        # "Running out of Upgrade cards is not a malfunction - reshuffle the
        # Upgrade discard instead." The discard is every card revealed and not
        # kept, so the Upgrade deck is effectively inexhaustible.
        while len(self.upgrade_deck) < 2:
            self.upgrade_deck += self.discard
            self.discard = []
            if not self.upgrade_deck:
                return False

        target = EXPERIMENT_TARGETS[self.deck.pop()] + TARGET_DELTA
        # Accelerated Trials: Experiments with printed Target 4+ have -1 Target.
        accelerated = self.protocol == "accelerated_trials" and target >= ACCEL_FLOOR
        if accelerated:
            target -= 1
        self.accel_cost = accelerated
        options = [self.upgrade_deck.pop(), self.upgrade_deck.pop()]
        if (self.protocol == "questionable_methodology" and target >= METHODOLOGY_FLOOR
                and len(self.splices) < 4 and self.upgrade_deck):
            # Feed the Tyrant the better Upgrade in exchange for an easier
            # Experiment and a fresh reveal.
            strongest = max(options, key=splice_value)
            self.splices.append(Splice(splice_value(strongest), splice_cat(strongest),
                                       splice_effect(strongest), splice_colors(strongest)))
            options.remove(strongest)
            options.append(self.upgrade_deck.pop())
            target = max(1, target + METHODOLOGY_DELTA)
        if any(kind == "s" for kind, _ in options):
            # Successful Integration can be spent to ignore the +1 Target a
            # revealed Specimen would add.
            if self.notes > 0:
                self.notes -= 1
            else:
                target += 1

        # Policy: pick the Rat with the most dice ready, then the best dice.
        # Redundant Organs blocks its holder from acting twice in a row.
        eligible = [r for r in self.rats if not r.down
                    and not (r is self.last_active and r.has("no_streak"))]
        if not eligible:
            eligible = [r for r in self.rats if not r.down]
        rat = max(
            eligible,
            key=lambda r: (r is self.red_holder and not self.red_aside,
                           len(self.available(r)),
                           sum(EV[d.color] for d in self.available(r))),
        )
        previous = self.last_active
        self.last_active = rat
        if rat.ability == "prepared" and previous is not None and previous is not rat:
            for d in rat.dice:
                if d.zone == "exhausted":
                    d.zone = "available"
                    break
        # Self-Sufficient: forgo borrowing and Red for a Target reduction,
        # but only when this Rat's own dice can cover the lower Target. Taken
        # unconditionally it costs more than the -1 is worth.
        solo_rat = False
        if rat.ability == "self_sufficient":
            own = sum(EV[d.color] for d in self.available(rat))
            if own >= target - 1:
                solo_rat = True
                target = max(1, target - 1)

        # "At the start of the next turn, after the active Rat has been
        # chosen, place the set-aside Red on any non-active Rat." So the turn
        # after Red is used, the active Rat cannot possibly hold it - Red is
        # available every other turn at best, not every turn.
        if self.red_aside:
            others = [r for r in self.rats if r is not rat and not r.down]
            if others:
                self.red_holder = self.rng.choice(others)
            self.red_aside = False
        has_red = self.red_holder is rat

        successes = 0
        committed = []
        rolled = []          # (die, value) so a side can reroll one
        used_red = False
        borrowed = None
        specimen_up = any(kind == "s" for kind, _ in options)
        phases = STR_PHASES + (1 if (rat.ability == "experimental" and specimen_up) else 0)
        for phase in range(phases):
            if successes >= target:
                break
            pool = sorted(self.available(rat), key=lambda d: -EV[d.color])
            if phase == 0:
                take = []
                expected = 0.0
                for d in pool:
                    if expected >= target:
                        break
                    take.append(d)
                    expected += EV[d.color]
                # Secondary Brain forbids its holder the Red die.
                if expected < target and has_red and \
                        not rat.has("no_red") and not solo_rat:
                    used_red = True
                    expected += EV["red"]
                # Still short: borrow one die from another Rat. Extra Limbs
                # forbids its holder from borrowing at all.
                if expected < target and borrowed is None and \
                        not rat.has("no_borrow") and not solo_rat:
                    borrowed = self.borrow_for(rat)
            elif PHASE2_POLICY == "extra_die":
                take = pool[:1]  # second Strategy phase: one more die
            elif PHASE2_POLICY == "push":
                # Rerolling a miss is free: it scored nothing to lose.
                again = [k for k, (d, v) in enumerate(rolled) if v == 0]
                hits = [k for k, (d, v) in enumerate(rolled) if v == 1]
                # Commit further dice alongside them until the throw is
                # expected to cover what is still missing.
                extra = []
                expected = successes + sum(EV[rolled[k][0].color] for k in again)
                for d in [d for d in pool if d.zone == "available"]:
                    if expected >= target:
                        break
                    extra.append(d)
                    expected += EV[d.color]
                # Borrowing is not tied to the first roll either: one die for
                # the whole Experiment, whenever the Rat finds itself short.
                borrow_now = None
                if expected < target and borrowed is None and \
                        not rat.has("no_borrow") and not solo_rat:
                    borrowed = borrow_now = self.borrow_for(rat)
                    if borrow_now is not None:
                        expected += EV[borrow_now.color]
                # A thrown die comes back as at most a Crit. If that ceiling
                # still falls short, trading basic hits is the only way left
                # to find one - worth it only if enough of them get there.
                ceiling = (successes + sum(2 - rolled[k][1] for k in again)
                           + 2 * len(extra) + (2 if borrow_now is not None else 0))
                if ceiling < target:
                    for k in hits:
                        again.append(k)
                        ceiling += 1
                        if ceiling >= target:
                            break
                    else:
                        again = [k for k in again if rolled[k][1] == 0]
                # Everything chosen above goes in the cup together.
                for k in again:
                    die, old_value = rolled[k]
                    fresh = roll(die.color, self.rng)
                    successes += fresh - old_value
                    rolled[k] = (die, fresh)
                for d in extra:
                    value = roll(d.color, self.rng)
                    successes += value
                    rolled.append((d, value))
                    d.zone = "exhausted"
                    committed.append(d)
                if borrow_now is not None:
                    successes += roll(borrow_now.color, self.rng)
                continue
            else:
                # Reroll what was not worth banking. A miss is always worth
                # rerolling; a basic hit only on a die whose EV beats the 1 it
                # already scored, and only while the Target is still short.
                again = [(die, v) for die, v in rolled if v == 0]
                if PHASE2_POLICY == "reroll_unbanked":
                    again += [(die, v) for die, v in rolled
                              if v == 1 and EV[die.color] > 1.0]
                if not again:
                    break
                for die, old_value in again:
                    fresh = roll(die.color, self.rng)
                    successes += fresh - old_value
                    for k, (d2, v2) in enumerate(rolled):
                        if d2 is die:
                            rolled[k] = (die, fresh)
                            break
                continue
            if not take and not used_red:
                break
            for d in take:
                value = roll(d.color, self.rng)
                successes += value
                rolled.append((d, value))
                d.zone = "exhausted"
                committed.append(d)
            if used_red and phase == 0:
                successes += roll("red", self.rng)
                # Red is set aside, not exhausted, and moves to a non-active
                # Rat at the start of the next turn.
                self.red_aside = True
            if borrowed is not None and phase == 0:
                successes += roll(borrowed.color, self.rng)

        # Jury-Rig: reroll one miss. Fine Tuning: reroll a basic hit, keeping
        # the original if the reroll is worse.
        if rat.ability == "jury_rig" and successes < target:
            for d, v in rolled:
                if v == 0:
                    successes += roll(d.color, self.rng)
                    break
        elif rat.ability == "fine_tuning" and successes < target:
            for d, v in rolled:
                if v == 1:
                    successes += max(0, roll(d.color, self.rng) - 1)
                    break

        # The borrowed die is rolled again by itself; a miss banishes it.
        self.resolve_borrowed(borrowed, rat)

        best = max(options, key=splice_value)
        # The card not taken or Spliced is discarded, and the discard is
        # reshuffled when the Upgrade deck runs dry.
        self.discard += [c for c in options if c is not best]
        if successes >= target:
            # Questionable Procurement lets the first Specimen sit outside the
            # 3-Upgrade limit.
            cap = 4 if self.protocol == "questionable_procurement" else 3
            if len(rat.upgrades) < cap:
                rat.upgrades.append(Upgrade(splice_value(best),
                                            splice_effect(best),
                                            splice_name(best),
                                            splice_cat(best)))
                if best[0] == "m":
                    rat.take_mod(best[1])
                if best[0] == "s":
                    rat.specimens += 1
            if accelerated:
                # "After completing one, exhaust 2 of the active Rat's
                # available dice."
                for d in self.available(rat)[:2]:
                    d.zone = "exhausted"
        else:
            self.splices.append(Splice(splice_value(best), splice_cat(best), splice_effect(best), splice_colors(best)))
            if best[0] == "m":
                self.splice_mods += 1

        # Hypermetabolism burns a die every Experiment its holder attempts.
        if rat.has("burn_die"):
            for d in self.available(rat)[:1]:
                d.zone = "exhausted"

        recovery = rat.effective_rec()
        if rat.ability == "experimental" and specimen_up:
            recovery += 1
        if rat.ability == "adaptation" and successes >= target:
            recovery += rat.specimens
        if self.protocol == "shared_equipment" and successes >= target:
            # "After completing an Experiment, the active Rat may exchange one
            # personal die with one Equipment die." The Equipment dice are
            # never exhausted by this Rat's turn, so a completed Experiment
            # effectively buys back one die.
            recovery += 1
        for d in committed[:recovery]:  # Recover equal to REC
            d.zone = "available"
        lender = getattr(self, "pending_funding", None)
        if lender is not None:
            self.pending_funding = None
            if successes >= target:
                for d in lender.dice:
                    if d.zone == "exhausted":
                        d.zone = "available"
                        break
        if getattr(self, "accel_cost", False) and (successes >= target or ACCEL_COST_ALWAYS):
            # Accelerated Trials bills 2 of the active Rat's available dice.
            billed = 0
            for d in rat.dice:
                if billed >= 2:
                    break
                if d.zone == "available":
                    d.zone = "exhausted"
                    billed += 1
        self.claim_notes(rat, successes >= target, committed, used_red)
        self.experiments += 1
        return len(self.splices) < 5

    # ------------------------------------------------------------------
    # Tyrant Battle
    # ------------------------------------------------------------------
    def start_battle(self):
        """Current rules carve the Tyrant's six dice out of the Rats' pool.
        With tyrant_takes_rat_dice=False the Tyrant instead brings its own six,
        which is what the printed rulebook describes."""
        # Each Modification the Tyrant holds may be tapped once in the battle.
        self.tyrant_taps = self.splice_mods
        # Flip one Attack card to supply the Buff HP / Health color.
        self.attack_color = ATTACK_COLORS[self.rng.randrange(ATTACK_COUNT)]
        if not self.tyrant_takes_rat_dice:
            self.tyrant_dice = [Die(c) for c, n in TYRANT_NEED
                                for _ in range(n)][:self.tyrant_pool]
            for r in self.rats:
                for d in r.dice:
                    if d.zone == "exhausted":
                        d.zone = "available"
            self.rng.shuffle(self.splices)
            return
        need = []
        for color, count in TYRANT_NEED:
            need += [color] * count
        need = need[:self.tyrant_pool]
        for color, count in [(c, need.count(c)) for c in
                             sorted(set(need), key=need.index)]:
            alive = [d for r in self.rats for d in r.dice
                     if d.color == color and d.zone not in ("banished", "tyrant")]
            banished = [d for r in self.rats for d in r.dice
                        if d.color == color and d.zone == "banished"]
            for _ in range(count):
                pick = None
                if alive:
                    pick = alive.pop(0)
                elif banished:
                    pick = banished.pop(0)
                if pick is not None:
                    pick.zone = "tyrant"
                    self.tyrant_dice.append(pick)
        # Every surviving personal die joins the shared pool, all available.
        for r in self.rats:
            for d in r.dice:
                if d.zone == "exhausted":
                    d.zone = "available"
        self.rng.shuffle(self.splices)

    def shared_pool(self):
        return [d for r in self.rats for d in r.dice if d.zone == "available"]

    def damage_tyrant(self, dmg):
        """Buff HP, then the five Splices left to right, then Health.
        Anything left over carries straight through to the next card."""
        if self.buff > 0:
            hit = min(self.buff, dmg)
            self.buff -= hit
            dmg -= hit
        for s in self.track():
            if dmg <= 0:
                break
            dmg = s.soak(dmg)
            if not s.alive:
                self.last_destroyed = s.colors   # the Tyrant absorbs it
        if dmg > 0:
            self.health = max(0, self.health - dmg)

    def rat_dice_cap(self, rat):
        """How many dice the attacking Rat may commit.

        "six" is the current rule: up to 6 from the shared pool.

        "highest_upgrade" is the proposed variant - the Rat may commit dice up
        to the Value of its highest Upgrade, tapped or not, with a minimum of
        2 if it holds none. That mirrors the Tyrant's own draw rule and makes
        an Upgrade do double duty: armor, and permission to roll dice.
        """
        if self.dice_rule == "six":
            return 6
        if not rat.upgrades:
            return 2
        return min(6, max(2, max(u.value for u in rat.upgrades)))

    def commit_for_splice(self, cap):
        """Pick up to `cap` dice from the shared pool, honoring the leftmost
        Splice's color requirement when color_rule is on.

        The Rat takes its strongest dice, then - if the requirement is not
        met - swaps its weakest committed die for one of the required color.
        When no die of that color is available it needs a pair of one other
        color instead, which six strong dice almost always already contain.
        Buff HP and the Tyrant's own Health carry no requirement.
        """
        avail = sorted(self.shared_pool(), key=lambda d: -EV[d.color])
        pick = avail[:cap]
        if self.color_rule == "off":
            return pick
        front = self.track()
        if self.color_rule == "attack_only":
            need = [self.attack_color] if self.attack_color else []
            return self._satisfy(pick, avail, need, cap, both=False)
        full = self.color_rule == "both_full"
        by_card = self.color_rule == "both_attack"
        if self.buff > 0:
            # Buff HP: none, or under both_full it shields - and so shares
            # the color of - the Splice directly behind it.
            if by_card:
                need = [self.attack_color]
            elif not (full and front):
                return pick
            else:
                need = list(front[0].colors)
        elif not front:
            # Tyrant Health: none, or under both_full it carries the color
            # of the last Splice destroyed.
            if by_card:
                need = [self.attack_color]
            elif not (full and self.last_destroyed):
                return pick
            else:
                need = list(self.last_destroyed)
        else:
            need = list(front[0].colors)
        if self.color_rule == "either":
            need = [need[0]] if len(need) == 1 else need
        both = self.color_rule in ("both", "both_full", "both_attack")
        return self._satisfy(pick, avail, need, cap, both)

    def _satisfy(self, pick, avail, need, cap, both):
        """Make `pick` meet the color requirement `need`: one die of the
        color, or a same-color pair when none of it is available."""
        if not need:
            return pick
        rest = [d for d in avail if d not in pick]
        colors_needed = need if (both and len(need) > 1) else [None]
        for want in colors_needed:
            wanted = [want] if want else need
            if any(d.color in wanted for d in pick):
                continue
            cand = [d for d in rest if d.color in wanted]
            if cand:
                # swap the weakest committed die for the required color
                if len(pick) >= cap and pick:
                    rest.append(pick.pop())
                chosen = cand[0]
                pick.append(chosen)
                rest.remove(chosen)
            else:
                # none of that color available: need a same-color pair
                counts = {}
                for d in pick:
                    counts[d.color] = counts.get(d.color, 0) + 1
                if not any(n >= 2 for n in counts.values()):
                    for d in rest:
                        if d.color in counts:
                            if len(pick) >= cap and pick:
                                rest.append(pick.pop())
                            pick.append(d)
                            break
        return pick

    def recover_pick(self, rolled, keep):
        """Which committed dice come back to the shared pool.

        Every recovered die returns to the same pool, so with no other rule
        the choice is trivial: take the strongest. The alternatives are
        candidate rules for giving that choice some weight.

          strongest  - the current rule, and the only sensible play under it
          misses     - only dice whose final roll was a MISS come back; dice
                       that scored are spent. Strong dice rarely miss, so
                       committing them becomes a real, lasting cost.
          one_each   - at most one die of each color
          purple_2   - REC is a budget; a Purple die costs 2 of it
        """
        ranked = [d for d, _ in rolled]                  # strongest first
        if self.rec_rule == "misses":
            return [d for d, v in rolled if v == 0][:keep]
        if self.rec_rule == "one_each":
            out, seen = [], set()
            for d in ranked:
                if d.color not in seen and len(out) < keep:
                    out.append(d)
                    seen.add(d.color)
            return out
        if self.rec_rule == "hit_costs_2":
            # REC is a budget: a die that scored costs 2 to recover, a miss
            # costs 1. Spending strong dice is now a choice with a price.
            out, budget = [], keep
            for d, v in rolled:
                cost = 2 if v > 0 else 1
                if cost <= budget:
                    out.append(d)
                    budget -= cost
            return out
        if self.rec_rule == "crit_spent":
            # A die that rolled a Crit is spent this turn and cannot return.
            return [d for d, v in rolled if v < 2][:keep]
        if self.rec_rule == "purple_2":
            out, budget = [], keep
            for d in ranked:
                cost = 2 if d.color == "purple" else 1
                if cost <= budget:
                    out.append(d)
                    budget -= cost
            return out
        return ranked[:keep]

    def front_effect(self):
        """The frontmost surviving Splice's effect, free on every attack."""
        if not self.card_effects:
            return NO_EFFECT
        front = self.track()
        return front[0].effect if front else NO_EFFECT

    def track(self):
        """Surviving Splices, left to right.

        The track is Buff HP, then the five Splices in random order, then the
        Health dial - so damage chews through them in the order they were laid
        down, and the leftmost surviving card is whichever that happens to be.
        Note that rules/bat.html currently words the damage step as "Buff HP
        first, then its Defense Splices, then its remaining Splices, then its
        Health", which reads as sorting Defense to the front; the random
        layout is the intended order.
        """
        return [s for s in self.splices if s.alive]

    def battle_round(self):
        # "Untap. Every Upgrade tapped last round untaps now."
        for r in self.rats:
            for u in r.upgrades:
                u.tapped = False
        standing = [r for r in self.rats if not r.down]
        if not standing:
            return False
        # Under the proposed rule the attacker's dice are gated by its best
        # Upgrade, so the choice of attacker matters: lead with the Rat that
        # can actually roll. Under the current rule every Rat rolls 6, so this
        # falls back to picking the healthiest.
        if self.attacker_policy == "best_roller":
            rat = max(standing, key=lambda r: (self.rat_dice_cap(r), r.hp))
        else:
            rat = max(standing, key=lambda r: (r.hp, self.rat_dice_cap(r)))

        cap = self.rat_dice_cap(rat)
        if self.commit_policy == "conserve":
            # Commit only what will come back, so nothing is lost for good.
            cap = min(cap, rat.effective_rec() + self.battle_rec_bonus)
        pool = self.commit_for_splice(cap)
        if not pool and self.notes > 0:
            # Unexpected Resilience: recover all of that Rat's dice.
            self.notes -= 1
            for d in rat.dice:
                if d.zone == "exhausted":
                    d.zone = "available"
            pool = sorted(self.shared_pool(), key=lambda d: -EV[d.color])[:cap]
        if not pool:
            return False

        rolled = [(d, roll(d.color, self.rng)) for d in pool]
        for i, (d, value) in enumerate(rolled):
            if value == 0:  # STR 2: reroll each miss once
                rolled[i] = (d, roll(d.color, self.rng))
        dmg = sum(v for _, v in rolled)

        # "Either tap one Upgrade or commit Red - not both", and a tapped
        # Upgrade cannot soak the Tyrant's reply.
        #
        # Because the Tyrant destroys at most one Upgrade with no carryover,
        # every untapped Upgrade blocks a whole attack outright. So the last
        # one is never worth tapping - spending it would expose the Rat's
        # Health - and a spare is only worth tapping when its effect beats
        # Red's 1.17 average damage.
        tappable = [u for u in rat.upgrades
                    if not u.tapped] if self.card_effects else []
        tap_soak = 0
        # Three options: tap an Upgrade for damage, tap one for defense, or
        # commit Red for its 1.17 average. Pick whichever is worth most.
        # When a tapped Upgrade still defends, tapping costs nothing, so the
        # Rat will reach for it far more readily; otherwise the last Upgrade
        # is never worth spending, because untapped it blocks a whole attack.
        # Value every way a card can pay, in damage-equivalent terms:
        #   damage added; damage prevented (soaking, or removing the Tyrant's
        #   successes - the same thing from the Rat's side); and dice
        #   recovered, which are worth about a point of damage each since a
        #   die contributes ~1.1 damage and the pool is the real constraint.
        def bonus_for(u):
            if self.tap_bonus == "all":
                return 1
            if self.tap_bonus == "mobility_senses" and u.cat in ("Mobility",
                                                                 "Senses"):
                return 1
            return 0

        options = []
        for u in tappable:
            dmg_v = u.effect[0] + bonus_for(u)
            def_v = u.effect[1] + u.effect[2]
            rec_v = u.effect[4] * EV_REROLL["green"]
            if dmg_v:
                options.append((dmg_v, "dmg", u))
            if def_v:
                options.append((def_v + bonus_for(u), "soak", u))
            if rec_v:
                options.append((rec_v + bonus_for(u), "recover", u))
        spare = self.tapped_defends or len(tappable) > 1
        best = max(options, key=lambda o: o[0]) if options else None
        # Tapping normally forgoes Red, so an effect must beat Red's 1.17
        # average to be worth it. Under "free" there is nothing to forgo, so
        # any positive effect is worth tapping.
        floor = 0 if self.tap_bonus == "free" else EV_REROLL["red"]
        if spare and best is not None and best[0] > floor:
            _, kind, card = best
            card.tapped = True
            if self.tap_bonus == "free":
                dmg += roll("red", self.rng)
            if kind == "dmg":
                dmg += card.effect[0] + bonus_for(card)
            elif kind == "soak":
                tap_soak = card.effect[1] + card.effect[2]
                dmg += bonus_for(card) + roll("red", self.rng)
            else:
                recovered = card.effect[4]
                for r in self.rats:
                    for d in r.dice:
                        if recovered and d.zone == "exhausted":
                            d.zone = "available"
                            recovered -= 1
                dmg += bonus_for(card) + roll("red", self.rng)
        else:
            dmg += roll("red", self.rng)

        # A defensive Splice at the front blunts the Rats' attack. Only the
        # "remove successes" effects are applied here: the rule sits inside
        # the Tyrant's-attack step ("Add the effect of the frontmost Splice in
        # the row"), so the damage-reduction cards are read as applying to the
        # attack being resolved rather than as a standing aura. Reading them
        # as a permanent -1/-3 on every Rat attack drops BAT Standard to 14%,
        # which is not a game anyone shipped.
        # A defensive Splice at the front blunts the Rats' attack while it
        # survives - "Reduce incoming damage by 2", "Remove 1 success from the
        # opponent's next attack". Only the leftmost card's effect applies.
        _, soak, penalty, _, _ = self.front_effect()
        dmg = max(0, dmg - soak - penalty)

        self.damage_tyrant(dmg)
        if self.health <= 0:
            return False

        for d, _ in rolled:
            d.zone = "exhausted"
        if self.battle_rec == "upgrades":
            keep = rat.effective_rec() + len(rat.upgrades)
        elif self.battle_rec == "upgrades_plus":
            keep = rat.effective_rec() + 1 + len(rat.upgrades)
        else:
            keep = rat.effective_rec() + self.battle_rec_bonus
        for d in self.recover_pick(rolled, keep):  # Recover REC + bonus
            d.zone = "available"

        # --- the Tyrant attacks ---
        # "a number of dice equal to the highest Value among the Splices it
        # still holds - 2 if it holds none, never more than its 6". Value is
        # printed, so damage already marked does not reduce the draw.
        live = [s.value for s in self.splices if s.alive]
        draws = min(6, max(2, max(live) if live else 0))
        card = self.draw_attack()
        if card is not None:
            self.attack_color = ATTACK_COLORS[card]

        # Two cards retarget the attack away from the active Rat.
        target = rat
        if card == ADAPTIVE_STRIKE:
            # "This attack deals damage to the next Lab Rat (clockwise, with
            # wrapping)." A knocked-out Rat is set aside, so it is skipped.
            for step in range(1, len(self.rats) + 1):
                nxt = self.rats[(rat.i + step) % len(self.rats)]
                if not nxt.down:
                    target = nxt
                    break
        elif card == PREDATORY_INSTINCT:
            up = [r for r in self.rats if not r.down]
            if up:
                target = max(up, key=lambda r: sum(u.value for u in r.upgrades))

        hits = self.tyrant_dice_damage(draws)
        # And the frontmost Splice attacks for free, every attack.
        bonus, _, _, drain, _ = self.front_effect()
        if hits > 0:
            hits += bonus
        hits = max(0, hits - tap_soak)
        for _ in range(drain):
            live_dice = self.shared_pool()
            if live_dice:
                live_dice[0].zone = "exhausted"

        if card == OVERWHELMING_MASS:
            hits += 3
        elif card == SPLICED_REFLEXES:
            hits += sum(1 for sp in self.splices if sp.alive)
        elif card == TERRIFYING_ROAR:
            # "The Tyrant deals no damage this attack. Instead, exhaust
            # dice from the shared battle pool." Printed as 2 dice; capped at
            # 1, because against a pool that starts at only 8.6 dice a 2-die
            # burn was ending 86% of games on its own.
            hits = 0
            for _ in range(TERRIFYING_ROAR_DICE):
                pool_now = self.shared_pool()
                if pool_now:
                    pool_now[-1].zone = "exhausted"

        self.resolve_attack(target, hits, card)

        # "If the target was not knocked out, the Tyrant immediately attacks
        # again, committing 2 dice. Do not reveal a Tyrant Attack card."
        if card == UNSTABLE_GROWTH and not target.down:
            self.resolve_attack(target, self.tyrant_dice_damage(2))
        return True

    def draw_attack(self):
        """Reveal the top Tyrant Attack card, reshuffling the discard first
        if the deck has run out."""
        if not self.attack_cards:
            return None
        if not self.attack_deck:
            self.attack_deck = list(range(ATTACK_COUNT))
            self.rng.shuffle(self.attack_deck)
        return self.attack_deck.pop()

    def tyrant_dice_damage(self, draws):
        if not self.tyrant_dice:
            return 0
        drawn = self.rng.sample(self.tyrant_dice,
                                min(draws, len(self.tyrant_dice)))
        return sum(roll(d.color, self.rng) for d in drawn)

    def resolve_attack(self, rat, hits, card=None):
        """Land a Tyrant attack on one Rat, honoring its Attack card.

        A Tyrant attack destroys AT MOST ONE of a Rat's Upgrades and carries
        over nothing - if it cannot meet any held Upgrade's Value the Rat
        keeps it, and nothing reaches Health unless the Rat holds none. Two
        Attack cards deliberately break that: Adaptive Strike bypasses an
        Upgrade and carries through to Health, and Crushing Blow sends 1
        damage straight past the armor.

        NOTE rules/bat.html words the baseline the other way ("the rest
        carries on to the next Upgrade... then to Health"), which contradicts
        the intended rule and is worth correcting there.
        """
        if hits <= 0:
            return
        direct = 0
        if card == CRUSHING_BLOW:
            direct = min(1, hits)
            hits -= direct

        armor = ([u for u in rat.upgrades] if self.tapped_defends
                  else [u for u in rat.upgrades if not u.tapped])
        if armor:
            affordable = [u for u in armor if hits >= u.value]
            if affordable:
                lost = min(affordable, key=lambda u: u.value)
                rat.upgrades.remove(lost)
                if rat.mods:
                    rat.drop_mod(lost.value)
            hits = 0                      # no carryover, ever

        hits += direct
        if hits > 0:
            rat.hp -= hits
            if rat.hp <= 0:
                rat.hp = 0
                rat.down = True
                rat.upgrades = []         # knocked out: discard its Upgrades
                rat.mod_ids = []


    def play(self):
        while self.splice_turn():
            pass
        # "Splicing Machine Malfunction. If the Experiment deck runs out
        # first, randomly select enough UNUSED UPGRADE CARDS to bring the
        # Tyrant to exactly 5 Splices." Not Specimens - whatever is left.
        while len(self.splices) < 5:
            if self.upgrade_deck:
                card = self.upgrade_deck.pop(
                    self.rng.randrange(len(self.upgrade_deck)))
            else:
                card = ("u", self.rng.randrange(16))
            self.splices.append(Splice(splice_value(card), splice_cat(card), splice_effect(card), splice_colors(card)))
        self.start_battle()
        for _ in range(500):
            if self.health <= 0:
                return True
            if all(r.down for r in self.rats):
                return False
            if not self.battle_round():
                break
        return self.health <= 0


def run(difficulty="Standard", games=20000, seed=20, tyrant_takes_rat_dice=True,
        tier="none", card_effects=False, dice_rule="six", sides=None,
        attacker_policy="healthiest", tapped_defends=False,
        tap_bonus="none", attack_cards=True, tyrant_pool=6,
        battle_rec_bonus=2, battle_rec="flat", rec_rule="strongest",
        color_rule="attack_only", commit_policy="conserve"):
    """Win rate over `games` complete games.

    card_effects=True turns on the printed tap effects - the Tyrant's
    frontmost Splice firing free on every attack, and the Rats tapping one
    Upgrade per attack instead of committing Red. It is OFF by default, and
    that is a deliberate, uncomfortable choice: with the effects off this
    model reproduces the published ladder almost exactly at Standard (62.9%
    against ~63%), and with them on it collapses to about 16%. One of those
    is wrong and this package cannot tell which. See README.md.
    """
    rng = random.Random(seed)
    wins = 0
    for _ in range(games):
        if Game(difficulty, rng, tyrant_takes_rat_dice, tier,
                card_effects, dice_rule, attacker_policy,
                tapped_defends, tap_bonus, attack_cards, tyrant_pool,
                battle_rec_bonus, battle_rec, rec_rule, color_rule,
                commit_policy, sides=sides).play():
            wins += 1
    return wins / float(games)


if __name__ == "__main__":
    print("%-10s %8s %8s %8s %8s" % ("difficulty", "none", "I", "II", "III"))
    for name in DIFFICULTY:
        row = ["%7.1f%%" % (100 * run(name, 4000, tier=t))
               for t in ("none", "I", "II", "III")]
        print("%-10s %s" % (name, " ".join(row)))
