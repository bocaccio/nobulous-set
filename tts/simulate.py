"""Run every setup against a stand-in for the TTS object API.

The dealing code cannot be tried without launching the game, and three bugs
got as far as the table before this existed: the setup panel being swept into
the Card Bank on Start Game, and takeObject being called on a one-card deck by
both the Time Slot and the Following Setbacks paths.

    python simulate.py

Prints one line per game/difficulty/tier combination. sim.lua fires Waits
immediately, so this checks what happens, not when.
"""
import io, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from decks import DECKS

COMBOS = [('BAT', 'Easy', (0, 0, 0)), ('BAT', 'Standard', (1, 0, 0)),
          ('BAT', 'Hard', (1, 1, 1)), ('NAP', 'Standard', (0, 0, 0)),
          ('NAP', 'Standard', (1, 0, 0)), ('NAP', 'Standard', (1, 1, 1)),
          ('AoS', 'Easy', (0, 0, 0)), ('AoS', 'Standard', (0, 1, 0)),
          ('AoS', 'Hard', (1, 1, 1)), ('IMP', 'Standard', (0, 0, 0))]


def run(lupa, src, sim, game, diff, tiers):
    L = lupa.LuaRuntime()
    L.execute(sim)
    L.execute(src)
    for d in DECKS:
        L.execute("table.insert(BANKOBJ.contents, mkObj(%r, %d, 'Deck'))"
                  % (d['label'], d['count']))
    for c in ('Program Cover', 'Advanced Cover'):
        L.execute("table.insert(BANKOBJ.contents, mkObj(%r, 1, 'Tile'))" % c)
    L.execute("PANEL=mkPanel('Control Panel') SETUP=mkPanel('Setup Panel') BANK=BANKOBJ")
    L.execute("STATE.game=%r STATE.difficulty=%r" % (game, diff))
    for i, on in enumerate(tiers, 1):
        if on:
            L.execute("STATE.tiers[%d]=true" % i)
    L.execute('startGame()')

    n = int(L.eval('#ERRORS'))
    errs = [str(L.eval('ERRORS[%d]' % i)) for i in range(1, n + 1)]
    dealt = int(L.eval('#OBJECTS'))
    banked = [str(L.eval('BANKOBJ.contents[%d].nick' % i))
              for i in range(1, int(L.eval('#BANKOBJ.contents')) + 1)]
    for panel in ('Setup Panel', 'Control Panel'):
        if panel in banked:
            errs.append('%s was swept into the Card Bank' % panel)
    return errs, dealt


def main():
    import lupa
    src = json.load(open(os.path.join(HERE, 'NobulousSet.json'),
                         encoding='utf-8'))['LuaScript']
    sim = io.open(os.path.join(HERE, 'sim.lua'), encoding='utf-8').read()
    bad = 0
    for game, diff, tiers in COMBOS:
        errs, dealt = run(lupa, src, sim, game, diff, tiers)
        tag = '%s %-8s %s' % (game, diff,
                              ''.join('123'[i] if t else '-'
                                      for i, t in enumerate(tiers)))
        print('  %-22s %2d dealt   %s' % (tag, dealt, '; '.join(errs) or 'ok'))
        bad += len(errs)
    print('\n%d problems' % bad)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
