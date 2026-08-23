import sys; sys.path.insert(0, '/home/claude/cards'); sys.path.insert(0, '/home/claude/nap')
from gen import render_deck, render_duplex, make_back, elements, LANDSCAPE, PORTRAIT
from aos import ROUTINE, SPECIALIZED, UNSTABLE, ADVANCED, REQ_MAP

REWARD = {'hp1': 'Recover 1 HP',
          'rec3': 'Recover 3 exhausted dice',
          'rec_up_remove': '+1 REC; remove this Program',
          'unheat': 'Return 1 Overheated Program to Stable',
          'str_up_remove': '+1 STR; remove this Program',
          'opt_placeholder': 'Banish 1 Limitation from the game.'}

STABLE_FTR = 'Any failed element makes this Program Overheated.'
OVER_FTR = 'Any failed element sets this Program aside.'
ADV_FTR = ('2+ failed elements: lose 1 HP and the next Advanced Program is Overheated. '
           '0-1 failed elements: next Advanced Program is Stable. Recover between Advanced Programs.')


DECK_ACCENT = {'Routine': '#315c49', 'Specialized': '#4c4a75', 'Unstable': '#7a3838',
               'Advanced': '#8a5a20', 'Limitation': '#2f5966', 'Technician': '#3f5260',
               'Mat': '#555555'}

BIG = ('.txt{font-size:9.4pt;line-height:1.3}.sub{font-size:7.2pt}.ftr{font-size:6.8pt}'
       '.hdr .t{font-size:11.6pt}.hdr .s{font-size:6.8pt}'
       '.el .n{width:8.6mm;height:8.6mm;line-height:8.4mm;font-size:12.5pt}'
       '.el .d{width:3.8mm;height:3.8mm}.el .sp{height:3.8mm}.bar{margin-top:4.2mm}')


def C(title, sub, body, ftr='', warn=False, acc=None):
    f = ('<div class="ftr%s">%s</div>' % (' warn' if warn else '', ftr)) if ftr else ''
    st = ' style="--a:%s"' % acc if acc else ''
    return ('<div class="card"%s><div class="hdr"><div class="t%s">%s</div><div class="s">%s</div></div>'
            '<div class="body">%s<div class="spacer"></div>%s</div></div>'
            % (st, (' xlong' if len(title) > 30 else (' long' if len(title) > 19 else '')), title, sub, body, f))


def program(name, targets, mark, reward, deck, overheated):
    t = list(targets)
    if overheated:
        t[mark] += 1
    dots = REQ_MAP.get(name, [None] * len(t))
    dots = (list(dots) + [None] * len(t))[:len(t)]
    body = elements(t, dots, mark)
    if reward:
        body += ('<div class="spacer"></div><div class="sub">Program Reward</div>'
                 '<div class="txt" style="margin-top:.4mm">%s</div>' % reward)
    sub = '%s &middot; %s' % (deck, 'Overheated' if overheated else 'Stable')
    ftr = (OVER_FTR if overheated else STABLE_FTR) if reward else ADV_FTR
    return C(name, sub, body, ftr, warn=True, acc=DECK_ACCENT[deck])


for deckname, data in [('Routine', ROUTINE), ('Specialized', SPECIALIZED), ('Unstable', UNSTABLE)]:
    stable = [program(n, t, m, REWARD[r], deckname, False) for n, t, m, r in data]
    over = [program(n, t, m, REWARD[r], deckname, True) for n, t, m, r in data]
    print(deckname, render_duplex('AoS_%s' % deckname, stable, over, 'AoS', PORTRAIT, BIG), 'two-sided')

stable = [program(n, t, m, None, 'Advanced', False) for n, t, m in ADVANCED]
over = [program(n, t, m, None, 'Advanced', True) for n, t, m in ADVANCED]
print('Advanced', render_duplex('AoS_Advanced', stable, over, 'AoS', PORTRAIT, BIG), 'two-sided')

LIM_FTR = ('Reveal after required-color dice are committed. '
           'Withheld dice come from the remaining pool.')
LIMS = [("Yellow Shortage", "Withhold 2 Yellow dice."),
        ("Green Shortage", "Withhold 2 Green dice."),
        ("Blue Shortage", "Withhold 2 Blue dice."),
        ("Purple Shortage", "Withhold 2 Purple dice."),
        ("Diversity Protocol", "Withhold 2 dice of different non-Red colors."),
        ("Red Quarantine", "Withhold the Red die.")]
cards = [C(n, "Limitation", '<div class="txt c" style="font-size:10.5pt;margin-top:9mm">%s</div>' % e,
           LIM_FTR, acc=DECK_ACCENT['Limitation']) for n, e in LIMS]
print('Limitations', render_deck('AoS_Limitations', cards, 'AoS', PORTRAIT, BIG))

TECHS = [
    ("Architect", "Reconfigure", "Once per Program, before rolling an element, move up to 2 allocated dice between unresolved elements."),
    ("Debugger", "Debug", "Once per Program, after failing by exactly 1 success, reroll 1 allocated die. If it still fails, exhaust that die."),
    ("Optimizer", "Optimize", "Once per Program, Target +1 successes may count as Optimal Implementation."),
    ("Engineer", "Redundancy", "For up to 2 elements per Program, the safe allocation threshold is Target +2 instead of Target +1."),
    ("Operator", "Workaround", "When a non-Red Limitation would withhold 2 dice, you may withhold 1 of those dice as another non-Red color instead."),
    ("Compiler", "Compile", "When spending an additional STR roll, reroll any number of dice on that element while keeping the others."),
]
def techcard(n, a_, t):
    return C(n, "Experimental Technician",
             '<div class="txt c" style="font-size:9.4pt;font-weight:bold;margin-top:.6mm">'
             'HP 2 &nbsp;|&nbsp; STR 2 &nbsp;|&nbsp; REC 3</div>'
             '<div class="sub" style="margin-top:3mm">%s</div>'
             '<div class="txt" style="margin-top:.4mm">%s</div>' % (a_, t),
             'Choose one Technician card and one side at setup.', acc=DECK_ACCENT['Technician'])


tech_a = [techcard(*t) for t in TECHS[0::2]]
tech_b = [techcard(*t) for t in TECHS[1::2]]
print('Technicians', render_duplex('AoS_Technicians', tech_a, tech_b, 'AoS', LANDSCAPE, BIG), 'two-sided')

cards = []
for i in range(1, 6):
    cards.append('<div class="card" style="--a:%s">'
                 '<div class="hdr"><div class="t">Element %d</div>'
                 '<div class="s">Dice Allocation</div></div>'
                 '<div class="body" style="padding:3mm">'
                 '<div style="flex:1;border:1pt dashed #9c9484;border-radius:2mm;'
                 'background:#f2eee2"></div>'
                 '<div style="font-size:7.4pt;line-height:1.26;text-align:center;margin-top:2.4mm;'
                 'color:#4a4239">Place all dice assigned to this element here before running '
                 'the Program.</div></div></div>' % (DECK_ACCENT['Mat'], i))
print('Element mats', render_deck('AoS_ElementMats', cards, 'AoS', PORTRAIT, BIG))

make_back('CardBack_AoS_Limitation', 'AoS', 'Limitation', '#2f5966')
print('back done')
