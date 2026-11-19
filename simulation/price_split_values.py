# -*- coding: utf-8 -*-
"""Two numbers per Upgrade, and the choice between arming a Rat and
choosing the Tyrant's wall. What Jon's design prices out at.

    python3 price_split_values.py [games]          # the Rat number
    python3 price_split_values.py [games] choice   # the take-or-splice choice
    python3 price_split_values.py [games] tyrant   # the gap on the Tyrant side

JON, 2026-11-18: "It's almost like I want two numbers for each upgrade, a
smaller number for the rats and a larger number for the tyrant (in essence,
the upgrades are a weaker benefit to the rats). Then, instead of just
choosing to take an upgrade, you can choose whether to take the upgrade or
splice one of them onto the tyrant... your primary agency is choosing what
to splice." The Rat scale he picked, asked directly: Tyrant value minus 1.

EVERY FIGURE BELOW IS QUOTED TWICE, under the borrow policy BAT's published
numbers were measured through and under one that declines a borrow it cannot
profit from. The policy alone is worth 10 to 12 points and it flips the sign
of several of these - see price_borrow.py. The arm to read is the competent
one: it is the table Jon plays at.

-----------------------------------------------------------------------
1. THE RAT NUMBER DOES NOTHING. This is the finding, and it is not a
   measurement artifact - it is what the printed rules say.
-----------------------------------------------------------------------

RAT_VALUE_DELTA -1, shipped borrow policy, 20,000 games an arm:

    rung       printed   rat -1   delta
    Easy          59.8     59.9    +0.0
    Standard      51.6     51.4    -0.3
    Hard          39.2     38.9    -0.3
    Nobulous      27.5     26.9    -0.6

The Rats' total held Upgrade Value falls from 14.71 to 10.78 - nearly four
points of Value taken off the table - and the win rate does not move. The
reason is printed in rules/bat.html: "A Rat's Upgrade blocks one attack and
is spent." A Rat's Value is not a budget, a threshold or a shield. Its only
jobs are to rank the two revealed cards, which a uniform shift cannot
change, and to feed Predatory Instinct's targeting. So "a weaker benefit to
the rats" is, as written, not a benefit that was ever being measured.

-----------------------------------------------------------------------
2. GIVING IT A JOB COSTS MORE THAN THE WHOLE DIFFICULTY LADDER.
-----------------------------------------------------------------------

RAT_BLOCK_RULE offers two readings that make the Rat number load-bearing.
"threshold" reads it the way a Tyrant Splice is read - an Upgrade only stops
a blow its Value meets. "absorb" reads it as a budget - the card soaks up to
its Value and is spent, and the overflow lands on the Rat.

    rung       threshold  +(-1)      absorb   +(-1)      policy
    Easy           -20.0  -28.8       -20.3   -31.7      see below
    Standard       -17.9  -26.6       -18.7   -30.2
    Hard           -15.3  -22.6       -17.7   -26.7
    Nobulous       -10.7  -16.3       -13.6   -20.6

threshold is measured on the shipped policy, absorb on the competent one;
they are the same size either way. Both cost 11 to 20 points BEFORE the -1
is applied, and the -1 then adds 9 to 11 more. For comparison, the entire
gap from Easy to Nobulous is 34 points. A rule that makes the Rat number
matter is not a tuning; it is a different game.

-----------------------------------------------------------------------
3. AN OPTIONAL CHOICE CANNOT APPLY PRESSURE. This one is an argument
   rather than a measurement, and the measurements agree with it.
-----------------------------------------------------------------------

Declining to Splice is always legal, so a player who never uses the option
plays the printed game. The printed win rate is therefore a FLOOR for
anyone choosing well: adding the choice can raise the Rats' win rate and
can never lower it. What the numbers below price is what a fixed heuristic
pays, not what the mechanic costs.

SPLICE_CHOICE, competent borrow policy, with RAT_VALUE_DELTA -1:

    rung       printed  when_full  cheap   cheap+threshold
    Easy          71.8       71.7   63.9              40.4
    Standard      63.5       63.2   57.8              34.4
    Hard          49.7       49.8   45.3              23.7
    Nobulous      37.2       37.1   34.5              17.8

"when_full" - Splice only when the Rat cannot take an Upgrade anyway - is
free and does nothing, because THE 3-UPGRADE LIMIT NEVER BINDS: the Rats
reach the Tyrant holding 3.7 Upgrades of a possible 12, so it fires 0.01
times a game. "cheap" - also Splice when the weaker revealed card is a 2 -
fires 1.4 to 1.7 times a game and costs 2.7 to 7.9 points, so a player
offered that trade should mostly refuse it. Forced ("always") it is -18 to
-31, with the phase over in exactly 5 Experiments and 0.27 Upgrades banked.

WHAT IT COSTS IS NOT WHAT IT DOES, THOUGH. Under the shipped borrow policy
the same "cheap" heuristic GAINS the Rats 1.9 to 6.0 points, because the
phase ends two Experiments early and the model's bad borrows end with it.
The sign of this mechanic is set by how well the phase is played, which is
the clearest single illustration of why price_borrow.py comes first.

-----------------------------------------------------------------------
4. AND THE TYRANT NUMBER IS ALREADY AT THE EDGE OF A CLIFF.
-----------------------------------------------------------------------

The same design gap can be put on the other side: Rat = printed, Tyrant =
printed + 1. That number is doing real work, so it is not inert - it is
catastrophic. TYRANT_VALUE_DELTA, competent policy:

    rung       printed     +1     +2     +3
    Easy          71.8   19.6    1.1    0.0
    Standard      63.5   13.8    0.7    0.0
    Hard          49.7    8.7    0.3    0.0
    Nobulous      37.2    5.1    0.2    0.0

A Splice Value is a threshold a blow must MEET IN ONE ATTACK - damage_tyrant
returns outright on `dmg < s.value`, and a blow that falls short is wasted
entirely. So +1 does not add five points to a wall; it moves Splices past
what the Rats can assemble in a single attack, and the printed 2-to-5 range
sits exactly at that limit. +2 ends the game.

-----------------------------------------------------------------------
5. AND THE OPTIONAL-CHOICE ARGUMENT SURVIVES A CAP BUILT TO DEFEAT IT.
-----------------------------------------------------------------------

The one way to make the choice compulsory is to make TAKING impossible, so
UPGRADE_CAP is a dial too. Competent policy, 20,000 games an arm:

    rung       cap 3   cap 2  cap 2+choice   cap 1  cap 1+choice
    Easy        71.8    72.0          71.9    69.1          72.6
    Standard    63.5    63.3          63.8    60.8          63.9
    Hard        49.7    49.9          49.5    46.8          51.6
    Nobulous    37.2    37.0          37.3    34.5          39.1

Cap 2 still does not bind - 0.05 chosen Splices a game. CAP 1 IS A CLEAN
LEVER: -2.7, -2.6, -2.8, -2.7, the same on every rung, working by cutting
the Rats from 3.70 Upgrades to 3.04. It is the only small, linear, uniform
pressure found anywhere in the Splice Phase.

AND THEN THE CHOICE GIVES IT ALL BACK, +3.5 against the capped baseline and
+0.4 to +1.9 against the printed one. A cap designed to force the Splice
instead hands the Rats a profitable option 0.4 times a game. That is the
argument of section 3 measured rather than asserted.

-----------------------------------------------------------------------
6. SO THE GAP CANNOT BE BUILT BY SHIFTING EITHER NUMBER BY ONE.
-----------------------------------------------------------------------

The Rat number is free to lower and worth nothing; the Tyrant number is
worth everything and cannot move. The design needs the two numbers to be
doing different jobs ALREADY, and in this game only one of them has a job
at all. What survives is the take-or-splice choice as a TEXTURE rule: it
costs nothing when the Rats may always decline, it gives the Splice Phase
the decision Jon described wanting, and `when_full` turns a wasted success
into a choice at no measured cost. Difficulty has to keep coming from the
difficulty table - Buff HP and core Health, which are linear and already
calibrated (price_buff_ladder.py) - or, if the phase itself must carry
some, from UPGRADE_CAP, which is the only lever in it that behaves.
"""
import sys

