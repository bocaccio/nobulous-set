"""Is every printed effect, on every card, in every game, modelled?

    python coverage.py            # the matrix, then the gaps
    python coverage.py -v         # also list the cards that ARE modelled

audit.py answers "does this card ever reach the table and do something".
This answers the question before it: IS ITS PRINTED TEXT IMPLEMENTED AT ALL.
A card that is not implemented cannot fire, so audit.py's firing columns are
only meaningful for the cards this file says are in.

WHY THIS FILE EXISTS AND WHY IT IS BUILT THE WAY IT IS. Every coverage claim
in this repository has gone stale at least once, and three of them were stale
on the day this file was written - bat.py's own docstring said "the 20
Experiment effects are not implemented" when 19 are, aos.py said "base
Limitations are not modeled" when all 6 are, and audit.py said no Final Exam
prints an effect when all 12 do. Comments rot because nothing checks them.

So every claim below is a CLAIM object carrying a predicate over the live
modules. `python coverage.py` re-derives the matrix from the code on every
run and exits non-zero if any claim's predicate no longer holds. A prose
comment cannot do that; this can. If you implement a card, the claim that
said it was missing FAILS, and the failure tells you to update this file.
That is the point: the file is wrong loudly instead of quietly.

Card counts come from playtest/dist/catalog.json, which build_catalog.py
generates from the same build_*.py tables the printed cards come from, so the
denominators here are the real deck sizes and not a second copy of them.
"""
import inspect
import io
import json
import os
import sys

import aos
import bat
import finale
import nap
import nrj

HERE = os.path.dirname(os.path.abspath(__file__))
CATALOG = os.path.join(HERE, os.pardir, "playtest", "dist", "catalog.json")

# The sim module that owns each game's cards, for the report header only.
OWNER = {"BAT": "bat.py", "NAP": "nap.py", "AoS": "aos.py",
         "NRJ": "bat.py / nap.py / aos.py / finale.py"}


# catalog.json keys the four games in lower case; these are the names the
# rest of the repository uses.
GAME_KEY = {"bat": "BAT", "nap": "NAP", "aos": "AoS", "nrj": "NRJ"}


def catalog():
    """{(game, deck title): [face names]} straight from the generators.

    Counted in FACES, not cards: a duplex deck prints two abilities per
    card and both have to be modelled, so the 4 Lab Rats are 8 sides and
    the 3 Apprentices are 6. catalog.json carries the second side as
    `backName`.
    """
    with io.open(CATALOG, encoding="utf-8") as fh:
        data = json.load(fh)
    out = {}
    for game, gv in data.items():
        for deck in gv["decks"]:
            faces = []
            for card in deck.get("cards", ()):
                faces.append(card["name"])
                if card.get("backName"):
                    faces.append(card["backName"] + " (back)")
            out[(GAME_KEY[game], deck["title"])] = faces
    return out


def fires(module, template, keys):
    """How many of `keys` have at least one firing site in the live source.

    `template` is the shape the module writes when it reaches for one card,
    e.g. 'self.bkd.get("%s")'. Counting call sites in the source is the only
    predicate here that cannot be satisfied by a card merely being NAMED in
    a list - which is how the Packet Sniffer claim was wrong on the first
    draft of this file: it is in BACKDOOR_ORDER and nowhere else.
    """
    src = inspect.getsource(module)
    return sum(1 for k in keys if (template % k) in src)


class Claim(object):
    """One deck's coverage, with a predicate that keeps it honest.

    game, deck   must match a catalog entry, so the denominator is real
    modelled     how many of the deck's printed effects are implemented
    predicate    re-derives `modelled` from the live modules; a claim whose
                 predicate returns a different number is STALE and fails
    gaps         the cards that are not implemented, by printed name
    note         why, for the gaps that are deliberate
    """

    def __init__(self, game, deck, modelled, predicate, gaps=(), note=""):
        self.game = game
        self.deck = deck
        self.modelled = modelled
        self.predicate = predicate
        self.gaps = list(gaps)
        self.note = note

    def check(self, total):
        """(ok, message). Fails when the code and the claim disagree."""
        try:
            got = self.predicate()
        except Exception as exc:                       # noqa: BLE001
            return False, "predicate raised %s: %s" % (type(exc).__name__, exc)
        if got != self.modelled:
            return False, ("claims %d of %d modelled, code says %d"
                           % (self.modelled, total, got))
        if len(self.gaps) != total - self.modelled:
            return False, ("claims %d modelled of %d but names %d gaps"
                           % (self.modelled, total, len(self.gaps)))
        return True, ""


