"""Does every card actually do something?

    python audit.py            # 1500 games per game
    python audit.py 4000

Every coverage claim in this repository has turned out to be stale at least
once - bat.py said borrowing was unmodelled when it is not, table.py blamed
the Tyrant Attack deck when all seven cards are handled, nap.py still says
Apprentice abilities and per-card Demand penalties are not modelled when
both are. So this measures instead of reading.

For each deck it reports, per card:

    seen    how many games the card turned up in at all
    fired   how many games its printed effect actually did something

A card at 0% seen is unreachable. A card seen often but fired at 0% is
paying rent in the rulebook without doing any work - which is how
Cross-Species Compatibility ("all four Rats hold 2+ Upgrades", never true in
1500 games) and Independent Funding (+0.1 before it was redesigned) were
caught. Both numbers are per GAME, not per draw.

Where a deck's printed text is not modelled at all the report says so rather
than showing a column of zeroes that look like bugs. WHICH DECKS THOSE ARE IS
NOT DECIDED HERE: coverage.py owns that question, derives it from the live
modules on every run, and fails if a claim has gone stale. Run it first - a
firing column means nothing for a card whose effect was never implemented.

This file's own notes were stale twice on 2026-11-06, which is the hazard it
was written to warn about: it said BAT's 20 Experiment effects were not
modelled when 19 are, and that no Final Exam prints an effect when all 12
print a dice restriction. Both are now read from coverage.py instead of
being retyped here.
"""
import collections
import inspect
import random
import sys

import aos
import bat
import finale
import nap

# bat.py names the Attack cards as index constants, not a list.
ATTACK_NAMES = ["Overwhelming Mass", "Adaptive Strike", "Predatory Instinct",
                "Spliced Reflexes", "Terrifying Roar", "Crushing Blow",
                "Unstable Growth"]

# Coverage is coverage.py's job, not a second copy of it here. These are the
# decks this file cannot measure firing for AT ALL, and why - a different
# claim, and one about the instrumentation rather than the models.
NO_FIRING_COLUMN = {
    ("BAT", "Experiments"):
        "19 of the 20 effects are modelled (coverage.py) but they fire "
        "inside one dispatch with no per-card record to read back",
}


def pct(n, d):
    return 100.0 * n / d if d else 0.0


def report(game, deck, total, seen, fired, note=None):
    print()
    print("  %s - %s (%d cards)" % (game, deck, total))
    if note:
        print("    %s" % note)
        return
    dead_seen = [i for i in range(total) if not seen.get(i)]
    dead_fire = [i for i in range(total)
                 if seen.get(i) and not fired.get(i)]
    for i in range(total):
        flag = ""
        if not seen.get(i):
            flag = "   <-- never appears"
        elif fired is not None and not fired.get(i):
            flag = "   <-- never fires"
        print("    %-3d seen %5.0f%%   fired %5.0f%%%s"
              % (i, pct(seen.get(i, 0), GAMES), pct(fired.get(i, 0), GAMES),
                 flag))
    if dead_seen or dead_fire:
        problem("%d never appear, %d never fire",
                len(dead_seen), len(dead_fire))


GAMES = 1500

# THE ONE CLAIM CONDITION THIS MODEL CANNOT REACH, named here so that any
# OTHER card falling under CONDITION_FLOOR is a PROBLEM rather than another
# line of prose. Controlled Failure claims on deliberately committing zero
# dice to an Experiment - throwing it away to bank the Note - which is a
# real line for a player and one no policy in bat.py takes. Priced
# 2026-11-08 at Standard: granted free it is worth -0.5 points, so the
# card is dead twice over and implementing the policy would not pay.
NOTE_DECLARED = {
    "controlled": "committing zero dice, which no policy here takes",
}

# EVERY PROBLEM LINE GOES THROUGH problem(), so the exit code cannot drift
# from what the report says. AGENTS.md groups this file with coverage.py
# under "exit code = stale claims" and it had no exit code at all until
# 2026-11-08: four PROBLEM sites printed into a run that exited 0, so
# nothing in CI could fail on them.
PROBLEMS = []


