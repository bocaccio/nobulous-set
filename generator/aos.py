"""Canonical Automaton of Shale card data, including all flavor text."""

ROUTINE = [
    ("Maintain Balance", [2, 3, 2], 0, "hp1"),
    ("Lift a Heavy Object", [3, 2, 2], 1, "rec3"),
    ("Climb an Incline", [2, 2, 3], 0, "rec_up_remove"),
    ("Move at Speed", [2, 3, 2], 1, "unheat"),
    ("Navigate a Passage", [3, 2, 2], 2, "str_up_remove"),
    ("Cross Uneven Ground", [2, 2, 2, 2], 1, "opt_placeholder"),
    ("Manipulate an Object", [2, 3, 2], 2, "rec3"),
    ("Detect an Obstacle", [2, 2, 2, 3], 2, "unheat"),
]

SPECIALIZED = [
    ("Traverse Difficult Terrain", [3, 2, 3], 1, "hp1"),
    ("Move Without Detection", [2, 3, 2, 2], 0, "str_up_remove"),
    ("Track a Moving Subject", [3, 3, 2], 1, "rec3"),
    ("Climb a Vertical Surface", [2, 3, 2, 3], 3, "rec_up_remove"),
    ("Clear an Obstacle", [3, 2, 3], 0, "unheat"),
    ("Operate in Low Light", [3, 2, 3, 2], 2, "opt_placeholder"),
    ("Maintain a Pursuit", [2, 3, 3, 2], 1, "rec3"),
    ("Carry a Moving Load", [3, 2, 2, 3], 2, "unheat"),
]

UNSTABLE = [
    ("Navigate Without Guidance", [3, 2, 3, 2], 0, "hp1"),
    ("Evade Observation", [2, 3, 2, 3], 3, "rec_up_remove"),
    ("Overcome a Barrier", [3, 2, 3, 2], 2, "unheat"),
    ("Intercept a Moving Subject", [2, 3, 3, 2], 1, "str_up_remove"),
    ("Maintain Control of a Load", [3, 2, 2, 3], 0, "rec3"),
    ("Adapt to Changing Terrain", [2, 3, 2, 3], 3, "opt_placeholder"),
    ("Execute a Complex Route", [3, 3, 2, 3], 1, "rec3"),
    ("Operate Autonomously", [3, 2, 3, 2], 1, "unheat"),
]

ADVANCED = [
    ("Rapid Approach", [2, 3, 3, 3, 2], 2),
    ("Unobserved Entry", [3, 3, 3, 3], 1),
    ("Subject Acquisition", [2, 3, 3, 3, 3], 3),
    ("Difficult Extraction", [3, 3, 3, 2], 0),
    ("Autonomous Infiltration", [3, 2, 3, 2, 3], 2),
    ("Controlled Restraint", [3, 3, 3, 3], 2),
    ("Adaptive Pursuit", [2, 3, 3, 3, 2], 1),
    ("Council Extraction Protocol", [3, 3, 3, 3, 3], 1),
]

REQ_MAP = {
    "Maintain Balance": ["G", None, None],
    "Lift a Heavy Object": ["P", None, None],
    "Climb an Incline": [None, None, "Y"],
    "Move at Speed": [None, "B", None],
    "Navigate a Passage": ["G", None, None],
    "Cross Uneven Ground": [None, None, "P", None],
    "Manipulate an Object": ["Y", None, None],
    "Detect an Obstacle": [None, None, "B", None],
    "Traverse Difficult Terrain": ["P", None, "Y"],
    "Move Without Detection": ["G", None, "B", None],
    "Track a Moving Subject": [None, "Y", "P"],
    "Climb a Vertical Surface": ["B", None, None, "G"],
    "Clear an Obstacle": ["P", "Y", None],
    "Operate in Low Light": [None, "G", None, "B"],
    "Maintain a Pursuit": ["Y", None, "P", None],
    "Carry a Moving Load": ["Y", "P", "B", "G"],
    "Navigate Without Guidance": ["P", None, None, None],
    "Evade Observation": [None, None, "Y", None],
    "Overcome a Barrier": [None, "B", None, None],
    "Intercept a Moving Subject": [None, None, "G", None],
    "Maintain Control of a Load": ["Y", None, None, None],
    "Adapt to Changing Terrain": [None, None, None, "P"],
    "Execute a Complex Route": [None, "G", None, None],
    "Operate Autonomously": [None, None, "B", None],
    "Rapid Approach": ["P", None, "G", "Y", None],
    "Unobserved Entry": ["Y", "G", None, "B"],
    "Subject Acquisition": ["Y", None, None, "P", None],
    "Difficult Extraction": [None, "B", None, "G"],
    "Autonomous Infiltration": ["G", None, None, "Y", None],
    "Controlled Restraint": [None, "P", None, "B"],
    "Adaptive Pursuit": ["B", None, None, "G", None],
    "Council Extraction Protocol": ["Y", None, "P", None, None],
}

