"""THE SPECIAL RECOVERY AGE RULE, RE-PEGGED. Measured 2026-11-25, at Jon's ask.

napcommit.py ended on a cliff. Jon's own diagnosis of why a NAP Standard can
be won on the last die and still never ask for a hard decision -

    "I know I will get back all purple at the end of afternoon.
     Let me roll them all now."

- is right, and the fix measured there is too strong. The Primary's dot names
the NEXT slot's Special Recovery colour, so a queued colour is one you may as
well spend to the floor: the dice stop being a cost and become a loan already
granted. Making the recovery reach only dice that were already exhausted when
the slot began takes the certainty away without touching the SIZE of the
refill - and costs 17 points at Standard, which puts Easy below where
Standard should sit.

This file does the re-peg. Five things are measured:

  1. THE AGE RULE AS A KNOB, not a switch. SPECIAL_RECOVERY_AGE_ALLOW hands
     back N of the dice you spent during the slot, and
     SPECIAL_RECOVERY_AGE_SLOTS applies the rule to some Time Slots and not
     others. Both are new, both default to the hard reading napcommit.py
     measured, so that file still reproduces.

  2. WHAT PAYS FOR IT. The age rule takes dice INCOME away, so the first
     place to look is the other income: REC, which is 2 on all six
     Apprentice cards.

  3. THE TWO EXAM QUESTIONS Jon settled the same day - what "must
     contribute" means, and what an exam restriction the dice pool cannot
     answer costs. The second is not the corner case it looks like, which is
     why it is measured here rather than written straight into the rulebook.

  4. THE LADDER. Three candidate pitches, each at every NRJ tier, against
     the shipped one. Both ladder dials were already at their soft end on
     today's Easy rung - 4 Credits, 1 Setback - so the surface is swept down
     to a 3-Credit goal and a Setback-free deck to see what lies below it.

  5. THE DICE ECONOMY ITSELF, because a win rate cannot answer "it never
     asked for a hard decision". How many dice the player is choosing
     between when a Time Slot's work begins, how often that number is
     small, and how big the refill is - which is the claim the rule rests
     on: that it changes WHEN the dice come back and not HOW MANY.

  6. WHETHER THE RULE RE-PRICES THE TWO THINGS THAT FELT LIKE DECORATION -
     the Apprentice abilities, worth +1.0 to +3.2 at Standard, and FINF
     Reduce, worth about a point a card. Both are dice-timing effects, and
     the age rule is a dice-timing rule.

NOTHING HERE CHANGES A PRINTED RULE. Every dial defaults to the shipped
reading; this file sets them, measures, and puts them back.

    cd simulation && python napage.py > napage.txt
"""
import collections
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nap

LEVELS = ("Easy", "Standard", "Hard", "Nobulous")
APPS = ["Prodigy", "Slacker", "Technician", "Savant", "Opportunist", "Lab Rat"]
PUBLISHED = (58.1, 49.0, 37.0, 26.3)
# BAT's ladder, the one in the set pegged against the 20 Strong community
# band deliberately, and the house style to aim at.
HOUSE = (63.7, 52.8, 37.8, 25.8)
GAMES = 3000        # per Apprentice on a four-rung row
LADDER_GAMES = 2000  # per Apprentice per tier on the candidate ladders
GRID_GAMES = 2500   # per cell on the Prodigy-only difficulty surface

AGE = dict(SPECIAL_RECOVERY_AGE=True)
# The package the re-peg is measured under: the age rule in full, a third
# die at End of Day to pay for it, and "must contribute" read as the card
# prints it.
PACKAGE = dict(SPECIAL_RECOVERY_AGE=True, REC_START=3, EXAM_NEED="success")
# ...and the softer rule that needs no ladder change at all: one die of what
# you spent this slot still comes back.
SOFT = dict(PACKAGE, SPECIAL_RECOVERY_AGE_ALLOW=1)

L = dict
CANDIDATES = [
    ("A  goals one lower, Setbacks as printed", PACKAGE,
     L(Easy=(3, 1), Standard=(4, 2), Hard=(5, 3), Nobulous=(6, 4))),
    ("B  one die of this slot back, ladder as printed", SOFT,
     L(Easy=(4, 1), Standard=(5, 2), Hard=(6, 3), Nobulous=(7, 4))),
    ("C  Setbacks one lower, goals as printed", PACKAGE,
     L(Easy=(4, 0), Standard=(5, 1), Hard=(6, 2), Nobulous=(7, 3))),
]
GOALS = (3, 4, 5, 6, 7)
SETBACKS = (0, 1, 2, 3, 4)


