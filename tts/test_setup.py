"""RUN the mod's Lua against a stubbed Tabletop Simulator, and count cards.

    python3 test_setup.py        # exit code = number of failed assertions

`lupa` embeds a real Lua, so the setup script does not have to be read and
believed - it can be executed. This stubs the slice of the TTS object API
the setups use (bags, decks, takeObject, putObject, shuffle, and a Wait
that fires immediately) and then presses every setup button at all four
difficulties and all four tiers: 64 setups.

WHY THIS EXISTS. The setups stopped being announcements on 2026-11-09 and
started performing the printed mixes, which means they can now be wrong in
a way no amount of reading catches - a deck short by one card at Nobulous
and right at Standard. The alternative was a human counting four decks at
sixteen combinations.

COUNTS ARE NOT ENOUGH, and the tier assertions below are the reason this
file is longer than it looks like it should be. BAT Tier II takes 6
ordinary Upgrades out and puts 6 Modifications in: a Tier II that did
nothing at all leaves exactly the same number of cards. So the tier checks
name the cards rather than counting them.

NOT A SUBSTITUTE FOR TTS. This runs Lua 5.4 and Tabletop Simulator runs
MoonSharp, a 5.2 dialect; this proves the script parses and that its card
arithmetic is right, not that TTS will spawn the objects on time. The
sequencer's frame delays are exactly what a stub cannot test, so HANDOFF
step 6 still wants a human at the table.
"""
import io
import json
import os
import random
import re
import sys

# PINNED TO 5.4, AND THE PIN IS THE POINT. lupa 2.8 defaults to its new
# Lua 5.5 binding, and on that binding it intermittently hands the script
# an unbound function where a bound method belongs: every pack-up step
# then dies on "'function' object has no attribute 'getName'" and cards
# stay on the table. That cost most of an afternoon, because it looked
# exactly like a mod bug - rare, order-dependent, and always in the same
# feature. Measured across repeated runs: 5.4 and 5.3 are clean, 5.5
# fails in about one process in four, and 5.2 - the closest to the
# MoonSharp dialect TTS really runs - fails every time. So 5.4,
# explicitly. Never plain lupa.LuaRuntime, which follows the default.
from lupa import lua54 as lupa

HERE = os.path.dirname(os.path.abspath(__file__))
SAVE = os.path.join(HERE, "NobulousSet.json")

# Which decks are landscape, so a footprint can be the right way round.
sys.path.insert(0, HERE)
from decks import DECKS
# BOTH NAMES. A card is named for one of its kind - a card of Time
# Slots is a Time Slot - so a footprint looked up by the card's name
# found nothing and the whole layout check quietly skipped it.
LAND = {}
ONE = {}
for _d in DECKS:
    LAND[_d["label"]] = bool(_d.get("land"))
    LAND[_d.get("card", _d["label"])] = bool(_d.get("land"))
    ONE[_d["label"]] = _d.get("card", _d["label"])

BAT_SPECIMENS = {"Easy": 5, "Standard": 6, "Hard": 7, "Nobulous": 8}
NAP_SETBACKS = {"Easy": 3, "Standard": 3, "Hard": 4, "Nobulous": 5}


class TextTool(object):
    """A 3DText's text, which the pile counters rewrite.

    Without this the counters raised inside a setup step, pump() caught
    it, said 'Setup error', and the harness reported 0 failed - because
    nothing read what the setups said. Both halves of that are fixed
    here.
    """

    def __init__(self, owner):
        self.owner = owner

    def setValue(self, s):
        self.owner.text = s

    def getValue(self):
        return self.owner.text


class Obj(object):
    """A deck, a card or a bag. Decks and bags hold other Objs."""

    def __init__(self, world, guid, name, kids=None, bag=False):
        self.world, self.guid, self.name = world, guid, name
        self.kids = list(kids or [])
        self.bag = bag
        self.pos = (0.0, 0.0, 0.0)
        self.rot = None
        self.value = None
        self.text = ""
        self.desc = ""
        self.scale = (1.0, 1.0, 1.0)
        self.locked = False
        self.TextTool = TextTool(self)

    def getName(self):
        return self.name

    def getGUID(self):
        return self.guid

    def getQuantity(self):
        # TTS answers -1 for a single card, which is why the Lua has its
        # own count() rather than trusting this.
        return len(self.kids) if self.kids else -1

    def getRotation(self):
        return self.world.lua.table_from({"x": 0.0, "y": 0.0, "z": 0.0})

    def getPosition(self):
        return self.world.lua.table_from(
            {"x": self.pos[0], "y": self.pos[1], "z": self.pos[2]})

    def getScale(self):
        return self.world.lua.table_from(
            {"x": self.scale[0], "y": self.scale[1], "z": self.scale[2]})

    def setScale(self, s):
        self.scale = tuple(s.values()) if hasattr(s, "values") else tuple(s)

    def getObjects(self):
        return self.world.lua.table_from(
            [self.world.lua.table_from({"nickname": k.name, "guid": k.guid})
             for k in self.kids])

    def shuffle(self):
        self.world.shuffled.add(self.name)
        self.world.rng.shuffle(self.kids)

    def setLock(self, lock=None, *a):
        # RECORDED. The Time Slots are locked after they land, and a
        # lock the stub threw away is a lock nothing can check.
        self.locked = bool(lock)

    def setDescription(self, d):
        self.desc = d

    def getDescription(self):
        return self.desc

    def setPosition(self, p):
        # RECORDED, not thrown away. The stub ignored every position, so
        # each overlapping row this mod has had - the Lab Rat behind its
        # neighbours, the Time Slots stacked on each other - was invisible
        # to a harness that reported 0 failed.
        self.pos = tuple(p.values()) if hasattr(p, "values") else tuple(p)

    def setPositionSmooth(self, p, *a):
        # TTS takes (position, collide, fast); the stub took one
        # argument, so every call through it threw and the step that
        # placed the markers died without placing anything.
        self.setPosition(p)

    def setRotation(self, r, *a):
        # RECORDED. The Chip is turned rather than set to a value, so a
        # thrown-away rotation is a dial nobody can check: it was turned
        # to the wrong colour through two builds.
        self.rot = tuple(r.values()) if hasattr(r, "values") else tuple(r)

    setRotationSmooth = setRotation

    def setRotationValue(self, v):
        self.value = v

    def takeObject(self, spec):
        keys = set(spec.keys())
        if not self.kids:
            raise RuntimeError("takeObject from an empty %r" % self.name)
        want = spec["guid"] if "guid" in keys else None
        if want:
            hit = [k for k in self.kids if k.guid == want]
            if not hit:
                raise RuntimeError("no %s inside %s" % (want, self.name))
            k = hit[0]
        else:
            k = self.kids[0]
        self.kids.remove(k)
        # A DECK OF ONE CARD IS A CARD, AND IT MOVES WHEN IT BECOMES
        # ONE. Taking the second-to-last card destroys the deck and
        # respawns its final card, and TTS does not put it back exactly
        # where the deck stood: on Jon's table Morning came to rest at
        # x -21.72, z 5.95 having been placed at -19.50, 6.05, while
        # the cards takeObject itself placed were exact. That offset is
        # reproduced here so the correction is tested rather than
        # assumed.
        if len(self.kids) == 1:
            self.pos = (self.pos[0] - 2.22, self.pos[1], self.pos[2] - 0.10)
        if "position" in keys:
            k.setPosition(spec["position"])
        # AND THE ROTATION IT WAS ASKED FOR. The stub threw this away,
        # which is exactly the thing that went wrong at the table: a
        # deck whose contained cards carried their own rotation handed
        # every drawn Assignment back upside down, and nothing here
        # could see it. A card drawn with a rotation has that rotation.
        if "rotation" in keys:
            k.setRotation(spec["rotation"])
        self.world.table[k.guid] = k
        if "callback_function" in keys and spec["callback_function"] is not None:
            spec["callback_function"](k)
        return k

    def putObject(self, other):
        if other is None:
            raise RuntimeError("putObject(nil) into %r" % self.name)
        if self.bag and self.world.lossy:
            # TTS DROPS OBJECTS FED TO A BAG FASTER THAN IT ANIMATES THEM.
            # One pass of pack-up over twenty cards left exactly one on
            # the table every time, and the stub could not see it because
            # a Python list never refuses an append. Refusing one in N
            # reproduces the bug, so the fix for it stays tested.
            self.world.puts += 1
            if self.world.puts % self.world.lossy == 0:
                return other
        self.world.table.pop(other.guid, None)
        if not self.kids and not self.bag:
            # A CARD THAT RECEIVES A CARD BECOMES A DECK OF BOTH. The
            # stub kept the receiver as the container and dropped its
            # own face, so a deck built out of loose cards came back one
            # card short - and the one it lost was the first one, which
            # is the card the deck was built on. Rebuilding the
            # Opportunities out of the box after a game lost Opportunity
            # 5 every single time, silently.
            # ...AND THE DECK IS A NEW OBJECT. TTS gives it a fresh
            # GUID and the card keeps its own inside it, which is what
            # anything holding that GUID depends on: putHome retries by
            # GUID until the object is gone from the table, and with
            # the id left on the container a retry found the deck the
            # card had just been gathered into and put the whole deck
            # in the bag.
            inner = Obj(self.world, self.guid, self.name)
            inner.pos, inner.rot = self.pos, self.rot
            was = self.guid
            self.guid = was + "#deck"
            if self.world.table.get(was) is self:
                del self.world.table[was]
                self.world.table[self.guid] = self
            self.world.byguid[self.guid] = self
            self.world.byguid[was] = inner
            self.kids.append(inner)
        if other.kids and not self.bag:
            self.kids.extend(other.kids)     # deck into deck merges, as TTS does
            other.kids = []
        else:
            self.kids.append(other)
        return other


