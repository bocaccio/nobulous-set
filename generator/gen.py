"""Card generator for The Nobulous Set."""
import json
import re
import pathlib
import os, subprocess, math
from weasyprint import HTML
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.environ.get("NOBULOUS_CARD_OUT", os.path.join(HERE, "out"))
os.makedirs(OUT, exist_ok=True)

PORTRAIT = (63.5, 88.9)
LANDSCAPE = (88.9, 63.5)
# 300 for print production. Everything that lays out a card measures in
# millimetres and converts through DPI, and title_lines' text width and its
# limit both scale with it, so the wrapping and the physical card size are
# unchanged - only the resolution. Raised from 200 on 2026-10-30; the
# largest sheet, a 10x3 grid, goes from 5000x2100 to 7500x3150 px, still
# inside what Tabletop Simulator will load.
DPI = 300
# The cream margin between a card's printed face and the edge of its cell on
# the sheet. ONE number with three readers: the CSS below insets the card by
# it, build_catalog.py publishes it per deck so the playtest lab can size a
# preview without guessing, and check_app_sync.py holds the three together.
# Until 2026-11-02 the lab carried its own copy as a 200 DPI pixel literal,
# left behind when the art moved to 300 on 2026-10-30. Nothing caught it
# because 15/500 and 23.6/750 are near enough the same ratio that the
# preview stayed almost right - it just ate the card's whole margin.
CARD_INSET_MM = 2.0

ACCENT = {'BAT': '#2c5f4a', 'NAP': '#6b3f8c', 'AoS': '#8a3d2e',
          'NRJ': '#1f4e6b', 'IMP': '#4a3b6b'}
# One palette for the whole set.
DOT = {'Y': '#e8b93a', 'G': '#4f9c62', 'B': '#4a86c8', 'P': '#8d5bb0', 'R': '#c0392b'}
DOT_NAP = DOT

SKULL = ('<svg viewBox="0 0 24 24" width="%s" height="%s" style="vertical-align:-.5mm">'
         '<path fill="#2a2119" d="M12 1.6c-4.7 0-8.1 3.2-8.1 7.6 0 2.5 1.1 4.3 2.6 5.5v2.4c0 .8.6 1.4 1.4 1.4h1.1v1.5'
         'c0 .8.6 1.4 1.4 1.4h3.2c.8 0 1.4-.6 1.4-1.4V18.5h1.1c.8 0 1.4-.6 1.4-1.4v-2.4c1.5-1.2 2.6-3 2.6-5.5'
         'C20.1 4.8 16.7 1.6 12 1.6z"/>'
         '<circle cx="8.6" cy="9.4" r="2.3" fill="#fbf9f3"/><circle cx="15.4" cy="9.4" r="2.3" fill="#fbf9f3"/>'
         '<path fill="#fbf9f3" d="M12 12.2l-1.2 2.5h2.4z"/></svg>')


def skulls(n, size='3.4mm'):
    return ''.join(SKULL % (size, size) for _ in range(n))


SUBJ_ICON = {
 'Anatomy': ('<svg viewBox="0 0 24 24" width="%s" height="%s"><path fill="#a8332c" d="M12 21.3l-1.7-1.6C5.1 15 2 12.2 2 8.7 2 5.9 4.1 3.8 6.8 3.8c1.6 0 3.1.7 4 1.9.9-1.2 2.4-1.9 4-1.9C17.9 3.8 20 5.9 20 8.7c0 3.5-3.1 6.3-8.3 11z"/></svg>'),
 'Engineering': ('<svg viewBox="0 0 24 24" width="%s" height="%s"><path fill="#2f6ba8" d="M12 8.4a3.6 3.6 0 100 7.2 3.6 3.6 0 000-7.2zm9 4.5v-1.8l-2.2-.5a7 7 0 00-.6-1.5l1.2-1.9-1.3-1.3-1.9 1.2a7 7 0 00-1.5-.6L14.2 4h-1.8l-.5 2.5a7 7 0 00-1.5.6L8.5 5.9 7.2 7.2l1.2 1.9a7 7 0 00-.6 1.5L5.4 11v1.8l2.4.5a7 7 0 00.6 1.5l-1.2 1.9 1.3 1.3 1.9-1.2a7 7 0 001.5.6l.5 2.4h1.8l.5-2.4a7 7 0 001.5-.6l1.9 1.2 1.3-1.3-1.2-1.9a7 7 0 00.6-1.5z"/></svg>'),
 'Procedure': ('<svg viewBox="0 0 24 24" width="%s" height="%s"><path fill="#7a4fa3" d="M20.7 3.3a1 1 0 00-1.4 0l-9 9-1.3 3.4a.6.6 0 00.8.8l3.4-1.3 9-9a1 1 0 000-1.4zM8.6 15.9l-4 4a1.4 1.4 0 102 2l4-4z"/></svg>'),
 'Theory': ('<svg viewBox="0 0 24 24" width="%s" height="%s"><path fill="#6f7a2e" d="M4 4.4h6.2c1 0 1.8.8 1.8 1.8v13c0-.8-.8-1.4-1.8-1.4H4zm16 0h-6.2c-1 0-1.8.8-1.8 1.8v13c0-.8.8-1.4 1.8-1.4H20z"/></svg>'),
}


