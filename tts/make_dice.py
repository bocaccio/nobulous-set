# -*- coding: utf-8 -*-
"""Draw the eight dice: five unit dice and three stat dice.

    python3 make_dice.py            -> images/Die_*.png

WHY THESE ARE DRAWN AND NOT BORROWED. The mod used the dice out of
the official 20 Strong mod, served from Steam, and CONTENT_NOTICE.md
says the set reproduces no Chip Theory Games artwork. Pointing at
someone else's upload kept that true in the letter but left the mod
depending on art it does not own and cannot keep alive. These are
originals, so the dependency goes.

WHAT THE DICE ACTUALLY ARE, which the textures hide. A unit die is
five success faces and one crit. A stat die is a plain 1-6 in a
themed frame - a down arrow for Recovery, a concave-sided square for
Strategy, a heart for Health - and the three share one layout.

THE LAYOUT IS MEASURED, NOT DERIVED. Where TTS puts each face of a
custom d6 on its texture is TTS's business and guessing costs a
round trip through the client per guess, so this copies the geometry
of the sheets it replaces: a 2048 square on a 682.67 grid, glyph
centres at x 341/1024/1707 and y 1024/1707, the top third of the
image carrying no face at all. Whatever the mapping is, identical
placement maps identically.

AND TWO CELLS ARE DRAWN UPSIDE DOWN. (0,1) and (2,1) are rotated 180
degrees in the original textures, identically on all eight dice, so
they read upright on the die. Rotate the originals back and the stat
dice's "9" is a 6 and their two "up arrows" are down arrows. Draw
six upright numerals instead and two faces of every stat die land
upside down on the table, with every flat preview of the sheet
looking perfect. check_app_sync holds this.

THE HEART IS NOT DRAWN HERE. gen.py already carries one - the
Anatomy subject icon, printed on the cards - so Health is built from
the project's own art. It is READ from gen.py rather than copied, so
a redrawn icon reaches the die and there is only ever one heart.
"""
import hashlib
import io
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from PIL import Image, ImageChops, ImageDraw

import glyphs

IMAGES = os.path.join(ROOT, "images")
FONT = os.path.join(ROOT, "fonts", "DejaVuSans-Bold.ttf")
SIDE = 2048
CELL = SIDE / 3.0
SS = 4
INK = (255, 255, 255)
CX = [CELL * (i + 0.5) for i in range(3)]
CY = [CELL * 1.5, CELL * 2.5]
CRIT_AT = (0, 1)
# value, and whether the cell is drawn upside down
LAYOUT = {(0, 0): (2, False), (1, 0): (4, False), (2, 0): (5, False),
          (0, 1): (1, True), (1, 1): (3, False), (2, 1): (6, True)}

# Body colours, read off the sheets these replace, so the dice still
# match the ones in the player's box even though the faces do not.
UNIT = [("Red", (193, 18, 86)), ("Purple", (119, 70, 210)),
        ("Blue", (57, 124, 233)), ("Green", (93, 146, 54)),
        ("Yellow", (233, 209, 55))]
STAT_BODY = (208, 199, 200)
#  name        ink             w/CELL h/CELL numeral dy
STAT = {
    "Recovery": ((63, 122, 78), 0.776, 0.710, 0.300, -0.028),
    "Strategy": ((47, 107, 168), 0.762, 0.763, 0.330, 0.0),
    "Health": ((168, 51, 44), 0.770, 0.678, 0.300, -0.030),
}
TEETH, TIP, DEPTH = 8, 0.28, 0.095
NUMPAT = r"[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?"


