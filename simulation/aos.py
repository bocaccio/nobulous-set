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

from dice import COLORS, EV, roll

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
LEVELS = {
    "Easy": (5, 3, 0),
    "Standard": (4, 3, 1),
    "Hard": (3, 3, 2),
    "Nobulous": (2, 3, 3),
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

# Backdoor Routines: at most 2 claimed per game. The two modeled are the ones
# whose rewards change an outcome rather than an allocation choice - "treat one
# failed element as successful" and "recover 2 exhausted dice".
BACKDOOR_CLAIMS = 2


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
        self.lim_queue = list(LIMITATIONS)
        self.rng.shuffle(self.lim_queue)

        # --- NRJ overlay ---
        self.intf = None
        self.corrupt = False
        self.backdoors = 0
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

    def allocate(self, targets):
        """Fill each element to its cap.

        Target + 1 is a hard cap in the rules, raised to Target + 2 on up to
        two elements by the Engineer. It used to be a soft threshold you
        could exceed by paying exhausted dice; that penalty fired zero times
        in 266,000 element resolutions across all six Technicians, because
        going past it is never worth the dice, so it became a limit.
        """
        pool = sorted(self.available, key=lambda c: -EV[c])
        plan = [[] for _ in targets]
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
            while pool and len(plan[i]) < cap:
                plan[i].append(pool.pop(0))
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

    def run_program(self, deck, pid, face, slot=None):
        targets = [t + TARGET_DELTA for t in self.targets_for(deck, pid, face)]

        # A Corrupted Limitation withholds 2 dice of a randomly selected
        # color before allocation; they come back once the Program resolves.
        withheld = []
        if not self.lim_queue:
            self.lim_queue = list(LIMITATIONS)
            self.rng.shuffle(self.lim_queue)
        withheld += self.withhold_for(self.lim_queue.pop())
        if self.corrupt and self.rng.random() < CORRUPT_CHANCE:
            color = self.rng.choice(COLORS)
            for _ in range(CORRUPT_WITHHOLD):
                if color in self.available:
                    self.available.remove(color)
                    withheld.append(color)

        if self.tech == "optimize" and targets:
            worst = max(range(len(targets)), key=lambda i: targets[i])
            if targets[worst] > 1:
                targets = list(targets)
                targets[worst] -= 1
        plan = self.allocate(targets)
        rerolls = max(0, self.str_ - 1)
        failed = 0
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

        # Root Access: treat one failed element as successful. Spent to save a
        # Program from Catastrophic Failure, which is the only thing that costs
        # Health.
        if failed >= 2 and self.backdoors > 0:
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
            self.hp -= 1
        elif failed == 0 and deck in PROGRAM_REWARDS:
            self.reward(PROGRAM_REWARDS[deck][pid], slot)
        self.completed += 1
        return failed

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
                    self.queue = [p["id"] for p in active]
                    self.rng.shuffle(self.queue)
                else:
                    break  # into Advanced Programming
            pid = self.queue.pop(0)
            prog = self.programs[pid]
            face = "back" if prog["status"] == "overheated" else "front"
            failed = self.run_program(prog["deck"], prog["pid"], face,
                                      slot=pid)
            if failed > 0:
                if prog["status"] == "stable":
                    prog["status"] = "overheated"
                elif self.intf == "all_overheated":
                    # "cycle it to the bottom of its deck instead of setting
                    # it aside" - the Program keeps coming back.
                    self.queue.append(pid)
                else:
                    prog["status"] = "aside"
        if self.hp <= 0:
            return False
        # "Select 3 Advanced Programs." Eight are shuffled and set aside at
        # setup, but only three are ever faced - running all eight made the
        # finale nearly three times as long as the rules call for.
        adv = self.rng.sample(range(8), 3)
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