def subj_icon(subject, size='4.4mm'):
    t = SUBJ_ICON.get(subject)
    return (t % (size, size)) if t else ''


def css(w, h):
    return """
@page { size: %fmm %fmm; margin: 0; }
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: "DejaVu Sans", sans-serif; width: %fmm; height: %fmm;
       background: #f6f3ea; color: #201c17; position: relative; }
.card { position:absolute; inset:%fmm; border:0.5pt solid #b8b0a0; border-radius:1.6mm;
        background:#fbf9f3; overflow:hidden; display:flex; flex-direction:column; }
/* NRJ module marker: a solid edge band along the foot of every NRJ card face */
.card.nrj > .body { margin-bottom:3.4mm; }
.card.nrj > .spine, .card.nrj > .mid { bottom:3.4mm; }
.nrjtag { position:absolute; left:0; right:0; bottom:0; height:3.4mm; background:#1f4e6b;
          color:#ffffffd0; font-size:5.2pt; font-weight:bold; letter-spacing:.38em;
          text-transform:uppercase; text-align:center; line-height:3.4mm; }
.hdr { background: var(--a); color:#fff; padding:1.9mm 2.4mm 2mm; flex:0 0 auto; }
.hdr .t { font-size:11pt; font-weight:bold; line-height:1.04; }
.hdr .t.long { font-size:9.2pt; }
.hdr .t.xlong { font-size:8.2pt; }
.hdr .s { font-size:6.4pt; letter-spacing:.11em; text-transform:uppercase; opacity:.9; margin-top:.7mm; }
.body { flex:1; padding:2.4mm; display:flex; flex-direction:column; }
.big { font-size:30pt; font-weight:bold; text-align:center; line-height:1; color:var(--a); }
.biglbl { font-size:6.2pt; letter-spacing:.14em; text-transform:uppercase; text-align:center;
          color:#8a8272; margin-top:.7mm; }
.txt { font-size:8.4pt; line-height:1.3; margin-top:2mm; }
.txt.c { text-align:center; }
.txt.sm { font-size:7.4pt; }
.sub { font-size:6.6pt; letter-spacing:.09em; text-transform:uppercase; color:var(--a);
       font-weight:bold; margin-bottom:.9mm; }
.spacer { flex:1; }
.ftr { font-size:6.2pt; line-height:1.22; letter-spacing:.03em; color:#7d7566;
       border-top:.4pt solid #ddd6c6; padding-top:1.1mm; margin-top:1.5mm; }
.ftr.warn { color:#a5502a; }
.row { display:flex; align-items:center; gap:1.6mm; }
.pill { display:inline-block; font-size:6.4pt; letter-spacing:.09em; text-transform:uppercase;
        background:var(--a); color:#fff; padding:.7mm 1.8mm; border-radius:.8mm; font-weight:bold; }
.elems { display:flex; align-items:flex-start; justify-content:center; gap:0; margin:2.6mm 0 1mm; }
.el { text-align:center; position:relative; padding:0 .8mm; }
.el .n { width:7.2mm; height:7.2mm; border-radius:50%%; border:1pt solid #3a332a;
         font-size:10.5pt; font-weight:bold; line-height:7mm; background:#fff; }
.el.mark .n { border-color:#c0392b; border-width:1.5pt; }
.el .d { width:3.2mm; height:3.2mm; border-radius:50%%; margin:1mm auto 0; border:.4pt solid #6b6459; }
.el .sp { height:3.2mm; margin-top:1mm; }
.bar { height:.9pt; background:#6b6459; flex:1; margin-top:3.5mm; min-width:1.4mm; }
.back { position:absolute; inset:0; display:flex; align-items:center;
        justify-content:center; flex-direction:column; }
.back .bt { color:#fff; font-size:16pt; font-weight:bold; letter-spacing:.06em; }
.back .bs { color:#ffffffcc; font-size:6.6pt; letter-spacing:.16em; text-transform:uppercase;
            margin-top:1.6mm; font-weight:bold; text-align:center; padding:0 4mm; }
/* --- landscape spine layout (NAP tasks) --- */
.spine { position:absolute; top:0; bottom:0; width:12mm; overflow:hidden; }
.track { position:absolute; left:0; right:0; bottom:1.5mm; display:flex;
         align-items:center; justify-content:center; }
.track.n { top:17mm; } .track.p { top:1.5mm; }
.spine.l { left:0; border-right:.5pt solid #ddd6c6; background:#f2eee2; }
.spine.r { right:0; border-left:.5pt solid #ddd6c6; background:#f7ebe6; }
.vert { transform:rotate(-90deg); transform-origin:center; text-align:center; }
.vert.nowrap { white-space:nowrap; }
.vert.rr { transform:rotate(90deg); }
.name { font-size:9pt; font-weight:bold; line-height:1.08; }
.pen { font-size:6.8pt; letter-spacing:.05em; text-transform:uppercase; color:#a5502a; }
.penlbl { font-size:5.6pt; letter-spacing:.24em; text-transform:uppercase; color:#a5502a; }
.marks { position:absolute; left:0; width:12mm; top:1.4mm; text-align:center; z-index:2; line-height:1; }
.marks .dt { width:3.8mm; height:3.8mm; border-radius:50%%; border:.5pt solid #6b6459; margin:1mm auto .8mm; }
.mid { position:absolute; left:12mm; right:12mm; top:0; bottom:0; display:flex; flex-direction:column; }
.half { flex:1; padding:1.6mm 2.6mm; display:flex; flex-direction:column; }
.rule { height:0; border-top:.6pt solid #c9c1b1; margin:0 2.6mm; flex:0 0 auto; }
.half.d { transform:rotate(180deg); justify-content:flex-start; }
.band { font-size:7pt; font-weight:bold; letter-spacing:.16em; text-transform:uppercase;
        color:#fff; text-align:center; padding:1.1mm; flex:0 0 auto; }
.band.d180 { transform:rotate(180deg); }
""" % (w, h, w, h, CARD_INSET_MM)


