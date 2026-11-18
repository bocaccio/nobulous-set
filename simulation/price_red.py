# -*- coding: utf-8 -*-
"""What charging a REC slot for the Red die would do.

    python3 price_red.py [games]

THE SPLICE PHASE APPLIES NO PRESSURE - Jon, 2026-11-18, from play rather
than from a model. The model agrees about the cause and not about the
symptom: the phase is already TIGHT, with the acting Rat holding 2.8 of its
4 dice and a hand worth 2.2 expected successes against a mean printed
Target of 4.15, borrowing in three Experiments out of four and committing
Red in half of them. What it has no trace of is JEOPARDY. Nothing in the
phase can touch a Rat's Health - 6.00 of 6 at the moment the Tyrant wakes,
in every game measured - so failing two Experiments in three costs only
tempo, and tempo is also what ends the phase.

Red is the phase's most reliable crutch and it is free: the printed rule
sets it aside rather than exhausting it. bat.RED_COSTS_REC charges the
active Rat one REC slot on a turn it commits Red, which is the half of
Jon's proposal that is not already the rule.

AND IT MAKES THE RATS WIN MORE, which is not what it was for. 40,000 games
an arm: Easy 59.9 -> 62.0, Standard 51.3 -> 53.3, six standard errors and
five. The Tyrant is identical in both - Splice totals 20.22 against 20.15,
core 7.71 against 7.74 - so the whole difference is what the Rats carry out
of the phase, and that is:

    free      8.27 dice, pool EV 5.82, 3.94 Upgrades, 1.75 banished
    charged   8.51 dice, pool EV 6.02, 3.53 Upgrades, 1.52 banished

THE BORROW RULE IS A FEEDBACK LOOP, and this is the mechanism. "The more
Upgrades the borrower already holds, the worse the die it is allowed to
take", and the printed banish risks are the miss chances of the best die
each row allows: 17 / 33 / 50 / 67%. So holding Upgrades makes your
borrowing worse, and a worse borrow is a die gone for good. Charging for
Red leaves the Rats one Upgrade short of where they would have been, which
PERMITS BETTER BORROWS, which banishes fewer dice - and the dice it saves
are the good ones: blue +0.13 and purple +0.04 of the +0.24.

TWO EARLIER EXPLANATIONS WERE WRONG and are recorded here so they are not
tried again. "Pressure that does not survive the phase cannot make the game
harder" is true but does not explain a gain. "It banishes fewer dice, and
banishment is the only cost the phase imposes" is false: PHASE_CONCEDE
drops banishment to 0.25 and loses 41 points, because Upgrades carry the
battle.

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

    def watched_turn(self):
        up = [r for r in self.rats if not r.down]
        avail = [len(self.available(r)) for r in up]
        ROWS.setdefault(NAME[0], []).append(dict(
            best=max(avail) if avail else 0,
            ev=max([sum(bat.EV[d.color] for d in self.available(r))
                    for r in up] or [0]),
            thin=1 if (max(avail) if avail else 0) <= 2 else 0))
        return turn(self)

    def photograph(self):
        dice = [d for r in self.rats for d in r.dice]
        ROWS.setdefault(NAME[0] + "/end", []).append(dict(
            banished=sum(1 for d in dice if d.zone == "banished"),
            upg=sum(len(r.upgrades) for r in self.rats)))
        return start(self)

    bat.Game.splice_turn = watched_turn
    bat.Game.start_battle = photograph


def arm(name, games, charged):
    key = "%s %s" % (name, "charged" if charged else "free")
    NAME[0] = key
    bat.RED_COSTS_REC = charged
    win = 100 * bat.run(name, games, tier="none")
    rows, ends = ROWS.get(key, []), ROWS.get(key + "/end", [])
    n, m = float(len(rows)) or 1.0, float(len(ends)) or 1.0
    return dict(win=win, exps=len(rows) / float(games),
                best=sum(r["best"] for r in rows) / n,
                ev=sum(r["ev"] for r in rows) / n,
                thin=100.0 * sum(r["thin"] for r in rows) / n,
                banished=sum(r["banished"] for r in ends) / m,
                upg=sum(r["upg"] for r in ends) / m)


def main():
    games = int(sys.argv[1]) if len(sys.argv) > 1 else 6000
    instrument()
    was = bat.RED_COSTS_REC
    print("%d games a rung, tier none. Mean printed Target is %.2f.\n"
          % (games, sum(bat.EXPERIMENT_TARGETS)
             / float(len(bat.EXPERIMENT_TARGETS))))
    print("%-10s %-8s %7s %6s %6s %5s %6s %6s %6s"
          % ("rung", "Red", "win%", "Exps", "hand", "EV", "thin%", "lost",
             "Upgs"))
    try:
        for name in LEVELS:
            for charged in (False, True):
                r = arm(name, games, charged)
                print("%-10s %-8s %6.1f%% %6.1f %6.2f %5.2f %5.1f%% %6.2f "
                      "%6.2f"
                      % (name, "charged" if charged else "free", r["win"],
                         r["exps"], r["best"], r["ev"], r["thin"],
                         r["banished"], r["upg"]))
                sys.stdout.flush()
    finally:
        bat.RED_COSTS_REC = was
    print("\nhand = dice the Rat that acts holds, of 4. EV = what that hand")
    print("is worth in expected successes. thin% = Experiments begun with")
    print("the best hand down to 2 dice. lost = dice banished for good.")


if __name__ == "__main__":
    main()