# ------------------------------------------------------------- shapes
def gear(cx, cy, r_out, r_root, teeth, tip=0.40, root=0.40, arc=9):
    """A gear outline, built the way a gear is: an arc at each tooth
    tip, an arc at the root between them, straight flanks joining.

    An earlier version rode a smoothed wave between the two radii and
    drew a splat - teeth of uneven width with ragged edges, from a
    phase test that was wrong in a way only the picture showed. Arcs
    cannot go uneven: every tooth is the same four spans of one pitch.
    """
    pitch = 2 * math.pi / teeth
    flank = (1.0 - tip - root) / 2.0
    pts = []
    for i in range(teeth):
        c = i * pitch
        a0, a1 = c - tip * pitch / 2.0, c + tip * pitch / 2.0
        for k in range(arc + 1):
            a = a0 + (a1 - a0) * k / arc
            pts.append((cx + r_out * math.cos(a), cy + r_out * math.sin(a)))
        b0 = a1 + flank * pitch
        b1 = b0 + root * pitch
        for k in range(arc + 1):
            a = b0 + (b1 - b0) * k / arc
            pts.append((cx + r_root * math.cos(a), cy + r_root * math.sin(a)))
    return pts


def arrow(cx, cy, w, h, sw_f=0.62, head_f=0.42):
    """A down arrow as one polygon: shaft, shoulders, point."""
    sw = w * sw_f
    hy = cy + h / 2.0 - h * head_f
    return [(cx - sw / 2, cy - h / 2), (cx + sw / 2, cy - h / 2),
            (cx + sw / 2, hy), (cx + w / 2, hy), (cx, cy + h / 2),
            (cx - w / 2, hy), (cx - sw / 2, hy)]


def star4(cx, cy, w, h, bow=0.584, steps=20):
    """A square with its corners kept and its edges bowed inward.

    w and h are the extent of the DRAWN shape, as they are for the
    other two frames. The corners sit on the diagonals, so the radius
    is the half-width over cos 45 - without that the frame comes out
    at 0.707 of the size asked for, which measured 367 wide against
    the 520 the original draws.

    bow sets how far the edges pull in: the quadratic's midpoint sits
    at rx * (cos45 + bow) / 2, so the width at mid-height works out
    as (0.354 + bow/2) / 0.707 of the full width. The original
    measures 0.914, which is bow 0.584. At 0.46 it read 0.827 and
    looked like a throwing star rather than a pillow.
    """
    rx = (w / 2.0) / math.cos(math.pi / 4)
    ry = (h / 2.0) / math.cos(math.pi / 4)
    corners = [(cx + rx * math.cos(a), cy + ry * math.sin(a))
               for a in (math.pi / 4, 3 * math.pi / 4,
                         5 * math.pi / 4, 7 * math.pi / 4)]
    mids = [(cx + rx * bow * math.cos(a), cy + ry * bow * math.sin(a))
            for a in (math.pi / 2, math.pi, 3 * math.pi / 2, 0.0)]
    pts = []
    for i in range(4):
        p0, p2, c = corners[i], corners[(i + 1) % 4], mids[i]
        for k in range(steps + 1):
            t = k / float(steps)
            u = 1.0 - t
            pts.append((u * u * p0[0] + 2 * u * t * c[0] + t * t * p2[0],
                        u * u * p0[1] + 2 * u * t * c[1] + t * t * p2[1]))
    return pts


