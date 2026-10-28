"""PROTOTYPE: the Imposter finale with each game's cards gated to its domain.

    python proto/finale2.py

Exploratory, not shipped. The brief:

  * NAP cards affect only Knowledge checks, BAT only Physical, AoS only
    Cover-Up. No off-domain spending at all.
  * the Suspicion row stays, and stays tied to REC.
  * AoS's lever is Stable against Overheated, BAT's is Specimen against
    regular Upgrade. NAP's lever is open, so three candidates are measured.

WHY THE TARGETS MUST MOVE. In the shipped finale a retained card reduces 2
off-category and its printed Value on a match, and only 16% of spends land
on a match - so 84% of all reduction comes from off-domain spending. Gating
removes that: measured on the shipped Targets, strict gating wins 1.2% and
leaves most of the hand dead. The pool becomes about a sixth as liquid, so
the whole Target ladder has to come down with it.

WHAT THE GEOMETRY GIVES YOU. The deck is 4 Scenarios from each domain and 9
attempts are made, which is exactly 3.00 per domain on average. Each game
contributes 3 retained cards. So a gated finale is one card per attempt of
its own domain - a much cleaner correspondence than the current pool, and
the reason the rework is worth doing even though it costs a re-pitch.

The per-domain COUNT varies though, and that variance is the design's main
risk: a draw with 5 Knowledge Scenarios leaves two of them unanswerable
however well NAP went. Reported below as `short`.
"""
import collections
import random
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import nrj
from dice import EV_REROLL

GAMES = 20000

# ---------------------------------------------------------------- the dials
TARGET_SHIFT = -4         # the re-pitch; swept below
SPECIMEN = 6              # BAT's lever: Specimen against regular Upgrade
UPGRADE = 3
STABLE = 6                # AoS's lever: pure reduction
OVERHEATED = 3            # less reduction, but it can buy an avoid
NAP_VALUE = 4
CANDIDATE = 1             # a Candidate's within-domain reduction
CAND_AVOID = 1            # how many AoS Candidates can buy an avoid
NAP_LEVER = "none"        # "none" | "suspicion" | "recover"
POLICY = "cheapest"       # "cheapest" | "biggest" | "hoard"
SCALE = 1.0               # multiplies every printed card value

DOMAIN_OF = {"NAP": "Knowledge", "BAT": "Physical", "AoS": "Cover-Up"}


def build(rng, mode="standalone", bat_cards=None, aos_cards=None):
    """The printed 18, re-valued for a gated pool."""
    pool = []

    def add(game, value, retained, avoid=False):
        value = int(round(value * SCALE))
        c = nrj.Research(game, rng.choice(nrj.CATEGORIES[DOMAIN_OF[game]]),
                         value, retained, can_avoid=avoid,
                         dot=rng.choice(nrj.COLORS))
        pool.append(c)

    for _ in range(3):                                  # NAP: 3 exams faced
        add("NAP", NAP_VALUE, True)
    specimen = rng.random() < 0.5
    for i in range(3):                                  # BAT: held Upgrades
        add("BAT", SPECIMEN if (specimen and i == 0) else UPGRADE, True)
    for _ in range(3):                                  # AoS: Programs faced
        stable = rng.random() < 0.65
        add("AoS", STABLE if stable else OVERHEATED, True, avoid=not stable)
    made = 0
    for game in ("NAP", "BAT", "AoS"):                  # 3 Candidates each
        for _ in range(3):
            avoid = game == "AoS" and made < CAND_AVOID
            add(game, CANDIDATE, CANDIDATE > 0, avoid=avoid)
            made += avoid
    return pool