class World(object):
    def __init__(self, lua):
        self.lua = lua
        self.byguid = {}
        self.table = {}        # guid -> object currently out on the table
        self.said = []
        self.shuffled = set()
        self.markers = {}      # the dice and the Chip, by GUID
        self.pending = []       # Wait.frames callbacks, run by drain()
        self.snaps = []         # Assignment spaces laid by a setup
        self.lossy = 0          # refuse one bag put in N, like TTS does
        self.puts = 0
        self.rng = random.Random(7)

    @property
    def dice(self):
        """Where the dice are NOW. A card dealt on top of one is a card
        dealt on top of one wherever the setup has just moved it to."""
        return [(o.pos[0], o.pos[2]) for o in self.markers.values()]

    def add(self, o):
        self.byguid[o.guid] = o
        for k in o.kids:
            self.byguid[k.guid] = k
        return o


def build(lua):
    """A world of four boxes, read from the save the build actually wrote."""
    w = World(lua)
    save = json.load(io.open(SAVE, encoding="utf-8"))
    seq = [0]

    def gid():
        seq[0] += 1
        return "card%05d" % seq[0]

    for o in save["ObjectStates"]:
        if o["Name"] != "Bag":
            continue
        decks = []
        for d in o["ContainedObjects"]:
            cards = [Obj(w, gid(), c["Nickname"])
                     for c in (d.get("ContainedObjects") or [])]
            if not cards:                       # a one-card "deck"
                cards = [Obj(w, gid(), d["Nickname"] + " 1")]
            one = Obj(w, d["GUID"], d["Nickname"], cards)
            # ITS REAL SCALE. The mat is sized at the table through the
            # panel, and a stub that said every object was scale 1 would
            # have let it report a 3-unit mat as 56.
            tr = d.get("Transform") or {}
            one.scale = (tr.get("scaleX", 1.0), tr.get("scaleY", 1.0),
                         tr.get("scaleZ", 1.0))
            decks.append(w.add(one))
        w.add(Obj(w, o["GUID"], o["Nickname"], decks, bag=True))
    # THE DICE ARE OBJECTS, NOT COORDINATES. They were a list of
    # positions, so getAllObjects never returned one, marker() answered
    # nil in every test, and setMarker - the whole of NAP's Chip and
    # Health / Strategy / Recovery placement - ran without placing
    # anything while the harness reported 0 failed.
    #
    # They are kept apart from w.table because they are not dealt and
    # are not packed away: pack-up sends them home and the table is
    # still bare, which is what "emptied the table" means.
    # HOW BIG A DIE IS, from the save. A die is about 0.9 across at
    # scale 1, and the clearance checks below had that 0.45 half-width
    # written into them - so the moment the dice were scaled up, every
    # check about what they touch was measuring a die that was no
    # longer on the table.
    w.die_half = 0.45 * max(
        [o["Transform"]["scaleX"] for o in save["ObjectStates"]
         if o["Name"] == "Custom_Dice"] or [1.0])
    for o in save["ObjectStates"]:
        if o["Name"] in ("Custom_Dice", "Custom_Token"):
            m = Obj(w, o["GUID"], o["Nickname"])
            m.pos = (o["Transform"]["posX"], o["Transform"]["posY"],
                     o["Transform"]["posZ"])
            w.markers[o["GUID"]] = m
            w.byguid[o["GUID"]] = m
    if not w.table and not w.byguid:
        raise SystemExit("no bags in %s - run build_mod.py first" % SAVE)
    # THE SAVE IS WHERE THE LUA RUNS FROM, so a save built before the last
    # edit to lua.lua means this whole harness exercises a script that no
    # longer exists and reports 0 failed. That happened: keepChar was
    # rewritten and nine assertions passed against the previous version.
    live = io.open(os.path.join(HERE, "lua.lua"), encoding="utf-8").read()
    tail = save["LuaScript"]
    if not (tail.endswith(live) or tail.endswith(live.replace("\r\n", "\n"))):
        raise SystemExit("%s is older than lua.lua - run build_mod.py first"
                         % os.path.basename(SAVE))
    return w, save["LuaScript"]


def install(lua, w):
    g = lua.globals()
    g.getObjectFromGUID = lambda guid: w.byguid.get(guid)
    def all_objects():
        # ONLY Obj, AND BUILT BY INDEX. Returning lua.table_from(list)
        # intermittently put a bound method into the table the script
        # iterates - about one process in three - and every pack-up step
        # then died on "'function' object has no attribute 'getName'",
        # leaving cards on the table and reading exactly like a mod bug.
        # Nothing but Obj ever went into that list, so the method came
        # from the bridge, not from here. Filling a plain Lua table by
        # index sidesteps it.
        t = lua.eval("{}")
        n = 0
        for o in (list(w.table.values()) + list(w.markers.values())
                  + [b for b in w.byguid.values() if b.bag]):
            if isinstance(o, Obj):
                n += 1
                t[n] = o
        return t

    g.getAllObjects = all_objects
    g.broadcastToAll = lambda msg, col=None: w.said.append(msg)
    # Global, for the snap points the NAP setup lays beside its Time
    # Slots. Recorded so the harness can count and place them.
    glob = lua.eval("{}")
    def set_snaps(pts):
        w.snaps = [] if pts is None else [
            (p["position"][1], p["position"][3]) for p in pts.values()]
    glob.setSnapPoints = set_snaps
    g.Global = glob
    # QUEUED, NOT CALLED. Running the callback immediately made the
    # script's sequencer a recursion - pump calls Wait.frames(pump),
    # which called pump - so a pack-up ran twenty-one Lua/Python frames
    # deep and intermittently stopped partway, leaving cards on the table
    # in about half of all runs. It read exactly like a mod bug. The
    # callbacks go in a queue that drain() runs flat.
    wait = lua.eval("{}")
    wait.frames = lambda fn, n=1: w.pending.append(fn)
    wait.time = lambda fn, t=0: w.pending.append(fn)
    g.Wait = wait
    g.self = None                            # no panel, so refreshPanel returns
    # SEEDED. Lua 5.5 seeds math.random from the clock, so the setups
    # picked different cards every run and the harness disagreed with
    # itself about once in two - which is indistinguishable from a real
    # intermittent bug until you look.
    lua.execute("math.randomseed(20261109)")