# --------------------------------------------------------- the heart
def svg_path(d, steps=24):
    """Flatten an SVG path of M/L/H/V/C/S/Z into one closed polygon.

    Enough of the grammar for the icons in gen.py and no more: those
    are Material-style glyphs - moves, lines and cubics, absolute and
    relative, with implicit repeats and no arcs. An arc raises a
    KeyError here rather than quietly drawing a straight line.
    """
    toks = re.findall(r"[MmLlHhVvCcSsZz]|" + NUMPAT, d)
    pts = []
    cur = start = (0.0, 0.0)
    prev_c2 = None
    cmd = None
    i = 0

    def cubic(p0, c1, c2, p3):
        for k in range(1, steps + 1):
            t = k / float(steps)
            u = 1.0 - t
            pts.append((u * u * u * p0[0] + 3 * u * u * t * c1[0]
                        + 3 * u * t * t * c2[0] + t * t * t * p3[0],
                        u * u * u * p0[1] + 3 * u * u * t * c1[1]
                        + 3 * u * t * t * c2[1] + t * t * t * p3[1]))

    while i < len(toks):
        t = toks[i]
        if t.isalpha():
            cmd = t
            i += 1
            if cmd in ("Z", "z"):
                cur = start
                continue
        rel = cmd.islower()
        k = cmd.upper()
        n = {"M": 2, "L": 2, "H": 1, "V": 1, "C": 6, "S": 4}[k]
        a = [float(x) for x in toks[i:i + n]]
        i += n
        if k == "M":
            cur = (cur[0] + a[0], cur[1] + a[1]) if rel else (a[0], a[1])
            start = cur
            pts.append(cur)
            cmd = "l" if rel else "L"       # a second pair after M is an L
        elif k == "L":
            cur = (cur[0] + a[0], cur[1] + a[1]) if rel else (a[0], a[1])
            pts.append(cur)
        elif k == "H":
            cur = (cur[0] + a[0], cur[1]) if rel else (a[0], cur[1])
            pts.append(cur)
        elif k == "V":
            cur = (cur[0], cur[1] + a[0]) if rel else (cur[0], a[0])
            pts.append(cur)
        else:
            if k == "C":
                c1 = (cur[0] + a[0], cur[1] + a[1]) if rel else (a[0], a[1])
                c2 = (cur[0] + a[2], cur[1] + a[3]) if rel else (a[2], a[3])
                p3 = (cur[0] + a[4], cur[1] + a[5]) if rel else (a[4], a[5])
            else:
                c1 = ((2 * cur[0] - prev_c2[0], 2 * cur[1] - prev_c2[1])
                      if prev_c2 else cur)
                c2 = (cur[0] + a[0], cur[1] + a[1]) if rel else (a[0], a[1])
                p3 = (cur[0] + a[2], cur[1] + a[3]) if rel else (a[2], a[3])
            cubic(cur, c1, c2, p3)
            prev_c2, cur = c2, p3
            continue
        prev_c2 = None
    return pts


def heart_path():
    """The Anatomy heart, read out of gen.py."""
    src = io.open(os.path.join(ROOT, "generator", "gen.py"),
                  encoding="utf-8").read()
    m = re.search(r"'Anatomy':.*?<path fill=\"[^\"]+\" d=\"([^\"]+)\"",
                  src, re.S)
    if not m:
        raise SystemExit("gen.py no longer carries an Anatomy heart path")
    pts = svg_path(m.group(1))
    # THE TIP IS OFF CENTRE AND IT SHOWS AT THIS SIZE. The path puts
    # the point at x 12 while the two shoulders feeding it sit at 10.3
    # and 11.7, so the V is lopsided and the heart grows a small hook.
    # At 24px on a card that is invisible, which is presumably why it
    # has never mattered; blown up to a die face it reads as a drawing
    # error. Moving the lowest point to the midpoint of its neighbours
    # fixes it and touches nothing else - and gen.py is NOT edited, so
    # the printed icon stays exactly as it is.
    lo = max(range(len(pts)), key=lambda i: pts[i][1])
    near = [q[0] for q in pts
            if q[1] > pts[lo][1] - 2.0 and abs(q[1] - pts[lo][1]) > 0.3]
    if near:
        pts[lo] = ((min(near) + max(near)) / 2.0, pts[lo][1])
    return pts


def fit(pts, cx, cy, w, h):
    """Scale a path to w x h about its own bounds, centred on cx, cy."""
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    sx, sy = w / (x1 - x0), h / (y1 - y0)
    return [(cx + (p[0] - (x0 + x1) / 2.0) * sx,
             cy + (p[1] - (y0 + y1) / 2.0) * sy) for p in pts]


# --------------------------------------------------------- the faces
def unit_face(u, bg, crit):
    """One unit-die face: a gear with an open bore, or the crit, whose
    bore is filled and carries a thin ring of the die's own colour."""
    n = int(u * SS)
    im = Image.new("RGB", (n, n), bg)
    d = ImageDraw.Draw(im)
    c = n / 2.0
    # 0.383, not 0.42, which is what the originals draw at: a glyph of
    # 0.42 spans 573px of the 682.67 cell against their 523, and a
    # face texture that overruns its cell looks fine in the PNG and
    # clips on the die.
    r_out = n * 0.383
    r_root = r_out - n * DEPTH
    r_in = r_root - n * 0.085
    d.polygon(gear(c, c, r_out, r_root, TEETH, tip=TIP), fill=INK)
    if crit:
        r = r_in * 0.74
        d.ellipse([c - r, c - r, c + r, c + r], outline=bg,
                  width=int(n * 0.030))
    else:
        d.ellipse([c - r_in, c - r_in, c + r_in, c + r_in], fill=bg)
    return im.resize((int(u), int(u)), Image.LANCZOS)


