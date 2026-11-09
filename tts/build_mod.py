"""Build the Tabletop Simulator save file for The Nobulous Set.

Image hosting: TTS loads card sheets over HTTP, so the PNGs in cards/out must be
uploaded somewhere public first (Steam Cloud, GitHub raw, imgur, any static host).
Set BASE_URL below to the folder that will contain them, keeping the filenames.

    python3 build_mod.py                 -> NobulousSet.json using BASE_URL
    python3 build_mod.py --local /path   -> file:/// URLs, for solo testing only
"""
import ast, io, json, os, sys, random

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
CDN = "https://cdn.jsdelivr.net/gh/%s/%s@%s/images"      # cached, fast, recommended
RAW = "https://raw.githubusercontent.com/%s/%s/%s/images"  # works, uncached
BASE_URL = ""
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
CARD_SHORT, CARD_LONG = 2.4, 3.35
CARD_SCALE = 2.6
LAND_SCALE = CARD_SCALE * CARD_SHORT / CARD_LONG
CARD_W = CARD_SHORT * CARD_SCALE   # a portrait card, across
CARD_L = CARD_LONG * CARD_SCALE    # a landscape card, across - which is
                                   # the portrait card's long edge, because
                                   # that is all a rotation can make it

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
    home = dict((d['label'], 'NRJ' if d['game'] == 'IMP' else d['game'])
                for d in DECKS)
    j = lambda xs: ', '.join(xs)
    return '\n'.join([
        '-- ================= GENERATED BY build_mod.py =================',
        '-- Box GUIDs come from the save being built; the two card-index',
        '-- tables are read out of generator/build_nap.py and build_nrj.py.',
        '-- Edit build_mod.py, never this block.',
        'CARD_SCALE = %.2f' % CARD_SCALE,
        'CARD_W = %.3f' % CARD_W,
        'CARD_L = %.3f' % CARD_L,
        'BOX = { %s }' % j("%s = '%s'" % (g, box_guids[g]) for g in BOX_ORDER),
        'HOME = { %s }' % j("['%s'] = '%s'" % (k, v) for k, v in sorted(home.items())),
        'NAP_CREDIT = { %s }' % j('%s = {%s}' % (k, j(str(i) for i in v))
                                  for k, v in sorted(nap_credit_tasks().items())),
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


def xf(x, y, z, rot=(0, 180, 0), s=1.0):
    return {"posX": x, "posY": y, "posZ": z, "rotX": rot[0], "rotY": rot[1], "rotZ": rot[2],
            "scaleX": s, "scaleY": s, "scaleZ": s}


def url(name):
    return "%s/%s" % (BASE_URL.rstrip('/'), name)


def card(deck_id, idx, nickname, desc=''):
    return {"GUID": guid(), "Name": "Card", "Transform": xf(0, 0, 0),
            "Nickname": nickname, "Description": desc, "CardID": deck_id * 100 + idx,
            "Locked": False, "Grid": True, "Snap": True, "Autoraise": True, "Sticky": True,
            "SidewaysCard": False}


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
    contained, ids = [], []
    for i in range(first, first + d['count']):
        contained.append(card(deck_id, i, '%s %d' % (d['label'], i - first + 1)))
        ids.append(deck_id * 100 + i)
    r, g, b = GAME_COLOR[d['game']]
    obj = {"GUID": guid(), "Name": "Deck" if d['count'] > 1 else "CardCustom",
           "Transform": xf(pos[0], pos[1], pos[2], (0, 180, 180),
                           LAND_SCALE if d['land'] else CARD_SCALE),
           "Nickname": d['label'],
           "Description": "%s  |  %d cards" % (d['game'], d['count']),
           "ColorDiffuse": {"r": 1.0, "g": 1.0, "b": 1.0},
           "Locked": False, "Grid": True, "Snap": True, "Autoraise": True, "Sticky": True,
           "SidewaysCard": bool(d['land']),
           "DeckIDs": ids, "CustomDeck": custom, "ContainedObjects": contained}
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


def dice_objects():
    # Checked in beside this script, so read it from there rather than
    # from the machine it was first written on - that hardcoded path
    # meant build_mod.py could not run anywhere else at all.
    src = json.load(open(os.path.join(os.path.dirname(
        os.path.abspath(__file__)), 'dice_objects.json')))
    out = []
    # ONE ROW PER COLOUR, DOWN THE LEFT EDGE, in the order the rules
    # name them: Red, Purple, Blue, Green, Yellow. The colours used to sit
    # 2 apart with their four dice stepping 1.1 each, so every colour's
    # second die stood on the next colour's first and the pool read as one
    # heap. x -24.5 keeps the whole column clear of the widest dealt row,
    # which is four landscape cards at +/-18.
    # FAR ENOUGH LEFT TO CLEAR THE NAP TIME SLOT COLUMN, whose cards
    # reach x -23.86. At -24.5 the second die of every block sat under
    # them - the comment in lua.lua claimed -26.5 before the number did.
    XCOL = -26.5
    ROWS = {'Pink': 10.5, 'Purple': 8.0, 'Blue': 4.0,
            'Green': 0.0, 'Yellow': -4.0}
    # A 2x2 block per colour rather than a row of four: four in a line is
    # as wide as a card and reads as a queue, not a pool.
    OFFS = ((0.0, 0.0), (1.4, 0.0), (0.0, -1.4), (1.4, -1.4))
    # The Chip sits beside the Red die, which is the one it belongs to:
    # Red is communal and the Chip marks who holds it.
    # The Chip sits directly ABOVE the Red die it marks, in the same
    # column; the three utility dice stay inside the same two columns,
    # clear of the FINF card at z -10.
    lay = {'Chip': (XCOL, ROWS['Pink'] + 2.0),
           'Health': (XCOL, -8.5), 'Strategy': (XCOL + 1.4, -8.5),
           'Recovery': (XCOL, -9.9)}
    seen = {}
    for o in src:
        nick = o.get('Nickname') or 'Die'
        seen[nick] = seen.get(nick, 0) + 1
        if nick in ROWS:
            ox, oz = OFFS[(seen[nick] - 1) % len(OFFS)]
            bx, bz = XCOL + ox, ROWS[nick] + oz
        else:
            bx, bz = lay.get(nick, (XCOL + 1.4, -9.9))
        d = {"GUID": guid(), "Name": o['Name'],
             "Transform": xf(bx, 1.4, bz, (0, 0, 0)),
             "Nickname": 'Red' if nick == 'Pink' else nick,
             "Description": o.get('Description') or '',
             "ColorDiffuse": o.get('ColorDiffuse') or {"r": 1, "g": 1, "b": 1},
             "Locked": False, "Grid": True, "Snap": True, "Autoraise": True, "Sticky": True,
             "CustomImage": o['CustomImage']}
        out.append(d)
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
         "  3. Set up BAT / NAP / AoS / Imposter.\n\n"
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
         "Keep 1 / 2 / 3 -- for NAP, AoS and the finale, keeps that\n"
         "  character and bags the others. Every card is two characters,\n"
         "  so flip the one you keep for the other side.\n"
         "Pack up -- everything, including loose cards, goes back in its\n"
         "  bag.\n\n"
         "The script deals and counts. It never enforces a rule in play."),
        ("BAT quick reference",
         "Turn: reveal Encounter, reveal 2 Upgrades (+1 Target if either is a\n"
         "Specimen), choose the active Rat, commit, roll, resolve, recover.\n\n"
         "Success: take one revealed Upgrade (max 3 per Rat).\n"
         "Failure: Splice the stronger revealed Upgrade into the Tyrant.\n"
         "Five Splices awaken the Tyrant. You cannot avoid this - the game is\n"
         "about WHICH five cards it gets.\n\n"
         "DIFFICULTY sets the Specimens shuffled in with the 16 Upgrades and\n"
         "the Tyrant's HEALTH:\n"
         "  Easy 5 and 9   Standard 6 and 10   Hard 7 and 12   Nobulous 8 and 14\n"
         "Set the Health DIAL to that number. The Buff HP card is optional -\n"
         "hold part of the Health on it and spend that first.\n\n"
         "Tyrant track, left to right: the five Splices in a RANDOM order,\n"
         "then Health. Damage has to come through it in that order.\n"
         "A blow must meet a Splice's printed Value in one attack or the whole\n"
         "attack is wasted; meet it and the remainder carries on to the next.\n"
         "Each Splice you break banishes one pool die of its own color, or any\n"
         "die if none of that color is left. Splices chip; Health chips.\n"
         "Rat Upgrades do NOT: an attack either meets an Upgrade's Value and\n"
         "destroys it, or it stops. No Rat card is ever part-damaged.\n\n"
         "The Tyrant's six dice come out of the Rats' own supply - 2 Purple /\n"
         "2 Blue / 1 Green / 1 Yellow, kept in a bag - and it draws as many as\n"
         "its highest remaining Splice Value, 2 if none. Its FRONTMOST Splice\n"
         "adds that Value minus 1 to every attack. The Tyrant never taps.\n\n"
         "Borrowing - one non-Red die, before either Strategy roll:\n"
         "  0 Upgrades held: Purple, Blue, Green or Yellow\n"
         "  1: Blue, Green or Yellow   2: Green or Yellow   3: Yellow only\n"
         "Roll it by itself afterwards; on a miss it is banished.\n\n"
         "Red is communal and belongs to no Rat. After use it is set aside,\n"
         "then placed on a NON-active Rat at the start of the next turn.\n"
         "In the BATTLE Red is not in the shared pool and is not passed\n"
         "around: the attacking Rat may commit it, but only if they do not tap\n"
         "an Upgrade as part of that attack.\n\n"
         "Strategy die marks the active Rat. The Health DIAL runs the Tyrant\n"
         "track. The Recovery die is not used."),
        ("NAP quick reference",
         "Three Time Slots a day. Reveal 2 Assignments, choose the Primary;\n"
         "a Setback must be taken. The Primary's dot queues the next slot's\n"
         "Special Recovery color.\n\n"
         "STR = rolls in the slot AND the cap on completions in the slot.\n"
         "Unresolved Assignments flip to Demand and stay in the row.\n"
         "End of Day: reveal and discard the top Assignment card, ignoring\n"
         "all of its text, effects and Skulls.\n\n"
         "DIFFICULTY is the Credit goal and the Setbacks in the deck:\n"
         "  Easy 5 and 3   Standard 6 and 3   Hard 7 and 4   Nobulous 8 and 5\n"
         "The exam begins at the END of a Day, never part-way through one.\n"
         "An empty Assignment deck sends you to it as well.\n\n"
         "FINAL EXAM. Place cards into the pool per subject by the Credits you\n"
         "hold in it - 0-1 Credits 1 card, 2-3 two, 4+ three - then shuffle\n"
         "and draw 3. Each exam's base Target drops by 1 per Credit in its\n"
         "subject, and you lose 1 Health per success short. Honor the printed\n"
         "restriction. Survive all three to win."),
        ("AoS quick reference",
         "1 Reveal the Program.\n"
         "2 Reveal the Limitation. Withheld dice sit out this Program.\n"
         "3 Commit required-color dice -- these lock to their element.\n"
         "4 Finish the allocation. EVERY ELEMENT MUST RECEIVE AT LEAST ONE\n"
         "  DIE, never fewer than one.  5 Execute.\n\n"
         "Cannot supply a required color: lose 1 Health, do not execute,\n"
         "treat as failed.  Red never satisfies a required color.\n"
         "Routine and Unstable carry one required-color dot, Specialized and\n"
         "Advanced two - except Rapid Approach and Unobserved Entry, three.\n\n"
         "Exact Target: Optimal Implementation, recover 2. +1 over: free.\n"
         "+2 or more: burn 1. Fail: burn all.\n"
         "Two or more failed elements in one Program: lose 1 Health.\n\n"
         "THE PROGRAM REWARD IS THE ONLY HEALING IN THE GAME, and it needs a\n"
         "Program finished with NO failed element. Giving up an element you\n"
         "cannot fund is proper play - but a Program with any failed element\n"
         "pays nothing, so failing your way through the deck gives up every\n"
         "Reward while still paying a die each time. The deck outlasts you.\n\n"
         "DIFFICULTY is the 8-card Program mix, Routine / Specialized /\n"
         "Unstable: Easy 3-3-2, Standard 2-3-3, Hard 1-3-4, Nobulous 0-3-5.\n"
         "Each step up trades one Routine for one Unstable.\n\n"
         "Cycle the deck three times, then face three Advanced Programs.\n"
         "SURVIVING Advanced Programming is the win condition: work through\n"
         "all three with at least 1 Health, whether or not you completed\n"
         "them. Health never goes above 6. Technicians start 2 HP / 2 STR /\n"
         "3 REC."),
        ("NRJ campaign",
         "Win BAT, NAP and AoS at Tier III, replaying only a game you lose.\n"
         "Each lays 6 Tier III cards out and every one is a favor: claiming\n"
         "it makes that game easier and costs it something. A card you\n"
         "CLAIMED is retained; one you never claimed is a candidate.\n\n"
         "Retain at most: NAP 3, BAT 2, AoS 2. Keep all 18 face-up beside the\n"
         "table. EVERY RETAINED CARD REDUCES ONE EXHIBIT'S TARGET BY 2, and a\n"
         "card spent in the finale is gone for the rest of it. Candidates\n"
         "answer nothing - only the Understudy can spend one."),
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
         "  a hit is 1 success, a Crit 2. Then take up what you did not apply,\n"
         "  add more if you like, and throw again. Nothing is compulsory.\n"
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
         "until the card falls."),
    ]:
        tabs.append({"title": title, "body": body, "color": "Grey", "visibleColor":
                     {"r": 0.5, "g": 0.5, "b": 0.5}})
    return tabs


