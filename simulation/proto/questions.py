"""Two structural questions about the reworked battle.

    python questions.py            # 4000 games per cell

1. THE 6-DICE CAP. Is it load-bearing or vestigial? The shared pool is only
   about 10 dice and recovery returns REC+2, so committing much more than 6
   may already be self-limiting. Raising the cap says which.

2. THE BUFF HP CARD. It was added as a workaround: the Health chip only goes
   to 20, so the Tyrant's bulk had to live somewhere else. With Health cut
   to 4 that reason is gone, and the same points could simply be Health -
   which would put the chip phase at the END of the fight instead of the
   start. Both are measured here.

   front = Buff HP card first, then the five Splices, then Health 4
   folded = no Buff card; Health = 4 + that difficulty's Buff, walls first
"""
import sys

import bat
import trial

BUFF = {"Easy": 5, "Standard": 6, "Hard": 8, "Nobulous": 10}
SPEC = {"Easy": 5, "Standard": 6, "Hard": 7, "Nobulous": 8}
LEVELS = ("Easy", "Standard", "Hard", "Nobulous")


def set_dial(name, buff):
    bat.DIFFICULTY[name] = (SPEC[name], buff)


def row(label, fn):
    print("  %-26s" % label, end="")
    for name in LEVELS:
        print("%9.1f%%" % fn(name), end="")
    print(flush=True)


def main(games=4000):
    print("%-28s" % "" + "".join("%10s" % n for n in LEVELS))

    print()
    print("1. The 6-dice cap  (Buff at the front, as it ships)")
    for cap in (6, 8, 10):
        def run(name, cap=cap):
            set_dial(name, BUFF[name])
            bat.RAT_DICE_CAP = cap
            return trial.trial(name, games=games, policy="threshold",
                               **trial.CONFIG)["win"]
        row("commit up to %d" % cap, run)
    bat.RAT_DICE_CAP = 6

    print()
    print("2. Where the chip damage sits")

    def front(name):
        set_dial(name, BUFF[name])
        cfg = dict(trial.CONFIG)
        cfg["health"] = 4
        return trial.trial(name, games=games, policy="threshold", **cfg)["win"]

    def folded(name):
        set_dial(name, 0)                      # no Buff HP card at all
        cfg = dict(trial.CONFIG)
        cfg["health"] = 4 + BUFF[name]         # those points become Health
        return trial.trial(name, games=games, policy="threshold", **cfg)["win"]

    row("Buff card at the front", front)
    row("folded into Health", folded)

    print()
    print("   folded Health totals: " + ", ".join(
        "%s %d" % (n, 4 + BUFF[n]) for n in LEVELS) + "  (dial maximum 20)")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 4000)
