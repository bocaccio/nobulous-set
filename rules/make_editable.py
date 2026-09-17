"""Flatten the four rulebooks into one editable Word document.

    python3 make_editable.py

Writes Nobulous_Set_Rules_EDITABLE.docx containing every word of the four
PDFs, in order, with the games as top-level headings.  Edit it in Word, send
it back, and the changes get folded into the HTML sources that build the PDFs.
"""
import os, re, subprocess
from bs4 import BeautifulSoup

HERE = os.path.dirname(os.path.abspath(__file__))
BOOKS = [('bat', 'Build-a-Tyrant (BAT)'),
         ('nap', 'Nobulous Apprenticeship Program (NAP)'),
         ('aos', 'Automaton of Shale (AoS)'),
         ('nrj', 'Nobulous Research Journal (NRJ)')]

parts = ['<h1>The Nobulous Set &mdash; Rules</h1>',
         '<p><em>A fan expansion for 20 Strong. Three standalone solo games plus a campaign '
         'overlay. This document is the editable copy of the four rulebook PDFs; every '
         'heading, table and callout below appears in them.</em></p>']

for key, title in BOOKS:
    soup = BeautifulSoup(open(os.path.join(HERE, key + '.html')).read(), 'html.parser')

    # --- cover ---------------------------------------------------------
    cover = soup.select_one('.cover')
    parts.append('<h1>%s</h1>' % title)
    tag = cover.select_one('.tagline')
    if tag:
        parts.append('<p><em>%s</em></p>' % tag.get_text(' ', strip=True))
    blurb = cover.select_one('.blurb')
    if blurb:
        parts.append('<p>%s</p>' % blurb.decode_contents().strip())

    body = soup.select_one('.body')

    # coloured die pips carry no text; the colour is already written out
    for sw in body.select('span.sw'):
        sw.decompose()

    # callouts -> blockquote with the label in bold, so they stay visibly apart
    for box in body.select('div.box'):
        lbl = box.select_one('.lbl')
        label = lbl.get_text(' ', strip=True) if lbl else ''
        if lbl:
            lbl.decompose()
        inner = box.decode_contents().strip()
        bq = BeautifulSoup(
            '<blockquote><p><strong>%s</strong>%s%s</p></blockquote>'
            % (label, ' &mdash; ' if label else '', inner), 'html.parser')
        box.replace_with(bq)

    # demote one level so the games sit above their sections
    for level in (3, 2):
        for h in body.find_all('h%d' % level):
            h.name = 'h%d' % (level + 1)

    foot = body.select_one('.foot')
    if foot:
        foot.decompose()

    parts.append(body.decode_contents())

html = ('<!DOCTYPE html><html><head><meta charset="utf-8">'
        '<title>The Nobulous Set - Rules</title></head><body>%s</body></html>'
        % '\n'.join(parts))
html = re.sub(r'<blockquote>\s*<p><strong></strong>', '<blockquote><p>', html)

src = os.path.join(HERE, '_editable.html')
out = os.path.join(HERE, 'Nobulous_Set_Rules_EDITABLE.docx')
open(src, 'w').write(html)
subprocess.run(['pandoc', src, '-f', 'html', '-t', 'docx',
                '-o', out], check=True)
os.remove(src)
print('wrote', out)
