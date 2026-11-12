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
# ONE FELT, OR ONE PER GAME. Each game's overlay is its own tile in
# its own bag, so they CAN be different pictures - they were, for a
# while: gold for BAT, green for AoS, magenta for the Imposter
# scenario. Jon preferred the turquoise everywhere, so that is what
# they all use.
#
# A game still gets its own by having its own file. Drop a
# felt_AoS.jpg in beside this and AoS uses it; nothing here has to
# change, and nothing has to be remembered for the three that do
# not have one.
#
# THE SHAPE IS NOT A MATTER OF TASTE. The cover-and-crop onto the
# table keeps whatever fits and throws the rest away, so a source
# of a different shape loses a different amount: the gold arrived a
# fifth taller than the rest and its dark border landed somewhere
# else until it was cut to match. 1318 x 2000 is what they are.
FELT = os.path.join(HERE, "felt.jpg")
TEXTURE = dict(
    (g, os.path.join(HERE, "felt_%s.jpg" % g)
        if os.path.exists(os.path.join(HERE, "felt_%s.jpg" % g))
        else FELT)
    for g in ("BAT", "NAP", "AoS", "IMP"))
# Light lines for the transparent templates, which get painted over on
# whatever background you like; dark ones for the parchment, which they
# would otherwise vanish into.
PALE = {"ink": (235, 232, 224, 235), "snap": (235, 232, 224, 150),
        "text": (235, 232, 224, 170)}
# White on the table texture, which is dark: the parchment wanted dark
# ink and this one wants the opposite.
DARK = {"ink": (255, 255, 255, 235), "snap": (255, 255, 255, 180),
        "text": (255, 255, 255, 225)}
# AND DARK AGAIN FOR A LIGHT FELT. BAT's gold is bright through the
# middle where the others are not, and white lines disappear into it.
# Which ink a game gets is a property of its felt, so it is chosen here
# beside them rather than at each call - and chosen by MEASURING the
# felt rather than by eye, so a recoloured texture gets the right ink
# without anyone remembering to change it.
SEPIA = {"ink": (48, 30, 6, 245), "snap": (48, 30, 6, 205),
         "text": (48, 30, 6, 235)}