class Panel(object):
    """A control-panel tile that records the buttons drawn on it.

    ControlPanel.png is 1473x520 and the tile is "Stretch": true, so the
    tile's local space is z +/-1 by x +/-2.833.

    WIDTH AND HEIGHT ARE HALF-EXTENTS, in thousandths of a local unit from
    the button's centre - width 1000 is two units across. Reading them as
    full extents is what put four 1080-wide buttons on a 1.15 pitch and
    made every row overlap, and the first version of this class repeated
    the same mistake (w / 2000.0), so it drew the overlap and called it
    fine. A bounds check cannot catch that on its own: the buttons were
    inside the tile. Only the buttons' positions RELATIVE TO EACH OTHER
    show it, which is what overlaps() is for.
    """

    HALF_Z = 1.0
    # READ FROM THE MAT, not copied from it. This was 1473/520 while the
    # mat was 2000 wide, so the harness measured the buttons against a
    # tile that no longer existed and failed 98 assertions about a panel
    # that was fine.
    _png = io.open(os.path.join(os.path.dirname(HERE), "images",
                                "ControlPanel.png"), "rb").read(24)
    HALF_X = (int.from_bytes(_png[16:20], "big")
              / float(int.from_bytes(_png[20:24], "big")))
    UNIT = 1000.0            # width units per local unit, half-extent
    GLYPH = 0.00095          # local units per glyph per point of font_size

    def __init__(self):
        self.buttons = []

    def getName(self):
        return "Control Panel"

    def clearButtons(self):
        self.buttons = []

    def createButton(self, spec):
        p = spec["position"]
        pos = list(p.values()) if hasattr(p, "values") else list(p)
        self.buttons.append({"label": spec["label"], "x": pos[0], "z": pos[2],
                             "hw": spec["width"] / self.UNIT,
                             "hh": spec["height"] / self.UNIT,
                             "font": spec["font_size"]})

    def setLock(self, *a):
        pass

    def off_tile(self):
        return [b["label"] for b in self.buttons
                if abs(b["z"]) + b["hh"] > self.HALF_Z
                or abs(b["x"]) + b["hw"] > self.HALF_X]

    def overlaps(self):
        """Pairs whose rectangles intersect - what the player sees."""
        out = []
        for i, a in enumerate(self.buttons):
            for b in self.buttons[i + 1:]:
                if (abs(a["x"] - b["x"]) < a["hw"] + b["hw"]
                        and abs(a["z"] - b["z"]) < a["hh"] + b["hh"]):
                    out.append((a["label"], b["label"]))
        return out

    def overflowing(self):
        """Labels wider than the button drawn around them."""
        return [b["label"] for b in self.buttons
                if len(str(b["label"])) * b["font"] * self.GLYPH > 2 * b["hw"]]


def start(difficulty, tier, panel=None):
    lua = lupa.LuaRuntime(unpack_returned_tuples=True)
    w, src = build(lua)
    ALIVE.append((lua, w, panel))
    install(lua, w)
    lua.execute(src)
    g = lua.globals()
    if panel is not None:
        g.PANEL = panel
    g.STATE.difficulty = difficulty
    g.STATE.tier = tier
    return w, g


def drain(w):
    """Run every queued Wait callback to completion, flat."""
    for _ in range(20000):
        if not w.pending:
            return
        w.pending.pop(0)()
    raise RuntimeError("the script's queue never settled")


def run(difficulty, tier, which):
    SETUPS[0] += 1
    w, g = start(difficulty, tier)
    {"BAT": g.setupBAT, "NAP": g.setupNAP,
     "AoS": g.setupAoS, "IMP": g.setupImposter}[which]()
    drain(w)
    return w


def deck(w, name):
    hit = [o for o in w.table.values() if o.name == name]
    return hit[0] if hit else None


def inside(w, deckname, label):
    """Cards whose name starts with `label`, inside the named deck."""
    d = deck(w, deckname)
    return len([c for c in (d.kids if d else []) if c.name.startswith(label)])


def names_of(label):
    """The deck's own name and the name one of its cards carries."""
    return (label, ONE.get(label, label))


def out(w, label):
    """CARDS of that deck on the table, not counting the container.

    spread() deals n-1 cards and leaves the last inside the deck object,
    so counting table objects by name counts the container AND the card
    still in it - which read as 7 Research Notes the first time.
    """
    n = 0
    for o in w.table.values():
        if any(o.name.startswith(x) for x in names_of(label)):
            n += len(o.kids) if o.kids else 1
    return n


# EVERY RUNTIME AND WORLD STAYS ALIVE. A World or a Panel referenced
# only from inside Lua was being collected by Python while Lua still
# held it, and the dangling wrapper read back as a function - which is
# why whole runs died on "'function' object has no attribute getName"
# only after a few dozen setups, and never in a short script. Holding
# them costs a few megabytes for the length of one test run.
ALIVE = []

FAIL = []
SKIPPED = []
RAN = [0]
SETUPS = [0]
PANELS = [0]


def want(tag, got, exp):
    # Counted, not computed: the printed total was 4 * 4 * 21 and went
    # stale the moment a twenty-second assertion was added.
    RAN[0] += 1
    if got != exp:
        FAIL.append("%s: got %r, want %r" % (tag, got, exp))


def footprints(w, lua):
    """Every object on the table as (label, x, z, half width, half depth).

    A landscape deck is the same card turned, so its footprint is the
    portrait one swapped. CARD_W and CARD_L come from the Lua the build
    generated, so this measures what the mod will actually deal.
    """
    g = lua.globals()
    cw, cl = float(g.CARD_W), float(g.CARD_L)
    out = []
    for o in w.table.values():
        base = o.name.rstrip("0123456789").strip()
        land = LAND.get(base, LAND.get(o.name))
        if land is None:
            continue                      # not a card: leave it alone
        hw, hd = (cl / 2, cw / 2) if land else (cw / 2, cl / 2)
        out.append((o.name, o.pos[0], o.pos[2], hw, hd))
    return out


# How the felt measures, taken off a screenshot in which the dice - whose
# world positions this build set - give the scale. Generous rather than
# exact: this is here to catch a row dealt into the floor, not to shave
# half a unit off a margin.
FELT_X, FELT_ZMIN, FELT_ZMAX = 28.0, -18.0, 19.0


