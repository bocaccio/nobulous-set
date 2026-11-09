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


def reads(module, text):
    """1 if the live source contains this exact text, else 0.

    The one-shot form of `fires`, for an effect that has one site rather than
    a table of them.
    """
    return 1 if text in inspect.getsource(module) else 0


def paid(deck):
    """Programs in `deck` whose printed Reward has a branch that acts on it.

    A name in PROGRAM_REWARDS is not an implementation: "banish" sat in all
    three decks for weeks with no branch in Game.reward, and this claim
    passed anyway because its predicate was len() of the table.
    """
    src = inspect.getsource(aos.Game.reward)
    return sum(1 for k in aos.PROGRAM_REWARDS[deck]
               if ('kind == "%s"' % k) in src)


def exhibit_faces():
    """How many of the 24 Council Tests print an effect to model.

    FIVE. The shipping Exhibit face prints Target, Damage and a Reward band,
    and only the five in build_nrj.EXHIBIT_REWARD print a rule in that band.
    The other nineteen print an italic COURTESY whose design rule is that it
    may not name a thing the game has - COURTESY_FORBIDDEN is the word list
    and check_app_sync.py enforces it - so there is nothing on them to model.
    The Scenario clauses still in build_nrj.SCEN are the record of the
    SUPERSEDED card and are no longer rendered.

    THE 2026-11-06 AUDIT GOT THIS WRONG FIRST TIME, and this function is the
    correction. It read the 19 dropped Scenario clauses as 19 unmodelled
    printed effects and called the deck "the regression in the set", when the
    shipping cards do not print them at all. Returns the modelled count only
    when the two generator tables really do partition the 24, so the claim
    fails if a courtesy is ever promoted to a rule.
    """
    rew = _gen_dict("EXHIBIT_REWARD")
    crt = _gen_dict("EXHIBIT_COURTESY")
    names = set(n for n, _d, _k, _t in finale.DECK)
    if set(rew) & set(crt) or (set(rew) | set(crt)) != names:
        return -1                      # fails the claim, loudly
    return len(names)


