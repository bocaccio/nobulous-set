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
  * AT "ANY COLOR" IT COSTS PRECEDENT, AND THE FIX IS TO AIM IT
    BACKWARD. The Archivist's side B is "apply 1 die of any color,
    ignoring the attention entirely", free, once a Scenario, worth about
    +3. An any-color job is that same ability bought with cards, worth
    +3.1, so the two are ONE ability - and with the job in, Precedent and
    both Usher sides go NEGATIVE at the handicapped rungs, because all
    three are competing for the same spare wrong-color die. The job does
    not cost one card; it degrades the whole attention lane, three of ten
    sides.

    Nobody, though, occupies BACKWARD. Precedent takes any color, Early
    Admittance one step forward, Double Doors a third color forward. Aim
    the job at the color the attention has just LEFT and it keeps the flat
    mechanism and collides with nothing:

      job / side (4000 x 5)        Easy    r11    r13    r16   spread
      4 Cand, one step BACK       54.3%  33.4%  24.8%  14.3%    1.1
      4 Cand, any color           53.7%  33.3%  26.7%  13.7%    2.0
      Precedent alone             53.5%  33.9%  25.0%  13.9%    0.4
      Precedent + backward job    55.3%  31.9%  24.6%  13.4%    3.5
      Double Doors + backward     55.7%  33.1%  25.0%  14.2%    2.6
      Double Doors + any color    55.8%  32.0%  24.6%  13.7%    3.9

    So the backward job is the one to ship if any is: spread 1.1, worth
    +2.6 to +3.8, and Precedent keeps its job. NO REPLACEMENT ARCHIVIST
    SIDE IS NEEDED.

  * AND THEN IT FAILED ON THE RUNGS THE SET ACTUALLY PRINTS - 2026-10-31,
    the measurement that closed the question. Everything above was
    measured on this module's own rungs, Easy / r11 / r13 / r16, where
    the backward job reads spread 1.1 and looks like the one job that
    works. The set does not print r11, r13 or r16. It prints Easy,
    Standard, Hard and Nobulous, and on those four, measured across all
    ten Imposter sides (`python candidates.py shipped`):

      the job's worth        mean      min      max
      at Easy               +2.65     +0.6     +4.2
      at Nobulous           -0.15     -2.1     +1.4

    It is INVERSE-SCALING on the shipped ladder - worth about three
    points at Easy and nothing at all at Nobulous - which is the same
    fault as the dice-priced jobs with the sign flipped, and the one
    thing this whole investigation existed to avoid. The flatness was an
    artifact of the rungs, not a property of the job.

    The band settles it. The finale report marks 47-57% as the community
    band, and the Easy row is the hot end of the matrix:

      hottest Easy cell, no job    55.1%  (Double Doors)   0 of 11 outside
      hottest Easy cell, with job  58.2%  (Standing Order) 3 of 11 outside

    Early Admittance, Requisition and Standing Order all leave the band
    at Easy once the job is in. Without it every one of the eleven is
    inside it, and the no-Imposter ladder reads 50.6 / 39.0 / 30.6 / 19.4
    against aims of 50 / 40 / 30 / 20 - as close as it has ever been.

  * NO PRICE FIXES IT, because the price is not a dial. Sweeping the cost
    at 4, 5, 6, 7 and 8 Candidates returns exactly TWO distinct results,
    and "4 a use capped at one" is byte-identical to the 6/7/8 row:

      cost 4 or 5         54.3 / 40.6 / 33.3 / 20.3   affordable twice
      cost 6, 7 or 8      53.5 / 41.2 / 33.8 / 21.3   affordable once
      capped at one use   53.5 / 41.2 / 33.8 / 21.3   the same thing

    One use is still worth +3.5, because a policy with one use spends it
    at the moment of maximum value. The only configuration left is zero
    uses.

  * AND THE REASON IS THE REASON IT WAS CHOSEN. Backward was picked
    because it collides with no Imposter side - Precedent takes any
    colour, Early Admittance one step forward, Double Doors a third
    colour forward, and nobody goes back. But non-collision and
    non-stacking are the same property seen twice. The any-colour job
    left the ladder alone only because it CANNIBALISED Precedent, the
    two fighting over one spare die. The backward job competes with
    nothing, so it ADDS to all ten sides, and that is exactly why Easy
    goes to 58.2%.

    So: not shipped, and the cards and rules are untouched. The
    Candidates stay a record of what you could not afford, and the
    Understudy stays the one Imposter who spends them.

  * AND THE REPLACEMENT SIDES ALL FAILED ANYWAY, which is worth keeping
    because of what it says about the pool. Measured with a job in, the
    band is about 0 to +4:
      Filed Twice (split a card into two 1s)  +5.5 Easy, -0.8 r16, x1
      Certified Copy (one card takes 4, once) +2.6 Easy, +8.6 r16
      Duplicate Filed (first card comes back) +7.5 .. +11.3
    Filed Twice is INVERSE and a use cap cannot fix it - uncapped it reads
    +18.9 at Easy - because the pool's REACH is bounded by its card count
    and not by its total value, one card an Exhibit, so splitting doubles
    how many Exhibits it touches. That is the same fact section 6 of the
    finale report records as "eight cards worth 1.5 beat six worth 2".
    Reach buys TEMPO, and tempo is what Easy already has. Certified Copy
    SCALES because it adds reduction, and reduction is dice by another
    name. Side A is flat only because it is gated to Target 5 and adds no
    reduction at all: it relaxes WHICH card may answer, nothing more.

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


