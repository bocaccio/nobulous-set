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
import io
import json
import os
import re
import sys

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


def check(label, ok, detail=""):
    print("  %-52s %s%s" % (label, "PASS" if ok else "FAIL",
                            "" if ok else "  " + detail))
    if not ok:
        FAILS.append(label)


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
rows("build_nap TASKS vs NAP_TASKS", gn["TASKS"], jt,
     {"name": (G(0), G(0)), "request": (G(4), G(1)), "demand": (G(6), G(2)),
      "color": (G(2), G(3)), "credits": (G(3), G(4))})
# simulation TASKS: Req, Dem, color, credits
rows("nap.py TASKS vs NAP_TASKS", sn["TASKS"], jt,
     {"request": (G(0), G(1)), "demand": (G(1), G(2)),
      "color": (G(2), G(3)), "credits": (G(3), G(4))})
rows("build_nap TASKS vs nap.py TASKS", gn["TASKS"], sn["TASKS"],
     {"request": (G(4), G(0)), "demand": (G(6), G(1)),
      "color": (G(2), G(2)), "credits": (G(3), G(3))})
je = js_literal("playtest/dist/suite.js", "NAP_EXAMS")
rows("build_nap EXAMS vs NAP_EXAMS", gn["EXAMS"], je,
     {"name": (G(0), G(0)), "subject": (G(1), G(1)),
      "color": (G(2), G(2)), "target": (G(3), G(3))})
js = js_literal("playtest/dist/suite.js", "NAP_SETBACKS")
rows("build_nap SETBACKS vs NAP_SETBACKS", gn["SETBACKS"], js,
     {"name": (G(0), G(0)), "color": (G(1), G(2)), "target": (G(2), G(1))})

print()
print("AoS - generator/aos.py and simulation/aos.py vs playtest")
ga = py_tables("generator/aos.py")
sa = py_tables("simulation/aos.py")
jpt = js_literal("playtest/dist/app.js", "PROGRAM_TARGETS")
jpm = js_literal("playtest/dist/app.js", "PROGRAM_MARKS")
for deck, key in (("Routine", "ROUTINE"), ("Specialized", "SPECIALIZED"),
                  ("Unstable", "UNSTABLE"), ("Advanced", "ADVANCED")):
    src = ga[key]
    rows("aos.py %s vs PROGRAM_TARGETS front" % deck,
         src, jpt[deck]["front"], {"targets": (G(1), lambda r: r)})
    rows("aos.py %s marks vs PROGRAM_MARKS" % deck,
         src, jpm[deck], {"mark": (G(2), lambda r: r)})
    # the Overheated face is the Stable one with +1 on the marked element
    want = []
    for name, t, mark in [(r[0], list(r[1]), r[2]) for r in src]:
        t[mark] += 1
        want.append(t)
    rows("%s back == front +1 at the mark" % deck,
         want, jpt[deck]["back"], {"targets": (lambda r: r, lambda r: r)})

jsrc = text("playtest/dist/app.js")
check("MISSES_TO_NEGATE: aos.py %r == app.js" % sa.get("MISSES_TO_NEGATE"),
      ("const MISSES_TO_NEGATE = %d;" % sa["MISSES_TO_NEGATE"]) in jsrc)
check("rules/aos.html states the negate rule",
      "exhaust 2 misses" in text("rules/aos.html").lower())
check("build_aos.py footers state the negate rule",
      text("generator/build_aos.py").count("exhaust 2 misses on them") >= 3)
check("rules/nap.html does not promise a higher Demand Target",
      "higher Target" in text("rules/nap.html")
      and "often a higher Target" in text("rules/nap.html"))

print()
print("NRJ - generator/build_nrj.py vs playtest")
gr = py_tables("generator/build_nrj.py")
for key, jsname, fields in (
        ("FOLLOWING", "NAP_FOLLOWING", None),
        ("IMPOSTOR", "NAP_IMPOSTOR", None),
        ("DEVIOUS", "NAP_DEVIOUS", None),
        ("SCEN", "SCENARIOS", None)):
    try:
        j = js_literal("playtest/dist/suite.js", jsname)
    except KeyError as ex:
        check("%s vs %s" % (key, jsname), False, str(ex))
        continue
    g = gr[key]
    if len(g) != len(j):
        check("%s vs %s" % (key, jsname), False,
              "%d vs %d rows; gen[0]=%r js[0]=%r" % (len(g), len(j), g[0], j[0]))
        continue
    # The Target index differs by table: SCEN and IMPOSTOR carry a domain or
    # subject before it, so the pair is named per table rather than guessed.
    ti = {"FOLLOWING": (2, 2), "IMPOSTOR": (3, 3),
          "DEVIOUS": (2, 2), "SCEN": (3, 3)}[key]
    bad = [(a[0], a[ti[0]], b[ti[1]]) for a, b in zip(g, j)
           if a[0] != b[0] or a[ti[0]] != b[ti[1]]]
    check("%s vs %s - %d names and Targets" % (key, jsname, len(g)), not bad,
          "%r" % (bad[:3],))

