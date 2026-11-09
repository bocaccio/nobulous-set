"""Draw the table layout as PNG templates, to paint a background over.

    python3 make_template.py          -> tts/templates/*.png

One image per game plus one of everything together, all at the same
scale and registration, so they can be stacked as layers.

WHERE THE POSITIONS COME FROM. Not from a list kept here - from running
the mod. test_setup.py already embeds the real lua.lua and a stub of the
TTS object API, so this presses each setup button and draws what the
script actually dealt: card footprints, the snap points beside the Time
Slots, and the dice out of the built save. A template that was typed out
separately would be wrong the first time a row moved, and it would be
wrong silently, which is the whole problem this repo keeps having with
numbers written down twice.

THE FELT IS WHAT BUILD_MOD SAYS IT IS - 56.5 by 36.1, x +/-28.25 and
z -18.21 to 17.89 - because that is what Jon sized the mat to at the
table. At 50 px per unit the image is 2825 x 1805, drawn with world x
-28.25 on the left edge and world z 17.89 at the top; TTS's +z runs
away from the player, which is up on the page.

Getting that rectangle right is not cosmetic. The mat is stretched over
it, so a picture drawn for a different one puts every printed box
somewhere the cards are not - which is exactly what happened when the
mat was widened to the table and the drawing was not redrawn to match.

TEXT IS DRAWN FROM GLYPH OUTLINES (tts/glyphs.py), not by Pillow:
Windows Smart App Control blocks Pillow's unsigned text DLL on this
machine, and without this module the overlay could not be redrawn at
all.
"""
import hashlib
import io
import json
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import glyphs                                            # noqa: E402
import test_setup as T                                   # noqa: E402
from build_mod import (EXHAUSTED, FELT_X0, FELT_X1,      # noqa: E402
                       FELT_Z0, FELT_Z1)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "templates")

PX = 50.0                     # pixels per table unit
X0, X1 = FELT_X0, FELT_X1
Z0, Z1 = FELT_Z1, FELT_Z0     # top, bottom
W = int(round((X1 - X0) * PX))
H = int(round((Z0 - Z1) * PX))

FONT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "fonts", "DejaVuSans-Bold.ttf")

INK = (235, 232, 224, 235)    # card outlines
SNAP = (235, 232, 224, 150)   # the spaces you drop a card into
DICE = (235, 232, 224, 120)
BACK = (0, 0, 0, 0)           # transparent, for painting over
# TTS DOES NOT HONOUR A TILE'S ALPHA: a transparent PNG on a Custom_Tile
# comes out black, which is what the first overlay did to the table. So
# the copy that ships needs a background of its own - this one, which
# Jon supplied. It arrives portrait and is turned, scaled to cover and
# cropped from the middle.
TEXTURE = os.path.join(HERE, "table_texture.png")
# Light lines for the transparent templates, which get painted over on
# whatever background you like; dark ones for the parchment, which they
# would otherwise vanish into.
PALE = {"ink": (235, 232, 224, 235), "snap": (235, 232, 224, 150),
        "text": (235, 232, 224, 170)}
# White on the table texture, which is dark: the parchment wanted dark
# ink and this one wants the opposite.
DARK = {"ink": (255, 255, 255, 235), "snap": (255, 255, 255, 180),
        "text": (255, 255, 255, 225)}
PEN = dict(PALE)
LINE = 5
RADIUS = 14

GAMES = ("BAT", "NAP", "AoS", "IMP")


def px(x, z):
    return ((x - X0) * PX, (Z0 - z) * PX)


def trim_dark(im, floor=28):
    """Cut the near-black border off a scanned texture.

    The supplied parchment has black edges. Turned and cropped to the
    table they landed down the right-hand side as a band, which looks
    like a bug in the overlay rather than the edge of a photograph.
    """
    g = im.convert("L")
    w, h = g.size
    rows = [sum(g.getpixel((x, y)) for x in range(0, w, 7)) / float(len(range(0, w, 7)))
            for y in range(h)]
    cols = [sum(g.getpixel((x, y)) for y in range(0, h, 7)) / float(len(range(0, h, 7)))
            for x in range(w)]
    top = next((i for i, v in enumerate(rows) if v > floor), 0)
    bot = next((i for i, v in enumerate(reversed(rows)) if v > floor), 0)
    left = next((i for i, v in enumerate(cols) if v > floor), 0)
    right = next((i for i, v in enumerate(reversed(cols)) if v > floor), 0)
    return im.crop((left, top, w - right, h - bot))


