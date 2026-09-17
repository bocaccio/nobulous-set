import sys; sys.path.insert(0, '/home/claude/cards')
from gen import render_deck, render_duplex, make_back, elements, LANDSCAPE, PORTRAIT

SPEC_FTR = 'If at least one revealed Upgrade is a Specimen, +1 Target total.'
TAP_FTR = 'Tap to use. A tapped Upgrade cannot absorb damage.'

EXPERIMENTS = [
    ("Baseline Calibration", 2, "Flip the active Lab Rat to its other side. That side remains active until another effect flips it.", "Every breakthrough begins by proving the researcher probably still works."),
    ("Fine Motor Trial", 2, "A Yellow die must be committed to this Experiment. If unable to do so, increase the Target by 1.", "Tiny claws. Tiny screws. Absolutely no margin for error."),
    ("Structural Stress Trial", 3, "Reveal 1 additional Upgrade for this Experiment. Resolve the normal Upgrade choice using all revealed options.", "Nobulous calls the third prototype a control. Nobody asks what it controls."),
    ("Contaminated Tissue", 3, "Discard the revealed Upgrades and reveal 2 new Upgrades. These become the Upgrades for this Experiment.", "The sample was sterile until Nobulous explained his definition of sterile."),
    ("Performance Trial", 3, "Discard the top 2 cards of the Experiment deck face down without resolving them.", "The schedule has been accelerated by removing the parts involving caution."),
    ("Load-Bearing Trial", 3, "A Purple die must be committed to this Experiment. If unable to do so, discard this Experiment and draw another one, replacing any revealed Upgrades.", "Add weight until something fails. Preferably not the researcher."),
    ("Diagnostic Trial", 3, "If you commit a Blue die to this Experiment, you may look at the next Experiment and return it to the top of the deck.", "The instruments say everything is fine. The smoke has submitted a dissenting report."),
    ("Rapid Response Trial", 3, "A Green die must be committed to this Experiment. If unable to do so, discard the stronger revealed Upgrade and continue the Experiment.", "There is no time to do it right, only time to make it testable."),
    ("Full-Spectrum Trial", 3, "Committed dice must include 3 different colors.", "Nobulous requested versatility. The equipment requested mercy."),
    ("Workspace Efficiency Study", 3, "You may only commit two dice to this Experiment.", "Four researchers. One bench. Zero lessons learned."),
    ("Restricted Materials Trial", 3, "Place the Red die on the active Rat. Red cannot be used for this Experiment.", "The best reagent is unavailable for reasons marked administrative."),
    ("Independent Performance Trial", 3, "You cannot borrow a die during this Experiment.", "Collaboration introduces confounds. Nobulous has generously removed collaboration."),
    ("Resource Depletion Study", 3, "During your second Strategy phase, you may commit no additional dice.", "There was a second prototype. Past tense."),
    ("Reliability Trial", 3, "Hits and Crits on Purple and Blue dice in the first Strategy phase must be rerolled.", "It only fails when you need it, which is remarkably consistent."),
    ("Reagent Exclusion Trial", 3, "Randomly select one available die belonging to the active Rat. That die cannot be committed to this Experiment.", "Science advances rapidly once you stop checking the labels."),
    ("Containment Failure", 4, "You may choose to reduce the Target by 2. If you do, before committing, roll a Yellow die. On a hit or Crit, banish one available Blue die. Otherwise, banish that Yellow die.", "The blast shield performed exactly as specified. The blast did not."),
    ("Endurance Trial", 4, "STR is 1 for this Experiment.", "The experiment is repeatable. Unfortunately, so is the overtime."),
    ("Field Retrofit Trial", 4, "If successful, you may swap one of the active Rat's Upgrades with one of the revealed Upgrades. Specimens cannot be swapped.", "The replacement fits perfectly once you stop asking what it replaced."),
    ("Methodological Optimization", 4, "You may reduce the Target to 0. If you do, take the weaker revealed Upgrade and Splice the stronger revealed Upgrade into the Prototyrant. If tied, choose which to take.", "Why test both prototypes when the Prototyrant can test the better one?"),
    ("Degraded Tissue Study", 4, "If successful, reduce the Prototyrant's Health dial by 2.", "The tissue is weaker than projected. Nobulous has classified this as progress."),
]

