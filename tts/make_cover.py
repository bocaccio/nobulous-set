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

    spaced(im, "THE", 58, 15, MUTED, 5.0)
    spaced(im, "NOBULOUS", 95, 30, CREAM, 2.0)
    spaced(im, "SET", 122, 15, MUTED, 5.0)
    d = ImageDraw.Draw(im)
    d.line([64, 190, SIDE - 64, 190], fill=MUTED, width=1)
    spaced(im, "BAT  NAP  AoS  NRJ", 215, 13, CREAM, 1.5)
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