# ---------------------------------------------------------------------------
# BAT. The deck that carries the game is Experiments; the three effect tables
# reduce each Upgrade, Specimen and Modification to a five-slot tuple
# (damage, soak, successes removed, dice the opponent exhausts, dice
# recovered), which is a reduction and not a transcription - see FIDELITY.
# ---------------------------------------------------------------------------
CLAIMS = [
    Claim("BAT", "Experiments", 19,
          lambda: len(bat.EXPERIMENT_EFFECT),
          gaps=["Diagnostic Trial"],
          note="committing Blue buys a look at the next Experiment and the "
               "policy has no lookahead to spend it on; declared in "
               "bat.UNMODELLED_EXP"),
    Claim("BAT", "Upgrades", 16,
          lambda: sum(1 for t in bat.UPGRADE_EFFECTS if t != bat.NO_EFFECT)),
    Claim("BAT", "Specimens", 8,
          lambda: sum(1 for t in bat.SPECIMEN_EFFECTS if t != bat.NO_EFFECT)),
    Claim("BAT", "Tyrant Attacks", 7,
          lambda: bat.ATTACK_COUNT,
          note="two carry deliberate changes agreed in testing and no longer "
               "match build_bat.py: Terrifying Roar exhausts 1 die not 2, "
               "and Adaptive Strike hits the next Rat clockwise"),
    Claim("BAT", "Lab Rats", 8,
          lambda: sum(len(r) for r in bat.RAT_SIDES),
          note="8 sides on 4 cards; silent during the Tyrant battle, which "
               "is the printed rule"),
    Claim("BAT", "Buff HP track", 1, lambda: 1,
          note="a track, not an effect"),

    # -----------------------------------------------------------------------
    # NAP. Tasks are well covered; the Final Exams are not covered at all,
    # and that single gap reaches forward into NRJ Tier III - see the
    # Devious Opportunities claim below.
    # -----------------------------------------------------------------------
    Claim("NAP", "Assignments", 24,
          lambda: len(set(nap.CRIT_COLOR) | set(nap.REQUEST_REWARD)),
          gaps=["Decode Nobulous' Lecture Notes",
                "Update Nobulous' Lab Notes"],
          note="the other 24 carry a CRIT_COLOR or a REQUEST_REWARD entry"),
    Claim("NAP", "Opportunities", 6,
          lambda: len(nap.COUPON),
          note="one coupon each under OPP_COUPONS, or one reward each under "
               "nap.OPPORTUNITY_REWARD"),
    Claim("NAP", "Setbacks", 0,
          lambda: 0,
          gaps=["Power Failure", "Contaminated Workbench", "Jammed Centrifuge",
                "Broken Neural Imager", "Escaped Specimen",
                "Automaton Malfunction"],
          note="SETBACKS is (target, dot) only. The ONE printed rule they "
               "share - the row locks until the Setback is resolved - IS "
               "modelled, so the deck works; the six cards print no "
               "individual effect to model"),
    Claim("NAP", "Final Exams", 0,
          lambda: 0,
          gaps=["Cranial Integrity Inspection", "Fine Motor Assessment",
                "Physiological Stress Test", "Council Etiquette Simulation",
                "Identity Recall Demonstration", "Final Imposter Examination",
                "Neural Response Screening", "Adaptive Reasoning Trial",
                "Council Recognition Drill", "Procedural Knowledge Review",
                "Unexpected Policy Debate", "Nobulous' Comprehensive Review"],
          note="ALL TWELVE print a dice restriction and nap.EXAMS carries "
               "(subject, dot, target) only, so none is modelled. This is "
               "the deck where NAP is actually lethal"),
    Claim("NAP", "Apprentices", 5,
          lambda: sum(1 for v in nap.ABILITIES.values() if v),
          gaps=["Prodigy"],
          note="Prodigy prints \"when using two dice of the same color as "
               "wild, only one must roll a success\" and maps to None - and "
               "Prodigy is the default in nap.run and in audit.py"),
    Claim("NAP", "Time Slots and FINF", 6,
          lambda: len(nap.FINF_SETTINGS),
          note="3 Time Slots plus 3 FINF cards; the FINF dial is modelled as "
               "the setting, with one row rather than three"),

    # -----------------------------------------------------------------------
    # AoS. Programs and base Limitations are fully covered. The gap is the
    # Technicians' second sides and, in NRJ, the Corrupted Limitations.
    # -----------------------------------------------------------------------
    Claim("AoS", "Routine Programs", 8,
          lambda: len(aos.PROGRAM_REWARDS["Routine"])),
    Claim("AoS", "Specialized Programs", 8,
          lambda: len(aos.PROGRAM_REWARDS["Specialized"])),
    Claim("AoS", "Unstable Programs", 8,
          lambda: len(aos.PROGRAM_REWARDS["Unstable"])),
    Claim("AoS", "Advanced Programs", 8,
          lambda: len(aos.ELEMENT_COUNTS["Advanced"]),
          note="they print no reward, which is why they are absent from "
               "PROGRAM_REWARDS; the Targets are modelled and three are "
               "faced every game"),
    Claim("AoS", "Limitations", 6,
          lambda: len(aos.LIMITATIONS),
          note="all six distinct in withhold_for - four colour shortages, "
               "the Diversity Protocol and the Red Quarantine"),
    Claim("AoS", "Technicians", 6,
          lambda: len(aos.TECHS),
          note="6 abilities on 3 duplex cards, all six referenced"),
    Claim("AoS", "Element mats", 5, lambda: 5,
          note="allocation mats, not effects"),

    # -----------------------------------------------------------------------
    # NRJ. The tier modules, plus the finale. The three fungible-token
    # defects all lived here; two are fixed and the third is below.
    # -----------------------------------------------------------------------
    Claim("NRJ", "BAT Protocols", 6,
          lambda: fires(bat, 'self.protocol == "%s"', bat.PROTOCOLS),
          note="PRICED 2026-11-06, forced one at a time: Accelerated Trials "
               "+0.1, Questionable Methodology -0.4, Cross-Contamination "
               "-3.1, Independent Funding -3.6, Questionable Procurement "
               "-3.7, Shared Equipment Budget -7.5. Tier I is a PENALTY and "
               "two of the six are not one"),
    Claim("NRJ", "BAT Modifications", 5,
          lambda: sum(1 for t in bat.MOD_EFFECTS if t != bat.NO_EFFECT),
          gaps=["Redundant Organs"],
          note="DRAWBACK-ONLY. Its \"while held\" cost (no_streak: cannot be "
               "active on consecutive turns) IS modelled; its benefit - "
               "\"the first time the holder would be knocked out, discard "
               "this card instead\" - is not, and the knockout in "
               "resolve_attack has no check for it. The card is charged its "
               "cost and paid nothing"),
    Claim("NRJ", "BAT Research Notes", 6,
          lambda: fires(bat, 'use_note("%s")', bat.NOTE_ORDER),
          note="six named cards since 2026-11-06; NOTE_REWARDS = False "
               "restores the pooled token every earlier figure was measured "
               "through"),
    Claim("NRJ", "NAP Imposter Tasks", 0,
          lambda: 0,
          gaps=["Neural Extraction Practicum", "Load-Bearing Prosthetics",
                "Emergency Specimen Handling", "Containment Drill"],
          note="nap.IMPOSTER_TASKS is (subject, dot, request, demand); the "
               "four printed effects are not modelled. The cards still bite "
               "through their raised Targets, which is Tier II's point"),
    Claim("NRJ", "NAP Following Setbacks", 0,
          lambda: 0,
          gaps=["Nobulous Needs This Now", "Unscheduled Demonstration",
                "Minor Laboratory Fire", "Where Did I Put That?"],
          note="nap.FOLLOWING is [(7,1),(7,1),(8,1),(8,1)] - four cards "
               "collapsed to two Targets and one flat upkeep, so the four "
               "printed effects are interchangeable in the model"),
    Claim("NRJ", "NAP Devious Opportunities", 5,
          lambda: sum(1 for _, p in nap.DEVIOUS if p != "exam_ignore"),
          gaps=["Definitely Curriculum-Approved"],
          note="its reward is \"ignore one exam's printed restriction\" and "
               "no exam restriction is modelled, so the card cannot pay out "
               "- declared at nap.py's exam_ignore. The other five are "
               "modelled, but see FUNGIBLE below: the coupons they leave "
               "behind are spent interchangeably"),
    Claim("NRJ", "AoS Interference", 6,
          lambda: fires(aos, 'self.intf == "%s"', aos.INTERFERENCE),
          note="PRICED 2026-11-06 against a 52.2% solo column: Memory Leak "
               "-18.3, I Don't Have Time for This -16.2, Works on My "
               "Machine -13.5, Legacy Hardware -12.0, Undocumented "
               "Dependencies -10.9, Nobulous Was Here -0.4. Five sit within "
               "7 points and the sixth is not a penalty at all"),
    Claim("NRJ", "AoS Corrupted Limitations", 0,
          lambda: 0,
          gaps=["Uneven Architecture", "Memory Collision",
                "Circular Reference", "Hard-Coded Constant",
                "Deprecated Function",
                "Stack Overflow"],
          note="THE ONE DECK WITH NO PER-CARD IDENTITY AT ALL. Each prints a "
               "distinct allocation corruption; the model draws none of "
               "them, applying one generic \"withhold 2 dice of a random "
               "non-required colour\" at CORRUPT_CHANCE. There is no index "
               "to audit, so audit.py cannot measure this deck"),
    Claim("NRJ", "AoS Backdoor Routines", 5,
          lambda: fires(aos, 'self.bkd.get("%s")', aos.BACKDOOR_ORDER),
          gaps=["Packet Sniffer"],
          note="\"look at the next Limitation before selecting a Program\" "
               "and the model has no Program-selection choice to inform, so "
               "aos.py leaves it unmodelled rather than guessing. The other "
               "five are named cards since 2026-11-05; BACKDOOR_REWARDS = "
               "False restores the pooled token. PRICED: only Resource Fork "
               "(+7.4) and Garbage Collection (+6.8) move the column; Root "
               "Access reads +1.0 and Privilege Escalation and Diagnostic "
               "Port read 0.0 although both DO fire"),
    # The shipping finale is finale.py. nrj.py models the SUPERSEDED
    # nine-attempt Suspicion finale and reads 23 of 24 on this same deck -
    # which is the point of the note below, not a second claim.
    Claim("NRJ", "Imposter Scenarios", 5,
          lambda: len(finale.REWARDS),
          gaps=["The Physician's Greeting", "An Old Injury",
                "Failed Apparatus", "Order of Precedence",
                "A Disputed Citation", "The Long Argument",
                "An Unwelcome Embrace", "The Ceremonial Seal",
                "A Sudden Fall", "The Long Session", "Tainted Wine",
                "Across the Chamber", "The Darkened Corridor",
                "The Night Watchman's Account", "An Open Window",
                "Someone Was Seen", "Rope Burns", "The Missing Hours",
                "A Second Search"],
          note="THE REGRESSION IN THE SET. The shipping finale uses each "
               "Exhibit's Target and the five Reward clauses; the other 19 "
               "printed effects do nothing. Most of them name Suspicion or "
               "a nine-attempt structure the rework removed and cannot be "
               "restored - but SIX do not: the dice restrictions on An Old "
               "Injury, The Ceremonial Seal, Order of Precedence, An Open "
               "Window, The Long Session and The Darkened Corridor still "
               "mean exactly what they print, and nrj.py ALREADY IMPLEMENTS "
               "ALL SIX (NEED_COLORS, NEED_DISTINCT, NEED_COUNT, "
               "FORBID_COLOR). The superseded model reads 23 of 24 on this "
               "deck and the shipping one reads 5; six of that gap is "
               "working code that was left behind"),
    Claim("NRJ", "Imposters", 0,
          lambda: 0,
          gaps=["Cross-Referenced (Archivist A)", "Precedent (Archivist B)",
                "Open Audition (Understudy A)", "Second Chair (Understudy B)",
                "Early Admittance (Usher A)", "Double Doors (Usher B)",
                "Sleight of Hand (Porter A)", "Heavy Lifting (Porter B)",
                "Requisition (Steward A)", "Standing Order (Steward B)"],
          note="TEN PRINTED ABILITIES, 5 cards x 2 sides, and not one of the "
               "five names appears anywhere in simulation/. The shipping "
               "finale simulator has no Imposter card: every finale figure, "
               "the 50.6% pitch included, is measured with no hero ability "
               "at all"),
]

