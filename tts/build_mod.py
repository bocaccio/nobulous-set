"""Build the Tabletop Simulator save file for The Nobulous Set.

Image hosting: TTS loads card sheets over HTTP, so the PNGs in cards/out must be
uploaded somewhere public first (Steam Cloud, GitHub raw, imgur, any static host).
Set BASE_URL below to the folder that will contain them, keeping the filenames.

    python3 build_mod.py                 -> NobulousSet.json using BASE_URL
    python3 build_mod.py --local /path   -> file:/// URLs, for solo testing only
"""
import ast, hashlib, io, json, os, sys, random

sys.path.insert(0, os.path.dirname(__file__))
from decks import DECKS, GAME_COLOR

# Where the images live. Set with --user / --repo / --ref, or edit GH_USER.
# GH_USER was "YOUR-GITHUB-USERNAME" until 2026-11-05, which meant the default
# build produced a mod whose every sheet URL 404s - it loads with no card
# faces. The repo's own remote names the owner, so this was never a guess.
# GH_REF stays "main" even when you build from a branch: these URLs are for
# the published mod and resolve once the branch merges. Pass --ref to aim at
# a branch, or --local to build file:/// URLs against SHEETS.
GH_USER, GH_REPO, GH_REF = "bocaccio", "nobulous-set", "main"
CDN = "https://cdn.jsdelivr.net/gh/%s/%s@%s"      # cached, fast, recommended
RAW = "https://raw.githubusercontent.com/%s/%s/%s"  # works, uncached
# The card sheets live under images/ and the rulebooks under rules/, so
# the templates above stop at the repo and these two name the folder.
BASE_URL = ""
RULES_URL = ""
# Repo-relative so this runs wherever the repo is checked out. The defaults
# used to be /home/claude paths from the sandbox that wrote the script, so
# OUT died with FileNotFoundError and SHEETS made REQUIRED_IMAGES.txt report
# every image MISSING. images/ is where deploy.py puts the TTS sheets and
# what the CDN template above already points at. The env vars still win.
_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.environ.get("TTS_OUT", os.path.join(_REPO, "tts", "NobulousSet.json"))
SHEETS = os.environ.get("TTS_SHEETS", os.path.join(_REPO, "images"))

rng = random.Random(20260823)
USED = set()

# The four boxes, left to right. IMP's two decks live in the NRJ box: the
# Imposter Scenario is NRJ's finale, not a fifth game.
# HOW BIG A CARD IS, and everything downstream of that.
#
# A die has to fit in a Buff HP box. That card prints a 3x5 grid of boxes
# each about 15% of the card's width; a TTS card is roughly 2.4 units wide
# and a TTS die about 0.9 across, so a box at scale 1 is 0.37 units and
# will not take one. 0.9 / (0.15 * 2.4) is 2.5, and 2.6 leaves a margin.
#
# TUNE IT HERE AND NOWHERE ELSE. The Lua lays the table out in multiples
# of CARD_W and CARD_L, which are derived below and generated into it, so
# the rows respace themselves rather than needing 30 literals edited.
# A LANDSCAPE DECK NEEDS A SMALLER NUMBER FOR THE SAME CARD. TTS sizes a
# SidewaysCard by its own aspect, so one scale applied to both
# orientations does not rotate a card - it enlarges it, by LONG/SHORT.
# At 2.6 the Lab Rats came out about 1.36x the portrait cards and
# overlapped at a gap of exactly one card. Scaled by SHORT/LONG they are
# the same card, turned.
# THE FELT, MEASURED AT THE TABLE AND NOT OFF A SCREENSHOT.
#
# Jon sized the overlay until it covered the table and stopped: scaleX
# 18.9679, scaleZ 18.0500, centre z -0.1645. At the mat's own aspect
# that is 56.5 across and 36.1 deep, z running -18.21 to 17.89. The
# guess it replaces was "about 56 by 37, z -18 to +19" - a table a
# unit and a half deeper than the real one, which is why the bottom
# row of dice hung over the edge and why the printed boxes and the
# cards were working from two different ideas of how big the table is.
#
# EVERY OTHER NUMBER IN THIS FILE THAT TOUCHES THE TABLE COMES FROM
# HERE, and so does the template and the harness.
FELT_X0, FELT_X1 = -28.25, 28.25
FELT_Z0, FELT_Z1 = -18.21, 17.89

CARD_SHORT, CARD_LONG = 2.4, 3.35
# 2.6 UNTIL THE FELT WAS MEASURED. Four rows of portrait cards plus a
# dice block have to fit in 36.1 units of depth, and at 2.6 they came
# to 38.4: the rows were sized against a table that was never there.
# This is the largest that leaves the dice their 3.7 - see dice_objects
# - and it is about 6% off a card, which is the price of the dice being
# the size Jon wanted them.
CARD_SCALE = 2.45
LAND_SCALE = CARD_SCALE * CARD_SHORT / CARD_LONG
CARD_W = CARD_SHORT * CARD_SCALE   # a portrait card, across
CARD_L = CARD_LONG * CARD_SCALE    # a landscape card, across - which is
                                   # the portrait card's long edge, because
                                   # that is all a rotation can make it

# THE LOWER RIGHT CORNER IS LEFT EMPTY ON PURPOSE: exhausted dice go
# there. Two Assignment columns wide - 2 x 8.5 - and it fills the gap
# between the lowest card edge at -16.26 and the front of the felt.
# Module level so tts/make_template.py can draw the space.
# (x from, x to, z top, z bottom)

# Filled in by dice_objects(), read by lua_header().
#
# TWO TABLES, BECAUSE THERE ARE TWO QUESTIONS. HOME_MARKERS answers
# "where does the Chip live", by name, for the four one-of-a-kind
# markers a setup moves about. MARKER_HOME answers "where did THIS
# object come from", by GUID, for every loose thing on the table -
# which is the question Pack up has to ask, because there are four
# Purple dice and one name between them. Keyed by name, Pack up sent
# one Purple home and left three where the game left them.
HOME_MARKERS = {}
MARKER_HOME = {}

# FOUR ROWS, ANCHORED TO THE BACK EDGE. The top row is landscape in
# every game, so it sits half a card's SHORT side below the felt's back
# edge and the rest follow at a card and a hair. Computed rather than
# written down: four literals that happened to fit a table nobody had
# measured is what this replaces.
ROW_PITCH = CARD_LONG * CARD_SCALE + 0.1
ROW_CHAR = FELT_Z1 - CARD_SHORT * CARD_SCALE / 2.0
ROW_MAIN = ROW_CHAR - ROW_PITCH
ROW_SIDE = ROW_CHAR - 2 * ROW_PITCH
ROW_TIER = ROW_CHAR - 3 * ROW_PITCH

# THE EXHAUSTED CORNER, in the same band the dice live in: from the
# bottom of the lowest card row to the back edge of the felt, and
# right of everything the dice row uses. It ran to -18.5 when the felt
# was thought to end at -18.6; the felt ends at -18.21.
EXHAUSTED = (10.0, 27.5, ROW_TIER - CARD_LONG * CARD_SCALE / 2.0,
             FELT_Z0 + 0.1)

# How big a die is. TTS scales an object by 0.1 a press, so this is the
# two presses that still leave room for two rows of them under the
# cards; see dice_objects(). The Chip is not a die and keeps its size.
DIE_SCALE = 1.8

# THE DIAL'S FIVE COLOURS, and where each one has to be turned to.
#
# THESE ARE NOT THE ART'S OWN ANGLES, whatever the comment here used to
# say. Read off the dial image itself - a 1 degree sweep of the colour
# ring, 2026-11-09 - the wedge centres sit at Red 233, Yellow 305,
# Green 17, Blue 89, Purple 161 clockwise from the top of the picture.
# Every number below is that, less 197. The constant difference is
# absorbed by CHIP_TRIM, so the pair still turns the dial correctly and
# the five numbers here are only meaningful together with it.
CHIP_SEGMENT = {'Red': 36, 'Yellow': 108, 'Green': 180,
                'Blue': 252, 'Purple': 324}

# How far past the top the turn lands. Turning each colour to minus its
# own segment put yellow on 1 but left the whole dial a half segment
# clockwise of the mark, so it came back 36 degrees - and that was 19
# too many, settled at the table with the panel +/-. THIS IS THE ONE
# NUMBER TO NUDGE if it is ever off again: 72 is a whole segment, and
# the sign is clockwise-positive.
CHIP_TRIM = -17

# WHICH WAY UP THE COLOURS ARE. Zero - the side the token spawns on.
#
# It was 180, and that is what put the dial on no colour in particular
# after the turn was finally firing: a Custom_Token with one image is
# an extruded disc with the art on top and the SAME ART MIRRORED
# underneath, so rotZ 180 shows a dial whose colours run the other way
# round. It still looks like a dial, which is why it read as a trim
# that had drifted rather than as the wrong face.
#
# The art measurement above settles it. Every colour's CHIP_ANGLE plus
# its own angle in the picture comes to 180, which means the colour is
# turned to the edge NEAREST THE PLAYER - the calibration Jon made with
# the panel's +/-, and the thing that is true only on the printed side.
CHIP_FACE_Z = 0

# THE OTHER FACE, which turned out to exist after all. Jon has both
# scans of the physical chip: the colour wheel, and a 0-20 dial with a
# sun in the middle. The official 20 Strong mod never modelled it - its
# Chip is a Custom_Token carrying one image, and a token with one image
# shows that image MIRRORED underneath - which is why the script spent
# weeks believing in a number side it could not turn to.
#
# A CUSTOM_TILE, NOT A TOKEN. Of the 2,611 Custom_Tokens in the mods on
# this machine not one carries a second image, and 2,991 of the 4,079
# Custom_Tiles do: the back face is a tile's feature, and the token's
# import dialog has only one image field. Type 2 is the circular tile,
# which is 1,839 of those.
CHIP_TILE_TYPE = 2
# TWO OBJECTS, ONE PER GAME, rather than one with a face each way up.
# Jon's call, and the right one: no game uses both faces, so nothing is
# lost, and what goes with the two-faced version is most of its cost -
# the Chip stays the Custom_Token every other marker is, nothing is
# ever flipped so it does not matter which way TTS draws an underside,
# the typing handler stops having to work out which way up a thing is,
# and each object carries its own RotationValues so TTS does the
# turning itself.
#
# A token at scale 1 is the size the Chip has always been, about 3.3
# units across; the tile needed 1.65 to match it.
CHIP_SCALE = 1.0

# WHERE THE NUMBERS ARE, measured off the dial scan. The olive moon
# marker sits at 327.8 degrees clockwise from the top of the picture
# and takes a slot of its own, so the rim holds 22 slots of 16.364
# degrees: the moon, then 0 through 20 running clockwise after it.
CHIP_DIAL_MARK = 327.8
CHIP_DIAL_SLOTS = 22
CHIP_DIAL_ZERO = CHIP_DIAL_MARK + 360.0 / CHIP_DIAL_SLOTS

# The nudge that lands the dial's numbers where the colour wheel's
# colours land - at the edge nearest the player. ONE NUMBER TO TURN if
# the dial reads off by a step: 16 degrees is one number, and the sign
# is clockwise-positive, exactly like CHIP_TRIM.
CHIP_DIAL_TRIM = 0