# ---------------------------------------------------------------------------
# Print-and-play sheet layout.  Nine cards to a page, 3 x 3, with the page
# turned to suit the cards: portrait cards on a portrait Letter page, landscape
# cards on a landscape one.  Both fit 3 x 3 at poker size with a 0.25in margin.
# ---------------------------------------------------------------------------
PNP_COLS, PNP_ROWS = 3, 3
LETTER_LONG, LETTER_SHORT = 11.0, 8.5


def pnp_layout(card_px):
    """-> (page_w, page_h, cols, rows, off_x, off_y) in pixels at DPI."""
    w, h = card_px
    if w > h:
        pw, ph = int(LETTER_LONG * DPI), int(LETTER_SHORT * DPI)
    else:
        pw, ph = int(LETTER_SHORT * DPI), int(LETTER_LONG * DPI)
    cols, rows = PNP_COLS, PNP_ROWS
    while cols > 1 and cols * w > pw:
        cols -= 1
    while rows > 1 and rows * h > ph:
        rows -= 1
    return pw, ph, cols, rows, (pw - cols * w) // 2, (ph - rows * h) // 2


def _crop_marks(pg, lay, card_px):
    """Faint tick marks in the margins on every cut line."""
    from PIL import ImageDraw
    pw, ph, cols, rows, ox, oy = lay
    w, h = card_px
    d = ImageDraw.Draw(pg)
    t = max(6, int(.05 * DPI))
    for c in range(cols + 1):
        x = ox + c * w
        d.line([(x, max(0, oy - t)), (x, oy)], fill='#9a9a9a', width=1)
        d.line([(x, oy + rows * h), (x, min(ph, oy + rows * h + t))], fill='#9a9a9a', width=1)
    for r in range(rows + 1):
        y = oy + r * h
        d.line([(max(0, ox - t), y), (ox, y)], fill='#9a9a9a', width=1)
        d.line([(ox + cols * w, y), (min(pw, ox + cols * w + t), y)], fill='#9a9a9a', width=1)


