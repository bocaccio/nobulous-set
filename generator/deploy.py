"""Promote generator/out/ into the trees that ship, and cut the releases.

    python deploy.py                 # promote, and report anything stale
    python deploy.py --prune         # also delete the stale files
    python deploy.py --release       # also write release/tts and release/print

AGENTS.md: "images/ and the card/rule copies under playtest/dist/assets/ are
generated or deployment output. Do not treat copied assets as masters." Until
2026-10-31 nothing performed that copy, so it was done by hand, and the trees
drifted apart twice - once with images/ BEHIND playtest/dist/assets/, which is
the copy being ahead of the master, and once when a deck was renamed and its
old sheet stayed behind in every destination.

What goes where:

  images/                 every deck sheet and card back, plus ControlPanel.
                          This is what the TTS mod's BASE_URL serves.
  playtest/dist/assets/   the same sheets, plus the rule PDFs the lab links.
  print-and-play/         the four PnP PDFs and the contents file.

The set of sheets is not hardcoded: it is read out of the *_cards.json
manifests that render_deck writes, so a deck that is renamed, added or
dropped is picked up without editing this file. That is what makes --prune
safe, and --prune is what the rename of NRJ_NAP_ImpostorTasks needed.

The releases differ only in resolution, which is the whole reason to cut two:

  release/print/   300 DPI, exactly as rendered. The PnP PDFs, the rules, and
                   the full-size sheets for anyone cutting from the sheet.
  release/tts/     the same sheets scaled so neither side exceeds 4096 px.
                   Tabletop Simulator will not render more than that, so the
                   extra pixels are upload time and cache for nothing - a
                   10000 px NAP_Tasks sheet is 1000 px a card where TTS shows
                   about 400. The mod JSON and its image list go with them.
"""
import io
import json
import os
import shutil
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(HERE, "out")

IMAGES = os.path.join(ROOT, "images")
ASSETS = os.path.join(ROOT, "playtest", "dist", "assets")
PNP = os.path.join(ROOT, "print-and-play")
RULES = os.path.join(ROOT, "rules")
RELEASE = os.path.join(ROOT, "release")

# TTS will not render a texture larger than this on the hardware most people
# have, so a sheet above it costs upload and cache for pixels nobody sees.
TTS_MAX = 4096
# Sheets are big; Pillow's decompression-bomb guard is aimed at untrusted
# input and these are ours.
Image.MAX_IMAGE_PIXELS = None

# Lives in images/ and is NOT generated - the TTS control panel was drawn by
# hand. So it is kept rather than copied, and never pruned.
EXTRA_IMAGES = ("ControlPanel.png",)
# Lives in playtest/dist/assets but has no source in rules/ - left alone.
ASSET_KEEP = ("AoS_Full_Rules.pdf",)
GAMES = ("BAT", "NAP", "AoS", "NRJ")


def sheets():
    """Every PNG the decks need, read from the manifests render_deck wrote."""
    want = set()
    for f in sorted(os.listdir(OUT)):
        if not f.endswith("_cards.json"):
            continue
        d = json.load(io.open(os.path.join(OUT, f), encoding="utf-8"))
        want.add(d["sheet"])
        if d.get("backIsSheet"):
            want.add(d["sheet"].replace("_TTS.png", "_TTS_back.png"))
        elif isinstance(d.get("back"), list):
            # A sheet whose cards do not all share one back records them per
            # card. NAP_SlotsFINF is the only one, and its list is what the
            # two TTS decks over that sheet are cut to match.
            want.update(d["back"])
        elif d.get("back"):
            want.add(d["back"])
    return want


def copy(src, dst, report):
    """Copy only when the bytes differ, so a no-op deploy says so."""
    if not os.path.exists(src):
        report.append("MISSING SOURCE  %s" % os.path.relpath(src, ROOT))
        return 0
    if os.path.exists(dst) and (io.open(src, "rb").read()
                                == io.open(dst, "rb").read()):
        return 0
    shutil.copyfile(src, dst)
    report.append("  wrote  %s" % os.path.relpath(dst, ROOT))
    return 1


def prune(folder, keep, report, doit):
    """Anything in a destination that nothing produces any more."""
    gone = [f for f in sorted(os.listdir(folder))
            if os.path.isfile(os.path.join(folder, f)) and f not in keep]
    for f in gone:
        if doit:
            os.remove(os.path.join(folder, f))
        report.append("  %s  %s" % ("removed" if doit else "STALE  ",
                                    os.path.join(os.path.relpath(folder, ROOT),
                                                 f)))
    return gone