def problem(line, *args):
    """Print a PROBLEM line and remember that it fired."""
    text = line % args if args else line
    PROBLEMS.append(text)
    print("    PROBLEM: %s" % text)


def audit_bat(games):
    """Experiments drawn, Upgrades/Specimens taken, Attacks revealed,
    Protocols, Modifications held, Research Notes claimed."""
    exp_seen = collections.Counter()
    att_seen = collections.Counter()
    mod_held = collections.Counter()
    note_met = collections.Counter()      # the printed condition fired
    note_held = collections.Counter()     # and grant_note gave you the card
    note_spent = collections.Counter()    # and its one use was spent
    side_seen = collections.Counter()

    real_draw = bat.Game.draw_attack
    real_turn = bat.Game.splice_turn
    real_grant = bat.Game.grant_note
    real_use = bat.Game.use_note

    # grant_note DECLINES - on the claim cap, and on the timing that makes a
    # claim payable - so a condition firing is not a card in hand, and the
    # old column could not tell the two apart. Recorded per game, not per
    # call, because each Note is once per game.
    def grant(self, key):
        real_grant(self, key)
        if self.hold_note(key):
            self._held = getattr(self, "_held", set())
            self._held.add(key)

    def use(self, key):
        got = real_use(self, key)
        if got:
            self._spent = getattr(self, "_spent", set())
            self._spent.add(key)
        return got

    def draw(self):
        c = real_draw(self)
        if c is not None:
            self._att = getattr(self, "_att", set())
            self._att.add(c)
        return c

    def turn(self):
        before = len(self.deck)
        r = real_turn(self)
        if len(self.deck) < before:
            self._exp = getattr(self, "_exp", set())
        return r

    bat.Game.draw_attack = draw
    bat.Game.grant_note = grant
    bat.Game.use_note = use
    try:
        for i in range(games):
            g = bat.Game("Standard", random.Random(i), card_effects=True,
                         sides="random", tier="III")
            g.play()
            for a in getattr(g, "_att", ()):
                att_seen[a] += 1
            for r in g.rats:
                side_seen[bat.RAT_SIDES[r.i][r.side]] += 1
                for m in r.mod_ids:
                    mod_held[m] += 1
            for n in g.claimed:
                note_met[n] += 1
            for n in getattr(g, "_held", ()):
                note_held[n] += 1
            for n in getattr(g, "_spent", ()):
                note_spent[n] += 1
    finally:
        bat.Game.draw_attack = real_draw
        bat.Game.grant_note = real_grant
        bat.Game.use_note = real_use

    print()
    print("  BAT - Tyrant Attacks (%d cards)" % bat.ATTACK_COUNT)
    for i in range(bat.ATTACK_COUNT):
        flag = "   <-- never appears" if not att_seen[i] else ""
        print("    %-22s seen %5.0f%%%s"
              % (ATTACK_NAMES[i][:22], pct(att_seen[i], games), flag))

    print()
    print("  BAT - Unauthorized Modifications (6 cards, Tier II+)")
    for i, (val, drawback) in enumerate(bat.MODS):
        flag = "   <-- never held" if not mod_held[i] else ""
        print("    %-22s held at end %5.0f%%  (Value %d, %s)%s"
              % (bat.MOD_NAMES[i][:22], pct(mod_held[i], games), val,
                 drawback, flag))

    print()
    print("  BAT - Research Notes (6 cards, Tier III)")
    # All six, from bat.NOTE_ORDER, so a seventh card cannot be added
    # without appearing here. This loop used to name five by hand and
    # describe the sixth as unmodelled.
    print("    'met' is how often the printed CONDITION fired, 'held' how")
    print("    often grant_note then gave you the card - it declines past")
    print("    the claim cap and before the claim can be paid for - and")
    print("    'spent' how often the card's one use was taken. The column")
    print("    here read g.claimed and was LABELLED claimed until")
    print("    2026-11-08, so it was the met figure under the held name.")
    for key in bat.NOTE_ORDER:
        m, h = pct(note_met[key], games), pct(note_held[key], games)
        flag = ""
        if m < CONDITION_FLOOR:
            flag = "   <-- UNREACHABLE, met %.1f%%" % m
            if key in NOTE_DECLARED:
                flag = "   <-- DECLARED: %s" % NOTE_DECLARED[key]
        elif not note_held[key]:
            flag = "   <-- met but never held"
        elif not note_spent[key]:
            # HELD AND NEVER SPENT is a card that does nothing, and it is
            # not a PROBLEM here because one card is in that state ON
            # PURPOSE: Unexpected Resilience took its printed timing on
            # 2026-11-06 - "when a Rat has no available dice" - and that
            # almost never arises. bat.RESILIENCE_TRIGGER = "short" is the
            # unrestricted card, priced at 57.9% against 47.9%. A SECOND
            # card arriving here would want reading, not a dial.
            flag = "   <-- held but never spent"
        print("    %-22s met %4.0f%%   held %4.0f%%   spent %4.0f%%%s"
              % (key, m, h, pct(note_spent[key], note_held[key] or 1), flag))
    _cold = [k for k in bat.NOTE_ORDER
             if pct(note_met[k], games) < CONDITION_FLOOR
             and k not in NOTE_DECLARED]
    if _cold:
        problem("%d of 6 Research Notes print a condition the game meets in "
                "under %.0f%% of games: %s.", len(_cold), CONDITION_FLOOR,
                ", ".join(_cold))

    print()
    print("  BAT - Lab Rat sides (8 sides)")
    for row in bat.RAT_SIDES:
        for side in row:
            flag = "   <-- never drawn" if not side_seen[side] else ""
            print("    %-22s drawn %5.0f%%%s"
                  % (side, pct(side_seen[side], games * 4), flag))

    print()
    print("  BAT - Experiments (20 cards)")
    print("    %s" % NO_FIRING_COLUMN[("BAT", "Experiments")])


