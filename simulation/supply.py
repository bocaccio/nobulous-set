"""Can the campaign's cards actually be saved, and does standalone match?

    python supply.py            # ~1200 games per game per difficulty

The Imposter Scenario is played with an 18-card Research Pool, 6 cards from
each of the three games. imposter.py audits what the finale does with that
pool; this audits whether the pool can be assembled at all, and whether the
standalone draw is the same hand a real campaign produces.

Four things are checked.

  SUPPLY     are there enough printed cards to make each game's 6? Counted
             from generator/build_*.py, which is the authoritative text.
  BANKING    what each game actually leaves on the table when it is won,
             measured by running the game and reading the hand-off. BAT is
             the one with any doubt in it: NAP always faces exactly 3 Final
             Exams and AoS always faces exactly 3 Advanced Programs, but
             BAT retains "up to 3 of the Upgrade cards the Rats earned".
  STANDALONE rules/nrj.html's standalone mode draws 3 retained and 3
             Candidates per game at random, which always banks the maximum.
             A campaign may bank less. This measures the gap.
  CARRY      whether the three carry-forward rules and the Research Pool
             table in rules/nrj.html agree with each other. They did not.
"""
import collections
import random
import re
import statistics
import sys
import os

import aos
import bat
import nrj

GAMES = 1200
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEVELS = ("Easy", "Standard", "Hard", "Nobulous")


# ---------------------------------------------------------------------------
def printed_counts():
    """Card counts read off the generators."""
    out = {}
    p = os.path.join(ROOT, "generator", "build_bat.py")
    t = open(p, encoding="utf-8").read()
    for name in ("UPGRADES", "SPECIMENS", "EXPERIMENTS"):
        m = re.search(r"^%s = \[(.*?)\n\]" % name, t, re.S | re.M)
        out["BAT " + name] = len(re.findall(r'^ {4}\("', m.group(1), re.M))
    p = os.path.join(ROOT, "generator", "build_nap.py")
    t = open(p, encoding="utf-8").read()
    m = re.search(r"^EXAMS = \[(.*?)\n\]", t, re.S | re.M)
    out["NAP EXAMS"] = len(re.findall(r'^ \("', m.group(1), re.M))
    p = os.path.join(ROOT, "generator", "aos.py")
    t = open(p, encoding="utf-8").read()
    m = re.search(r"^ADVANCED = \[(.*?)\n\]", t, re.S | re.M)
    out["AoS ADVANCED"] = len(re.findall(r"^ {4}\(", m.group(1), re.M))
    return out


# ---------------------------------------------------------------------------
def bat_banking(level, games, seed=4):
    """Upgrades the Rats hold when the battle begins, on wins only.

    rules/bat.html: "retain up to 3 of the Upgrade cards the Rats earned -
    the ones they held when the battle began - of which at most 1 may be a
    Specimen... Cards spliced into the Tyrant are candidates; fill any
    remaining slots from those, so BAT contributes 6 in total."
    """
    rng = random.Random(seed)
    held, spec, splices, hands = [], [], [], []
    wins = played = 0
    for _ in range(games):
        g = bat.Game(level, rng, card_effects=True, sides="random")
        snap = {}
        real = g.start_battle

        def start(g=g, real=real, snap=snap):
            cards = [u for r in g.rats for u in r.upgrades]
            snap["n"] = len(cards)
            snap["s"] = sum(1 for u in cards if u.name in bat.SPECIMEN_NAMES)
            snap["sp"] = len(g.splices)
            return real()

        g.start_battle = start
        won = g.play()
        played += 1
        if not (won and snap):
            continue
        wins += 1
        held.append(snap["n"])
        spec.append(snap["s"])
        splices.append(snap["sp"])
        # The hand a player would keep: one Specimen if there is one, then
        # Upgrades, to a maximum of three cards.
        keep = ([5] if snap["s"] else []) + [3] * max(0, snap["n"] - snap["s"])
        hands.append(keep[:3])
    return dict(winrate=100.0 * wins / played, held=held, spec=spec,
                splices=splices, hands=hands)


def aos_banking(level, games, seed=4):
    """Stable / Overheated of the 3 Advanced Programs faced, on wins only.

    rules/aos.html: "Advanced Program 1 begins Stable. The next begins
    Overheated if this one ended in Catastrophic Failure, and Stable
    otherwise." So the first is never Overheated, and the model's flat 50%
    was never right.
    """
    rng = random.Random(seed)
    hands = []
    wins = played = 0
    for _ in range(games):
        g = aos.Game("Specialized", rng, composition=aos.LEVELS[level])
        seq = []
        real = g.run_program

        def run(kind, pid, face, *a, **k):
            if kind == "Advanced":
                seq.append(face == "front")       # True = Stable
            return real(kind, pid, face, *a, **k)

        g.run_program = run
        won = g.play()
        played += 1
        if won and len(seq) == 3:
            wins += 1
            hands.append(list(seq))
    return dict(winrate=100.0 * wins / played, hands=hands)


