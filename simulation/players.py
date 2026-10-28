"""What kind of player is at the table? Five of them, across all four games.

    python players.py              # 8,000 games per cell
    python players.py 20000

Every other tool in this package runs one fixed policy. Until 2026-10-27
that policy was "take the strongest dice, throw one expected success past
the requirement" in all four games, and this file is what showed it was 6
to 34 points off its own optimum in three of them. The policies were
retuned on the strength of it, so `strategic` below is now per-game: NAP
throws one BELOW each requirement and spends weak dice first, the finale
throws two above, BAT clears a wall by 1.20x, AoS was already right.

THE PROFILES COME FROM HOW PEOPLE ACTUALLY PLAY, described by Jon, who has
played these games. An earlier version of this file guessed, and guessed
backwards - it had the novice hoarding strong dice and the aggressive
player gambling. Both are wrong, and the corrected definitions are:

  strategic    as many dice as the Target needs and no more, with a sense
               of the odds. The strongest player, and the one the models
               now run; what Jon calls the aggressive player
  cautious     out to win every STR phase outright, so commits heavily at
               each one and runs out of dice. Never declines an attempt
  novice       leads with their best dice, and their commitment wobbles a
               point either side of right while they work out a strategy
  haphazard    empties the pool into one roll, then has to starve the next
               few until REC bails them out. Games go off the rails fast
  pre-retune   the single uniform policy every model ran before the retune,
               kept as a row so the retune stays measurable here

The dice columns are the point of the table as much as the win rates: Jon's
cautious player "runs out of dice", which is a claim about the pool and not
about winning, so the pool is measured with the same instrument
dicetension.py uses on the shipping policy.

WHAT THIS STILL CANNOT MODEL: misreading a card, forgetting a trigger, or a
novice sensibly picking Easy. AoS also has the least room of the three by
construction - Target + 1 is a RULES cap, so an AoS player can fill less
but never more, and three of these profiles leave its column untouched.
"""
import sys
import time

import aos
import bat
import dicetension
import nap
import nrj
import table

GAMES = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
LEVELS = ("Standard", "Nobulous")


# ---------------------------------------------------------------- margins
def wobble(lo, hi):
    """A commitment that is nearly right and never settles."""
    def margin(game):
        return game.rng.randint(lo, hi)
    return margin


def dump_then_starve(full, flush, empty):
    """Everything into this roll; nothing into the next few.

    `full` is the pool size at which the player dumps. Once the pool is
    below it they have nothing left to throw and under-commit until REC
    refills them, which is the swing Jon describes.
    """
    def margin(game):
        return flush if len(game.available) >= full else empty
    return margin


def bat_dump_then_starve(game):
    """The same swing against a Splice, where the margin is a multiplier."""
    return 2.0 if len(game.shared_pool()) >= 5 else 0.8


PROFILES = [
    # The retuned optimum. Jon's "aggressive": exactly what is needed.
    ("strategic", {}),

    ("cautious", {
        # Win this phase, whatever it costs the next one.
        "nap": {"COMMIT_MARGIN": 3, "DICE_ORDER": "strongest"},
        "nrj": {"COMMIT_MARGIN": 5, "DICE_ORDER": "strongest",
                "COMMIT_HOPELESS": True},
        "bat": {"THRESHOLD_MARGIN": 1.6},
        # No AoS entry: the Target + 1 cap means there is no heavier commit
        # available, which is its own finding about that game.
    }),

    ("novice", {
        # Leads with the best dice - which is right in BAT and AoS and
        # wrong in NAP - and cannot yet judge how much is enough.
        "nap": {"COMMIT_MARGIN": wobble(-1, 1), "DICE_ORDER": "strongest"},
        "nrj": {"COMMIT_MARGIN": wobble(1, 3), "DICE_ORDER": "strongest"},
        "bat": {"THRESHOLD_MARGIN": wobble(1, 1)},     # 1.0: no spread left
        "aos": {"FILL_MARGIN": wobble(-1, 0)},
    }),

    ("haphazard", {
        "nap": {"COMMIT_MARGIN": dump_then_starve(6, 4, -2),
                "DICE_ORDER": "strongest"},
        "nrj": {"COMMIT_MARGIN": dump_then_starve(8, 6, -1),
                "DICE_ORDER": "strongest"},
        "bat": {"THRESHOLD_MARGIN": bat_dump_then_starve},
        "aos": {"FILL_MARGIN": dump_then_starve(9, 0, -2)},
    }),

    ("pre-retune", {
        "nap": {"COMMIT_MARGIN": 1, "DICE_ORDER": "strongest"},
        "nrj": {"COMMIT_MARGIN": 0, "DICE_ORDER": "strongest"},
        "bat": {"THRESHOLD_MARGIN": 1.15},
    }),
]