def stamp(pg, text):
    """A small label centred in the page's bottom margin: "Page 3 - Back"."""
    from PIL import ImageDraw, ImageFont
    d = ImageDraw.Draw(pg)
    size = max(11, int(.11 * DPI))
    try:
        font = ImageFont.truetype(str(_FONT_DIR / 'DejaVuSans.ttf'), size)
    except OSError:
        font = ImageFont.load_default()
    w = d.textlength(text, font=font)
    d.text(((pg.width - w) / 2, pg.height - int(.19 * DPI)), text, fill='#6b6459', font=font)


def paginate(ims, mirror=False, lay=None):
    """Tile card images into Letter pages.  mirror=True flips the column order
    about the center of the grid, which is what a long-edge duplex flip does."""
    if not ims:
        return []
    lay = lay or pnp_layout(ims[0].size)
    pw, ph, cols, rows, ox, oy = lay
    w, h = ims[0].size
    # The grid strides by one card size, so a card of any other size would
    # be pasted over its neighbour instead of into its own cell. Mixing
    # sizes is how the NAP pages broke; it fails here now rather than
    # printing.
    odd = next((im.size for im in ims if im.size != (w, h)), None)
    if odd:
        raise SystemExit('paginate: card sizes differ on one page - %dx%d and %dx%d'
                         % (w, h, odd[0], odd[1]))
    per = cols * rows
    pages = []
    for i in range(0, len(ims), per):
        pg = Image.new('RGB', (pw, ph), 'white')
        for j, im in enumerate(ims[i:i + per]):
            col, row = j % cols, j // cols
            if mirror:
                col = cols - 1 - col
            pg.paste(im, (ox + col * w, oy + row * h))
        _crop_marks(pg, lay, (w, h))
        pages.append(pg)
    return pages


def write_pnp(path, pages):
    if not pages:
        return
    from reportlab.pdfgen import canvas as _cv
    from reportlab.lib.utils import ImageReader
    # invariant=1 fixes the CreationDate and the document ID that reportlab
    # otherwise stamps per run. Without it two packs of identical input
    # produce different bytes, which is the PnP non-reproducibility
    # HANDOFF recorded: the card sheets were always deterministic, only the
    # PDF wrapper was not.
    c = _cv.Canvas(path, invariant=1)
    for pg in pages:
        wpt, hpt = pg.width / DPI * 72.0, pg.height / DPI * 72.0
        c.setPageSize((wpt, hpt))
        c.drawImage(ImageReader(pg), 0, 0, width=wpt, height=hpt)
        c.showPage()
    c.save()


# Bundled DejaVu fonts (repo fonts/). Without these, machines that lack DejaVu
# (e.g. Windows) silently substitute other fonts and the cards reflow.
_FONT_DIR = pathlib.Path(__file__).resolve().parent.parent / 'fonts'
FONT_FACES = ''.join(
    '@font-face { font-family: "%s"; font-weight: %s; font-style: %s; src: url("%s"); } '
    % (fam, wt, st, (_FONT_DIR / fn).as_uri()) for fam, wt, st, fn in [
        ("DejaVu Sans", "normal", "normal", "DejaVuSans.ttf"), ("DejaVu Sans", "bold", "normal", "DejaVuSans-Bold.ttf"),
        ("DejaVu Sans", "normal", "italic", "DejaVuSans-Oblique.ttf"), ("DejaVu Sans", "bold", "italic", "DejaVuSans-BoldOblique.ttf"),
        ("DejaVu Serif", "normal", "normal", "DejaVuSerif.ttf"), ("DejaVu Serif", "bold", "normal", "DejaVuSerif-Bold.ttf"),
        ("DejaVu Serif", "normal", "italic", "DejaVuSerif-Italic.ttf"), ("DejaVu Serif", "bold", "italic", "DejaVuSerif-BoldItalic.ttf")])


def page(inner, accent, size=PORTRAIT, extra=''):
    return ('<!DOCTYPE html><html><head><meta charset="utf-8"><style>%s%s%s</style></head>'
            '<body style="--a:%s">%s</body></html>' % (FONT_FACES, css(*size), extra, accent, inner))


