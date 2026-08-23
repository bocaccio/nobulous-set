import sys; sys.path.insert(0, '/home/claude/cards')
from gen import render_deck, render_duplex, make_back, DOT_NAP as DOT, LANDSCAPE, PORTRAIT, skulls, subj_icon

ANA, ENG, PRO, THE = 'Anatomy', 'Engineering', 'Procedure', 'Theory'

# name, subject, dot, skulls, ReqTarget, req effect, DemTarget, dem effect, penalty
TASKS = [
 ("Organize the Specimen Cabinet", THE,'Y',0,2,"Exact Work: If completed with exactly 2 successes, recover 1 committed die.",3,"Nobulous Can't Find Anything: One Crit rolled here counts as 1 success.","Exhaust 1 available die."),
 ("Prepare the Tissue Samples", ANA,'G',1,3,"Clean Cuts: If completed using 3 or fewer dice, recover 1 committed die.",5,"Samples Are Degrading: Stored progress here loses 1 success at the end of the Time Slot.","Lose 1 Health."),
 ("Calibrate the Neural Imager", ENG,'B',1,4,"Fine Calibration: One Blue Crit counts as 3 successes here.",5,"Emergency Calibration: Blue Crits count as 1 success here.","Exhaust 2 available dice."),
 ("Stabilize the Prototype Brain", ANA,'P',2,5,"Stable Pattern: If dice of 3+ colors contribute, add 1 success.",7,"Neural Cascade: No more than 2 dice may be stored here.","Lose 1 Health."),
 ("Sterilize the Surgical Tools", PRO,'Y',0,3,"Efficient Routine: If completed without using a Crit, recover 1 committed die.",4,"Contamination: One successful die rolled here each attempt cannot be stored.","Exhaust 1 available die."),
 ("Label the Neural Samples", THE,'G',0,3,"Good Records: If this is the Primary, add 1 success after rolling.",4,"Mislabeling: Requires +1 success for each other unresolved Assignment in this row.","Exhaust 1 available die."),
 ("Monitor the Growth Vats", ANA,'B',0,3,"Healthy Growth: If Exact, gain 1 Health.",5,"Unstable Growth: If completed with excess successes, exhaust 1 additional available die.","Lose 1 Health."),
 ("Tune the Cranial Resonator", ENG,'P',0,5,"Harmonic Match: Purple Crits count as 3 successes here.",6,"Resonance Drift: One Crit rolled here counts as 1 success.","Exhaust 1 available die."),
 ("Prepare the Transplant Rig", ENG,'G',1,4,"Organized Setup: If Exact, recover 1 committed die.",5,"Rush Setup: At least 3 dice must be committed whenever you work this Assignment.","Lose 1 Health."),
 ("Align the Memory Probes", ENG,'B',1,4,"Precise Alignment: If you exactly meet the target, recover 1 committed die.",9,"Signal Loss: Excess successes cannot be shifted elsewhere.","Exhaust 1 available die."),
 ("Test the Cerebral Coupler", ENG,'B',1,4,"Bench Test: If Exact, recover 1 committed die.",5,"Live Test: Requires at least 2 Blue dice.","Exhaust 2 available dice."),
 ("Recalibrate the Bone Saw", PRO,'P',1,4,"Sharp Enough: One Purple Crit counts as 3 successes here.",9,"It's Binding: One Purple Crit counts as 1 success here.","Lose 1 Health."),
 ("Prime the Synaptic Pump", PRO,'P',1,5,"Steady Pressure: If completed using exactly 3 dice, recover 1 committed die.",9,"Pressure Drop: Each attempt must commit at least 2 dice.","Exhaust 1 available die."),
 ("Map the Council Brain", ANA,'P',1,6,"Breakthrough: If completed as a Request, permanently increase REC by 1.",7,"Incomplete Map: Stored progress on this Assignment is capped at 4 successes.","Lose 1 Health."),
 ("Condition the Donor Tissue", ANA,'Y',1,3,"Fresh Tissue: If completed in one attempt, recover 1 committed die.",5,"Tissue Is Failing: At the end of an unsuccessful attempt, exhaust 1 stored die from this card.","Lose 1 Health."),
 ("Verify the Identity Matrix", THE,'B',2,4,"Cross-check: If dice of 3+ colors contribute, add 1 success.",9,"Identity Conflict: One Crit rolled here counts as 1 success.","Exhaust 2 available dice."),
 ("Complete the Splice Protocol", PRO,'P',2,5,"Clean Splice: If completed with no stored dice, recover 1 committed die.",7,"Emergency Splice: No more than 3 dice may be stored here.","Lose 1 Health."),
 ("Document the Procedure", THE,'G',0,3,"Clear Notes: If completed as Primary, recover 1 committed die.",4,"Rewrite It: Requires at least 2 Green dice.","Exhaust 1 available die."),
 ("Suture the Donor Incision", PRO,'Y',1,4,"Steady Hands: If completed using exactly 4 dice, recover 1 committed die.",9,"Torn Suture: One Crit rolled here counts as 1 success.","Lose 1 Health."),
 ("Decode Nobulous' Lecture Notes", THE,'G',0,4,"Insight: Look at the next 3 Assignment cards and return them in any order.",5,"Contradictions Everywhere: Requires at least 3 different die colors.","Exhaust 1 available die."),
 ("Update Nobulous' Lab Notes", None,'Y',0,3,"Useful Margin Note: Look at the next Assignment; return it to the top or bottom.",4,"Nobulous Wants Details: You may store no more than 1 die here.","Exhaust 1 available die."),
 ("Inventory the Spare Organs", None,'G',0,3,"Found Something Useful: If completed, recover 1 exhausted Yellow or Green die.",4,"Where Is the Spleen?: If another Assignment in this row is unresolved, this requires +1 success.","Exhaust 1 available die."),
 ("Clean the Restraint Table", None,'B',0,4,"Quick Cleanup: If completed using 4 or fewer dice, recover 1 committed die.",5,"Scrub It Again: Stored dice here cannot be recovered by other effects.","Exhaust 1 available die."),
 ("Reassemble the Automaton Hand", None,'P',1,6,"Masterwork: If completed as a Request, permanently increase STR by 1.",8,"It Keeps Twitching: One Crit rolled here counts as 1 success.","Lose 1 Health."),
 ("Dispose of Failed Samples", None,'B',1,4,"Efficient Disposal: If completed in one attempt, recover 1 exhausted die.",9,"They're Leaking: If unresolved after an attempt, exhaust 1 additional available die.","Lose 1 Health."),
 ("Sharpen the Surgical Implements", None,'P',0,4,"Razor Edge: If completed using a Crit, recover 1 committed die.",5,"Dull Again: Crits count as 1 success here.","Exhaust 2 available dice."),
]

