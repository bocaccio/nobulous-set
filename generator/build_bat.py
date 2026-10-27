import sys; sys.path.insert(0, '/home/claude/cards')
from gen import render_deck, render_duplex, make_back, elements, hdr_fit, LANDSCAPE, PORTRAIT, DOT

# The shape of the cards being built, for header measurement.
CARD_SIZE = PORTRAIT

SPEC_FTR = 'If at least one revealed Upgrade is a Specimen, +1 Target total.'
TAP_FTR = 'Tap to use. A tapped Upgrade cannot absorb damage.'

EXPERIMENTS = [
    ("Baseline Calibration", 3, "Flip the active Lab Rat to its other side. That side remains active until another effect flips it.", "Every breakthrough begins by proving the researcher probably still works."),
    ("Fine Motor Trial", 3, "A Yellow die must be committed to this Experiment. If unable to do so, increase the Target by 1.", "Tiny claws. Tiny screws. Absolutely no margin for error."),
    ("Structural Stress Trial", 4, "Reveal 1 additional Upgrade for this Experiment. Resolve the normal Upgrade choice using all revealed options.", "Nobulous calls the third prototype a control. Nobody asks what it controls."),
    ("Contaminated Tissue", 4, "Discard the revealed Upgrades and reveal 2 new Upgrades. These become the Upgrades for this Experiment.", "The sample was sterile until Nobulous explained his definition of sterile."),
    ("Performance Trial", 4, "Discard the top 2 cards of the Experiment deck face down without resolving them.", "The schedule has been accelerated by removing the parts involving caution."),
    ("Load-Bearing Trial", 4, "A Purple die must be committed to this Experiment. If unable to do so, discard this Experiment and draw another one, replacing any revealed Upgrades.", "Add weight until something fails. Preferably not the researcher."),
    ("Diagnostic Trial", 4, "If you commit a Blue die to this Experiment, you may look at the next Experiment and return it to the top of the deck.", "The instruments say everything is fine. The smoke has submitted a dissenting report."),
    ("Rapid Response Trial", 4, "A Green die must be committed to this Experiment. If unable to do so, discard the stronger revealed Upgrade and continue the Experiment.", "There is no time to do it right, only time to make it testable."),
    ("Full-Spectrum Trial", 4, "Committed dice must include 3 different colors.", "Nobulous requested versatility. The equipment requested mercy."),
    ("Workspace Efficiency Study", 4, "You may only commit two dice to this Experiment.", "Four researchers. One bench. Zero lessons learned."),
    ("Restricted Materials Trial", 4, "Place the Red die on the active Rat. Red cannot be used for this Experiment.", "The best reagent is unavailable for reasons marked administrative."),
    ("Independent Performance Trial", 4, "You cannot borrow a die during this Experiment.", "Collaboration introduces confounds. Nobulous has generously removed collaboration."),
    ("Resource Depletion Study", 4, "During your second Strategy phase, you may commit no additional dice.", "There was a second prototype. Past tense."),
    ("Reliability Trial", 4, "Hits and Crits on Purple and Blue dice in the first Strategy phase must be rerolled.", "It only fails when you need it, which is remarkably consistent."),
    ("Reagent Exclusion Trial", 4, "Randomly select one available die belonging to the active Rat. That die cannot be committed to this Experiment.", "Science advances rapidly once you stop checking the labels."),
    ("Containment Failure", 5, "You may choose to reduce the Target by 2. If you do, before committing, roll a Yellow die. On a hit or Crit, banish one available Blue die. Otherwise, banish that Yellow die.", "The blast shield performed exactly as specified. The blast did not."),
    ("Endurance Trial", 5, "STR is 1 for this Experiment.", "The experiment is repeatable. Unfortunately, so is the overtime."),
    ("Field Retrofit Trial", 5, "If successful, you may swap one of the active Rat's Upgrades with one of the revealed Upgrades. Specimens cannot be swapped.", "The replacement fits perfectly once you stop asking what it replaced."),
    ("Methodological Optimization", 5, "You may reduce the Target to 0. If you do, take the weaker revealed Upgrade and Splice the stronger revealed Upgrade into the Prototyrant. If tied, choose which to take.", "Why test both prototypes when the Prototyrant can test the better one?"),
    ("Degraded Tissue Study", 5, "If successful, reduce the Prototyrant's Health dial by 2.", "The tissue is weaker than projected. Nobulous has classified this as progress."),
]

