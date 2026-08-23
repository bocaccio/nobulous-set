import sys; sys.path.insert(0, '/home/claude/cards')
from gen import render_deck, render_duplex, make_back, elements, LANDSCAPE

SPEC_FTR = 'If at least one revealed Upgrade is a Specimen, +1 Target total.'
TAP_FTR = 'Tap to use. A tapped Upgrade cannot absorb damage.'

ENCOUNTERS = [
    ("Basic Calibration", 2, "No additional effect."),
    ("Fine Manipulation", 2, "At least one applied hit must be Yellow."),
    ("Structural Integrity", 3, "No additional effect."),
    ("Precision Assembly", 3, "No additional effect."),
    ("Performance Trial", 3, "No additional effect."),
    ("Load Bearing", 3, "At least one applied hit must be Purple."),
    ("Diagnostics", 3, "At least one applied hit must be Blue."),
    ("Rapid Response", 3, "At least one applied hit must be Green."),
    ("Full Spectrum Test", 3, "Applied hits must include at least 3 different colors."),
    ("Limited Workspace", 3, "Commit no more than 2 dice initially."),
    ("Resource Constraint", 3, "Red cannot be used."),
    ("Independent Work", 3, "You cannot borrow a die."),
    ("Prototype Shortage", 3, "During your second Strategy phase, you may commit no additional dice."),
    ("Unreliable Equipment", 3, "One committed die of your choice cannot be rerolled during this Encounter."),
    ("Color Blind", 3, "Before committing, choose one color. Dice of that color cannot be used this Encounter."),
    ("Stress Test", 4, "No additional effect."),
    ("Exhaustive Testing", 4, "Recover 1 fewer die this turn, minimum 0."),
    ("Nobulous' Deadline", 4, "No additional effect."),
    ("Risky Shortcut", 4, "Before committing, you may reduce Target by 1. If you do and borrow a die, "
                          "that borrowed die is automatically banished."),
    ("What Could Go Wrong?", 5, "No additional effect."),
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


def C(title, sub, body, ftr='', warn=False, acc=None, tint=None):
    f = ('<div class="ftr%s">%s</div>' % (' warn' if warn else '', ftr)) if ftr else ''
    cls = ' xlong' if len(title) > 30 else (' long' if len(title) > 19 else '')
    st = ' style="--a:%s"' % acc if acc else ''
    bs = ' style="background:%s"' % tint if tint else ''
    return ('<div class="card"%s><div class="hdr"><div class="t%s">%s</div><div class="s">%s</div></div>'
            '<div class="body"%s>%s<div class="spacer"></div>%s</div></div>'
            % (st, cls, title, sub, bs, body, f))


cards = []
for n, t, e in ENCOUNTERS:
    cards.append(C(n, "Build-a-Tyrant Encounter",
                   '<div class="big">%d</div><div class="biglbl">Target</div>'
                   '<div class="txt c">%s</div>' % (t, e), SPEC_FTR))
print("Encounters", render_deck('BAT_Encounters', cards, 'BAT'))

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


make_back('CardBack_BAT_Encounter', 'BAT', 'Encounter', '#2c5f4a')
make_back('CardBack_BAT_Upgrade', 'BAT', 'Upgrade &middot; Specimen', '#2c5f4a')
make_back('CardBack_BAT_TyrantAttack', 'BAT', 'Tyrant Attack', '#4a1f1f')
print("backs done")
