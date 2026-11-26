"""Cross-check the playtest lab's card data against the generators.

    python check_app_sync.py

AGENTS.md: "Keep BAT, NAP, AoS and NRJ card data synchronized with the
authoritative generator and rule sources." Nothing enforced that, so this
does. It found one divergence the day it was written: the lab printed the
Overheated face of the eighth Advanced Program with the extra success on
the wrong element.

Neither side is executed. The generators have no `if __name__` guard, so
importing one would render every card; they are walked as an AST instead
and only module-level literal assignments are evaluated. The dist JS is
matched bracket-by-bracket and parsed as JSON once trailing commas are
stripped and JS's unquoted object keys are quoted.

Exit status is the number of failed checks, so it can gate a commit.
"""
import ast
import hashlib
import io
import json
import math
import os
import re
import sys
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def py_tables(rel):
    """Module-level literal assignments of a generator, in file order."""
    with io.open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        tree = ast.parse(f.read())
    env = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for t in node.targets:
            # `ANA, ENG, PRO, THE = 'Anatomy', ...` is a tuple target, and
            # the subject constants the card tables reference are bound that
            # way - skipping it left every table unresolvable.
            if isinstance(t, (ast.Tuple, ast.List)):
                try:
                    vals = _ev(node.value, env)
                except (ValueError, KeyError, TypeError):
                    continue
                if len(vals) == len(t.elts):
                    for sub, v in zip(t.elts, vals):
                        if isinstance(sub, ast.Name):
                            env[sub.id] = v
                continue
            if not isinstance(t, ast.Name):
                continue
            try:
                env[t.id] = _ev(node.value, env)
            except (ValueError, KeyError, TypeError):
                pass
    return env


def _ev(n, env):
    if isinstance(n, ast.Constant):
        return n.value
    if isinstance(n, ast.Name):
        return env[n.id]            # KeyError -> skipped by the caller
    if isinstance(n, (ast.Tuple, ast.List)):
        return [_ev(x, env) for x in n.elts]
    if isinstance(n, ast.Dict):
        return dict((_ev(k, env), _ev(v, env))
                    for k, v in zip(n.keys, n.values))
    if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Add):
        return _ev(n.left, env) + _ev(n.right, env)
    if isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.USub):
        return -_ev(n.operand, env)
    raise ValueError("not a literal")


def js_array(rel, name):
    """The array literal assigned to `name` in a dist JS file."""
    with io.open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        s = f.read()
    m = re.search(r"\b(?:const|let|var)\s+" + re.escape(name) + r"\s*=\s*\[", s)
    if not m:
        raise KeyError("%s not found in %s" % (name, rel))
    i = m.end() - 1
    depth, j, instr, esc = 0, i, False, False
    while j < len(s):
        c = s[j]
        if instr:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                instr = False
        elif c == '"':
            instr = True
        elif c in "[{":
            depth += 1
        elif c in "]}":
            depth -= 1
            if depth == 0:
                break
        j += 1
    body = s[i:j + 1]
    body = re.sub(r",(\s*[\]\}])", r"\1", body)        # trailing commas
    return json.loads(body)


def js_literal(rel, name):
    """Like js_array but also takes an object literal, and tolerates the
    unquoted keys JS allows (NAP_EXAMS and PROGRAM_TARGETS both use them)."""
    with io.open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        s = f.read()
    m = re.search(r"\b(?:const|let|var)\s+" + re.escape(name) + r"\s*=\s*[\[{]", s)
    if not m:
        raise KeyError("%s not found in %s" % (name, rel))
    i = m.end() - 1
    depth, j, instr, esc, quote = 0, i, False, False, ""
    while j < len(s):
        c = s[j]
        if instr:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == quote:
                instr = False
        elif c in "\"'":
            instr, quote = True, c
        elif c in "[{":
            depth += 1
        elif c in "]}":
            depth -= 1
            if depth == 0:
                break
        j += 1
    return js_parse(s[i:j + 1])


def js_parse(body):
    out, i, n = [], 0, len(body)
    while i < n:
        c = body[i]
        if c == "'":                      # single-quoted string -> double
            j, buf = i + 1, []
            while j < n and body[j] != "'":
                if body[j] == "\\":
                    buf.append(body[j:j + 2]); j += 2; continue
                buf.append('\\"' if body[j] == '"' else body[j]); j += 1
            out.append('"' + "".join(buf) + '"'); i = j + 1; continue
        if c == '"':
            j = i + 1
            while j < n and body[j] != '"':
                j += 2 if body[j] == "\\" else 1
            out.append(body[i:j + 1]); i = j + 1; continue
        out.append(c); i += 1
    s = "".join(out)
    s = re.sub(r"([\{,]\s*)([A-Za-z_$][\w$]*)(\s*:)", r'\1"\2"\3', s)
    s = re.sub(r",(\s*[\]\}])", r"\1", s)
    return json.loads(s)



FAILS = []
SKIPPED = []


def check(label, ok, detail=""):
    print("  %-52s %s%s" % (label, "PASS" if ok else "FAIL",
                            "" if ok else "  " + detail))
    if not ok:
        FAILS.append(label)


def skip(label, why):
    """A check that could not run here.

    NOT a pass. The whole value of this file is that a line it prints
    was tested, so a check that never ran printing PASS is the one lie
    it must not tell - and it was telling it: the Pillow guard below
    called check(..., True, "skipped"), and check() only prints a
    detail when it FAILS, so a missing tool read as a clean pass.
    """
    print("  %-52s SKIP  %s" % (label, why))
    SKIPPED.append("%s - %s" % (label, why))


def rows(label, a, b, fields):
    """Compare two row lists field by field. `fields` maps a name to a pair
    of index-getters, (from a, from b)."""
    if len(a) != len(b):
        check(label, False, "%d rows vs %d" % (len(a), len(b)))
        return
    bad = []
    for i, (ra, rb) in enumerate(zip(a, b)):
        for name, (ga, gb) in fields.items():
            try:
                va, vb = ga(ra), gb(rb)
            except (IndexError, KeyError, TypeError) as ex:
                bad.append("row %d %s: %s" % (i, name, ex))
                continue
            if va != vb:
                bad.append("row %d %s: %r vs %r" % (i, name, va, vb))
    check("%s (%d rows)" % (label, len(a)), not bad,
          "; ".join(bad[:4]) + (" ..." if len(bad) > 4 else ""))


def text(rel):
    with io.open(ROOT + "\\" + rel, encoding="utf-8") as f:
        return f.read()


G = lambda i: (lambda r: r[i])

print("NAP - generator/build_nap.py and simulation/nap.py vs playtest")
gn = py_tables("generator/build_nap.py")
sn = py_tables("simulation/nap.py")
jt = js_literal("playtest/dist/suite.js", "NAP_TASKS")
# generator TASKS: name, subject, dot, credits, Req, req effect, Dem, ...
rows("build_nap TASKS vs nap.py TASKS", gn["TASKS"], sn["TASKS"],
     {"request": (G(4), G(0)), "demand": (G(6), G(1)),
      "color": (G(2), G(2)), "credits": (G(3), G(3))})
je = js_literal("playtest/dist/suite.js", "NAP_EXAMS")
# "restriction" is the printed clause itself, and nothing compared it until
# 2026-11-08: the four rows below are what a Final Exam IS, and the clause
# was the one field the card, the lab and the model could disagree about in
# silence. Neural Response Screening did, for weeks, in all three at once.
# AND THE MODEL'S COPY OF THE SAME THREE NUMBERS, which nothing compared
# either: the check above holds the card against the LAB, and nap.py carries
# its own (subject, dot, Target) for all twelve. A Target that moves on the
# card now has to move in both other owners. Neural Response Screening's
# Target came down to 5 on 2026-11-08 and this is what makes that one edit
# three.
rows("build_nap EXAMS vs nap.py EXAMS", gn["EXAMS"], sn["EXAMS"],
     {"subject": (G(1), G(0)), "color": (G(2), G(1)),
      "target": (G(3), G(2))})
_exam_text = dict((r[0], r[4]) for r in gn["EXAMS"])
_nrs = "Each Crit counts as 1 success instead of 2."
_suite = text("playtest/dist/suite.js")
check("Neural Response Screening prints one clause in all three owners",
      _exam_text.get("Neural Response Screening") == _nrs
      and sn["EXAMS"][6][3].get("crit_val") == {"any": 1},
      "card=%r model=%r" % (_exam_text.get("Neural Response Screening"),
                            sn["EXAMS"][6][3]))
# A key in a rule dict is a table entry, and AGENTS.md's warning applies: the
# lab has to be caught READING it. "critAll1" sat in NAP_EXAMS for one commit
# with nothing scoring it, which is the shape of every claim in this repo
# that has ever passed while the card did nothing.
# The lab blocked Resolve until the restriction was met, so a clause the dice
# decide - and that STR cannot be spent to retry once it is gone - could
# dead-end an exam with no way forward. Only roll-outcome clauses can do
# that, and this was the only one that was unanswerable.
check("no Final Exam still prints Assignment language",
      not any("complete this Assignment" in r[4] for r in gn["EXAMS"]),
      "an exam still asks to COMPLETE itself, which exams do not do")
check("EXAM_CRIT_GATE still restores the printed gate and ships off",
      sn["EXAM_CRIT_GATE"] is False
      and 'if EXAM_CRIT_GATE and rule.get("crit")' in text("simulation/nap.py"),
      "EXAM_CRIT_GATE=%r" % (sn.get("EXAM_CRIT_GATE"),))
js = js_literal("playtest/dist/suite.js", "NAP_SETBACKS")

# -----------------------------------------------------------------------
# THE 2026-11-12 ASSIGNMENT REVISION. Three things changed on all 26 Tasks
# at once - the Request conditions went, the reward names a colour, and the
# Demand side gained a reward of its own - and the lab prints that text to
# the player. Nothing compared the EFFECT STRINGS until now: the tables
# above compare names, Targets, dots and Skulls, so a card could be
# reworded in the generator and the lab could go on teaching the old rule
# indefinitely. Both faces, string for string.
# -----------------------------------------------------------------------
# EVERY DEMAND FACE PAYS. That is the whole of the revision's second half,
# and it is the kind of thing that is true on 25 of 26 cards for a week.
_norew = [r[0] for r in gn["TASKS"] if "<b>Reward:</b>" not in r[7]]
check("every one of the 26 Demand faces prints a Reward", not _norew,
      "%r" % (_norew[:3],))

# AND A FIXED-COLOUR REQUEST RECOVERY NEVER PAYS THE CARD'S OWN DOT. The dot
# is what the Primary queues for the next Time Slot, so recovering it twice
# is half a reward - the design rule behind the whole colour column. Read
# off the printed text, both halves of a two-colour offer, so a card
# reworded to pay its own dot fails here rather than at the table.
_DOTNAME = {"Y": "Yellow", "B": "Blue", "G": "Green", "P": "Purple"}
_selfpay = []
for _r in gn["TASKS"]:
    # (?:die|dice), NOT dice? - which matches "dic" and "dice" and never
    # "die", so this check saw nothing on any single-die reward and
    # passed vacuously on 21 of the 26 cards. Found by mutation, not by
    # reading it: a card edited to pay its own dot stayed green.
    _m = re.search(r"[Rr]ecover (?:up to \d+ )?(.+?) (?:die|dice)\.", _r[5])
    if not _m:
        continue
    _named = [c for c in _DOTNAME.values() if c in _m.group(1)]
    if _DOTNAME[_r[2]] in _named:
        _selfpay.append((_r[0], _r[2], _m.group(1)))
check("no Request recovery pays the colour the card's own dot queues",
      not _selfpay, "%r" % (_selfpay[:3],))


print()
print("AoS - generator/aos.py and simulation/aos.py vs playtest")
ga = py_tables("generator/aos.py")
sa = py_tables("simulation/aos.py")
jpt = js_literal("playtest/dist/app.js", "PROGRAM_TARGETS")
# AGAINST THE MODEL, NOT THE LAB, since 2026-11-25. This loop used to
# hold generator/aos.py's Targets against playtest/dist/app.js, and when
# the lab stopped being maintained that made it the ONLY owner the
# Targets were checked against - which would have left them checked
# against nothing. simulation/aos.py carries the same two faces, so it
# takes the job over.
#
# FOUR DECKS NOW. The three-deck list was already a gap: Volatile was
# added on 2026-11-25 and this loop would have skipped it silently, which
# is the failure mode the whole file exists to prevent.
#
# The marks are not compared directly - the model has no PROGRAM_MARKS,
# it carries the consequence instead - so the Overheated face IS the
# assertion: the back must be the front with +1 on the ringed element,
# and a wrong mark cannot survive that.
_spt = sa["PROGRAM_TARGETS"]
for deck, key in (("Routine", "ROUTINE"), ("Specialized", "SPECIALIZED"),
                  ("Unstable", "UNSTABLE"), ("Volatile", "VOLATILE")):
    src = ga[key]
    rows("aos.py %s vs the model's front Targets" % deck,
         src, _spt[deck]["front"], {"targets": (G(1), lambda r: r)})
    want = []
    for name, t, mark in [(r[0], list(r[1]), r[2]) for r in src]:
        t[mark] = min(4, t[mark] + 1)
        want.append(t)
    rows("%s back == front +1 at the mark" % deck,
         want, _spt[deck]["back"], {"targets": (lambda r: r, lambda r: r)})

# ---- Assemblies: one card, two faces, and four owners ----------------
# The front conceals the back on purpose, so the two must NOT be derivable
# from each other - except the Advanced colors line, which IS derived from
# the back and is the one thing that must never be stored twice.
_gasm = ga["ASSEMBLIES"] + [ga["COVERT"]]
_sasm = sa["ASSEMBLIES"] + [sa["COVERT"]]
check("generator and model hold the same nine Assemblies",
      _gasm == _sasm, "%r" % ([a for a, b in zip(_gasm, _sasm) if a != b][:2],))
check("...and there are nine of them, eight base and one Tier III",
      len(ga["ASSEMBLIES"]) == 8 and ga["COVERT"][0] == "Covert Sensor Array",
      "%d base, ninth is %r" % (len(ga["ASSEMBLIES"]), ga["COVERT"][0]))

# EVERY BACK IS TWO COLOURS ACROSS TWO OR THREE ELEMENTS, which is what
# makes the Advanced colors line short enough to print and vague enough to
# conceal the element count.
_badback = [a[0] for a in _gasm
            if len({c for c, _ in a[3]}) != 2 or not 2 <= len(a[3]) <= 3]
check("every Assembly back is two colours over two or three elements",
      not _badback, "%r" % (_badback,))

# A DOUBLED COLOUR IS THE FLEXIBLE RECIPE, measured in aosbuild.py: a
# recipe asking three DISTINCT colours is three chances to be blocked
# where two is two, and respeccing them that way made dead setups WORSE
# (23.4% against 15.4%). So every Build recipe is two colours too.
_badbuild = [a[0] for a in _gasm if len(set(a[1])) != 2]
check("...and every Build recipe asks exactly two colours",
      not _badbuild, "%r" % (_badbuild,))

# Short colour codes to the names the rest of the file uses. It lived in
# the lab-export block until that went on 2026-11-25; the Assembly checks
# below still need it.
_LONGA = {"P": "purple", "B": "blue", "G": "green", "Y": "yellow"}

# THE ADVANCED COLORS LINE IS DERIVED, and the point of saying so here is
# that four of the nine print a FRONT recipe in colours their own back
# never asks for. That is the concealment working. If this ever came out
# as nine, somebody had derived one face from the other.
_hidden = [a[0] for a in _gasm
           if {_LONGA[c] for c in a[1]} != {_LONGA[c] for c, _ in a[3]}]
check("four Assemblies build in colours their own back never asks",
      len(_hidden) == 4, "%r" % (_hidden,))

# THE MOD DROPS 'Assembly 4' AT TIER III, because a card's nickname is its
# index in this table and the standard Sensor Array is the card the Covert
# one replaces. Reordering ASSEMBLIES has to fail here, not at the table.
check("the Sensor Array is the fourth Assembly, which tts/lua.lua drops by index",
      ga["ASSEMBLIES"][3][0] == "Sensor Array",
      "fourth is %r" % (ga["ASSEMBLIES"][3][0],))
check("...and lua.lua still drops that index at Tier III",
      "dropCard(asm, 'Assembly 4')" in text("tts/lua.lua"))

# ONE NAME IS SHARED BY TWO CARDS THAT ARE BOTH IN PLAY. The Assembly back
# "Carry a Moving Load" is also a Specialized Program, and both are on the
# table in the same game. It is deliberate - the handed-over mockup names
# it - but a SECOND collision would be a mistake, and name-keyed tables
# like REQ_MAP and FLAVOR would swallow it silently.
_progs = {r[0] for k in ("ROUTINE", "SPECIALIZED", "UNSTABLE") for r in ga[k]}
_collide = sorted(a[2] for a in _gasm if a[2] in _progs)
check("exactly one Assembly back shares a name with a Program still in play",
      _collide == ["Carry a Moving Load"], "%r" % (_collide,))

# THE SETUP NUMBERS, in the book, the lab and the model. Six offered and a
# colour floor of two are not decoration: at the handed-over five with no
# floor, 15.4% of Standard setups cannot build three Assemblies at all.
check("the model offers six Assemblies and floors the colours at two",
      sa["OFFER_SIZE"] == 6 and sa["COLOR_FLOOR"] == 2,
      "offer %r floor %r" % (sa.get("OFFER_SIZE"), sa.get("COLOR_FLOOR")))
# AGAINST THE RAW BOOK, not _RULES: that is built further down this file
# and strips the tags these phrases are made of.
_aoshtml = text("rules/aos.html")
check("...and rules/aos.html prints both",
      "reveal <b>6</b> of them" in _aoshtml
      and "at least two</b> of your 10 Programs" in _aoshtml)

# THE FINALE'S THRESHOLD, which is the whole endgame: at most one failed
# element across three stages, and at least 1 Health.
check("the model scores the finale on one failed element across all of it",
      sa["FINALE_ALLOWED"] == 1 and sa["BUILD_TARGET"] == 3
      and sa["ROUNDS"] == 3,
      "allowed %r build %r rounds %r"
      % (sa.get("FINALE_ALLOWED"), sa.get("BUILD_TARGET"), sa.get("ROUNDS")))
check("...and rules/aos.html prints it that way round",
      "At most one</b>, and <b>at least 1" in _aoshtml
      and "loses the game outright</b>" in _aoshtml)
check("...and the Assembly card's own footer says the same",
      "A 2nd failed element across the finale loses the game."
      in text("generator/aos_faces.py"))

# THE OLD ENDGAME IS GONE EVERYWHERE, which is the check that would have
# caught a book still telling a player to face three Advanced Programs.
_ghosts = [w for w in ("Advanced Programming", "AoS_Advanced")
           if w in _aoshtml or w in text("playtest/dist/app.js")]


# Required-colour dots. simulation/aos.py's PROGRAM_REQS is GENERATED from
# generator/aos.py's REQ_MAP, so the only way it goes wrong is someone
# editing a dot on one side and not the other. Dot counts are NOT uniform
# per deck: rules/aos.html claims two for Specialized and Advanced and three
# cards disagree, which is a card-vs-rulebook question rather than drift.
_LONG = {"G": "green", "P": "purple", "Y": "yellow", "B": "blue"}
_req = ga["REQ_MAP"]
_sim_req = sa["PROGRAM_REQS"]
_wrong = []
for deck, key in (("Routine", "ROUTINE"), ("Specialized", "SPECIALIZED"),
                  ("Unstable", "UNSTABLE"), ("Volatile", "VOLATILE")):
    for pid, row in enumerate(ga[key]):
        name, targets = row[0], row[1]
        want = [_LONG[d] if d else None
                for d in (list(_req.get(name, [])) + [None] * len(targets))
                [:len(targets)]]
        got = list(_sim_req[deck][pid])
        if got != want:
            _wrong.append("%s: %r != %r" % (name, got, want))
        elif len(got) != len(targets):
            _wrong.append("%s: %d dots for %d elements"
                          % (name, len(got), len(targets)))
check("PROGRAM_REQS matches generator REQ_MAP for all 32 Programs",
      not _wrong, "; ".join(_wrong[:3]))
_asrc = text("simulation/aos.py")
check("the model actually applies required colours",
      "REQUIRED_COLORS = True" in _asrc and "PROGRAM_REQS[deck][pid]" in _asrc)
check("a required die is not charged for twice",
      "for held in locked:" in _asrc)
check("rules/aos.html still teaches the required-colour commitment",
      "required&#8209;color dice" in text("rules/aos.html"))

# THE ALLOCATION FLOOR has three owners and they must agree: the rulebook
# prints it, simulation/aos.py enforces it through seed_minimum, and the lab
# has enforced it all along in rollElement. The rulebook used to say the
# OPPOSITE - "an element may be left with no dice at all" - which is what
# made deliberate single-element sacrifice free and worth up to 27 points.
_arules = text("rules/aos.html")
check("rules/aos.html prints the allocation floor",
      "Every element must receive at least one die." in _arules
      and "never fewer than one" in _arules)
check("rules/aos.html no longer says an element may be left bare",
      "may be left with no dice at all" not in _arules)
check("simulation/aos.py enforces the floor (MIN_DICE_PER_ELEMENT %r)"
      % sa.get("MIN_DICE_PER_ELEMENT"),
      sa.get("MIN_DICE_PER_ELEMENT") == 1
      and "def seed_minimum" in _asrc)

# A CORRUPTED LIMITATION WITHHOLDS A COLOUR THE PROGRAM DOES NOT REQUIRE.
# Four owners: the card, the supplement, the model and the lab. The lab is
# the one that can silently go wrong, because it is the only one that has to
# CHOOSE the colour, and it needs the dots to do it.
_jsrc_a = text("playtest/dist/app.js")
# THE EXCLUSION CAME OFF ON 2026-11-06 and all four owners had to drop it
# together, so these four checks now assert its ABSENCE. It made the Tier II
# card gentler than the native Limitation it is drawn instead of, and the
# whole tier was worth +0.1 points over Tier I because of it.
check("the Corrupted Limitation card no longer excludes required colours",
      "does <b>not</b> require" not in text("generator/build_nrj.py")
      and "A withheld color cannot answer a required-color dot."
      in text("generator/build_nrj.py"))
check("and the card drops the all-colours escape clause with it",
      "If the Program requires every color, select any."
      not in text("generator/build_nrj.py"))
check("rules/nrj.html drops the exclusion too",
      "a color the Program does not require" not in text("rules/nrj.html"))
check("the model draws any colour (CORRUPT_AVOID_REQUIRED %r)"
      % sa.get("CORRUPT_AVOID_REQUIRED"),
      sa.get("CORRUPT_AVOID_REQUIRED") is False)
# Each reveal re-rolls: the cards say "a randomly selected color" and
# "randomly select one element", which is per card, not per game.
# rules/aos.html must not claim a uniform dot count: one card breaks it.
# IT NO LONGER NAMES THE CARD, as of 2026-11-25, when the rulebooks were
# stripped of text about specific cards. So the claim being held is the one
# that is still a rules error if it goes wrong: the book must tell a player
# to read the card, and must not assert a count the deck contradicts. The
# count itself is checked against generator/aos.py further down.
check("rules/aos.html does not claim a uniform dot count",
      "some cards ask for more" in _arules
      and "carry two required&#8209;color dots; Routine" not in _arules)
# PERCENTAGES ARE OUT OF THE SUPPLEMENT ENTIRELY, 2026-11-25. They used to
# be allowed on condition the book said where they came from, and the
# "About the percentages" box was that disclosure. The rulebooks no longer
# carry model output, commentary on impact, or design rationale at all, so
# the disclosure has nothing left to disclose and the check is inverted:
# nothing in the supplement may quote a rate again. This is the editorial
# rule made testable, and it fails on the next figure someone pastes in.
_nrules = text("rules/nrj.html")
_rates = [_p for _p in ("win rate", "about 1 in", "about 2 in", "about 3 in",
                        "about 4 in", "in the model", "design simulation",
                        "% chance", "points of win")
          if _p in _nrules]
check("rules/nrj.html quotes no model percentages",
      not _rates, "still quotes: %r" % (_rates,))
check("no bare win-rate claim is left in rules/aos.html",
      "points of win rate" not in _arules)
# THE WIN CONDITION IS SURVIVAL, AND THE RULEBOOK HAS TO SAY SO. aos.play()
# ends `return self.hp > 0` after the third Advanced Program, so an Advanced
# Program you fail still counts as faced. The rulebook once said "Complete
# all three with Health remaining", where "complete" reads as "succeed at" -
# the one phrase that made the deliberate-failure route look open on paper.
# Fixed 2026-11-03 in e812c7e; HANDOFF.md went on calling it open for five
# days because nothing held the sentence to the model. This is that.
# AND THE WIN CONDITION CHANGED AGAIN ON 2026-11-24, the other way. It is
# no longer survival: the Assembly finale is scored on ONE failed element
# across three stages, so a stage you fail twice does lose the game. The
# old danger was a book that read as "succeed at all three" when surviving
# was enough; the new one is a book that still says surviving is enough.
check("rules/aos.html scores the finale on failed elements, not survival",
      "At most one</b>, and <b>at least 1" in _aoshtml
      and "loses the game outright</b>" in _aoshtml
      and "Work through all three with Health remaining" not in _arules
      and "still counts as faced" not in _arules)
check("simulation/aos.py scores it the same way",
      "self.finale_failed > FINALE_ALLOWED" in _asrc
      and "return self.hp > 0 and self.finale_failed <= FINALE_ALLOWED" in _asrc)
# THE DEADLINE IS THE OTHER HALF, and it is the half the measurement says
# decides the game: 63.5% of Standard losses are reaching the end of round
# three without three Assemblies built. A book that forgets to print it
# leaves a player with no reason to hurry.
check("rules/aos.html prints the three-round deadline",
      "three rounds</b> to <b>build three Assemblies" in _aoshtml
      and "without three Assemblies built" in _aoshtml)
check("...and the model enforces it",
      "if len(done) < BUILD_TARGET:" in _asrc)
# And the brake that makes survival-as-the-rule safe to print: Health is
# only ever regained by a Program Reward, and a Reward needs no failed
# element, so dumping Programs forfeits the only healing in the game.
# AGAINST THE RAW BOOK, so every phrase here has to be one the source
# does not wrap across a line - _arules is text(), not _plain().
# THE PROSE THAT ARGUED THIS IS GONE, 2026-11-25 - it was rationale, and
# the rulebooks no longer carry any. What made the argument true is still
# printed, and it is two card-facing conditions rather than a paragraph, so
# those are what this holds now. If either stops being printed, failing
# deliberately becomes a free move again and no other check would say so.
# READ WHITESPACE-INSENSITIVELY, unlike the check it replaces. The old
# one matched the raw source and carried a comment warning that every
# phrase had to be one the book does not wrap across a line - which made
# it a check on the typesetting as much as on the rule, and it broke the
# moment the paragraph above it got shorter and the clause moved up onto
# one line. 2026-11-25.
_aflat = " ".join(_arules.split())
check("rules/aos.html prints both halves of the failure price",
      "no failed elements at all" in _aflat
      and "never above 6" in _aflat
      and "without a Catastrophic Failure" in _aflat)

# THE DECK MIX IS AoS'S DIFFICULTY DIAL and it had three unchecked copies:
# simulation/aos.py's LEVELS, the lab's AOS_LEVELS and the printed table.
# Retuned 2026-11-03, so hold them together from here on.
_slv = sa["LEVELS"]
_mix_wrong = []
for lvl in ("Easy", "Standard", "Hard", "Nobulous"):
    want = list(_slv[lvl])
    # the printed table prints the same numbers on one row. FOUR of them
    # since 2026-11-25, so this is built from the tuple rather than from a
    # fixed count - the next deck added here must not need this edited.
    row = "<tr><td>%s</td>%s</tr>" % (
        lvl, "".join("<td>%d</td>" % n for n in want))
    bold = "<tr><td><b>%s</b></td>%s</tr>" % (
        lvl, "".join("<td><b>%d</b></td>" % n for n in want))
    if row not in _arules and bold not in _arules:
        _mix_wrong.append("%s: not printed as %r" % (lvl, want))
check("the deck mix agrees between the model and the rulebook",
      not _mix_wrong, "; ".join(_mix_wrong[:4]))
# THE PIN ON SPECIALIZED CAME OFF on 2026-11-25. This used to read "every
# rung still holds Specialized at 3", which was the printed sentence's
# promise - and that sentence went the same day, as commentary, in eb35114.
# Jon then asked for Volatile at two rungs, which the pin made impossible:
# with S fixed and Routine already 0 by Hard, the only cards a bottom rung
# had left to spend were Unstable ones and Unstable is capped at 8 printed.
# So the shape this holds is the shape that is still TRUE of every rung,
# rather than a count that is now a design choice per rung:
#
#   the deck is ten cards, because aosdeck.py chose ten; and
#   no rung asks for more of a class than the 8 that are PRINTED, which is
#   the one way this table can name a deal nobody can physically make.
#
# A rung's own counts are free, and aosvol.py is what measures them.
_deck_wrong = []
for _l, _mix in _slv.items():
    if sum(_mix) != 10:
        _deck_wrong.append("%s deals %d cards, not 10" % (_l, sum(_mix)))
    for _d, _n in zip(("Routine", "Specialized", "Unstable", "Volatile"),
                      _mix):
        if _n > 8:
            _deck_wrong.append("%s asks for %d %s, and 8 are printed"
                               % (_l, _n, _d))
check("every rung deals ten Programs and no more of a class than is printed",
      not _deck_wrong, "; ".join(_deck_wrong[:4]))
# AND THE MOD CAN STILL DEAL IT. tts/lua.lua builds the Program deck by
# cutting ONE class down and moving the others into it, so the class it
# starts from has to be a real Deck - two cards at least, since a one-card
# "deck" in TTS is a loose card and cutTo(0) is nothing at all. While
# Specialized was pinned at 3 the Lua could name it outright and the
# comment there said so. It now picks the largest count at runtime, which
# only works if SOME class is at 2 or more on every rung - true of any
# ten-card split, but checked rather than assumed, because the sweep's own
# floor at Nobulous was 0/1/5/4 and that mix would have been dealt as a
# single Specialized card.
# VOLATILE IS EXCLUDED, the same way the Lua excludes it: pad(2) is the one
# pad the Corrupted Limitations borrow back at Tier II, and a base deck's
# remainder stays out for the rest of the game. So this reads the first
# three counts only - which matters at Nobulous, where Volatile is 4 and the
# largest count of all, and reading max() over the whole tuple would pass a
# rung the mod cannot deal.
check("...and every rung leaves the mod a class of 2 or more to deal from",
      all(max(_mix[:3]) >= 2 for _mix in _slv.values()),
      "%r" % ({_l: _slv[_l] for _l in _slv},))
# THE TRADE RULE IS NO LONGER DESCRIBED IN PROSE, 2026-11-25: the sentence
# explained what the difficulty table already shows, which is commentary on
# what the mix does rather than a rule. The table is held against
# simulation/aos.py by the check above, so the numbers cannot drift; what is
# gone is only the paragraph about them.

# THE FOURTH COPY.  7f01a88 retuned the mix in three places and said there were
# three; the <option> labels in index.html are a fourth, and they were missed,
# so the lab built 3/3/2 under a label reading "Standard 4/3/1" - a mix that is
# still real, one rung along, which is why it did not look wrong.  Read the
# labels and compare them with the models.  NAP's are checked too: they were
# right, but nothing was holding them either.
_idx = text("playtest/dist/index.html")


def options(select_id):
    """The (value, label) pairs of one <select>, in document order."""
    m = re.search(r'<select id="%s"[^>]*>(.*?)</select>' % select_id,
                  _idx, re.S)
    if not m:
        return []
    return [(v, lab.strip()) for v, lab in
            re.findall(r'<option value="([^"]*)"[^>]*>(.*?)</option>',
                       m.group(1), re.S)]


# AND THE AoS ARM CAME OUT ON 2026-11-25 TOO, a few hours after NAP's and
# for the same reason - see the note directly below, which is the one this
# check should have been retired alongside. It compared the frozen page's
# deckSelect labels with aos.LEVELS, so releasing the pin on Specialized
# failed it with nothing to fix: the lab is frozen, it is not an owner of
# any rule, and AGENTS.md says not to update it when a ladder changes. Two
# lab checks have now outlived the cull by being quiet rather than by being
# live, and both were found by a ladder moving under them.
#
# THE MIX HAS THREE LIVE OWNERS and all three are checked: aos.LEVELS above,
# the printed table in rules/aos.html above that, and AOS_MIX in
# tts/lua.lua further down. The options() helper stays because the NRJ arm
# below still uses it.

# THE NAP DIFFICULTY LABELS IN THE LAB WERE CHECKED HERE UNTIL 2026-11-25,
# against a derived "Easy - 4 Cr, 1 Setback" string. The lab is frozen and is
# no longer an owner of any rule (AGENTS.md), and this check was one of the
# ones the lab-removal pass missed: it reads the frozen page's dropdown,
# which is keyed by the CREDIT GOAL, so moving the goals to 3/4/5/6 the same
# day failed it with nothing to fix. The ladder the mod really deals is
# checked below instead, which is a live owner.

# AND A SEVENTH OWNER, found when the ladder stepped to 4/1, 5/2, 6/3, 7/4 on
# 2026-11-12: the notice the lab prints when you pick a level carried its own
# goal -> name map, hand-typed inside the onchange handler. Nothing compared
# THE SETBACK COUNT IS PRINTED, so three sources carried it: nap.LEVELS, the
# difficulty table in rules/nap.html, and NAP_SETBACK_COUNT in suite.js - and
# NOTHING COMPARED THEM until the 2026-11-06 re-peg had to change all three by
# hand. THE LAB ARM CAME OUT 2026-11-25 with the freeze; the two live owners
# are the model and the book, and the mod's own copy of the ladder is checked
# further down. It is the same gap that let the End-of-Day burn sit unplayed
# in simulation/nap.py for weeks while the other two sources played it, and
# the note below records that one.
_nap_sb = []
_rules_rows = re.findall(
    r"<tr><td>(?:<b>)?(Easy|Standard|Hard|Nobulous)(?:</b>)?</td>"
    r"<td>(?:<b>)?(\d+) Credits(?:</b>)?</td>"
    r"<td>(?:<b>)?(\d+)(?:</b>)?</td></tr>", text("rules/nap.html"))
_rules_sb = dict((int(g), int(s)) for _l, g, s in _rules_rows)
for lvl in ("Easy", "Standard", "Hard", "Nobulous"):
    goal, sb = sn["LEVELS"][lvl]
    if _rules_sb.get(goal) != sb:
        _nap_sb.append("%s: nap.py %d, rules/nap.html %r"
                       % (lvl, sb, _rules_sb.get(goal)))
check("the Setbacks per level agree in nap.py and the rules",
      len(_rules_sb) == 4 and not _nap_sb, "; ".join(_nap_sb[:4]))

# AND THE MOD DEALS THE SAME LADDER, which NOTHING compared until
# 2026-11-25. The Credit goals moved 4/5/6/7 -> 3/4/5/6 that day to pay for
# the Special Recovery age rule, and the mod carries the ladder TWICE -
# NAP_DIFF, which is what it really deals, and the line the NAP quick
# reference prints. Both are derived from nap.LEVELS here, so neither can
# drift from the model again; the lab used to be the third copy and is
# frozen out of this check deliberately.
_want_diff = ("NAP_DIFF = { Easy = {%d, %d}, Standard = {%d, %d}, "
              "Hard = {%d, %d}, Nobulous = {%d, %d} }"
              % tuple(n for lvl in ("Easy", "Standard", "Hard", "Nobulous")
                      for n in sn["LEVELS"][lvl]))
_want_ref = ("  " + "   ".join(
    "%s %d and %d" % ((lvl,) + tuple(sn["LEVELS"][lvl]))
    for lvl in ("Easy", "Standard", "Hard", "Nobulous")))
check("the mod deals the ladder nap.LEVELS plays",
      _want_diff in text("tts/lua.lua"), _want_diff)
check("the mod's NAP quick reference prints that same ladder",
      _want_ref in text("tts/build_mod.py"), _want_ref)
# And the setup step restates the four counts in prose, so it drifts too.
check("rules/nap.html's setup step restates the same four counts",
      "%d, %d, %d or %d of the 6" % tuple(
          sn["LEVELS"][k][1]
          for k in ("Easy", "Standard", "Hard", "Nobulous"))
      in text("rules/nap.html"))

# THE TIER I SETBACK SWAP, and the count it must not change.
#
# Four owners carry it - the Following Setback footer in build_nrj.py, the
# Tier I row in rules/nrj.html, nap.FOLLOWING_REPLACE_ALL, and the Tier I
# branch of buildNAPDeck in the lab - and three of them had the number 3
# hard-coded until 2026-11-07, sweeping the base Setbacks out entirely for
# exactly 3 Following cards. That matched the model only while every
# difficulty played 3 Setbacks. After the re-peg gave Hard 4 and Nobulous 5,
# TURNING TIER I ON HANDED A SETBACK BACK and the tier measured EASIER than
# no module at all on both rungs - Tier I 40.1% against a solo 38.6% at Hard.
# The checks below are about the swap being one for one, which is the
# property that was violated; the counts themselves are checked above.
# AND THE PER-RUNG SPLIT IN PROSE, which nothing read until 2026-11-12. The
# supplement names what each difficulty ends up with, and the retune to
# 0/1/2/4 Setbacks made all four of those numbers wrong at once - Easy,
# Standard and Hard now have nothing to give back, so Tier I RAISES their
# count to 3 instead of swapping. Derived from nap.LEVELS, so the sentence
# cannot drift from the table again.
_t1 = ", ".join(
    ("%s 3 Following and %d base" % (lvl, max(0, sn["LEVELS"][lvl][1] - 3)))
    if lvl == "Easy" else
    ("%s 3 and %d" % (lvl, max(0, sn["LEVELS"][lvl][1] - 3)))
    for lvl in ("Easy", "Standard", "Hard", "Nobulous"))
