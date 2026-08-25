"""Build the Tabletop Simulator save file for The Nobulous Set.

Image hosting: TTS loads card sheets over HTTP, so the PNGs in cards/out must be
uploaded somewhere public first (Steam Cloud, GitHub raw, imgur, any static host).
Set BASE_URL below to the folder that will contain them, keeping the filenames.

    python3 build_mod.py                 -> NobulousSet.json using BASE_URL
    python3 build_mod.py --local /path   -> file:/// URLs, for solo testing only
"""
import json, os, sys, random

sys.path.insert(0, os.path.dirname(__file__))
from decks import DECKS, GAME_COLOUR
import layout

# Where the images live. Set with --user / --repo / --ref, or edit GH_USER.
GH_USER, GH_REPO, GH_REF = "YOUR-GITHUB-USERNAME", "nobulous-set", "main"
CDN = "https://cdn.jsdelivr.net/gh/%s/%s@%s/images"      # cached, fast, recommended
RAW = "https://raw.githubusercontent.com/%s/%s/%s/images"  # works, uncached
BASE_URL = ""
_HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.environ.get("TTS_OUT", os.path.join(_HERE, "NobulousSet.json"))
SHEETS = os.environ.get("TTS_SHEETS", os.path.join(_HERE, os.pardir, "images"))

rng = random.Random(20260823)
USED = set()

BANK_POS = (-13.0, 1.5, 20.0)        # beside the nameplate, clear of the cards

# The nameplate sits at the top all game. The setup surface sits in the middle
# and is hidden once play starts, so the cards can be dealt into that space.
NAMEPLATE_POS, NAMEPLATE_SCALE = (0.0, 1.02, 20.0), 5.0
SETUP_POS, SETUP_SCALE = (0.0, 1.02, 0.0), 5.0


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


def cover(name, image, pos, scale):
    """A tile that hides a deck. The AoS Program decks are two-sided, so face
    down they still show a real card; a tile rests on top without merging into
    the deck the way a card would."""
    return {"GUID": guid(), "Name": "Custom_Tile",
            "Transform": xf(pos[0], pos[1], pos[2], (0, 180, 0), scale),
            "Nickname": name, "Description": "Lift to reveal the deck",
            "ColorDiffuse": {"r": 1.0, "g": 1.0, "b": 1.0},
            "Locked": False, "Grid": True, "Snap": True,
            "CustomImage": {"ImageURL": url(image), "ImageSecondaryURL": "",
                            "ImageScalar": 1.0, "WidthScale": 0.0,
                            "CustomTile": {"Type": 3, "Thickness": 0.1,
                                           "Stackable": False, "Stretch": True}}}


def build_deck(d, deck_id, pos, scale=1.0):
    face = url(d['key'] + '_TTS.png')
    back = (url(d['key'] + '_TTS_back.png') if d['back'] == 'unique'
            else url(d['back'] + '.png'))
    custom = {str(deck_id): {"FaceURL": face, "BackURL": back,
                             "NumWidth": d['w'], "NumHeight": d['h'],
                             "BackIsHidden": True, "UniqueBack": d['back'] == 'unique',
                             "Type": 0}}
    contained, ids = [], []
    for i in range(d['count']):
        contained.append(card(deck_id, i, '%s %d' % (d['label'], i + 1)))
        ids.append(deck_id * 100 + i)
    r, g, b = GAME_COLOUR[d['game']]
    obj = {"GUID": guid(), "Name": "Deck" if d['count'] > 1 else "CardCustom",
           "Transform": xf(pos[0], pos[1], pos[2], (0, 180, 180), scale),
           "Nickname": d['label'],
           "Description": "%s  |  %d cards" % (d['game'], d['count']),
           "ColorDiffuse": {"r": 1.0, "g": 1.0, "b": 1.0},
           "Locked": False, "Grid": True, "Snap": True, "Autoraise": True, "Sticky": True,
           "SidewaysCard": bool(d['land']),
           "DeckIDs": ids, "CustomDeck": custom, "ContainedObjects": contained}
    if d['count'] == 1:
        obj.pop("DeckIDs")
        obj.pop("ContainedObjects")
        obj["CardID"] = deck_id * 100
    return obj