def ship_pen(game):
    """White on a dark felt, sepia on a light one."""
    im = Image.open(TEXTURE[game]).convert("L")
    w, h = im.size
    mid = [im.getpixel((x, y))
           for x in range(w // 4, 3 * w // 4, 40)
           for y in range(h // 4, 3 * h // 4, 40)]
    return dict(SEPIA if sum(mid) / float(len(mid)) > 140 else DARK)
PEN = dict(PALE)
LINE = 5
RADIUS = 14

GAMES = ("BAT", "NAP", "AoS", "IMP")

# Where the exhausted-dice corner has to stop on BAT, set by
# draw_bat from the script's own Chip position.
BAT_STOP = None
BAT_START = None


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


def table_texture(game="NAP"):
    """The supplied texture, trimmed, turned and cropped to the table."""
    im = trim_dark(Image.open(TEXTURE[game]).convert("RGB")).rotate(90, expand=True)
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


def draw_bat(d, lua):
    """BAT'S SPACES COME FROM THE SCRIPT, not from where it put cards.

    batBoxes() is the list the setup draws its own snap points from, so
    a box on the felt and a space you can drop onto cannot disagree -
    there is one of them. The Lab Rats and the two decks are
    deliberately absent: Jon asked for no outline under either, and a
    deck is a stack you can already see.
    """
    for b in lua.globals().batBoxes().values():
        card(d, float(b.x), float(b.z), float(b.hw), float(b.hd),
             PEN["snap"], 4)
    g = lua.globals()
    rx = lambda k: float(g.batRightX(k))
    rz = lambda r: float(g.batRowZ(r))
    half = float(g.BAT_BOX_HW)
    # The three rows on the right hold things you cannot tell apart by
    # looking at an empty space.
    # BY THE SCRIPT'S OWN COLUMNS, not by 1 and 2. These were
    # literals, so swapping the two in lua.lua moved the cards and
    # left the felt labelling the places they had come from. A mat
    # that lies is worse than a mat with no labels on it.
    label(d, "ATTACK\nDECK", rx(int(g.BAT_ATTACK_DECK)), rz(3),
          fit=half * 1.8)
    label(d, "TYRANT\nATTACK", rx(int(g.BAT_ATTACK_UP)), rz(3),
          fit=half * 1.8)
    label(d, "BUFF HP", rx(3), rz(3), fit=half * 1.8)
    label(d, "TYRANT\nSPLICES", rx(1), rz(4), fit=half * 1.8)
    # What the NRJ tiers put out and you keep in front of you: the
    # Tier I Protocol, and the six Tier III Research Notes as one
    # face-up stack rather than a row this table has no room for.
    label(d, "PROTOCOL", rx(int(g.BAT_PROTOCOL)), rz(1), fit=half * 1.8)
    label(d, "RESEARCH\nNOTES", rx(int(g.BAT_NOTES)), rz(1),
          fit=half * 1.8)
    # The two piles that fill every turn, past the three revealed
    # cards in the same row.
    label(d, "EXPERIMENT\nDISCARD", rx(int(g.BAT_EXP_DISCARD)), rz(2),
          fit=half * 1.8)
    label(d, "UPGRADE\nDISCARD", rx(int(g.BAT_UPG_DISCARD)), rz(2),
          fit=half * 1.8)
    # The Tyrant's own dice, two columns wide over the Splices.
    label(d, "TYRANT DICE",
          rx(int(g.BAT_TYRANT_DICE)) + float(g.BAT_COL) / 2, rz(3),
          fit=float(g.BAT_WIDE_HW) * 1.8)
    # Dice that are out of the game, in the corner the grid leaves.
    # Drawn as a card space, because that is what it is now.
    bx0, bx1, bzt, bzb = [float(v) for v in g.batBanished().values()]
    bcx, bcz = (bx0 + bx1) / 2.0, (bzt + bzb) / 2.0
    card(d, bcx, bcz, (bx1 - bx0) / 2.0, (bzt - bzb) / 2.0, PEN["snap"], 4)
    label(d, "BANISHED\nDICE", bcx, bcz, fit=half * 1.8)
    # The Chip's own circle, the way NAP marks the dial's place, and
    # where the exhausted-dice corner has to stop to clear it.
    # WHERE THE EXHAUSTED CORNER STOPS AT EITHER END, read off the
    # script rather than guessed at here: its left edge lines up with
    # the second Splice - Jon's own call - and its right edge stops
    # short of the Health readout, which stands between it and the
    # Dial.
    global BAT_STOP, BAT_START
    BAT_START = float(g.BAT_EXHAUST_X0)
    BAT_STOP = float(g.BAT_EXHAUST_X1)
    # The readout's own plate, so the felt says where it belongs.
    card(d, float(g.BAT_READOUT_X), float(g.BAT_READOUT_Z),
         float(g.BAT_READOUT_HW), 0.95, PEN["snap"], 4)
    circle(d, float(g.BAT_CHIP_X), float(g.BAT_CHIP_Z), 1.1)


def draw_aos(d, lua):
    """AoS'S SPACES COME FROM THE SCRIPT, the way BAT's do.

    aosBoxes() is the list the setup makes its snap points from, so a
    box on the felt and a space you can drop onto cannot disagree.
    Everything is labelled except the five element mats, which say what
    they are on the card itself.
    """
    g = lua.globals()
    for b in g.aosBoxes().values():
        card(d, float(b.x), float(b.z), float(b.hw), float(b.hd),
             PEN["snap"], 4)
    col = lambda k: float(g.aosCol(k))
    r1, r3 = float(g.AOS_ROW1), float(g.AOS_ROW3)
    fit = float(g.AOS_BOX_HW) * 1.8
    label(d, "PROGRAM\nDECK", col(1), r1, fit=fit)
    label(d, "PROGRAM", col(2), r1, fit=fit)
    label(d, "LIMITATION\nDECK", col(3), r1, fit=fit)
    label(d, "LIMITATION", col(4), r1, fit=fit)
    label(d, "ADVANCED", float(g.AOS_RIGHT) - float(g.AOS_COL), r1, fit=fit)
    # The space a tier lays its one face-up card on, which is empty
    # and unexplained at tier 0.
    label(d, "TIER CARD", float(g.AOS_RIGHT), r1, fit=fit)
    label(d, "DISCARD", col(int(g.AOS_DISCARD)), r1, fit=fit)
    label(d, "SET ASIDE", float(g.AOS_TECH_X), r3, fit=fit)
    label(d, "BANISHED\nDICE", float(g.AOS_RIGHT), r3, fit=fit)


def draw_game(d, which, slots_out=None):
    fp, snaps, w, lua = places_for(which)
    if which == "BAT":
        draw_bat(d, lua)
        return fp
    if which == "AoS":
        draw_aos(d, lua)
        return fp
    # NAP OUTLINES WHERE YOU PUT THINGS, NOT WHERE THE GAME PUTS THEM.
    # A box under the Time Slot, the Assignment deck, the Apprentice or
    # the FINF card only draws a line round a card that is already
    # there. The other three games have no snap points, so for them the
    # card places are all there is to show.
    # NO OUTLINE UNDER THE CHARACTER. Jon asked for none under BAT's
    # Lab Rats and none under the Imposter; the card is the only thing
    # that ever stands there, so a box round it draws a line nobody
    # needs and the stat dice under it have nothing to do with it.
    bare = ()
    if which == "IMP":
        one = str(lua.globals().CARD_NAME["Imposters (A / B)"])
        bare = (one, "Imposters (A / B)")
    if which != "NAP":
        for name, x, z, hw, hd in fp:
            if name.rstrip("0123456789").strip() in bare:
                continue
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
    # THE CHIP'S THREE SNAPS ARE NOT CARD SPACES. Every other NAP
    # snap is somewhere a card goes and is drawn as a card-shaped box;
    # these are drawn as circles below, and a box over a circle reads
    # as a space for something that never stands there.
    chips = [(x - hw - 1.9, z) for name, x, z, hw, hd in fp
             if which == "NAP" and name.startswith("Time Slot")]
    for sx, sz in snaps:
        if any(abs(sx - cx) < 0.3 and abs(sz - cz) < 0.3
               for cx, cz in chips):
            continue
        card(d, sx, sz, half, cw, PEN["snap"], 4)
    if which == "NAP":
        # The two piles down the right are the only places on this table
        # whose contents a player cannot guess from what is in them.
        slots = sorted([f[2] for f in fp if f[0].startswith("Time Slot")],
                       reverse=True)
        gl = lua.globals()
        if len(slots) >= 3:
            label(d, "COMPLETED\nCREDITS", float(gl.PILE_X), slots[1],
                  fit=half * 1.8)
            label(d, "COMPLETED\nOPPORTUNITIES", float(gl.PILE_X), slots[2],
                  fit=half * 1.8)
        # The Assignment you did not take, past the two you revealed.
        label(d, "DISCARD", float(gl.NAP_DISCARD_X), float(gl.ROW_CHAR),
              fit=half * 1.8)
    # The Chip goes beside a Time Slot, so give it a circle there.
    for cx, cz in chips:
        circle(d, cx, cz, 1.1)
        if slots_out is not None:
            slots_out.append((cx, cz))
    return fp


def frame(d, game=None):
    """The exhausted-dice corner. The dice themselves are not outlined:
    they are loose things that move, and drawing a box round each one
    only clutters a background that has to sit under them.

    IT STOPS SHORT ON BAT, because BAT's Chip stands below the
    rightmost Splice and the corner would otherwise be drawn straight
    through it. There is nowhere else for either to go: the bottom band
    is the only clear strip left once four rows of cards are down."""
    x0, x1, zt, zb = EXHAUSTED
    if game == "BAT" and BAT_STOP is not None:
        x0, x1 = BAT_START, BAT_STOP
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
        slots = []
        # DRAWN FIRST, because BAT's spaces are what tell the corner
        # where to stop.
        draw_game(d, game, slots)
        frame(d, game)
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
    for game in GAMES:
        globals()["PEN"] = ship_pen(game)
        ship_im = table_texture(game)
        sd = ImageDraw.Draw(ship_im)
        # DRAWN FIRST, because BAT's spaces are what tell the corner
        # where to stop.
        draw_game(sd, game, [])
        frame(sd, game)
        buf = io.BytesIO()
        ship_im.convert("RGB").save(buf, "JPEG", quality=88, optimize=True)
        raw = buf.getvalue()
        name = "%s_Table_%s.jpg" % (game, hashlib.md5(raw).hexdigest()[:8])
        for old in os.listdir(img):
            if old.startswith("%s_Table" % game) and old != name:
                os.remove(os.path.join(img, old))
        ship = os.path.join(img, name)
        io.open(ship, "wb").write(raw)
        wrote.append(ship)
    PEN = dict(PALE)
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