def chip_dial_angles():
    """y rotation that brings each number to the player's edge.

    THE DIAL IS ITS OWN OBJECT AND LIES FACE UP, so there is no
    mirroring to undo: a point at art angle A shows at A plus however
    far the object is turned, and the player's edge is 180. Exactly the
    arithmetic CHIP_ANGLE does for the colours.

    When the dial was the back of a two-faced tile this had to guess at
    how TTS hands a bottom face over, which was the last assumption in
    here that only the table could settle.
    """
    out = {}
    for n in range(21):
        art = (CHIP_DIAL_ZERO + n * 360.0 / CHIP_DIAL_SLOTS) % 360.0
        out[n] = int(round((180.0 - art + CHIP_DIAL_TRIM) % 360.0))
    return out


def die_image(nick):
    """A die's face filename, which carries its content hash.

    THE DICE ARE OURS NOW. dice_objects.json still holds the
    positions, scales and rotation values lifted from the official
    mod's dice, but every one of its CustomImage URLs pointed at a
    Steam upload of Chip Theory Games' art. tts/make_dice.py draws
    replacements; this finds them, and dice_objects() swaps the URL.
    """
    for f in sorted(os.listdir(SHEETS)):
        if f.startswith('Die_%s_' % nick) and f.endswith('.png'):
            return f
    raise SystemExit('no Die_%s image in images/ - run tts/make_dice.py'
                     % nick)


def chip_image(which):
    """The chip face's filename, which carries its content hash."""
    for f in sorted(os.listdir(SHEETS)):
        if f.startswith('Chip_%s' % which) and f.endswith('.png'):
            return f
    raise SystemExit('no Chip_%s image in images/' % which)

ATTENTION = ('Yellow', 'Green', 'Blue', 'Purple', 'Red')
CHIP_ANGLE = dict((c, (360 - a + CHIP_TRIM) % 360)
                  for c, a in CHIP_SEGMENT.items())

BOX_ORDER = ['BAT', 'NAP', 'AoS', 'NRJ']
BOX_TITLE = {'BAT': 'BAT  Build-a-Tyrant',
             'NAP': 'NAP  Apprenticeship Program',
             'AoS': 'AoS  Automaton of Shale',
             'NRJ': 'NRJ  Journal and Imposter finale'}
GENERATOR = os.path.join(_REPO, 'generator')


def _table(script, name):
    """The elements of a top-level list literal in a generator script."""
    src = io.open(os.path.join(GENERATOR, script), encoding='utf-8').read()
    for node in ast.parse(src).body:
        if isinstance(node, ast.Assign) and getattr(node.targets[0], 'id', '') == name:
            return node.value.elts
    raise SystemExit('%s has no %s table' % (script, name))


def nap_credit_tasks():
    """1-based Task indices per subject, READ OUT OF build_nap.py.

    NAP Tier II is the one tier swap that has to name individual cards:
    each of the 4 Imposter Tasks replaces a Credit Task of the same
    subject. A Task carrying a subject is a Credit Task; the six that
    carry None are not. Deriving it here means a reordered TASKS table
    cannot leave a stale index in the Lua.
    """
    out = {}
    for i, e in enumerate(_table('build_nap.py', 'TASKS'), 1):
        subj = getattr(e.elts[1], 'id', None)
        if subj:
            out.setdefault(subj, []).append(i)
    if len(out) != 4:
        raise SystemExit('expected 4 Task subjects, found %r' % (sorted(out),))
    return out


def nap_exam_subjects():
    """1-based Final Exam indices per subject, READ OUT OF build_nap.py.

    The exam pool is built per subject - 1 card at 0-1 Credits in it,
    2 at 2-3, 3 at 4+ - so the script has to know which of the twelve
    belong to which. The cards are nicknamed "Final Exam N" in EXAMS
    order, so the index is the whole of the answer and a reordered
    EXAMS table cannot leave a stale one behind.
    """
    out = {}
    for i, e in enumerate(_table('build_nap.py', 'EXAMS'), 1):
        subj = getattr(e.elts[1], 'id', None)
        if not subj:
            raise SystemExit('Final Exam %d carries no subject' % i)
        out.setdefault(subj, []).append(i)
    if len(out) != 4:
        raise SystemExit('expected 4 exam subjects, found %r' % (sorted(out),))
    return out


def nap_subject_names():
    """ANA -> 'Anatomy', read out of build_nap.py's own line.

    NAP_CREDIT is keyed by the CONSTANT name because that is what the
    TASKS table holds, and ANA is not what a player calls a subject.
    The printed name is on the card, so it comes from the same file
    rather than from a second list here that could drift from it.
    """
    src = io.open(os.path.join(GENERATOR, 'build_nap.py'), encoding='utf-8').read()
    for n in ast.parse(src).body:
        if (isinstance(n, ast.Assign) and len(n.targets) == 1
                and isinstance(n.targets[0], ast.Tuple)):
            names = [e.id for e in n.targets[0].elts
                     if isinstance(e, ast.Name)]
            try:
                vals = ast.literal_eval(n.value)
            except ValueError:
                continue
            if sorted(names) == ['ANA', 'ENG', 'PRO', 'THE']:
                return dict(zip(names, vals))
    raise SystemExit('build_nap.py no longer names the four subjects')


def duplex_characters(script, name, suffix=None):
    """A duplex character deck in (card, side, name) order.

    HALF AS MANY CARDS AS CHARACTERS. All three of these decks are
    rendered the same way - render_duplex(T[0::2], T[1::2]) - so card 1
    is the first name over the second, and so on. The panel picks one
    by name and has to know which card to deal and which way up;
    deriving both here means a reordered table cannot leave the panel
    showing a name on the wrong side of the wrong card.
    """
    names = []
    for e in _table(script, name):
        n = e.elts[0].value
        # AN IMPOSTER'S TWO SIDES ARE THE SAME PERSON. Apprentices and
        # Technicians are six people on three cards; the five Imposters
        # print two abilities each under one name, so without the side
        # letter the panel would offer "The Archivist" twice and the
        # player could not tell which ability they were picking.
        if suffix is not None:
            n = '%s %s' % (n, e.elts[suffix].value)
        names.append(n)
    if len(names) % 2:
        raise SystemExit('%s has %d %s, which does not pair into '
                         'two-sided cards' % (script, len(names), name))
    if len(set(names)) != len(names):
        raise SystemExit('%s %s does not name its characters uniquely: %s'
                         % (script, name, sorted(names)))
    out = []
    for i, (a, b) in enumerate(zip(names[0::2], names[1::2]), 1):
        out.append((i, 'front', a))
        out.append((i, 'back', b))
    return out


# The three games whose character is chosen from a two-sided stack, and
# the table each one's names are written in. BAT is not here: all four
# Lab Rats stay in play, so there is nothing to choose between them.
CHARACTERS = [('APPRENTICE', 'build_nap.py', 'APPS', None),
              ('TECHNICIAN', 'build_aos.py', 'TECHS', None),
              ('IMPOSTER', 'build_nrj.py', 'IMPOSTERS', 2)]


