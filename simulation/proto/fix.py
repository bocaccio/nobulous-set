"""Candidate repairs for the Imposter Scenario, measured.

    python proto/fix.py            # 4000 games per cell, from simulation/

imposter.py's diagnosis, in one line: the finale has a Health clock and a
dice floor that never touch. The pool falls from 17 to exactly REC by the
fourth attempt and sits there; the Targets climb past it; and the one clause
that would make dice a currency - "lose 1 Health OR banish 2 available
dice" - is offered at the trough of the pool, when 90% of the time there is
nothing to pay it with.

So a repair is not judged on win rate alone. Four things are reported:

  win       distance from the ~50% a finished game in this system sits at.
  tension   dice available when asked to commit, on dicetension.py's scale.
            A real dice game shows `low` high and `empty` non-zero. NAP
            scores 32% and 3.2%; the finale scores 0% and 0.0%.
  shape     the pool at attempts 1, 5 and 9, and dice banished per game. A
            repair that works makes the pool DECLINE rather than plateau -
            running out has to be possible for it to be a worry.
  cliff     the swing from one point of starting Health. The printed finale
            moves 23 to 32 points on that one step, against about 4 for a
            point of Tyrant Health in BAT, so it cannot be tuned. A repair
            should flatten this.

The candidates are described in nrj.py beside the dials.
"""
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import nrj
from imposter import measure, tension, win

GAMES = 4000

CANDIDATES = [
    ("the printed rules", {}),
    ("A  banish 1 die per missing success, max 2", dict(PARTIAL_PAY=2)),
    ("A+ the same, max 4", dict(PARTIAL_PAY=4)),
    ("B  failure trade may banish exhausted dice", dict(BANISH_EXHAUSTED=True)),
    ("C  recover 1 extra die after a success", dict(RECOVER_ON_PASS=1)),
    ("C+ recover 2 extra dice after a success", dict(RECOVER_ON_PASS=2)),
    ("D  every printed Target -2", dict(TARGET_SHIFT=-2)),
    ("D+ every printed Target -3", dict(TARGET_SHIFT=-3)),
    ("E  Suspicion capped at 3", dict(SUSPICION_CAP=3)),
    ("A+B together", dict(PARTIAL_PAY=2, BANISH_EXHAUSTED=True)),
    ("A+C together", dict(PARTIAL_PAY=2, RECOVER_ON_PASS=1)),
    ("A+B+E together", dict(PARTIAL_PAY=2, BANISH_EXHAUSTED=True,
                            SUSPICION_CAP=3)),
    ("B+D  trade payable, Targets -2",
     dict(BANISH_EXHAUSTED=True, TARGET_SHIFT=-2)),
    ("F  REC -1 per 2 Suspicion", dict(REC_PER_SUSPICION=2)),
    ("F+ REC -1 per Suspicion", dict(REC_PER_SUSPICION=1)),
    ("G  1 committed die banished on a failure", dict(FAIL_BANISHES=1)),
    ("G+ 2 committed dice banished on a failure", dict(FAIL_BANISHES=2)),
    ("F+G  floor falls and failure drains",
     dict(REC_PER_SUSPICION=2, FAIL_BANISHES=1)),
    ("F+G+D  the same, Targets -2",
     dict(REC_PER_SUSPICION=2, FAIL_BANISHES=1, TARGET_SHIFT=-2)),
    ("F+G+D+ the same, Targets -3",
     dict(REC_PER_SUSPICION=2, FAIL_BANISHES=1, TARGET_SHIFT=-3)),
    ("F+G+C+D  plus recover 1 on a success",
     dict(REC_PER_SUSPICION=2, FAIL_BANISHES=1, RECOVER_ON_PASS=1,
          TARGET_SHIFT=-2)),
    ("H  REC = 3 - Suspicion, floor 0",
     dict(REC_PER_SUSPICION=1, REC_FLOOR=0)),
    ("H  the same, 5 starting Health  <<< RECOMMENDED",
     dict(REC_PER_SUSPICION=1, REC_FLOOR=0, START_HP=5)),
    ("H  the same plus partial payment (redundant)",
     dict(REC_PER_SUSPICION=1, REC_FLOOR=0, START_HP=5, PARTIAL_PAY=1)),
]

