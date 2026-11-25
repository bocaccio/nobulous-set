from gen import render_deck, render_duplex, make_back, elements, hdr_fit, title_cls, LANDSCAPE, PORTRAIT

# The shape of the cards being built, for header measurement.
CARD_SIZE = PORTRAIT
from aos import (ROUTINE, SPECIALIZED, UNSTABLE, VOLATILE, ASSEMBLIES,
                 ASSEMBLY_FLAVOR, COVERT, REQ_MAP, FLAVOR, LIMITATIONS)
from aos_faces import ASSEMBLY_CSS, assembly_back, assembly_front

REWARD = {'hp1': 'Gain 1 HP',
          'rec3': 'Recover 3 exhausted dice',
          'rec_up_remove': '+1 REC; remove this Program',
          'unheat': 'Return 1 Overheated Program to Stable',
          'str_up_remove': '+1 STR; remove this Program',
          'opt_placeholder': 'Banish 1 Limitation from the game.'}

# "or exhaust 2 misses on them" is scoped to the HEALTH LOSS alone. In aos.py
# the save sits inside `if failed >= 2:` and only skips `self.hp -= 1`, while
# the flip to Overheated is computed outside it - so a negated Catastrophic
# Failure still costs the Program its face. The half of this that used to
# matter MOST, a negated failure still overheating the next ADVANCED Program,
# is gone with the Advanced deck (2026-11-24); the scoping itself still
# decides what these two footers mean.
STABLE_FTR = ('1 failed element: this Program Overheats. '
              '2+ (Catastrophic Failure): lose 1 HP, or exhaust 2 misses on them.')
OVER_FTR = ('1 failed element: this Program is set aside. '
            '2+ (Catastrophic Failure): lose 1 HP, or exhaust 2 misses on them.')
# NO ADV_FTR ANY MORE. The eight standalone Advanced Programs are gone, and
# with them the Overheated-carryover rule they printed: the finale is now three
# Assembly BACKS resolved as one Program, scored on one failed element across
# the whole sequence, so there is no next-Program state left to carry. The
# Assembly back's own footer is aos_faces.BACK_FTR.


DECK_ACCENT = {'Routine': '#315c49', 'Specialized': '#4c4a75', 'Unstable': '#7a3838',
               'Volatile': '#6b2d5c',
               'Advanced': '#8a5a20', 'Limitation': '#2f5966', 'Technician': '#3f5260',
               'Mat': '#555555'}

# Body text, subheads, the footer and flavour used to be set here and are
# now in gen.py's base stylesheet, printed by every family. What is left is
# genuinely AoS-only: the top header rung (gen.HDR_STYLES['aos'] records it,
# and it is what makes HDR_H_MM what it is) and the element circles.
BIG = ('.hdr .t{font-size:11.6pt}.hdr .s{font-size:6.8pt}'
       '.el .n{width:8.6mm;height:8.6mm;line-height:8.4mm;font-size:12.5pt}'
       '.el .d{width:3.8mm;height:3.8mm}.el .sp{height:3.8mm}.bar{margin-top:4.2mm}')


def C(title, sub, body, ftr='', warn=False, acc=None, flavor=''):
    f = ('<div class="ftr%s">%s</div>' % (' warn' if warn else '', ftr)) if ftr else ''
    # Flavor text sits at the bottom of the card, just above the footer.
    fl = '<div class="flavor">%s</div>' % flavor if flavor else ''
    st = ' style="--a:%s"' % acc if acc else ''
    # BIG below sets this family's header sizes, so measure against those.
    cls = title_cls(title, CARD_SIZE, 'aos')
    fit = hdr_fit(title, cls, CARD_SIZE, 'aos')
    return ('<div class="card"%s><div class="hdr"%s><div class="t%s">%s</div><div class="s">%s</div></div>'
            '<div class="body">%s<div class="spacer"></div>%s%s</div></div>'
            % (st, ' style="%s"' % fit if fit else '', cls, title, sub, body, fl, f))


def program(name, targets, mark, reward, deck, overheated):
    t = list(targets)
    if overheated:
        t[mark] += 1
    dots = REQ_MAP.get(name, [None] * len(t))
    dots = (list(dots) + [None] * len(t))[:len(t)]
    body = elements(t, dots, mark)
    flavor = FLAVOR[name][1 if overheated else 0]
    if reward:
        body += ('<div class="spacer"></div><div class="sub">Program Reward</div>'
                 '<div class="txt" style="margin-top:.4mm">%s</div>' % reward)
    sub = '%s &middot; %s' % (deck, 'Overheated' if overheated else 'Stable')
    # Every caller passes a reward now: the Advanced deck was the only
    # rewardless one and the Assemblies replaced it.
    assert reward, '%s: a Program with no reward is no longer a card' % name
    ftr = OVER_FTR if overheated else STABLE_FTR
    return C(name, sub, body, ftr, warn=True, acc=DECK_ACCENT[deck], flavor=flavor)


for deckname, data in [('Routine', ROUTINE), ('Specialized', SPECIALIZED),
                       ('Unstable', UNSTABLE), ('Volatile', VOLATILE)]:
    stable = [program(n, t, m, REWARD[r], deckname, False) for n, t, m, r in data]
    over = [program(n, t, m, REWARD[r], deckname, True) for n, t, m, r in data]
    print(deckname, render_duplex('AoS_%s' % deckname, stable, over, 'AoS', PORTRAIT, BIG), 'two-sided')