def table_texture():
    """The supplied texture, trimmed, turned and cropped to the table."""
    im = trim_dark(Image.open(TEXTURE).convert("RGB")).rotate(90, expand=True)
    scale = max(W / float(im.width), H / float(im.height))
    im = im.resize((int(im.width * scale + 0.5), int(im.height * scale + 0.5)),
                   Image.LANCZOS)
    left = (im.width - W) // 2
    top = (im.height - H) // 2
    return im.crop((left, top, left + W, top + H)).convert("RGBA")


def card(d, x, z, hw, hd, ink=None, width=LINE):
    ink = ink if ink is not None else PEN["ink"]
    a = px(x - hw, z + hd)
    b = px(x + hw, z - hd)
    d.rounded_rectangle([a[0], a[1], b[0], b[1]], RADIUS, outline=ink,
                        width=width)


# ONE SIZE FOR ALL THREE BOX LABELS. They name the same kind of thing -
# a box - so they are set from one constant rather than from a number
# chosen per box, and main() checks they really do come out equal:
# `fit` can shrink one of them below it.
LABEL_PT = 34

# What size each label was actually drawn at, so main() can check.
DREW = []


def label(d, text, x, z, size=LABEL_PT, ink=None, fit=None):
    """Centred text, for the boxes whose contents are not obvious.

    MEASURED AND SHRUNK TO FIT. Chosen by eye, 34pt ran COMPLETED
    CREDITS out of its box and off the right-hand edge of the image -
    the labels that need one are the two furthest right, so guessing a
    size that works is guessing twice. `fit` is the width to stay
    inside, in table units.
    """
    ink = ink if ink is not None else PEN["text"]
    lines = text.split("\n")
    for pt in range(size, 9, -2):
        widest = max(glyphs.text_size(ln, pt, FONT)[0] for ln in lines)
        if fit is None or widest <= fit * PX:
            break
    cx, cy = px(x, z)
    step = pt * 1.25
    cap = max(glyphs.text_size(ln, pt, FONT)[1] for ln in lines)
    top = cy - step * (len(lines) - 1) / 2.0
    for i, ln in enumerate(lines):
        w = glyphs.text_size(ln, pt, FONT)[0]
        # draw_text takes a LEFT BASELINE, so half the cap height puts
        # the line's middle on the row rather than its feet.
        # d._image is the Image the caller handed ImageDraw; glyphs
        # composites onto it directly, which an ImageDraw cannot do.
        glyphs.draw_text(d._image, (cx - w / 2.0, top + i * step + cap / 2.0),
                         ln, pt, ink, FONT)
    DREW.append((lines[0], pt))


def circle(d, x, z, r, ink=None, width=LINE):
    ink = ink if ink is not None else PEN["ink"]
    a = px(x - r, z + r)
    b = px(x + r, z - r)
    d.ellipse([a[0], a[1], b[0], b[1]], outline=ink, width=width)


def dice_places():
    """Every die and token in the built save, as (x, z)."""
    save = json.load(io.open(os.path.join(HERE, "NobulousSet.json"),
                             encoding="utf-8"))
    return [(o["Transform"]["posX"], o["Transform"]["posZ"])
            for o in save["ObjectStates"]
            if o["Name"] in ("Custom_Dice", "Custom_Token")]


def runtime_for(w):
    for alive in reversed(T.ALIVE):
        if alive[1] is w:
            return alive[0]
    return None


def places_for(which, difficulty="Standard", tier=3):
    """Run the setup and report what it put on the table.

    Tier III on purpose: it deals everything the lower tiers do and more,
    so a template drawn from it has a space for every card that can
    appear.
    """
    w, g = T.start(difficulty, tier, T.Panel())
    {"BAT": g.setupBAT, "NAP": g.setupNAP,
     "AoS": g.setupAoS, "IMP": g.setupImposter}[which]()
    T.drain(w)
    lua = runtime_for(w)
    return T.footprints(w, lua), list(w.snaps), w, lua


