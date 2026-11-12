# -*- coding: utf-8 -*-
"""Draw the save thumbnail Tabletop Simulator shows in its Saves list.

    python3 make_cover.py            -> tts/cover.png
    python3 make_cover.py --install  -> ...and into the Saves folder

TTS SHOWS THE PNG SITTING BESIDE THE SAVE. Every save in the folder
has one - NobulousSet.json and NobulousSet.png - and TTS writes its
own 256x256 grab of the table whenever you save over it. Ours is
drawn instead, so the mod is recognisable in a list of saves before
anything has been set up, and so it says which four games are in it.

It is deliberately NOT a picture of the table. A 256px screenshot of
a table this wide is twenty illegible rectangles; the card backs in
this set are type on flat colour and nothing else, so the cover is
the same thing.

The gears are the unit dice's own, drawn by make_dice, in the five
die colours and carrying each colour's real tooth count - so the
cover states the ladder that the dice state: yellow 2 through red 6.
"""
import io
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from PIL import Image, ImageDraw

import glyphs
import make_dice

SIDE = 256
SS = 4
FONT = os.path.join(ROOT, "fonts", "DejaVuSans-Bold.ttf")
DARK = (36, 31, 26)              # #241f1a, the Final Exam card back
CREAM = (245, 242, 232)          # the card stock
MUTED = (150, 142, 126)
SAVES = os.path.join(os.path.expanduser("~"), "Documents", "My Games",
                     "Tabletop Simulator", "Saves")


# WHICH NAME SITS ON WHICH EDGE, Jon's placing rather than the order
# the boxes sit in. Named here instead of zipped against a tuple of
# sides, so moving one is moving one.
GAMES = [("BAT", "Build-a-Tyrant", "left"),
         ("NAP", "Nobulous Apprenticeship Program", "top"),
         ("AoS", "Automaton of Shale", "right"),
         ("NRJ", "Nobulous Research Journal", "bottom")]
EDGE_INSET = 7           # border to ink, once the tile is cropped
EDGE_MARGIN = 20         # clear of the corners, so four lines do not meet


def spaced(d, text, y, px, fill, track):
    """One centred line, letterspaced, the way the card backs set it.

    glyphs.draw_text lays a whole string at once and applies no
    tracking, and these titles are three words of caps that want
    some - so the line is drawn a character at a time and measured
    the same way.
    """
    widths = [glyphs.text_size(ch, px, FONT)[0] for ch in text]
    total = sum(widths) + track * (len(text) - 1)
    x = SIDE / 2.0 - total / 2.0
    for ch, w in zip(text, widths):
        if ch != " ":
            glyphs.draw_text(d, (x, y), ch, px, fill, FONT)
        x += w + track


def line_px(text, px, track):
    """Width of one letterspaced line."""
    w = [glyphs.text_size(ch, px, FONT)[0] for ch in text]
    return sum(w) + track * (len(text) - 1), w


def edge_size(track):
    """One type size for all four names, set by the longest.

    Fitting each name to its own edge would give four sizes - a
    fourteen-character edge in large caps opposite a thirty-one
    character one in small - and a frame of four names has to read
    as one frame.
    """
    run = SIDE - 2 * EDGE_MARGIN
    px = 12.0
    while px > 4.0:
        if max(line_px(n, px, track)[0] for _, n, _s in GAMES) <= run:
            return px
        px -= 0.25
    return px


