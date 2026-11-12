# -*- coding: utf-8 -*-
"""Draw the Chip's two faces, from the constants that read them.

    python3 make_chip.py            -> images/Chip_Colour_*.png
                                       images/Chip_Dial_*.png

WHY THIS IS NOT A DRAWING JOB LIKE THE DICE. The script does not
merely display these faces, it TURNS them. build_mod.py carries the
angle each colour wedge sits at (CHIP_SEGMENT) and the angle the
dial's zero marker sits at (CHIP_DIAL_MARK), both of which used to
be measured off photographs of the physical component; CHIP_ANGLE
and CHIP_DIAL are derived from them, and check_app_sync re-measures
the marker to make sure the table still agrees with the picture.

So a replacement cannot merely look right. Registered even a few
degrees out, every turn the script makes lands on the wrong colour
and the wrong number - and nothing about the picture would look
wrong. This generates the art FROM those constants rather than
measuring art afterwards, which turns the relationship the right way
round: the picture cannot disagree with the table, because the table
is what drew it.

  colour wedges   CHIP_SEGMENT[c] + ART_OFFSET, clockwise from top
  dial            CHIP_DIAL_MARK for the marker, then 0..20 clockwise
                  in slots of 360 / CHIP_DIAL_SLOTS

ART_OFFSET is the 197 that build_mod.py's own comment records: it
says the wedges sit at Red 233, Yellow 305, Green 17, Blue 89,
Purple 161 and that every CHIP_SEGMENT number is that less 197, the
difference being absorbed by CHIP_TRIM. Keeping the art on those
angles is what lets CHIP_TRIM stay the number Jon calibrated at the
table.

WHAT IS DELIBERATELY NOT HERE. The scans have a crescent in the
middle of the colour wheel and a sun in the middle of the dial. The
set has no emblem anywhere - its card backs are type on flat colour -
so the well is left plain rather than given heraldry it has never
had. The wedges use the DIE body colours, so a wedge and the die it
names are the same colour, which the scans were not.
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

from PIL import Image, ImageDraw

import glyphs

IMAGES = os.path.join(ROOT, "images")
FONT = os.path.join(ROOT, "fonts", "DejaVuSans-Bold.ttf")
SIDE = 1024
SS = 2
ART_OFFSET = 197

DARK = (36, 31, 26)              # #241f1a, the Final Exam card back
RIM = (24, 21, 18)
WELL = (46, 41, 36)
LINE = (208, 203, 193)
OLIVE = (111, 122, 46)           # #6f7a2e, the Theory olive
WEDGE = {"Red": (193, 18, 86), "Yellow": (233, 209, 55),
         "Green": (93, 146, 54), "Blue": (57, 124, 233),
         "Purple": (119, 70, 210)}


def consts():
    """CHIP_SEGMENT, CHIP_DIAL_MARK and CHIP_DIAL_SLOTS, read out of
    build_mod.py rather than copied, so the art tracks the table."""
    src = io.open(os.path.join(HERE, "build_mod.py"),
                  encoding="utf-8").read()
    seg = dict((k, int(v)) for k, v in re.findall(
        r"'(\w+)': (\d+)",
        re.search(r"CHIP_SEGMENT = \{(.*?)\}", src, re.S).group(1)))
    mark = float(re.search(r"^CHIP_DIAL_MARK = ([\d.]+)", src, re.M).group(1))
    slots = int(re.search(r"^CHIP_DIAL_SLOTS = (\d+)", src, re.M).group(1))
    if sorted(seg) != sorted(WEDGE):
        raise SystemExit("CHIP_SEGMENT names %r, the art has %r"
                         % (sorted(seg), sorted(WEDGE)))
    return seg, mark, slots


def at(cx, cy, r, deg):
    """A point r from the centre at deg CLOCKWISE FROM THE TOP, which
    is how every angle in build_mod.py is written."""
    t = math.radians(deg)
    return (cx + r * math.sin(t), cy - r * math.cos(t))


def wedge(d, cx, cy, r0, r1, a0, a1, fill, steps=96):
    pts = [at(cx, cy, r1, a0 + (a1 - a0) * i / steps)
           for i in range(steps + 1)]
    pts += [at(cx, cy, r0, a1 - (a1 - a0) * i / steps)
            for i in range(steps + 1)]
    d.polygon(pts, fill=fill)


def gear(cx, cy, r_out, r_root, teeth=8, tip=0.28, arc=7):
    """The unit die's gear, so the chip and the dice share a mark."""
    pitch = 2 * math.pi / teeth
    root = 0.40
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


