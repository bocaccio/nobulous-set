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
# "restriction" is the printed clause itself, and nothing compared it until
# 2026-11-08: the four rows below are what a Final Exam IS, and the clause
# was the one field the card, the lab and the model could disagree about in
# silence. Neural Response Screening did, for weeks, in all three at once.
rows("build_nap EXAMS vs NAP_EXAMS", gn["EXAMS"], je,
     {"name": (G(0), G(0)), "subject": (G(1), G(1)),
      "color": (G(2), G(2)), "target": (G(3), G(3)),
      "restriction": (G(4), G(4))})
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
      and sn["EXAMS"][6][3].get("crit_val") == {"any": 1}
      and je[6][5] == {"scoring": "critAll1"},
      "card=%r model=%r lab=%r" % (_exam_text.get("Neural Response Screening"),
                                   sn["EXAMS"][6][3], je[6][5]))
# A key in a rule dict is a table entry, and AGENTS.md's warning applies: the
# lab has to be caught READING it. "critAll1" sat in NAP_EXAMS for one commit
# with nothing scoring it, which is the shape of every claim in this repo
# that has ever passed while the card did nothing.
check("the lab scores every Crit at 1 where that card says so",
      'rule.scoring==="critAll1"' in _suite
      and "?critWorth:1" in _suite,
      "no critAll1 scoring site in playtest/dist/suite.js")
# The lab blocked Resolve until the restriction was met, so a clause the dice
# decide - and that STR cannot be spent to retry once it is gone - could
# dead-end an exam with no way forward. Only roll-outcome clauses can do
# that, and this was the only one that was unanswerable.
check("the lab no longer blocks Resolve on a Crit nobody can commit for",
      "rule.needCrit" not in _suite
      and not any("needCrit" in r[5] for r in je),
      "suite.js still fails an exam for want of a Crit")
check("no Final Exam still prints Assignment language",
      not any("complete this Assignment" in r[4] for r in gn["EXAMS"])
      and not any("complete this Assignment" in r[4] for r in je),
      "an exam still asks to COMPLETE itself, which exams do not do")
check("EXAM_CRIT_GATE still restores the printed gate and ships off",
      sn["EXAM_CRIT_GATE"] is False
      and 'if EXAM_CRIT_GATE and rule.get("crit")' in text("simulation/nap.py"),
      "EXAM_CRIT_GATE=%r" % (sn.get("EXAM_CRIT_GATE"),))
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
                  ("Unstable", "UNSTABLE"), ("Advanced", "ADVANCED")):
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
check("the lab refuses to roll an element with no dice",
      "Allocate at least one die first." in text("playtest/dist/app.js"))

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
check("the lab no longer screens the corrupt colour against the dots",
      "need.has(c)" not in _jsrc_a)
# Each reveal re-rolls: the cards say "a randomly selected color" and
# "randomly select one element", which is per card, not per game.
check("the lab re-rolls the corruption picks on every reveal",
      "state.corruptColor = null; state.corruptElement = null;" in _jsrc_a)
# The lab's dot table is generated from the same REQ_MAP as the model's.
_jreq = js_literal("playtest/dist/app.js", "PROGRAM_REQS")
_lab_wrong = []
for deck, key in (("Routine", "ROUTINE"), ("Specialized", "SPECIALIZED"),
                  ("Unstable", "UNSTABLE"), ("Advanced", "ADVANCED")):
    for pid, row in enumerate(ga[key]):
        name, targets = row[0], row[1]
        want = [_LONG[d] if d else None
                for d in (list(_req.get(name, [])) + [None] * len(targets))
                [:len(targets)]]
        if list(_jreq[deck][pid]) != want:
            _lab_wrong.append("%s: %r != %r" % (name, _jreq[deck][pid], want))
check("the lab's PROGRAM_REQS matches generator REQ_MAP",
      not _lab_wrong, "; ".join(_lab_wrong[:3]))

# rules/aos.html must not claim a uniform dot count: three cards break it.
check("rules/aos.html names the three dot-count exceptions",
      all(n in _arules for n in ("Carry a Moving Load", "Rapid Approach",
                                 "Unobserved Entry"))
      and "carry two required&#8209;color dots; Routine" not in _arules)
# Percentages in the supplement are model output and must say so.
_nrules = text("rules/nrj.html")
check("rules/nrj.html says where its percentages come from",
      "About the percentages" in _nrules
      and "not from recorded play" in _nrules)