# H, with Health as the difficulty dial the finale has never had.
LADDER = [("Nobulous", 3), ("Hard", 4), ("Standard", 5), ("Easy", 6)]


def row(label, over, games):
    p = measure(games, **over)
    t = tension(p)
    first = statistics.mean(p.by_attempt[0])
    mid = statistics.mean(p.by_attempt[4]) if p.by_attempt[4] else float("nan")
    last = statistics.mean(p.by_attempt[-1]) if p.by_attempt[-1] \
        else float("nan")
    hp = over.get("START_HP", nrj.START_HP)
    lo = measure(games, **dict(over, START_HP=hp - 1))
    hi = measure(games, **dict(over, START_HP=hp + 1))
    cliff = (win(hi) - win(lo)) / 2.0
    print("%-42s %6.1f%% | %5.1f %5.0f%% %6.1f%% | %5.1f %5.1f %5.1f %5.2f |"
          " %5.1f"
          % (label, win(p), t[0], t[1], t[2], first, mid, last,
             statistics.mean(p.banished), cliff))
    return p


def main(games=GAMES):
    print("CANDIDATE REPAIRS FOR THE IMPOSTER SCENARIO, %d games per cell"
          % games)
    print("every dial defaults to the printed rules; see nrj.py")
    print()
    print("%-42s %7s | %-20s | %-27s | %5s"
          % ("", "win", "tension at commit", "pool shape", "cliff"))
    print("%-42s %7s | %5s %6s %7s | %5s %5s %5s %5s | %5s"
          % ("", "", "mean", "<=2", "empty", "att1", "att5", "att9", "bnsh",
             "+-1HP"))
    print("-" * 118)
    for label, over in CANDIDATES:
        row(label, over, games)
    print("-" * 118)
    print()
    print("for scale, dicetension.py on the three games:")
    print("  NAP  (Standard)   mean 4.3   <=2 32%   empty 3.2%")
    print("  AoS  (Standard)   mean 6.2   <=2 22%   empty 0.9%")
    print("  a point of Tyrant Health in BAT is worth about 4 points of win")
    print("  rate; a point of Imposter Health is worth 20 to 30.")
    print()
    print("WHAT THE TENSION COLUMN SAYS. Only the candidates that touch the")
    print("RECOVERY FLOOR move it. A, B, D, E and G leave `<=2` at 0% and")
    print("`empty` at 0.0% however far they move the win rate - G banishes")
    print("eight dice a game and changes the tension not at all. The reason")
    print("is that 'recover up to REC exhausted dice' refills the pool to a")
    print("fixed floor every attempt whatever happened, so the pool cannot")
    print("trend toward zero and running out cannot become a worry. Win rate")
    print("is reachable with any dial here; tension is reachable only by")
    print("making the floor itself fall.")
    print()
    print("RECOMMENDED: H. One line on the Imposter card -")
    print("  \"Your REC is 3 minus the number of cards in the Suspicion row.\"")
    print("plus starting Health 5 rather than 4. No new components: the")
    print("Suspicion row is already face-up on the table, and it already")
    print("drives the Target climb, so the more the Council suspects you the")
    print("less you recover. It lands at the middle of the community band")
    print("with the highest dice tension in the set, and the pool declines")
    print("17 -> 3.3 -> 0.7 across the nine attempts instead of sitting on")
    print("a floor of 3. Partial payment on top is redundant and pushes it")
    print("to 82%.")
    print()
    print("AND IT GIVES THE FINALE A DIFFICULTY DIAL, which it has never")
    print("had. Starting Health, everything else as printed:")
    print()
    print("   %-12s %7s %6s %7s" % ("", "win", "<=2", "empty"))
    for label, hp in LADDER:
        q = measure(games, REC_PER_SUSPICION=1, REC_FLOOR=0, START_HP=hp)
        t = tension(q)
        print("   %-12s %6.1f%% %5.0f%% %6.1f%%  (%d Health)"
              % (label, win(q), t[1], t[2], hp))
    print()
    print("The rungs are wider than the other three games', because nine")
    print("pass/fail attempts against a small failure budget amplify any")
    print("dial about ninefold. That steepness is the finale's real")
    print("structural problem and it is not fixed here - but it is what")
    print("makes one number serve as a four-rung ladder.")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else GAMES)