def disc(d, cx, cy, r, fill):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fill)


def colour_face():
    seg, _mark, _slots = consts()
    n = SIDE * SS
    im = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = n / 2.0
    disc(d, c, c, n * 0.495, RIM)
    disc(d, c, c, n * 0.452, DARK)
    for name, a in sorted(seg.items()):
        mid = (a + ART_OFFSET) % 360
        wedge(d, c, c, n * 0.300, n * 0.440,
              mid - 36.0, mid + 36.0, WEDGE[name])
    # Dividers, carried out onto the rim so a boundary stays readable
    # with a die sitting on the wheel.
    for name, a in sorted(seg.items()):
        for edge in (-36.0, 36.0):
            b = ((a + ART_OFFSET) % 360) + edge
            d.line([at(c, c, n * 0.296, b), at(c, c, n * 0.482, b)],
                   fill=DARK, width=int(n * 0.007))
    for name, a in sorted(seg.items()):
        mid = (a + ART_OFFSET) % 360
        gx, gy = at(c, c, n * 0.370, mid)
        d.polygon(gear(gx, gy, n * 0.040, n * 0.030), fill=(255, 255, 255))
        disc(d, gx, gy, n * 0.0165, WEDGE[name])
    disc(d, c, c, n * 0.296, DARK)
    disc(d, c, c, n * 0.250, WELL)
    d.ellipse([c - n * 0.250, c - n * 0.250, c + n * 0.250, c + n * 0.250],
              outline=LINE, width=int(n * 0.006))
    disc(d, c, c, n * 0.030, LINE)
    return im.resize((SIDE, SIDE), Image.LANCZOS)


def dial_face():
    _seg, mark, slots = consts()
    n = SIDE * SS
    im = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = n / 2.0
    step = 360.0 / slots
    disc(d, c, c, n * 0.495, RIM)
    disc(d, c, c, n * 0.452, DARK)
    disc(d, c, c, n * 0.440, WELL)
    # THE MARKER SLOT, in the Theory olive. check_app_sync hunts this
    # colour between 0.55 and 0.95 of the half-width and asserts it
    # sits at CHIP_DIAL_MARK, so it is the one olive thing out there -
    # the hub below is olive too but lies inside 0.55 and is not seen.
    wedge(d, c, c, n * 0.300, n * 0.440,
          mark - step / 2, mark + step / 2, OLIVE)
    for i in range(slots):
        b = (mark + (i + 0.5) * step) % 360
        d.line([at(c, c, n * 0.300, b), at(c, c, n * 0.440, b)],
               fill=DARK, width=int(n * 0.005))
    d.ellipse([c - n * 0.300, c - n * 0.300, c + n * 0.300, c + n * 0.300],
              outline=LINE, width=int(n * 0.005))
    disc(d, c, c, n * 0.294, DARK)
    d.polygon(gear(c, c, n * 0.215, n * 0.170, teeth=20, tip=0.30), fill=LINE)
    disc(d, c, c, n * 0.150, OLIVE)
    im = im.resize((SIDE, SIDE), Image.LANCZOS)
    # The numbers last, at final size, so glyphs.py does its own
    # supersampling instead of being scaled twice.
    cc = SIDE / 2.0
    pt = int(SIDE * 0.062)
    for v in range(21):
        a = (mark + (v + 1) * step) % 360
        w_, cap = glyphs.text_size(str(v), pt, FONT)
        tile = Image.new("RGBA", (int(w_) + 12, int(cap) + 14), (0, 0, 0, 0))
        glyphs.draw_text(tile, (6, cap + 6), str(v), pt, LINE, FONT)
        tile = tile.rotate(-a, resample=Image.BICUBIC, expand=True)
        px, py = at(cc, cc, SIDE * 0.370, a)
        im.alpha_composite(tile, (int(px - tile.width / 2),
                                  int(py - tile.height / 2)))
    return im


