# -*- coding: utf-8 -*-
"""What the borrow table is worth - and why the model was the problem.

    python3 price_borrow.py [games]            # the five readings
    python3 price_borrow.py [games] policy     # the four policies

BORROWING IS THE ONLY THING IN THE SPLICE PHASE THAT TAKES ANYTHING FOR
GOOD. Nothing in the phase can touch a Rat's Health - 6.00 of 6 at the
moment the Tyrant wakes, in every game measured - and every exhausted die
comes back when the Tyrant does. What does not come back is a banished die,
and a die is banished only by being borrowed and then missing its solo
roll. So the borrow table is not one cost among several. It is the cost.

THE MODEL BORROWED BADLY, AND THAT IS THE HEADLINE. bat.BORROW_POLICY was
not a dial until 2026-11-18; the model borrowed whenever its hand fell
short of the Target and never weighed a one-in-four chance of losing the
die for good. Measured against policies that do, 20,000 games a cell, tier
none:

    rung       short_best  decisive    never
    Easy             59.8      71.8     71.5
    Standard         51.6      63.5     63.5
    Hard             39.2      49.7     49.5
    Nobulous         27.5      37.2     36.7

Ten to twelve points. "decisive" differs from the shipped policy in one
respect - it declines a borrow when the best die the row allows still
cannot close the gap to the Target - and that one restraint is worth more
than every rule change measured in this repository put together. It borrows
1.89 times a game instead of 6.15 and loses 0.48 dice instead of 1.75, for
0.24 fewer Upgrades. Not borrowing AT ALL scores the same to within noise,
so essentially the whole 12 points is bad borrows declined, not good
borrows found.

WHICH IS WHY THE PHASE DOES NOT FEEL LIKE IT BITES. Jon, 2026-11-18, from
play: the Rats end each turn holding effectively a purple and a blue "with
an occasional green or yellow for borrowing purposes". That is the decisive
policy. The pressure the model reported was pressure the model inflicted on
itself, and a table that borrows deliberately never pays it.

SO EVERY FIGURE IN THIS REPOSITORY FOR BAT IS MEASURED THROUGH IT, and
Standard at 51.6% is pegged into a 49-54% band that the same game under a
competent borrow policy leaves at 63.5%. The shipped policy is kept as the
default because every published figure stands on it, but it should not be
mistaken for a model of a good table. Raising the band or fixing the policy
is a design decision and Jon's to make.

THE TABLE'S OWN ORDERING REVERSES WITH THE POLICY, which is the second
finding and the reason this file exists. bat.BORROW_RULE swaps the number
that picks the row. Deltas against the printed rule, 20,000 games a cell:

                       under short_best        under decisive
    rung            flat  worst  splices    flat  worst  splices
    Easy            +0.7   +2.0     +1.5    -0.6   -2.6     -1.5
    Standard        +0.5   +1.0     +1.3    -1.2   -2.5     -1.8
    Hard            +0.4   -0.2     +0.5    -0.5   -2.0     -1.8
    Nobulous         0.0   -0.2     +0.8    -0.9   -2.1     -1.3

Under the shipped policy every alternative reads as a GIFT and the printed
rule looks like the harshest table of the five. Under a competent policy
the signs flip and all sixteen cells go the other way: the printed rule is
the most generous of the five, and yellow-only on every row - which reads
like the cruellest table anyone could print - really is worth two points of
pressure. The first version of this file reported the first half of that as
the finding. It was an artifact of the policy.

WHY THE SIGNS FLIP. Banishment is volume times risk, and the two policies
sit at opposite ends of both. Easy, Red free:

    rule       policy       borrows  of Exps  lost/borrow  dice lost
    printed    short_best      6.15    72.2%        24.9%       1.75
    flat       short_best      6.73    78.1%        20.3%       1.59
    worst      short_best      1.87    23.8%        61.8%       1.27
    printed    decisive        1.89    22.8%        14.1%       0.48
    flat       decisive        2.36    27.8%        13.3%       0.53
    worst      decisive        0.40     5.0%        58.6%       0.43

A policy that borrows 6 times a game is saved money by any rule that stops
it; yellow-only stops it hardest, because the lending pool is then usually
EMPTY and the borrow does not happen at all. A policy that borrows twice a
game is already declining the bad ones, so a narrower table takes away
borrows it actually wanted - and 0.40 borrows a game under yellow-only is
the pressure showing up as Experiments lost rather than dice lost.

WHAT THIS RULES OUT, AND WHAT IT LEAVES. No rule in the borrow family is
worth more than about two and a half points either way, against a policy
difference of twelve. If the Splice Phase is to apply pressure, the lever
is not what the Rats MAY borrow. Red withheld for the rest of the phase is
worth -2.1 to -3.4 under a competent policy (price_red.py), which is the
same order. Upgrades not banked remain the only large lever: 7.2 points for
the fourth and about 16 for the first.
"""
import sys

