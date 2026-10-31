"""Pricing the confidence mechanic: the Council drops a line of inquiry.

    python proto/confidence.py

Exploratory, and NOT applied. Jon asked whether completing Council Tests
should pay - "the imposter builds confidence". The five printed Reward
cards answer the cheap half of that and are now live in the finale
(simulation/finale.py REWARDS, worth +17.1). This prices the expensive
half: a reward that pays in CLOCK, the one currency the finale is short
of, because dice and Health measured nearly inert at +1.3 and +1.9.

THE VERDICT, from the table this file prints:

  IT IS AFFORDABLE IN ONE SHAPE ONLY. A buried Reward Exhibit discarding
  one card from the Dossier reads 55.9% at the shipped 15 Exhibits -
  inside the 47-57% band with no re-pitch at all. The confidence TRACK
  instead, every third burial, reads 67.0% and is simply too strong.

  IT CANNOT BE PAID FOR WITH A BIGGER DOSSIER. 18 Exhibits reads 4.2% and
  21 reads 0.1%. That is the cliff finale.py's header records: past 15
  the economy collapses, so there is no room to trade more work for the
  mechanic. REC cannot trim it either, since REC 2 is 20.2%. It would
  ship pinned near the top of the band with no way to centre it.

  IT TAXES THE DIAL. The recovery gap - what reading the wheel is worth,
  and the whole reason the attention rotates - falls from 9.2 to 5.6,
  about 40%. The pace gap rises from 17.2 to 22.4 in exchange. So the
  mechanic buys pacing pressure, which the finale already has, with the
  decision that makes it distinctive.

  Measured against the BEST AVAILABLE POLICY of 24, not one fixed policy,
  because pitching to a suboptimal player is the mistake this project
  already made once (see HANDOFF.md on the 2026-10-27 retune).

Three shapes are measured:

  reward   a buried REWARD Exhibit discards one card from the Dossier
           (5 of the 15 Exhibits dealt are Reward cards)
  every3   every third Exhibit buried discards one - a confidence TRACK
           rather than a card property
  none     the control

What matters as much as the win rate is whether it flattens the
decisions: a mechanic that makes the pace or the wheel irrelevant has
bought nothing, however thematic, so both gaps are reported per cell.

DROPPED 2026-10-31, on Jon's call. Kept as the record of the price. Nothing
in the shipped rules, cards or simulators refers to a confidence mechanic.
"""
import os
import statistics as st
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))

import random

import finale as F

GAMES = 3000
SEEDS = (11, 23, 47)
PACES = ("two", "clock", "ceil", "throttle")
RECOVS = ("best", "next", "horizon")
COMMITS = ("all", "adaptive")


def play(rng, mode, pace, recov, commit):
    g = F.Game(rng)
    buried = 0
    for _ in range(F.SESSIONS):
        if not g.deck and not g.active:
            return True
        standing = list(g.active)
        if not F.session(g, pace, recov, "dice", commit, "small"):
            return False
        for e in [x for x in standing if x not in g.active]:
            buried += 1
            drop = (mode == "reward" and e.name in F.REWARDS) or \
                   (mode == "every3" and buried % 3 == 0)
            if drop and g.deck:
                g.deck.pop(0)      # the Council stops asking about one
    return not g.deck and not g.active


def run(mode, pace="clock", recov="horizon", commit="all", seed=11,
        games=GAMES, **over):
    saved = {k: getattr(F, k) for k in over}
    for k, v in over.items():
        setattr(F, k, v)
    rng = random.Random(seed)
    try:
        return 100.0 * sum(1 for _ in range(games)
                           if play(rng, mode, pace, recov, commit)) / games
    finally:
        for k, v in saved.items():
            setattr(F, k, v)


def mean(mode, **kw):
    return st.mean(run(mode, seed=s, **kw) for s in SEEDS)


def best(mode, **over):
    """The best (pace, recov, commit) available, and what it wins."""
    cells = {}
    for p in PACES:
        for r in RECOVS:
            for c in COMMITS:
                cells[(p, r, c)] = mean(mode, pace=p, recov=r, commit=c,
                                        **over)
    k = max(cells, key=cells.get)
    pace_gap = max(cells[(p, k[1], k[2])] for p in PACES) - \
        min(cells[(p, k[1], k[2])] for p in PACES)
    rec_gap = max(cells[(k[0], r, k[2])] for r in RECOVS) - \
        min(cells[(k[0], r, k[2])] for r in RECOVS)
    return cells[k], k, pace_gap, rec_gap


def band(w):
    return "*" if 47.0 <= w <= 57.0 else " "


if __name__ == "__main__":
    print("PRICING THE CONFIDENCE MECHANIC")
    print("=" * 72)
    print("%d finales x %d seeds a cell, best of %d policies."
          % (GAMES, len(SEEDS), len(PACES) * len(RECOVS) * len(COMMITS)))
    print("* = inside the 47-57%% community band.")
    print()
    print("  %-34s %8s %8s %8s" % ("", "win", "pace", "recover"))
    print("  %-34s %8s %8s %8s" % ("", "", "gap", "gap"))
    rows = (("no confidence - as it ships", "none", {}),
            ("a Reward Exhibit drops one", "reward", {}),
            ("...at 18 Exhibits", "reward", {"DEAL": 6}),
            ("...at 21 Exhibits", "reward", {"DEAL": 7}),
            ("every 3rd burial drops one", "every3", {}),
            ("...at 18 Exhibits", "every3", {"DEAL": 6}),
            ("...at 21 Exhibits", "every3", {"DEAL": 7}))
    for lab, mode, over in rows:
        w, k, pg, rg = best(mode, **over)
        print("  %-34s %7.1f%%%s %7.1f %8.1f   %s"
              % (lab, w, band(w), pg, rg, "/".join(k)))
        sys.stdout.flush()