def promote(doit_prune):
    want = sheets()
    report, n = [], 0
    for f in sorted(want):
        n += copy(os.path.join(OUT, f), os.path.join(IMAGES, f), report)
    for f in sorted(want):
        n += copy(os.path.join(IMAGES, f), os.path.join(ASSETS, f), report)
    for f in sorted(os.listdir(RULES)):
        if f.endswith(".pdf"):
            n += copy(os.path.join(RULES, f), os.path.join(ASSETS, f), report)
    for g in GAMES:
        f = "NobulousSet_%s_PnP.pdf" % g
        n += copy(os.path.join(OUT, f), os.path.join(PNP, f), report)
    n += copy(os.path.join(OUT, "PNP_CONTENTS.txt"),
              os.path.join(PNP, "PNP_CONTENTS.txt"), report)

    rule_pdfs = {f for f in os.listdir(RULES) if f.endswith(".pdf")}
    stale = prune(IMAGES, want | set(EXTRA_IMAGES), report, doit_prune)
    stale += prune(ASSETS, want | rule_pdfs | set(ASSET_KEEP), report,
                   doit_prune)
    stale += prune(PNP, {"NobulousSet_%s_PnP.pdf" % g for g in GAMES}
                   | {"PNP_CONTENTS.txt"}, report, doit_prune)

    print("promote: %d sheet(s) and file(s) written, %d stale"
          % (n, len(stale)))
    for line in report:
        print(line)
    if stale and not doit_prune:
        print("\n  re-run with --prune to delete the files marked STALE")
    return want


def release(want):
    print("\nrelease:")
    for sub in ("print", "tts"):
        d = os.path.join(RELEASE, sub)
        if os.path.isdir(d):
            shutil.rmtree(d)
        os.makedirs(d)

    pr = os.path.join(RELEASE, "print")
    big = 0
    for f in sorted(want):
        shutil.copyfile(os.path.join(IMAGES, f), os.path.join(pr, f))
        big += os.path.getsize(os.path.join(pr, f))
    for g in GAMES:
        f = "NobulousSet_%s_PnP.pdf" % g
        shutil.copyfile(os.path.join(PNP, f), os.path.join(pr, f))
    shutil.copyfile(os.path.join(PNP, "PNP_CONTENTS.txt"),
                    os.path.join(pr, "PNP_CONTENTS.txt"))
    for f in sorted(os.listdir(RULES)):
        if f.endswith(".pdf"):
            shutil.copyfile(os.path.join(RULES, f), os.path.join(pr, f))

    tt = os.path.join(RELEASE, "tts")
    small, scaled = 0, 0
    for f in sorted(want):
        im = Image.open(os.path.join(IMAGES, f))
        w, h = im.size
        k = min(1.0, float(TTS_MAX) / max(w, h))
        if k < 1.0:
            im = im.resize((max(1, int(round(w * k))),
                            max(1, int(round(h * k)))), Image.LANCZOS)
            scaled += 1
            # The art is flat colour over large areas, which is why a 300 DPI
            # sheet of 21 million pixels is under 3 MB: PNG's filters predict
            # a flat run almost perfectly. LANCZOS puts an interpolated ramp
            # on every edge and destroys that - resizing ALONE made this
            # folder bigger than the 300 DPI one. Quantising back to a
            # palette restores the flat runs and costs nothing visible at
            # about 400 px a card, which is all TTS draws.
            im = im.quantize(colors=256, method=Image.MEDIANCUT,
                             dither=Image.NONE)
        im.save(os.path.join(tt, f), optimize=True)
        small += os.path.getsize(os.path.join(tt, f))
    for f in ("NobulousSet.json", "REQUIRED_IMAGES.txt"):
        src = os.path.join(ROOT, "tts", f)
        if os.path.exists(src):
            shutil.copyfile(src, os.path.join(tt, f))

    print("  release/print  %d sheets at 300 DPI, %d PnP PDFs, "
          "%d rulebooks  (%.1f MB of sheets)"
          % (len(want), len(GAMES),
             len([f for f in os.listdir(RULES) if f.endswith(".pdf")]),
             big / 1e6))
    print("  release/tts    %d sheets, %d scaled to <= %d px  (%.1f MB, "
          "%.0f%% of print)"
          % (len(want), scaled, TTS_MAX, small / 1e6, 100.0 * small / big))


def main():
    args = sys.argv[1:]
    for d in (IMAGES, ASSETS, PNP):
        if not os.path.isdir(d):
            os.makedirs(d)
    want = promote("--prune" in args)
    if "--release" in args:
        release(want)


if __name__ == "__main__":
    main()