import bat

LEVELS = ("Easy", "Standard", "Hard", "Nobulous")
RULES = ("upgrades", "flat", "worst", "borrows", "splices")
POLICIES = ("short_best", "short_cheapest", "decisive", "never")
KEY = [None]
R = {}


def instrument():
    """Count borrows and banishments: volume and risk, which is the whole
    explanation of every number above."""
    turn, start = bat.Game.splice_turn, bat.Game.start_battle
    resolve = bat.Game.resolve_borrowed

    def watched(self):
        R.setdefault(KEY[0], []).append(dict(borrow=0, lost=0))
        return turn(self)

    def watched_resolve(self, die, rat):
        out = resolve(self, die, rat)
        rows = R.get(KEY[0])
        if rows and die is not None:
            rows[-1]["borrow"] = 1
            rows[-1]["lost"] = 1 if die.zone == "banished" else 0
        return out

    def photo(self):
        dice = [d for r in self.rats for d in r.dice]
        R.setdefault(KEY[0] + "/end", []).append(dict(
            banished=sum(1 for d in dice if d.zone == "banished"),
            upg=sum(len(r.upgrades) for r in self.rats)))
        return start(self)

    bat.Game.splice_turn = watched
    bat.Game.resolve_borrowed = watched_resolve
    bat.Game.start_battle = photo


def arm(name, games, key):
    KEY[0] = "%s|%s" % (name, key)
    win = 100 * bat.run(name, games, tier="none")
    rows, ends = R.get(KEY[0], []), R.get(KEY[0] + "/end", [])
    n, m, g = float(len(rows)) or 1.0, float(len(ends)) or 1.0, float(games)
    borrows = sum(r["borrow"] for r in rows)
    lost = sum(r["lost"] for r in rows)
    return dict(win=win, exps=len(rows) / g, borrows=borrows / g,
                brate=100.0 * borrows / n,
                lostrate=100.0 * lost / borrows if borrows else 0.0,
                banished=sum(r["banished"] for r in ends) / m,
                upg=sum(r["upg"] for r in ends) / m)


def header():
    print("%-10s %-16s %7s %6s %7s %7s %7s %7s %6s %6s"
          % ("rung", "arm", "win%", "Exps", "borrow", "of Exps", "lost/b",
             "banish", "Upgs", "delta"))


def line(name, label, r, base):
    print("%-10s %-16s %6.1f%% %6.1f %7.2f %6.1f%% %6.1f%% %7.2f %6.2f %s"
          % (name, label, r["win"], r["exps"], r["borrows"], r["brate"],
             r["lostrate"], r["banished"], r["upg"],
             "" if base is None else "%+6.1f" % (r["win"] - base)))
    sys.stdout.flush()


def sweep_rules(games, policy):
    print("\nThe five readings of the borrow table, BORROW_POLICY=%s.\n"
          % policy)
    header()
    bat.BORROW_POLICY = policy
    for name in LEVELS:
        base = None
        for rule in RULES:
            bat.BORROW_RULE = rule
            r = arm(name, games, "r:%s:%s" % (policy, rule))
            if base is None:
                base = r["win"]
            line(name, rule, r, None if rule == RULES[0] else base)
        print()
    bat.BORROW_RULE = "upgrades"


def sweep_policies(games):
    print("\nThe four borrow policies, printed rules throughout.\n")
    header()
    for name in LEVELS:
        base = None
        for pol in POLICIES:
            bat.BORROW_POLICY = pol
            r = arm(name, games, "p:" + pol)
            if base is None:
                base = r["win"]
            line(name, pol, r, None if pol == POLICIES[0] else base)
        print()


def main():
    games = int(sys.argv[1]) if len(sys.argv) > 1 else 6000
    want_policy = len(sys.argv) > 2 and sys.argv[2].startswith("pol")
    instrument()
    was = (bat.BORROW_RULE, bat.BORROW_POLICY)
    print("%d games a cell, tier none, Red free. SE on a difference is "
          "about %.2f points." % (games, 100 * (0.5 / games ** 0.5)
                                 * 2 ** 0.5))
    try:
        if want_policy:
            sweep_policies(games)
        else:
            sweep_rules(games, "short_best")
            sweep_rules(games, "decisive")
    finally:
        bat.BORROW_RULE, bat.BORROW_POLICY = was
    print("borrow = borrowed dice resolved per game. of Exps = the share of")
    print("Experiments that resolved one. lost/b = the share of those that")
    print("banished the die. banish = dice gone for good when the Tyrant")
    print("wakes, from every source, so it runs above borrow x lost/b:")
    print("Containment banishes without anyone borrowing.")


if __name__ == "__main__":
    main()
