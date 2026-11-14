"""Check every card for text that does not fit.

    python3 check_cards.py

Each card is laid out again with its height released and a marker placed just
after it: the marker's position is the height the card actually wants, and
anything taller than the printed card would have been clipped.

Cards whose layout is pinned to the card edges (the NAP Task and NRJ Imposter
Task spines) carry no flow height, so they are skipped by the flow pass.

THE FLOW PASS CANNOT SEE TEXT OVERFLOW, which is what the ink pass below is
for. Released-height measurement answers "is there another block here", not
"does this block fit": on a Research Note, 199 characters of body measured
52.9mm and 738 characters measured the same 65.6mm as 278 did. Eighteen cards
passed it on 2026-11-14 that printed with the footer shoved off the card.

The ink pass renders each card at its printed height with the overflow
released and reads the pixels, so it answers the question in the only
currency that cannot be argued with. It is slower - one render per card
rather than one per card, but rasterised - so `--flow-only` skips it.

Nothing is written; the build scripts are only imported, with rendering stubbed.
"""
import os
import subprocess
import sys
import tempfile
import types

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import gen  # noqa: E402
from weasyprint import HTML  # noqa: E402

DECKS = []          # (deck, [card html], size, extra)
SHEETS = []         # (deck, sheet file, cols, rows, count)


def _record(name, cards, accent_key, size=gen.PORTRAIT, extra='', back=None):
    DECKS.append((name, list(cards), size, extra))
    return len(cards)


def _record_duplex(name, fronts, backs, accent_key, size=gen.PORTRAIT, extra=''):
    DECKS.append((name + ' front', list(fronts), size, extra))
    DECKS.append((name + ' back', list(backs), size, extra))
    return len(fronts)


def collect():
    stub = types.ModuleType('gen')
    for attr in dir(gen):
        if not attr.startswith('__'):
            setattr(stub, attr, getattr(gen, attr))
    stub.render_deck = _record
    stub.render_duplex = _record_duplex
    stub.make_back = lambda *a, **k: None
    sys.modules['gen'] = stub
    for mod in ('build_bat', 'build_nap', 'build_aos', 'build_nrj'):
        __import__(mod)


INSET = 2.0                      # .card sits 2mm inside the page
SLACK_MM = 0.4


def wanted_height(card_html, size, extra):
    """Height the card's content needs, or None when the card is edge-pinned."""
    w, h = size
    free = ('.card{position:static;inset:auto;height:auto;min-height:0;overflow:visible;'
            'margin:%fmm;width:%fmm}' % (INSET, w - 2 * INSET))
    doc = HTML(string=gen.page(card_html + '<hr>', '#2c5f4a', (w, h * 8), extra + free)).render()

    def find(box):
        if getattr(box, 'element_tag', None) == 'hr':
            return box.position_y
        for child in getattr(box, 'all_children', lambda: [])():
            found = find(child)
            if found is not None:
                return found
        return None

    y = find(doc.pages[0]._page_box)
    return None if y is None else y / 96.0 * 25.4


def flow_pass():
    problems = 0
    for name, cards, size, extra in DECKS:
        for i, card in enumerate(cards, 1):
            need = wanted_height(card, size, extra)
            if need is None or need < 1:
                continue                      # edge-pinned layout; see the ink pass
            if need > size[1] + SLACK_MM:
                print('  OVERRUN  %-26s card %2d wants %.1fmm of %.1fmm'
                      % (name, i, need, size[1]))
                problems += 1
    return problems


TAG_MM = 3.4                     # the NRJ edge band, painted over the body
INK_DPI = 150
INK_SLACK_MM = 0.3               # antialiasing on the band's own top edge


def _free(w, h, nrj):
    """Card at its printed height, overflow released, floor exposed."""
    css = ('.card{position:relative;inset:auto;overflow:visible;'
           'margin:%fmm;width:%fmm;height:%fmm;min-height:0;max-height:none}'
           '.body>*{flex:0 0 auto}.spacer{display:none}'
           % (INSET, w - 2 * INSET, h - 2 * INSET))
    # position:RELATIVE, or the NRJ band is positioned against the page
    # instead of the card. flex:0 0 auto, or WeasyPrint squashes the
    # items and the overrun prints on top of its neighbour rather than
    # below the card where it can be seen. See the module docstring.
    return css + ('.nrjtag{display:none}' if nrj else '')


def _lowest_ink(im):
    """Bottom-most dark row, in pixels; everything below a card is pale."""
    px = im.convert('L').load()
    w, h = im.size
    for y in range(h - 1, -1, -1):
        if any(px[x, y] < 120 for x in range(0, w, 2)):
            return y
    return 0


def ink_pass():
    from PIL import Image
    problems = 0
    tmp = tempfile.mkdtemp(prefix='nobulous_ink_')
    for name, cards, size, extra in DECKS:
        w, h = size
        nrj = any('card nrj' in c for c in cards)
        floor_mm = INSET + (h - 2 * INSET) - (TAG_MM if nrj else 0.0)
        html = ''.join('<div style="page-break-after:always">%s</div>' % c
                       for c in cards)
        pdf = os.path.join(tmp, '%s.pdf' % name.replace(' ', '_'))
        stem = pdf[:-4]
        HTML(string=gen.page(html, gen.ACCENT['NRJ'], (w, h * 3),
                             extra + _free(w, h, nrj))).write_pdf(pdf)
        subprocess.run(['pdftoppm', '-r', str(INK_DPI), '-png', pdf, stem],
                       check=True, capture_output=True)
        pages = sorted(f for f in os.listdir(tmp)
                       if f.startswith(os.path.basename(stem) + '-')
                       and f.endswith('.png'))
        for i, f in enumerate(pages, 1):
            p = os.path.join(tmp, f)
            over = (_lowest_ink(Image.open(p)) / INK_DPI * 25.4) - floor_mm
            os.remove(p)
            if over > INK_SLACK_MM:
                print('  OVERFLOW %-26s card %2d prints %.1fmm past the '
                      'bottom of its text area' % (name, i, over))
                problems += 1
        os.remove(pdf)
    try:
        os.rmdir(tmp)
    except OSError:
        pass
    return problems


if __name__ == '__main__':
    collect()
    total = sum(len(c) for _, c, _, _ in DECKS)
    print('flow pass: %d cards in %d decks' % (total, len(DECKS)))
    bad = flow_pass()
    if '--flow-only' not in sys.argv:
        print('ink pass: %d cards in %d decks' % (total, len(DECKS)))
        bad += ink_pass()
    print('no problems found' if not bad else '%d problem(s)' % bad)
    raise SystemExit(1 if bad else 0)
