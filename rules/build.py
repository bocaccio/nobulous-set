"""Rebuild the rulebook PDFs from the HTML sources.

    python3 build.py            # all four
    python3 build.py bat nap    # just those

Needs WeasyPrint:  pip install weasyprint
On Windows WeasyPrint also needs GTK; WSL or any Linux box is far easier.

The HTML files are the master copy. style.css controls every visual choice --
typeface, the two-column body, the coloured section bars, the boxes, the tables.
Editing text in the HTML is safe: it is ordinary prose between tags.

Useful patterns already in the stylesheet:

    <h2>Section bar</h2>              full-width coloured heading
    <h3>Sub-heading</h3>             accent-coloured, no bar
    <ol class="seq"> <li>...         numbered steps with circled numerals
    <div class="box">                tinted callout
      <span class="lbl">Label</span> ... its small caps heading
    <div class="box warn">           the same callout in warning orange
    <table><tr><th>..  <tr><td>..    rules table
    <span class="sw P"></span>       a coloured die pip: P B G Y R

Each file sets its own accent colour in the <style> block at the top.
"""
import sys, os
from weasyprint import HTML

HERE = os.path.dirname(os.path.abspath(__file__))
BOOKS = {
    'bat': 'BAT_Rulebook.pdf',
    'nap': 'NAP_Rulebook.pdf',
    'aos': 'AoS_Rulebook.pdf',
    'nrj': 'NRJ_Campaign_Supplement.pdf',
}

want = [a.lower() for a in sys.argv[1:]] or list(BOOKS)
for key in want:
    if key not in BOOKS:
        print('unknown book:', key, '- choose from', ', '.join(BOOKS))
        continue
    src = os.path.join(HERE, key + '.html')
    out = os.path.join(HERE, BOOKS[key])
    HTML(src).write_pdf(out)
    print('%-4s %s -> %s' % (key, os.path.basename(src), os.path.basename(out)))
