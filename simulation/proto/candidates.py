"""What job should a Candidate do? REJECTED - none of them, globally.

    python candidates.py          # the options, measured against doing nothing

THE VERDICT, 2026-10-31. No global Candidate job ships. Four currencies and
six prices were measured and every one of them FAILED THE UNIFORMITY TEST:
worth nothing at Easy and a great deal at every handicapped rung, because
the job and the difficulty ladder spend the same scarcity.

  job                   Easy    r11    r13    r16    worth E -> 16   spread
  no job               50.6%  30.6%  22.1%  10.8%        -             -
  4 Candidates a die   51.7%  39.0%  31.4%  19.5%    +1.1 .. +8.7      8.2
  2 Candidates, -1 Tgt 65.4%  56.3%  48.0%  34.0%   +14.8 .. +23.2    11.0
  3 Candidates, -1 Tgt 55.3%  44.4%  36.0%  23.2%    +4.7 .. +12.4     9.3
  4 Candidates, -1 Tgt 52.5%  40.7%  31.6%  19.0%    +1.9 ..  +8.2     8.2
  6 Candidates, -1 Tgt 51.0%  36.3%  26.8%  15.6%    +0.5 ..  +4.8     5.2
  (4000 finales a cell x 5 seeds. Rungs are yellow/green/blue/purple
  dice exhausted at setup: r11 = 3/3/3/2, r13 = 3/4/3/3, r16 = 4/4/4/4.)

Changing the CURRENCY does not help - paying in Targets is worse than
paying in dice, spread 11.0 against 8.2 - and changing the PRICE only
shrinks the job: at 6 Candidates a Target it is worth +0.5 at Easy and
still ten times that at Nobulous. The cause is not the currency at all.
AT EASY THE MODELLED POLICY IS NOT DICE-CONSTRAINED, so any global aid is
marginal there and decisive once a handicap binds. That is a property of
the ladder, so no job priced in anything can be uniform.

Taking the job anyway was the alternative, and it costs the dial: with the
job in, the usable range falls from 40 points (50.6 down to 10.8) to 32
(51.7 down to 19.5) and Nobulous has to exhaust all sixteen coloured dice
to reach 20%, leaving no headroom. Eleven inert cards are a cosmetic fault;
a compressed difficulty dial with nothing in reserve is a functional one.

WHAT SHIPPED INSTEAD. The Candidates stay on the table and answer nothing
*unless your Imposter says otherwise* - one of the five Imposter cards is
built around spending them. A hero ability is a visible choice, so a player
who takes that card at Nobulous is knowingly trading flavour for help,
which is legible in a way a silent global re-scaling is not. See
proto/imposters.py.

THE PROBLEM. The Research Pool is 18 cards: the Tier III cards each game
laid out. The ones you CLAIMED are retained and take 2 off an Exhibit's
Target. The ones you never claimed are Candidates, and since the Exhibits
were reprinted on 2026-10-30 - which removed Rope Burns' random discard, the
last card text that touched them - a Candidate does nothing whatsoever.
Seven of the eighteen do the work and eleven are decoration.

WHY THIS IS WORTH FIXING RATHER THAN CUTTING. Candidates are the exact
complement of claims: claim seven and you carry eleven, claim none and you
carry eighteen. So a job for them is automatically a consolation for the
player whose three games could not afford to claim, and it turns the claim
decision from a one-way ratchet into a trade. That is worth more than
dropping ten cards from the box.

THE CONSTRAINT. A Candidate must be worth clearly LESS than a retained card
or nobody claims, and claiming is already priced at about 6 points of the
owning game's win rate. A retained card is worth 2 Target and about 6 points
of the finale. So the bar is: the option must leave claiming ahead.

Each option below is measured at the shipped pool and then re-measured
against a campaign that claimed nothing, which is the test that matters.
"""
import collections
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import finale as F  # noqa: E402

SEEDS = (11, 23, 47, 101, 7)
GAMES = 4000

# How many Tier III cards each game lays out, against how many are retained.
LAID_OUT = 6
CANDS = {"claimed as the rules allow": F.RETAIN,
         "claimed nothing": (0, 0, 0)}


class Pool(object):
    """The retained cards, plus the Candidates the finale now ignores."""

    def __init__(self, retain):
        self.retain = retain


