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
        obj["CardID"] = deck_id * 100 + first
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
    # Checked in beside this script, so read it from there rather than
    # from the machine it was first written on - that hardcoded path
    # meant build_mod.py could not run anywhere else at all.
    src = json.load(open(os.path.join(os.path.dirname(
        os.path.abspath(__file__)), 'dice_objects.json')))
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
         "  Difficulty -- Easy / Standard / Hard / Nobulous. Every game uses\n"
         "  all four, and the setup message tells you that level's numbers.\n"
         "  For AoS it names the 8-card Program MIX to build; all three\n"
         "  Program decks are dealt, because difficulty mixes them rather\n"
         "  than choosing between them.\n"
         "  NRJ Tier -- off / I Agenda / II Contamination / III Exploitation.\n"
         "  Set the tier BEFORE pressing a setup button.\n\n"
         "The script deals and counts. It never enforces a rule."),
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
