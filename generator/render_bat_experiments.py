"""Render the authoritative BAT Experiments when WeasyPrint is unavailable.

This updates only the Experiment sprite and the first three BAT print-and-play
pages. Other BAT card families keep their existing artwork and PDF pages.
"""

from __future__ import annotations

import ast
from io import BytesIO
from pathlib import Path
import shutil
import subprocess
import tempfile

from PIL import Image
from pypdf import PdfReader, PdfWriter
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import simpleSplit
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(__file__).with_name("build_bat.py")
PNP = ROOT / "print-and-play" / "NobulousSet_BAT_PnP.pdf"
SPRITE = ROOT / "images" / "BAT_Encounters_TTS.png"
PLAYTEST_SPRITE = ROOT / "playtest" / "dist" / "assets" / "BAT_Encounters_TTS.png"
CARD_W, CARD_H = 180, 252  # 2.5 x 3.5 inches at 72 points/inch


def experiments():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "EXPERIMENTS"
            for target in node.targets
        ):
            data = ast.literal_eval(node.value)
            if len(data) != 20 or any(len(row) != 4 for row in data):
                raise ValueError("Expected 20 BAT Experiments with flavor text")
            return data
    raise ValueError("EXPERIMENTS missing from build_bat.py")


def fonts():
    for name, filename in (
        ("Georgia", "georgia.ttf"),
        ("Georgia-Bold", "georgiab.ttf"),
        ("Georgia-Italic", "georgiai.ttf"),
        ("Arial", "arial.ttf"),
        ("Arial-Bold", "arialbd.ttf"),
    ):
        pdfmetrics.registerFont(TTFont(name, str(Path("C:/Windows/Fonts") / filename)))


def centered_lines(pdf, lines, x, first_y, leading, font, size, color):
    pdf.setFont(font, size)
    pdf.setFillColor(HexColor(color))
    for index, line in enumerate(lines):
        pdf.drawCentredString(x, first_y - index * leading, line)


def draw_card(pdf, x, y, name, target, effect, flavor):
    green = "#285e4a"
    cream = "#fcfaf3"
    pdf.setFillColor(HexColor(cream))
    pdf.setStrokeColor(HexColor("#ada795"))
    pdf.setLineWidth(0.7)
    pdf.rect(x + 1, y + 1, CARD_W - 2, CARD_H - 2, fill=1, stroke=1)

    pdf.setFillColor(HexColor(green))
    pdf.rect(x + 1, y + CARD_H - 48, CARD_W - 2, 47, fill=1, stroke=0)
    name_lines = simpleSplit(name, "Georgia-Bold", 13.1, CARD_W - 16)
    if len(name_lines) > 2:
        name_lines = simpleSplit(name, "Georgia-Bold", 11.5, CARD_W - 16)
    centered_lines(pdf, name_lines, x + CARD_W / 2,
                   y + CARD_H - (19 if len(name_lines) == 1 else 12),
                   14, "Georgia-Bold", 13.1 if len(name_lines) <= 2 else 11.5, "#fffdf7")
    centered_lines(pdf, ["BUILD-A-TYRANT EXPERIMENT"], x + CARD_W / 2,
                   y + CARD_H - 42, 0, "Arial-Bold", 6.2, "#e9dfb7")

    centered_lines(pdf, [str(target)], x + CARD_W / 2, y + 164,
                   0, "Georgia-Bold", 29, green)
    centered_lines(pdf, ["TARGET"], x + CARD_W / 2, y + 151,
                   0, "Arial-Bold", 7, green)

    effect_size = 10.0
    effect_lines = simpleSplit(effect, "Georgia", effect_size, CARD_W - 22)
    while len(effect_lines) > 6 and effect_size > 8.4:
        effect_size -= 0.3
        effect_lines = simpleSplit(effect, "Georgia", effect_size, CARD_W - 22)
    leading = effect_size * 1.23
    effect_mid = y + 111
    centered_lines(pdf, effect_lines, x + CARD_W / 2,
                   effect_mid + leading * (len(effect_lines) - 1) / 2,
                   leading, "Georgia", effect_size, "#242822")

    flavor_lines = simpleSplit(flavor, "Georgia-Italic", 7.7, CARD_W - 21)
    centered_lines(pdf, flavor_lines, x + CARD_W / 2,
                   y + 48 + 9 * (len(flavor_lines) - 1) / 2,
                   9, "Georgia-Italic", 7.7, "#575748")
    pdf.setStrokeColor(HexColor("#b2ae9f"))
    pdf.line(x + 11, y + 26, x + CARD_W - 11, y + 26)
    centered_lines(pdf, ["Specimen revealed: +1 Target total (once)."],
                   x + CARD_W / 2, y + 15, 0, "Arial", 6.7, "#485247")


def render_pages(data):
    stream = BytesIO()
    pdf = canvas.Canvas(stream, pagesize=(612, 792))
    for page in range(3):
        for slot, row in enumerate(data[page * 9:(page + 1) * 9]):
            col, grid_row = slot % 3, slot // 3
            draw_card(pdf, 36 + col * CARD_W, 18 + (2 - grid_row) * CARD_H, *row)
        pdf.showPage()
    pdf.save()
    stream.seek(0)
    return PdfReader(stream)


def render_sprite(data, temp):
    card_pdf = temp / "cards.pdf"
    pdf = canvas.Canvas(str(card_pdf), pagesize=(CARD_W, CARD_H))
    for row in data:
        draw_card(pdf, 0, 0, *row)
        pdf.showPage()
    pdf.save()
    prefix = temp / "card"
    subprocess.run(["pdftoppm", "-f", "1", "-l", "20", "-r", "144", "-png",
                    str(card_pdf), str(prefix)], check=True)
    raster_paths = sorted(temp.glob("card-*.png"))
    if len(raster_paths) != 20:
        raise RuntimeError("Expected 20 rendered Experiment cards")
    with Image.open(raster_paths[0]) as first:
        width, height = first.size
    sprite = Image.new("RGB", (width * 10, height * 2), "white")
    for index, path in enumerate(raster_paths):
        with Image.open(path) as card:
            sprite.paste(card.convert("RGB"), ((index % 10) * width, (index // 10) * height))
    sprite.save(SPRITE, optimize=True)
    shutil.copyfile(SPRITE, PLAYTEST_SPRITE)


def main():
    fonts()
    data = experiments()
    existing = PdfReader(str(PNP))
    if len(existing.pages) != 10:
        raise ValueError("BAT PnP page count changed; review merge before replacing pages")
    replacement = render_pages(data)
    writer = PdfWriter()
    for page in replacement.pages:
        writer.add_page(page)
    for page in existing.pages[3:]:
        writer.add_page(page)
    with tempfile.TemporaryDirectory() as folder:
        temp = Path(folder)
        render_sprite(data, temp)
        temporary_pdf = temp / "BAT_PnP.pdf"
        with temporary_pdf.open("wb") as out:
            writer.write(out)
        shutil.copyfile(temporary_pdf, PNP)
    print(f"Updated {PNP}, {SPRITE}, and {PLAYTEST_SPRITE}")


if __name__ == "__main__":
    main()
