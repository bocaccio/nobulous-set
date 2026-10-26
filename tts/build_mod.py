"""Build the Tabletop Simulator save file for The Nobulous Set.

Image hosting: TTS loads card sheets over HTTP, so the PNGs in cards/out must be
uploaded somewhere public first (Steam Cloud, GitHub raw, imgur, any static host).
Set BASE_URL below to the folder that will contain them, keeping the filenames.

    python3 build_mod.py                 -> NobulousSet.json using BASE_URL
    python3 build_mod.py --local /path   -> file:/// URLs, for solo testing only
"""
import json, os, sys, random

sys.path.insert(0, os.path.dirname(__file__))
from decks import DECKS, GAME_COLOR

# Where the images live. Set with --user / --repo / --ref, or edit GH_USER.
GH_USER, GH_REPO, GH_REF = "YOUR-GITHUB-USERNAME", "nobulous-set", "main"
CDN = "https://cdn.jsdelivr.net/gh/%s/%s@%s/images"      # cached, fast, recommended
RAW = "https://raw.githubusercontent.com/%s/%s/%s/images"  # works, uncached
BASE_URL = ""
OUT = os.environ.get("TTS_OUT", "/home/claude/tts/NobulousSet.json")
SHEETS = os.environ.get("TTS_SHEETS", "/home/claude/cards/out")

rng = random.Random(20260823)
USED = set()


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
    r, g, b = GAME_COLOR[d['game']]
    obj = {"GUID": guid(), "Name": "Deck" if d['count'] > 1 else "CardCustom",
           "Transform": xf(pos[0], pos[1], pos[2], (0, 180, 180)),
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
    return {"GUID": guid(), "Name": "Custom_Tile",
            "Transform": xf(0, 0.96, 14, (0, 180, 0), 3.4),
            "Nickname": "Control Panel",
            "Description": "Setup and counters for The Nobulous Set",
            "ColorDiffuse": {"r": 0.93, "g": 0.91, "b": 0.85},
            "Locked": True, "Grid": False, "Snap": False,
            "CustomImage": {"ImageURL": url("ControlPanel.png"), "ImageSecondaryURL": "",
                            "ImageScalar": 1.0, "WidthScale": 0.0,
                            "CustomTile": {"Type": 3, "Thickness": 0.1,
                                           "Stackable": False, "Stretch": True}}}


def dice_objects():
    src = json.load(open('/home/claude/cards/dice_objects.json'))
    out = []
    lay = {'Purple': (-16, -14), 'Blue': (-14, -14), 'Green': (-12, -14),
           'Yellow': (-10, -14), 'Pink': (-8, -14),
           'Health': (-16, -17), 'Strategy': (-14, -17), 'Recovery': (-12, -17),
           'Chip': (-10, -17)}
    seen = {}
    for o in src:
        nick = o.get('Nickname') or 'Die'
        seen[nick] = seen.get(nick, 0) + 1
        bx, bz = lay.get(nick, (-6, -17))
        d = {"GUID": guid(), "Name": o['Name'],
             "Transform": xf(bx + (seen[nick] - 1) * 1.1, 1.4, bz, (0, 0, 0)),
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
         "The Tyrant always has 20 Health. Difficulty adds Buff HP, removed first:\n"
         "Difficulty sets two numbers: how many Specimens go into the Upgrade\n"
         "deck, and the Tyrant's starting Buff HP. Easy 5 Specimens and 3 Buff,\n"
         "Standard 6 and 4, Hard 7 and 7, Nobulous 8 and 11. Buff HP sits at the\n"
         "FRONT of the Tyrant's row, ahead of its\n"
         "Splices, which are shuffled into a random order. Put the Health die on the\n"
         "difficulty number; it steps right through Buff HP, the Splices, then Health.\n\n"
         "The Tyrant draws its dice AT RANDOM from 2 Purple / 2 Blue / 1 Green /\n"
         "1 Yellow - as many as its highest remaining Splice Value, 2 if none.\n"
         "Its FRONTMOST Splice adds its printed Value minus 1 to every attack.\n"
         "The Tyrant never taps; damage on that card does not weaken the effect.\n\n"
         "Tyrant Splices accumulate damage (the Health die tracks it). Rat Upgrades\n"
         "do NOT: an attack either meets an Upgrade's Value and destroys it, or it\n"
         "stops. No Rat card is ever part-damaged.\n\n"
         "Borrowing: 0 Upgrades any color, 1 no Purple, 2 Green/Yellow,\n"
         "3 Yellow only. Roll the borrowed die after; on a miss it is banished.\n\n"
         "Red is set aside after use and placed on a non-active Rat next turn.\n"
         "In the BATTLE Red is always available instead: commit it on top of the\n"
         "six pool dice, for free, but only if you do NOT tap an Upgrade.\n\n"
         "Strategy die marks the active Rat. Health die runs the Tyrant track.\n"
         "The Recovery die is not used."),
        ("NAP quick reference",
         "Three Time Slots a day. Reveal 2 Assignments, choose the Primary;\n"
         "a Setback must be taken. The Primary's dot queues the next slot's\n"
         "Special Recovery color.\n\n"
         "STR = rolls in the slot AND the cap on completions in the slot.\n"
         "Unresolved Assignments flip to Demand and stay in the row.\n"
         "6 Credits reaches the Final Exam. Draw 3 from the weighted pool.\n"
         "Lose 1 Health per success short. Survive all three to win."),
        ("AoS quick reference",
         "1 Reveal the Program.\n"
         "2 Reveal the Limitation. Withheld dice sit out this Program.\n"
         "3 Commit required-color dice -- these lock to their element.\n"
         "4 Finish the allocation.  5 Execute.\n\n"
         "Cannot supply a required color: lose 1 Health, do not execute,\n"
         "treat as failed.  Red never satisfies a required color.\n\n"
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

    objects = []
    # decks laid out in a parking row; the Lua script moves them on setup
    x, z = -34.0, -22.0
    for i, d in enumerate(DECKS):
        objects.append(build_deck(d, i + 1, (x, 2.0, z)))
        x += 3.0
        if x > 34:
            x, z = -34.0, z - 6.0
    objects.append(panel())
    objects += dice_objects()

    save = {
        "SaveName": "The Nobulous Set",
        "GameMode": "The Nobulous Set - BAT / NAP / AoS / NRJ",
        "Gravity": 0.5, "PlayArea": 0.8, "Date": "", "Table": "Table_Custom",
        "Sky": "Sky_Museum", "Note": "Fan expansion for 20 Strong. Prototype.",
        "Rules": "See the Notebook.",
        "TabStates": {str(i): t for i, t in enumerate(notebook())},
        "LuaScript": open(os.path.join(os.path.dirname(__file__), 'lua.lua')).read(),
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
    with open(os.path.join(os.path.dirname(OUT), 'REQUIRED_IMAGES.txt'), 'w') as f:
        f.write("Upload these to BASE_URL, keeping the filenames:\n\n")
        for n in sorted(need):
            p = os.path.join(SHEETS, n)
            f.write("  %-38s %s\n" % (n, 'ok' if os.path.exists(p) else 'MISSING'))
    print("image list ->", os.path.join(os.path.dirname(OUT), 'REQUIRED_IMAGES.txt'))


if __name__ == '__main__':
    main()
