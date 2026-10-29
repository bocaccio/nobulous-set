import sys; sys.path.insert(0, '/home/claude/cards')
from gen import render_deck, make_back, hdr_fit, DOT, LANDSCAPE, PORTRAIT, subj_icon

# The shape of the cards being built, for header measurement.
CARD_SIZE = PORTRAIT

# Match each NRJ card to its base-game analog.
BAT_H, NAP_H, AOS_H = '#2c5f4a', '#6b3f8c', '#8a3d2e'
CAT = {'Power': '#8a3d2e', 'Mobility': '#2c6e63', 'Defense': '#3c5a8a', 'Senses': '#6b4a8a'}
NAP_SETBACK, NAP_OPP = '#2f6ba8', '#c79a1e'
AOS_LIM = '#2f5966'
DOMAIN = {'Knowledge': NAP_H, 'Physical': BAT_H, 'Cover-Up': AOS_H}
MOD_STRIP = '#4a4238'


def C(title, sub, body, ftr='', warn=False, acc=None, tint=None):
    f = ('<div class="ftr%s">%s</div>' % (' warn' if warn else '', ftr)) if ftr else ''
    cls = ' xlong' if len(title) > 30 else (' long' if len(title) > 19 else '')
    st = ' style="--a:%s"' % acc if acc else ''
    bs = ' style="background:%s"' % tint if tint else ''
    hs = hdr_fit(title, cls, CARD_SIZE)
    return ('<div class="card nrj"%s><div class="hdr"%s><div class="t%s">%s</div>'
            '<div class="s">%s</div></div>'
            '<div class="body"%s>%s<div class="spacer"></div>%s</div>'
            '<div class="nrjtag">Nobulous Research Journal</div></div>'
            % (st, ' style="%s"' % hs if hs else '', cls, title, sub, bs, body, f))


def dotspan(c):
    return '<span style="display:inline-block;width:2.8mm;height:2.8mm;border-radius:50%%;' \
           'background:%s;border:.4pt solid #6b6459;vertical-align:-.4mm"></span>' % DOT[c]


def successes_row(dot, count, color):
    """Same shape as the NAP Opportunity / Setback cards."""
    return ('<div class="row" style="gap:3mm;align-items:center">%s'
            '<div style="font-size:24pt;font-weight:bold;color:%s;line-height:1">%d</div>'
            '<div style="font-size:6.4pt;letter-spacing:.14em;text-transform:uppercase;color:#8a8272">'
            'Successes</div></div>' % (dotspan(dot), color, count))


def T(x, cls='txt'):
    return '<div class="%s">%s</div>' % (cls, x)