UPGRADES = [
    ("Serrated Claws", "P1 - Power", 2, "+1 damage from each Blue or Green basic hit you apply during this attack."),
    ("Reinforced Jaw", "P2 - Power", 3, "Add +2 damage to this attack if at least one Purple hit is applied."),
    ("Capacitor Muscles", "P3 - Power", 3, "Commit one exhausted Purple or Blue die to the current attack. It remains exhausted afterward."),
    ("Piercing Horn", "P4 - Power", 4, "Add +2 damage. If you roll a Yellow hit or Crit, bypass one Defense Upgrade when assigning this attack."),
    ("Spring-Loaded Legs", "M1 - Mobility", 2, "Roll 1 exhausted Green die. It must match a color already committed to the attack; exhaust it afterward."),
    ("Prehensile Tail", "M2 - Mobility", 2, "Roll 1 exhausted Yellow die. It must match a color already committed to the attack; exhaust it afterward."),
    ("Tripwire Tendons", "M3 - Mobility", 3, "Opponent exhausts one Green die; if unable, one Yellow die, if able."),
    ("Evasive Reflexes", "M4 - Mobility", 3, "Remove 1 success from the opponent's next attack."),
    ("Thickened Hide", "D1 - Defense", 2, "Reduce incoming damage by 1."),
    ("Layered Carapace", "D2 - Defense", 3, "Reduce incoming damage by 2."),
    ("Chromatic Plating", "D3 - Defense", 3, "Reduce damage dealt by Blue and Green dice by 1 each. Yellow dice are unaffected."),
    ("Reactive Shell", "D4 - Defense", 4, "Reduce damage dealt by Purple and Yellow dice by 1 each."),
    ("Acute Hearing", "S1 - Senses", 2, "+1 STR during your next turn."),
    ("Predatory Focus", "S2 - Senses", 3, "+1 STR for the current attack."),
    ("Rapid Metabolism", "S3 - Senses", 2, "Recover 1 additional die this turn."),
    ("Neural Overclock", "S4 - Senses", 4, "Recover 2 additional dice this turn."),
]

SPECIMENS = [
    ("Titanium-Toothed Mole", "Power Specimen", "Add +3 damage to the current attack."),
    ("Voltaic Mantis", "Power Specimen", "Add +2 damage; one applied Crit deals +2 additional damage."),
    ("Blink Hare", "Mobility Specimen", "Roll up to 2 exhausted dice matching colors already committed to this attack."),
    ("Ghost Gecko", "Mobility Specimen", "Remove 2 successes from the opponent's next attack."),
    ("Ironback Beetle", "Defense Specimen", "Reduce incoming damage by 3."),
    ("Prismatic Tortoise", "Defense Specimen", "Reduce damage from two colors of your choice by 1 per die for this attack."),
    ("Echo Bat", "Senses Specimen", "+1 STR for this turn and recover 1 additional die afterward."),
    ("Regenerator Newt", "Senses Specimen", "Recover 3 additional dice this turn."),
]

ATTACKS = [
    ("Overwhelming Mass", "This attack deals +3 damage."),
    ("Adaptive Strike", "Ignore the first Upgrade that would absorb this attack. It neither absorbs damage nor is damaged. Remaining damage continues to the next eligible Upgrade, then to Health."),
    ("Predatory Instinct", "This attack is made against the Rat holding the greatest total Upgrade Value instead of the active Rat. If tied, the player chooses. If only one Rat remains, it is the target."),
    ("Spliced Reflexes", "This attack deals +1 damage for each Splice the Tyrant still holds."),
    ("Terrifying Roar", "The Tyrant deals no damage this attack. Instead, exhaust 2 dice from the shared battle pool. The player chooses which dice."),
    ("Crushing Blow", "1 damage from this attack is dealt directly to the target Rat's Health and cannot be absorbed by Upgrades. Any remaining damage is absorbed normally."),
    ("Unstable Growth", "Resolve this attack. If the target was not knocked out, the Tyrant immediately attacks again, committing 2 dice. Do not reveal a Tyrant Attack card for the second attack."),
]

