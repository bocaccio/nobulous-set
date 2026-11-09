# -*- coding: utf-8 -*-
"""Draw text with polygons, because Pillow's text engine is blocked.

WHY THIS EXISTS. Windows Smart App Control started refusing Pillow's
_imagingft.pyd on 2026-11-09 - it is an unsigned native DLL - and with
it went every ImageFont call in tts/make_template.py. The overlay could
not be redrawn at all, which matters because the mat has to be redrawn
whenever the felt is re-measured.

So the glyphs come out of the font file itself. fontTools is pure
Python once its own compiled bezierTools is stepped around (see
pure_fonttools below), a TrueType glyph is a set of closed contours of
lines and quadratic curves, and PIL can fill a polygon without any of
the blocked code. Flattened at 8 segments a curve and drawn into a 4x
supersample, the result is indistinguishable from FreeType at these
sizes - these are three short labels on a table mat, not body text.

It renders a single line of text and reports its width, which is all
make_template asks of a font. Kerning is not applied: fonts of this
kind carry almost none in uppercase, and a mat label is not typography.
"""
import io
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
SS = 4                      # supersample, then box-filter down


def pure_fonttools():
    """Import fontTools with its compiled bezierTools stepped around.

    Python prefers an extension module to a .py of the same name, so
    fontTools.misc.bezierTools resolves to the .pyd that Smart App
    Control blocks - even though the pure-Python file sits right beside
    it. Loading that file under the module's name first means every
    later import finds it already there.
    """
    import importlib.util
    import fontTools.misc
    name = "fontTools.misc.bezierTools"
    if name not in sys.modules:
        path = os.path.join(os.path.dirname(fontTools.misc.__file__),
                            "bezierTools.py")
        if os.path.exists(path):
            spec = importlib.util.spec_from_file_location(name, path)
            mod = importlib.util.module_from_spec(spec)
            sys.modules[name] = mod
            try:
                spec.loader.exec_module(mod)
            except Exception:
                del sys.modules[name]
    from fontTools.ttLib import TTFont
    return TTFont


class Pen(object):
    """Collects a glyph's contours as flattened point lists."""

    def __init__(self, glyphset, steps=8):
        self.glyphset = glyphset
        self.steps = steps
        self.contours = []
        self._pts = []
        self._cur = (0.0, 0.0)

    # -- the pen protocol fontTools calls ------------------------------
    def moveTo(self, p):
        self._flush()
        self._cur = p
        self._pts = [p]

    def lineTo(self, p):
        self._pts.append(p)
        self._cur = p

    def qCurveTo(self, *points):
        # TrueType gives a run of off-curve points with an optional
        # on-curve last one; consecutive off-curve points imply an
        # on-curve midpoint between them.
        pts = list(points)
        end = pts.pop() if pts[-1] is not None else None
        if end is None:
            end = self._pts[0]
        prev = self._cur
        for i, c in enumerate(pts):
            nxt = (end if i == len(pts) - 1
                   else ((c[0] + pts[i + 1][0]) / 2.0,
                         (c[1] + pts[i + 1][1]) / 2.0))
            for s in range(1, self.steps + 1):
                t = s / float(self.steps)
                u = 1.0 - t
                self._pts.append(
                    (u * u * prev[0] + 2 * u * t * c[0] + t * t * nxt[0],
                     u * u * prev[1] + 2 * u * t * c[1] + t * t * nxt[1]))
            prev = nxt
        self._cur = end

    def curveTo(self, *points):
        # Cubic, for the CFF fonts this may meet one day.
        pts = list(points)
        end = pts[-1]
        c1, c2 = pts[0], pts[1] if len(pts) > 2 else pts[0]
        prev = self._cur
        for s in range(1, self.steps + 1):
            t = s / float(self.steps)
            u = 1.0 - t
            self._pts.append(
                (u ** 3 * prev[0] + 3 * u * u * t * c1[0]
                 + 3 * u * t * t * c2[0] + t ** 3 * end[0],
                 u ** 3 * prev[1] + 3 * u * u * t * c1[1]
                 + 3 * u * t * t * c2[1] + t ** 3 * end[1]))
        self._cur = end

    def closePath(self):
        self._flush()

    endPath = closePath

    def addComponent(self, name, transform):
        sub = Pen(self.glyphset, self.steps)
        self.glyphset[name].draw(sub)
        a, b, c, d, e, f = transform
        for con in sub.contours:
            self.contours.append([(a * x + c * y + e, b * x + d * y + f)
                                  for x, y in con])

    def _flush(self):
        if len(self._pts) > 2:
            self.contours.append(self._pts)
        self._pts = []