# THE IMPOSTOR TASK DOTS. Every NAP Assignment prints a recovery-colour dot
# and three printed rules read "that Assignment's color dot" - Required
# Effort, completing or storing progress, and the colour the Primary queues
# for the next Time Slot. The 4 Impostor Tasks printed none until 2026-10-31,
# so the card, the model (which inherited the replaced Task's dot) and the
# lab (which fell back to "P") all disagreed, and nothing here could see it.
IMP_DOTS = (("Neural Extraction Practicum", "P"),
            ("Load-Bearing Prosthetics", "B"),
            ("Emergency Specimen Handling", "Y"),
            ("Containment Drill", "G"))
gen_imp = {r[0]: r[2] for r in gr["IMPOSTOR"]}
js_imp = {r[0]: r[2] for r in js_literal("playtest/dist/suite.js",
                                         "NAP_IMPOSTOR")}
sim_imp = dict((s, d) for s, d, _r, _t in
               py_tables("simulation/nap.py")["IMPOSTOR"])
sim_subj = {n: s for (n, s, _d, _r, _t, _e) in gr["IMPOSTOR"]}
bad = [n for n, d in IMP_DOTS
       if gen_imp.get(n) != d or js_imp.get(n) != d
       or sim_imp.get(sim_subj.get(n)) != d]
check("the 4 Impostor Task dots agree in the cards, the lab and nap.py",
      not bad, "%r" % (bad,))

# The Tier III decks the lab keeps outside suite.js. Every field is compared,
# because the claim CONDITION now carries the cost clause that prices it -
# "Claiming gives up..." - and a lab that kept the old wording would teach the
# player a rule the rulebooks no longer have.
for key, path, jsname in (("NOTES", "playtest/dist/bat.js", "BAT_NOTES"),
                          ("BACKDOOR", "playtest/dist/app.js",
                           "AOS_BACKDOOR")):
    try:
        j = js_literal(path, jsname)
    except KeyError as ex:
        check("%s vs %s" % (key, jsname), False, str(ex))
        continue
    g = gr[key]
    if len(g) != len(j):
        check("%s vs %s" % (key, jsname), False,
              "%d vs %d rows" % (len(g), len(j)))
        continue
    bad = [a[0] for a, b in zip(g, j) if list(a[:3]) != list(b[:3])]
    check("%s vs %s - %d cards, name, condition and effect"
          % (key, jsname, len(g)), not bad, "%r" % (bad[:3],))

check("the Tier III claim cost is printed on all 12 BAT and AoS cards",
      text("generator/build_nrj.py").count(
          "Claiming gives up the next Upgrade a completed Experiment earns.")
      == 6
      and text("generator/build_nrj.py").count(
          "Claiming gives up the next Program Reward you would claim.") == 6)

check("the campaign is Tier III only in all four books",
      all("Tier III\nonly" in text(f) or "Tier III only" in text(f)
          for f in ("rules/nrj.html", "rules/bat.html", "rules/nap.html",
                    "rules/aos.html")))

# HOW MANY CARDS ARE RETAINED, in the three places that say so. NAP 3, BAT 2,
# AoS 2: with one card value the pool is just a count, and seven is the count
# that reads 50.6%. Six reads 41.5% and eight 57.8%, so a place that drifts by
# one card drifts by about eight points of win rate.
check("finale.py retains 3 NAP / 2 BAT / 2 AoS",
      "RETAIN = (3, 2, 2)" in text("simulation/finale.py"))
check("suite.js retains the same",
      "const RETAIN={NAP:3,BAT:2,AoS:2};" in text("playtest/dist/suite.js"))
check("nrj.html's standalone mode deals the same",
      "<b>3 Opportunities, 2 Notes and 2 Routines</b>" in text("rules/nrj.html")
      and "At most seven retained cards" in text("rules/nrj.html"))

# RETAINED OR NOT - one value. The spent/unspent split was dropped on
# 2026-10-30 because nothing on the table records which a card is. A file
# that kept it would be asking the player for bookkeeping the others do not.
check("a retained card is worth 2, with no spent/unspent split",
      "Card(game, CARD_VALUE)" in text("simulation/finale.py")
      and "CARD_VALUE = 2" in text("simulation/finale.py")
      and "const NRJ_CARD_VALUE=2;" in text("playtest/dist/suite.js")
      and "val:NRJ_CARD_VALUE" in text("playtest/dist/suite.js"))
check("no file still halves a card for having been spent",
      "SPENT" not in text("simulation/finale.py")
      and "c.used" not in text("playtest/dist/suite.js")
      and "never spent it" not in text("rules/nrj.html"))

# THE DIFFICULTY LADDER names its dice, so all three files carry the same
# four rows of yellow / green / blue / purple or the lab is not playing the
# game the book describes. The counts are not interchangeable: the same
# total taken from different colours measured 28.7% against 38.4%.
LADDER = (("easy", (0, 0, 0, 0)), ("standard", (3, 2, 2, 2)),
          ("hard", (3, 3, 3, 2)), ("nobulous", (3, 3, 4, 4)))
