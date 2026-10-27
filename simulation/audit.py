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

Where a deck's printed text is not modelled at all - BAT's 20 Experiment
effects, for instance, where only the Target is used - the report says so
rather than showing a column of zeroes that look like bugs.
"""
import collections
import random
import sys

import aos
import bat
import nap

# bat.py names the Attack cards as index constants, not a list.
ATTACK_NAMES = ["Overwhelming Mass", "Adaptive Strike", "Predatory Instinct",
                "Spliced Reflexes", "Terrifying Roar", "Crushing Blow",
                "Unstable Growth"]

UNMODELLED = {
    ("BAT", "Experiments"):
        "only the printed Target is used; the 20 effect texts are not modelled",
    ("NAP", "Final Exams"):
        "subject, dot and Target are used; no exam prints an effect",
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
        print("    PROBLEM: %d never appear, %d never fire"
              % (len(dead_seen), len(dead_fire)))


GAMES = 1500


def audit_bat(games):
    """Experiments drawn, Upgrades/Specimens taken, Attacks revealed,
    Protocols, Modifications held, Research Notes claimed."""
    exp_seen = collections.Counter()
    att_seen = collections.Counter()
    mod_held = collections.Counter()
    note_claim = collections.Counter()
    side_seen = collections.Counter()

    real_draw = bat.Game.draw_attack
    real_turn = bat.Game.splice_turn

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
                note_claim[n] += 1
    finally:
        bat.Game.draw_attack = real_draw

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
    for key in ("resilience", "integration", "losses", "compatibility",
                "red_means_go"):
        flag = "   <-- never claimed" if not note_claim[key] else ""
        print("    %-22s claimed %5.0f%%%s"
              % (key, pct(note_claim[key], games), flag))
    print("    %-22s not modelled (needs a deliberate zero-dice turn)"
          % "controlled_failure")

    print()
    print("  BAT - Lab Rat sides (8 sides)")
    for row in bat.RAT_SIDES:
        for side in row:
            flag = "   <-- never drawn" if not side_seen[side] else ""
            print("    %-22s drawn %5.0f%%%s"
                  % (side, pct(side_seen[side], games * 4), flag))

    print()
    print("  BAT - Experiments (20 cards)")
    print("    only the printed Target is used; the 20 effect texts are not")
    print("    modelled, so there is nothing to measure firing against")


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
            print("    PROBLEM: %d of %d never drawn" % (dead, total))

    print()
    print("  NAP - Final Exams (%d cards)" % len(nap.EXAMS))
    print("    subject, recovery dot and Target are used; no exam prints an")
    print("    effect, so there is no firing to measure")

    print()
    print("  NAP - Apprentices (6)")
    for a in nap.APPRENTICES:
        print("    %-22s ability modelled" % a)


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
            print("    NOTE: %d of 8 never run at this mix (Standard is 4/3/1,"
                  " so whole decks are thinned)" % dead)

    print()
    print("  AoS - Limitations (%d cards)" % len(aos.LIMITATIONS))
    for lim in aos.LIMITATIONS:
        n = lims[lim]
        print("    %-22s drawn %5.0f%%%s"
              % (lim, pct(n, games), "   <-- never drawn" if not n else ""))


def main(games=GAMES):
    global GAMES
    GAMES = games
    print("CARD AUDIT - does every card do something? %d games per deck."
          % games)
    print("Percentages are per GAME: 'seen' means the card turned up at all.")
    audit_bat(games)
    audit_nap(games)
    audit_aos(games)


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else GAMES)