UPGRADES = [
    ("Serrated Claws", "P1 - Power", 2, "+1 damage from each Blue or Green basic hit you apply during this attack.", "Fine motor control was sacrificed for a more persuasive handshake."),
    ("Reinforced Jaw", "P2 - Power", 3, "Add +2 damage to this attack if at least one Purple hit is applied.", "The bite test ended when the test fixture stopped existing."),
    ("Capacitor Muscles", "P3 - Power", 3, "Commit one exhausted Purple or Blue die to the current attack. It remains exhausted afterward.", "Why rest a muscle when you can overvolt it?"),
    ("Piercing Horn", "P4 - Power", 4, "Add +2 damage. If you roll a Yellow hit or Crit, bypass one Defense Upgrade when assigning this attack.", "Evolution took millennia. Nobulous used a drill press."),
    ("Spring-Loaded Legs", "M1 - Mobility", 2, "Roll 1 exhausted Green die. It must match a color already committed to the attack; exhaust it afterward.", "The landing remains an unsolved engineering problem."),
    ("Prehensile Tail", "M2 - Mobility", 2, "Roll 1 exhausted Yellow die. It must match a color already committed to the attack; exhaust it afterward.", "Another limb means another place to hold something dangerous."),
    ("Tripwire Tendons", "M3 - Mobility", 3, "Opponent exhausts one Green die; if unable, one Yellow die, if able.", "Anatomically questionable. Tactically hilarious."),
    ("Evasive Reflexes", "M4 - Mobility", 3, "Remove 1 success from the opponent's next attack.", "The nervous system now reacts several moments before good judgment."),
    ("Thickened Hide", "D1 - Defense", 2, "Reduce incoming damage by 1.", "Subtle? No. Puncture-resistant? Increasingly."),
    ("Layered Carapace", "D2 - Defense", 3, "Reduce incoming damage by 2.", "Nobulous discovered the elegant principle of adding more shell."),
    ("Chromatic Plating", "D3 - Defense", 3, "Reduce damage dealt by Blue and Green dice by 1 each. Yellow dice are unaffected.", "The coating blocks two wavelengths and several reasonable questions."),
    ("Reactive Shell", "D4 - Defense", 4, "Reduce damage dealt by Purple and Yellow dice by 1 each.", "It hardens on impact. It also hardens when startled."),
    ("Acute Hearing", "S1 - Senses", 2, "+1 STR during your next turn.", "You can hear the Tyrant coming. You can also hear Nobulous chewing."),
    ("Predatory Focus", "S2 - Senses", 3, "+1 STR for the current attack.", "Everything unnecessary disappears, including most ethical concerns."),
    ("Rapid Metabolism", "S3 - Senses", 2, "Recover 1 additional die this turn.", "Calories in. Violence out. The lab has charts."),
    ("Neural Overclock", "S4 - Senses", 4, "Recover 2 additional dice this turn.", "The brain is operating beyond specification. So is the smoke."),
]

