# -*- coding: utf-8 -*-
"""Revised standalone Build-a-Tyrant: the scavenged-Tyrant redesign.

    python3 batrev.py one           # one complete seeded playthrough, named cards
    python3 batrev.py batch [n]     # seeded batch at all four difficulties
    python3 batrev.py assumptions   # the ruling log alone

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
PARTS_AT_SETUP = {"Easy": 10, "Standard": 14, "Hard": 18, "Nobulous": 22}
SPECIMENS_IN_POOL = {"Easy": 5, "Standard": 6, "Hard": 7, "Nobulous": 8}
LEVELS = ("Easy", "Standard", "Hard", "Nobulous")

EXPERIMENTS_DEALT = 8      # six, then a three-card packet with the Wake-Up
WAKEUP_PACKET = 3
TARGET_FLOOR = 1
STR_PHASES = 2
OPENING_RECOVERY = 2       # dice recovered once at the transition
PASS_RECOVERY_BONUS = 2    # a recovery pass pays REC + 2
NO_GRAFT_CAP = 3           # dice cap with no graft revealed
BANISH_ON_BREAK = False    # R19: off for the main run
TYRANT_BAG = ["purple", "purple", "blue", "blue", "green", "yellow"]
ROUND_GUARD = 300          # genuine stalls are reported, not won or lost
COMMIT_MARGIN = 0.0        # extra expected damage the policy wants

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
    __slots__ = ("value", "name", "cat", "card")

    def __init__(self, card):
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
        return [d for r in self.rats if not r.down for d in r.dice]

    def shared_available(self):
        return [d for d in self.all_dice() if d.zone == "available"]

    def shared_exhausted(self):
        return [d for d in self.all_dice() if d.zone == "exhausted"]

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

    def commit_dice(self, cap):
        """Up to `cap` dice honouring the commit colour (one of it, or two of
        one other colour)."""
        avail = pick_order(self.shared_available(), self.rng)
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

    def best_possible(self, cap, graft):
        """Most damage the Rats could roll with what they hold - for the
        'cannot mathematically break it' count."""
        avail = pick_order(self.shared_available(), self.rng)[:cap]
        top = sum(max(FACES[d.color]) for d in avail)
        return top + (GRAFT_DAMAGE.get(graft.name, 0) if graft else 0)

    def battle_round(self):
        self.rounds += 1
        graft = self.graft_pile.pop(0) if self.graft_pile else None
        if graft is None and self.grafts:
            self.graft_pile = [g for g in self.grafts if g is not None]
            self.rng.shuffle(self.graft_pile)
            graft = self.graft_pile.pop(0) if self.graft_pile else None
        splice = self.splices[0]
        rat = self.choose_rat()
        if rat is None:
            return False

        cap = graft.value if graft is not None else NO_GRAFT_CAP
        ceiling = self.best_possible(cap, graft)
        viable = ceiling >= splice.value
        if not viable:
            self.unbreakable += 1

        # Decision policy, visible information only.
        pick = self.commit_dice(cap)
        expect = sum(EV[d.color] for d in pick) \
            + (GRAFT_DAMAGE.get(graft.name, 0) if graft else 0)
        want_pass = (graft is not None
                     and (not viable
                          or expect < splice.value - COMMIT_MARGIN)
                     and len(self.shared_exhausted()) > 0)
        self.say("")
        self.say("Round %d: graft %s [%d] / Splice %s [%d]  (colour %s)",
                 self.rounds, graft.name if graft else "none",
                 cap, splice.name, splice.value, self.attack_color)

        broke = False
        if want_pass:
            self.passes += 1
            if not viable:
                self.forced_passes += 1
            self.say("  RECOVERY PASS (%s): ceiling %d vs Target %d",
                     "no legal break" if not viable else "rational",
                     ceiling, splice.value)
        else:
            dmg = 0
            for d in pick:
                d.zone = "exhausted"
                dmg += roll(d.color, self.rng)
            if graft is not None:
                dmg += GRAFT_DAMAGE.get(graft.name, 0)
            self.say("  commit %d dice -> %d damage vs Target %d",
                     len(pick), dmg, splice.value)
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
        draws = min(splice.value, len(self.bag))
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

        self.apply_attack(target, hits, graft, direct, passed=want_pass)

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

        if all(r.down for r in self.rats):
            return "loss"
        if not self.splices:
            return "win"
        return True

    def apply_attack(self, rat, hits, graft, direct, passed):
        """R15: a revealed graft defends; a Rat is only reached without one."""
        if direct:
            rat.hp -= direct
        if graft is not None:
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
            rat.hp -= hits
            if hits:
                self.say("  no graft: %s takes %d to Health.", rat.name, hits)
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


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "batch"
    if mode == "one":
        lvl = sys.argv[2] if len(sys.argv) > 2 else "Standard"
        one(lvl, int(sys.argv[3]) if len(sys.argv) > 3 else 20)
    elif mode == "assumptions":
        print(__doc__)
    else:
        batch(int(sys.argv[2]) if len(sys.argv) > 2 else 4000)
