"""Write playtest/dist/catalog.json: every card, its deck, and its sprite position.

    python3 build_catalog.py

The card names come from the build scripts themselves, so the catalog cannot
drift from the printed cards. The build scripts render on import, so `gen` is
stubbed out first: nothing is drawn, only the data lists are read.

Grid size is read from the manifest the renderer wrote, never assumed: at
300 DPI a portrait cell is 750x1050 and a landscape one 1050x750, gen.py
narrows the grid for a deck too wide for Tabletop Simulator, and fit_tts may
still shrink a sheet to something else again.

Each deck also publishes `cell` and `gutter` - the cell's real pixel size and
gen.py's CARD_INSET_MM expressed at that size. The lab needs both to place a
sprite and had been hard-coding them, which is how it ended up cropping a
300 DPI card by a 200 DPI margin.
"""
import io
import json
import os
import sys
import types

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out')
DEST = os.path.join(HERE, os.pardir, 'playtest', 'dist', 'catalog.json')

# ---- stub gen so importing a build script renders nothing -------------------
stub = types.ModuleType('gen')
stub.render_deck = lambda *a, **k: 0
stub.render_duplex = lambda *a, **k: 0
stub.make_back = lambda *a, **k: None
stub.elements = lambda *a, **k: ''
stub.skulls = lambda *a, **k: ''
stub.subj_icon = lambda *a, **k: ''
stub.hdr_fit = lambda *a, **k: ''
stub.title_cls = lambda *a, **k: ''
# gen.py is the authority on card geometry and is not imported here (it
# renders on import), so its constants are read out of the source. A second
# hand-kept copy is exactly the drift this file exists to prevent.
def gen_consts():
    import ast
    with io.open(os.path.join(HERE, 'gen.py'), encoding='utf-8') as fh:
        tree = ast.parse(fh.read())
    want = ('PORTRAIT', 'LANDSCAPE', 'DPI', 'CARD_INSET_MM')
    out = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name)                 and node.targets[0].id in want:
            out[node.targets[0].id] = ast.literal_eval(node.value)
    missing = [k for k in want if k not in out]
    if missing:
        raise SystemExit('gen.py no longer defines %s' % ', '.join(missing))
    return out


GEN = gen_consts()
stub.LANDSCAPE = GEN['LANDSCAPE']
stub.PORTRAIT = GEN['PORTRAIT']


class _Dots(dict):
    def __missing__(self, key):
        return '#888888'


stub.DOT = _Dots()
stub.DOT_NAP = _Dots()
sys.modules['gen'] = stub
sys.path.insert(0, HERE)

import build_bat, build_nap, build_aos, build_nrj  # noqa: E402
import aos as aos_data  # noqa: E402


def names(rows):
    """First element of each row is the printed card name."""
    return [r[0] if isinstance(r, (list, tuple)) else r for r in rows]


def grid(sheet, n):
    """(cols, rows, landscape, cell_w, cell_h) for a sprite sheet of n cards.

    The layout is READ FROM THE MANIFEST render_deck wrote beside the sheet,
    not inferred by dividing the sheet by a card size and not recomputed
    from a rule kept in step by hand. Both of those have failed here.
    Inferring was hard-coded to 500x700, which is 200 DPI; gen.py went to
    300 DPI on 2026-10-30 and nothing re-ran this script, so all 29 decks
    came out with the wrong cols, rows and orientation (Lab Rats 4x1
    landscape read as 8x1 portrait). And no fixed pixel size can work while
    fit_tts may shrink a sheet to a smaller cell. A copy of gen.py's own
    rule then went stale the moment that rule changed. The renderer's
    record is the only thing that cannot drift.

    The CELL is still divided out of the real sheet, because that is what
    the lab has to crop, shrunk or not.
    """
    from PIL import Image
    stem = sheet.replace('_TTS_back.png', '').replace('_TTS.png', '')
    mf = os.path.join(OUT, '%s_cards.json' % stem)
    if not os.path.exists(mf):
        raise SystemExit('build_catalog: no manifest for %s - run the build '
                         'scripts first' % sheet)
    with io.open(mf, encoding='utf-8') as fh:
        m = json.load(fh)
    if m['count'] != n:
        raise SystemExit('build_catalog: %s has %d cards, the manifest says %d'
                         % (sheet, n, m['count']))
    cols, rows = m['cols'], m['rows']
    with Image.open(os.path.join(OUT, sheet)) as im:
        w, h = im.size
    cw, ch = w // cols, h // rows
    return cols, rows, cw > ch, cw, ch