def _gen_dict(name):
    """The keys of a dict literal in generator/build_nrj.py."""
    import ast
    src = os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "generator", "build_nrj.py")
    with io.open(src, encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    for node in tree.body:
        if (isinstance(node, ast.Assign) and len(node.targets) == 1
                and getattr(node.targets[0], "id", "") == name):
            return [k.value for k in node.value.keys]
    raise RuntimeError("%s not found in generator/build_nrj.py" % name)


# The restriction keys exam_commit and the scoring step actually honour -
# DERIVED from the live source, not listed, so a key that stops being read
# stops counting. A hand-kept list of keys is the same mistake as counting
# names: it says a clause is modelled because somebody wrote it down.
# "crit" is deliberately absent from the candidates - it scores nothing on
# its own and is only the handle EXAM_CRIT_GATE attaches to; see the note on
# nap.EXAMS.
EXAM_KEYS = tuple(k for k in ("no_red", "colors", "need", "among", "dice",
                              "crit_val")
                  if reads(nap, 'rule.get("%s"' % k))


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
    Claim("NAP", "Assignments", 26,
          lambda: len(set(nap.CRIT_COLOR) | set(nap.REQUEST_REWARD)
                      | set(nap.TASK_EFFECT)),
          note="each carries a CRIT_COLOR, a REQUEST_REWARD or a "
               "TASK_EFFECT entry. The last two went in on 2026-11-06 and "
               "both pay in DECK ORDER rather than in dice, which is why "
               "they sat out: Decode Nobulous' Lecture Notes reorders the "
               "next three and Update Nobulous' Lab Notes sends one to the "
               "top or the bottom, worth +1.2 points between them. Their "
               "Demand sides - 3 colours, and store at most 1 die - are "
               "the only two Demand clauses in the deck that restrict "
               "rather than penalise, and are on the card as TASK_EFFECT"),
    Claim("NAP", "Opportunities", 6,
          lambda: len(nap.COUPON),
          note="one coupon each under OPP_COUPONS, or one reward each under "
               "nap.OPPORTUNITY_REWARD"),
    Claim("NAP", "Setbacks", 6,
          lambda: len(nap.SETBACKS),
          note="SIX CARDS PRINTING ONE SHARED RULE and a flavour line - "
               "build_nap.SB_TEXT, the same text on all six - and BOTH of "
               "its clauses are modelled: the row locks until the Setback "
               "is resolved, and an undiced Setback exhausts 1 die at the "
               "start of the Time Slot. nap.SETBACKS carries (target, dot) "
               "because that is all the cards print per card. Counted as a "
               "gap until 2026-11-06, which was the same over-count the "
               "audit made on the Exhibit courtesies: a card with no "
               "printed effect is not an unmodelled effect"),
    Claim("NAP", "Final Exams", 12,
          lambda: sum(1 for e in nap.EXAMS
                      if any(k in e[3] for k in EXAM_KEYS)),
          note="TWELVE OF TWELVE SINCE 2026-11-08. Eleven went in on "
               "2026-11-06, when nap.EXAMS grew a restriction column and "
               "exam_commit began honouring it - which also made Definitely "
               "Curriculum-Approved payable for the first time. The twelfth "
               "was not a model gap but a CARD-TEXT one, and the card was "
               "reworded: Neural Response Screening printed \"at least 1 "
               "Crit must contribute to COMPLETE THIS ASSIGNMENT\", which "
               "is Assignment language, and a Final Exam has no completion "
               "step - it charges 1 Health per success short. No reading of "
               "it said anything a player could act on: as a gate it dealt "
               "the card's whole Target in 23% of the sittings it got, "
               "-3.9 points across the solo column, which no other single "
               "exam comes near; as a commit rule it said nothing, because "
               "there is no way to commit FOR a Crit. It now prints \"each "
               "Crit counts as 1 success instead of 2\", which is the "
               "idiom the other two Crit cards already use, and "
               "EXAM_CRIT_GATE restores the printed gate"),
    Claim("NAP", "Apprentices", 6,
          lambda: sum(1 for v in nap.ABILITIES.values() if v),
          note="SIX OF SIX SINCE 2026-11-06, and Prodigy is the clearest "
               "case in this file of a card that cannot be modelled by "
               "itself. It prints \"when using two dice of the same color "
               "as wild, only one of those dice must roll a success\" - a "
               "relaxation of a rule the model did not have, because the "
               "colour requirement was enforced on the COMMIT and never on "
               "the successes. So ABILITIES mapped it to None, and the "
               "DEFAULT Apprentice in nap.run and in audit.py was the one "
               "with nothing to do. COLOR_RULE_ON_SUCCESS put the rule in "
               "first; it costs about 5 points of win rate across the "
               "whole ladder, because the model had been more generous "
               "than the cards"),
    Claim("NAP", "Time Slots and FINF", 6,
          lambda: len(nap.FINF_SETTINGS),
          note="3 Time Slots plus 3 FINF cards; the FINF dial is modelled as "
               "the setting, with one row rather than three"),

    # -----------------------------------------------------------------------
    # AoS. Programs and base Limitations are fully covered. The gap is the
    # Technicians' second sides and, in NRJ, the Corrupted Limitations.
    # -----------------------------------------------------------------------
    # THESE THREE PASSED ON A COUNT OF NAMES until 2026-11-06, and one of
    # the names did nothing: "banish" - "Banish 1 Limitation from the game",
    # printed on one Program of each deck - had no branch in Game.reward, so
    # three of the 24 Programs paid out silently nothing. len() of the table
    # could never have caught it. The predicate now counts the Programs
    # whose reward name has a branch that acts on it, which is the same
    # source-counting rule `fires` exists for.
    Claim("AoS", "Routine Programs", 8,
          lambda: paid("Routine")),
    Claim("AoS", "Specialized Programs", 8,
          lambda: paid("Specialized")),
    Claim("AoS", "Unstable Programs", 8,
          lambda: paid("Unstable")),
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
    Claim("NRJ", "BAT Modifications", 6,
          lambda: (sum(1 for t in bat.MOD_EFFECTS if t != bat.NO_EFFECT)
                   + reads(bat, '("m", REDUNDANT_ORGANS)')),
          note="SIX OF SIX SINCE 2026-11-06. Redundant Organs was "
               "drawback-only until then - its no_streak cost was charged "
               "and its printed save was never written, which is why "
               "MOD_EFFECTS[4] is the one all-zero row. The save is now in "
               "resolve_attack and fires in 12.6% of Tier II games; it is "
               "worth about 0.0 points, because a Rat holding a Value-5 "
               "Upgrade is almost never reached in Health at all. "
               "MOD_EFFECTS[4] STAYS ZERO AND IS RIGHT TO: damage_tyrant "
               "walks surviving Splices only and a blow under a card's "
               "Value bounces, so a Spliced Redundant Organs cannot be "
               "alive when the Tyrant would fall"),
    Claim("NRJ", "BAT Research Notes", 6,
          lambda: fires(bat, 'use_note("%s")', bat.NOTE_ORDER),
          note="six named cards since 2026-11-06; NOTE_REWARDS = False "
               "restores the pooled token every earlier figure was measured "
               "through"),
    Claim("NRJ", "NAP Imposter Tasks", 4,
          lambda: fires(nap, 'effect == "%s"',
                        [e for _s, _d, _r, _dm, e in nap.IMPOSTER_TASKS]),
          note="FOUR OF FOUR SINCE 2026-11-06. nap.IMPOSTER_TASKS was "
               "(subject, dot, request, demand) and the four cards were "
               "interchangeable; each now carries its printed effect - a "
               "die locked until the end of the Day, two successes needed "
               "from one colour, a 2-die minimum commit, and a die burned "
               "on the flip to Demand"),
    Claim("NRJ", "NAP Following Setbacks", 4,
          lambda: fires(nap, 'effect == "%s"',
                        [e for _t, _d, e in nap.FOLLOWING]),
          note="FOUR OF FOUR SINCE 2026-11-06, and the old model was wrong "
               "three ways at once. nap.FOLLOWING was [(7,1),(7,1),(8,1),"
               "(8,1)] - a Target and a FLAT 1-die upkeep - but only one of "
               "the four prints an upkeep, so the other three were charged "
               "a die a slot for text they do not carry; the four printed "
               "effects were interchangeable; and the dot was drawn at "
               "random from PBGY when all four print one. A Following "
               "Setback does not print the base card's row lock either - "
               "only Unscheduled Demonstration prints a weaker version of "
               "it. FOLLOWING_EFFECTS = False restores the flat upkeep"),
    Claim("NRJ", "NAP Devious Opportunities", 6,
          lambda: sum(1 for _, p in nap.DEVIOUS
                      if reads(nap, '"%s" in self.devious_coupons' % p)
                      or reads(nap, 'payout == "%s"' % p)),
          note="SIX OF SIX SINCE 2026-11-06. Definitely Curriculum-Approved "
               "ignores one exam's printed restriction and there was no "
               "restriction to ignore: earned in 153 of 6000 Tier III games "
               "and paid in 0 of them. With all twelve now modelled it is "
               "spent in 469 of the 733 games that earn it, measured the "
               "same way on 2026-11-08 - 390 of 690 when eleven were. "
               "See FUNGIBLE below for the other half of this deck's fix"),
    Claim("NRJ", "AoS Interference", 6,
          lambda: fires(aos, 'self.intf == "%s"', aos.INTERFERENCE),
          note="PRICED 2026-11-06 against a 52.2% solo column: Memory Leak "
               "-18.3, I Don't Have Time for This -16.2, Works on My "
               "Machine -13.5, Legacy Hardware -12.0, Undocumented "
               "Dependencies -10.9, Nobulous Was Here -0.4. Five sit within "
               "7 points and the sixth is not a penalty at all"),
    Claim("NRJ", "AoS Corrupted Limitations", 6,
          lambda: fires(aos, 'name == "%s"', aos.CORRUPTED)
                  + reads(aos, "self.corrupt_color"),
          note="SIX OF SIX SINCE 2026-11-06, and until then this was the "
               "ONE DECK IN THE SET THE MODEL NEVER DREW: CORRUPT_CHANCE "
               "stood in for drawing a card at all and CORRUPT_WITHHOLD for "
               "whatever the drawn card would have said, so there was no "
               "index for audit.py to count and the whole Tier II column "
               "was measured through a stand-in. Five of the six constrain "
               "the ALLOCATION, which corrupt_plan applies to the plan after "
               "allocation and before the roll; Deprecated Function is a "
               "scoring corruption and element_values applies it. "
               "CORRUPT_MODE = \"generic\" restores the stand-in"),
    Claim("NRJ", "AoS Backdoor Routines", 5,
          lambda: fires(aos, 'self.bkd.get("%s")', aos.BACKDOOR_ORDER),
          gaps=["Packet Sniffer"],
          note="\"look at the next Limitation before selecting a Program\" "
               "and play() takes Programs off a shuffled queue, so there is "
               "no selection for it to inform - and the dice a Limitation "
               "withholds already leave the pool before this model "
               "allocates. Unmodelled rather than guessed at, and the only "
               "one of the six in that position. THE OTHER FIVE NOW REACH "
               "THE TABLE: until 2026-11-06 BACKDOOR_CLAIM granted the "
               "front of BACKDOOR_ORDER at setup, so Resource Fork and "
               "Garbage Collection were held in 100% of games and the other "
               "four in 0% - three of them implemented, firing and never "
               "held. Claiming is now EARNED off the card's own printed "
               "condition and costs the next Program Reward, as all six "
               "print"),
    # The shipping finale is finale.py. nrj.py models the SUPERSEDED
    # nine-attempt Suspicion finale and reads 23 of 24 on this same deck -
    # which is the point of the note below, not a second claim.
    Claim("NRJ", "Imposter Scenarios", 24,
          exhibit_faces,
          note="FIVE REWARDS MODELLED AND NINETEEN CARDS WITH NO PRINTED "
               "EFFECT, which is the whole deck. The audit of 2026-11-06 "
               "first read this as 5 of 24 and called it the regression in "
               "the set; it was reading the dropped Scenario clauses in "
               "build_nrj.SCEN, which the shipping Exhibit face does not "
               "render. An Exhibit prints Target, Damage and a Reward band, "
               "and nineteen of those bands carry an italic courtesy that "
               "may not name a thing the game has. exhibit_faces() asserts "
               "the partition rather than trusting this paragraph"),
    Claim("NRJ", "Imposters", 10,
          lambda: sum(1 for h in finale.HEROES
                      if reads(finale, 'hero == "%s"' % h)),
          note="TEN OF TEN SINCE 2026-11-06, ported in from "
               "proto/imposters.py, which had all ten implemented and "
               "calibrated while the shipping module had no hero code at "
               "all. The audit's first pass said no Imposter name appeared "
               "anywhere in simulation/; proto/ is under simulation/, so "
               "the gap was a port and not a write. HERO = None is still "
               "the pitch and still reproduces every published figure, "
               "because a side is quoted as a delta against a heroless "
               "baseline - but the centrepiece of the set is no longer the "
               "one deck the shipping simulator could not play"),
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
# Rewards spent out of a shared pool rather than per card. All three were
# found and fixed between 2026-11-05 and 2026-11-06; each predicate below is
# what keeps the fix from being undone quietly.
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
    ("NAP", "Devious Opportunities", "FIXED 2026-11-06",
     lambda: not (nap.DEVIOUS_IGNORE_SETBACK or nap.DEVIOUS_MOVE_SETBACK
                  or nap.DEVIOUS_CASH_EARLY),
     "devious_coupons IS a list of payouts, but ignore_setback() and "
     "move_setback() called .pop(), which takes whichever coupon is on the "
     "end - so a coupon earned by any of the six bought \"ignore a "
     "Setback\", an ability none of them prints, and 27% of every coupon "
     "earned left the hand that way. This one ran the opposite way to the "
     "other two: the pool OVER-delivered. The three off-card levers now "
     "take a TUPLE OF NAMES rather than a boolean, so a lever has to name "
     "the card paying for it and the fungible form cannot be written again "
     "by accident; all three ship empty"),
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
    # DERIVED, not typed. The previous version of this footer was three
    # hardcoded sentences about the three largest gaps, and two of the three
    # were fixed within a day of being written - which is the exact failure
    # this whole file exists to stop, reproduced in its own summary.
    if missing:
        print("  The %d widest, by cards:" % min(3, len(missing)))
        for claim in sorted(missing, key=lambda c: -len(c.gaps))[:3]:
            print("    %-4s %-26s %d of %d"
                  % (claim.game, claim.deck, len(claim.gaps),
                     len(cards[(claim.game, claim.deck)])))

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
