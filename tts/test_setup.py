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
import hashlib
import io
import heapq
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


def is_card(o):
    """A card or a deck of them - not the overlay, the panel or a die."""
    base = o.name.rstrip("0123456789").strip()
    return LAND.get(base, LAND.get(o.name)) is not None


# Which markers a setup deliberately stands on a card.
ON_CARD = {"BAT": ("Recovery", "Red")}

# READ OUT OF THE LUA, NOT TYPED HERE. These were a hand-copy of
# BAT_DIFF and NAP_DIFF until 2026-11-12, when Standard's Setback count
# went 3 -> 2 and the harness reported the MOD wrong - "got 2, want 3" -
# because the only thing that had changed was the copy going stale. A
# second table of the same numbers is not a check, it is a second thing
# to update.
def _diff_column(name, at):
    src = io.open(os.path.join(HERE, "lua.lua"), encoding="utf-8").read()
    row = re.search(r"^%s = \{(.+?)\}\s*$" % name, src, re.M)
    if not row:
        raise SystemExit("no %s table in lua.lua" % name)
    out = {}
    for lvl, nums in re.findall(r"(\w+) = \{([^}]*)\}", row.group(1)):
        out[lvl] = int(nums.split(",")[at])
    return out


BAT_SPECIMENS = _diff_column("BAT_DIFF", 0)
NAP_SETBACKS = _diff_column("NAP_DIFF", 1)


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
        # A DIE IS A BLOCK; EVERYTHING ELSE HERE LIES FLAT. Set from the
        # save for the dice, so getBounds below can tell the one kind of
        # object that is as tall as it is wide from the cards, the Chip,
        # the Dial and the table overlays, which are all plates.
        self.solid = False
        self.locked = False
        self.TextTool = TextTool(self)
        self.custom = {}
        self.buttons = []
        # The Alt view's angle, which only landscape cards carry.
        self.alt_view_angle = None
        self.dead = False
        # IN A BAG. getObjectFromGUID does not reach inside a container
        # in TTS, and getAllObjects does not list what is in one - so a
        # marker a setup has stowed is gone until something goes and
        # looks for it, which is the whole point of the stowing.
        self.bagged = False

    def getName(self):
        return self.name

    def getGUID(self):
        return self.guid

    def getData(self):
        """The object's save entry - the script reads SidewaysCard off it.

        decks.py says which decks are landscape and build_mod.py writes
        the flag from the same field, so this answers from the source
        both of them use rather than from a copy.
        """
        base = self.name.rstrip("0123456789").strip()
        return self.world.lua.table_from(
            {"SidewaysCard": bool(LAND.get(base, LAND.get(self.name)))})

    # WHICH WAY UP IT IS LYING. FACEDOWN is {0, 180, 180} and FACEUP is
    # {0, 180, 0}, so the z is the whole answer. The stub had no notion
    # of this at all, which meant the Alt-angle code could be called in
    # every test and do nothing in all of them.
    @property
    def is_face_down(self):
        z = (self.rot or (0.0, 0.0, 0.0))[2]
        return 90.0 < (float(z) % 360.0) < 270.0

    def getQuantity(self):
        # TTS answers -1 for a single card, which is why the Lua has its
        # own count() rather than trusting this.
        #
        # A CORPSE ANSWERS A RED LINE AND A CARD. count() is the first
        # thing anything asks of a deck handle, so this is where a
        # script that kept the wrong one gets found out.
        if self.dead:
            self._live("getQuantity")
            return -1
        return len(self.kids) if self.kids else -1

    def getRotation(self):
        # IT ANSWERS WHAT IT WAS TURNED TO. The stub answered zero
        # whatever had happened, so a script asking which way up
        # something is always heard "face up" - and the Chip, which
        # has two faces that are read differently, could not be
        # told apart from itself. setMarker and turnChip read this
        # too, and were reading a constant.
        r = self.rot or (0.0, 0.0, 0.0)
        return self.world.lua.table_from(
            {"x": float(r[0]), "y": float(r[1]), "z": float(r[2])})

    def getPosition(self):
        return self.world.lua.table_from(
            {"x": self.pos[0], "y": self.pos[1], "z": self.pos[2]})

    def getScale(self):
        return self.world.lua.table_from(
            {"x": self.scale[0], "y": self.scale[1], "z": self.scale[2]})

    # How tall a thing is, for getBounds. A die is 0.9 across at scale 1
    # - the figure w.die_half is built from - and a card, a tile and a
    # token are all plates.
    DIE_EDGE = 0.9
    FLAT_THICK = 0.08

    def getBounds(self):
        """The world-space box TTS answers. dropOnto reads this.

        THERE IS NO GRAVITY IN THIS HARNESS. A dealt card keeps the y
        the script let it go at - 3, or 1.2 for the Buff HP card -
        where TTS would have it resting on the felt a unit lower. So
        no height that comes out of here is TTS's height and none of
        them may be read as one.

        What it is good for is the RELATION dropOnto exists to get
        right: a die sent onto a card has to be let go above that
        card's top face rather than at the height of bare felt, and
        that comparison comes out the same way here as it does on the
        table. FLAT_THICK only has to be more than nothing, or a die
        let go at the card's own centre would read as clearing it.
        """
        g = self.world.lua.globals()
        base = self.name.rstrip("0123456789").strip()
        land = LAND.get(base, LAND.get(self.name))
        if self.solid:
            sx = sz = sy = self.DIE_EDGE * float(self.scale[0])
        elif land is not None:
            cw, cl = float(g.CARD_W), float(g.CARD_L)
            sx, sz = (cl, cw) if land else (cw, cl)
            sy = self.FLAT_THICK
        else:
            # A tile or a token: the overlays, the Chip, the Dial, the
            # readout, the panel. Square at twice its scale, which is
            # what TTS's unit tile measures, and flat.
            sx = sz = 2.0 * float(self.scale[0])
            sy = self.FLAT_THICK
        return self.world.lua.table_from(
            {"center": self.world.lua.table_from(
                {"x": self.pos[0], "y": self.pos[1], "z": self.pos[2]}),
             "size": self.world.lua.table_from(
                {"x": sx, "y": sy, "z": sz})})

    def setScale(self, s):
        self.scale = tuple(s.values()) if hasattr(s, "values") else tuple(s)

    @property
    def type(self):
        """What TTS calls this: the thing you ask BEFORE getObjects.

        EVERY LEAF HERE IS A "Card", the overlay and the counters
        included, where TTS would answer Tile and 3D Text. That is
        harsher than the real thing and it stays that way: a second
        `type` was added above this one that told them apart, Python
        kept the LAST definition in the class body, and the finale
        sweep - written against the kinder one - bagged the NAP
        overlay. Nothing in lua.lua may decide what an object is from
        this string alone; isGameCard() asks DECK_OF instead.
        """
        if self.bag:
            return "Bag"
        return "Deck" if self.kids else "Card"

    def getObjects(self):
        # IT LOGS AND HANDS BACK NOTHING, the way TTS does - it does not
        # raise. That is the whole trap: `o.getObjects and
        # o.getObjects()` is not a guard, because the method exists on
        # every object and only the call is wrong; and pcall around it
        # buys nothing either, because what you are trying to avoid is
        # a message, not an error. Jon's chat filled with one red line
        # per die on every load, twice, through both of those.
        #
        # The stub used to answer an empty list here and say nothing,
        # which is what let the bad call look fine for months.
        if self.type not in ("Bag", "Deck", "Infinite"):
            self.world.errors.append(
                "[%s] Lua Error <getObjects>: Attempting to call"
                " getObjects() on an object that does not support"
                " getObjects()" % self.name)
            return self.world.lua.table_from([])
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

    def setName(self, n):
        self.name = n

    # ---------------------------------------------- the rulebook's corner
    # A Custom_PDF carries the URL it is showing, takes buttons the way
    # the panel does, and RESPAWNS when reloaded. The last of those is
    # the trap: reload destroys the object and hands back a new one, so
    # a script that keeps its old reference is holding a corpse and
    # every call on it is a red line in Jon's chat. The stub had none of
    # this - getObjectFromGUID answered nil for the Rulebook, showRules
    # returned on its first line, and nothing about the rules in the
    # corner was ever exercised.
    def setCustomObject(self, spec):
        self._live("setCustomObject")
        self.custom = dict(spec.items()) if hasattr(spec, "items") else dict(spec)

    def reload(self):
        self._live("reload")
        fresh = Obj(self.world, self.guid, self.name)
        fresh.pos, fresh.rot, fresh.locked = self.pos, self.rot, self.locked
        fresh.custom = dict(self.custom)
        self.dead = True
        self.world.byguid[self.guid] = fresh
        if self.world.table.get(self.guid) is self:
            self.world.table[self.guid] = fresh
        return fresh

    def clearButtons(self):
        self._live("clearButtons")
        self.buttons = []

    def createButton(self, spec):
        self._live("createButton")
        self.buttons.append(
            dict(spec.items()) if hasattr(spec, "items") else dict(spec))

    def _live(self, call):
        """TTS logs and carries on when you touch a destroyed object."""
        if self.dead:
            self.world.errors.append(
                "[%s] Lua Error <%s>: object has been destroyed"
                % (self.name, call))

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
        if self.dead:
            self._live("takeObject")
            return None
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
        k.bagged = False
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
            # DEALT ONTO SOMETHING THAT IS ALREADY THERE. A card
            # dropped on a deck joins it, so a deck parked on the point
            # every takeObject drops at eats whatever passes through -
            # which is what OFF being pad(3) did to AoS: a correct
            # 8-card Program deck, and five of its own cards left lying
            # in the staging band beside it.
            #
            # Measured rather than named: this fails for any pair of
            # places that overlap, not just for the pair that was wrong.
            self.world.land(k)
        # AND THE ROTATION IT WAS ASKED FOR. The stub threw this away,
        # which is exactly the thing that went wrong at the table: a
        # deck whose contained cards carried their own rotation handed
        # every drawn Assignment back upside down, and nothing here
        # could see it. A card drawn with a rotation has that rotation.
        if "rotation" in keys:
            k.setRotation(spec["rotation"])
        # A MARKER TAKEN BACK OUT OF A BAG IS A MARKER AGAIN, not a
        # dealt card. w.table is what a setup has put out and what
        # Pack up has to clear; the dice and the two faces live in
        # their own index and are never in both.
        if k.guid not in self.world.markers:
            self.world.table[k.guid] = k
        if "callback_function" in keys and spec["callback_function"] is not None:
            spec["callback_function"](k)
        return k

    def putObject(self, other):
        if other is None:
            raise RuntimeError("putObject(nil) into %r" % self.name)
        # ONE CONTAINER REFUSING A RUN OF PUTS, which one-in-N cannot
        # express. gatherInto's last resort is the bag: after eight
        # refusals it stops asking and files the card instead, and
        # reaching that needs ONE deck to refuse eight times running
        # while the bag that takes the card still works. Turning
        # `lossy` down to 1 refuses the bag's puts too, so putHome
        # achieves nothing there and dropping it changed no assertion
        # at all - measured 2026-11-12, which is why this exists.
        jam = self.world.jam.get(self.name)
        if jam:
            self.world.jam[self.name] = jam - 1
            return other
        # A DESTROYED RECEIVER TAKES NOTHING. Without this the corpse a
        # card-to-card put leaves behind builds a SECOND deck out of
        # the next card handed to it, which is a card quietly leaving
        # the deal and no red line to say so.
        if self.dead:
            self._live("putObject")
            return other
        if self.world.lossy:
            # TTS DROPS OBJECTS FED TO A CONTAINER FASTER THAN IT ANIMATES
            # THEM. One pass of pack-up over twenty cards left exactly one
            # on the table every time, and the stub could not see it
            # because a Python list never refuses an append. Refusing one
            # in N reproduces the bug, so the fix for it stays tested.
            #
            # A DECK REFUSES TOO, AND ONE DIAL SAYS SO FOR BOTH. This had
            # a second dial for a day, lossy_decks, off by default,
            # because turning deck refusal on for the whole suite failed
            # nine assertions beyond the one it was added for. Every one
            # of those nine was the same mod bug wearing a different
            # hat - gatherInto made exactly ONE attempt when the receiver
            # was a single card, and moveN and merge made one at
            # anything - so the dial was measuring the fix's absence and
            # calling it a different question. The nine were:
            #
            #   NAP/BAT/AoS t0 and t3 dealt a different table on the
            #   second setup (29-card Assignment deck, one Time Slot of
            #   three, Specimens and Programs left in the band);
            #   AoS lost Element Mats until spread() took from an empty
            #   deck; FINF Increase 3 hid one or two cards of the three;
            #   and a pile of four came back three.
            #
            # With the fix in they pass with refusal on, so there is one
            # dial again and a deck is as lossy as a bag. See
            # gather_assertions and lua.lua's gatherInto.
            self.world.puts += 1
            if self.world.puts % self.world.lossy == 0:
                return other
        self.world.table.pop(other.guid, None)
        other.bagged = True
        into = self
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
            # ...AND THE RECEIVER IS DESTROYED BY IT. This is the half
            # the stub kept getting wrong in the caller's favour: it
            # turned THIS object into the new deck, so the handle the
            # script was holding went on working, and every line of
            # lua.lua written to follow the deck instead was untestable
            # here. Measured 2026-11-12, with the lenient stub put back
            # and one line of the fix dropped at a time: deckOut's two
            # gather loops losing the reassignment, and liveDeck losing
            # the look inside decks, all three passed 0 failed. Against
            # this version the same three fail 12, 8 and 22.
            #
            # TTS respawns the card inside the deck under its own GUID
            # and leaves the old reference a corpse, so that is what
            # happens here: a fresh object carries the card into the
            # deck, another is the deck, and this one is marked dead.
            was, nick = self.guid, self.name
            # ...AND IT HAS NO NAME. A deck TTS builds for you out of
            # loose cards carries no nickname at all - the cards keep
            # theirs inside it - and the stub gave the container the
            # first card's name, which made every gathered deck look
            # like something homeBox could place. It cannot: putHome
            # read "" , found no bag for it and quietly did nothing, so
            # the three unused Setbacks stayed in the staging band at
            # dead centre of the bottom edge, face down and wearing the
            # Assignment back.
            into = Obj(self.world, was + "#deck", "")
            into.pos, into.rot = self.pos, self.rot
            inner = Obj(self.world, was, nick)
            inner.pos, inner.rot = self.pos, self.rot
            if self.world.table.get(was) is self:
                del self.world.table[was]
            self.world.table[into.guid] = into
            self.world.byguid[into.guid] = into
            self.world.byguid[was] = inner
            into.kids.append(inner)
            self.dead = True
        if other.kids and not into.bag:
            into.kids.extend(other.kids)     # deck into deck merges, as TTS does
            other.kids = []
        else:
            into.kids.append(other)
        return other