def deck(title, sheet, card_names, kind, back=None, back_kind=None,
         back_names=None, hdr=''):
    per_card = isinstance(back, (list, tuple))
    cols, rows, landscape, cw, ch = grid(sheet, len(card_names))
    # The inset is a physical 2mm, so at this cell's own scale it is that
    # fraction of the card's width - which survives fit_tts shrinking a sheet.
    mm_w = (GEN['LANDSCAPE'] if landscape else GEN['PORTRAIT'])[0]
    entry = {
        'title': title, 'sheet': sheet, 'cols': cols, 'rows': rows, 'landscape': landscape,
        'cell': [cw, ch], 'gutter': int(round(cw * GEN['CARD_INSET_MM'] / mm_w)),
        # Which gen.HDR_STYLES entry this deck's build script prints with.
        # check_app_sync.py needs it to measure a title the way the card
        # really sets it; the lab ignores it.
        'hdr': hdr,
        'cards': [{'name': n, 'kind': kind(n, i) if callable(kind) else kind}
                  for i, n in enumerate(card_names)],
    }
    if per_card:
        entry['back'] = back[0]
        entry['backs'] = list(back)
        entry['backIsSheet'] = False
        entry['backLabel'] = back_kind or 'Card back'
        return entry
    if back:
        entry['back'] = back
        entry['backIsSheet'] = back.endswith('_TTS_back.png')
        if entry['backIsSheet']:
            entry['backLabel'] = back_kind or 'Reverse side'
            if back_names:
                for card, bn in zip(entry['cards'], back_names):
                    card['backName'] = bn
        else:
            entry['backLabel'] = back_kind or 'Card back'
    return entry


CATALOG = {'bat': {'title': 'Build-a-Tyrant', 'decks': []},
           'nap': {'title': "Nobulous Apprenticeship Program", 'decks': []},
           'aos': {'title': 'Automaton of Shale', 'decks': []},
           'nrj': {'title': 'Nobulous Research Journal', 'decks': []}}

# ---- BAT -------------------------------------------------------------------
CATALOG['bat']['decks'] += [
    deck('Experiments', 'BAT_Encounters_TTS.png', names(build_bat.EXPERIMENTS),
         'Experiment card', 'CardBack_BAT_Encounter.png'),
    deck('Upgrades', 'BAT_Upgrades_TTS.png', names(build_bat.UPGRADES),
         lambda n, i: 'Upgrade card · %s' % build_bat.UPGRADES[i][1].split(' - ')[1],
         'CardBack_BAT_Upgrade.png'),
    deck('Specimens', 'BAT_Specimens_TTS.png', names(build_bat.SPECIMENS),
         lambda n, i: 'Specimen card · %s' % build_bat.SPECIMENS[i][1].split(' ')[0],
         'CardBack_BAT_Upgrade.png'),
    # The only deck with a colour dot in the header, which narrows the title.
    deck('Tyrant Attacks', 'BAT_TyrantAttacks_TTS.png', names(build_bat.ATTACKS),
         'Tyrant Attack card', 'CardBack_BAT_TyrantAttack.png', hdr='dot'),
    # Two-sided decks print the odd-indexed entries on the back sheet.
    deck('Lab Rats', 'BAT_Rats_TTS.png', names(build_bat.RATS[0::2]), 'Lab Rat card · side A',
         'BAT_Rats_TTS_back.png', 'Lab Rat card · side B', names(build_bat.RATS[1::2])),
    deck('Buff HP track', 'BAT_BuffHP_TTS.png', ['Buff HP track'], 'Tyrant track card',
         'CardBack_BAT_BuffHP.png'),
]

