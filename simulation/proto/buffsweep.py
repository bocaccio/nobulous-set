"""Re-tune Buff HP against the PROTOTYPE rules.

    python buffsweep.py            # 4000 games per cell
    python buffsweep.py 8000

The shipping dial (3 / 4 / 7 / 11) was calibrated against a battle that no
longer exists: threshold damage, the 8-round clock and spent armor all move
the win rate, so every one of those four numbers has to be found again.

Specimen count stays at the published 5 / 6 / 7 / 8 - that is the Upgrade
deck, which the prototype does not touch - and only Buff HP is swept.

Two candidate ladders are reported, because re-tuning from scratch is the
moment to decide which one BAT wants:

  CURRENT  49 / 43 / 32 / 21, the shipping shape, whose steps are uneven
           (-6 / -11 / -11): a gentle on-ramp, then two hard drops.
  EVEN     50 / 40 / 30 / 20, three even steps of about ten points.

Neither is picked here. The table is printed in full so the choice is made
on the numbers rather than on the argmin.
"""
import sys

import bat
import trial

SPEC = {"Easy": 5, "Standard": 6, "Hard": 7, "Nobulous": 8}
LADDERS = {
    "CURRENT 49/43/32/21": {"Easy": 49, "Standard": 43, "Hard": 32,
                            "Nobulous": 21},
    "EVEN    50/40/30/20": {"Easy": 50, "Standard": 40, "Hard": 30,
                            "Nobulous": 20},
}
TRACK = range(0, 16)          # the printed Buff HP card is 15 spaces


def main(games=4000):
    print("Buff HP re-tune against the PROTOTYPE rules")
    print("threshold damage, 8-round clock, Health 4, break-banish 1,")
    print("Upgrades spent to block, battle recovery REC+2, %d games per cell."
          % games)
    print()
    print("%-10s" % "Buff HP" + "".join("%7d" % b for b in TRACK))

    rows = {}
    for name in ("Easy", "Standard", "Hard", "Nobulous"):
        row = []
        for buff in TRACK:
            bat.DIFFICULTY[name] = (SPEC[name], buff)
            row.append(trial.trial(name, games=games, policy="threshold",
                                   **trial.CONFIG)["win"])
        rows[name] = row
        print("%-10s" % name + "".join("%6.1f%%" % v for v in row), flush=True)

    for label, target in sorted(LADDERS.items()):
        print()
        print(label)
        prev = None
        for name in ("Easy", "Standard", "Hard", "Nobulous"):
            row = rows[name]
            best = min(range(len(row)), key=lambda b: abs(row[b] - target[name]))
            step = "" if prev is None else "  (%+.1f)" % (row[best] - prev)
            prev = row[best]
            print("  %-10s target %2d%% -> Buff HP %2d  (%.1f%%)%s"
                  % (name, target[name], best, row[best], step))


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 4000)