PROTOCOLS = [
 ("Cross-Contamination", "The first time each Rat borrows a die, it may borrow any color regardless of Upgrade count. If that die is banished, reveal the top 3 Upgrades and Splice them into the Tyrant."),
 ("Shared Equipment Budget", "At setup, randomly select 1 personal die and place it in a common Equipment pool. After completing an Experiment, the active Rat may exchange up to 2 personal dice with Equipment dice."),
 ("Accelerated Trials", "Experiments with printed Target 5+ have -1 Target. Before every such attempt, exhaust 2 of the active Rat's available dice, Purple first; if it holds no Purple, exhaust its weakest."),
 ("Questionable Procurement", "Shuffle 1 additional random Specimen into the Upgrade deck. The first Specimen acquired by each Rat does not count against its 3-Upgrade limit until that Rat gains another Upgrade."),
 ("Independent Funding", "At the start of each Experiment with printed Target 4 or lower, exhaust 2 of the active Rat's available dice, Blue first; if it holds no Blue, exhaust its weakest. The grant funds ambitious work only. When a Rat lends a die to a Rat holding fewer Upgrades and that Experiment is completed, the lender recovers 1 die."),
 ("Questionable Methodology", "After revealing the two Upgrades for an Experiment with printed Target 5+, Splice the stronger one into the Tyrant and reveal a replacement. This is not optional."),
]
MODS = [
 ("Extra Limbs", "Mobility &middot; Value 4", "Tap: roll 1 exhausted Green or Yellow die. While held, the holder may not borrow dice."),
 ("Secondary Brain", "Senses &middot; Value 4", "Tap before rolling: +1 STR for this Experiment/attack. While held, the holder may not use the Red die."),
 ("Adrenal Gland", "Power &middot; Value 5", "Tap: +3 damage. While held, the holder has 1 less Health, minimum 1."),
 ("Bone Plating", "Defense &middot; Value 4", "Reduce incoming damage by 2. While held, the holder has -1 REC, minimum 1."),
 ("Redundant Organs", "Defense &middot; Value 5", "The first time the holder would be knocked out, discard this card instead; the holder remains at 1 Health. While held, the holder cannot be selected as active on consecutive turns."),
 ("Hypermetabolism", "Senses &middot; Value 4", "Tap: recover +2 dice. While held, exhaust 1 available die at the end of each Experiment the holder attempts, Purple first; if it holds no Purple, exhaust its weakest."),
]
NOTES = [
 ("Unexpected Resilience", "Claim after a Rat completes an Experiment without committing Red.", "Once per game, recover all of that Rat's dice."),
 ("Successful Integration", "Claim when a Rat holds a Specimen.", "Once per game, ignore the +1 Target from revealing a Specimen."),
 ("Acceptable Losses", "Claim after failing 3 Experiments within the same four-Rat rotation.", "Once per game after another failure, choose which revealed Upgrade is Spliced."),
 ("Cross-Species Compatibility", "Claim after a Rat completes an Experiment using a borrowed die.", "Once during the Tyrant battle, the active Rat may tap an Upgrade held by another surviving Rat."),
 ("Controlled Failure", "Claim after deliberately committing zero dice to an Experiment.", "Once later, after revealing an Experiment, discard it and reveal the next one instead."),
 ("Red Means Go", "Claim after Red provides the success that completes an Experiment and at least one die belonging to another Rat also contributed.", "Once per game after using Red, place it directly on any non-active Rat rather than setting it aside."),
]
NRJ_BLUE = '#1f4e6b'
# Card backs first: the deck PnPs interleave them behind the fronts.
make_back('CardBack_NRJ_Protocol', 'NRJ', 'Experimental Protocol', NRJ_BLUE)
make_back('CardBack_NRJ_ResearchNote', 'NRJ', 'Research Note', NRJ_BLUE)
make_back('CardBack_NRJ_Interference', 'NRJ', 'Nobulous Interference', NRJ_BLUE)
make_back('CardBack_NRJ_BackdoorRoutine', 'NRJ', 'Backdoor Routine', NRJ_BLUE)
make_back('CardBack_NRJ_CouncilTest', 'Council Test', 'Imposter Scenario', '#4a3b6b')
print("card backs done")

prot = [C(n, "NRJ &middot; Experimental Protocol", '<div class="sub">Draw 1 at setup</div>' + T(e),
           'Tier I &mdash; Agenda.', acc=BAT_H) for n, e in PROTOCOLS]
mods = [C(n, "NRJ &middot; " + s,
            '<div style="background:%s;color:#fff;font-size:6.2pt;font-weight:bold;letter-spacing:.18em;'
            'text-transform:uppercase;text-align:center;padding:.9mm;margin:-2.4mm -2.4mm 0">'
            'Unauthorized</div>' % MOD_STRIP + T(e),
            'Either a Rat or the Tyrant may hold this card. Tier II &mdash; Contamination.',
            acc=CAT[s.split(' ')[0]], tint='#f6f2ea') for n, s, e in MODS]
notes = [C(n, "NRJ &middot; Research Note", '<div class="sub">Claim when earned</div>' + T(c) +
            '<div class="sub" style="margin-top:2.5mm">Reward</div>' + T(r),
            'Tier III &mdash; Exploitation.', acc=BAT_H) for n, c, r in NOTES]
print("Protocols", render_deck('NRJ_BAT_Protocols', prot, 'NRJ', back='CardBack_NRJ_Protocol'))
print("Modifications", render_deck('NRJ_BAT_Modifications', mods, 'NRJ', back='CardBack_NRJ_Protocol'))
print("Research Notes", render_deck('NRJ_BAT_ResearchNotes', notes, 'NRJ', back='CardBack_NRJ_ResearchNote'))