def buff_cells():
    """The 15 track cells on the Buff HP card, as offsets from its centre.

    MEASURED OFF THE PRINTED CARD, not counted out from the CSS that
    drew it. generator/build_bat.py lays the track as 5 rows of 3 pale
    squares, and a snap point is wanted in the middle of each so the
    Health die sits where the number is. Reading the rendered sheet
    means a redesign of that card moves the snap points with it; a grid
    typed out here would go on pointing at where the boxes used to be,
    and nothing at the table would say so.

    The cells are the pale fill (#f2eee2) inside a darker border, on a
    card body that is darker still, so they find themselves: scan for
    runs of that colour and keep the 15 biggest blobs.
    """
    from PIL import Image
    path = os.path.join(SHEETS, 'BAT_BuffHP_TTS.png')
    im = Image.open(path).convert('RGB')
    w, h = im.size
    px = im.load()

    def pale(x, y):
        r, g, b = px[x, y]
        return abs(r - 242) < 10 and abs(g - 238) < 10 and abs(b - 226) < 12

    # BY ROWS AND COLUMNS, NOT BY BLOB. The number printed in a cell's
    # corner cuts that cell's fill in two, and both halves are square
    # enough to pass for cells - which crowded a real one out of the
    # fifteen and put two snap points on top of each other. The track
    # is a grid, so find the grid: three bands of pale down the card
    # and five across, and the cells are where they cross.
    cols = [sum(1 for y in range(0, h, 2) if pale(x, y)) for x in range(w)]
    rows = [sum(1 for x in range(0, w, 2) if pale(x, y)) for y in range(h)]

    def bands(counts, floor, wide):
        # WIDE BANDS ONLY. The card's own cream border is the same
        # colour as a cell and runs the full height and width, so a
        # band narrower than half a cell is the margin, not a cell.
        out, start = [], None
        for i, v in enumerate(list(counts) + [0]):
            if v >= floor and start is None:
                start = i
            elif v < floor and start is not None:
                if i - start >= wide:
                    out.append((start + i - 1) / 2.0)
                start = None
        return out

    xs = bands(cols, max(cols) // 3, w // 12)
    ys = bands(rows, max(rows) // 3, h // 18)
    if len(xs) != 3 or len(ys) != 5:
        raise SystemExit('the Buff HP track reads as %d columns by %d rows,'
                         ' not 3 by 5' % (len(xs), len(ys)))
    cells = [(0, cx, cy) for cy in ys for cx in xs]
    out = []
    for _, cx, cy in cells:
        out.append(((cx / float(w) - 0.5) * CARD_SHORT * CARD_SCALE,
                    (0.5 - cy / float(h)) * CARD_LONG * CARD_SCALE))
    return out


def exhibit_blocks():
    """1-based index range of each Exhibit domain in build_nrj.py's SCEN.

    The finale deals 5 Knowledge, 5 Physical and 5 Cover-Up, so the Lua
    needs to know which indices are which. Each domain must be one
    contiguous run: if the table is ever interleaved, a range is the wrong
    shape for the job and this says so instead of dealing the wrong cards.
    """
    seen = {}
    for i, e in enumerate(_table('build_nrj.py', 'SCEN'), 1):
        seen.setdefault(e.elts[1].value, []).append(i)
    out = {}
    for dom, idx in seen.items():
        if idx != list(range(idx[0], idx[-1] + 1)):
            raise SystemExit('Exhibit domain %r is not contiguous: %r' % (dom, idx))
        out[dom] = (idx[0], idx[-1])
    return out


def lua_header(box_guids):
    """The generated block prepended to lua.lua: GUIDs and card indices."""
    # Both names map home: a deck is found by its label, a card by its
    # own name with the number stripped off.
    home = {}
    for d in DECKS:
        g = 'NRJ' if d['game'] == 'IMP' else d['game']
        home[d['label']] = g
        home[d.get('card', d['label'])] = g
    # Not decks, but they live in a bag and go home like one. The
    # Imposter scenario's cards are in the NRJ bag, so its overlay is
    # too.
    home['NAP Table'] = 'NAP'
    home['BAT Table'] = 'BAT'
    home['AoS Table'] = 'AoS'
    home['IMP Table'] = 'NRJ'
    home['Health Readout'] = 'BAT'
    # THE TWO FACES. Neither is dealt - both lie in the row at the
    # bottom of the table - but each has a box, because a setup stows
    # the one its game does not read. BAT reads the Dial, NAP reads
    # the Chip's colours, and AoS and the Imposter scenario read
    # neither.
    home['Chip'] = 'NAP'
    home['Dial'] = 'BAT'
    # Each game's rulebook goes home to that game's box. The Imposter
    # scenario is NRJ's finale, so its book is the campaign supplement
    # and it lives in the NRJ box with the rest of NRJ.
    for _g, _nick in RULES_NICK.items():
        home[_nick] = 'NRJ' if _g == 'IMP' else _g
    for _nick, _ in NAP_COUNTERS:
        home[_nick] = 'NAP'
    j = lambda xs: ', '.join(xs)
    return '\n'.join([
        '-- ================= GENERATED BY build_mod.py =================',
        '-- Box GUIDs come from the save being built; the two card-index',
        '-- tables are read out of generator/build_nap.py and build_nrj.py.',
        '-- Edit build_mod.py, never this block.',
        'CARD_SCALE = %.2f' % CARD_SCALE,
        'FELT = { x0 = %.2f, x1 = %.2f, z0 = %.2f, z1 = %.2f }' % (
            FELT_X0, FELT_X1, FELT_Z0, FELT_Z1),
        'ROW_PITCH = %.3f' % ROW_PITCH,
        'ROW_CHAR = %.3f' % ROW_CHAR,
        'ROW_MAIN = %.3f' % ROW_MAIN,
        'ROW_SIDE = %.3f' % ROW_SIDE,
        'ROW_TIER = %.3f' % ROW_TIER,
        'CARD_W = %.3f' % CARD_W,
        'CARD_L = %.3f' % CARD_L,
        'BOX = { %s }' % j("%s = '%s'" % (g, box_guids[g]) for g in BOX_ORDER),
        'HOME = { %s }' % j("['%s'] = '%s'" % (k, v) for k, v in sorted(home.items())),
        'CARD_NAME = { %s }' % j("['%s'] = '%s'" % (d['label'], d['card'])
                                 for d in DECKS if d.get('card')),
        # WHICH DECK A CARD BELONGS TO, both ways round: by the name a
        # card carries and by the deck's own label.
        #
        # A SETUP MERGES DECKS - the Opportunities and the Setbacks go
        # into the Assignment deck and the Opportunities deck ceases to
        # exist - so packing up and setting up again looked for a deck
        # that was not there any more and said MISSING DECK. This is
        # what lets the pack-up take the strangers back out of a deck
        # before it stows it.
        'DECK_OF = { %s }' % j(
            "['%s'] = '%s'" % (n, d['label'])
            for d in DECKS
            for n in dict.fromkeys([d.get('card') or d['label'], d['label']])),
        'CHIP_FACE = { %s }' % j('%s = %d' % (c, CHIP_ANGLE[c])
                                 for c in ATTENTION),
        # THE MEASUREMENT, NOT ONLY WHAT IT COMES TO. The panel carries
        # a +/- that turns the dial and prints the offset, so the script
        # needs the same two numbers CHIP_ANGLE is derived from - and
        # chipFaces() has to be the same arithmetic as the line above,
        # or the control would move the dial away from what the save
        # says. test_setup.py checks the two agree.
        'CHIP_SEGMENT = { %s }' % j('%s = %d' % (c, CHIP_SEGMENT[c])
                                    for c in ATTENTION),
        'CHIP_TRIM = %d' % CHIP_TRIM,
        # WHICH FACE, not only which angle. The save's RotationValues and
        # the setup's own turn both have to name the same side of the
        # token or typing a number and pressing Set up NAP disagree.
        'CHIP_FACE_Z = %d' % CHIP_FACE_Z,
        # HALF THE HEALTH READOUT'S WIDTH. The plate is built here, so
        # its size is settled here and the script is told; lua.lua
        # works out where it goes from this and the space it has.
        'BAT_READOUT_HW = %.2f' % READOUT_HW,
        # THE EXHAUSTED CORNER'S BAND, so the Lua can place things
        # against it without re-deriving it from ROW_TIER and the
        # felt. BAT stands its Health and REC dice in a column off
        # its left edge, and a band that moved while the column did
        # not would put two dice inside the corner they are meant to
        # sit beside.
        'EXHAUST_Z = {%.3f, %.3f}' % (EXHAUSTED[2], EXHAUSTED[3]),
        # BAT's dial: the angle that brings each number to the player's
        # edge. The object carries these as RotationValues too, so TTS
        # turns it when you type a number; the script needs them to set
        # the Tyrant's Health at setup.
        'CHIP_DIAL = { %s }' % j('[%d] = %d' % (n, a)
                                 for n, a in sorted(
                                     chip_dial_angles().items())),
    ] + [
        # Each choosable character: which card carries it, which way up.
        '%s = { %s }' % (var, j("{card = %d, back = %s, name = '%s'}"
                                % (c, 'true' if s == 'back' else 'false', n)
                                for c, s, n in duplex_characters(mod, tab, sfx)))
        for var, mod, tab, sfx in CHARACTERS
    ] + [
        # THE MAT'S OWN SHAPE, so the script can resize it at the
        # table. A stretched tile's local space is 1 deep by its
        # image's aspect wide, so world depth is 2 * scaleZ and world
        # width is 2 * aspect * scaleX - and the felt those were set to
        # cover was measured off a screenshot, which is why they are
        # adjustable rather than final.
        'MAT_ASPECT = %.5f' % (lambda wh: wh[0] / float(wh[1]))(
            jpeg_size(os.path.join(SHEETS, nap_table_image()))),
        'MAT_Z = %.2f' % NAP_TABLE_Z,
        # The Buff HP track's cells, so BAT can put a snap point in the
        # middle of each one. Measured off the printed card.
        'BUFF_CELL = { %s }' % j('{%.3f, %.3f}' % c for c in buff_cells()),
        'DIE_SCALE = %.2f' % DIE_SCALE,
        # THE ALT VIEW'S ANGLE FOR EACH FACE of a landscape card. The
        # save bakes the face-up one into every such card; the script
        # swaps them as cards are turned over, because one angle is
        # right for one face and upside down on the other.
        'ALT_LOOK_UP = {%d, %d, %d}' % ALT_LOOK_UP,
        'ALT_LOOK_DOWN = {%d, %d, %d}' % ALT_LOOK_DOWN,
        # WHICH BOOK BELONGS TO WHICH GAME, where a setup stands it,
        # and which way up. Four objects now rather than one whose URL
        # was swapped - see RULES_NICK for why.
        'RULES_NICK = { %s }' % j("%s = '%s'" % (g, RULES_NICK[g])
                                  for g in ('BAT', 'NAP', 'AoS', 'IMP')),
        'RULES_POS = {%.2f, %.3f, %.3f}' % RULES_POS,
        'RULES_ROT = {%d, %d, %d}' % RULES_ROT,
        # Where the four one-of-a-kind markers live when nothing has
        # borrowed them, so a setup can move them and Pack up can put
        # them back.
        'DICE_HOME = { %s }' % j("['%s'] = {%.2f, %.2f}" % (k, v[0], v[1])
                                 for k, v in sorted(HOME_MARKERS.items())),
        # ...and where every loose object on the table belongs, by
        # GUID, which is the only thing that tells four Purple dice
        # apart. Pack up reads this one.
        'MARKER_HOME = { %s }' % j("['%s'] = {%.2f, %.2f}" % (k, v[0], v[1])
                                   for k, v in sorted(MARKER_HOME.items())),
        'NAP_CREDIT = { %s }' % j('%s = {%s}' % (k, j(str(i) for i in v))
                                  for k, v in sorted(nap_credit_tasks().items())),
        'NAP_SUBJECT = { %s }' % j("%s = '%s'" % (k, v)
                                   for k, v in sorted(
                                       nap_subject_names().items())),
        'NAP_EXAM = { %s }' % j('%s = {%s}' % (k, j(str(i) for i in v))
                                for k, v in sorted(
                                    nap_exam_subjects().items())),
        'EXHIBIT_BLOCK = { %s }' % j("['%s'] = {%d, %d}" % (k, v[0], v[1])
                                     for k, v in sorted(exhibit_blocks().items())),
        '-- ======================= end generated =======================',
        '', ''])


def box(game, contained, x):
    r, g, b = GAME_COLOR[game]
    return {"GUID": guid(), "Name": "Bag",
            # Also dropped onto the rail on load; see panel() above.
            "Transform": xf(x, 5.20, 20.5, (0, 0, 0), 1.6),
            "Nickname": BOX_TITLE[game],
            "Description": "%d decks. A setup button takes out what it needs."
                           % len(contained),
            "ColorDiffuse": {"r": r, "g": g, "b": b},
            # Locked: a bag resting on the rail rolls off it otherwise,
            # and a locked bag still opens and still takes putObject.
            "Locked": True, "Grid": True, "Snap": True, "Autoraise": True,
            "Sticky": True, "MaterialIndex": -1, "MeshIndex": -1,
            "ContainedObjects": contained}


def guid():
    while True:
        g = ''.join(rng.choice('0123456789abcdef') for _ in range(6))
        if g not in USED:
            USED.add(g)
            return g


# How a deck sits in its bag: face down. The cards inside it have to
# agree - see card() - so this is named rather than written twice.
DECK_ROT = (0, 180, 180)

# WHICH WAY UP THE ALT VIEW HOLDS A LANDSCAPE CARD.
#
# Hold Alt over a Lab Rat and it came up on its side: the preview turns
# every card's long edge vertical, so the eleven landscape decks - the
# Rats, the Technicians, the Imposters, every NAP Task, Opportunity,
# Setback, Final Exam, Time Slot and FINF card, and NRJ's Imposter
# Tasks, Following Setbacks and Devious Opportunities - were read with
# your head tilted.
#
# SidewaysCard was already right: the sheets are 1050x750 cells and
# both the deck and every card inside it carry the flag, which is all
# TTS gives you for the TABLE. The Alt view is a separate thing with
# its own field, AltLookAngle, which is {0, 0, 0} on every object in
# every save on this machine - nobody had ever set one, so the preview
# was using its default.
#
# The TTS API says of alt_view_angle only that "when non-zero, the Alt
# view will use the specified Euler angle to look at the object". The
# z is the roll that matters here and the y is the card's own facing.
#
# ONE ANGLE CANNOT BE RIGHT FOR BOTH FACES. Flipping a card reverses
# the sense of the roll, so a single number is right for the side it
# was measured on and 180 degrees out on the other: the first value
# tried here was (0, 180, 90), which Jon reported as side B correct
# and side A - the side you actually read - upside down. The two
# differ by exactly that 180, and which one an object wants depends on
# which way up it is lying, so lua.lua sets it as cards are turned.
#
# THE SAVE BAKES THE FACE-UP ONE, because every landscape card this
# mod deals is dealt face-up, and because it is the fallback: if
# assigning alt_view_angle from a script turns out not to take on this
# build - as setCustomObject on a PDF did not - the front still reads
# correctly and only the backs are upside down, which is the better
# half of the trade rather than a new bug.
#
# AND DO NOT PRESS Q OR E IN THE ALT VIEW. Those rotate the preview and
# TTS saves the result onto the object, so one press on one card is a
# setting you then have to find; that is the mechanism behind every
# report of a deck that comes up sideways on one player's machine and
# not another's.
ALT_LOOK_UP = (0, 180, 270)
ALT_LOOK_DOWN = (0, 180, 90)


def alt_look(sideways):
    """The Alt view's angle for a card lying face up, if it needs one.

    Portrait cards get no field at all rather than an explicit zero:
    zero IS the default, and writing it would say this had been
    thought about for a card where there is nothing to think about.
    """
    if not sideways:
        return {}
    x, y, z = ALT_LOOK_UP
    return {"AltLookAngle": {"x": float(x), "y": float(y), "z": float(z)}}


def xf(x, y, z, rot=(0, 180, 0), s=1.0):
    return {"posX": x, "posY": y, "posZ": z, "rotX": rot[0], "rotY": rot[1], "rotZ": rot[2],
            "scaleX": s, "scaleY": s, "scaleZ": s}


_URL_HASH = {}


def url(name):
    """An image's URL, carrying its content hash as ?v=.

    MOST SHEETS DO NOT CARRY A HASH IN THEIR NAME. The table
    overlays and the eight dice do - make_template and make_dice
    rename them whenever the picture changes - but every card sheet
    and every card back is a fixed filename, so a re-rendered deck
    arrives at a URL TTS already holds in its cache and the old art
    goes on showing. The Tyrant Attack cards were lightened on
    2026-11-12 and would not have changed on the table.

    The rulebooks were given this token first, for the same reason
    and after the same symptom. jsdelivr resolves the file and
    ignores the token; TTS keys its cache on the whole string.

    Memoised, because url() is called once per card and some of
    these sheets are several megabytes.
    """
    u = "%s/%s" % (BASE_URL.rstrip('/'), name)
    if not BASE_URL.startswith('http'):
        return u          # file:// - a '?' there is part of the name
    if name not in _URL_HASH:
        p = os.path.join(SHEETS, name)
        _URL_HASH[name] = (hashlib.md5(io.open(p, 'rb').read()).hexdigest()[:8]
                           if os.path.exists(p) else None)
    # A missing file keeps its bare URL; REQUIRED_IMAGES.txt is what
    # reports it, and a token on a name that resolves to nothing
    # would only make the 404 harder to read.
    if not _URL_HASH[name]:
        return u
    return "%s?v=%s" % (u, _URL_HASH[name])


# THE FOUR RULEBOOKS, by the game key the script uses. IMP is not a
# fifth game - the Imposter Scenario is NRJ's finale - so it reads the
# campaign supplement, which is where that scenario is written down.
RULEBOOK = {'BAT': 'BAT_Rulebook.pdf', 'NAP': 'NAP_Rulebook.pdf',
            'AoS': 'AoS_Rulebook.pdf', 'IMP': 'NRJ_Campaign_Supplement.pdf'}
RULEBOOK_DIR = os.path.join(_REPO, 'rules')

# FOUR BOOKS, NOT ONE BOOK THAT CHANGES.
#
# It was one Custom_PDF and showRules swapped its URL with
# setCustomObject() and reload(), which is the documented way to do
# it. At Jon's table it did not take: his autosave after a NAP setup
# still held BAT_Rulebook.pdf as the object's own URL, so the call had
# not changed the object's DATA, let alone failed to fetch a file.
# There was no Lua error in the chat or in Player.log, the GUID the
# script looks the object up by is the one the object has, and the
# URL table it reads from is right - the mechanism simply does not
# work on this build.
#
# So the book is a component now, like the table overlay: each game's
# lives in that game's box and its setup deals it to the rail. Taking
# a thing out of a bag and putting it back is the one piece of
# machinery in this mod that has never let us down.
RULES_NICK = {'BAT': 'BAT Rules', 'NAP': 'NAP Rules',
              'AoS': 'AoS Rules', 'IMP': 'NRJ Rules'}
# WHERE JON PUT IT, read off his table rather than guessed at.
RULES_POS = (30.10, 3.622, 19.092)
RULES_ROT = (0, 180, 0)
RULES_SCALE = 1.25


def rules_hash(game):
    """The md5 of the book as it is on disk, eight hex, as the sheets use."""
    p = os.path.join(RULEBOOK_DIR, RULEBOOK[game])
    if not os.path.exists(p):
        raise SystemExit('%s is missing - run rules/build.py' % p)
    return hashlib.md5(io.open(p, 'rb').read()).hexdigest()[:8]


def rules_url(game):
    """One game's book, with its content hash carried as ?v=.

    THE PICTURE PROBLEM AGAIN, AND THIS WAS THE HALF LEFT UNDONE.
    Every image in this mod is named for its own content hash
    because a stable URL means both jsdelivr and TTS's own asset
    cache will go on serving a superseded copy - see table_image,
    where both of them did exactly that.

    The four books cannot take the same medicine: they are published
    deliverables, linked from the README and shipped inside
    print-and-play, so their FILENAMES have to stay put. A query
    token does the same work from the other end. jsdelivr resolves
    the file and ignores the token; TTS keys its cache on the whole
    URL string, so a revised book arrives as a URL nothing has ever
    fetched and cannot be answered from a cache.

    Jon read a NAP book on 2026-11-11 that was three revisions old
    while the CDN was serving the current one byte for byte. Nothing
    was wrong with the push, the file or the URL - the fetch simply
    never happened.
    """
    u = "%s/%s" % (RULES_URL.rstrip('/'), RULEBOOK[game])
    if not RULES_URL.startswith('http'):
        return u      # file:// - a '?' there is part of the filename
    return "%s?v=%s" % (u, rules_hash(game))


def rulebook(game, on_rail=False):
    """One game's rulebook. BAT's starts on the rail; the rest wait.

    It is NOT in settle() - settling would drop it onto whatever is
    under it and undo the placement.
    """
    pos = RULES_POS if on_rail else (0, 2.0, 0)
    return {"GUID": guid(), "Name": "Custom_PDF",
            "Transform": xf(pos[0], pos[1], pos[2], RULES_ROT, RULES_SCALE),
            "Nickname": RULES_NICK[game],
            "Description": "The rules for %s. Click the button, then zoom"
                           " in to read." % game,
            "Tooltip": True,
            "ColorDiffuse": {"r": 1.0, "g": 1.0, "b": 1.0},
            "Locked": True, "Grid": False, "Snap": False,
            "CustomPDF": {"PDFUrl": rules_url(game), "PDFPassword": "",
                          "PDFPage": 0, "PDFPageOffset": 0}}


def card(deck_id, idx, nickname, rot, s, sideways, desc=''):
    # A CONTAINED CARD CARRIES ITS OWN ROTATION, AND TTS HONOURS IT. The
    # deck was stored face down and every card inside it face up, which
    # is how TTS records a card someone has flipped over inside a deck.
    # So dragging one off the Assignment deck handed you a card turned
    # 180 degrees from the deck it came out of - it arrived upside down,
    # and only on that first drag, because from then on the card was
    # already turned. All 30 decks had it.
    #
    # Scale and SidewaysCard went the same way: a card out of a
    # landscape deck is a landscape card, at the deck's size.
    #
    # NO DEFAULTS. The bug was a default - xf(0, 0, 0) quietly meant
    # face up - and a default here hid the fix just as well: dropping
    # the caller's rot=DECK_ROT changed nothing and no check noticed,
    # because the signature put it back. The caller says.
    out = {"GUID": guid(), "Name": "Card", "Transform": xf(0, 0, 0, rot, s),
           "Nickname": nickname, "Description": desc, "CardID": deck_id * 100 + idx,
           "Locked": False, "Grid": True, "Snap": True, "Autoraise": True, "Sticky": True,
           "SidewaysCard": sideways}
    # THE CARD CARRIES IT, NOT JUST THE DECK. A card dragged off a deck
    # is a new object built from the entry inside it, so an angle set
    # on the deck alone is an angle the card you are actually holding
    # has never heard of - the same way SidewaysCard and the scale had
    # to go on both.
    out.update(alt_look(sideways))
    return out


def build_deck(d, deck_id, pos):
    # `sheet` and `first` let two decks share ONE face sheet and take
    # different slices of it, which is how a sheet whose cards need two
    # different backs is shipped: a TTS deck carries exactly one BackURL.
    # TTS addresses a card as deck_id * 100 + its index in the grid, so the
    # offset is all that is needed. See NAP_Slots / NAP_FINF in decks.py.
    sheet = d.get('sheet', d['key'])
    first = d.get('first', 0)
    face = url(sheet + '_TTS.png')
    back = (url(sheet + '_TTS_back.png') if d['back'] == 'unique'
            else url(d['back'] + '.png'))
    custom = {str(deck_id): {"FaceURL": face, "BackURL": back,
                             "NumWidth": d['w'], "NumHeight": d['h'],
                             "BackIsHidden": True, "UniqueBack": d['back'] == 'unique',
                             "Type": 0}}
    # A CARD IS NOT ITS DECK. The hover text on one card of Time Slots
    # read "Time Slots 2"; it is a Time Slot. `card` in decks.py names
    # the singular where it differs, and the Lua is told the mapping so
    # that it can still find a card by name.
    one = d.get('card', d['label'])
    scale = LAND_SCALE if d['land'] else CARD_SCALE
    contained, ids = [], []
    for i in range(first, first + d['count']):
        contained.append(card(deck_id, i, '%s %d' % (one, i - first + 1),
                              rot=DECK_ROT, s=scale,
                              sideways=bool(d['land'])))
        ids.append(deck_id * 100 + i)
    r, g, b = GAME_COLOR[d['game']]
    obj = {"GUID": guid(), "Name": "Deck" if d['count'] > 1 else "CardCustom",
           "Transform": xf(pos[0], pos[1], pos[2], DECK_ROT, scale),
           "Nickname": d['label'],
           "Description": "%s  |  %d cards" % (d['game'], d['count']),
           "ColorDiffuse": {"r": 1.0, "g": 1.0, "b": 1.0},
           "Locked": False, "Grid": True, "Snap": True, "Autoraise": True, "Sticky": True,
           "SidewaysCard": bool(d['land']),
           "DeckIDs": ids, "CustomDeck": custom, "ContainedObjects": contained}
    obj.update(alt_look(bool(d['land'])))
    if d['count'] == 1:
        obj.pop("DeckIDs")
        obj.pop("ContainedObjects")
        obj["CardID"] = deck_id * 100 + first
    return obj


def panel():
    return {"GUID": guid(), "Name": "Custom_Tile",
            # ON the rail, not behind it. At scale 2.6 the mat was 5.2
            # deep - deeper than the rail - so at z 21 most of it hung off
            # the back of the table and only the buttons, which float 0.5
            # above it, cleared the woodwork. At 2.0 it is 4 deep, and
            # z 20 puts its front edge at 18, just clear of the top dealt
            # row at 17.96. The height is above the rail rather than on
            # JUST ABOVE THE RAIL, AND LET IT FALL. 1.70, 2.20 and 3.00
            # buried the mat in the rail; 5.75, read off two cards that
            # turned out not to have been resting on it, floated it well
            # above. The height of that rail is not in the save and three
            # guesses and one bad measurement did not find it, so lua.lua
            # unlocks this on load, lets gravity put it on the surface,
            # and locks it where it lands. Start low enough that the drop
            # is short and it cannot bounce off onto the felt.
            "Transform": xf(0, 5.40, 20.0, (0, 180, 0), 2.0),
            "Nickname": "Control Panel",
            "Description": "Setup and counters for The Nobulous Set",
            "ColorDiffuse": {"r": 0.93, "g": 0.91, "b": 0.85},
            "Locked": True, "Grid": False, "Snap": False,
            "CustomImage": {"ImageURL": url("ControlPanel.png"), "ImageSecondaryURL": "",
                            "ImageScalar": 1.0, "WidthScale": 0.0,
                            "CustomTile": {"Type": 3, "Thickness": 0.1,
                                           "Stackable": False, "Stretch": True}}}


# THE NAP TABLE OVERLAY. A transparent PNG of the NAP layout, laid flat
# on the felt so the red shows through its outlines. It lives in the NAP
# bag like everything else, so the setup deals it and Pack up bags it.
#
# A stretched tile's local space is 1 deep by its image's aspect wide,
# so scale IS the half-depth: 18.8 covers z -18.6 to 19.0, and
# 18.8 * 2800/1880 is 28.0, which is the felt's half-width. The template
# is drawn to exactly that frame, so the two cannot disagree.
# THE MAT COVERS THE FELT EXACTLY, and both come from FELT above: half
# the depth is the scale, because a stretched tile's local space is 1
# deep by its image's aspect wide. The template is drawn at that same
# aspect, so the scale stays uniform and nothing in the picture is
# stretched - which it was, by 5%, when the mat was widened to the
# table without the drawing being redrawn to match.
NAP_TABLE_SCALE = (FELT_Z1 - FELT_Z0) / 2.0
NAP_TABLE_Z = (FELT_Z1 + FELT_Z0) / 2.0


# THE TWO READOUTS ABOVE NAP'S PILES.
#
# 3DText, not a tile: a tile needs an image, and these need TEXT that
# the script rewrites as cards land on the pile. rotX 90 lies the text
# flat on the table facing up - read off Jon's own save, which is also
# where the shape of this object came from.
#
# They live in the NAP box and are dealt by the NAP setup, like the
# table overlay, because the other three games have no piles to count.
NAP_COUNTERS = (
    ('Credit Record', 'CREDITS  0'),
    ('Banked Opportunities', 'BANKED  0'),
)


def counter(nick, text):
    return {"GUID": guid(), "Name": "3DText",
            "Transform": xf(0, 2.0, 0, (90, 0, 0), 1.0),
            "Nickname": nick,
            "Description": "Dealt by Set up NAP, above the pile it counts.",
            "Locked": True, "Grid": False, "Snap": False, "Tooltip": True,
            "Text": {"Text": text,
                     "colorstate": {"r": 1.0, "g": 1.0, "b": 1.0},
                     "fontSize": 52}}


def png_size(path):
    """(width, height) of a PNG, from its IHDR, for the same reason."""
    with open(path, 'rb') as fh:
        d = fh.read(24)
    if d[1:4] != b'PNG':
        raise SystemExit('%s is not a PNG' % path)
    return (int.from_bytes(d[16:20], 'big'), int.from_bytes(d[20:24], 'big'))


def jpeg_size(path):
    """(width, height) of a JPEG, without Pillow.

    Pillow's text engine is blocked on this machine by Windows Smart
    App Control and its image half may follow, so the one number the
    build needs out of this file is read from the file.
    """
    with open(path, 'rb') as fh:
        d = fh.read()
    i = 2
    while i < len(d) - 9:
        if d[i] != 0xFF:
            i += 1
            continue
        m = d[i + 1]
        if 0xC0 <= m <= 0xCF and m not in (0xC4, 0xC8, 0xCC):
            h = (d[i + 5] << 8) | d[i + 6]
            w = (d[i + 7] << 8) | d[i + 8]
            return w, h
        i += 2 + ((d[i + 2] << 8) | d[i + 3])
    raise SystemExit('no JPEG size in %s' % path)


def table_image(game):
    """A game's overlay filename, which carries its content hash.

    Found rather than named: tts/make_template.py renames it whenever
    the picture changes, so that no CDN and no TTS cache can serve a
    superseded one. Both of them did.
    """
    for f in sorted(os.listdir(SHEETS)):
        if f.startswith('%s_Table' % game) and f.endswith('.jpg'):
            return f
    return '%s_Table.jpg' % game


def nap_table_image():
    """The overlay's current filename, which carries its content hash.

    Found rather than named: tts/make_template.py renames it whenever
    the picture changes, so that no CDN and no TTS cache can serve a
    superseded one. Both of them did.
    """
    for f in sorted(os.listdir(SHEETS)):
        if f.startswith('NAP_Table') and f.endswith('.jpg'):
            return f
    return 'NAP_Table.jpg'


def dial_object(pos=(0, 1.4, 0)):
    """BAT's 0-20 dial: the Chip's other face, as an object of its own.

    IT LIES ON THE TABLE BESIDE THE CHIP, and is moved rather than
    dealt. It was in the BAT bag, which meant Pack up swallowed it;
    Jon wants it back in its place at the bottom of the table with the
    dice, which is exactly what the Chip already does. Only BAT reads
    it - the Tyrant's Health - and only NAP reads the Chip, so both
    simply wait their turn in the same row.

    ITS OWN ROTATION VALUES, so typing a number at it is TTS's job
    rather than the script's: twenty-one of them, one per number, from
    the same measurement of the scan that CHIP_DIAL comes from.
    """
    return {"GUID": guid(), "Name": "Custom_Token",
            "Transform": xf(pos[0], pos[1], pos[2], (0, 0, 0), CHIP_SCALE),
            "Nickname": "Dial",
            "Description": "The Tyrant's Health. Set up BAT turns it.",
            "ColorDiffuse": {"r": 1.0, "g": 1.0, "b": 1.0},
            "Locked": False, "Grid": True, "Snap": True,
            "Autoraise": True, "Sticky": True,
            "CustomImage": {"ImageURL": url(chip_image('Dial')),
                            "ImageSecondaryURL": "", "ImageScalar": 1.0,
                            "WidthScale": 0.0,
                            "CustomToken": {"Thickness": 0.2,
                                            "MergeDistancePixels": 15.0,
                                            "StandUp": False,
                                            "Stackable": False}},
            "RotationValues": [
                {"Value": n, "Rotation": {"x": 0, "y": a, "z": 0}}
                for n, a in sorted(chip_dial_angles().items())]}


# THE HEALTH READOUT'S PLATE, AND IT IS NOT A PLATE ANY MORE. It was
# the control panel's dark mat, small; Jon wanted it narrower and
# without the dark ground, so the image is a transparent one of its
# own and what you see is the three buttons and the outline the felt
# already draws under them.
#
# A stretched tile's local space is 1 deep by its image's aspect wide,
# so a uniform scale s makes it 2s deep and 2 * aspect * s across. The
# half width is the one number lua.lua and this file both read, and
# the aspect is what sets where the buttons go inside it.
READOUT_HW = 2.0
READOUT_IMAGE = 'DialPlate.png'


def readout_object():
    """BAT's Health readout: a plate beside the Dial, with +/- buttons.

    IT CARRIES NO BUTTONS HERE. lua.lua draws them, as it does for the
    rulebook, because the label in the middle is the Tyrant's Health
    and changes; a button written into the save would be a number
    frozen at whatever it was when this file ran.
    """
    aspect = (lambda wh: wh[0] / float(wh[1]))(
        png_size(os.path.join(SHEETS, READOUT_IMAGE)))
    return {"GUID": guid(), "Name": "Custom_Tile",
            "Transform": xf(0, 1.2, 0, (0, 180, 0), READOUT_HW / aspect),
            "Nickname": "Health Readout",
            "Description": "The Tyrant's Health, with a button each side.",
            "ColorDiffuse": {"r": 1.0, "g": 1.0, "b": 1.0},
            "Locked": True, "Grid": False, "Snap": False,
            "CustomImage": {"ImageURL": url(READOUT_IMAGE),
                            "ImageSecondaryURL": "", "ImageScalar": 1.0,
                            "WidthScale": 0.0,
                            "CustomTile": {"Type": 3, "Thickness": 0.1,
                                           "Stackable": False,
                                           "Stretch": True}}}


def game_table(game):
    """The printed layout a setup lays down. One shape, two pictures.

    NAP's and BAT's overlays are the same tile stretched over the same
    felt; only the drawing differs, so there is one builder rather than
    two that could drift apart in scale or in which way up they go.
    """
    return {"GUID": guid(), "Name": "Custom_Tile",
            "Transform": xf(0, 0.98, NAP_TABLE_Z, (0, 180, 0),
                            NAP_TABLE_SCALE),
            "Nickname": "%s Table" % game,
            "Description": "The %s layout. Set up %s lays it down."
                           % (game, game),
            "ColorDiffuse": {"r": 1.0, "g": 1.0, "b": 1.0},
            "Locked": True, "Grid": False, "Snap": False,
            "Tooltip": False,
            "CustomImage": {"ImageURL": url(table_image(game)),
                            "ImageSecondaryURL": "", "ImageScalar": 1.0,
                            "CustomTile": {"Type": 0, "Thickness": 0.05,
                                           "Stackable": False,
                                           "Stretch": True}}}



# A DIE WITH NO ROTATION VALUES CANNOT BE SET TO A NUMBER. These carried
# none, so nothing - not a script, not typing a number over one - could
# put a 2 face up.
#
# MEASURED, NOT ASSUMED. TTS's own d6 arrangement was the obvious guess
# and it was wrong for these faces: typing 1 to 6 on it produced 2, 4,
# 1, 6, 3, 5. So each rotation now carries the value it actually shows.
# The 5 also takes a 180 turn about Y, because flipping about X alone
# brings that face up upside down.
D6 = [{"Value": 1, "Rotation": {"x": -90, "y": 0, "z": 0}},
      {"Value": 2, "Rotation": {"x": 0, "y": 0, "z": 0}},
      {"Value": 3, "Rotation": {"x": 0, "y": 0, "z": -90}},
      {"Value": 4, "Rotation": {"x": 0, "y": 0, "z": 90}},
      {"Value": 5, "Rotation": {"x": 180, "y": 180, "z": 0}},
      {"Value": 6, "Rotation": {"x": 90, "y": 0, "z": 0}}]


def dice_objects():
    # Checked in beside this script, so read it from there rather than
    # from the machine it was first written on - that hardcoded path
    # meant build_mod.py could not run anywhere else at all.
    src = json.load(open(os.path.join(os.path.dirname(
        os.path.abspath(__file__)), 'dice_objects.json')))
    out = []
    # ONE ROW ALONG THE BOTTOM, UNDER EVERY CARD. Still a 2x2 block per
    # colour - four in a line reads as a queue, not a pool - but the
    # blocks run left to right instead of down the left edge, which is
    # what leaves the lower right corner free for exhausted dice.
    #
    # The lowest card row reaches z -16.26, so the blocks sit at -16.9
    # and -17.9. Every number in here is spoken for.
    # THE BAND UNDER THE CARDS, AND THE WHOLE OF IT. A die is about a
    # unit across at scale 1, so 1.8 here, and a 2x2 block of them is
    # DROP + 1.8 deep. The band runs from the bottom of the lowest card
    # row to the back edge of the felt, and the pair of rows is centred
    # in it - so moving a card row moves the dice, rather than leaving
    # them where a previous felt put them.
    strip_top = ROW_TIER - CARD_L / 2.0
    DROP = 1.9
    DICE_Z = (strip_top + FELT_Z0) / 2.0 + DROP / 2.0
    ORDER = ('Pink', 'Purple', 'Blue', 'Green', 'Yellow')
    BLOCK0, BLOCK_PITCH = -27.0, 4.3
    BLOCK = dict((n, BLOCK0 + i * BLOCK_PITCH) for i, n in enumerate(ORDER))
    OFFS = ((0.0, 0.0), (1.9, 0.0), (0.0, -DROP), (1.9, -DROP))
    # The Chip and the three utility dice follow the colours along the
    # same row, and all of it stops well left of the exhausted corner.
    # The Chip and the three stat dice follow the blocks along the same
    # band, in one row now that a die is 1.8 across.
    lay = {'Chip': (-4.8, DICE_Z - DROP / 2),
           'Health': (-2.0, DICE_Z), 'Strategy': (0.0, DICE_Z),
           'Recovery': (2.0, DICE_Z),
           # Right of the three stat dice and left of where BAT's
           # exhausted corner begins.
           'Dial': (4.6, DICE_Z - DROP / 2)}
    HOME_MARKERS.update(lay)
    seen = {}
    for o in src:
        nick = o.get('Nickname') or 'Die'
        seen[nick] = seen.get(nick, 0) + 1
        if nick in BLOCK:
            ox, oz = OFFS[(seen[nick] - 1) % len(OFFS)]
            bx, bz = BLOCK[nick] + ox, DICE_Z + oz
        else:
            bx, bz = lay.get(nick, (0.0, DICE_Z))
        # BY GUID, NOT BY NAME. There are four Purple dice and one
        # name between them, so a table keyed by nickname sends one of
        # them home and leaves three where the game left them - which
        # is what Pack up had been doing to fourteen of the seventeen.
        d = {"GUID": guid(), "Name": o['Name'],
             "Transform": xf(bx, 1.4, bz, (0, 0, 0),
                             DIE_SCALE if o['Name'] == 'Custom_Dice' else 1.0),
             "Nickname": 'Red' if nick == 'Pink' else nick,
             "Description": o.get('Description') or '',
             "ColorDiffuse": o.get('ColorDiffuse') or {"r": 1, "g": 1, "b": 1},
             "Locked": False, "Grid": True, "Snap": True, "Autoraise": True, "Sticky": True,
             "CustomImage": o['CustomImage']}
        if o['Name'] == 'Custom_Dice':
            d["RotationValues"] = [dict(v) for v in D6]
            # OUR FACE, NOT THE ONE THE FILE CAME WITH. Keyed on the
            # nickname the object ends up with, so the one Pink die
            # in dice_objects.json looks up Die_Red like the rest.
            d['CustomImage'] = dict(
                o['CustomImage'], ImageURL=url(die_image(d['Nickname'])))
        if nick == 'Chip':
            # OUR OWN COPY OF THE FACE, so the pair of scans that the
            # dial's angles were measured from is the pair that ships.
            d['Transform'] = xf(bx, 1.4, bz, (0, 0, 0), CHIP_SCALE)
            d['CustomImage'] = dict(
                o['CustomImage'], ImageURL=url(chip_image('Colour')))
            # THE DIAL NEEDS ROTATION VALUES TOO - typing a number over
            # it did nothing until it had them - and they have to be the
            # SAME angles the script turns it to, so CHIP_ANGLE owns
            # both and lua_header() generates the Lua copy.
            d["RotationValues"] = [
                {"Value": i + 1,
                 "Rotation": {"x": 0, "y": CHIP_ANGLE[c],
                              "z": CHIP_FACE_Z}}
                for i, c in enumerate(ATTENTION)]
        MARKER_HOME[d['GUID']] = (bx, bz)
        out.append(d)
    # The Dial is loose on the table too, beside the Chip, so it goes
    # home with everything else rather than into a bag.
    dx, dz = lay['Dial']
    dial = dial_object((dx, 1.4, dz))
    MARKER_HOME[dial['GUID']] = (dx, dz)
    out.append(dial)
    return out


def notebook():
    tabs = []
    for title, body in [
        ("How to use this mod",
         "FOUR BAGS hold every card, one per game, along the back rail.\n"
         "You never open them by hand: a setup button takes out what that\n"
         "game needs, performs the printed setup, and leaves the rest in\n"
         "the bag.\n\n"
         "ON THE CONTROL PANEL, in this order:\n\n"
         "  1. Difficulty -- Easy / Standard / Hard / Nobulous.\n"
         "  2. NRJ Tier -- off / I Agenda / II Contamination / III\n"
         "     Exploitation. BOTH are read when you press a setup button,\n"
         "     so set them FIRST. Changing either afterwards does nothing\n"
         "     until you press setup again.\n"
         "  3. Set up BAT / NAP / AoS / Imposter.\n"
         "  4. Start the Final Exam / the Tyrant Battle / Advanced\n"
         "     Programming -- the bottom row, once a game is dealt.\n\n"
         "WHAT A SETUP BUTTON ACTUALLY DOES, so you can check it:\n\n"
         "  BAT  -- deals the four Lab Rats, shuffles the Experiments and\n"
         "          the Tyrant Attacks, and shuffles your difficulty's\n"
         "          Specimens into the 16 Upgrades.\n"
         "  NAP  -- builds the Assignment deck: 26 Tasks + 6 Opportunities\n"
         "          + your difficulty's Setbacks, shuffled together, with\n"
         "          Morning active and one FINF card drawn.\n"
         "  AoS  -- builds the 8-card Program deck from your difficulty's\n"
         "          mix of Routine / Specialized / Unstable, shuffles the\n"
         "          Limitations, sets the Advanced Programs aside and lays\n"
         "          out the five element mats.\n"
         "  Imposter -- deals the 15-card Dossier, 5 Knowledge + 5 Physical\n"
         "          + 5 Cover-Up at random from the 24 Exhibits, and puts\n"
         "          the Research Pool out face-up.\n\n"
         "The TIER SWAPS happen too: the Modifications replacing 6 ordinary\n"
         "Upgrades, the Following Setbacks going in one-for-one, the Imposter\n"
         "Tasks replacing a Credit Task of each subject, the Devious\n"
         "Opportunities replacing the base six, the Corrupted Limitations\n"
         "shuffled in. Read the setup message in chat: it names every number\n"
         "it just used.\n\n"
         "Apprentice / Technician / Imposter -- the row under the\n"
         "  difficulty, once a game is dealt. Every character card is two\n"
         "  characters, one per side; press it to cycle through all of\n"
         "  them, card and side, and it deals the one it names. BAT has\n"
         "  no such button - you play all four Lab Rats.\n"
         "Start the Final Exam / the Tyrant Battle / Advanced\n"
         "  Programming -- the last part of each game, which you reach\n"
         "  by playing rather than by setting it up. It puts away the\n"
         "  cards that part of the game is finished with, deals the\n"
         "  ones the finale needs, and says in chat the steps you do\n"
         "  by hand -- which are mostly dice. Once per game: the\n"
         "  button leaves the panel after it is used.\n"
         "Pack up -- everything, including loose cards, goes back in its\n"
         "  bag.\n\n"
         "The script deals and counts. It never enforces a rule in play."),
        ("BAT quick reference",
         "SPLICE PHASE, a turn: reveal the next Experiment; reveal 2 Upgrades\n"
         "(+1 Target if either is a Specimen, once only even for two); choose\n"
         "the active Rat and put the Recovery die on it; place the set-aside\n"
         "Red on a NON-active Rat; commit, roll, resolve; exhaust the dice you\n"
         "committed and recover that Rat's REC.\n\n"
         "Success: successes at or over the Target, and the printed\n"
         "restriction honored. The active Rat takes one of the two revealed\n"
         "Upgrades (max 3 per Rat, Specimens counting) and discards the other.\n"
         "Failure: Splice the stronger revealed Upgrade into the Tyrant and\n"
         "discard the other; on a tie choose either. Committing nothing is a\n"
         "legal choice - the Experiment fails, the stronger Upgrade is\n"
         "Spliced, recovery still happens, and it earns no bonus.\n"
         "Five Splices awaken the Tyrant. You cannot avoid this - the game is\n"
         "about WHICH five cards it gets. If the Experiment deck runs out\n"
         "first, random unused Upgrades bring it to exactly 5 and the battle\n"
         "begins; running out of UPGRADES is not a malfunction, reshuffle\n"
         "their discard.\n\n"
         "DIFFICULTY sets the Specimens shuffled in with the 16 Upgrades and\n"
         "the Tyrant's HEALTH:\n"
         "  Easy 5 and 9   Standard 6 and 10   Hard 7 and 12   Nobulous 8 and 14\n"
         "Set the Health DIAL to that number. The Buff HP card is optional:\n"
         "hold part of the Tyrant's Health on the track instead of the dial,\n"
         "and the die goes on that many spaces. It is the FRONT layer, so it\n"
         "comes off before any Splice can be damaged - which means the five\n"
         "Splices shelter behind it at full strength while you carve it away.\n"
         "Moving a point from the dial to the track makes the game harder.\n\n"
         "BORROWING, one available non-Red die from another Rat, before either\n"
         "Strategy roll. The more Upgrades you already hold, the worse the die\n"
         "you may take:\n"
         "  0 Upgrades held: Purple, Blue, Green or Yellow\n"
         "  1: Blue, Green or Yellow   2: Green or Yellow   3: Yellow only\n"
         "Roll it by itself afterwards: on a miss it is banished from the game\n"
         "for good, on a hit or Crit it goes home exhausted.\n\n"
         "RED is communal, is never banished, and belongs to no workbench. The\n"
         "Rat holding it may commit it normally. After use it is set aside\n"
         "rather than exhausted, then placed on a NON-active Rat at the start\n"
         "of the next turn; if it was not used, that step is skipped.\n\n"
         "THE BATTLE, a round:\n"
         "1 Untap every Upgrade tapped last round.\n"
         "2 Choose the attacking Rat from those still standing and move the\n"
         "  Recovery die to it. Rat abilities are silent in the battle.\n"
         "3 Commit as many dice from the shared pool as you like, honoring the\n"
         "  commit color, and roll - no limit, but you only get REC + 2 back.\n"
         "  A hit is 1 damage, a Crit 2; STR 2 gives a second Strategy roll.\n"
         "4 Either tap ONE Upgrade or commit Red, not both; neither is also\n"
         "  fine. A tapped card cannot absorb damage until it untaps.\n"
         "5 Apply the damage left to right.\n"
         "6 Recover REC + 2 of the dice you just committed. The rest exhaust.\n"
         "7 At 0 Tyrant Health the Rats win; otherwise the Tyrant attacks.\n"
         "Eight rounds and it breaks containment: eight attacks, five walls.\n\n"
         "COMMIT COLOR. Every Tyrant Attack card prints a colored dot in its\n"
         "title band (3 Green, 3 Yellow, 1 Blue), and the one that counts is\n"
         "on top of the Attack discard - the card flipped up at setup supplies\n"
         "the first. An attacking Rat must commit at least one die of that\n"
         "color, or two dice of a single other color if the pool holds none of\n"
         "it. Red never counts toward the commit color.\n\n"
         "THE TYRANT TRACK, left to right: the Buff HP layer if you are using\n"
         "one, the five Splices in a RANDOM order, then Health. That is the\n"
         "order damage has to chew through, and a Splice does NOT chip - your\n"
         "blow must meet its printed Value in this one attack or it bounces\n"
         "off and the whole attack is wasted. Meet it and the Splice is\n"
         "destroyed outright and the remainder carries on, and whatever\n"
         "survives all five comes off Health. The Buff track and the dial are\n"
         "the two things that DO chip.\n"
         "Each Splice you break banishes one pool die of its own color, or any\n"
         "die if none of that color is left. On the Tyrant a Splice is only\n"
         "its Value: it never taps and a Splice's printed effect is never\n"
         "used.\n\n"
         "A RAT'S UPGRADE IS THE OTHER KIND OF ARMOR, and neither kind chips.\n"
         "It stops an attack dead whatever the blow was worth, and it is\n"
         "spent: discard it. At most one Upgrade is lost and nothing carries\n"
         "over. Only a Rat with no untapped Upgrade takes damage to its\n"
         "Health, and a Rat at 0 Health is knocked out, its Upgrades\n"
         "discarded, and cannot be chosen to attack again.\n\n"
         "The Tyrant's six dice come out of the Rats' own supply - 2 Purple /\n"
         "2 Blue / 1 Green / 1 Yellow, kept in a bag and never exhausting -\n"
         "and it draws as many as the highest Value among the Splices it still\n"
         "holds, 2 if it holds none. In the BATTLE Red is not in the shared\n"
         "pool and is not passed around: the attacking Rat may commit it, but\n"
         "only if they do not tap an Upgrade as part of that attack.\n\n"
         "The RECOVERY die marks the active Rat all game, and moves to the\n"
         "attacking Rat in the battle. The Health DIAL runs the Tyrant track.\n"
         "A Rat's own Health, STR and REC are printed on its card, so the\n"
         "Strategy die is not used."),
        ("NAP quick reference",
         "Three Time Slots a day, Morning / Afternoon / Evening, then End of\n"
         "Day. A SLOT:\n"
         "1 Special Recovery: recover ALL exhausted dice of the color on the\n"
         "  dial. Day 1 Morning has nothing queued, so there is none.\n"
         "2 Reveal 2 Assignments, place one in the row as the Primary and\n"
         "  discard the other. A Setback must be taken; if both are Setbacks,\n"
         "  take the one with the higher Target. A card with Skulls adds that\n"
         "  many cards from the deck to the slot.\n"
         "3 Attempt Assignments with Strategy rolls.\n"
         "4 Rotate or discard what is unresolved, exhaust non-stored\n"
         "  committed dice, set the dial to the Primary's dot and advance the\n"
         "  chip. Do NOT recover again - the dial you just set is what the\n"
         "  next slot recovers in step 1.\n\n"
         "REC HAPPENS ONLY AT END OF DAY. Inside the day, dice come back\n"
         "through Special Recovery or a card effect and nowhere else.\n\n"
         "STR is the number of Strategy rolls in a slot, and it resets every\n"
         "slot. IT DOES NOT CAP HOW MANY ASSIGNMENTS YOU MAY COMPLETE: one\n"
         "roll's successes can be spread across several Assignments, and\n"
         "cards already holding stored progress can finish alongside them.\n"
         "Clearing more Assignments than you have rolls is normal - it is\n"
         "what storing progress is for.\n\n"
         "THE COLOR RULE. To commit, choose at least one Assignment - a\n"
         "Setback if one is present - and commit either one die matching that\n"
         "card's color dot, Red, or at least two dice of another color. To\n"
         "complete a card or store progress on it, the successes you apply\n"
         "must include that same legal die; after that you may add successes\n"
         "from any other committed die.\n\n"
         "A slot holds at most 4 Assignments. If the row is already full when\n"
         "you reveal, discard both revealed cards and take nothing - and the\n"
         "dial does not change, so the next slot recovers the same color\n"
         "again. Assignments stay in their own slot and never follow you into\n"
         "the next one.\n\n"
         "UNRESOLVED at the end of a slot: a Task flips to its Demand side,\n"
         "harsher and often a higher Target, which costs nothing by itself.\n"
         "An Opportunity instead rotates 180 for one last chance in that slot\n"
         "the following day, and can never hold stored progress. A card\n"
         "ALREADY on Demand inflicts its printed penalty and is discarded.\n"
         "Successful dice may be stored on an unresolved card rather than\n"
         "exhausted, and once the next slot begins they are locked to it.\n\n"
         "Completed cards rotate 90 and stay in their slot until End of Day.\n"
         "Tasks are the only source of Credits, and a Credit Task completed\n"
         "on its Demand side still counts. An Opportunity pays nothing on the\n"
         "spot: keep the card in front of you as a coupon and spend it\n"
         "whenever you like, on any Day, the Final Exam included.\n\n"
         "END OF DAY: clear the completed cards to the discard, reveal and\n"
         "discard the top Assignment card ignoring all of its text, effects\n"
         "and Skulls, then recover exhausted dice equal to your REC.\n\n"
         "SKULLS resolve only on Assignments YOU chose. Ignore them on cards\n"
         "added by another Skull, by FINF, or by a forced replacement. If a\n"
         "Skull would add a card while the slot already holds 4, add nothing\n"
         "and instead rotate the Skull-generating Assignment to its Demand\n"
         "side once; further blocked Skulls do nothing.\n\n"
         "FINF is a second dial, independent of difficulty, set once and kept\n"
         "for the whole game. INCREASE 1-3 shuffles that many FINF cards into\n"
         "the deck: a drawn one adds an Assignment from the top of the deck to\n"
         "the matching Time Slot, ignoring that card's Skulls and never\n"
         "passing 4 in one row. REDUCE 1-3 keeps them face-up, one use each:\n"
         "spend the card numbered for the ACTIVE slot to remove a\n"
         "non-Final-Exam card from it, exhausting every die stored on it.\n"
         "FINF is not used during the Final Exam, in either direction.\n\n"
         "DIFFICULTY is the Credit goal and the Setbacks in the deck:\n"
         "  Easy 5 and 3   Standard 6 and 3   Hard 7 and 4   Nobulous 8 and 5\n"
         "The exam begins at the END of a Day, never part-way through one, so\n"
         "a goal reached in a Morning still plays out the Afternoon and the\n"
         "Evening - and every Credit ABOVE the goal recovers another die in\n"
         "Preparation. An empty Assignment deck sends you to the exam as\n"
         "well, and that one ends the apprenticeship immediately, with the\n"
         "slots that are left unplayed. Health reaching 0 loses on the spot,\n"
         "during the apprenticeship or during the exams.\n\n"
         "LEAVING THE APPRENTICESHIP: discard unresolved Assignments and\n"
         "exhaust their stored dice. Short of your Credit goal, exhaust 1\n"
         "available die per missing Credit in the order Red, Purple, Blue,\n"
         "Green, Yellow, looping as needed.\n"
         "PREPARATION: recover 1 exhausted die, then 1 more per Credit above\n"
         "the goal, never the same color twice, then perform the queued\n"
         "Morning Special Recovery.\n\n"
         "FINAL EXAM. Place cards into the pool per subject by the Credits you\n"
         "hold in it - 0-1 Credits 1 card, 2-3 two, 4+ three - then shuffle\n"
         "and draw 3. Each exam's base Target drops by 1 per Credit in its\n"
         "subject, and you lose 1 Health per success short. Honor the printed\n"
         "restriction, then Special Recover on that exam card's own color dot\n"
         "before the next one. All three are mandatory; survive all three\n"
         "with at least 1 Health to win."),
        ("AoS quick reference",
         "RUNNING A PROGRAM. This order matters more than anything else in\n"
         "the game:\n"
         "1 Reveal the Program: a row of elements, each with a Target, one\n"
         "  of them ringed as the overheat marker.\n"
         "2 Reveal exactly 1 Limitation. Withheld dice sit out this Program\n"
         "  altogether - not even for a required color.\n"
         "3 Commit required-color dice. Every colored dot beside an element\n"
         "  takes one available die of that color NOW, and it locks there.\n"
         "4 Finish the allocation. EVERY ELEMENT MUST RECEIVE AT LEAST ONE\n"
         "  DIE, and at most its Target + 1 unless a card raises that cap.\n"
         "  Hold fewer dice than the Program has elements and the ones left\n"
         "  bare fail.\n"
         "5 Execute: roll each element and resolve it. A hit is 1 success,\n"
         "  a Crit 2.\n"
         "6 Recover dice equal to your REC, at the end of every Program and\n"
         "  before the next is revealed.\n\n"
         "Cannot supply a required color: do not execute, lose 1 Health,\n"
         "return withheld dice, and treat the Program as failed for\n"
         "Stable / Overheated progression.  Red never satisfies a required\n"
         "color.  Routine and Unstable carry one required-color dot,\n"
         "Specialized and Advanced two - except Carry a Moving Load, which\n"
         "requires all four colors, and Rapid Approach and Unobserved Entry,\n"
         "which require three. Read the card rather than the deck.\n\n"
         "EXTRA ROLLS. Each element gets one Strategy roll; the rolls beyond\n"
         "that, up to your STR, are a pool spent anywhere in the Program - at\n"
         "STR 2 that is one extra roll for the whole Program. An extra roll is\n"
         "a FULL reroll of that element: pick its dice up, throw them all\n"
         "again, and the new result stands, better or worse.\n\n"
         "ALLOCATING IS NOT SPENDING. When an element resolves its dice go\n"
         "back to your available pool, except where this burns them:\n"
         "  Exactly meet Target: Optimal Implementation, recover 2.\n"
         "  +1 over: free.   +2 or more: burn 1 die on that element.\n"
         "  Fail the element: burn every die on it.\n"
         "  Used an extra STR roll: that element's dice burn either way.\n"
         "An element that used an extra roll and landed exactly on Target\n"
         "does both - exhaust its dice first, then recover 2, which may take\n"
         "back the very dice it just exhausted.\n\n"
         "CATASTROPHIC FAILURE. One failed element in a Program costs no\n"
         "Health. Two or more in the same Program is one Catastrophic Failure\n"
         "and costs 1 Health in total - and you may exhaust 2 misses still\n"
         "showing on failed elements to negate that loss. Those dice were\n"
         "exhausting anyway, so an element you have already given up on is\n"
         "worth loading rather than leaving bare.\n\n"
         "THE PROGRAM REWARD IS THE ONLY HEALING IN THE GAME, and it needs a\n"
         "Program finished with NO failed element. Giving up an element you\n"
         "cannot fund is proper play - but a Program with any failed element\n"
         "pays nothing, so failing your way through the deck gives up every\n"
         "Reward while still paying a die each time. The deck outlasts you.\n"
         "Two of the Rewards are permanent, +1 REC and +1 STR, and claiming\n"
         "either removes that Program from the deck. Advanced Programs carry\n"
         "no Reward at all.\n\n"
         "A Stable Program that fails flips to Overheated, which raises the\n"
         "ringed element's Target; an Overheated Program that fails again is\n"
         "set aside. Programs that leave the deck never come back, so later\n"
         "cycles are shorter.\n\n"
         "DIFFICULTY is the 8-card Program mix, Routine / Specialized /\n"
         "Unstable: Easy 3-3-2, Standard 2-3-3, Hard 1-3-4, Nobulous 0-3-5.\n"
         "Each step up trades one Routine for one Unstable.\n\n"
         "Cycle the deck three times - or until it is empty - then face three\n"
         "Advanced Programs: 4 or 5 elements each, with a Recovery between\n"
         "them. The first begins Stable; each one after it begins Overheated\n"
         "if the one before ended in Catastrophic Failure and Stable\n"
         "otherwise.\n"
         "SURVIVING Advanced Programming is the win condition: work through\n"
         "all three with at least 1 Health, whether or not you completed\n"
         "them. Health never goes above 6. Technicians start 2 HP / 2 STR /\n"
         "3 REC."),
        ("NRJ campaign",
         "THE CAMPAIGN IS TIER III ONLY, because the Research Pool is built\n"
         "out of the Tier III cards themselves. Win BAT, NAP and AoS in any\n"
         "order; if you lose one, replay that game only - the campaign never\n"
         "restarts - then play the Imposter Scenario. No written bookkeeping:\n"
         "the cards and their printed states carry the whole history, and\n"
         "nothing the finale uses comes from outside this box.\n\n"
         "Each game lays 6 Tier III cards out and every one is a favor:\n"
         "claiming it makes that game easier and costs it something. A\n"
         "Research Note costs the next Upgrade a completed Experiment earns,\n"
         "a Backdoor Routine the next Program Reward, and a Devious\n"
         "Opportunity has to be worked like an Assignment in place of a\n"
         "Credit Task. A card you CLAIMED is retained; one you never claimed\n"
         "is a candidate. Whether you went on to spend it makes no\n"
         "difference - nothing on the table records that.\n\n"
         "  NAP  6 Devious Opportunities  answer Knowledge  retain up to 3\n"
         "  BAT  6 Research Notes         answer Physical   retain up to 2\n"
         "  AoS  6 Backdoor Routines      answer Cover-Up   retain up to 2\n\n"
         "Keep all 18 face-up beside the table. EVERY RETAINED CARD REDUCES\n"
         "ONE EXHIBIT'S TARGET BY 2, no Exhibit ever dropping below Target 1,\n"
         "and a card spent in the finale is gone for the rest of it. Claim\n"
         "more than you may retain and you choose which to carry. Seven\n"
         "retained against fifteen Exhibits is the best case, so the campaign\n"
         "answers under half the Dossier - and only while the right domains\n"
         "come up. Candidates answer nothing: only the Understudy spends one.\n\n"
         "THE TIERS ARE NOT DIFFICULTY LEVELS, and each includes the ones\n"
         "before it. I Agenda introduces Nobulous' interference. II\n"
         "Contamination injects corrupted material into the game's own decks\n"
         "and is the pressure peak. III Exploitation hands you tools to\n"
         "exploit the mess.\n\n"
         "STANDALONE: the finale plays without the campaign. Take the 6\n"
         "Research Notes, 6 Devious Opportunities and 6 Backdoor Routines,\n"
         "draw 3 Opportunities, 2 Notes and 2 Routines at random as retained\n"
         "- the campaign's own caps - leave the other eleven as candidates,\n"
         "and play the nine sessions."),
        ("Imposter Scenario",
         "Deal 5 Knowledge, 5 Physical and 5 Cover-Up at random from the 24\n"
         "Exhibits and shuffle those 15 into a face-down Dossier. Choose one\n"
         "Imposter and one of its two sides. Begin at 5 HP / 2 STR / 3 REC\n"
         "with all 17 dice, less the ones the difficulty starts exhausted:\n"
         "  Easy none   Standard 3Y 2G 2B 2P   Hard 3Y 3G 3B 2P\n"
         "  Nobulous 3Y 3G 4B 4P      Red is never exhausted at setup.\n\n"
         "WIN the moment the Dossier is empty and no Exhibit is standing.\n"
         "LOSE if the 9th session ends with any Exhibit left, or Health hits 0.\n\n"
         "A SESSION:\n"
         "1 Deploy. Take any number of Exhibits off the top of the Dossier,\n"
         "  including none. For EACH one, recover 1 exhausted die - or mend 1\n"
         "  Health if nothing is exhausted.\n"
         "2 Answer the evidence. Spend Research Pool cards on the Exhibits you\n"
         "  just deployed. Ones deployed earlier can no longer be answered.\n"
         "3 Strategy, twice. Commit, roll, apply hits to standing Exhibits -\n"
         "  a hit is 1 success, a Crit 2, and only the allowed colors may be\n"
         "  applied. Then take up the dice that missed and throw again.\n"
         "  Nothing is compulsory.\n"
         "4 Resolve, in this order: every Exhibit still standing deals its\n"
         "  Damage; exhaust every committed die that applied nothing and every\n"
         "  die on a card that just fell; take the Reward of each fallen\n"
         "  Exhibit (only the five in bold pay); recover up to REC; advance\n"
         "  the attention and tick the clock.\n\n"
         "THE COUNCIL'S ATTENTION starts on Yellow and advances one step at\n"
         "the end of every session: Yellow > Green > Blue > Purple > Red >\n"
         "Yellow. You may only APPLY dice of the attention's color or the NEXT\n"
         "one on that list. Other dice still commit, roll and exhaust - they\n"
         "just cannot be applied. So recover for the color that is coming.\n"
         "Session 5 is the hard one: Red and Yellow only, and you own one Red.\n\n"
         "An Exhibit falls when successes on it reach its Target. Dice applied\n"
         "to one still standing STAY on it and keep their successes - progress\n"
         "is never lost, and those dice are neither available nor exhausted\n"
         "until the card falls.\n\n"
         "THE FIVE REWARDS THAT PAY are printed in bold and begin 'When this\n"
         "Exhibit falls'; the other nineteen, in italics, are the Council\n"
         "being gracious.\n"
         "  The Chamber Mechanism   recover 2 exhausted dice\n"
         "  The Sedative Ledger     recover 3 exhausted dice\n"
         "  The Vote                recover all exhausted of one color\n"
         "  Tracks in the Yard      recover 1 each of two colors\n"
         "  The Narrow Stair        next Exhibit deployed is Target -1\n"
         "Four of the five are Target 3 as dealt, so the cheapest evidence is\n"
         "also the evidence that pays. A retained card answers only its own\n"
         "domain, and only an Exhibit you deployed THIS session.\n\n"
         "COUNT THE EXHIBITS LEFT AGAINST THE SESSIONS LEFT and do not fall\n"
         "behind that number. Deploying more than you must is how you get\n"
         "ahead of the clock and each Exhibit pays you a die for it;\n"
         "deploying more than you can bury is how you bleed. Slowing down\n"
         "when Health is short feels prudent and loses games, because the\n"
         "clock kills more reliably than the Council does."),
    ]:
        tabs.append({"title": title, "body": body, "color": "Grey", "visibleColor":
                     {"r": 0.5, "g": 0.5, "b": 0.5}})
    return tabs


def main():
    global BASE_URL, RULES_URL, GH_USER, GH_REPO, GH_REF
    a = sys.argv
    for flag, var in (('--user', 'GH_USER'), ('--repo', 'GH_REPO'), ('--ref', 'GH_REF')):
        if flag in a:
            globals()[var] = a[a.index(flag) + 1]
    tpl = RAW if '--raw' in a else CDN
    root = tpl % (GH_USER, GH_REPO, GH_REF)
    BASE_URL = root + '/images'
    RULES_URL = root + '/rules'
    if '--local' in a:
        BASE_URL = 'file://' + SHEETS
        RULES_URL = 'file://' + RULEBOOK_DIR
    print("BASE_URL =", BASE_URL)
    print("RULES_URL =", RULES_URL)

    objects = []
    # Every deck starts INSIDE its game's box. The parking row this
    # replaced was 68 units wide and wrapped to a second row at z -28,
    # which is past the front edge of the table: eleven decks shipped
    # sitting on the floor.
    grouped = dict((g, []) for g in BOX_ORDER)
    for i, d in enumerate(DECKS):
        grouped['NRJ' if d['game'] == 'IMP' else d['game']].append(
            build_deck(d, i + 1, (0, 2.0, 0)))
    grouped['NAP'].append(game_table('NAP'))
    grouped['BAT'].append(game_table('BAT'))
    grouped['AoS'].append(game_table('AoS'))
    grouped['NRJ'].append(game_table('IMP'))
    grouped['BAT'].append(readout_object())
    # BAT's book starts on the rail so that a table nobody has set up
    # yet still has something to read; the other three wait in their
    # boxes until their setup deals them.
    rail = rulebook('BAT', on_rail=True)
    for _g in ('NAP', 'AoS', 'IMP'):
        grouped['NRJ' if _g == 'IMP' else _g].append(rulebook(_g))
    for _nick, _text in NAP_COUNTERS:
        grouped['NAP'].append(counter(_nick, _text))
    box_guids = {}
    for n, game in enumerate(BOX_ORDER):
        # Also on the back rail, two either side of the mat, which is
        # 14.7 wide and sits in the middle of it.
        bx = box(game, grouped[game], (-21.0, -14.5, 14.5, 21.0)[n])
        box_guids[game] = bx['GUID']
        objects.append(bx)
    objects.append(panel())
    objects.append(rail)
    objects += dice_objects()

    save = {
        "SaveName": "The Nobulous Set",
        "GameMode": "The Nobulous Set - BAT / NAP / AoS / NRJ",
        "Gravity": 0.5, "PlayArea": 0.8, "Date": "",
        # THE RECTANGLE TABLE IS CALLED Table_RPG in the save format.
        # Table_Custom made TTS offer to import a custom table on every
        # load, because the save carries no URL for one; "Table_Rectangle"
        # then looked like the obvious replacement and is not a value TTS
        # has, so it resolved to nothing and the load died on a null
        # reference with no mention of the table. The name came from Jon's
        # own saves of this mod, which is where to look for the next one.
        "Table": "Table_RPG",
        # NO HAND ZONES, AND SO NO SEATS THAT CAN TAKE A CARD. A card
        # dropped near the edge of the table was being flipped and
        # carried off to the rail: that is what a hand zone does with a
        # card, and the two Assignment spaces nearest the back were
        # inside one. This is a solitaire game - every seat but one is
        # scenery - so the zones go rather than the layout.
        "Hands": {"Enable": False, "DisableUnused": False, "Hiding": 0},
        "Sky": "Sky_Museum", "Note": "Fan expansion for 20 Strong. Prototype.",
        "Rules": "See the Notebook.",
        "TabStates": {str(i): t for i, t in enumerate(notebook())},
        "LuaScript": lua_header(box_guids) + io.open(
            os.path.join(os.path.dirname(__file__), 'lua.lua'),
            encoding='utf-8').read(),
        "LuaScriptState": "",
        "XmlUI": "",
        "ObjectStates": objects,
    }
    with open(OUT, 'w') as f:
        json.dump(save, f, indent=1)
    print("wrote", OUT, "-", len(objects), "objects,",
          sum(d['count'] for d in DECKS), "cards in",
          len(BOX_ORDER), "bags")

    # WHAT THE SAVE ACTUALLY ASKS FOR, read out of the save. This list
    # used to be rebuilt here from DECKS plus two names typed in - a
    # second derivation of the same thing, and it fell behind the
    # moment anything that was not a card deck grew an image. It was
    # missing the BAT, AoS and Imposter overlays, both faces of the
    # Chip and the readout's tile: six files it told Jon he did not
    # need to upload, and six that deploy.py --prune would have
    # deleted out of images/ for not being on it.
    need = set()
    base = BASE_URL.rstrip('/') + '/'

    def harvest(node):
        if isinstance(node, dict):
            for k, v in node.items():
                if (isinstance(v, str) and v.startswith(base)
                        and k.endswith('URL')):
                    need.add(v[len(base):])
                else:
                    harvest(v)
        elif isinstance(node, list):
            for v in node:
                harvest(v)

    harvest(save)
    if not need:
        raise SystemExit('the save references no images under BASE_URL')
    with open(os.path.join(os.path.dirname(OUT), 'REQUIRED_IMAGES.txt'), 'w') as f:
        f.write("Upload these to BASE_URL, keeping the filenames:\n\n")
        # WITHOUT THE CACHE TOKEN. These names are harvested out of
        # the save's URLs, which now carry ?v=<hash>, and this list
        # is not decoration: deploy.py reads it to learn which
        # images the mod needs and protects exactly those from
        # --prune. A token on the end makes its regex miss the line,
        # so every tokened image reads as unreferenced - which is
        # 67 of them, and deploy refused to run at all rather than
        # prune them, which is the only reason this was caught here
        # instead of by a missing images/ folder.
        for n in sorted(set(x.split('?')[0] for x in need)):
            p = os.path.join(SHEETS, n)
            f.write("  %-38s %s\n" % (n, 'ok' if os.path.exists(p) else 'MISSING'))
        # THE RULEBOOKS ARE FETCHED BY THE MOD TOO, from rules/ rather
        # than images/. Left off this list they would be the one set of
        # files nobody checked before publishing.
        f.write("\nAnd these to RULES_URL, from rules/:\n\n")
        for g in ('BAT', 'NAP', 'AoS', 'IMP'):
            n = RULEBOOK[g]
            p = os.path.join(RULEBOOK_DIR, n)
            f.write("  %-38s %s\n" % (n, 'ok' if os.path.exists(p) else 'MISSING'))
    print("image list ->", os.path.join(os.path.dirname(OUT), 'REQUIRED_IMAGES.txt'))


if __name__ == '__main__':
    main()