# ---- NAP -------------------------------------------------------------------
SUBJ = {'Anatomy': 'Anatomy', 'Engineering': 'Engineering', 'Procedure': 'Procedure',
        'Theory': 'Theory', None: 'Unmarked'}
CATALOG['nap']['decks'] += [
    deck('Assignments', 'NAP_Tasks_TTS.png', names(build_nap.TASKS),
         lambda n, i: 'Assignment card · %s' % SUBJ[build_nap.TASKS[i][1]],
         'CardBack_NAP_Assignment.png'),
    deck('Opportunities', 'NAP_Opportunities_TTS.png', names(build_nap.OPPS),
         'Opportunity card', 'CardBack_NAP_Assignment.png'),
    deck('Setbacks', 'NAP_Setbacks_TTS.png', names(build_nap.SETBACKS),
         'Setback card', 'CardBack_NAP_Assignment.png'),
    deck('Final Exams', 'NAP_FinalExams_TTS.png', names(build_nap.EXAMS),
         lambda n, i: 'Final Exam card · %s' % build_nap.EXAMS[i][1],
         'CardBack_NAP_FinalExam.png'),
    deck('Apprentices', 'NAP_Apprentices_TTS.png', names(build_nap.APPS[0::2]),
         'Apprentice card · front', 'NAP_Apprentices_TTS_back.png',
         'Apprentice card · back', names(build_nap.APPS[1::2])),
    deck('Time Slots and FINF', 'NAP_SlotsFINF_TTS.png',
         names(build_nap.SLOTS) + ["Following in Nobulous' Footsteps"] * len(build_nap.FINF_SLOTS),
         lambda n, i: ('FINF card \u00b7 %d %s' % build_nap.FINF_SLOTS[i - len(build_nap.SLOTS)][:2]
                       if i >= len(build_nap.SLOTS) else 'Time Slot card'),
         back=['CardBack_NAP_TimeSlot.png'] * len(build_nap.SLOTS)
              + ['CardBack_NAP_Assignment.png'] * len(build_nap.FINF_SLOTS)),
]

# ---- AoS -------------------------------------------------------------------
for label, data in [('Routine Programs', aos_data.ROUTINE),
                    ('Specialized Programs', aos_data.SPECIALIZED),
                    ('Unstable Programs', aos_data.UNSTABLE)]:
    sheet = 'AoS_%s_TTS.png' % label.split()[0]
    CATALOG['aos']['decks'].append(
        deck(label, sheet, names(data), '%s · Stable side' % label[:-1],
             sheet.replace('_TTS.png', '_TTS_back.png'), '%s · Overheated side' % label[:-1]))
CATALOG['aos']['decks'] += [
    deck('Advanced Programs', 'AoS_Advanced_TTS.png', names(aos_data.ADVANCED),
         'Advanced Program · Stable side', 'AoS_Advanced_TTS_back.png',
         'Advanced Program · Overheated side'),
    deck('Limitations', 'AoS_Limitations_TTS.png', names(aos_data.LIMITATIONS),
         'Limitation card', 'CardBack_AoS_Limitation.png'),
    deck('Technicians', 'AoS_Technicians_TTS.png', names(build_aos.TECHS[0::2]),
         'Technician card · front', 'AoS_Technicians_TTS_back.png',
         'Technician card · back', names(build_aos.TECHS[1::2])),
    # The mats carry no data list to count, and they render at BIG rather
    # than a card size, so the count comes from the loop in build_aos.py.
    deck('Element mats', 'AoS_ElementMats_TTS.png',
         ['Element mat %d' % i for i in range(1, 6)],
         'Element allocation mat', 'CardBack_AoS_ElementMat.png'),
]
# Every AoS deck renders through build_aos.BIG, which sets its own header
# sizes - one statement for the family rather than a keyword on seven calls.
for _d in CATALOG['aos']['decks']:
    _d['hdr'] = 'aos'