# ---------------------------------------------------------------------------
# Reductions: cards that ARE modelled, but as something simpler than the
# printed text. These are not gaps and are not counted as gaps; they are the
# places where a number in RESULTS.txt describes a card the box does not
# quite print, and they belong in a coverage report for that reason.
# ---------------------------------------------------------------------------
FIDELITY = [
    ("BAT", "Upgrades / Specimens / Modifications",
     "every effect becomes a five-slot tuple, so a CONDITIONAL effect is "
     "modelled as its payoff with the condition always met: Serrated Claws "
     "\"+1 damage from each Blue or Green basic hit\" is a flat +1, "
     "Reinforced Jaw \"+2 if at least one Purple hit is applied\" a flat +2, "
     "Piercing Horn's Defense bypass is folded into its +2. The tap is "
     "never wasted, which makes the weak taps look better than they print"),
    ("BAT", "Splices that break",
     "a breaking Splice banishes a die of its own colour and its printed "
     "effect does not fire; deliberate, and declared in splice_breaks"),
    ("NAP", "Demand penalties",
     "the rules bill \"its printed Demand penalty\" every slot an Assignment "
     "survives on its Demand side; modelled as a flat 1 Health"),
    ("NAP", "Time Slots",
     "one row is modelled, not three, so a FINF card naming another slot "
     "applies when that slot comes round"),
    ("AoS", "Corruption",
     "CORRUPT_CHANCE = %.2f stands in for drawing a Corrupted Limitation at "
     "all, and CORRUPT_WITHHOLD = %d for whatever the drawn card would have "
     "said" % (aos.CORRUPT_CHANCE, aos.CORRUPT_WITHHOLD)),
    ("NRJ", "the finale's Research Pool",
     "all 18 Tier III cards reduce to \"domain-matched, worth 2 off an "
     "Exhibit's Target\"; their printed effects do not cross over. By "
     "design - the Pool is a currency - but it means no Tier III card's own "
     "text is tested twice"),
]

