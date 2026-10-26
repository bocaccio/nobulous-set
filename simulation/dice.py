"""The 20 Strong dice, shared by all four games.

Every die is a d6. Face values: Crit = 2 successes, Hit = 1, blank = 0.
Distributions are lifted verbatim from the playtest engines, which are the
canonical implementation (playtest/dist/bat.js and app.js agree exactly).
"""
import random

# color -> the six faces, as success values
FACES = {
    "purple": [1, 1, 1, 1, 2, 0],
    "blue":   [1, 1, 1, 2, 0, 0],
    "green":  [1, 1, 2, 0, 0, 0],
    "yellow": [1, 2, 0, 0, 0, 0],
    "red":    [1, 1, 1, 1, 1, 2],
}

COLORS = ["purple", "blue", "green", "yellow"]

# expected successes per die, handy for allocation policies
EV = {c: sum(f) / 6.0 for c, f in FACES.items()}

# Expected successes when a miss may be rerolled once - what STR 2 buys.
# A die contributes its own EV plus, with probability P(miss), another EV.
EV_REROLL = {c: EV[c] * (1 + FACES[c].count(0) / 6.0) for c in FACES}


def roll(color, rng):
    return FACES[color][rng.randrange(6)]


def roll_many(colors, rng):
    return [roll(c, rng) for c in colors]


def best_first(colors):
    """Strongest dice first - the ordering every policy here uses."""
    return sorted(colors, key=lambda c: -EV[c])