check("no bare win-rate claim is left in rules/aos.html",
      "points of win rate" not in _arules)
# THE WIN CONDITION IS SURVIVAL, AND THE RULEBOOK HAS TO SAY SO. aos.play()
# ends `return self.hp > 0` after the third Advanced Program, so an Advanced
# Program you fail still counts as faced. The rulebook once said "Complete
# all three with Health remaining", where "complete" reads as "succeed at" -
# the one phrase that made the deliberate-failure route look open on paper.
# Fixed 2026-11-03 in e812c7e; HANDOFF.md went on calling it open for five
# days because nothing held the sentence to the model. This is that.
check("rules/aos.html states survival, not completion, as the win condition",
      "Work through all three with Health remaining to win AoS." in _arules
      and "still counts as faced" in _arules
      and "is the win condition" in _arules
      and "Complete all three" not in _arules)
check("simulation/aos.py wins on surviving the three Advanced Programs",
      "return self.hp > 0" in _asrc
      and "self.advanced_done += 1" in _asrc)
# And the brake that makes survival-as-the-rule safe to print: Health is
# only ever regained by a Program Reward, and a Reward needs no failed
# element, so dumping Programs forfeits the only healing in the game.
check("rules/aos.html prints why failing on purpose is not a shortcut",
      "only way to heal is to do the work" in _arules
      and "The deck outlasts you." in _arules)

# THE DECK MIX IS AoS'S DIFFICULTY DIAL and it had three unchecked copies:
# simulation/aos.py's LEVELS, the lab's AOS_LEVELS and the printed table.
# Retuned 2026-11-03, so hold them together from here on.
_slv = sa["LEVELS"]
_jlv = js_literal("playtest/dist/app.js", "AOS_LEVELS")
_mix_wrong = []
for lvl in ("Easy", "Standard", "Hard", "Nobulous"):
    want = list(_slv[lvl])
    if list(_jlv[lvl]) != want:
        _mix_wrong.append("%s: lab %r != model %r" % (lvl, _jlv[lvl], want))
    # the printed table prints the same three numbers on one row
    row = "<tr><td>%s</td><td>%d</td><td>%d</td><td>%d</td></tr>" % (
        lvl, want[0], want[1], want[2])
    bold = ("<tr><td><b>%s</b></td><td><b>%d</b></td><td><b>%d</b></td>"
            "<td><b>%d</b></td></tr>" % (lvl, want[0], want[1], want[2]))
    if row not in _arules and bold not in _arules:
        _mix_wrong.append("%s: not printed as %r" % (lvl, want))
check("the deck mix agrees across model, lab and rulebook",
      not _mix_wrong, "; ".join(_mix_wrong[:4]))
# Specialized at 3 every rung is what the printed sentence promises.
check("every rung still holds Specialized at 3",
      all(_slv[l][1] == 3 for l in _slv),
      "%r" % ({l: _slv[l] for l in _slv},))
check("rules/aos.html still states the trade-one rule",
      "each step up trades one Routine Program for one Unstable" in _arules)

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


_lbl_wrong = []
_aos_opts = dict(options("deckSelect"))
for lvl in ("Easy", "Standard", "Hard", "Nobulous"):
    want = "%s &middot; %d/%d/%d" % ((lvl,) + tuple(sa["LEVELS"][lvl]))
    got = _aos_opts.get(lvl)
    if got != want:
        _lbl_wrong.append("AoS %s: label %r, model wants %r" % (lvl, got, want))
check("the lab's AoS difficulty labels name the mix it builds",
      len(_aos_opts) == 4 and not _lbl_wrong, "; ".join(_lbl_wrong[:4]))

_nap_wrong = []
_nap_opts = dict(options("napCreditGoal"))
for lvl in ("Easy", "Standard", "Hard", "Nobulous"):
    goal, sb = sn["LEVELS"][lvl]
    want = "%s &middot; %d Cr, %d Setbacks" % (lvl, goal, sb)
    got = _nap_opts.get(str(goal))
    if got != want:
        _nap_wrong.append("NAP %s: label %r, model wants %r"
                          % (lvl, got, want))
check("the lab's NAP difficulty labels name the goal it plays",
      len(_nap_opts) == 4 and not _nap_wrong, "; ".join(_nap_wrong[:4]))