class World(object):
    def __init__(self, lua):
        self.lua = lua
        self.byguid = {}
        self.table = {}        # guid -> object currently out on the table
        self.said = []
        # What TTS would have printed in red. Not exceptions: TTS logs
        # a bad API call and carries on, so nothing fails on its own.
        self.errors = []
        self.shuffled = set()
        self.markers = {}      # the dice and the Chip, by GUID
        # A HEAP OF (due frame, order, fn), NOT A LIST. drain() runs
        # them in time order, so a callback that asked for 6 frames
        # really does run before one that asked for 10 - see install().
        self.pending = []
        self.frame = 0          # frames since this world was built
        self.waits = 0          # tie-break, so two due together keep order
        self.snaps = []         # Assignment spaces laid by a setup
        # Every time a card was dealt onto something already standing
        # there. A card dropped on a deck joins it, so a deck parked
        # where cards are dropped eats them.
        self.landings = []
        self.card_half = 0.0
        # Refuse one container put in N - bag or deck alike, like TTS
        # does. ONE DIAL FOR BOTH: see putObject for the day there were
        # two of them and why there is not any more.
        self.lossy = 0
        self.puts = 0
        # Container name -> puts it still has to refuse. See putObject:
        # the limit case one-in-N cannot reach.
        self.jam = {}
        self.rng = random.Random(7)

    @property
    def dice(self):
        """Where the dice are NOW. A card dealt on top of one is a card
        dealt on top of one wherever the setup has just moved it to -
        and a marker a setup has stowed in a bag is not on the table
        at all, so nothing can be dealt onto it."""
        return [(o.pos[0], o.pos[2]) for o in self.markers.values()
                if not o.bagged]

    def land(self, k):
        """Record a card dealt on top of something already standing there.

        Two cards at the same point are one pile in TTS. The setups
        rely on that nowhere; every place they deal to is meant to be
        clear when the card arrives.
        """
        h = self.card_half
        # CARDS ONLY. The thing everything is dealt onto is the table
        # overlay, a 56-unit tile that is meant to be underneath.
        if not h or not is_card(k):
            return
        for o in self.table.values():
            if o is k or o.guid == k.guid or not is_card(o):
                continue
            if (abs(o.pos[0] - k.pos[0]) < h and abs(o.pos[2] - k.pos[2]) < h):
                self.landings.append((k.name, o.name,
                                      round(k.pos[0], 2), round(k.pos[2], 2)))

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
            # NOT EVERYTHING IN A BOX IS A DECK. Three of the four
            # rulebooks wait in theirs, and a Custom_PDF has no cards
            # inside it - inventing one gave the NAP box a card called
            # "NAP Rules 1" that nothing could ever put anywhere.
            if d["Name"] not in ("Deck", "DeckCustom", "Card", "CardCustom"):
                leaf = Obj(w, d["GUID"], d["Nickname"])
                tr = d.get("Transform") or {}
                leaf.scale = (tr.get("scaleX", 1.0), tr.get("scaleY", 1.0),
                              tr.get("scaleZ", 1.0))
                if "CustomPDF" in d:
                    leaf.custom = dict(d["CustomPDF"])
                decks.append(w.add(leaf))
                continue
            cards = []
            for c in (d.get("ContainedObjects") or []):
                kid = Obj(w, gid(), c["Nickname"])
                # THE ANGLE IS IN THE SAVE, not set by a script at
                # load - so a card that is never turned over has to
                # start out holding it, or a check that the right one
                # is on the right card can only ever see the ones the
                # script has touched.
                kid.alt_view_angle = c.get("AltLookAngle")
                cards.append(kid)
            if not cards:                       # a one-card "deck"
                cards = [Obj(w, gid(), d["Nickname"] + " 1")]
                cards[0].alt_view_angle = d.get("AltLookAngle")
            one = Obj(w, d["GUID"], d["Nickname"], cards)
            one.alt_view_angle = d.get("AltLookAngle")
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
    # THE MARKERS ARE THE LOOSE THINGS A SETUP MOVES: the dice, and
    # the Chip. The Chip became a Custom_Tile the day it was given
    # a second face - a token carries only one image - so the type
    # is no longer what identifies it. Anything on the table that
    # is not a bag is one of these.
    # THE BOOK IN THE CORNER IS AN OBJECT TOO. It was not in this world
    # at all, so getObjectFromGUID answered nil for it, showRules
    # returned on its first line, and every run of this harness tested
    # a rulebook that was not there.
    # THE BOOK ON THE RAIL IS ON THE TABLE. The other three are in
    # their boxes and were added by the loop above; this is the one
    # the save stands out, which is what a fresh load shows.
    for o in save["ObjectStates"]:
        if o["Name"] == "Custom_PDF":
            b = Obj(w, o["GUID"], o.get("Nickname") or "Rulebook")
            b.custom = dict(o["CustomPDF"])
            b.pos = (o["Transform"]["posX"], o["Transform"]["posY"],
                     o["Transform"]["posZ"])
            b.locked = bool(o.get("Locked"))
            w.byguid[o["GUID"]] = b
            w.table[o["GUID"]] = b
    for o in save["ObjectStates"]:
        if o["Name"] in ("Custom_Dice", "Custom_Token") or (
                o.get("Nickname") in ("Chip",)):
            m = Obj(w, o["GUID"], o["Nickname"])
            m.pos = (o["Transform"]["posX"], o["Transform"]["posY"],
                     o["Transform"]["posZ"])
            # ITS REAL SCALE, AND WHETHER IT IS A BLOCK. getBounds
            # needs both: the dice are the only things on this table
            # that are as tall as they are wide, and how tall decides
            # how high a die standing on a card has to be let go.
            m.scale = (o["Transform"].get("scaleX", 1.0),
                       o["Transform"].get("scaleY", 1.0),
                       o["Transform"].get("scaleZ", 1.0))
            m.solid = o["Name"] == "Custom_Dice"
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
    def by_guid(guid):
        o = w.byguid.get(guid)
        return None if (o is not None and o.bagged) else o
    g.getObjectFromGUID = by_guid
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
            if isinstance(o, Obj) and not o.bagged:
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
    #
    # AND THE DELAY IS NOT DECORATION. This used to append to a plain
    # list, so every callback ran in the order it was CREATED and the
    # number of frames it asked for was discarded - which makes the
    # harness model one interleaving out of many, and not the one TTS
    # produces. A putHome retry asking for 6 frames, created before a
    # finfApply step asking for 10, ran BEFORE that step here and AFTER
    # it at the table.
    #
    # Both of the bugs Jon reported on 2026-11-12 are orderings of a
    # retry against a deal, so a model with no clock in it is a model
    # that cannot fail on either. One of them it did not: the FINF
    # cycle was green through the whole thing.
    def later(fn, n):
        w.waits += 1
        heapq.heappush(w.pending, (w.frame + max(0, int(n)), w.waits, fn))
    wait = lua.eval("{}")
    wait.frames = lambda fn, n=1: later(fn, n or 1)
    # Seconds, at the 60 fps TTS runs its own waits against.
    wait.time = lambda fn, t=0: later(fn, round(float(t or 0) * 60))
    g.Wait = wait
    # VECTOR, TAGGED. Every published example of alt_view_angle uses
    # Vector() and the plain {x, y, z} table is reported to error from
    # the console, so which of the two the script reaches for is worth
    # asserting rather than hoping. The tag is how a test can tell -
    # the fallback table does not carry it.
    g.Vector = lambda x, y, z: lua.table_from(
        {"x": float(x), "y": float(y), "z": float(z), "vector": True})
    # Player.Action.FlipOver, which is what F is. onObjectRotate is
    # documented for deliberate rotations and did not cover Jon's
    # flip, so the action event is one of the three ways in.
    g.Player = lua.eval("{Action = {FlipOver = 'FlipOver'}}")
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
                             "font": spec["font_size"],
                             "fn": spec["click_function"]})

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
    # HOW WIDE A CARD IS, from the Lua the build generated, so the
    # "dealt onto something" check measures the card this mod deals
    # rather than a number written down here.
    w.card_half = float(g.CARD_W) * 0.9
    if panel is not None:
        g.PANEL = panel
    g.STATE.difficulty = difficulty
    g.STATE.tier = tier
    return w, g