check("rules/nrj.html names the Tier I split each rung really gets",
      _t1 in " ".join(text("rules/nrj.html").split()), _t1)
# The printed card may no longer promise a 3-for-3 swap either: at three of
# the four rungs there are not 3 base Setbacks to replace.
check("the Following Setback footer does not promise 3 for 3",
      "replace 3 of your" not in text("generator/build_nrj.py")
      and "one base Setback leaves for each" in text("generator/build_nrj.py"))

check("nap.py swaps Setbacks one for one at Tier I, not all for 3",
      sn["FOLLOWING_REPLACE_ALL"] is False,
      "FOLLOWING_REPLACE_ALL = %r sets EVERY base Setback aside, which makes "
      "Hard and Nobulous EASIER at Tier I" % (sn["FOLLOWING_REPLACE_ALL"],))
# The lab has no table to read here, so this reads the one expression that
# carries the rule: the leftover base Setbacks concatenated onto the three
# Following ones. Without the concat the Tier I deck holds 3 Setbacks at
# every difficulty, which is the inversion.
_tier1 = re.search(r"const sb=\(tier===\"1\".*?: setbacks;",
                   text("playtest/dist/suite.js"), re.S)
# And no owner may still PRINT the old sweep. "Never use both kinds together"
# was the printed rule and is exactly what the fix repeals, so the phrase
# surviving in the book is the inversion coming back in words; the card
# footer carried its own copy.
#
# EACH PHRASE IS LOOKED FOR WHERE IT WOULD BE PRINTED, not anywhere in the
# file. A first cut of this searched build_nrj.py whole and failed on the
# comment above FOLLOWING that QUOTES the old footer to explain the fix -
# a check that punishes you for recording what changed is a worse check than
# none.
_fol = re.search(r"\nfol = \[C\(.*?for n, d, t, e in FOLLOWING\]",
                 text("generator/build_nrj.py"), re.S)
_sweep = []
if "Never use both kinds together" in text("rules/nrj.html"):
    _sweep.append("rules/nrj.html still prints it")
if not _fol:
    _sweep.append("the Following Setback card block was not found")
elif "replace the 3 base Setbacks" in _fol.group(0):
    _sweep.append("the Following Setback footer still prints it")
check("no owner still states the all-for-3 sweep it replaced",
      not _sweep, "; ".join(_sweep))

# ---------------------------------------------------------------------------
# THE NUMBERS THE RULEBOOKS PRINT, against the thing that owns each one.
#
# Added 2026-11-06. Until then the rules were the one source here with no
# number check at all: the block above asks whether a rulebook still CONTAINS
# a phrase, which catches a deletion and not a wrong figure. A read of all
# four books against their sources that day turned up a rulebook
# contradicting ITSELF on required-colour dots, and two printed claim costs
# that no model was charging - so a figure in a rulebook is exactly as likely
# to drift as a figure anywhere else in this repo.
#
# Each check pulls the number OUT of the rulebook with a pattern and holds it
# against the generator or the model. Rewording near the number is fine; the
# number moving is not.
# ---------------------------------------------------------------------------
def _plain(rel):
    """A rulebook with its markup taken off.

    These checks are about what the book PRINTS, so they read it the way a
    player does: tags gone, entities resolved, whitespace flattened. Matching
    the raw HTML instead makes a check fail the moment a number is wrapped in
    <b>, which is a formatting change and not an error.
    """
    t = text(rel)
    t = re.sub(r"<[^>]+>", "", t)
    for a, b in (("&#8209;", "-"), ("&mdash;", " - "), ("&ndash;", "-"),
                 ("&rsquo;", "'"), ("&lsquo;", "'"), ("&ldquo;", '"'),
                 ("&rdquo;", '"'), ("&middot;", "-"), ("&nbsp;", " "),
                 ("&amp;", "&")):
        t = t.replace(a, b)
    return re.sub(r"\s+", " ", t)


_RULES = dict((g, _plain("rules/%s.html" % g))
              for g in ("bat", "nap", "aos", "nrj"))


def _num(game, pattern, label):
    """The integer a rulebook prints at `pattern`, or None if it is gone."""
    m = re.search(pattern, _RULES[game])
    if not m:
        _rulenum_missing.append("%s: %s" % (game, label))
        return None
    return int(m.group(1))


def rulenum(game, pattern, want, label):
    got = _num(game, pattern, label)
    check("rules/%s.html: %s" % (game, label),
          got == want, "rulebook %r, source %r" % (got, want))


_rulenum_missing = []

# -- BAT ---------------------------------------------------------------------
# BAT'S MODEL OF RECORD IS batrev.py as of 2026-11-20, when rules/bat.html
# adopted the scavenged-Tyrant design. simulation/bat.py models the printed
# game that preceded it and is retired: its card tables are still the
# transcription every other table here is held against, and nothing else in
# it describes BAT. Both are loaded, and the retirement is checked below so
# that bat.py cannot quietly become the model of record again.
_bat = py_tables("simulation/bat.py")        # retired, card tables only
_brev = py_tables("simulation/batrev.py")    # the model of record
_satr = text("simulation/batrev.py")
_gbat = py_tables("generator/build_bat.py")
check("simulation/bat.py says it is retired, and batrev.py says it is not",
      "RETIRED: the PRINTED Build-a-Tyrant" in text("simulation/bat.py")
      and "BAT'S MODEL OF RECORD IS simulation/batrev.py"
          in text("simulation/bat.py")
      and "BAT'S MODEL OF RECORD" in text("simulation/batrev.py")
      and "retired" in text("simulation/batrev.py"),
      "one of the two modules stopped saying which one the game is")
rulenum("bat", r"(\d+) Experiment cards", len(_gbat["EXPERIMENTS"]),
        "the Experiment deck size")
# THE TABLE IS STILL CALLED UPGRADES IN build_bat.py, and the book
# calls what it prints Splices: the generator's variable is a name in
# a file and the book's is the word on the card. 2026-11-23.
rulenum("bat", r"(\d+) Splice cards", len(_gbat["UPGRADES"]),
        "the Splice deck size")
rulenum("bat", r"(\d+) Specimen cards", len(_gbat["SPECIMENS"]),
        "the Specimen count")
rulenum("bat", r"(\d+) Tyrant Attack cards", len(_gbat["ATTACKS"]),
        "the Tyrant Attack count")
# THE ROUNDS ARE THE LADDER NOW, so the book prints four of them and the
# setup table is where they live. Read out of the plain text of that table
# rather than matched as a phrase, and compared against batrev's own dict,
# so renaming a rung or reordering the columns fails here.
# THE SETUP TABLE HAS NO WHITESPACE BETWEEN CELLS, so _plain collapses
# "Easy 5 12" into "Easy512" and no digit regex can split it. Read the
# ROWS out of the markup instead, which also fails if a column is
# reordered or a rung renamed.
_rows = re.findall(r"<tr><td>(?:<b>)?(Easy|Standard|Hard|Nobulous)"
                   r"(?:</b>)?</td><td>(\d+)</td><td>(\d+)</td></tr>",
                   text("rules/bat.html"))
_book_rounds = [(a, int(b), int(c)) for a, b, c in _rows]
_want_rounds = [(k, _brev["SPECIMENS_IN_POOL"][k], _brev["ROUND_LIMITS"][k])
                for k in ("Easy", "Standard", "Hard", "Nobulous")]
check("rules/bat.html prints batrev's Specimens and rounds per rung",
      _book_rounds == _want_rounds,
      "book %r, source %r" % (_book_rounds, _want_rounds))
# AND THE WORD 'PART' IS NOT A GAME TERM ANY MORE, 2026-11-23. A card in
# the carcass is a SPLICE and it is a GRAFT once the Prototyrant takes
# it; both words were already in the book, and what went was the generic
# one sitting in front of them.
#
# A COUNT, NOT A SPELLING. The book still says 'Red is not part of the
# pool', which is ordinary English, so this cannot ask for the string to
# be absent - it asks that the five places that NAMED the thing name a
# Splice, and that the section heading is not Parts any more.
#
# ANCHORED ON THE NAME, NOT THE SENTENCE AROUND IT (2026-11-24). Three of
# the five phrases this used to match died in one editing pass that renamed
# nothing: the reveal step now says 'from the Carcass deck', the Target line
# was rewritten as 'Splice A value + Splice B value - Experiment value', and
# the box says 'Thirteen Splices on the carcass'. All three still called the
# card a Splice, so the check failed on prose while the rule it guards held -
# exactly what its own 'A COUNT, NOT A SPELLING' note above warns against.
# Each anchor is now the NAME plus the one word that places it, and the count
# carries the rest of the book (49 at the time of writing).
check("rules/bat.html calls a card out of the carcass a Splice",
      "2 Splices from the" in _RULES["bat"]          # revealing a pair
      and "Splice A value" in _RULES["bat"]          # working out the Target
      and "Splices leave the deck" in _RULES["bat"]  # resolving the Experiment
      and "Thirteen Splices" in _RULES["bat"]        # the conservation box
      and _RULES["bat"].count("Splice") >= 30        # ...and everywhere else
      and "<h2>Splices</h2>" in text("rules/bat.html")
      and "<h2>Parts</h2>" not in text("rules/bat.html"),
      "the book half-renamed the thing both halves of the table hold")
# ...AND THE FELT SAYS THE SAME, because the overlay is the only rules
# text some tables ever read, and it is the one Jon renamed first.
_tmpl_bat = text("tts/make_template.py")
check("...and so does the overlay",
      '"REVEALED\\nSPLICES"' in _tmpl_bat
      and '"RECLAIMED\\nSPLICE"' in _tmpl_bat
      and '"REVEALED\\nPARTS"' not in _tmpl_bat
      and '"TYRANT\\nRECLAIMED"' not in _tmpl_bat,
      "the felt and the book disagree about what a card is called")
# ...AND THE HEALTH LABEL CLEARS THE DISC IT NAMES. It was two lines
# 2.1 below the dial's centre until 2026-11-23 and the token sat over
# the first of them - a thing no harness here could see, because the
# overlay is a picture and nothing measures a picture.
#
# SO THE DRAWING MEASURES ITSELF. make_template.py works the position
# out from the ring and the top of the exhausted corner and then
# ASSERTS the gap both ways, against the text's own measured height -
# so putting the label back under the dial fails the build that draws
# it. What this check does is stop that assertion being deleted, which
# is the only way the property can be lost quietly.
check("...and the overlay proves its Health label clears the dial",
      "hp_half = glyphs.text_size(hp_txt, LABEL_PT, FONT)" in _tmpl_bat
      and "assert hp_z + hp_half < float(g.BAT_CHIP_Z) - CHIP_R"
      in _tmpl_bat
      and "assert hp_z - hp_half > EXHAUSTED[2]" in _tmpl_bat
      # ...AND ONE RADIUS SERVES THE RING AND THE CLEARANCE, so a ring
      # drawn at one size cannot be measured at another. That is what
      # the last clause is for: no circle may carry a literal again.
      and "CHIP_R = 1.1" in _tmpl_bat
      and "circle(d, float(g.BAT_CHIP_X), float(g.BAT_CHIP_Z), CHIP_R)"
      in _tmpl_bat
      and not re.search(r"circle\(d, [^)]*, 1\.1\)", _tmpl_bat),
      "the label can go back under the disc without failing a build")

# AND THE PARTS DECK IS ONE NUMBER ON EVERY RUNG. It was 12/13/14/15 for a
# day; a deck card is a whole Splice, which is a whole attack out of ten
# rounds, so the rungs could not be spaced with it.
_parts = set(_brev["PARTS_AT_SETUP"].values())
rulenum("bat", r"deal (\d+) at random", sorted(_parts)[0],
        "the old Tyrant's Splice deck")
check("...and that deck is the same size on every rung",
      len(_parts) == 1, "%r" % (_brev["PARTS_AT_SETUP"],))
# THERE IS NO GRAFT LIMIT, and the book has to say so: a Rat held at most 3
# Upgrades in the printed game, and the Prototyrant holds everything it is
# given. The borrow table below is the only thing a graft count still gates.
check("rules/bat.html: no limit on grafts, and batrev has no cap for one",
      "There is no limit on grafts" in _RULES["bat"]
      # NO_GRAFT_CAP is the dice cap for a round with no graft revealed,
      # which is a printed rule. What must not exist is a cap on how MANY
      # grafts the Prototyrant may hold.
      and not [k for k in _brev
               if k in ("UPGRADE_CAP", "GRAFT_LIMIT", "MAX_GRAFTS")],
      "%r" % ([k for k in _brev if "CAP" in k or "LIMIT" in k],))
# AND THE CLOCK IS THE EXPERIMENT DECK, not a Splice count. Eight dealt and
# a three-card packet holding the Wake-Up gives six, seven or eight.
rulenum("bat", r"shuffle the 20 Experiments and deal (\d+)",
        _brev["EXPERIMENTS_DEALT"], "the Experiments dealt")
check("rules/bat.html prints the Wake-Up window batrev deals",
      "six, seven or eight" in _RULES["bat"]
      and _brev["WAKEUP_PACKET"] == 3
      and _brev["EXPERIMENTS_DEALT"] == 8,
      "dealt %r, packet %r" % (_brev.get("EXPERIMENTS_DEALT"),
                               _brev.get("WAKEUP_PACKET")))

# The commit-colour dot is the card; the model reads its own copy of the
# order. Nothing compared them until 2026-11-06.
_dots = {"G": "green", "B": "blue", "Y": "yellow"}
check("the Tyrant Attack dots agree in build_bat.py and bat.py",
      [_dots[d] for d in _gbat["ATTACK_DOTS"]] == _bat["ATTACK_COLORS"],
      "%r vs %r" % (_gbat["ATTACK_DOTS"], _bat["ATTACK_COLORS"]))
_want = {"green": 3, "yellow": 3, "blue": 1}
_got = dict((c, _bat["ATTACK_COLORS"].count(c))
            for c in set(_bat["ATTACK_COLORS"]))
check("rules/bat.html: 3 Green, 3 Yellow and 1 Blue Attack dots",
      _got == _want and "3 Green, 3 Yellow and 1 Blue" in _RULES["bat"],
      "%r" % (_got,))

# "Take 2 Purple, 2 Blue, 1 Green and 1 Yellow out of the Rats' personal dice"
check("rules/bat.html: the Tyrant's six dice match bat.TYRANT_NEED",
      "2 Purple, 2 Blue, 1 Green and 1 Yellow" in _RULES["bat"]
      and [list(x) for x in _bat["TYRANT_NEED"]]
      == [["purple", 2], ["blue", 2], ["green", 1], ["yellow", 1]],
      "%r" % (_bat["TYRANT_NEED"],))

# -- NAP ---------------------------------------------------------------------
_nap, _gnap = sn, gn
rulenum("nap", r"with the (\d+) Tasks", len(_gnap["TASKS"]), "the Task count")
rulenum("nap", r"the (\d+) Final Exams\b", len(_gnap["EXAMS"]),
        "the Final Exam count")
rulenum("nap", r"maximum of (\d+) Assignments", _nap["ROW_MAX"],
        "the row limit")
rulenum("nap", r"draw (\d+) Final Exams", 3, "how many exams are sat")

# -- AoS ---------------------------------------------------------------------
_aos = sa
rulenum("aos", r"(\d+) Limitation cards", len(_aos["LIMITATIONS"]),
        "the Limitation deck size")
rulenum("aos", r"(\d+) Element allocation mats", 5, "the element mats")
rulenum("aos", r"never above (\d+)", 6, "the Health cap")
rulenum("aos", r"Optimal Implementation: recover (\d+) exhausted dice",
        _aos["OPTIMAL_BONUS"], "what Optimal Implementation recovers")
rulenum("aos", r"exhaust (\d+) misses on failed elements",
        _aos["MISSES_TO_NEGATE"], "the misses that negate a Catastrophe")
rulenum("aos", r"at most Target \+ (\d+) dice", 1, "the allocation cap")

# THE REQUIRED-COLOUR DOT COUNTS, per deck, which is where rules/aos.html was
# caught contradicting itself: the dot-count paragraph names the three
# exceptions and the Advanced Programming section then said "each carries 2",
# while two of the eight carry three.
_byDeck = dict((d, [sum(1 for x in r if x) for r in rows])
               for d, rows in _aos["PROGRAM_REQS"].items())
check("rules/aos.html: Routine and Unstable carry one dot each",
      set(_byDeck["Routine"]) == {1} and set(_byDeck["Unstable"]) == {1},
      "%r %r" % (_byDeck["Routine"], _byDeck["Unstable"]))
# THE BOOK NO LONGER NAMES IT, 2026-11-25, so only the deck is checked:
# seven Specialized Programs carry two dots and exactly one carries four.
# That is the fact the dropped sentence was reporting, and it is the half
# that can actually break.
check("generator/aos.py: one Specialized Program carries four colours",
      sorted(_byDeck["Specialized"]) == [2, 2, 2, 2, 2, 2, 2, 4],
      "%r" % (_byDeck["Specialized"],))
# AND THE ASSEMBLY BACKS, which took the Advanced Programs' place: every
# element of one carries a colour, so the count is the element count and
# the old "each carries 2, except these two" question does not arise. What
# can still go wrong is a back whose dots stop matching its own elements.
# THE DOTS THEMSELVES ARE CHECKED IN THE ASSEMBLY BLOCK ABOVE, against
# generator/aos.py, because the model and the lab both DERIVE them from
# the Assemblies rather than transcribing them - there is no third copy
# here to hold against a second. What is worth checking at this end is
# that the book tells a player the rule at all: a finale element always
# asks a colour, where a Program element usually does not, and a player
# who does not know that plans the wrong dice.
check("rules/aos.html tells a player every finale element asks a colour",
      "every element carries a required color" in _RULES["aos"].lower(),
      "the book never says the finale asks a colour per element")

# -- NRJ and the finale ------------------------------------------------------
_fin = py_tables("simulation/finale.py")
rulenum("nrj", r"Play (\d+) sessions", _fin["SESSIONS"], "the session count")
rulenum("nrj", r"claim at most (\d+) per game", _aos["BACKDOOR_CLAIMS"],
        "the Backdoor claim cap")
rulenum("nrj", r"takes (\d+) off the Target of one Exhibit",
        _fin["CARD_VALUE"], "what a retained card is worth")
check("rules/nrj.html: the Imposter's 5 HP / 2 STR / 3 REC",
      "5 HP / 2 STR / 3 REC" in _RULES["nrj"]
      and (_fin["HEALTH"], _fin["STRAT"], _fin["REC_BASE"]) == (5, 2, 3),
      "%r" % ((_fin["HEALTH"], _fin["STRAT"], _fin["REC_BASE"]),))
check("rules/nrj.html: 5 Knowledge, 5 Physical and 5 Cover-Up Exhibits",
      "5 Knowledge, 5 Physical and 5 Cover-Up" in _RULES["nrj"]
      and _fin["DEAL"] == 5, _fin["DEAL"])

# THE TWO PRINTED CLAIM COSTS. Both rulebooks print them and NEITHER MODEL
# CHARGED THEM until 2026-11-06, so both Tier III columns were measured with
# free cards. These two checks are the reason that cannot happen quietly
# again: the rulebook says the price and the model has to be charging it.
# BAT'S PRICE IS RE-EXPRESSED, because the printed wording charges twice in
# this structure: the part the Prototyrant forfeits is a part the old Tyrant
# reclaims, so a graft is lost AND a Splice joins the wall. Measured at 30
# points of great-lab win rate against the 6 nrj.html advertises. The book
# charges the PICK instead, and batrev has to be charging the same thing.
check("rules/bat.html prints the Research Note claim cost, and batrev.py "
      "charges it",
      "Claiming one costs you the choice" in _RULES["bat"]
      and "the old Tyrant picks the Splice it reclaims" in _RULES["bat"]
      and _brev["NOTE_PRICE"] == "choice",
      "NOTE_PRICE=%r" % (_brev.get("NOTE_PRICE"),))
check("rules/aos.html prints the Backdoor Routine claim cost, and aos.py "
      "charges it",
      "costs the next Program Reward" in _RULES["aos"]
      and _aos["BACKDOOR_COSTS_REWARD"] is True,
      "BACKDOOR_COSTS_REWARD=%r" % (_aos.get("BACKDOOR_COSTS_REWARD"),))
# THE SUPPLEMENT'S COPY OF THIS WENT WITH THE "Tier III is a loan" BOX on
# 2026-11-25. Both costs are still printed where they are charged - in
# rules/bat.html and rules/aos.html - and the two checks directly above hold
# each of those against the model that charges it, which is the pairing that
# matters. The supplement was a third copy of the same two facts.
check("rules/nrj.html states the claim costs where it claims",
      "giving up the next Upgrade" in _RULES["nrj"]
      and "or the next Program Reward" in _RULES["nrj"])

# AND THE CONDITION THE COST BUYS HAS TO BE ONE THE GAME CAN MEET.
# Diagnostic Port printed "no element over-allocated" while rules/aos.html
# caps an element at Target + 1 and the best allocation fills every element
# to that cap, so the condition was met in 0.2% of games and was a strict
# subset of Resource Fork besides. The card asks for 2 such elements as of
# 2026-11-08; DIAG_RESTRAINT = None is the old reading. The rate itself is
# measured by simulation/audit.py, which now prints how often each of the
# six CONDITIONS is met and flags any under 5%.
check("the Diagnostic Port card and aos.py ask for the same restraint",
      _aos["DIAG_RESTRAINT"] == 2
      and "at least two elements holding no more than their Target in dice"
          in dict((n, t) for n, t, _r
                  in py_tables("generator/build_nrj.py")["BACKDOOR"]
                  )["Diagnostic Port"],
      "DIAG_RESTRAINT=%r" % (_aos.get("DIAG_RESTRAINT"),))

# A CORRUPTED LIMITATION IS A CARD IN THE LIMITATION DECK and withholds dice
# on top of its printed corruption - both halves, which the model had wrong
# in both directions on 2026-11-06 before this check existed.
check("rules/nrj.html: Corrupted Limitations go INTO the Limitation deck",
      "Corrupted Limitations into the Limitation deck" in _RULES["nrj"]
      and _aos["CORRUPT_MODE"] == "cards", _aos.get("CORRUPT_MODE"))
check("rules/nrj.html: and withhold dice on top of their corruption",
      "on top of their printed corruption" in _RULES["nrj"]
      and _aos["CORRUPT_WITHHOLD"] == 2, _aos.get("CORRUPT_WITHHOLD"))

check("every rulebook number this block looks for is still there",
      not _rulenum_missing, "; ".join(_rulenum_missing[:4]))

# END OF DAY IS PRINTED, SO ALL THREE SOURCES MUST PLAY IT. rules/nap.html:
# "Reveal and discard the top card of the Assignment deck." The lab burned a
# card from the day it shipped and simulation/nap.py never did, so every
# published NAP figure measured a game missing a printed rule until
# 2026-11-05. Nothing compared the three, which is why it sat.
_nap_rules = text("rules/nap.html")
check("rules/nap.html still prints the End-of-Day burn",
      "top card of the Assignment deck" in _nap_rules)
check("simulation/nap.py plays the printed End-of-Day burn",
      sn.get("END_OF_DAY_BURN") is True,
      "END_OF_DAY_BURN = %r" % (sn.get("END_OF_DAY_BURN"),))

# THE 2026-11-11 REVISION, SENTENCE BY DIAL. Five rules in rules/nap.html
# changed that day and simulation/nap.py implemented all five the old way -
# which is how NAP's published ladder came to describe a game the book no
# longer does. Each check reads the VALUE out of nap.py rather than matching
# a name, so flipping a dial back without touching the page fails here.
#
# The rulebook side is matched against the page with its whitespace
# collapsed: these sentences wrap, and a rewrap is not a rules change. That
# lesson is already paid for twice over - "Separate"/"Set aside the 12 Final
# Exams" and "a row"/"one row" both failed checks that nothing had broken.
_napflat = " ".join(_nap_rules.split())


def _says(phrase):
    return " ".join(phrase.split()) in _napflat


check("Assignments stay in their Time Slot, in the book and the model",
      _says("they do not follow you into the next Time Slot")
      and sn.get("SLOT_ROWS") is True,
      "SLOT_ROWS = %r" % (sn.get("SLOT_ROWS"),))
check("a Demand-side Assignment bills once and is discarded",
      _says("<b>inflicts its printed Demand penalty</b> and is then discarded")
      and sn.get("DEMAND_ONCE") is True,
      "DEMAND_ONCE = %r" % (sn.get("DEMAND_ONCE"),))
check("REC recovers at End of Day and nowhere else",
      _says("REC only occurs at the end of the day")
      and _says("Then recover exhausted dice equal to your <b>REC</b>")
      and sn.get("REC_AT_END_OF_DAY") is True,
      "REC_AT_END_OF_DAY = %r" % (sn.get("REC_AT_END_OF_DAY"),))
# THE SPECIAL RECOVERY AGE RULE, 2026-11-25. The complaint it answers is
# Jon's: "I know I will get back all purple at the end of afternoon. Let me
# roll them all now." The Primary's dot used to name the NEXT slot's
# recovery colour, so a queued colour was one you may as well spend to the
# floor - the dice stopped being a cost and became a loan already granted.
#
# IT IS PRINTED AS A SEQUENCING CHANGE and that is the thing to hold
# together: the recovery is now the LAST step of the slot, before the dice
# you used in it are exhausted, so those dice are still in front of you and
# out of its reach. There is no second pile and no marker. The old step 1
# and its "Do not recover again" warning are both gone, and a book that
# still carried either would be describing the exploitable game - so this
# checks for their ABSENCE as well as for the new wording.
check("the Special Recovery is the last step of the slot, not the first",
      sn.get("SPECIAL_RECOVERY_AGE") is True
      and _says("Perform <b>Special Recovery</b> for the color on the dial,"
                " and <b>only then</b> exhaust the")
      and _says("non&#8209;stored dice you committed this Time Slot")
      and "Do not recover again" not in _napflat
      and "nothing queued, so there is none" not in _napflat,
      "SPECIAL_RECOVERY_AGE = %r" % (sn.get("SPECIAL_RECOVERY_AGE"),))
check("the book says what the age rule costs you, in the recovery box",
      _says("so the dice you have just spent are still in front of you,"
            " are not in the exhausted pool, and are not recovered"),
      "the Special Recovery box no longer explains the age rule")
check("the mod's quick reference puts the recovery last too",
      "4 SPECIAL RECOVERY LAST" in text("tts/build_mod.py")
      and "WHAT YOU SPEND IN A SLOT, YOU SPEND" in text("tts/build_mod.py")
      and "Do NOT recover again" not in text("tts/build_mod.py"),
      "tts/build_mod.py still prints the pre-2026-11-25 slot order")
check("two Setbacks revealed: the higher Target is the one you take",
      _says("If two Setbacks are revealed, take the one with the higher"
            " Target")
      and sn.get("SETBACK_PICK_HIGHER") is True,
      "SETBACK_PICK_HIGHER = %r" % (sn.get("SETBACK_PICK_HIGHER"),))

# AND TWO THAT ARE NOT NEW, just never played. Both were printed long before
# the revision and both lived in the same silent `return` in draw_into_row.
check("a blocked Skull rotates its own Assignment, as the box says",
      _says("instead rotate the Skull&#8209;generating Assignment to its"
            " Demand side once")
      and sn.get("SKULL_BLOCKED_DEMAND") is True,
      "SKULL_BLOCKED_DEMAND = %r" % (sn.get("SKULL_BLOCKED_DEMAND"),))
check("the Slacker's row holds the 3 the card prints",
      "maximum of 3 Assignments instead of 4" in text("generator/build_nap.py")
      and sn.get("SMALL_ROW_CAPS_ADDS") is True
      and "self.row_cap()" in text("simulation/nap.py"),
      "SMALL_ROW_CAPS_ADDS = %r" % (sn.get("SMALL_ROW_CAPS_ADDS"),))

# NAP'S NAME, ONE SPELLING. rules/nap.html is the authority and its <h1>
# reads "Nobulous Apprenticeship Program (NAP)". Until 2026-11-05 the set
# printed it three ways: "Nobulous' Apprentice Program" in build_catalog.py
# - so in catalog.json, which the lab reads and DISPLAYS - and twice in
# index.html, plus "Nobulous' Apprenticeship Program" in nap.py and
# table.py. Nothing compared them, so all three looked deliberate.
_NAP_NAME = "Nobulous Apprenticeship Program"
_nap_h1 = re.search(r"<h1>(.*?)</h1>", text("rules/nap.html"), re.S)
_nap_h1 = " ".join(re.sub(r"<[^>]+>", " ", _nap_h1.group(1)).split()) if _nap_h1 else ""
check("rules/nap.html still prints the canonical NAP name",
      _NAP_NAME in _nap_h1, _nap_h1[:60])
_nap_strays = []
for _rel in ("generator/build_catalog.py", "playtest/dist/index.html",
             "playtest/dist/catalog.json", "simulation/nap.py",
             "simulation/table.py", "README.md", "rules/nrj.html",
             "rules/make_editable.py"):
    _t = text(_rel)
    for _wrong in ("Nobulous' Apprentice Program",
                   "Nobulous' Apprenticeship Program",
                   "Nobulous Apprentice Program"):
        if _wrong in _t:
            _nap_strays.append("%s has %r" % (_rel, _wrong))
check("NAP's name is spelled one way across every source",
      not _nap_strays, "; ".join(_nap_strays[:3]))

# NO ORPHAN ASSETS. AoS_Full_Rules.pdf lived in playtest/dist/assets from
# 17 September to 2026-11-05 with nothing linking it. The lab served it at
# HTTP 200, it contradicted the shipping rulebook on seven points - it still
# printed "An element may receive no dice and will then fail", the sentence
# the allocation floor replaced - and deploy.py's ASSET_KEEP protected it
# from --prune BY NAME, so no promotion could ever clear it. Anyone who
# found it got the old game. This fires on the next one.
_assets_dir = os.path.join(ROOT, "playtest", "dist", "assets")
_asset_pdfs = sorted(f for f in os.listdir(_assets_dir) if f.endswith(".pdf"))
_orphan_pdfs = [f for f in _asset_pdfs if f not in _idx]

# THE TRANSCRIPTS MUST NAME THE CURRENT LADDER. RESULTS.txt and
# simulation/README.md each carry a hand-maintained copy of the AoS grid, and
# on 2026-11-05 both were TWO generations stale - indexed by a ladder that had
# moved twice, with figures from before required colours. The figures cannot
# be checked here, since they need a 20,000-game run, but the row LABELS can,
# and a row labelled with a mix the model no longer has is the tell that the
# numbers beside it are stale too.
_aos_mixes = ["/".join(str(n) for n in sa["LEVELS"][k])
              for k in ("Easy", "Standard", "Hard", "Nobulous")]
for _rel in ("simulation/RESULTS.txt", "simulation/README.md"):
    _missing = [m for m in _aos_mixes if m not in text(_rel)]
    check("%s names the current AoS ladder" % _rel,
          not _missing, "does not mention %s" % ", ".join(_missing))

# THE SIX TECHNICIAN ABILITIES ARE WRITTEN TWICE: in generator/build_aos.py,
# which prints them on the cards, and in playtest/dist/app.js, which shows
# them to the playtester. Nothing compared them until 2026-11-05, so a card
# whose text changed could have gone to print while the lab taught the old
# ability - the same shape of bug as the difficulty labels. The lab joins the
# ability name to its text with an em dash; that is the only difference
# allowed.
_gen_techs = py_tables("generator/build_aos.py").get("TECHS") or []
_lab_techs = js_literal("playtest/dist/app.js", "TECHS")
_tech_bad = []
if len(_gen_techs) != len(_lab_techs):
    _tech_bad.append("%d on the cards, %d in the lab"
                     % (len(_gen_techs), len(_lab_techs)))
else:
    for _g, _lab in zip(_gen_techs, _lab_techs):
        _name, _ability, _txt = _g
        if _lab.get("name") != _name:
            _tech_bad.append("order: %s vs %s" % (_name, _lab.get("name")))
        elif _lab.get("ability") != u"%s — %s" % (_ability, _txt):
            _tech_bad.append(_name)
check("the lab prints the Technician abilities the cards print",
      _gen_techs and not _tech_bad, "; ".join(_tech_bad[:3]))

# TWO CADENCES, printed and implemented, and they are NOT the same one.
# Optimize went to "once per cycle and once in Advanced Programming" on
# 2026-11-05; Debug was tried on that same clause the same day and then
# replaced outright, because metering was never the fix - a reroll only
# pays when you are short by exactly 1, so its value climbed with the
# difficulty and flattened the ladder. Debug is now a pre-roll swap and is
# back to once per Program. The lab has to agree in CODE as well as in
# card text, and the two cards want OPPOSITE answers at all three reset
# sites, so each is checked on its own.
# RENAMED WITH THE PHASE IT NAMED, 2026-11-24: a cycle is a round now and
# Advanced Programming is the finale, so the card could not keep pointing
# at either. The cadence itself - once per pass through the deck, and once
# more at the end - is unchanged, which is why this is still one string
# checked at every site rather than a new rule.
CADENCE = "Once per round and once in the finale"
_tech_txt = {_g[0]: _g[2] for _g in _gen_techs}
check("the Optimizer card is the per-cycle wording",
      CADENCE in _tech_txt.get("Optimizer", ""),
      _tech_txt.get("Optimizer", "")[:60])
check("the Debugger card is the pre-roll swap, not a reroll",
      "swap 1 of its dice" in _tech_txt.get("Debugger", "")
      and "reroll" not in _tech_txt.get("Debugger", "").lower(),
      _tech_txt.get("Debugger", "")[:60])
_app = text("playtest/dist/app.js")


def _body(fn):
    """The source of one top-level function in app.js, brace-matched."""
    m = re.search(r"function %s\(" % re.escape(fn), _app)
    if not m:
        return ""
    i = _app.index("{", m.end() - 1)
    depth, j = 0, i
    while j < len(_app):
        if _app[j] == "{":
            depth += 1
        elif _app[j] == "}":
            depth -= 1
            if depth == 0:
                return _app[i:j + 1]
        j += 1
    return ""


_draw, _adv = _body("drawProgram"), _body("beginAdvanced")
_cycle_turn = re.search(r"state\.cycle \+= 1;[^\n]*", _draw)
# One regex, reused: the cycle-turn line is where Optimize comes back.
_draw_np = _draw.replace(_cycle_turn.group(0), "") if _cycle_turn else _draw
check("the lab does not refresh Optimize every Program",
      _draw and "state.optimizerUsed = false" not in _draw_np,
      "drawProgram() still clears it per Program")
check("the lab refreshes Optimize when a cycle turns over",
      _cycle_turn and "state.optimizerUsed = false" in _cycle_turn.group(0))
check("the lab refreshes Optimize for Advanced Programming",
      _adv and "state.optimizerUsed = false" in _adv)
check("the lab refreshes Debug every Program",
      _draw and "state.debuggerUsed = false" in _draw_np,
      "drawProgram() does not clear it")
check("the lab does not hand Debug back at a cycle turn",
      _cycle_turn and "state.debuggerUsed = false" not in _cycle_turn.group(0))
check("the lab does not hand Debug back in Advanced Programming",
      _adv and "state.debuggerUsed = false" not in _adv)
# ...and the reroll route has to be gone, not merely unused: a disabled
# button and a live handler is how a replaced ability comes back.

# EVERY LAB ASSET MUST CARRY THE CACHE TOKEN, on ONE token. AGENTS.md: a
# cached index.html "pins you to an old build however often you bump them",
# and the symptom "reads exactly like code that was never written".
# bat_experiments.js carried none until 2026-11-04 and nothing noticed.
_assets = re.findall(r'(?:src|href)="([^"]+\.(?:js|css)[^"]*)"', _idx)
_untokened = sorted(set(a for a in _assets if "?v=" not in a))
# Read the tokens out of the LINKS, not out of the file text: index.html's
# own comment recounts the ?v=dpi300 incident, and a check that scanned the
# prose counted that as a live second token.
_linked = re.findall(r'(?:src|href)="([^"]*\?v=[^"]*)"', _idx)
_tokens = sorted(set(re.findall(r"\?v=([A-Za-z0-9._-]+)", " ".join(_linked))))

jsrc = text("playtest/dist/app.js")
check("rules/aos.html states the negate rule",
      "exhaust 2 misses" in text("rules/aos.html").lower())
check("build_aos.py footers state the negate rule",
      text("generator/build_aos.py").count("exhaust 2 misses on them") >= 3)