def elements(targets, dots=None, mark=None):
    dots = dots or [None] * len(targets)
    out = ['<div class="elems">']
    for i, t in enumerate(targets):
        if i:
            out.append('<div class="bar"></div>')
        cls = 'el mark' if mark == i else 'el'
        d = ('<div class="d" style="background:%s"></div>' % DOT[dots[i]]) if dots[i] else '<div class="sp"></div>'
        out.append('<div class="%s"><div class="n">%d</div>%s</div>' % (cls, t, d))
    out.append('</div>')
    return ''.join(out)


def _manifest(name, sheet_cols, sheet_rows, count, card_px, back, back_is_sheet):
    """What pack.py needs to cut single cards back out of the TTS sheets."""
    w, h = card_px
    with open(os.path.join(OUT, '%s_cards.json' % name), 'w', encoding='utf-8') as fh:
        json.dump({'name': name, 'sheet': '%s_TTS.png' % name,
                   'cols': sheet_cols, 'rows': sheet_rows, 'count': count,
                   # The cell size BEFORE fit_tts. Dividing the sheet gives
                   # the shrunk one, and pack.py has to know the difference.
                   'card': [w, h],
                   'landscape': w > h, 'back': back, 'backIsSheet': back_is_sheet}, fh, indent=1)


# A title that wraps makes the header taller, but WeasyPrint sizes the flex
# header from one line and the body then covers the subtitle. Measuring the
# title here and reserving the height keeps every header honest.
HDR_PAD = (1.9, 2.0, 2.4)          # top, bottom, side (mm)
SUB_SIZE, SUB_GAP, PT_MM = 6.4, 0.7, 25.4 / 72.0
# `.card` draws a 0.5pt border and `* { box-sizing: border-box }` takes it
# out of the content width, so the title has this much less room than the
# padding alone suggests.
CARD_BORDER_MM = 0.5 * PT_MM
# WeasyPrint lays the title out with Pango; title_lines measures it with
# PIL, and PIL runs a little short. On 2026-11-02 "Undocumented
# Dependencies" measured 99.86% of the available width, so hdr_fit
# reserved no second line - and Pango wrapped it anyway. The body then
# rode up and cut the subtitle in half.
#
# This margin was first picked, not measured: the set happened to have an
# empty band between 96.1% and 99.86%, so anything inside it caught that
# one title and touched nothing else. Sizing titles by measurement (see
# title_cls) fills that band, so the margin had to be measured properly.
#
# It now is. Every multi-word title in the set was laid out by WeasyPrint
# itself in a box of a known width in mm, narrowing until it wrapped - the
# narrowest box a title survives IS Pango's width for it. Pango needs at
# most 1.014x PIL's estimate (`Rapid Approach`, `Maintain Balance` and
# `Climb an Incline`, all at 11.6pt), so anything at or below 1/1.014 =
# 0.9862 is safe. 0.98 keeps about 0.6% in hand. One-word titles are
# excluded: they cannot wrap at any width, which is why an earlier sweep
# that included them appeared to show an 18% spread.
#
# Do not read widths out of WeasyPrint's box tree to redo this - those
# came out ~12% under what the shipped art plainly shows. Ask whether it
# WRAPPED.
#
# Err low rather than high: reserving a line that turns out not to be
# needed costs a slightly deeper header, while not reserving one costs a
# clipped card.
TITLE_SAFETY = 0.98
# The worst Pango-over-PIL ratio measured across the set, for
# check_app_sync.py to hold TITLE_SAFETY against.
TITLE_PANGO_RATIO = 1.014
# How a header is really printed: the title sizes largest-first with the
# class that selects each one in the CSS above, the subtitle size, and any
# extra side padding the markup adds. Two decks do not print the header the
# stylesheet above describes, and a title measured against the wrong one is
# a title that wraps:
#
#   - build_aos.py renders with its BIG stylesheet, which sets `.hdr .t` to
#     11.6pt and `.hdr .s` to 6.8pt. The `.long` and `.xlong` rules still
#     win on specificity, so only AoS's TOP rung moves.
#   - BAT's dotted cards pad the header's right edge out to 10mm to clear
#     the colour dot, leaving the title 7.6mm less room than HDR_PAD says.
#
# Every caller that lays out a header names its style, and
# build_catalog.py publishes the choice per deck so check_app_sync.py can
# check the real rule. Spelled out in full rather than derived from one
# base, because both of those readers parse this as a literal.
#
# Add a style here rather than overriding header sizes or padding in a
# build script and leaving this file to guess.
HDR_STYLES = {
    '':    (((11.0, ''), (9.2, ' long'), (8.2, ' xlong')), 6.4, 0.0),
    'aos': (((11.6, ''), (9.2, ' long'), (8.2, ' xlong')), 6.8, 0.0),
    'dot': (((11.0, ''), (9.2, ' long'), (8.2, ' xlong')), 6.4, 7.6),
}
TITLE_LADDER = HDR_STYLES[''][0]