IMPOSTOR = [
 ("Neural Extraction Practicum", "Anatomy", 5, 6, "One die committed here remains locked until the end of the Day even if completed."),
 ("Load-Bearing Prosthetics", "Engineering", 4, 5, "At least 2 applied successes must come from the same color."),
 ("Emergency Specimen Handling", "Procedure", 4, 5, "Before rolling, commit at least 2 dice initially."),
 ("Containment Drill", "Theory", 4, 5, "If unresolved, exhaust 1 available die before flipping it to Demand."),
]
# name, recovery-color dot, successes, effect
FOLLOWING = [
 ("Nobulous Needs This Now", 'Y', 7, "While unresolved, the first die you commit to another Assignment each Time Slot must match that Assignment's recovery-color dot."),
 ("Unscheduled Demonstration", 'G', 7, "While unresolved, you must commit at least one die here before committing dice to another Assignment in this Time Slot."),
 ("Minor Laboratory Fire", 'B', 8, "At the end of each Time Slot this remains unresolved, exhaust 1 available die."),
 ("Where Did I Put That?", 'P', 8, "While unresolved, one die committed here cannot be recovered by Special Recovery."),
]
# name, recovery-color dot, successes, effect
# name, dot, successes, effect, when: "exam" keeps the card for the Final Exam,
# "now" resolves on completion. Tier III banks its help for the exams, where NAP
# is actually lethal; the two immediate cards do things an exam has no room for.
DEVIOUS = [
 ("Borrow the Master's Notes", 'G', 3, "Exhaust 2 available dice to immediately complete one Request-side non-Credit Task with printed Target 4 or less.", "now"),
 ("Raid the Supply Cabinet", 'Y', 3, "Final Exam: recover 3 exhausted dice of different colors before any one exam.", "exam"),
 ("Extra Credit?", 'G', 3, "Gain 1 Credit in the subject of the most recently completed Task; then reveal an additional Assignment.", "now"),
 ("Helpful Test Subject", 'B', 3, "Final Exam: after rolling one exam, reroll any number of failed dice.", "exam"),
 ("Nobulous Owes You One", 'P', 4, "Final Exam: reduce one exam's Target by 3.", "exam"),
 ("Definitely Curriculum-Approved", 'Y', 3, "Final Exam: ignore one exam's printed restriction.", "exam"),
]
DEV_FOOTER = {
 "now": "Optional. No storage. Resolve immediately. Tier III &mdash; Exploitation.",
 "exam": "Optional. No storage. When completed, keep this card: spend it once during the "
         "Final Exam, or discard it during the apprenticeship to ignore one Setback's "
         "restrictions for the rest of the game. Tier III &mdash; Exploitation.",
}
# Impostor Tasks use the base NAP Task layout: spine name, Request band top,
# Demand band bottom, key rule on the right spine.
CARD_SIZE = LANDSCAPE
imp = []
for n, subj, rt, dt, e in IMPOSTOR:
    marks = '<div class="marks">%s</div>' % subj_icon(subj)
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
            '</div></div></div>%s' % (fs, l1, l2, marks))
    right = ('<div class="spine r" style="background:#f3eef7"><div class="track p">'
             '<div class="vert rr nowrap" style="width:52mm">'
             '<span class="penlbl" style="color:#6b3f8c">Impostor Task &nbsp;</span>'
             '<span class="pen" style="color:#6b3f8c">Grants no Credit</span>'
             '</div></div></div>')
    mid = ('<div class="mid">'
           '<div class="band" style="background:#3f7a4e">Request</div>'
           '<div class="half"><div class="row" style="gap:2.8mm;align-items:center">'
           '<div style="font-size:23pt;font-weight:bold;color:#3f7a4e;line-height:1">%d</div>'
           '<div style="font-size:9pt;line-height:1.26">%s</div></div></div>'
           '<div class="rule"></div>'
           '<div class="half d"><div class="row" style="gap:2.8mm;align-items:center">'
           '<div style="font-size:23pt;font-weight:bold;color:#a8332c;line-height:1">%d</div>'
           '<div style="font-size:8.4pt;line-height:1.26">Mandatory. If unresolved, flip to Demand. '
           'Tier II &mdash; Contamination.</div></div></div>'
           '<div class="band d180" style="background:#a8332c">Demand</div>'
           '</div>' % (rt, e, dt))
    imp.append('<div class="card nrj">%s%s%s'
                 '<div class="nrjtag">Nobulous Research Journal</div></div>' % (left, mid, right))
