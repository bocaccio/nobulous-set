"""Assemble the per-deck PnP PDFs into one print-and-play file per game.

    python3 pack.py

Reads <deck>_PnP.pdf out of OUT and writes NobulousSet_<GAME>_PnP.pdf.
Two-sided decks are placed last in each file so the duplex pages are together
and a printer can be switched to double-sided for one contiguous run.
"""
import os
from pypdf import PdfReader, PdfWriter
from gen import OUT

# (stem, human label, two-sided?)
GAMES = {
    'BAT': [
        ('BAT_Encounters', '20 Encounters', False),
        ('BAT_Upgrades', '16 Upgrades', False),
        ('BAT_Specimens', '8 Specimens', False),
        ('BAT_TyrantAttacks', '7 Tyrant Attacks', False),
        ('BAT_Rats', '4 Lab Rats (A / B)', True),
        ('BAT_BuffHP', '1 Buff HP track', False),
    ],
    'NAP': [
        ('NAP_Tasks', '26 Tasks', False),
        ('NAP_Opportunities', '6 Opportunities', False),
        ('NAP_Setbacks', '6 Setbacks', False),
        ('NAP_FinalExams', '12 Final Exams', False),
        ('NAP_SlotsFINF', '3 Time Slots + FINF', False),
        ('NAP_Apprentices', '6 Apprentices on 3 cards', True),
    ],
    'AoS': [
        ('AoS_Limitations', '6 Limitations', False),
        ('AoS_ElementMats', '5 Element mats', False),
        ('AoS_Routine', '8 Routine Programs', True),
        ('AoS_Specialized', '8 Specialized Programs', True),
        ('AoS_Unstable', '8 Unstable Programs', True),
        ('AoS_Advanced', '8 Advanced Programs', True),
        ('AoS_Technicians', '6 Technicians on 3 cards', True),
    ],
    'NRJ': [
        ('NRJ_BAT_Protocols', '6 Experimental Protocols', False),
        ('NRJ_BAT_Modifications', '6 Unauthorized Modifications', False),
        ('NRJ_BAT_ResearchNotes', '6 Research Notes', False),
        ('NRJ_NAP_ImpostorTasks', '4 Impostor Tasks', False),
        ('NRJ_NAP_FollowingSetbacks', '4 Following Setbacks', False),
        ('NRJ_NAP_DeviousOpportunities', '6 Devious Opportunities', False),
        ('NRJ_AoS_Interference', '6 Nobulous Interference', False),
        ('NRJ_AoS_CorruptedLimitations', '6 Corrupted Limitations', False),
        ('NRJ_AoS_BackdoorRoutines', '6 Backdoor Routines', False),
        ('NRJ_ImposterScenarios', '24 Council Test Scenarios', False),
    ],
}


def build(game):
    w = PdfWriter()
    lines, page_no = [], 1
    for stem, label, duplex in GAMES[game]:
        src = os.path.join(OUT, stem + '_PnP.pdf')
        if not os.path.exists(src):
            lines.append('  MISSING  %s' % stem)
            continue
        r = PdfReader(src)
        n = len(r.pages)
        for p in r.pages:
            w.add_page(p)
        lines.append('  p%-3d %-30s %-34s %s'
                     % (page_no, stem, label,
                        'DUPLEX %d sheet(s)' % (n // 2) if duplex else '%d page(s)' % n))
        page_no += n
    out = os.path.join(OUT, 'NobulousSet_%s_PnP.pdf' % game)
    with open(out, 'wb') as f:
        w.write(f)
    return out, page_no - 1, lines


if __name__ == '__main__':
    report = []
    for g in ('BAT', 'NAP', 'AoS', 'NRJ'):
        out, pages, lines = build(g)
        print('%-4s %2d pages -> %s' % (g, pages, os.path.basename(out)))
        report.append('%s  (%d pages)' % (os.path.basename(out), pages))
        report += lines
        report.append('')
    with open(os.path.join(OUT, 'PNP_CONTENTS.txt'), 'w') as f:
        f.write('PRINT AND PLAY CONTENTS\n'
                'Letter paper, 9 cards per page (3 x 3), poker size 63.5 x 88.9 mm.\n'
                'Pages of landscape cards are themselves landscape - print at 100%,\n'
                'scale to fit OFF, and let the printer auto-rotate.\n\n'
                'Sections marked DUPLEX are genuinely two-sided: their pages alternate\n'
                'front / back with the back columns mirrored. Print those sheets\n'
                'double-sided, flip on the LONG edge.\n\n')
        f.write('\n'.join(report))
    print('contents ->', os.path.join(OUT, 'PNP_CONTENTS.txt'))