def stat_shape(kind, cx, cy, w, h):
    if kind == "Recovery":
        return arrow(cx, cy, w, h)
    if kind == "Strategy":
        return star4(cx, cy, w, h)
    return fit(heart_path(), cx, cy, w, h)


def stat_face(kind, u, value):
    ink, wf, hf, nf, dy = STAT[kind]
    n = int(u * SS)
    im = Image.new("RGB", (n, n), STAT_BODY)
    ImageDraw.Draw(im).polygon(
        stat_shape(kind, n / 2.0, n / 2.0, u * SS * wf, u * SS * hf),
        fill=ink)
    im = im.resize((int(u), int(u)), Image.LANCZOS).convert("RGBA")
    pt = int(u * nf)
    w_, cap = glyphs.text_size(str(value), pt, FONT)
    glyphs.draw_text(im, (u / 2.0 - w_ / 2.0, u / 2.0 + cap / 2.0 + u * dy),
                     str(value), pt, STAT_BODY, FONT)
    return im.convert("RGB")


def sheet(name):
    if name in STAT:
        im = Image.new("RGB", (SIDE, SIDE), STAT_BODY)
        for (c, r), (v, rot) in sorted(LAYOUT.items()):
            f = stat_face(name, CELL, v)
            if rot:
                f = f.rotate(180)
            im.paste(f, (int(CX[c] - CELL / 2), int(CY[r] - CELL / 2)))
        return im
    bg = dict(UNIT)[name]
    im = Image.new("RGB", (SIDE, SIDE), bg)
    for r in range(2):
        for c in range(3):
            im.paste(unit_face(CELL, bg, (c, r) == CRIT_AT),
                     (int(CX[c] - CELL / 2), int(CY[r] - CELL / 2)))
    return im


def envelope(im):
    """How big the glyph in the first face is, as (width, height).

    The same measurement that read the layout off the sheets being
    replaced, and worth printing on every run: a face texture that
    overruns its cell looks perfectly fine in the PNG and clips on
    the die, so the number to watch is this one against the 480-530
    the originals draw.

    Done with PIL's own channel ops rather than a Python pixel loop -
    a loop over eight 2048 squares takes the best part of a minute -
    and MAX of the three channel differences rather than their mean,
    because white on yellow differs in one channel only and an
    average washes it out below any sane threshold.
    """
    box = (int(CX[0] - CELL / 2), int(CY[0] - CELL / 2),
           int(CX[0] + CELL / 2), int(CY[0] + CELL / 2))
    cell = im.convert("RGB").crop(box)
    flat = Image.new("RGB", cell.size, cell.getpixel((3, 3)))
    r, g, b = ImageChops.difference(cell, flat).split()
    mask = ImageChops.lighter(ImageChops.lighter(r, g), b).point(
        lambda v: 255 if v > 25 else 0)
    hit = mask.getbbox()
    return (0, 0) if not hit else (hit[2] - hit[0], hit[3] - hit[1])


def main():
    names = [n for n, _ in UNIT] + sorted(STAT)
    for name in names:
        im = sheet(name)
        buf = io.BytesIO()
        im.save(buf, "PNG", optimize=True)
        raw = buf.getvalue()
        out = "Die_%s_%s.png" % (name, hashlib.md5(raw).hexdigest()[:8])
        # ONE FILE PER DIE, hashed, so no CDN and no TTS cache can
        # serve a superseded face - the same reason every other image
        # in the mod carries its content hash.
        for old in os.listdir(IMAGES):
            if old.startswith("Die_%s_" % name) and old != out:
                os.remove(os.path.join(IMAGES, old))
        io.open(os.path.join(IMAGES, out), "wb").write(raw)
        gw, gh = envelope(im)
        print("  %-28s glyph %dw x %dh" % (out, gw, gh))
    print("%d dice written to images/" % len(names))


if __name__ == "__main__":
    main()
