import re
import sys; sys.path.insert(0, '/home/claude/cards')
from gen import render_deck, render_duplex, make_back, hdr_fit, title_cls, DOT, LANDSCAPE, PORTRAIT, subj_icon

# The shape of the cards being built, for header measurement.
CARD_SIZE = PORTRAIT

# Match each NRJ card to its base-game analog.
BAT_H, NAP_H, AOS_H = '#2c5f4a', '#6b3f8c', '#8a3d2e'
CAT = {'Power': '#8a3d2e', 'Mobility': '#2c6e63', 'Defense': '#3c5a8a', 'Senses': '#6b4a8a'}
NAP_SETBACK, NAP_OPP = '#2f6ba8', '#c79a1e'
AOS_LIM = '#2f5966'
DOMAIN = {'Knowledge': NAP_H, 'Physical': BAT_H, 'Cover-Up': AOS_H}
MOD_STRIP = '#4a4238'


def C(title, sub, body, ftr='', warn=False, acc=None, tint=None, hdr=None,
      flavor=''):
    f = ('<div class="ftr%s">%s</div>' % (' warn' if warn else '', ftr)) if ftr else ''
    # Flavour sits under the rules and above the footer, as build_bat.C does.
    fl = ('<div class="flavor c">%s</div>' % flavor) if flavor else ''
    cls = title_cls(title, CARD_SIZE)
    st = ' style="--a:%s"' % acc if acc else ''
    bs = ' style="background:%s"' % tint if tint else ''
    # `hdr` fixes the header depth for a whole deck, so a two-line title does
    # not push the body down relative to a one-line one.
    hs = hdr_fit(title, cls, CARD_SIZE) if hdr is None else hdr
    return ('<div class="card nrj"%s><div class="hdr"%s><div class="t%s">%s</div>'
            '<div class="s">%s</div></div>'
            '<div class="body"%s>%s<div class="spacer"></div>%s%s</div>'
            '<div class="nrjtag">Nobulous Research Journal</div></div>'
            % (st, ' style="%s"' % hs if hs else '', cls, title, sub, bs, body, fl, f))


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
 ("Extra Limbs", "Mobility &middot; Value 4", "Tap: roll 1 exhausted Green or Yellow die. While held, the holder may not borrow dice.",
  "The tailor asks how many sleeves. Nobulous asks how soon he needs to know."),
 ("Secondary Brain", "Senses &middot; Value 4", "Tap before rolling: +1 STR for this Experiment/attack. While held, the holder may not use the Red die.",
  "A second opinion, now available during the first."),
 ("Adrenal Gland", "Power &middot; Value 5", "Tap: +3 damage. While held, the holder has 1 less Health, minimum 1.",
  "The gland arrives packed in ice. The ice is sweating."),
 ("Bone Plating", "Defense &middot; Value 4", "Reduce incoming damage by 2. While held, the holder has -1 REC, minimum 1.",
  "The skeleton has taken an interest in exterior work."),
 ("Redundant Organs", "Defense &middot; Value 5", "The first time the holder would be knocked out, discard this card instead; the holder remains at 1 Health. While held, the holder cannot be selected as active on consecutive turns.",
  "Nobulous counts the kidneys twice. He prefers the larger answer."),
 ("Hypermetabolism", "Senses &middot; Value 4", "Tap: recover +2 dice. While held, exhaust 1 available die at the end of each Experiment the holder attempts, Purple first; if it holds no Purple, exhaust its weakest.",
  "The feeding schedule has been replaced by a chute."),
]
NOTES = [
 ("Unexpected Resilience", "Claim after a Rat completes an Experiment without committing Red. Claiming gives up the next Upgrade a completed Experiment earns.", "Once per game, recover all of that Rat's dice."),
 ("Successful Integration", "Claim when a Rat holds a Specimen. Claiming gives up the next Upgrade a completed Experiment earns.", "Once per game, ignore the +1 Target from revealing a Specimen."),
 ("Acceptable Losses", "Claim after failing 3 Experiments within the same four-Rat rotation. Claiming gives up the next Upgrade a completed Experiment earns.", "Once per game after another failure, choose which revealed Upgrade is Spliced."),
 ("Cross-Species Compatibility", "Claim after a Rat completes an Experiment using a borrowed die. Claiming gives up the next Upgrade a completed Experiment earns.", "Once during the Tyrant battle, the active Rat may tap an Upgrade held by another surviving Rat."),
 ("Controlled Failure", "Claim after deliberately committing zero dice to an Experiment. Claiming gives up the next Upgrade a completed Experiment earns.", "Once later, after revealing an Experiment, discard it and reveal the next one instead."),
 ("Red Means Go", "Claim after Red provides the success that completes an Experiment and at least one die belonging to another Rat also contributed. Claiming gives up the next Upgrade a completed Experiment earns.", "Once per game after using Red, place it directly on any non-active Rat rather than setting it aside."),
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
            flavor=fl, acc=CAT[s.split(' ')[0]], tint='#f6f2ea') for n, s, e, fl in MODS]