def hdr_depth_mm(title_pt, sub_pt=SUB_SIZE, lines=1):
    """The depth a header of this many title lines needs, in mm."""
    return (HDR_PAD[0] + lines * title_pt * 1.04 * PT_MM
            + SUB_GAP + sub_pt * 1.25 * PT_MM + HDR_PAD[1])


# EVERY header in the set is this deep, so a row of face-up cards lines up:
# title, subtitle and the top of the body sit at one height whatever the
# card and whatever size its title is set at. A title set below its style's
# top rung leaves a little more clear band under its subtitle rather than
# making the card a different shape, and the number is the same for
# portrait and landscape since none of the terms depends on the card's
# width.
#
# It has to be the DEEPEST style's one-line header, not the default's,
# because min-height is a floor and not a ceiling: WeasyPrint grows a
# header whose content does not fit. The first version of this used the
# default style's 11.46mm, so AoS's 11.6pt titles pushed their own headers
# to 11.86mm and that family shipped on 2026-11-02 three pixels deeper than
# the rest of the set - the exact unevenness the constant exists to remove.
HDR_H_MM = max(hdr_depth_mm(ladder[0][0], sub_pt)
               for ladder, sub_pt, _pad in HDR_STYLES.values())


def title_lines(title, size_pt, width_mm):
    """How many lines a title takes at this size, by real glyph widths."""
    from PIL import ImageFont
    px = max(8, int(round(size_pt * PT_MM * DPI / 25.4)))
    try:
        font = ImageFont.truetype(str(_FONT_DIR / 'DejaVuSans-Bold.ttf'), px)
    except OSError:
        return 1
    limit = width_mm * DPI / 25.4
    lines, line = 1, ''
    for word in title.split():
        trial = (line + ' ' + word).strip()
        if font.getlength(trial) <= limit * TITLE_SAFETY or not line:
            line = trial
        else:
            lines, line = lines + 1, word
    return lines


def _plain(title):
    return (re.sub('<[^>]+>', ' ', title)
            .replace('&#8209;', '-').replace('&middot;', '.'))


def title_width_mm(size=PORTRAIT, style=''):
    """The room a title actually has, inside the inset, border and padding."""
    return (size[0] - 2 * CARD_INSET_MM - 2 * CARD_BORDER_MM
            - 2 * HDR_PAD[2] - HDR_STYLES[style][2])


def title_pt(cls='', style=''):
    """The point size the CSS will print a title of this class at."""
    ladder = HDR_STYLES[style][0]
    # Largest-last, because 'long' is a substring of 'xlong'.
    for pt, c in reversed(ladder):
        if c and c.strip() in cls:
            return pt
    return ladder[0][0]


def title_cls(title, size=PORTRAIT, style=''):
    """The size class for a title: the LARGEST rung on its style's ladder
    that still keeps the title to one line.

    This used to be five copies of one character-count expression, and a
    count is the wrong instrument in both directions. It cannot know that
    "Undocumented Dependencies" sets wider than "Emergency Specimen
    Handling" despite being three characters shorter, so three titles were
    printed at a size they did not fit. And it cannot know that a landscape
    card is 88.9mm wide where a portrait one is 63.5, so it shrank 82
    titles that had room to spare - most of a whole landscape deck, set two
    sizes down for no reason a reader could see.

    Measuring answers both. Nothing here is a judgement about how a card
    should look: the ladder is still the three sizes the CSS offers, and a
    title only leaves the top rung when it genuinely does not fit on it.
    """
    plain = _plain(title)
    ladder = HDR_STYLES[style][0]
    for pt, cls in ladder[:-1]:
        if title_lines(plain, pt, title_width_mm(size, style)) < 2:
            return cls
    return ladder[-1][1]


