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
