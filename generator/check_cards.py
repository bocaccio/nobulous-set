"""Check every card for text that does not fit.

    python3 check_cards.py

Each card is laid out again with its height released and a marker placed just
after it: the marker's position is the height the card actually wants, and
anything taller than the printed card would have been clipped.

Cards whose layout is pinned to the card edges (the NAP Task and NRJ Impostor
Task spines) carry no flow height, so they are skipped - those two decks have
fixed geometry and are checked by eye.

Nothing is written; the build scripts are only imported, with rendering stubbed.
"""
import os
import sys
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


if __name__ == '__main__':
    collect()
    total = sum(len(c) for _, c, _, _ in DECKS)
    print('flow pass: %d cards in %d decks' % (total, len(DECKS)))
    bad = flow_pass()
    print('no problems found' if not bad else '%d problem(s)' % bad)
    raise SystemExit(1 if bad else 0)