def hdr_fit(title, cls='', size=PORTRAIT, style=''):
    """The header's depth, as a style attribute. One number for the set.

    A title that still wraps at the smallest size gets a deeper header
    rather than a clipped subtitle. title_cls makes that unreachable for
    every card in the set today, and check_app_sync.py keeps it that way.
    """
    size_pt = title_pt(cls, style)
    lines = title_lines(_plain(title), size_pt, title_width_mm(size, style))
    if lines < 2:
        return 'min-height:%.2fmm' % HDR_H_MM
    return 'min-height:%.2fmm' % hdr_depth_mm(size_pt, HDR_STYLES[style][1], lines)


# Tabletop Simulator will not load a custom deck image above 10000 px on a
# side. At 300 DPI a card is 750x1050, so a 10-wide grid of portrait cards
# is 7500 across - fine - but NAP's 26 Tasks and 12 Final Exams are
# LANDSCAPE, ten 1050px cards to a row, and came out 10500.
#
# That used to be handled by downscaling the finished sheet, on the grounds
# that "the PnP pages are built from the full-resolution card images, not
# from this". That was true of each deck's own <deck>_PnP.pdf and FALSE of
# the shipped per-game one: pack.py cuts its cards back out of the TTS
# sheet. So those two decks printed at 1000x714 where the rest of NAP
# printed at 750x1050, and because paginate strides by the first card's
# size, every full-size card after them sat 36px right and 50px low of its
# cell and overlapped its neighbour. NAP pages 3-7 were unusable.
#
# So the grid is narrowed instead and nothing is resampled: 26 Tasks go
# 9x3 rather than 10x3. fit_tts stays as a backstop for a deck that cannot
# be made to fit any grid, and pack.py scales such a deck's cards back up
# rather than letting the page grid break again.
TTS_MAX = 10000


def tts_grid(n, card_px):
    """(cols, rows) for an n-card sheet: the widest grid up to 10 that TTS
    will still load. Fewer columns means more rows, so a deck can only run
    out of room if it will not fit in any grid - then this gives the 10-wide
    one and fit_tts shrinks it."""
    w, h = card_px
    for cols in range(min(10, n), 0, -1):
        rows = math.ceil(n / cols)
        if cols * w <= TTS_MAX and rows * h <= TTS_MAX:
            return cols, rows
    cols = min(10, n)
    return cols, math.ceil(n / cols)


def fit_tts(sheet, cols, rows):
    """Shrink a deck sheet to TTS's ceiling, keeping the cells integral."""
    if max(sheet.width, sheet.height) <= TTS_MAX:
        return sheet
    k = TTS_MAX / float(max(sheet.width, sheet.height))
    cw = int(sheet.width / cols * k)
    ch = int(sheet.height / rows * k)
    return sheet.resize((cw * cols, ch * rows), Image.LANCZOS)


