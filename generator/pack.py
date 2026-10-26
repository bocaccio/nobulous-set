"""Assemble the per-deck output into one print-and-play file per game.

    python3 pack.py

Reads the card manifests written by render_deck / render_duplex, cuts the cards
back out of the TTS sheets, and fills every page: nine cards to a sheet, mixing
decks rather than starting a new page for each one. Each page of fronts is
followed by its page of backs, with the columns mirrored, so the whole file
prints double-sided on a long-edge flip.

Landscape cards are the same size as the rest, only turned, so they are rotated
a quarter turn and share the same pages. Every page carries a label in its
bottom margin: "Page 3 - Front", "Page 3 - Back".
"""
import json
import os

from PIL import Image

from gen import OUT, paginate, pnp_layout, stamp, write_pnp

# Deck order within each game; the label is what the contents file prints.
GAMES = {
    'BAT': [
        ('BAT_Encounters', 'Encounters'),
        ('BAT_Upgrades', 'Upgrades'),
        ('BAT_Specimens', 'Specimens'),
        ('BAT_TyrantAttacks', 'Tyrant Attacks'),
        ('BAT_BuffHP', 'Buff HP track'),
        ('BAT_Rats', 'Lab Rats (A / B)'),
    ],
    'NAP': [
        ('NAP_Tasks', 'Tasks'),
        ('NAP_Opportunities', 'Opportunities'),
        ('NAP_Setbacks', 'Setbacks'),
        ('NAP_FinalExams', 'Final Exams'),
        ('NAP_Apprentices', 'Apprentices (2 per card)'),
        ('NAP_SlotsFINF', 'Time Slots + FINF'),
    ],
    'AoS': [
        ('AoS_Limitations', 'Limitations'),
        ('AoS_Routine', 'Routine Programs'),
        ('AoS_Specialized', 'Specialized Programs'),
        ('AoS_Unstable', 'Unstable Programs'),
        ('AoS_Advanced', 'Advanced Programs'),
        ('AoS_Technicians', 'Technicians (2 per card)'),
        ('AoS_ElementMats', 'Element mats'),
    ],
    'NRJ': [
        ('NRJ_BAT_Protocols', 'Experimental Protocols'),
        ('NRJ_BAT_Modifications', 'Unauthorized Modifications'),
        ('NRJ_BAT_ResearchNotes', 'Research Notes'),
        ('NRJ_NAP_ImpostorTasks', 'Impostor Tasks'),
        ('NRJ_NAP_FollowingSetbacks', 'Following Setbacks'),
        ('NRJ_NAP_DeviousOpportunities', 'Devious Opportunities'),
        ('NRJ_AoS_Interference', 'Nobulous Interference'),
        ('NRJ_AoS_CorruptedLimitations', 'Corrupted Limitations'),
        ('NRJ_AoS_BackdoorRoutines', 'Backdoor Routines'),
        ('NRJ_ImposterScenarios', 'Council Test Scenarios'),
    ],
}


def cut(sheet, cols, rows, index):
    """One card out of a TTS sheet."""
    w, h = sheet.width // cols, sheet.height // rows
    col, row = index % cols, index // cols
    return sheet.crop((col * w, row * h, (col + 1) * w, (row + 1) * h))


def deck_cards(stem):
    """[(front, back or None, label)] for one deck, plus its manifest."""
    mf = os.path.join(OUT, '%s_cards.json' % stem)
    if not os.path.exists(mf):
        return None, None
    m = json.load(open(mf, encoding='utf-8'))
    sheet = Image.open(os.path.join(OUT, m['sheet'])).convert('RGB')
    back_names = m['back'] if isinstance(m['back'], list) else ([m['back']] * m['count'] if m['back'] else [])
    cache = {}

    def back_image(stem):
        if stem not in cache:
            cache[stem] = Image.open(os.path.join(OUT, stem)).convert('RGB')
        return cache[stem]

    backs = back_image(m['back']) if isinstance(m['back'], str) else None
    out = []
    for i in range(m['count']):
        front = cut(sheet, m['cols'], m['rows'], i)
        if not back_names:
            back = None
        elif m['backIsSheet']:
            back = cut(backs, m['cols'], m['rows'], i)
        else:
            img = back_image(back_names[i])
            back = img if img.size == front.size else img.resize(front.size)
        out.append((front, back))
    return out, m


def build(game):
    """One stream of cards, nine to a page, fronts then their mirrored backs."""
    cards, missing = [], []
    for stem, label in GAMES[game]:
        deck, m = deck_cards(stem)
        if deck is None:
            missing.append(stem)
            continue
        for n, (front, back) in enumerate(deck, 1):
            if m['landscape']:
                # Same card, turned upright; front and back turn together so the
                # two sides still line up after cutting.
                front = front.rotate(90, expand=True)
                back = back.rotate(90, expand=True) if back is not None else None
            cards.append((front, back, label, n))

    pages, lines = [], []
    lay = pnp_layout(cards[0][0].size) if cards else None
    per = lay[2] * lay[3] if lay else 9
    for sheet_no, i in enumerate(range(0, len(cards), per), 1):
        chunk = cards[i:i + per]
        front_pg = paginate([c[0] for c in chunk], lay=lay)[0]
        stamp(front_pg, 'Page %d - Front' % sheet_no)
        pages.append(front_pg)
        if all(c[1] is not None for c in chunk):
            back_pg = paginate([c[1] for c in chunk], mirror=True, lay=lay)[0]
            stamp(back_pg, 'Page %d - Back' % sheet_no)
            pages.append(back_pg)
        span = []
        for label in dict.fromkeys(c[2] for c in chunk):
            nums = [c[3] for c in chunk if c[2] == label]
            span.append('%s %d-%d' % (label, nums[0], nums[-1]) if len(nums) > 1
                        else '%s %d' % (label, nums[0]))
        lines.append('  Page %-2d  %d cards  %s' % (sheet_no, len(chunk), ', '.join(span)))
    for stem in missing:
        lines.append('  MISSING  %s' % stem)
    out = os.path.join(OUT, 'NobulousSet_%s_PnP.pdf' % game)
    write_pnp(out, pages)
    return out, len(pages), lines


if __name__ == '__main__':
    report = []
    for g in ('BAT', 'NAP', 'AoS', 'NRJ'):
        out, pages, lines = build(g)
        print('%-4s %2d pages -> %s' % (g, pages, os.path.basename(out)))
        report.append('%s  (%d pages)' % (os.path.basename(out), pages))
        report += lines
        report.append('')
    with open(os.path.join(OUT, 'PNP_CONTENTS.txt'), 'w') as f:
        f.write('PRINT AND PLAY CONTENTS\n'
                'Letter paper, 9 cards per page (3 x 3), poker size 63.5 x 88.9 mm.\n'
                'Print at 100%, scale to fit OFF.\n\n'
                'Pages alternate fronts and backs, labelled in the bottom margin:\n'
                'Page 1 - Front, then Page 1 - Back for those same nine cards. The\n'
                'back columns are mirrored, so print double-sided and flip on the\n'
                'LONG edge.\n\n')
        f.write('\n'.join(report))
    print('contents ->', os.path.join(OUT, 'PNP_CONTENTS.txt'))
