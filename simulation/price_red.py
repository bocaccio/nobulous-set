# -*- coding: utf-8 -*-
"""What charging a REC slot for the Red die would do.

    python3 price_red.py [games]

READ price_borrow.py FIRST. Everything in this file up to the last two
sections is measured through the borrow policy bat.BORROW_POLICY shipped
with, and that policy is itself worth 10 to 12 points - more than every
rule change priced in this repository put together. The Red numbers below
are real but they are second-order, and the last two sections say what the
dial is worth once the policy is a competent one.

THE SPLICE PHASE APPLIES NO PRESSURE - Jon, 2026-11-18, from play rather
than from a model. The model agrees about the cause and not about the
symptom: the phase is already TIGHT, with the best hand on the table down
to 2.8 of 4 dice and worth 2.2 expected successes against a mean printed
Target of 4.15, borrowing in three Experiments out of four and committing
Red in half of them. What it has no trace of is JEOPARDY. Nothing in the
phase can touch a Rat's Health - 6.00 of 6 at the moment the Tyrant wakes,
in every game measured - so failing two Experiments in three costs only
tempo, and tempo is also what ends the phase.

THE "BORROWING IN THREE EXPERIMENTS OUT OF FOUR" IS THE MODEL, NOT THE
GAME. A competent policy borrows in roughly one in four, which is what Jon
reported from the table, and wins 12 points more for it.

Red is the phase's most reliable crutch and it is free: the printed rule
sets it aside rather than exhausting it. bat.RED_COSTS_REC has three
readings, because the first one written was a penalty with no choice in it:

    False      the printed game - Red is set aside and returns free
    "always"   Red returns every turn, at the cost of one REC slot
    "afford"   using Red EXHAUSTS it, and it stays off the table until some
               Rat with RED_AFFORD_FLOOR slots spends RED_AFFORD_COST of
               them on it

Jon's words are "a rat with REC 1 could only recover red, if they choose to
do so", so FLOOR 1 is the faithful reading - and floor 1 measures bit for
bit identical to "always", because a Rat that can always pay always does
and Red is never off the table. The proposal as written IS the charged arm.

AND IT MAKES THE RATS WIN MORE, which is not what it was for. 40,000 games
an arm: Easy 59.9 -> 62.0, Standard 51.3 -> 53.3, six standard errors and
five. The Tyrant is identical in both - Splice totals 20.22 against 20.15,
core 7.71 against 7.74 - so the whole difference is what the Rats carry out
of the phase, and that is:

    free      8.27 dice, pool EV 5.82, 3.94 Upgrades, 1.75 banished
    charged   8.51 dice, pool EV 6.02, 3.53 Upgrades, 1.52 banished

IT THROTTLES BORROWING, and that is the mechanism. A REC slot spent on Red
is a slot not spent recovering the Rat's own dice, so every Rat carries
more exhausted dice - and the lending pool is made of OTHER Rats' AVAILABLE
dice. A die that is not available cannot be lent, a die that is not lent
cannot be banished, and banishment is the only thing the phase takes for
good. Easy, 20,000 games an arm:

    free      8.5 Experiments, 6.15 borrows, 24.9% of them banish, 1.75 lost
    charged   8.1 Experiments, 5.28 borrows, 24.3% of them banish, 1.50 lost

The risk PER BORROW barely moves. The number of borrows falls by nearly
one a game, and 6.15 x 0.249 - 5.28 x 0.243 = 0.25, which is the whole
measured drop in dice lost.

A THIRD EXPLANATION WAS WRONG, AND IT IS THE ONE THIS FILE USED TO GIVE.
It said the borrow table's feedback loop did it: fewer Upgrades, a better
row, safer borrows. Three measurements killed it. Under BORROW_RULE="flat"
every row is the best row and the Upgrade count picks nothing at all, yet
charging for Red still gains +1.7 at Easy and +1.3 at Standard. Under flat
the banish rate per borrow goes the WRONG WAY when Red is charged, 20.3%
to 21.1%, while the gain persists. And under BORROW_RULE="worst", where
yellow-only keeps the lending pool empty and borrowing is already throttled
to 1.87 a game, charging for Red stops paying and COSTS 1.6 at Easy and 1.2
at Standard - the sign flips exactly where there is no borrowing left to
throttle. See price_borrow.py.

TWO EARLIER EXPLANATIONS WERE WRONG TOO, kept here so they are not tried
again. "Pressure that does not survive the phase cannot make the game
harder" is true but does not explain a gain. "It banishes fewer dice, and
banishment is the only cost the phase imposes" is false: PHASE_CONCEDE
drops banishment to 0.25 and loses 41 points, because Upgrades carry the
battle.

A BUG OF MINE READ -8.3 HERE FIRST, and it is worth recording because it
survived a whole round of measurement looking like the best result in the
file. Set RED_AFFORD_FLOOR to 3 and no Rat can ever pay - RAT_REC is
[2, 2, 1, 1] - so Red is used once and is gone for the rest of the phase.
That measured -8.3 at Easy. It was not the rule. The active-Rat policy
sorted on `r is self.red_holder and not self.red_aside` and never consulted
red_down, so in that arm it handed the turn, over and over, to a Rat
holding a die it was not allowed to roll, ahead of a Rat with more dice
ready. Fixing the key - the one-line `and not red_down` in splice_turn -
moved the same arm to +4.1. A dial that withholds a die MUST be visible to
the policy that chooses who acts, or the measurement prices the model's
confusion instead of the rule.

AND ALL OF IT TURNED OUT TO BE A SECOND-ORDER EFFECT. Everything above is
measured through a borrow policy that borrows whenever it is short and
never weighs losing the die for good, and that policy is worth 10 to 12
points on its own - see price_borrow.py. Under bat.BORROW_POLICY=
"decisive", which declines a borrow that cannot close the gap, the Red
dial reads completely differently, 20,000 games an arm:

    rung       free  charged  withheld
    Easy       71.8     71.6      68.7
    Standard   63.5     62.8      60.1
    Hard       49.7     48.5      47.5
    Nobulous   37.2     36.6      34.7

CHARGING A REC SLOT IS WORTH NOTHING, -0.2 to -1.2, because against a
policy that borrows twice a game there is no longer a stream of bad borrows
for the slot to throttle. WITHHOLDING RED IS WORTH -2.1 TO -3.4, honest
pressure of the same size as the whole borrow-table family, and for the
plain reason rather than any feedback: the Rats arrive with 3.1 to 3.3
Upgrades instead of 3.5 to 3.7, having had a free die taken out of half
the Experiments in the phase.

SO JON'S INSTINCT WAS RIGHT ABOUT THE SHAPE AND THE PRICE IS SMALL. The
rule has to WITHHOLD Red rather than charge for it, and even then it buys
two or three points, not the ten the phase would need to feel different.

AND THE MARGINALS DO NOT ADD UP, which is the honest state of it. Docking
the party one die at the moment the Tyrant wakes costs 9.9 points at Easy
and docking it one Upgrade costs 7.2, so this trade should lose half a
point rather than win two. They are not additive: a knocked-out Rat loses
its Upgrades AND stops rolling, so armour and dice interact through
knockouts, and the Upgrade curve is convex - the fourth is cheap at 7.2
while going to none costs about 16 a card.

Prints both arms per rung with the pressure metrics beside the win rate, so
the cost is visible as more than a number.
"""
import sys