def dial(**dials):
    old = dict((k, getattr(nap, k)) for k in dials)
    for k, v in dials.items():
        setattr(nap, k, v)
    return old


def restore(old, keep):
    for k, v in old.items():
        setattr(nap, k, v)
    nap.CREDITS_TO_LEAVE, nap.SETBACKS_IN_DECK = keep


def ladder(levels=None, games=None, tier="none", **dials):
    """A four-rung row, the six Apprentices averaged."""
    games = GAMES if games is None else games
    old, keep = dial(**dials), (nap.CREDITS_TO_LEAVE, nap.SETBACKS_IN_DECK)
    try:
        out = []
        for name in LEVELS:
            nap.CREDITS_TO_LEAVE, nap.SETBACKS_IN_DECK = (
                levels or nap.LEVELS)[name]
            out.append(100.0 * sum(nap.run(a, "-1", games, tier=tier)
                                   for a in APPS) / len(APPS))
        return out
    finally:
        restore(old, keep)


def standard(**dials):
    """The Standard rung alone, 5 Credits and 2 Setbacks."""
    old, keep = dial(**dials), (nap.CREDITS_TO_LEAVE, nap.SETBACKS_IN_DECK)
    nap.CREDITS_TO_LEAVE, nap.SETBACKS_IN_DECK = nap.LEVELS["Standard"]
    try:
        return 100.0 * sum(nap.run(a, "-1", GAMES, tier="none")
                           for a in APPS) / len(APPS)
    finally:
        restore(old, keep)


def one(goal, sb, **dials):
    old, keep = dial(**dials), (nap.CREDITS_TO_LEAVE, nap.SETBACKS_IN_DECK)
    nap.CREDITS_TO_LEAVE, nap.SETBACKS_IN_DECK = goal, sb
    try:
        return 100.0 * nap.run("Prodigy", "-1", GRID_GAMES, seed=20,
                               tier="none")
    finally:
        restore(old, keep)


W = 44


def head():
    print("%-*s %8s %8s %8s %8s   %s" % ((W, "") + LEVELS + ("vs shipped",)))


def row(label, cells, base=None):
    line = "%-*s %s" % (W, label, " ".join("%7.1f%%" % x for x in cells))
    if base:
        line += "   " + " ".join("%+5.1f" % (cells[i] - base[i])
                                 for i in range(len(cells)))
    print(line)


def rung(label, value, base=None):
    line = "%-*s %6.1f%%" % (W, label, value)
    if base is not None:
        line += "   %+5.1f" % (value - base)
    print(line)


# ----------------------------------------------------------------------
def section_knob():
    print("1. THE AGE RULE IS A KNOB. At the Standard rung, 5 Credits and")
    print("   2 Setbacks, six Apprentices averaged, %d games each." % GAMES)
    print()
    base = standard()
    rung("as shipped - no age rule", base)
    print()
    print("   AN ALLOWANCE: '...plus up to N of the dice you spent this")
    print("   slot'. 4 is the whole of a colour, so it is the printed rule")
    print("   back, and that it lands on the shipped figure is the check")
    print("   that both ends are the same rule.")
    for allow in (0, 1, 2, 3, 4, "half"):
        rung("   allowance %s, every slot" % allow,
             standard(**dict(AGE, SPECIAL_RECOVERY_AGE_ALLOW=allow)), base)
    print()
    print("   OR THE RULE ON SOME TIME SLOTS ONLY, no allowance.")
    for slots, name in (((0,), "Morning only"), ((1,), "Afternoon only"),
                        ((2,), "Evening only"), ((1, 2), "all but Morning"),
                        ((0, 1), "all but Evening")):
        rung("   %s" % name,
             standard(**dict(AGE, SPECIAL_RECOVERY_AGE_SLOTS=slots)), base)
    print()
    print("   The allowance is the dial that behaves - it runs smoothly from")
    print("   the hard rule back to the printed one. Slot subsets are not a")
    print("   softener of the same kind: Morning is the recovery the Day has")
    print("   already paid for, so exempting it changes almost nothing while")
    print("   exempting the other two leaves the exploit exactly where Jon")
    print("   found it, at the end of the Afternoon.")
    return base