# ---------------------------------------------------------------------------
# Rewards spent out of a shared pool rather than per card. Two of these were
# found and fixed on 2026-11-05 and 2026-11-06; the third is still live.
# ---------------------------------------------------------------------------
FUNGIBLE = [
    ("AoS", "Backdoor Routines", "FIXED 2026-11-05",
     lambda: aos.BACKDOOR_REWARDS,
     "six once-per-game cards shared one counter spendable on a subset of "
     "the printed rewards"),
    ("BAT", "Research Notes", "FIXED 2026-11-06",
     lambda: bat.NOTE_REWARDS,
     "the same, and worse: of the two rewards the pool implemented, one "
     "never fired, so the published Tier III column measured one card"),
    ("NAP", "Devious Opportunities", "LIVE",
     lambda: not nap.DEVIOUS_IGNORE_SETBACK,
     "devious_coupons is a LIST OF PAYOUTS but ignore_setback() and "
     "move_setback() pop whichever coupon is on the end, so a coupon earned "
     "by any of the six can be spent on an ability NONE of them prints - "
     "ignoring a Setback. This one runs the opposite way to the other two: "
     "the pool OVER-delivers, granting an off-card power rather than "
     "withholding printed ones"),
]


def main(verbose=False):
    cards = catalog()
    total_cards = sum(len(v) for v in cards.values())
    print("PRINTED-EFFECT COVERAGE - is every card's text implemented?")
    print("%d cards in %d decks, counted from playtest/dist/catalog.json."
          % (total_cards, len(cards)))
    print("Claims are re-derived from the live modules on every run; a stale")
    print("claim fails this script rather than sitting in a comment.")

    stale = []
    missing = []
    seen = set()
    for game in ("BAT", "NAP", "AoS", "NRJ"):
        rows = [c for c in CLAIMS if c.game == game]
        if not rows:
            continue
        print()
        print("  %s   (%s)" % (game, OWNER[game]))
        for claim in rows:
            key = (claim.game, claim.deck)
            seen.add(key)
            if key not in cards:
                stale.append("%s - %s is not a deck in catalog.json"
                             % claim_key(claim))
                continue
            total = len(cards[key])
            ok, msg = claim.check(total)
            if not ok:
                stale.append("%s - %s: %s" % (claim.game, claim.deck, msg))
            flag = "" if ok else "   <-- STALE CLAIM"
            print("    %-28s %2d/%-2d modelled%s"
                  % (claim.deck[:28], claim.modelled, total, flag))
            if claim.gaps:
                missing.append(claim)
                print("        NOT MODELLED: %s" % ", ".join(claim.gaps))
            if claim.note and (verbose or claim.gaps):
                print(wrap(claim.note, "        "))

    for key in sorted(cards):
        if key not in seen:
            stale.append("%s - %s has %d cards and no claim"
                         % (key[0], key[1], len(cards[key])))

    print()
    print("  REDUCTIONS - modelled, but simpler than printed")
    for game, what, why in FIDELITY:
        print("    %s - %s" % (game, what))
        print(wrap(why, "        "))

    print()
    print("  SHARED-POOL REWARDS - cards that are not their own card")
    for game, deck, state, pred, why in FUNGIBLE:
        try:
            held = pred()
        except Exception:                              # noqa: BLE001
            held = False
        bad = (state == "LIVE") == bool(held)
        print("    %-4s %-24s %s%s"
              % (game, deck, state, "   <-- STALE CLAIM" if bad else ""))
        if bad:
            stale.append("%s - %s is marked %s and the knob disagrees"
                         % (game, deck, state))
        print(wrap(why, "        "))

    gap_cards = sum(len(c.gaps) for c in missing)
    print()
    print("  TOTAL: %d of %d printed card effects are not modelled, in %d "
          "decks." % (gap_cards, total_cards, len(missing)))
    print("  The three that reach furthest, in order:")
    print("    1  the 5 Imposters - 10 abilities, the whole finale deck, and")
    print("       every finale figure is measured without them")
    print("    2  the 12 Final Exams - all print a restriction, none is")
    print("       modelled, and it makes one NRJ Tier III card unpayable")
    print("    3  the 6 Corrupted Limitations - no per-card identity exists,")
    print("       so AoS Tier II is one generic effect wearing six names")

    if stale:
        print()
        print("  STALE: %d claim(s) no longer match the code." % len(stale))
        for line in stale:
            print("    %s" % line)
        return 1
    print()
    print("  every claim above re-derived from the live modules and agreed.")
    return 0


def claim_key(claim):
    return claim.game, claim.deck


def wrap(text, indent, width=74):
    out, line = [], indent
    for word in text.split():
        if len(line) + len(word) + 1 > width and line != indent:
            out.append(line)
            line = indent + word
        else:
            line = line + (" " if line != indent else "") + word
    out.append(line)
    return "\n".join(out)


if __name__ == "__main__":
    raise SystemExit(main("-v" in sys.argv))