def install(retain, job):
    """Rebuild research() so the Game also carries Candidates."""
    def research(rng):
        out = []
        for game, n in zip(F.TIRED_COLOURS[:0] or ("NAP", "BAT", "AoS"),
                           retain):
            out += [F.Card(game, F.CARD_VALUE) for _ in range(n)]
        return out
    F.research = research

    cands = {g: LAID_OUT - n for g, n in zip(("NAP", "BAT", "AoS"), retain)}
    orig_init = F.Game.__init__

    def __init__(self, rng):
        orig_init(self, rng)
        self.cands = collections.Counter(cands)
        self.cand_used = 0
    F.Game.__init__ = __init__
    return orig_init


def restore(orig_init, orig_research, orig_spend, orig_session):
    F.Game.__init__ = orig_init
    F.research = orig_research
    F.Game.spend_research = orig_spend
    F.session = orig_session


def main():
    orig_research = F.research
    orig_spend = F.Game.spend_research
    orig_session = F.session

    def measure(label, job, note=""):
        row = []
        for cl, retain in CANDS.items():
            orig_init = install(retain, job)
            job(F)
            xs = [F.run(games=GAMES, seed=s) for s in SEEDS]
            row.append(sum(xs) / len(xs))
            F.Game.__init__ = orig_init
            F.research = orig_research
            F.Game.spend_research = orig_spend
            F.session = orig_session
        print("  %-34s %7.1f%% %9.1f%%   %+5.1f   %s"
              % (label, row[0], row[1], row[1] - row[0], note))
        sys.stdout.flush()
        return row

    print("CANDIDATE JOBS - %d finales a cell x %d seeds" % (GAMES, len(SEEDS)))
    print("The second column is a campaign that claimed NOTHING, so it")
    print("carries 18 Candidates and no retained cards. The gap is what")
    print("claiming is still worth; if it closes, nobody claims.")
    print()
    print("  %-34s %8s %10s %8s" % ("", "claimed", "claimed 0", "gap"))

    def nothing(F):
        pass
    base = measure("A. nothing (as it ships)", nothing,
                   "11 of 18 cards inert")

    # B. SALVAGE. Two Candidates of a domain do what one retained card does
    #    half of: -1 from a just-deployed Exhibit of that domain.
    def salvage(F):
        base_spend = orig_spend

        def spend_research(self, fresh, policy):
            base_spend(self, fresh, policy)
            if policy == "none":
                return
            want = {"Knowledge": "NAP", "Physical": "BAT", "Cover-Up": "AoS"}
            for e in sorted(fresh, key=lambda e: -e.target):
                g = want[e.domain]
                while e.target > 1 and self.cands[g] >= 2:
                    self.cands[g] -= 2
                    e.target -= 1
                    break          # one salvage an Exhibit
        F.Game.spend_research = spend_research
    measure("B. 2 Candidates of a domain: -1", salvage,
            "half a retained card, two to one")

    # C. RECOVERY. Discard a Candidate to recover an exhausted die, which is
    #    the currency the finale is actually short of.
    def recovery(F):
        base_session = orig_session

        def session(g, pace, recov, rew, commit, res):
            # Spend one Candidate a session when something is exhausted.
            total = sum(g.cands.values())
            if total and g.exhausted:
                for k in list(g.cands):
                    if g.cands[k]:
                        g.cands[k] -= 1
                        break
                g.recover(recov, 1)
            return base_session(g, pace, recov, rew, commit, res)
        F.session = session
    measure("C. discard 1: recover 1 die", recovery,
            "one a session, the scarce currency")

    # D. SOAK. Discard a Candidate to prevent 1 Damage, once a session.
    def soak(F):
        base_session = orig_session

        def session(g, pace, recov, rew, commit, res):
            before = g.hp
            out = base_session(g, pace, recov, rew, commit, res)
            lost = before - g.hp
            if lost > 0 and sum(g.cands.values()):
                for k in list(g.cands):
                    if g.cands[k]:
                        g.cands[k] -= 1
                        break
                g.hp = min(F.HEALTH, g.hp + 1)
                if g.hp > 0 and out is False:
                    out = True      # the soak saved the game
            return out
        F.session = session
    measure("D. discard 1: prevent 1 Damage", soak, "one a session")

    print()
    print("  A is the floor. Any option that closes the gap in the last")
    print("  column has made claiming pointless, whatever it does for the")
    print("  finale's own number.")
    return base


if __name__ == "__main__":
    main()