def section_pay(base):
    print()
    print("2. WHAT PAYS FOR IT. The rule takes dice income away, so look at")
    print("   the other income first. REC and STR are 2 on all six")
    print("   Apprentice cards and so is HP. Same rung, same games, the hard")
    print("   age rule on throughout.")
    print()
    rung("age rule, nothing paid back", standard(**AGE), base)
    for d, label in ((dict(REC_START=3), "REC 3, a third die each End of Day"),
                     (dict(REC_START=4), "REC 4"),
                     (dict(STR_START=3), "STR 3, a third Strategy roll"),
                     (dict(HP_START=3), "HP 3"),
                     (dict(REC_START=3, STR_START=3), "REC 3 and STR 3")):
        rung("   ...and " + label, standard(**dict(AGE, **d)), base)
    print()
    print("   REC fits the hole the rule makes. +1 REC is worth about what")
    print("   the age rule costs, and it buys dice back WITHOUT buying the")
    print("   certainty back: an End of Day recovery is one choice of")
    print("   colours a day, not a colour you can see coming and dump into.")
    print("   STR 3 costs nearly as much and does hand the certainty back,")
    print("   because a spare Strategy roll is what the dumped dice are")
    print("   spent on; HP 3 pays at the exams, which is not where the")
    print("   decision was missing.")


def exam_census(games=2000):
    """How often can the dice pool not answer an exam's restriction?"""
    real = nap.exam_commit
    tally, pool = collections.Counter(), collections.Counter()

    def spy(available, target, rule, rng):
        used, waived = real(available, target, rule, rng)
        tally["sittings"] += 1
        pool[min(len(available), 9)] += 1
        for kind in ("need", "among", "colors", "dice"):
            has = (bool(rule.get("among", (0, ()))[0]) if kind == "among"
                   else bool(rule.get(kind)))
            if not has:
                continue
            tally[kind + " printed"] += 1
            if any(w.startswith(kind) for w in waived):
                tally[kind + " UNMEETABLE"] += 1
        if any(w.startswith(("need", "among")) for w in waived):
            tally["a CONTRIBUTE clause unmeetable"] += 1
        if waived:
            tally["any clause unmeetable"] += 1
        return used, waived

    nap.exam_commit = spy
    try:
        for app in APPS:
            nap.run(app, "-1", games, tier="none")
    finally:
        nap.exam_commit = real
    return tally, pool


def section_exams(base_l):
    print()
    print("3. THE TWO EXAM QUESTIONS, settled 2026-11-25. Fine Motor")
    print("   Assessment prints 'At least 1 Yellow and 1 Blue die must")
    print("   contribute' and Jon sat it holding no Blue. The three owners")
    print("   disagreed: the lab BLOCKS the roll and offers no way on, this")
    print("   model added nothing and scored the exam free, the mod printed")
    print("   a reminder. Jon's answers were that contribute means SUCCEED,")
    print("   and that a restriction the pool cannot answer is waived for")
    print("   1 Health.")
    print()
    head()
    row("AS SHIPPED - commit only, waived free", base_l)
    row("contribute = SUCCEED, unmet scores nothing",
        ladder(EXAM_NEED="success"), base_l)
    row("...unmet costs 1 Health, successes stand",
        ladder(EXAM_NEED="success_soft"), base_l)
    row("waiver 1 Health, contribute clauses only",
        ladder(EXAM_WAIVER_COST=1), base_l)
    row("waiver 1 Health, every clause",
        ladder(EXAM_WAIVER_COST=1, EXAM_WAIVER_SCOPE="all"), base_l)
    print()
    print("   SUCCEED IS CHEAP AND THE WAIVER IS NOT, and one fact about")
    print("   NAP explains both: you arrive at the exams having spent nearly")
    print("   everything, so the pool usually cannot answer the card at all.")
    print()
    tally, pool = exam_census()
    n = float(tally["sittings"])
    print("   %d exam sittings, six Apprentices:" % tally["sittings"])
    for key in ("need printed", "need UNMEETABLE", "among printed",
                "among UNMEETABLE", "colors printed", "colors UNMEETABLE",
                "dice printed", "dice UNMEETABLE",
                "a CONTRIBUTE clause unmeetable", "any clause unmeetable"):
        if key in tally:
            print("     %-34s %5.1f%%" % (key, 100.0 * tally[key] / n))
    print("   dice available as an exam begins:")
    print("     " + "  ".join(
        "%s%d: %.0f%%" % ("9+" if k == 9 else "", k, 100.0 * v / n)
        for k, v in sorted(pool.items())))
    print()
    print("   So a restriction you cannot meet is the exam's ORDINARY")
    print("   resolution, not a dead end: a colour clause is printed on a")
    print("   quarter of all sittings and unmeetable in over half of those.")
    print("   A Health each time, against a starting 2, costs more than a")
    print("   rung of the ladder does - and the dead end Jon hit is already")
    print("   answered by waiving it, which is what this model has always")
    print("   done. The price is the part to decide; the waiver itself is")
    print("   not in question.")


