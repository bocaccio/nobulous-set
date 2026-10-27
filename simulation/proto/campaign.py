"""What the Rats carry out of a won battle, for the NRJ campaign.

    python campaign.py          # 6000 games per configuration

rules/bat.html: "After a successful battle, retain up to 3 Upgrade cards
held by Rats that survived, of which at most 1 may be a Specimen. ... If
fewer than 3 eligible Upgrades survive, fill the remaining slots with
candidates so BAT contributes 6 cards in total."

So the question is how often a win actually leaves 3 retainable Upgrades on
surviving Rats. Making a Rat's Upgrade SPENT whenever it blocks burns them
far faster than the old rule, which only destroyed a card when the blow met
its Value - so this is worth knowing before the campaign is tuned.

Specimens are the only Value 5 cards in the game (Upgrades are 2-4,
Modifications 3-4), so Value identifies them without a flag.
"""
import random
import statistics
import sys

import bat
import trial

SPEC = {"Easy": 5, "Standard": 6, "Hard": 7, "Nobulous": 8}
HEALTH = {"Easy": 9, "Standard": 10, "Hard": 12, "Nobulous": 14}
LEVELS = ("Easy", "Standard", "Hard", "Nobulous")


def survey(difficulty="Standard", games=6000, **over):
    """Upgrades left on standing Rats, counted only on wins."""
    bat.PROTO.update(trial.OFF)
    cfg = dict(trial.CONFIG)
    cfg["health"] = HEALTH[difficulty]
    cfg.update(over)
    bat.PROTO.update(cfg)
    bat.DIFFICULTY[difficulty] = (SPEC[difficulty], 0)

    held, specimens, wins, played = [], [], 0, 0
    for i in range(games):
        g = bat.Game(difficulty, random.Random(i), card_effects=True,
                     sides="random", commit_policy="threshold",
                     battle_rec_bonus=2)
        won = g.play()
        played += 1
        if not won:
            continue
        wins += 1
        alive = [r for r in g.rats if not r.down]
        cards = [u for r in alive for u in r.upgrades]
        held.append(len(cards))
        specimens.append(sum(1 for u in cards if u.value == 5))
    if not held:
        return None
    return dict(
        winrate=100.0 * wins / played,
        mean=statistics.mean(held),
        median=statistics.median(held),
        spec=statistics.mean(specimens),
        short=100.0 * sum(1 for h in held if h < 3) / len(held),
        zero=100.0 * sum(1 for h in held if h == 0) / len(held),
        dist=[100.0 * sum(1 for h in held if h == k) / len(held)
              for k in range(5)],
    )


def main(games=6000):
    bat.RAT_DICE_CAP = 99                      # the cap is gone
    print("Upgrades still held by standing Rats, on a WIN")
    print("(the campaign wants 3, of which at most 1 a Specimen)")
    print()
    print("%-12s %8s %7s %8s %9s %11s"
          % ("difficulty", "win", "mean", "median", "Specimens", "short of 3"))
    for d in LEVELS:
        r = survey(d, games)
        if r:
            print("%-12s %7.1f%% %7.2f %8.0f %9.2f %10.0f%%"
                  % (d, r["winrate"], r["mean"], r["median"], r["spec"],
                     r["short"]))

    print()
    print("Standard, how the count is distributed on a win:")
    r = survey("Standard", games)
    for k in range(5):
        print("   %d Upgrades %6.0f%%" % (k, r["dist"][k]))

    print()
    print("Does spending armor to block cause this?  (Standard)")
    print("   %-26s %7s %7s %11s" % ("", "win", "mean", "short of 3"))
    for label, spend in (("Upgrade spent on block", True),
                         ("old rule: only shatters", False)):
        r = survey("Standard", games, armor_spend=spend)
        print("   %-26s %6.1f%% %7.2f %10.0f%%"
              % (label, r["winrate"], r["mean"], r["short"]))


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 6000)