def marker_angle(im):
    """Where the olive marker sits, by the rule check_app_sync uses.

    Kept here as well so the generator fails rather than shipping a
    dial the check will reject - and so the two agree on what "the
    marker" means.
    """
    w, h = im.size
    px = im.convert("RGBA").load()
    cx, cy = (w - 1) / 2.0, (h - 1) / 2.0
    sx = sy = 0.0
    n = 0
    for rr in range(int(cx * 0.55), int(cx * 0.95), 2):
        for deg in range(720):
            t = deg * math.pi / 360
            x, y = cx + rr * math.sin(t), cy - rr * math.cos(t)
            if not (0 <= x < w and 0 <= y < h):
                continue
            r, g, b, a = px[int(x), int(y)]
            if (a > 200 and 90 < r < 175 and 100 < g < 185
                    and b < 110 and g > b + 30):
                sx += math.sin(math.radians(deg / 2.0))
                sy += math.cos(math.radians(deg / 2.0))
                n += 1
    if not n:
        return None
    return math.degrees(math.atan2(sx, sy)) % 360.0


def wedge_angles(im):
    """Where each colour wedge's centre sits, swept off the art."""
    w, h = im.size
    px = im.convert("RGBA").load()
    cx, cy = (w - 1) / 2.0, (h - 1) / 2.0
    acc = {}
    for deg in range(3600):
        a = deg / 10.0
        t = math.radians(a)
        for rf in (0.33, 0.36, 0.39, 0.42):
            x, y = cx + (w * rf) * math.sin(t), cy - (h * rf) * math.cos(t)
            if not (0 <= x < w and 0 <= y < h):
                continue
            r, g, b, al = px[int(x), int(y)]
            if al < 200:
                continue
            best, bd = None, 1e9
            for nm, (R, G, B) in WEDGE.items():
                dd = (r - R) ** 2 + (g - G) ** 2 + (b - B) ** 2
                if dd < bd:
                    best, bd = nm, dd
            if bd < 2500:
                acc.setdefault(best, []).append(a)
    out = {}
    for nm, angs in acc.items():
        sx = sum(math.sin(math.radians(x)) for x in angs)
        sy = sum(math.cos(math.radians(x)) for x in angs)
        out[nm] = math.degrees(math.atan2(sx, sy)) % 360.0
    return out


def write(which, im):
    buf = io.BytesIO()
    im.save(buf, "PNG", optimize=True)
    raw = buf.getvalue()
    out = "Chip_%s_%s.png" % (which, hashlib.md5(raw).hexdigest()[:8])
    # EXACTLY ONE OF EACH, which check_app_sync asserts - and the hash
    # is what stops a CDN or a TTS cache serving the superseded face.
    for old in os.listdir(IMAGES):
        if old.startswith("Chip_%s_" % which) and old != out:
            os.remove(os.path.join(IMAGES, old))
    io.open(os.path.join(IMAGES, out), "wb").write(raw)
    return out


def main():
    """Draw both faces, and refuse to write one that is out of true.

    WHAT THIS CANNOT CATCH is ART_OFFSET being wrong: the wedges are
    drawn from it and then checked against it, so the two agree
    however wrong the number is. check_app_sync.py keeps its own copy
    of the 197 and measures the finished picture, which is the check
    that would fail - verified by drawing the wheel 10 degrees out
    and watching it do so.
    """
    seg, mark, _slots = consts()
    col = colour_face()
    got = wedge_angles(col)
    bad = [(c, round(got.get(c, -1), 1), (a + ART_OFFSET) % 360)
           for c, a in sorted(seg.items())
           if c not in got
           or min((got[c] - (a + ART_OFFSET)) % 360,
                  ((a + ART_OFFSET) - got[c]) % 360) > 1.0]
    if bad:
        raise SystemExit("wedges are off their CHIP_SEGMENT angles: %r" % bad)
    print("  wedges  " + ", ".join(
        "%s %.1f" % (c, got[c]) for c in sorted(got)))

    dial = dial_face()
    at_deg = marker_angle(dial)
    if at_deg is None or abs(at_deg - mark) > 1.0:
        raise SystemExit("the marker came out at %r, CHIP_DIAL_MARK is %s"
                         % (at_deg, mark))
    print("  marker  %.1f, CHIP_DIAL_MARK %s" % (at_deg, mark))
    print("  wrote " + write("Colour", col))
    print("  wrote " + write("Dial", dial))


if __name__ == "__main__":
    main()