SPECIMENS = [
    ("Titanium-Toothed Mole", "Power Specimen", "Add +3 damage to the current attack.", "It tunneled through the enclosure, the wall, and part of Accounting."),
    ("Voltaic Mantis", "Power Specimen", "Add +2 damage; one applied Crit deals +2 additional damage.", "Do not ground the specimen. Do not touch the specimen. Too late."),
    ("Blink Hare", "Mobility Specimen", "Roll up to 2 exhausted dice matching colors already committed to this attack.", "It does not teleport. Nobulous is almost certain."),
    ("Ghost Gecko", "Mobility Specimen", "Remove 2 successes from the opponent's next attack.", "The camera sees it. The eye does not. The paperwork sees neither."),
    ("Ironback Beetle", "Defense Specimen", "Reduce incoming damage by 3.", "The shell survived the press. The press has been replaced."),
    ("Prismatic Tortoise", "Defense Specimen", "Reduce damage from two colors of your choice by 1 per die for this attack.", "Its shell refracts light, force, and straightforward explanations."),
    ("Echo Bat", "Senses Specimen", "+1 STR for this turn and recover 1 additional die afterward.", "One squeak maps the room. Two squeaks map your fillings."),
    ("Regenerator Newt", "Senses Specimen", "Recover 3 additional dice this turn.", "Nobulous stopped asking what grows back. The answer was \"yes.\""),
]

ATTACKS = [
    ("Overwhelming Mass", "This attack deals +3 damage."),
    ("Adaptive Strike", "This attack is made against the next Lab Rat clockwise from the active Rat instead of the active Rat, wrapping around the table. Skip any Rat that has been knocked out."),
    ("Predatory Instinct", "This attack is made against the Rat holding the greatest total Upgrade Value instead of the active Rat. If tied, the player chooses. If only one Rat remains, it is the target."),
    ("Spliced Reflexes", "This attack deals +1 damage for each Splice the Tyrant still holds."),
    ("Terrifying Roar", "The Tyrant deals no damage this attack. Instead, exhaust 1 die from the shared battle pool. The player chooses which die."),
    ("Crushing Blow", "1 damage from this attack is dealt directly to the target Rat's Health and cannot be absorbed by Upgrades. Any remaining damage is absorbed normally."),
    ("Unstable Growth", "Resolve this attack. If the target was not knocked out, the Tyrant immediately attacks again, committing 2 dice. Do not reveal a Tyrant Attack card for the second attack."),
]

RATS = [
    ("Rummage", "Scrounger - Side A", 1, 2, 2, "Careful Borrower",
     "When checking whether a die Rummage borrowed is banished, you may reroll the check once."),
    ("Rummage", "Scrounger - Side B", 1, 2, 2, "Tool Keeper",
     "When another Rat borrows one of Rummage's dice and it is not banished, return it available instead of exhausted."),
    ("Fidget", "Tinkerer - Side A", 1, 2, 2, "Jury-Rig",
     "Once per Experiment, after Fidget rolls, reroll one miss. This does not use a Strategy phase."),
    ("Fidget", "Tinkerer - Side B", 1, 2, 2, "Fine Tuning",
     "Once per Experiment, reroll one of Fidget's basic hits. If the reroll misses, retain the original basic hit."),
    ("Whiz", "Prodigy - Side A", 2, 2, 1, "Self-Sufficient",
     "If Whiz commits no borrowed die and does not use the Red die this Experiment, reduce the Experiment's Target by 1."),
    ("Whiz", "Prodigy - Side B", 2, 2, 1, "Prepared",
     "If a different Rat was active on the previous turn, recover 1 of Whiz's exhausted dice after selecting Whiz and before committing dice."),
    ("Mottle", "Mutant - Side A", 2, 2, 1, "Experimental Subject",
     "If at least one Specimen is revealed, Mottle has +1 STR for that Experiment and recovers 1 additional die this turn."),
    ("Mottle", "Mutant - Side B", 2, 2, 1, "Specimen Adaptation",
     "After Mottle completes an Experiment, recover 1 additional die for each Specimen Mottle holds."),
]


CAT = {'Power': '#8a3d2e', 'Mobility': '#2c6e63', 'Defense': '#3c5a8a', 'Senses': '#6b4a8a'}
ATTACK_ACC = '#4a1f1f'
SPEC_GOLD = '#b08a2e'