def shipped(games=GAMES):
    """The backward job on the four rungs the set prints, against all ten
    Imposter sides. This is the measurement that closed the question: see
    the fourth bullet of this module's docstring.
    """
    sys.path.insert(0, HERE)
    import imposters as I

    rungs = ("easy", "standard", "hard", "nobulous")
    aims = dict(easy=50, standard=40, hard=30, nobulous=20)
    job = dict(CANDIDATE_JOB="back", CANDIDATE_COST=4, CANDIDATE_USES=0)
    nojob = dict(CANDIDATE_JOB="none", CANDIDATE_COST=0, CANDIDATE_USES=0)
    sides = [("no Imposter", None),
             ("Precedent", "archivist_b"),
             ("Early Admittance", "usher_a"),
             ("Double Doors", "usher_b"),
             ("Cross-Referenced", "archivist_a"),
             ("Open Audition", "understudy_a"),
             ("Second Chair", "understudy_b"),
             ("Sleight of Hand", "porter_a"),
             ("Heavy Lifting", "porter_b"),
             ("Requisition", "steward_a"),
             ("Standing Order", "steward_b")]

    def cell(rung, hero, dials):
        over = dict(START_TIRED=I.LADDER[rung], HERO=hero)
        over.update(dials)
        return sum(I.run(games=games, seed=s, **over)
                   for s in SEEDS) / len(SEEDS)

    print("THE BACKWARD JOB ON THE SHIPPED LADDER - %d x %d seeds"
          % (games, len(SEEDS)))
    print("Aims %s. Community band 47-57%%."
          % " / ".join(str(aims[r]) for r in rungs))
    print()
    print("  %-20s %-27s %-27s" % ("", "without the job", "with the job"))
    print("  %-20s %6s %6s %6s %6s %6s %6s %6s %6s"
          % ("", "easy", "std", "hard", "nob", "easy", "std", "hard", "nob"))
    de, dn, hot_off, hot_on, outside = [], [], 0.0, 0.0, []
    for label, hero in sides:
        off = [cell(r, hero, nojob) for r in rungs]
        on = [cell(r, hero, job) for r in rungs]
        de.append(on[0] - off[0])
        dn.append(on[3] - off[3])
        hot_off, hot_on = max(hot_off, off[0]), max(hot_on, on[0])
        if on[0] > 57.0:
            outside.append(label)
        print("  %-20s %5.1f%% %5.1f%% %5.1f%% %5.1f%% %5.1f%% %5.1f%% "
              "%5.1f%% %5.1f%%"
              % tuple([label] + off + on))
        sys.stdout.flush()
    print()
    print("  the job is worth %+.2f at Easy and %+.2f at Nobulous"
          % (sum(de) / len(de), sum(dn) / len(dn)))
    print("  hottest Easy cell  %.1f%% without, %.1f%% with"
          % (hot_off, hot_on))
    print("  Easy cells outside the band with the job: %d %r"
          % (len(outside), outside))
    print()
    print("  Inverse-scaling on the rungs that ship, and three cells out")
    print("  of the band that are all inside it today. Not shipped.")


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
    # An optional game count after the name, so the table can be smoke
    # tested in seconds: `python candidates.py shipped 50`.
    _n = next((int(a) for a in sys.argv[1:] if a.isdigit()), GAMES)
    if "shipped" in sys.argv[1:]:
        shipped(_n)
    elif "currencies" in sys.argv[1:]:
        currencies()
    else:
        main()