import bat

LEVELS = ("Easy", "Standard", "Hard", "Nobulous")
NAME = [None]
ROWS = {}


def instrument():
    turn = bat.Game.splice_turn
    start = bat.Game.start_battle
    resolve = bat.Game.resolve_borrowed

    def watched_turn(self):
        up = [r for r in self.rats if not r.down]
        ROWS.setdefault(NAME[0], []).append(dict(
            ev=max([sum(bat.EV[d.color] for d in self.available(r))
                    for r in up] or [0]),
            # "afford" only: Red exhausted and nobody has paid to lift it.
            down=1 if getattr(self, "red_down", False) else 0,
            borrow=0, lost=0))
        return turn(self)

    def watched_resolve(self, die, rat):
        # THE LOAD-BEARING COUNT. The explanation this file used to give was
        # about the RISK of a borrow; the one that survived measurement is
        # about the NUMBER of them, so both have to be on the table.
        out = resolve(self, die, rat)
        rows = ROWS.get(NAME[0])
        if rows and die is not None:
            rows[-1]["borrow"] = 1
            rows[-1]["lost"] = 1 if die.zone == "banished" else 0
        return out

    def photograph(self):
        dice = [d for r in self.rats for d in r.dice]
        ROWS.setdefault(NAME[0] + "/end", []).append(dict(
            banished=sum(1 for d in dice if d.zone == "banished"),
            upg=sum(len(r.upgrades) for r in self.rats)))
        return start(self)

    bat.Game.splice_turn = watched_turn
    bat.Game.start_battle = photograph
    bat.Game.resolve_borrowed = watched_resolve