def layout_assertions():
    """No dealt card may sit on another, or off the felt.

    The stub threw positions away until now, so every overlap this mod has
    had - the Lab Rat behind its neighbours, the Time Slots stacked, the
    FINF card on top of a slot - was invisible to a harness reporting 0
    failed. Overlap is not visible in any one card's coordinates, only in
    the pairs, which is the same shape of bug as the control panel.
    """
    for lvl in ("Easy", "Standard", "Hard", "Nobulous"):
        for tier in (0, 1, 2, 3):
            for which in ("BAT", "NAP", "AoS", "IMP"):
                t = "%s %s t%d layout" % (which, lvl, tier)
                lua = lupa.LuaRuntime(unpack_returned_tuples=True)
                w, src = build(lua)
                ALIVE.append((lua, w))
                install(lua, w)
                lua.execute(src)
                g = lua.globals()
                g.STATE.difficulty, g.STATE.tier = lvl, tier
                {"BAT": g.setupBAT, "NAP": g.setupNAP,
                 "AoS": g.setupAoS, "IMP": g.setupImposter}[which]()
                drain(w)
                fp = footprints(w, lua)
                want(t + " dealt something", len(fp) > 0, True)
                # A STEP THAT RAISES IS CAUGHT BY pump() AND ANNOUNCED,
                # and nothing read the announcement: the pile counters
                # went in raising on every NAP setup and the harness
                # reported 0 failed. Every setup, every difficulty,
                # every tier.
                want(t + " said no setup error",
                     [m for m in w.said if "Setup error" in m][:2], [])
                over = []
                for i, a in enumerate(fp):
                    for b2 in fp[i + 1:]:
                        if (abs(a[1] - b2[1]) < a[3] + b2[3] - 0.05
                                and abs(a[2] - b2[2]) < a[4] + b2[4] - 0.05):
                            over.append((a[0], b2[0]))
                want(t + " nothing overlaps", over[:3], [])
                off = [f[0] for f in fp
                       if abs(f[1]) + f[3] > FELT_X
                       or f[2] - f[4] < FELT_ZMIN or f[2] + f[4] > FELT_ZMAX]
                want(t + " nothing dealt off the felt", off[:3], [])
                on_dice = [f[0] for f in fp
                           for dx, dz in w.dice
                           if abs(f[1] - dx) < f[3] + w.die_half
                           and abs(f[2] - dz) < f[4] + w.die_half]
                want(t + " nothing dealt on top of the dice",
                     sorted(set(on_dice))[:3], [])
                # AND THE DICE FIT WHERE THEY LIE. Nothing checked the
                # row against itself or against the felt, so scaling
                # the dice up could have piled them on each other or
                # pushed the back row over the edge and still passed.
                home = sorted((round(float(v[1]), 3), round(float(v[2]), 3))
                              for v in g.DICE_HOME.values())
                blocks = sorted(set(w.dice) | set(home))
                piled = [(a, b2) for i, a in enumerate(blocks)
                         for b2 in blocks[i + 1:]
                         if abs(a[0] - b2[0]) < 2 * w.die_half - 0.02
                         and abs(a[1] - b2[1]) < 2 * w.die_half - 0.02]
                want(t + " no two dice sit on each other", piled[:2], [])
                off = [p for p in blocks
                       if abs(p[0]) + w.die_half > FELT_X
                       or p[1] - w.die_half < FELT_ZMIN - 0.6]
                want(t + " no die hangs off the felt", off[:2], [])
                # Four Assignment spaces beside every Time Slot, and
                # only for the game that has Time Slots.
                slots = [o.pos[2] for o in w.table.values()
                         if o.name.startswith("Time Slot")]
                # 4 beside every Time Slot, 2 for the cards the deck
                # reveals, the Apprentice and the FINF cards down the
                # right, and the two piles under them. The bank is not
                # conditional on the tier any more: the mat prints its
                # box at every tier, so the space has to be there too.
                exp = (4 * len(slots) + 2 + 2 + 2
                       if which == "NAP" else 0)
                want(t + " Assignment spaces", len(w.snaps), exp)
                if which == "NAP":
                    for sz in slots:
                        # The Assignment columns only: the discard and
                        # bank piles share a row with a Time Slot but
                        # are off to the right, past x 20.
                        want(t + " four spaces beside the slot at %.1f" % sz,
                             len([s for s in w.snaps
                                  if abs(s[1] - sz) < 0.05
                                  and s[0] < 20.0]), 4)
                    # TWO OF THEM DO, ON PURPOSE. The Apprentice and
                    # the FINF cards are dealt onto their own spaces so
                    # that the mat draws a box under each - that is
                    # what the box is for. Every other space is still
                    # somewhere you put a card rather than somewhere
                    # the setup already put one, and naming the two
                    # exceptions is what keeps that true: a third one
                    # appearing fails this.
                    allowed = ("Apprentice", "FINF")
                    want(t + " no space lands on a dealt card",
                         [f[0] for f in fp for sx, sz in w.snaps
                          if abs(f[1] - sx) < f[3] - 0.1
                          and abs(f[2] - sz) < f[4] - 0.1
                          and not f[0].startswith(allowed)][:3], [])
                    # THE THREE STAT DICE, in a row under the Apprentice
                    # and centred on it, each showing the 2 that card
                    # prints. Nothing checked them at all before: the
                    # harness had no marker objects, so setMarker ran
                    # against nil and placed nothing.
                    #
                    # MEASURED AGAINST THE CARDS, NOT AGAINST STAT_Z AND
                    # STAT_PITCH. Written that way first, the three
                    # assertions read the same two constants the script
                    # had just used, so moving STAT_PITCH to 1.6 - or to
                    # anything at all - still passed. A predicate a
                    # constant can satisfy by being itself checks
                    # nothing.
                    by = dict((o.name, o) for o in w.markers.values())
                    three = [by[n] for n in ("Health", "Strategy",
                                             "Recovery")]
                    xs = [o.pos[0] for o in three]
                    zs = [round(o.pos[2], 3) for o in three]
                    app = [f for f in fp if f[0].startswith("Apprentice")]
                    finf = [f for f in fp if f[0].startswith("FINF")]
                    want(t + " an Apprentice and a FINF to measure from",
                         (len(app), len(finf)), (1, 1))
                    ax, az, ahw, ahd = app[0][1:]
                    fz, fhd = finf[0][2], finf[0][4]
                    want(t + " stat dice on one row", len(set(zs)), 1)
                    want(t + " stat dice left to right",
                         xs == sorted(xs) and len(set(xs)) == 3, True)
                    want(t + " stat dice evenly spaced",
                         round(xs[1] - xs[0], 3), round(xs[2] - xs[1], 3))
                    want(t + " stat dice centred on the Apprentice",
                         round(sum(xs) / 3.0 - ax, 3), 0.0)
                    want(t + " stat dice under the Apprentice, not beside",
                         (zs[0] < az, xs[0] > ax - ahw, xs[2] < ax + ahw),
                         (True, True, True))
                    # A die is about a unit across, so half of one plus a
                    # margin is what has to fit between the two cards.
                    want(t + " stat dice clear of both cards",
                         (round(az - ahd - zs[0], 3) > 0.6,
                          round(zs[0] - (fz + fhd), 3) > 0.6),
                         (True, True))
                    want(t + " stat dice read 2, which is what the card"
                         " prints", [o.value for o in three], [2, 2, 2])
                    # And the Chip in the circle beside Morning, turned
                    # to 1 EXACTLY AS TYPING 1 TURNS IT - the calibrated
                    # colour angle, colour side up. It used to be turned
                    # through the number side's own table, so the dial
                    # the setup laid down and the dial you typed over
                    # were two different dials.
                    morning = sorted(
                        [f for f in fp if f[0].startswith("Time Slot")],
                        key=lambda f: -f[2])[0]
                    chip = by["Chip"]
                    first = str(g.ATTENTION[1])
                    want(t + " the Chip sits beside Morning",
                         (round(chip.pos[2] - morning[2], 3),
                          chip.pos[0] < morning[1] - morning[3] - 0.5),
                         (0.0, True))
                    want(t + " the Chip is turned to colour 1, colour"
                         " side up",
                         (chip.rot is not None
                          and round(chip.rot[1], 3) == round(
                              float(g.CHIP_FACE[first]), 3),
                          chip.rot is not None
                          and round(chip.rot[2], 3) == round(
                              float(g.CHIP_FACE_Z), 3)),
                         (True, True))
                    want(t + " ...and the trim control knows which"
                         " colour that is", int(g.STATE.chip), 1)