OPPS = [("Take an Unauthorized Break",'Y',4,"Gain 1 Health."),
        ("Raid the Supply Closet",'Y',4,"Recover up to 2 exhausted dice of different colors."),
        ("Borrow Better Instruments",'Y',5,"Gain +1 STR during the next Time Slot only."),
        ("Study Nobulous' Notes",'Y',5,"Gain +1 REC during the next Time Slot only."),
        ("Salvage Useful Components",'G',4,"Recover up to 3 exhausted dice; none may be Red or Purple."),
        ("Practice on a Spare Brain",'G',5,"During the next Time Slot, one Crit of your choice counts as 3 successes.")]

SETBACKS = [("Power Failure",'Y',6),("Contaminated Workbench",'G',6),("Jammed Centrifuge",'G',7),
            ("Broken Neural Imager",'B',7),("Escaped Specimen",'B',8),("Automaton Malfunction",'P',8)]
SB_TEXT = ("No other Assignment may be worked until this Setback is resolved.<br><br>"
           "At the start of this Time Slot, if this Setback has no stored dice, exhaust 1 available die.")

EXAMS = [
 ("Cranial Integrity Inspection", ANA,'B',5,"Commit dice of at least 3 different colors."),
 ("Fine Motor Assessment", ANA,'Y',6,"At least 1 Yellow and 1 Blue die must contribute."),
 ("Physiological Stress Test", ANA,'P',6,"At least 2 Blue/Purple dice total must contribute."),
 ("Council Etiquette Simulation", THE,'G',5,"Red cannot be committed; use at least 3 colors."),
 ("Identity Recall Demonstration", THE,'P',6,"At least 1 Blue and 1 Purple die must contribute."),
 ("Final Impostor Examination", THE,'Y',7,"Use at least 4 different colors. A Red Crit counts as 1 success."),
 ("Neural Response Screening", ENG,'G',5,"At least 1 Crit must contribute to complete this Assignment."),
 ("Adaptive Reasoning Trial", ENG,'B',6,"Commit at least 4 dice. One Yellow Crit counts as 3 successes."),
 ("Council Recognition Drill", ENG,'B',6,"Red cannot be committed. At least 1 Purple die must contribute."),
 ("Procedural Knowledge Review", PRO,'Y',6,"Red cannot be committed; use at least 3 different colors."),
 ("Unexpected Policy Debate", PRO,'P',7,"Commit at least 4 dice from at least 3 different colors."),
 ("Nobulous' Comprehensive Review", PRO,'G',7,"Commit at least 5 dice from at least 3 different colors."),
]