# Card backs first: the deck PnPs interleave them behind the fronts.
make_back('CardBack_AoS_Limitation', 'AoS', 'Limitation', '#2f5966')
make_back('CardBack_AoS_ElementMat', 'AoS', 'Element mat', '#555555', PORTRAIT)
print("card backs done")

# THE EIGHT ASSEMBLIES, replacing the eight standalone Advanced Programs.
# Front is the recipe built during the game, back is the finale stage it
# becomes - two different jobs on one piece of card, which is why the faces
# share nothing but the accent colour. The ninth, the Covert Sensor Array, is
# printed in NRJ's print-and-play because it is offered only in a Tier III
# setup; build_nrj.py builds it from these same two functions.
ACC = DECK_ACCENT['Advanced']
fronts = [assembly_front(n, rec, els, ASSEMBLY_FLAVOR[n][0], C, ACC)
          for n, rec, _, els in ASSEMBLIES]
backs = [assembly_back(bn, els, ASSEMBLY_FLAVOR[n][1], C, ACC)
         for n, _, bn, els in ASSEMBLIES]
print('Assemblies', render_duplex('AoS_Assemblies', fronts, backs, 'AoS', PORTRAIT,
                                  BIG + ASSEMBLY_CSS), 'two-sided')

# THE NINTH ASSEMBLY SHIPS IN NRJ'S PRINT-AND-PLAY but is built here, in AoS's
# own stylesheet and header style, so all nine are one card format. That is not
# tidiness: the recipe side's Advanced colors line is what a player reads to
# plan a build, and a ninth card that presented it differently would be a
# different promise. It carries no NRJ tag for the same reason.
#
# The deck NAME is what files it: pack.py lists NRJ_* under NRJ, so this lands
# in the NRJ booklet and the NRJ box beside the Backdoor Routines, which are
# also AoS cards printed by the campaign.
_cn, _crec, _cbn, _cels = COVERT
print('Covert Sensor Array',
      render_duplex('NRJ_AoS_CovertAssembly',
                    [assembly_front(_cn, _crec, _cels, ASSEMBLY_FLAVOR[_cn][0], C, ACC)],
                    [assembly_back(_cbn, _cels, ASSEMBLY_FLAVOR[_cn][1], C, ACC)],
                    'AoS', PORTRAIT, BIG + ASSEMBLY_CSS), 'two-sided')

LIM_FTR = ('Reveal before committing required-color dice. '
           'Withheld dice cannot be used in this Program.')
cards = [C(n, "Limitation", '<div class="txt c" style="font-size:10.5pt;margin-top:9mm">%s</div>' % effect,
           LIM_FTR, acc=DECK_ACCENT['Limitation'], flavor=flavor) for n, effect, flavor in LIMITATIONS]
print('Limitations', render_deck('AoS_Limitations', cards, 'AoS', PORTRAIT, BIG, back='CardBack_AoS_Limitation'))

TECHS = [
    ("Architect", "Reconfigure", "Once per Program, before rolling an element, move up to 2 allocated dice between unresolved elements."),
    ("Debugger", "Debug", "Once per Program, before rolling an element, swap 1 of its dice for a die from your available pool."),
    ("Optimizer", "Optimize", "Once per round and once in the finale, Target +1 successes may count as Optimal Implementation."),
    ("Engineer", "Redundancy", "For up to 2 elements per Program, the allocation cap is Target +2 instead of Target +1."),
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


CARD_SIZE = LANDSCAPE
tech_a = [techcard(*t) for t in TECHS[0::2]]
tech_b = [techcard(*t) for t in TECHS[1::2]]
print('Technicians', render_duplex('AoS_Technicians', tech_a, tech_b, 'AoS', LANDSCAPE, BIG), 'two-sided')

cards = []
for i in range(1, 6):
    cards.append('<div class="card" style="--a:%s">'
                 # Hand-rolled header, so the set's depth has to be applied
                 # explicitly or the mats are the one odd card out. It goes
                 # in as a format argument, not by concatenation: `%` binds
                 # tighter than `+`, so a `+` here would apply the format to
                 # the last fragment alone.
                 '<div class="hdr" style="%s"><div class="t">Element %d</div>'
                 '<div class="s">Dice Allocation</div></div>'
                 '<div class="body" style="padding:3mm;background:#e8e4d8">'
                 '<div style="flex:1;border:1.2pt dashed #8d8676;border-radius:2mm;'
                 'background:#f7f4ea;box-shadow:inset 0 0 0 1.6mm #e8e4d8"></div>'
                 '<div style="font-size:7.4pt;line-height:1.26;text-align:center;margin-top:2.4mm;'
                 'color:#4a4239">Place all dice assigned to this element here before running '
                 'the Program.</div></div></div>'
                 % (DECK_ACCENT['Mat'], hdr_fit('Element 1', '', PORTRAIT, 'aos'), i))
print('Element mats', render_deck('AoS_ElementMats', cards, 'AoS', PORTRAIT, BIG, back='CardBack_AoS_ElementMat'))