import bat

LEVELS = ("Easy", "Standard", "Hard", "Nobulous")
KEY = [None]
R = {}


def instrument():
    turn, start = bat.Game.splice_turn, bat.Game.start_battle
    choose = bat.Game.choose_splice

    def watched(self):
        R.setdefault(KEY[0], []).append(dict(chose=0))
        return turn(self)

    def watched_choose(self, rat, options, best, cap):
        out = choose(self, rat, options, best, cap)
        rows = R.get(KEY[0])
        if rows and out is not None:
            rows[-1]["chose"] = 1
        return out

    def photo(self):
        vals = [sp.value for sp in self.splices]
        R.setdefault(KEY[0] + "/end", []).append(dict(
            upg=sum(len(r.upgrades) for r in self.rats),
            upval=sum(u.value for r in self.rats for u in r.upgrades),
            spl=sum(vals), top=max(vals) if vals else 0))
        return start(self)

    bat.Game.splice_turn = watched
    bat.Game.choose_splice = watched_choose
    bat.Game.start_battle = photo


def arm(name, games, key):
    KEY[0] = "%s|%s" % (name, key)
    win = 100 * bat.run(name, games, tier="none")
    rows, ends = R.get(KEY[0], []), R.get(KEY[0] + "/end", [])
    n, m, g = float(len(rows)) or 1.0, float(len(ends)) or 1.0, float(games)
    f = lambda k: sum(r[k] for r in ends) / m
    return dict(win=win, exps=len(rows) / g,
                chose=sum(r["chose"] for r in rows) / g,
                upg=f("upg"), upval=f("upval"), spl=f("spl"), top=f("top"))


