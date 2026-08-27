"""Blank cover cards for the AoS Program and Advanced Program decks.

Those decks are genuinely two-sided (Stable face / Overheated back), so a
face-down deck still shows a real card. These covers sit on top to hide it.

Standalone: needs only pillow, not the WeasyPrint toolchain the other
generators use. Writes straight into ../images.

    python build_covers.py
"""
import os
from PIL import Image, ImageDraw, ImageFont

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, "images")

W, H = 500, 700                      # matches every other portrait card back
BG = (47, 89, 102)                   # AoS teal, sampled from CardBack_AoS_Limitation
TITLE = (255, 255, 255)
LABEL = (213, 221, 224)
MUTED = (116, 144, 153)

# Band geometry, measured off CardBack_AoS_Limitation.png so the covers sit in
# the same family as the rest of the deck backs.
TITLE_TOP, TITLE_CAP = 286, 34       # "AoS"
LABEL_TOP, LABEL_CAP = 345, 15       # deck name, letter-spaced
RULE_Y, RULE_W, RULE_H = 384, 174, 2
FOOT_TOP, FOOT_CAP, FOOT_W = 407, 12, 200

FONT = r"C:\Windows\Fonts\arialbd.ttf"


def fit(cap_px):
    """Font whose cap height is cap_px, found by measurement not by guessing."""
    for size in range(8, 120):
        f = ImageFont.truetype(FONT, size)
        if f.getbbox("H")[3] - f.getbbox("H")[1] >= cap_px:
            return f
    raise RuntimeError("no font size reached cap height %d" % cap_px)


def spaced(draw, text, font, top, colour, target_w=None, max_w=430):
    """Draw letter-spaced text centred on the card.

    target_w stretches the tracking to a measured width; it is clamped so a
    long label cannot run off the card edge.
    """
    widths = [font.getbbox(c)[2] - font.getbbox(c)[0] for c in text]
    base = sum(widths)
    gaps = max(len(text) - 1, 1)
    track = 0.0
    if target_w:
        track = (min(target_w, max_w) - base) / gaps
        track = max(track, 0.0)
    total = base + track * gaps
    if total > max_w:                       # too wide even with no tracking
        return spaced(draw, text, fit(font.size * max_w / total), top, colour,
                      None, max_w)
    x = (W - total) / 2.0
    for c, w in zip(text, widths):
        draw.text((x - font.getbbox(c)[0], top - font.getbbox("H")[1]), c,
                  font=font, fill=colour)
        x += w + track


def cover(label, filename):
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)

    f_title = fit(TITLE_CAP)
    tw = d.textlength("AoS", font=f_title)
    d.text(((W - tw) / 2, TITLE_TOP - f_title.getbbox("H")[1]), "AoS",
           font=f_title, fill=TITLE)

    spaced(d, label, fit(LABEL_CAP), LABEL_TOP, LABEL, target_w=141 + 14 * len(label))
    d.rectangle([(W - RULE_W) // 2, RULE_Y,
                 (W + RULE_W) // 2, RULE_Y + RULE_H - 1], fill=MUTED)
    spaced(d, "THE NOBULOUS SET", fit(FOOT_CAP), FOOT_TOP, MUTED, target_w=FOOT_W)

    path = os.path.normpath(os.path.join(OUT, filename))
    im.save(path)
    print("wrote", path, "%dx%d" % im.size)


# --- setup panel backdrop -------------------------------------------------
# The nameplate art is 2.83:1, so a tile using it has very little vertical
# room; buttons placed more than ~0.18 local from its centre fall off the
# plate. The setup wizard gets its own near-square surface instead.
PANEL_W, PANEL_H = 1400, 1400
PANEL_BG = (17, 15, 13)
PANEL_INNER = (26, 23, 20)
PANEL_GOLD = (212, 167, 44)


def setup_panel(filename="SetupPanel.png"):
    im = Image.new("RGB", (PANEL_W, PANEL_H), PANEL_BG)
    d = ImageDraw.Draw(im)
    m = 40
    d.rounded_rectangle([m, m, PANEL_W - m, PANEL_H - m], radius=34,
                        fill=PANEL_INNER, outline=PANEL_GOLD, width=6)
    f = fit(30)
    t = "SET UP A GAME"
    widths = [f.getbbox(c)[2] - f.getbbox(c)[0] for c in t]
    track = 14.0
    total = sum(widths) + track * (len(t) - 1)
    x = (PANEL_W - total) / 2.0
    for c, w in zip(t, widths):
        d.text((x - f.getbbox(c)[0], 96 - f.getbbox("H")[1]), c, font=f,
               fill=PANEL_GOLD)
        x += w + track
    path = os.path.normpath(os.path.join(OUT, filename))
    im.save(path)
    print("wrote", path, "%dx%d" % im.size)


def nameplate(filename="Nameplate.png"):
    """The nameplate plus room to put buttons under it.

    ControlPanel.png is 2.83:1, so a stretched tile using it has a local Z
    range of only about +/-0.18 -- a single shallow row. Padding it out to a
    gentler aspect gives the buttons a second row to sit on without changing
    the plate artwork itself.
    """
    plate = Image.open(os.path.normpath(os.path.join(OUT, "ControlPanel.png")))
    W = plate.width
    H = int(W / 1.23)                       # local z becomes about +/-0.41
    im = Image.new("RGB", (W, H), PANEL_BG)
    im.paste(plate.convert("RGB"), (0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([160, plate.height - 20, W - 160, H - 40], radius=28,
                        fill=PANEL_INNER, outline=PANEL_GOLD, width=4)
    path = os.path.normpath(os.path.join(OUT, filename))
    im.save(path)
    print("wrote", path, "%dx%d" % im.size)


def tracker(filename="Tracker.png"):
    """Two blank slots for the play tracker.

    The Workshop tracker this replaces had its labels painted into the image,
    which fixed it to one game. These slots are empty and the XML writes the
    labels, so the same tile reads Splices / Tyrant HP for BAT and Attempts /
    Suspicion for the Imposter. 3:1 keeps it shorter than a landscape card.
    """
    W, H = 1536, 512
    im = Image.new("RGB", (W, H), (8, 8, 8))
    d = ImageDraw.Draw(im)
    pad, gap = 26, 22
    slot_w = (W - pad * 2 - gap) // 2
    for i in range(2):
        x0 = pad + i * (slot_w + gap)
        d.rounded_rectangle([x0, pad, x0 + slot_w, H - pad], radius=26,
                            fill=(0, 0, 0), outline=(150, 150, 150), width=4)
    path = os.path.normpath(os.path.join(OUT, filename))
    im.save(path)
    print("wrote", path, "%dx%d" % im.size)


if __name__ == "__main__":
    cover("PROGRAM", "CardBack_AoS_Program.png")
    cover("ADVANCED PROGRAM", "CardBack_AoS_Advanced.png")
    setup_panel()
    nameplate()
    tracker()