def edge(im, text, side, px, track, fill):
    """One name along one edge, reading clockwise from the top.

    Drawn flat into its own tile and turned, because a letterspaced
    line is laid out a character at a time and rotating each glyph
    would scatter them.
    """
    w, widths = line_px(text, px, track)
    tile = Image.new("RGBA", (int(w) + 8, int(px * 1.9) + 8), (0, 0, 0, 0))
    x = 4.0
    base = px * 1.35
    for ch, cw in zip(text, widths):
        if ch != " ":
            glyphs.draw_text(tile, (x, base), ch, px, fill, FONT)
        x += cw + track
    # THE BOTTOM READS THE RIGHT WAY UP. Running the frame strictly
    # clockwise turns it through 180 and nobody reads a cover upside
    # down; the two verticals turn, the two horizontals do not.
    # CROPPED TO THE INK FIRST. The tile is built with a baseline a
    # third of its height down and slack above and below, so placing
    # the TILE at the inset left the TEXT a good deal further in -
    # and by different amounts on the horizontals and the verticals,
    # which is why the frame looked loose and uneven. Cropped, the
    # inset is the real distance from the border to the letters.
    hit = tile.getbbox()
    if hit:
        tile = tile.crop(hit)
    tile = tile.rotate({"top": 0, "right": -90, "bottom": 0,
                        "left": 90}[side], expand=True)
    tw, th = tile.size
    pos = {"top": ((SIDE - tw) // 2, EDGE_INSET),
           "bottom": ((SIDE - tw) // 2, SIDE - EDGE_INSET - th),
           "left": (EDGE_INSET, (SIDE - th) // 2),
           "right": (SIDE - EDGE_INSET - tw, (SIDE - th) // 2)}[side]
    im.alpha_composite(tile, pos)


def cover():
    im = Image.new("RGBA", (SIDE, SIDE), DARK + (255,))

    # The five gears, in a row across the middle, each with its own
    # colour's tooth count.
    teeth = make_dice.unit_teeth()
    order = [n for n, _ in make_dice.UNIT][::-1]      # yellow .. red
    cell = 44
    y = 150
    x0 = SIDE / 2.0 - (len(order) * cell) / 2.0 + cell / 2.0
    big = Image.new("RGBA", (SIDE * SS, SIDE * SS), (0, 0, 0, 0))
    gd = ImageDraw.Draw(big)
    for i, name in enumerate(order):
        cx = (x0 + i * cell) * SS
        cy = y * SS
        r_out = 17.0 * SS
        r_root = r_out - 17.0 * SS * (make_dice.DEPTH / 0.383)
        r_in = r_root - 17.0 * SS * (0.085 / 0.383)
        col = dict(make_dice.UNIT)[name]
        gd.polygon(make_dice.gear(cx, cy, r_out, r_root, teeth[name]),
                   fill=col + (255,))
        gd.ellipse([cx - r_in, cy - r_in, cx + r_in, cy + r_in],
                   fill=DARK + (255,))
    im.alpha_composite(big.resize((SIDE, SIDE), Image.LANCZOS))

    spaced(im, "THE", 70, 15, MUTED, 5.0)
    # 27, not 30: at 30 the word runs within a few pixels of the two
    # vertical names and the frame closes in on the title.
    spaced(im, "NOBULOUS", 107, 27, CREAM, 2.0)
    spaced(im, "SET", 134, 15, MUTED, 5.0)

    # THE FOUR GAMES AROUND THE EDGE, spelled out. The three-letter
    # codes are what the set calls them everywhere else, and they
    # tell a stranger nothing; a cover has room to say them once.
    # Clockwise from the top, in the order the boxes sit on the
    # table.
    track = 1.4
    px = edge_size(track)
    for _code, name, side in GAMES:
        edge(im, name.upper(), side, px, track, MUTED)
    return im.convert("RGB")


def main():
    im = cover()
    out = os.path.join(HERE, "cover.png")
    im.save(out)
    print("  wrote %s  %dx%d" % (os.path.relpath(out, ROOT), *im.size))
    if "--install" in sys.argv:
        if not os.path.isdir(SAVES):
            raise SystemExit("no Saves folder at %s" % SAVES)
        dst = os.path.join(SAVES, "NobulousSet.png")
        shutil.copyfile(out, dst)
        print("  installed %s" % dst)


if __name__ == "__main__":
    main()