APPS = [
 ("Prodigy","Once per Time Slot, when using two dice of the same color as wild, only one of those dice must roll a success.","Reroll one die showing no successes."),
 ("Slacker","The first time each Day you voluntarily draw an additional Assignment, ignore one Skull on that card.","Discard one non-Setback, non-Final-Exam Assignment from the current Time Slot. Exhaust any dice stored on it."),
 ("Technician","A Setback with at least one stored die allows you to work on one other Assignment during that Time Slot.","Recover one die stored on a Setback to your available pool; its stored successes remain."),
 ("Savant","During special recovery, recover all but 1 exhausted die of the special color and recover 1 exhausted die of an adjacent color.","After special color recovery, recover one additional exhausted die of the indicated color."),
 ("Opportunist","When you complete an Assignment on its Request side, recover 1 exhausted die of that Assignment's recovery-color dot.","After revealing an Opportunity, you may discard it and draw another Assignment. Resolve Skulls normally."),
 ("Lab Rat","The first time each Day you would lose Health, you may exhaust one available die instead.","Gain 1 Health. Maximum Health: 3."),
]


def C(title, sub, body, ftr='', warn=False, acc=None, bg=None):
    f = ('<div class="ftr%s">%s</div>' % (' warn' if warn else '', ftr)) if ftr else ''
    st = ' style="--a:%s"' % acc if acc else ''
    bs = ' style="background:%s"' % bg if bg else ''
    cls = ' xlong' if len(title) > 30 else (' long' if len(title) > 19 else '')
    return ('<div class="card"%s><div class="hdr"><div class="t%s">%s</div><div class="s">%s</div></div>'
            '<div class="body"%s>%s<div class="spacer"></div>%s</div></div>'
            % (st, cls, title, sub, bs, body, f))


def dotspan(c):
    return '<span style="display:inline-block;width:2.8mm;height:2.8mm;border-radius:50%%;' \
           'background:%s;border:.4pt solid #6b6459;vertical-align:-.4mm"></span>' % DOT[c]