def panel():
    """The nameplate. Lives at the top of the table and stays there all game,
    carrying Select a New Game and the counters."""
    return {"GUID": guid(), "Name": "Custom_Tile",
            "Transform": xf(NAMEPLATE_POS[0], NAMEPLATE_POS[1], NAMEPLATE_POS[2],
                            (0, 180, 0), NAMEPLATE_SCALE),
            "Nickname": "Control Panel",
            "Description": "The Nobulous Set",
            "ColorDiffuse": {"r": 0.93, "g": 0.91, "b": 0.85},
            "Locked": True, "Grid": False, "Snap": False,
            "CustomImage": {"ImageURL": url("Nameplate.png"), "ImageSecondaryURL": "",
                            "ImageScalar": 1.0, "WidthScale": 0.0,
                            "CustomTile": {"Type": 3, "Thickness": 0.1,
                                           "Stackable": False, "Stretch": True}}}


def setup_panel():
    """The wizard surface, in the middle of the table. The nameplate art is
    2.83:1, so a tile using it has almost no vertical room -- this one is
    square, giving the buttons somewhere to sit in both axes. The Lua clears
    and hides it once a game starts, freeing the middle for the cards."""
    return {"GUID": guid(), "Name": "Custom_Tile",
            "Transform": xf(SETUP_POS[0], SETUP_POS[1], SETUP_POS[2],
                            (0, 180, 0), SETUP_SCALE),
            "Nickname": "Setup Panel",
            "Description": "Choose a game, set the options, then Start Game",
            "ColorDiffuse": {"r": 1.0, "g": 1.0, "b": 1.0},
            "Locked": True, "Grid": False, "Snap": False,
            "CustomImage": {"ImageURL": url("SetupPanel.png"), "ImageSecondaryURL": "",
                            "ImageScalar": 1.0, "WidthScale": 0.0,
                            "CustomTile": {"Type": 3, "Thickness": 0.1,
                                           "Stackable": False, "Stretch": True}}}


def dice_objects():
    """Dice and the chip, at the exact positions Jon arranged in TTS.

    layout.LOOSE holds one entry per physical die, so identical nicknames are
    consumed in save order and each die keeps its own spot in the block.
    """
    src = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dice_objects.json')))
    queue = {}
    for name, nick, x, y, z, rot, scale in layout.LOOSE:
        if name != 'Custom_Tile':
            queue.setdefault(nick, []).append((x, y, z, rot, scale))

    # The dial sits just above the block of coloured dice, not off beside the
    # cards, so it is derived from where those dice actually ended up.
    colour = [q for n, q in queue.items()
              if n in ('Red', 'Purple', 'Blue', 'Green', 'Yellow')]
    spots = [p for q in colour for p in q]
    if spots:
        cx = (min(p[0] for p in spots) + max(p[0] for p in spots)) / 2.0
        cz = max(p[2] for p in spots) + 1.6
        queue['Chip'] = [(round(cx, 2), 1.1, round(cz, 2), (0, 180, 0), 0.85)]

    out, spare_z = [], -20.0
    for o in src:
        nick = 'Red' if o.get('Nickname') == 'Pink' else (o.get('Nickname') or 'Die')
        if queue.get(nick):
            x, y, z, rot, scale = queue[nick].pop(0)
        else:                                   # not in the arranged save
            x, y, z, rot, scale = -20.0, 1.4, spare_z, (0, 0, 0), 1.0
            spare_z -= 1.2
        out.append({"GUID": guid(), "Name": o['Name'],
                    "Transform": xf(x, y, z, rot, scale),
                    "Nickname": nick,
                    "Description": o.get('Description') or '',
                    "ColorDiffuse": o.get('ColorDiffuse') or {"r": 1, "g": 1, "b": 1},
                    "Locked": False, "Grid": True, "Snap": True,
                    "Autoraise": True, "Sticky": True,
                    "CustomImage": o['CustomImage']})
    return out