# THE SETBACK COUNT IS PRINTED, so three sources carry it: nap.LEVELS, the
# difficulty table in rules/nap.html, and NAP_SETBACK_COUNT in suite.js - and
# NOTHING COMPARED THEM until the 2026-11-06 re-peg had to change all three by
# hand. The label check above reads the dropdown text, which is prose; this
# reads the number each source actually plays. It is the same gap that let the
# End-of-Day burn sit unplayed in simulation/nap.py for weeks while the other
# two sources played it, and the note below records that one.
_nap_sb = []
_sb_js = re.search(r"NAP_SETBACK_COUNT\s*=\s*\{([^}]*)\}",
                   text("playtest/dist/suite.js"))
_js_sb = {}
if _sb_js:
    _js_sb = dict((int(k), int(v)) for k, v in
                  re.findall(r"(\d+)\s*:\s*(\d+)", _sb_js.group(1)))
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
    if _js_sb.get(goal) != sb:
        _nap_sb.append("%s: nap.py %d, suite.js %r"
                       % (lvl, sb, _js_sb.get(goal)))
check("the Setbacks per level agree in nap.py, the rules and the lab",
      len(_rules_sb) == 4 and len(_js_sb) == 4 and not _nap_sb,
      "; ".join(_nap_sb[:4]))
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
check("the lab keeps the difficulty's leftover base Setbacks at Tier I",
      bool(_tier1) and "setbacks.slice(3)" in _tier1.group(0),
      "buildNAPDeck's Tier I branch drops them" if _tier1
      else "the Tier I branch of buildNAPDeck was not found")
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
_bat = py_tables("simulation/bat.py")
_gbat = py_tables("generator/build_bat.py")
rulenum("bat", r"(\d+) Experiment cards", len(_gbat["EXPERIMENTS"]),
        "the Experiment deck size")
rulenum("bat", r"(\d+) regular Upgrade cards", len(_gbat["UPGRADES"]),
        "the Upgrade deck size")
rulenum("bat", r"(\d+) Specimen cards", len(_gbat["SPECIMENS"]),
        "the Specimen count")
rulenum("bat", r"(\d+) Tyrant Attack cards", len(_gbat["ATTACKS"]),
        "the Tyrant Attack count")
rulenum("bat", r"survived (\d+) rounds", _bat["ROUND_LIMIT"],
        "the round limit")
rulenum("bat", r"hold at most (\d+) Upgrades", 3,
        "the Upgrade limit a Rat may hold")