def audit_nap(games):
    """Which Assignments reach the row, and which get completed.

    A Task that is never drawn is unreachable; one drawn often but never
    completed is a card the player always walks past, which is a different
    kind of dead.
    """
    drawn = collections.Counter()
    done = collections.Counter()
    kinds = {}

    real = nap.Game.reveal

    def reveal(self):
        before = {id(c) for c in self.row}
        r = real(self)
        for c in self.row:
            if id(c) not in before and getattr(c, "index", None) is not None:
                key = (c.kind, c.index)
                kinds[key] = c.kind
                self._drawn = getattr(self, "_drawn", set())
                self._drawn.add(key)
        return r

    nap.Game.reveal = reveal
    try:
        for i in range(games):
            g = nap.Game("Prodigy", "-1", random.Random(i))
            g._completed = set()
            real_done = g.complete if hasattr(g, "complete") else None
            g.play()
            for k in getattr(g, "_drawn", ()):
                drawn[k] += 1
    finally:
        nap.Game.reveal = real

    for kind, total, label in (("task", len(nap.TASKS), "Tasks"),
                               ("setback", len(nap.SETBACKS), "Setbacks"),
                               ("opportunity", 6, "Opportunities")):
        print()
        print("  NAP - %s (%d cards)" % (label, total))
        dead = 0
        for i in range(total):
            n = drawn[(kind, i)]
            flag = "   <-- never drawn" if not n else ""
            if not n:
                dead += 1
            print("    %-3d drawn %5.0f%% of games%s" % (i, pct(n, games), flag))
        if dead:
            problem("%d of %d never drawn", dead, total)

    print()
    print("  NAP - Final Exams (%d cards)" % len(nap.EXAMS))
    # Counted off the live table rather than stated. It read "11 of the 12"
    # for two days after the twelfth went in, which is the whole reason
    # AGENTS.md says to run coverage.py before trusting a sentence like it.
    _done = sum(1 for e in nap.EXAMS if set(e[3]) - set(["crit"]))
    print("    %d of the %d printed restrictions are modelled; exam_commit"
          % (_done, len(nap.EXAMS)))
    print("    and the scoring step honour them when the exam is sat.")
    for subject, dot, base, rule in nap.EXAMS:
        bits = ", ".join("%s=%s" % (k, v) for k, v in sorted(rule.items()))
        print("    %-12s %s  %s" % (subject, dot, bits))

    print()
    print("  NAP - Apprentices (6)")
    # Read from nap.ABILITIES rather than asserted. Prodigy maps to None -
    # its printed ability is the only one not modelled - and Prodigy is the
    # default in nap.run AND the apprentice this file audits NAP with.
    for a in nap.APPRENTICES:
        ability = nap.ABILITIES.get(a)
        print("    %-22s %s"
              % (a, ability if ability else "ability NOT modelled"))
    print("    All six are modelled since 2026-11-06. Prodigy needed the")
    print("    colour rule enforced on SUCCESSES before it had anything to")
    print("    relax - nap.COLOR_RULE_ON_SUCCESS - and until then the")
    print("    default Apprentice here and in nap.run was the one with no")
    print("    ability at all.")


