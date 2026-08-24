"""Read a hand-arranged TTS save and emit an evenly-spaced layout.

Jon arranges the decks in TTS; this reads those positions, applies the portrait
card scale-up, then re-spaces each row so the gaps are uniform. Output is
layout.py, which build_mod.py and lua.lua both consume.

    python relayout.py "<path to TS_Save_36.json>"

Card footprints in table units. TTS derives a custom card's width from its
image aspect at a fixed height, so a 700x500 landscape sheet renders wider than
a 500x700 portrait one. Scaling portrait decks by PORTRAIT_SCALE makes every
card the same physical card, just rotated.
"""
import json, os, sys

PORTRAIT_SCALE = 1.4                 # 7/5 exactly: 2.5 -> 3.5 wide
CARD_W, CARD_H = 3.5, 4.9            # portrait footprint after scaling
GAP = 0.8                            # uniform edge gap between neighbours

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from decks import DECKS

LAND = {d['label']: d['land'] for d in DECKS}
ROW_TOL = 1.5                        # z values within this count as one row
CLUSTER_GAP = 8.0                    # x-gap that separates two arrangements

# Loose cards are named "<deck label> <n>" once taken off the deck.
def base_label(nick):
    parts = nick.rsplit(' ', 1)
    if len(parts) == 2 and parts[1].isdigit() and parts[0] in LAND:
        return parts[0]
    return nick


def footprint(label):
    """(width, height) in table units."""
    return (CARD_H, CARD_W) if LAND.get(label) else (CARD_W, CARD_H)


def zone_of(x, z):
    """Reporting only -- the layout itself is never grouped by zone."""
    if z > 12:                 return 'BAT'
    if x > 20 and z < -3:      return 'IMP'
    if x > 10:                 return 'NRJ'
    if z < -9:                 return 'AoS'
    return 'NAP'


def load(path):
    d = json.load(open(path, encoding='utf-8'))
    items = []
    for o in d['ObjectStates']:
        if o.get('Name') not in ('Deck', 'Card', 'CardCustom'):
            continue
        nick = o.get('Nickname') or ''
        if not nick:
            continue
        t = o['Transform']
        items.append({'nick': nick, 'label': base_label(nick),
                      'x': t['posX'], 'z': t['posZ'], 'y': t['posY']})
    return d, items


def regrid(items):
    """Open up just enough room for the larger footprints.

    An earlier version re-gridded each zone into uniform rows. It inferred the
    grouping wrongly -- splitting the Time Slot column, folding Advanced
    Programs into the Element Mats row -- so this instead treats the arrangement
    as authoritative and only separates pairs that would actually overlap.
    Displacement is shared equally and applied on the axis of least overlap, so
    a row opens sideways rather than buckling out of line.
    """
    for it in items:
        it['zone'] = zone_of(it['x'], it['z'])
        it['nx'], it['nz'] = it['x'], it['z']

    # ---- rows are read off the ORIGINAL positions, where the grouping is
    # unambiguous and tight, then aligned and evenly spaced.
    rows, used = [], set()
    for it in sorted(items, key=lambda i: -i['z']):
        if id(it) in used:
            continue
        row = [j for j in items
               if id(j) not in used and abs(j['z'] - it['z']) <= ROW_TOL]
        for j in row:
            used.add(id(j))
        rows.append(sorted(row, key=lambda i: i['x']))

    for row in rows:
        mean_z = sum(i['z'] for i in row) / len(row)
        for it in row:
            it['nz'] = mean_z                       # align the row

        # An x-gap this large means two separate arrangements that happen to
        # share a z -- e.g. a NAP time slot and an NRJ module. Space each
        # cluster on its own so they are not dragged together.
        clusters, cur = [], [row[0]]
        for prev, it in zip(row, row[1:]):
            if it['x'] - prev['x'] > CLUSTER_GAP:
                clusters.append(cur); cur = []
            cur.append(it)
        clusters.append(cur)

        for cl in clusters:
            widths = [footprint(i['label'])[0] for i in cl]
            total = sum(widths) + GAP * (len(cl) - 1)
            centre = (min(i['x'] for i in cl) + max(i['x'] for i in cl)) / 2.0
            cursor = centre - total / 2.0
            for it, w in zip(cl, widths):
                it['nx'] = cursor + w / 2.0
                cursor += w + GAP

    # ---- part rows that now collide vertically, moving whole rows so the
    # alignment just established survives.
    rows.sort(key=lambda r: -r[0]['nz'])
    for upper, lower in zip(rows, rows[1:]):
        def span(r):
            return (min(i['nx'] - footprint(i['label'])[0] / 2 for i in r),
                    max(i['nx'] + footprint(i['label'])[0] / 2 for i in r))
        ua, ub = span(upper); la, lb = span(lower)
        if ub < la or lb < ua:
            continue                                 # side by side, no clash
        need = (max(footprint(i['label'])[1] for i in upper) +
                max(footprint(i['label'])[1] for i in lower)) / 2.0 + GAP
        drop = need - (upper[0]['nz'] - lower[0]['nz'])
        if drop > 0:
            for r in rows[rows.index(lower):]:
                for it in r:
                    it['nz'] -= drop

    for _ in range(400):
        worst = 0.0
        for i, a in enumerate(items):
            aw, ah = footprint(a['label'])
            for b in items[i + 1:]:
                bw, bh = footprint(b['label'])
                dx = abs(a['nx'] - b['nx'])
                dz = abs(a['nz'] - b['nz'])
                ox = (aw + bw) / 2.0 + GAP - dx
                oz = (ah + bh) / 2.0 + GAP - dz
                if ox <= 0 or oz <= 0:
                    continue                       # already clear
                worst = max(worst, min(ox, oz))
                if ox < oz:                        # cheaper to part sideways
                    s = ox / 2.0 if a['nx'] <= b['nx'] else -ox / 2.0
                    a['nx'] -= s
                    b['nx'] += s
                else:
                    s = oz / 2.0 if a['nz'] <= b['nz'] else -oz / 2.0
                    a['nz'] -= s
                    b['nz'] += s
        if worst < 0.01:
            break

    for it in items:
        it['nx'] = round(it['nx'], 2)
        it['nz'] = round(it['nz'], 2)
    return items


def main():
    src = sys.argv[1]
    save, items = load(src)
    regrid(items)

    out = os.path.join(HERE, 'layout.py')
    with open(out, 'w', encoding='utf-8', newline='\n') as f:
        f.write('"""Generated by relayout.py from %s. Do not hand-edit."""\n'
                % os.path.basename(src))
        f.write('TABLE = %r\n' % save.get('Table'))
        f.write('SKY = %r\n' % save.get('Sky'))
        f.write('PORTRAIT_SCALE = %r\n\n' % PORTRAIT_SCALE)
        f.write('# label -> (x, z); loose cards keep their numbered nickname\n')
        f.write('POS = {\n')
        for it in sorted(items, key=lambda i: (i['zone'], -i['nz'], i['nx'])):
            f.write("    %-28r: (%7.2f, %7.2f),   # %s\n"
                    % (it['nick'], it['nx'], it['nz'], it['zone']))
        f.write('}\n')
    print('wrote', out, '-', len(items), 'placements')

    for zone in sorted({i['zone'] for i in items}):
        g = [i for i in items if i['zone'] == zone]
        moved = max(max(abs(i['nx'] - i['x']), abs(i['nz'] - i['z'])) for i in g)
        print('  %-4s %2d objects, max shift %.1f' % (zone, len(g), moved))


if __name__ == '__main__':
    main()