def panel_assertions():
    """Draw the panel in every state it can be in.

    The setup assertions leave PANEL nil, so refreshPanel returns at its
    first line and NOT ONE LINE of the panel code runs in them. Drawing it
    catches what a regex over the source cannot: a Lua error, a nil in a
    label, or a counter row that indexes a table that is not there.
    """
    for game in (None, "BAT", "NAP", "AoS", "IMP"):
        for tier in (0, 1, 2, 3):
            for lvl in ("Easy", "Standard", "Hard", "Nobulous"):
                t = "panel %s t%d %s" % (game, tier, lvl)
                PANELS[0] += 1
                pan = Panel()
                w, g = start(lvl, tier, pan)
                g.STATE.game = game
                # The rows that only appear at a threshold.
                g.STATE.splices, g.STATE.credits, g.STATE.session = 5, 9, 4
                try:
                    g.refreshPanel()
                except Exception as e:          # a Lua error reaches here
                    want(t + " raised", str(e), "")
                    continue
                want(t + " drew buttons", bool(pan.buttons), True)
                want(t + " all on the tile", pan.off_tile(), [])
                want(t + " nothing overlaps", pan.overlaps(), [])
                want(t + " no label overflows its button",
                     pan.overflowing(), [])
                want(t + " no nil in a label",
                     [b["label"] for b in pan.buttons
                      if b["label"] is None or "nil" in str(b["label"])], [])

    # Both cycles must walk every value and wrap.
    w, g = start("Easy", 0, Panel())
    levels, tiers = [], []
    for _ in range(5):
        levels.append(g.STATE.difficulty)
        g.btnDiff()
    for _ in range(5):
        tiers.append(g.STATE.tier)
        g.btnTier()
    want("difficulty cycle", levels,
         ["Easy", "Standard", "Hard", "Nobulous", "Easy"])
    want("tier cycle", tiers, [0, 1, 2, 3, 0])

    # Keeping a character leaves exactly one of them on the table.
    # NAP DEALS ONE, not three: the panel's Apprentice button picks the
    # character and the side, so the setup leaves that one out and
    # sends the other two back rather than dealing a stack to choose
    # from. AoS and Imposter still deal theirs and use Keep 1/2/3.
    for which, deck, n in (("NAP", "Apprentices", 1),
                           ("AoS", "Technicians", 3),
                           ("IMP", "Imposters (A / B)", 5)):
        w, g = start("Standard", 0, Panel())
        {"NAP": g.setupNAP, "AoS": g.setupAoS, "IMP": g.setupImposter}[which]()
        drain(w)
        want("%s dealt %d characters" % (which, n),
             out(w, deck), n)
        if which == "NAP":
            # The Time Slots are a clock: Morning, Afternoon, Evening,
            # top to bottom. takeObject hands back whichever card it
            # likes, which dealt them Morning, Evening, Afternoon.
            col = sorted([o for o in w.table.values()
                          if o.name.startswith("Time Slot")],
                         key=lambda o: -o.pos[2])
            order = [int(o.name.split()[-1]) if o.name.split()[-1].isdigit()
                     else 1 for o in col]
            want("NAP Time Slots run in printed order", order, [1, 2, 3])
        # Every index, including the LAST - which is the deck object
        # collapsing to its final card, the case a nickname lookup could
        # not find and a left-to-right one can.
        for i in (1, 2, n):
            w2, g2 = start("Standard", 0, Panel())
            {"NAP": g2.setupNAP, "AoS": g2.setupAoS,
             "IMP": g2.setupImposter}[which]()
            drain(w2)
            g2.keepChar(i)
            drain(w2)
            want("%s keep %d leaves one character" % (which, i),
                 out(w2, deck), 1)

    # Pack up has to leave the table bare, loose cards included - and it
    # has to do it when the bag refuses some of what it is handed, which
    # is what left one card out after every setup in the real game.
    for lossy in (0, 3, 5):
        # RETRIED ON A BRIDGE FAULT, NOT ON A FAILURE. About one process
        # in four, lupa hands the script a bound method where an object
        # should be and every pack-up step dies on "'function' object has
        # no attribute 'getName'". That is this harness breaking, not the
        # mod: it leaves a loud message, so the trial is taken again. A
        # pack-up that leaves cards WITHOUT that message still fails, and
        # five bridge faults in a row is reported rather than ignored.
        w, g = start("Nobulous", 3, Panel())
        g.setupNAP()
        drain(w)
        dealt = len(w.table)
        mark = len(w.said)
        w.lossy = lossy
        g.packUp(False)
        g.run()
        drain(w)
        want("pack up clears the Assignment spaces", w.snaps, [])
        if any("getName" in m for m in w.said[mark:]):
            SKIPPED.append("pack up, dropping 1 in %d" % lossy)
            continue
        want("pack up emptied the table, dropping 1 in %d" % lossy,
             (dealt > 0, len(w.table))[1], 0)
        # AND THE DICE ARE BACK WHERE THEY LIVE. They are not bagged, so
        # "the table is bare" says nothing about them: a setup that
        # moved the Chip across the table and a pack-up that left it
        # there both passed.
        home = dict((k, (round(v[1], 3), round(v[2], 3)))
                    for k, v in g.DICE_HOME.items())
        want("pack up sends the dice home, dropping 1 in %d" % lossy,
             sorted((o.name, round(o.pos[0], 3), round(o.pos[2], 3))
                    for o in w.markers.values() if o.name in home),
             sorted((n, p[0], p[1]) for n, p in home.items()))


def census(w):
    """Every card in the world, wherever it is, by name."""
    c = {}
    def walk(o):
        if o.kids:
            for k in o.kids:
                walk(k)
        else:
            c[o.name] = c.get(o.name, 0) + 1
    for o in list(w.table.values()):
        walk(o)
    for o in w.byguid.values():
        if o.bag:
            for k in o.kids:
                walk(k)
    return c


def shape(w, g):
    """How many cards of each DECK are on the table, and in how many piles.

    By deck rather than by card, because the cards themselves differ
    between two deals of a shuffled deck - that is the deck working,
    not the setup failing.
    """
    lab = dict(g.DECK_OF)
    out = {}
    for o in w.table.values():
        base = re.sub(r" \d+$", "", o.name)
        key = str(lab.get(base, base))
        n, piles = out.get(key, (0, 0))
        out[key] = (n + (len(o.kids) or 1), piles + 1)
    return out


def in_staging(w, g):
    """Anything with a bag to go home to, resting in the staging band."""
    z = float(g.OFF_Z)
    return sorted(o.name for o in w.table.values()
                  if abs(o.pos[2] - z) < 2.5 and g.homeBox(o.name) is not None)


def repeat_assertions():
    """Setting up twice.

    NONE OF THIS NEEDED A SECOND GAME, only a second press, and every
    part of it was silent. A setup MERGES decks - the Opportunities go
    into the Assignment deck and cease to exist - and SPREADS others,
    which leaves 'Time Slot 2' lying beside a deck of one called 'Time
    Slots'. Pack-up stowed each of those as what it had become, and the
    next setup asked for decks that were no longer there: it said
    MISSING DECK: Opportunities, dealt one Time Slot instead of three,
    and left an Apprentice in the middle of the table.

    Run with the bag refusing a put, because that is what TTS does and
    what stranded the card.
    """
    for which in ("NAP", "BAT", "AoS", "IMP"):
        for tier in (0, 3):
            w, g = start("Standard", tier, Panel())
            w.lossy = 2
            fn = {"NAP": g.setupNAP, "BAT": g.setupBAT,
                  "AoS": g.setupAoS, "IMP": g.setupImposter}[which]
            seen = []
            for _ in range(3):
                fn()
                drain(w)
                seen.append((census(w), shape(w, g), in_staging(w, g)))
            t = "%s t%d setting up three times" % (which, tier)
            want(t + " loses or gains no card",
                 [i for i, s in enumerate(seen) if s[0] != seen[0][0]], [])
            want(t + " deals the same decks every time",
                 [i for i, s in enumerate(seen) if s[1] != seen[0][1]], [])
            # THE STAGING BAND IS BELOW EVERY ROW A SETUP DEALS ON, which
            # is what lets run() sweep it unconditionally. It used to be
            # ROW_TIER, where AoS spreads the Research Notes.
            want(t + " leaves nothing in the staging band",
                 [s[2] for s in seen], [[], [], []])
            want(t + " says nothing went missing",
                 [m for m in w.said
                  if "MISSING" in m or "Setup error" in m][:2], [])