notes = [C(n, "NRJ &middot; Research Note", '<div class="sub">Claim when earned</div>' + T(c) +
            '<div class="sub" style="margin-top:2.5mm">Reward</div>' + T(r),
            'Tier III &mdash; Exploitation.', acc=BAT_H) for n, c, r in NOTES]
print("Protocols", render_deck('NRJ_BAT_Protocols', prot, 'NRJ', back='CardBack_NRJ_Protocol'))
print("Modifications", render_deck('NRJ_BAT_Modifications', mods, 'NRJ', back='CardBack_NRJ_Protocol'))
print("Research Notes", render_deck('NRJ_BAT_ResearchNotes', notes, 'NRJ', back='CardBack_NRJ_ResearchNote'))


# name, subject, recovery-color dot, ReqTarget, DemTarget, effect.
# The dot is not decoration: Required Effort, completing, storing progress
# and the next slot's queued colour all read "that Assignment's color dot",
# so an Assignment without one is under-specified. One of each colour, each
# matching a colour its own subject already uses.
# Not IMPOSTERS, which is the five hero cards further down. These are
# NAP's four Tier II Assignments.
IMPOSTER_TASKS = [
 ("Neural Extraction Practicum", "Anatomy", 'P', 5, 6, "One die committed here remains locked until the end of the Day even if completed."),
 ("Load-Bearing Prosthetics", "Engineering", 'B', 4, 5, "At least 2 applied successes must come from the same color."),
 ("Emergency Specimen Handling", "Procedure", 'Y', 4, 5, "Before rolling, commit at least 2 dice initially."),
 ("Containment Drill", "Theory", 'G', 4, 5, "If unresolved, exhaust 1 available die before flipping it to Demand."),
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
# TARGETS RAISED 2026-11-06 to 4/4/5/5/4/5, which is what the six base
# Opportunities these REPLACE cost - nap.OPPORTUNITIES. They were 3/3/3/3/4/3,
# a mean of 3.17 against the base 4.50, so Tier III was handing out six cards
# that were both stronger and cheaper than the ones they displaced. Tier I's
# own note already states the principle: the Following Setbacks "displace base
# Setbacks of similar weight". This is the same rule applied to Tier III, and
# it is a cost correction, not a re-pitch - see simulation/RESULTS.txt.
DEVIOUS = [
 ("Borrow the Master's Notes", 'G', 4, "Exhaust 2 available dice to immediately complete one Request-side non-Credit Task with printed Target 4 or less.", "now"),
 ("Raid the Supply Cabinet", 'Y', 4, "Final Exam: recover 3 exhausted dice of different colors before any one exam.", "exam"),
 ("Extra Credit?", 'G', 5, "Gain 1 Credit in the subject of the most recently completed Task; then reveal an additional Assignment.", "now"),
 ("Helpful Test Subject", 'B', 5, "Final Exam: after rolling one exam, reroll any number of failed dice.", "exam"),
 ("Nobulous Owes You One", 'P', 4, "Final Exam: reduce one exam's Target by 3.", "exam"),
 ("Definitely Curriculum-Approved", 'Y', 5, "Final Exam: ignore one exam's printed restriction.", "exam"),
]
DEV_FOOTER = {
 "now": "Optional. No storage. Resolve immediately. Tier III &mdash; Exploitation.",
 "exam": "Optional. No storage. When completed, keep this card: spend it once during the "
         "Final Exam, or discard it during the apprenticeship to ignore one Setback's "
         "restrictions for the rest of the game. Tier III &mdash; Exploitation.",
}
# Imposter Tasks use the base NAP Task layout: spine name, Request band top,
# Demand band bottom, key rule on the right spine.
CARD_SIZE = LANDSCAPE
imp = []
for n, subj, dot, rt, dt, e in IMPOSTER_TASKS:
    # Same marks block as a base Task: subject icon, then the colour dot.
    marks = ('<div class="marks">%s<div class="dt" style="background:%s">'
             '</div></div>' % (subj_icon(subj), DOT[dot]))
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
             '<span class="penlbl" style="color:#6b3f8c">Imposter Task &nbsp;</span>'
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
print("Imposter Tasks", render_deck('NRJ_NAP_ImposterTasks', imp, 'NRJ', LANDSCAPE, back='CardBack_NAP_Assignment'))
print("Following Setbacks", render_deck('NRJ_NAP_FollowingSetbacks', fol, 'NRJ', LANDSCAPE, back='CardBack_NAP_Assignment'))
print("Devious Opportunities", render_deck('NRJ_NAP_DeviousOpportunities', dev, 'NRJ', LANDSCAPE, back='CardBack_NAP_Assignment'))
CARD_SIZE = PORTRAIT

# THE RECYCLE CLAUSE IS CAPPED AT ONCE PER PROGRAM. It read "WHEN an
# already-Overheated Program fails" until 2026-11-06, with no limit, and
# measured 1.2% at Tier I against a 51.8% solo column - a loss rather than a
# difficulty setting, drawn 1 game in 6. The clause is the whole of it: with
# the recycle off the card reads 52.1%, ABOVE the solo column, so this wants
# capping and not cutting. Normal escalation is stable -> overheated ->
# aside; "begin all Programs Overheated" starts every Program at the SECOND
# step, so the clause replaced the THIRD and nothing could ever leave the
# deck. "The first time each" gives every Program one reprieve and reads
# 34.9%, which puts the card beside Memory Leak as the harshest of the six
# rather than outside the deck. See RECYCLE_LIMIT in simulation/aos.py.
INTF = [
 ("I Don't Have Time for This", "Begin all Programs Overheated. The first time each already-Overheated Program fails, cycle it to the bottom of its deck instead of setting it aside."),
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
 ("Diagnostic Port", "Claim after completing a Program with no element over-allocated. Claiming gives up the next Program Reward you would claim.", "Later, reroll one entire Strategy roll."),
 ("Privilege Escalation", "Claim after completing an Overheated Program without failing an element. Claiming gives up the next Program Reward you would claim.", "Later, ignore one Limitation."),
 ("Resource Fork", "Claim after completing a Program while committing no more than Target + 1 dice in total beyond its summed Targets. Claiming gives up the next Program Reward you would claim.", "Later, recover 2 exhausted dice."),
 ("Packet Sniffer", "Claim after completing a Program with Crits on at least two different elements. Claiming gives up the next Program Reward you would claim.", "Later, look at the next Limitation before selecting a Program."),
 ("Garbage Collection", "Claim after completing a Program while at least 4 dice are exhausted. Claiming gives up the next Program Reward you would claim.", "Later, recover one die of each of two different colors."),
 ("Root Access", "Claim after completing a Program with Optimal Implementation on at least two elements. Claiming gives up the next Program Reward you would claim.", "During Advanced Programming, treat one failed element as successful."),
]
intf = [C(n, "NRJ &middot; Nobulous Interference", '<div class="sub">Draw 1 at setup</div>' + T(e),
           'Tier I &mdash; Agenda.', acc=AOS_H) for n, e in INTF]
corr = [C(n, "NRJ &middot; Corrupted Limitation",
            T("Withhold 2 available dice of a <b>randomly selected</b> color "
              "that this Program does <b>not</b> require.") +
            '<div class="sub" style="margin-top:2.5mm">Corruption</div>' + T(e),
            'Reveal before committing required-color dice. Withheld dice cannot be used in this Program. '
            'If the Program requires every color, select any. Tier II &mdash; Contamination.',
            acc=AOS_LIM) for n, e in CORRUPT]
bkd = [C(n, "NRJ &middot; Backdoor Routine",
            '<div class="sub">Maximum 2 Backdoor Routines claimed per game</div>' + T(c) +
            '<div class="sub" style="margin-top:2.5mm">Reward</div>' + T(r),
            'Once you have claimed 2, you cannot claim more. Tier III &mdash; Exploitation.',
            warn=True, acc=AOS_H) for n, c, r in BACKDOOR]
print("Interference", render_deck('NRJ_AoS_Interference', intf, 'NRJ', back='CardBack_NRJ_Interference'))
print("Corrupted Limitations", render_deck('NRJ_AoS_CorruptedLimitations', corr, 'NRJ', back='CardBack_AoS_Limitation'))
print("Backdoor Routines", render_deck('NRJ_AoS_BackdoorRoutines', bkd, 'NRJ', back='CardBack_NRJ_BackdoorRoutine'))

# The 24 Council Tests. The Scenario clause in the last column is the card's
# ORIGINAL text and is no longer rendered - see exhibit_body below. The
# printed Target stays 8 / 9 / 10 here because that spread is the deck's
# provenance and simulation/finale.py asserts it.
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
# THE EXHIBIT FACE. An Exhibit's Target is the printed Council Test Target
# minus EXHIBIT_OFFSET, and it deals 2 Damage at BIG_TARGET or above and 1
# below it. Both were table arithmetic until 2026-10-30; they are printed
# now. The Scenario clause in SCEN above is kept as the record of what the
# card used to say and is no longer rendered - the finale uses none of it.
EXHIBIT_OFFSET = 5
BIG_TARGET = 5

# The five Rewards that still pay in a currency this finale has. "If you
# succeed" is reworded to the event the finale actually has: the Exhibit
# falling. These five are worth +7.8 points of win rate and are the reason
# REC is 3 rather than 4 - see simulation/finale.py. DO NOT ADD TO THIS
# TABLE without re-running the grid; a sixth paying Reward is a balance
# change, not a text change.
EXHIBIT_REWARD = {
    "The Chamber Mechanism": "When this Exhibit falls, recover 2 exhausted dice.",
    "The Sedative Ledger": "When this Exhibit falls, recover 3 exhausted dice.",
    "The Vote": "When this Exhibit falls, recover all exhausted dice of one color.",
    "Tracks in the Yard": "When this Exhibit falls, recover 1 exhausted die of each of two colors.",
    "The Narrow Stair": "When this Exhibit falls, the next Exhibit you deploy has its Target reduced by 1.",
}

# THE OTHER NINETEEN ARE COURTESIES, AND THEY DO NOTHING. Every Exhibit
# prints a Reward band, because nineteen cards reading Target and Damage
# over an inch of white space look unfinished, and because a Reward band on
# only five of them tells a player across the table which five matter
# before anything is turned over. The courtesies cost nothing: they are
# flavour, set in italics where a real Reward is upright, and no simulation
# number moves.
#
# TWO RULES KEEP THEM READABLE AS FLAVOUR, and both are enforced below:
#   - a courtesy NEVER opens "When this Exhibit falls". That phrase belongs
#     to the five that pay, and it is the player's cue.
#   - a courtesy NEVER names a thing the game has. That is the checkable
#     form of "it must not read as a rule"; grammatical mood is not, since
#     "Help yourself to anything that isn't smoking" is imperative and
#     plainly flavour, while "the next Exhibit you deploy" is a statement
#     of fact and plainly a rule. What makes a line safe is that nothing
#     in it can be acted on: a brooch, a candlestick and a moth are not
#     components. COURTESY_FORBIDDEN is the list; check_app_sync.py reads
#     it from here and applies it, so a courtesy that drifts fails the
#     check people actually run rather than only the build.
# Sixteen of these cards were never Reward cards at all - they were
# Constraints, Aggravators and Reliefs, and the rework drops every Scenario
# clause. The other three (An Unwelcome Embrace, The Night Watchman's
# Account, Across the Chamber) WERE printed Rewards whose effect modified a
# single attempt, which this finale has no unit for. finale.py puts
# restoring them at +1.3 points, which is outside the one-point tolerance
# the four difficulty rungs hold to, so they get a courtesy like the rest.
EXHIBIT_COURTESY = {
    # Knowledge
    "The Physician's Greeting": "For once, the physician warms his hands.",
    "An Old Injury": "Your limp is entered into the minutes as a longstanding commitment to the institution.",
    "Failed Apparatus": "Help yourself to anything that isn’t smoking.",
    "Order of Precedence": "After considerable debate, you are permitted to enter before the sandwiches.",
    "A Disputed Citation": "The passage is found in the Chairman’s own book. He proposes a short recess.",
    "The Long Argument": "You have the last word, delivered to a room of empty chairs.",
    # Physical
    "The Ceremonial Seal": "A handsome lump of wax, yours to treasure.",
    "An Unwelcome Embrace": "Released at last, you discover that you have acquired a brooch and lost a button.",
    "A Sudden Fall": "“Excellent reflexes,” observes the member who was standing behind you.",
    "The Long Session": "By dawn, even your enemies are voting to let you leave.",
    "Tainted Wine": "A better vintage is brought up from the cellar while someone quietly waters the fern with yours.",
    "Across the Chamber": "A solitary clap greets your return. The moth had been bothering him all evening.",
    "The Darkened Corridor": "You may borrow the candlestick, provided you stop asking about the scratches around the lock.",
    # Cover-Up
    "The Night Watchman's Account": "The watchman retracts his statement in exchange for a chair facing away from the courtyard.",
    "An Open Window": "“Fresh air,” explains the Chairman, brushing soil from his cuffs.",
    "Someone Was Seen": "You are invited to supply a less distinctive description of yourself.",
    "Rope Burns": "The cord is returned to you in a gift box.",
    "The Missing Hours": "Midnight through three is struck from the inquiry. A member asks whether eleven might also be available.",
    "A Second Search": "This time they let you watch.",
}

# A narrative line under each of the five that pay. Flavour only, like a
# courtesy, and held to the same rules - it may not borrow the cue phrase
# and may not name a thing the game has. It is set in the courtesy's
# italics so that the bold Reward above it stays the thing you read.
EXHIBIT_REWARD_FLAVOR = {
    "The Chamber Mechanism": "The clerk demonstrates the catch from behind someone else’s chair.",
    "The Vote": "The Chairman empties his pockets. The motion passes.",
    "The Narrow Stair": "You are offered the service stairs, where fewer portraits can watch you struggle.",
    "Tracks in the Yard": "The gardener is asked to rake more discreetly.",
    "The Sedative Ledger": "Your dose is crossed out in a hand you recognize.",
}

# Words that name something the game has. A courtesy containing one of
# these is either a rule or reads like one; nineteen pieces of Council
# flavour have no business mentioning any of them.
COURTESY_FORBIDDEN = (
    "die", "dice", "target", "damage", "health", "exhibit", "exhibits",
    "card", "cards", "success", "successes", "crit", "crits", "recover",
    "exhaust", "exhausted", "color", "colors", "session", "sessions",
    "dossier", "suspicion", "deploy", "banish", "commit",
)

_overlap = sorted(set(EXHIBIT_REWARD) & set(EXHIBIT_COURTESY))
_absent = sorted(n for n, _d, _c, _t, _e in SCEN
                 if n not in EXHIBIT_REWARD and n not in EXHIBIT_COURTESY)
_flavour = dict(EXHIBIT_COURTESY, **EXHIBIT_REWARD_FLAVOR)
_cue = sorted(n for n, t in _flavour.items()
              if "When this Exhibit falls" in t)
_names = sorted(n for n, t in _flavour.items()
                if re.search(r'(%s)' % '|'.join(COURTESY_FORBIDDEN), t, re.I))
_unpaid = sorted(set(EXHIBIT_REWARD_FLAVOR) - set(EXHIBIT_REWARD))
if _overlap or _absent or _cue or _names or _unpaid:
    raise SystemExit("Exhibit Rewards: %s pay twice, %s print nothing, %s borrow "
                     "the cue phrase, %s name something the game has, %s carry a "
                     "Reward flavour line without a Reward"
                     % (_overlap, _absent, _cue, _names, _unpaid))


def exhibit_body(name, target):
    damage = 2 if target >= BIG_TARGET else 1
    # A FIXED top margin, not a centring spacer. Centring floats the
    # numbers higher on the five cards that also carry a Reward, and the
    # Target is the one thing a player reads across a row of face-up
    # Exhibits - it has to sit at the same height on all 24.
    stats = ('<div class="row" style="justify-content:center;gap:7mm;'
             'margin-top:6mm">'
             '<div><div class="big">%d</div><div class="biglbl">Target</div></div>'
             '<div><div class="big">%d</div><div class="biglbl">Damage</div></div>'
             '</div>' % (target, damage))
    # The band is on all 24; only the five in EXHIBIT_REWARD do anything.
    # Bold upright text is a rule, italic text is the Council being
    # gracious. The weight carries across a table where the italics do not:
    # at arm's length you can see WHICH Exhibit pays without reading it.
    # The <b> lives here rather than in EXHIBIT_REWARD so that the table
    # stays plain strings - check_app_sync.py and finale.py read it.
    def italic(text, top):
        # Mid-body, under the Reward subhead rather than above the footer, so
        # the top margin is the only thing set here; gen.py owns the rest.
        return ('<div class="flavor c" style="margin:%smm 0 0">%s</div>'
                % (top, text))

    stats += '<div class="sub" style="margin-top:3.2mm">Reward</div>'
    reward = EXHIBIT_REWARD.get(name)
    if reward:
        # The narrative line is tucked closer to the Reward than a courtesy
        # is to the band, so it reads as a remark on the Reward rather than
        # as a second clause of it.
        stats += T('<b>%s</b>' % reward, 'txt c sm')
        stats += italic(EXHIBIT_REWARD_FLAVOR[name], '1.6')
    else:
        stats += italic(EXHIBIT_COURTESY[name], '2')
    return stats


def _hdr_mm(style):
    return float(style.split(':')[1].rstrip('mm')) if style else 0.0


def _cls(title):
    return title_cls(title, CARD_SIZE)


# The deepest header any Exhibit title needs, applied to all of them, so the
# Target sits at one height across a row of face-up cards.
EXHIBIT_HDR = max((hdr_fit(n, _cls(n), CARD_SIZE) for n, _d, _c, _t, _e in SCEN),
                  key=_hdr_mm)

cards = [C(n, "%s Exhibit &middot; %s" % (dom, cat.split(" - ")[0]),
           exhibit_body(n, t - EXHIBIT_OFFSET),
           'Dossier. A retained %s card reduces this Target by 2, to a minimum of 1.'
           % {'Knowledge': 'NAP', 'Physical': 'BAT', 'Cover-Up': 'AoS'}[dom],
           acc=DOMAIN[dom], hdr=EXHIBIT_HDR) for n, dom, cat, t, e in SCEN]
print("Exhibits", render_deck('NRJ_ImposterScenarios', cards, 'IMP', back='CardBack_NRJ_CouncilTest'))


# ---- The Imposters: 5 two-sided cards, 10 abilities ------------------------
# WHO YOU ARE PRETENDING TO BE. Every side prints the finale's own statline,
# 5 HP / 2 STR / 3 REC, because the house rule across the set is that heroes
# differ only in ability text (AoS and NAP say so in as many words; see
# simulation/cards.py). The choice is one Imposter and one of its sides.
#
# WHAT THEY MAY NOT TOUCH, measured in simulation/finale.py:
#   STR         a point is worth 85 points of win rate
#   REC         REC 4 inverts the commit decision and the finale stops
#               being a game of holding dice back
#   the window  a third colour reads 90%
#   the PHASE   the attention wheel's phase swings the finale 27 points
#               (8 sessions 23.8%, 9 sessions 50.5%, 10 sessions 21.8%), so
#               a card that holds the dial is a difficulty dial. Measured at
#               +11.9 and cut.
#   dice back,
#   per session nine sessions of one recovered die IS the Nobulous handicap,
#               so these read +15 to +20 at the hard rungs while reading +2
#               at Easy. Every such side was rebuilt as once per Scenario.
#
# Each side is measured at Easy and at a handicapped rung, and has to pass
# both a LEVEL test (close to the others) and a UNIFORMITY test (worth about
# the same at both). See simulation/proto/imposters.py for the table.
IMP_STATS = (5, 2, 3)
IMPOSTERS = [
 ("The Archivist", "Records Clerk", 'A', "Passive", "Cross-Referenced",
  "A retained card may answer an Exhibit at Target 5 of <i>any</i> domain, not only its own.",
  "He finds your alibi filed under Building Maintenance."),
 ("The Archivist", "Records Clerk", 'B', "Once per Scenario", "Precedent",
  "Apply 1 die of <i>any</i> color, ignoring the attention entirely.",
  "Every ruling has a precedent. Finding it is merely clerical."),
 ("The Understudy", "Stand-In", 'A', "Once per Scenario", "Open Audition",
  "Discard 4 Candidates to reroll <i>every</i> committed die that applied nothing this Strategy phase.",
  "The part was always available. Nobody else wanted it."),
 ("The Understudy", "Stand-In", 'B', "Twice per Scenario", "Second Chair",
  "Discard 2 Candidates to reroll one committed die that applied nothing.",
  "Rehearsal is the performance nobody is charged for."),
 ("The Usher", "Doorkeeper", 'A', "Once per Scenario", "Early Admittance",
  "Apply 1 die of the color <i>one step beyond</i> the attention&rsquo;s two colors.",
  "The doors open at the hour. The hour is a matter of interpretation."),
 ("The Usher", "Doorkeeper", 'B', "Once per Scenario", "Double Doors",
  "For one session, the attention covers a <i>third</i> color &mdash; one step beyond its usual two.",
  "He admits your entourage before you have acquired one."),
 ("The Porter", "Chamber Hand", 'A', "Once per Session", "Sleight of Hand",
  "Take 1 die lying on a standing Exhibit and exhaust it. That Exhibit keeps its successes.",
  "Nothing was removed. Things were carried."),
 ("The Porter", "Chamber Hand", 'B', "Once per Scenario", "Heavy Lifting",
  "Exhaust 1 available die, then recover 2 exhausted dice.",
  "Two crates, one trip, and a brief disregard for the manifest."),
 ("The Steward", "Chamber Steward", 'A', "Once per Scenario", "Requisition",
  "Commit 1 exhausted die of a color the attention allows. It remains exhausted afterward.",
  "Your requisition was approved yesterday. He suggests dating it accordingly."),
 ("The Steward", "Chamber Steward", 'B', "Once per Scenario", "Standing Order",
  "Take a third Strategy phase this session.",
  "The session runs until the business concludes. He decides what the business is."),
]

IMP_ACC = {"The Archivist": NAP_H, "The Understudy": '#6b4a2e',
           "The Usher": '#3c5a8a', "The Porter": BAT_H,
           "The Steward": AOS_H}


def impcard(n, role, side, trig, an, at, fl):
    hp, st, rec = IMP_STATS
    return C(n, "Imposter &middot; %s &mdash; Side %s" % (role, side),
             '<div class="txt c" style="font-size:9.4pt;font-weight:bold;'
             'margin-top:.6mm">HP %d &nbsp;|&nbsp; STR %d &nbsp;|&nbsp; '
             'REC %d</div>'
             '<div class="sub" style="margin-top:3mm">%s &middot; %s</div>'
             '<div class="txt" style="margin-top:.4mm">%s</div>'
             '<div class="flavor c" style="margin:1.6mm 0 0">%s</div>'
             % (hp, st, rec, trig, an, at, fl),
             'Choose one Imposter and one of its sides at setup.',
             acc=IMP_ACC[n])


CARD_SIZE = LANDSCAPE
imp_a = [impcard(*i) for i in IMPOSTERS[0::2]]
imp_b = [impcard(*i) for i in IMPOSTERS[1::2]]
print("Imposters", render_duplex('NRJ_Imposters', imp_a, imp_b, 'IMP',
                                 LANDSCAPE), 'two-sided')
CARD_SIZE = PORTRAIT
