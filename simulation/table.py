"""Results tables for NAP, BAT and AoS, split by difficulty and NRJ tier.

    python table.py              # 20,000 games per cell
    python table.py 4000         # quicker pass

Every cell is a modeled win rate. Tier columns are cumulative - "each tier
includes the ones before it" - and are NOT difficulty levels: Tier II is the
pressure peak and Tier III hands tools back.

Reference: the 20 Strong Community Game Stats sheet puts the published games
at 47-57%, and 53% across 955 recorded games. That is the band a finished
game in this system lands in, and it is the yardstick for the tables below.
"""
import sys
import time

import aos
import bat
import cards
import nap
import nrj

DEFAULT = 20000

# NAP difficulty is the Credit goal; the FINF dial is a separate setting.
NAP_LEVELS = {"Easy": 5, "Standard": 6, "Hard": 7, "Nobulous": 8}
NAP_APPS = ["Prodigy", "Slacker", "Technician", "Savant", "Opportunist", "Lab Rat"]
TIERS = ["none", "I", "II", "III"]

# 20 Strong Community Game Stats, read 2026-09-20. Published titles only.
COMMUNITY = [
    ("Solar Sentinels", 282, 49),
    ("Too Many Bones", 194, 55),
    ("Hoplomachus: Victorum", 103, 53),
    ("Tanglewoods: Red", 122, 47),
    ("Tanglewoods: White", 49, 53),
    ("Tanglewoods: Gold", 68, 57),
    ("Tanglewoods: Rose", 35, 31),
    ("all titles", 955, 53),
]


def pct(x):
    return "%.1f%%" % (100 * x)


def grid(title, subtitle, rows, runner, games, notes=()):
    print()
    print("=" * 66)
    print(title)
    print("=" * 66)
    print("  %s" % subtitle)
    print()
    print("  %-22s %9s %9s %9s %9s" % ("", "no NRJ", "Tier I", "Tier II", "Tier III"))
    for label, key in rows:
        cells = [pct(runner(key, t, games)) for t in TIERS]
        print("  %-22s %9s %9s %9s %9s" % tuple([label] + cells))
    for n in notes:
        print("  %s" % n)