def C(title, sub, body, ftr='', warn=False, acc=None, tint=None, flavor='', dot=None):
    f = ('<div class="ftr%s">%s</div>' % (' warn' if warn else '', ftr)) if ftr else ''
    cls = ' xlong' if len(title) > 30 else (' long' if len(title) > 19 else '')
    st = ' style="--a:%s"' % acc if acc else ''
    bs = ' style="background:%s"' % tint if tint else ''
    flavor_html = ('<div style="font-size:8.6pt;font-style:italic;text-align:center;'
                   'line-height:1.25;margin:1mm 0">%s</div>' % flavor) if flavor else ''
    # An optional color dot sits in the top-right corner of the title band.
    fit, dot_html = hdr_fit(title, cls, CARD_SIZE), ''
    hs = ' style="%s"' % fit if fit else ''
    if dot:
        hs = ' style="position:relative;padding-right:10mm;%s"' % fit
        dot_html = ('<span style="position:absolute;top:2mm;right:2.4mm;width:5.6mm;height:5.6mm;'
                    'border-radius:50%%;background:%s;border:.8pt solid #fff"></span>' % dot)
    return ('<div class="card"%s><div class="hdr"%s>%s<div class="t%s">%s</div><div class="s">%s</div></div>'
            '<div class="body"%s>%s<div class="spacer"></div>%s%s</div></div>'
            % (st, hs, dot_html, cls, title, sub, bs, body, flavor_html, f))


# Card backs first: the deck PnPs interleave them behind the fronts.
make_back('CardBack_BAT_BuffHP', 'BAT', 'Buff HP', '#2c5f4a')
make_back('CardBack_BAT_Encounter', 'BAT', 'Experiment', '#2c5f4a')
make_back('CardBack_BAT_Upgrade', 'BAT', 'Upgrade &middot; Specimen', '#2c5f4a')
make_back('CardBack_BAT_TyrantAttack', 'BAT', 'Tyrant Attack', '#4a1f1f')
print("card backs done")

cards = []
for n, t, e, flavor in EXPERIMENTS:
    cards.append(C(n, "Build-a-Tyrant Experiment",
                   '<div class="big">%d</div><div class="biglbl">Target</div>'
                   '<div class="txt c">%s</div>' % (t, e), SPEC_FTR, flavor=flavor))
print("Experiments", render_deck('BAT_Encounters', cards, 'BAT', back='CardBack_BAT_Encounter'))

cards = [C(n, s, '<div class="big">%d</div><div class="biglbl">Value</div><div class="txt">%s</div>' % (v, e),
           TAP_FTR, acc=CAT[s.split(' - ')[1]], flavor=f) for n, s, v, e, f in UPGRADES]
print("Upgrades", render_deck('BAT_Upgrades', cards, 'BAT', back='CardBack_BAT_Upgrade'))

cards = [C(n, s,
           '<div style="background:%s;color:#fff;font-size:6.4pt;font-weight:bold;letter-spacing:.2em;'
           'text-transform:uppercase;text-align:center;padding:.9mm;margin:-2.4mm -2.4mm 0">Specimen</div>'
           '<div class="big" style="margin-top:2mm">5</div><div class="biglbl">Value</div>'
           '<div class="txt">%s</div>' % (SPEC_GOLD, e),
           'Specimen. At most 1 may be retained for the Imposter Research Pool.',
           acc=CAT[s.split(' ')[0]], tint='#faf5e8', flavor=f) for n, s, e, f in SPECIMENS]
print("Specimens", render_deck('BAT_Specimens', cards, 'BAT', back='CardBack_BAT_Upgrade'))

# Each Attack card carries a color dot in the corner of its title band. The
# most recently revealed card sets the color the attacking Rat must commit
# (one die of it, or a same-color pair if none is available). 3 Green, 3 Yellow, 1 Blue - weighted to the weak
# dice, so the requirement usually costs the Rats something.
ATTACK_DOTS = ['G', 'B', 'Y', 'G', 'Y', 'G', 'Y']