RATS = [
    ("Rummage", "Scrounger - Side A", 1, 2, 2, "Careful Borrower",
     "When checking whether a die you borrowed is banished, you may reroll the check once."),
    ("Rummage", "Scrounger - Side B", 1, 2, 2, "Tool Keeper",
     "When another Rat borrows one of your dice and it is not banished, return it available instead of exhausted."),
    ("Fidget", "Tinkerer - Side A", 1, 2, 2, "Jury-Rig",
     "Once per Encounter, after rolling, reroll one miss. This does not use a Strategy phase."),
    ("Fidget", "Tinkerer - Side B", 1, 2, 2, "Fine Tuning",
     "Once per Encounter, reroll one basic hit. If the reroll misses, retain the original basic hit."),
    ("Whiz", "Prodigy - Side A", 2, 2, 1, "Self-Sufficient",
     "If this Rat commits no borrowed die and does not use the Red die this Encounter, reduce the Encounter's Target by 1."),
    ("Whiz", "Prodigy - Side B", 2, 2, 1, "Prepared",
     "If a different Rat was active on the previous turn, recover 1 of this Rat's exhausted dice after selecting this Rat and before committing dice."),
    ("Mottle", "Mutant - Side A", 2, 2, 1, "Experimental Subject",
     "If at least one Specimen is revealed, this Rat has +1 STR for that Encounter and recovers 1 additional die this turn."),
    ("Mottle", "Mutant - Side B", 2, 2, 1, "Specimen Adaptation",
     "After this Rat completes an Encounter, recover 1 additional die for each Specimen this Rat holds."),
]


CAT = {'Power': '#8a3d2e', 'Mobility': '#2c6e63', 'Defense': '#3c5a8a', 'Senses': '#6b4a8a'}
ATTACK_ACC = '#4a1f1f'
SPEC_GOLD = '#b08a2e'


def C(title, sub, body, ftr='', warn=False, acc=None, tint=None, flavor=''):
    f = ('<div class="ftr%s">%s</div>' % (' warn' if warn else '', ftr)) if ftr else ''
    cls = ' xlong' if len(title) > 30 else (' long' if len(title) > 19 else '')
    st = ' style="--a:%s"' % acc if acc else ''
    bs = ' style="background:%s"' % tint if tint else ''
    flavor_html = ('<div style="font-size:8.6pt;font-style:italic;text-align:center;'
                   'line-height:1.25;margin:1mm 0">%s</div>' % flavor) if flavor else ''
    return ('<div class="card"%s><div class="hdr"><div class="t%s">%s</div><div class="s">%s</div></div>'
            '<div class="body"%s>%s<div class="spacer"></div>%s%s</div></div>'
            % (st, cls, title, sub, bs, body, flavor_html, f))


cards = []
for n, t, e, flavor in EXPERIMENTS:
    cards.append(C(n, "Build-a-Tyrant Experiment",
                   '<div class="big">%d</div><div class="biglbl">Target</div>'
                   '<div class="txt c">%s</div>' % (t, e), SPEC_FTR, flavor=flavor))
print("Experiments", render_deck('BAT_Encounters', cards, 'BAT'))

cards = [C(n, s, '<div class="big">%d</div><div class="biglbl">Value</div><div class="txt">%s</div>' % (v, e),
           TAP_FTR, acc=CAT[s.split(' - ')[1]]) for n, s, v, e in UPGRADES]
print("Upgrades", render_deck('BAT_Upgrades', cards, 'BAT'))

cards = [C(n, s,
           '<div style="background:%s;color:#fff;font-size:6.4pt;font-weight:bold;letter-spacing:.2em;'
           'text-transform:uppercase;text-align:center;padding:.9mm;margin:-2.4mm -2.4mm 0">Specimen</div>'
           '<div class="big" style="margin-top:2mm">5</div><div class="biglbl">Value</div>'
           '<div class="txt">%s</div>' % (SPEC_GOLD, e),
           'Specimen. At most 1 may be retained for the Imposter Research Pool.',
           acc=CAT[s.split(' ')[0]], tint='#faf5e8') for n, s, e in SPECIMENS]
