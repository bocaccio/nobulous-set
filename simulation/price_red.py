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
