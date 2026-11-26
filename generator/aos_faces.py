"""The two faces of an Assembly card, shared by build_aos.py and build_nrj.py.

An Assembly is not a Program with two moods. A Program's Regulated/Overheated
faces are the same card read twice; an Assembly's faces are two different
jobs, and the front deliberately conceals most of the back:

    FRONT   Build slots - every slot, repeats included - and the Advanced
            colors line, which names each colour the back will ask for
            exactly once. It reveals neither the number of elements nor any
            Target.
    BACK    the Advanced Program the built Assembly becomes in the finale:
            one (colour, Target) element per slot of the real thing.

Four of the nine print front slots in colours the back never asks for.
That is the concealment doing its job, so NOTHING here may derive one face
from the other - except the Advanced colors line, which is derived FROM the
back on purpose, because a stored copy could only drift.

This module lives apart from both build scripts because the Covert Sensor
Array ships in NRJ's print-and-play while the other eight ship in AoS's, and
a build script cannot be imported - it builds on import.
"""
from aos import COLOR_NAME, advanced_colors
from gen import DOT, elements

# Slot discs, the Advanced colors line, and the one-line hint under the
# slots. Appended to build_aos.py's BIG so both decks print identically; mm
# throughout, because card geometry has one owner and it is not this file.
# A SLOT IS A HOLE, NOT A DOT. Drawn as a thick coloured ring round the card
# stock so it reads as somewhere a Program goes, which a filled disc does not -
# the back's element dots are filled discs, and the two faces must not look
# like they are saying the same thing. The ring is a border rather than an
# inset box-shadow because WeasyPrint 69 renders the shadow as nothing at all
# and the slots came out solid.
#
# flex:none on both round things: a flex child with only width/height set gets
# stretched by align-items, and the colour dots came out as ovals.
ASSEMBLY_CSS = (
    '.slots{display:flex;align-items:center;justify-content:center;gap:3.6mm;margin:3mm 0 0}'
    '.slot{flex:none;width:9.6mm;height:9.6mm;border-radius:50%;box-sizing:border-box;'
    'border:1.8mm solid var(--c);background:#fbf9f3}'
    '.slothint{font-size:7.1pt;line-height:1.24;margin-top:2.4mm;color:#4a4239}'
    '.advcols{display:flex;align-items:center;justify-content:center;gap:4.4mm;'
    'margin-top:1.8mm;font-size:8.6pt;font-weight:bold}'
    '.advcols span{display:flex;align-items:center;gap:1.3mm}'
    '.advcols i{flex:none;width:3.6mm;height:3.6mm;border-radius:50%;display:inline-block;'
    'border:.4pt solid #6b6459}')

# A Program fills one slot and counts as one colour, so the footer has to say
# BOTH halves of that: which slot it may take, and that the choice is made
# once, when it goes in. "Two Purple slots require two separate Programs"
# follows from "one slot", and the rulebook spells it out.
FRONT_FTR = ('A cleanly&#8209;run Program fills 1 slot and counts as 1 of its '
             'required colors, chosen as it is installed.')
# At most one failed element across the whole finale, so the second one is
# what loses the game - printed that way round because that is the number a
# player is counting toward, not away from.
BACK_FTR = ('Reveal 1 Limitation. Recover before the next stage. '
            'A 2nd failed element across the finale loses the game.')


def assembly_front(name, build, back_elements, flavor, card, accent):
    """The design: what to build, and which colours it will later ask."""
    slots = ''.join('<div class="slot" style="--c:%s"></div>' % DOT[c] for c in build)
    cols = ''.join('<span><i style="background:%s"></i>%s</span>' % (DOT[c], COLOR_NAME[c])
                   for c in advanced_colors(back_elements))
    body = ('<div class="sub">Build</div>'
            '<div class="slots">%s</div>'
            '<div class="txt c slothint">Install a cleanly&#8209;run Program in each slot.</div>'
            '<div class="sub" style="margin-top:3.4mm">Advanced colors</div>'
            '<div class="advcols">%s</div>' % (slots, cols))
    return card(name, 'Assembly', body, FRONT_FTR, warn=False,
                acc=accent, flavor=flavor)


def assembly_back(back_name, back_elements, flavor, card, accent):
    """The finale side: one stage of the single final Program."""
    targets = [t for _, t in back_elements]
    dots = [c for c, _ in back_elements]
    body = elements(targets, dots)
    return card(back_name, 'Advanced Program &middot; Finale stage', body, BACK_FTR,
                warn=True, acc=accent, flavor=flavor)
