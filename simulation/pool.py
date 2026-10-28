"""How much does the Imposter finale depend on the cards you bring in?

    python pool.py                 # 8,000 finales per cell
    python pool.py 20000

supply.py already shows that a real campaign hand and the standalone sample
score within about three points of each other. That compares two REALISTIC
hands and so cannot say whether the Research Pool matters at all. This
measures the span instead: the finale with no cards whatsoever against the
finale with a hand that cannot be improved, and then where inside that span
the printed pool actually sits.

The pool is 18 cards, 6 from each game, and only 9 of them do anything:
each game retains 3 and fills to 6 with Candidates, which reduce nothing
(nrj.Research.value_for returns 0 for a Candidate). A retained card pays
its printed value on a category match and a flat 2 off it. So the question
has three parts, and they are measured separately:

    how many cards    the size sweep, 0 to 9 useful cards
    whose cards       dropping each game's six in turn
    which cards       Specimen or not, Stable or Overheated

Every section patches nrj.build_pool rather than editing it, the way
supply.py and imposter.py hook what they measure.
"""
import collections
import random
import sys

import nrj

GAMES = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
# Captured before anything patches it: the sections that build on the
# printed pool have to call the real thing, not whatever is installed.
REAL_BUILD = nrj.build_pool
ALL_CATS = [c for cats in nrj.CATEGORIES.values() for c in cats]


# ------------------------------------------------------------------ pools
def card(game, category, match, retained=True, can_avoid=False):
    return nrj.Research(game, category, match, retained, can_avoid=can_avoid,
                        dot=random.choice(nrj.COLORS))


def empty(rng):
    """No Research Pool at all - the floor the finale stands on."""
    return []


def candidates_only(rng):
    """All 18 cards present and every one of them a Candidate."""
    return [card("NAP", rng.choice(ALL_CATS), 0, retained=False)
            for _ in range(18)]


def ideal(rng):
    """18 retained cards, best printed value, spread across the domains.

    Not reachable in play - it is the ceiling, to size the span.
    """
    pool = []
    for i in range(18):
        domain = ("Knowledge", "Physical", "Cover-Up")[i % 3]
        pool.append(card("BAT", rng.choice(nrj.CATEGORIES[domain]), 5))
    return pool


def sized(useful):
    """`useful` retained cards in the printed proportions, rest Candidates."""
    def make(rng):
        pool = []
        spec = [("NAP", "Knowledge", 2), ("BAT", "Physical", 3),
                ("AoS", "Cover-Up", 4)]
        for i in range(useful):
            game, domain, value = spec[i % 3]
            pool.append(card(game, rng.choice(nrj.CATEGORIES[domain]), value,
                             can_avoid=(game == "AoS" and i % 6 >= 3)))
        while len(pool) < 18:
            pool.append(card("NAP", rng.choice(ALL_CATS), 0, retained=False))
        return pool
    return make


def without(game_dropped):
    """The printed pool, minus everything one game contributes."""
    def make(rng):
        return [c for c in REAL_BUILD(rng) if c.game != game_dropped]
    return make


def printed(rng):
    return REAL_BUILD(rng)


# ---------------------------------------------------------------- harness
def win(maker, games, **over):
    """Win rate with `maker` building every pool."""
    real = nrj.build_pool
    saved = {k: getattr(nrj, k) for k in over}
    for k, v in over.items():
        setattr(nrj, k, v)

    def patched(rng, mode="standalone", bat_cards=None, aos_cards=None):
        return maker(rng)

    nrj.build_pool = patched
    try:
        return 100 * nrj.run("standalone", games)
    finally:
        nrj.build_pool = real
        for k, v in saved.items():
            setattr(nrj, k, v)