# THE EIGHT ADVANCED PROGRAMS LEFT THIS TABLE on 2026-11-24 with the deck
# itself. Six of those cards no longer exist; the two names that survive as
# Assembly backs - Rapid Approach and Unobserved Entry - carry their flavour
# in ASSEMBLY_FLAVOR, beside the recipe side's. check_app_sync.py holds every
# line here against the lab's copy, and a dead entry here is a line the lab
# has nowhere to match.
FLAVOR = {
    "Maintain Balance": ("The shale frame holds steady while Nobulous adds one unnecessary clipboard.", "The frame still balances, provided nobody breathes near it."),
    "Lift a Heavy Object": ("The test mass rises smoothly, with Nobulous still standing on it.", "The test mass rises. The floor follows."),
    "Climb an Incline": ("It reaches the top. Nobulous raises the ramp.", "Each step lands harder than the last; the ramp files a complaint."),
    "Move at Speed": ("The timing gates agree: it is fast, controlled, and technically indoors.", "It clears the final gate before the first one stops shaking."),
    "Navigate a Passage": ("No contact with either wall. The plasterers are sent home.", "The corridor is now wider, though not by design."),
    "Cross Uneven Ground": ("The chassis crosses the rubble without spilling Nobulous's tea.", "The joints correct so violently that the ground becomes the stable part."),
    "Manipulate an Object": ("Stone fingers adjust a screw the apprentices have been rounding off all morning.", "The instrument turns three notches and ceases to be calibrated."),
    "Detect an Obstacle": ("It stops for the glass wall, to the disappointment of the spectators.", "It detects each obstruction immediately after impact."),
    "Traverse Difficult Terrain": ("Nobulous follows in its footsteps until the gaps become inconvenient.", "It reads the terrain correctly, then challenges every conclusion."),
    "Move Without Detection": ("Noise dampers reduce a stone machine to a passing draft.", "The dampers hold; the footprints still resemble impact craters."),
    "Track a Moving Subject": ("The assistant ducks behind a screen. The head keeps turning.", "The lock tightens until every movement looks like an escape attempt."),
    "Climb a Vertical Surface": ("A bell rings at the ceiling. Now for the descent.", "The anchors bite deeper; sections of wall begin climbing too."),
    "Clear an Obstacle": ("The apprentice is allowed to put the ladder away.", "It clears the barrier. The barrier does not clear it."),
    "Operate in Low Light": ("It finds the switch without needing the light.", "The map is perfect; the glowing heat signature is less subtle."),
    "Maintain a Pursuit": ("The subject slows to a walk. So does the automaton, with considerably less wheezing.", "Pursuit logic discards 'too quickly' as an unnecessary constraint."),
    "Carry a Moving Load": ("The crate objects throughout the journey but arrives upright.", "The load remains secure while everything beneath it shifts."),
    "Navigate Without Guidance": ("It takes the short route that Nobulous insists he was about to suggest.", "It builds several routes and attempts all of them at once."),
    "Evade Observation": ("Timing and cover reduce a stone chassis to a rumor.", "It avoids every observer except the ones staring at the new hole."),
    "Overcome a Barrier": ("The door opens. Nobulous checks that it can still close.", "It applies exactly enough force to redefine the obstruction."),
    "Intercept a Moving Subject": ("It waits at the corner while the assistant discovers how predictable he is.", "Prediction becomes certainty; the path has no remaining alternatives."),
    "Maintain Control of a Load": ("The crate stays level through every lunge from inside.", "Corrections accelerate until the cargo is the calmest thing in motion."),
    "Adapt to Changing Terrain": ("The gait rewrites itself as the ground changes.", "The gait keeps rewriting after the ground stops."),
    "Execute a Complex Route": ("It takes a turn missing from the diagram. Nobulous pencils it in.", "The sequence remains flawless; the surrounding architecture does not."),
    "Operate Autonomously": ("Nobulous leaves it to work and returns to find his instructions followed exactly.", "It completes a different objective with alarming confidence."),
}

LIMITATIONS = [
    ("Yellow Shortage", "Withhold 2 Yellow dice.", "The precision components are on another bench. Nobulous has misplaced the bench."),
    ("Green Shortage", "Withhold 2 Green dice.", "Mobility actuators have been reassigned to a 'more urgent' prototype."),
    ("Blue Shortage", "Withhold 2 Blue dice.", "Sensor stock is low; confidence remains inexplicably high."),
    ("Purple Shortage", "Withhold 2 Purple dice.", "Load-bearing modules are delayed. The load is not."),
    ("Diversity Protocol", "Withhold 2 dice of different non-Red colors.", "Nobulous removes two components to demonstrate how little you needed them."),
    ("Red Quarantine", "Withhold the Red die.", "The emergency die is perfectly safe inside the locked cabinet."),
]