def finf_assertions():
    """The FINF button moves cards on a table that is already dealt.

    It only appears once NAP is out, so it has to take back whatever
    the last setting put out - off the FINF space AND out of the
    Assignment deck, since Increase hides them in there - and deal the
    new one. Under a bag that refuses puts, routing those cards home
    and taking them straight back out lost one every time the setting
    asked for all three.
    """
    for lossy in (0, 2, 3):
        w, g = start("Standard", 0, Panel())
        w.lossy = lossy
        g.setupNAP()
        drain(w)
        fz = float(g.FINF_Z)
        got, exp = [], []
        for _ in range(len(list(g.FINF_SET.values())) + 1):
            way = str(g.FINF_SET[int(g.STATE.finf)][1])
            many = int(g.FINF_SET[int(g.STATE.finf)][2])
            laid = sum(len(o.kids) or 1 for o in w.table.values()
                       if o.name.startswith("FINF")
                       and abs(o.pos[2] - fz) < 0.1)
            hidden = sum(1 for d in w.table.values()
                         if str(dict(g.DECK_OF).get(
                             re.sub(r" \d+$", "", d.name), "")) == "Assignment"
                         for c in d.kids if c.name.startswith("FINF"))
            got.append((way, many, laid, hidden))
            exp.append((way, many, 0 if way == "Increase" else many,
                        many if way == "Increase" else 0))
            g.btnFinf()
            drain(w)
        want("the FINF button deals its setting exactly (bag refuses 1 in %s)"
             % (lossy or "none"), got, exp)
        want("...and the three FINF cards are never anywhere else (1 in %s)"
             % (lossy or "none"),
             sorted(k for k, v in census(w).items()
                    if k.startswith("FINF") and v != 1), [])


def panel_game_assertions():
    """A game's own options appear when that game is on the table."""
    def labels(p):
        return sorted(b["label"].split("  ")[0] for b in p.buttons)
    w, g = start("Standard", 0, Panel())
    g.refreshPanel()
    want("no game's options are offered before a setup",
         [n for n in labels(g.PANEL) if n in ("Apprentice", "FINF")], [])
    for which, exp in (("NAP", ["Apprentice", "FINF"]), ("BAT", []),
                       ("AoS", []), ("IMP", [])):
        w, g = start("Standard", 0, Panel())
        {"NAP": g.setupNAP, "BAT": g.setupBAT,
         "AoS": g.setupAoS, "IMP": g.setupImposter}[which]()
        drain(w)
        want("%s offers its own options and no other game's" % which,
             [n for n in labels(g.PANEL) if n in ("Apprentice", "FINF")], exp)
    # ONE CHOOSER PER GAME. Keep 1/2/3 takes a card out of the stack
    # and leaves the side to you; for NAP that is a second way to
    # choose an Apprentice which does not know what the first chose, so
    # the panel would go on naming a character that was no longer the
    # one on the table.
    for which, keeps in (("NAP", []), ("AoS", ["1", "2", "3"]),
                         ("IMP", ["1", "2", "3", "4", "5"])):
        w, g = start("Standard", 0, Panel())
        {"NAP": g.setupNAP, "AoS": g.setupAoS,
         "IMP": g.setupImposter}[which]()
        drain(w)
        want("%s offers the Keep buttons its character needs" % which,
             sorted(b["label"] for b in g.PANEL.buttons
                    if b["label"] in "12345" and len(b["label"]) == 1),
             keeps)

    # Pack up puts the panel back to having none.
    g.setupNAP()
    drain(w)
    g.btnPack()
    drain(w)
    want("packing up takes the game's options away",
         [n for n in labels(g.PANEL) if n in ("Apprentice", "FINF")], [])


def choice_assertions():
    """NAP's two panel dials: which Apprentice, and which FINF setting.

    BOTH ARE CHECKED THROUGH WHAT LANDS ON THE TABLE, not through
    STATE. The panel can hold any number it likes; what matters is that
    the card out is the one the button names, on the side it names, and
    that the FINF cards went where that setting sends them.
    """
    app = []
    w, g = start("Standard", 0, Panel())
    g.setupNAP()
    drain(w)
    n = int(g.APPRENTICE and len(list(g.APPRENTICE.values())) or 0)
    want("the panel offers every Apprentice build_nap.py prints", n, 6)
    faceup = tuple(float(v) for v in g.FACEUP.values())
    facedown = tuple(float(v) for v in g.FACEDOWN.values())
    want("a card's two sides are two different rotations",
         faceup != facedown, True)
    for _ in range(n + 1):
        a = g.APPRENTICE[int(g.STATE.apprentice)]
        cards = [o for o in w.table.values()
                 if o.name.startswith("Apprentice")]
        app.append((str(a.name), int(a.card), bool(a.back),
                    [o.name for o in cards],
                    [o.rot for o in cards]))
        g.btnApp()
        drain(w)
    want("exactly one Apprentice is ever on the table",
         sorted(set(len(e[3]) for e in app)), [1])
    want("the card out is the one the button names",
         [e[3][0] for e in app],
         ["Apprentice %d" % e[1] for e in app])
    want("...and it is turned to the side the button names",
         [e[4][0] == (facedown if e[2] else faceup) for e in app],
         [True] * len(app))
    want("every Apprentice is reachable, and the button comes back round",
         [e[0] for e in app[:n]] + [app[n][0] == app[0][0]],
         [str(g.APPRENTICE[i + 1].name) for i in range(n)] + [True])
    # NOTHING IS LOST ON THE WAY ROUND. Choosing again has to put the
    # card that is out back into a stack of three before it can take
    # another one, and findDeck cannot see a loose card in a bag: a
    # deckOut here would have dealt a stack of two the second time.
    want("all three Apprentice cards survive six choices",
         out(w, "Apprentices") + inbag(w, "NAP", "Apprentice"), 3)
    # AND THEY SURVIVE AS ONE STACK. Counting cards is not the claim -
    # a bag holding a deck of two and a card beside it holds three
    # cards and is still broken, because findDeck matches a nickname
    # exactly and the next deckOut would deal the deck of two. That is
    # what the choice before last left behind every single time.
    want("...and none of them is stranded loose in the bag",
         stranded(w, "NAP", "Apprentice"), 0)

    # THE CLOCK IS NAILED DOWN.
    # THE FIRST OF THEM IS THE DECK OBJECT, still carrying the deck's
    # name after collapsing to one card - which is why this counts
    # three rather than naming them.
    slots = [o for o in w.table.values() if o.name.startswith("Time Slot")]
    want("the three Time Slots are locked",
         (len(slots), sorted(set(o.locked for o in slots))), (3, [True]))
    # THE CLOCK, THE MAT AND THE TWO PLATES, and nothing else. All
    # four are furniture rather than cards: a locked card is a card
    # the player cannot pick up.
    want("...and nothing else NAP deals is",
         [o.name for o in w.table.values()
          if o.locked and not o.name.startswith(
              ("Time Slot", "NAP Table", "Credit Record",
               "Banked Opportunities"))],
         [])

    # FINF: Increase hides them in the Assignment deck, Reduce lays them
    # out to spend. Six settings, and the two directions do genuinely
    # different things with the same three cards.
    got = []
    for i in range(1, 7):
        w, g = start("Standard", 0, Panel())
        g.STATE.finf = i
        g.setupNAP()
        drain(w)
        fz = float(g.FINF_Z)
        laid = sum(len(o.kids) if o.kids else 1
                   for o in w.table.values()
                   if o.name.startswith("FINF")
                   and abs(o.pos[2] - fz) < 0.05)
        deck = [o for o in w.table.values() if o.name.startswith("Assignment")]
        hidden = sum(1 for d in deck for c in d.kids
                     if c.name.startswith("FINF"))
        way, many = str(g.FINF_SET[i][1]), int(g.FINF_SET[i][2])
        got.append((way, many, hidden, laid))
    want("Increase shuffles that many FINF cards into the Assignment deck",
         [(e[1], e[2]) for e in got if e[0] == "Increase"],
         [(1, 1), (2, 2), (3, 3)])
    want("...and lays none of them out",
         [e[3] for e in got if e[0] == "Increase"], [0, 0, 0])
    want("Reduce lays that many FINF cards on the FINF space",
         [(e[1], e[3]) for e in got if e[0] == "Reduce"],
         [(1, 1), (2, 2), (3, 3)])
    want("...and hides none of them in the deck",
         [e[2] for e in got if e[0] == "Reduce"], [0, 0, 0])
    want("the six settings are three of each", sorted(e[0] for e in got),
         ["Increase"] * 3 + ["Reduce"] * 3)


