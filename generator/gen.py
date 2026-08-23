"""Card generator for The Nobulous Set."""
import os, subprocess, math
from weasyprint import HTML
from PIL import Image

OUT = "/home/claude/cards/out"
os.makedirs(OUT, exist_ok=True)

PORTRAIT = (63.5, 88.9)
LANDSCAPE = (88.9, 63.5)
DPI = 200

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
.card { position:absolute; inset:2.0mm; border:0.5pt solid #b8b0a0; border-radius:1.6mm;
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
""" % (w, h, w, h)


def page(inner, accent, size=PORTRAIT, extra=''):
    return ('<!DOCTYPE html><html><head><meta charset="utf-8"><style>%s%s</style></head>'
            '<body style="--a:%s">%s</body></html>' % (css(*size), extra, accent, inner))


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


def render_deck(name, cards, accent_key, size=PORTRAIT, extra=''):
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
    cols = min(10, len(ims))
    rows = math.ceil(len(ims) / cols)
    sheet = Image.new('RGB', (cols * w, rows * h), '#f6f3ea')
    for i, im in enumerate(ims):
        sheet.paste(im, ((i % cols) * w, (i // cols) * h))
    sheet.save(os.path.join(OUT, '%s_TTS.png' % name))
    per_row = max(1, int((8.5 * DPI - .8 * DPI) // w))
    per_col = max(1, int((11 * DPI - .8 * DPI) // h))
    per = per_row * per_col
    pnp = []
    for i in range(0, len(ims), per):
        pg = Image.new('RGB', (int(8.5 * DPI), int(11 * DPI)), 'white')
        for j, im in enumerate(ims[i:i + per]):
            pg.paste(im, (int(.4 * DPI) + (j % per_row) * w, int(.4 * DPI) + (j // per_row) * h))
        pnp.append(pg)
    if pnp:
        from reportlab.pdfgen import canvas as _cv
        from reportlab.lib.utils import ImageReader
        c = _cv.Canvas(os.path.join(OUT, '%s_PnP.pdf' % name), pagesize=(8.5 * 72, 11 * 72))
        for pg in pnp:
            c.drawImage(ImageReader(pg), 0, 0, width=8.5 * 72, height=11 * 72)
            c.showPage()
        c.save()
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
    cols = min(10, n)
    rows = math.ceil(n / cols)
    for tag, suffix in (('f', ''), ('b', '_back')):
        sheet = Image.new('RGB', (cols * w, rows * h), '#f6f3ea')
        for i, im in enumerate(ims[tag]):
            sheet.paste(im, ((i % cols) * w, (i // cols) * h))
        sheet.save(os.path.join(OUT, '%s_TTS%s.png' % (name, suffix)))
    per_row = max(1, int((8.5 * DPI - .8 * DPI) // w))
    per_col = max(1, int((11 * DPI - .8 * DPI) // h))
    per = per_row * per_col
    pages = []
    for i in range(0, n, per):
        chunk_f = ims['f'][i:i + per]
        chunk_b = ims['b'][i:i + per]
        for tag, chunk in (('f', chunk_f), ('b', chunk_b)):
            pg = Image.new('RGB', (int(8.5 * DPI), int(11 * DPI)), 'white')
            for j, im in enumerate(chunk):
                col, row = j % per_row, j // per_row
                if tag == 'b':                       # mirror columns for long-edge duplex
                    filled = min(per_row, len(chunk) - row * per_row)
                    col = filled - 1 - col
                pg.paste(im, (int(.4 * DPI) + col * w, int(.4 * DPI) + row * h))
            pages.append(pg)
    from reportlab.pdfgen import canvas as _cv
    from reportlab.lib.utils import ImageReader
    c = _cv.Canvas(os.path.join(OUT, '%s_PnP.pdf' % name), pagesize=(8.5 * 72, 11 * 72))
    for pg in pages:
        c.drawImage(ImageReader(pg), 0, 0, width=8.5 * 72, height=11 * 72)
        c.showPage()
    c.save()
    return n


def make_back(fname, title, sub, colour, size=PORTRAIT):
    """One card back image.  fname is the output stem."""
    inner = ('<div class="back" style="background:%s">'
             '<div class="bt">%s</div><div class="bs">%s</div>'
             '<div style="width:22mm;height:.6pt;background:#ffffff55;margin:2.6mm 0"></div>'
             '<div style="color:#ffffff88;font-size:5pt;letter-spacing:.28em;text-transform:uppercase">'
             'The Nobulous Set</div></div>' % (colour, title, sub))
    doc = page(inner, colour, size)
    p = os.path.join(OUT, '_b.pdf')
    HTML(string=doc).write_pdf(p)
    subprocess.run(['pdftoppm', '-r', str(DPI), '-png', '-singlefile', p,
                    os.path.join(OUT, fname)], check=True, capture_output=True)
    os.remove(p)
