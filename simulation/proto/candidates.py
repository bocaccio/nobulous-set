"""What job should a Candidate do? ONE thing works: bend the attention.

    python candidates.py             # the options, against doing nothing
    python candidates.py currencies  # the uniformity table below

THE ANSWER, 2026-10-31, second pass. There IS a uniform global Candidate
job, and it is this:

    Discard 4 Candidates to apply 1 die the attention forbids.

Worth +2.5 at Easy and +3.2 at Nobulous - a spread of 0.7 across a forty
point ladder, which is flatter than any card in the set. RAISED, NOT
SHIPPED: it needs Jon's call, because it duplicates an Imposter side. The
first pass below rejected the idea on a diagnosis that was half wrong, and
both halves are worth keeping, so this docstring now carries both.

THE FIRST PASS, and what it got right. Every job it measured paid in dice
or in Targets, and every one FAILED THE UNIFORMITY TEST - worth nothing at
Easy and a great deal at every handicapped rung:

  job                   Easy    r11    r13    r16    worth E -> 16   spread
  no job               50.6%  30.6%  22.1%  10.8%        -             -
  4 Candidates a die   51.7%  39.0%  31.4%  19.5%    +1.1 .. +8.7      8.2
  2 Candidates, -1 Tgt 65.4%  56.3%  48.0%  34.0%   +14.8 .. +23.2    11.0
  3 Candidates, -1 Tgt 55.3%  44.4%  36.0%  23.2%    +4.7 .. +12.4     9.3
  4 Candidates, -1 Tgt 52.5%  40.7%  31.6%  19.0%    +1.9 ..  +8.2     8.2
  6 Candidates, -1 Tgt 51.0%  36.3%  26.8%  15.6%    +0.5 ..  +4.8     5.2
  (4000 finales a cell x 5 seeds. Rungs are yellow/green/blue/purple
  dice exhausted at setup: r11 = 3/3/3/2, r13 = 3/4/3/3, r16 = 4/4/4/4.)

That diagnosis was RIGHT about dice and Targets and WRONG in its last
clause, which read "no job priced in anything can be uniform." Two
corrections, both found by varying what the first pass held fixed.

CORRECTION 1: THOSE WERE NOT SIX PRICES. THEY WERE FOUR USE-CAPS.
A claiming campaign carries 11 Candidates, so a job costing 4 can be done
twice and one costing 6 once, whatever the rules say. The price never bound
- the POOL SIZE did, and every "cheaper" row above is simply a row with
fewer uses. Measured with the cap as its own dial, cost stops mattering the
moment it is not what limits you: 3-a-use twice, 4-a-use twice, 4-a-use
three times and 5-a-use three times all return the SAME four numbers,
because on 11 Candidates all four ARE two uses. So the first pass never
tested a price. It tested 5, 3, 2 and 1 uses, and read the cap as a price.

CORRECTION 2: THE LADDER IS PRICED IN DICE, AND SO WAS EVERY JOB.
A Target is a die by another name - fewer dice is a higher effective Target
- so dice and Targets are ONE currency, not two, and it is the currency the
difficulty ladder itself spends. That is the whole of the non-uniformity.
The finale has three other scarcities, and the ATTENTION WHEEL is one the
ladder never touches: nine sessions of Yellow-Green-Blue-Purple-Red are
identical at Easy and at Nobulous. Priced there, the same job goes flat.

  job                       Easy    r11    r13    r16   worth E->16  spread
  no job                   50.6%  30.6%  22.1%  10.8%       -           -
  4 Cand a die (2 uses)    51.7%  39.0%  31.4%  19.5%   +1.1 .. +9.3   8.2
  4 Cand, off-colour, x1   53.1%  33.8%  25.0%  14.0%   +2.5 .. +3.3   0.7
  4 Cand, off-colour, x2   53.7%  33.3%  26.9%  13.8%   +2.8 .. +4.8   2.0
  2 Cand, off-colour, x5   59.7%  31.1%  24.8%  15.2%   +0.5 .. +9.2   8.6
  2 Cand, soak 1 Damage    51.1%  31.7%  22.7%  10.7%   -0.1 .. +1.1   1.2
  3 Cand, dearest on top   54.7%  30.2%  20.3%   9.0%   -1.8 .. +4.1   6.0
  2 Cand, reroll a miss x2 53.9%  36.8%  27.6%  14.6%   +3.3 .. +6.2   2.9

WHY ATTENTION IS FLAT, which is the reusable part. The job needs an
AVAILABLE DIE OF A FORBIDDEN COLOUR. The handicap removes available dice,
so it quietly limits how OFTEN the job can be taken, while the wheel's
restriction is the same at every rung. The two effects cancel. The x5 row
is the proof: extra uses pay at Easy (+6.6 over x1) and not at r11 (-2.7),
because at r11 there is often no spare wrong-colour die to spend again.
Uncapped it is as bad as the dice job - the CAP is load-bearing, and at
cost 4 the pool supplies the cap without a printed clause.

WHAT THE OTHER TWO SCARCITIES DO. DAMAGE reads -0.1 .. +1.1, which is zero:
it binds at no rung, the same fact that killed Triage and Transposed Labels.
THE DOSSIER'S ORDER is worth +4.1 at Easy and -1.8 at Nobulous - the only
INVERSE-scaling effect measured in this finale, because reordering buys
tempo and tempo is what you already have at Easy. A REROLL is the odd one:
HUMPED, +3.3 at Easy, +6.2 at r11, +3.9 at r16, because it needs committed
dice to exist and slack for the miss to matter, and those fail at opposite
ends of the ladder.

WHAT IT COSTS TO SHIP, measured, which is Jon's call:
  * NOT the ladder. The job and the Imposters compete for the same spare
    wrong-colour die, so they do not stack. With the strongest Imposter the
    rungs read 55.8 / 39.6 / 32.0 / 20.2 against today's 55.1 / 41.0 /
    32.2 / 19.6 - Easy moves +0.7 and Standard and Hard move TOWARDS aim.
  * NOT the policy. `pace: clock` still wins with the job in, 53.7%
    against 50.8% for `ceil`, so this is the best policy, not a weaker one.
  * NOT the claim decision. Claiming is worth 42 points, not 6: a campaign
    that claims nothing in all three games reads 8.4% at Easy against
    50.6%. The gap WIDENS, from -42.2 to -44.7.
  * IT COSTS PRECEDENT. The Archivist's side B is "apply 1 die of any
    color, ignoring the attention entirely", free, once a Scenario, worth
    about +3 (+2.5 in the roster table, +2.9 re-measured beside the job).
    The job is that same ability bought with cards, worth +3.1. They are
    ONE ability, and a free once is dominated by four spare cards twice. If
    this ships, Archivist B needs replacing. Note the model does not know
    to stop paying for what Precedent gives away, so "Precedent with the
    job" reads WORSE at every handicapped rung (38.5 / 31.5 / 19.2 against
    41.9 / 33.9 / 21.2) - that much is a modelling artifact, but two cards
    doing one job is not.

AND ONE RATIONALE BELOW IS WRONG. The note further down says a job is
"automatically a consolation for the player whose three games could not
afford to claim." It is not, at any price: that player is at a floor. The
job pays a full claimer +5.3 and a claim-nothing campaign +0.6, because 15
Exhibits at undiminished Targets are lost whatever you are holding. A
Candidate job cannot be a catch-up mechanic. If one ships, it ships as a
decision for everybody.

WHAT SHIPPED FOR NOW. The Candidates stay on the table and answer nothing
*unless your Imposter says otherwise* - one of the five Imposter cards is
built around spending them. A hero ability is a visible choice, so a player
who takes that card at Nobulous is knowingly trading flavour for help,
which is legible in a way a silent global re-scaling is not. See
proto/imposters.py, whose CANDIDATE_JOB dial now carries every currency
measured here.

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


# ---------------------------------------------------------------------------
# THE SECOND PASS. What currency can a Candidate job be priced in?
#
# This path drives proto/imposters.py rather than finale.py, because the
# CANDIDATE_JOB and CANDIDATE_USES dials live there: finale.py is the
# calibrated build and carries no Candidate job at all, which is the state
# the first pass left it in and the state it should stay in until this is
# Jon's decision rather than a measurement.
RUNGS = [("Easy", (0, 0, 0, 0)), ("r11", (3, 3, 3, 2)),
         ("r13", (3, 4, 3, 3)), ("r16", (4, 4, 4, 4))]


def _job(cost=0, kind="none", uses=0):
    return dict(CANDIDATE_COST=cost, CANDIDATE_JOB=kind, CANDIDATE_USES=uses)


# Priced in dice the job scales with the handicap; priced in ATTENTION it
# does not, because the ladder never spends the wheel. The x5 row is there
# to show the CAP is what does the work, not the price.
CURRENCIES = [
    ("no job", _job()),
    ("4 Cand a die (2 uses)", _job(4, "die")),
    ("4 Cand, off-colour, x1", _job(4, "colour", 1)),
    ("4 Cand, off-colour, x2", _job(4, "colour", 2)),
    ("2 Cand, off-colour, x5", _job(2, "colour", 5)),
    ("2 Cand, soak 1 Damage", _job(2, "soak")),
    ("3 Cand, dearest on top", _job(3, "front")),
    ("2 Cand, reroll a miss x2", _job(2, "reroll", 2)),
]


def currencies(games=GAMES):
    """Reproduce the uniformity table in this module's docstring."""
    sys.path.insert(0, HERE)
    import imposters as I

    print("CANDIDATE CURRENCIES - %d finales a cell x %d seeds"
          % (games, len(SEEDS)))
    print("Rungs are yellow/green/blue/purple dice exhausted at setup.")
    print("Easy is the floor: 0 dice, so it cannot be pegged back.")
    print()
    print("  %-25s %6s %6s %6s %6s  %-14s %6s"
          % ("job", "Easy", "r11", "r13", "r16", "worth E->16", "spread"))
    base = None
    for label, dials in CURRENCIES:
        row = []
        for _, tired in RUNGS:
            xs = [I.run(games=games, seed=sd, START_TIRED=tired, **dials)
                  for sd in SEEDS]
            row.append(sum(xs) / len(xs))
        if base is None:
            base = row
            print("  %-25s %5.1f%% %5.1f%% %5.1f%% %5.1f%%  %-14s %6s"
                  % (label, row[0], row[1], row[2], row[3], "-", "-"))
        else:
            w = [r - b for r, b in zip(row, base)]
            print("  %-25s %5.1f%% %5.1f%% %5.1f%% %5.1f%%  "
                  "%+4.1f .. %+4.1f %6.1f"
                  % (label, row[0], row[1], row[2], row[3],
                     min(w), max(w), max(w) - min(w)))
        sys.stdout.flush()
    print()
    print("  Spread is the test. A job worth +2.5 at Easy and +9 at")
    print("  Nobulous is the only pick at Nobulous, which is what the")
    print("  first pass rejected; one worth +3 at both is a decision.")


if __name__ == "__main__":
    if "currencies" in sys.argv[1:]:
        currencies()
    else:
        main()