def surface(label, **dials):
    print("   %s (Prodigy, %d games a cell)" % (label, GRID_GAMES))
    print("   %-5s" % "goal" + "".join("%9s" % ("%d sb" % s)
                                       for s in SETBACKS))
    for g in GOALS:
        print("   %-5d" % g
              + "".join("%8.1f%%" % one(g, s, **dials) for s in SETBACKS))


def section_repeg(base_l):
    print()
    print("4. THE LADDER. The package is the age rule in full, REC 3 to pay")
    print("   for it, and contribute = succeed.")
    print()
    head()
    row("AS SHIPPED", base_l)
    row("published, 20k games", PUBLISHED)
    row("BAT, the ladder pegged deliberately", HOUSE)
    row("the package on the SHIPPED rungs", ladder(**PACKAGE), base_l)
    print()
    surface("the surface under the package", **PACKAGE)
    print()
    surface("...and the same cells as shipped", **{})
    print()
    print("   THE THREE CANDIDATES, %d games an Apprentice a tier, six"
          % LADDER_GAMES)
    print("   Apprentices averaged.")
    print()
    print("   %-24s" % "" + "".join("%10s" % ("tier " + t)
                                    for t in ("0", "I", "II", "III")))
    for name, dials, levels in (
            ("SHIPPED", {}, nap.LEVELS),) + tuple(CANDIDATES):
        print("   " + name)
        cols = [ladder(levels=levels, games=LADDER_GAMES, tier=t, **dials)
                for t in ("none", "I", "II", "III")]
        for i, level in enumerate(LEVELS):
            goal, sb = levels[level]
            print("     %-22s" % ("%-9s %d Cr / %d sb" % (level, goal, sb))
                  + "".join("%9.1f%%" % col[i] for col in cols))
        steps = [cols[0][i] - cols[0][i + 1] for i in range(3)]
        print("     %-22s" % "solo steps"
              + "   %s" % "  ".join("%.1f" % s for s in steps))


def ability_worth(levels, **dials):
    """Each Apprentice with and without its own printed ability."""
    out = []
    old, keep = dial(**dials), (nap.CREDITS_TO_LEAVE, nap.SETBACKS_IN_DECK)
    nap.CREDITS_TO_LEAVE, nap.SETBACKS_IN_DECK = levels["Standard"]
    try:
        for app in APPS:
            with_it = 100.0 * nap.run(app, "-1", GAMES, tier="none")
            was = nap.ABILITIES[app]
            nap.ABILITIES[app] = None
            try:
                without = 100.0 * nap.run(app, "-1", GAMES, tier="none")
            finally:
                nap.ABILITIES[app] = was
            out.append((app, with_it, with_it - without))
    finally:
        restore(old, keep)
    return dict((a, (w, d)) for a, w, d in out)


def finf_worth(levels, **dials):
    old, keep = dial(**dials), (nap.CREDITS_TO_LEAVE, nap.SETBACKS_IN_DECK)
    nap.CREDITS_TO_LEAVE, nap.SETBACKS_IN_DECK = levels["Standard"]
    try:
        return dict(
            (s, 100.0 * sum(nap.run(a, s, GAMES, tier="none")
                            for a in APPS) / len(APPS))
            for s in ("-1", "-2", "-3", "+1", "+2", "+3"))
    finally:
        restore(old, keep)