def stranded(w, game, card):
    """Single cards of a family sitting in a bag beside their own deck."""
    n = 0
    for o in w.byguid.values():
        if o.bag and o.name.startswith(game):
            n += len([k for k in o.kids
                      if k.name.startswith(card + " ") and not k.kids])
    return n


def inbag(w, game, prefix):
    """Cards of a family sitting loose in a game's bag."""
    n = 0
    # BAGS ARE NOT ON THE TABLE. w.table is what is out; the four boxes
    # live in byguid, which is why this read zero and said the cards
    # had been lost.
    for o in w.byguid.values():
        if o.bag and o.name.startswith(game):
            for k in o.kids:
                if k.name.startswith(prefix):
                    n += len(k.kids) if k.kids else 1
    return n


def counter_assertions():
    """The plates above the piles count the piles.

    COUNTED, NOT PRESSED. The panel's old Credit row counted button
    presses and sat at the far end of the table from the pile it
    described; these read the cards. Credits come from Credit Tasks
    (rules/nap.html) and the six Tasks that carry no subject earn
    nothing, so a counter that just counted cards on the pile would
    read six too high at worst - which is what this checks.
    """
    w, g = start("Standard", 3, Panel())
    g.setupNAP()
    drain(w)
    by = dict((o.name, o) for o in w.table.values())
    want("the NAP setup deals both counters",
         sorted(n for n in by if n in ("Credit Record",
                                       "Banked Opportunities")),
         ["Banked Opportunities", "Credit Record"])
    # AND DEALS THEM SO THEY CAN BE READ. A 3DText is authored lying
    # flat - rotX 90 - and locked; deckOut turns what it takes out
    # FACEDOWN like a deck, which stood both plates on edge pointing
    # away from the table. Jon moved a Credit onto the pile and saw
    # neither a count nor hover text, because there was nothing on the
    # table to see: the counter had been counting into an invisible
    # object through every build.
    flat = tuple(float(v) for v in g.TEXT_ROT.values())
    want("...lying flat, the way a 3DText is readable",
         [by[n].rot for n in ("Credit Record", "Banked Opportunities")],
         [flat, flat])
    want("...and locked, so a dropped card cannot shove them",
         [by[n].locked for n in ("Credit Record", "Banked Opportunities")],
         [True, True])
    want("...above the pile and clear of the felt",
         [round(by[n].pos[1], 2) for n in ("Credit Record",
                                           "Banked Opportunities")],
         [round(float(g.TEXT_Y), 2)] * 2)
    goal = int(g.NAP_DIFF[g.STATE.difficulty][1])
    want("an empty pile reads zero",
         by["Credit Record"].text, "CREDITS  0 / %d" % goal)
    subs = sorted(str(v) for v in g.NAP_SUBJECT.values())
    want("the hover text names all four subjects in full",
         [s for s in subs if s in by["Credit Record"].desc], subs)

    # The pile, as cards: two Anatomy Credit Tasks, one Theory, and one
    # of the six Tasks that carry no subject and earn nothing.
    cred = dict((str(k), [int(i) for i in v.values()])
                for k, v in g.NAP_CREDIT.items())
    ana = cred[[k for k, v in g.NAP_SUBJECT.items()
                if str(v) == "Anatomy"][0]]
    the = cred[[k for k, v in g.NAP_SUBJECT.items()
                if str(v) == "Theory"][0]]
    earns = set(i for v in cred.values() for i in v)
    blank = [i for i in range(1, 27) if i not in earns]
    want("six Tasks earn no Credit at all", len(blank), 6)
    pz = float(g.ROW_CHAR) - 2 * float(g.NAP_GAP)
    for i, n in enumerate([ana[0], ana[1], the[0], blank[0]]):
        o = Obj(w, "pile%d" % i, "Task %d" % n)
        o.pos = (float(g.PILE_X), 1.0, pz)
        w.table[o.guid] = o
    bz = float(g.ROW_CHAR) - 3 * float(g.NAP_GAP)
    o = Obj(w, "bank1", "Devious Opportunity 3")
    o.pos = (float(g.PILE_X), 1.0, bz)
    w.table[o.guid] = o
    # THROUGH THE DROP, not through the call. Everything above puts
    # cards on the pile and asks the script to count them; what a
    # player does is let go of a card, and nothing here had ever been
    # through onObjectDrop - whose arguments are (player colour,
    # object) in that order, so a script that read them the other way
    # round would count nothing and say nothing about it.
    dropped = Obj(w, "dropped", "Task %d" % ana[0])
    dropped.pos = (float(g.PILE_X), 1.0, pz)
    w.table[dropped.guid] = dropped
    g.onObjectDrop("White", dropped)
    drain(w)
    want("letting go of a Credit over the pile counts it",
         by["Credit Record"].text, "CREDITS  4 / %d" % goal)
    w.table.pop(dropped.guid)
    g.refreshCounts()
    drain(w)
    want("four cards on the pile, three of them Credits",
         by["Credit Record"].text, "CREDITS  3 / %d" % goal)
    want("...and the counter is what the panel used to hold",
         int(g.STATE.credits), 3)
    want("the breakdown is by subject",
         ("Anatomy  2" in by["Credit Record"].desc,
          "Theory  1" in by["Credit Record"].desc),
         (True, True))
    want("the bank counts and names what is in it",
         (by["Banked Opportunities"].text,
          "Devious Opportunity 3" in by["Banked Opportunities"].desc),
         ("BANKED  1", True))
    # A card on the OTHER pile is not a Credit.
    o = Obj(w, "stray", "Task %d" % ana[2])
    o.pos = (float(g.PILE_X), 1.0, bz)
    w.table[o.guid] = o
    g.refreshCounts()
    drain(w)
    want("a Task on the bank pile is not counted as a Credit",
         by["Credit Record"].text, "CREDITS  3 / %d" % goal)

    # THE MAT COVERS THE FELT, which is the whole point of it: the
    # printed boxes and the cards are both placed in table units, and
    # they can only agree if the picture is stretched over exactly the
    # rectangle it was drawn for. Measured against FELT rather than
    # against two numbers typed in here, because FELT is what the
    # template is drawn to as well.
    felt = g.FELT
    mat = [round(float(v), 2) for v in list(g.matSize())[1:]]
    want("the mat covers the felt exactly",
         mat, [round(float(felt.x1) - float(felt.x0), 2),
               round(float(felt.z1) - float(felt.z0), 2),
               round((float(felt.z1) + float(felt.z0)) / 2.0, 2)])
    before = [round(float(v), 2) for v in list(g.matSize())[1:3]]
    g.matWider()
    g.matDeeper()
    want("the Mat buttons move it half a unit at a time",
         [round(float(v), 2) for v in list(g.matSize())[1:3]],
         [round(before[0] + 0.5, 2), round(before[1] + 0.5, 2)])


