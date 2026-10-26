"""Canonical rosters for the axes a balance table is asked to cross.

Everything here is transcribed from the authoritative sources - the RATS,
APPS and TECHS tables in generator/build_*.py and the tier tables in
rules/nrj.html - so the table names real cards rather than invented ones.

THE CENTRAL FACT ABOUT THE HERO AXIS
------------------------------------
Every game's hero cards share one statline and differ only in ability text.
The rulebooks say so in as many words:

  AoS  "Choose a Technician. All six begin at 2 HP / 2 STR / 3 REC and
        differ only in ability."                        (rules/aos.html:34)
  NAP  "Choose an Apprentice. All six begin at 2 HP / 2 STR / 2 REC; they
        differ only in abilities."                      (rules/nap.html:33)
  BAT  Each Rat's two sides print the same HP/STR/REC; only the named
        ability changes.                    (generator/build_bat.py RATS)

Ability text is precisely the category these models do not implement, so the
hero axis carries no signal here and the table says so per cell instead of
reprinting one number under six headings. Same for the NRJ tiers below: all
twelve modules are card effects.
"""

# ---------------------------------------------------------------------------
# BAT - 4 double-sided Lab Rat cards. Statline is per Rat, not per side.
# (name, side, HP, STR, REC, ability name)
# ---------------------------------------------------------------------------
RAT_SIDES = [
    ("Rummage", "A", 1, 2, 2, "Careful Borrower"),
    ("Rummage", "B", 1, 2, 2, "Tool Keeper"),
    ("Fidget",  "A", 1, 2, 2, "Jury-Rig"),
    ("Fidget",  "B", 1, 2, 2, "Fine Tuning"),
    ("Whiz",    "A", 2, 2, 1, "Self-Sufficient"),
    ("Whiz",    "B", 2, 2, 1, "Prepared"),
    ("Mottle",  "A", 2, 2, 1, "Experimental Subject"),
    ("Mottle",  "B", 2, 2, 1, "Specimen Adaptation"),
]

# All four Rats are always in play; the choice is one side each, so the hero
# axis for BAT is 2^4 = 16 team configurations, not a pick of one card.
RAT_TEAM_CONFIGS = 16

# ---------------------------------------------------------------------------
# NAP - 6 Apprentices, all 2/2/2.
# ---------------------------------------------------------------------------
APPRENTICES = ["Prodigy", "Slacker", "Technician",
               "Savant", "Opportunist", "Lab Rat"]

# ---------------------------------------------------------------------------
# AoS - 6 Experimental Technicians, all 2/2/3.
# ---------------------------------------------------------------------------
TECHNICIANS = ["Architect", "Debugger", "Optimizer",
               "Engineer", "Operator", "Compiler"]

# ---------------------------------------------------------------------------
# NRJ overlay modules. "The tiers are not difficulty levels" (rules/nrj.html).
# Each tier includes the ones before it. 6 cards per entry.
# ---------------------------------------------------------------------------
TIERS = ["none", "I", "II", "III"]

TIER_CONTENT = {
    "BAT": {
        "I":   "1 of 6 Experimental Protocols drawn at setup",
        "II":  "6 Unauthorized Modifications shuffled into the Upgrade deck",
        "III": "6 Research Notes claimable for one-shot rewards",
    },
    "NAP": {
        "I":   "3 of 4 Following Setbacks replace 3 base Setbacks",
        "II":  "4 Impostor Tasks - Mandatory, grant no Credits",
        "III": "6 Devious Opportunities replace the 6 Opportunities",
    },
    "AoS": {
        "I":   "1 of 6 Nobulous Interference cards drawn at setup",
        "II":  "6 Corrupted Limitations shuffled into the Limitation deck",
        "III": "6 Backdoor Routines, at most 2 claimable per game",
    },
}

# Tier II is called out in the rules as "the pressure peak"; tier III hands
# the player tools back. So the tier axis is not monotonic in difficulty.
#
# All twelve modules ARE implemented as of 2026-09-20 - see the tier blocks in
# bat.py, nap.py and aos.py. AoS and NAP reproduce the documented shape (Tier
# II is the trough, Tier III recovers some ground). BAT does not, for reasons
# recorded in the CAVEATS block that table.py prints.