def main(games=DEFAULT):
    started = time.time()
    print()
    print("THE NOBULOUS SET - results by difficulty and NRJ tier")
    print("%d games per cell" % games)

    # ---------------------------------------------------------------- NAP
    def nap_level(level, tier, g):
        """Mean of the six Apprentices at one Credit goal."""
        nap.CREDITS_TO_LEAVE = NAP_LEVELS[level]
        each = max(200, g // len(NAP_APPS))
        return sum(nap.run(a, "-1", each, tier=tier) for a in NAP_APPS) / len(NAP_APPS)

    grid(
        "NAP  Nobulous' Apprenticeship Program",
        "difficulty = the Credit goal; FINF held at Reduce 1",
        [(("%s (%d Credits)" % (k, NAP_LEVELS[k])) + (" *" if k == "Standard" else ""), k)
         for k in ("Easy", "Standard", "Hard", "Nobulous")],
        nap_level,
        games,
        notes=("",
               "  * Standard difficulty. Mean of the six Apprentices.",
               "  Tier I   3 of 4 Following Setbacks replace 3 base Setbacks",
               "  Tier II  4 Impostor Tasks - Mandatory, and grant no Credits",
               "  Tier III 6 Devious Opportunities replace the 6 base ones"),
    )
    nap.CREDITS_TO_LEAVE = NAP_LEVELS["Standard"]

    # ---------------------------------------------------------------- BAT
    grid(
        "BAT  Build-a-Tyrant",
        "difficulty = Specimens added / Buff HP; random Rat sides",
        [(d, d) for d in ("Easy", "Standard", "Hard", "Nobulous")],
        lambda d, t, g: bat.run(d, g, tier=t, card_effects=True, sides="random"),
        games,
        notes=("",
               "  Tier I   1 of 6 Experimental Protocols drawn at setup",
               "  Tier II  6 Unauthorized Modifications in the Upgrade deck",
               "  Tier III 6 Research Notes claimable for one-shot rewards",
               "",
               "  READ THE BAT CAVEAT at the foot of this table."),
    )

    print()
    print("  BAT - the Tyrant dice rule")
    print("  %-12s %13s %15s" % ("difficulty", "current rules", "rulebook rules"))
    for d in ("Easy", "Standard", "Hard", "Nobulous"):
        now = bat.run(d, games, tyrant_takes_rat_dice=True, card_effects=True, sides="random")
        book = bat.run(d, games, tyrant_takes_rat_dice=False, card_effects=True, sides="random")
        print("  %-12s %13s %15s" % (d, pct(now), pct(book)))
    print("  current  = the Tyrant's six dice come out of the Rats' pool")
    print("  rulebook = the Tyrant brings its own six, as rules/bat.html says")

    # ---------------------------------------------------------------- AoS
    def aos_level(level, tier, g):
        """Mean of the six Technicians at one Program-deck mix."""
        each = max(200, g // len(aos.TECHS))
        return sum(aos.run(level, each, tier=tier, tech=k)
                   for k in aos.TECHS) / len(aos.TECHS)

    grid(
        "AoS  Automaton of Shale",
        "difficulty = the Routine/Specialized/Unstable mix",
        [("%s  %d/%d/%d" % ((k,) + aos.LEVELS[k]), k) for k in aos.LEVEL_NAMES],
        aos_level,
        games,
        notes=("",
               "  Mean of the six Technicians.",
               "  Tier I   1 of 6 Nobulous Interference cards drawn at setup",
               "  Tier II  6 Corrupted Limitations in the Limitation deck",
               "  Tier III 6 Backdoor Routines, at most 2 claimed per game"),
    )

    # ---------------------------------------------------------------- NRJ
    print()
    print("=" * 66)
    print("NRJ  Imposter Scenario (the campaign finale)")
    print("=" * 66)
    print("  The tiers apply to the three games above, not to the finale, and")
    print("  the finale has no difficulty dial. Its variable is the Research")
    print("  Pool.")
    print()
    for mode in nrj.POOL_MODES:
        print("  %-14s %9s" % (mode, pct(nrj.run(mode, games))))

    # ---------------------------------------------------------------- refs
    print()
    print("=" * 66)
    print("CALIBRATION - published 20 Strong titles, community-recorded")
    print("=" * 66)
    print("  %-24s %7s %9s" % ("title", "games", "win rate"))
    for name, n, rate in COMMUNITY:
        print("  %-24s %7d %8d%%" % (name, n, rate))
    print()
    print("  Source: 20 Strong Community Game Stats, read 2026-09-20.")
    print("  A finished game in this system sits near 50%. Against that:")
    print("    AoS  below band at every mix, and furthest below at Unstable.")
    print("    NAP  near band at Easy, below it from Standard down.")
    print("    BAT  in band at Easy, below it from Standard down.")
    print("  The BAT ladder in rules/bat.html (~49/43/32/21) is this model's")
    print("  own output - the Buff HP dial was tuned against it - so agreement")
    print("  there is construction, not corroboration.")

    # ---------------------------------------------------------------- caveats
    print()
    print("=" * 66)
    print("CAVEATS")
    print("=" * 66)
    print("""
  THE BAT TIER COLUMNS RUN THE WRONG WAY. In this model the tier modules
  make BAT easier, which contradicts the design intent that Tier II is the
  pressure peak. AoS and NAP both reproduce that intent, so the fault is
  specific to the BAT model, and the reason is structural: its only real
  loss channel is Rats being knocked out, and Upgrades are armor that stops
  damage outright. Adding six Upgrade-class cards to the deck therefore
  increases the armor supply, while the modules' hostile clauses live in
  content the model omits - the Tyrant Attack deck, the frontmost-Splice
  effect, and the Protocol clauses that turn on die-borrowing between Rats.
  Both Modification sides ARE modeled (the Tyrant may tap one for +2, and
  all six printed drawbacks apply while a Rat holds one); it is not enough.
  Treat BAT's difficulty column as usable and its tier row as not.

  Per-card text is the omission that remains:
    BAT  20 Experiment effects, 16 Upgrade abilities, 7 Tyrant Attacks.
         card_effects=True covers only the frontmost Splice firing free and
         the Rats tapping an Upgrade. Hostile on net.
    NRJ  18 of the 24 Scenario effects.
  Modeled in the later passes, and no longer omissions: the six Apprentice
  abilities and the 26 Request rewards, the six Technician abilities and the
  six base Limitations, the Opportunity coupons, and both sides of the
  Unauthorized Modifications.

  Heroes move numbers a long way, and every bit of it is ability text. The
  printed statlines really are identical - Technicians 2/2/3, Apprentices
  2/2/2, both sides of each Lab Rat the same - so the spread comes entirely
  from the abilities, which are now modeled: about 14 points between the
  best and worst Technician, about 6 between Apprentices. This cross-tab
  reports their mean; the per-hero tables are in RESULTS.txt, and cards.py
  lists all twenty.

  Policy sensitivity is large. NRJ moved from 3.4% to 9.2% on how it spends
  the Research Pool, with no rules change. Prefer the shape of a column to
  the level of any single cell.
""")
    print("finished in %.1fs" % (time.time() - started))


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT)