sim = text("simulation/finale.py")
check("finale.py carries the ladder as a per-colour table",
      'TIRED_COLOURS = ("yellow", "green", "blue", "purple")' in sim
      and all('"%s": (%s)' % (lvl, ", ".join(str(n) for n in c)) in sim
              for lvl, c in LADDER))
check("suite.js carries the same four rows",
      'const NRJ_TIRED_COLORS=["yellow","green","blue","purple"];'
      in text("playtest/dist/suite.js")
      and "const NRJ_LADDER={%s};"
      % ",".join("%s:[%s]" % (lvl, ",".join(str(n) for n in c))
                 for lvl, c in LADDER) in text("playtest/dist/suite.js"))
nrj = text("rules/nrj.html")
check("nrj.html prints the same four rows",
      "Four difficulties" in nrj
      and all("".join("<td>%d</td>" % n for n in c) in
              nrj.replace("\n", "").replace("      ", "")
              for lvl, c in LADDER if lvl != "easy"))
check("and nobody exhausts the single red die",
      "red" not in sim[sim.index("TIRED_COLOURS"):
                       sim.index("START_TIRED = ")]
      and '"red"' not in text("playtest/dist/suite.js")[
          text("playtest/dist/suite.js").index("NRJ_TIRED_COLORS"):
          text("playtest/dist/suite.js").index("NRJ_LADDER")])

# THE EXHIBIT FACE. Target and Damage are printed now, so the rulebook must
# NOT still be telling the player to subtract 5.
nrjgen = text("generator/build_nrj.py")
check("the Exhibit face prints Target and Damage",
      "def exhibit_body" in nrjgen and "EXHIBIT_OFFSET = 5" in nrjgen
      and "BIG_TARGET = 5" in nrjgen
      and '<div class="biglbl">Damage</div>' in nrjgen)
check("and the rulebook no longer asks for the subtraction",
      "minus 5" not in nrj
      and "Each Exhibit prints its <b>Target</b> and its <b>Damage</b>" in nrj)
check("the five Rewards are reworded for the finale",
      nrjgen.count("When this Exhibit falls") == 5)

check("the Research Pool is the Tier III cards, not the games' own decks",
      "the Tier III cards you claimed" in text("rules/nrj.html")
      and "6 Research Notes" in text("rules/nrj.html")
      and "6 Devious Opportunities" in text("rules/nrj.html")
      and "6 Backdoor Routines" in text("rules/nrj.html"))

# The finale restores five printed Rewards by NAME, in three places: the
# rulebook, suite.js's NRJ_REWARDS and finale.py's REWARDS. A renamed card
# would silently stop paying, so the names are checked against the deck.
print()
print("NRJ - the five restored Reward cards")
scen = gr["SCEN"]
printed_rewards = set(r[0] for r in scen if r[2].endswith("Reward"))
js_rewards = set(js_literal("playtest/dist/suite.js", "NRJ_REWARDS"))
sim = text("simulation/finale.py")
rules = text("rules/nrj.html")
check("suite.js names 5 Reward cards", len(js_rewards) == 5,
      "%d: %s" % (len(js_rewards), sorted(js_rewards)))
missing = sorted(js_rewards - printed_rewards)
check("every one is printed as a Reward card", not missing, "%s" % missing)
for name in sorted(js_rewards):
    check("  %s in finale.py and the rulebook" % name,
          name in sim and name in rules)

print()
print("BAT - rules and app")
jb = text("playtest/dist/bat.js")
hb = text("rules/bat.html")
hbd = js_literal("playtest/dist/bat.js", "HEALTH_BY_DIFFICULTY")
check("bat.js Tyrant Health 9/10/12/14 (%s)"
      % "/".join(str(hbd[k]) for k in ("Easy", "Standard", "Hard", "Nobulous")),
      [hbd[k] for k in ("Easy", "Standard", "Hard", "Nobulous")] == [9, 10, 12, 14])
check("bat.js ROUND_LIMIT = 8", "ROUND_LIMIT = 8" in jb or "ROUND_LIMIT=8" in jb)
check("rules/bat.html: 8-round containment breach", "8 rounds" in hb or "eight rounds" in hb)
check("rules/bat.html: Splice met in one attack",
      "one attack" in hb.lower())
check("rules/bat.html: no commit cap left",
      "up to 6 dice" not in hb.lower())
# Buff HP is no longer the difficulty dial, but the card survives in the PnP
# as an optional tracker - so the test is that it is marked optional, not
# that the words are absent.
check("rules/bat.html: Buff HP demoted to an optional tracker",
      "Buff HP" in hb and "optional" in hb.lower()
      and "Tyrant Health" in hb)

print()
print("%d check(s) failed" % len(FAILS))
for f in FAILS:
    print("   -", f)

sys.exit(len(FAILS))
