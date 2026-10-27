"""Tune the six Experimental Protocols so they all push the same way.

    python protocols.py            # 4000 games per cell

Tier I is a difficulty tier, and its six cards used to disagree violently:
forcing each in turn, three made BAT HARDER and three made it EASIER,
spanning 29 points from Shared Equipment Budget at -18.8 to Questionable
Methodology at +10.7, so Tier I measured about -1 because that cancelled
out. They were retuned and now all push the same way.

The target band is roughly -3 to -6 against no-NRJ, which is where NAP's
Tier I sits (-3.1). Each card is swept over the one knob that is expressible
as a change to its printed text.

As shipped, forced one at a time against a 46.8% baseline (2026-10-27):
Cross-Contamination -7.3, Shared Equipment -7.2, Questionable Procurement
-4.8, Independent Funding -4.4, Questionable Methodology -2.8, Accelerated
Trials -0.8. Five sit in or near the band; Accelerated Trials gates on
printed Target 5+, which fell from 18 of the 20 Experiments to 5 when the
model stopped adding +1 to the printed numbers, and it has not been retuned
since. That is a design question, not a dial to turn quietly.
"""
import sys

import bat

GAMES = 4000
BAND = (-6.5, -2.5)


def win(protocol, games=GAMES, **knobs):
    saved = {k: getattr(bat, k) for k in knobs}
    bat.FORCE_PROTOCOL = protocol
    for k, v in knobs.items():
        setattr(bat, k, v)
    try:
        return 100 * bat.run("Standard", games, card_effects=True,
                             sides="random", tier="I")
    finally:
        bat.FORCE_PROTOCOL = None
        for k, v in saved.items():
            setattr(bat, k, v)


def sweep(label, protocol, knob, values, base, games=GAMES):
    print("  %s" % label)
    for v in values:
        w = win(protocol, games, **{knob: v})
        d = w - base
        mark = "  <-- in band" if BAND[0] <= d <= BAND[1] else ""
        print("    %-26s %6.1f%%  (%+.1f)%s"
              % ("%s = %s" % (knob, v), w, d, mark), flush=True)


def main(games=GAMES):
    base = 100 * bat.run("Standard", games, card_effects=True, sides="random")
    print("Standard, no NRJ: %.1f%%.  Target band %+.1f to %+.1f."
          % (base, BAND[0], BAND[1]))
    print()

    sweep("Accelerated Trials", "accelerated_trials",
          "ACCEL_FLOOR", [4, 5, 6], base, games)
    sweep("Questionable Methodology", "questionable_methodology",
          "METHODOLOGY_DELTA", [-1, 0, 1], base, games)
    sweep("Cross-Contamination", "cross_contamination",
          "CROSS_SPLICE_N", [1, 2, 3], base, games)
    sweep("Shared Equipment Budget", "shared_equipment",
          "SHARED_EQUIP_DICE", [2, 1], base, games)
    sweep("Independent Funding", "independent_funding",
          "INDEP_ON_WIN", [True, False], base, games)
    sweep("Questionable Procurement", "questionable_procurement",
          "TIER2_EXTRA_SPECIMEN", [0], base, games)


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else GAMES)
