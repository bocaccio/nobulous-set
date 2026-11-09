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

The felt is about 56 by 37.6 units. At 50 px per unit that is a
2800 x 1880 image, with world x -28 on the left edge and world z +19 at
the top - TTS's +z runs away from the player, which is up on the page.
"""
import io
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import test_setup as T                                   # noqa: E402
from build_mod import EXHAUSTED                          # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "templates")

PX = 50.0                     # pixels per table unit
X0, X1 = -28.0, 28.0
Z0, Z1 = 19.0, -18.6          # top, bottom
W = int((X1 - X0) * PX)
H = int((Z0 - Z1) * PX)

FONT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "fonts", "DejaVuSans-Bold.ttf")

INK = (235, 232, 224, 235)    # card outlines
SNAP = (235, 232, 224, 150)   # the spaces you drop a card into
DICE = (235, 232, 224, 120)
BACK = (0, 0, 0, 0)           # transparent: this is an overlay
LINE = 5
RADIUS = 14

GAMES = ("BAT", "NAP", "AoS", "IMP")


def px(x, z):
    return ((x - X0) * PX, (Z0 - z) * PX)


def card(d, x, z, hw, hd, ink=INK, width=LINE):
    a = px(x - hw, z + hd)
    b = px(x + hw, z - hd)
    d.rounded_rectangle([a[0], a[1], b[0], b[1]], RADIUS, outline=ink,
                        width=width)


def label(d, text, x, z, size=34, ink=(235, 232, 224, 170)):
    """Centred text, for the boxes whose contents are not obvious."""
    try:
        f = ImageFont.truetype(FONT, size)
    except Exception:
        f = ImageFont.load_default()
    cx, cy = px(x, z)
    box = d.textbbox((0, 0), text, font=f)
    d.text((cx - (box[2] - box[0]) / 2.0, cy - (box[3] - box[1]) / 2.0),
           text, font=f, fill=ink)


def circle(d, x, z, r, ink=INK, width=LINE):
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
    lua = None
    for alive in reversed(T.ALIVE):
        if alive[1] is w:
            lua = alive[0]
            break
    return T.footprints(w, lua), list(w.snaps), w


def draw_game(d, which, slots_out=None):
    fp, snaps, w = places_for(which)
    for name, x, z, hw, hd in fp:
        card(d, x, z, hw, hd)
    cw, cl = fp[0][3], fp[0][4]
    for sx, sz in snaps:
        # A snap point holds one landscape card.
        card(d, sx, sz, max(cw, cl), min(cw, cl), SNAP, 4)
    if which == "NAP":
        # The two piles down the right are the only places on this table
        # whose contents a player cannot guess from what is in them.
        slots = sorted([f[2] for f in fp if f[0].startswith("Time Slot")],
                       reverse=True)
        if len(slots) >= 3:
            label(d, "COMPLETED CREDITS", 23.5, slots[1])
            label(d, "DEVIOUS OPPORTUNITIES", 23.5, slots[2], 28)
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
                        outline=(235, 232, 224, 110), width=4)
    label(d, "EXHAUSTED DICE", (x0 + x1) / 2.0, (zt + zb) / 2.0)


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
    ship = os.path.join(os.path.dirname(HERE), "images", "NAP_Table.png")
    Image.open(os.path.join(OUT, "table_NAP.png")).save(ship)
    wrote.append(ship)
    print("%d x %d at %g px per unit, world x %g..%g, z %g..%g"
          % (W, H, PX, X0, X1, Z1, Z0))
    for p in wrote:
        print("  wrote", os.path.relpath(p, os.path.dirname(HERE)))


if __name__ == "__main__":
    main()
