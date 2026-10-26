"""Full sweep: every game, every difficulty, every hero, every NRJ tier."""
import sys
import nap
import bat
import aos

GAMES = 4000
TIERS = ["none", "I", "II", "III"]
APPS = ["Prodigy", "Slacker", "Technician", "Savant", "Opportunist", "Lab Rat"]
NAP_LEVELS = [("Easy", 5), ("Standard", 6), ("Hard", 7), ("Nobulous", 8)]


def pct(x):
    return "%5.1f%%" % (100 * x)


def header(title, cols):
    print()
    print(title)
    print("%-22s" % "" + "".join("%9s" % c for c in cols))


def nap_sweep():
    for level, credits in NAP_LEVELS:
        nap.CREDITS_TO_LEAVE = credits
        header("NAP - %s (%d Credits), FINF Reduce 1" % (level, credits), TIERS)
        for app in APPS:
            row = [nap.run(app, "-1", GAMES, tier=t) for t in TIERS]
            print("%-22s" % app + "".join("%9s" % pct(v) for v in row))
        sys.stdout.flush()


def bat_sweep():
    levels = list(bat.DIFFICULTY.keys())
    # Each Rat is double-sided, so a representative game randomises the four
    # side choices rather than running all fronts.
    header("BAT - win rate by difficulty, random Rat sides", TIERS)
    for level in levels:
        row = [bat.run(level, GAMES, tier=t, card_effects=True, sides="random")
               for t in TIERS]
        print("%-22s" % level + "".join("%9s" % pct(v) for v in row))
    header("BAT - Standard, each Rat side alone against no ability", TIERS)
    for i in range(4):
        for sd in (0, 1):
            cfg = [2, 2, 2, 2]
            cfg[i] = sd
            row = [bat.run("Standard", GAMES, tier=t, card_effects=True, sides=cfg)
                   for t in TIERS]
            print("%-22s" % bat.RAT_SIDES[i][sd] + "".join("%9s" % pct(v) for v in row))
    sys.stdout.flush()


def aos_sweep():
    # Every game is played by a Technician, so average over the six the way
    # the NAP table averages over its Apprentices.
    header("AoS - win rate by difficulty, mean of the six Technicians", TIERS)
    each = max(400, GAMES // len(aos.TECHS))
    for level in aos.LEVEL_NAMES:
        row = [sum(aos.run(level, each, tier=t, tech=k) for k in aos.TECHS) / len(aos.TECHS)
               for t in TIERS]
        label = "%s  %d/%d/%d" % ((level,) + aos.LEVELS[level])
        print("%-22s" % label + "".join("%9s" % pct(v) for v in row))
    header("AoS - Standard, by Technician", TIERS)
    for k in aos.TECHS:
        row = [aos.run("Standard", each, tier=t, tech=k) for t in TIERS]
        print("%-22s" % k + "".join("%9s" % pct(v) for v in row))
    sys.stdout.flush()


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    if which in ("all", "nap"):
        nap_sweep()
    if which in ("all", "bat"):
        bat_sweep()
    if which in ("all", "aos"):
        aos_sweep()