def drain(w):
    """Run every queued Wait callback to completion, in time order.

    The clock only ever moves forward, and it moves to whatever is due
    next rather than a frame at a time: nothing in the mod polls, so a
    frame with no callback in it is a frame with nothing to model.
    """
    for _ in range(20000):
        if not w.pending:
            return
        due, _, fn = heapq.heappop(w.pending)
        w.frame = max(w.frame, due)
        fn()
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
                # A BAD API CALL IS NOT AN ERROR IN TTS. It prints a
                # red line in the chat, attributed to the object, and
                # carries on - so nothing fails, nothing throws, and
                # the only symptom is a wall of red and a load that
                # takes its time. Jon saw one line per die, twice,
                # through two different attempts at a guard.
                want(t + " printed nothing in red",
                     w.errors[:2], [])
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
                # MARKERS THAT ARE MEANT TO BE ON A CARD are not part
                # of the pool this is about. BAT's setup puts the
                # Recovery die on the active Rat's corner and the Red
                # die on whichever Rat drew it, which is a marking,
                # not a die left lying where a card was dealt.
                pool = [(o.pos[0], o.pos[2]) for o in w.markers.values()
                        if o.name not in ON_CARD.get(which, ())]
                on_dice = [f[0] for f in fp
                           for dx, dz in pool
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

                def _piled(pts):
                    pts = sorted(set(pts))
                    return [(a, b2) for i, a in enumerate(pts)
                            for b2 in pts[i + 1:]
                            if abs(a[0] - b2[0]) < 2 * w.die_half - 0.02
                            and abs(a[1] - b2[1]) < 2 * w.die_half - 0.02]
                # EACH LAYOUT AGAINST ITSELF, not the two mixed. This
                # unioned where the dice ARE with where they LIVE, and
                # a setup that moves a marker off its home slot was
                # then compared against the empty slot it had just
                # left: BAT standing its Health and REC dice beside
                # the exhausted corner reported them piled on
                # Recovery's own vacant home, 1.2 away. Nothing is
                # ever at both at once. Checked separately, the live
                # table still cannot pile two dice and the idle
                # layout still cannot overlap two homes.
                piled = _piled(w.dice) + _piled(home)
                want(t + " no two dice sit on each other", piled[:2], [])
                # THE UNION IS RIGHT HERE, where it was wrong above:
                # every point is tested on its own, so a live
                # position and an idle home can be asked the same
                # question without being compared to each other.
                off = [p for p in sorted(set(w.dice) | set(home))
                       if abs(p[0]) + w.die_half > FELT_X
                       or p[1] - w.die_half < FELT_ZMIN - 0.6]
                want(t + " no die hangs off the felt", off[:2], [])
                # Four Assignment spaces beside every Time Slot, and
                # only for the game that has Time Slots.
                slots = [o.pos[2] for o in w.table.values()
                         if o.name.startswith("Time Slot")]
                # 4 beside every Time Slot, 2 for the cards the deck
                # reveals and 1 for the one you did not take, the
                # Apprentice in its corner, the FINF cards at the head
                # of the right-hand column, and the two piles under
                # them. The bank is not conditional on the tier any
                # more: the mat prints its box at every tier, so the
                # space has to be there too.
                if which == "NAP":
                    # ...plus the Chip's circle beside each Time Slot.
                    exp = 4 * len(slots) + len(slots) + 2 + 1 + 1 + 1 + 2
                elif which == "BAT":
                    # Twelve Upgrade spaces beside the Rats, three
                    # revealed, the Tyrant's three, the Splices; then
                    # the places with no box of their own - a Rat, its
                    # active-Rat mark, the opposite corner the Red die
                    # marks and its row of dice on each row, the two
                    # decks, and one per cell of the Buff HP track.
                    rows, ups = int(g.BAT_ROWS), int(g.BAT_UPGRADES)
                    cols = len(list(g.BAT_RAT_DICE.values()))
                    exp = (rows * ups + 2 + 3 + 2 + 3 + 1
                           + int(g.BAT_SPLICES) + (3 + cols) * rows + 2
                           + len(list(g.BUFF_CELL.values())))
                elif which == "AoS":
                    # The Technician, the two decks and the two
                    # cards they reveal, the Advanced Programs and
                    # whatever a tier lays face-up beside them; the
                    # five element mats; and along the bottom the
                    # Programs finished with, the six Backdoor
                    # Routines and the banished dice.
                    exp = (1 + 4 + 1 + 2 + int(g.AOS_MATS)
                           + 1 + int(g.AOS_BACKDOORS) + 1)
                else:
                    exp = 0
                want(t + " spaces laid", len(w.snaps), exp)
                if which == "NAP":
                    for sz in slots:
                        # The Assignment columns only: the discard and
                        # bank piles share a row with a Time Slot but
                        # are off to the right, past x 20.
                        want(t + " four spaces beside the slot at %.1f" % sz,
                             len([s for s in w.snaps
                                  if abs(s[1] - sz) < 0.05
                                  and s[0] < 20.0
                                  and s[0] > float(g.CHIP_X) + 0.5]), 4)
                        want(t + " and the Chip's circle at %.1f" % sz,
                             len([s for s in w.snaps
                                  if abs(s[1] - sz) < 0.05
                                  and abs(s[0] - float(g.CHIP_X)) < 0.05]), 1)
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
                # EVERYTHING ON THE MAT IS A THING YOU PRESS. One row
                # was a pale strip reading "set up NAP, AoS or Imposter
                # to choose a character", drawn with click_function
                # 'nop' so that a press did nothing - in a row where
                # every other state of the panel puts a button. A row
                # you cannot press is a row players press. Checked in
                # all eighty states, because the label only appeared in
                # the ones with no character to cycle.
                want(t + " every row is pressable",
                     [b["label"] for b in pan.buttons
                      if b["fn"] in (None, "", "nop")], [])

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

    # EVERY SETUP LEAVES ONE CHARACTER OUT, not a stack to choose
    # from. The panel's character button picks the card AND the side,
    # so the setup deals the one it names and sends the rest back.
    # Keep 1/2/3 used to stand beside that button for AoS and the
    # Imposter scenario and is gone: two ways to choose that know
    # nothing about each other left the panel naming a character
    # nobody had picked, which is why NAP dropped it first.
    for which, deck, n in (("NAP", "Apprentices", 1),
                           ("AoS", "Technicians", 1),
                           ("IMP", "Imposters (A / B)", 1)):
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
        # THE RULEBOOK IS NOT CLEARED AWAY. It has a box, because
        # showRules puts the three a game does not want back in
        # theirs, but taking the rules off the table at the end of a
        # game is not tidying up, it is confiscating them.
        want("pack up emptied the table, dropping 1 in %d" % lossy,
             (dealt > 0,
              sorted(o.name for o in w.table.values()
                     if not o.name.endswith(" Rules")))[1], [])
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
                if k.guid not in w.markers:
                    walk(k)        # a stowed Chip is not a card
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
    z, x = float(g.OFF_Z), float(g.OFF_X)
    return sorted(o.name for o in w.table.values()
                  if abs(o.pos[2] - z) < 2.5 and abs(o.pos[0]) < x
                  and g.homeBox(o.name) is not None)


def buried(w):
    """Nameless decks sitting inside a box.

    A BOX CANNOT SEE INSIDE A DECK IT HOLDS. findDeck matches a
    nickname and the gather loop reads the box's top level, so a deck
    with no name in there is cards nobody can get back - the next setup
    deals without them and says nothing. Getting the deck INTO the box
    is not enough; it has to be able to come out again.
    """
    out = []
    for b in w.byguid.values():
        if b.bag:
            out += ["%s(%d)" % (k.name or "<unnamed deck>", len(k.kids))
                    for k in b.kids if k.kids and not k.name]
    return sorted(out)


def nameless(w):
    """Decks on the table that nothing can put away.

    A DECK TTS BUILDS FOR YOU HAS NO NICKNAME. Gathering a deck out of
    loose cards makes one of these, and homeBox has nothing to look
    up - so putHome read "", found no bag and quietly did nothing,
    however many times it tried. in_staging could not see it either,
    because it only looks at objects that HAVE a home: the one object
    that cannot go home was the one it skipped.
    """
    return sorted("%s(%d)" % (o.name or "<unnamed deck>", len(o.kids) or 1)
                  for o in w.table.values() if not o.name)


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
                seen.append((census(w), shape(w, g), in_staging(w, g),
                             nameless(w), buried(w)))
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
            want(t + " leaves no deck on the table that nothing can stow",
                 [s[3] for s in seen], [[], [], []])
            want(t + " puts nothing in the box it cannot get back",
                 [s[4] for s in seen], [[], [], []])
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
        # AND NOTHING IS LEFT BEHIND BY THE CHANGE. Increase 3
        # puts all three cards into the Assignment deck, which
        # consumes the FINF deck object itself - so the next
        # setting has to build one out of loose cards, and a deck
        # TTS builds for you has no name to go home by.
        want("cycling the setting strands nothing (1 in %s)"
             % (lossy or "none"),
             (nameless(w), in_staging(w, g)), ([], []))


def round_trip_assertions():
    """Cycle the FINF setting, pack up, set up again.

    THE BAG CANNOT SEE INSIDE A NAMELESS DECK. Increase 3 puts all three
    FINF cards into the Assignment deck, which consumes the FINF deck
    object itself, so the next setting has to build one out of loose
    cards - and the deck TTS builds for you has no nickname. boxFor
    gets that deck into the box by asking what is inside it, but
    findDeck matches a nickname and the gather loop reads the box's top
    level, so a nameless deck in there is a deck nobody can find again:
    the next setup says MISSING DECK and deals without it.
    """
    for lossy in (0, 3):
        w, g = start("Standard", 0, Panel())
        w.lossy = lossy
        g.setupNAP()
        drain(w)
        for _ in range(len(list(g.FINF_SET.values()))):
            g.btnFinf()
            drain(w)
        g.btnPack()
        drain(w)
        g.setupNAP()
        drain(w)
        t = "cycling FINF, packing up and setting up again (1 in %s)" % (
            lossy or "none")
        want(t + " finds every deck",
             [m for m in w.said if "MISSING" in m][:2], [])
        want(t + " strands nothing",
             (nameless(w), in_staging(w, g)), ([], []))
        want(t + " buries nothing in the box", buried(w), [])
        want(t + " prints nothing in red", w.errors[:2], [])
        want(t + " still deals three Time Slots",
             sum(1 for o in w.table.values()
                 if o.name.startswith("Time Slot")), 3)
        want(t + " still has all three FINF cards",
             sorted(k for k, v in census(w).items()
                    if k.startswith("FINF") and v != 1), [])


def in_the_bag_assertions():
    """Decks a setup leaves alone on purpose.

    IN_THE_BAG IS A DECLARATION, and the only thing that makes "every
    deck is dealt by a setup" a real check rather than one that quietly
    stops covering a deck. So it has to be true: what it names must
    still be in its box after the setup that could have dealt it, and
    what it does NOT name must not be sitting there forgotten.
    """
    bagged = sorted(str(v) for v in g_in_the_bag())
    want("four decks are declared as staying in the bag", bagged,
         ["Advanced Programs", "Buff HP Track", "Final Exams",
          "Tyrant Attacks"])
    for which, tier in (("BAT", 0), ("BAT", 3), ("NAP", 0), ("NAP", 3),
                        ("AoS", 0), ("AoS", 3)):
        w, g = start("Standard", tier, Panel())
        {"BAT": g.setupBAT, "NAP": g.setupNAP, "AoS": g.setupAoS}[which]()
        drain(w)
        out = sorted(n for n in bagged if out_count(w, n))
        want("%s t%d deals none of them" % (which, tier), out, [])
        still = sorted(n for n in bagged
                       for b in w.byguid.values() if b.bag
                       for k in b.kids if k.name == n)
        want("%s t%d leaves all three in their boxes" % (which, tier),
             still, bagged)


def out_count(w, label):
    return sum(1 for o in w.table.values() if o.name == label)


def g_in_the_bag():
    w, g = start("Standard", 0, Panel())
    return list(g.IN_THE_BAG.values())


def overlay_assertions():
    """Every game lays its own felt, and only its own.

    Each overlay is a tile in that game's bag, which is what lets
    them be four different pictures - turquoise, gold, green,
    magenta. The Imposter scenario's lives in the NRJ bag with the
    rest of its cards.
    """
    mats = ["NAP Table", "BAT Table", "AoS Table", "IMP Table"]
    for which, mine in (("NAP", "NAP Table"), ("BAT", "BAT Table"),
                        ("AoS", "AoS Table"), ("IMP", "IMP Table")):
        w, g = start("Standard", 3, Panel())
        w.lossy = 3
        {"NAP": g.setupNAP, "BAT": g.setupBAT,
         "AoS": g.setupAoS, "IMP": g.setupImposter}[which]()
        drain(w)
        out = dict((o.name, o) for o in w.table.values())
        want("%s lays its own overlay" % which,
             sorted(n for n in out if n in mats), [mine])
        want("...and locks it so it cannot be dragged",
             out[mine].locked if mine in out else None, True)
        # AND PACKS IT AWAY AGAIN, into the bag it came out of.
        g.btnPack()
        drain(w)
        want("...and packs it away again" % (),
             [n for n in (o.name for o in w.table.values()) if n in mats],
             [])


def bat_assertions():
    """The BAT table Jon laid out, squared up.

    THE GRID IS THE CLAIM, not the card positions: a space on the felt
    is drawn from batBoxes() and a snap point is made from the same
    list, so what has to be checked is that the grid itself holds
    together - rows that line up with the Rats, spaces that do not
    overlap each other or run off the felt, and the things that sit
    outside it.
    """
    w, g = start("Standard", 0, Panel())
    w.lossy = 3
    g.setupBAT()
    drain(w)
    by = dict((o.name, o) for o in w.table.values())
    cw, cl = float(g.CARD_W) / 2, float(g.CARD_L) / 2

    # The four Rats are a column down the left, in order, top to bottom.
    rats = sorted([o for o in w.table.values() if o.name.startswith("Lab Rat")],
                  key=lambda o: -o.pos[2])
    want("BAT deals four Lab Rats in a column",
         [round(o.pos[0], 2) for o in rats],
         [round(float(g.BAT_RAT_X), 2)] * 4)
    want("...one to a row, in the script's order",
         [round(o.pos[2], 2) for o in rats],
         [round(float(g.batRatZ(i)), 2) for i in range(1, 5)])

    # EACH RAT'S THREE UPGRADE SPACES SHARE ITS TOP EDGE. That is the
    # thing Jon asked for by eye and the one relation a pitch change
    # could quietly break.
    bad = []
    for r in range(1, 5):
        top = float(g.batRatZ(r)) + cw
        for k in range(1, 4):
            if abs((float(g.batRowZ(r)) + cl) - top) > 0.01:
                bad.append((r, k))
    want("every Upgrade space is level with its Rat's top edge", bad, [])

    # The spaces are a grid: none overlaps another, none leaves the felt.
    boxes = [(float(b.x), float(b.z), float(b.hw), float(b.hd))
             for b in g.batBoxes().values()]
    # Twelve beside the Rats; the Protocol and the Research Notes on
    # the deck row; three revealed and two discards; the Tyrant's
    # three and its dice tray; the five Splices.
    want("BAT draws a space for every card you put down", len(boxes),
         int(g.BAT_ROWS) * int(g.BAT_UPGRADES) + 2 + 3 + 2 + 3 + 1
         + int(g.BAT_SPLICES))
    over = [(a, b) for i, a in enumerate(boxes) for b in boxes[i + 1:]
            if abs(a[0] - b[0]) < a[2] + b[2] - 0.02
            and abs(a[1] - b[1]) < a[3] + b[3] - 0.02]
    want("no two spaces overlap", over[:2], [])
    felt = g.FELT
    off = [b for b in boxes
           if b[0] - b[2] < float(felt.x0) or b[0] + b[2] > float(felt.x1)
           or b[1] - b[3] < float(felt.z0) or b[1] + b[3] > float(felt.z1)]
    want("no space runs off the felt", off[:2], [])

    # A CARD OVERHANGS ITS SPACE, which is what the pitch buys: the
    # grid is a shade under a card wide, the way NAP's is.
    want("a card is wider than the space it sits in",
         (round(cw * 2, 2) > round(float(g.BAT_BOX_HW) * 2, 2),
          round(cl * 2, 2) > round(float(g.BAT_BOX_HD) * 2, 2)),
         (True, True))

    # The Rats and the two decks get no box - Jon asked for none - but
    # they do get somewhere to drop onto.
    def snapped(x, z):
        return any(abs(s[0] - x) < 0.05 and abs(s[1] - z) < 0.05
                   for s in w.snaps)
    want("a Rat has a snap point and no box",
         ([snapped(float(g.BAT_RAT_X), float(g.batRatZ(r)))
           for r in range(1, 5)],
          [b for b in boxes if abs(b[0] - float(g.BAT_RAT_X)) < 0.05]),
         ([True] * 4, []))
    # THE TWO DECK COLUMNS ONLY. Row 1 also carries the three Upgrade
    # spaces beside the top Rat, a long way to the left; and, to the
    # right of the decks, the Protocol, the Research Notes and the
    # banished dice, all three of which DO have boxes.
    want("so do the two decks",
         ([snapped(float(g.batRightX(k)), float(g.batRowZ(1)))
           for k in (1, 2)],
          [b for b in boxes if abs(b[1] - float(g.batRowZ(1))) < 0.05
           and abs(b[0] - float(g.batRightX(1))) < 0.05
           or abs(b[1] - float(g.batRowZ(1))) < 0.05
           and abs(b[0] - float(g.batRightX(2))) < 0.05]),
         ([True, True], []))

    # The banished-dice corner is clear of everything the grid draws.
    bq = [float(v) for v in g.batBanished().values()]
    want("the banished-dice corner is in the top right",
         (bq[1] <= float(felt.x1), bq[2] <= float(felt.z1),
          bq[0] > float(g.BAT_RIGHT1)),
         (True, True, True))
    # ONE SPACE, THE SAME SIZE AS EVERY OTHER. It began as a wide
    # corner like the exhausted-dice one; Jon asked for a card.
    want("...and is one space, the size of all the others",
         (round((bq[1] - bq[0]) / 2, 3), round((bq[2] - bq[3]) / 2, 3)),
         (round(float(g.BAT_BOX_HW), 3), round(float(g.BAT_BOX_HD), 3)))
    want("...and nothing else is drawn inside it",
         [b for b in boxes
          if b[0] + b[2] > bq[0] and b[1] - b[3] < bq[2]
          and b[1] + b[3] > bq[3]][:2], [])

    # The active-Rat mark sits ON its Rat, near the top right corner.
    marks = []
    for r in range(1, 5):
        mx = float(g.BAT_RAT_X) + cl - float(g.BAT_MARK_IN)
        mz = float(g.batRatZ(r)) + cw - float(g.BAT_MARK_IN)
        marks.append(snapped(mx, mz)
                     and mx < float(g.BAT_RAT_X) + cl
                     and mz < float(g.batRatZ(r)) + cw)
    want("each Rat has a mark on it for being the active one",
         marks, [True] * 4)

    # AND IT IS THE RECOVERY DIE ON IT. This asked only whether the
    # corner was a snap point, so the setup could have put any die
    # there - and it has put two different wrong ones, the Health die
    # and then the Strategy die, against the three statements in
    # rules/bat.html that name the marker. A snap point is a place;
    # this is what is on it. Jon's call, 2026-11-12: Recovery.
    mx, mz = float(g.batMarkX()), float(g.batMarkZ(1))
    on_top = sorted(o.name for o in w.markers.values()
                    if abs(o.pos[0] - mx) < 0.05 and abs(o.pos[2] - mz) < 0.05)
    want("...and the Recovery die is the one on the top Rat", on_top,
         ["Recovery"])
    # The Health die has no job in BAT at all: the Tyrant's Health is
    # the dial, and a Rat's is written on its card.
    rat_z = [float(g.batRatZ(r)) for r in range(1, 5)]
    want("...and no Health die is sitting on any Rat",
         [(round(o.pos[0], 2), round(o.pos[2], 2))
          for o in w.markers.values() if o.name == "Health"
          and abs(o.pos[0] - float(g.BAT_RAT_X)) < cl
          and any(abs(o.pos[2] - z) < cw for z in rat_z)], [])

    # A ROW OF FOUR DICE UNDER EVERY RAT, which the setup message asked
    # the players to lay out by hand until Jon asked for it to be dealt.
    # Four colours, four of each in the pool and four Rats, so this is
    # the whole supply out on the table: what has to hold is that every
    # row gets one of EACH colour - the failure that reads as right at a
    # glance is four Purples on one Rat - and that no die is left behind
    # in the block it came from.
    colours = [str(c) for c in g.BAT_RAT_DICE.values()]
    want("BAT names the four colours a Rat is given", colours,
         ["Purple", "Blue", "Green", "Yellow"])
    rows, wrong, unplaced = {}, [], []
    for o in w.markers.values():
        if o.name not in colours:
            continue
        hit = None
        for r in range(1, 5):
            for i, c in enumerate(colours, 1):
                if (abs(o.pos[0] - float(g.batDieX(i))) < 0.05
                        and abs(o.pos[2] - float(g.batDieZ(r))) < 0.05):
                    hit = (r, c)
        if hit is None:
            unplaced.append((o.name, round(o.pos[0], 2), round(o.pos[2], 2)))
        elif hit[1] != o.name:
            wrong.append((o.name, hit))         # a Blue in the Purple column
        else:
            rows.setdefault(hit[0], []).append(o.name)
    want("every colour die is under a Rat", unplaced, [])
    want("...each in its own colour's column", wrong, [])
    want("...one of each colour per Rat",
         sorted((r, sorted(v)) for r, v in rows.items()),
         sorted((r, sorted(colours)) for r in range(1, 5)))

    # AND THE ROW CLEARS THE CARDS AT BOTH ENDS. The band between two
    # Rats is 1.94 units and a die is 1.62 across, so there is a sixth
    # of a unit at each edge and no more: a row measured down from the
    # card instead of centred in the band, or a pitch change above,
    # puts dice under the cards rather than between them.
    bad = []
    for r in range(1, 5):
        dz = float(g.batDieZ(r))
        for edge in [float(g.batRatZ(q)) for q in range(1, 5)]:
            if abs(dz - edge) < cw + w.die_half:
                bad.append((r, round(dz, 2), round(edge, 2)))
    want("...and no row of dice touches a Rat card", bad, [])
    want("...with every die on a snap point",
         [(r, i) for r in range(1, 5) for i in range(1, len(colours) + 1)
          if not snapped(float(g.batDieX(i)), float(g.batDieZ(r)))], [])

    # The Buff HP track's cells are snap points inside the Buff HP space.
    bx, bz = float(g.batRightX(int(g.BAT_BUFF))), float(g.batRowZ(3))
    cells = [(bx + float(c[1]), bz + float(c[2]))
             for c in g.BUFF_CELL.values()]
    want("the Buff HP track has fifteen cells", len(cells), 15)
    want("...every one of them inside the card's own space",
         [c for c in cells
          if abs(c[0] - bx) > cw or abs(c[1] - bz) > cl][:2], [])
    want("...and every one of them a snap point",
         [c for c in cells if not snapped(c[0], c[1])][:2], [])

    # The Chip stands below the rightmost Splice, clear of the row.
    # The markers are not on w.table - they live in their own
    # index, keyed by GUID - so ask the script for it by name.
    chip = g.marker("Chip")
    # AND BAT MOVES ITS OWN DIAL under the Splices, turned to this
    # difficulty's Tyrant Health. The Dial is an object of its own,
    # not a face of the Chip: no game reads both, so two objects cost
    # one more thing to put away and save working out which way up a
    # thing is every time somebody types at it. It lies loose on the
    # table beside the Chip, so it is a marker, not a dealt card.
    hp = int(g.BAT_DIFF[g.STATE.difficulty][2])
    dial = g.marker("Dial")
    want("BAT moves the Dial below the rightmost Splice",
         (dial is not None, round(dial.pos[0], 2) if dial else None),
         (True, round(float(g.batRightX(int(g.BAT_SPLICES))), 2)))
    want("...turned to the Tyrant's Health",
         dial.rot[1] if dial and dial.rot else None,
         float(g.CHIP_DIAL[hp]))
    want("...and the dial has an angle for every number it prints",
         sorted(int(k) for k in dict(g.CHIP_DIAL)), list(range(21)))
    # THE CHIP IS NAP'S AND GOES IN THE NAP BOX. It used to stay in
    # the row at the bottom of the table through a game of BAT, which
    # is a thing with five colours on it that this game never reads.
    want("...while the Chip is stowed in its own box",
         (chip is None,
          sorted(k.name for b in w.byguid.values() if b.bag
                 and b.name.startswith("NAP")
                 for k in b.kids if k.name == "Chip")),
         (True, ["Chip"]))

    # The overlay goes down and is locked.
    want("BAT lays its own overlay", "BAT Table" in by, True)
    want("...and locks it so it cannot be dragged",
         by["BAT Table"].locked, True)
    want("...and prints nothing in red", w.errors[:2], [])


def aos_assertions():
    """The AoS table.

    FIVE ELEMENT MATS ACROSS THE MIDDLE, because that is where the
    dice go: every element must receive at least one die and an
    element holds up to its Target plus one, so that row is the only
    part of this table that needs room around it. The decks and the
    two cards they reveal run along the top, what a tier adds along
    the bottom.
    """
    w, g = start("Standard", 3, Panel())
    w.lossy = 3
    g.setupAoS()
    drain(w)
    by = dict((o.name, o) for o in w.table.values())
    boxes = [(float(b.x), float(b.z), float(b.hw), float(b.hd))
             for b in g.aosBoxes().values()]
    over = [(a, b) for i, a in enumerate(boxes) for b in boxes[i + 1:]
            if abs(a[0] - b[0]) < a[2] + b[2] - 0.02
            and abs(a[1] - b[1]) < a[3] + b[3] - 0.02]
    want("no two AoS spaces overlap", over[:2], [])
    felt = g.FELT
    off = [b for b in boxes
           if b[0] - b[2] < float(felt.x0) or b[0] + b[2] > float(felt.x1)
           or b[1] - b[3] < float(felt.z0) or b[1] + b[3] > float(felt.z1)]
    want("no AoS space runs off the felt", off[:2], [])

    def at(name, x, z):
        o = by.get(name)
        return (o is not None
                and abs(o.pos[0] - x) < 0.05 and abs(o.pos[2] - z) < 0.05)

    # ONE TECHNICIAN ON THE CHARACTER SPACE, the one the panel names -
    # the setup ends by dealing the panel's pick and sending the rest
    # of the stack back, the way NAP's has always ended.
    techs = [o for o in w.table.values() if of_family(o.name, "Technician")]
    want("the Technicians are one card on the character space",
         (len(techs), len(techs[0].kids) if techs else 0), (1, 0))
    want("...level with the decks beside it",
         round(techs[0].pos[2] + float(g.CARD_W) / 2, 2) if techs else None,
         round(float(g.AOS_ROW1) + float(g.CARD_L) / 2, 2))
    want("the Program deck and the Limitations are on their spaces",
         (at("Specialized Programs", float(g.aosCol(int(g.AOS_PROGRAMS))),
             float(g.AOS_ROW1))
          or at("Routine Programs", float(g.aosCol(int(g.AOS_PROGRAMS))),
                float(g.AOS_ROW1)),
          at("Limitations", float(g.aosCol(int(g.AOS_LIMITS))),
             float(g.AOS_ROW1))),
         (True, True))
    # THE TOP ROW READS DECK, DECK, CARD, CARD as of 2026-11-12, left to
    # right, and the two orders are not interchangeable: you draw from
    # both decks in one step and then read both face-up cards together.
    # Compared as POSITIONS rather than as index numbers, so renaming the
    # constants cannot satisfy it and swapping two of them cannot hide.
    want("the top row is Program Deck, Limitation Deck, Program, Limitation",
         [round(float(g.aosCol(int(k))), 2)
          for k in (g.AOS_PROGRAMS, g.AOS_LIMITS, g.AOS_PROGRAM, g.AOS_LIMIT)],
         sorted(round(float(g.aosCol(k)), 2) for k in range(1, 5)))

    # AND THE DISCARD LEFT THAT ROW for the right-hand column, directly
    # above the banished dice, so the top row is the four spaces of a turn
    # and nothing else.
    _disc = (round(float(g.AOS_DISCARD_X), 2), round(float(g.AOS_DISCARD_Z), 2))
    _right = round(float(g.AOS_RIGHT), 2)
    want("the discard sits above the banished dice, not in the top row",
         (_disc[0] == _right,
          _disc[1] > round(float(g.AOS_ROW3), 2),
          _disc[1] != round(float(g.AOS_ROW1), 2),
          any(abs(float(b.x) - _right) < 0.05
              and abs(float(b.z) - float(g.AOS_ROW3)) < 0.05
              for b in g.aosBoxes().values())),
         (True, True, True, True))
    want("...and nothing else is on the discard's space",
         len([b for b in g.aosBoxes().values()
              if abs(float(b.x) - _disc[0]) < 0.05
              and abs(float(b.z) - _disc[1]) < 0.05]), 1)
    want("...leaving the fifth top-row column empty",
         [b for b in g.aosBoxes().values()
          if abs(float(b.x) - float(g.aosCol(5))) < 0.05
          and abs(float(b.z) - float(g.AOS_ROW1)) < 0.05], [])

    # THE ADVANCED PROGRAMS STAY IN THE BAG - they are the endgame -
    # but their space is still drawn, because they come out onto it.
    want("the Advanced Programs are not on the table",
         "Advanced Programs" in by, False)
    want("...and their space is still drawn",
         any(abs(float(b.x) - (float(g.AOS_RIGHT) - float(g.AOS_COL))) < 0.05
             and abs(float(b.z) - float(g.AOS_ROW1)) < 0.05
             for b in g.aosBoxes().values()), True)
    mats = sorted(o.pos[0] for o in w.table.values()
                  if o.name.startswith("Element Mat"))
    want("the five element mats are a row across the middle",
         [round(x, 2) for x in mats],
         [round(float(g.aosMid(k, int(g.AOS_MATS))), 2)
          for k in range(1, int(g.AOS_MATS) + 1)])
    want("...all on the same row",
         sorted(set(round(o.pos[2], 2) for o in w.table.values()
                    if o.name.startswith("Element Mat"))),
         [round(float(g.AOS_ROW2), 2)])
    want("AoS prints nothing in red", w.errors[:2], [])


def chip_face_assertions():
    """Two objects, read two ways, and neither has to be flipped.

    The Chip shows five colours and the Dial shows 0 to 20. No game
    reads both - NAP reads the attention colours, BAT reads the
    Tyrant's Health - which is what lets them be separate objects and
    lets each carry its own rotation values, so TTS does the turning.
    While it was one two-faced object, typing 3 at the dial turned it
    to BLUE: the right amount, in the right direction, on the wrong
    face, and nothing said so.
    """
    # EACH FACE IN THE GAME THAT READS IT. BAT stows the Chip in the
    # NAP box and NAP stows the Dial in BAT's, so the two halves of
    # this are measured in the two games rather than in one.
    w, g = start("Standard", 0, Panel())
    g.setupNAP()
    drain(w)
    chip = g.marker("Chip")
    g.onObjectNumberTyped(chip, "White", 2)
    drain(w)
    want("typing 2 at the Chip turns it to a colour",
         chip.rot[1], float(g.CHIP_FACE[g.ATTENTION[2]]))
    want("...and NAP has stowed the Dial it does not read",
         g.marker("Dial"), None)
    w, g = start("Standard", 0, Panel())
    g.setupBAT()
    drain(w)
    dial = g.marker("Dial")
    want("the Dial is a separate object, not a face of the Chip",
         (dial is not None, dial.guid != chip.guid if dial else None),
         (True, True))
    want("...and BAT has stowed the Chip it does not read",
         g.marker("Chip"), None)
    # ITS OWN ROTATION VALUES, so typing at it is TTS's job and the
    # script does not have to work out which way up anything is.
    vals = dial_values()
    want("...carrying a rotation value for every number it prints",
         sorted(vals), list(range(21)))
    want("...each one the angle the script would turn it to",
         [vals[n] for n in range(21)],
         [int(g.CHIP_DIAL[n]) for n in range(21)])
    # And nothing claims a face that is gone: CHIP_DIAL_Z said which
    # way up the dial was while it was the Chip's other side.
    want("...and nothing claims a face that no longer exists",
         g.CHIP_DIAL_Z, None)


def dial_values():
    """The Dial's RotationValues, read out of the built save."""
    save = json.load(io.open(SAVE, encoding="utf-8"))
    out = {}
    def walk(objs):
        for o in objs:
            if o.get("Nickname") == "Dial":
                for v in o.get("RotationValues") or []:
                    out[int(v["Value"])] = int(v["Rotation"]["y"])
            walk(o.get("ContainedObjects", []))
    walk(save["ObjectStates"])
    return out


def on_card_assertions():
    """A die that stands on a card is let go above it, not inside it.

    moveMarker let every marker go at one height, 1.6, which is a
    height for bare felt. A die is 1.62 across at DIE_SCALE, so its
    underside is 0.81 lower than that - below the face of a card lying
    on the table - and the move is made with collide off, so nothing
    stops the die arriving inside the card. Which way Unity then
    pushes the two apart is not the script's to choose, and three
    dice in this mod stand on a card: the Recovery die on the active
    Rat, the Red die on the Rat that drew it, and the Health die on
    the Buff HP track. Two of the three have been seen to lose.

    WHAT IS CHECKED IS THE RELATION, NOT THE HEIGHT. There is no
    gravity here, so the cards are still at the y the script let them
    go at and no number below is TTS's (see Obj.getBounds). The
    predicate is the one that was false: does the die's underside
    clear the top of the card it is standing on.
    """
    w, g = start("Standard", 0)
    g.setupBAT()
    drain(w)
    gl = w.lua.globals()
    half = w.die_half

    def card_top_under(x, z):
        """The top of the tallest card the point (x, z) is over."""
        top = None
        for o in w.table.values():
            base = o.name.rstrip("0123456789").strip()
            land = LAND.get(base, LAND.get(o.name))
            if land is None:
                continue
            cw, cl = float(gl.CARD_W), float(gl.CARD_L)
            hw, hd = (cl / 2, cw / 2) if land else (cw / 2, cl / 2)
            if abs(o.pos[0] - x) <= hw and abs(o.pos[2] - z) <= hd:
                t = o.pos[1] + Obj.FLAT_THICK / 2
                if top is None or t > top:
                    top = (t, o.name)
        return top

    by = dict((o.name, o) for o in w.markers.values() if o.name in
              ("Strategy", "Red", "Health", "Recovery"))
    clears, named = [], []
    for name in ("Recovery", "Red"):
        o = by[name]
        under = card_top_under(o.pos[0], o.pos[2])
        # BY PREFIX. column() leaves card one IN the deck, so the thing
        # under a die on the top Rat is the object still called
        # "Lab Rats (A / B)" rather than "Lab Rat 1".
        named.append(bool(under) and under[1].startswith("Lab Rat"))
        clears.append(bool(under) and o.pos[1] - half >= under[0])
    want("the two dice BAT stands on a Rat are standing on a Rat",
         named, [True, True])
    want("...and both are let go above its face, not inside it",
         clears, [True, True])
    # BY A REAL CLEARANCE, NOT BY A HAIR. 0.05 passed the assertion
    # above and lost at the table anyway: the Rat is dealt from y = 3
    # and is still settling when the die is let go, so the pair
    # interpenetrate and Unity picks a side. This pins the gap.
    # A NUMBER, NOT gl.ONTO_LIFT. Reading the constant out of the Lua
    # and comparing the gap with it is a predicate the script satisfies
    # whatever it is set to - 0.05 passed that version of this check.
    # 0.3 is the floor with a reason behind it: a die is 1.62 across at
    # DIE_SCALE, so a third of its own width is a real fall and well
    # clear of the bounce a card dealt from y = 3 is still finishing.
    lifts = [o.pos[1] - half - card_top_under(o.pos[0], o.pos[2])[0]
             for o in (by["Recovery"], by["Red"])]
    want("...by a third of a die at least, not by a hair",
         [round(v, 3) >= 0.3 for v in lifts], [True, True])

    # AND moveMarker ASKS IT, for the dice that stand on a card and for
    # no others. There is no physics here to lose the race for us, so
    # the backstop firing cannot be observed through a die's position -
    # but whether the move calls it at all can be, and a backstop
    # nothing calls is the whole bug back again.
    w2, g2 = start("Standard", 0)
    asked = []
    g2.liftIfUnder = lambda o, x, z: asked.append(
        (o.getName(), round(float(x), 2), round(float(z), 2))) or False
    g2.setupBAT()
    drain(w2)
    want("moveMarker asks the backstop for the two dice on a Rat",
         sorted(n for n, _x, _z in asked), ["Recovery", "Red"])

    # AND THE BACKSTOP PUTS BACK A DIE THAT LOST THE RACE ANYWAY.
    # Asked directly, with the die moved under its Rat by hand, because
    # there is no physics here to lose the race for us.
    red = by["Red"]
    rx, rz = red.pos[0], red.pos[2]
    top = card_top_under(rx, rz)[0]
    red.pos = (rx, top - 0.20, rz)
    want("the backstop sees a die that ended up under the card",
         bool(g.liftIfUnder(red, rx, rz)), True)
    want("...and puts it back above that card's face",
         red.pos[1] - half >= top, True)
    # ...AND LEAVES ALONE A DIE THAT IS SITTING ON IT. A backstop that
    # fires every time would lift every die ONTO_LIFT into the air on
    # every setup, which is the same bug the other way up.
    red.pos = (rx, top + half, rz)
    want("...and leaves a die that is already on the card where it is",
         (bool(g.liftIfUnder(red, rx, rz)), round(red.pos[1], 3)),
         (False, round(top + half, 3)))
    # AND THE OTHER TWO ARE UNCHANGED. The Health and REC dice go to
    # bare felt beside the exhausted corner, so they must still be let
    # go at the one height - a fix that lifted every marker would put
    # these two in the air.
    want("...while a die going to bare felt is still let go at DROP_Y",
         [round(by[n].pos[1], 3) for n in ("Health", "Strategy")],
         [round(float(gl.DROP_Y), 3)] * 2)
    want("...and nothing is standing on those two",
         [card_top_under(by[n].pos[0], by[n].pos[2])
          for n in ("Health", "Strategy")], [None, None])

    # THE SAME THING IN THE BATTLE, where the Health die stands on the
    # Buff HP track's printed grid. This is the one Jon saw first: the
    # card was being locked while still in the air and the die went
    # under it. The lock was fixed; the drop height was not.
    #
    # AND THE DIE GOES ON THE LAYER, NOT ON THE CORE HEALTH. It used to
    # stand on the core number while the dial read the same, which
    # printed the Tyrant's Health twice. The two are independent stats,
    # so this needs a difficulty that HAS a layer - every shipping rung
    # is 0 - and the 0 case is checked underneath it.
    def battle(layer):
        w, g = start("Standard", 0)
        w.lua.execute("BAT_DIFF.Standard[3] = %d" % layer)
        g.setupBAT()
        drain(w)
        g.btnFinale()
        drain(w)
        hd = [o for o in w.markers.values() if o.name == "Health"][0]
        return w, g, hd

    w, g, hd = battle(3)
    under = card_top_under(hd.pos[0], hd.pos[2])
    want("a layer puts the Health die on the Buff HP card",
         under and under[1], "Buff HP Track")
    want("...and lets it go above that card's face",
         bool(under) and hd.pos[1] - w.die_half >= under[0], True)
    # ON THE LAYER'S OWN SPACE. buffSpace(3) and buffSpace(10) are
    # different cells, so standing it on the core Health would land it
    # somewhere else on the same card and still pass the two above.
    bx, bz = (float(v) for v in g.buffSpace(3))
    want("...on the space for the LAYER, not for the core Health",
         (round(hd.pos[0] - bx, 3), round(hd.pos[2] - bz, 3)), (0.0, 0.0))

    # AND AT LAYER 0 THERE IS NOTHING TO STAND ON. The card still comes
    # out - it is part of the Tyrant's track either way - but a die on
    # it would be claiming a layer the difficulty does not give.
    w0, g0, hd0 = battle(0)
    want("layer 0 leaves the Health die off the Buff card",
         card_top_under(hd0.pos[0], hd0.pos[2]), None)
    want("...and the card is still dealt",
         sorted(o.name for o in w0.table.values()
                if o.name == "Buff HP Track"), ["Buff HP Track"])

    # A DESTINATION WITH NOTHING AT IT BEHAVES AS IT DID. dropOnto
    # never goes below DROP_Y, so an empty patch of felt is still the
    # same drop - asked of the function directly, because every marker
    # a setup moves has something under it somewhere.
    want("dropOnto over empty felt is DROP_Y",
         round(float(g.dropOnto(hd, 26.0, -17.5)), 3),
         round(float(gl.DROP_Y), 3))


def buff_lock_assertions():
    """The Buff HP card locks itself when it reaches its space.

    It starts in the bag, because it is optional; you fetch it when you
    want it. It holds part of the Tyrant's Health on a track you push a
    die along, so a card that slides when you nudge the die is worse
    than no card at all.
    """
    w, g = start("Standard", 0, Panel())
    g.setupBAT()
    drain(w)
    bx, bz = float(g.batRightX(int(g.BAT_BUFF))), float(g.batRowZ(3))
    card = Obj(w, "buff", "Buff HP Track")
    card.pos = (bx + 0.4, 1.0, bz - 0.3)
    w.table[card.guid] = card
    g.onObjectDrop("White", card)
    drain(w)
    want("the Buff HP card locks when it lands on its space",
         (card.locked, round(card.pos[0], 2), round(card.pos[2], 2)),
         (True, round(bx, 2), round(bz, 2)))

    # Dropped anywhere else it is just a card.
    loose = Obj(w, "buff2", "Buff HP Track")
    loose.pos = (bx, 1.0, bz + 12.0)
    w.table[loose.guid] = loose
    g.onObjectDrop("White", loose)
    drain(w)
    want("...and not when it lands somewhere else", loose.locked, False)


def live_pile(w, gid):
    """The object that holds that GUID now.

    A CARD THAT RECEIVES A CARD IS DESTROYED and TTS builds a new deck
    out of the two, so a hand that goes on dropping onto a pile has to
    follow it rather than keep aiming at the card it started from -
    which is exactly what lua.lua's liveDeck does for the script, and
    for the same reason.
    """
    for o in w.table.values():
        if o.guid == gid or any(k.guid == gid for k in o.kids):
            return o
    return None


def pile_assertions():
    """A pile the player built is the one thing on the table with no name.

    THAT IS WHAT THE COMPLETED CREDITS PILE IS - cards dropped onto each
    other - and the deck TTS makes for you carries no nickname at all.
    Pack up asked homeBox for a bag by name, got nothing for "", walked
    past the biggest pile on the table and then reported it as still out
    under a blank name.
    """
    w, g = start("Standard", 3, Panel())
    w.lossy = 3
    g.setupNAP()
    drain(w)
    pz = float(g.ROW_CHAR) - 2 * float(g.NAP_GAP)
    # Four Tasks dropped on each other, the way a Credit pile is made.
    pile = Obj(w, "pile", "Task 1")
    pile.pos = (float(g.PILE_X), 1.0, pz)
    w.table[pile.guid] = pile
    for i in range(2, 5):
        c = Obj(w, "pile%d" % i, "Task %d" % i)
        c.pos = pile.pos
        w.table[c.guid] = c
        # DROPPED AGAIN UNTIL IT LANDS. A container refuses a put
        # whoever made it, and a player who sees a card fail to join
        # the pile simply drops it again - that is the difference
        # between a hand and a script, and every retry in lua.lua
        # exists because the script cannot look. This pile is the
        # player's, so it is built the player's way; left to one
        # attempt each it is a pile of three, and the assertion below
        # is then about nothing.
        for _ in range(8):
            if c in pile.kids:
                break
            pile.putObject(c)
            pile = live_pile(w, pile.guid) or pile
    want("a pile of four cards has no name of its own",
         (pile.name, len(pile.kids)), ("", 4))
    g.btnPack()
    drain(w)
    want("a pile of loose cards prints nothing in red", w.errors[:2], [])
    want("pack up takes the pile away too",
         sorted(o.name for o in w.table.values()
                if g.packable(o) is not None), [])
    want("...as a pile the box can hand back", buried(w), [])
    want("...and says so rather than naming a blank",
         [m for m in w.said if "Still on the table" in m], [])
    # 26 Tasks from the deck and the four this test made.
    want("...and every card of it is back in the box",
         sum(1 for b in w.byguid.values() if b.bag
             for k in b.kids for c in ([k] if not k.kids else k.kids)
             if c.name.startswith("Task ")), 30)


def covered_assertions():
    """Every card a setup deals sits on a space the overlay draws.

    THIS IS THE CHECK THAT WAS MISSING. BAT's and AoS's overlays stopped
    being drawn from where the setup puts cards and started being drawn
    from the script's own list of boxes, which is right - a box on the
    felt and a space you can drop onto cannot then disagree - but it
    left nothing comparing the two halves. BAT's Tier I Protocol was
    being dealt onto bare felt right of the Buff HP space and its six
    Tier III Research Notes along the Splice row, each one straddling
    two boxes belonging to something else, for as long as that overlay
    has existed. Nothing failed, because nothing asked.

    Run at tier 3, which deals everything the lower tiers do and more.

    A FEW PLACES HAVE NO BOX ON PURPOSE and are named here. Jon asked
    for no outline under BAT's Lab Rats or under either of its decks:
    a deck is a stack you can already see. Naming them is the point -
    an unnamed card with nowhere to be is a failure, not a default.
    """
    BOXLESS = {"BAT": ("Lab Rat", "Lab Rats (A / B)", "Encounters",
                       "Experiment", "Upgrades"),
               "AoS": ()}
    for which, listing in (("BAT", "batBoxes"), ("AoS", "aosBoxes")):
        for lvl in ("Easy", "Nobulous"):
            w, g = start(lvl, 3, Panel())
            {"BAT": g.setupBAT, "AoS": g.setupAoS}[which]()
            drain(w)
            boxes = [(float(b.x), float(b.z), float(b.hw), float(b.hd))
                     for b in getattr(g, listing)().values()]
            if which == "BAT":
                x0, x1, zt, zb = [float(v) for v in g.batBanished().values()]
                boxes.append(((x0 + x1) / 2, (zt + zb) / 2,
                              (x1 - x0) / 2, (zt - zb) / 2))
            cw, cl = float(g.CARD_W), float(g.CARD_L)
            homeless = []
            for o in w.table.values():
                name = o.name
                base = name.rstrip("0123456789").strip()
                if LAND.get(base, LAND.get(name)) is None:
                    continue          # the overlay, the Dial, the plate
                x, z = o.pos[0], o.pos[2]
                if base in BOXLESS[which] or at_staging(g, x, z):
                    continue
                if not any(abs(x - b[0]) <= b[2] and abs(z - b[1]) <= b[3]
                           for b in boxes):
                    homeless.append((name, round(x, 2), round(z, 2)))
            want("%s %s t3 deals every card onto a drawn space"
                 % (which, lvl), sorted(homeless), [])


def at_staging(g, x, z):
    """Is this point in the band under the table, where a deck waits?"""
    return (abs(z - float(g.OFF_Z)) < 1.0
            and abs(x) <= float(g.OFF_X) + 0.01)


def alt_view_assertions():
    """The Alt view is shown the face that is actually up.

    A landscape card's preview is rolled one way face up and the other
    way face down, so the single angle baked into the save is right for
    one side and 180 degrees out on the other: with the first value
    tried, Jon got side B of a Lab Rat correct and side A - the side
    you read - upside down. build_mod.py bakes the face-up angle and
    lua.lua swaps it as cards are turned, which is the only way one
    card can be right both ways up.

    THE BAKED ANGLE IS ALSO THE FALLBACK. If assigning alt_view_angle
    from a script does not take on Jon's build - as setCustomObject on
    a PDF did not - every card still reads correctly face up and only
    the backs are wrong, so these two halves are checked apart.
    """
    w, g = start("Standard", 0, Panel())
    up = tuple(float(v) for v in g.ALT_LOOK_UP.values())
    down = tuple(float(v) for v in g.ALT_LOOK_DOWN.values())
    want("the two Alt angles are a half turn apart",
         round(abs(up[2] - down[2]) % 360.0, 3), 180.0)

    def angle(o):
        a = o.alt_view_angle
        if a is None:
            return None
        # TWO SHAPES FOR ONE ANGLE. The save writes {x=, y=, z=} and
        # the script assigns {0, 180, 270}, the sequence form every
        # other rotation in lua.lua uses; TTS takes either as a
        # Vector, so the harness has to as well or it compares the
        # baked angle with the set one and finds them different.
        if hasattr(a, "values"):
            d = dict(a)
            if "x" in d:
                return (float(d["x"]), float(d["y"]), float(d["z"]))
            return tuple(float(d[k]) for k in sorted(d))
        return tuple(float(v) for v in a)

    # EVERY LANDSCAPE CARD IN EVERY BOX, straight out of the save.
    missing, spurious = [], []
    for b in [o for o in w.byguid.values() if o.bag]:
        for d in b.kids:
            for o in [d] + list(d.kids):
                if not is_card(o):
                    continue
                base = o.name.rstrip("0123456789").strip()
                land = bool(LAND.get(base, LAND.get(o.name)))
                if land and angle(o) != up:
                    missing.append((o.name, angle(o)))
                elif not land and angle(o) is not None:
                    spurious.append((o.name, angle(o)))
    want("every landscape card is built holding the face-up angle",
         (bool(missing), missing[:3]), (False, []))
    want("...and no portrait card carries one", spurious[:3], [])

    # TURNED OVER BY A PLAYER. onObjectRotate fires on a deliberate
    # rotation; the handler waits for the card to get where it is
    # going before it reads which way up that is.
    g.setupBAT()
    drain(w)
    # A DEALT RAT, NOT THE STACK IT CAME OUT OF. "Lab Rats (A / B)" is
    # still on the table and its name starts with "Lab Rat" too - the
    # first draft flipped the deck and asserted the card's angle had
    # changed, which it rightly had not.
    rat = [o for o in w.table.values()
           if o.type == "Card" and o.name.startswith("Lab Rat")][0]
    want("a dealt Lab Rat is face up", rat.is_face_down, False)
    # BY NAME, NOT BY TRACEBACK. Rename the handler and the next line
    # calls nil: the harness died on "'NoneType' object is not
    # callable" six frames deep, which is a true report of a real
    # failure and tells you nothing about what broke.
    want("the script listens for a flip at all",
         callable(g.onObjectRotate), True)
    if not callable(g.onObjectRotate):
        return
    rat.setRotation(g.FACEDOWN)
    g.onObjectRotate(rat, 0, 180, "White", 0, 0)
    drain(w)
    want("...and turning it over gives the Alt view the other angle",
         angle(rat), down)
    rat.setRotation(g.FACEUP)
    g.onObjectRotate(rat, 0, 0, "White", 0, 180)
    drain(w)
    want("...and turning it back gives the first one again",
         angle(rat), up)
    # A VECTOR, NOT THREE NUMBERS IN A TABLE.
    want("...and the angle was set as a Vector",
         bool(dict(rat.alt_view_angle).get("vector")), True)

    # THREE WAYS TO TURN A CARD OVER, and onObjectRotate was not the
    # one Jon used: the preview stayed wrong at his table while every
    # test here passed. F is a player ACTION with its own event, and
    # picking a card up and putting it down the other way round is
    # physics, which raises neither.
    for trigger, call in (
            ("the F key", lambda o: g.onPlayerAction(
                None, g.Player.Action.FlipOver, w.lua.table_from([o]))),
            ("a pick-up and drop", lambda o: g.onObjectDrop("White", o))):
        rat.setRotation(g.FACEDOWN)
        rat.alt_view_angle = None
        call(rat)
        drain(w)
        want("%s turns the card and the Alt angle follows" % trigger,
             angle(rat), down)
        rat.setRotation(g.FACEUP)
        call(rat)
        drain(w)
        want("...and back again, for %s" % trigger, angle(rat), up)

    # AND IT SAYS NOTHING. The line that told the three faults apart
    # has done its job and gone; a preview that works does not
    # announce itself once per load for the rest of the mod's life.
    want("setting the Alt angle prints nothing in chat",
         [m for m in w.said if m.startswith("ALT ")], [])

    # NOT EVERYTHING THAT TURNS. A portrait card and a deck both have
    # to come through a flip with no angle at all: zero is the right
    # answer for a portrait card, and a deck is not a card.
    port = [o for o in w.table.values()
            if o.name.startswith("Experiment") or o.name.startswith("Upgrade")]
    for o in port[:1] + [deck(w, "Upgrades")]:
        if o is None:
            continue
        before = angle(o)
        o.setRotation(g.FACEDOWN)
        g.onObjectRotate(o, 0, 180, "White", 0, 0)
        drain(w)
        want("flipping %s leaves its Alt angle alone" % o.name,
             angle(o), before)

    # THE SCRIPT TURNS ONE OVER TOO. A character on side B is dealt
    # face down by showChar, which is a flip onObjectRotate never
    # hears about - the player did not make it.
    for game, setup in (("AoS", "setupAoS"), ("IMP", "setupImposter")):
        w, g = start("Standard", 0, Panel())
        getattr(g, setup)()
        drain(w)
        seen = {}
        for _ in range(12):
            a = g.charOf(game)
            if a is None:
                break
            card = [o for o in w.table.values()
                    if o.name.startswith(str(g.CARD_NAME[g.CHAR_DECK[game]]
                                             or ""))]
            if card:
                seen[bool(a.back)] = (card[0].is_face_down, angle(card[0]))
            if len(seen) == 2:
                break
            g.btnChar()
            drain(w)
        want("%s: a character on each side was dealt" % game,
             sorted(seen), [False, True])
        for back, (facedown, ang) in sorted(seen.items()):
            want("%s: side %s is dealt face %s"
                 % (game, "B" if back else "A", "down" if back else "up"),
                 facedown, back)
            want("%s: ...and the Alt view is given the matching angle"
                 % game, ang, down if back else up)


def take_from(w, g, deckname, x, z, nick=None):
    """Deal one card off a deck onto (x, z), the way the script would.

    NOT BY REACHING INTO .kids. A card inside a deck carries the same
    "in a container" flag as a card inside a bag - which is right,
    because getAllObjects cannot see either - and lifting one out by
    hand leaves the flag set. The card then sits on the table where
    nothing can find it, so a check that something DID NOT happen to
    it passes for the wrong reason. That is exactly what hid a sweep
    that bags the Upgrades a Rat is holding.
    """
    d = deck(w, deckname)
    if d is None or not d.kids:
        return None
    arg = {"position": w.lua.table_from([x, 1.6, z]), "smooth": False}
    if nick is not None:
        got = [k for k in d.kids if k.name == nick]
        if not got:
            return None
        arg["guid"] = got[0].guid
    c = d.takeObject(w.lua.table_from(arg))
    drain(w)
    return c


def finale_assertions():
    """Each game's last button: clear the old table, deal the new one.

    All three finales are REACHED rather than set up, so no setup deals
    them and nothing on the table could take their cards out of the box
    - Final Exams, Tyrant Attacks and Advanced Programs sat in their
    bags for the life of the mod. IN_THE_BAG has said "a later script
    option starts the exam" since it was written.

    WHAT IS EASY TO GET WRONG IS NOT THE DEALING. It is the sweep: each
    finale puts away the part of the table the game has finished with,
    and each of the three has something sitting in the middle of that
    which it must NOT touch - NAP's Completed Credits pile is the
    record the exam pool is built from, BAT's Rats keep their own
    Upgrades, and AoS still reveals a Limitation per Program. So every
    case below checks a keeper as well as a leaver.
    """
    FIN = {"NAP": ("Start the Final Exam", "setupNAP"),
           "BAT": ("Start the Tyrant Battle", "setupBAT"),
           "AoS": ("Start Advanced Programming", "setupAoS")}

    def pressed(pan):
        return [b for b in pan.buttons if b["fn"] == "btnFinale"]

    # NO BUTTON BEFORE THERE IS A GAME, and none for the Imposter
    # scenario, which has no finale to start because it IS one.
    w, g = start("Standard", 0, Panel())
    g.refreshPanel()
    want("a bare table offers no finale", pressed(g.PANEL), [])
    w, g = start("Standard", 3, Panel())
    g.setupImposter()
    drain(w)
    want("the Imposter scenario offers no finale", pressed(g.PANEL), [])

    for game, (label, setup) in sorted(FIN.items()):
        w, g = start("Standard", 0, Panel())
        getattr(g, setup)()
        drain(w)
        shown = pressed(g.PANEL)
        want("%s offers its finale once it is set up" % game,
             [b["label"] for b in shown], [label])
        before = dict((o.guid, o.name) for o in w.table.values())
        g.btnFinale()
        drain(w)
        want("%s: ...and the button goes once it is pressed" % game,
             pressed(g.PANEL), [])
        # PRESSED AGAIN, NOT ASKED ABOUT. This read the flag and the
        # panel and called that "does nothing", so removing the guard
        # in btnFinale passed it: the button is gone from the panel
        # either way, and a second press deals a second set of Final
        # Exams onto the first.
        dealt = {"NAP": ("Final Exams", 3), "BAT": ("Tyrant Attacks", 7),
                 "AoS": ("Advanced Programs", 3)}[game]
        want("%s: the finale deals %d %s" % (game, dealt[1], dealt[0]),
             out(w, dealt[0]), dealt[1])

        def shape():
            """How those cards are arranged, not just how many.

            Counting them is not enough: deckOut finds a deck already
            on the table and simply moves it, so a second press deals
            no extra cards in two of the three games. What it does do
            is turn a SECOND Tyrant Attack face-up, which changes the
            commit colour and shortens the deck - and that is only
            visible in the split, never in the total.
            """
            return sorted((len(o.kids) or 1, o.is_face_down)
                          for o in w.table.values()
                          if o.name.startswith(names_of(dealt[0])))

        was, said = shape(), len(w.said)
        g.btnFinale()
        drain(w)
        want("%s: ...and pressing it again changes nothing" % game,
             (out(w, dealt[0]), shape()), (dealt[1], was))
        # AND DOES NOT RUN. The two above are worth having but neither
        # can fail on its own: deckOut gathers a deck's stray cards
        # back in before it deals, so a second run of any of the three
        # puts the table back exactly as it was. What it really costs
        # is a re-shuffle - BAT would deal the five Splices a fresh
        # random order under a battle already in progress - and the
        # only deterministic mark a second run leaves is that it
        # speaks again.
        want("%s: ...and says nothing further" % game, len(w.said), said)
        want("%s: the finale printed nothing in red" % game, w.errors[:2], [])
        # THE FELT IS STILL THERE. The overlay is 56 units wide and
        # lies at the middle of the table, so its CENTRE sits inside
        # one of the spaces a finale sweeps - NAP's falls in an
        # Assignment box - and a sweep by position finds it there and
        # bags the table out from under the game. That is exactly what
        # the first version of this did, with all of the assertions
        # above it passing.
        want("%s: ...and the table overlay is still on the table" % game,
             bool([o for o in w.table.values()
                   if o.name.endswith(" Table")]), True)
        want("%s: ...and so is the rulebook and both counters" % game,
             sorted(o.name for o in w.table.values()
                    if o.name.endswith(" Rules")
                    or o.name in ("Credit Record", "Banked Opportunities",
                                  "Health Readout")),
             sorted(n for n in (
                 {"NAP": ["NAP Rules", "Credit Record",
                          "Banked Opportunities"],
                  "BAT": ["BAT Rules", "Health Readout"],
                  "AoS": ["AoS Rules"]}[game])))
        want("%s: ...and raised no setup error" % game,
             [m for m in w.said if "Setup error" in m][:2], [])
        # NOTHING IS LEFT LYING ON THE FELT. A card swept off a space
        # travels through OFF on its way to the bag, and one the bag
        # refuses stays there - which is the bug that left five ghost
        # cards on the AoS table.
        want("%s: the finale strands nothing in the staging band" % game,
             [o.name for o in w.table.values()
              if at_staging(g, o.pos[0], o.pos[2])][:3], [])
        g.btnPack()
        drain(w)
        want("%s: and Pack up still empties the table after it" % game,
             sorted(set(o.name for o in w.table.values()
                        if g.packable(o))), [])

    # ---- NAP: the exam comes out, the record stays -------------------
    w, g = start("Standard", 0, Panel())
    g.setupNAP()
    drain(w)
    want("NAP deals no Final Exams during setup", out(w, "Final Exams"), 0)
    # A DAY'S PLAY, not a fresh table. The Completed Credits pile is
    # the record the exam pool is built from and it sits inside the
    # area the exam sweeps; empty, there is nothing there to sweep, so
    # a sweep that took it passed every check here. One completed Task
    # on it is the whole difference. taken out of the deck the way the
    # script takes one, because a card lifted out of a deck's kids by
    # hand is still flagged as being inside a container and nothing on
    # the table can see it - which is how the same mistake hid the BAT
    # case below.
    done = take_from(w, g, "Assignment",
                     float(g.PILE_X), float(g.FINF_Z) - float(g.NAP_GAP))
    coupon = take_from(w, g, "Assignment",
                       float(g.PILE_X), float(g.FINF_Z) - 2 * float(g.NAP_GAP))
    g.btnFinale()
    drain(w)
    want("the Completed Credits pile survives the exam",
         done is not None and done.guid in w.table, True)
    want("...and so do the Banked Opportunities under it",
         coupon is not None and coupon.guid in w.table, True)
    want("the Final Exam draws 3 exams and no more",
         out(w, "Final Exams"), 3)
    want("...all three face up", sorted(o.is_face_down
         for o in w.table.values()
         if o.name.startswith(names_of("Final Exams"))),
         [False, False, False])
    # ON THE THREE PRINTED SPACES, which is the part a count cannot
    # see. The row the day revealed into is where they go, and the
    # third of them is the old discard space - the draw is laid out at
    # ASSIGN_PITCH precisely so it lands in boxes the mat has drawn.
    want("...one on each of the three spaces beside the old deck space",
         sorted(round(o.pos[0], 2) for o in w.table.values()
                if o.name.startswith(names_of("Final Exams"))),
         sorted(round(float(g.DECK_X) + k * float(g.ASSIGN_PITCH), 2)
                for k in (1, 2, 3)))
    want("...and all three on the row the Assignments used",
         sorted(set(round(o.pos[2], 2) for o in w.table.values()
                    if o.name.startswith(names_of("Final Exams")))),
         [round(float(g.ROW_CHAR), 2)])
    for gone in ("Assignment", "Time Slot", "FINF"):
        want("...and the %s cards are back in the box" % gone,
             [o.name for o in w.table.values()
              if o.name.startswith(gone)][:3], [])
    # THE KEEPERS. The two piles and the Apprentice are what the exam
    # is played with, and all three sit inside the area being swept.
    want("...while the Apprentice stays on the table",
         bool([o for o in w.table.values()
               if o.name.startswith("Apprentice")]), True)
    want("...and so do both pile counters",
         sorted(o.name for o in w.table.values()
                if o.name in ("Credit Record", "Banked Opportunities")),
         ["Banked Opportunities", "Credit Record"])

    # ---- BAT: the Attacks come out, the Rats keep their kit ----------
    w, g = start("Standard", 0, Panel())
    g.setupBAT()
    drain(w)
    want("BAT deals no Tyrant Attacks during setup",
         out(w, "Tyrant Attacks"), 0)
    # A PLAYED TABLE, not a fresh one. The sweep has to tell an Upgrade
    # a Rat has taken from one still in the deck, and after a bare
    # setup there is no difference to get wrong: both are in the deck.
    held = take_from(w, g, "Upgrades",
                     float(g.batLeftX(1)), float(g.batRowZ(1)))
    spliced = take_from(w, g, "Upgrades",
                        float(g.batRightX(1)), float(g.batRowZ(4)))
    g.btnFinale()
    drain(w)
    want("the Tyrant Battle deals all 7 Attack cards",
         out(w, "Tyrant Attacks"), 7)
    attacks = [o for o in w.table.values()
               if o.name.startswith(names_of("Tyrant Attacks"))]
    want("...as a face-down deck and one card face-up beside it",
         sorted((len(o.kids) or 1, o.is_face_down) for o in attacks),
         [(1, False), (6, True)])
    want("...with the face-up one on the discard space",
         [round(o.pos[0], 2) for o in attacks if not o.is_face_down],
         [round(float(g.batRightX(int(g.BAT_ATTACK_UP))), 2)])
    want("...and both Splice-Phase decks back in the box",
         [o.name for o in w.table.values()
          if o.name in ("Encounters", "Upgrades")], [])
    want("...while the Upgrade a Rat is holding stays with it",
         held.guid in w.table, True)
    want("...and the Splice stays on the Tyrant's track",
         (spliced.guid in w.table,
          round(spliced.pos[2], 2) == round(float(g.batRowZ(4)), 2)),
         (True, True))

    # ---- AoS: three of the eight, and the Limitations stay -----------
    w, g = start("Standard", 0, Panel())
    g.setupAoS()
    drain(w)
    want("AoS deals no Advanced Programs during setup",
         out(w, "Advanced Programs"), 0)
    g.btnFinale()
    drain(w)
    want("Advanced Programming deals 3 of the 8", out(w, "Advanced Programs"), 3)
    want("...and the other 5 go back in the box",
         inbag(w, "AoS", "Advanced Program"), 5)
    want("...face down on their own space",
         [(o.is_face_down, round(o.pos[0], 2))
          for o in w.table.values()
          if o.name.startswith(names_of("Advanced Programs"))],
         [(True, round(float(g.AOS_RIGHT) - float(g.AOS_COL), 2))])
    want("...with the Program deck put away",
         [o.name for o in w.table.values()
          if o.name.startswith("Specialized Program")
          or o.name.startswith("Program")], [])
    # THE LIMITATIONS STAY. An Advanced Program is run by the ordinary
    # rule, Limitation and all - the model runs the finale through the
    # same run_program - so sweeping them is the plausible mistake.
    want("...and the Limitation deck still on the table",
         bool([o for o in w.table.values()
               if o.name.startswith(names_of("Limitations"))]), True)
    want("...and the element mats too",
         out(w, "Element Mats"), int(g.AOS_MATS))


def markers_home_assertions():
    """Pack up puts every die, the Chip and the Dial back in their row.

    THERE ARE FOUR PURPLE DICE AND ONE NAME BETWEEN THEM. markersHome
    walked DICE_HOME, which is keyed by nickname, and marker() answers
    with the first object of that name - so of the four Purple dice
    Pack up could fetch exactly one, and the same for Blue, Green and
    Yellow. A setup only ever moves the Chip, the Dial and the stat
    dice, so a check that only ran a setup would barely notice; what
    leaves fourteen dice strewn over the table is PLAYING, which is
    what the scatter below stands in for.

    Checked after each game in turn, because each one starts them in
    a different place.
    """
    for which in ("BAT", "NAP", "AoS", "IMP"):
        w, g = start("Standard", 3, Panel())
        {"BAT": g.setupBAT, "NAP": g.setupNAP,
         "AoS": g.setupAoS, "IMP": g.setupImposter}[which]()
        drain(w)
        home = dict((str(k), [float(v) for v in p.values()])
                    for k, p in g.MARKER_HOME.items())
        want("%s: every loose object has a place to go back to" % which,
             sorted(home) == sorted(w.markers), True)
        moved = [o.name for gid, o in w.markers.items()
                 if abs(o.pos[0] - home[gid][0]) > 0.05
                 or abs(o.pos[2] - home[gid][1]) > 0.05]
        want("...and %s moves some of them" % which, bool(moved), True)
        # PLAYED WITH. Every die ends a game somewhere it was spent,
        # and that is the state Pack up has to clear - not the tidy
        # one a setup leaves.
        for i, o in enumerate(w.markers.values()):
            o.pos = (-20.0 + (i % 8) * 5.0, 1.6, 12.0 - (i // 8) * 6.0)
        g.btnPack()
        drain(w)
        away = sorted(set(
            o.name for gid, o in w.markers.items()
            if abs(o.pos[0] - home[gid][0]) > 0.05
            or abs(o.pos[2] - home[gid][1]) > 0.05))
        want("...and pack up brings every one of them back", away, [])
    # AND NO TWO OF THEM SHARE A PLACE, which is the other half of
    # keying this by GUID: a table that sent two dice to one spot
    # would pass the check above and pile them up.
    w, g = start("Standard", 0, Panel())
    seats = [tuple(round(float(v), 2) for v in p.values())
             for p in g.MARKER_HOME.values()]
    want("no two loose objects go home to the same place",
         len(set(seats)), len(seats))


def landing_assertions():
    """No setup deals a card onto something already standing there.

    A card dropped on a deck joins it. OFF - the point every takeObject
    in the script drops at on the way somewhere - WAS pad(3), one of
    the five places a deck is parked while it is being built, so AoS
    spent its whole middle step dropping cards onto the Specialized
    Programs deck. Jon's table showed the symptom the wrong way round:
    the Program deck was perfectly correct, and five of its own cards
    were ALSO lying in the staging band.

    Reads every pair, not the pair that was wrong, so a new deal onto
    an occupied spot fails here too.
    """
    for which in ("BAT", "NAP", "AoS", "IMP"):
        for lvl in ("Easy", "Standard", "Hard", "Nobulous"):
            for tier in (0, 1, 2, 3):
                w = run(lvl, tier, which)
                want("%s %s t%d deals nothing onto an occupied spot"
                     % (which, lvl, tier), w.landings, [])
    # AND THE TWO POINTS CANNOT BE THE SAME POINT, which is the whole
    # of the bug above stated in one line.
    lua = lupa.LuaRuntime(unpack_returned_tuples=True)
    w, src = build(lua)
    install(lua, w)
    lua.execute(src)
    g = lua.globals()
    off = [round(float(v), 3) for v in g.OFF.values()]
    want("no staging pad is the point cards are taken to",
         [i for i in range(1, 6)
          if [round(float(v), 3) for v in g.pad(i).values()] == off], [])
    want("...and none of them is within a card of it",
         [i for i in range(1, 6)
          if abs(float(g.pad(i)[1]) - off[0]) < float(g.CARD_W)], [])


RULES_DIR = os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "rules")


def md5(path):
    """Eight hex of a file's md5 - what build_mod puts in the URL."""
    return hashlib.md5(io.open(path, "rb").read()).hexdigest()[:8]


def exam_pool_assertions():
    """The Final Exam pool, built from the Credits actually earned.

    "For each subject independently, randomly add the following number
    of Final Exam cards from that subject to the pool" - 1 card at 0-1
    Credits in it, 2 at 2-3, 3 at 4+ - then shuffle and draw 3. It was
    the player's job and it is the one piece of NAP that cannot be
    done by eye: the pile counted by subject, four lookups, then a
    draw out of what those four produced.

    THE EASY HALF IS THE SIZE, AND IT IS NOT THE RULE. A pool of the
    right length that took every card out of Anatomy would satisfy any
    check a count can carry, and so would one that never read the
    Credit pile at all. So the pool is grouped BY SUBJECT here and
    each group is checked against what that subject's Credits bought.

    THROUGH THE PILE, NOT THROUGH A STUBBED TALLY. creditTally reads
    nicknames off the Completed Credits space and maps them through
    NAP_CREDIT; handing examDraw a tally directly would pass with
    nothing on the table reaching it, which is most of what there is
    to get wrong.
    """
    w, g = start("Standard", 0, Panel())
    exam = dict((str(s), sorted(int(i) for i in v.values()))
                for s, v in g.NAP_EXAM.items())
    cred = dict((str(s), sorted(int(i) for i in v.values()))
                for s, v in g.NAP_CREDIT.items())
    subject = dict((str(s), str(n)) for s, n in g.NAP_SUBJECT.items())
    one = str(g.CARD_NAME["Final Exams"])
    pz = float(g.ROW_CHAR) - 2 * float(g.NAP_GAP)

    def whose(nick):
        """Which subject a 'Final Exam N' belongs to."""
        n = int(nick.rsplit(" ", 1)[-1])
        return [s for s in sorted(exam) if n in exam[s]][0]

    want("every Final Exam belongs to exactly one subject",
         sorted(n for s in exam for n in exam[s]), list(range(1, 13)))

    # ONE CARD PER SUBJECT, WHATEVER THE TRANSCRIPT SAYS, as of
    # 2026-11-12. It used to read 1 at 0-1 Credits, 2 at 2-3 and 3 at
    # 4+, which put the subjects you had studied into the pool more
    # often than the ones you had not - so the Credit ladder was paying
    # out twice, once in Targets and once in which cards you faced.
    want("the pool puts in 1 card per subject at every Credit count",
         [int(g.examPoolSize(n)) for n in range(0, 8)], [1] * 8)

    # AND THE POOL IT BUILDS, for four transcripts: nothing studied, a
    # subject filled, two filled while one is empty, and one Credit
    # short of a threshold everywhere.
    for label, have in (("an empty transcript", {}),
                        ("Anatomy filled", {"ANA": 4}),
                        ("Anatomy and Procedure filled, Theory empty",
                         {"ANA": 5, "ENG": 2, "PRO": 4}),
                        ("one short of every threshold",
                         {"ANA": 1, "ENG": 3, "PRO": 1, "THE": 3})):
        w, g = start("Standard", 0, Panel())
        put = 0
        for s in sorted(have):
            for i in range(have[s]):
                o = Obj(w, "cr%d" % put, "Task %d" % cred[s][i])
                o.pos = (float(g.PILE_X), 1.0, pz)
                w.table[o.guid] = o
                put += 1
        n, subj = g.creditTally(None)
        want("%s: the Credit pile reads back what was put on it" % label,
             (int(n), dict((str(s), int(c)) for s, c in subj.items())),
             (put, dict((s, c) for s, c in have.items() if c)))
        draw, pool, line = g.examDraw()
        names = [str(v) for v in pool.values()]
        by = {}
        for nm in names:
            by[whose(nm)] = by.get(whose(nm), 0) + 1
        want("%s: every subject puts in exactly one card" % label,
             by, dict((s, 1) for s in sorted(exam)))
        want("%s: and no exam is in the pool twice" % label,
             len(set(names)), len(names))
        drawn = sorted(str(k) for k in draw.keys())
        want("%s: three are drawn out of it" % label,
             len(drawn), int(g.EXAM_DRAW))
        want("%s: ...and every one of them was in the pool" % label,
             [nm for nm in drawn if nm not in names], [])
        # THE LINE THE BRIEFING PRINTS, which is the only way a player
        # at the table can tell what the pool was built from. It still
        # reports the Credits, which now decide Targets rather than
        # which cards come up - so the number is worth printing and is
        # no longer the number that sized the pool.
        want("%s: the briefing reports each subject's Credits" % label,
             sorted(re.findall(r"(\w+) (\d+) Credits, (\d+) card",
                               str(line))),
             sorted((subject[s], str(have.get(s, 0)), "1")
                    for s in sorted(exam)))

    # FILLING A SUBJECT NO LONGER BUYS ITS WHOLE SHELF. 4 Credits in
    # Theory used to put all three Theory exams in the pool; it puts in
    # one, like every other subject, and the pool is 4 cards whatever
    # the transcript looks like. That is the whole of the 2026-11-12
    # change and it is worth stating on the transcript that used to be
    # the exception.
    w, g = start("Standard", 0, Panel())
    for i in range(4):
        o = Obj(w, "th%d" % i, "Task %d" % cred["THE"][i])
        o.pos = (float(g.PILE_X), 1.0, pz)
        w.table[o.guid] = o
    _, pool, _ = g.examDraw()
    _filled = [str(v) for v in pool.values()]
    want("4 Credits in Theory still puts exactly one Theory exam in",
         len([nm for nm in _filled if whose(nm) == "THE"]), 1)
    want("...and the pool is still one card from each of the 4 subjects",
         sorted(whose(nm) for nm in _filled), sorted(exam))

    # AND EVERY ONE OF THE TWELVE CAN COME UP, which is the half of this
    # that a count cannot see. The old pool took the FIRST cards of each
    # subject in table order, so a check on sizes passed while eight of
    # the twelve printed exams were unreachable on an empty transcript -
    # and those eight carry eight of the twelve printed restrictions.
    # Nothing short of drawing repeatedly notices that.
    w, g = start("Standard", 0, Panel())
    _seen = set()
    for _ in range(400):
        _, _pool, _ = g.examDraw()
        _seen.update(int(str(v).rsplit(" ", 1)[-1]) for v in _pool.values())
    want("every one of the 12 Final Exams can reach the pool",
         sorted(_seen), list(range(1, 13)))
    # AND NOTHING FROM A SUBJECT'S OWN CARDS ANYWHERE ELSE. The pool
    # is named by index, so an off-by-one in NAP_EXAM would hand
    # Theory an Engineering exam and every count above would still
    # come out right.
    want("...and the other nine stay out of Theory's share",
         sorted(whose("%s %d" % (one, n)) for n in exam["THE"]),
         ["THE", "THE", "THE"])


def rules_assertions():
    """The book on the rail is the one for the game on the table.

    IT WAS ONE BOOK WHOSE URL THE SCRIPT REWROTE, with setCustomObject
    and reload, which is the documented way and did not work at Jon's
    table: his autosave after a NAP setup still held BAT_Rulebook.pdf
    as the object's own URL. No Lua error anywhere, the right GUID,
    the right URL table - and the harness passed, because the stub
    did what the documentation says and TTS did not.

    SO THIS DOES NOT TEST THE MECHANISM ANY MORE, it tests the result:
    exactly one book is out, it is this game's, and the other three
    are in their boxes. That is a claim a stub cannot flatter, because
    taking an object out of a bag is the one thing this harness has
    always modelled honestly.
    """
    nick = {"BAT": "BAT Rules", "NAP": "NAP Rules",
            "AoS": "AoS Rules", "IMP": "NRJ Rules"}
    pdf = {"BAT Rules": "BAT_Rulebook.pdf", "NAP Rules": "NAP_Rulebook.pdf",
           "AoS Rules": "AoS_Rulebook.pdf",
           "NRJ Rules": "NRJ_Campaign_Supplement.pdf"}

    def out(w):
        return [o for o in w.table.values() if o.name in nick.values()]

    w, g = start("Standard", 3, Panel())
    want("a fresh table has BAT's book on the rail",
         sorted(o.name for o in out(w)), ["BAT Rules"])
    for which in ("BAT", "NAP", "AoS", "IMP"):
        w, g = start("Standard", 3, Panel())
        {"BAT": g.setupBAT, "NAP": g.setupNAP,
         "AoS": g.setupAoS, "IMP": g.setupImposter}[which]()
        drain(w)
        books = out(w)
        want("setting up %s leaves one book on the rail" % which,
             [o.name for o in books], [nick[which]])
        u = books[0].custom.get("PDFUrl", "")
        want("...and it is that game's rulebook",
             u.rsplit("/", 1)[-1].split("?")[0], pdf[nick[which]])
        # AND IT IS THE BOOK AS IT IS ON DISK RIGHT NOW. Jon re-read a
        # three-revision-old NAP book on 2026-11-11 off a stable URL
        # that TTS had cached weeks earlier. The push was fine, the
        # CDN was serving the current file byte for byte, and nothing
        # in this harness could tell: it checked the NAME, which had
        # not changed and was never going to. This checks the content
        # hash, so a rebuilt book whose URL did not move fails here.
        want("...carrying the content hash of the book on disk",
             u.split("?")[-1],
             "v=" + md5(os.path.join(RULES_DIR, pdf[nick[which]])))
        want("...standing where the rail is",
             (round(books[0].pos[0], 2), round(books[0].pos[2], 2)),
             (round(float(g.RULES_POS[1]), 2),
              round(float(g.RULES_POS[3]), 2)))
        want("...locked, so it cannot be dragged off", books[0].locked, True)
        want("...under a button naming the game",
             [b["label"] for b in books[0].buttons],
             ["Rules: " + ("NRJ" if which == "IMP" else which)])
        want("...and the other three are in their boxes",
             sorted(k.name for b in w.byguid.values() if b.bag
                    for k in b.kids if k.name in nick.values()),
             sorted(v for kk, v in nick.items() if kk != which))
        want("...and nothing printed in red", w.errors[:2], [])
        # PACK UP LEAVES IT THERE. Clearing the table at the end of a
        # game is no reason to take the rules away from someone who
        # may still be reading them.
        g.btnPack()
        drain(w)
        want("...and pack up leaves the book out" % (),
             [o.name for o in out(w)], [nick[which]])


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
    # ONE CHOOSER PER GAME, and it names the character on the table.
    # Keep 1/2/3 used to stand beside it for AoS and the Imposter
    # scenario: a second way to choose that knew nothing about the
    # first, so the panel went on naming someone who was no longer out.
    # It is gone, and nothing on the mat says "Keep" any more.
    for which, word in (("NAP", "Apprentice"), ("AoS", "Technician"),
                        ("IMP", "Imposter"), ("BAT", None)):
        w, g = start("Standard", 0, Panel())
        {"NAP": g.setupNAP, "BAT": g.setupBAT, "AoS": g.setupAoS,
         "IMP": g.setupImposter}[which]()
        drain(w)
        shown = [b["label"] for b in g.PANEL.buttons
                 if b["fn"] == "btnChar"]
        want("%s offers one character button" % which, len(shown),
             1 if word else 0)
        if word:
            want("...naming the character that is on the table",
                 shown[0], "%s  %s" % (word, g.charOf(which).name))
        want("%s offers no Keep row" % which,
             [b["label"] for b in g.PANEL.buttons
              if b["label"] == "Keep" or (len(b["label"]) == 1
                                          and b["label"] in "12345")], [])

    # Pack up puts the panel back to having none.
    g.setupNAP()
    drain(w)
    g.btnPack()
    drain(w)
    want("packing up takes the game's options away",
         [n for n in labels(g.PANEL) if n in ("Apprentice", "FINF")], [])


def choice_assertions():
    """The character dial on the panel, for each game that has one.

    CHECKED THROUGH WHAT LANDS ON THE TABLE, not through STATE. The
    panel can hold any number it likes; what matters is that the card
    out is the one the button names, on the side it names.

    All three decks are two-sided, so the button walks characters and
    not cards: three cards are six Apprentices and five are ten
    Imposters, and half of each walk is a flip rather than a swap.
    """
    faceup = facedown = None
    for which, deck, cards in (("NAP", "Apprentices", 3),
                               ("AoS", "Technicians", 3),
                               ("IMP", "Imposters (A / B)", 5)):
        w, g = start("Standard", 0, Panel())
        {"NAP": g.setupNAP, "AoS": g.setupAoS,
         "IMP": g.setupImposter}[which]()
        drain(w)
        faceup = tuple(float(v) for v in g.FACEUP.values())
        facedown = tuple(float(v) for v in g.FACEDOWN.values())
        want("a card's two sides are two different rotations",
             faceup != facedown, True)
        table = g.CHAR_LIST[which]
        n = len(list(table.values()))
        want("%s offers two characters per card" % which, n, cards * 2)
        one = str(g.CARD_NAME[deck]) if g.CARD_NAME[deck] else deck
        seen = []
        for _ in range(n + 1):
            a = g.charOf(which)
            out_now = [o for o in w.table.values()
                       if of_family(o.name, one)]
            seen.append((str(a.name), int(a.card), bool(a.back),
                         [o.name for o in out_now],
                         [o.rot for o in out_now]))
            g.btnChar()
            drain(w)
        want("%s has exactly one character on the table" % which,
             sorted(set(len(e[3]) for e in seen)), [1])
        want("%s deals the card the button names" % which,
             [e[3][0] for e in seen],
             ["%s %d" % (one, e[1]) for e in seen])
        want("...%s turns it to the side the button names" % which,
             [e[4][0] == (facedown if e[2] else faceup) for e in seen],
             [True] * len(seen))
        want("...%s reaches every character and comes back round" % which,
             [e[0] for e in seen[:n]] + [seen[n][0] == seen[0][0]],
             [str(table[i + 1].name) for i in range(n)] + [True])
        # NOTHING IS LOST ON THE WAY ROUND. Choosing again has to put
        # the card that is out back into a stack before it can take
        # another one, and findDeck cannot see a loose card in a bag:
        # a deckOut here would have dealt a short stack the second time.
        box = {"NAP": "NAP", "AoS": "AoS", "IMP": "NRJ"}[which]
        want("%s keeps all its cards through a full cycle" % which,
             out(w, deck) + inbag(w, box, one, deck), cards)
        want("...and strands none of them loose in the bag",
             stranded(w, box, one), 0)

    w, g = start("Standard", 0, Panel())
    g.setupNAP()
    drain(w)
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
          if o.locked and not o.name.endswith(" Rules")
          and not o.name.startswith(
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


def of_family(name, one):
    """A card of `one` is `one` and a number - never a longer name.

    "Imposter 3" is one of the Imposters and "Imposter Task 3" is not,
    and a startswith test cannot tell them apart. It counted the four
    Imposter Tasks as Imposters and reported nine cards in a deck of
    five.
    """
    return bool(re.match(r"^%s( \d+)?$" % re.escape(one), name))


def inbag(w, game, prefix, deck=None):
    """Cards of a family in a game's bag, loose or in their own deck."""
    n = 0
    # BAGS ARE NOT ON THE TABLE. w.table is what is out; the four boxes
    # live in byguid, which is why this read zero and said the cards
    # had been lost.
    for o in w.byguid.values():
        if o.bag and o.name.startswith(game):
            for k in o.kids:
                if of_family(k.name, prefix) or k.name == (deck or prefix):
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
    # A DIE PARKED ON THE PILE MUST NOT KILL THE COUNT. cardsAt
    # looks inside whatever it finds near the pile, and
    # getObjects() throws on anything that is not a container -
    # one die resting there took the counter out entirely.
    die = Obj(w, "stray-die", "Yellow")
    die.pos = (float(g.PILE_X), 1.0, pz)
    w.table[die.guid] = die
    g.refreshCounts()
    drain(w)
    want("a die resting on the pile does not stop the count",
         by["Credit Record"].text, "CREDITS  3 / %d" % goal)
    want("...and does not print a red line either",
         w.errors[:2], [])
    w.table.pop(die.guid)
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


def char_bag_assertions():
    """Cycling characters with the BAG refusing puts, which lost half.

    Jon, 2026-11-12: "when cycling heroes, sometime the card stays on
    the table. Other times it goes back to the bag." It did, and
    putHome was the one doing it - it always scheduled a look six
    frames after posting a card, and re-posted whatever was out under
    that GUID. showChar files the character that is out and then deals
    from the same stack, so a refused put left a chain alive across the
    deal and the chain filed the card the player had just asked for.

    SOMETIMES, because six characters live on three cards: every other
    press is a flip of the card already out, and only those presses
    re-deal the GUID a chain is holding. NAP and AoS lost 3 of 8
    presses here, the finale 5 of 12.

    WHY NEITHER OF THE TWO BLOCKS ABOVE SAW IT. choice_assertions
    walks this same cycle and does assert one character card is out
    after every press - with no refusal modelled at all, so no chain
    ever outlives anything. gather_assertions walks it with every
    container put refused, and counts the character cards wherever
    they are, on the table OR in the bag, because with the deck
    unbuildable that is the only honest count. A card filed instead of
    dealt passes both.

    SO THIS ONE ASKS WHERE THE CARD IS, at the position CHAR_HOME
    gives for that game, and it asks it after every single press
    rather than at the end of the walk.
    """
    for which, deck_name in (("NAP", "Apprentices"),
                             ("AoS", "Technicians"),
                             ("IMP", "Imposters (A / B)")):
        for lossy in (3, 2):
            w, g = start("Standard", 0, Panel())
            {"NAP": g.setupNAP, "AoS": g.setupAoS,
             "IMP": g.setupImposter}[which]()
            drain(w)
            one = str(g.CARD_NAME[deck_name]) if g.CARD_NAME[deck_name] \
                else deck_name
            n = len(list(g.CHAR_LIST[which].values()))
            hx, hz = [float(v) for v in g.CHAR_HOME[which].values()]
            w.lossy = lossy
            at_home, named, dealt = [], [], []
            for _ in range(n + 2):
                g.btnChar()
                drain(w)
                # The button names the character it has just dealt, so
                # the card that should be out is read off the script's
                # own table rather than written down here.
                a = g.charOf(which)
                want_card = "%s %d" % (one, int(a.card))
                home = [o.name for o in w.table.values()
                        if of_family(o.name, one)
                        and abs(o.pos[0] - hx) < 1.0
                        and abs(o.pos[2] - hz) < 1.0]
                at_home.append(len(home))
                named.append(home == [want_card])
                dealt.append(want_card)
            w.lossy = 0
            drain(w)
            tag = "%s, bag dropping 1 put in %d" % (which, lossy)
            want("%s: a character is on the table after every press"
                 % tag, sorted(set(at_home)), [1])
            want("...and %s it is the one the button names" % tag,
                 sorted(set(named)), [True])
            # AND THE WALK STILL GOES ROUND. A fix that stopped filing
            # anything would pass both of the above and leave the cycle
            # stuck on one card.
            want("...and %s the walk still reaches every character"
                 % tag, len(set(dealt)), n // 2)
            # AND NOTHING IS LOST OR DUPLICATED. The cards are counted
            # wherever they are: the deck is whole in the bag by now,
            # bar the one on the table.
            box = {"NAP": "NAP", "AoS": "AoS", "IMP": "NRJ"}[which]
            want("...and %s still has every character card" % tag,
                 out(w, deck_name) + inbag(w, box, one, deck_name),
                 {"NAP": 3, "AoS": 3, "IMP": 5}[which])


def carry_assertions():
    """The carry-forward bag is furniture, not a box.

    Jon asked for a yellow bag to keep the cards he is carrying into
    the next game of the campaign (2026-11-12). Where it sits and what
    colour it is are checked in generator/check_app_sync.py, which
    reads the save; what matters HERE is the two behaviours:

      PACK UP MUST NOT TOUCH IT. packable() answers with the box an
      object belongs in, and this bag belongs in none - so Pack up
      neither stows it nor lists it among the things left on the table.
      A bag that got itself reported every single time would train the
      player to ignore that message, which is the one message Pack up
      has.

      AND settle() MUST. The mat and the four boxes are unlocked on
      load and dropped onto the rail to find their resting height; a
      bag left out of that list hangs above it. This is the one line of
      the script that is allowed to know the bag's GUID.
    """
    w, g = start("Standard", 0, Panel())
    carry = [o for o in w.byguid.values()
             if (o.name or "").startswith("CARRY")]
    want("the carry-forward bag is in the world", len(carry), 1)
    if not carry:
        return
    bag = carry[0]
    want("...and Pack up has no home for it", g.packable(bag), None)
    want("...and it holds nothing to start with", len(bag.kids), 0)
    # SETTLE TOUCHES IT. Unlocked by hand first, because the save ships
    # it locked: settle unlocks every object in its list and locks them
    # again two seconds later, so a bag it skipped stays unlocked.
    bag.locked = False
    g.settle()
    drain(w)
    want("...and settle() drops it onto the rail with the others",
         bag.locked, True)
    # AND IT IS NOT ONE OF BOX. deckOut, putHome and packUp all work
    # through that table, so this is the line that keeps the carried
    # cards carried.
    want("...and it is not one of the four boxes",
         bag.guid in [str(v) for v in g.BOX.values()], False)
    # AND IT SURVIVES A SETUP WITH CARDS IN IT, which is not the same
    # claim as any of the three above - and is the one that was false.
    #
    # packable() answers boxFor(), and boxFor does not ask BOX. It asks
    # what is INSIDE the object, and homeBox(firstCard(bag)) is the NRJ
    # box for a bag holding a Research Note. So unmix() called every
    # carried card a stray and took all but the last one out onto the
    # felt, where the pack-up passes filed them into the game boxes -
    # and packable() handed Pack up the NRJ box for the CARRY BAG
    # ITSELF.
    #
    # EVERY CHECK OF THIS PASSED, the three above included, because
    # every one of them asked of an EMPTY bag: firstCard is nil then,
    # so there was nothing to look up and no home to find. Empty is the
    # one state this bag is never in when any of it matters.
    w, g = start("Standard", 0, Panel())
    bag = carry_stock(w, {"Research Note": 2, "Backdoor Routine": 1})
    want("...and Pack up has no home for it with cards IN it",
         g.packable(bag), None)
    before = sorted(c.name for c in bag.kids)
    g.packUp(False)
    drain(w)
    want("...and a Pack up leaves what is in it alone",
         sorted(c.name for c in bag.kids), before)
    want("...and does not report it as something left on the table",
         [m for m in w.said if "CARRY" in m], [])


def carry_bag(w):
    """The carry-forward bag. It is furniture, so it is not on w.table."""
    for o in w.byguid.values():
        if (o.name or "").startswith("CARRY"):
            return o
    return None


def carry_stock(w, cards):
    """Carry cards forward: {card name: how many}, into the carry bag.

    OUT OF THE DECK THEY SHIP IN, never spawned. A card the save does
    not have is a card no census can balance, and balancing the census
    over every family is most of what pool_assertions asserts.
    """
    bag = carry_bag(w)
    for one, n in sorted(cards.items()):
        moved = 0
        for box in w.byguid.values():
            if not box.bag or box is bag:
                continue
            for d in list(box.kids):
                for c in list(d.kids):
                    if moved < n and of_family(c.name, one):
                        d.kids.remove(c)
                        bag.kids.append(c)
                        moved += 1
        if moved != n:
            raise RuntimeError("only %d of %d %s to carry" % (moved, n, one))
    return bag


def pool_assertions():
    """What the Imposter setup retains, and where it reads it from.

    Jon, 2026-11-13: "fix the imposter scenario so it checks for cards
    in the yellow bag during setup. Otherwise, select the correct
    number of cards from each missing deck."

    A Tier III card you CLAIMED is retained and reduces an Exhibit's
    Target by 2; one you never claimed is a candidate and answers
    nothing. Nothing printed on a card says which it is, so the carry
    bag says it - and a family the bag has nothing of is dealt its cap
    at random, which is the rulebook's standalone mode. Before this the
    setup dealt all three decks out of the NRJ box and never looked in
    the bag at all: a carried card stayed in the bag and its deck came
    to the table two cards short with nothing saying so.

    BY NAME, NOT BY COUNT, and that is the point of this block. Three
    Opportunities dealt at random are three Opportunities, so every
    count here passes on the old behaviour for the full-campaign case.
    What cannot pass is "the retained cards are the ones that were in
    the bag".
    """
    cases = (("nothing carried", {}),
             ("two Notes carried", {"Research Note": 2}),
             ("a full campaign", {"Research Note": 2,
                                  "Devious Opportunity": 3,
                                  "Backdoor Routine": 2}),
             ("one Note, two Routines, no Opportunity",
              {"Research Note": 1, "Backdoor Routine": 2}),
             ("a whole deck in the bag", {"Research Note": 6}),
             ("over the cap", {"Devious Opportunity": 5}))
    for tag, cards in cases:
        w, g = start("Standard", 3, Panel())
        bag = carry_stock(w, cards)
        was = {}
        for c in bag.kids:
            was.setdefault(c.name.rsplit(" ", 1)[0], []).append(c.name)
        g.setupImposter()
        drain(w)
        tier, side = float(g.ROW_TIER), float(g.ROW_SIDE)
        pop = census(w)
        for p in g.IMP_POOL.values():
            lab, cap, laid = str(p[1]), int(p[2]), int(p[4])
            one = str(g.CARD_NAME[lab]) if g.CARD_NAME[lab] else lab
            mine = sorted(was.get(one, []))
            ret = sorted(o.name for o in w.table.values()
                         if of_family(o.name, one)
                         and abs(o.pos[2] - tier) < 0.1)
            cand = sum(len(o.kids) or 1 for o in w.table.values()
                       if (o.name == lab or of_family(o.name, one))
                       and abs(o.pos[2] - side) < 0.1)
            left = sum(1 for c in bag.kids if of_family(c.name, one))
            if mine:
                # THE CARDS THEMSELVES. This is the assertion the old
                # setup fails and no count does.
                want("%s: %s retained are the ones out of the bag"
                     % (tag, lab), ret, mine)
            else:
                want("%s: %s is dealt its cap of %d at random"
                     % (tag, lab, cap), len(ret), cap)
            want("...and %s the rest of %s are candidates" % (tag, lab),
                 cand, laid - len(ret))
            want("...and %s no %s is left in the carry bag" % (tag, lab),
                 left, 0)
            # AND ALL SIX EXIST, ONCE EACH, wherever they are. A setup
            # that dealt the deck AND emptied the bag would put eight
            # Research Notes on the table and pass every count above.
            want("...and %s every one of the %d %s exists exactly once"
                 % (tag, laid, lab),
                 sorted((i, pop.get("%s %d" % (one, i), 0))
                        for i in range(1, laid + 1)
                        if pop.get("%s %d" % (one, i), 0) != 1), [])
        # AND THE ROW IS ON THE TABLE. Over the cap the row is longer
        # than the slots, and poolSlots squeezes the pitch rather than
        # dealing cards over the edge of the felt.
        edge = float(g.FELT.x1) - 1.0
        want("%s: the retained row stays on the felt" % tag,
             sorted(round(o.pos[0], 2) for o in w.table.values()
                    if abs(o.pos[2] - tier) < 0.1
                    and abs(o.pos[0]) > edge), [])

    # THE SLOTS ARE FIXED AT THE CAPS, and this is why that matters:
    # make_template.py paints the felt from the footprints this setup
    # leaves, so a row centred on however many you happened to carry
    # would land in its own printed boxes in the seven-card case and in
    # no other. A full campaign and a standalone deal fill the same
    # seven places.
    rows = []
    for cards in ({"Research Note": 2, "Devious Opportunity": 3,
                   "Backdoor Routine": 2}, {}):
        w, g = start("Standard", 3, Panel())
        carry_stock(w, cards)
        g.setupImposter()
        drain(w)
        rows.append(sorted(round(o.pos[0], 2) for o in w.table.values()
                           if abs(o.pos[2] - float(g.ROW_TIER)) < 0.1))
    want("a full campaign fills the same slots a standalone deal does",
         rows[0], rows[1])
    want("...and there are as many of them as the caps allow",
         len(rows[0]), sum(int(p[2]) for p in g.IMP_POOL.values()))

    # AND THE SETUP TAKES ONLY THE RESEARCH POOL OUT OF THE BAG.
    # Whatever else you keep in there is none of its business.
    w, g = start("Standard", 3, Panel())
    bag = carry_stock(w, {"Experimental Protocol": 1, "Research Note": 2})
    g.setupImposter()
    drain(w)
    want("the Imposter setup takes only the Research Pool out of the bag",
         sorted(c.name for c in bag.kids), ["Experimental Protocol 1"])


def gather_assertions():
    """A refused merge must not leave a card lying in the band.

    THE BUG, AT THE TABLE (Jon, 2026-11-12): cycling the hero card in
    NAP, AoS or the Imposter scenario left blank cards at the bottom
    edge, one more for every press. showChar files the card that is out
    and then has deckOut gather it straight back, and deckOut's two
    gather loops put ONCE and never looked - so a put TTS dropped left
    the card at OFF, face down and wearing a back.

    REFUSED EVERY TIME, and it has to be every time. At one in two the
    stub never happens to refuse the single put deckOut makes per press,
    so the test passes against the old code as well - three mutations
    proved exactly that. Refusing all of them also drives the deck down
    to a single card in the bag, which is the stale-handle case moveN
    has been bitten by twice, so the fix has to answer for that too:
    eight tries at the receiver, re-acquiring it after each one, then
    home to its own bag.

    EVERY BLOCK THAT TURNS REFUSAL ON NOW REFUSES DECKS TOO - the dial
    that exempted them is gone, though the default is still no refusal
    at all - so this is no longer the only place a refused merge
    happens, and the three checks below are weak on their
    own: only a mutation that stops gatherInto putting at all fails
    them, and that one fails 355 others with it. What is still theirs
    is the LIMIT CASE, and it took two loads to reach it:

      ONE IN ONE refuses every put anywhere, which is what the button
      met at the table. It does NOT reach putHome, because a bag that
      refuses everything is no escape either - dropping putHome(c)
      from gatherInto changed no assertion at all under this load, so
      the claim that used to stand here was wrong.

      JAMMED refuses every put into the one deck and leaves the bag
      working, which is the only shape in which filing the card is
      the answer. Under it, dropping putHome(c) fails exactly the two
      assertions it should and nothing else.

    THE TWO GATHER LOOPS STILL COVER FOR EACH OTHER HERE, which is
    worth knowing before a green run is read as proof of either.
    Mutating one call site back to a bare putObject leaves the band
    clean under both loads, because the OTHER loop collects the
    straggler off the table at the next press - what catches each of
    them is repeat_assertions (12 failures) and finf_assertions (8),
    not this function.
    """
    for which, setup, deck_name in (("NAP", "setupNAP", "Apprentices"),
                                    ("AoS", "setupAoS", "Technicians"),
                                    ("IMP", "setupImposter",
                                     "Imposters (A / B)")):
        # TWO LOADS, because they reach different lines. Under the
        # first nothing anywhere takes a put, which is what the button
        # met at the table; under the second ONE deck refuses
        # everything and the bag still works, which is the only way to
        # reach the line where gatherInto stops asking and files the
        # card instead. See the jam in putObject.
        for load, what in (("refused", "every put is refused"),
                           ("jammed", "the deck itself never takes one")):
            w, g = start("Standard", 0, Panel())
            {"NAP": g.setupNAP, "AoS": g.setupAoS,
             "IMP": g.setupImposter}[which]()
            drain(w)
            base = sorted(o.name for o in w.table.values())
            one = str(g.CARD_NAME[deck_name]) if g.CARD_NAME[deck_name] \
                else deck_name
            n = len(list(g.CHAR_LIST[which].values()))
            if load == "refused":
                w.lossy = 1
            else:
                # More presses than the whole cycle can ask for, so the
                # deck never relents.
                w.jam[deck_name] = 500
            for _ in range(n + 2):
                g.btnChar()
                drain(w)
            w.lossy, w.jam = 0, {}
            drain(w)
            offz = float(g.OFF_Z)
            band = sorted(o.name for o in w.table.values()
                          if abs(o.pos[2] - offz) < 3.0)
            want("%s leaves nothing in the staging band when %s"
                 % (which, what), band, [])
            # AND THE CARDS ARE STILL ALL THERE. A fix that swept the band by
            # deleting what it found would pass the one above. Note that it is
            # the DECK that cannot be rebuilt while every put is refused, so
            # the cards are counted wherever they are - on the table or in
            # their bag - rather than expected back in one stack.
            box = {"NAP": "NAP", "AoS": "AoS", "IMP": "NRJ"}[which]
            want("...and %s still has every character card (%s)"
                     % (which, load),
                 out(w, deck_name) + inbag(w, box, one, deck_name),
                 {"NAP": 3, "AoS": 3, "IMP": 5}[which])
            # ...AND NOTHING LANDED SOMEWHERE NEW. Every object out is one
            # the setup had out or a character card; the band check above
            # only looks at one strip of felt.
            extra = sorted(o.name for o in w.table.values()
                           if o.name not in base
                           and not of_family(o.name, one)
                           and o.name != deck_name)
            want("...and %s leaves nothing else lying about (%s)"
                     % (which, load),
                 extra, [])


def main():
    layout_assertions()
    panel_assertions()
    counter_assertions()
    dial_assertions()
    choice_assertions()
    repeat_assertions()
    finf_assertions()
    round_trip_assertions()
    in_the_bag_assertions()
    overlay_assertions()
    bat_assertions()
    aos_assertions()
    chip_face_assertions()
    buff_lock_assertions()
    on_card_assertions()
    pile_assertions()
    landing_assertions()
    markers_home_assertions()
    alt_view_assertions()
    finale_assertions()
    exam_pool_assertions()
    covered_assertions()
    rules_assertions()
    panel_game_assertions()
    gather_assertions()
    char_bag_assertions()
    carry_assertions()
    pool_assertions()
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
            # WHAT THE SETUP SAYS IN CHAT, which is the only account of the
            # deck a player at the table gets - and the one thing the
            # 2026-11-12 Setback change actually broke. At Standard the mod
            # computed `sb - 3` with no floor, so Tier I announced "-1 base";
            # the DECK was right, because moveN(-1) moves nothing, so every
            # assertion below this one passed while the message was wrong.
            # It also under-reported the total: three Following cards arrive
            # and only `sb` base ones can leave, so at sb < 3 the deck holds
            # MORE Setbacks than the difficulty asks for.
            _msg = " ".join(str(m) for m in n.said)
            want(t + " NAP's setup message counts no negative cards",
                 [frag for frag in _msg.split() if frag.startswith("-")
                  and frag[1:2].isdigit()], [])
            # ONE BASE SETBACK OUT PER FOLLOWING SETBACK IN, FLOORED AT NONE.
            # The 4-for-3 swap handed a Setback back at Hard and Nobulous;
            # the floor is the other end of the same rule and it started
            # mattering on 2026-11-12, when Standard went to 2 Setbacks.
            # Three Following cards arrive and only two base ones can
            # leave, so Tier I ADDS a Setback at Standard: 2 becomes 3.
            # That is the tier doing its job - what a tier must never do is
            # hand one back - but it is why the Setback lever is worth
            # nothing from Tier I upward at Easy and Standard.
            base = max(0, sb - 3) if tier >= 1 else sb
            following = 3 if tier >= 1 else 0
            want(t + " NAP Assignment deck", len(deck(n, "Assignment").kids),
                 26 + 6 + base + following)
            want(t + " NAP base Setbacks", inside(n, "Assignment", "Setback"),
                 base)
            want(t + " ...and the message names the Setbacks really dealt",
                 ("+ %d Setbacks" % (base + following)) in _msg, True)
            if tier >= 1:
                want(t + " ...and names the split it dealt",
                     ("(3 Following and %d base)" % base) in _msg, True)
            want(t + " NAP Following Setbacks",
                 inside(n, "Assignment", "Following Setback"), following)
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