def bank(contents, pos):
    """Everything starts in here. The table opens showing only dice, the chip
    and the Control Panel; setup takes out just what that game needs, and
    leftovers stay put so they can still be searched out by hand."""
    return {"GUID": guid(), "Name": "Bag",
            "Transform": xf(pos[0], pos[1], pos[2], (0, 0, 0), 1.2),
            "Nickname": "Card Bank",
            "Description": "Every deck starts here. Right-click > Search to browse.",
            "ColorDiffuse": {"r": 0.31, "g": 0.27, "b": 0.23},
            "Locked": False, "Grid": True, "Snap": True, "Autoraise": True,
            "Sticky": True, "MaterialIndex": -1, "MeshIndex": -1,
            "Bag": {"Order": 0}, "ContainedObjects": contents}


def lua_script():
    """lua.lua with the generated layout table substituted in."""
    src = open(os.path.join(_HERE, 'lua.lua'), encoding='utf-8').read()
    rows = ['LAYOUT = {']
    for label, (x, z) in sorted(layout.POS.items()):
        rows.append('  [%s] = {%.2f, %.2f},' % (lua_str(label), x, z))
    rows.append('}')
    rows.append('PORTRAIT_SCALE = %s' % layout.PORTRAIT_SCALE)
    return src.replace('--[[LAYOUT]]', "\n".join(rows))


def lua_str(s):
    return '"%s"' % s.replace('\\', '\\\\').replace('"', '\\"')


