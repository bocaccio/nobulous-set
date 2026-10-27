"""Measure the BAT prototype against the shipping model.

    python trial.py            # the three questions below
    python trial.py 8000       # more games per cell

Three things are worth measuring and only one of them is the win rate:

  win       the win rate, which only says whether the dial is in band
  rounds    battle length - 9.1 in the shipping rules is the tedium
  dice      dice left in the shared pool when the battle ended; the
            shipping rules finish with 7.1 of about 10 still unspent,
            which is why the pool never feels like a budget
  dry-loss  share of LOSSES that ended because the Rats could not put a
            die on the table, rather than because every Rat was knocked
            out. See the README: driving this to 100% is a trap.

The headline number is the gap between the `conserve` and `threshold`
policies. Under the shipping rules conserving - committing only what
recovery returns, so no die is ever spent for good - beats playing to
break walls by 7 points. That is the whole reason the battle has no
resource tension, and the prototype exists to invert it.
"""
import random
import statistics
import sys

import bat

bat.RAT_DICE_CAP = 99          # the commit cap was removed; see README

CONFIG = dict(threshold=True, break_banish=1, armor_spend=True,
              round_cap=8, attrition=False)
# Difficulty is Tyrant Health; Buff HP used to carry these points on its own
# card, back when Health was a flat 20. Specimen count is unchanged.
HEALTH = {"Easy": 9, "Standard": 10, "Hard": 12, "Nobulous": 14}
SPECIMENS = {"Easy": 5, "Standard": 6, "Hard": 7, "Nobulous": 8}
REC = 2
DEFAULT = 4000

OFF = dict(threshold=False, overflow=True, break_banish=0, armor_spend=False,
           health=None, attrition=False, bite=1, bite_ramp=0, round_cap=0)


def trial(difficulty="Standard", games=DEFAULT, policy="threshold", rec=REC,
          **over):
    """Win rate, battle length, dice left and dry-loss share."""
    bat.PROTO.update(OFF)
    # No Buff HP card: the difficulty's points are Health.
    if "health" not in over and over.get("threshold", CONFIG["threshold"]):
        bat.DIFFICULTY[difficulty] = (SPECIMENS[difficulty], 0)
        over = dict(over, health=HEALTH[difficulty])
    bat.PROTO.update(over)
    wins = rounds = 0
    dice, on_win, dry, losses = [], [], 0, 0
    real = bat.Game.battle_round

    def counted(self):
        self._n = getattr(self, "_n", 0) + 1
        ok = real(self)
        if not ok:
            self._dry = bool(self.shared_pool() == []
                             and not all(r.down for r in self.rats))
        return ok

    bat.Game.battle_round = counted
    try:
        for i in range(games):
            g = bat.Game(difficulty, random.Random(i), card_effects=True,
                         sides="random", commit_policy=policy,
                         battle_rec_bonus=rec)
            won = g.play()
            n = getattr(g, "_n", 0)
            if not n:
                continue                   # never reached the battle
            rounds += n
            dice.append(len(g.shared_pool()))
            if won:
                wins += 1
                on_win.append(len(g.shared_pool()))
            else:
                losses += 1
                dry += bool(getattr(g, "_dry", False))
    finally:
        bat.Game.battle_round = real
    n = len(dice) or 1
    return dict(win=100.0 * wins / n, rounds=rounds / float(n),
                dice=statistics.mean(dice), on_win=on_win,
                dry=100.0 * dry / losses if losses else 0.0)


def main(games=DEFAULT):
    print("BAT prototype - threshold damage, 8-round clock, no commit cap,")
    print("Splice breaks banish a die, Upgrades spent to block,")
    print("Buff HP folded into Health (9/10/12/14). %d games." % games)

    print()
    print("1. Is spending correct?  (Standard)")
    print("   %-12s %8s %8s %10s" % ("policy", "win", "rounds", "dice left"))
    got = {}
    # Under the shipping rules there are no walls, so the threshold policy
    # has nothing to aim at and collapses into conserve. The meaningful
    # contrast there is hoarding against spending freely.
    for name, cfg in (("shipping rules", OFF), ("prototype", CONFIG)):
        spender = "all-out" if cfg is OFF else "threshold"
        for pol in ("conserve", spender):
            r = trial(games=games, policy=pol, **cfg)
            got[(name, pol)] = r["win"]
            print("   %-12s %7.1f%% %8.1f %10.1f   %s/%s"
                  % (pol, r["win"], r["rounds"], r["dice"], name, pol))
        gap = got[(name, spender)] - got[(name, "conserve")]
        print("   -> %s: spending beats hoarding by %+.1f" % (name, gap))
        print()

    print("2. The ladder")
    print("   %-10s %8s %8s %10s %9s"
          % ("difficulty", "win", "rounds", "dice left", "dry-loss"))
    prev = None
    for d in ("Easy", "Standard", "Hard", "Nobulous"):
        r = trial(d, games=games, **CONFIG)
        step = "" if prev is None else "  (%+.1f)" % (r["win"] - prev)
        prev = r["win"]
        print("   %-10s %7.1f%% %8.1f %10.1f %8.0f%%%s"
              % (d, r["win"], r["rounds"], r["dice"], r["dry"], step))

    print()
    print("3. How close are the wins?  (Standard)")
    r = trial(games=games, **CONFIG)
    w = sorted(r["on_win"])
    if w:
        print("   dice left on a win: mean %.1f, median %d, <=2 in %.0f%%"
              % (statistics.mean(w), statistics.median(w),
                 100.0 * sum(1 for x in w if x <= 2) / len(w)))


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT)