def render_deck(name, cards, accent_key, size=PORTRAIT, extra='', back=None):
    """One-faced deck. `back` is the stem of a card back already built by
    make_back; the PnP then alternates a page of fronts with a page of that back,
    mirrored, so the sheets can be printed double-sided like the duplex decks."""
    acc = ACCENT[accent_key]
    html = ''.join('<div style="page-break-after:always">%s</div>' % c for c in cards)
    p = os.path.join(OUT, '_%s.pdf' % name)
    HTML(string=page(html, acc, size, extra)).write_pdf(p)
    subprocess.run(['pdftoppm', '-r', str(DPI), '-png', p, os.path.join(OUT, '_%s' % name)],
                   check=True, capture_output=True)
    imgs = sorted(f for f in os.listdir(OUT) if f.startswith('_%s-' % name) and f.endswith('.png'))
    ims = [Image.open(os.path.join(OUT, f)).convert('RGB') for f in imgs]
    if not ims:
        return 0
    w, h = ims[0].size
    cols, rows = tts_grid(len(ims), (w, h))
    sheet = Image.new('RGB', (cols * w, rows * h), '#f6f3ea')
    for i, im in enumerate(ims):
        sheet.paste(im, ((i % cols) * w, (i // cols) * h))
    fit_tts(sheet, cols, rows).save(os.path.join(OUT, '%s_TTS.png' % name))
    lay = pnp_layout((w, h))
    pages = paginate(ims, lay=lay)
    if back:
        # One back for the deck, or a list with one back per card.
        names = list(back) if isinstance(back, (list, tuple)) else [back] * len(ims)
        if len(names) != len(ims):
            raise SystemExit('render_deck(%s): %d backs for %d cards' % (name, len(names), len(ims)))
        cache, backs_for_cards = {}, []
        for stem in names:
            if stem not in cache:
                bp = os.path.join(OUT, '%s.png' % stem)
                if not os.path.exists(bp):
                    raise SystemExit('render_deck(%s): card back %s.png is not built yet - '
                                     'call make_back before the deck' % (name, stem))
                bim = Image.open(bp).convert('RGB')
                cache[stem] = bim if bim.size == (w, h) else bim.resize((w, h))
            backs_for_cards.append(cache[stem])
        per = lay[2] * lay[3]
        backs = [paginate(backs_for_cards[i:i + per], mirror=True, lay=lay)[0]
                 for i in range(0, len(ims), per)]
        pages = [pg for pair in zip(pages, backs) for pg in pair]
    write_pnp(os.path.join(OUT, '%s_PnP.pdf' % name), pages)
    _manifest(name, cols, rows, len(ims), (w, h),
              ['%s.png' % stem for stem in back] if isinstance(back, (list, tuple))
              else ('%s.png' % back if back else None), False)
    for f in imgs:
        os.remove(os.path.join(OUT, f))
    os.remove(p)
    return len(ims)


def render_duplex(name, fronts, backs, accent_key, size=PORTRAIT, extra=''):
    """True two-sided deck. Emits
         <name>_TTS.png       face grid
         <name>_TTS_back.png  back grid, card-for-card (TTS: tick 'Unique Backs')
         <name>_PnP.pdf       front page then mirrored back page, for duplex printing
    """
    assert len(fronts) == len(backs)
    acc = ACCENT[accent_key]
    ims = {}
    for tag, cards in (('f', fronts), ('b', backs)):
        html = ''.join('<div style="page-break-after:always">%s</div>' % c for c in cards)
        p = os.path.join(OUT, '_%s%s.pdf' % (name, tag))
        HTML(string=page(html, acc, size, extra)).write_pdf(p)
        subprocess.run(['pdftoppm', '-r', str(DPI), '-png', p, os.path.join(OUT, '_%s%s' % (name, tag))],
                       check=True, capture_output=True)
        fs = sorted(f for f in os.listdir(OUT) if f.startswith('_%s%s-' % (name, tag)) and f.endswith('.png'))
        ims[tag] = [Image.open(os.path.join(OUT, f)).convert('RGB') for f in fs]
        for f in fs:
            os.remove(os.path.join(OUT, f))
        os.remove(p)
    w, h = ims['f'][0].size
    n = len(ims['f'])
    cols, rows = tts_grid(n, (w, h))
    for tag, suffix in (('f', ''), ('b', '_back')):
        sheet = Image.new('RGB', (cols * w, rows * h), '#f6f3ea')
        for i, im in enumerate(ims[tag]):
            sheet.paste(im, ((i % cols) * w, (i // cols) * h))
        fit_tts(sheet, cols, rows).save(
            os.path.join(OUT, '%s_TTS%s.png' % (name, suffix)))
    # Front page then its mirrored back page, so a long-edge duplex flip puts
    # each back behind its own face.  The mirror is about the center of the
    # full 3-wide grid, not about the cards that happen to be present, because
    # that is where the paper actually folds.
    lay = pnp_layout((w, h))
    fronts_p = paginate(ims['f'], lay=lay)
    backs_p = paginate(ims['b'], mirror=True, lay=lay)
    pages = [p for pair in zip(fronts_p, backs_p) for p in pair]
    write_pnp(os.path.join(OUT, '%s_PnP.pdf' % name), pages)
    _manifest(name, cols, rows, n, (w, h), '%s_TTS_back.png' % name, True)
    return n


def make_back(fname, title, sub, color, size=PORTRAIT):
    """One card back image.  fname is the output stem."""
    inner = ('<div class="back" style="background:%s">'
             '<div class="bt">%s</div><div class="bs">%s</div>'
             '<div style="width:22mm;height:.6pt;background:#ffffff55;margin:2.6mm 0"></div>'
             '<div style="color:#ffffff88;font-size:5pt;letter-spacing:.28em;text-transform:uppercase">'
             'The Nobulous Set</div></div>' % (color, title, sub))
    doc = page(inner, color, size)
    p = os.path.join(OUT, '_b.pdf')
    HTML(string=doc).write_pdf(p)
    subprocess.run(['pdftoppm', '-r', str(DPI), '-png', '-singlefile', p,
                    os.path.join(OUT, fname)], check=True, capture_output=True)
    os.remove(p)