def spending(games):
    """How many pool cards actually get spent, and does the pool run dry?

    If the finale never spends what it is given, extra cards are worth
    nothing however good they are, and that is the whole answer.
    """
    real_spend = nrj.Game.spend
    stats = collections.Counter()
    held = []

    def spend(self, sid, target):
        before = len(self.pool)
        out = real_spend(self, sid, target)
        stats["spent"] += before - len(self.pool)
        stats["calls"] += 1
        return out

    real_play = nrj.Game.play

    def play(self):
        r = real_play(self)
        stats["games"] += 1
        useful = sum(1 for c in self.pool if c.retained)
        held.append(useful)
        if useful == 0:
            stats["dry"] += 1
        return r

    nrj.Game.spend, nrj.Game.play = spend, play
    try:
        nrj.run("standalone", games)
    finally:
        nrj.Game.spend, nrj.Game.play = real_spend, real_play
    n = float(stats["games"])
    return (stats["spent"] / n, sum(held) / n, 100.0 * stats["dry"] / n)


def main(games=GAMES):
    print()
    print("THE RESEARCH POOL - what the cards you bring are worth")
    print("=" * 66)
    print("%d finales per cell, standalone, retuned policy" % games)

    base = win(printed, games)
    floor = win(empty, games)
    print()
    print("1. THE SPAN")
    print("   %-34s %6.1f%%" % ("no Research Pool at all", floor))
    print("   %-34s %6.1f%%" % ("every card a Candidate", win(candidates_only, games)))
    print("   %-34s %6.1f%%   <-- as printed" % ("the printed pool", base))
    print("   %-34s %6.1f%%" % ("18 retained, best value", win(ideal, games)))
    print()
    print("   So the pool is worth %.1f points against bringing nothing,"
          % (base - floor))
    print("   and a perfect hand would add %.1f more."
          % (win(ideal, games) - base))

    print()
    print("2. HOW MANY CARDS - useful (retained) cards, rest Candidates")
    print("   A flat value mix - NAP 2, BAT 3, AoS 4 - so the 9-card row")
    print("   reads below the printed pool, whose nine include Specimens at")
    print("   5 and Stable Programs at 4. The shape is the point, not the")
    print("   level: this is where the cliff is.")
    print("   %-10s %8s %8s" % ("useful", "win", "vs printed"))
    for useful in (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 12, 18):
        w = win(sized(useful), games)
        print("   %-10d %7.1f%% %+8.1f%s"
              % (useful, w, w - base, "   <-- printed has 9" if useful == 9 else ""))
        sys.stdout.flush()

    print()
    print("3. WHOSE CARDS - drop everything one game contributes")
    print("   %-16s %8s %8s" % ("", "win", "vs printed"))
    for game in ("NAP", "BAT", "AoS"):
        w = win(without(game), games)
        print("   %-16s %7.1f%% %+8.1f" % ("without " + game, w, w - base))
        sys.stdout.flush()

    print()
    print("4. WHICH CARDS - the choices a real campaign actually makes")
    rows = [
        ("BAT banks a Specimen", dict(bat_cards=[5, 3, 3])),
        ("BAT banks no Specimen", dict(bat_cards=[3, 3, 3])),
        ("BAT banks 1 card only", dict(bat_cards=[3])),
        ("AoS all Stable", dict(aos_cards=[True] * 3)),
        ("AoS all Overheated", dict(aos_cards=[False] * 3)),
        ("best realistic hand", dict(bat_cards=[5, 3, 3],
                                     aos_cards=[True] * 3)),
        ("worst realistic hand", dict(bat_cards=[3, 3, 3],
                                      aos_cards=[False] * 3)),
    ]
    print("   %-24s %8s %8s" % ("", "win", "vs printed"))
    for label, kw in rows:
        real = nrj.build_pool
        w = 100 * nrj.run("standalone", games, **kw)
        nrj.build_pool = real
        print("   %-24s %7.1f%% %+8.1f" % (label, w, w - base))
        sys.stdout.flush()

    print()
    print("   You cannot arrive with less than a full pool: rules/nrj.html")
    print("   says to win all three games and replay any you lose, and that")
    print("   each WON game contributes 6. So section 2 is a fact about the")
    print("   design, not a risk a campaign runs - what a player can")
    print("   actually vary is the spread in this section.")
    print()
    print("5. DOES THE POOL EVEN BIND?")
    spent, left, dry = spending(games)
    print("   cards spent per finale        %4.1f of 18" % spent)
    print("   useful cards left unspent     %4.1f of 9" % left)
    print("   finales that used every one   %4.1f%%" % dry)


if __name__ == "__main__":
    main()