MODULES = {"nap": nap, "aos": aos, "bat": bat, "nrj": nrj}


def apply(profile):
    """Set a profile and return what it replaced, for restoring."""
    saved = {}
    for key, mod in MODULES.items():
        for attr, value in profile.get(key, {}).items():
            saved[(key, attr)] = getattr(mod, attr)
            setattr(mod, attr, value)
    return saved


def restore(saved):
    for (key, attr), value in saved.items():
        setattr(MODULES[key], attr, value)


def measure(profile, games):
    """Win rates, then what the dice pool looked like getting them."""
    saved = apply(profile)
    run = dict(card_effects=True, sides="random", tier="none")
    run.update(profile.get("bat_run", {}))
    try:
        row = []
        for level in LEVELS:
            nap.CREDITS_TO_LEAVE, nap.SETBACKS_IN_DECK = table.NAP_LEVELS[level]
            each = max(200, games // len(table.NAP_APPS))
            row.append(sum(nap.run(a, "-1", each) for a in table.NAP_APPS)
                       / len(table.NAP_APPS))
            row.append(bat.run(level, games, **run))
            per = max(200, games // len(aos.TECHS))
            row.append(sum(aos.run(level, per, tier="none", tech=k)
                           for k in aos.TECHS) / len(aos.TECHS))
        row.append(nrj.run("standalone", games))
        nap.CREDITS_TO_LEAVE, nap.SETBACKS_IN_DECK = table.NAP_LEVELS["Standard"]
        tension = dicetension.sample(dicetension.nap_game, max(400, games // 10))
        return row, tension
    finally:
        nap.CREDITS_TO_LEAVE, nap.SETBACKS_IN_DECK = table.NAP_LEVELS["Standard"]
        restore(saved)


def main(games=GAMES):
    started = time.time()
    print()
    print("THE PLAYER AT THE TABLE - %d games per cell" % games)
    print("=" * 74)
    print("%-12s %21s   %21s   %7s" % ("", "- - Standard - -",
                                       "- - Nobulous - -", "finale"))
    print("%-12s %6s %6s %6s   %6s %6s %6s   %7s"
          % ("profile", "NAP", "BAT", "AoS", "NAP", "BAT", "AoS", "NRJ"))
    print("-" * 74)
    rows, pools = {}, {}
    for name, profile in PROFILES:
        row, tension = measure(profile, games)
        rows[name], pools[name] = row, tension
        print("%-12s %5.1f%% %5.1f%% %5.1f%%   %5.1f%% %5.1f%% %5.1f%%   %6.1f%%"
              % ((name,) + tuple(100 * v for v in row)))
        sys.stdout.flush()

    base = rows["strategic"]
    print()
    print("  Against the strategic player, in points of win rate:")
    print("-" * 74)
    for name, _ in PROFILES[1:]:
        print("%-12s %+5.1f  %+5.1f  %+5.1f   %+5.1f  %+5.1f  %+5.1f   %+6.1f"
              % ((name,) + tuple(100 * (a - b)
                                 for a, b in zip(rows[name], base))))

    print()
    print("  DO THEY RUN OUT OF DICE? NAP's pool at every commit decision,")
    print("  measured the way dicetension.py measures the shipping policy.")
    print("-" * 74)
    print("  %-12s %8s %8s %8s  | %8s %8s" % ("profile", "mean", "<=2",
                                              "empty", "trough", "dry"))
    for name, _ in PROFILES:
        t = pools[name]
        if t:
            print("  %-12s %8.1f %7.0f%% %7.1f%%  | %8.1f %7.1f%%"
                  % (name, t["mean"], t["low"], t["starved"], t["trough"],
                     t["dry"]))

    print()
    cols = list(zip(*rows.values()))
    labels = ["NAP Std", "BAT Std", "AoS Std", "NAP Nob", "BAT Nob",
              "AoS Nob", "NRJ"]
    print("  How much the player matters, best profile to worst:")
    for label, col in zip(labels, cols):
        print("    %-10s %4.1f points" % (label, 100 * (max(col) - min(col))))
    print()
    print("  finished in %.0fs" % (time.time() - started))


if __name__ == "__main__":
    main()
