"""WHY THREE ASSEMBLIES IN THREE ROUNDS IS NOT REACHABLE, and what each
lever is worth. Measured 2026-11-24, against the Assembly rules as handed
over (with the offer of six and the colour floor already in, which only
affect whether a setup is buildable AT ALL - see aosbuild.py).

THE HEADLINE: 2.7% at Standard, against 52.0% for the AoS this replaced.
The finale is not the problem - 94% of the games that reach it win it.
Almost nothing reaches it: 5.5% of Standard games build three Assemblies.

THE MECHANISM is that success removes capacity. An installed Program is
held out of the deck, so every clean run makes the next round shorter and
leaves it made of the Programs that FAILED - which are Overheated by then,
with a raised Target on the marked element. Round 1 is eight cards at full
strength; round 3 is whatever could not manage a clean run twice.

Three rounds therefore have to produce six to nine clean runs out of a
pool that shrinks every time one lands, while two Health absorbs every
Catastrophic Failure along the way. The numbers below are the measurement,
not an argument.
"""
import collections
import random
import sys

sys.path.insert(0, ".")
import aos


def survey(level, n=3000, seed=7, **dials):
    old = {k: getattr(aos, k) for k in dials}
    for k, v in dials.items():
        setattr(aos, k, v)
    try:
        rng = random.Random(seed)
        comp = aos.LEVELS[level]
        won = 0
        built = collections.Counter()
        runs = installs = 0
        dead_hp = dead_line = dead_fin = 0
        for _ in range(n):
            g = aos.Game("Specialized", rng, "none", composition=comp)
            w = g.play()
            won += 1 if w else 0
            b = len(g.built())
            built[b] += 1
            runs += g.ran
            installs += g.installed
            if g.hp <= 0:
                dead_hp += 1
            elif b < 3:
                dead_line += 1
            elif not w:
                dead_fin += 1
        return dict(win=100.0 * won / n, built3=100.0 * built[3] / n,
                    runs=runs / float(n), installs=installs / float(n),
                    hp0=100.0 * dead_hp / n, deadline=100.0 * dead_line / n,
                    finale=100.0 * dead_fin / n)
    finally:
        for k, v in old.items():
            setattr(aos, k, v)


LEVELS = ("Easy", "Standard", "Hard", "Nobulous")


def line(label, rows):
    print("%-38s %s" % (label, " ".join("%7.1f%%" % r["win"] for r in rows)))


def main():
    print("AoS Assembly rules - where the games go")
    print()
    print("%-38s %8s %8s %8s %8s" % ("", *LEVELS))
    base = [survey(l) for l in LEVELS]
    line("AS HANDED OVER: 3 rounds, 3 Assemblies", base)
    print()
    print("  Standard, in detail:")
    b = base[1]
    print("    Programs run per game        %5.2f" % b["runs"])
    print("    Programs installed per game  %5.2f  (6 to 9 are needed)" % b["installs"])
    print("    built all three              %5.1f%%" % b["built3"])
    print("    lost to Health reaching 0    %5.1f%%" % b["hp0"])
    print("    lost to the three-round deadline %5.1f%%" % b["deadline"])
    print("    lost in the finale           %5.1f%%" % b["finale"])
    print()
    print("  LEVERS, each on its own:")
    print("%-38s %8s %8s %8s %8s" % ("", *LEVELS))
    # An installed Program is NOT held out of the deck: it keeps running,
    # and the deck stops shrinking as you succeed.
    line("installed Programs stay in the deck",
         [survey(l, KEEP_INSTALLED=True) for l in LEVELS])
    # Four rounds rather than three.
    line("four rounds", [survey(l, ROUNDS=4) for l in LEVELS])
    line("five rounds", [survey(l, ROUNDS=5) for l in LEVELS])
    # Build two Assemblies rather than three; the finale is then 2 stages.
    line("build two, not three", [survey(l, BUILD_TARGET=2) for l in LEVELS])
    # The finale allows two failed elements rather than one.
    line("finale allows 2 failed elements",
         [survey(l, FINALE_ALLOWED=2) for l in LEVELS])
    print()
    print("  AND TOGETHER, the combination that lands nearest the old ladder:")
    print("%-38s %8s %8s %8s %8s" % ("", *LEVELS))
    line("stay in deck + four rounds",
         [survey(l, KEEP_INSTALLED=True, ROUNDS=4) for l in LEVELS])
    line("stay in deck + four rounds + 2 allowed",
         [survey(l, KEEP_INSTALLED=True, ROUNDS=4, FINALE_ALLOWED=2)
          for l in LEVELS])
    print()
    print("  AND THE ONE WORD THAT DECIDES ALL OF IT: what \"complete a")
    print("  Program\" has to mean before it can be installed. The handoff")
    print("  says \"after a clean run\", and clean is AoS's own word for the")
    print("  Program Reward - no failed element at all. Charging the same")
    print("  failure twice, once for the Reward and once for the slot, is")
    print("  the whole difference between a broken game and a good one:")
    print("%-38s %8s %8s %8s %8s" % ("", *LEVELS))
    for label, req in (("no failed element (as written)", "clean"),
                       ("at most one failed element", "nocat"),
                       ("just finishing the Program", "any")):
        line(label, [survey(l, INSTALL_REQUIRES=req) for l in LEVELS])
    print()
    print("  For reference, the AoS this replaced measured 60.6 / 52.0 /")
    print("  43.6 / 35.6 for a player who triages. \"At most one failed")
    print("  element\" lands just under it with the spread intact, and")
    print("  leaves all three failure modes live: at Standard, 29.9% lose")
    print("  to the deadline, 23.4% to Health, 4.8% in the finale.")


if __name__ == "__main__":
    main()