fol = [C(n, "NRJ &middot; Following Setback",
            successes_row(d, t, NAP_SETBACK) + T(e),
            'Mandatory. Follows into the next Time Slot if unresolved, including Evening to the next '
            'Morning. These 4 replace the 3 base Setbacks. Tier I &mdash; Agenda.', warn=True, acc=NAP_SETBACK)
          for n, d, t, e in FOLLOWING]
dev = [C(n, "NRJ &middot; Devious Opportunity",
            successes_row(d, t, '#9a7410') + T(e),
            DEV_FOOTER[w], acc=NAP_OPP) for n, d, t, e, w in DEVIOUS]
print("Impostor Tasks", render_deck('NRJ_NAP_ImpostorTasks', imp, 'NRJ', LANDSCAPE, back='CardBack_NAP_Assignment'))
print("Following Setbacks", render_deck('NRJ_NAP_FollowingSetbacks', fol, 'NRJ', LANDSCAPE, back='CardBack_NAP_Assignment'))
print("Devious Opportunities", render_deck('NRJ_NAP_DeviousOpportunities', dev, 'NRJ', LANDSCAPE, back='CardBack_NAP_Assignment'))
CARD_SIZE = PORTRAIT

INTF = [
 ("I Don't Have Time for This", "Begin all Programs Overheated. When an already-Overheated Program fails, cycle it to the bottom of its deck instead of setting it aside."),
 ("Legacy Hardware", "At setup, choose and banish 1 non-Red die."),
 ("Nobulous Was Here", "Randomly flip 2 Programs to their Overheated sides before play."),
 ("Undocumented Dependencies", "The first element of every Program must receive at least 1 die and no more than its Target."),
 ("Works on My Machine", "A Crit rolled on the second element counts as 3 successes. Crits on every other element count as basic successes."),
 ("Memory Leak", "Whenever you over-allocate an element, exhaust 1 additional available die after resolving the Program."),
]
CORRUPT = [
 ("Uneven Architecture", "The first element must receive more dice than the last."),
 ("Memory Collision", "No two adjacent elements may receive the same number of dice."),
 ("Circular Reference", "The first and final elements must receive different numbers of dice."),
 ("Hard-Coded Constant", "Randomly select one element. It must receive exactly its Target number of dice."),
 ("Deprecated Function", "Randomly select one color. Crits rolled by that color count as basic successes for this Program."),
 ("Stack Overflow", "If any element receives 5+ dice, exhaust one die committed to that element before rolling."),
]
BACKDOOR = [
 ("Diagnostic Port", "Claim after completing a Program with no element over-allocated.", "Later, reroll one entire Strategy roll."),
 ("Privilege Escalation", "Claim after completing an Overheated Program without failing an element.", "Later, ignore one Limitation."),
 ("Resource Fork", "Claim after completing a Program while committing no more than Target + 1 dice in total beyond its summed Targets.", "Later, recover 2 exhausted dice."),
 ("Packet Sniffer", "Claim after completing a Program with Crits on at least two different elements.", "Later, look at the next Limitation before selecting a Program."),
 ("Garbage Collection", "Claim after completing a Program while at least 4 dice are exhausted.", "Later, recover one die of each of two different colors."),
 ("Root Access", "Claim after completing a Program with Optimal Implementation on at least two elements.", "During Advanced Programming, treat one failed element as successful."),
]
intf = [C(n, "NRJ &middot; Nobulous Interference", '<div class="sub">Draw 1 at setup</div>' + T(e),
           'Tier I &mdash; Agenda.', acc=AOS_H) for n, e in INTF]
corr = [C(n, "NRJ &middot; Corrupted Limitation",
            T("Withhold 2 available dice of a <b>randomly selected</b> color.") +
            '<div class="sub" style="margin-top:2.5mm">Corruption</div>' + T(e),
            'Reveal before committing required-color dice. Withheld dice cannot be used in this Program. '
            'Tier II &mdash; Contamination.', acc=AOS_LIM) for n, e in CORRUPT]
bkd = [C(n, "NRJ &middot; Backdoor Routine",
            '<div class="sub">Maximum 2 Backdoor Routines claimed per game</div>' + T(c) +
            '<div class="sub" style="margin-top:2.5mm">Reward</div>' + T(r),
            'Once you have claimed 2, you cannot claim more. Tier III &mdash; Exploitation.',
            warn=True, acc=AOS_H) for n, c, r in BACKDOOR]