# ---- NRJ -------------------------------------------------------------------
CATALOG['nrj']['decks'] += [
    deck('BAT Protocols', 'NRJ_BAT_Protocols_TTS.png', names(build_nrj.PROTOCOLS),
         'NRJ Protocol · BAT', 'CardBack_NRJ_Protocol.png'),
    deck('BAT Modifications', 'NRJ_BAT_Modifications_TTS.png', names(build_nrj.MODS),
         'NRJ Modification · BAT', 'CardBack_NRJ_Protocol.png'),
    deck('BAT Research Notes', 'NRJ_BAT_ResearchNotes_TTS.png', names(build_nrj.NOTES),
         'Research Note · BAT', 'CardBack_NRJ_ResearchNote.png'),
    deck('NAP Imposter Tasks', 'NRJ_NAP_ImposterTasks_TTS.png', names(build_nrj.IMPOSTER_TASKS),
         'Imposter Task · NAP', 'CardBack_NAP_Assignment.png'),
    deck('NAP Following Setbacks', 'NRJ_NAP_FollowingSetbacks_TTS.png', names(build_nrj.FOLLOWING),
         'Following Setback · NAP', 'CardBack_NAP_Assignment.png'),
    deck('NAP Devious Opportunities', 'NRJ_NAP_DeviousOpportunities_TTS.png', names(build_nrj.DEVIOUS),
         'Devious Opportunity · NAP', 'CardBack_NAP_Assignment.png'),
    deck('AoS Interference', 'NRJ_AoS_Interference_TTS.png', names(build_nrj.INTF),
         'Nobulous Interference · AoS', 'CardBack_NRJ_Interference.png'),
    deck('AoS Corrupted Limitations', 'NRJ_AoS_CorruptedLimitations_TTS.png', names(build_nrj.CORRUPT),
         'Corrupted Limitation · AoS', 'CardBack_AoS_Limitation.png'),
    deck('AoS Backdoor Routines', 'NRJ_AoS_BackdoorRoutines_TTS.png', names(build_nrj.BACKDOOR),
         'Backdoor Routine · AoS', 'CardBack_NRJ_BackdoorRoutine.png'),
    deck('Imposter Scenarios', 'NRJ_ImposterScenarios_TTS.png', names(build_nrj.SCEN),
         lambda n, i: 'Council Test · %s' % build_nrj.SCEN[i][1], 'CardBack_NRJ_CouncilTest.png'),
    deck('Imposters', 'NRJ_Imposters_TTS.png', names(build_nrj.IMPOSTERS[0::2]),
         'Imposter card · side A', 'NRJ_Imposters_TTS_back.png',
         'Imposter card · side B', names(build_nrj.IMPOSTERS[1::2])),
]

total = 0
for key, game in CATALOG.items():
    for d in game['decks']:
        count = d['cols'] * d['rows']
        # A sheet may have blank cells at the end; more cards than cells is a real error.
        if len(d['cards']) > count:
            print('  ! %-28s sheet holds %d, catalog has %d' % (d['sheet'], count, len(d['cards'])))
        total += len(d['cards'])
    print('%-4s %2d decks, %3d cards' % (key, len(game['decks']), sum(len(d['cards']) for d in game['decks'])))

with open(DEST, 'w', encoding='utf-8') as fh:
    json.dump(CATALOG, fh, ensure_ascii=False, indent=1)
print('%d cards -> %s' % (total, os.path.normpath(DEST)))