def economy(levels, games=1200, **dials):
    """The pool the player is actually choosing from, slot by slot."""
    pool, refill, slots = [], [], collections.Counter()
    real_work, real_rc = nap.Game.work, nap.Game.recover_color

    def work(self):
        pool.append(len(self.available))
        return real_work(self)

    def recover_color(self, color, limit=None):
        before = len(self.available)
        real_rc(self, color, limit=limit)
        refill.append(len(self.available) - before)

    old, keep = dial(**dials), (nap.CREDITS_TO_LEAVE, nap.SETBACKS_IN_DECK)
    nap.CREDITS_TO_LEAVE, nap.SETBACKS_IN_DECK = levels["Standard"]
    nap.Game.work, nap.Game.recover_color = work, recover_color
    try:
        for app in APPS:
            nap.run(app, "-1", games, tier="none")
    finally:
        nap.Game.work, nap.Game.recover_color = real_work, real_rc
        restore(old, keep)
    n = float(len(pool))
    slots["mean"] = sum(pool) / n
    slots["tight"] = 100.0 * sum(1 for x in pool if x <= 3) / n
    slots["starved"] = 100.0 * sum(1 for x in pool if x <= 1) / n
    slots["flush"] = 100.0 * sum(1 for x in pool if x >= 8) / n
    slots["slots"] = n / (len(APPS) * games)
    slots["refill"] = sum(refill) / float(len(refill))
    return slots


def section_economy():
    print()
    print("5. THE DICE ECONOMY, which is the part a win rate cannot answer.")
    print("   Measured at each ladder's own Standard rung: the pool in front")
    print("   of the player when a Time Slot's work begins, and the size of")
    print("   the Special Recovery that filled it.")
    print()
    print("   %-30s %7s %7s %7s %7s %7s %7s"
          % ("", "dice", "<=3", "<=1", ">=8", "slots", "refill"))
    rows = [("as shipped, 5 Cr / 2 sb", nap.LEVELS, {})]
    for name, dials, levels in CANDIDATES:
        goal, sb = levels["Standard"]
        rows.append(("%s, %d Cr / %d sb" % (name.split()[0], goal, sb),
                     levels, dials))
    for label, levels, dials in rows:
        s = economy(levels, **dials)
        print("   %-30s %6.2f %6.1f%% %6.1f%% %6.1f%% %6.2f %6.2f"
              % (label[:30], s["mean"], s["tight"], s["starved"],
                 s["flush"], s["slots"], s["refill"]))
    print()
    print("   THE REFILL COLUMN IS WHERE THIS DIFFERS FROM A CAP. A cap")
    print("   shrinks the refill and leaves the certainty exactly where it")
    print("   was, which is why capping at 2 read 4.4% and still answered")
    print("   nothing Jon raised. Some income does go with the age rule all")
    print("   the same - a die exhausted during a slot waits for its colour")
    print("   to come round again, and a colour that never comes round")
    print("   again never returns it - and that is what REC 3 pays back.")
    print("   The first four columns are the part he asked for: the pool in")
    print("   front of the player is smaller and tight far more often, so a")
    print("   die spent is a die missed.")


def section_decoration():
    name, dials, levels = CANDIDATES[0]
    print()
    print("6. DOES THE RULE RE-PRICE WHAT FELT LIKE DECORATION? Jon never")
    print("   used his Apprentice's ability and never used FINF at Reduce 1,")
    print("   and measurement agreed with him - the abilities are worth +1.0")
    print("   to +3.2 and a Reduce card about a point. Both are dice-timing")
    print("   effects and the age rule is a dice-timing rule, so both should")
    print("   move. Each measured at its own ladder's Standard rung, under")
    print("   candidate %s." % name.split()[0])
    print()
    print("   %-14s %19s %19s" % ("", "shipped", "candidate A"))
    print("   %-14s %9s %9s %9s %9s"
          % ("ability", "Standard", "worth", "Standard", "worth"))
    a, b = ability_worth(nap.LEVELS), ability_worth(levels, **dials)
    for app in APPS:
        print("   %-14s %8.1f%% %+9.1f %8.1f%% %+9.1f"
              % (app, a[app][0], a[app][1], b[app][0], b[app][1]))
    print()
    print("   %-14s %19s %19s" % ("FINF", "shipped", "candidate A"))
    fa, fb = finf_worth(nap.LEVELS), finf_worth(levels, **dials)
    for s in ("-1", "-2", "-3", "+1", "+2", "+3"):
        label = ("Reduce " if s[0] == "-" else "Increase ") + s[1]
        print("   %-14s %18.1f%% %18.1f%%" % (label, fa[s], fb[s]))


if __name__ == "__main__":
    print(__doc__.strip().split("\n\n")[0])
    print()
    base_std = section_knob()
    section_pay(base_std)
    base_l = ladder()
    section_exams(base_l)
    section_repeg(base_l)
    section_economy()
    section_decoration()