class Font(object):
    """One TrueType face, measured and drawn without FreeType."""

    _cache = {}

    def __init__(self, path):
        TTFont = pure_fonttools()
        self.tt = TTFont(path, fontNumber=0, lazy=True)
        self.upem = self.tt["head"].unitsPerEm
        self.cmap = self.tt.getBestCmap()
        self.glyphset = self.tt.getGlyphSet()
        self.hmtx = self.tt["hmtx"]

    @classmethod
    def get(cls, path):
        if path not in cls._cache:
            cls._cache[path] = cls(path)
        return cls._cache[path]

    def _name(self, ch):
        return self.cmap.get(ord(ch))

    def advance(self, ch, px):
        n = self._name(ch)
        if n is None:
            return 0.0
        return self.hmtx[n][0] * px / float(self.upem)

    def width(self, text, px):
        return sum(self.advance(c, px) for c in text)

    def contours(self, text, px):
        """Every closed contour of a line of text, in pixels, y down."""
        out, x = [], 0.0
        s = px / float(self.upem)
        for ch in text:
            n = self._name(ch)
            if n is not None:
                pen = Pen(self.glyphset)
                self.glyphset[n].draw(pen)
                for con in pen.contours:
                    out.append([(x + px_ * s, -py * s) for px_, py in con])
                x += self.advance(ch, px)
        return out


def draw_text(img, xy, text, px, fill, font_path):
    """Draw one line with its LEFT BASELINE at xy. Returns its width.

    Supersampled and composited, so the edges are as smooth as the
    blocked engine would have given.
    """
    font = Font.get(font_path)
    cons = font.contours(text, px * SS)
    if not cons:
        return 0.0
    w = font.width(text, px * SS)
    xs = [p[0] for c in cons for p in c]
    ys = [p[1] for c in cons for p in c]
    x0, x1 = min(min(xs), 0.0), max(max(xs), w)
    y0, y1 = min(ys), max(ys)
    pad = SS * 2
    tw = int(x1 - x0) + 2 * pad
    th = int(y1 - y0) + 2 * pad
    if tw <= 0 or th <= 0:
        return 0.0
    # EVEN-ODD, WHICH IS WHAT A COUNTER NEEDS. The hole in an O is a
    # contour wound the other way; filling each one in turn would fill
    # the hole back in, so they are XOR-ed together instead.
    acc = Image.new("L", (tw, th), 0)
    for con in cons:
        one = Image.new("L", (tw, th), 0)
        ImageDraw.Draw(one).polygon(
            [(p[0] - x0 + pad, p[1] - y0 + pad) for p in con], fill=255)
        acc = Image.frombytes("L", (tw, th), bytes(
            a ^ b for a, b in zip(acc.tobytes(), one.tobytes())))
    mask = acc.resize((max(1, tw // SS), max(1, th // SS)), Image.LANCZOS)
    paste = (int(round(xy[0] + x0 / SS)), int(round(xy[1] + y0 / SS)))
    layer = Image.new("RGBA", mask.size, tuple(fill[:3]) + (0,))
    if len(fill) > 3 and fill[3] != 255:
        mask = mask.point(lambda v: int(v * fill[3] / 255.0))
    layer.putalpha(mask)
    img.alpha_composite(layer, paste)
    return w / float(SS)


def text_size(text, px, font_path):
    """(width, cap height) in pixels, the two numbers a layout needs."""
    font = Font.get(font_path)
    cons = font.contours(text, px)
    ys = [p[1] for c in cons for p in c] or [0.0]
    return font.width(text, px), max(ys) - min(ys)
