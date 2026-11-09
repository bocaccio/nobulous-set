"""Draw the TTS control-panel mat into images/ControlPanel.png.

    python3 make_panel.py

The mat was a hand-drawn PNG with no source, kept by name in deploy.py's
EXTRA_IMAGES so --prune could not remove it. It printed THE NOBULOUS SET
and three game names, every one of which the script then covered with
buttons - the title row was removed from the panel precisely because the
art already said it, and then the art was hidden anyway.

So it is a plain mat now: a dark rounded panel with a thin rule, no text.
The ASPECT IS LOAD-BEARING. The tile is "Stretch": true, so the image's
proportions ARE the tile's local space: 4.615 by 1 here, which is what
refreshPanel lays its five rows out inside and what check_app_sync.py
recomputes from this file. Change the shape and the buttons move - this
went from 1473 to 2000 to 2400 precisely to give the rows elbow room,
and every x in refreshPanel moved with it.
"""
import os

from PIL import Image, ImageDraw

W, H = 2400, 520
RADIUS = 46
BACK = (26, 23, 20)
EDGE = (92, 80, 62)
INNER = (38, 34, 29)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "images", "ControlPanel.png")


def main():
    im = Image.new("RGBA", (W * 2, H * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, W * 2 - 1, H * 2 - 1], RADIUS * 2, fill=BACK)
    d.rounded_rectangle([18, 18, W * 2 - 19, H * 2 - 19], RADIUS * 2 - 12,
                        fill=INNER)
    # One hairline inset, which is all the decoration a mat under four rows
    # of buttons can carry without showing between them.
    d.rounded_rectangle([34, 34, W * 2 - 35, H * 2 - 35], RADIUS * 2 - 24,
                        outline=EDGE, width=5)
    im = im.resize((W, H), Image.LANCZOS)
    im.convert("RGB").save(OUT, optimize=True)
    print("wrote %s  %dx%d" % (OUT, W, H))


if __name__ == "__main__":
    main()