# ---------------------------------------------------------------------------
def finale(games, bat_hands=None, aos_hands=None, seed=11):
    """Run the finale, drawing each game's hand-off from a measured pool."""
    rng = random.Random(seed)
    wins = 0
    for _ in range(games):
        bc = rng.choice(bat_hands) if bat_hands else None
        ac = rng.choice(aos_hands) if aos_hands else None
        if nrj.Game("campaign", rng, bat_cards=bc, aos_cards=ac).play():
            wins += 1
    return 100.0 * wins / games


# ---------------------------------------------------------------------------
def main(games=GAMES):
    print("CAN THE CAMPAIGN'S CARDS BE SAVED? %d games per game per level"
          % games)
    print()

    print("1. SUPPLY - printed cards against what the rules ask for")
    print()
    counts = printed_counts()
    need = [("NAP", "3 Final Exams faced + 3 unused", counts["NAP EXAMS"], 6),
            ("AoS", "3 Advanced Programs faced + 3 unused",
             counts["AoS ADVANCED"], 6),
            ("BAT", "up to 3 Upgrades held + Splices to fill 6",
             counts["BAT UPGRADES"] + counts["BAT SPECIMENS"], 6)]
    for game, what, have, want in need:
        print("   %-5s %-40s %2d printed, needs %d  %s"
              % (game, what, have, want, "ok" if have >= want else "SHORT"))
    print()
    print("   The Tyrant always carries exactly 5 Splices, so BAT's Candidate")
    print("   supply from the Tyrant alone is 5: 3 retained needs 3 of them,")
    print("   1 retained needs 5, and a win with NO retained Upgrade would")
    print("   need 6 and come up one short. That did not happen in any win")
    print("   measured below, but the rules permit it - winning the battle")
    print("   having completed no Experiments - and they used to be silent")
    print("   on it. rules/bat.html now fills from unused Upgrade cards when")
    print("   the Splices do not cover it, which is the source Splicing")
    print("   Machine Malfunction already uses to top the Tyrant up to 5.")
    print()

    print("2. BANKING - what each game leaves on the table when it is won")
    print()
    print("   BAT: Upgrades the Rats hold when the battle begins")
    print("   %-10s %7s %7s %8s %9s %9s"
          % ("", "win", "mean", "3+ held", "Specimen", "2 Spec"))
    bat_hands = {}
    for level in LEVELS:
        r = bat_banking(level, games)
        bat_hands[level] = r["hands"]
        h, sp = r["held"], r["spec"]
        print("   %-10s %6.1f%% %7.2f %7.0f%% %8.0f%% %8.0f%%"
              % (level, r["winrate"], statistics.mean(h),
                 100.0 * sum(1 for x in h if x >= 3) / len(h),
                 100.0 * sum(1 for x in sp if x >= 1) / len(sp),
                 100.0 * sum(1 for x in sp if x >= 2) / len(sp)))
        assert set(r["splices"]) == {5}, "the Tyrant should always hold 5"
    print()
    print("   So the three retained slots fill on nearly every win, and a")
    print("   Specimen - worth -5 against an Upgrade's -3 - is there to take")
    print("   almost always. The 'at most 1 Specimen' cap is the binding")
    print("   rule, not the supply: a second Specimen is on the table in the")
    print("   last column's share of wins and has to be left behind.")
    print()
    print("   AoS: Stable / Overheated of the 3 Advanced Programs faced")
    print("   %-10s %7s %9s %28s" % ("", "win", "Overheat", "commonest hand"))
    aos_hands = {}
    for level in aos.LEVEL_NAMES:
        r = aos_banking(level, games)
        aos_hands[level] = r["hands"]
        flat = [s for hand in r["hands"] for s in hand]
        common = collections.Counter(tuple(h) for h in r["hands"]).most_common(1)
        label = " / ".join("Stable" if s else "Overheated" for s in common[0][0])
        print("   %-10s %6.1f%% %8.0f%% %28s"
              % (level, r["winrate"],
                 100.0 * sum(1 for s in flat if not s) / len(flat), label))
    print()
    print("   The first Advanced Program is Stable by rule, so a retained AoS")
    print("   hand can never be all-Overheated and the finale's flat 50/50")
    print("   was never reachable. Stable is -4 and cannot be discarded to")
    print("   avoid; Overheated is -2 and can - so the real hand reduces more")
    print("   and avoids less than the model assumed.")
    print()
    print("   NAP: nothing to measure. final_exam draws pool[:3] from 12")
    print("   printed exams, so exactly 3 are faced and retained in every")
    print("   game that reaches the exam, and 9 remain to draw 3 Candidates")
    print("   from. NAP's contribution is 3 retained + 3 Candidates always.")
    print()

    print("3. STANDALONE AGAINST A REAL CAMPAIGN HAND")
    print()
    print("   Standalone draws 3 retained and 3 Candidates per game at")
    print("   random, so it banks the maximum every time. These rows feed")
    print("   the finale the hands the games above actually produced.")
    print()
    print("   %-34s %8s" % ("", "finale"))
    print("   %-34s %8.1f%%" % ("standalone, as printed", finale(games * 3)))
    for level in LEVELS:
        ao = level if level in aos_hands else "Standard"
        print("   %-34s %8.1f%%"
              % ("campaign hand-off, %s" % level,
                 finale(games * 3, bat_hands[level], aos_hands[ao])))
    print()

    print("4. CARRY-FORWARD RULES - do the four documents agree?")
    print()
    # Every document that says where a knocked-out Rat's Upgrades go. The
    # first version of this check read nrj.html only, which let the same
    # stale rule sit inside bat.html three paragraphs from the rule it
    # contradicted.
    STALE = ("Upgrades held by surviving Rats",
             "its Upgrades become candidates",
             "Upgrades become candidates rather than retained")
    found = []
    for doc in ("bat.html", "nrj.html"):
        text = open(os.path.join(ROOT, "rules", doc), encoding="utf-8").read()
        for phrase in STALE:
            if phrase in text:
                found.append((doc, phrase))
    stale = bool(found)
    print("   rules/bat.html   retains 'the ones they held when the battle")
    print("                    began... it does not matter whether the card")
    print("                    or its holder survived', with Tyrant Splices")
    print("                    as the Candidates")
    if stale:
        for doc, phrase in found:
            print("   rules/%-10s STALE: %r" % (doc, phrase))
        print("                    Under the current rule a knocked-out")
        print("                    Rat's Upgrades are RETAINABLE, so these")
        print("                    disagree with bat.html's own rule about")
        print("                    which pile a card goes in.")
    else:
        print("   rules/nrj.html   agrees - checked on this run")
        print("   rules/bat.html   self-consistent - checked on this run")
    print("   rules/nap.html   3 Final Exams faced + 3 unused = 6          ok")
    print("   rules/aos.html   3 Advanced Programs faced + 3 unused = 6    ok")
    print()
    print("   Two copies of the old rule were stale when the audit ran and")
    print("   both have been corrected. nrj.html's Research Pool table")
    print("   predated the bat.html rewrite; bat.html's own knockout step")
    print("   also still said a knocked-out Rat's Upgrades 'become")
    print("   candidates rather than retained cards', three paragraphs from")
    print("   the rule saying it does not matter whether the card or its")
    print("   holder survived - 'the Rats are not the imposters, they chose")
    print("   what went into one, and winning proves the choice was right.'")
    print()

    print("5. THE PLAYTEST TABLE - the other place the hand-off is entered")
    print()
    print("   playtest/dist/suite.js keeps the Research Pool as a COUNT of 18")
    print("   and six number inputs for what is being spent, because the")
    print("   player holds the physical cards. Three things came out of")
    print("   auditing it:")
    print()
    print("   fixed   drawNRJ guarded on `if(state.nrj.current||...)`, a")
    print("           falsy test on a card INDEX. Scenario index 0 is The")
    print("           Physician's Greeting, so with that card on the table")
    print("           pressing Reveal again silently discarded it, drew a")
    print("           replacement and counted no attempt. Verified in the")
    print("           running app before and after: current 0 -> 7 with the")
    print("           attempt count unmoved, now unchanged. Every other read")
    print("           of nrj.current already used === null.")
    print("   fixed   the six spend inputs had no maximum, so a slip could")
    print("           spend more cards of a kind than the pool holds. Caps")
    print("           are now 3 per retained kind, 1 for the Specimen, 9 for")
    print("           wrong-category.")
    print("   fixed   `eligibleAvoid` was a flat 3 and the pool-mode selector")
    print("           only changed the overlay label. These were one issue:")
    print("           the app could not derive the avoid count because it")
    print("           tracked the pool as a COUNT of 18 rather than as")
    print("           cards, and standalone mode offered a random sample")
    print("           without dealing one.")
    print()
    print("           Standalone mode now deals the 18 cards rules/nrj.html")
    print("           describes - 3 retained and 3 Candidates per game,")
    print("           retained AoS randomised Stable/Overheated")
    print("           independently, BAT held to at most 1 Specimen - and")
    print("           the player spends them by clicking. So the Target")
    print("           reduction is computed from the cards actually spent, a")
    print("           spent card is gone for the rest of the finale, the")
    print("           avoid count is read off the pool (3 to 5, as section 2")
    print("           predicts), and 'The Long Argument: spend at most one")
    print("           NAP card' is now enforceable and enforced. Avoiding")
    print("           discards a Candidate before a retained Overheated")
    print("           Program, since a Candidate reduces nothing anyway.")
    print()
    print("           Campaign mode keeps the manual tally - there the")
    print("           player holds the physical cards - and gains one setup")
    print("           input, how many retained Overheated Programs were")
    print("           banked, which is exactly what the avoid count needed.")
    print("   fixed   drawNRJ rebuilt the pool when the Scenario deck ran")
    print("           empty, which silently restarted the finale. Twelve")
    print("           Scenarios against nine attempts means it cannot")
    print("           happen, but losing a game in progress is a worse")
    print("           answer than doing nothing, so it now does nothing.")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else GAMES)