# ---------------------------------------------------------------------------
# Assembly cards (2026-11-24), which REPLACE the eight standalone Advanced
# Programs. One card, two faces, and the faces are not the same card's two
# moods the way a Program's Stable/Overheated faces are:
#
#   FRONT  the recipe you build during the game - BUILD slots, every slot
#          including repeats, each filled by one cleanly-run Program that
#          counts as ONE of its printed required colours.
#   BACK   the Advanced Program that Assembly becomes in the finale, as
#          (colour, Target) elements.
#
# THE FRONT'S "ADVANCED COLORS" LINE IS DERIVED, NOT STORED - advanced_colors()
# below reads it off the back. It is there to tell a player which colours the
# finale will ask of this Assembly while concealing how many elements it has
# and what the Targets are, so a stored copy could only ever drift out of
# agreement with the thing it describes. Four of the nine print a front recipe
# in different colours from their own back (Balance Gyro, Sensor Array,
# Traction Module, Covert Sensor Array); that is the concealment working, not
# a transcription error, and it is why nothing may derive one from the other.
#
# Keyed by the ASSEMBLY name, never by the Advanced Program name: "Carry a
# Moving Load" is also a Specialized Program, and REQ_MAP and FLAVOR are
# name-keyed dicts that would silently overwrite each other. See
# check_app_sync.py, which asserts the two stay distinct cards.
ASSEMBLIES = [
    ("Drive Train",     ["P", "Y"],      "Rapid Approach",         [("P", 3), ("Y", 3)]),
    ("Control Array",   ["B", "G"],      "Correct a Heading",      [("B", 2), ("G", 4)]),
    ("Balance Gyro",    ["P", "G"],      "Recover from a Stumble", [("B", 3), ("Y", 3)]),
    ("Sensor Array",    ["B", "Y"],      "Unobserved Entry",       [("P", 4), ("G", 2)]),
    ("Load Frame",      ["P", "P", "Y"], "Carry a Moving Load",    [("P", 3), ("P", 2), ("Y", 3)]),
    ("Power Regulator", ["B", "B", "G"], "Sustain Peak Output",     [("B", 3), ("B", 2), ("G", 2)]),
    ("Articulated Arm", ["P", "G", "G"], "Place a Fragile Load",   [("P", 2), ("G", 3), ("G", 2)]),
    ("Traction Module", ["B", "Y", "Y"], "Cross Broken Ground",    [("P", 3), ("B", 3)]),
]

# The ninth Assembly, printed in the NRJ supplement and offered only in a
# Tier III setup, where it replaces the standard Sensor Array. Same Build
# recipe as the card it displaces, so Tier III's build problem is the base
# game's; only the finale stage it becomes differs.
COVERT = ("Covert Sensor Array", ["B", "Y"], "Erase the Audit Trail",
          [("P", 2), ("G", 3), ("G", 2)])

ALL_ASSEMBLIES = ASSEMBLIES + [COVERT]

COLOR_NAME = {"P": "Purple", "B": "Blue", "G": "Green", "Y": "Yellow"}


def advanced_colors(elements):
    """The front's Advanced colors line: each colour of the back once, in
    order of first appearance. Count and Targets stay concealed."""
    out = []
    for c, _ in elements:
        if c not in out:
            out.append(c)
    return out


ASSEMBLY_FLAVOR = {
    # (front - the parts on the bench, back - the Program it can now run)
    "Drive Train": ("Two housings, a shaft, and a note reading &lsquo;DO NOT OVER-TIGHTEN&rsquo; in Nobulous&rsquo; hand.",
                    "It reaches the target before the warning can become an alarm."),
    "Control Array": ("A lattice of linkages that answers the wrong lever twice before settling.",
                      "The heading corrects itself so smoothly that nobody admits it was wrong."),
    "Balance Gyro": ("It spins up quietly and stays level while the bench does not.",
                     "The stumble is absorbed on the second step. The first step is still under review."),
    "Sensor Array": ("Lenses, whiskers and one component Nobulous insists is a sensor.",
                     "Locks open, cameras loop, and the corridor never learns it was occupied."),
    "Load Frame": ("Ribs and crossmembers, rated for a mass Nobulous has not disclosed.",
                   "The crate arrives upright, having objected throughout."),
    "Power Regulator": ("A governor, two reservoirs, and a gauge that only reads &lsquo;ADEQUATE&rsquo;.",
                        "Output holds flat for the full duration, which surprises the gauge."),
    "Articulated Arm": ("Three joints, each tested by Nobulous handing it something fragile.",
                        "It sets the vessel down without a sound and waits to be told it may let go."),
    "Traction Module": ("Treads, grousers, and a spare set because the first set is &lsquo;learning&rsquo;.",
                        "The broken ground is crossed. Some of it is carried along."),
    "Covert Sensor Array": ("The same array, with the indicator lamps quietly omitted.",
                            "The ledger agrees with itself again. It never agreed with anything else."),
}