# THE FINAL EXAM POOL, IN ALL FOUR OWNERS. "Randomly select 1 Final Exam
# card from each subject... shuffle the 4 selected cards and draw 3", as of
# 2026-11-12. It replaced a Credit-weighted pool - 1 card at 0-1 Credits in
# that subject, 2 at 2-3, 3 at 4+ - which two of the four owners implemented
# by taking the FIRST cards of each subject in table order, so eight of the
# twelve printed exams could not come up at all on an empty transcript.
#
# Four owners have to agree: the book, the model, the lab and the mod. Each
# is read for the thing it actually does, not for a phrase - a dial's VALUE
# in nap.py, the per-subject pick in suite.js, the constant in lua.lua - so
# an owner left behind on the old rule fails here.
_pool_say = _says("Randomly select <b>1 Final Exam card from each subject</b>")
_pool_sim = sn.get("EXAM_POOL_BY_CREDITS") is False
_pool_lab = "pool.push(shuffle(ofSubject)[0])" in text("playtest/dist/suite.js")
_pool_mod = "EXAM_POOL_PER_SUBJECT = 1" in text("tts/lua.lua")
check("the exam pool is 1 card per subject in the book, model, lab and mod",
      _pool_say and _pool_sim and _pool_mod,
      "book=%s model=%s mod=%s" % (_pool_say, _pool_sim, _pool_mod))

# A RESTRICTION THE POOL CANNOT ANSWER, printed 2026-11-25. Jon sat a Fine
# Motor Assessment with no Blue in hand and the book had no answer: it
# waived Required Effort "only if no legal commitment/assignment is
# possible" and said nothing about the exams. The model had always waived
# silently, so the three owners agreed by accident on a rule none of them
# printed - which is the same shape as the End-of-Day burn, where two
# sources played a rule and the one publishing the figures did not.
#
# THE FREE WAIVER IS THE CLAIM, not merely the waiver. A price was
# measured and rejected: 1 Health on the colour-contribution clauses reads
# -7.5 points at Standard and -21.6 with the commitment counts added
# (simulation/napharder.txt), which is difficulty arriving at random -
# whether it fires depends on which colour you ran out of. So
# EXAM_WAIVER_COST must be 0 for the book to be telling the truth, and the
# check reads the DIAL rather than the prose that explains it.
_waive_say = _says("<b>one you cannot meet is waived at no cost.</b>")
_waive_sim = sn.get("EXAM_WAIVER_COST") == 0
_waive_mod = ("A RESTRICTION YOU CANNOT MEET is waived for free"
              in text("tts/build_mod.py"))
check("an unmeetable exam restriction is waived free in the book, "
      "the model and the mod",
      _waive_say and _waive_sim and _waive_mod,
      "book=%s model=%s (cost=%r) mod=%s"
      % (_waive_say, _waive_sim, sn.get("EXAM_WAIVER_COST"), _waive_mod))
# AND THE BOOK PRINTS THE RULE, NOT THE REASONING, because NAP's book has
# no room for the reasoning. It was four pages with its last column full to
# the line: one wrapped line anywhere in the exam section spills the footer
# onto a fifth page, and a fifth page holding a footer is not a rulebook.
# The sentence paid for itself by retiring "and you never know which exam
# is next" from the draw paragraph, which the paragraph above it already
# says as "turning each over only as you come to it". No rule was cut.
#
# SO WHICH KIND OF CLAUSE PAYS FOR ITSELF lives in the mod's quick
# reference and beside EXAM_WAIVER_COST, and this holds the mod to it: a
# count of dice or colours charges itself in successes the Health rule
# already takes, so only the colour-contribution clauses are really
# forgiven. Dropping it would leave the free waiver reading more generous
# than it is.
#
# WHAT THE NOTEBOOK NO LONGER CARRIES, as of 2026-11-25, is the ARGUMENT
# for that ruling - the worked example with no Blue in hand, and that a
# restriction constrains which dice you choose. The notebook took the
# same pass the four books took and is prose about how to play, not about
# why. The ruling itself is how a class of clause RESOLVES, so it stayed,
# and this check is pointed at it rather than at the paragraph that used
# to defend it. The argument survives beside EXAM_WAIVER_COST in
# simulation/nap.py, which no player reads.
check("the mod says a clause demanding a COUNT needs no waiver",
      "needs no" in text("tts/build_mod.py")
      and "dice you cannot commit are successes you do" in
          text("tts/build_mod.py"))
# THE 75% IS GONE, 2026-11-25, with every other figure in the rulebooks.
# The draw it described is still printed and still checked above; what the
# figure added was the consequence, which is commentary.
check("...and the book still prints the draw that gives it",
      _says("Each subject can appear at most once"))

# BOTH FACES PAY, in the model and in the lab. The model's call site was
# gated on `not card.on_demand` and the lab's on `a.demandSide`, because a
# Demand face printed no reward at all until 2026-11-12. A reward table with
# 26 entries proves nothing on its own - AGENTS.md's warning - so this reads
# the branch that pays, and the absence of the gate that used to stop it.
_nap_src = text("simulation/nap.py")
_lab_src = text("playtest/dist/suite.js")
check("the model pays a Task reward on whichever face completed it",
      "table = DEMAND_REWARD if card.on_demand else REQUEST_REWARD" in _nap_src
      and "self.apply_task_reward(card.index, card, take," in _nap_src
      and 'if card.kind in ("task", "impostor") and not card.on_demand:'
      not in _nap_src,
      "simulation/nap.py still gates the reward on the Request side")
# AND AN IMPOSTER TASK PAYS TOO, which is its own branch in both.
check("an Imposter Task's recovery is paid in the model",
      "self.apply_imposter_reward(card.index, card)" in _nap_src
      and "IMPOSTER_REWARD[index][1 if card.on_demand else 0]" in _nap_src)

# THE DEMAND-TARGET CENSUS, READ OFF THE CARDS. rules/nap.html used to say an
# unresolved Task flips to "a harsher printed effect, and often a higher
# Target", and this check only looked for that phrase - so it could not tell
# whether "often" was true. It was not: the 2026-10-28 Target rise left 14 of
# 26 printing the same number on both faces. The 2026-11-12 revision brought
# the six Demands of 9 down to 6, which moved the census again.
#
# So count the gaps instead of matching a word. The book now prints both
# numbers, and a Target that moves on a card has to move in the book.
_gaps = [r[6] - r[4] for r in gn["TASKS"]]
_up = sum(1 for _g in _gaps if _g > 0)
_same = sum(1 for _g in _gaps if _g == 0)
# THE BOOK STOPPED PRINTING THE COUNTS on 2026-11-25 - a deck census is a
# statement about what the cards do rather than a rule - so the two numeric
# clauses are gone and the card-side invariant is what is left: no Demand
# Target is more than 1 above its Request. That is the thing a reprint can
# break. The book still has to promise no more than "sometimes".
check("no Demand Target is more than 1 above its Request",
      _up + _same == len(_gaps) and max(_gaps) == 1
      and "sometimes a higher Target" in _nap_rules,
      "cards: %d up by 1, %d level, widest gap %d" % (_up, _same, max(_gaps)))

print()
# build_nrj's own tables. The binding lived in the generator-vs-lab loop
# until that went on 2026-11-25, and the checks below still read it.
gr = py_tables("generator/build_nrj.py")

# THE IMPOSTER TASK DOTS. Every NAP Assignment prints a recovery-colour dot
# and three printed rules read "that Assignment's color dot" - Required
# Effort, completing or storing progress, and the colour the Primary queues
# for the next Time Slot. The 4 Imposter Tasks printed none until 2026-10-31,
# so the card, the model (which inherited the replaced Task's dot) and the
# lab (which fell back to "P") all disagreed, and nothing here could see it.
IMP_DOTS = (("Neural Extraction Practicum", "P"),
            ("Load-Bearing Prosthetics", "B"),
            ("Emergency Specimen Handling", "Y"),
            ("Containment Drill", "G"))
gen_imp = {r[0]: r[2] for r in gr["IMPOSTER_TASKS"]}
js_imp = {r[0]: r[2] for r in js_literal("playtest/dist/suite.js",
                                         "NAP_IMPOSTER_TASKS")}
# Indexed rather than unpacked: nap.IMPOSTER_TASKS grew a fifth column on
# 2026-11-06 when the four printed effects were modelled.
sim_imp = dict((r[0], r[1])
               for r in py_tables("simulation/nap.py")["IMPOSTER_TASKS"])
# Indexed, not unpacked: the table grew a Request reward and a Demand
# reward on 2026-11-12 and would have grown this line a TypeError.
sim_subj = {r[0]: r[1] for r in gr["IMPOSTER_TASKS"]}
bad = [n for n, d in IMP_DOTS
       if gen_imp.get(n) != d or js_imp.get(n) != d
       or sim_imp.get(sim_subj.get(n)) != d]

# The Tier III decks the lab keeps outside suite.js. Every field is compared,
# because the claim CONDITION now carries the cost clause that prices it -
# "Claiming gives up..." - and a lab that kept the old wording would teach the
# player a rule the rulebooks no longer have.
# INTF and CORRUPT joined this list on 2026-11-06, when the recycle clause on
# "I Don't Have Time for This" was capped: app.js:280 prints the Interference
# card's text to the player and app.js:414 prints the Corrupted Limitation's,
# so a copy that keeps the old wording teaches a rule no card has. Nothing
# was comparing either deck until the cap had to be made in two places.
# BAT'S TIER MODULES ARE NOT PORTED TO THE SCAVENGED-TYRANT LAB YET, so
# the lab must carry NO copy of their text rather than a stale one - the
# revision rewrites every card (R33/R34/R35) and an old copy would teach a
# rule no card has, which is exactly what this block exists to stop. The
# pair of conditions is the point: no stale data AND a notice where a
# playtester sees it. When the modules are ported, BAT_NOTES comes back and
# this check is replaced by the loop below.
# THE RECYCLE CAP, in the card and in the model. Uncapped, this one card
# measured 1.2% at Tier I against a 51.8% solo column and was drawn 1 game in
# 6, so the two copies drifting apart is a 33-point drift in one sixth of all
# AoS campaign games.
check("'I Don't Have Time for This' caps the recycle at once per Program",
      "The first time each already-Overheated Program fails"
      in text("generator/build_nrj.py"))
check("aos.py caps it the same way (RECYCLE_LIMIT / RECYCLE_SCOPE)",
      "RECYCLE_LIMIT = 1" in text("simulation/aos.py")
      and 'RECYCLE_SCOPE = "program"' in text("simulation/aos.py"))

check("the Tier III claim cost is printed on all 12 BAT and AoS cards",
      text("generator/build_nrj.py").count(
          "Claiming gives up the next Upgrade a completed Experiment earns.")
      == 6
      and text("generator/build_nrj.py").count(
          "Claiming gives up the next Program Reward you would claim.") == 6)

check("the campaign is Tier III only in all four books",
      ("Tier III\nonly" in text("rules/nrj.html")
       or "Tier III only" in text("rules/nrj.html"))
      and all(re.search(r"Tier III\s*(only|\))", text(f))
              for f in ("rules/bat.html", "rules/nap.html",
                        "rules/aos.html")))

# HOW MANY CARDS ARE RETAINED, in the three places that say so. NAP 3, BAT 2,
# AoS 2: with one card value the pool is just a count, and seven is the count
# that reads 50.6%. Six reads 41.5% and eight 57.8%, so a place that drifts by
# one card drifts by about eight points of win rate.
check("finale.py retains 3 NAP / 2 BAT / 2 AoS",
      "RETAIN = (3, 2, 2)" in text("simulation/finale.py"))
check("nrj.html's standalone mode deals the same",
      "<b>3 Opportunities, 2 Notes and 2 Routines</b>" in text("rules/nrj.html")
      and "At most seven retained cards" in text("rules/nrj.html"))

# RETAINED OR NOT - one value. The spent/unspent split was dropped on
# 2026-10-30 because nothing on the table records which a card is. A file
# that kept it would be asking the player for bookkeeping the others do not.
check("a retained card is worth 2, with no spent/unspent split",
      "Card(game, CARD_VALUE)" in text("simulation/finale.py")
      and "CARD_VALUE = 2" in text("simulation/finale.py"))
check("no file still halves a card for having been spent",
      "SPENT" not in text("simulation/finale.py")
      and "never spent it" not in text("rules/nrj.html"))

# THE DIFFICULTY LADDER names its dice, so all three files carry the same
# four rows of yellow / green / blue / purple or the lab is not playing the
# game the book describes. The counts are not interchangeable: the same
# total taken from different colours measured 28.7% against 38.4%.
LADDER = (("easy", (3, 3, 3, 3)), ("standard", (3, 3, 4, 4)),
          ("hard", (3, 3, 4, 4)), ("nobulous", (3, 3, 4, 4)))
# AND THE HEALTH ROW, which is new on 2026-11-16 and is the first time this
# ladder has been cut on two axes. Sixteen is every colour die there is and
# the cap still read 27% once the model scored its hand, so the last rung
# lowers Health instead. Four files carry it and all four have to agree:
# the rulebook's own table is the owner, exactly as it is for the dice.
LADDER_HP = (("easy", 5), ("standard", 5), ("hard", 4), ("nobulous", 3))
sim = text("simulation/finale.py")
check("finale.py carries the ladder as a per-colour table",
      'TIRED_COLOURS = ("yellow", "green", "blue", "purple")' in sim
      and all('"%s": (%s)' % (lvl, ", ".join(str(n) for n in c)) in sim
              for lvl, c in LADDER))
nrj = text("rules/nrj.html")
check("nrj.html prints the same four rows",
      "Four difficulties" in nrj
      and all("".join("<td>%d</td>" % n for n in c) in
              nrj.replace("\n", "").replace("      ", "")
              for lvl, c in LADDER))
check("finale.py carries the Health row beside the dice",
      "LADDER_HEALTH = {%s}"
      % ", ".join('"%s": %d' % r for r in LADDER_HP) in sim
      and "HEALTH=LADDER_HEALTH[lab]" in sim)
check("nrj.html prints the Health column",
      all("".join("<td>%d</td>" % n for n in c + (hp,)) in
          nrj.replace("\n", "").replace("      ", "")
          for (lvl, c), (_l2, hp) in zip(LADDER, LADDER_HP))
      # WHITESPACE-INSENSITIVE since 2026-11-25: the sentence survived the
      # editorial pass but its line break did not, and a check that fails
      # on a reflowed paragraph reports a rule change that did not happen.
      and "Hard and Nobulous lower your Health instead"
      in " ".join(nrj.split()))
# AND NO RUNG OPENS WITH NOTHING IT MAY APPLY. The attention starts on
# Yellow with a Yellow+Green window, so a rung that exhausts all four
# yellow AND all four green begins holding only the red die and session 1
# is skipped rather than hard. This is the same argument the rulebook
# already makes for the red die one session further on, and it is what
# caps the dice at fourteen and pushes the last two rungs onto Health.
check("no rung starts with nothing the opening window can apply",
      all(c[0] < 4 and c[1] < 4 for _lvl, c in LADDER),
      "y/g fully exhausted at: %r"
      % ([l for l, c in LADDER if c[0] >= 4 and c[1] >= 4],))
check("and nobody exhausts the single red die",
      "red" not in sim[sim.index("TIRED_COLOURS"):
                       sim.index("START_TIRED = ")])

# THE EXHIBIT FACE. Target and Damage are printed now, so the rulebook must
# NOT still be telling the player to subtract 5.
nrjgen = text("generator/build_nrj.py")
check("the Exhibit face prints Target and Damage",
      "def exhibit_body" in nrjgen and "EXHIBIT_OFFSET = 5" in nrjgen
      and "BIG_TARGET = 5" in nrjgen
      and '<div class="biglbl">Damage</div>' in nrjgen)
check("and the rulebook no longer asks for the subtraction",
      "minus 5" not in nrj
      and "Each Exhibit prints its <b>Target</b>, its <b>Damage</b>" in nrj)
# The five Rewards being reworded for the finale is checked further down,
# against EXHIBIT_REWARD itself. It used to be counted by grepping the
# generator for the cue phrase, which also counted the comments that
# explain the phrase.

# THE FIVE IMPOSTERS, AND THEIR ABILITIES ARE NOT IN THE BOOK.
#
# Jon, 2026-11-13: take them out. They were a ten-row table of the card
# text - a full column of the supplement and two of its six pages - and
# the cards print every word of it, so the book names the five
# Imposters, says the ability is printed on the card, and stops.
#
# INVERTED, NOT DELETED. It used to fail when an ability name was
# MISSING from the rulebook; it fails now when one is back in it, which
# is the thing that would quietly undo the change. The five Imposter
# NAMES are still required, because you have to be able to look up
# which five there are.
imp = py_tables("generator/build_nrj.py").get("IMPOSTERS", [])
# The rulebook wraps its lines and hyphenates with &#8209; so that a card
# name does not break across a column. Compare against a flattened copy
# rather than making the rules uglier to suit the checker.
nrj_flat = " ".join(nrj.replace("&#8209;", "-").split())
check("five Imposters, two sides each", len(imp) == 10
      and len(set(r[0] for r in imp)) == 5
      and sorted(r[2] for r in imp) == ['A'] * 5 + ['B'] * 5)
check("every Imposter prints the finale's own 5 HP / 2 STR / 3 REC",
      "IMP_STATS = (5, 2, 3)" in nrjgen
      and "The Imposter begins at <b>5 HP / 2 STR / 3 REC</b>" in nrj_flat)
# finale.py prices a point of STR at 30 points of win rate and REC 5 inverts
# the commit decision, so no ability may hand out either.
check("no Imposter ability touches STR or REC",
      not any("STR" in r[5] or "REC" in r[5] for r in imp))
check("the five Imposters are named in rules/nrj.html",
      all(n in nrj_flat for n in sorted(set(r[0] for r in imp))),
      "%r" % ([n for n in sorted(set(r[0] for r in imp))
               if n not in nrj_flat],))
check("...and not one of their ten abilities is duplicated in it",
      not [n for n in sorted(set(r[4] for r in imp)) if n in nrj_flat],
      "%r" % ([n for n in sorted(set(r[4] for r in imp))
               if n in nrj_flat],))
check("...and the book says where to read them instead",
      "the ability is printed on the card" in nrj_flat
      and "differ only in the ability printed on the card" in nrj_flat)
check("the Imposter deck is registered for PnP, TTS and the lab",
      "'NRJ_Imposters'" in text("generator/pack.py")
      and "key='NRJ_Imposters'" in text("tts/decks.py")
      and "'NRJ_Imposters_TTS.png'" in text("generator/build_catalog.py"))

# THE DICE, BY COLOR, IN THE COMPONENTS LIST (Jon, 2026-11-13). The
# supplement asked for "the 17 unit dice" and left the player to find
# out from the difficulty table that there is exactly one Red. The
# counts are the set's own 4/4/4/4/1, and they are written with the
# stylesheet's colored pip so the list shows the colors rather than
# naming them.
_comp = nrj_flat[nrj_flat.index("<h2>Components</h2>"):
                 nrj_flat.index("<h2>What NRJ adds</h2>")]
check("the components list breaks the 17 dice down by color",
      all(('class="sw %s"></span>%d %s' % (_k, _n, _c)) in _comp
          for _k, _n, _c in (("Y", 4, "Yellow"), ("G", 4, "Green"),
                             ("B", 4, "Blue"), ("P", 4, "Purple"),
                             ("R", 1, "Red"))),
      _comp[_comp.index("From 20 Strong"):][:220])

# ONE FACE-DOWN CANDIDATE DECK, NOT THREE FACE-UP STACKS (Jon,
# 2026-11-13: "it makes more sense to just mix all 11 together, create
# a draw deck and a discard space for them"). Nothing in the finale
# asks which candidate a candidate is, so the book says shuffle them
# together and the mod does it - and the check is on BOTH ends,
# because a rulebook that says deck while the table deals three stacks
# is worse than either.
_nrjtext = " ".join(re.sub(r"<[^>]+>", " ", text("rules/nrj.html")).split())
_nrjtext = _nrjtext.replace("&#8209;", "-").replace("&mdash;", "--")
check("rules/nrj.html shuffles the candidates into one face-down deck",
      "Shuffle them into one face-down Candidate deck" in _nrjtext)
check("...and counts a card you could not carry among them",
      "a card you claimed and could not carry among them" in _nrjtext)

# AND THE SECTION OPENS ON THE CAPS (Jon, 2026-11-13: "I don't care how
# many cards can potentially go into the pool. I want to know how many
# cards I can retain from each game"). It used to open on the 18, with
# a four-column table about the 18, and put the caps in a SECOND table
# below a paragraph of definitions - so the one number a player needs
# was third in reading order behind two pieces of bookkeeping.
#
# THE ORDER IS THE CLAIM, which is why this measures a distance rather
# than looking for the words somewhere in the file. The caps have to
# come before the first mention of six-of-anything.
_pool = _nrjtext[_nrjtext.index("The Research Pool --"):]
_caps = _pool.index("At most 3 out of NAP, 2 out of BAT and 2 out of AoS")
check("...and the Pool section opens on how many you carry out of each game",
      _caps < 90, "%d characters in" % _caps)
check("...before it mentions how many each game lays out",
      _caps < _pool.index("6 Research Notes"),
      "caps at %d, the six at %d"
      % (_caps, _pool.index("6 Research Notes")))
check("the Research Pool is the Tier III cards, not the games' own decks",
      "the Tier III cards you claimed" in text("rules/nrj.html")
      and "6 Research Notes" in text("rules/nrj.html")
      and "6 Devious Opportunities" in text("rules/nrj.html")
      and "6 Backdoor Routines" in text("rules/nrj.html"))

# The finale restores five printed Rewards by NAME, in four places: the
# card (build_nrj.EXHIBIT_REWARD), the rulebook, suite.js's NRJ_REWARDS and
# finale.py's REWARDS. A renamed card would silently stop paying, so the
# names are checked against the deck.
#
# ALL 24 EXHIBITS PRINT A REWARD BAND and only those five do anything.
# Those five are bold; the other nineteen carry a courtesy, which is
# flavour set in italics. The
# danger is a courtesy that reads like a rule, so the wording is checked
# too: it may not borrow the five's cue phrase, and it may not name a
# thing the game has. Mood is not the test - "Help yourself to anything
# that isn't smoking" is imperative and plainly flavour. Having nothing
# in it that can be acted on is the test, and build_nrj's
# COURTESY_FORBIDDEN is the list this reads.
print()
print("NRJ - the Reward band, and the five that pay")
scen = gr["SCEN"]
printed_rewards = set(r[0] for r in scen if r[2].endswith("Reward"))
paying = gr["EXHIBIT_REWARD"]
courtesy = gr["EXHIBIT_COURTESY"]
js_rewards = set(js_literal("playtest/dist/suite.js", "NRJ_REWARDS"))
sim = text("simulation/finale.py")
rules = text("rules/nrj.html")
names = [r[0] for r in scen]
check("every Exhibit prints a Reward band",
      all(n in paying or n in courtesy for n in names),
      "%s" % sorted(n for n in names if n not in paying and n not in courtesy))
check("exactly 5 of the %d pay" % len(names), len(paying) == 5,
      "%d: %s" % (len(paying), sorted(paying)))
check("no Exhibit carries both a Reward and a courtesy",
      not (set(paying) & set(courtesy)), "%s" % sorted(set(paying) & set(courtesy)))
CUE = "When this Exhibit falls"
check("all 5 paying Rewards open with the cue phrase",
      all(t.startswith(CUE) for t in paying.values()),
      "%s" % sorted(n for n, t in paying.items() if not t.startswith(CUE)))
check("no courtesy borrows the cue phrase",
      not any(CUE in t for t in courtesy.values()),
      "%s" % sorted(n for n, t in courtesy.items() if CUE in t))
_banned = re.compile(r"(%s)" % "|".join(gr["COURTESY_FORBIDDEN"]), re.I)
_leaks = sorted(n for n, t in courtesy.items() if _banned.search(t))
check("no courtesy names a thing the game has", not _leaks, "%s" % _leaks)
check("the rulebook says every Exhibit prints one and five pay",
      "Every Exhibit prints a Reward and <b>five of them pay</b>" in rules)
# THE SUPPLEMENT NO LONGER LISTS THEM BY NAME, 2026-11-25: five cards and
# what each one does is card text, and the cards print it. So each is held
# against finale.py alone - the model still has to implement the five the
# generator prints, which is the half that was ever load-bearing.
missing = sorted(js_rewards - printed_rewards)
for name in sorted(js_rewards):
    check("  %s in finale.py" % name, name in sim)

print()
print("FLAVOUR TEXT THE LAB KEEPS ITS OWN COPY OF")
# The lab does not read flavour out of the generators: app.js carries all
# 32 AoS programs (both sides) and the 6 Limitations, and
# bat_experiments.js carries all 20 Experiments. On 2026-11-02 a 57-line
# flavour revision landed in the generators and those two files had to be
# walked by hand, which is the moment a copy goes stale. These checks are
# cheap and would have caught it.
_lab = "".join(text("playtest/dist/%s" % f)
               for f in ("app.js", "bat_experiments.js", "suite.js", "bat.js",
                         "aos_assemblies.js"))
_gb, _ga = py_tables("generator/build_bat.py"), py_tables("generator/aos.py")
for _label, _lines in (
        ("BAT Experiments", [r[3] for r in _gb["EXPERIMENTS"]]),
        ("AoS Stable sides", [v[0] for v in _ga["FLAVOR"].values()]),
        ("AoS Overheated sides", [v[1] for v in _ga["FLAVOR"].values()]),
        ("AoS Limitations", [r[2] for r in _ga["LIMITATIONS"]]),
        # Both faces of every Assembly: the recipe side's flavour and the
        # Advanced Program's. These reach the lab through the generated
        # aos_assemblies.js rather than a transcription, so what this
        # catches is an export that was not re-run.
        ("AoS Assembly fronts", [v[0] for v in _ga["ASSEMBLY_FLAVOR"].values()]),
        ("AoS Assembly backs", [v[1] for v in _ga["ASSEMBLY_FLAVOR"].values()])):
    _stale = [t for t in _lines if t and t not in _lab]
    check("  the lab's %d %s lines match the generator" % (len(_lines), _label),
          not _stale, "%d stale, e.g. %r" % (len(_stale), _stale[:1]))

print()
print("THE DECK REGISTRIES - sheet, manifest, TTS and the lab")
# EVERY DECK IS REGISTERED IN FIVE PLACES and until 2026-10-31 nothing
# compared them. NAP_SlotsFINF had been 3 Time Slots + 1 FINF card; when
# FINF went to one card per Slot the sheet grew to six 1050x750 cells and
# CARD_MANIFEST.txt and tts/decks.py were left saying four. tts/build_mod.py
# writes NumWidth straight into the saved object, so TTS sliced the 6300px
# sheet into four 1575px columns - every face mis-cut, two cards missing.
# The lab was right because build_catalog.py counts the generator's tables.
cat = json.loads(text("playtest/dist/catalog.json"))
tts_src = text("tts/decks.py")
man = text("CARD_MANIFEST.txt")
man = man[man.index("DECK SHEETS AND BACKS"):man.index("CARD BACKS")]
for game in sorted(cat):
    for d in cat[game]["decks"]:
        key = d["sheet"].replace("_TTS.png", "")
        n, cols, rows = len(d["cards"]), d["cols"], d["rows"]
        # One SHEET may be served by more than one TTS deck, because a TTS
        # deck carries exactly one back and NAP_SlotsFINF needs two. So the
        # entries are gathered by sheet, their counts summed, and the grid
        # required to be the whole image in every one of them - NumWidth
        # slices the file, so a deck taking half of it still says 6x1.
        ents = [m.group(1) for m in
                re.finditer(r"dict\(([^)]*)\)", tts_src)
                if re.search(r"sheet='%s'" % re.escape(key), m.group(1))
                or re.search(r"key='%s'" % re.escape(key), m.group(1))
                and "sheet=" not in m.group(1)]
        if ents:
            got = [dict(re.findall(r"(count|w|h|first)=(\d+)", b)) for b in ents]
            check("  %s is %dx%d in TTS and the lab%s"
                  % (key, cols, rows,
                     " (%d decks)" % len(ents) if len(ents) > 1 else ""),
                  all(g.get("w") == str(cols) and g.get("h") == str(rows)
                      for g in got)
                  and sum(int(g["count"]) for g in got) == n)
            if len(ents) > 1:
                # The only reason to split a sheet is two different backs,
                # and the slices must tile it exactly once.
                backs = [re.search(r"back='([^']*)'", b).group(1) for b in ents]
                spans = sorted((int(g.get("first", 0)), int(g["count"]))
                               for g in got)
                at = 0
                tiled = True
                for f, c in spans:
                    tiled = tiled and f == at
                    at += c
                check("  %s's %d decks have distinct backs and tile it once"
                      % (key, len(ents)),
                      len(set(backs)) == len(backs) and tiled and at == n,
                      "%r %r" % (backs, spans))
        elif key not in ("AoS_ElementMats",):
            check("  %s is in tts/decks.py" % key, False)
        row = re.search(r"\n  %s\s+(\d+)x(\d+)\s+(portrait|landscape)"
                        % re.escape(key), man)
        check("  %s matches CARD_MANIFEST" % key,
              bool(row) and (int(row.group(1)), int(row.group(2)),
                             row.group(3) == "landscape")
              == (cols, rows, d["landscape"]))

print()
print("BAT - rules and app")
jb = text("playtest/dist/bat.js")
jr = text("playtest/dist/bat_rules.js")
hb = text("rules/bat.html")
_ORDER = ("Easy", "Standard", "Hard", "Nobulous")

check("...and the node harness exists and names what it is for",
      "test_bat_rules" in text("playtest/test_bat_rules.js")[:400]
      or "rules checks pass" in text("playtest/test_bat_rules.js"),
      "playtest/test_bat_rules.js is missing or says nothing")

for _name, _want in (("PARTS_DECK", sorted(set(
                          _brev["PARTS_AT_SETUP"].values()))[0]),
                     ("EXPERIMENTS_DEALT", _brev["EXPERIMENTS_DEALT"]),
                     ("WAKEUP_PACKET", _brev["WAKEUP_PACKET"]),
                     ("PROTO_HP", _brev["SHARED_HP_START"]),
                     ("NO_GRAFT_CAP", _brev["NO_GRAFT_CAP"]),
                     ("GRAFT_REVEAL", _brev["GRAFT_REVEAL"]),
                     ("TARGET_FLOOR", _brev["TARGET_FLOOR"]),
                     ("OPENING_RECOVERY", _brev["OPENING_RECOVERY"]),
                     ("PASS_RECOVERY_BONUS",
                      _brev["PASS_RECOVERY_BONUS"])):
    _m = re.search(r"var %s = (\d+);" % _name, jr)
    check("  bat_rules.%s is batrev's %r" % (_name, _want),
          bool(_m) and int(_m.group(1)) == _want,
          "lab %s" % (_m and _m.group(1),))


# THE ROUNDS ARE PER RUNG NOW, so the book cannot print one number. It has
# to print the sentence that makes the clock a loss condition, and the
# table above is what holds the four values.
check("rules/bat.html: the clock is a loss condition",
      "rounds are used up" in _RULES["bat"]
      and "the Rats lose" in _RULES["bat"]
      and "8 rounds" not in hb and "eight rounds" not in hb)
check("rules/bat.html: Splice met in one attack",
      "one attack" in hb.lower())
check("rules/bat.html: no commit cap left",
      "up to 6 dice" not in hb.lower())
# HEALTH IS WHAT A BLOW STRIPS FIRST, and the book has to say the ORDER.
#
# It said "optional, hold part of the Health on it and spend that first",
# which with a track of Splices THEN Health put it last but one - and its
# whole purpose is that the Splices shelter behind it. Jon's framing,
# 2026-11-12: Health and a core Health are two independent stats, and
# damage has to get past the Health AND every Splice to reach the core.
# Three things have to hold together, so three things are checked.
#
# AND THE STAT IS CALLED HEALTH, after the card it stands on. It was "the
# Tyrant's outer layer" until 2026-11-18; the term is retired, and the
# retirement is an invariant here rather than a tidy-up somebody has to
# remember - two glosses on one stat is how the Encounters/Experiment
# split started.
# HEALTH AND THE CORE HEALTH ARE BOTH RETIRED. The old Tyrant has no
# Health at all now - its bulk IS its wall of Splices - and the one Health
# track in the game is the PROTOTYRANT's, shared by all four Rats. The
# retirement is an invariant rather than a tidy-up, for the same reason the
# "outer layer" wording was: two glosses on one stat is how the
# Encounters/Experiment split started.
# AND THE TRACK CARD IS OUT OF THE BOOK, 2026-11-22. The component, the
# Wake-Up step that stood a die on it and the Fine-tuning sentence that
# offered its fifteenth space all went; what is left is a number you
# keep, which is what every other count in the set already is.
check("rules/bat.html: one shared Health, and the Tyrant's own Health is retired",
      "Prototyrant&rsquo;s <b>Health</b> at <b>12</b>" in hb
      and "Health track card" not in hb
      and "Health track has 15 spaces" not in hb
      # THE RETIRED NAMES, not the live one. A blind rename turned this
      # into "Health" not in hb, which can never pass in a book whose
      # subject is a Health track - and a check that cannot pass is worse
      # than none, because it hides the ones that can.
      and "Buff HP" not in hb and "core Health" not in hb
      and "Tyrant Health</th>" not in hb
      and not re.search(r"\blayers?\b", hb, re.I))
# ...AND IT IS THE NUMBER batrev STARTS IT AT. Read out of the Wake-Up
# step, which is the one sentence in the book that sets it.
rulenum("bat", r"Prototyrant.s Health at (\d+)", _brev["SHARED_HP_START"],
        "the Prototyrant's starting Health")
check("...and batrev pools it rather than tracking a Health per Rat",
      _brev["SHARED_HP"] is True, "SHARED_HP=%r" % (_brev.get("SHARED_HP"),))
# AND THE ORDER IS PRINTED, in the sentence that lists the track. Read out of
# the sentence rather than matched as a phrase, so saying it differently
# still passes and saying it backwards does not.
# BY POSITION IN THE SENTENCE, NOT BY MEMBERSHIP. The first version of
# this read `[w for w in ("Health", "Splices", "core Health") if w in
# sentence]`, which sorts by the TUPLE's order and not the text's - so it
# passed with the sentence printed backwards. Mutation-tested both ways now.
# THERE IS NO DAMAGE ORDER LEFT TO PRINT. The Tyrant track - Health, then
# five Splices, then a core dial - is gone with the printed game. One
# Splice faces the Rats at a time, and the only thing damage can reach is
# that Splice. What the book has to say instead is that nothing carries:
# the old order let a blow run on through the wall.
check("...and no damage order survives, because only one Splice is exposed",
      "the top Splice" in _RULES["bat"]
      and "Nothing carries over to the next" in _RULES["bat"]
      and "Tyrant track" not in hb)
# AND THE MODEL RUNS THAT ORDER. The book could say it while damage_tyrant
# went straight to the Splices; this is the call site, not a table entry.


def _method(rel, name):
    """One method's source, from its def to the next def at that indent.

    A CALL SITE, NOT A TABLE ENTRY. AGENTS.md is explicit about this trap:
    three coverage claims have passed while the card did nothing because the
    predicate counted entries in a table. A layer value in DIFFICULTY proves
    nothing about whether damage ever touches it, so the claim below is
    about the inside of the function that would have to.
    """
    src = text(rel)
    m = re.search(r"^(\s*)def %s\(" % re.escape(name), src, re.M)
    if not m:
        return ""
    indent = m.group(1)
    rest = src[m.end():]
    nxt = re.search(r"^%sdef " % re.escape(indent), rest, re.M)
    return rest[:nxt.start()] if nxt else rest


_dmg = _method("simulation/bat.py", "damage_tyrant")
check("...and simulation/bat.py damages the layer before any Splice",
      "self.buff -= take" in _dmg
      and "if self.buff > 0 or dmg <= 0:" in _dmg
      and _dmg.index("self.buff") < _dmg.index("for s in self.track()"),
      "damage_tyrant does not strip the layer before the Splices")