rulenum("bat", r"awakens the moment it reaches (\d+) Splices", 5,
        "the Splice count that awakens the Tyrant")

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
rulenum("nap", r"Separate the (\d+) Final Exams", len(_gnap["EXAMS"]),
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
check("rules/aos.html: Carry a Moving Load is the four-colour exception",
      sorted(_byDeck["Specialized"]) == [2, 2, 2, 2, 2, 2, 2, 4]
      and "requires all four colors" in _RULES["aos"],
      "%r" % (_byDeck["Specialized"],))
check("rules/aos.html: the two Advanced three-dot exceptions are named "
      "wherever it gives the Advanced count",
      sorted(_byDeck["Advanced"]) == [2, 2, 2, 2, 2, 2, 3, 3]
      and _RULES["aos"].count("Rapid Approach and Unobserved Entry") >= 2,
      "%r, named %d time(s)"
      % (_byDeck["Advanced"],
         _RULES["aos"].count("Rapid Approach and Unobserved Entry")))

# -- NRJ and the finale ------------------------------------------------------
_fin = py_tables("simulation/finale.py")
rulenum("nrj", r"Play (\d+) sessions", _fin["SESSIONS"], "the session count")
rulenum("nrj", r"claim at most (\d+) per game", _aos["BACKDOOR_CLAIMS"],
        "the Backdoor claim cap")
rulenum("nrj", r"reduces one Exhibit's Target by (\d+)",
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
check("rules/bat.html prints the Research Note claim cost, and bat.py "
      "charges it",
      "Claiming one costs the next Upgrade" in _RULES["bat"]
      and _bat["NOTE_COSTS_UPGRADE"] is True,
      "NOTE_COSTS_UPGRADE=%r" % (_bat.get("NOTE_COSTS_UPGRADE"),))
check("rules/aos.html prints the Backdoor Routine claim cost, and aos.py "
      "charges it",
      "costs the next Program Reward" in _RULES["aos"]
      and _aos["BACKDOOR_COSTS_REWARD"] is True,
      "BACKDOOR_COSTS_REWARD=%r" % (_aos.get("BACKDOOR_COSTS_REWARD"),))
check("rules/nrj.html names both claim costs in one sentence",
      "costs the next Upgrade a completed Experiment earns" in _RULES["nrj"]
      and "a Backdoor Routine the next Program" in _RULES["nrj"])

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
check("the lab burns a card at the day rollover too",
      "n.discard.push(n.deck.pop())" in text("playtest/dist/suite.js"))

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
check("every PDF in playtest/dist/assets is linked from index.html",
      _asset_pdfs and not _orphan_pdfs, ", ".join(_orphan_pdfs))

# THE TRANSCRIPTS MUST NAME THE CURRENT LADDER. RESULTS.txt and
# simulation/README.md each carry a hand-maintained copy of the AoS grid, and
# on 2026-11-05 both were TWO generations stale - indexed by a ladder that had
# moved twice, with figures from before required colours. The figures cannot
# be checked here, since they need a 20,000-game run, but the row LABELS can,
# and a row labelled with a mix the model no longer has is the tell that the
# numbers beside it are stale too.
_aos_mixes = ["%d/%d/%d" % tuple(sa["LEVELS"][k])
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
CADENCE = "Once per cycle and once in Advanced Programming"
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
check("the lab implements Debug as a swap, with no reroll left behind",
      "function swapDebugDie" in _app and "function toggleDebugMode" in _app
      and "debugElement" not in _app and "data-debug" not in _app)

# EVERY LAB ASSET MUST CARRY THE CACHE TOKEN, on ONE token. AGENTS.md: a
# cached index.html "pins you to an old build however often you bump them",
# and the symptom "reads exactly like code that was never written".
# bat_experiments.js carried none until 2026-11-04 and nothing noticed.
_assets = re.findall(r'(?:src|href)="([^"]+\.(?:js|css)[^"]*)"', _idx)
_untokened = sorted(set(a for a in _assets if "?v=" not in a))
check("every script and stylesheet index.html loads carries ?v=",
      _assets and not _untokened, ", ".join(_untokened))
# Read the tokens out of the LINKS, not out of the file text: index.html's
# own comment recounts the ?v=dpi300 incident, and a check that scanned the
# prose counted that as a live second token.
_linked = re.findall(r'(?:src|href)="([^"]*\?v=[^"]*)"', _idx)
_tokens = sorted(set(re.findall(r"\?v=([A-Za-z0-9._-]+)", " ".join(_linked))))
check("index.html links one cache token, not several (%s)"
      % ", ".join(_tokens), len(_tokens) == 1)

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
        ("IMPOSTER_TASKS", "NAP_IMPOSTER_TASKS", None),
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
    # The Target index differs by table: SCEN and IMPOSTER_TASKS carry a domain or
    # subject before it, so the pair is named per table rather than guessed.
    ti = {"FOLLOWING": (2, 2), "IMPOSTER_TASKS": (3, 3),
          "DEVIOUS": (2, 2), "SCEN": (3, 3)}[key]
    bad = [(a[0], a[ti[0]], b[ti[1]]) for a, b in zip(g, j)
           if a[0] != b[0] or a[ti[0]] != b[ti[1]]]
    check("%s vs %s - %d names and Targets" % (key, jsname, len(g)), not bad,
          "%r" % (bad[:3],))

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
sim_subj = {n: s for (n, s, _d, _r, _t, _e) in gr["IMPOSTER_TASKS"]}
bad = [n for n, d in IMP_DOTS
       if gen_imp.get(n) != d or js_imp.get(n) != d
       or sim_imp.get(sim_subj.get(n)) != d]
check("the 4 Imposter Task dots agree in the cards, the lab and nap.py",
      not bad, "%r" % (bad,))

# The Tier III decks the lab keeps outside suite.js. Every field is compared,
# because the claim CONDITION now carries the cost clause that prices it -
# "Claiming gives up..." - and a lab that kept the old wording would teach the
# player a rule the rulebooks no longer have.
# INTF and CORRUPT joined this list on 2026-11-06, when the recycle clause on
# "I Don't Have Time for This" was capped: app.js:280 prints the Interference
# card's text to the player and app.js:414 prints the Corrupted Limitation's,
# so a copy that keeps the old wording teaches a rule no card has. Nothing
# was comparing either deck until the cap had to be made in two places.
for key, path, jsname in (("NOTES", "playtest/dist/bat.js", "BAT_NOTES"),
                          ("BACKDOOR", "playtest/dist/app.js",
                           "AOS_BACKDOOR"),
                          ("INTF", "playtest/dist/app.js",
                           "AOS_INTERFERENCE"),
                          ("CORRUPT", "playtest/dist/app.js",
                           "AOS_CORRUPT")):
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
    check("%s vs %s - %d cards, every printed field"
          % (key, jsname, len(g)), not bad, "%r" % (bad[:3],))

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
      and "Each Exhibit prints its <b>Target</b>, its <b>Damage</b>" in nrj)
# The five Rewards being reworded for the finale is checked further down,
# against EXHIBIT_REWARD itself. It used to be counted by grepping the
# generator for the cue phrase, which also counted the comments that
# explain the phrase.

# THE FIVE IMPOSTERS. Ten sides, one statline, and every ability name has
# to reach the rulebook - a side that only exists on the card is a side
# nobody can look up. The abilities are read from the generator, so adding
# one here fails this check until the rules carry it too.
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
# finale.py prices a point of STR at 85 points and REC 4 inverts the commit
# decision, so no ability may hand out either.
check("no Imposter ability touches STR or REC",
      not any("STR" in r[5] or "REC" in r[5] for r in imp))
for name in sorted(set(r[4] for r in imp)):
    check("  %s is in the rulebook" % name, name in nrj_flat)
check("the Imposter deck is registered for PnP, TTS and the lab",
      "'NRJ_Imposters'" in text("generator/pack.py")
      and "key='NRJ_Imposters'" in text("tts/decks.py")
      and "'NRJ_Imposters_TTS.png'" in text("generator/build_catalog.py"))

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
check("suite.js names 5 Reward cards", len(js_rewards) == 5,
      "%d: %s" % (len(js_rewards), sorted(js_rewards)))
missing = sorted(js_rewards - printed_rewards)
check("every one is printed as a Reward card", not missing, "%s" % missing)
check("suite.js and the card agree on which five pay",
      js_rewards == set(paying), "%s" % sorted(js_rewards ^ set(paying)))
for name in sorted(js_rewards):
    check("  %s in finale.py and the rulebook" % name,
          name in sim and name in rules)

print()
print("FLAVOUR TEXT THE LAB KEEPS ITS OWN COPY OF")
# The lab does not read flavour out of the generators: app.js carries all
# 32 AoS programs (both sides) and the 6 Limitations, and
# bat_experiments.js carries all 20 Experiments. On 2026-11-02 a 57-line
# flavour revision landed in the generators and those two files had to be
# walked by hand, which is the moment a copy goes stale. These checks are
# cheap and would have caught it.
_lab = "".join(text("playtest/dist/%s" % f)
               for f in ("app.js", "bat_experiments.js", "suite.js", "bat.js"))
_gb, _ga = py_tables("generator/build_bat.py"), py_tables("generator/aos.py")
for _label, _lines in (
        ("BAT Experiments", [r[3] for r in _gb["EXPERIMENTS"]]),
        ("AoS Stable sides", [v[0] for v in _ga["FLAVOR"].values()]),
        ("AoS Overheated sides", [v[1] for v in _ga["FLAVOR"].values()]),
        ("AoS Limitations", [r[2] for r in _ga["LIMITATIONS"]])):
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
print("NRJ - the five Imposters")
# The lab enforces the ten abilities as of 2026-10-31, so the ability TEXT is
# now live data and not decoration: suite.js renders it as innerHTML, which
# is why NRJ_IMPOSTERS carries build_nrj.py's strings verbatim - <i> tags,
# entities and all - and why this compares them character for character.
# Before this, the lab had no Imposter picker at all.
js_imp = js_literal("playtest/dist/suite.js", "NRJ_IMPOSTERS")
gen_rows = gr["IMPOSTERS"]
check("suite.js carries all 10 Imposter sides", len(js_imp) == len(gen_rows),
      "lab %d, generator %d" % (len(js_imp), len(gen_rows)))
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
check("the lab's 10 sides match the printed cards field for field", not bad,
      "; ".join(bad[:3]))
# All five print the finale's own statline. A per-Imposter statline would
# make the choice a difficulty dial, which is the one thing it may not be.
check("the cards print one statline, 5 HP / 2 STR / 3 REC",
      tuple(gr["IMP_STATS"]) == (5, 2, 3), "%r" % (gr["IMP_STATS"],))
check("suite.js has no per-Imposter statline to drift",
      not any(k in a for a in js_imp for k in ("hp", "str", "rec")))
# The lab keys every ability off `key`, and `per`/`uses` is how it counts
# them, so a duplicate key or a zero-use active side would silently disable
# one of the ten.
keys = [a["key"] for a in js_imp]
check("the 10 ability keys are distinct", len(set(keys)) == 10,
      "%r" % (sorted(k for k in set(keys) if keys.count(k) > 1),))
bad = [a["ability"] for a in js_imp
       if (a["per"] == "passive") != (a["when"] == "Passive")
       or a["per"] != "passive" and a["uses"] < 1
       or a["when"].startswith("Twice") and a["uses"] != 2
       or a["when"] == "Once per Session" and a["per"] != "session"]
check("each side's per/uses agrees with its printed timing", not bad,
      "%r" % (bad,))
# The Understudy is the only one who spends Candidates, in the cards, the
# rules and now the lab.
cost = [a["ability"] for a in js_imp if a.get("cost")]
check("only the Understudy's two sides cost Candidates",
      cost == ["Open Audition", "Second Chair"], "%r" % (cost,))
# The rules set the ability names with a non-breaking hyphen so they do not
# break across a line in the roster table; the cards use a plain one. That
# is typography rather than drift, so it is normalised away here.
nrjh = text("rules/nrj.html").replace("&#8209;", "-").replace(u"‑", "-")
missing = [a for (_n, _r, _s, _w, a, _t, _f) in gen_rows if a not in nrjh]
check("rules/nrj.html lists all 10 abilities by name", not missing,
      "%r" % (missing,))

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
check("the lab reads the published geometry instead of assuming it",
      "deck.cell" in _sj and "cellOf" in _sj)

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
try:
    from PIL import ImageFont
except ImportError:
    check("card titles are clear of the measure/render gap", True,
          "skipped: Pillow not installed")
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
# The lab links the rulebook PDFs out of playtest/dist/assets/, which are
# deployment copies of rules/*.pdf, which are built from rules/*.html. A
# player reading "Full BAT rules" in the lab and a player reading the PDF
# have to be reading the same document, and nothing checked that.
#
# This does NOT check rules/*.pdf against rules/*.html - that needs
# WeasyPrint and a full rebuild. `cd rules && python build.py` is the test:
# the build is byte reproducible, so if it rewrites nothing, the PDFs are
# current. Verified that way on 2026-11-03.
_books = ("BAT_Rulebook.pdf", "NAP_Rulebook.pdf", "AoS_Rulebook.pdf",
          "NRJ_Campaign_Supplement.pdf")
_stale = []
for _b in _books:
    _src = os.path.join(ROOT, "rules", _b)
    _dst = os.path.join(ROOT, "playtest", "dist", "assets", _b)
    if not os.path.exists(_dst):
        _stale.append(_b + " (not deployed)")
    elif io.open(_src, "rb").read() != io.open(_dst, "rb").read():
        _stale.append(_b)
check("the app serves the rulebooks that rules/ built",
      not _stale, "differ from rules/: %r" % (_stale,))

_idx = text("playtest/dist/index.html")
_linked = [_b for _b in _books if _b in _idx]
check("the app links all four rulebooks (%d)" % len(_linked),
      len(_linked) == len(_books),
      "missing: %r" % ([_b for _b in _books if _b not in _linked],))

# BAT's two armors are not mirror images of each other, and a HANDOFF
# paragraph claimed they were for three days because nothing held the claim
# against the book. These pin the four facts that distinguish them. If a
# rewording trips one, read rules/bat.html and HANDOFF 9a0000000 before
# "fixing" the check - the rule is the thing being protected, not the
# phrasing.
_bat = text("rules/bat.html")
for _label, _needle in (
        ("a Splice does not chip", "A Splice does not chip"),
        ("a broken Splice's remainder carries on", "the remainder carries on"),
        ("a Rat's Upgrade has no threshold", "whatever the blow was worth"),
        ("nothing carries over past a Rat's Upgrade", "nothing carries over")):
    check("rules/bat.html still says %s" % _label, _needle in _bat)

# The lab stopped modelling Buff HP when Health became the difficulty dial,
# so its Tyrant track is five Splices and nothing else. The track hint said
# damage ran through Buff HP first until 2026-11-03.
_hint = re.search(r'<p class="hint bat-track-hint">([^<]*Damage runs[^<]*)</p>',
                  _idx)
check("the Tyrant track hint describes the track the lab draws",
      bool(_hint) and "Buff HP" not in _hint.group(1),
      "hint: %r" % (_hint.group(1) if _hint else None,))
_js = text("playtest/dist/bat.js")
check("nothing in bat.js still renders a Buff HP cell",
      "bat-buff" not in _js and '"Buff HP"' not in _js)

# An Assignment Task prints its Demand half upside down, to be read by
# turning the card over. In a Time Slot the lab turns it for you; in the
# Choose-the-Primary panel you are comparing two cards you have not taken,
# so there is a turn button per card. Three things have to stay true or it
# silently stops working.
_suite = text("playtest/dist/suite.js")
check("both choice cards have a turn control",
      _idx.count('data-nap-turn="0"') == 1 and _idx.count('data-nap-turn="1"') == 1)
check("the turn control is wired in suite.js",
      "[data-nap-turn]" in _suite and "napTurned" in _suite)
# Only Tasks are two-sided. Opportunities, Setbacks and Final Exams are
# single-faced cards that happen to be landscape too, and turning one would
# just show it upside down.
check("the turn is offered only for two-sided Tasks",
      'const twoSided=x.type==="t"' in _suite and "tb.hidden=!twoSided" in _suite)
# Same rule in the Time Slots, where the lab turns a card for you. It used
# to turn ANY card carrying `demandSide`, and that flag means something
# different on an Opportunity - see HANDOFF.
check("only a Task is turned in the Time Slots",
      'a.demandSide&&a.type==="t"?"nap-demand"' in _suite)
check("an Opportunity says Last chance instead of being turned",
      "nap-last-chance" in _suite and
      "nap-last-chance" in text("playtest/dist/styles.css"))

print()
print("NAVIGATION PROMPTS - THE SHARED STEP STRIP")
# BAT had numbered step prompts and the other three screens had nothing.
# steps.js is that strip generalised; each screen passes its own step list.
# A chip's button is a PROXY for a control that already exists on the page,
# so the thing that silently breaks a step is renaming that control.
_steps = text("playtest/dist/steps.js")
_app = text("playtest/dist/app.js")
_css = text("playtest/dist/styles.css")
check("steps.js defines the shared component",
      "window.LabSteps" in _steps and "data-step-proxy" in _steps)
# It must be parsed before any screen renders, or the first render of a
# game silently skips its strip.
_order = [_idx.find('src="steps.js'), _idx.find('src="app.js'),
          _idx.find('src="suite.js'), _idx.find('src="bat.js')]
check("index.html loads steps.js before the screens that use it",
      _order[0] >= 0 and all(_order[0] < _o for _o in _order[1:]))
for _host, _src, _where in (("napSteps", _suite, "suite.js"),
                            ("nrjSteps", _suite, "suite.js"),
                            ("aosSteps", _app, "app.js")):
    check("%s has a host and %s renders it" % (_host, _where),
          ('id="%s"' % _host) in _idx and ('"%s"' % _host) in _src)
# The strip's CSS is shared, so no screen may keep a private copy and BAT
# must not still be emitting the old names.
check("the strip's CSS is named for the strip, not for BAT",
      ".step{" in _css and "bat-step" not in _css and
      "bat-step" not in text("playtest/dist/bat.js"))
# Every control a step points at by id has to exist, or that step is a
# chip that can never light.
_missing = sorted({_m for _src in (_suite, _app)
                   for _m in re.findall(r'ctrl: ?"#([A-Za-z][\w-]*)"', _src)
                   if ('id="%s"' % _m) not in _idx})
check("every step points at a control that exists",
      not _missing, "no such id: %r" % (_missing,))

# ---------------------------------------------------------------------------
# THE TTS MOD, which had no checks at all until 2026-11-08 and had drifted
# a whole design generation: lua.lua still dealt a flat-20-Health Tyrant with
# per-difficulty Buff HP, a 12-card Imposter Dossier with a Suspicion row,
# and one AoS Program deck chosen by difficulty instead of a mix of three.
# Two findDeck labels matched nothing in decks.py, so NAP's Time Slots were
# never dealt and Tier II dealt nothing. The notebook is a FOURTH copy of
# the rules after rules/*.html, the lab and the models.
_lua = text("tts/lua.lua")
_mod = text("tts/build_mod.py")
_decks = text("tts/decks.py")
sb_ = py_tables("simulation/bat.py")

# Every deck the script reaches for has to exist, by label, in decks.py.
# COUNTED, not merely compared: this matched findDeck('...') until the
# setups started calling deckOut('...'), and an empty set is a subset of
# anything. A check a RENAME can satisfy is not a check - AGENTS.md says
# so, and this is the fourth time in this repo.
_labels = set(re.findall(r"label='([^']+)'", _decks))
_want = set(re.findall(r"deckOut\('([^']+)'", _lua))
check("tts/lua.lua still asks for its decks by label",
      len(_want) >= 20, "found only %d deckOut labels" % len(_want))
check("every deck label in tts/lua.lua exists in tts/decks.py",
      _want <= _labels, "no such deck: %r" % (sorted(_want - _labels),))
# ...and the other direction, which is the one with teeth now that the
# cards live in boxes: a deck no setup ever names is dead cardboard that
# a player can only reach by opening a box and guessing.
_named = set(l for l in _labels if ("'" + l + "'") in _lua)
check("every deck in the boxes is reachable from a setup button",
      _named == _labels, "never dealt: %r" % (sorted(_labels - _named),))


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
      and "'Exhibits ' .. idx[i]" in _lua
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
# Every row is btn(label, fn, x, z, width) or lbl(text, x, z, width), so
# the triple to check is two decimals followed by an integer width. The
# {r, g, b} colours cannot match it: their third number is not an integer.
_rows = re.findall(r"(-?\d+\.\d+),\s*(-?\d+\.\d+),\s*(\d{3,4})", _pan)
check("the panel layout was read out of tts/lua.lua",
      len(_rows) >= 10, "found %d button positions" % len(_rows))
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
_calls = [m.start() for m in re.finditer(r"spread\(", _lua)]
_bare = [_lua[i:i + 60].split(chr(10))[0]
         for i in _calls if "CARD_" not in _lua[i:i + 220]]
check("every row is spaced in card widths",
      len(_calls) >= 6 and not _bare,
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
check("the dice are a 2x2 block per colour down the left edge",
      "ROWS = {" in _mod and "XCOL = " in _mod and "OFFS = (" in _mod
      and "(seen[nick] - 1) * 1.1" not in _mod)
check("the Chip sits with the Red die it marks, not on it",
      "'Chip': (XCOL + 3.2, ROWS['Pink'])" in _mod)
# The rail's height is not in the save, and four attempts to name it
# failed, so the mat and the boxes are dropped onto it and locked where
# they land.
check("the mat and the boxes are settled onto the rail, not placed on it",
      "function settle()" in _lua and "settle()" in _lua.split("function onLoad")[1]
      and "o.setLock(true)" in _lua)
# The panel art is generated now, so the shape the layout depends on has
# a source rather than being a hand-drawn PNG nobody can regenerate.
_panel = text("generator/make_panel.py")
check("the control-panel mat has a source",
      "W, H = 1473, 520" in _panel and "ControlPanel.png" in _panel)
check("the panel mat matches the aspect the layout is built for",
      abs((1473.0 / 520.0) - _half_x) < 0.001)


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
check("tts/lua.lua BAT_DIFF matches bat.DIFFICULTY",
      _lua_rows("BAT_DIFF", _lvl) == dict(
          (k, tuple(v)) for k, v in sb_["DIFFICULTY"].items()))
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

# The notebook quotes the same dials in words, so derive the words.
_bat_line = "   ".join("%s %d and %d" % (l, sb_["DIFFICULTY"][l][0],
                                         sb_["DIFFICULTY"][l][1])
                       for l in _lvl)
check("the TTS notebook prints BAT's Specimens and Tyrant Health",
      _bat_line in _mod, "wanted %r" % _bat_line)
_nap_line = "   ".join("%s %d and %d" % (l, sn["LEVELS"][l][0],
                                         sn["LEVELS"][l][1])
                       for l in _lvl)
check("the TTS notebook prints NAP's Credit goal per difficulty",
      _nap_line in _mod, "wanted %r" % _nap_line)
check("the TTS notebook prints AoS's Program mix",
      ", ".join("%s %d-%d-%d" % ((l,) + tuple(sa["LEVELS"][l]))
                for l in _lvl) in _mod.replace("\\n\"\n         \"", " "))
# The superseded finale's vocabulary must not come back anywhere in tts/.
check("no tts/ file still describes the superseded finale",
      not any(w in _lua + _mod for w in
              ("Suspicion", "Impostor", "shuffle those 12", "4 HP / 2 STR")))
check("the TTS notebook prints the AoS allocation floor and the Reward brake",
      "MUST RECEIVE AT LEAST ONE" in _mod
      and "ONLY HEALING IN THE GAME" in _mod)

print()
print("%d check(s) failed" % len(FAILS))
for f in FAILS:
    print("   -", f)

sys.exit(len(FAILS))