cards = [C(n, "Tyrant Attack",
           '<div class="sub">Reveal after Rat turn</div>'
           '<div class="txt">%s</div>' % e,
           'Discard after resolving. Reshuffle the discard when the deck is empty.',
           acc=ATTACK_ACC, tint='#f7f0ee', dot=DOT[ATTACK_DOTS[i]]) for i, (n, e) in enumerate(ATTACKS)]
print("Attacks", render_deck('BAT_TyrantAttacks', cards, 'BAT', back='CardBack_BAT_TyrantAttack'))

def ratcard(n, s, hp, st, rec, an, at):
    return C(n, s,
             '<div class="txt c" style="font-size:9.4pt;font-weight:bold;margin-top:.6mm">'
             'HP %d &nbsp;|&nbsp; STR %d &nbsp;|&nbsp; REC %d</div>'
             '<div class="sub" style="margin-top:3mm">%s</div>'
             '<div class="txt" style="margin-top:.4mm">%s</div>' % (hp, st, rec, an, at),
             'Choose one side of each Lab Rat at setup.')


CARD_SIZE = LANDSCAPE
sides_a = [ratcard(*r) for r in RATS[0::2]]
sides_b = [ratcard(*r) for r in RATS[1::2]]
print("Rats", render_duplex('BAT_Rats', sides_a, sides_b, 'BAT', LANDSCAPE), 'two-sided')
CARD_SIZE = PORTRAIT


# ---- Buff HP dial: 1-4 on one face, 5-8 on the other -----------------------
# ---- Buff HP: a 15-space track. Put the Health die on the difficulty's number
#      and step it down one space per point of damage.
BUFF_GREEN = '#2c5f4a'
# A die is placed on the track, so the spaces are square and as large as the
# card allows: 5 rows of 3 at 11mm leaves just enough room once the heading
# text is trimmed. The number sits in a corner so a die resting on the space
# does not hide it.
TRACK_CSS = ('.trk{display:flex;flex-direction:column;gap:.6mm;margin-top:1mm}'
             '.trow{display:flex;justify-content:center;gap:.6mm}'
             '.sp{width:11mm;height:11mm;border:.9pt solid #b8b0a0;border-radius:1.4mm;'
             'background:#f2eee2;display:flex;align-items:flex-start;'
             'justify-content:flex-start;padding:.6mm 0 0 1mm;box-sizing:border-box;'
             'font-size:8.5pt;font-weight:bold;color:#2c5f4a;line-height:1}'
             '.sp.mark{border-width:1.8pt;border-color:#8a6d1f;background:#f7efd8}'
             '.bufftip{font-size:6.2pt;line-height:1.25;text-align:center;'
             'color:#6f675a;margin:0 0 1.4mm}')


def track():
    # No gold spaces any more: difficulty is Tyrant Health, read off the dial.
    # The card is optional, for players who would rather push a die along a
    # track than read a dial, and any space is a legal start.
    marks = set()
    cells = ['<div class="sp%s">%d</div>' % (' mark' if v in marks else '', v)
             for v in range(15, 0, -1)]
    rows = ['<div class="trow">%s</div>' % ''.join(cells[i:i + 3])
            for i in range(0, len(cells), 3)]
    return '<div class="trk">%s</div>' % ''.join(rows)


buff = [C('Buff HP', 'Tyrant · remove before Health',
          '<div class="bufftip">Optional. Hold part of the Tyrant’s Health here: '
          'put the die on that many and spend it before the dial.</div>' + track(),
          'Removed before the Tyrant’s Health can be damaged.',
          acc=BUFF_GREEN)]
print("Buff HP track", render_deck('BAT_BuffHP', buff, 'BAT', PORTRAIT, TRACK_CSS, back='CardBack_BAT_BuffHP'))

