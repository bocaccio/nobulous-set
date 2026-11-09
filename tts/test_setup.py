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

NOT A SUBSTITUTE FOR TTS. lupa bundles Lua 5.5 and Tabletop Simulator runs
MoonSharp, a 5.2 dialect; this proves the script parses and that its card
arithmetic is right, not that TTS will spawn the objects on time. The
sequencer's frame delays are exactly what a stub cannot test, so HANDOFF
step 6 still wants a human at the table.
"""
import io
import json
import os
import random
import sys

import lupa

HERE = os.path.dirname(os.path.abspath(__file__))
SAVE = os.path.join(HERE, "NobulousSet.json")

BAT_SPECIMENS = {"Easy": 5, "Standard": 6, "Hard": 7, "Nobulous": 8}
NAP_SETBACKS = {"Easy": 3, "Standard": 3, "Hard": 4, "Nobulous": 5}


class Obj(object):
    """A deck, a card or a bag. Decks and bags hold other Objs."""

    def __init__(self, world, guid, name, kids=None, bag=False):
        self.world, self.guid, self.name = world, guid, name
        self.kids = list(kids or [])
        self.bag = bag

    def getName(self):
        return self.name

    def getGUID(self):
        return self.guid

    def getQuantity(self):
        # TTS answers -1 for a single card, which is why the Lua has its
        # own count() rather than trusting this.
        return len(self.kids) if self.kids else -1

    def getObjects(self):
        return self.world.lua.table_from(
            [self.world.lua.table_from({"nickname": k.name, "guid": k.guid})
             for k in self.kids])

    def shuffle(self):
        self.world.shuffled.add(self.name)
        self.world.rng.shuffle(self.kids)

    def setLock(self, *a):
        pass

    def setPosition(self, *a):
        pass

    setPositionSmooth = setPosition

    def setRotation(self, *a):
        pass

    setRotationSmooth = setRotation

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
        self.world.table[k.guid] = k
        if "callback_function" in keys and spec["callback_function"] is not None:
            spec["callback_function"](k)
        return k

    def putObject(self, other):
        if other is None:
            raise RuntimeError("putObject(nil) into %r" % self.name)
        self.world.table.pop(other.guid, None)
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
        self.rng = random.Random(7)

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
            decks.append(w.add(Obj(w, d["GUID"], d["Nickname"], cards)))
        w.add(Obj(w, o["GUID"], o["Nickname"], decks, bag=True))
    if not w.table and not w.byguid:
        raise SystemExit("no boxes in %s - run build_mod.py first" % SAVE)
    return w, save["LuaScript"]


def install(lua, w):
    g = lua.globals()
    g.getObjectFromGUID = lambda guid: w.byguid.get(guid)
    g.getAllObjects = lambda: lua.table_from(
        list(w.table.values()) + [o for o in w.byguid.values() if o.bag])
    g.broadcastToAll = lambda msg, col=None: w.said.append(msg)
    wait = lua.eval("{}")
    wait.frames = lambda fn, n=1: fn()      # the stub cannot test timing
    wait.time = lambda fn, t=0: fn()
    g.Wait = wait
    g.self = None                            # no panel, so refreshPanel returns


def run(difficulty, tier, which):
    lua = lupa.LuaRuntime(unpack_returned_tuples=True)
    w, src = build(lua)
    install(lua, w)
    lua.execute(src)
    g = lua.globals()
    g.STATE.difficulty = difficulty
    g.STATE.tier = tier
    {"BAT": g.setupBAT, "NAP": g.setupNAP,
     "AoS": g.setupAoS, "IMP": g.setupImposter}[which]()
    return w


def deck(w, name):
    hit = [o for o in w.table.values() if o.name == name]
    return hit[0] if hit else None


def inside(w, deckname, label):
    """Cards whose name starts with `label`, inside the named deck."""
    d = deck(w, deckname)
    return len([c for c in (d.kids if d else []) if c.name.startswith(label)])


def out(w, label):
    """CARDS of that deck on the table, not counting the container.

    spread() deals n-1 cards and leaves the last inside the deck object,
    so counting table objects by name counts the container AND the card
    still in it - which read as 7 Research Notes the first time.
    """
    n = 0
    for o in w.table.values():
        if o.name.startswith(label):
            n += len(o.kids) if o.kids else 1
    return n


FAIL = []
RAN = [0]


def want(tag, got, exp):
    # Counted, not computed: the printed total was 4 * 4 * 21 and went
    # stale the moment a twenty-second assertion was added.
    RAN[0] += 1
    if got != exp:
        FAIL.append("%s: got %r, want %r" % (tag, got, exp))


def main():
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
                 inside(w, "Upgrades", "Specimens"), spec)
            want(t + " BAT ordinary Upgrades in it",
                 inside(w, "Upgrades", "Upgrades "), 16 - 6 if tier >= 2 else 16)
            want(t + " BAT Modifications in it",
                 inside(w, "Upgrades", "Unauthorized Modifications"),
                 6 if tier >= 2 else 0)
            want(t + " BAT Protocol dealt",
                 out(w, "Experimental Protocols"), 1 if tier >= 1 else 0)
            want(t + " BAT Research Notes out",
                 out(w, "Research Notes"), 6 if tier >= 3 else 0)
            want(t + " BAT shuffled the Experiments",
                 "Encounters" in w.shuffled, True)

            n = run(lvl, tier, "NAP")
            want(t + " NAP Assignment deck", len(deck(n, "Tasks").kids),
                 26 + 6 + sb)
            # One base Setback out per Following Setback in - the 4-for-3
            # swap handed a Setback back at Hard and Nobulous.
            want(t + " NAP base Setbacks", inside(n, "Tasks", "Setbacks"),
                 sb - 3 if tier >= 1 else sb)
            want(t + " NAP Following Setbacks",
                 inside(n, "Tasks", "Following Setbacks"), 3 if tier >= 1 else 0)
            want(t + " NAP Imposter Tasks",
                 inside(n, "Tasks", "Imposter Tasks"), 4 if tier >= 2 else 0)
            want(t + " NAP base Tasks", inside(n, "Tasks", "Tasks "),
                 26 - 4 if tier >= 2 else 26)
            want(t + " NAP Opportunities",
                 inside(n, "Tasks", "Opportunities "), 0 if tier >= 3 else 6)
            want(t + " NAP Devious Opportunities",
                 inside(n, "Tasks", "Devious Opportunities"),
                 6 if tier >= 3 else 0)
            want(t + " NAP one FINF card", out(n, "FINF"), 1)

            a = run(lvl, tier, "AoS")
            prog = [o for o in a.table.values()
                    if o.name.endswith("Programs") and o.name != "Advanced Programs"]
            want(t + " AoS Program deck", sum(len(p.kids) for p in prog), 8)
            want(t + " AoS Limitation deck", len(deck(a, "Limitations").kids),
                 12 if tier >= 2 else 6)
            want(t + " AoS Corrupted in it",
                 inside(a, "Limitations", "Corrupted Limitations"),
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

    print("%d assertions over 64 setups, %d failed" % (RAN[0], len(FAIL)))
    for f in FAIL:
        print("  -", f)
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