print("Specimens", render_deck('BAT_Specimens', cards, 'BAT'))

cards = [C(n, "Tyrant Attack", '<div class="sub">Reveal after Rat turn</div><div class="txt">%s</div>' % e,
           'Discard after resolving. Reshuffle the discard when the deck is empty.',
           acc=ATTACK_ACC, tint='#f7f0ee') for n, e in ATTACKS]
print("Attacks", render_deck('BAT_TyrantAttacks', cards, 'BAT'))

def ratcard(n, s, hp, st, rec, an, at):
    return C(n, s,
             '<div class="txt c" style="font-size:9.4pt;font-weight:bold;margin-top:.6mm">'
             'HP %d &nbsp;|&nbsp; STR %d &nbsp;|&nbsp; REC %d</div>'
             '<div class="sub" style="margin-top:3mm">%s</div>'
             '<div class="txt" style="margin-top:.4mm">%s</div>' % (hp, st, rec, an, at),
             'Choose one side of each Lab Rat at setup.')


sides_a = [ratcard(*r) for r in RATS[0::2]]
sides_b = [ratcard(*r) for r in RATS[1::2]]
print("Rats", render_duplex('BAT_Rats', sides_a, sides_b, 'BAT', LANDSCAPE), 'two-sided')


# ---- Buff HP dial: 1-4 on one face, 5-8 on the other -----------------------
# ---- Buff HP: a 12-space track. Put the Health die on the difficulty's number
#      and step it down one space per point of damage.
TRACK_CSS = ('.trk{position:absolute;left:3.2mm;right:3.2mm;top:22mm;bottom:4mm;'
             'display:flex;flex-direction:column;justify-content:space-between}'
             '.trow{display:flex;justify-content:space-between}'
             '.trow.last{justify-content:center}'
             '.sp{width:15mm;height:11mm;border:.9pt solid #b8b0a0;border-radius:1.4mm;'
             'background:#f2eee2;display:flex;align-items:center;justify-content:center;'
             'font-size:15pt;font-weight:bold;color:#2c5f4a;line-height:1}'
             '.sp.zero{background:#2c5f4a;color:#fbf9f3;border-color:#2c5f4a;font-size:9pt;'
             'letter-spacing:.06em}'
             '.sp.mark{border-width:1.8pt;border-color:#8a6d1f;background:#f7efd8}')


def track():
    rows = []
    order = [12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0]
    marks = {8, 7, 6, 5, 4}                   # the five difficulty starts
    cells = []
    for v in order:
        if v == 0:
            cells.append('<div class="sp zero">DEAD</div>')
        else:
            cells.append('<div class="sp%s">%d</div>'
                         % (' mark' if v in marks else '', v))
    for i in range(0, len(cells), 3):
        chunk = cells[i:i + 3]
        cls = 'trow last' if len(chunk) < 3 else 'trow'
        rows.append('<div class="%s">%s</div>' % (cls, ''.join(chunk)))
    return '<div class="trk">%s</div>' % ''.join(rows)


HEAD = ('<div class="hdr"><div class="t">Buff HP</div>'
        '<div class="s">Tyrant &middot; remove before Health</div></div>'
        '<div style="position:absolute;top:14.5mm;left:3.2mm;right:3.2mm;font-size:5.3pt;'
        'line-height:1.25;color:#6b6459;text-align:center">Place the Health die on your '
        'difficulty&rsquo;s number, then move it one space per damage.</div>')

buff = ['<div class="card">' + HEAD + track() + '</div>']
print("Buff HP track", render_deck('BAT_BuffHP', buff, 'BAT', PORTRAIT, TRACK_CSS))
make_back('CardBack_BAT_BuffHP', 'BAT', 'Buff HP', '#2c5f4a')

make_back('CardBack_BAT_Encounter', 'BAT', 'Encounter', '#2c5f4a')
make_back('CardBack_BAT_Upgrade', 'BAT', 'Upgrade &middot; Specimen', '#2c5f4a')
make_back('CardBack_BAT_TyrantAttack', 'BAT', 'Tyrant Attack', '#4a1f1f')
print("backs done")
