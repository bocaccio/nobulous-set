import sys; sys.path.insert(0, '/home/claude/cards')
from gen import render_deck, render_duplex, make_back, hdr_fit, DOT_NAP as DOT, LANDSCAPE, PORTRAIT, skulls, subj_icon

# Every NAP card built through C() is landscape.
CARD_SIZE = LANDSCAPE

ANA, ENG, PRO, THE = 'Anatomy', 'Engineering', 'Procedure', 'Theory'

# name, subject, dot, skulls, ReqTarget, req effect, DemTarget, dem effect, penalty
TASKS = [
 ("Organize the Specimen Cabinet", THE,'Y',0,2,"If completed with exactly 2 successes across all committed dice this strategy phase, recover 1 committed die.",3,"Nobulous Can't Find Anything: One Crit rolled here counts as 1 success.","Exhaust 1 available die."),
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

# name, dot, successes, effect, flavor
OPPS = [("Take an Unauthorized Break",'Y',3,"Spend: cancel 1 Health loss.",
         "Nobulous noticed. It has been added to your file."),
        ("Raid the Supply Closet",'Y',3,"Spend: one die counts as any color for one roll.",
         "Most of it is labeled. Very little of it is labeled correctly."),
        ("Borrow Better Instruments",'Y',4,"Spend: add 1 success to a roll.",
         "Return them before Nobulous notices. Nobulous always notices."),
        ("Study Nobulous' Notes",'Y',4,"Spend: reduce one Assignment's remaining need by 2.",
         "Half the margins are equations. The other half are grudges."),
        ("Salvage Useful Components",'G',3,"Spend: add 2 successes to an Assignment, without rolling.",
         "One apprentice's scrap is another apprentice's promotion."),
        ("Practice on a Spare Brain",'G',4,"Spend: one Crit counts as 3 successes.",
         "It was a spare. Nobody asked the brain.")]

# name, dot, successes, flavor
SETBACKS = [("Power Failure",'Y',6,"Somewhere in the dark, something in a vat starts breathing faster."),
            ("Contaminated Workbench",'G',6,"Nobody admits to eating lunch here. The evidence disagrees."),
            ("Jammed Centrifuge",'G',7,"The centrifuge stopped spinning. The samples did not."),
            ("Broken Neural Imager",'B',7,"It still shows images. None of them are of the brain."),
            ("Escaped Specimen",'B',8,"It left a trail. It also left a note."),
            ("Automaton Malfunction",'P',8,"It is sweeping the ceiling with tremendous dedication.")]
SB_TEXT = ("No other Assignment may be worked until this Setback is resolved. "
           "At the start of this Time Slot, if this Setback has no stored dice, exhaust 1 available die.")

# name, subject, dot, base successes, requirement, flavor
EXAMS = [
 ("Cranial Integrity Inspection", ANA,'B',5,"Commit dice of at least 3 different colors.",
  "The Council taps your skull. It is supposed to sound like that."),
 ("Fine Motor Assessment", ANA,'Y',6,"At least 1 Yellow and 1 Blue die must contribute.",
  "Thread the needle. The needle is in a specimen that is still moving."),
 ("Physiological Stress Test", ANA,'P',6,"At least 2 Blue/Purple dice total must contribute.",
  "Your pulse is being monitored. So is the examiner's."),
 ("Council Etiquette Simulation", THE,'G',5,"Red cannot be committed; use at least 3 colors.",
  "Bow to the eldest member. Do not ask which one is the eldest."),
 ("Identity Recall Demonstration", THE,'P',6,"At least 1 Blue and 1 Purple die must contribute.",
  "State your name. Say it like you have always had it."),
 ("Final Impostor Examination", THE,'Y',7,"Use at least 4 different colors. A Red Crit counts as 1 success.",
  "Every answer is correct. That is what makes the Council suspicious."),
 ("Neural Response Screening", ENG,'G',5,"At least 1 Crit must contribute to complete this Assignment.",
  "Electrodes on, lights off. Try not to think anything incriminating."),
 ("Adaptive Reasoning Trial", ENG,'B',6,"Commit at least 4 dice. One Yellow Crit counts as 3 successes.",
  "The rules change halfway through. So does the examiner."),
 ("Council Recognition Drill", ENG,'B',6,"Red cannot be committed. At least 1 Purple die must contribute.",
  "Match every face to a name. Some of the faces have been replaced."),
 ("Procedural Knowledge Review", PRO,'Y',6,"Red cannot be committed; use at least 3 different colors.",
  "Recite the procedure. Nobulous wrote it in a hurry and in the wrong order."),
 ("Unexpected Policy Debate", PRO,'P',7,"Commit at least 4 dice from at least 3 different colors.",
  "Nobody scheduled this debate. Everybody brought notes."),
 ("Nobulous' Comprehensive Review", PRO,'G',7,"Commit at least 5 dice from at least 3 different colors.",
  "Nobulous has prepared questions. Nobulous has also prepared excuses."),
]

# name, when the ability applies, ability. One ability per Apprentice.
APPS = [
 ("Prodigy", "Once per Time Slot",
  "When using two dice of the same color as wild, only one of those dice must roll a success."),
 ("Slacker", "Passive",
  "Your Time Slot rows hold a maximum of 3 Assignments instead of 4."),
 ("Technician", "Passive",
  "When you complete a Setback, recover 2 exhausted dice."),
 ("Savant", "Passive",
  "During special recovery, recover all but 1 exhausted die of the special color and recover 1 exhausted die of an adjacent color."),
 ("Opportunist", "Passive",
  "When you complete an Assignment on its Request side, recover 1 exhausted die of that Assignment's recovery-color dot."),
 ("Lab Rat", "Once per Day",
  "The first time you would lose Health, you may exhaust one available die instead."),
]



def C(title, sub, body, ftr='', warn=False, acc=None, bg=None, flavor=''):
    f = ('<div class="ftr%s">%s</div>' % (' warn' if warn else '', ftr)) if ftr else ''
    # Flavor text sits at the bottom of the card, just above the footer.
    fl = ('<div style="font-size:7.4pt;font-style:italic;text-align:center;line-height:1.25;'
          'color:#6f675a;margin:1.2mm 0 1mm">%s</div>' % flavor) if flavor else ''
    st = ' style="--a:%s"' % acc if acc else ''
    bs = ' style="background:%s"' % bg if bg else ''
    cls = ' xlong' if len(title) > 30 else (' long' if len(title) > 19 else '')
    fit = hdr_fit(title, cls, CARD_SIZE)
    return ('<div class="card"%s><div class="hdr"%s><div class="t%s">%s</div><div class="s">%s</div></div>'
            '<div class="body"%s>%s<div class="spacer"></div>%s%s</div></div>'
            % (st, ' style="%s"' % fit if fit else '', cls, title, sub, bs, body, fl, f))


def dotspan(c):
    return '<span style="display:inline-block;width:2.8mm;height:2.8mm;border-radius:50%%;' \
           'background:%s;border:.4pt solid #6b6459;vertical-align:-.4mm"></span>' % DOT[c]


# Card backs first: the deck PnPs interleave them behind the fronts.
make_back('CardBack_NAP_Assignment', 'NAP', 'Assignment', '#6b3f8c', LANDSCAPE)
make_back('CardBack_NAP_FinalExam', 'Final Exam', 'Set aside at setup', '#241f1a', LANDSCAPE)
make_back('CardBack_NAP_TimeSlot', 'NAP', 'Time Slot \u00b7 FINF', '#9f3f23', LANDSCAPE)
print("card backs done")

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
print("Tasks", render_deck('NAP_Tasks', cards, 'NAP', LANDSCAPE, back='CardBack_NAP_Assignment'))

cards = [C(n, "Opportunity &middot; Optional",
           '<div class="row" style="gap:3mm;align-items:center">%s'
           '<div style="font-size:24pt;font-weight:bold;color:#9a7410;line-height:1">%d</div>'
           '<div style="font-size:6.4pt;letter-spacing:.14em;text-transform:uppercase;color:#8a8272">'
           'Successes</div></div><div class="txt">%s</div>' % (dotspan(d), s_, e),
           'No storage. When completed, keep this card and spend it once, at any time. '
           'Last chance: if unresolved again, discard this Opportunity.',
           acc='#c79a1e', flavor=fl) for n, d, s_, e, fl in OPPS]
print("Opportunities", render_deck('NAP_Opportunities', cards, 'NAP', LANDSCAPE, back='CardBack_NAP_Assignment'))

cards = [C(n, "Setback &middot; Mandatory",
           '<div class="row" style="gap:3mm;align-items:center">%s'
           '<div style="font-size:24pt;font-weight:bold;color:#2f6ba8;line-height:1">%d</div>'
           '<div style="font-size:6.4pt;letter-spacing:.14em;text-transform:uppercase;color:#8a8272">'
           'Successes</div></div>' % (dotspan(d), s_),
           SB_TEXT, acc='#2f6ba8', flavor=fl) for n, d, s_, fl in SETBACKS]
print("Setbacks", render_deck('NAP_Setbacks', cards, 'NAP', LANDSCAPE, back='CardBack_NAP_Assignment'))

cards = [C(n, "Final Exam &middot; " + subj,
           '<div class="row" style="gap:2.6mm;align-items:center">%s%s'
           '<div style="font-size:24pt;font-weight:bold;color:#241f1a;line-height:1">%d</div>'
           '<div style="font-size:6.4pt;letter-spacing:.14em;text-transform:uppercase;color:#8a8272">'
           'Base successes</div></div>'
           '<div class="txt sm">Reduce this target by 1 for each %s Credit you earned.</div>'
           '<div class="txt">%s</div>' % (subj_icon(subj, '5.2mm'), dotspan(d), t, subj, e),
           '', acc='#241f1a', flavor=fl)
         for n, subj, d, t, e, fl in EXAMS]
print("Final Exams", render_deck('NAP_FinalExams', cards, 'NAP', LANDSCAPE, back='CardBack_NAP_FinalExam'))

def appcard(n, when, ability):
    return C(n, "Apprentice",
             '<div class="txt c" style="font-size:9.4pt;font-weight:bold;margin-top:.6mm">'
             'HP 2 &nbsp;|&nbsp; STR 2 &nbsp;|&nbsp; REC 2</div>'
             '<div class="sub" style="margin-top:3.4mm">%s</div>'
             '<div class="txt" style="margin-top:.6mm">%s</div>' % (when, ability),
             'Choose one Apprentice card and one side at setup.')


app_a = [appcard(*a) for a in APPS[0::2]]
app_b = [appcard(*a) for a in APPS[1::2]]
print("Apprentices", render_duplex('NAP_Apprentices', app_a, app_b, 'NAP', LANDSCAPE), 'two-sided')

TAIL = ('After exhausting non-stored dice, complete special color recovery. Then set the dial to the '
        'Primary Assignment dot and move it to the next Time Slot.')
SLOTS = [("Morning", "#9f3f23", "Perform the recovery shown on the dial. No special color recovery on Day 1 Morning."),
         ("Afternoon", "#086c70", "Perform the recovery shown on the dial."),
         ("Evening", "#363c82", "Perform the recovery shown on the dial.")]
cards = []
for nm, band, lead in SLOTS:
    cards.append('<div class="card" style="background:#fbf9f3;border-color:#b8b0a0">'
                 '<div style="height:20mm;background:%s;border-bottom:1mm solid #ffffff33;'
                 'display:flex;align-items:center;justify-content:space-between;padding:0 5mm;color:white">'
                 '<span style="font-size:6.5pt;font-weight:bold;letter-spacing:.16em">TIME SLOT</span>'
                 '<strong style="font-family:DejaVu Serif,serif;font-size:21pt;line-height:1">%s</strong></div>'
                 '<div style="flex:1;padding:4mm 5mm;display:flex;flex-direction:column;'
                 'justify-content:center;color:#2a2119">'
                 '<div style="color:#6b3f8c;font-size:6.5pt;font-weight:bold;letter-spacing:.12em;'
                 'text-transform:uppercase;margin-bottom:2mm">%s</div>'
                 '<div style="font-size:8pt;font-weight:bold;line-height:1.28">%s</div>'
                 '<div style="font-size:6.5pt;line-height:1.25;color:#655b4e;margin-top:2mm">%s</div>'
                 '</div></div>' % (band, nm,
                 {'Morning':'Start the day','Afternoon':'Continue the work','Evening':'Close the day'}[nm],
                 lead, TAIL))
# Three FINF cards, numbered for the Time Slot they act on.
FINF_SLOTS = [(1, 'Morning', '#9f3f23'), (2, 'Afternoon', '#086c70'), (3, 'Evening', '#363c82')]
for number, slot, band in FINF_SLOTS:
    cards.append(C("Following in Nobulous' Footsteps",
       "FINF %d &middot; %s" % (number, slot),
       '<div class="row" style="gap:4mm;align-items:center;margin-top:1mm">'
       '<div style="width:14mm;height:14mm;border-radius:50%%;background:%s;color:#fff;'
       'display:flex;align-items:center;justify-content:center;font-size:19pt;font-weight:bold">%d</div>'
       '<div style="font-size:8.6pt;font-weight:bold;letter-spacing:.1em;text-transform:uppercase;'
       'color:#655b4e">%s</div></div>'
       '<div class="sub" style="margin-top:2.6mm">Increase</div>'
       '<div class="txt" style="margin-top:.4mm">Add an Assignment to the specified Time Slot.</div>'
       '<div class="sub" style="margin-top:2.2mm">Reduce</div>'
       '<div class="txt" style="margin-top:.4mm">Remove a non-Final-Exam card from the specified '
       'Time Slot.</div>' % (band, number, slot),
       'Not used during the Final Exam.', acc='#7a2f52'))

print("Slots + FINF", render_deck('NAP_SlotsFINF', cards, 'NAP', LANDSCAPE,
            # FINF shuffles into the Assignment deck, so it takes that back.
            back=['CardBack_NAP_TimeSlot'] * len(SLOTS)
                 + ['CardBack_NAP_Assignment'] * len(FINF_SLOTS)))

