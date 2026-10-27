"""Can AoS be given a dice economy, and what does it cost?

    python aoseconomy.py            # 2500 games per cell

AoS measured 1% of games ever dropping to 2 or fewer available dice, against
NAP's 20% (see dicetension.py). The brake on over-allocating exists - every
die past Target+1 burns, plus one more for beating the Target by 2 or more -
but exhausted dice flow back through a generous per-Program recovery, so it
taxes waste without ever threatening supply.

Two levers, both in aos.py and both defaulting to the printed rules:

  OVERKILL_SCALE   burn one die per point ABOVE Target+1, instead of a flat
                   one die however far you overshoot.
  RECOVERY_DELTA   cut the REC recovered each Program.

Reported per setting: the win rate (mean of the six Technicians, as
table.py reports it) and the dice pressure the change actually buys.
"""
import random
import statistics
import sys

import aos

LEVELS = ("Easy", "Standard", "Hard", "Nobulous")


def winrate(level, games):
    """Mean of the six Technicians, matching table.py."""
    return 100 * statistics.mean(
        aos.run(level, games, tech=t) for t in aos.TECHS)


def pressure(level, games):
    """Share of games whose pool ever drops to 2 or fewer, and the trough."""
    troughs = []
    for i in range(games):
        g = aos.Game("Specialized", random.Random(i),
                     composition=aos.LEVELS[level])
        seen = []
        real = g.allocate

        def hooked(*a, **k):
            seen.append(len(g.available))
            return real(*a, **k)
        g.allocate = hooked
        g.play()
        if seen:
            troughs.append(min(seen))
    if not troughs:
        return 0.0, 0.0
    return (statistics.mean(troughs),
            100.0 * sum(1 for t in troughs if t <= 2) / len(troughs))


def setting(label, games, scale=False, delta=0):
    aos.OVERKILL_SCALE = scale
    aos.RECOVERY_DELTA = delta
    wins = [winrate(l, games) for l in LEVELS]
    trough, tight = pressure("Standard", games)
    print("%-28s %s | %6.1f %6.0f%%"
          % (label, "".join("%8.1f%%" % w for w in wins), trough, tight),
          flush=True)


def main(games=2500):
    print("AoS dice economy. Win rate is the mean of the six Technicians;")
    print("trough and tight are measured at Standard. %d games per cell."
          % games)
    print()
    print("%-28s %8s %8s %8s %9s | %6s %7s"
          % ("", "Easy", "Standard", "Hard", "Nobulous", "trough", "<=2"))
    print("-" * 82)
    setting("as printed", games)
    print()
    setting("scaled over-allocation", games, scale=True)
    print()
    for d in (-1, -2):
        setting("recovery REC%d" % d, games, delta=d)
    print()
    for d in (-1, -2):
        setting("scaled + recovery REC%d" % d, games, scale=True, delta=d)
    aos.OVERKILL_SCALE, aos.RECOVERY_DELTA = False, 0


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 2500)