def audit_aos(games):
    """Programs run, and Limitations drawn."""
    progs = collections.Counter()
    lims = collections.Counter()

    real = aos.Game.run_program

    def run(self, deck, pid, face, slot=None):
        self._p = getattr(self, "_p", set())
        self._p.add((deck, pid))
        return real(self, deck, pid, face, slot=slot)

    real_w = aos.Game.withhold_for

    def withhold(self, lim):
        self._l = getattr(self, "_l", set())
        self._l.add(lim)
        return real_w(self, lim)

    aos.Game.run_program = run
    aos.Game.withhold_for = withhold
    try:
        for i in range(games):
            g = aos.Game("Specialized", random.Random(i),
                         composition=aos.LEVELS["Standard"])
            g.play()
            for k in getattr(g, "_p", ()):
                progs[k] += 1
            for k in getattr(g, "_l", ()):
                lims[k] += 1
    finally:
        aos.Game.run_program = real
        aos.Game.withhold_for = real_w

    for deck in aos.DECKS:
        print()
        print("  AoS - %s Programs (8 cards)" % deck)
        dead = 0
        for i in range(8):
            n = progs[(deck, i)]
            if not n:
                dead += 1
            print("    %-3d run %5.0f%% of games%s"
                  % (i, pct(n, games), "   <-- never run" if not n else ""))
        if dead:
            # Read the mix from aos.LEVELS; this used to print the
            # literal "4/3/1", which went stale at the 2026-11-03 retune.
            print("    NOTE: %d of 8 never run at this mix (Standard is"
                  " %d/%d/%d, so whole decks are thinned)"
                  % ((dead,) + tuple(aos.LEVELS["Standard"])))

    print()
    print("  AoS - Limitations (%d cards)" % len(aos.LIMITATIONS))
    for lim in aos.LIMITATIONS:
        n = lims[lim]
        print("    %-22s drawn %5.0f%%%s"
              % (lim, pct(n, games), "   <-- never drawn" if not n else ""))

DEV_NAMES = {
    "free_task": "Borrow the Master's Notes",
    "exam_recover": "Raid the Supply Cabinet",
    "credit": "Extra Credit?",
    "exam_reroll": "Helpful Test Subject",
    "exam_target": "Nobulous Owes You One",
    "exam_ignore": "Definitely Curriculum-Approved",
}
BACKDOOR_NAMES = {
    "diag": "Diagnostic Port", "escalate": "Privilege Escalation",
    "fork": "Resource Fork", "sniff": "Packet Sniffer",
    "garbage": "Garbage Collection", "root": "Root Access",
}
REVERSE = dict((v, k) for k, v in BACKDOOR_NAMES.items())
# A claim condition met in fewer than this many games is not a condition a
# player can play for. Diagnostic Port read 0.2% until 2026-11-07, because
# it asked for no element over-allocated while the best allocation fills
# every element to the Target + 1 cap; the five that worked read 19.6 to
# 71.8%. The floor is set below the lowest of those five with room to spare,
# so it flags a card that has become unreachable rather than one that is
# merely hard.
CONDITION_FLOOR = 5.0


