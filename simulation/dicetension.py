"""Is running out of dice actually the pressure, in each game?

    python dicetension.py            # 3000 games per cell

20 Strong's core tension is resource management: "am I going to run out of
dice?" BAT's old Tyrant battle failed this - the correct play was to commit
only what recovery returned, so the pool was a per-round income and the
fight ended with 7.1 of about 10 dice unspent. This asks the same question
of NAP and AoS, which were never checked.

Three numbers, measured the same way in each game:

  starved    share of decision points where NO die was available. The
             sharpest form of the question: how often does the game stop
             you because the pool is empty?
  low        share of decision points with 2 or fewer available. Scarcity
             that is felt without being absolute.
  mean       average dice available at a decision point.

A game with real dice tension should show `low` high and `starved`
non-zero. A game where the pool is income rather than budget shows both
near zero and a comfortable mean.
"""
import random
import statistics
import sys

import aos
import bat
import nap


def sample(fn, games, seed0=0):
    """Run `games` games, collecting the available-dice count each time the
    game is about to spend dice.

    The mean hides the trough, so the per-game MINIMUM is collected too:
    that is the moment a player would actually feel the pool running out.
    """
    counts, troughs = [], []
    for i in range(games):
        mine = []
        fn(random.Random(seed0 + i), mine)
        if mine:
            counts.extend(mine)
            troughs.append(min(mine))
    if not counts:
        return None
    return dict(
        n=len(counts),
        mean=statistics.mean(counts),
        starved=100.0 * sum(1 for c in counts if c == 0) / len(counts),
        low=100.0 * sum(1 for c in counts if c <= 2) / len(counts),
        trough=statistics.mean(troughs),
        tight=100.0 * sum(1 for t in troughs if t <= 2) / len(troughs),
        dry=100.0 * sum(1 for t in troughs if t == 0) / len(troughs),
    )


# ---- NAP ----------------------------------------------------------------
def nap_game(rng, counts):
    g = nap.Game("Prodigy", "-1", rng)
    real = g.work

    def hooked():
        counts.append(len(g.available))
        return real()
    g.work = hooked
    g.play()


# ---- AoS ----------------------------------------------------------------
def aos_game(rng, counts):
    # `deck` names a whole deck; a difficulty level goes in as a composition.
    g = aos.Game("Specialized", rng, composition=aos.LEVELS["Standard"])
    # allocate() is where dice are actually chosen; run_program runs before
    # any are spent, so sampling there just reports a full pool.
    real = g.allocate

    def hooked(*a, **k):
        counts.append(len(g.available))
        return real(*a, **k)
    g.allocate = hooked
    g.play()


# ---- BAT, for the comparison the other two are being judged against ------
def bat_game_factory(proto):
    def bat_game(rng, counts):
        g = bat.Game("Standard", rng, card_effects=True, sides="random")
        real = g.battle_round

        def hooked():
            counts.append(len(g.shared_pool()))
            return real()
        g.battle_round = hooked
        g.play()
    return bat_game


def main(games=3000):
    print("Dice available at the moment the game asks you to spend, %d games."
          % games)
    print()
    print("per decision point            |  worst point in a game")
    print("%-26s %7s %7s %8s  | %8s %8s %7s"
          % ("", "mean", "<=2", "empty", "trough", "<=2", "empty"))
    for label, fn in (("NAP  (Standard, Reduce 1)", nap_game),
                      ("AoS  (Standard)", aos_game),
                      ("BAT battle (shipping)", bat_game_factory(False))):
        r = sample(fn, games)
        if r:
            print("%-26s %7.1f %6.0f%% %7.1f%%  | %8.1f %7.0f%% %6.1f%%"
                  % (label, r["mean"], r["low"], r["starved"],
                     r["trough"], r["tight"], r["dry"]))


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 3000)