# label, RED_COSTS_REC, RED_AFFORD_FLOOR, RED_AFFORD_COST. "afford f1c1" is
# Jon's proposal as written and measures identical to "always"; "never" is
# the unreachable floor, which is the only arm that costs the Rats anything.
ARMS = (
    ("free", False, 1, 1),
    ("always", "always", 1, 1),
    ("afford f1c1", "afford", 1, 1),
    ("afford f2c1", "afford", 2, 1),
    ("afford f2c2", "afford", 2, 2),
    ("never", "afford", 3, 1),
)


def arm(name, games, label, mode, floor, cost):
    key = "%s %s" % (name, label)
    NAME[0] = key
    bat.RED_COSTS_REC = mode
    bat.RED_AFFORD_FLOOR, bat.RED_AFFORD_COST = floor, cost
    win = 100 * bat.run(name, games, tier="none")
    rows, ends = ROWS.get(key, []), ROWS.get(key + "/end", [])
    n, m = float(len(rows)) or 1.0, float(len(ends)) or 1.0
    borrows = sum(r["borrow"] for r in rows)
    lost = sum(r["lost"] for r in rows)
    return dict(win=win, exps=len(rows) / float(games),
                down=100.0 * sum(r["down"] for r in rows) / n,
                ev=sum(r["ev"] for r in rows) / n,
                borrows=borrows / float(games),
                lostrate=100.0 * lost / borrows if borrows else 0.0,
                banished=sum(r["banished"] for r in ends) / m,
                upg=sum(r["upg"] for r in ends) / m)


def main():
    games = int(sys.argv[1]) if len(sys.argv) > 1 else 6000
    instrument()
    was = (bat.RED_COSTS_REC, bat.RED_AFFORD_FLOOR, bat.RED_AFFORD_COST)
    print("%d games a rung, tier none. Mean printed Target is %.2f.\n"
          % (games, sum(bat.EXPERIMENT_TARGETS)
             / float(len(bat.EXPERIMENT_TARGETS))))
    print("%-10s %-12s %7s %6s %6s %5s %7s %7s %6s %6s"
          % ("rung", "Red", "win%", "Exps", "down%", "EV", "borrow",
             "lost/b", "lost", "Upgs"))
    try:
        for name in LEVELS:
            for label, mode, floor, cost in ARMS:
                r = arm(name, games, label, mode, floor, cost)
                print("%-10s %-12s %6.1f%% %6.1f %5.1f%% %5.2f %7.2f "
                      "%6.1f%% %6.2f %6.2f"
                      % (name, label, r["win"], r["exps"], r["down"],
                         r["ev"], r["borrows"], r["lostrate"],
                         r["banished"], r["upg"]))
                sys.stdout.flush()
            print()
    finally:
        bat.RED_COSTS_REC, bat.RED_AFFORD_FLOOR, bat.RED_AFFORD_COST = was
    print("down%  = Experiments begun with Red off the table entirely.")
    print("EV     = the BEST hand among standing Rats in expected")
    print("         successes - not the acting Rat's, though the policy")
    print("         usually picks it. It RISES in the withheld arm,")
    print("         because hands go unspent when Red cannot top them up.")
    print("borrow = borrowed dice resolved per game; lost/b = the share of")
    print("those that banished the die. lost = dice gone for good when the")
    print("Tyrant wakes. The win-rate gain tracks borrow, not lost/b.")


if __name__ == "__main__":
    main()