def notebook():
    tabs = []
    for title, body in [
        ("How to use this mod",
         "Press the buttons on the Control Panel.\n\n"
         "  Set up BAT / NAP / AoS / Imposter -- deals that game's decks.\n"
         "  Difficulty -- Easy / Standard / Hard. For AoS this also picks the\n"
         "  Program deck: Routine / Specialized / Unstable.\n"
         "  NRJ Tier -- off / I Agenda / II Contamination / III Exploitation.\n"
         "  Set the tier BEFORE pressing a setup button.\n\n"
         "The script deals and counts. It never enforces a rule."),
        ("BAT quick reference",
         "Turn: reveal Encounter, reveal 2 Upgrades (+1 Target if either is a\n"
         "Specimen), choose the active Rat, commit, roll, resolve, recover.\n\n"
         "Success: take one revealed Upgrade (max 3 per Rat).\n"
         "Failure: Splice the stronger revealed Upgrade into the Tyrant.\n"
         "Five Splices awakens the Tyrant.\n\n"
         "Tyrant Health is always 20. Harder modes add Buff Health on top --\n"
         "+2 on Standard, +4 on Hard, up to +8 -- and every Buff must be\n"
         "removed before any normal Health comes off. The Control Panel\n"
         "tracks the total; set it with the - / + buttons for other values.\n\n"
         "Borrowing: 0 Upgrades any colour, 1 no Purple, 2 Green/Yellow,\n"
         "3 Yellow only. Roll the borrowed die after; on a miss it is banished.\n\n"
         "Red is set aside after use and placed on a non-active Rat next turn."),
        ("NAP quick reference",
         "Three Time Slots a day. Reveal 2 Assignments, choose the Primary;\n"
         "a Setback must be taken. The Primary's dot queues the next slot's\n"
         "Special Recovery colour.\n\n"
         "STR = rolls in the slot AND the cap on completions in the slot.\n"
         "Unresolved Assignments flip to Demand and stay in the row.\n"
         "6 Credits reaches the Final Exam. Draw 3 from the weighted pool.\n"
         "Lose 1 Health per success short. Survive all three to win."),
        ("AoS quick reference",
         "1 Reveal the Program.\n"
         "2 Commit required-colour dice -- these lock to their element.\n"
         "3 Reveal the Limitation. It withholds from the REMAINING pool.\n"
         "4 Finish the allocation.  5 Execute.\n\n"
         "Cannot supply a required colour: lose 1 Health, do not execute,\n"
         "treat as failed.  Red never satisfies a required colour.\n\n"
         "Exact Target: recover 2. +1 over: free. +2 or more: burn 1.\n"
         "Fail: burn all. Extra STR roll: burn that element's dice anyway.\n"
         "Two or more failed elements in one Program: lose 1 Health."),
        ("NRJ campaign",
         "Win BAT, NAP and AoS at the same tier, replaying only a game you lose.\n"
         "Each contributes 6 cards to the 18-card Research Pool.\n\n"
         "Imposter: 4 Knowledge + 4 Physical + 4 Cover-Up shuffled to 12.\n"
         "4 HP / 2 STR / 3 REC. Nine attempts; avoided Scenarios do not count.\n\n"
         "Spend: matching retained NAP -2, BAT -3 (Specimen -5),\n"
         "AoS Stable -4 / Overheated -2. Retained off-category -2.\n"
         "Candidate or damaged card 0.\n\n"
         "Failure: Suspicion row +1 Target to every later Scenario, and\n"
         "lose 1 Health or banish 2 available dice."),
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

    # Every deck and cover starts inside the Card Bank; the Lua deals them out
    # on Start Game. Positions still come from layout.py, generated by
    # relayout.py off the save Jon arranged by hand.
    stored = []
    for i, d in enumerate(DECKS):
        scale = 1.0 if d['land'] else layout.PORTRAIT_SCALE
        stored.append(build_deck(d, i + 1, (0.0, 2.0, 0.0), scale))
    for image, name in (('CardBack_AoS_Program.png', 'Program Cover'),
                        ('CardBack_AoS_Advanced.png', 'Advanced Cover')):
        stored.append(cover(name, image, (0.0, 2.6, 0.0), layout.PORTRAIT_SCALE))

    objects = [panel(), setup_panel(), bank(stored, BANK_POS)]
    objects += dice_objects()

    save = {
        "SaveName": "The Nobulous Set",
        "GameMode": "The Nobulous Set - BAT / NAP / AoS / NRJ",
        "Gravity": 0.5, "PlayArea": 0.8, "Date": "", "Table": layout.TABLE,
        "Sky": "Sky_Museum", "Note": "Fan expansion for 20 Strong. Prototype.",
        "Rules": "See the Notebook.",
        "TabStates": {str(i): t for i, t in enumerate(notebook())},
        "LuaScript": lua_script(),
        "LuaScriptState": "",
        "XmlUI": "",
        "ObjectStates": objects,
    }
    with open(OUT, 'w') as f:
        json.dump(save, f, indent=1)
    print("wrote", OUT, "-", len(objects), "objects,", sum(d['count'] for d in DECKS), "cards")

    need = set()
    for d in DECKS:
        need.add(d['key'] + '_TTS.png')
        need.add(d['key'] + '_TTS_back.png' if d['back'] == 'unique' else d['back'] + '.png')
    need.add('ControlPanel.png')
    need.add('CardBack_AoS_Program.png')
    need.add('CardBack_AoS_Advanced.png')
    need.add('SetupPanel.png')
    need.add('Nameplate.png')
    with open(os.path.join(os.path.dirname(OUT), 'REQUIRED_IMAGES.txt'), 'w') as f:
        f.write("Upload these to BASE_URL, keeping the filenames:\n\n")
        for n in sorted(need):
            p = os.path.join(SHEETS, n)
            f.write("  %-38s %s\n" % (n, 'ok' if os.path.exists(p) else 'MISSING'))
    print("image list ->", os.path.join(os.path.dirname(OUT), 'REQUIRED_IMAGES.txt'))


if __name__ == '__main__':
    main()