print()
print("NRJ - the five Imposters")
# The lab enforces the ten abilities as of 2026-10-31, so the ability TEXT is
# now live data and not decoration: suite.js renders it as innerHTML, which
# is why NRJ_IMPOSTERS carries build_nrj.py's strings verbatim - <i> tags,
# entities and all - and why this compares them character for character.
# Before this, the lab had no Imposter picker at all.
js_imp = js_literal("playtest/dist/suite.js", "NRJ_IMPOSTERS")
gen_rows = gr["IMPOSTERS"]
bad = []
for k, (name, _role, side, when, ability, at, _fl) in enumerate(gen_rows):
    if k >= len(js_imp):
        break
    a = js_imp[k]
    for field, want, got in (("name", name, a["name"]), ("side", side, a["side"]),
                             ("when", when, a["when"]),
                             ("ability", ability, a["ability"]),
                             ("text", at, a["text"]),
                             ("sprite column", k // 2, a["i"]),
                             ("id", "%d%s" % (k // 2, side), a["id"])):
        if want != got:
            bad.append("%s %s: card %r, lab %r" % (ability, field, want, got))
# All five print the finale's own statline. A per-Imposter statline would
# make the choice a difficulty dial, which is the one thing it may not be.
check("the cards print one statline, 5 HP / 2 STR / 3 REC",
      tuple(gr["IMP_STATS"]) == (5, 2, 3), "%r" % (gr["IMP_STATS"],))
# The lab keys every ability off `key`, and `per`/`uses` is how it counts
# them, so a duplicate key or a zero-use active side would silently disable
# one of the ten.
keys = [a["key"] for a in js_imp]
bad = [a["ability"] for a in js_imp
       if (a["per"] == "passive") != (a["when"] == "Passive")
       or a["per"] != "passive" and a["uses"] < 1
       or a["when"].startswith("Twice") and a["uses"] != 2
       or a["when"] == "Once per Session" and a["per"] != "session"]
# The Understudy is the only one who spends Candidates, in the cards, the
# rules and now the lab.
cost = [a["ability"] for a in js_imp if a.get("cost")]
# THE SAME DEMAND, THE OTHER WAY ROUND, and from the lab's own table
# rather than the generator's - see THE FIVE IMPOSTERS above. The
# hyphen normalisation stays: the cards set an ability name with a
# plain hyphen and the book used a non-breaking one, so a check that
# did not normalise would pass on a name that really was still there.
nrjh = text("rules/nrj.html").replace("&#8209;", "-").replace(u"‑", "-")
back = [a for (_n, _r, _s, _w, a, _t, _f) in gen_rows if a in nrjh]
check("rules/nrj.html carries no ability text of its own", not back,
      "%r" % (back,))

print()
print("Card geometry - gen.py vs catalog.json vs the lab")
# The lab has to know a sheet's cell size and the cream margin inside it to
# place a preview. It used to assume them, as 200 DPI pixel literals, and
# went on assuming them through the move to 300 DPI on 2026-10-30 - the
# ratios are close enough that the preview merely cropped the card's whole
# margin away instead of breaking outright. gen.py owns the numbers now and
# build_catalog.py publishes them per deck; this is what keeps that true.
gen_src = text("generator/gen.py")
check("gen.py's CSS insets the card by CARD_INSET_MM, not a literal",
      "inset:%fmm" in gen_src and "CARD_INSET_MM = " in gen_src)
_g = {}
for _line in gen_src.splitlines():
    for _k in ("PORTRAIT", "LANDSCAPE", "DPI", "CARD_INSET_MM"):
        if _line.startswith(_k + " = "):
            _g[_k] = ast.literal_eval(_line.split(" = ", 1)[1].strip())
with io.open(os.path.join(ROOT, "playtest", "dist", "catalog.json"),
             encoding="utf-8") as _fh:
    _cat = json.load(_fh)
_decks = [d for _game in _cat.values() for d in _game["decks"]]
_have = [d for d in _decks if "cell" in d and "gutter" in d]
check("every catalog deck publishes its cell size and gutter",
      len(_have) == len(_decks), "%d of %d" % (len(_have), len(_decks)))


def _want_gutter(d):
    """The 2mm inset is physical, so at a cell's own scale it is that
    fraction of the card's width - which survives fit_tts shrinking a sheet
    (NAP Assignments are 1000x714 where every other portrait deck is
    750x1050, and its gutter is 22px rather than 24)."""
    mm = (_g["LANDSCAPE"] if d["landscape"] else _g["PORTRAIT"])[0]
    return int(round(d["cell"][0] * _g["CARD_INSET_MM"] / mm))


_off = ["%s %s vs %s" % (d["sheet"], d["gutter"], _want_gutter(d))
        for d in _have if abs(d["gutter"] - _want_gutter(d)) > 1]
check("each gutter is gen.py's %.1fmm inset at that cell size"
      % _g["CARD_INSET_MM"], not _off, "; ".join(_off[:3]))
_square = [d["sheet"] for d in _have
           if (d["cell"][0] > d["cell"][1]) != bool(d["landscape"])]
check("every cell's shape agrees with the deck's orientation", not _square,
      "%r" % (_square,))
_sj = text("playtest/dist/suite.js")

print()
print("Card titles - the gap between measuring and rendering")
# hdr_fit reserves a second line of header when a title wraps, because
# WeasyPrint sizes the flex header from one line and the body then covers
# the subtitle. It measures with PIL; WeasyPrint lays out with Pango, and
# PIL runs short. "Undocumented Dependencies" measured 99.86% of the
# available width on 2026-11-02, so nothing was reserved and Pango wrapped
# it anyway - the subtitle was cut in half on the printed card.
#
# TITLE_SAFETY is the margin that covers that gap, and gen.py records the
# measured size of the gap next to it. These checks hold the margin
# against the measurement and every printed title against the margin.
_FT_FONT = os.path.join(ROOT, "fonts", "DejaVuSans-Bold.ttf")
try:
    from PIL import ImageFont
    # EXERCISED, NOT MERELY IMPORTED. Pillow loads its FreeType binding
    # lazily, so `from PIL import ImageFont` succeeds and the first
    # truetype() call is where it dies - which is what happened on this
    # machine on 2026-11-09, when Windows Smart App Control started
    # blocking _imagingft.pyd for being unsigned. The suite died there
    # with a traceback, taking the summary and the 40 checks after it
    # with it, and read like a failure rather than a missing tool.
    ImageFont.truetype(_FT_FONT, 20).getlength("x")
except Exception as _ft_err:
    skip("card titles are clear of the measure/render gap",
         "no PIL text engine here (%s). Card art is rendered by "
         "WeasyPrint, not by this, so a rebuild is unaffected; only "
         "the title-width measurement is." % _ft_err.__class__.__name__)
else:
    _gs = text("generator/gen.py")
    # gen.py renders on import, so its constants are read out of the source
    # rather than imported. HDR_STYLES is spelled out as a literal there so
    # this can read it; if that stops being true, this check stops running
    # rather than quietly measuring the default style for every deck.
    _gv = {}
    for _n in ast.parse(_gs).body:
        if isinstance(_n, ast.Assign) and isinstance(_n.targets[0], ast.Name) \
                and _n.targets[0].id in ("PORTRAIT", "LANDSCAPE", "DPI",
                                         "CARD_INSET_MM", "TITLE_SAFETY",
                                         "TITLE_PANGO_RATIO", "HDR_PAD",
                                         "HDR_STYLES"):
            try:
                _gv[_n.targets[0].id] = ast.literal_eval(_n.value)
            except ValueError:
                pass
    _pt_mm = 25.4 / 72.0
    _border = 0.5 * _pt_mm
    _fdir = os.path.join(ROOT, "fonts", "DejaVuSans-Bold.ttf")

    _missing = [_k for _k in ("HDR_STYLES", "HDR_PAD", "TITLE_SAFETY")
                if _k not in _gv]
    check("gen.py still declares the header styles this check reads",
          not _missing, "cannot literal_eval: %r" % (_missing,))

    def _limit(deck):
        """The title's room in px, in the style this deck really prints."""
        _size = _gv["LANDSCAPE"] if deck["landscape"] else _gv["PORTRAIT"]
        _extra = _gv["HDR_STYLES"][deck.get("hdr", "")][2]
        return ((_size[0] - 2 * _gv["CARD_INSET_MM"] - 2 * _border
                 - 2 * _gv["HDR_PAD"][2] - _extra) * _gv["DPI"] / 25.4)

    def _width(name, pt):
        _px = max(8, int(round(pt * _pt_mm * _gv["DPI"] / 25.4)))
        return ImageFont.truetype(_fdir, _px).getlength(name)

    def _printed_pt(name, deck):
        """Mirror of gen.title_cls: the largest rung that keeps one line."""
        _ladder = _gv["HDR_STYLES"][deck.get("hdr", "")][0]
        for _pt, _c in _ladder[:-1]:
            if _width(name, _pt) <= _limit(deck) * _gv["TITLE_SAFETY"]:
                return _pt
        return _ladder[-1][0]

    # A deck whose build script overrides the header sizes or padding
    # without declaring a style here is a deck measured as something it is
    # not - which is how AoS shipped 3px deeper than the rest of the set.
    _styles = set()
    for _game in _cat.values():
        for _d in _game["decks"]:
            _styles.add(_d.get("hdr", "\u2014 not published"))
    _unknown = sorted(_styles - set(_gv["HDR_STYLES"]))
    check("every deck names a header style gen.py defines",
          not _unknown, "unknown: %r" % (_unknown,))

    # Titles are sized by measurement now, so they sit wherever they fit
    # rather than in a tidy band well clear of the cut. What keeps them
    # safe is no longer distance from the edge - it is that TITLE_SAFETY
    # is below the reciprocal of the worst Pango-over-PIL ratio actually
    # measured across the set. Re-measure (gen.py says how) and update
    # TITLE_PANGO_RATIO if the fonts or the sizes change.
    _ratio = _gv.get("TITLE_PANGO_RATIO")
    check("TITLE_SAFETY %.3f covers the measured Pango gap of %sx"
          % (_gv["TITLE_SAFETY"], _ratio),
          _ratio is not None and _gv["TITLE_SAFETY"] <= 1.0 / _ratio,
          "needs <= %.4f" % (1.0 / _ratio) if _ratio else "gen.py has no ratio")

    _worst = (0.0, "")
    for _game in _cat.values():
        for _d in _game["decks"]:
            if _d.get("hdr", "") not in _gv["HDR_STYLES"]:
                continue
            _lim = _limit(_d)
            for _c in _d["cards"]:
                _nm = _c["name"]
                _r = _width(_nm, _printed_pt(_nm, _d)) / _lim
                if _r > _worst[0] and _r <= _gv["TITLE_SAFETY"]:
                    _worst = (_r, _nm)
    check("widest safe title is %.1f%% of the line, margin %.1f%% to the %d%% cut"
          % (_worst[0] * 100, (_gv["TITLE_SAFETY"] - _worst[0]) * 100,
             _gv["TITLE_SAFETY"] * 100), True, _worst[1])

    # Every header in the set is one depth, so a row of face-up cards lines
    # up. Two things have to hold for that. Every title must fit on ONE
    # line, because hdr_fit returns gen.HDR_H_MM for one line and a deeper
    # header for two - a title that wraps is a title that breaks the row.
    # And HDR_H_MM must be the DEEPEST style's one-line header, since
    # min-height is a floor: a header whose content does not fit grows past
    # it, which is what AoS's 11.6pt titles did.
    check("gen.py gives every header one depth (HDR_H_MM)",
          "HDR_H_MM = " in _gs and "min-height:%.2fmm' % HDR_H_MM" in _gs)
    _deepest = max((_l[0][0], _s, _k) for _k, (_l, _s, _p) in _gv["HDR_STYLES"].items())
    check("HDR_H_MM is taken from the deepest style (%r, %.1fpt/%.1fpt)"
          % (_deepest[2], _deepest[0], _deepest[1]),
          "HDR_H_MM = max(" in _gs and "HDR_STYLES.values()" in _gs)
    _wrap = []
    for _game in _cat.values():
        for _d in _game["decks"]:
            if _d.get("hdr", "") not in _gv["HDR_STYLES"]:
                continue
            _lim = _limit(_d)
            for _c in _d["cards"]:
                _nm = _c["name"]
                if _width(_nm, _printed_pt(_nm, _d)) > _lim * _gv["TITLE_SAFETY"]:
                    _wrap.append(_nm)
    check("every card title fits on one line at its printed size",
          not _wrap, "%d wrap: %r" % (len(_wrap), _wrap[:3]))

print()
print("BODY TEXT, FOOTERS AND FLAVOUR - ONE OWNER")
# build_aos.py used to set its own body, subhead, footer and flavour sizes
# in its BIG stylesheet while the other three families printed gen.py's
# smaller base set, so a row of face-up cards from different families did
# not read as one game. On 2026-11-03 AoS's sizes became the base ones for
# everybody. The way that comes undone is quiet: a build script setting one
# of these sizes for itself again, or a card hand-rolling an italic flavour
# div instead of using the class. Both are caught here.
_genss = text("generator/gen.py")
_BODY = (('.txt', '9.4pt'), ('.sub', '7.2pt'), ('.ftr', '6.8pt'),
         ('.flavor', '7.1pt'))
_FAMILIES = ("generator/build_bat.py", "generator/build_nap.py",
             "generator/build_aos.py", "generator/build_nrj.py")

for _sel, _pt in _BODY:
    check("gen.py sets %-8s at %s" % (_sel, _pt),
          re.search(re.escape(_sel) + r"\s*\{[^}]*font-size:" + re.escape(_pt),
                    _genss) is not None)
check("flavour is italic and grey, not near-black",
      bool(re.search(r"\.flavor\s*\{[^}]*font-style:italic", _genss)) and
      bool(re.search(r"\.flavor\s*\{[^}]*color:#6f675a", _genss)))

# `.txt.sm` is deliberately NOT scaled with `.txt`: it is the reduced size
# for a secondary line (the NAP Credit note, the NRJ Exhibit Reward), and
# leaving it at 7.4pt is what keeps the Exhibit Reward the same size it was
# signed off at. Asserted so that scaling it becomes a decision rather than
# a tidy-up.
check("gen.py keeps .txt.sm at 7.4pt",
      re.search(r"\.txt\.sm\s*\{[^}]*font-size:7\.4pt", _genss) is not None)

_reowned = []
for _rel in _FAMILIES:
    _src = text(_rel)
    for _sel, _pt in _BODY:
        # `.txt.sm`/`.txt.c` would match `.txt`, so require the brace.
        if re.search(re.escape(_sel) + r"\s*\{[^}]*font-size", _src):
            _reowned.append("%s sets %s" % (_rel.split("/")[-1], _sel))
check("no build script sets a body size for itself",
      not _reowned, repr(_reowned))

_inline = [_r.split("/")[-1] for _r in _FAMILIES
           if "font-style:italic" in text(_r)]
check("no card hand-rolls an italic flavour div",
      not _inline, "still inline in %r" % (_inline,))

_noclass = [_r.split("/")[-1] for _r in _FAMILIES
            if 'class="flavor' not in text(_r)]
check("all four families print flavour through the class",
      not _noclass, "not using it: %r" % (_noclass,))

print()
print("THE RULEBOOKS THE APP SERVES, AND THE RULES IT RESTATES")
# THE RULEBOOK NAMES, kept because two checks further down read them: the
# PDF ladder check just below and the lab's index.html link list.
#
# WHAT USED TO BE HERE was the lab's deployment copies of these PDFs held
# against rules/*.pdf, and it was dropped on 2026-11-25 with the other 70
# lab checks. It outlived them by a few hours for a reason worth writing
# down: IT CAN ONLY FAIL ONCE A RULEBOOK IS REBUILT, and none had been
# rebuilt that day, so it passed the cull by being quiet rather than by
# being live. The first `cd rules && python build.py` after the freeze
# failed it on three books at once.
#
# It cannot come back while the lab is frozen: it asks the frozen
# interface to track every rules edit, which is the one thing the freeze
# says not to do. The ?v= content-hash check near the end of this file is
# NOT the same check - its _books comes out of the mod's save JSON and
# holds the TTS notebook's URLs against the bytes on disk, which is live
# and stays.
#
# AND IT CAUGHT ONE REAL THING ON ITS WAY OUT. rules/AoS_Rulebook.pdf was
# 907 bytes short of its own HTML: the AoS install rule went into
# rules/aos.html earlier on 2026-11-25 and `rules/build.py` was never run
# after it, so the shipped AoS PDF - and the copy the mod serves - printed
# the old "no failed elements" rule. Nothing else checks a PDF against its
# HTML; the comment that used to sit here said so, and said the test is to
# run the build and see whether it rewrites anything. It is still the test.
_books = ("BAT_Rulebook.pdf", "NAP_Rulebook.pdf", "AoS_Rulebook.pdf",
          "NRJ_Campaign_Supplement.pdf")
# THE TWO REROLLS THAT ARE NOT THE BASE GAME'S, AND ARE MEANT.
#
# 20 Strong rerolls MISSES. BAT printed a sentence saying otherwise and
# it was deleted on 2026-11-10; AoS and NRJ print the same shape of
# sentence and Jon kept both, because in those two it is deliberate and
# the models run it. Which makes the sentences load-bearing: a later
# tidy-up pass that removes them for the reason BAT's went would leave
# the books describing a game nothing plays. This is what notices.
_aos_rules = text("rules/aos.html")
_aos_sim = text("simulation/aos.py")
_mode = re.search(r'^REROLL_MODE = "(\w+)"', _aos_sim, re.M)
check("AoS prints the full-element reroll, and aos.py runs it",
      "full reroll of that element" in _aos_rules
      and "roll all of them again" in _aos_rules
      and _mode and _mode.group(1) == "element",
      "rulebook %r, REROLL_MODE %r"
      % ("full reroll of that element" in _aos_rules,
         _mode and _mode.group(1)))
# THE FINALE TAKES UP THE MISSES, which is 20 Strong's rule and is
# what it always did. It used to SAY "any dice you have not applied",
# which is broader than both: a hit that found no Exhibit joins
# `unapplied` but is never thrown again, because the phase loop breaks
# the moment nothing is standing. Measured over 4000 finales, 15,812
# such hits and not one rethrow - so the book was reworded to the
# model rather than the model changed to the book.
#
# The old phrasing must not come back, in either place.
_nrj_rules = text("rules/nrj.html")
_fin_sim = text("simulation/finale.py")
# "ADD MORE IF YOU WANT" IS GONE TOO - 20 Strong already allows it, so
# the page does not restate it. The model still does it, and one line
# says both halves: `rolling = unapplied + take` is the misses rejoined
# PLUS whatever this phase just committed.
#
# WHAT THIS CHECK CANNOT DO is prove the model still commits in the
# second phase. That is behaviour, and this is a text match: a guard
# put on want_dice would leave every string here intact, and a
# mutation that did exactly that went through. The claim is therefore
# limited to what can fail - the two sentences, and the model line
# that answers them - and audit.py is where a behavioural version of
# it would belong.
check("the finale takes up the misses, as nrj.html now says",
      "take up the dice that missed" in _nrj_rules
      and "any dice you have not applied" not in _nrj_rules
      and "add more if you" not in _nrj_rules
      and "rolling = unapplied + take" in _fin_sim,
      "rulebook %r, model %r"
      % ("take up the dice that missed" in _nrj_rules,
         "rolling = unapplied + take" in _fin_sim))
# ...AND BAT NO LONGER PRINTS ONE, which is the other half of the same
# decision: its sentence went because nothing about BAT needed it.
check("...and BAT no longer prints a reroll rule of its own",
      "misses, hits or both" not in text("rules/bat.html"))

# AND EACH ONE IS THE LENGTH IT IS MEANT TO BE.
#
# BAT ran to four pages, the fourth holding eight lines and a footer.
# It is three now, and the thing that got it there is four lines of
# CSS in bat.html's own style block - so the next paragraph anybody
# adds puts it back, silently, in a PDF nobody re-opens. A page count
# is cheap to read and it is the only thing that notices.
#
# A BUDGET, NOT A MEASUREMENT. These are what each book SHOULD be, so
# a book that grows fails and a book that shrinks fails too - the
# second because a page that disappeared is a section that went
# missing, which is worth hearing about.
# NAP WENT TO FOUR ON 2026-11-12 and that is a budget rise, not a leak.
# The Assignment revision added a Demand-reward rule, a reward-timing box, a
# Setback box, an added-die box, a six-row rulings table and a rewritten
# coupon table to a book with about 10mm of blank paper left. Its style block
# is unchanged and still earns its keep - it is buying the fourth page now
# instead of the third, and loosening it costs a fifth.
# AOS WENT TO FOUR ON 2026-11-24, and that is a budget rise too. The
# Assembly redesign replaced the eight standalone Advanced Programs with
# eight double-sided Assemblies and brought three sections the book did not
# have: installing a Program in a Build slot, abandoning an unfinished
# Assembly, and a finale scored on one failed element across three concealed
# stages. It also rewrote setup and the whole endgame. Page 4 comes out about
# three-fifths full of rules the game now has, not of slack: the alternative
# to the fourth page was cutting a rule, not tightening a paragraph.
# AoS AND NRJ CAME DOWN A PAGE EACH on 2026-11-25, which is a budget CUT
# and the first one this file has recorded. Stripping design rationale,
# strategy and card-by-card text took about a page out of each of those two;
# BAT and NAP stayed where they were, NAP because its last column was full
# to the line either way. A shrink still fails here, so the next section
# that goes missing by accident is still caught.
_PAGES = {"BAT_Rulebook.pdf": 3, "NAP_Rulebook.pdf": 4,
          "AoS_Rulebook.pdf": 3, "NRJ_Campaign_Supplement.pdf": 3}
try:
    import pypdf
except ImportError:
    skip("every rulebook is the length it is meant to be",
         "pypdf is not installed")
else:
    _long = []
    for _b, _want in sorted(_PAGES.items()):
        _f = os.path.join(ROOT, "rules", _b)
        if not os.path.exists(_f):
            _long.append((_b, "missing", _want))
            continue
        _got = len(pypdf.PdfReader(_f).pages)
        if _got != _want:
            _long.append((_b, _got, _want))
    check("every rulebook is the length it is meant to be",
          not _long, "%r" % (_long,))
    # BOTH FITS ARE RECORDED WHERE THEY LIVE, because each is a few
    # lines of CSS in one book's own style block and nothing else
    # says why the book is set differently from its neighbours.
    check("...and each squeezed fit is recorded where it lives",
          # BAT's marker changed with the 2026-11-20 rewrite, which is
          # itself the thing worth recording: the book is longer now and
          # the leading came down 1.31 -> 1.25 to hold three pages, with
          # 1.26 measured at four. The phrasing is free; what is checked
          # is that the measurement and the value it produced are both in
          # the book's own style block, where the CSS is.
          "PAGE COUNT IS MEASURED, NOT GUESSED" in text("rules/bat.html")
          and "1.26 with the spacing it had is four pages"
              in text("rules/bat.html")
          and "FOUR PAGES, NOT FIVE" in text("rules/nap.html")
          and "FOUR PAGES, NOT SIX" in text("rules/nrj.html")
          and "line-height: 1.25" in text("rules/bat.html")
          and "line-height: 1.30" in text("rules/nap.html")
          and "line-height: 1.24" in text("rules/nrj.html"))
    # AND THE CREDIT LINE IS IN THE BOOK ITSELF, which nothing had ever
    # asked. .foot spans both columns, and a full-width band needs room
    # under BOTH of them - so when NRJ was squeezed to four pages
    # WeasyPrint had nowhere to put it and dropped it, silently. The
    # page count passed. The HTML still had the line in it, so every
    # check that reads the HTML passed too. What shipped was a rulebook
    # with "not affiliated with Chip Theory Games" nowhere on it.
    _nocredit = []
    for _b in sorted(_PAGES):
        _f = os.path.join(ROOT, "rules", _b)
        if not os.path.exists(_f):
            continue
        _txt = " ".join(" ".join(_p.extract_text()
                                 for _p in pypdf.PdfReader(_f).pages).split())
        if "not affiliated with Chip Theory Games" not in _txt:
            _nocredit.append(_b)
    check("every rulebook PDF carries the Chip Theory credit line",
          not _nocredit, "%r" % (_nocredit,))
    # ...AND NAP KEEPS THE SET'S TYPE SIZE. It fits at 8.3pt too, with
    # the same room to spare, which would have made it the one book
    # set smaller than the other three. The margin does the work
    # instead, and this is what stops a later tidy-up swapping them
    # back the other way.
    check("...and NAP buys its page with margin, not with smaller type",
          "font-size" not in text("rules/nap.html")
          and "margin: 11mm" in text("rules/nap.html"))

    # AND THE SHIPPED PDF IS THE ONE ITS HTML BUILDS. Every check above
    # this one reads the HTML; the PDF is what a player opens, and
    # nothing compared the two. NRJ_Campaign_Supplement.pdf was
    # committed stale on 2026-11-12 - the Tier I split sentence had been
    # corrected in rules/nrj.html the same day and the book in the tree
    # still printed the wrong four numbers. The page count passed,
    # because a stale book is exactly as long as a fresh one.
    #
    # DERIVED FROM nap.LEVELS, both of them, so this cannot be satisfied
    # by a book that prints any ladder but the current one. The strings
    # are what pypdf really extracts from the two places the ladder is
    # printed: NAP's difficulty table, and the Tier I row of the
    # supplement that says what each rung ends up holding.
    # ITS OWN NAME, NOT _stale: the copy check 60 lines below reads a
    # _stale built at line 1894, and a second list by that name here
    # emptied it and made that check pass with the lab's copies really
    # out of date. A check that cannot fail is worse than no check.
    _pdf_stale = []
    _want_pdf = {
        "NAP_Rulebook.pdf": [
            " ".join("%s %d Credits %d" % (l, sn["LEVELS"][l][0],
                                           sn["LEVELS"][l][1])
                     for l in ("Easy", "Standard", "Hard", "Nobulous")),
            "%d, %d, %d or %d of the 6" % tuple(
                sn["LEVELS"][l][1]
                for l in ("Easy", "Standard", "Hard", "Nobulous")),
        ],
        "NRJ_Campaign_Supplement.pdf": [
            "Easy 3 Following and %d base, Standard 3 and %d, Hard 3 and "
            "%d, Nobulous 3 and %d" % tuple(
                max(0, sn["LEVELS"][l][1] - 3)
                for l in ("Easy", "Standard", "Hard", "Nobulous")),
        ],
        # ADDED 2026-11-25, because this book had been stale for hours and
        # nothing here could see it. Only NAP's ladder and NRJ's split were
        # ever extracted from a shipped PDF, so AoS's book was checked for
        # its page count and its fonts and for nothing it says. The install
        # rule had changed in rules/aos.html that morning and the PDF - and
        # the copy the mod serves - still printed the old one.
        #
        # TWO CLAIMS, both derived rather than typed: the deck mix out of
        # simulation/aos.py's LEVELS, which is the four-column table the
        # rules print, and the install condition out of INSTALL_REQUIRES.
        #
        # THE INSTALL CLAIM QUOTES THE WIN SENTENCE, not the phrase on its
        # own, and that is the whole point of its shape. "no failed
        # elements" is not a wording this rule ever had to itself - the
        # Program REWARD genuinely requires a clean run and says so in
        # three places - so a "clean" predicate looking for that phrase
        # alone would pass on prose about a different rule, in the book
        # that had just gone stale. AGENTS.md says to write a claim a NAME
        # cannot satisfy; this is the same trap one step along.
        "AoS_Rulebook.pdf": [
            " ".join(
                ("%s " % l) + " ".join(str(n) for n in sa["LEVELS"][l])
                for l in ("Easy", "Standard", "Hard", "Nobulous")),
            "Come out of the finale with %s and at least 1 Health"
            % {"nocat": "at most one failed element",
               "clean": "no failed elements",
               "any": "any elements failed"}[sa["INSTALL_REQUIRES"]],
        ],
    }
    for _b, _wants in sorted(_want_pdf.items()):
        _f = os.path.join(ROOT, "rules", _b)
        if not os.path.exists(_f):
            _pdf_stale.append("%s is missing" % _b)
            continue
        _txt = re.sub(r"\s+", " ",
                      " ".join(_p.extract_text()
                               for _p in pypdf.PdfReader(_f).pages))
        for _w in _wants:
            if _w not in _txt:
                _pdf_stale.append("%s does not print %r" % (_b, _w))
    check("every shipped rulebook PDF prints the current ladder",
          not _pdf_stale, "; ".join(_pdf_stale[:3]))

# THE RULEBOOKS ARE WELL-FORMED WHERE IT SHOWS. Lists only: a nested
# <li> or text loose inside a list silently renumbers a sequence, and
# tag counts do not catch it because the nesting is balanced.
class _ListShape(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.stack, self.bad = [], []

    def handle_starttag(self, tag, attrs):
        if tag == "li" and self.stack and self.stack[-1] == "li":
            self.bad.append("<li> inside <li> at line %d" % self.getpos()[0])
        if tag in ("ol", "ul", "li"):
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in ("ol", "ul", "li") and tag in self.stack:
            while self.stack.pop() != tag:
                pass

    def handle_data(self, data):
        if (data.strip() and self.stack
                and self.stack[-1] in ("ol", "ul")):
            self.bad.append("loose text in <%s> at line %d: %r"
                            % (self.stack[-1], self.getpos()[0],
                               data.strip()[:40]))


_shape = []
for _g in ("bat", "nap", "aos", "nrj"):
    _lp = _ListShape()
    _lp.feed(text("rules/%s.html" % _g))
    _shape += ["%s.html: %s" % (_g, b) for b in _lp.bad]
check("no rulebook nests a list item or strands text in a list",
      not _shape, "; ".join(_shape[:3]))

_idx = text("playtest/dist/index.html")
_linked = [_b for _b in _books if _b in _idx]

# BAT's two armors are not mirror images of each other, and a HANDOFF
# paragraph claimed they were for three days because nothing held the claim
# against the book. These pin the four facts that distinguish them. If a
# rewording trips one, read rules/bat.html and HANDOFF 9a0000000 before
# "fixing" the check - the rule is the thing being protected, not the
# phrasing.
_bat = text("rules/bat.html")
for _label, _needle in (
        ("a Splice does not chip", "A Splice does not chip"),
        ("a graft has no threshold to meet", "whatever the blow was worth"),
        ("nothing carries past the exposed Splice", "Nothing carries over")):
    check("rules/bat.html still says %s" % _label, _needle in _bat)
# AND IT NO LONGER SAYS THE OPPOSITE. A broken Splice's remainder used to
# run on into the next one and into the core Health behind it; in this
# design a blow either meets the exposed Splice or is wasted, and there is
# nothing behind it to reach.
check("rules/bat.html: no remainder carries on any more",
      "the remainder carries on" not in _bat
      and "whatever survives all five" not in _bat)

# THE TRACK HINT NAMES EVERY CARD THE LAB DRAWS. It stopped naming Health
# on 2026-11-03, when the lab stopped modelling it - which was right then,
# because the wall was 0 on every rung. Both came back on 2026-11-18, so
# the hint has to name it again and has to say the thing that makes it
# different from a Splice: it CHIPS, where a Splice must be met in one blow.
# THE HINT DESCRIBES THE TRACK THE LAB NOW DRAWS: one exposed Splice, met
# in one blow or not at all, with the exposed graft defending and the
# Prototyrant's shared Health behind it. The old hint walked a left-to-
# right track of Health, five Splices and a core dial, none of which
# exists. Both halves are checked, because a hint that says only the first
# is the half-truth that sent a playtester looking for a wall to chip.
_hint = re.search(r'<p class="hint bat-track-hint">([^<]*one blow[^<]*)</p>',
                  _idx)
_js = text("playtest/dist/bat.js")
# ...AND THE SCRIPT THE HINT DESCRIBES IS CACHE-BUSTED. index.html names
# every ?v= token in the lab, so a changed bat.js that keeps its old token
# is a feature that is simply absent in a browser that has been here
# before - which reads exactly like code nobody wrote. AGENTS.md says so.
# ...SO EVERY TOKEN IN THE PAGE MOVES TOGETHER. Pinning one literal here
# meant editing this check on every bump, and it never checked the thing
# that actually bites: index.html names every ?v= in the lab, so a page a
# browser already has pins EVERY asset behind it, however many tokens were
# bumped. One token for the whole page is the rule, and the old value
# cannot survive anywhere in it.
_tokens = set(re.findall(r"\?v=([A-Za-z0-9_.-]+)", _idx))
# AND THE RULES ENGINE LOADS BEFORE THE TABLE THAT READS IT. bat.js reads
# window.BAT_RULES at parse time, so the order is not a style question.

# An Assignment Task prints its Demand half upside down, to be read by
# turning the card over. In a Time Slot the lab turns it for you; in the
# Choose-the-Primary panel you are comparing two cards you have not taken,
# so there is a turn button per card. Three things have to stay true or it
# silently stops working.
_suite = text("playtest/dist/suite.js")
# Only Tasks are two-sided. Opportunities, Setbacks and Final Exams are
# single-faced cards that happen to be landscape too, and turning one would
# just show it upside down.
# Same rule in the Time Slots, where the lab turns a card for you. It used
# to turn ANY card carrying `demandSide`, and that flag means something
# different on an Opportunity - see HANDOFF.

print()
print("NAVIGATION PROMPTS - THE SHARED STEP STRIP")
# BAT had numbered step prompts and the other three screens had nothing.
# steps.js is that strip generalised; each screen passes its own step list.
# A chip's button is a PROXY for a control that already exists on the page,
# so the thing that silently breaks a step is renaming that control.
# The strip's CSS is shared, so no screen may keep a private copy and BAT
# must not still be emitting the old names.
# Every control a step points at by id has to exist, or that step is a
# chip that can never light.
_missing = sorted({_m for _src in (_suite, _app)
                   for _m in re.findall(r'ctrl: ?"#([A-Za-z][\w-]*)"', _src)
                   if ('id="%s"' % _m) not in _idx})

# ---------------------------------------------------------------------------
# THE TTS MOD, which had no checks at all until 2026-11-08 and had drifted
# a whole design generation: lua.lua still dealt a flat-20-Health Tyrant with
# per-difficulty Health, a 12-card Imposter Dossier with a Suspicion row,
# and one AoS Program deck chosen by difficulty instead of a mix of three.
# Two findDeck labels matched nothing in decks.py, so NAP's Time Slots were
# never dealt and Tier II dealt nothing. The notebook is a FOURTH copy of
# the rules after rules/*.html, the lab and the models.
_lua = text("tts/lua.lua")
# CODE ONLY, for the checks that say a thing is NOT in the script. Every
# such check has a comment next to it explaining what used to be there,
# and three of them have failed on their own explanation: the deck-name
# check quoted the literal it forbids, the rulebook check named
# setCustomObject, and the no-labels check wrote "lbl() has gone". A
# comment is not code. This was computed twice further down, both times
# below the checks that needed it first.
_lua_code = chr(10).join(l.split("--")[0] for l in _lua.splitlines())
_mod = text("tts/build_mod.py")
_decks = text("tts/decks.py")
sb_ = py_tables("simulation/bat.py")

# Every deck the script reaches for has to exist, by label, in decks.py.
# COUNTED, not merely compared: this matched findDeck('...') until the
# setups started calling deckOut('...'), and an empty set is a subset of
# anything. A check a RENAME can satisfy is not a check - AGENTS.md says
# so, and this is the fourth time in this repo.
_labels = set(re.findall(r"label='([^']+)'", _decks))
# THREE WAYS A SETUP REACHES A DECK, and this knew one: deckOut takes the
# whole deck, drawOne deals a single card from it, and a tier can pick
# between two with "and 'A' or 'B'". Counting only deckOut made four live
# decks look abandoned.
_want = set(re.findall(r"(?:deckOut|drawOne|takeWhole)\('([^']+)'", _lua))
# A TIER CAN PICK BETWEEN TWO DECKS - "local opps = ... and 'A' or 'B'"
# - and the name only reaches a deck through the variable. Matching the
# and/or on its own read every ternary in the file as a pair of deck
# names, including 'back' or 'front' on the Apprentice button; the
# variable has to actually be handed to one of the three.
for _v, _a, _b in re.findall(
        r"local (\w+) = [^\n]*?and '([^']+)' or '([^']+)'", _lua):
    if re.search(r"(?:deckOut|drawOne|takeWhole)\(%s\b" % _v, _lua):
        _want |= set([_a, _b])
check("tts/lua.lua still asks for its decks by label",
      len(_want) >= 20, "found only %d deckOut labels" % len(_want))
# A bag can hold something that is not a deck - the NAP table overlay
# is a tile - so a name the Lua deals is good if decks.py has it OR
# build_mod.py builds an object with that nickname.
# NICKNAMES FROM THE SAVE, not from build_mod's source. The two
# table overlays are built by one function now - the nickname is
# '%s Table' % game - so a regex over the builder finds neither of
# them, and this went looking for a deck called NAP Table that has
# been shipping for weeks. What matters is what is IN the save.
_objs = set()


def _nicknames(objs):
    for o in objs:
        if o.get('Nickname'):
            _objs.add(o['Nickname'])
        _nicknames(o.get('ContainedObjects', []))


_nicknames(json.load(io.open(os.path.join(ROOT, 'tts',
                                          'NobulousSet.json'),
                             encoding='utf-8'))['ObjectStates'])
check("every deck label in tts/lua.lua exists in tts/decks.py",
      _want <= (_labels | _objs),
      "no such deck or object: %r" % (sorted(_want - _labels - _objs),))
# ...and the other direction, which is the one with teeth now that the
# cards live in boxes: a deck no setup ever names is dead cardboard that
# a player can only reach by opening a box and guessing.
# A deck no setup deals is cardboard a player can only reach by opening
# a bag and guessing - unless it is MEANT to stay there, which lua.lua
# has to say out loud in IN_THE_BAG. The Final Exams are the first: you
# reach them rather than set them up.
_bagged = set()
_inbag = re.search(r"IN_THE_BAG = \{([^}]*)\}", _lua)
if _inbag:
    _bagged = set(re.findall(r"'([^']+)'", _inbag.group(1)))
check("every deck is dealt by a setup, or declared as staying in the bag",
      (_labels - _want) <= _bagged,
      "neither dealt nor declared: %r" % (sorted(_labels - _want - _bagged),))


def _elts(rel, name):
    """Elements of a top-level list literal, unevaluated."""
    with io.open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        tree = ast.parse(f.read())
    for node in tree.body:
        if isinstance(node, ast.Assign) and \
                getattr(node.targets[0], "id", "") == name:
            return node.value.elts
    return []


# ---------------------------------------------------------------------
# THE FOUR BOXES. Every card starts in its game's box and a setup button
# takes out what the printed setup asks for, so a deck in no box is a deck
# no button can reach.
_games = set(re.findall(r"game='([^']+)'", _decks))
_ord = re.search(r"BOX_ORDER = \[([^\]]*)\]", _mod)
_boxes = set(re.findall(r"'([^']+)'", _ord.group(1))) if _ord else set()
check("tts/build_mod.py ships one box per game",
      _boxes == set(["BAT", "NAP", "AoS", "NRJ"]),
      "boxes: %r" % (sorted(_boxes),))
check("every deck in tts/decks.py lands in one of those boxes",
      _games - set(["IMP"]) <= _boxes
      and "grouped['NRJ' if d['game'] == 'IMP' else d['game']].append(" in _mod,
      "homeless: %r" % (sorted(_games - set(["IMP"]) - _boxes),))
check("nothing is parked in the old row that ran off the table",
      "x, z = -34.0, -22.0" not in _mod)

# The two card-index tables are DERIVED from the generators at build time:
# a hand-typed index is the same bug as a hand-typed difficulty number, and
# the finale would deal the wrong domains in silence.
check("tts/build_mod.py reads the Credit Tasks out of build_nap.py",
      "def nap_credit_tasks" in _mod and "'build_nap.py', 'TASKS'" in _mod)
check("tts/build_mod.py reads the Exhibit domains out of build_nrj.py",
      "def exhibit_blocks" in _mod and "'build_nrj.py', 'SCEN'" in _mod
      and "is not contiguous" in _mod)
check("tts/lua.lua uses those tables instead of typing the indices",
      "NAP_CREDIT" in _lua and "EXHIBIT_BLOCK" in _lua
      and "keep[one .. ' ' .. idx[i]]" in _lua
      and not re.search(r"\{\s*17\s*,\s*24\s*\}", _lua))

# ... and the derivation has to agree with the card tables as they stand.
_credit = {}
for _i, _e in enumerate(_elts("generator/build_nap.py", "TASKS"), 1):
    _s = getattr(_e.elts[1], "id", None)
    if _s:
        _credit.setdefault(_s, []).append(_i)
check("build_nap.py carries 4 Task subjects for the 4 Imposter Tasks",
      len(_credit) == 4 and min([len(v) for v in _credit.values()] or [0]) >= 1,
      "subjects: %r" % (sorted(_credit),))
_dom = {}
for _i, _e in enumerate(_elts("generator/build_nrj.py", "SCEN"), 1):
    _dom.setdefault(_e.elts[1].value, []).append(_i)
check("every Exhibit domain is one contiguous block of at least 5",
      len(_dom) == 3 and all(v == list(range(v[0], v[-1] + 1)) and len(v) >= 5
                             for v in _dom.values()),
      "domains: %r" % (dict((k, (v[0], v[-1])) for k, v in _dom.items()),))

# THE FINAL EXAM POOL, which the script now builds instead of asking
# for it by hand - so the book's table and the script's thresholds are
# two copies of one rule and will drift the first time either moves.
#
# The bands are READ OUT OF THE BOOK and the Lua is checked against
# what they say, rather than both being typed here: a check that
# names "4" on both sides of itself cannot tell you the book still
# says 4.
# THE THREE CREDIT BANDS ARE GONE, 2026-11-12, and their absence is
# what this checks now. The pool was 1 card of a subject at 0-1
# Credits in it, 2 at 2-3 and 3 at 4+; it is 1 card from every
# subject, whatever the transcript says. A book that still prints a
# band table, or a script that still has a threshold in it, is an
# owner left behind - and a leftover band in lua.lua would be
# invisible, because examPoolSize would still answer 1 for most
# transcripts and only diverge for a player who had studied.
_pool_tbl = _nap_rules[_nap_rules.find("Building the Final Exam pool"):]
_pool_tbl = _pool_tbl[:_pool_tbl.find("<h3>Resolving")]
_bands = re.findall(r"<tr><td>([^<]+)</td><td>(\d+)</td></tr>", _pool_tbl)
check("rules/nap.html prints no Credit bands for the exam pool",
      not _bands, "bands: %r" % (_bands,))
check("tts/lua.lua's examPoolSize answers 1 at every Credit count",
      "if credits >=" not in _lua
      and "function examPoolSize" in _lua
      and re.search(r"function examPoolSize\(_?\w*\)\n"
                    r"  return EXAM_POOL_PER_SUBJECT\nend", _lua),
      "examPoolSize still reads the Credit count")
# \s+ because this sentence wraps, and a rewrap is not a rules change -
# the lesson the _napflat block further up already paid for twice.
_draw = re.search(r"draw\s+<b>(\d+)</b> Final Exams", _nap_rules)
check("...and draws as many Final Exams as the book says",
      _draw is not None
      and ("EXAM_DRAW = %s" % _draw.group(1)) in _lua,
      "book %r" % (_draw and _draw.group(1),))
# ...AND YOU DO NOT SEE THEM COMING, 2026-11-24. The mod dealt the
# three drawn exams FACE-UP in a row, so the whole exam was on the
# table before the first roll and a player could plan three exams'
# worth of coupons and colours against it. simulation/nap.py never
# could - final_exam resolves the drawn exams in order and spends
# every coupon inside the exam it is sitting - so the face-up row
# was an easier game than the one every published NAP figure was
# measured through, and nothing compared the two. The lab already
# rendered one exam at a time; what this holds together is the book
# and the mod, each read for what it does rather than for a word.
check("the exams are turned over one at a time, in the book and the mod",
      _says("turning each over only as you come to it")
      and "are dealt FACE-DOWN on the" in _lua
      and "rotation = FACEDOWN, smooth = false" in _lua
      and "snapFirst(CARD_NAME['Final Exams'] or 'Final Exam', x1, ROW_CHAR,"
          " FACEDOWN)" in _lua)
# AND THE POOL IS BUILT FROM THE PILE, not from a count the script
# kept for itself. STATE.credits is a total and the pool is per
# subject, so reading it would quietly build the same pool for a
# transcript of four Anatomy Credits and one of four different ones.
check("examDraw builds the pool from the Credit pile, by subject",
      "function examDraw" in _lua
      and "creditTally(" in _lua[_lua.find("function examDraw"):
                                 _lua.find("function startExam")]
      and "NAP_EXAM[s]" in _lua)
# ---------------------------------------------------------------------
# THE CONTROL PANEL HAS TO FIT ON THE CONTROL PANEL. ControlPanel.png is
# 1473x520 and the tile is "Stretch": true, so the tile's local space is
# about z +/-1 and x +/- that times the image aspect. The layout used to
# run from z -4.3 to -0.6 in rows 0.9 apart: four of its five rows hung in
# the air off the top edge of the tile, which is what the mod looked like
# on the table. Width is in thousandths of a local unit.
_png = io.open(os.path.join(ROOT, "images", "ControlPanel.png"), "rb").read(24)
_pw = int.from_bytes(_png[16:20], "big")
_ph = int.from_bytes(_png[20:24], "big")
_half_z = 1.0
_half_x = _half_z * (float(_pw) / _ph)
# find(), not index(): a renamed function should FAIL this check, not
# crash the whole script on a ValueError before the rest of it runs.
_pi = _lua.find("function refreshPanel")
_pan = _lua[_pi:] if _pi >= 0 else ""
_pj = _pan.find("\nfunction nop")
_pan = _pan[:_pj] if _pj >= 0 else _pan
_pan_code = chr(10).join(l.split("--")[0] for l in _pan.splitlines())
# Every row is btn(label, fn, x, z, width), so the triple to check is two
# decimals followed by an integer width. The {r, g, b} colours cannot
# match it: their third number is not an integer.
_rows = re.findall(r"(-?\d+\.\d+),\s*(-?\d+\.\d+),\s*(\d{3,4})", _pan)
# AS MANY POSITIONS AS THERE ARE ROWS. This was `>= 10`, which is the
# count the panel happened to have the day it was written: removing the
# one row that was a label and not a button left nine, and a check that
# the layout had been READ failed because the layout had got smaller.
# Counting what exists is not a claim about anything. What has to be
# true is that the regex found EVERY row - miss one and the bounds
# check below never looks at it, which is how four rows came to hang
# off the top edge of the tile with this check passing.
_sites = re.findall(r"(?m)^[ \t]*btn\(", _pan_code)
check("every button on the panel was read out of tts/lua.lua",
      len(_rows) == len(_sites) and _sites,
      "%d positions for %d btn() calls" % (len(_rows), len(_sites)))
# width is a HALF-extent in thousandths of a local unit, so a button of
# width 1000 is TWO units across. This divided by 2000 and so believed
# every button was half its real size: it passed a panel whose rows
# overlapped on screen. Bounds alone cannot see that anyway - the
# overlapping buttons were all inside the tile - so the overlap itself is
# asserted in tts/test_setup.py, which draws every panel state.
_off = [(x, z, w) for x, z, w in _rows
        if abs(float(z)) > _half_z
        or abs(float(x)) + int(w) / 1000.0 > _half_x]
check("every control-panel button sits on the control panel",
      not _off, "off the tile: %r" % (_off,))
check("tts/lua.lua records what a button width actually means",
      "PANEL_UNIT = 500" in _lua and "HALF-EXTENT" in _lua)
check("tts/test_setup.py asserts the buttons do not overlap each other",
      "def overlaps" in text("tts/test_setup.py")
      and "nothing overlaps" in text("tts/test_setup.py"))
# NOTHING ON THE PANEL IS A LABEL. Jon asked for no labels on it, and
# the reason holds on its own: every other row is a button, so a pale
# unpressable strip in the same grid is a button that is broken. The
# harness draws all eighty states and fails on any row whose click
# function does nothing; this is the source side of it - lbl() is gone,
# and 'nop' is left only on the BAT readout's number, which is not on
# the panel.
# AND THE NOTEBOOK NAMES BUTTONS THAT EXIST. It went on describing
# "Keep 1 / 2 / 3" for a row deleted from the panel, and nothing
# noticed, because the notebook is prose in build_mod.py while the
# panel is code in lua.lua. It matters more now that the panel carries
# no labels: the notebook is the only place the controls are explained,
# so a control it names has to be one you can press.
#
# Every entry in that list is "<name> -- what it does", and the first
# word of the name has to be a word the panel prints on a button. The
# character row's label is built from CHAR_WORD, so those three words
# come from the table rather than from the btn() call.
_told = re.findall(r'(?m)^\s*"(?:\s*\d+\.\s+)?([A-Z][\w /]*?) -- ',
                   text("tts/build_mod.py"))
_words = set()
for _l in (re.findall(r"btn\('([^']*)'", _pan_code)
           + re.findall(r"'([^']+)'",
                        re.search(r"CHAR_WORD = \{([^}]*)\}",
                                  _lua).group(1))):
    _words.update(_l.split())
_ghost = sorted(set(t for t in _told if t.split()[0] not in _words))
check("the notebook explains no button the panel does not draw",
      _told and not _ghost,
      "%d entries, named but not on the panel: %r" % (len(_told), _ghost))
check("the panel draws no labels, only buttons",
      "lbl(" not in _lua_code and "'nop'" not in _pan_code
      and "every row is pressable" in text("tts/test_setup.py"))

# ---------------------------------------------------------------------
# THE TABLE, THE CARD SIZE AND PACK-UP, all reported from the table on
# 2026-11-09.
# A TABLE TTS ACTUALLY HAS. "Table_Rectangle" is not one of them - the
# rectangle table is Table_RPG - and an unknown name does not fall back
# to a default: the load dies on a null reference that says nothing about
# tables. So this checks membership rather than checking that one wrong
# value is absent.
_TABLES = ("Table_RPG", "Table_Square", "Table_Hexagon", "Table_Octagon",
           "Table_Round", "Table_Poker", "Table_Glass", "Table_None",
           "Table_Custom", "Table_Custom_Square")
_table = re.search(r'"Table": "([^"]+)"', _mod)
check("the mod names a table TTS has",
      _table and _table.group(1) in _TABLES and _table.group(1) != "Table_Custom",
      "table is %r" % (_table and _table.group(1),))
# One constant owns how big a card is, and the Lua spaces the rows in
# multiples of it. Thirty position literals is how a layout stops being
# changeable at all.
check("one constant owns how big a card is",
      "CARD_SCALE = " in _mod and "'CARD_W = %.3f' % CARD_W" in _mod)
# A landscape deck carries a SMALLER number for the same physical card,
# because TTS sizes a SidewaysCard by its own aspect: one scale for both
# orientations enlarges the landscape ones by LONG/SHORT rather than
# turning them.
check("landscape decks are scaled to the same card, turned",
      "LAND_SCALE = CARD_SCALE * CARD_SHORT / CARD_LONG" in _mod
      and "LAND_SCALE if d['land'] else CARD_SCALE" in _mod)
check("tts/lua.lua spaces the table in card widths, not literals",
      all(k in _lua for k in ("ROW_CHAR", "ROW_MAIN", "ROW_SIDE",
                              "function col(i)", "CARD_L", "CARD_W")))
# EVERY SPREAD IS SPACED IN CARDS, not in numbers someone liked. These
# three checks matched implementation strings and all three went stale
# the first time the implementation moved, so they are properties now.
# A spread() call spans two lines and contains parentheses of its own,
# so a [^)]*? regex stops at the first one: the first version of this
# inspected ONE of the eight call sites and passed. Take a window after
# each call instead, and count them.
# CODE ONLY. A comment that says "spread() does not know which card it
# will be left holding" is not a call site, and counting it failed this
# check on prose - the same trap the deck-name check fell into, two
# checks down, which is why the stripped copy exists at all.
_code_only = chr(10).join(l.split("--")[0] for l in _lua.splitlines())
_calls = [m.start() for m in re.finditer(r"spread\(", _code_only)]
# A NAMED PITCH COUNTS TOO. What this is against is a bare number
# for the gap between cards in a row; CARD_W + 0.6 is one way to
# say it and AOS_COL - itself CARD_W less a hair - is another. A
# literal is still a literal.
_bare = [_code_only[i:i + 60].split(chr(10))[0]
         for i in _calls
         if not re.search(r"CARD_|_COL|_PITCH|_GAP",
                          _code_only[i:i + 220])]
# THE FLOOR IS AGAINST A REGEX THAT HAS STOPPED MATCHING, and
# nothing else. It was 6, then 5, then 4, and each time a layout
# got better by spreading one row fewer - the Technicians became a
# stack, then the Research Notes did - the number here was wrong
# and the code was right. Counting what happens to exist is not a
# claim about anything; one call proves the regex still finds them.
check("every row is spaced in card widths",
      len(_calls) >= 1 and not _bare,
      "%d call(s), bare: %r" % (len(_calls), _bare))
# TTS drops objects fed to a bag faster than it animates them, which left
# exactly one card on the table after every setup. tts/test_setup.py
# refuses one bag put in N and proves a single pass fails.
_passes = re.search(r"for _ = 1, (\d+) do step\(post\) end", _lua)
check("pack up takes several passes and reports what is left",
      _passes and int(_passes.group(1)) >= 4
      and "Still on the table: " in _lua,
      "passes: %r" % (_passes and _passes.group(1),))
check("tts/test_setup.py models a bag that drops what it is handed",
      "self.lossy" in text("tts/test_setup.py")
      and "dropping 1 in" in text("tts/test_setup.py"))
# The dice are a pool, not a heap: one block per colour, blocks apart.
check("the dice are a 2x2 block per colour in a row under the cards",
      "DICE_Z = " in _mod and "BLOCK_PITCH" in _mod and "OFFS = (" in _mod
      and "ORDER = ('Pink', 'Purple', 'Blue', 'Green', 'Yellow')" in _mod)
# The lower right corner is left empty for exhausted dice, and the
# template draws it, so the two have to agree about where it is.
_tmpl = text("tts/make_template.py")
# A PROPERTY, NOT A SPELLING. This matched the exact import line and
# failed the moment that line grew a second name - which is the trap
# this file keeps relearning: it was testing how the import was
# written, not that the template has no copy of its own.
check("the exhausted corner is declared where the template reads it",
      "EXHAUSTED = (" in _mod
      and re.search("from build_mod import " + chr(92) + "(?[^)]*EXHAUSTED",
                    _tmpl)
      and "EXHAUSTED = " not in _tmpl)
# DRAWN FROM THE SETUPS, not from a second copy of the layout: the
# template presses each setup button through test_setup.py and outlines
# what the script actually dealt. A template typed out separately would
# be wrong the first time a row moved, and wrong silently.
check("the table template runs the mod rather than repeating it",
      "import test_setup" in _tmpl and "T.footprints" in _tmpl
      and "T.start(" in _tmpl)
# The rail's height is not in the save, and four attempts to name it
# failed, so the mat and the boxes are dropped onto it and locked where
# they land.
# The three games with a character to choose can choose it from the
# mat, and there is ONE way to do it. Keep 1/2/3 used to stand beside
# the character button for AoS and the Imposter scenario: it took a
# card out of the stack and left the side to you, which is a second
# chooser that knows nothing about the first, so the panel went on
# naming a character who was no longer on the table. NAP dropped it
# first and the other two have followed it.
check("the mat picks a character for the games that have one",
      "CHAR_DECK = {" in _lua and "CHAR_LIST = {" in _lua
      and "function btnChar" in _lua and "function showChar" in _lua)
check("...and there is only one way to pick one",
      "function keepChar" not in _lua
      and not any(("function keep%d()" % i) in _lua for i in (1, 2, 3, 4, 5)))
# THE TTS CARD AND THE PRINTED CARD ARE THE SAME IMAGE. render_deck
# renders the deck ONCE, turns that one PDF into per-card PNGs, and then
# builds the TTS sheet and the PnP pages from that same list - so the two
# cannot show different cards, only the same cards arranged differently.
# Verified end to end on 2026-11-09 by re-rendering every family into a
# scratch directory: all 52 sheets and all 4 PnP PDFs came back byte for
# byte identical to what ships.
_rd = _gen_src = text("generator/gen.py")
_rd = _gen_src[_gen_src.index("def render_deck"):_gen_src.index("def render_duplex")]
check("the TTS sheet and the PnP are built from the same card renders",
      _rd.count("HTML(string=page(") == 1
      and "sheet.paste(im" in _rd and "paginate(ims" in _rd,
      "render_deck renders %d times" % _rd.count("HTML(string=page("))
# lupa 2.8's Lua 5.5 binding intermittently hands the script an unbound
# function where a bound method belongs, which kills every pack-up step
# and reads exactly like a mod bug. 5.4 is clean; the harness must name
# it rather than take lupa's default.
_ts = text("tts/test_setup.py")
# A CARD IS NOT ITS DECK, and matching one by the other's name fails
# silently. BAT Tier II looked for cards starting "Upgrades " when they
# were called "Upgrade N": it removed nothing and added six
# Modifications to a full deck. Any card prefix must come from
# CARD_NAME, so a literal "<label> " in the Lua is the bug itself.
_cards = dict(re.findall(r"label='([^']+)', card='([^']+)'", _decks))
# CODE ONLY (_lua_code, at the top): the comment explaining this bug
# quotes the very string it warns about, and the first version of the
# check failed on itself.
_lit = [l for l in _cards if (chr(39) + l + " ") in _lua_code]
check("no card is matched by its deck's name",
      not _lit, "literal card prefixes: %r" % (_lit,))
check("tts/decks.py gives nearly every deck a singular card name",
      len(_cards) >= 25, "only %d" % len(_cards))

# AND BAT'S POOL IS CALLED ONE THING IN EVERY PLACE A PLAYER MEETS IT.
# The 16 ordinary cards were UPGRADES until 2026-11-23 and are SPLICES
# now: they come out of the carcass like everything else, and a second
# type name in front of that bought nothing.
#
# FIVE PLACES, because a type name is not one string - it is the card
# BACK a player turns over, the DECK they pick up in TTS, the CATALOG
# the lab reads, the COMPONENT LIST in the book and NRJ's Tier II swap.
# A rename that reaches four of those is the failure worth catching: a
# back printing UPGRADE over a deck called Splices is a table arguing
# with itself, and nothing else here would notice.
_bbat = text("generator/build_bat.py")
check("BAT's ordinary cards are called Splices wherever a player looks",
      "make_back('CardBack_BAT_Upgrade', 'BAT', 'Splice'" in _bbat
      and "label='Splices', card='Splice'" in _decks
      and "deck('Splices', 'BAT_Upgrades_TTS.png'"
      in text("generator/build_catalog.py")
      and "Splice cards (4 each of" in _RULES["bat"]
      and "ordinary Splices from the Splice deck" in _RULES["nrj"]
      # ...AND THE SHEET STEM DID NOT FOLLOW, which is the decision
      # this records rather than an omission: BAT_Upgrades is a
      # filename, and renaming it would re-point every baked art URL
      # in the mod - this back's among them, which NRJ's Modifications
      # deck prints too.
      and "'BAT_Upgrades'" in _bbat
      and "key='BAT_Upgrades'" in _decks,
      "the type is half-renamed, or the sheet stem moved with it")

# AND NOTHING A BAT PLAYER READS MENTIONS TAPPING, because nothing in
# this design taps. Until 2026-11-23 all 16 Splices printed 'Tap to
# use. A tapped Upgrade cannot absorb damage.' - a rule carried over
# from the PRINTED game, where a Rat held its own Upgrades and the
# battle attacked Rats. Here the Prototyrant holds grafts and the
# exposed one blocks an attack whether or not its effect was used, so
# the footer told every player to do something the rulebook does not
# define. Nothing caught it: a phantom rule is spelled correctly, it
# renders, it fits the card, and no other check reads a footer.
#
# THE PREDICATE IS THE WORD, not the constant. 'TAP_FTR not in' is
# satisfied by a rename, and renaming it to 'a tapped Splice' was the
# tempting half-fix - same phantom rule, now reading as live text. So
# this asks the three places a BAT player actually reads: the
# generator's printed strings, the book's body, and the lab's BAT
# modules. \btap\b, so the Tyrant Attack flavor line about holding
# the TAPE while it grows still passes.
#
# THE BOOK'S BODY, not _RULES['bat']: _plain() strips tags but leaves
# what is INSIDE <style>, and the changelog comment up at the top of
# bat.html is where this decision is written down - in the words
# 'nothing taps'. Reading that would make the check fail on its own
# explanation.
_tap = re.compile(r"\btap(s|ped|ping)?\b", re.I)
_bat_body = re.sub(r"<[^>]+>", " ",
                   re.sub(r"<style.*?</style>", " ",
                          text("rules/bat.html"), flags=re.S))
_tap_src = chr(10).join(l.split("#")[0]
                        for l in text("generator/build_bat.py").splitlines())
_taps = sorted(f for f, body in
               (("generator/build_bat.py", _tap_src),
                ("rules/bat.html", _bat_body),
                ("playtest/dist/bat.js", text("playtest/dist/bat.js")),
                ("playtest/dist/bat_rules.js",
                 text("playtest/dist/bat_rules.js")),
                ("playtest/dist/bat_experiments.js",
                 text("playtest/dist/bat_experiments.js")))
               if _tap.search(body))
# ONE SET OF ANGLES FOR ONE DIAL. The save's rotation values and the
# angles the script turns the Chip to were two separate tables that
# could only agree by accident, and did not. build_mod.py owns them and
# generates the Lua copy, so this checks the generator rather than the
# script - where CHIP_FACE no longer appears at all.
check("typing a number over the Chip turns it to that colour",
      "function onObjectNumberTyped" in _lua
      and "CHIP_ANGLE = dict(" in _mod
      and "'CHIP_FACE = { %s }'" in _mod
      and "'CHIP_FACE_Z = %d' % CHIP_FACE_Z" in _mod)
check("tts/test_setup.py pins the Lua version it runs on",
      "from lupa import lua54 as lupa" in _ts
      and "lupa.LuaRuntime(" in _ts and "import lupa" + chr(10) not in _ts)
# NAP'S SECOND DIAL. rules/nap.html offers Increase 1-3 and Reduce 1-3
# and calls Reduce 1 Standard; the panel button is the only way to pick
# one, so a setting the rules have and the button does not is a setting
# nobody can play. Held against the RULES rather than against a copy of
# the list, and the default is held too - it is one index into a table
# and an off-by-one there plays the wrong game without saying so.
_fset = re.search(r"FINF_SET = \{(.*?)\}\s*$", _lua, re.M | re.S)
_fs = re.findall(r"\{'(\w+)', (\d)\}", _fset.group(1)) if _fset else []
_fdef = re.search(r"finf = (\d+)", _lua)
_rule_dirs = set(m.lower() for m in
                 re.findall(r"<h3>(Increase|Reduce) ", _nap_rules))
check("the FINF button offers every setting rules/nap.html prints",
      _fs == [("Increase", "1"), ("Increase", "2"), ("Increase", "3"),
              ("Reduce", "1"), ("Reduce", "2"), ("Reduce", "3")]
      and _rule_dirs == set(["increase", "reduce"]),
      "script %r, rules %r" % (_fs, sorted(_rule_dirs)))
_std = re.search(r"Standard is <b>(Increase|Reduce) (\d)</b>", _nap_rules)
check("it starts on the setting rules/nap.html calls Standard",
      bool(_fdef) and bool(_std) and 1 <= int(_fdef.group(1)) <= len(_fs)
      and list(_fs[int(_fdef.group(1)) - 1]) == list(_std.groups()),
      "starts on %r, rules say %r"
      % (_fs[int(_fdef.group(1)) - 1] if _fs and _fdef else None,
         _std and _std.groups()))
# AND THE TWO DIRECTIONS DO DIFFERENT THINGS WITH THE SAME THREE CARDS.
# Increase shuffles them into the Assignment deck, which can only
# happen before that deck is shuffled; Reduce lays them out to spend.
check("Increase hides the FINF cards in the deck and Reduce lays them out",
      bool(re.search(r"if set\[1\] == 'Increase' then\s*\n\s*"
                     r"moveN\(d, asg, n\)", _lua))
      and "FINF_Z" in _lua and "function finfOut" in _lua
      and bool(re.search(r"step\(function\(\) finfOut\(asg\) end\)\s*\n"
                         r"\s*step\(function\(\) if asg then asg\.shuffle",
                         _lua)),
      "the FINF step is missing, or no longer runs before the shuffle")

# getObjects() EXISTS ON EVERY TTS OBJECT and throws on anything with
# no inside, so `o.getObjects and o.getObjects()` is not a guard in
# front of the call - it IS the call, and the test always passes. It
# was written that way twice and shipped twice: every die threw it on
# load, and the pile counter died on the first die it walked past.
# Asking an unknown object what is inside it goes through contents().
check("nothing tests for getObjects() by calling it",
      "function contents(obj)" in _lua
      and "pcall(function() return obj.getObjects() end)" in _lua
      and "getObjects and " not in _lua.replace(
          chr(96) + 'o.getObjects and o.getObjects()' + chr(96), ''),
      "the not-a-guard is back in tts/lua.lua")
check("the two that walk unknown objects use it",
      bool(re.search(r"function firstCard.*?contents\(obj\)", _lua, re.S))
      and bool(re.search(r"function cardsAt.*?contents\(o\)", _lua, re.S)),
      "firstCard or cardsAt looks inside an object without asking")

# THE NUMBER, NOT THE SENTENCE. This matched "never exceed 4
# Assignments in a row" literally, so changing "a row" to "one row" -
# which says the same thing about the same cap - failed a check about
# how many spaces the lab draws. What has to agree is the CAP: the
# rulebook prints it and ASSIGN_SLOTS is how many spaces that buys.
_cap = re.search(r"never exceed (\d+) Assignments in", _nap_rules)
_slots = re.search(r"^ASSIGN_SLOTS = (\d+)", _lua, re.M)
check("NAP lays as many Assignment spaces as the rulebook allows",
      _cap and _slots and _cap.group(1) == _slots.group(1)
      and "function napSnaps" in _lua and "Global.setSnapPoints" in _lua,
      "rulebook caps at %r, the lab draws %r"
      % (_cap and _cap.group(1), _slots and _slots.group(1)))
check("tts/test_setup.py refuses a save older than lua.lua",
      "older than lua.lua" in text("tts/test_setup.py"))
check("the mat and the bags are settled onto the rail, not placed on it",
      "function settle()" in _lua and "settle()" in _lua.split("function onLoad")[1]
      and "o.setLock(true)" in _lua)
# The panel art is generated now, so the shape the layout depends on has
# a source rather than being a hand-drawn PNG nobody can regenerate.
_panel = text("generator/make_panel.py")
check("the control-panel mat has a source",
      re.search(r"W, H = \d+, \d+", _panel) and "ControlPanel.png" in _panel)
# The size the script draws and the size of the file it drew have to be
# the same, and the layout is measured against the file. Both were
# written as 1473 here and went stale the moment the mat was widened.
_mw, _mh = re.search(r"W, H = (\d+), (\d+)", _panel).groups()
check("the panel mat on disk is the one make_panel.py draws",
      (int(_mw), int(_mh)) == (_pw, _ph),
      "script %sx%s, file %dx%d" % (_mw, _mh, _pw, _ph))


def _lua_rows(name, levels):
    """The named Lua table, level -> tuple of its numbers."""
    win = _lua[_lua.index(name + " = {"):][:500]
    out = {}
    for lv in levels:
        m = re.search(r"%s = \{([^}]*)\}" % lv, win)
        out[lv] = tuple(int(x) for x in re.findall(r"-?\d+", m.group(1))) \
            if m else None
    return out


_lvl = sa["LEVEL_NAMES"]
check("tts/lua.lua offers all four difficulties",
      re.search(r"LEVELS = \{([^}]*)\}", _lua)
      and [s for s in re.findall(r"'([A-Za-z]+)'",
                                 re.search(r"LEVELS = \{([^}]*)\}",
                                           _lua).group(1))] == _lvl)
# BAT_DIFF IS {SPECIMENS, ROUNDS} NOW, and held against batrev - the
# model of record - rather than the retired printed game's three-column
# DIFFICULTY. The old table carried a core Health and a Health, and
# neither exists: the old Tyrant's bulk is its wall and the one Health
# track belongs to the Prototyrant.
check("tts/lua.lua BAT_DIFF is batrev's Specimens and rounds",
      _lua_rows("BAT_DIFF", _lvl) == dict(
          (k, (_brev["SPECIMENS_IN_POOL"][k], _brev["ROUND_LIMITS"][k]))
          for k in _lvl),
      "%r" % (_lua_rows("BAT_DIFF", _lvl),))
# ...AND THE HEALTH LADDER IS THE ONE SOMEBODY MEASURED. It was 0 on every
# rung until 2026-11-18 and this check held it there, because an unmeasured
# non-zero value would have moved every published figure. The four values
# below were chosen against a core x Health grid and confirmed at 20,000
# games a rung - simulation/price_buff_ladder.py - so they are pinned here
# by VALUE: a point of Health is worth two to three of core, and a number
# a test left behind would show up as a win rate nobody published.
_lay = dict((k, v[2]) for k, v in sb_["DIFFICULTY"].items())
check("...and the Tyrant's Health is 1/1/2/2",
      [_lay[k] for k in _lvl] == [1, 1, 2, 2], "%r" % (_lay,))
# ...AND NO RUNG SHIPS A 0, which is the thing Jon asked for: a column of
# four zeros reads as a table nobody filled in, and the card did nothing in
# any game anyone played.
check("...and no rung leaves the Health track card doing nothing",
      0 not in set(_lay.values()), "%r" % (_lay,))
# ...AND THE CORE LADDER STILL LADDERS. This is the real constraint on how
# steep the Health column can get: holding the win rates at Health 3 wants
# a Hard core near 7 and a Nobulous core near 9, and at Health 2 it wants a
# Standard core of 6 - LOWER than Easy's 8. A table whose core column goes
# down as the difficulty goes up is wrong on its face, so the column stops
# at 2 until somebody decides to re-pitch the set.
_core = [sb_["DIFFICULTY"][k][1] for k in _lvl]
check("...and the core Health still rises with the difficulty",
      _core == sorted(_core), "%r" % (list(zip(_lvl, _core)),))
# ...AND THE BOOK'S OWN TABLE IS THE SAME FOUR ROWS. The rulebook is the
# player-facing copy of this ladder and had no check at all: the zeros it
# printed were right by accident of never having been touched.
# BAT'S SETUP TABLE IS TWO COLUMNS NOW - Specimens and rounds - and it is
# held against batrev where the table is read, further up this file. What
# is checked here is that the THREE-column printed table is gone, so the
# retired bat.DIFFICULTY cannot drift back into the book.
_hrows = re.findall(
    r"<tr><td>(?:<b>)?(Easy|Standard|Hard|Nobulous)(?:</b>)?</td>"
    r"<td>(\d+)</td><td>(\d+)</td><td>(\d+)</td></tr>", hb)
check("rules/bat.html no longer prints the retired three-column table",
      not _hrows, "book says %r" % (_hrows,))
check("tts/lua.lua NAP_DIFF matches nap.LEVELS",
      _lua_rows("NAP_DIFF", _lvl) == dict(
          (k, tuple(v)) for k, v in sn["LEVELS"].items()))
check("tts/lua.lua AOS_MIX matches aos.LEVELS",
      _lua_rows("AOS_MIX", _lvl) == dict(
          (k, tuple(v)) for k, v in sa["LEVELS"].items()))

# The finale's starting-exhausted dice are printed in rules/nrj.html and
# nowhere in a model, so the rulebook's own table is the owner.
_tired = {}
for _m in re.finditer(r"<tr><td>(Easy|Standard|Hard|Nobulous)</td>(.*?)</tr>",
                      _nrules, re.S):
    _cells = re.findall(r"<td>(?:&mdash;|(\d+))</td>", _m.group(2))
    if len(_cells) >= 4:
        _tired[_m.group(1)] = tuple(int(x) if x else 0 for x in _cells[:4])
check("tts/lua.lua IMP_TIRED matches the table in rules/nrj.html",
      _tired and _lua_rows("IMP_TIRED", _lvl) == _tired,
      "rulebook says %r" % (_tired,))
# THE HEALTH COLUMN IS THE FIFTH NUMBER IN THE SAME ROWS, so it is read
# from the same table rather than from a second source of truth. The mod
# sets the Health die from it; before 2026-11-16 that die was a literal 5
# and every rung started on it.
_imp_hp = {}
for _m in re.finditer(r"<tr><td>(Easy|Standard|Hard|Nobulous)</td>(.*?)</tr>",
                      _nrules, re.S):
    _cells = re.findall(r"<td>(?:&mdash;|(\d+))</td>", _m.group(2))
    if len(_cells) >= 5:
        _imp_hp[_m.group(1)] = int(_cells[4])
check("tts/lua.lua IMP_HEALTH matches the same table",
      _imp_hp and all(
          re.search(r"IMP_HEALTH = \{[^}]*%s = %d\b" % (_l, _imp_hp[_l]),
                    _lua, re.S) for _l in _lvl),
      "rulebook says %r" % (_imp_hp,))
check("...and the mod sets the Health die from it rather than from a 5",
      "setMarker('Health', sx[1], sz, IMP_HEALTH[STATE.difficulty] or 5)"
      in _lua)

# The notebook quotes the same dials in words, so derive the words. BAT's
# ladder is batrev's Specimens and ROUNDS now - there is no Tyrant Health
# and no third column - so the quoted line is built from those two.
_bat_line = "   ".join("%s %d and %d" % (l, _brev["SPECIMENS_IN_POOL"][l],
                                         _brev["ROUND_LIMITS"][l])
                       for l in _lvl)
check("the TTS notebook prints BAT's Specimens and rounds",
      _bat_line in _mod, "wanted %r" % _bat_line)
# ...AND THE ONE HEALTH IN THE GAME IS THE PROTOTYRANT'S, at the one
# number every rung uses. The notebook used to print a per-difficulty
# Buff HP here and called the card optional; both are retired, and a
# notebook still saying either would teach a rule no card has.
check("...and the Prototyrant's Health, which no rung varies",
      "Health to 12" in _mod
      and "Buff HP" not in _mod and "core Health" not in _mod
      and "Health track at" not in _mod
      and "Health track card is optional" not in _mod
      # ...AND IT DOES NOT TELL THEM TO COUNT ROUNDS ON THE DIAL. The
      # dial is the Health as of 2026-11-21 and the plate beside it
      # stopped being the round count on 2026-11-22, so a notebook
      # saying either is teaching a table that is not there.
      and "Turn the DIAL to your round" not in _mod
      and "Nothing on the table counts" in _mod,
      "the notebook still prints a retired Health stat, or stopped "
      "printing the live one")
_nap_line = "   ".join("%s %d and %d" % (l, sn["LEVELS"][l][0],
                                         sn["LEVELS"][l][1])
                       for l in _lvl)
check("the TTS notebook prints NAP's Credit goal per difficulty",
      _nap_line in _mod, "wanted %r" % _nap_line)
check("the TTS notebook prints AoS's Program mix",
      ", ".join("%s %s" % (l, "-".join(str(n) for n in sa["LEVELS"][l]))
                for l in _lvl) in _mod.replace("\\n\"\n         \"", " "))
# The superseded finale's vocabulary must not come back anywhere in tts/.
check("no tts/ file still describes the superseded finale",
      not any(w in _lua + _mod for w in
              ("Suspicion", "Impostor", "shuffle those 12", "4 HP / 2 STR")))
check("the TTS notebook prints the AoS allocation floor and the Reward brake",
      "MUST RECEIVE AT LEAST ONE" in _mod
      and "ONLY HEALING IN THE GAME" in _mod)

# ------------------------------------------------------------------ the save
# THE BUILT SAVE, NOT THE SCRIPT THAT WRITES IT. Everything above reads
# build_mod.py; these read what it produced, because the bugs they are
# here for were in the output of code that looked right.
_sv = json.loads(text("tts/NobulousSet.json"))

# THE INDEX TABLE, derived here a second time and independently of
# build_mod's own function. An off-by-one in it would hand Theory an
# Engineering exam, and every count on either side would still come
# out right - the harness checks the pool against the same NAP_EXAM
# the script built it from, so it cannot see this at all.
_exsub = {}
for _i, _e in enumerate(_elts("generator/build_nap.py", "EXAMS"), 1):
    _exsub.setdefault(getattr(_e.elts[1], "id", "?"), []).append(_i)
# The whole header line: [^}] cannot cross the nested braces, and
# stopping at the first one read Anatomy and called it the table.
_navx = re.search(r"^NAP_EXAM = \{(.*)\}\s*$", _sv["LuaScript"],
                  re.M)
_lua_ex = dict((k, [int(i) for i in v.split(",")]) for k, v in
               re.findall(r"(\w+) = \{([^}]*)\}",
                          _navx.group(1) if _navx else ""))
check("NAP_EXAM in the save is build_nap.py's own EXAMS table",
      _lua_ex == _exsub and len(_exsub) == 4,
      "save %r vs build_nap.py %r" % (_lua_ex, _exsub))


def _decks_in(objs):
    for o in objs:
        if o["Name"] in ("Deck", "DeckCustom"):
            yield o
        for k in o.get("ContainedObjects") or []:
            for d in _decks_in([k]):
                yield d


def _rsx(t):
    return (round(t["rotX"]), round(t["rotY"]), round(t["rotZ"]),
            round(t["scaleX"], 4))


# A CARD INSIDE A DECK CARRIES ITS OWN ROTATION, AND TTS HONOURS IT.
# Every one of the 30 decks was stored face down with every card inside
# it face up - which is how TTS records a card someone flipped over
# inside a deck - so the first card you dragged off the Assignment deck
# arrived upside down, and only the first, because after that the card
# was already turned. Scale and SidewaysCard were inconsistent the same
# way.
_mix = []
for _d in _decks_in(_sv["ObjectStates"]):
    _kids = _d.get("ContainedObjects") or []
    if not _kids:
        continue
    _want_rsx = _rsx(_d["Transform"])
    for _k in _kids:
        if (_rsx(_k["Transform"]) != _want_rsx
                or _k.get("SidewaysCard") != _d.get("SidewaysCard")):
            _mix.append((_d.get("Nickname"), _k.get("Nickname")))
            break
check("a card drawn off a deck comes out the way the deck looked",
      not _mix, "deck and contents disagree: %r" % (_mix[:4],))

# AND IT SAYS WHICH DECK IT IS FROM AND HOW MANY ARE IN IT. Until
# 2026-11-23 the DECK object's hover read 'BAT  |  16 cards' and every
# card inside it had an empty Description - so the count was there
# while the pile was on the table and gone the moment you picked a
# card up, which is when you want it. Jon's call to put it on the
# card.
#
# COUNTED, NOT MATCHED. The predicate is arithmetic against the save's
# OWN ContainedObjects, so no string satisfies it: a deck that gains
# or loses a card and keeps its old hover fails, and so does a card
# carrying a sibling deck's number. A check that looked for
# "16 cards" would have passed all three.
#
# 'cards?' because BAT's Wake-Up is one card, and its hover said
# '1 cards' from the day the mod was first built until this went in.
_hov_n = re.compile(r"\|\s+(\d+) (cards?)$")


def _hov_says(desc, want):
    """The number AND the plural this hover owes, or None if it owes neither.

    'cards?' alone would read '1 cards' as a one, agree with the pile and
    pass - which is the string that was actually shipping. The plural is
    half of what a player reads, so it is checked, not tolerated.
    """
    m = _hov_n.search(desc or "")
    if not m or int(m.group(1)) != want:
        return False
    return m.group(2) == ("card" if want == 1 else "cards")


def _hov_objs(objs):
    for o in objs:
        yield o
        for k in o.get("ContainedObjects") or []:
            for x in _hov_objs([k]):
                yield x


_hov = []
for _o in _hov_objs(_sv["ObjectStates"]):
    _cards = [k for k in (_o.get("ContainedObjects") or [])
              if k.get("Name") == "Card"]
    # A ONE-CARD DECK IS NOT A PILE. build_mod ships BAT's Wake-Up as a
    # bare CardCustom with nothing inside it, so counting its children
    # gives 0 and this check would have skipped the only object whose
    # hover was WRONG - '1 cards' since the mod was first built. It is
    # its own deck, so the number it owes is 1.
    #
    # CardCustom AND NOT Card: _hov_objs walks INTO the piles, so every
    # card in the set comes round again as _o with no children of its
    # own. Counting those as one-card decks asked all 240 of them to
    # claim '1 card' when what they correctly say is 16.
    _want = len(_cards) if _cards else (
        1 if _o.get("Name") == "CardCustom" else None)
    if _want is None:
        continue
    _nick = _o.get("Nickname") or ""
    if not _hov_says(_o.get("Description"), _want):
        _hov.append((_nick, _o.get("Description"),
                     "holds %d" % _want))
        continue
    for _k in _cards:
        _kd = _k.get("Description") or ""
        # The card has to NAME the deck as well as count it: its own
        # nickname is 'Splice 7' and the label is written nowhere else
        # on the object it hands you.
        if not _hov_says(_kd, _want) or _nick not in _kd:
            _hov.append((_nick, _k.get("Nickname"), _kd))
            break
check("every card says which deck it is from and how many are in it",
      not _hov, "hover disagrees with the pile: %r" % (_hov[:4],))

# A HAND ZONE TAKES A CARD DROPPED IN IT, flips it and carries it to the
# edge of the table. The Assignment spaces nearest the back rail were
# inside one, and a card snapped there vanished to the rail. This is a
# solitaire game; every seat but one is scenery.
check("no seat can take a card off the table",
      _sv.get("Hands", {}).get("Enable") is False,
      "Hands = %r" % (_sv.get("Hands"),))

_tile = [o for o in _sv["ObjectStates"]
         if o["Name"] == "Custom_Tile" and o.get("Nickname") == "NAP Table"]
_tile += [k for o in _sv["ObjectStates"] for k in (o.get("ContainedObjects") or [])
          if k["Name"] == "Custom_Tile" and k.get("Nickname") == "NAP Table"]
check("the NAP overlay is in the save exactly once", len(_tile) == 1,
      "found %d" % len(_tile))
if _tile:
    _t = _tile[0]
    # Type 3 is the rounded tile, and it cut the background away from
    # the four corners of the table. Type 0 is square.
    check("the NAP overlay covers the corners of the table",
          _t["CustomImage"]["CustomTile"]["Type"] == 0,
          "tile type %r" % (_t["CustomImage"]["CustomTile"]["Type"],))
    # It is 56 units wide: hover text on it is in the way of every card.
    check("the NAP overlay has no hover text of its own",
          _t.get("Tooltip") is False, "Tooltip = %r" % (_t.get("Tooltip"),))

# ONE DIAL, ONE SET OF ANGLES, MEASURED. The save's RotationValues and
# the CHIP_FACE the Lua header generates are two consumers of
# CHIP_SEGMENT + CHIP_TRIM; this compares the two consumers, so a trim
# applied to one and not the other fails here rather than at the table.
_chip = [o for o in _sv["ObjectStates"] if o.get("Nickname") == "Chip"]
check("the Chip is in the save exactly once", len(_chip) == 1,
      "found %d" % len(_chip))
check("the Chip's angles are measured off the dial, not written twice",
      "CHIP_SEGMENT = {" in _mod and "CHIP_TRIM = " in _mod
      and "CHIP_ANGLE = dict((c, (360 - a + CHIP_TRIM) % 360)" in _mod)
if _chip:
    _rv = dict((v["Value"], round(v["Rotation"]["y"]))
               for v in _chip[0].get("RotationValues") or [])
    _att = re.search(r"ATTENTION = \(([^)]*)\)", _mod)
    _cols = re.findall(r"'([^']+)'", _att.group(1)) if _att else []
    _face = re.search(r"CHIP_FACE = \{([^}]*)\}", _sv["LuaScript"])
    _lf = dict((m[0], int(m[1])) for m in
               re.findall(r"(\w+) = (-?\d+)", _face.group(1))) if _face else {}
    check("typing a number over the Chip turns it to the same angle the"
          " save would",
          len(_rv) == 5 and len(_cols) == 5
          and all(_rv.get(i + 1) == _lf.get(c)
                  for i, c in enumerate(_cols)),
          "save %r vs script %r" % (_rv, _lf))
    # AND THE SAME WAY UP. Typing a number uses the save's z; the setup
    # uses the script's. They were 180 and 180 and both wrong; they
    # could as easily be 0 and 180 and only one wrong, which is a dial
    # that reads correctly until you press Set up NAP.
    _rz = set(round(v["Rotation"]["z"])
              for v in _chip[0].get("RotationValues") or [])
    # WHICH SIDE OF THE TOKEN, not only which angle. A Custom_Token with one
    # image is an extruded disc with that art on top and the same art
    # MIRRORED underneath, so rotZ 180 shows a dial whose colours run the
    # other way round - it still looks like a dial, which is why it read as
    # a trim that had drifted rather than as the wrong face. The face has
    # one owner in build_mod.py and the Lua copy is generated from it;
    # nothing may write the number down a second time.
    check("the dial's face has one owner",
          bool(re.search(r"^CHIP_FACE_Z = \d+$", _mod, re.M))
          and not re.search(r"^CHIP_FACE_Z = ", _lua, re.M)
          and bool(re.search(r"^CHIP_FACE_Z = \d+$",
                             _sv["LuaScript"], re.M)),
          "tts/lua.lua writes CHIP_FACE_Z down itself, or the header does not")
    _lz = re.search(r"^CHIP_FACE_Z = (\d+)$", _sv["LuaScript"], re.M)
    check("the Chip's numbers and the setup agree which way up it is",
          len(_rz) == 1 and _lz and int(_lz.group(1)) in _rz,
          "save z %r vs script %r" % (sorted(_rz),
                                      _lz and _lz.group(1)))

# EVERY CHOOSABLE CHARACTER COMES FROM THE SCRIPT THAT PRINTS IT.
# All three decks are duplex, fronts over backs, so a hand-typed list
# in the mod is a list that can name the wrong character on the wrong
# side of the right card - and nothing at the table would say so,
# because every card of a deck looks like every other until you read
# it.
#
# THE IMPOSTERS CARRY THEIR SIDE LETTER. The other two decks are six
# and six people on three cards; the five Imposters print two
# abilities each under one name, so without the A or the B the panel
# would offer "The Archivist" twice.
_chars = [("APPRENTICE", "build_nap.py", "APPS", None),
          ("TECHNICIAN", "build_aos.py", "TECHS", None),
          ("IMPOSTER", "build_nrj.py", "IMPOSTERS", 2)]
for _var, _script, _tab, _sfx in _chars:
    _src = [e for e in _elts("generator/" + _script, _tab)]
    _names = [e.elts[0].value if _sfx is None
              else "%s %s" % (e.elts[0].value, e.elts[_sfx].value)
              for e in _src]
    _paired = [x for p in zip(_names[0::2], _names[1::2]) for x in p]
    _row = re.search(r"^%s = \{(.*)\}$" % _var, _sv["LuaScript"], re.M)
    _latable = re.findall(r"\{card = (\d+), back = (\w+), name = '([^']+)'\}",
                          _row.group(1) if _row else "")
    check("the panel's %s are %s's, in card and side order"
          % (_var.title() + "s", _script),
          [(int(k), b == "true", n) for k, b, n in _latable] ==
          [(i // 2 + 1, bool(i % 2), n) for i, n in enumerate(_paired)],
          "script %r vs %s %r" % (_latable, _script, _paired))
    check("...and the mod does not write the %s list down a second time"
          % _var.title(),
          ("%s = {" % _var) not in _lua)
check("one function reads all three of them out of the generators",
      "def duplex_characters" in _mod and "CHARACTERS = [" in _mod
      and _mod.count("duplex_characters(") == 2)

# THE STAGING BAND IS BELOW EVERY ROW. A deck being built is held in
# the air over it, and a card the bag will not take falls out of that
# air. It used to be held over ROW_TIER, which is where AoS spreads the
# Research Notes, so the card landed in the middle of a row and read as
# one the setup had dealt - that is what Jon found. putHome keeps
# trying, so this is the margin rather than the mechanism, but a margin
# that overlaps the thing it is protecting is not one.
_hdr = _sv["LuaScript"]
_num = lambda k, s=None: float(re.search(
    r"^%s = (-?[\d.]+)" % k, s or _hdr, re.M).group(1))
_feltz0 = float(re.search(r"FELT = \{[^}]*z0 = (-?[\d.]+)", _hdr).group(1))
_offz = _feltz0 + 2.0
check("the staging band is below every row a setup deals on",
      "OFF_Z = FELT.z0 + 2.0" in _lua and "14, OFF_Z}" in _lua
      and _offz + 1.0 < _num("ROW_TIER") - _num("CARD_L") / 2.0,
      "staging at z %.2f, the lowest row reaches %.2f"
      % (_offz, _num("ROW_TIER") - _num("CARD_L") / 2.0))

# AND NO PARKING SPOT IS THE DROP POINT. Every takeObject in the script
# puts its card down at OFF on the way to wherever it is going, so a
# deck parked there collects them: OFF was pad(3) exactly, and AoS
# parked the Specialized Programs on it. This check used to assert the
# string "OFF = {0, 14, OFF_Z}", which is to say it held the bug in
# place and called it a check.
_pitch = _num("CARD_W") + 1.0
_pads = int(re.search(r"^BAND_PADS = (\d+)", _lua, re.M).group(1))
_offx = -(_pads / 2.0) * _pitch
_padx = [(i - _pads / 2.0) * _pitch for i in range(1, _pads + 1)]
check("pad() is called with every slot it has and no more",
      sorted(set(int(i) for i in re.findall(r"\bpad\((\d)\)", _lua)))
      == list(range(1, _pads + 1)),
      "pad() called with %r for %d slots"
      % (sorted(set(re.findall(r"\bpad\((\d)\)", _lua))), _pads))
check("no staging pad is within a card of the point cards are taken to",
      all(abs(x - _offx) >= _num("CARD_W") for x in _padx),
      "OFF at x %.2f, pads at %s" % (_offx, [round(x, 2) for x in _padx]))

# AND EACH RAT'S FOUR DICE FIT BESIDE IT.
#
# A slot is 13.88 wide, a Lab Rat is a landscape card 8.21 across and a
# die is 1.62 at DIE_SCALE, so the 2x2 block has 5.67 of felt to live
# in and two tenths of clearance against the card. That is the whole
# budget: a change to the pitch, or one more press of the scale key,
# puts dice on the cards - and a die ON a Rat is how a BANISHED die is
# recorded, so an overlap here is not untidiness, it is a die the
# battle will refuse to sweep.
#
# THE BLOCK MOVED BESIDE THE CARD on 2026-11-21, when the Rats became a
# row. There are 1.26 units between a Rat's bottom edge and the top of
# the row below, and a die is 1.62 across; under the card there is no
# longer anywhere to put one.
#
# EVALUATE THE SCRIPT'S OWN PLACING. An earlier version matched
# "batRatZ(r) - <rest of line>" and evaluated the rest as the drop,
# which reads `- CARD_W / 2 - 0.9` as 2.04 where the Lua means 3.84 -
# so it failed a mutation for the wrong reason and would have passed
# the next one. The functions are run here instead.
_die_half = 0.45 * _num("DIE_SCALE", _mod)
_cols = re.search(r"^BAT_RAT_DICE = \{([^}]*)\}", _lua, re.M)
_colours = re.findall(r"'([^']+)'", _cols.group(1) if _cols else "")
_nrats = int(re.search(r"^BAT_ROWS = (\d+)", _lua, re.M).group(1))


def _lua_fn(name, arg, **env):
    """One of lua.lua's one-line geometry functions, as a Python one."""
    m = re.search(r"function %s\(%s\)\s+return (.+?)\s+end"
                  % (name, arg), _lua, re.S)
    if not m:
        return None
    env.update({"__builtins__": {}})
    body = m.group(1).replace("#BAT_RAT_DICE", str(len(_colours)))
    return lambda v: eval(body, env, {arg: v})            # noqa: S307


def _lua_fn2(name, **env):
    """...and one of the two-argument ones, which have a body.

    STILL THE SCRIPT'S OWN ARITHMETIC, not a copy of it here. The
    bodies are a `local` or two and a `return`, and nothing else; a
    function that grows a branch stops matching and comes back None,
    which the check below fails on rather than quietly skipping.
    """
    m = re.search(r"function %s\((\w+), (\w+)\)\n(.*?)\nend"
                  % name, _lua, re.S)
    if not m:
        return None
    a1, a2, body = m.group(1), m.group(2), m.group(3)
    lines = [ln.strip() for ln in body.split("\n") if ln.strip()]
    if not lines[-1].startswith("return ") or not all(
            ln.startswith("local ") for ln in lines[:-1]):
        return None
    env.update({"__builtins__": {}, "math": math})

    def call(v1, v2):
        loc = {a1: v1, a2: v2}
        for ln in lines[:-1]:
            nm, expr = ln[len("local "):].split("=", 1)
            loc[nm.strip()] = eval(expr.strip(), env, loc)   # noqa: S307
        return eval(lines[-1][len("return "):], env, loc)    # noqa: S307
    return call


# THE SCRIPT'S OWN CONSTANTS, then its own functions on top of them.
# BAT_DIE_OUT and BAT_RAT_PITCH are expressions rather than literals, so
# they are evaluated here too: a check that re-derived either of them
# would pass whatever lua.lua said.
_dieout = re.search(r"^BAT_DIE_OUT = (.+)$", _lua, re.M)
_env = dict(CARD_L=_num("CARD_L"), CARD_W=_num("CARD_W"),
            DIE_SCALE=_num("DIE_SCALE"),
            BAT_RAT_IN=_num("BAT_RAT_IN", _lua),
            BAT_RAT_PITCH=None, BAT_DIE_PITCH=_num("BAT_DIE_PITCH", _lua),
            BAT_DIE_COLS=_num("BAT_DIE_COLS", _lua), ROW_CHAR=_num("ROW_CHAR"))
_env["BAT_DIE_OUT"] = (eval(_dieout.group(1), dict(_env, __builtins__={}))
                       if _dieout else None)
_pitchm = re.search(r"^BAT_RAT_PITCH = (.+)$", _lua, re.M)
_feltx1 = float(re.search(r"FELT = \{[^}]*x1 = (-?[\d.]+)", _hdr).group(1))
_feltx0 = float(re.search(r"FELT = \{[^}]*x0 = (-?[\d.]+)", _hdr).group(1))
_env["FELT"] = type("F", (), {"x0": _feltx0, "x1": _feltx1})
_env["BAT_RAT_PITCH"] = (eval(_pitchm.group(1), dict(_env, __builtins__={}))
                         if _pitchm else None)
_mid = _lua_fn("batRatMid", "", **_env)
_env["batRatMid"] = (lambda: _mid(None)) if _mid else None
_slot = _lua_fn("batRatSlot", "i", **_env)
_env["batRatSlot"] = _slot
_ratX = _lua_fn("batRatX", "i", **_env)
_ratZ = _lua_fn("batRatZ", "_", **_env)
_dieX = _lua_fn2("batDieX", **_env)
_dieZ = _lua_fn2("batDieZ", **_env)
check("the script's dice-block geometry could be read at all",
      None not in (_mid, _slot, _ratX, _ratZ, _dieX, _dieZ) and _colours,
      "mid %s slot %s ratX %s ratZ %s dieX %s dieZ %s colours %r"
      % (_mid is not None, _slot is not None, _ratX is not None,
         _ratZ is not None, _dieX is not None, _dieZ is not None, _colours))
if None not in (_mid, _slot, _ratX, _ratZ, _dieX, _dieZ) and _colours:
    _n = len(_colours)
    _rats = range(1, _nrats + 1)
    _dice = [(r, i, _dieX(r, i), _dieZ(r, i)) for r in _rats
             for i in range(1, _n + 1)]
    # ON A CARD IS WHAT BANISHED MEANS, so a die that overlaps ANY Rat
    # - its own or its neighbour's - is a die the sweep leaves behind.
    _hit = [(r, i, q) for r, i, x, z in _dice for q in _rats
            if abs(x - _ratX(q)) < _num("CARD_L") / 2.0 + _die_half
            and abs(z - _ratZ(q)) < _num("CARD_W") / 2.0 + _die_half]
    check("every die in a Rat's block clears every Rat card on the table",
          not _hit, "overlaps: %r" % (_hit[:3],))
    # ...AND SITS WITHIN ITS RAT'S OWN SLOT, so a block reads as
    # belonging to the card beside it rather than to the next one.
    _stray = [(r, i, round(x - _slot(r), 2)) for r, i, x, _z in _dice
              if abs(x - _slot(r)) > _env["BAT_RAT_PITCH"] / 2.0]
    check("...and inside its own Rat's slot",
          not _stray, "strays: %r" % (_stray[:3],))
    # ...AND ON THE CARD'S OWN DEPTH, which is what makes the block read
    # as that Rat's: a block floated above or below the row would clear
    # every card and belong to none of them.
    _zs = sorted(set(round(z, 3) for _r, _i, _x, z in _dice))
    check("...on the Rat row's own depth, not above or below it",
          all(abs(z - _num("ROW_CHAR")) + _die_half
              <= _num("CARD_W") / 2.0 for z in _zs),
          "dice at z %r on a row at %.2f" % (_zs, _num("ROW_CHAR")))
    # ...AND NO TWO DICE TOUCH.
    _close = [(a[:2], b[:2]) for n, a in enumerate(_dice) for b in _dice[n + 1:]
              if abs(a[2] - b[2]) < 2 * _die_half
              and abs(a[3] - b[3]) < 2 * _die_half]
    check("...and no two dice in a block touch each other",
          not _close, "touching: %r" % (_close[:3],))
    # AND THE WHOLE ROW IS ON THE FELT, at both ends. The row is four
    # slots of card-and-block and the felt is 56.5: the margin is 1.5 at
    # each end, which is what batRatMid buys by centring the row on what
    # a slot actually holds rather than on the slot.
    _edges = (min(_ratX(r) - _num("CARD_L") / 2.0 for r in _rats),
              max(x + _die_half for _r, _i, x, _z in _dice))
    check("...and the row of Rats and their dice is on the felt",
          _edges[0] > _feltx0 and _edges[1] < _feltx1,
          "row runs %.2f..%.2f, felt %.2f..%.2f"
          % (_edges[0], _edges[1], _feltx0, _feltx1))
    check("...with the same margin at each end, which is what centres it",
          abs((_edges[0] - _feltx0) - (_feltx1 - _edges[1])) < 0.02,
          "margins %.2f and %.2f"
          % (_edges[0] - _feltx0, _feltx1 - _edges[1]))

# THE COLOURS ARE THE DICE THAT EXIST, one row's worth of each. The
# pool is four Purple, four Blue, four Green and four Yellow and there
# are four Rats, so the row is the whole supply dealt out - name a
# fifth colour, drop one, or rename a die in dice_objects.json and the
# setup moves nothing while the message still promises a full row.
_pool = {}
for _o in _sv["ObjectStates"]:
    if _o["Name"] == "Custom_Dice":
        _pool[_o["Nickname"]] = _pool.get(_o["Nickname"], 0) + 1
_supply = sorted(n for n, k in _pool.items() if k == _nrats)
check("a Rat's dice are the colours the mod really has, one per Rat",
      sorted(_colours) == _supply and len(_colours) == 4,
      "row %r, dice with %d copies %r" % (_colours, _nrats, _supply))

# THE TWO NUMBERS SHARE A ROW, and it is a tight one. The dial is the
# Prototyrant's Health and the plate beside it is the rounds left, and
# they stand between the Prototyrant's discard on their left and the
# middle's first column on their right - with the dice tray above them
# and the exhausted band below. Six things in one strip is exactly the
# sort of arithmetic that silently stops being true.
#
# READ THE SCRIPT'S OWN PLACING, not a copy of it. Recomputing the
# right answer here and comparing it with itself is a check that passes
# whatever lua.lua says - which is what the first draft of this did,
# and moving the plate onto the staging band did not trouble it.
_rhw = _num("BAT_READOUT_HW")
_col = _num("CARD_W") - 0.02
_boxhw = (_col - 0.25) / 2.0
_rx = _num("BAT_READOUT_X", _lua)
_dialx = _num("BAT_CHIP_X", _lua)
_deckx = _num("BAT_DECK_X", _lua)
_midx = -_col + (3 - 1) * _col          # batRightX(3) is not what bounds it
_mid1 = -_col                            # ...batRightX(1) is
check("the round counter clears the Prototyrant's discard on its left",
      _rx - _rhw >= -_deckx + _boxhw + 0.2,
      "plate starts %.2f, the discard ends %.2f"
      % (_rx - _rhw, -_deckx + _boxhw))
check("...and the dial clears the plate and the middle column",
      _dialx - 1.1 >= _rx + _rhw + 0.5 and _dialx + 1.1 <= _mid1 - _boxhw,
      "plate ends %.2f, dial %.2f..%.2f, the middle starts %.2f"
      % (_rx + _rhw, _dialx - 1.1, _dialx + 1.1, _mid1 - _boxhw))
# AND BOTH ARE ON THE BOTTOM CARD ROW, not in the dice band under it.
# They stood in that band until 2026-11-21, because BAT had four rows
# of cards above it and nothing else was clear; the band is the
# exhausted corner's now, and a disc parked in it reads as a die.
# BY NAME, NOT BY NUMBER. BAT's three card rows ARE the shared ones
# now - ROW_MAIN, ROW_SIDE and ROW_TIER, which build_mod.py derives
# from the felt - so the table holds three names and no literals, and
# the thing worth checking is that it still does.
_rowz = re.search(r"^BAT_ROW_Z = \{([^}]*)\}", _lua, re.M)
_rows = [v.strip() for v in (_rowz.group(1).split(",") if _rowz else [])]
check("...and both stand on the bottom card row, clear of the dice band",
      _rows == ["ROW_MAIN", "ROW_SIDE", "ROW_TIER"]
      and "BAT_CHIP_Z = ROW_TIER" in _lua
      and "BAT_READOUT_Z = BAT_CHIP_Z" in _lua
      and _num("ROW_TIER") - _num("CARD_L") / 2.0
      >= float(re.search(r"^EXHAUST_Z = \{(-?[\d.]+)",
                         _sv["LuaScript"], re.M).group(1)) - 0.01,
      "BAT rows %r, ROW_TIER %.2f" % (_rows, _num("ROW_TIER")))
check("...and the exhausted corner's ends are measured, not typed",
      "BAT_EXHAUST_X0 = batGraftShowX() - BAT_SHOW_HW" in _lua
      and "BAT_EXHAUST_X1 = FELT.x1 - 0.75" in _lua)
check("the readout's width has one owner",
      bool(re.search(r"^READOUT_HW = ", _mod, re.M))
      and not re.search(r"^BAT_READOUT_HW = [\d.]", _lua, re.M)
      and bool(re.search(r"^BAT_READOUT_HW = [\d.]+$",
                         _sv["LuaScript"], re.M)))
# AND THE PLATE IS THE DIAL'S OTHER FACE, 2026-11-22. They were two
# numbers for a day - the Health and the rounds left - and Jon took the
# round count off the table, so the plate shows what the disc reads.
#
# TWO OBJECTS SHOWING ONE NUMBER IS ONLY SAFE WHILE THERE IS NO PATH
# THAT WRITES ONE ALONE, which is the invariant here and the reason the
# old arrangement was worth a check of its own in the other direction.
# So: dialSet draws the plate, drawReadout reads STATE.dial and nothing
# else, the plate's buttons go through dialSet, and no clock survives.
_dialset = re.search(r"function dialSet\(.*?\nend", _lua, re.S).group(0)
_drawro = re.search(r"function drawReadout\(\).*?\nend\n",
                    _lua, re.S).group(0)
check("the plate is a face of the dial, not a number of its own",
      "drawReadout()" in _dialset
      and "STATE.dial" in _drawro
      and "STATE.clock" not in _drawro
      and "function dialPlus() dialSet(" in _lua
      and "function dialMinus() dialSet(" in _lua
      and "btn('-', 'dialMinus'" in _lua
      and "btn('+', 'dialPlus'" in _lua
      # ...AND THE CLOCK IS GONE FROM THE CODE, not merely unused: a
      # clockSet still sitting there is a second writer waiting to be
      # called. The comments that explain the removal are allowed to
      # name it, which is why this reads the stripped source.
      and not any(n in _lua_code for n in
                  ("STATE.clock", "clockSet", "clockPlus", "clockMinus",
                   "CLOCK_MAX")),
      "the plate and the dial can still disagree")
# ...AND NOTHING COUNTS THE ROUNDS, so both the setup and the battle
# have to SAY that in so many words. The rule did not go away with the
# counter - "if its last Splice is still standing when your difficulty's
# rounds are used up, it finishes the job and the Rats lose" - so a table
# that shows no count and says nothing about one is a table that has
# quietly dropped a losing condition.
check("...and the table says out loud that nothing counts the rounds",
      _lua_code.count("keep the count yourselves") == 2
      and "rounds are used up" in _RULES["bat"]
      and "the Rats lose" in _RULES["bat"],
      "the round count vanished without the table admitting it")
check("...and the plate is named for the number it carries",
      "READOUT_NAME = 'Health Readout'" in _lua
      and '"Nickname": "Health Readout"' in _mod
      and "Round Counter" not in _lua and "Round Counter" not in _mod)

# THE DIE THAT MARKS THE ACTIVE RAT IS THE ONE THE RULEBOOK NAMES.
#
# setupBAT laid the Health die on the Rat's corner and nothing compared
# it with the book, because the harness only asked whether that corner
# was a snap point and the rulebook checks are all about numbers. This
# reads the die out of the sentence that defines it.
#
# RE-ANCHORED 2026-11-16, from the components list to the Splice Phase.
# The components bullet used to name the die and say what it was for;
# all four books now print one shared From-20-Strong wording that lists
# the stat dice and the Chip and says nothing about what each game does
# with them, because a future revision may use the ones a game does not.
# The die is still named twice in bat.html - when it is placed and when
# it moves - and the second check holds those two against each other, so
# the cross-check this had before the move survives the move.
_bat_html = text("rules/bat.html")
# THE VERB IS NOT THE RULE (2026-11-24). This read 'put the <b>X die</b>
# on it' and went None the moment the Splice Phase step was reworded to
# 'place', which took both checks below down with it and reported the
# rulebook as naming no die at all - a scary failure for a line that still
# names the Recovery die as plainly as before. Only the die name is the
# claim, so either verb is accepted; the battle's own sentence (checked
# just below) is what holds the two halves of the book together.
_marks = re.search(r"(?:put|place) the <b>(\w+) die</b> on it", _bat_html)
_mark_src = re.search(r"setMarker\('(\w+)', batMarkX\(1\), batMarkZ\(\)[,)]",
                      _lua)
check("the mod marks the active Rat with the die rules/bat.html names",
      _marks and _mark_src and _marks.group(1) == _mark_src.group(1),
      "rulebook %r, setup %r"
      % (_marks and _marks.group(1), _mark_src and _mark_src.group(1)))
check("...and the battle moves the same die the Splice Phase placed",
      _marks and ("move the <b>%s die</b> to it" % _marks.group(1))
      in _bat_html,
      "the Splice Phase places %r" % (_marks and _marks.group(1),))
check("...and the harness checks which die is really on the card",
      "and the Recovery die is the one on the first Rat" in _ts
      and "and no Health die is sitting on any Rat" in _ts)

# EVERY DECK THAT WAITS IN A BOX HAS SOMETHING THAT TAKES IT OUT.
#
# IN_THE_BAG names the decks no SETUP deals, because they belong to a
# part of the game you reach rather than one you set up: the Final
# Exams, the Tyrant Attacks, the Health track card and the Advanced
# Programs. Every one of them now has a finale that deals it - the
# Health track card was the last holdout, and the Tyrant battle now puts
# it out with the Health die standing on the difficulty's number. So
# the list is empty, which is a stronger claim than the one this
# made while the card was still called optional.
_bagged = re.findall(r"'([^']+)'",
                     re.search(r"IN_THE_BAG = \{([^}]*)\}",
                               _lua, re.S).group(1))
_dealt_by_finale = [d for d in _bagged
                    if re.search(r"deckOut\('%s'" % re.escape(d), _lua_code)]
# ...EXCEPT THE ONE THE PLAYER FETCHES. The Wake-Up card belongs in a
# packet three cards deep, row 1 is full at Tier III, and TTS deck
# surgery at setup is the least reliable thing in lua.lua - so the setup
# tells the player to build the clock by hand instead of guessing at a
# put that may not land. It is named here so that staying in the bag is a
# DECISION rather than a deck somebody forgot, and the setup has to say
# so out loud.
BY_HAND = {"Wake-Up"}
check("every deck that waits in a box is dealt by a finale or handed "
      "to the player in words",
      sorted(set(_bagged) - set(_dealt_by_finale) - BY_HAND) == [],
      "never dealt: %r"
      % (sorted(set(_bagged) - set(_dealt_by_finale) - BY_HAND),))

# AND THERE IS NO RETIRED CARD IN THE BAG ANY MORE. A third set sat
# here for a day - RETIRED = {"Health Track"} - for a printed card the
# table had no job for: the dial took its number on 2026-11-21 and the
# rulebook dropped the component on 2026-11-22, but the sheet was still
# rendered and the deck was still in the box, so the mod had to tell a
# player who fetched it what carried the number instead.
#
# JON RETIRED THE PRINT ON 2026-11-23, so the whole chain is gone and
# this check is the stronger claim: not that the card is explained, but
# that no registry makes one.
#
# A PREDICATE SIX FILES WIDE, because a removal like this half-happens.
# A deck dropped from tts/decks.py while build_bat.py still renders the
# sheet leaves a PnP page no rulebook mentions; a sheet dropped while
# the manifest stands leaves the mod baking an art URL deploy.py never
# writes, and TTS answers that 404 by opening the Custom Tile dialog
# over a blank face - which reads as a broken object, not a missing
# file. So every file that named it is asked, in its CODE and not in
# its prose: each one carries a comment saying what left and why.
_track_homes = (("generator/build_bat.py",
                 ("BAT_HealthTrack", "TRACK_CSS", "TRACK_GREEN")),
                ("generator/pack.py", ("BAT_HealthTrack",)),
                ("generator/build_catalog.py", ("BAT_HealthTrack",)),
                ("tts/decks.py", ("BAT_HealthTrack", "Health Track")))
_track_left = sorted(
    "%s: %s" % (f, n) for f, names in _track_homes for n in names
    if n in chr(10).join(l.split("#")[0]
                         for l in text(f).splitlines()))
check("the Health track card is gone from every registry that made it",
      not _track_left
      # ...AND OUT OF THE SCRIPT'S OWN LISTS, which is where the
      # evidence of a half-removal sits: a label left in IN_THE_BAG
      # with no deck behind it, or a drop handler for a card that
      # cannot be held.
      and "'Health Track'" not in _lua_code
      and "Health track card is not used" not in _lua
      and "deckOut('Health Track'" not in _lua
      # ...AND OUT OF THE BOOK, and out of the SAVE, which is the only
      # one of these a player can see.
      and "Health track card" not in _RULES["bat"]
      and "Health Track" not in json.dumps(_sv),
      "still registered: %r" % (_track_left,))
# AND THE SPECIMENS DECK IS NEVER ASKED FOR ALL BUT ONE OF ITSELF.
#
# TTS COLLAPSES A DECK OF ONE into the card inside it: the Deck object
# is destroyed and a Card respawns in its place. moveN sends the
# remainder home after taking what it was asked for, so a call that
# leaves exactly one card is a call whose putHome is handed a handle
# that no longer exists - and the card stands where the deck was. That
# is pad(4), the staging band at the bottom edge of the felt. Jon
# photographed it there on 2026-11-21 and again on 2026-11-22: a
# Specimen lying across the exhausted corner, at Standard and at Hard,
# which take 7 of the 8.
#
# tts/test_setup.py CANNOT CATCH THIS. Its deck model keeps a deck of
# one alive and named, so putHome succeeds there and the card goes
# home; every assertion about the band passed while the table had a
# card lying in it. Modelling the collapse is the real fix and is not
# done - so this is a SOURCE check, and it is the only thing standing
# between that card and the felt.
#
# THE PREDICATE IS THE CALL, not a name: setupBAT hands moveN the whole
# deck, and no moveN call anywhere is handed BAT's per-rung count.
_spec_n = len(_gbat["SPECIMENS"])
_moveN_args = re.findall(r"moveN\([^;]*?,\s*([A-Za-z_][\w.\[\]']*)\)",
                         _lua_code)
check("BAT asks moveN for the whole Specimens deck, never all but one",
      ("upg = moveN(deckOut('Specimens', pad(4)), upg, BAT_SPECIMENS)"
       in _lua_code)
      and ("BAT_SPECIMENS = %d" % _spec_n) in _lua_code
      and "spec" not in _moveN_args
      # ...AND THE RUNG'S COUNT IS REACHED BY TAKING THE SURPLUS BACK
      # OUT, one card per step, after the pool is shuffled - so which
      # Specimens go back to the box is random rather than whichever
      # two the deck order put first.
      and "if held > spec and pick then dropCard(upg, pick) end" in _lua_code
      and _lua_code.index("if upg then upg.shuffle() end")
      < _lua_code.index("if held > spec and pick"),
      "%d Specimens printed; moveN counts in lua.lua: %r"
      % (_spec_n, _moveN_args))

check("...and the setup really tells them to build the clock",
      "BUILD THE CLOCK BEFORE YOU START" in _lua
      and "shuffle it" in _lua and "underneath the first six" in _lua,
      "the Wake-Up card waits in the bag and nothing says to fetch it")


# THE HEALTH TRACK CARD'S PRINTED GRID WAS MEASURED HERE, off the
# rendered sheet, and held against TRACK_PITCH and TRACK_GRID_DZ: the
# mod put a snap point in the middle of each of the fifteen spaces, so
# an art change that moved the grid a millimetre would have dropped
# the Health die between numbers.
#
# NOTHING POINTS AT THAT GRID ANY MORE. The dial beside the battle
# pool carries the Prototyrant's Health as of 2026-11-21, nothing
# deals the card, and TRACK_PITCH, TRACK_GRID_DZ, TRACK_SPACES and
# TRACK_CELL went with it - so this measured a card against constants
# that no longer exist. The claim that replaces it is below: that the
# constants really are gone, which is what makes the measurement
# unnecessary rather than merely unperformed.
# IN THE CODE, NOT IN THE PROSE. Both files carry a comment naming
# what was removed and why, which is the point of the comment; what
# must be gone is every line that could still be executed.
_mod_code = chr(10).join(l.split("#")[0]
                        for l in _mod.splitlines())
_gone = [n for n in
         ("TRACK_PITCH", "TRACK_GRID_DZ", "TRACK_SPACES", "TRACK_CELL",
          "trackSpace", "trackPark", "BAT_TRACK")
         if n in _lua_code or n in _mod_code
         or re.search(r"^%s" % n, _sv["LuaScript"], re.M)]
check("nothing in the mod still points at the Health track's grid",
      not _gone and "def track_cells" not in _mod_code,
      "still live: %r" % (_gone,))
# ONE BUTTON PER GAME THAT HAS A FINALE, and none for the Imposter
# scenario, which is itself NRJ's finale and has nothing after it.
_fin = re.search(r"^FINALE = \{(.*?)^\}", _lua, re.M | re.S)
_fingames = re.findall(r"(\w+) = \{'([^']+)', (\w+),",
                       _fin.group(1) if _fin else "")
check("each of the three games has a finale button",
      sorted(g for g, _, _ in _fingames) == ["AoS", "BAT", "NAP"],
      "%r" % (_fingames,))
check("...and each one calls a function that exists",
      all(re.search(r"^function %s\(" % fn, _lua, re.M)
          for _, _, fn in _fingames),
      "%r" % ([fn for _, _, fn in _fingames],))
# THE PANEL SHOWS IT ONCE. It deals cards and shuffles decks, so
# pressing it twice would deal a second set of Final Exams onto the
# first - and the thing that stops that is one flag, set before the
# work starts and cleared by every setup.
check("...shown only after a setup, and only until it is used",
      "if FINALE[g] and not STATE.finale then" in _lua_code
      and _lua_code.count("STATE.finale = false") == 5
      and "STATE.finale = true" in _lua_code,
      "%d resets" % _lua_code.count("STATE.finale = false"))
# A SWEEP ASKS DECK_OF, NOT o.type. In TTS the overlay is a Tile and
# the type test spares it; in the harness every leaf answers "Card",
# and the sweep bagged the NAP table - the mat is 56 units wide, so
# its centre sits inside an Assignment space. DECK_OF holds exactly
# the cards this mod prints, which is the question being asked.
check("the finale sweep decides what a card is from DECK_OF",
      "function isGameCard" in _lua_code
      and "DECK_OF[base] ~= nil" in _lua_code
      and "if isGameCard(o) and packable(o) then" in _lua_code
      and not re.search(r"t == 'Card' or t == 'Deck'", _lua_code))
check("...and the harness checks the overlay survives all three",
      "and the table overlay is still on the table" in _ts
      and "and so is the rulebook and both counters" in _ts)
# EVERY FINALE PLACEMENT IS A BOX THE MAT ALREADY DRAWS. The overlay
# is a printed image built when the mod is built, so a finale space
# that is not one of the drawn ones is a card on bare felt with no
# outline under it and no snap to catch it.
_placed = re.findall(r"deckOut\('(?:Final Exams|Tyrant Attacks|"
                     r"Advanced Programs)'[^)]*\{([^}]*)\}", _lua_code)
check("the finales deal onto spaces, not onto coordinates",
      _placed and not [p for p in _placed if re.search(r"-?\d+\.\d", p)],
      "literal positions: %r" % (_placed,))

# THE ALT VIEW IS TOLD WHICH WAY UP A LANDSCAPE CARD IS.
#
# SidewaysCard is what makes the card landscape ON THE TABLE and it was
# always right; the Alt preview is a separate thing that reads
# AltLookAngle, and with no angle set it stands every card's long edge
# up. Eleven of the thirty decks are landscape, so this was most of the
# text in the mod being read with your head tilted.
#
# AND ONE ANGLE IS NOT ENOUGH. A flip reverses the sense of the roll,
# so a single value is right for the face it was measured on and 180
# degrees out on the other: the first one tried gave Jon side B of a
# Lab Rat correct and side A - the side you read - upside down. The
# save bakes the face-up angle, which is the one every landscape card
# is dealt on and the one that still reads correctly if assigning the
# angle from a script turns out not to take; lua.lua swaps them as
# cards are turned over.
#
# BOTH HALVES, OR NEITHER. A card dragged off a deck is built from the
# entry inside it, so the deck and every card in it have to carry the
# angle - exactly like SidewaysCard and the scale, both of which were
# once set on the deck alone.
_alt_up = re.search(r"^ALT_LOOK_UP = \((-?[\d.]+), (-?[\d.]+), (-?[\d.]+)\)",
                    _mod, re.M)
_alt_dn = re.search(r"^ALT_LOOK_DOWN = \((-?[\d.]+), (-?[\d.]+), (-?[\d.]+)\)",
                    _mod, re.M)
_up = tuple(float(v) for v in _alt_up.groups()) if _alt_up else None
_dn = tuple(float(v) for v in _alt_dn.groups()) if _alt_dn else None
check("there is an Alt-view angle for each face of a landscape card",
      None not in (_up, _dn), "up %r, down %r" % (_up, _dn))
check("...and they are a half turn apart, which is what a flip does",
      _up and _dn and round(abs(_up[2] - _dn[2]) % 360.0, 3) == 180.0,
      "up %r, down %r" % (_up, _dn))
# ONE OWNER. Both numbers are generated into the header, so the script
# cannot drift from the angle the save was built with.
check("...and the script is given both of them, not its own copies",
      bool(re.search(r"^ALT_LOOK_UP = \{-?\d+, -?\d+, -?\d+\}$",
                     _sv["LuaScript"], re.M))
      and bool(re.search(r"^ALT_LOOK_DOWN = \{-?\d+, -?\d+, -?\d+\}$",
                         _sv["LuaScript"], re.M))
      and not re.search(r"^ALT_LOOK_(UP|DOWN) = ", _lua, re.M),
      "the header or lua.lua has the wrong one")
_noangle, _extra = [], []
_counts = {True: 0, False: 0}


def _walk_cards(o):
    if o.get("Name") in ("Card", "CardCustom", "Deck"):
        got = o.get("AltLookAngle")
        got = ((got["x"], got["y"], got["z"]) if got else None)
        name = o.get("Nickname") or o.get("Name")
        _counts[bool(o.get("SidewaysCard"))] += 1
        if o.get("SidewaysCard"):
            if got != _up:
                _noangle.append((name, got))
        elif got is not None:
            _extra.append((name, got))
    for k in o.get("ContainedObjects") or []:
        _walk_cards(k)


for _o in _sv["ObjectStates"]:
    _walk_cards(_o)
check("every landscape card and deck is built holding the face-up angle",
      not _noangle and _counts[True] > 0,
      "%d sideways objects, %d wrong: %r"
      % (_counts[True], len(_noangle), _noangle[:4]))
check("...and no portrait one carries an angle it does not need",
      not _extra, "%d with an angle they should not have: %r"
      % (len(_extra), _extra[:4]))
# AND IT IS THE LANDSCAPE DECKS OF decks.py, not a list typed twice:
# the sheets are 1050x750 cells for exactly those, so the flag, the
# scale and now the Alt angle all come off the same `land`.
_land = re.findall(r"land=(True|False)", _decks)
check("the mod's landscape cards are decks.py's landscape decks",
      _counts[True] > 0 and _land.count("True") > 0
      and "alt_look(bool(d['land']))" in _mod
      and "out.update(alt_look(sideways))" in _mod,
      "%d sideways objects for %d landscape decks"
      % (_counts[True], _land.count("True")))
# THE SWAP ITSELF: read off the face the card is lying on, and only
# for a landscape CARD - a deck is not a card and a portrait card
# wants no angle at all. tts/test_setup.py turns one over both ways
# and checks the angle follows; this is that the mechanism is there.
check("the script sets the angle from the face that is actually up",
      "function onObjectRotate" in _lua_code
      and "o.is_face_down and ALT_LOOK_DOWN or ALT_LOOK_UP" in _lua_code
      and "o.type ~= 'Card'" in _lua_code
      and "d.SidewaysCard == true" in _lua_code)
check("...and the harness turns a card over and checks it followed",
      "...and turning it over gives the Alt view the other angle" in _ts
      and "and turning it back gives the first one again" in _ts
      and "leaves its Alt angle alone" in _ts)
# THREE WAYS IN, because onObjectRotate alone did not catch the flip
# Jon actually made. The docs raise it for a deliberate rotation and
# not for physics, which leaves F - a player ACTION with its own
# event - and picking a card up and putting it down the other way up.
check("every way of turning a card over reaches the Alt angle",
      all(t in _lua_code for t in ("function onObjectRotate",
                                   "function onPlayerAction",
                                   "Player.Action.FlipOver",
                                   "altFace(obj)")),
      "a trigger is missing")
check("...and the harness exercises all three of them",
      "the F key" in _ts and "a pick-up and drop" in _ts
      and "g.onObjectRotate(" in _ts)
# A VECTOR. Every rotation in lua.lua is a plain {x, y, z} and TTS
# takes them all, so the first version assigned one here too and
# nothing changed at the table; every published example of
# alt_view_angle uses Vector(), and the plain form is reported to
# error from the console.
check("the Alt angle is assigned as a Vector, not three loose numbers",
      "Vector(a[1], a[2], a[3])" in _lua_code
      and "o.alt_view_angle = altVector(want)" in _lua_code
      and "and the angle was set as a Vector" in _ts)

# DECK_OF IS WHAT LETS A MERGED DECK BE TAKEN APART AGAIN - it is the
# only table that says a Task belongs to the Assignment deck - so it is
# generated from decks.py rather than typed, and it has to cover every
# deck: one missing entry is one deck that never comes back.
_dof = re.search(r"^DECK_OF = \{(.*)\}$", _hdr, re.M)
_dcards = dict(re.findall(r"\['([^']+)'\] = '([^']+)'",
                          _dof.group(1) if _dof else ""))
_dlabels = set(re.findall(r"label='([^']+)'", _decks))
check("every deck in tts/decks.py can be found again from its cards",
      set(_dcards.values()) == _dlabels
      and all(_dcards.get(l) == l for l in _dlabels),
      "DECK_OF covers %r, decks.py has %r"
      % (sorted(set(_dcards.values())), sorted(_dlabels)))
check("nothing writes that table down a second time",
      "DECK_OF = {" not in _lua and "'DECK_OF = { %s }'" in _mod)

# ONE OBJECT PER FACE. The Chip was a Custom_Token carrying one image,
# and a token with one image shows that image MIRRORED on its
# underside - which is why the script spent weeks turning to a number
# side that did not exist. It briefly became a two-faced Custom_Tile;
# it is a token again, and BAT's dial is an object of its own, because
# no game reads both and two objects cost almost nothing.
_chip_obj = [o for o in _sv['ObjectStates'] if o.get('Nickname') == 'Chip']
_ci = (_chip_obj[0].get('CustomImage') or {}) if _chip_obj else {}
_dial_obj = []


def _find_dial(objs):
    for o in objs:
        if o.get('Nickname') == 'Dial':
            _dial_obj.append(o)
        _find_dial(o.get('ContainedObjects', []))


_find_dial(_sv['ObjectStates'])
_di = (_dial_obj[0].get('CustomImage') or {}) if _dial_obj else {}
check("the Chip carries the colours and nothing else",
      bool(_chip_obj) and _chip_obj[0]['Name'] == 'Custom_Token'
      and 'Chip_Colour' in (_ci.get('ImageURL') or '')
      and not (_ci.get('ImageSecondaryURL') or ''),
      'the Chip is %r with a second image %r'
      % (_chip_obj[0]['Name'] if _chip_obj else None,
         (_ci.get('ImageSecondaryURL') or '(none)')[-22:]))
check("the Dial is an object of its own, with the dial on it",
      len(_dial_obj) == 1 and 'Chip_Dial' in (_di.get('ImageURL') or ''),
      'found %d Dial objects' % len(_dial_obj))
# ITS OWN ROTATION VALUES, so TTS turns it when a number is typed.
_dv = (dict((int(v['Value']), int(v['Rotation']['y']))
            for v in (_dial_obj[0].get('RotationValues') or []))
       if _dial_obj else {})
check("the Dial turns itself when you type a number at it",
      sorted(_dv) == list(range(21)),
      'rotation values %r' % sorted(_dv))
check("both faces ship from images/",
      len([f for f in os.listdir(os.path.join(ROOT, 'images'))
           if f.startswith('Chip_Colour')]) == 1
      and len([f for f in os.listdir(os.path.join(ROOT, 'images'))
               if f.startswith('Chip_Dial')]) == 1)
# AND NOTHING CLAIMS THE OLD IMAGINARY ONE. CHIP_NUM was five angles
# for a face that was never there.
check("nothing turns the Chip to a face it does not have",
      not re.search(r'^CHIP_NUM', _lua, re.M)
      and bool(re.search(r'^CHIP_DIAL = ', _sv['LuaScript'], re.M)),
      'CHIP_NUM is back, or CHIP_DIAL is not generated')

# ---------------------------------------------------------------------
# EVERY ASSET THE MOD LOADS COMES OUT OF THIS REPOSITORY.
#
# The dice were the official 20 Strong mod's, served from Steam, and
# both Chip faces were photographs of the physical component sitting
# in images/ - which made CONTENT_NOTICE.md false where it says no
# Chip Theory Games artwork is reproduced here. tts/make_dice.py and
# tts/make_chip.py draw replacements. This is the check that keeps
# the notice honest: anything loaded from a host that is not the
# repo's own CDN is a dependency on art the set does not own.
_hosts = set()
for _m in re.finditer(r'"(?:FaceURL|BackURL|ImageURL|ImageSecondaryURL'
                      r'|DiffuseURL|PDFUrl|URL)": "([^"]+)"',
                      json.dumps(_sv)):
    _u = _m.group(1)
    if _u:
        _hosts.add(re.sub(r'^(https?://[^/]+).*', r'\1', _u))
check("every image and book the mod loads comes from this repository",
      _hosts <= set(["https://cdn.jsdelivr.net",
                     "https://raw.githubusercontent.com"]),
      "also loads from %r" % (sorted(_hosts - set([
          "https://cdn.jsdelivr.net",
          "https://raw.githubusercontent.com"])),))
# AND THE EIGHT DICE ARE REALLY THERE. A die whose URL 404s shows as
# a blank white cube with no error anywhere, which is the same way a
# missing card sheet failed for a month.
_dice_want = ["Blue", "Green", "Health", "Purple", "Recovery", "Red",
              "Strategy", "Yellow"]
_dice_have = sorted(set(re.findall(r'Die_(\w+)_[0-9a-f]{8}\.png',
                                   json.dumps(_sv))))
_dice_png = sorted(set(re.findall(r'^Die_(\w+)_[0-9a-f]{8}\.png$', f)[0]
                       for f in os.listdir(os.path.join(ROOT, "images"))
                       if re.match(r'^Die_\w+_[0-9a-f]{8}\.png$', f)))
check("the save names all eight dice, and all eight are in images/",
      _dice_have == _dice_want and _dice_png == _dice_want,
      "save %r, images/ %r" % (_dice_have, _dice_png))

# AND EACH DIE SHOWS THE FACES IT IS ROLLED WITH.
#
# simulation/dice.py FACES is the project's canonical table - every
# simulation run and both playtest engines roll against it - and the
# colours are a ladder: red hits on five faces in six, purple four,
# blue three, green two, yellow one, each with a single crit.
#
# THE FIRST GENERATED DICE GAVE EVERY COLOUR FIVE HITS AND A CRIT,
# which is the red die drawn five times, so a yellow die hit on five
# faces instead of one. Nothing caught it: the geometry was verified
# to the pixel, the registration to a tenth of a degree, and the mod
# harness counts cards rather than reading art. A playtest on those
# dice would have produced numbers that meant nothing and no error
# anywhere. This reads the ink off the drawing and holds it to the
# table the model uses.
_FACES_SRC = text("simulation/dice.py")
_faces_m = re.search(r"^FACES = \{(.*?)^\}", _FACES_SRC, re.S | re.M)
_faces = dict((k, [int(v) for v in re.findall(r"\d+", vals)])
              for k, vals in re.findall(r'"(\w+)":\s*\[([^\]]*)\]',
                                        _faces_m.group(1) if _faces_m else ""))
check("simulation/dice.py still gives every colour six faces",
      len(_faces) == 5 and all(len(v) == 6 for v in _faces.values()),
      "got %r" % (dict((k, len(v)) for k, v in sorted(_faces.items())),))


def _die_faces(path):
    """The six faces of a die sheet as success values, read off the art.

    BY LEVEL, NOT BY THRESHOLD. A blank is an empty face here and a
    full gear ring on the components these replace, so no absolute
    cut classifies both; the crit is the single highest ink level,
    and if two levels remain below it the lower is the blank.
    """
    from PIL import Image, ImageChops
    im = Image.open(path).convert("RGB")
    side = im.size[0]
    cell = side / 3.0
    vals = []
    for r in (1, 2):
        for c in (0, 1, 2):
            box = (int(cell * (c + 0.5) - cell / 2),
                   int(cell * (r + 0.5) - cell / 2),
                   int(cell * (c + 0.5) + cell / 2),
                   int(cell * (r + 0.5) + cell / 2))
            f = im.crop(box)
            flat = Image.new("RGB", f.size, f.getpixel((3, 3)))
            ch = ImageChops.difference(f, flat).split()
            m = ImageChops.lighter(ImageChops.lighter(ch[0], ch[1]),
                                   ch[2]).point(lambda v: 255 if v > 25 else 0)
            vals.append(sum(1 for v in m.get_flattened_data() if v))
    lv = sorted(set(int(round(v / 2000.0)) for v in vals))
    out = []
    for v in vals:
        k = int(round(v / 2000.0))
        out.append(2 if k == lv[-1] else (0 if len(lv) > 2 and k == lv[0]
                                          else 1))
    return out


_face_bad = []
for _c in sorted(_faces):
    _png = [f for f in os.listdir(os.path.join(ROOT, "images"))
            if f.startswith("Die_%s_" % _c.capitalize())]
    if not _png:
        _face_bad.append((_c, "no image"))
        continue
    _drawn = sorted(_die_faces(os.path.join(ROOT, "images", _png[0])))
    if _drawn != sorted(_faces[_c]):
        _face_bad.append((_c, _drawn, sorted(_faces[_c])))
check("every die is drawn with the faces simulation/dice.py rolls",
      not _face_bad, "drawn vs table: %r" % (_face_bad,))


# AND THE GEAR COUNTS THEM TOO.
#
# The components encode the ladder in the teeth: counted off the real
# dice, yellow has 2, green 3, blue 4, purple 5, red 6 - each one its
# number of non-blank faces, so a die says what it is worth before it
# is rolled. Ours do the same, from the same FACES table, which means
# a die now carries the claim twice and the two must agree.
#
# COUNTED OFF THE DRAWING, not off the constant that drew it. The
# radial profile has to be centred on the INK, not on the cell: two
# of the real dice have a glyph a few pixels off centre, and centring
# on the cell adds a one-cycle wobble that merges peaks and reads
# 2/2/4/4/6 instead of 2/3/4/5/6.


def _tooth_count(path, cell_col=0, cell_row=0):
    from PIL import Image
    im = Image.open(path).convert("RGB")
    side = im.size[0]
    cell = side / 3.0
    box = (int(cell * (cell_col + 0.5) - cell / 2),
           int(cell * (cell_row + 1.5) - cell / 2),
           int(cell * (cell_col + 0.5) + cell / 2),
           int(cell * (cell_row + 1.5) + cell / 2))
    f = im.crop(box)
    w, h = f.size
    px = f.load()
    bg = px[3, 3]

    def ink(x, y):
        p = px[int(x), int(y)]
        return (abs(p[0] - bg[0]) + abs(p[1] - bg[1])
                + abs(p[2] - bg[2]) > 60)

    sx = sy = n = 0
    for y in range(0, h, 3):
        for x in range(0, w, 3):
            if ink(x, y):
                sx += x
                sy += y
                n += 1
    if not n:
        return 0
    cx, cy = sx / float(n), sy / float(n)
    prof = []
    for d in range(360):
        t = math.radians(d)
        got = 0
        for rr in range(int(w * 0.49), 10, -2):
            x, y = cx + rr * math.sin(t), cy - rr * math.cos(t)
            if 0 <= x < w and 0 <= y < h and ink(x, y):
                got = rr
                break
        prof.append(got)
    sm = [sum(prof[(i + k) % 360] for k in (-1, 0, 1)) / 3.0
          for i in range(360)]
    mean = sum(sm) / 360.0
    return sum(1 for i in range(360) if sm[i] > mean and sm[i - 1] <= mean)


_teeth_bad = []
for _c in sorted(_faces):
    _png = [f for f in os.listdir(os.path.join(ROOT, "images"))
            if f.startswith("Die_%s_" % _c.capitalize())]
    if not _png:
        continue
    _want = sum(1 for v in _faces[_c] if v)
    _got = _tooth_count(os.path.join(ROOT, "images", _png[0]))
    if _got != _want:
        _teeth_bad.append((_c, _got, _want))
check("each gear has one tooth per scoring face",
      not _teeth_bad, "drawn vs table: %r" % (_teeth_bad,))


# THE COLOUR WHEEL IS HELD TO CHIP_SEGMENT, the way the dial is held
# to CHIP_DIAL_MARK below. The script TURNS this face - CHIP_ANGLE is
# derived from these numbers - so art a few degrees out of register
# sends every turn to the wrong colour, and nothing about the picture
# looks wrong. make_chip.py draws the wedges FROM these angles; this
# measures the drawing and says so independently.
#
# ART_OFFSET is build_mod.py's own 197: its comment records the
# wedges at Red 233, Yellow 305, Green 17, Blue 89, Purple 161 and
# every CHIP_SEGMENT number as that less 197, the difference absorbed
# by CHIP_TRIM. CHIP_TRIM itself is not held here and cannot be - it
# is the nudge that lands a colour where a player reads it, and only
# the table can say what that is.
_ART_OFFSET = 197
_WEDGE_RGB = {"Red": (193, 18, 86), "Yellow": (233, 209, 55),
              "Green": (93, 146, 54), "Blue": (57, 124, 233),
              "Purple": (119, 70, 210)}


def _wedge_angles(path):
    import math
    from PIL import Image
    im = Image.open(path).convert("RGBA")
    w, h = im.size
    px = im.load()
    cx, cy = (w - 1) / 2.0, (h - 1) / 2.0
    acc = {}
    for deg in range(1440):
        a = deg / 4.0
        t = math.radians(a)
        for rf in (0.33, 0.36, 0.39, 0.42):
            x, y = cx + (w * rf) * math.sin(t), cy - (h * rf) * math.cos(t)
            if not (0 <= x < w and 0 <= y < h):
                continue
            r, g, b, al = px[int(x), int(y)]
            if al < 200:
                continue
            best, bd = None, 1e9
            for nm, (R, G, B) in _WEDGE_RGB.items():
                dd = (r - R) ** 2 + (g - G) ** 2 + (b - B) ** 2
                if dd < bd:
                    best, bd = nm, dd
            if bd < 2500:
                acc.setdefault(best, []).append(a)
    out = {}
    for nm, angs in acc.items():
        sx = sum(math.sin(math.radians(x)) for x in angs)
        sy = sum(math.cos(math.radians(x)) for x in angs)
        out[nm] = math.degrees(math.atan2(sx, sy)) % 360.0
    return out


_seg_said = dict((k, int(v)) for k, v in re.findall(
    r"'(\w+)': (\d+)",
    re.search(r"CHIP_SEGMENT = \{(.*?)\}", _mod, re.S).group(1)))
_colour_png = [f for f in os.listdir(os.path.join(ROOT, "images"))
               if f.startswith("Chip_Colour")]
_got_wedge = (_wedge_angles(os.path.join(ROOT, "images", _colour_png[0]))
              if _colour_png else {})
_off = []
for _c, _a in sorted(_seg_said.items()):
    _want = (_a + _ART_OFFSET) % 360
    _have = _got_wedge.get(_c)
    if _have is None or min((_have - _want) % 360,
                            (_want - _have) % 360) > 1.5:
        _off.append((_c, None if _have is None else round(_have, 1), _want))
check("every colour wedge is where CHIP_SEGMENT says it is",
      not _off, "off register: %r" % (_off,))

# ---------------------------------------------------------------------

# THE DIAL IS HELD TO ITS OWN PICTURE. CHIP_DIAL is generated from
# where the numbers sit, so the picture is what can say the table is
# wrong: find the olive marker again and check it is where
# build_mod.py says it is, and that the numbers come out one slot
# apart all the way round.
#
# This outlived the scan it was written for. make_chip.py now draws
# the dial FROM CHIP_DIAL_MARK, and the check reads the same 327.8
# off the drawing that it read off the photograph.
#
# CHIP_DIAL_TRIM is NOT held here and cannot be: it is the nudge that
# lands the numbers where a player reads them, and only the table can
# say what that is. The same is true of CHIP_TRIM on the other face.
_dial_png = [f for f in os.listdir(os.path.join(ROOT, 'images'))
             if f.startswith('Chip_Dial')]
_said_mark = float(re.search(r'^CHIP_DIAL_MARK = ([\d.]+)', _mod,
                             re.M).group(1))
_slots = int(re.search(r'^CHIP_DIAL_SLOTS = (\d+)', _mod, re.M).group(1))


def _marker_angle(path):
    import math
    from PIL import Image
    im = Image.open(path).convert('RGBA')
    w, h = im.size
    px = im.load()
    cx, cy = (w - 1) / 2.0, (h - 1) / 2.0
    sx = sy = 0.0
    n = 0
    for rr in range(int(cx * 0.55), int(cx * 0.95)):
        for d in range(1440):
            t = d * math.pi / 720
            x, y = cx + rr * math.sin(t), cy - rr * math.cos(t)
            if not (0 <= x < w and 0 <= y < h):
                continue
            r, g, b, a = px[int(x), int(y)]
            if (a > 200 and 90 < r < 175 and 100 < g < 185
                    and b < 110 and g > b + 30):
                sx += math.sin(math.radians(d / 4.0))
                sy += math.cos(math.radians(d / 4.0))
                n += 1
    if not n:
        return None
    return math.degrees(math.atan2(sx, sy)) % 360.0


_got_mark = (_marker_angle(os.path.join(ROOT, 'images', _dial_png[0]))
             if _dial_png else None)
check("the dial's zero is measured off the dial",
      _got_mark is not None and abs(_got_mark - _said_mark) < 1.5,
      'the scan puts the marker at %s, build_mod.py says %s'
      % (None if _got_mark is None else round(_got_mark, 1), _said_mark))
_dial = dict((int(a), int(b)) for a, b in
             re.findall(r'\[(\d+)\] = (\d+)',
                        re.search(r'^CHIP_DIAL = \{([^}]*)\}',
                                  _sv['LuaScript'], re.M).group(1)))
_step = 360.0 / _slots
_gaps = [(_dial[n + 1] - _dial[n]) % 360 for n in range(20)]
# EITHER WAY ROUND. The numbers run one way on the picture and the
# turn that brings them to the player goes the other, so what is
# held here is the size of the step, not its sign.
check("its numbers are one slot apart, all the way round",
      sorted(_dial) == list(range(21))
      and all(abs(min(g, 360 - g) - _step) < 1.0 for g in _gaps),
      'gaps %r, a slot is %.2f' % (sorted(set(_gaps)), _step))


# HOW MANY SLOTS THE RIM HOLDS IS AN OBSERVATION, like the five
# segment angles on the other face, and it is NOT checked here.
# Laying the numbers out for each candidate count and asking where
# the white ink falls looked like a measurement and is not one:
# 22 scores 1.19 against 24's 1.33, so the test prefers a count
# that is plainly wrong. A predicate that cannot tell right from
# wrong is worse than none - it would have passed whatever the
# table said. The count and CHIP_DIAL_TRIM are both for the table
# to confirm; what is held above is that the marker is where the
# scan puts it and that the numbers come out evenly spaced.

# THE RULEBOOK IN THE CORNER. Four PDFs fetched from rules/ rather than
# images/, so they are the one set of files the image manifest would
# not have covered, and a URL that 404s shows as a blank page with no
# error anywhere.
# FOUR BOOKS, ONE PER GAME. It was one Custom_PDF whose URL the
# script rewrote with setCustomObject and reload, which is the
# documented way and did not work at Jon's table: his autosave after a
# NAP setup still held BAT_Rulebook.pdf as the object's own URL. No
# error anywhere, right GUID, right URL table, wrong book in the
# corner. Each game's book is a component in that game's box now.
#
# They are fetched from rules/ rather than images/, so they are the
# one set of files the image manifest does not cover, and a URL that
# 404s shows as a blank page with no error anywhere.
_pdf = [o for o in _sv["ObjectStates"] if o["Name"] == "Custom_PDF"]
_bagged = [d for o in _sv["ObjectStates"] if o["Name"] == "Bag"
           for d in o.get("ContainedObjects", [])
           if d["Name"] == "Custom_PDF"]
check("there is one rulebook per game, and one of them starts out",
      (len(_pdf), len(_bagged)) == (1, 3),
      "%d on the table, %d in boxes" % (len(_pdf), len(_bagged)))
_books = dict((o["Nickname"], o["CustomPDF"]["PDFUrl"])
              for o in _pdf + _bagged)
_nick = re.search(r"RULES_NICK = \{([^}]*)\}", _sv["LuaScript"])
_want = dict(re.findall(r"(\w+) = '([^']+)'",
                        _nick.group(1))) if _nick else {}
check("the script names a rulebook for all four games",
      sorted(_want) == ["AoS", "BAT", "IMP", "NAP"],
      "got %r" % (sorted(_want),))
check("...and every name it uses is a book that is really there",
      sorted(_want.values()) == sorted(_books),
      "script %r vs save %r" % (sorted(_want.values()), sorted(_books)))
# THE CARRY-FORWARD BAG, and the two things about it that matter.
#
# Jon asked for somewhere to keep the cards he is carrying into the next
# game of the campaign (2026-11-12). It is a fifth bag on the rail, off
# the left end outside BAT - and it is NOT one of BOX, which is the
# whole point: BOX is what deckOut searches, putHome files into and
# packUp sweeps towards, so a fifth entry there would have the next
# setup deal the carried cards straight back out again.
_bags = dict((o.get("Nickname") or "", o) for o in _sv["ObjectStates"]
             if o["Name"] == "Bag")
_carry = [n for n in _bags if n.startswith("CARRY")]
check("there is one carry-forward bag on the rail",
      len(_carry) == 1, "%r" % (sorted(_bags),))
if len(_carry) == 1:
    _cb = _bags[_carry[0]]
    _ct = _cb["Transform"]
    # EMPTY IN THE SAVE. It is a place the player puts things; a bag
    # that shipped with cards in it would be holding them out of a game
    # nobody has played yet.
    check("...and it ships empty",
          not _cb.get("ContainedObjects"),
          "%d object(s) inside" % len(_cb.get("ContainedObjects") or []))
    # ON THE RAIL WITH THE OTHERS, at the pitch the pair it joins uses,
    # rather than at a number typed in here.
    _xs = dict((n, _bags[n]["Transform"]["posX"]) for n in _bags)
    _bat = [n for n in _bags if n.startswith("BAT")]
    _nap = [n for n in _bags if n.startswith("NAP")]
    _pitch = (round(_xs[_nap[0]] - _xs[_bat[0]], 2)
              if _bat and _nap else None)
    check("...to the left of the BAT box, at the same pitch",
          _pitch is not None
          and round(_xs[_bat[0]] - _ct["posX"], 2) == _pitch,
          "carry at %r, BAT at %r, pitch %r"
          % (_ct.get("posX"), _xs.get(_bat[0] if _bat else ""), _pitch))
    # AND CLEAR OF EVERYTHING ELSE ON THAT RAIL, which is the check
    # that was missing. The bag went to the right end first and landed
    # on BAT's rulebook, 2.6 away on the same z - the position checks
    # above all passed, because every one of them only compared the bag
    # with the other bags. One pitch of room is what the rail already
    # proves is enough for an object this size, so ask for that from
    # every neighbour rather than for a measured width.
    _rail = [o for o in _sv["ObjectStates"]
             if abs(o["Transform"]["posZ"] - _ct["posZ"]) < 2.5
             and o["GUID"] != _cb["GUID"]]
    _near = [((o.get("Nickname") or o["Name"]),
              round(o["Transform"]["posX"] - _ct["posX"], 2)) for o in _rail
             if _pitch is not None
             and abs(o["Transform"]["posX"] - _ct["posX"]) < _pitch - 0.01]
    check("...and a clear pitch from everything else on the rail",
          _pitch is not None and not _near, "%r" % (_near,))
    check("...and on the same rail, not in front of it",
          sorted(set(round(_bags[n]["Transform"]["posZ"], 2)
                     for n in _bags)) == [round(_ct["posZ"], 2)],
          "z values %r" % (sorted(set(round(_bags[n]["Transform"]["posZ"], 2)
                                      for n in _bags)),))
    # YELLOW, which is what was asked for and what tells it from the
    # four game boxes at a glance. Red and green high, blue low.
    _c = _cb["ColorDiffuse"]
    check("...and it is yellow",
          _c["r"] > 0.6 and _c["g"] > 0.5 and _c["b"] < 0.3
          and _c["r"] >= _c["g"] > _c["b"], "%r" % (_c,))
    # AND ONE FUNCTION TURNS THE GUID INTO AN OBJECT. It was settle()
    # alone until 2026-11-13, when Jon asked for the Imposter setup to
    # read what the campaign carried forward - so there are callers
    # now, and carryBag() is the single place that resolves it.
    _lua_all = _sv["LuaScript"]
    _boxtab = re.search(r"\nBOX = \{([^}]*)\}", _lua_all)
    check("...and its GUID is not one of BOX",
          _boxtab is not None and _cb["GUID"] not in _boxtab.group(1),
          "BOX = %r" % (_boxtab and _boxtab.group(1),))
    check("...but the script is given it, resolved in carryBag() alone",
          ("CARRY = '%s'" % _cb["GUID"]) in _lua_all
          and _lua_all.count("getObjectFromGUID(CARRY)") == 1
          and re.search(r"function carryBag\(\)[^}]*?"
                        r"getObjectFromGUID\(CARRY\)", _lua_all) is not None)
    # AND IT HAS NO HOME OF ITS OWN, which is NOT the same statement as
    # "it is not one of BOX" and is where the hole was. boxFor() does
    # not ask BOX; it asks what is INSIDE, so a bag holding a Research
    # Note answered the NRJ box and Pack up had somewhere to put the
    # carry bag. Two cards in, press a setup button, one card left.
    check("...and boxFor() exempts it, so Pack up cannot file it",
          "if isCarry(obj) then return nil end" in _lua_all
          and "function isCarry(obj)" in _lua_all)
    # AND EXACTLY ONE SETUP READS IT. A second one would be dealing
    # somebody else's carried cards into its own game.
    _reads = [_f for _f in re.findall(
        r"\nfunction (\w+)\([^)]*\)(.*?)\nend\n", _lua_all, re.S)
        if "carriedPool()" in _f[1]]
    check("...and the Imposter setup is the only thing that reads it",
          [_f[0] for _f in _reads] == ["setupImposter"],
          "%r" % ([_f[0] for _f in _reads],))

# THE RESEARCH POOL'S CAPS REACH THE MOD, out of the same tuple the
# rulebook and the lab are measured against above - see "HOW MANY CARDS
# ARE RETAINED". build_mod.research_pool() reads RETAIN out of
# simulation/finale.py and writes IMP_POOL into the generated header, so
# this compares the save with the file it was generated from rather than
# with a fifth copy of 3/2/2 typed in here.
#
# AND THE ORDER IS decks.py'S OWN, which is not decoration: the three
# sit side by side on the felt and only the landscape deck in the middle
# makes them fit, so a reordered table is a row that runs off the table.
_impool = re.search(r"\nIMP_POOL = \{(.*?)\}\n", _sv["LuaScript"])
check("the mod's IMP_POOL carries the same caps, in decks.py's order",
      _impool is not None
      and re.findall(r"\{'([^']+)', (\d+), (true|false), (\d+), '([^']+)'\}",
                     _impool.group(1))
      == [("Research Notes", "2", "false", "6", "Physical"),
          ("Devious Opportunities", "3", "true", "6", "Knowledge"),
          ("Backdoor Routines", "2", "false", "6", "Cover-Up")],
      "%r" % (_impool and _impool.group(1),))

# AND THE DOMAIN IN IT IS THE MODEL'S OWN. A retained card answers one
# domain and nothing printed on it says which, so the felt labels the
# row and the setup says it out loud - two more places for
# Knowledge/Physical/Cover-Up to drift from the three the simulation
# scores. build_mod.py reads ANSWERS out of simulation/finale.py; this
# is the other end of that wire.
_answers = py_tables("simulation/finale.py").get("ANSWERS", {})
check("...and the domains are simulation/finale.py's ANSWERS",
      _impool is not None
      and {g: d for d, g in _answers.items()}
      == {{"Research Notes": "BAT", "Devious Opportunities": "NAP",
           "Backdoor Routines": "AoS"}[n]: d
          for n, _c, _l, _k, d in re.findall(
              r"\{'([^']+)', (\d+), (true|false), (\d+), '([^']+)'\}",
              _impool.group(1))},
      "%r" % (_answers,))

# EVERY PLACE THE IMPOSTER TABLE DEALS TO HAS A BOX AND A SNAP UNDER
# IT (Jon, 2026-11-13: "label all the spaces and create snap points").
# impBoxes() is the one list the felt is painted from and the snap
# points are made from, so this counts the places rather than trusting
# that the two agree: the two corner piles, the row a session is
# played along, and one slot per card the caps allow.
_boxes = re.search(r"\nfunction impBoxes\(\)(.*?)\nend\n",
                   _sv["LuaScript"], re.S)
check("...and the mod builds those stacks and names them",
      "grp[k] = gatherInto(grp[k], d)" in _sv["LuaScript"]
      and "cand.setName('Candidates')" in _sv["LuaScript"]
      and "cand.setRotation(FACEDOWN)" in _sv["LuaScript"])
# AND NOTHING IN THAT CORNER IS TURNED. One build had both stacks laid
# on their side so a portrait card would fit a landscape row; the
# Opportunities ARE landscape, so that stood them on end and hung them
# over the back edge. Each stack keeps the shape of the card in it now,
# and the portrait one drops to share the back edge.
check("...and sets both of them down square, not on their side",
      "IMP_CAND_ROT" not in _sv["LuaScript"]
      and "IMP_CORNER_Z = ROW_CHAR + (CARD_W - CARD_L) / 2"
      in _sv["LuaScript"])
# AND IT MAKES TWO OF THEM, SPLIT BY CARD SHAPE - which is the one
# place the mod cannot do what the book says, and the reason is the
# tool rather than the game.
#
# A Deck in TTS carries ONE card size, taken from the sheet its cards
# were cut from, and the three families are not cut the same: a
# Devious Opportunity is 1050x750 per card and a Research Note
# 750x1050. Merged into one deck the stack keeps one aspect and paints
# the other family's back into it, stretched and hanging out of its
# box - which is what came out at Jon's table on 2026-11-13 with all
# eighteen cards correctly placed. On a table the eighteen really do
# shuffle together, every card being the same 63.5 x 88.9 stock, so
# rules/nrj.html is right and stays as it is.
check("...and splits them by card shape, because a TTS deck is one size",
      "local k = p[3] and 2 or 1" in _sv["LuaScript"]
      and "IMP_CANDW_X = impCorner(3)" in _sv["LuaScript"])
check("...and the sheets really are cut two ways",
      "land=False, game='NRJ', label='Research Notes'"
      in text("tts/decks.py")
      and "land=False, game='NRJ', label='Backdoor Routines'"
      in text("tts/decks.py")
      and "land=True, game='NRJ', label='Devious Opportunities'"
      in text("tts/decks.py"))
# AND unmix CAN TAKE IT APART AGAIN, which is not the same claim. A
# box cannot see into a deck it holds, so a Candidate deck stowed
# whole is cards the next deal cannot find: it came out 11, then 10,
# then 9, and every census said all 18 still existed.
check("...and unmix reads a pile the mod does not print by its contents",
      "if mine == '' or DECK_OF[mine] == nil then" in _sv["LuaScript"]
      and "DECK_OF[(n:gsub(' %d+$', ''))] ~= nil then" in _sv["LuaScript"])

check("the Imposter table paints its boxes from impBoxes()",
      _boxes is not None
      and "function impSnaps()" in _sv["LuaScript"]
      and "for _, b in ipairs(impBoxes()) do" in _sv["LuaScript"]
      and "step(function() impSnaps() end)" in _sv["LuaScript"])
check("...and make_template.py draws that same list",
      "for b in g.impBoxes().values():" in text("tts/make_template.py")
      and "draw_imp(d, lua)" in text("tts/make_template.py"))


def _bookfile(u):
    """The PDF a book's URL names, token and all stripped off."""
    return os.path.join(ROOT, "rules", u.rsplit("/", 1)[-1].split("?")[0])


_norules = [n for n, u in sorted(_books.items())
            if not os.path.exists(_bookfile(u))]
check("every rulebook the script can deal is a file in rules/",
      not _norules, "no such PDF: %r" % (_norules,))
# ...AND ITS URL MOVES WHEN THE BOOK DOES.
#
# The books keep fixed FILENAMES, unlike every image in the mod,
# because they are published deliverables that the README and the
# print-and-play both link by name. That makes their URLs stable,
# and a stable URL is one TTS answers out of its own asset cache for
# as long as the cache lives: Jon re-read a three-revision-old NAP
# book on 2026-11-11 while jsdelivr was serving the current file
# byte for byte. Nothing was broken. The fetch never happened.
#
# So build_mod hangs the file's own content hash off the URL as ?v=,
# which jsdelivr ignores and TTS keys its cache on. This checks the
# token against the bytes on disk, so a rebuilt book whose URL did
# not move fails here rather than at the table.
_stale = []
for _n, _u in sorted(_books.items()):
    _f = _bookfile(_u)
    if not os.path.exists(_f):
        continue
    _h = hashlib.md5(io.open(_f, "rb").read()).hexdigest()[:8]
    if _u.split("?")[-1] != "v=" + _h:
        _stale.append((_n, _u.split("?")[-1], "v=" + _h))
check("...and its URL carries that file's content hash, so no cache"
      " can pin an old one",
      not _stale, "%r" % (_stale,))

# ...AND SO DOES EVERY IMAGE THE MOD LOADS.
#
# The overlays and the eight dice carry their hash in the FILENAME,
# because make_template and make_dice rename them when the picture
# changes. Every card sheet and card back does not: those names are
# fixed, so a re-rendered deck arrives at a URL TTS already holds and
# the old art goes on showing. The Tyrant Attack cards were lightened
# on 2026-11-12 and would not have changed on the table.
_img_stale = []
for _m in re.finditer(r'"(?:FaceURL|BackURL|ImageURL|ImageSecondaryURL)":'
                      r' "([^"]+\.(?:png|jpg))(\?v=([0-9a-f]+))?"',
                      json.dumps(_sv)):
    _nm = _m.group(1).rsplit("/", 1)[-1]
    _f = os.path.join(ROOT, "images", _nm)
    if not os.path.exists(_f):
        _img_stale.append((_nm, "no such file"))
        continue
    _h = hashlib.md5(io.open(_f, "rb").read()).hexdigest()[:8]
    if _m.group(3) != _h:
        _img_stale.append((_nm, _m.group(3), _h))
check("every image URL carries its own file's content hash",
      not _img_stale, "%r" % (_img_stale[:3],))

# AND THE MANIFEST DOES NOT CARRY IT. REQUIRED_IMAGES.txt is not
# decoration: deploy.py reads it to learn which images the mod needs
# and protects exactly those from --prune. Its regex wants a filename
# followed by whitespace, so a ?v= on the end makes every line miss
# and every image read as unreferenced. deploy refused to run rather
# than delete 67 files, which is the only reason that was caught at
# the desk.
_manifest = text("tts/REQUIRED_IMAGES.txt")
check("...and tts/REQUIRED_IMAGES.txt lists bare filenames, for deploy",
      "?v=" not in _manifest and "MISSING" not in _manifest,
      "tokens in the manifest: %s, missing files: %s"
      % ("?v=" in _manifest, "MISSING" in _manifest))
check("the rulebooks are served from rules/, not images/",
      all("/rules/" in u for u in _books.values()), "%r" % (_books,))
# EACH BOOK GOES HOME TO ITS OWN GAME'S BOX, which is what lets
# showRules put the three it does not want away; the Imposter
# scenario's is the campaign supplement and belongs with NRJ.
_hm = re.search(r"^HOME = \{(.*)\}$", _sv["LuaScript"], re.M)
_homes = dict(re.findall(r"\['([^']+)'\] = '([^']+)'",
                         _hm.group(1) if _hm else ""))
check("every rulebook has a box to go home to",
      all(_homes.get(_want.get(g)) == ("NRJ" if g == "IMP" else g)
          for g in ("BAT", "NAP", "AoS", "IMP")),
      "%r" % ({n: _homes.get(n) for n in _want.values()},))
# AND NOTHING REWRITES A BOOK ANY MORE. setCustomObject on a PDF is
# the mechanism that failed; leaving the call in the script would
# leave the next person to read it believing it works.
# CODE ONLY. The comment above showRules explains what setCustomObject
# did and why it is gone, and a check that reads the prose fails on
# the explanation - which is the trap the spread() check fell into
# further down, and the deck-name check before it.
check("no book has its URL rewritten at the table",
      "setCustomObject" not in _lua_code and ".reload()" not in _lua_code
      and "RULES_GUID" not in _lua_code)

# THE MAT IS STRETCHED OVER THE FELT, so a picture drawn to any other
# rectangle puts every printed box somewhere the cards are not. That is
# not a figure of speech: the mat was widened to the table without the
# drawing being redrawn, and the boxes and the cards ended up working
# from two different tables. Three things have to hold, and all three
# are measurable here.
_tile = [o for o in _sv["ObjectStates"] for k in (o.get("ContainedObjects") or [])
         if False] or None
_fx = re.search(r"FELT_X0, FELT_X1 = (-?[\d.]+), (-?[\d.]+)", _mod)
_fz = re.search(r"FELT_Z0, FELT_Z1 = (-?[\d.]+), (-?[\d.]+)", _mod)
check("build_mod.py records the felt it was measured to", bool(_fx and _fz))


def _jpeg_wh(path):
    """(width, height) of a JPEG, read from its own header."""
    with open(path, "rb") as fh:
        d = fh.read()
    i = 2
    while i < len(d) - 9:
        if d[i] != 0xFF:
            i += 1
            continue
        m = d[i + 1]
        if 0xC0 <= m <= 0xCF and m not in (0xC4, 0xC8, 0xCC):
            return ((d[i + 7] << 8) | d[i + 8], (d[i + 5] << 8) | d[i + 6])
        i += 2 + ((d[i + 2] << 8) | d[i + 3])
    return None


# EVERY GAME THAT LAYS AN OVERLAY, not just NAP. Each one is its own
# tile in its own bag, so they can be - and now are - different felts:
# gold for BAT, turquoise for NAP. Both are stretched over the same
# rectangle, so both have to be drawn to its shape, and a drawing made
# for a different one puts every printed box somewhere the cards are
# not.
if _fx and _fz:
    _fw = float(_fx.group(2)) - float(_fx.group(1))
    _fd = float(_fz.group(2)) - float(_fz.group(1))
    for _g in ("NAP", "BAT", "AoS", "IMP"):
        _mo = [k for o in _sv["ObjectStates"]
               for k in (o.get("ContainedObjects") or [])
               if k.get("Nickname") == "%s Table" % _g]
        _img = [f for f in os.listdir(os.path.join(ROOT, "images"))
                if f.startswith("%s_Table" % _g)]
        check("one %s overlay image ships" % _g,
              len(_img) == 1 and len(_mo) == 1,
              "%d images %r, %d tiles" % (len(_img), _img, len(_mo)))
        if _img:
            _wh = _jpeg_wh(os.path.join(ROOT, "images", _img[0]))
            check("the %s overlay is drawn to the felt's own shape" % _g,
                  bool(_wh) and abs(_wh[0] / float(_wh[1]) - _fw / _fd) < 0.002,
                  "image %r vs felt %.4f" % (_wh, _fw / _fd))
        if _mo:
            _t = _mo[0]["Transform"]
            check("the %s mat is scaled to cover the felt exactly" % _g,
                  abs(2 * _t["scaleZ"] - _fd) < 0.01
                  and abs(_t["scaleX"] - _t["scaleZ"]) < 0.01,
                  "scale %.3f/%.3f for a felt %.2f deep"
                  % (_t["scaleX"], _t["scaleZ"], _fd))
    # AND EVERY GAME HAS A FELT TO BE BUILT FROM. One shared file,
    # unless a game has its own beside it: felt_AoS.jpg would make
    # AoS green again without a line of code changing.
    #
    # WHAT IS NOT HELD HERE is that they are four DIFFERENT felts.
    # That check existed for a day and was wrong the moment Jon said
    # he preferred the turquoise everywhere: four colours was a
    # preference, and a preference written down as an invariant fails
    # the first time somebody changes their mind. The shape is not a
    # preference - a felt cut differently sits differently - so that
    # is what is checked.
    _felts = {}
    for _g in ('BAT', 'NAP', 'AoS', 'IMP'):
        _own = os.path.join(ROOT, 'tts', 'felt_%s.jpg' % _g)
        _fp = _own if os.path.exists(_own) else os.path.join(
            ROOT, 'tts', 'felt.jpg')
        if os.path.exists(_fp):
            _felts[_g] = _fp
    check("every game has a felt to draw its overlay on",
          sorted(_felts) == ['AoS', 'BAT', 'IMP', 'NAP'],
          'felts found for %r' % sorted(_felts))
    _sizes = set(_jpeg_wh(v) for v in _felts.values())
    check("the felts are all one shape",
          len(_sizes) == 1, 'sizes %r' % sorted(_sizes))

check("the template is drawn to the felt build_mod.py records",
      "from build_mod import (EXHAUSTED, FELT_X0, FELT_X1" in _tmpl
      and "X0, X1 = FELT_X0, FELT_X1" in _tmpl)
# Pillow's text engine is blocked here, so the labels come from glyph
# outlines. Without it the overlay cannot be redrawn at all - and it
# has to be redrawn every time the felt is re-measured.
check("the template can draw text without Pillow's text engine",
      "import glyphs" in _tmpl and "glyphs.draw_text(" in _tmpl
      and "ImageFont" not in _tmpl
      and os.path.exists(os.path.join(ROOT, "tts", "glyphs.py")))

# ONE OWNER FOR HOW BIG A DIE IS, and the spacing derived beside it.
# The row is laid out in multiples of a die, so a scale changed without
# the pitch would pile them up - which the harness now measures, with
# the half-width read from the save rather than remembered.
_dscale = sorted(set(o["Transform"]["scaleX"] for o in _sv["ObjectStates"]
                     if o["Name"] == "Custom_Dice"))
check("every die in the save is the one size build_mod.py sets",
      len(_dscale) == 1 and "DIE_SCALE = " in _mod
      and "DIE_SCALE if o['Name'] == 'Custom_Dice'" in _mod,
      "scales present: %r" % (_dscale,))
check("the harness measures the dice it was given",
      "w.die_half = 0.45 * max(" in _ts
      and "f[3] + w.die_half" in _ts
      and "no two dice sit on each other" in _ts)
# Jon placed the rulebook himself; settling it would drop it somewhere
# else and call that the same place.
check("the rulebook is not settled onto anything",
      "if RULES_OBJ then table.insert(t, RULES_OBJ) end" not in _lua
      and "THE RULEBOOK IS NOT SETTLED" in _lua)

# A TWEEN AND A PHYSICS CALL IN THE SAME FRAME FIGHT, and this mod has
# now lost that fight twice: setRotationValue cancelled the stat dice's
# move, and the move cancelled the Chip's turn part way round. Neither
# is visible to the harness, which has no physics - so the shape of the
# fix is checked instead. The turn is handed to setMarker and happens
# after the marker has landed, with an instant setRotation.
check("the setup turns the Chip after it lands, not while it moves",
      re.search(r"setMarker\('Chip'[^;]*CHIP_FACE\[ATTENTION\[1\]\],"
                r"\s*CHIP_FACE_Z\}", _lua)
      and "function setMarker(name, x, z, value, face, onto)" in _lua
      and "o.setRotation({r.x, face[1], face[2]})" in _lua)

# AND A DIE THAT STANDS ON A CARD IS LET GO ABOVE IT. moveMarker used
# one height for every marker, 1.6, which is a height for bare felt: a
# die is 1.62 across, so its underside arrives below the face of a card
# lying on the table, and the move is made with collide off so nothing
# stops it. Three dice in this mod stand on a card, and two of the
# three were seen to end up under it - the Red die on its Rat (Jon,
# 2026-11-12) and the Health die on the Health track before that.
#
# NAMED, NOT COUNTED. "three calls pass ONTO" would pass with the wrong
# three; these are the three, and a fourth on-card die that forgot the
# flag is the failure this is for. The behaviour - that the height
# really does clear the card - is tts/test_setup.py's on_card
# assertions; this is only that each call asks for it.
# TWO, NOT THREE. The Health die stood on the Health track card until
# 2026-11-21; nothing deals that card now, so the only dice that go on
# a card are the two in a Lab Rat's corners.
_onto = ["setMarker('Recovery', batMarkX(1), batMarkZ(), nil, nil, ONTO)",
         "setMarker('Red', batRedX(math.random(BAT_ROWS)), batRedZ(), nil,"
         " nil,\n              ONTO)"]
check("every die a setup stands on a card is dropped onto it",
      all(s in _lua for s in _onto)
      and _lua.count("ONTO)") == len(_onto)
      and "function dropOnto(o, x, z)" in _lua,
      "missing: %r" % ([s[:34] for s in _onto if s not in _lua],))

# The three dice say what the card says. One literal prints all six
# Apprentice sides, so there is nothing to average over.
#
# DERIVED FROM THE MODEL AS OF 2026-11-25, because the 2s were typed in
# here and REC rose to 3 that day - the compensation for the Special
# Recovery age rule - and this check was the only thing in the suite that
# had the old value written into it. Four owners now: the card literal, the
# die the mod stands up, the sentence the mod says, and Setup in the book.
_stats = (sn["HP_START"], sn["STR_START"], sn["REC_START"])
check("an Apprentice starts NAP at the stats its own card prints",
      sn["HP_START"] == sn["STR_START"]
      and "HP %d &nbsp;|&nbsp; STR %d &nbsp;|&nbsp; REC %d" % _stats in text(
          "generator/build_nap.py")
      and "NAP_START = %d" % sn["HP_START"] in _lua
      and "NAP_REC_START = %d" % sn["REC_START"] in _lua
      and "setMarker('Recovery', sx[3], STAT_Z, NAP_REC_START)" in _lua
      and "is out at %d HP / %d STR / %d REC" % _stats in _lua
      and "All six begin at <b>%d HP / %d STR / %d REC</b>" % _stats
      in text("rules/nap.html"),
      "model says %d HP / %d STR / %d REC" % _stats)
# ONE DROP FOR ALL THREE GAMES. NAP, AoS and the Imposter scenario all
# stand their character in the same corner and all three print their
# stats on it, so the row of dice under it is one rule measured from
# the card rather than three numbers that can drift apart. Every
# character card in the set is landscape, which is what makes one drop
# right for all of them.
check("the stat dice are a row under the character card, measured from it",
      "STAT_DROP = CARD_W / 2 + 1.3" in _lua
      and "function statZ(cardZ) return cardZ - STAT_DROP end" in _lua
      and "function statRow(x)" in _lua
      and _lua.count("statRow(") == 4
      and "MARKER_X" not in _lua)
# Three stat rows - NAP, AoS, the Imposter scenario - and ONE die
# placed once more, in BAT, where it is not a stat at all but the
# marker on the active Lab Rat's corner.
#
# NOT [4, 3, 3]. Those were the counts the day it was written and the
# extra one was the Health die, which was the bug: the moment the
# marker became the Strategy die, and then the Recovery die, the
# numbers moved and a check about
# stat rows failed for a reason that had nothing to do with stat rows.
# What has to hold is that the three rows are complete and exactly one
# game marks a card as well.
_mk = dict((d, _lua.count("setMarker('%s'" % d))
           for d in ("Health", "Strategy", "Recovery"))
_mark_die = _mark_src.group(1) if _mark_src else None
# ...AND BAT NOW STANDS TWO OF THEM IN A COLUMN. Jon's placing: the
# Health and REC dice beside the exhausted corner rather than lost in
# the shared dice band. So all three now appear four times - three
# stat rows each, plus BAT once - but for three different reasons,
# and a bare "all four" would pass if BAT dealt a second stat row by
# mistake. The two column calls are named here so the count has
# something behind it.
#
# THE COLUMN IS MEASURED OFF THE BAND, not typed: EXHAUST_Z is
# generated by build_mod from the same EXHAUSTED the mat is drawn
# from, so moving that corner moves the dice beside it.
# Health is placed once more than the other two: three stat rows,
# BAT's column beside the exhausted corner, and the Tyrant battle
# standing it on the Health track - on the layer's space when the
# difficulty gives one, and parked on the card when it does not.
# FOUR EACH, AND THE FOURTH IS BAT'S. Health was placed five times
# while the Tyrant battle stood it on the Health track card; nothing
# deals that card since 2026-11-21, so the Health die stays in BAT's
# own column all game and all three dice are placed the same number
# of times for the same two reasons.
check("...and every game that has a character places all three of them",
      _mark_die in _mk
      and _mk == {"Health": 4, "Strategy": 4, "Recovery": 4}
      and "setMarker('Health', BAT_STAT_X, BAT_STAT_Z[1])" in _lua
      and "setMarker('Strategy', BAT_STAT_X, BAT_STAT_Z[2])" in _lua
      # ...AND NOTHING STANDS IT ON A CARD ANY MORE. A predicate a
      # name cannot satisfy: this is the call that did it.
      and "setMarker('Health', bx, bz" not in _lua_code
      and "BAT_STAT_X = BAT_EXHAUST_X0 -" in _lua
      and "EXHAUST_Z[1]" in _lua
      and re.search(r"^EXHAUST_Z = \{", _sv["LuaScript"], re.M),
      "%r, with %r marking the active Rat" % (_mk, _mark_die))

# THE BATTLE CARRIES THE DIAL, it does not reset it. One Experiment in
# the deck writes to the Tyrant's core Health - Degraded Tissue Study,
# "reduce the Prototyrant's Health dial by 2" - and startBattle used
# to turn the dial back to the difficulty's printed core, which threw
# that away on the way into the fight it was earned for. The rulebook
# had the same hole in the same place: its Awakening paragraph said
# the dial is SET to the core Health.
#
# THREE SOURCES AND ALL THREE NAMED, because this script has no
# onSave: STATE.dial is 0 again after a reload while the disc still
# shows the number, so the disc is asked first and the difficulty is
# only the last resort.
_satk = text("simulation/bat.py")
_sdial = text("generator/build_bat.py")
# THE DIAL IS THE PROTOTYRANT'S HEALTH, and the battle still has to
# carry what the table left on it rather than resetting it: one
# Experiment raises it - "If successful, raise the Prototyrant's Health
# track by 2" - and the raise is earned in a lab phase that is long and
# a dial is a thing players lean on. The shape of the fallback chain is
# the invariant - read the dial, else a non-zero STATE.dial, else the
# rulebook's 12 - because a 0 is not an answer: STATE.dial starts and
# reloads at 0, and a battle announcing 0 Health is worse than one
# that resets.
check("the Tyrant battle carries the dial rather than resetting it",
      "local hp = dialRead() or (((STATE.dial or 0) > 0) and STATE.dial)"
      in _lua
      and "or PROTO_HP" in _lua
      and re.search(r"function dialRead\(\).*?getRotationValue", _lua, re.S)
      and "CARRIED, NOT RESET" in _lua
      # ...AND THE ROUNDS ARE STILL A REAL LIMIT, even though nothing
      # on the table counts them: the battle reads the rung's number
      # and announces it. "If its last Splice is still standing when
      # your difficulty's rounds are used up, it finishes the job and
      # the Rats lose."
      and "local rounds = BAT_DIFF[STATE.difficulty][2]" in _lua
      and "' ROUNDS.' .." in _lua
      # ...AND readoutOut TAKES NO NUMBER, so nothing can hand it one
      # that is not the dial. A predicate a name cannot satisfy: this
      # is the call, and the only argument it ever took was the rounds.
      and "function readoutOut()" in _lua
      and not re.search(r"readoutOut\([^)]", _lua_code)
      and "rounds are used up" in _RULES["bat"]
      and "the Rats lose" in _RULES["bat"]
      # ...AND batrev BOUNDS THE BATTLE BY IT, at the call site rather
      # than in a
      # table. Nothing is asserted ABSENT here: the first version of this
      # forbade "self.round_limit - self.rounds", which is a real line in
      # the clock-aware pass rule, so the check failed on correct code.
      and "if self.round_limit and self.rounds >= self.round_limit:"
      in _satr,
      "the battle does not carry the Health it was handed")
# AND THE ROUNDS ARE A SEPARATE THING FROM IT, on the plate beside the
# dial. Two quantities on one object is how the printed game's core
# Health and Health got confused for each other, and this pair can end
# the game two different ways - so one number must not write the other.
check("...and the Prototyrant's Health is 12, on the dial and nowhere else",
      "BAT_PROTO_HP = 12" in _lua
      and _lua_code.count("local PROTO_HP = BAT_PROTO_HP") == 2
      and not re.search(r"local PROTO_HP = \d", _lua_code)
      and "{CHIP_DIAL[PROTO_HP] or CHIP_DIAL[0], 0})" in _lua
      and "{CHIP_DIAL[hp] or CHIP_DIAL[0], 0})" in _lua
      # ...AND THE PLATE IS NEVER HANDED THE HEALTH.
      and "readoutOut(hp)" not in _lua_code
      and "readoutOut(PROTO_HP)" not in _lua_code
      and _brev["SHARED_HP_START"] == 12,
      "lua and batrev disagree on the Prototyrant's starting Health, or"
      " the plate has been handed it")
# NOTHING IS TURNED UP OUT OF THE ATTACK DECK. A card was flipped at
# setup to seed the first commit colour, which also showed the table
# one of the seven attacks coming for it; Jon, 2026-11-17. The deck is
# one card longer for it and the Rats' first attack honours no colour,
# which has to be true in all four places or the lab and the table
# play different games.
_atk_block = re.search(r"deckOut\('Tyrant Attacks'.*?end\)", _lua, re.S)
check("nothing is turned up out of the Tyrant Attack deck",
      _atk_block is not None
      and "d.shuffle()" in _atk_block.group(0)
      and "takeObject" not in _atk_block.group(0)
      and "leave them that way" in _RULES["bat"]
      and "first attack is unrestricted" in _RULES["bat"]
      and "FIRST_ATTACK_FREE = True" in _satk,
      "the battle still flips a card, or one of the three disagrees")

# THE SPLICE PHASE DIALS SHIP SET TO THE PRINTED GAME. Both of these
# change the Splice Phase for every game the model plays, so a dial left
# on silently invalidates every BAT figure in this repository - and
# neither one is visible in any output a reader would check. The
# predicates are about the SOURCE OF THE ROW and the fallthrough branch,
# not about a value in BORROWABLE: a table of four colour lists proves
# nothing about which index is ever looked up.
_brow = _method("simulation/bat.py", "borrow_row")
_bfor = _method("simulation/bat.py", "borrow_for")
check("the borrow table still reads off the borrower's Upgrades",
      # the dial ships at the printed reading...
      'BORROW_RULE = "upgrades"' in _satk
      # ...the lookup really goes through it, so the dial cannot be
      # decoration sitting beside a hard-coded len(rat.upgrades)...
      and "BORROWABLE[min(3, self.borrow_row(rat))]" in _bfor
      # ...and "upgrades" is the fallthrough, which is what makes the
      # printed rule the one you get when the dial is misspelled.
      and "return len(rat.upgrades)" in _brow
      # The alternatives exist, so deleting them cannot pass this.
      and 'BORROW_RULE == "flat"' in _brow
      and 'BORROW_RULE == "splices"' in _brow
      ,
      "BORROW_RULE does not ship at the printed reading, or nothing reads it")

# AND THE BOOK'S OWN TABLE IS HELD AGAINST batrev, which is the model of
# record. The column narrowed on the borrower's own Upgrades in the printed
# game; here the Prototyrant holds every graft, so the row rises as IT grows
# and the lab's borrowing degrades as the machine does. Printed as
# "3 or more", because a graft count does not stop at three any more.
check("rules/bat.html's borrow table reads the Prototyrant's grafts, and "
      "batrev does too",
      "Grafts held" in _RULES["bat"]
      # REWORDED 2026-11-25: the old lead-in explained WHY the table
      # narrows, which is rationale. What has to stay is that the book
      # reads the Prototyrant's grafts and not something else.
      and "how many grafts the Prototyrant holds" in _RULES["bat"]
      and "3 or more" in _RULES["bat"]
      and "return min(3, len(self.grafts))" in _satr
      and "Upgrades held" not in _RULES["bat"],
      "the book and batrev no longer agree on what narrows a borrow")

# THE BORROW POLICY IS WORTH MORE THAN ANY RULE IN THE GAME: 10 to 12
# points, measured 2026-11-18, which is larger than every rule change
# priced in this repository put together. It is a POLICY and not a rule -
# the rules say what a Rat MAY borrow, never what it SHOULD - so nothing
# in any player-facing file can contradict it and no other check would
# ever notice it move. Every published BAT figure is measured through
# "short_best", so this one guards the figures themselves.
check("the borrow POLICY still ships as the one BAT's figures were measured "
      "through",
      'BORROW_POLICY = "short_best"' in _satk
      # The policy really reaches the choice of die...
      and 'pick = min if BORROW_POLICY == "short_cheapest" else max' in _bfor
      # ...and the two restraints that beat it are implemented, so the
      # check cannot be satisfied by deleting the comparison.
      and 'if BORROW_POLICY == "never":' in _bfor
      and 'BORROW_POLICY == "decisive"' in _bfor
      # The decisive policy needs the gap, so the call sites must pass it;
      # without this the policy silently never declines anything.
      and "self.borrow_for(rat, target - expected)" in _satk
      # And the finding is written down where a reader of the figures
      # would meet it, rather than living only in this predicate.
      and "ten to twelve points" in text("simulation/price_borrow.py").lower(),
      "BORROW_POLICY moved, or nothing reads it, or the finding went "
      "unrecorded")

# ONE VALUE SERVES BOTH SIDES, which is what the card prints and what the
# book describes. Jon asked for two numbers - a Rat value of Tyrant minus
# one - and simulation/price_split_values.py measures that design at zero
# on the Rat side and off a cliff on the Tyrant side, so the dials exist
# and all five ship at the printed game.
#
# THE COUNTS ARE THE POINT OF THIS CHECK. A value dial wired into some of
# its construction sites and not others builds the Tyrant's wall out of
# two different numbers, and no output any reader checks would show it.
# Three of the six Splice sites were missed on the first pass here.
check("one Value still serves both the Rat and the Tyrant",
      "RAT_VALUE_DELTA = 0" in _satk
      and "TYRANT_VALUE_DELTA = 0" in _satk
      and 'RAT_BLOCK_RULE = "spend"' in _satk
      and 'SPLICE_CHOICE = "never"' in _satk
      and "UPGRADE_CAP = 3" in _satk
      # Every Splice and every Upgrade is built through the helper...
      and "Splice(splice_value(" not in _satk
      and "Upgrade(splice_value(" not in _satk
      and _satk.count("Splice(tyrant_value(") == 6
      and _satk.count("Upgrade(rat_value(") == 2
      # ...and the readings that would move them are really implemented,
      # so deleting the question cannot pass this.
      # "absorb" takes TWO call sites - picking the card that soaks, and
      # letting the overflow through - and naming the dial proves neither.
      # Asserting only the name let a mutation delete half of it and pass.
      and "armor = [min(able, key=lambda u: u.value) if able" in _satk
      and "max(0, hits - lost.value)" in _satk
      and 'RAT_BLOCK_RULE == "threshold"' in _satk
      and "def choose_splice(" in _satk
      ,
      "a Value dial ships on or is half-wired")

# AND IN THE GAME AS IT SHIPS, ONE VALUE DOES THREE JOBS - which is the
# reason one lost Experiment is worth so much: the part you keep caps your
# dice, the part it takes sets the Target you must meet in one blow, AND
# sets how many dice it rolls back. The book prints all three and batrev
# reads Value at all three CALL SITES, not in a table.
check("rules/bat.html prints Value's three jobs, and batrev reads it at "
      "all three",
      "Value is the stake" in _RULES["bat"]
      and "the dice cap for the round it is exposed in" in _RULES["bat"]
      and "the damage you must land in one blow" in _RULES["bat"]
      and "cap = graft.value if graft is not None else NO_GRAFT_CAP" in _satr
      and "need = splice.value - splice.dmg if PARTIAL_DAMAGE" in _satr
      and "draws = min(SPLICE_ATTACK_DICE or splice.value" in _satr,
      "the book and batrev disagree on what a part's Value does")

# THE SPLICE TRACK IS THE CLOCK: the phase runs while there are fewer than
# 5 Splices, and play tops the track up to exactly 5 before the battle. So
# what a volunteered Splice really costs is a TURN, and the dial that prices
# it has to leave both the clock and the top-up reading the same count or
# the phase quietly runs long.
check("a volunteered Splice still ticks the clock",
      'SPLICE_CHOICE_CLOCK = "advance"' in _satk
      # Both other readings are really implemented, so deleting the
      # question cannot satisfy this.
      and 'SPLICE_CHOICE_CLOCK == "replace"' in _satk
      and 'SPLICE_CHOICE_CLOCK == "free"' in _satk
      and "self.volunteered += 1" in _satk
      # "replace" has to splice OVER the biggest card on the track, not
      # append beside it - naming the dial proves nothing.
      and "self.splices[top] = fresh" in _satk
      # AND THE TWO COUNTS HAVE TO AGREE. The clock and the end-of-phase
      # top-up both read the track, and a discount applied to one but not
      # the other builds a Tyrant out of the wrong number of cards.
      and _satk.count("len(self.splices) - self.volunteered < 5") == 2
      and "self.volunteered = 0" in _satk,
      "the volunteer dial ships on, is half-wired, or the clock and the "
      "top-up stopped counting the track the same way")

# THE QUESTION THE VOLUNTEER DIAL PRICED DOES NOT EXIST ANY MORE. It asked
# what it should cost to hand the Tyrant a card you were allowed to keep,
# and in this design EVERY Experiment grafts one part and reclaims the
# other whether you win or lose - success only decides who picks. So the
# clock is the Experiment deck and the book must not print a Splice count
# that wakes anything, while batrev must graft on BOTH branches.
check("every Experiment grafts a part, so there is no Splice clock left",
      "Five Splices and it wakes up" not in _RULES["bat"]
      and "awakens the moment it reaches" not in _RULES["bat"]
      and "both Splices leave the deck" in _RULES["bat"]
      and "self.grafts.append(Part(graft))" in _satr
      and "graft = order[-1]" in _satr
      and "graft = max(parts, key=graft_score)" in _satr,
      "the book or batrev stopped giving each side a part every time")

check("Red still comes back free, as the printed rule has it",
      "RED_COSTS_REC = False" in _satk
      # The two charged readings are implemented, so this check cannot be
      # satisfied by deleting the dial and the question with it.
      and 'RED_COSTS_REC == "always"' in _satk
      and 'RED_COSTS_REC == "afford"' in _satk
      and "self.red_down = True" in _satk
      # "afford" has to be able to withhold Red, not merely charge for it:
      # the holder test is where that lands.
      and "has_red = self.red_holder is rat and not getattr(" in _satk,
      "the model charges for Red")

# RED IS SET ASIDE IN THE LAB AND EXHAUSTS IN THE BATTLE, and the two
# halves are a measured design choice rather than a tidy symmetry. Carried
# into the battle, the lab's set-aside rule made Red the one die that never
# runs out: usable in 100% of rounds and worth about one whole Splice.
# Exhausting, it is worth half that and usable in two rounds out of three -
# a die with downtime, which is the point. So the book prints both halves
# and batrev has to be running the second one.
check("rules/bat.html sets Red aside in the lab and exhausts it in the "
      "battle, and batrev agrees",
      "set aside rather than exhausted" in _RULES["bat"]
      and "exhausts</b> like any other committed die" in text("rules/bat.html")
      and "counts toward the exposed graft" in _RULES["bat"]
      and "RED_SET_ASIDE_IN_BATTLE = False" in _satr
      # ...and the dial is really wired, so deleting the question cannot
      # satisfy this: the commit site has to branch on it.
      and "if d is self.red and RED_SET_ASIDE_IN_BATTLE:" in _satr
      and "RED_IN_BATTLE = True" in _satr,
      "the book and batrev disagree about Red in the battle")

# The overlay's three box labels are one size, and make_template proves
# it at build time rather than leaving it to the eye: `fit` can shrink
# one of them below what it was asked for.
_tmpl = text("tts/make_template.py")
check("the overlay's box labels are all one size",
      "LABEL_PT = 34" in _tmpl
      and "size=LABEL_PT" in _tmpl
      and "assert len(sizes) == 1" in _tmpl
      and not re.search(r"label\(d, \"[A-Z][^\"]*\", [\d.]+, \w+\[\d\], \d\d",
                        _tmpl))

print()
if SKIPPED:
    print("%d check(s) COULD NOT RUN here:" % len(SKIPPED))
    for s in SKIPPED:
        print("   ~", s)
    print()
print("%d check(s) failed" % len(FAILS))
for f in FAILS:
    print("   -", f)

sys.exit(len(FAILS))