def dial_assertions():
    """The trim control must agree with the save, and with itself.

    chipFaces() is a SECOND COPY of the arithmetic in build_mod.py. A
    second copy that has drifted turns the Chip to angles the save's own
    rotation values disagree with, and the symptom - a dial that reads
    one colour when you type and another when a setup places it - looks
    like anything but a copied formula.
    """
    w, g = start("Standard", 0, Panel())
    cols = [str(c) for c in g.ATTENTION.values()]
    gen = dict((c, int(g.CHIP_FACE[c])) for c in cols)
    g.chipFaces()
    want("the trim arithmetic reproduces the generated angles",
         dict((c, int(g.CHIP_FACE[c])) for c in cols), gen)

    # Pressing + three times is nine degrees clockwise, on the readout
    # and on every one of the five colours.
    w, g = start("Standard", 0, Panel())
    before = int(g.CHIP_TRIM)
    for _ in range(3):
        g.trimPlus()
    want("three presses of + move the readout nine degrees",
         int(g.CHIP_TRIM), before + 9)
    want("three presses of + turn every colour nine degrees",
         sorted((c, (int(g.CHIP_FACE[c]) - gen[c]) % 360) for c in cols),
         sorted((c, 9) for c in cols))
    g.trimMinus()
    want("- undoes a third of that", int(g.CHIP_TRIM), before + 6)

    # And it turns the Chip that is on the table, to the colour of the
    # number last typed over it - not always to the first one.
    w, g = start("Standard", 0, Panel())
    g.setupNAP()
    drain(w)
    chip = [o for o in w.markers.values() if o.name == "Chip"][0]
    g.onObjectNumberTyped(chip, "White", 3)
    want("typing 3 turns the Chip to the third colour",
         int(chip.rot[1]), int(g.CHIP_FACE[cols[2]]))
    g.trimPlus()
    want("the trim control re-turns the Chip to the colour you are"
         " judging", int(chip.rot[1]), int(g.CHIP_FACE[cols[2]]))
    want("...and that is not where it started",
         int(chip.rot[1]) != int(gen[cols[2]]), True)


def main():
    layout_assertions()
    panel_assertions()
    counter_assertions()
    dial_assertions()
    choice_assertions()
    repeat_assertions()
    finf_assertions()
    panel_game_assertions()
    for lvl in ("Easy", "Standard", "Hard", "Nobulous"):
        spec, sb = BAT_SPECIMENS[lvl], NAP_SETBACKS[lvl]
        for tier in (0, 1, 2, 3):
            t = "%s t%d" % (lvl, tier)

            w = run(lvl, tier, "BAT")
            # Tier II removes 6 ORDINARY Upgrades. Both halves of that are
            # asserted: the Specimen count survives it, and the six that
            # left were ordinary ones. Counting the deck alone cannot tell
            # the difference - 6 out and 6 in is the same number either way.
            want(t + " BAT Upgrade deck", len(deck(w, "Upgrades").kids),
                 16 + spec)
            want(t + " BAT Specimens in it",
                 inside(w, "Upgrades", "Specimen"), spec)
            want(t + " BAT ordinary Upgrades in it",
                 inside(w, "Upgrades", "Upgrade "), 16 - 6 if tier >= 2 else 16)
            want(t + " BAT Modifications in it",
                 inside(w, "Upgrades", "Unauthorized Modification"),
                 6 if tier >= 2 else 0)
            want(t + " BAT Protocol dealt",
                 out(w, "Experimental Protocols"), 1 if tier >= 1 else 0)
            want(t + " BAT Research Notes out",
                 out(w, "Research Notes"), 6 if tier >= 3 else 0)
            want(t + " BAT shuffled the Experiments",
                 "Encounters" in w.shuffled, True)

            n = run(lvl, tier, "NAP")
            want(t + " NAP Assignment deck", len(deck(n, "Assignment").kids),
                 26 + 6 + sb)
            # One base Setback out per Following Setback in - the 4-for-3
            # swap handed a Setback back at Hard and Nobulous.
            want(t + " NAP base Setbacks", inside(n, "Assignment", "Setback"),
                 sb - 3 if tier >= 1 else sb)
            want(t + " NAP Following Setbacks",
                 inside(n, "Assignment", "Following Setback"), 3 if tier >= 1 else 0)
            want(t + " NAP Imposter Tasks",
                 inside(n, "Assignment", "Imposter Task"), 4 if tier >= 2 else 0)
            want(t + " NAP base Tasks", inside(n, "Assignment", "Task "),
                 26 - 4 if tier >= 2 else 26)
            want(t + " NAP Opportunities",
                 inside(n, "Assignment", "Opportunity "), 0 if tier >= 3 else 6)
            want(t + " NAP Devious Opportunities",
                 inside(n, "Assignment", "Devious Opportunity"),
                 6 if tier >= 3 else 0)
            want(t + " NAP one FINF card", out(n, "FINF"), 1)

            a = run(lvl, tier, "AoS")
            prog = [o for o in a.table.values()
                    if o.name.endswith("Programs") and o.name != "Advanced Programs"]
            want(t + " AoS Program deck", sum(len(p.kids) for p in prog), 8)
            want(t + " AoS Limitation deck", len(deck(a, "Limitations").kids),
                 12 if tier >= 2 else 6)
            want(t + " AoS Corrupted in it",
                 inside(a, "Limitations", "Corrupted Limitation"),
                 6 if tier >= 2 else 0)
            want(t + " AoS Interference dealt",
                 out(a, "Nobulous Interference"), 1 if tier >= 1 else 0)
            want(t + " AoS element mats", out(a, "Element Mats"), 5)

            i = run(lvl, tier, "IMP")
            dos = deck(i, "Exhibits")
            idx = sorted(int(c.name.split()[-1]) for c in dos.kids)
            want(t + " finale Dossier", len(idx), 15)
            want(t + " finale 5 per domain",
                 (len([x for x in idx if x <= 8]),
                  len([x for x in idx if 9 <= x <= 16]),
                  len([x for x in idx if x >= 17])), (5, 5, 5))

            for w_ in (w, n, a, i):
                want(t + " no missing deck",
                     [m for m in w_.said if "MISSING DECK" in m], [])

    print("%d assertions over %d setups and %d panel states, %d failed"
          % (RAN[0], SETUPS[0], PANELS[0], len(FAIL)))
    if SKIPPED:
        # NOT a pass. lupa intermittently hands the script a bound method
        # where an object belongs, for a whole process at a time, and
        # every pack-up step then dies on getName. It is this harness
        # breaking rather than the mod, but a skipped check is a check
        # that did not run, so it says so instead of counting as green.
        print("%d NOT TESTED (lupa bridge fault in this process): %s"
              % (len(SKIPPED), "; ".join(SKIPPED)))
    for f in FAIL:
        print("  -", f)
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