print("Interference", render_deck('NRJ_AoS_Interference', intf, 'NRJ', back='CardBack_NRJ_Interference'))
print("Corrupted Limitations", render_deck('NRJ_AoS_CorruptedLimitations', corr, 'NRJ', back='CardBack_AoS_Limitation'))
print("Backdoor Routines", render_deck('NRJ_AoS_BackdoorRoutines', bkd, 'NRJ', back='CardBack_NRJ_BackdoorRoutine'))

SCEN = [
 ("The Physician's Greeting", "Knowledge", "Anatomy - Relief", 8, "The first NAP card you spend here also performs its Special Recovery."),
 ("An Old Injury", "Knowledge", "Anatomy - Constraint", 9, "At least 2 Purple or Blue dice must contribute."),
 ("The Chamber Mechanism", "Knowledge", "Engineering - Reward", 8, "If you succeed, recover 2 exhausted dice."),
 ("Failed Apparatus", "Knowledge", "Engineering - Aggravator", 10, "If you fail, place two cards in the Suspicion row."),
 ("Order of Precedence", "Knowledge", "Procedure - Constraint", 9, "Commit dice of at least 3 different colors."),
 ("The Vote", "Knowledge", "Procedure - Reward", 8, "If you succeed, recover all exhausted dice of one color."),
 ("A Disputed Citation", "Knowledge", "Theory - Relief", 9, "This Scenario's Target is not increased by the Suspicion row."),
 ("The Long Argument", "Knowledge", "Theory - Constraint", 10, "You may spend at most one NAP card here."),
 ("The Ceremonial Seal", "Physical", "Power - Constraint", 8, "At least one Purple die must contribute."),
 ("An Unwelcome Embrace", "Physical", "Power - Reward", 9, "+1 STR for this Scenario."),
 ("The Narrow Stair", "Physical", "Mobility - Reward", 8, "If you succeed, the next Scenario's Target is reduced by 1."),
 ("A Sudden Fall", "Physical", "Mobility - Aggravator", 10, "Cannot be avoided with an AoS card."),
 ("The Long Session", "Physical", "Defense - Constraint", 9, "Commit at least 6 dice."),
 ("Tainted Wine", "Physical", "Defense - Aggravator", 10, "On failure you must lose 1 Health; you may not banish dice."),
 ("Across the Chamber", "Physical", "Senses - Reward", 8, "Before rolling, look at the top card of the Scenario deck."),
 ("The Darkened Corridor", "Physical", "Senses - Constraint", 9, "Yellow dice cannot contribute."),
 ("Tracks in the Yard", "Cover-Up", "Approach - Reward", 8, "If you succeed, recover 1 exhausted die of each of two colors."),
 ("The Night Watchman's Account", "Cover-Up", "Approach - Reward", 9, "A Crit counts as 3 successes here."),
 ("An Open Window", "Cover-Up", "Concealment - Constraint", 8, "At least 3 different colors must contribute."),
 ("Someone Was Seen", "Cover-Up", "Concealment - Aggravator", 10, "If avoided, place this on top of the deck rather than the bottom."),
 ("Rope Burns", "Cover-Up", "Restraint - Aggravator", 9, "Before rolling, discard one card from the Research Pool at random."),
 ("The Sedative Ledger", "Cover-Up", "Restraint - Reward", 9, "If you succeed, recover 3 exhausted dice."),
 ("The Missing Hours", "Cover-Up", "Extraction - Aggravator", 10, "+1 additional Target for each card in the Suspicion row."),
 ("A Second Search", "Cover-Up", "Extraction - Relief", 8, "Remove one card from the Suspicion row, then attempt this Scenario normally."),
]
cards = [C(n, "%s Test &middot; %s" % (dom, cat),
           '<div class="big">%d</div><div class="biglbl">Target</div>' % t + T(e, 'txt c'),
           'Imposter Scenario. Discounted by %s cards of the matching category.'
           % {'Knowledge': 'NAP', 'Physical': 'BAT', 'Cover-Up': 'AoS'}[dom],
           acc=DOMAIN[dom]) for n, dom, cat, t, e in SCEN]
print("Scenarios", render_deck('NRJ_ImposterScenarios', cards, 'IMP', back='CardBack_NRJ_CouncilTest'))

