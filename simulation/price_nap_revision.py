"""What the 2026-11-12 NAP Assignment revision costs, one dial at a time.

    python3 price_nap_revision.py [games]

Four things changed that the model can see, and they do not pull the same way:

  rewards   REQUEST_REWARD lost every dice-condition and names a colour, and
            DEMAND_REWARD pays on all 26 Demand faces. Pure gain.
  targets   six Demand Targets came down from 9 to 6, Suture's Request rose
            5 to 6. A gain: those six faces become clearable, which is what
            lets their new reward exist at all.
  pool      the Final Exam pool is one card per subject chosen at random
            instead of 1/2/3 by Credits taken in table order. A LOSS, and the
            big one - the old rule handed you three of the four cheapest
            exams in the box.
  following Unscheduled Demonstration bills per roll instead of per slot, and
            Where Did I Put That? now holds a die back unconditionally. Only
            visible at Tier I and above.

Run it before quoting any NAP figure measured before that date: every column
here is the same model with the dials moved, so the baseline column is the
published game and the difference is the revision.
"""
import sys

import nap

GAMES = int(sys.argv[1]) if len(sys.argv) > 1 else 4000
LEVELS = ("Easy", "Standard", "Hard", "Nobulous")

# name -> the dial settings that turn that piece OFF
OLD = {
    "rewards": {"TASK_REWARDS_2026_11_12": False},
    "targets": {"DEMAND_TARGETS_9": True},
    "pool": {"EXAM_POOL_BY_CREDITS": True},
}


def measure(level, tier, **dials):
    was = {k: getattr(nap, k) for k in dials}
    for k, v in dials.items():
        setattr(nap, k, v)
    goal, sb = nap.CREDITS_TO_LEAVE, nap.SETBACKS_IN_DECK
    nap.CREDITS_TO_LEAVE, nap.SETBACKS_IN_DECK = nap.LEVELS[level]
    try:
        return 100.0 * nap.run(games=GAMES, seed=20, tier=tier)
    finally:
        nap.CREDITS_TO_LEAVE, nap.SETBACKS_IN_DECK = goal, sb
        for k, v in was.items():
            setattr(nap, k, v)


def table(tier):
    cols = [("shipping", {})]
    everything = {}
    for name, dials in OLD.items():
        cols.append((name + " old", dials))
        everything.update(dials)
    cols.append(("all old", everything))
    print()
    print("Tier %s, Prodigy, FINF -1, %d games a cell" % (tier, GAMES))
    print("%-10s" % "level" + "".join("%13s" % c for c, _ in cols))
    for level in LEVELS:
        row = ["%-10s" % level]
        for _name, dials in cols:
            row.append("%12.1f%%" % measure(level, tier, **dials))
        print("".join(row))


if __name__ == "__main__":
    for tier in ("none", "III"):
        table(tier)