def audit_devious(games):
    """NAP Tier III: is each Devious coupon spent on what its card prints?

    devious_coupons is a LIST OF PAYOUTS, but ignore_setback() and
    move_setback() pop whichever one is on the end. So a coupon earned by
    any of the six can be spent on an ability none of them prints. This
    instruments the list itself - a subclass that records how each coupon
    left the hand - so the off-card spend is a measured number rather than
    a reading of the code.
    """
    earned = collections.Counter()
    printed = collections.Counter()    # removed by name, at an exam
    offcard = collections.Counter()    # popped off the end
    unused = collections.Counter()

    class Recording(list):
        def append(self, item):
            earned[item] += 1
            list.append(self, item)

        def remove(self, item):
            printed[item] += 1
            list.remove(self, item)

        def pop(self, index=-1):
            item = list.pop(self, index)
            offcard[item] += 1
            return item

    real = nap.Game.__init__

    def init(self, apprentice="Prodigy", finf="-1", rng=None, tier="none"):
        real(self, apprentice, finf, rng, tier)
        self.devious_coupons = Recording()

    nap.Game.__init__ = init
    try:
        rng = random.Random(20)
        each = max(100, games // len(nap.APPRENTICES))
        for app in nap.APPRENTICES:
            for _ in range(each):
                g = nap.Game(app, "-1", rng, "III")
                g.play()
                for key in g.devious_coupons:
                    unused[key] += 1
    finally:
        nap.Game.__init__ = real

    print()
    print("  NRJ/NAP - Devious Opportunities (6 cards, Tier III)")
    print("    A coupon is earned by finishing the card, then leaves the")
    print("    hand three ways: spent on what the card PRINTS, popped for")
    print("    the OFF-CARD setback-ignore, or never spent.")
    print("    %-30s %7s %7s %7s %7s"
          % ("", "earned", "printed", "offcard", "unused"))
    for _, key in nap.DEVIOUS:
        e = earned[key]
        if not e:
            # "Extra Credit?" and "Borrow the Master's Notes" pay out the
            # moment they are finished, so they never become a coupon.
            print("    %-30s   pays immediately, never held"
                  % DEV_NAMES[key][:30])
            continue
        flag = ""
        if not printed[key]:
            flag = "   <-- its printed reward NEVER pays"
        print("    %-30s %6d  %6.0f%% %6.0f%% %6.0f%%%s"
              % (DEV_NAMES[key][:30], e, pct(printed[key], e),
                 pct(offcard[key], e), pct(unused[key], e), flag))
    tot, off = sum(earned.values()), sum(offcard.values())
    if tot:
        print("    %d coupons earned, %d (%.0f%%) spent on the off-card"
              % (tot, off, pct(off, tot)))
        print("    setback-ignore - which is printed on none of the six.")


def audit_backdoor(games):
    """AoS Tier III: which Backdoor Routines does a game ever hold?"""
    held = collections.Counter()
    spent = collections.Counter()
    met = collections.Counter()
    rng = random.Random(20)
    each = max(100, games // len(aos.TECHS))
    for tech in aos.TECHS:
        for _ in range(each):
            g = aos.Game("Specialized", rng, "III",
                         composition=aos.LEVELS["Standard"], tech=tech)
            g.play()
            # Read AFTER the game: since 2026-11-06 a Routine is claimed off
            # a Program that met its printed condition, so bkd is empty at
            # setup. `claimed` is the claim log and bkd what is left unspent.
            for key in g.claimed:
                held[key] += 1
                if not g.bkd.get(key):
                    spent[key] += 1
            # And how often the CONDITION was met, claimed or not. `met` is
            # the set of printed conditions this game satisfied.
            for name in g.met:
                met[REVERSE[name]] += 1
    total = each * len(aos.TECHS)

    print()
    print("  NRJ/AoS - Backdoor Routines (6 cards, Tier III)")
    print("    BACKDOOR_CLAIM is %r and BACKDOOR_WHEN %r, cap %d."
          % (aos.BACKDOOR_CLAIM, aos.BACKDOOR_WHEN, aos.BACKDOOR_CLAIMS))
    print("    'met' is how often the printed CONDITION was satisfied and")
    print("    'held' how often a game went on to CLAIM the card. The two")
    print("    differ because claiming costs the next Program Reward, so")
    print("    the policy declines most of what it is offered.")
    print("    Until 2026-11-06 both claims were granted at setup off the")
    print("    front of BACKDOOR_ORDER, so Resource Fork and Garbage")
    print("    Collection read 100% held and the other four read 0%.")
    for key in aos.BACKDOOR_ORDER:
        h = held[key]
        m = pct(met[key], total)
        flag = "   <-- never held" if not h else ""
        if m < CONDITION_FLOOR:
            flag = "   <-- UNREACHABLE, met %.1f%%" % m
        print("    %-28s met %4.0f%%   held %5.0f%%   spent %5.0f%%%s"
              % (BACKDOOR_NAMES[key], m, pct(h, total),
                 pct(spent[key], h) if h else 0, flag))
    cold = [k for k in aos.BACKDOOR_ORDER
            if pct(met[k], total) < CONDITION_FLOOR]
    if cold:
        # THE DISTINCTION THIS COLUMN EXISTS FOR. A card the policy declines
        # is a design question; a card whose CONDITION the game never meets
        # is a broken card, and the two look identical in the held column.
        problem("%d of 6 print a condition the game meets in under %.0f%% "
                "of games: %s.", len(cold), CONDITION_FLOOR,
                ", ".join(BACKDOOR_NAMES[k] for k in cold))
        print("    That is not the policy declining them - it is the card")
        print("    asking for something the game's own best play never does.")
    dead = [k for k in aos.BACKDOOR_ORDER if not held[k]]
    if dead and aos.BACKDOOR_WHEN == "always":
        # Under "always" the policy claims whatever a condition offers, so a
        # card that is never held is a card the model cannot reach - a bug.
        problem("%d of 6 cannot be claimed at all.", len(dead))
    elif dead:
        # Under "value" it is a DECLINE, which is a different thing and not
        # a model fault: claiming costs the next Program Reward and these
        # four are worth less than one. The `met` column above is what makes
        # that a measurement rather than a hope - this used to say "set
        # BACKDOOR_WHEN = 'always' and all six are claimed, which is the
        # check that they are reachable", and that sentence was FALSE for
        # Diagnostic Port, whose condition was met in 0.2% of games. The
        # audit had no column that would have shown it.
        print("    %d of 6 are never claimed at BACKDOOR_WHEN = %r: %s."
              % (len(dead), aos.BACKDOOR_WHEN,
                 ", ".join(BACKDOOR_NAMES[k] for k in dead)))
        print("    That is the policy DECLINING them, not the model failing")
        print("    to reach them - claiming gives up the next Program")
        print("    Reward and these are worth less than one. The spread is")
        print("    a design question and is raised in RESULTS.txt.")


def audit_interference(games):
    """AoS Tier I: every game draws one of six, so each should be ~1 in 6."""
    drawn = collections.Counter()
    rng = random.Random(20)
    each = max(100, games // len(aos.TECHS))
    for tech in aos.TECHS:
        for _ in range(each):
            g = aos.Game("Specialized", rng, "I",
                         composition=aos.LEVELS["Standard"], tech=tech)
            g.play()
            if g.intf:
                drawn[g.intf] += 1
    total = each * len(aos.TECHS)
    print()
    print("  NRJ/AoS - Nobulous Interference (6 cards, Tier I)")
    for key in aos.INTERFERENCE:
        flag = "   <-- never drawn" if not drawn[key] else ""
        print("    %-28s drawn %5.0f%%%s"
              % (key, pct(drawn[key], total), flag))
    # Corrupted Limitations, measured since 2026-11-06. Until then this was
    # the one deck in the set the model never drew, so there was nothing
    # here to count and this section was a sentence of prose.
    corrupt = collections.Counter()
    rng = random.Random(20)
    for tech in aos.TECHS:
        for _ in range(each):
            g = aos.Game("Specialized", rng, "II",
                         composition=aos.LEVELS["Standard"], tech=tech)
            real = g.corrupt_plan

            def seen(plan, targets, locked, _g=g, _real=real):
                corrupt[_g.corrupt_card] += 1
                return _real(plan, targets, locked)
            g.corrupt_plan = seen
            g.play()
    drawn_total = sum(corrupt.values()) or 1
    print()
    print("  NRJ/AoS - Corrupted Limitations (6 cards, Tier II)")
    print("    %d drawn over %d games; each should be about 1 in 6."
          % (drawn_total, total))
    for key in aos.CORRUPTED:
        flag = "   <-- never drawn" if not corrupt[key] else ""
        print("    %-28s %5.1f%% of draws%s"
              % (key, pct(corrupt[key], drawn_total), flag))

    print()
    print("  NRJ - Imposters (5 cards, 10 sides)")
    print("    Ported into finale.py from proto/imposters.py on 2026-11-06.")
    print("    HERO = None is still the pitch, so a side is measured as a")
    print("    DELTA against it - see finale.py section 7 for the roster.")
    for h in finale.HEROES:
        who, side, when = finale.HERO_TEXT[h]
        fires = ('hero == "%s"' % h) in inspect.getsource(finale)
        print("    %-22s %-18s %-14s %s"
              % (who, side, when, "modelled" if fires else "NOT MODELLED"))


def audit_protocols(games):
    """BAT Tier I: one of six at setup. What each is WORTH is in RESULTS.txt;
    this only checks that all six reach the table."""
    drawn = collections.Counter()
    for i in range(games):
        g = bat.Game("Standard", random.Random(i), card_effects=True,
                     sides="random", tier="I")
        g.play()
        if g.protocol:
            drawn[g.protocol] += 1
    print()
    print("  NRJ/BAT - Experimental Protocols (6 cards, Tier I)")
    for key in bat.PROTOCOLS:
        flag = "   <-- never drawn" if not drawn[key] else ""
        print("    %-28s drawn %5.0f%%%s"
              % (key, pct(drawn[key], games), flag))


def main(games=GAMES):
    global GAMES
    GAMES = games
    print("CARD AUDIT - does every card do something? %d games per deck."
          % games)
    print("Percentages are per GAME: 'seen' means the card turned up at all.")
    audit_bat(games)
    audit_nap(games)
    audit_aos(games)
    # The NRJ tier decks. Added 2026-11-06: until then this file audited the
    # three base games and none of the nine overlay decks - which is where
    # all three of the fungible-token defects lived.
    audit_protocols(games)
    audit_devious(games)
    audit_interference(games)
    audit_backdoor(games)
    print()
    print("Printed-effect coverage is coverage.py, not this file. Run it too:")
    print("  python coverage.py")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else GAMES)
    # The exit code AGENTS.md says this file has. 0 PROBLEM lines at 1500 and
    # at 6000 games on 2026-11-08, so this is not a dial being turned on over
    # a known failure - it is a report that had no way to fail.
    if PROBLEMS:
        print()
        print("%d PROBLEM(s) above." % len(PROBLEMS))
    sys.exit(1 if PROBLEMS else 0)