# ---- Tasks: landscape, spine layout ----
cards = []
for n, subj, dot, sk, rt, rx, dt, dx, pen in TASKS:
    marks = ('<div class="marks">%s<div class="dt" style="background:%s"></div>%s</div>'
             % (subj_icon(subj), DOT[dot], skulls(sk, '3.4mm')))
    w = n.split()
    best, bi = 10**9, 1
    for i in range(1, len(w) or 1):
        m = max(len(' '.join(w[:i])), len(' '.join(w[i:])))
        if m < best:
            best, bi = m, i
    l1, l2 = ' '.join(w[:bi]), ' '.join(w[bi:])
    fs = max(6.4, min(9.4, 9.4 * 22.0 / max(best, 1)))
    left = ('<div class="spine l"><div class="track n">'
            '<div class="vert name" style="font-size:%.1fpt;width:40mm">'
            '<div style="white-space:nowrap">%s</div><div style="white-space:nowrap">%s</div>'
            '</div></div></div>' % (fs, l1, l2)) + marks
    right = ('<div class="spine r"><div class="track p">'
             '<div class="vert rr nowrap" style="width:52mm">'
             '<span class="penlbl">Penalty &nbsp;</span><span class="pen">%s</span>'
             '</div></div></div>' % pen)
    mid = ('<div class="mid">'
           '<div class="band" style="background:#3f7a4e">Request</div>'
           '<div class="half"><div class="row" style="gap:2.8mm;align-items:center">'
           '<div style="font-size:23pt;font-weight:bold;color:#3f7a4e;line-height:1">%d</div>'
           '<div style="font-size:9pt;line-height:1.26">%s</div></div>'
           '</div><div class="rule"></div>'
           '<div class="half d"><div class="row" style="gap:2.8mm;align-items:center">'
           '<div style="font-size:23pt;font-weight:bold;color:#a8332c;line-height:1">%d</div>'
           '<div style="font-size:9pt;line-height:1.26">%s</div></div></div>'
           '<div class="band d180" style="background:#a8332c">Demand</div>'
           '</div>' % (rt, rx, dt, dx))
    cards.append('<div class="card">%s%s%s</div>' % (left, mid, right))
print("Tasks", render_deck('NAP_Tasks', cards, 'NAP', LANDSCAPE))

cards = [C(n, "Opportunity &middot; Optional",
           '<div class="row" style="gap:3mm;align-items:center">%s'
           '<div style="font-size:24pt;font-weight:bold;color:#9a7410;line-height:1">%d</div>'
           '<div style="font-size:6.4pt;letter-spacing:.14em;text-transform:uppercase;color:#8a8272">'
           'Successes</div></div><div class="txt">%s</div>' % (dotspan(d), s_, e),
           'No storage. Last chance: if unresolved again, discard this Opportunity.',
           acc='#c79a1e') for n, d, s_, e in OPPS]
print("Opportunities", render_deck('NAP_Opportunities', cards, 'NAP', LANDSCAPE))

cards = [C(n, "Setback &middot; Mandatory",
           '<div class="row" style="gap:3mm;align-items:center">%s'
           '<div style="font-size:24pt;font-weight:bold;color:#2f6ba8;line-height:1">%d</div>'
           '<div style="font-size:6.4pt;letter-spacing:.14em;text-transform:uppercase;color:#8a8272">'
           'Successes</div></div><div class="txt">%s</div>' % (dotspan(d), s_, SB_TEXT),
           '', acc='#2f6ba8') for n, d, s_ in SETBACKS]
print("Setbacks", render_deck('NAP_Setbacks', cards, 'NAP', LANDSCAPE))

cards = [C(n, "Final Exam &middot; " + subj,
           '<div class="row" style="gap:2.6mm;align-items:center">%s%s'
           '<div style="font-size:24pt;font-weight:bold;color:#241f1a;line-height:1">%d</div>'
           '<div style="font-size:6.4pt;letter-spacing:.14em;text-transform:uppercase;color:#8a8272">'
           'Base successes</div></div>'
           '<div class="txt sm">Reduce this target by 1 for each %s Credit you earned.</div>'
           '<div class="txt">%s</div>' % (subj_icon(subj, '5.2mm'), dotspan(d), t, subj, e),
           '', acc='#241f1a')
         for n, subj, d, t, e in EXAMS]