def draw_game(d, which, slots_out=None):
    fp, snaps, w, lua = places_for(which)
    # NAP OUTLINES WHERE YOU PUT THINGS, NOT WHERE THE GAME PUTS THEM.
    # A box under the Time Slot, the Assignment deck, the Apprentice or
    # the FINF card only draws a line round a card that is already
    # there. The other three games have no snap points, so for them the
    # card places are all there is to show.
    if which != "NAP":
        for name, x, z, hw, hd in fp:
            card(d, x, z, hw, hd)
    cw = cl = None
    for name, x, z, hw, hd in fp:
        cw, cl = min(hw, hd), max(hw, hd)
        break
    # A SPACE IS AS WIDE AS THE PITCH, NOT AS WIDE AS A CARD. The
    # columns are 8.5 apart and a landscape card is 8.71 across, so
    # boxes drawn card-wide overlapped their neighbours all down the
    # table. The card overhangs its space by a tenth instead.
    half = cl
    if lua is not None:
        try:
            half = (float(lua.globals().ASSIGN_PITCH) - 0.3) / 2.0
        except Exception:
            pass
    for sx, sz in snaps:
        card(d, sx, sz, half, cw, PEN["snap"], 4)
    if which == "NAP":
        # The two piles down the right are the only places on this table
        # whose contents a player cannot guess from what is in them.
        slots = sorted([f[2] for f in fp if f[0].startswith("Time Slot")],
                       reverse=True)
        if len(slots) >= 3:
            label(d, "COMPLETED\nCREDITS", 23.5, slots[1],
                  fit=half * 1.8)
            label(d, "DEVIOUS\nOPPORTUNITIES", 23.5, slots[2],
                  fit=half * 1.8)
    # The Chip goes beside a Time Slot, so give it a circle there.
    if which == "NAP" and slots_out is not None:
        for name, x, z, hw, hd in fp:
            if name.startswith("Time Slot"):
                circle(d, x - hw - 1.9, z, 1.1)
                slots_out.append((x - hw - 1.9, z))
    return fp


def frame(d):
    """The exhausted-dice corner. The dice themselves are not outlined:
    they are loose things that move, and drawing a box round each one
    only clutters a background that has to sit under them."""
    x0, x1, zt, zb = EXHAUSTED
    a, b = px(x0, zt), px(x1, zb)
    d.rounded_rectangle([a[0], a[1], b[0], b[1]], RADIUS * 2,
                        outline=PEN["snap"], width=4)
    label(d, "EXHAUSTED DICE", (x0 + x1) / 2.0, (zt + zb) / 2.0,
          fit=(x1 - x0) * 0.8)


def main():
    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    wrote = []
    combined = Image.new("RGBA", (W, H), BACK)
    cd = ImageDraw.Draw(combined)
    frame(cd)
    for game in GAMES:
        im = Image.new("RGBA", (W, H), BACK)
        d = ImageDraw.Draw(im)
        frame(d)
        slots = []
        draw_game(d, game, slots)
        draw_game(cd, game, [])
        p = os.path.join(OUT, "table_%s.png" % game)
        im.save(p)
        wrote.append(p)
    p = os.path.join(OUT, "table_all.png")
    combined.save(p)
    wrote.append(p)
    # NAP's is not just a drawing aid: the mod lays it on the table, so
    # it goes to images/ with the card sheets and is served from there.
    # The shipped overlay is drawn AGAIN, in dark ink on the parchment:
    # the pale lines of the painting template disappear into it.
    global PEN
    PEN = dict(DARK)
    ship_im = table_texture()
    sd = ImageDraw.Draw(ship_im)
    frame(sd)
    draw_game(sd, "NAP", [])
    PEN = dict(PALE)
    # JPEG, NOT PNG: the texture is a photograph, so PNG made this 7.2
    # MB where a JPEG is a fifteenth of that.
    #
    # AND NAMED AFTER ITS OWN CONTENTS. jsDelivr twice went on serving
    # a superseded overlay with the purge endpoint reporting success,
    # and TTS cached what jsDelivr gave it, so the table showed an
    # image that had not existed for hours. A name containing the hash
    # of the bytes cannot have a stale copy anywhere: changed contents
    # mean a URL nobody has ever asked for.
    img = os.path.join(os.path.dirname(HERE), "images")
    buf = io.BytesIO()
    ship_im.convert("RGB").save(buf, "JPEG", quality=88, optimize=True)
    raw = buf.getvalue()
    name = "NAP_Table_%s.jpg" % hashlib.md5(raw).hexdigest()[:8]
    for old in os.listdir(img):
        if old.startswith("NAP_Table") and old != name:
            os.remove(os.path.join(img, old))
    ship = os.path.join(img, name)
    io.open(ship, "wb").write(raw)
    wrote.append(ship)
    # AND THEY REALLY ARE ONE SIZE. `fit` shrinks a label that would
    # run out of its box, so asking for LABEL_PT is not the same as
    # getting it. This fails the build rather than shipping a picture
    # whose three box labels disagree by two points.
    sizes = sorted(set(pt for _, pt in DREW))
    assert len(sizes) == 1, "box labels came out at %r: %r" % (sizes, DREW)
    print("  %d box labels, all at %dpt" % (len(DREW), sizes[0]))
    print("%d x %d at %g px per unit, world x %g..%g, z %g..%g"
          % (W, H, PX, X0, X1, Z1, Z0))
    for p in wrote:
        print("  wrote", os.path.relpath(p, os.path.dirname(HERE)))


if __name__ == "__main__":
    main()