def main():
    global BASE_URL, GH_USER, GH_REPO, GH_REF
    a = sys.argv
    for flag, var in (('--user', 'GH_USER'), ('--repo', 'GH_REPO'), ('--ref', 'GH_REF')):
        if flag in a:
            globals()[var] = a[a.index(flag) + 1]
    tpl = RAW if '--raw' in a else CDN
    BASE_URL = tpl % (GH_USER, GH_REPO, GH_REF)
    if '--local' in a:
        BASE_URL = 'file://' + SHEETS
    print("BASE_URL =", BASE_URL)

    objects = []
    # Every deck starts INSIDE its game's box. The parking row this
    # replaced was 68 units wide and wrapped to a second row at z -28,
    # which is past the front edge of the table: eleven decks shipped
    # sitting on the floor.
    grouped = dict((g, []) for g in BOX_ORDER)
    for i, d in enumerate(DECKS):
        grouped['NRJ' if d['game'] == 'IMP' else d['game']].append(
            build_deck(d, i + 1, (0, 2.0, 0)))
    box_guids = {}
    for n, game in enumerate(BOX_ORDER):
        # Also on the back rail, two either side of the mat, which is
        # 14.7 wide and sits in the middle of it.
        bx = box(game, grouped[game], (-21.0, -14.5, 14.5, 21.0)[n])
        box_guids[game] = bx['GUID']
        objects.append(bx)
    objects.append(panel())
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

    need = set()
    for d in DECKS:
        sheet = d.get('sheet', d['key'])
        need.add(sheet + '_TTS.png')
        need.add(sheet + '_TTS_back.png' if d['back'] == 'unique' else d['back'] + '.png')
    need.add('ControlPanel.png')
    with open(os.path.join(os.path.dirname(OUT), 'REQUIRED_IMAGES.txt'), 'w') as f:
        f.write("Upload these to BASE_URL, keeping the filenames:\n\n")
        for n in sorted(need):
            p = os.path.join(SHEETS, n)
            f.write("  %-38s %s\n" % (n, 'ok' if os.path.exists(p) else 'MISSING'))
    print("image list ->", os.path.join(os.path.dirname(OUT), 'REQUIRED_IMAGES.txt'))


if __name__ == '__main__':
    main()