def setd(**kw):
    bat.RAT_VALUE_DELTA = kw.get("delta", 0)
    bat.TYRANT_VALUE_DELTA = kw.get("ty", 0)
    bat.RAT_BLOCK_RULE = kw.get("block", "spend")
    bat.SPLICE_CHOICE = kw.get("choice", "never")
    bat.SPLICE_CHOICE_FLOOR = kw.get("floor", 2)
    bat.UPGRADE_CAP = kw.get("cap", 3)
    bat.BORROW_POLICY = kw.get("policy", "short_best")


def table(title, arms, games, note=""):
    print("\n=== %s ===" % title)
    if note:
        print(note)
    print("%d games an arm.\n" % games)
    print("%-10s %-24s %7s %6s %6s %6s %7s %7s %6s %7s"
          % ("rung", "arm", "win%", "Exps", "chose", "Upgs", "UpVal",
             "Splice", "worst", "delta"))
    for name in LEVELS:
        base = None
        for i, (label, kw) in enumerate(arms):
            setd(**kw)
            r = arm(name, games, "%s|%s" % (title[:3], label))
            if i == 0:
                base = r["win"]
            print("%-10s %-24s %6.1f%% %6.1f %6.2f %6.2f %7.2f %7.2f %6.2f %s"
                  % (name, label, r["win"], r["exps"], r["chose"], r["upg"],
                     r["upval"], r["spl"], r["top"],
                     "" if i == 0 else "%+6.1f" % (r["win"] - base)))
            sys.stdout.flush()
        print()
    setd()


RAT = [
    ("printed", {}),
    ("rat value -1", dict(delta=-1)),
    ("threshold block", dict(block="threshold")),
    ("-1 + threshold", dict(delta=-1, block="threshold")),
    ("absorb block", dict(block="absorb")),
    ("-1 + absorb", dict(delta=-1, block="absorb")),
]

CHOICE = [
    ("printed", dict(policy="decisive")),
    ("-1 + when_full", dict(delta=-1, choice="when_full", policy="decisive")),
    ("-1 + cheap", dict(delta=-1, choice="cheap", policy="decisive")),
    ("-1 + cheap, forced", dict(delta=-1, choice="always", policy="decisive")),
]

TYRANT = [
    ("printed", dict(policy="decisive")),
    ("tyrant +1", dict(ty=1, policy="decisive")),
    ("tyrant +2", dict(ty=2, policy="decisive")),
    ("tyrant +1 + cheap", dict(ty=1, choice="cheap", policy="decisive")),
]

CAP = [
    ("printed: cap 3", dict(policy="decisive")),
    ("cap 2", dict(cap=2, policy="decisive")),
    ("cap 1", dict(cap=1, policy="decisive")),
    ("cap 1 + when_full", dict(cap=1, choice="when_full",
                               policy="decisive")),
]


def main():
    games = int(sys.argv[1]) if len(sys.argv) > 1 else 6000
    which = (sys.argv[2] if len(sys.argv) > 2 else "rat").lower()
    instrument()
    try:
        if which.startswith("cho"):
            table("THE TAKE-OR-SPLICE CHOICE", CHOICE, games,
                  "Competent borrow policy. An option the Rats may decline\n"
                  "cannot cost them anything: these are what one fixed\n"
                  "heuristic pays, not what the mechanic taxes.")
        elif which.startswith("ty"):
            table("THE GAP ON THE TYRANT SIDE", TYRANT, games,
                  "Competent borrow policy. A Splice Value is a threshold a\n"
                  "blow must meet in ONE attack, so this number is a cliff.")
        elif which.startswith("cap"):
            table("THE UPGRADE LIMIT", CAP, games,
                  "Competent borrow policy. The only way to make the choice\n"
                  "compulsory is to make taking impossible - and the choice\n"
                  "then gives back more than the cap took.")
        else:
            table("THE RAT NUMBER", RAT, games,
                  "Shipped borrow policy. Does a smaller Rat number cost the\n"
                  "Rats anything? Only once some rule reads it.")
    finally:
        setd()
    print("chose = chosen Splices per game, of the 5 on the track.")
    print("UpVal = the Rats' total held Upgrade Value; watch it fall by 4")
    print("        under 'rat value -1' while the win rate does not move.")
    print("Splice = the Tyrant's wall; worst = its highest single Splice.")


if __name__ == "__main__":
    main()