print("Final Exams", render_deck('NAP_FinalExams', cards, 'NAP', LANDSCAPE))

def appcard(n, p, o):
    return C(n, "Apprentice",
             '<div class="txt c" style="font-size:9.4pt;font-weight:bold;margin-top:.6mm">'
             'HP 2 &nbsp;|&nbsp; STR 2 &nbsp;|&nbsp; REC 2</div>'
             '<div class="sub" style="margin-top:2.4mm">Passive</div>'
             '<div class="txt" style="margin-top:.4mm">%s</div>'
             '<div class="sub" style="margin-top:2.4mm">Once per Day</div>'
             '<div class="txt" style="margin-top:.4mm">%s</div>' % (p, o),
             'Choose one Apprentice card and one side at setup.')


app_a = [appcard(*a) for a in APPS[0::2]]
app_b = [appcard(*a) for a in APPS[1::2]]
print("Apprentices", render_duplex('NAP_Apprentices', app_a, app_b, 'NAP', LANDSCAPE), 'two-sided')

TAIL = ('After exhausting non-stored dice, complete special color recovery. Then set the dial to the '
        'Primary Assignment dot and move it to the next Time Slot.')
SLOTS = [("Morning", "#f6e6b8", "Perform the recovery shown on the dial. No special color recovery on Day 1 Morning."),
         ("Afternoon", "#d8ecd4", "Perform the recovery shown on the dial."),
         ("Evening", "#e0daf0", "Perform the recovery shown on the dial.")]
cards = []
for nm, tint, lead in SLOTS:
    cards.append('<div class="card"><div class="body" style="background:%s;padding:3mm 4mm;'
                 'align-items:center;justify-content:center;text-align:center">'
                 '<div style="font-size:30pt;font-weight:bold;letter-spacing:.04em;color:#241f1a;'
                 'line-height:1">%s</div>'
                 '<div style="font-size:6.2pt;letter-spacing:.24em;text-transform:uppercase;'
                 'color:#6b6459;margin-top:1.6mm">Time Slot</div>'
                 '<div style="font-size:8pt;line-height:1.3;margin-top:3.4mm;max-width:70mm">%s</div>'
                 '<div style="font-size:7pt;line-height:1.26;margin-top:2.2mm;max-width:74mm;color:#4a4239">'
                 '%s</div></div></div>' % (tint, nm, lead, TAIL))
cards.append(C("Following in Nobulous' Footsteps", "FINF &middot; Standard difficulty -1",
   '<div class="sub" style="margin-top:.4mm">Increase (+1 / +2 / +3)</div>'
   '<div class="txt sm" style="margin-top:.4mm">Shuffle FINF into the Assignment deck. When drawn, place it '
   'before the Primary. +1 adds 1 Assignment to the next Time Slot; +2 adds 1 to each of the next 2; +3 adds 1 '
   'to each of the next 3. Ignore Skulls on Assignments added by FINF. Maximum 4 Assignments per row.</div>'
   '<div class="sub" style="margin-top:2mm">Reduce (-1 / -2 / -3)</div>'
   '<div class="txt sm" style="margin-top:.4mm">Choose before play. You have 1, 2, or 3 uses per game. Rotate '
   'FINF after each use. Remove any non-Final-Exam Assignment from the current row and exhaust its stored dice. '
   'FINF is not used during the Final Exam.</div>', '', acc='#7a2f52'))
print("Slots + FINF", render_deck('NAP_SlotsFINF', cards, 'NAP', LANDSCAPE))

make_back('CardBack_NAP_Assignment', 'NAP', 'Assignment', '#6b3f8c', LANDSCAPE)
make_back('CardBack_NAP_FinalExam', 'Final Exam', 'Set aside at setup', '#241f1a', LANDSCAPE)
print("backs done")