def spend(self, sid, target):
    """Own-domain cards only, and never spend into a lost cause."""
    domain = nrj.SCENARIOS[sid][1]
    mine = [c for c in self.pool if DOMAIN_OF[c.game] == domain and c.match]
    reach = self.expected(self.available)

    # NAP's lever: talk a card out of the Suspicion row instead of reducing.
    if NAP_LEVER == "suspicion" and domain == "Knowledge" and self.suspicion:
        if reach >= target or not mine:
            # Nothing to gain here, so buy back REC and every later Target.
            if mine:
                self.pool.remove(mine[0])
                self.suspicion -= 1
            return target
    if NAP_LEVER == "recover" and domain == "Knowledge" and mine \
            and self.exhausted and reach >= target:
        card = mine[0]
        self.pool.remove(card)
        for c in list(self.exhausted):
            if c == card.dot:
                self.exhausted.remove(c)
                self.available.append(c)
                break
        return target

    if reach + sum(c.match for c in mine) < target:
        return target            # unanswerable: keep the cards for later
    if POLICY == "biggest":
        mine.sort(key=lambda c: -c.match)      # dump the best card now
    elif POLICY == "cheapest":
        mine.sort(key=lambda c: c.match)       # smallest that still works
    else:
        # "hoard": smallest sufficient, but keep the best card back while
        # Suspicion is still climbing - later Scenarios cost more.
        mine.sort(key=lambda c: c.match)
        if self.suspicion < 2 and len(mine) > 1:
            best = max(mine, key=lambda c: c.match)
            if reach + sum(c.match for c in mine if c is not best) >= target:
                mine.remove(best)
    for card in mine:
        if reach >= target:
            break
        target -= card.match
        self.pool.remove(card)
        if card.game == "NAP" and self.special_dot is None:
            self.special_dot = card.dot
    return max(0, target)


def measure(games=GAMES, **over):
    saved = {k: globals()[k] for k in over}
    globals().update(over)
    real_build, real_spend = nrj.build_pool, nrj.Game.spend
    base_shift = nrj.TARGET_SHIFT
    nrj.build_pool, nrj.Game.spend = build, spend
    nrj.TARGET_SHIFT = TARGET_SHIFT
    stats = collections.Counter()
    real_attempt = nrj.Game.attempt

    def attempt(self):
        sid = self.deck[0] if self.deck else None
        out = real_attempt(self)
        if sid is not None:
            domain = nrj.SCENARIOS[sid][1]
            stats[domain] += 1
            if not any(DOMAIN_OF[c.game] == domain and c.match
                       for c in self.pool):
                stats["short"] += 1
        return out

    nrj.Game.attempt = attempt
    try:
        w = 100 * nrj.run("standalone", games)
    finally:
        nrj.build_pool, nrj.Game.spend = real_build, real_spend
        nrj.Game.attempt = real_attempt
        nrj.TARGET_SHIFT = base_shift
        globals().update(saved)
    total = sum(stats[d] for d in ("Knowledge", "Physical", "Cover-Up"))
    return w, 100.0 * stats["short"] / max(1, total)


if __name__ == "__main__":
    print("PROTOTYPE - a gated Imposter finale, re-pitched")
    print("=" * 70)
    print("%d finales a cell. The first pass pitched this at 96-100%%; card" % GAMES)
    print("values are now scaled down against the printed Targets instead.")
    print()
    print("1. FINDING THE PITCH - card value scale against Target shift")
    print("   %-8s" % "scale" + "".join("%11s" % ("shift %+d" % s)
                                        for s in (0, 1, 2, 3)))
    for scale in (1.0, 0.75, 0.5, 0.35):
        cells = []
        for shift in (0, 1, 2, 3):
            w, short = measure(SCALE=scale, TARGET_SHIFT=shift)
            cells.append("%5.1f%%" % w)
        print("   %-8s" % scale + "".join("%11s" % c for c in cells))
        sys.stdout.flush()

    print()
    print("2. IS THERE A DECISION IN IT? the policy gap at each pitch")
    print("   If spending cleverly scores no better than spending blindly,")
    print("   the gating has made the finale rote.")
    print("   %-26s %10s %10s %10s %8s"
          % ("pitch", "cheapest", "biggest", "hoard", "gap"))
    for scale, shift in ((1.0, 2), (0.75, 1), (0.5, 0), (0.35, 0)):
        ws = []
        for pol in ("cheapest", "biggest", "hoard"):
            w, _ = measure(SCALE=scale, TARGET_SHIFT=shift, POLICY=pol)
            ws.append(w)
        print("   scale %-4s shift %+d       %9.1f%% %9.1f%% %9.1f%% %7.1f"
              % (scale, shift, ws[0], ws[1], ws[2], max(ws) - min(ws)))
        sys.stdout.flush()

    print()
    print("3. FOR COMPARISON - the policy gap in the SHIPPED finale")
    print("   Not gated, so off-domain spending is available.")
    real = 100 * nrj.run("standalone", GAMES)
    print("   shipped, as printed                     %5.1f%%" % real)
