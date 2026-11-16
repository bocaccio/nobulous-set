"""The Imposter finale: the Council's attention rotates, and you set the pace.

    python finale.py              # the pitch, the skill layer and the dials

Rules source: rules/nrj.html. This module is the calibrated simulator for the
finale that SHIPS. `nrj.py` models the superseded nine-attempt Suspicion
finale and is kept only as the record of it - read the note at the top of that
file before quoting any figure from it.

WHERE THIS CAME FROM. proto/finale10.py measured the design against two
mechanics taken from published 20 Strong decks: Tainted Grail's colour dial,
and Tanglewoods: Rose's player-set pace against a hard clock. It beat every
earlier prototype on the only thing that decides whether a scenario gets
replayed - the gap between playing it badly and playing it well - and it did
it without asking the player to remember anything, because every input is
face-up on the table. The prototype measured a bare economy with invented
Exhibit values. This module is the same design on the REAL components, and
the numbers moved enough that three of its claims did not survive. They are
recorded in THE PROTOTYPE'S ERRATA at the bottom of the report.

WHAT THE COMPONENTS SUPPLY

  1 THE EXHIBITS ARE THE PRINTED COUNCIL TESTS. The 24-card library already
    sorts into 8 Knowledge, 8 Physical and 8 Cover-Up, and every domain
    prints the same Target spread, 8 8 8 9 9 9 10 10. An Exhibit's Target is
    its printed Target MINUS 5, so the deck supplies 3s, 4s and 5s with not
    one card reprinted - three 3s, three 4s and two 5s per domain.
    check_components() asserts that spread against build_nrj.py.
  2 THE RESEARCH POOL IS THE TIER III CARDS. Each game lays 6 out - 6
    Research Notes, 6 Devious Opportunities, 6 Backdoor Routines - so the
    18-card Pool needs no other box. A card you claimed is retained and a
    card you never claimed is a Candidate, worth nothing. A retained card
    spent as you deploy removes 1 from that Exhibit's Target, or 2 if you
    never spent it in its own game: the campaign's challenge is to finish
    each game using as little of its own Tier III help as possible. It
    answers only its own domain - NAP to Knowledge, BAT to Physical, AoS to
    Cover-Up - which is the old category match, and the only thing that
    makes the three domains mean anything once the dial carries the colour
    layer. A card is RETAINED or it is not and every retained one is worth
    2: the spent/unspent split was dropped on 2026-10-30 because nothing on
    the table records which a card is. At most 7 retained against 15
    Exhibits - NAP 3, BAT 2, AoS 2 - which is the count that reads 50%.
  3 THE AVOID RULE IS GONE, because choosing your pace replaces it. So is
    Suspicion, the uncapped Target tax: standing Exhibits deal Damage every
    session, which is the same pressure paid in Health instead of arithmetic.

THE PITCH: 48.7% at EASY, which is the Easy rung of the 50/40/30/20 ladder
and sits inside the 47-57% community band. Measured over five seeds, because
one is not a pitch: 48.4 48.8 48.9 49.0 48.6.

IT IS ALMOST THE NUMBER IT WAS IN OCTOBER AND IT MEANS SOMETHING ELSE.
Three things moved in three days. The eighteen Imposter clauses printed
along the foot of every Tier III card were played for the first time
(2026-11-14); the policy grid turned out to have no WHEN on its Research
axis, all four values spending the Pool the session it was dealt
(2026-11-14); and the model started choosing WHICH card to spend rather
than taking whatever came to hand (2026-11-16). The first two took the old
Easy rung from 50.5% to 72.1% and the LADDER WAS RE-CUT THE SAME DAY; the
third lifted the whole dice dial by about two dice and the ladder was re-cut
AGAIN, this time needing a second axis because the colour dice ran out
before the hardest aim did. The two are not separable at the rung that
ships: holding a pool of FLAT -2s there LOSES 12.7 points and holding one of
clauses gains 4.6, so what pays is not banking the help, it is knowing which
help is worth banking. So the pitch is a coincidence of two large moves and
a re-cut, not a number that stood still: Easy is a tired rung now, and
exhausts twelve of the sixteen colour dice where it used to exhaust none.

EVERY FIGURE IN THIS FILE IS REPRODUCIBLE FROM ITS SEED SINCE 2026-11-14,
and was not before: the Vote broke a colour tie on a set's iteration order,
which CPython randomises per process, and one tie re-rolls every game after
it because a cell shares one random stream. Observed at 0.1 to 0.2 on
five-seed means and in principle a whole re-sample, which is about 0.4 -
the same figure this file already calls the edge of the noise. Figures
older than that date carry that much slop, the sweeps this ladder was cut
from among them, though nothing here was decided inside half a point.
audit.py fails if it returns.

EVERY POLICY FIGURE IN THE LIST BELOW WAS MEASURED ON 2026-11-13 - before
the clauses were played, before holding the Pool became the default, and
against an Easy rung that exhausted no dice. All three moved on 2026-11-14.
They are left exactly as they stood because each is the GAP between two
policies rather than a pitch, and re-stating a gap from memory is how this
repository has gone stale before. `python finale.py` recomputes every one of
them against the model as it now is; finale.txt is that output, and where it
disagrees with the list below it is the list that went stale.

  pace       clock 50.1   against every fixed pace: two 31.9, three 1.2,
             one and all 0.0, and the throttled variant 47.4
  recovery   horizon 50.1 and next 51.3, against best 45.6 and now 8.4 -
             reading the wheel pays, and grabbing this session's colour is
             far too late. next edges horizon on one seed and loses to it
             over five, 50.0 against 50.5 - which is the whole reason this
             file pitches on five.
  commit     adaptive 50.1 against 37.5 for throwing every allowed die
  Research   spending it 50.1 against 8.7 for ignoring it, with hoarding
             for the Target 5s at 42.1 and dumping it at 37.5. "WHICH card
             on WHICH Exhibit is the decision" is what this line used to
             say, and section 9 could not find it: choosing the card is
             worth +0.4 under this policy and -2.0 under the best one.
             WHEN to spend is the decision - res = "time", +17.4, and
             it is the DEFAULT since 2026-11-14
  Rewards    50.5 against 42.7 with the five Reward cards switched off
  carry-over 50.1 against 31.1 when progress resets, so the published rule
             that damage on a standing enemy persists is load-bearing
  blind play 0.5% - a player using none of the levers does not finish

  Every figure above is the BEST cell of the policy grid, and the policy
  this module models IS that cell - clock / horizon / adaptive / TIME since
  2026-11-14, where it was clock / horizon / adaptive / small before. The
  grid is 280 cells rather than the 224 this paragraph used to claim,
  because adding a WHEN to the Research axis took it from four values to
  five. This project has mis-pitched a game once by measuring it against a
  weaker policy than the one a player would find; the grid search is the
  guard against doing it twice, and on 2026-11-14 it caught it a second
  time - the grid had no WHEN in it at all, so the best cell it could
  report was the best of the wrong 224.

THE FIVE IMPOSTERS ARE MODELLED HERE SINCE 2026-11-06, ported in from
proto/imposters.py. Before that this module had no hero code and the ten
printed abilities lived only in that prototype, which made the centrepiece of
the set the one deck the shipping simulator could not play. HERO = None is
still the pitch, and still reproduces every figure above, because a side is
quoted as a delta against a heroless baseline. The ten, at Easy against
HERO = None:

  Imposter     side                 when            delta
  Archivist    Cross-Referenced     passive          +1.3
  Archivist    Precedent            once/Scenario    +1.8
  Understudy   Open Audition        once/Scenario    +5.5
  Understudy   Second Chair         twice/Scenario   +4.8
  Usher        Early Admittance     once/Scenario    +2.1
  Usher        Double Doors         once/Scenario    +1.8
  Porter       Sleight of Hand      once/session     -0.1
  Porter       Heavy Lifting        once/Scenario    +4.0
  Steward      Requisition          once/Scenario    +3.2
  Steward      Standing Order       once/Scenario    +3.4

RE-MEASURED 2026-11-16, AND THE ORDER MOVED IN BOTH DIRECTIONS: Heavy
Lifting went +0.7 to +4.0 while Double Doors went +3.4 to +1.8, so a side is
worth what it is worth at a RUNG and not in general. Nothing to five and a
half points each where this paragraph used to say two to four, and Sleight
of Hand is the one that now does nothing at all, at -0.1. Section 7 of
finale.txt is the live table and this is a summary of it. The band still
holds with one chosen. The ladder is NOT re-pegged for it, and the reason
changed on 2026-11-14: this paragraph used to say Easy was already zero dice
exhausted so there was nowhere to peg it down to. Easy exhausts twelve now,
so there is - but a side is quoted as a
DELTA against HERO = None and the pitch is quoted heroless, so re-pegging for
a side would price one of five choices into all four rungs.
proto/imposters.py carries the two tests each side had to pass - LEVEL and
UNIFORM - and the sides that failed them; its own header still argues from
the zero-dice Easy rung and was written before this.

THE LADDER IS CUT WITH DICE - see START_TIRED - AND, SINCE 2026-11-16,
WITH ONE POINT OF HEALTH AT THE LAST RUNG. It was re-cut on 2026-11-14
against a held Research Pool and again two days later against a scored
hand, and every one of its four rows moved both times:

                 11-13      11-14      is       HP   reads   aim
      Easy       -          3/3/2/2    3/3/3/3   5    48.7%   50
      Standard   3/2/2/2    3/3/3/4    3/3/4/4   5    39.6%   40
      Hard       3/3/3/2    4/3/4/4    3/3/4/4   4    33.0%   30
      Nobulous   3/3/4/4    4/4/4/4    3/3/4/4   3    22.1%   20

  yellow/green/blue/purple, and the dial was chosen over REC or the
  Dossier because the rungs still reward play - section 8 prints every
  rung with its own pace, recovery, commit, research, clause and CARD
  gaps, and the RECOVERY decision still pays more the harder the rung.

  THE DICE STOP AT FOURTEEN, which is the one thing this second cut
  could not do on the dial it was given, and the rule that stops them is
  the one this file already applies one session further on. The
  attention opens on Yellow with a Yellow+Green window, so a rung that
  takes every yellow AND every green starts with nothing it may APPLY -
  at sixteen you hold one red die and session 1 is not hard, it is
  skipped. Every rung keeps a yellow and a green and opens with two
  applicable dice. Health carries what is left, and the two axes are the
  same size: one point of Health costs 6.6 at Hard and 10.9 more at
  Nobulous against 6.1 for the fourteenth die.

  THE TOP THREE RUNGS THEREFORE SHARE A DICE ROW. That is what the cap
  costs the printed table, and the table tells the true story rather
  than a tidier one: the dice run out, and after that it costs you
  Health. The ladder is two axes wide now and was one for three weeks,
  so a figure quoted for "Hard" or "Nobulous" from any earlier run was
  quoted at 5 Health.

  SIXTEEN DICE WITH 4 HEALTH WAS BUILT AND MEASURED FIRST, at 21.5%, and
  it lands as well as this does. It was dropped for the skipped session
  rather than for its reading, which is the only reason worth recording:
  a rung that is unplayable for a ninth of the scenario is not a harder
  puzzle, it is a shorter one.

WHY IT HAD TO MOVE. The old counts were cut against a model that spent the
Research Pool the session it was dealt. That is not the best cell of the
grid and it is not what a player looking at a face-up Pool would do, and
with the clauses played and the Pool held the old counts read
74.6 / 57.7 / 47.7 / 33.7 against aims of 50/40/30/20. The ladder had not
stretched, it had come off its pegs altogether - every rung between 13.7 and
24.6 points too easy, and the easy end of it far out of the community
band.

ONE DIAL WAS ENOUGH ON 2026-11-14 AND IS NOT ENOUGH NOW, which is the
whole story of the second cut. The handicap used to do double duty: it took
the dice away AND it took away the value of banking help for a later
session - holding was worth +17.3 with nothing exhausted, +5.6 at ten dice
and LESS THAN NOTHING past thirteen - so the dial spanned 74.6 to 20.4 and
reached all four aims by itself. Scoring the hand lifts the whole curve by
about two dice:

    dice     10     11     12     13     14     15     16
    reads  55.9   52.9   48.7   43.8   39.6   33.5   27.2

and fourteen is the end of it - not because the dice run out at fourteen,
but because the fifteenth has to come off the yellow or the green, and the
opening window is Yellow+Green. The first two aims land on dice, 12 and 14;
the last two are 6.6 and 17.5 points further down and are paid in Health.

  THE +17.3 / +5.6 / -2.4 FIGURES WERE SWEPT THROUGH AN UNSCORED HAND at
  HOLD_LAST = 3, and they are quoted for the SHAPE - holding decays, then
  reverses - which is what the paragraph argues from. The per-rung gap at
  the LIVE default is recomputed by section 8 on every run, signed, so
  read finale.txt for the number and this for the reason.

THE PRICE IS PAID IN TWO PLACES. Both are design facts rather than
measurements, so they are recorded here rather than quietly fixed.

  1 EASY STARTS TIRED, and "Easy means nothing starts exhausted" was a
    rule of this scenario until 2026-11-14. Easy exhausts three of every
    colour now, leaving one of each and the red - twelve of sixteen,
    where the first cut took ten. The hard end pays in Health instead:
    Hard and Nobulous are the same dice as Standard at 4 and 3. That is
    what pegging Easy to 50% costs once the policy being modelled is the
    strong one. The alternative was
    to leave the counts alone and let the printed rates go on describing
    a weaker policy - which is what rules/nrj.html's own box already says
    they are, "a competent policy, but neither an optimal one nor a human
    one".
  2 NO SINGLE res IS BEST ON ALL FOUR RUNGS. Holding is worth most at
    Easy and least at Nobulous, so the hardest rung is cut against a
    policy a player could improve on by spending at once. Section 8
    prints that gap per rung WITH ITS SIGN rather than hiding it, and
    the same section now prints the CARD gap beside it. The reading is
    not that the model is wrong but that WHEN to spend is a live
    decision whose answer depends on how tired you are, which is a
    better property for a scenario than one right answer at every
    setting.
  3 AND THE PITCH RESTS ON CLAUSE_WORTH SINCE 2026-11-16. The cards are
    chosen by a scoring table this project wrote, and section 9's
    permutation test says the whole of that choice's value is the
    table's content: dealt to the wrong cards it is worth nothing. Four
    printed rungs are pegged to a guess being approximately right. It is
    the newest of the three prices and the only one that could be paid
    back, by replacing a term in CLAUSE_WORTH with something a rule
    prints.

THE COLOUR SPREAD STOPPED MATTERING, at the end of the dial where the rungs
now live, AND IT STOPPED BEING ORDERED THE WAY THIS PARAGRAPH SAID. Taking
whole colours is still the one thing that collides with the wheel - 4 yellow
and 4 green reads 28.7% against 38.4% for the same eight dice off the purple
end, because the wheel opens Yellow+Green - but re-swept through a scored
hand on 2026-11-16 the four ways to take twelve read 48.7, 49.0, 47.8 and
47.2 and the four ways to take fifteen read 33.5, 33.2, 32.5 and 31.8. Two
points across a whole column, against nine and a half at eight dice.

  AND "THE EXTRA DIE COMES OFF THE PURPLE END FIRST" IS NOT THE RULE at
  this end of the dial. It predicts that 2/2/4/4 is the easiest way to
  take twelve, since it takes the fewest of the two colours the wheel
  opens on; it is in fact the HARDEST of the four, at 47.2 against
  48.7 for 3/3/3/3. Emptying blue and purple outright leaves sessions 3
  and 4 with nothing they may apply, which is the same whole-colour
  collision the paragraph above is about, arriving from the other end.
  The rule that survives both sweeps is: keep one of every colour if you
  can, and past that the spread is worth about a point. It is why Easy
  is 3/3/3/3 - one die of each left and the red - and why the ordering
  is no longer load-bearing for the printed rows. What IS load-bearing
  is that the four rows stay per-colour monotone, for which see THE
  LADDER above.

AND THE PRINTED WIN RATES ARE STILL TRUE, through both cuts. rules/nrj.html
prints "about 1 in 2, 2 in 5, 3 in 10, 1 in 5" and the model reads
4.9, 4.0, 3.3 and 2.2 in 10 against them. That is the test each cut was
steered by and it is why the aims were not renegotiated when the dice ran
out: a ladder that reaches 27% at its hardest rung would have made the last
row of the book "about 1 game in 4" and left Hard and Nobulous half a game
in ten apart. What changed in the book across two cuts is four rows of dice
counts, one Health column, one sentence - and four table cells that lost
the word "game" so a seventh column would fit without the supplement
gaining a fifth page for one orphan line. Not one percentage.

THE EIGHTEEN CLAUSES, implemented 2026-11-14. Every Tier III card prints
one along its foot and this module played none of them: a retained card was
Card(game, value), so the campaign's seven chosen cards arrived as three
integers and the finale played the same whichever ones you carried. Jon:
"you want to feel like you had agency in obtaining the specific cards that
you carry into the imposter scenario". CLAUSES = False restores the flat
pool and every figure measured through it.

  RE-MEASURED 2026-11-16 on the twice-re-cut rungs. Sections 8 and 9
  recompute all of this on every run, so finale.txt is the authority and
  this is the summary. The readings this block carried before the re-cuts
  were taken on a Pool spent the session it was dealt and then on an
  unscored hand, and each set is replaced rather than kept, because not one
  of them describes the model that ships.

  the layer      +35.1 at Easy, 13.6 to 48.7 - the largest single thing
                 in the model now, ahead of pace and of recovery, because
                 a held card is worth whatever its clause is worth while
                 a spent one is worth 2 off a Target
  by rung        +35.1 Easy, +33.4 Standard, +30.0 Hard, +21.4 Nobulous.
                 THIS REVERSED on 2026-11-14. The clauses used to be
                 worth MORE the harder the rung, which is what broke the
                 old ladder; they are worth less now, because holding is
                 what makes them large and holding is the first thing the
                 handicap takes away
  choosing       +5.0, where it was +0.4 before the Pool was held, and
                 THE POLICY SINCE 2026-11-16 - see CARD_PICK, and the
                 permutation test in section 9 that says the whole +5.0
                 is the scoring table being right rather than the act of
                 scoring, which is what the four printed rungs are now
                 pegged to
  the spread     one forced into the hand at a time, Resource Fork +2.11
                 and Red Means Go +1.18 against Borrow the Master's Notes
                 -2.69 and Cross-Species Compatibility -2.05. Not quite
                 five points between best and worst, where it was two and
                 a half on a Pool spent at once - and 7.2 at the
                 2026-11-14 rungs, so the WIDTH of the spread is read at a
                 rung too and the cap narrowed it
  what bites     audit.py counts it, as a share of the finales the card
                 was spent in. Extra Credit? 100%, Resource Fork 99%,
                 Acceptable Losses 97%. HOLDING FIXED THE DEAD ONES:
                 Controlled Failure went 8% to 57%, Cross-Species
                 Compatibility 7% to 53%, Privilege Escalation 5% to 46%,
                 because a clause spent late is live in the session its
                 condition is likeliest to be true. Only Unexpected
                 Resilience is still under 10%, at 8%, and it needs the
                 session it is spent in to be the one you would have
                 died in

A GATE IS NOT TUNING, and five of these needed one. Measured ungated,
Controlled Failure read -7.45: an Exhibit put back is not an Exhibit
avoided, it is an Exhibit moved to the end of a clock that already sits one
Exhibit above a cliff. The others were a wild card spent on the first thing
that came up, two dice exhausted to finish an Exhibit that was falling
anyway, and the Dossier sorted comfortable-end-first. This module already
says why, for the Imposter sides: "a side the model spends unconditionally
measures as its WORST case".

TWO THINGS THE CLAUSES FOUND, and neither is about the clauses.

  1 DAMAGE WAS BEING READ OFF THE CURRENT TARGET. Exhibit.damage was
    `2 if self.target >= BIG`, and spend_research writes to self.target -
    so answering a Target 5 with one retained card also halved the Damage
    printed on it. build_nrj.py prints Damage as its own numeral beside
    the Target and rules/nrj.html says "Each Exhibit prints its Target,
    its Damage and a Reward", so nothing grants that. Worth +0.34 at the
    shipped policy, which is why no report this file has printed ever
    showed it.
    DAMAGE_TRACKS_TARGET restores it.

  2 THE POLICY GRID HAD NO "WHEN". `res` offered none, small, big and
    dump, and all four spend the moment an Exhibit of the right domain is
    deployed - so the Pool is empty by about session 4, which is the half
    of the scenario with the fewest Exhibits standing and the most dice to
    throw at them. HOLDING IT FOR THE SECOND HALF IS WORTH +13.3 ON A POOL
    OF FLAT -2s, and +17.4 with the clauses on: res = "time" reads 63.4
    and 72.2 against 50.1 and 54.8. It is legal - Deploy takes "any
    number, including none", Strategy says "Nothing is compulsory", and
    nothing makes answering an Exhibit mandatory - and it needs no memory,
    because the Pool is face-up.

    IT IS THE DEFAULT SINCE 2026-11-14, and it took the ladder with it.
    This paragraph used to say the opposite - left as a policy, because by
    this file's own rule that it models the best cell the pitch would be
    72.2% rather than 54.8%, and making that change here would re-pitch
    the scenario and contradict the win rates printed in rules/nrj.html on
    a measuring tool's own authority. That was Jon's call to make and he
    made it: res = "time" is what play() does now and the four rungs were
    re-cut against it the same day, which put the printed win rates back
    inside a point of true. res = "small" with CARD_PICK = "any"
    reproduces every figure this file published before 2026-11-14 - BOTH
    dials, since 2026-11-16, because the hand is scored now too - and
    HOLD_LAST and HOLD_FLOOR are the shape of the policy that replaced
    res = "small".

WHAT 2026-10-30 MOVED, in three corrections. research() was still dealing the
pool the Tier III rework replaced the day before - a NAP card always worth 1,
a BAT card worth 2 only on a 1-in-4 Specimen, an AoS card worth 2 on a coin
flip. Then the spent/unspent split went, because a campaign played over
several evenings cannot track it, and with one card value the pool became a
count that had to be re-derived: eight cards worth 1.5 beat six worth 2 on
the same total reduction, since spreading across more Exhibits and more
domains pays better than concentrating. And the Council Tests were reprinted
as Exhibits, Target and Damage on the face. Through all of it the pitch moved
about a point, and the COMMIT lever got stronger rather than weaker - 12.3
against 7.7 - because a pool that lowers Targets makes committing exactly
enough pay more.

THE FIVE REWARD CARDS ARE WORTH THREE TIMES WHAT THIS FILE SAID. Eight of
the 24 Council Tests are printed as Rewards and five of them still pay
something this finale has; switching them off costs 24.0 points, which puts
them level with choosing the pace and behind only the clause layer. That
figure was +7.8 while the Pool was spent the session it was dealt, and the
compounding is the same one the clause layer measures: dice handed back are
worth far more to a policy that is HOLDING help for the second half than to
one that has already spent it.

THEY ARE ALSO WHY REC IS 3, AND THE RUNG THAT BREAKS HAS MOVED. At REC 4
the commit gap falls from +13.9 to +1.4 - a decision worth about a point is
barely one - and by REC 5 it INVERTS, throwing every allowed die beating
adaptive by 4.6 and the best available policy reaching 73.2%, far out of
band. The gap reads +9.1 at REC 2, +13.9 at REC 3, +1.4 at REC 4 and -4.6
at REC 5, so REC 3 is both where committing pays MOST and the last rung
where a player who throws everything is making a mistake. The Rewards are
the fourth point of recovery, and they have to be earned.

THE CLOCK IS NOT MONOTONIC, and that is a property rather than a bug. The
window is two colours wide and the wheel is five long, so the length of the
clock decides which colour the LAST session lands on. Nine sessions puts the
red session - one die, the hard one - exactly in the middle at session 5, and
ends on purple, the strongest. Eight sessions reads 29.5% and ten 31.7%
against nine's 48.4%: eight ends on blue with Exhibits still standing, and
ten ENDS on red with one die to clear whatever is left. A LONGER clock being
worse is the whole of the argument, so the nine-session clock is chosen for
its phase on the wheel and not for its length.

WHAT IS STEEP, and where the edges are. REC is the usable dial and it is
not gentle: 2 / 3 / 4 / 5 read 15.5 / 48.4 / 64.2 / 69.2, and past REC 3
the modelled policy stops being the best one, exactly as described above -
section 8's own sweep has the commit gap down to +1.4 at REC 4 and INVERTED,
at -4.6, by REC 5. A point of STR takes the finale to 78.9%.

THE DOSSIER SITS ONE EXHIBIT ABOVE A CLIFF. At REC 3 the deck reads
12 / 13 / 14 / 15 / 16 / 18 Exhibits = 85.1 / 75.8 / 65.5 / 48.4 / 25.9 /
1.0%. It is a workable ten-points-an-Exhibit dial on the easy side and
falls off a cliff past the shipped 15, so a sixteenth Exhibit is not a
difficulty step, it is a different game - which is what ruled it out as the
ladder's second axis on 2026-11-16.

AND HEALTH STOPPED SATURATING, which this paragraph did not notice for two
days: it said Health was "a buffer rather than a dial" on a sweep reading
43.5 / 50.3 / 50.1 / 50.0, and 3 / 4 / 5 / 6 now read 31.6 / 41.6 / 48.4 /
52.2. It flattens UPWARD and not downward - a sixth point is worth 3.8 and
a third costs 16.8 - and the two hard rungs are cut on exactly that
asymmetry, which is why the second axis goes DOWN from 5 rather than the
easy end being given a sixth point.
"""
import collections
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dice import COLORS, EV_REROLL, FACES, roll

GAMES = 6000
# The pitch is a FIVE-SEED mean: one 6000-game cell lands about a point
# either side of it, so a single seed is not a pitch. Module-level because
# table.py reads these rather than copying them - a copied seed set gives a
# different mean and the two files then disagree about what the finale reads.
SEEDS = (11, 23, 47, 101, 7)

# --- the components ---------------------------------------------------------
# Every domain of the Council Test library prints this Target spread, and the
# Exhibit's Target is the printed one minus TARGET_OFFSET.
PRINTED = [8, 8, 8, 9, 9, 9, 10, 10]
TARGET_OFFSET = 5          # printed 8/9/10 -> Exhibit Target 3/4/5
DEAL = 5                   # Exhibits per domain; a 3-tuple deals unevenly
SESSIONS = 9               # the clock. Chosen for its phase: see the header
HEALTH = 5
STRAT = 2                  # Strategy phases per session
# REC 3 rather than 4: the five Reward cards hand back dice for burying
# the right evidence, so the extra recovery is earned instead of given.
# At REC 4 with the Rewards on the commit gap falls to +1.4 from +13.9, and
# by REC 5 throwing every allowed die beats holding any back by 4.6 and the
# commit decision is gone.
REC_BASE = 3
BIG = 5                    # an Exhibit PRINTED at this Target or above deals 2
# The bug this replaced, kept as a dial because every finale figure
# published before 2026-11-14 was measured through it: Damage recomputed
# from the Target as it stands, so a retained card spent on a Target 5 took
# the card's Damage down with it. See Exhibit.damage.
DAMAGE_TRACKS_TARGET = False
CARRY = True               # damage on a standing Exhibit carries over
RESEARCH = True            # the campaign's retained Tier III cards
# How many cards each game carries, NAP / BAT / AoS. The printed cap is 3 a
# game, but AoS's own limit of 2 claims a game binds first, so 8 is the most
# any campaign can carry and the standalone rule deals the same.
# NAP 3, BAT 2, AoS 2. With one value the pool is just a count, and seven
# cards is the count that reads 48.7%, the Easy rung's own figure. The
# caps match the economics: a NAP
# Opportunity is worked like an Assignment and apprentices finish about 2.5
# of them, a second BAT Note already costs that game 9 points, and AoS
# limits itself to 2 claims.
RETAIN = (3, 2, 2)
CARD_VALUE = 2             # what one retained card takes off an Exhibit
# Each game lays LAID_OUT Tier III cards out, so what you did not claim comes
# to the finale as CANDIDATES. They answer no Exhibit and are worth nothing on
# their own; the Understudy is the one Imposter that spends them.
LAID_OUT = 6

# THE EIGHTEEN IMPOSTER CLAUSES. Every Tier III card has printed one along
# its foot since 2026-11-14, used in this scenario and nowhere else. You get
# it AS WELL AS the -2, from the moment you spend the card to the end of that
# session. Jon, on why they exist: "if the specific cards don't matter, you
# may as well just play the standalone version... you want to feel like you
# had agency in obtaining the specific cards that you carry into the imposter
# scenario". The cause of that was in here - a retained card was (game,
# value), so seven chosen cards arrived as three integers.
#
# CLAUSES = False restores exactly that pool, and with it every figure this
# file published before 2026-11-14.
CLAUSES = True
# Two of the eighteen say how the card may be played rather than what happens
# once it has been, so they are asked while the card is still in the Pool.
# For these two `clause()` means HELD: the clause is what makes the spend
# legal in the first place.
SPEND_CLAUSES = ("Nobulous Owes You One", "Privilege Escalation")
# WHICH card to spend is the decision the clauses exist to create, so it is a
# policy with a control rather than a fixed rule. "clause" scores what each
# one is worth on the table in front of you; "any" spends whatever comes to
# hand, which is what this module did when every card was worth the same.
# "clause" IS THE DEFAULT SINCE 2026-11-16, and the ladder is cut against
# it. The history of the dial is the history of the finding. Scoring the
# hand measured +0.41 against a Pool spent the session it was dealt and
# -1.98 under the best policy then known, so for a day it could not be
# shown to help at all. Against a Pool that is HELD it measures +5.0, and
# the spread between the best and worst single clause went from 2.6 points
# to 4.8 - choosing WHEN gave choosing WHICH something to decide, which is
# what the clauses were printed to do in the first place. "any" is the
# control, and section 9 still prints the gap.
#
# AND THE PITCH NOW RESTS ON CLAUSE_WORTH. That is the one thing this
# default costs, and it is why the dial stood at "any" for two days after
# the evidence had turned: the table is a guess this file wrote, not a rule
# printed on anything, so four printed rungs cut against it are four rungs
# pegged to the guess.
#
# SO SECTION 9 MEASURES THE EXPOSURE RATHER THAN ARGUING ABOUT IT. It deals
# the same eighteen scoring functions to the WRONG cards - a table that is
# pure noise, with the same values in it - and re-reads the rung. Five
# permutations, measured at the Easy rung THAT SHIPS (3/3/3/3), where the
# true table is worth +5.0. Section 9 re-measures every one of them at
# whatever rung ships, so read finale.txt for the figures and this for the
# finding:
#
#   -1.0   -0.7   +4.1   +1.0   -2.2     mean +0.2
#
# A permuted table is worth NOTHING, inside the 0.4 that two five-seed
# means differ by, and three of the five read worse than spending what came
# to hand. So the +5.0 is the table's CONTENT, all of it. There is no part
# of it that comes free from the mere act of scoring, which is the
# comfortable answer this test was run to look for and did not find.
#
# WHAT MAKES IT BEARABLE, and it is a weaker claim than a measurement:
# every term in CLAUSE_WORTH reads something FACE-UP - dice exhausted,
# Health left, whether the window covers what is standing - so a player at
# the table can do the same arithmetic. The table is a guess at how a
# competent player would rank eighteen cards, not a lookup a player could
# not perform. Section 9 prints the per-clause deltas it implies, which is
# the honest width of the guess, and the one gate on changing a term in it
# is that the term stays something you can SEE.
CARD_PICK = "clause"
# Section 9 measures one clause at a time by forcing it into the hand.
FORCE_CLAUSE = None
# res = "time" holds a card whose clause is worth less than this now, while
# there are more than HOLD_LAST sessions left to spend it in. Past that it
# spends everything, so a held card is never stranded - which is the whole
# difference between holding and the "none" policy that reads 0.2%.
#
# BOTH WERE SWEPT ON 2026-11-14, when res = "time" became the default. While
# it was one policy among five these two were just the shape of that policy;
# as the default they set the number the LADDER is cut against, so cutting
# first and sweeping afterwards would have pegged four rulebook rows to a
# policy that is knowably beaten. HOLD_LAST was 3 and 3 is not the best cell.
#
# HOLD_LAST IS NOT A SMOOTH PREFERENCE - it names a session to dump on, and
# against a five-long wheel it had TWO local maxima. Re-swept 2026-11-16
# through a scored hand, at the twelve-dice rung that ships; section 9
# walks all seven values on every run:
#
#   0 -> 45.0   1 -> 48.7   2 -> 46.6   3 -> 45.4   5 -> 46.4
#
# 1 dumps in session 9 and 5 dumps from session 5, which is the RED session -
# one die, the hard one, sitting exactly in the middle of a five-long wheel.
# This is the same phase effect the header records for SESSIONS, arriving on
# a different dial, so do not read the dip at 3 as a preference about pools.
#
# THE TIE IS GONE, which is the news. At the old rung 1 and 5 read 51.6 and
# 51.8 - inside the 0.4 two five-seed means differ by - and this comment
# argued for keeping 1 on older evidence rather than on that reading. A
# scored hand separates them by 2.3, because the point of dumping on the red
# session was to unload cards the policy could not rank, and a policy that
# CAN rank them would rather hold the good ones to session 9. The second
# maximum is still there; it is no longer a rival.
#
# HOLD_FLOOR = 1.0 WAS A COMPROMISE AND IS NOW A MAXIMUM, which is the other
# thing the re-sweep settled. It used to change sign down the ladder - Easy
# wanting to bank more, the tired rungs less, and 1.0 only ever the value
# that was never badly wrong. Through a scored hand it is the best of six at
# twelve dice (0.50 -> 44.5, 0.75 -> 44.8, 1.00 -> 48.7, 1.25 -> 47.2,
# 1.50 -> 44.2, 2.00 -> 37.0) and the best of three at sixteen (0.50 ->
# 25.7, 1.00 -> 27.2, 2.00 -> 13.5). Scoring the hand is what did that: the
# floor only means anything if the scores it compares against mean
# something, and a policy that then spends the WRONG card wastes whatever
# the floor saved.
HOLD_FLOOR = 1.0
HOLD_LAST = 1

# THE IMPOSTER YOU CHOSE. Five two-sided cards, ten abilities, one lever each,
# and every side prints the finale's own 5 HP / 2 STR / 3 REC - the house rule
# across the set is that heroes differ only in ability text
# (simulation/cards.py). None of them touches STR, REC or the width of the
# attention window: a point of STR takes the finale to 79% here, REC 5
# inverts the commit decision and REC 4 leaves about a point of it, and a
# three-colour window reads 67% with the shipped recovery policy no longer
# the best one, so those three are not ability space.
#
# PORTED IN FROM proto/imposters.py ON 2026-11-06. Until then this module had
# no hero code at all and the ten sides lived only in that prototype, so every
# figure above - the 50.6% pitch included - was measured with NO IMPOSTER
# CHOSEN. That was defensible as a pitch (a side is a delta against a heroless
# baseline) and indefensible as coverage: the centrepiece of the set was the
# one deck the shipping simulator could not play. HERO = None still reproduces
# every published figure, which is the check.
#
# The gates are part of the abilities, not policy decoration. A side the model
# spends unconditionally measures as its WORST case: the Archivist's off-domain
# card read -3.4 ungated, because the model then spends the pool off-domain on
# small Exhibits and strands the big ones. Where a real player would hold an
# ability back, the gate is the model's stand-in for that judgement.
HERO = None
HEROES = ("archivist_a", "archivist_b", "understudy_a", "understudy_b",
          "usher_a", "usher_b", "porter_a", "porter_b",
          "steward_a", "steward_b")
# What each one prints, for the report. proto/imposters.py carries the two
# tests a side had to pass - LEVEL (worth about as much as every other side)
# and UNIFORM (worth about the same at Easy as at a handicapped rung) - and
# the sides that failed them.
HERO_TEXT = {
    "archivist_a": ("The Archivist", "Cross-Referenced", "passive"),
    "archivist_b": ("The Archivist", "Precedent", "once/Scenario"),
    "understudy_a": ("The Understudy", "Open Audition", "once/Scenario"),
    "understudy_b": ("The Understudy", "Second Chair", "twice/Scenario"),
    "usher_a": ("The Usher", "Early Admittance", "once/Scenario"),
    "usher_b": ("The Usher", "Double Doors", "once/Scenario"),
    "porter_a": ("The Porter", "Sleight of Hand", "once/session"),
    "porter_b": ("The Porter", "Heavy Lifting", "once/Scenario"),
    "steward_a": ("The Steward", "Requisition", "once/Scenario"),
    "steward_b": ("The Steward", "Standing Order", "once/Scenario"),
}
# THE IMPOSTER STARTS TIRED, and how tired is the difficulty. These dice
# begin exhausted; they return through ordinary recovery, so the handicap
# costs tempo rather than dice and bites hardest early, when the Dossier is
# full. The RULES name them, so there is no player choice here for this
# module to model badly - an earlier version let the model pick the dice and
# picked worse than random at the hard end.
#
# The counts are deliberately SPREAD across the four colours rather than
# taking whole ones, because whole colours collide with the attention wheel.
# The wheel opens on Yellow with a Yellow+Green window, so "4 yellow, 4
# green" empties the only colours sessions 1 and 2 may apply and reads 28.7%
# against 38.4% for the same eight dice taken off the purple end - a
# ten-point swing decided by the wheel's phase rather than by the handicap.
# Spread, the curve is smooth and the two stay independent.
#
# The single red is never exhausted: session 5 allows only Red and Yellow,
# and there is one red die.
#
# RE-CUT 2026-11-14 against the held Pool and AGAIN 2026-11-16 against a
# scored hand - see THE LADDER in the header for why, and for what the
# second cut cost. The aims are unchanged.
#
#   level      y  g  b  p     n   HP    win     aim
#   Easy       3  3  3  3    12    5   48.7%   -1.3
#   Standard   3  3  4  4    14    5   39.6%   -0.4
#   Hard       3  3  4  4    14    4   33.0%   +3.0
#   Nobulous   3  3  4  4    14    3   22.1%   +2.1
#
# THE DICE STOP AT FOURTEEN, and the rule that stops them is the one this
# file already applies to the red die one session further on. The attention
# opens on Yellow with a Yellow+Green window, so a rung that exhausts every
# yellow AND every green starts with nothing it may APPLY: at sixteen you
# hold one red die, and session 1 is not hard, it is skipped - deploy
# nothing, take nothing, recover 3, begin in session 2. Every rung keeps a
# yellow and a green and therefore opens with two applicable dice. The
# rulebook's own sentence for the other end is the precedent: "the single
# Red die is never exhausted at setup: session 5 allows only Red and
# Yellow, and you own exactly one Red."
#
# SO HEALTH CARRIES THE LAST TWO RUNGS. It is a ceiling and not a point of
# damage - recovery caps at it too - which is both what this module
# measures and the simpler thing to print. One point of it costs 6.6 at
# Hard and 10.9 more at Nobulous, against 6.1 for the fourteenth die, so
# the two axes are the same size and the ladder does not lurch when it
# changes feet.
#
# TWO CANDIDATES WERE MEASURED AND REJECTED. Sixteen dice with 4 Health
# reads 21.5%, lands as well as this and is the version that skips a
# session. A sixteenth Exhibit (6/5/5 rather than 5 a domain) reads 11.5%
# at that cap, eight and a half points past the aim: the Dossier is the
# steepest dial in this file and the only one that cannot be spent a
# fraction of.
#
# THE TOP THREE RUNGS SHARE A DICE ROW, which is what capping the dice
# costs the printed table and is worth saying out loud rather than hiding
# behind a spread that differs for the sake of differing. The story the
# table tells is the true one: the dice run out, and after that it costs
# you Health.
TIRED_COLOURS = ("yellow", "green", "blue", "purple")
LADDER = {"easy": (3, 3, 3, 3), "standard": (3, 3, 4, 4),
          "hard": (3, 3, 4, 4), "nobulous": (3, 3, 4, 4)}
# The second axis. HEALTH is a ceiling in this module, so a rung that
# lowers it lowers what recovery can climb back to as well.
LADDER_HEALTH = {"easy": 5, "standard": 5, "hard": 4, "nobulous": 3}
START_TIRED = LADDER["easy"]

DOMAINS = ("Knowledge", "Physical", "Cover-Up")

# THE FIVE REWARD CARDS. Eight of the 24 Council Tests are printed as
# Rewards; these five pay on success in a currency this finale still has,
# and "if you succeed" reads as "when the Exhibit falls". The other three
# (An Unwelcome Embrace, The Night Watchman's Account, Across the Chamber)
# modify an attempt that no longer exists as a unit, and are not restored.
# Measured at +1.3 points, which is why they cost nothing to put back.
REWARDS = {
    "The Chamber Mechanism": ("dice", 2),       # recover 2 exhausted dice
    "The Sedative Ledger": ("dice", 3),         # recover 3
    "The Vote": ("colour", 1),                  # all exhausted of one colour
    "Tracks in the Yard": ("spread", 2),        # 1 each of two colours
    "The Narrow Stair": ("discount", 1),        # next Exhibit deployed: -1
}
PAY_REWARDS = True
# Which game's retained cards answer which domain. Mirrors the category match
# of the superseded finale, scaled from Targets of 8-10 to Targets of 3-5.
ANSWERS = {"Knowledge": "NAP", "Physical": "BAT", "Cover-Up": "AoS"}

# The attention runs weakest to strongest and round again, as Tainted Grail's
# dial does, and starts on yellow. WINDOW is how many colours it covers: the
# colour it points to plus the next one clockwise. Two is the shipped rule.
# One is unplayable at 0.0%, and three takes the recovery lever off this
# module's own policy: at WINDOW = 3 the finale reads 67.4% on `horizon`
# against 73.0 on `next` and 71.1 on `best`, so looking a session ahead -
# the decision the wheel exists to create - stops being the right read.
WHEEL = ["yellow", "green", "blue", "purple", "red"]
WINDOW = 2


def deck_cards():
    """(name, domain, kind, printed Target) for the 24 Council Tests, read
    from generator/build_nrj.py so the model cannot drift from the cards."""
    import ast
    src = os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "generator", "build_nrj.py")
    with io.open(src, encoding="utf-8") as f:
        tree = ast.parse(f.read())
    for node in tree.body:
        if (isinstance(node, ast.Assign) and len(node.targets) == 1
                and getattr(node.targets[0], "id", "") == "SCEN"):
            out = []
            for row in node.value.elts:
                v = [e.value for e in row.elts[:4] if isinstance(e, ast.Constant)]
                out.append((v[0], v[1], v[2].split(" - ")[-1], v[3]))
            return out
    raise RuntimeError("SCEN not found in generator/build_nrj.py")


import io                                    # noqa: E402  (deck_cards needs it)


def tier3_names():
    """The six Tier III cards each game lays out, by the game that lays them.

    Read from generator/build_nrj.py so the Pool cannot drift from the
    printed cards: NOTES are BAT's Research Notes, DEVIOUS are NAP's Devious
    Opportunities and BACKDOOR are AoS's Backdoor Routines, which is ANSWERS
    read in the other direction. Every name is checked against IMP, the dict
    of printed clauses, so a card that is renamed on one and not the other
    fails here instead of quietly never firing.
    """
    import ast
    src = os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "generator", "build_nrj.py")
    with io.open(src, encoding="utf-8") as f:
        tree = ast.parse(f.read())
    want = {"DEVIOUS": "NAP", "NOTES": "BAT", "BACKDOOR": "AoS"}
    out, imp = {}, []
    for node in tree.body:
        if not (isinstance(node, ast.Assign) and len(node.targets) == 1):
            continue
        who = getattr(node.targets[0], "id", "")
        if who in want:
            out[want[who]] = [r.elts[0].value for r in node.value.elts]
        elif who == "IMP":
            imp = [k.value for k in node.value.keys]
    loose = [n for g in out.values() for n in g if n not in imp]
    if sorted(out) != ["AoS", "BAT", "NAP"] or loose:
        raise RuntimeError("Tier III names out of step with IMP: %r" % loose)
    return out


DECK = deck_cards()
TIER3 = tier3_names()


# WHAT EACH CLAUSE IS WORTH IF PLAYED NOW, read off the table in front of
# you. (Not the obvious word for it, in upper case: check_app_sync greps
# this file for that word to catch the 2026-10-30 spent/unspent split
# coming back, and a comment should not be what trips a tripwire.)
# This is the model's stand-in for the player's judgement, in the same sense
# as the Imposter gates further down: a clause spent in the wrong session
# measures as its worst case, so a model that spent them in hand order would
# report the design as weaker than it is. CARD_PICK = "any" IS that control
# and section 9 prints the gap, which is the honest width of this guess.
#
# The terms are coarse on purpose. Every one of them reads something that is
# face-up - how many dice are exhausted, how much Health is left, whether the
# window covers what is standing - because a player cannot do better either.
CLAUSE_WORTH = {
    # Health, when Health is what is running out.
    "Unexpected Resilience":
        lambda g, s: 3.0 if g.hp <= 2 else 0.3,
    "Successful Integration":
        lambda g, s: 0.9 * max([e.damage for e in s["standing"]] or [0]),
    "Acceptable Losses":
        lambda g, s: 1.4 if g.hp > 2 and s["tired"] >= 2 else 0.0,
    # Dice back, worth what there is to get back.
    "Resource Fork":
        lambda g, s: 0.7 * min(2, s["tired"]),
    "Raid the Supply Cabinet":
        lambda g, s: 0.7 * min(3, s["tired"]),
    "Red Means Go":
        lambda g, s: 1.0 if "red" in window(g.colour()) else 0.0,
    "Garbage Collection":
        lambda g, s: 0.5 + 0.1 * s["hand"],
    # Dice that work, when the window does not cover the table.
    "Definitely Curriculum-Approved":
        lambda g, s: 2.0 if s["short"] else 0.2,
    "Helpful Test Subject":
        lambda g, s: 1.2,
    "Diagnostic Port":
        lambda g, s: 1.1,
    "Root Access":
        lambda g, s: 1.0,
    # Successes outright.
    "Borrow the Master's Notes":
        lambda g, s: 1.8 if s["hand"] >= 4 else 0.0,
    "Cross-Species Compatibility":
        lambda g, s: (1.6 if len(s["standing"]) > 1
                      and any(e.dealt for e in s["standing"]) else 0.0),
    # The Dossier, when the clock is the problem.
    "Extra Credit?":
        lambda g, s: 1.5 if s["pressure"] > 1.0 and s["deck"] else 0.0,
    "Controlled Failure":
        lambda g, s: 1.5 if s["short"] and s["fresh"] > 1 else 0.0,
    "Packet Sniffer":
        lambda g, s: 0.5 if s["deck"] >= 3 else 0.0,
    # The two that are a licence rather than an effect. They score in the
    # middle because the model only reaches for them when the right domain
    # has run out, so the number mostly breaks ties.
    "Nobulous Owes You One":
        lambda g, s: 0.9,
    "Privilege Escalation":
        lambda g, s: 0.9,
}
BY_DOMAIN = {d: [c for c in DECK if c[1] == d] for d in DOMAINS}


def fresh():
    """4 each of purple, blue, green and yellow plus a SINGLE red: 17 unit
    dice (General Rules of Play, p.7)."""
    return [c for c in COLORS for _ in range(4)] + ["red"]


def _nil(g, s):
    """A clause with no entry in CLAUSE_WORTH scores nothing, so adding a
    card without scoring it makes the model ignore it rather than crash."""
    return 0.0


def window(dial):
    i = WHEEL.index(dial)
    out = [dial]
    for step in (1, -1, 2, -2):
        if len(out) >= WINDOW:
            break
        out.append(WHEEL[(i + step) % 5])
    return set(out)


class Exhibit(object):
    __slots__ = ("domain", "target", "dealt", "locked", "name", "kind",
                 "printed")

    def __init__(self, domain, target, name="", kind=""):
        self.domain = domain
        self.name = name
        self.kind = kind
        self.target = target
        # DAMAGE IS PRINTED, AND PRINTING IT IS WHAT FIXES IT. build_nrj.py
        # works it out once per card - "damage = 2 if target >= BIG_TARGET
        # else 1" - and sets it in its own big numeral beside the Target,
        # and rules/nrj.html says "Each Exhibit prints its Target, its
        # Damage and a Reward". So this is the Target AS DEALT and nothing
        # moves it afterwards.
        self.printed = target
        self.dealt = 0          # successes carried over from past sessions
        self.locked = []        # dice held on the card, neither side of the pool

    @property
    def damage(self):
        """What this Exhibit deals every session it is left standing.

        READ OFF THE PRINTED TARGET, NOT THE CURRENT ONE. Until 2026-11-14
        this was `self.target`, which spend_research and The Narrow Stair
        both write to - so answering a Target 5 with one retained card also
        halved its Damage, an effect no card prints and no rule grants. It
        made the Research Pool worth about a third more than it is and it
        is the larger part of why holding the Pool for the endgame measured
        +14, since the whole gain was buying Damage the cards do not sell.
        DAMAGE_TRACKS_TARGET restores it.
        """
        return 2 if (self.target if DAMAGE_TRACKS_TARGET
                     else self.printed) >= BIG else 1

    @property
    def left(self):
        return max(0, self.target - self.dealt)


class Card(object):
    """A retained card in the Research Pool.

    IT HAS A NAME. Until 2026-11-14 it was (game, value) and nothing else,
    which is precisely why the campaign's seven chosen cards reached the
    chamber as three integers and the finale played the same whichever ones
    you carried.
    """
    __slots__ = ("game", "value", "name")

    def __init__(self, game, value, name=""):
        self.game = game
        self.value = value
        self.name = name


def research(rng):
    """The retained Tier III cards, as rules/nrj.html deals them.

    Retained or not, and every retained card is worth the same. The earlier
    scheme paid 2 for a card never spent in its own game and 1 for one that
    was; it was dropped on 2026-10-30 because nothing on the table records
    which a card is, and a campaign can sit for weeks between games.
    """
    if not RESEARCH:
        return []
    out = []
    for game, n in zip(("NAP", "BAT", "AoS"), RETAIN):
        if not CLAUSES:
            # THE DIAL RESTORES THE OLD POOL EXACTLY, down to the random
            # numbers. Naming the cards draws from `rng`, and a draw spent
            # here is a different Dossier three lines later: without this
            # the control read 50.7% where the file had published 50.1%,
            # and nothing but the stream had moved.
            out += [Card(game, CARD_VALUE) for _ in range(n)]
            continue
        # WHICH cards you retained is the campaign's decision, and this model
        # has no campaign in it, so they are dealt at random from the six that
        # game lays out. That is also exactly what the standalone rule does -
        # "the same seven the campaign would have let you choose" - so every
        # clause figure here is the AVERAGE hand and not a chosen one. A
        # campaign that chooses well does better than this file reports.
        names = rng.sample(TIER3[game], min(n, len(TIER3[game])))
        out += [Card(game, CARD_VALUE, nm) for nm in names]
    if FORCE_CLAUSE:
        # Section 9 measures one clause at a time, so that card has to be in
        # the hand. It REPLACES one of its own game's picks rather than being
        # added, or the delta would be a bigger pool as much as a better one.
        for game, names in TIER3.items():
            if FORCE_CLAUSE in names:
                have = [c for c in out if c.game == game]
                if have and not any(c.name == FORCE_CLAUSE for c in have):
                    have[0].name = FORCE_CLAUSE
    return out


def dossier(rng):
    """DEAL Exhibits per domain, Targets dealt from the printed spread.

    The counts are fixed so the finale can be pitched to one number; what the
    campaign varies is the Research Pool. finale9 measured a 30-point
    difficulty swing when the campaign set the counts as well, which is a
    scenario nobody can tune.
    """
    out = []
    per = DEAL if isinstance(DEAL, tuple) else (DEAL,) * 3
    for d, n in zip(DOMAINS, per):
        for name, _, kind, p in rng.sample(BY_DOMAIN[d], min(n, len(BY_DOMAIN[d]))):
            out.append(Exhibit(d, p - TARGET_OFFSET, name, kind))
    rng.shuffle(out)
    return out


class Game(object):
    def __init__(self, rng):
        self.rng = rng
        self.deck = dossier(rng)
        self.pool = research(rng)
        self.active = []
        self.available, self.exhausted = fresh(), []
        self.candidates = sum(LAID_OUT - n for n in RETAIN) if RESEARCH else 0
        self.start_tired()
        self.hp = HEALTH
        self.dial = 0
        self.at = 0
        self.discount = 0          # The Narrow Stair, owed to the next deploy
        self.hero = HERO
        self.once = collections.Counter()    # uses this finale
        self.sess = collections.Counter()    # uses this session
        self.live = set()        # clauses granted this session, by card name
        self.bit = collections.Counter()     # clauses that actually went off

    def start_tired(self):
        """The dice rules/nrj.html names for the chosen difficulty."""
        for colour, n in zip(TIRED_COLOURS, START_TIRED):
            for _ in range(n):
                if colour not in self.available:
                    break
                self.available.remove(colour)
                self.exhausted.append(colour)

    # -- the state a policy may read. All of it is face-up on the table ----
    def colour(self):
        return WHEEL[self.dial % 5]

    def next_colour(self, ahead=1):
        return WHEEL[(self.dial + ahead) % 5]

    def sessions_left(self):
        return SESSIONS - self.at

    def pressure(self):
        """Exhibits left to bury per session remaining. Above 1 means the
        clock is winning and you have to take on more."""
        left = len(self.deck) + len(self.active)
        return left / float(max(1, self.sessions_left()))

    # -- the economy ------------------------------------------------------
    def recover(self, policy, n=None):
        rec = REC_BASE if n is None else n
        if not rec or not self.exhausted:
            return
        if policy == "next":                   # the colour coming up
            nxt = self.next_colour()
            key = {c: (10.0 if c == nxt else EV_REROLL[c]) for c in FACES}
        elif policy == "horizon":              # the next two
            a, b = self.next_colour(1), self.next_colour(2)
            key = {c: EV_REROLL[c] for c in FACES}
            key[a] += 20.0
            key[b] += 10.0
        elif policy == "now":
            cur = self.colour()
            key = {c: (10.0 if c == cur else EV_REROLL[c]) for c in FACES}
        else:                                  # "best": the naive rule
            key = {c: EV_REROLL[c] for c in FACES}
        self.exhausted.sort(key=lambda c: key[c])
        for _ in range(min(rec, len(self.exhausted))):
            self.available.append(self.exhausted.pop())

    def pay_reward(self, e):
        """A Reward Exhibit pays as it falls. Rules: rules/nrj.html, "What
        the Council lets slip"."""
        if not PAY_REWARDS:
            return
        pay = REWARDS.get(e.name)
        if not pay:
            return
        how, n = pay
        if how in ("colour", "spread") and not self.exhausted:
            return                 # nothing exhausted: the Reward pays nothing
        if how == "dice":
            self.recover("next", n)
        elif how == "discount":
            self.discount += n
        elif how == "colour":
            # All exhausted dice of ONE colour: take the colour the next
            # session wants, falling back to whichever there is most of.
            want = self.next_colour()
            if want not in self.exhausted:
                # OVER THE LIST, NOT OVER A SET OF ITS COLOURS. This read
                # max(set(self.exhausted), ...) until 2026-11-14, and a set
                # of STRINGS iterates in an order CPython randomises per
                # process, so a tie between two colours went a different way
                # in different runs. One Random is shared across all 6000
                # games of a cell, so a single tie broken differently
                # re-rolled every game after it and the same seed stopped
                # being the same sample: run(3000, seed=11) read 53.0333 at
                # PYTHONHASHSEED 0 and 53.0667 at 1, and five-seed means
                # moved up to about 0.3 between runs. The list has a fixed
                # order, so the tie now goes to the colour exhausted first.
                want = max(self.exhausted, key=self.exhausted.count)
            for c in [c for c in self.exhausted if c == want]:
                self.exhausted.remove(c)
                self.available.append(c)
        elif how == "spread":
            # One die of each of two colours: the next two on the wheel.
            for want in (self.next_colour(1), self.next_colour(2)):
                if want in self.exhausted:
                    self.exhausted.remove(want)
                    self.available.append(want)

    def reward(self, policy):
        """Rose pays for every enemy you deploy, which is what makes taking
        on more than the clock demands worth considering. Measured against
        the alternatives in the prototype: a die 85.0%, Health 57.1%.
        """
        if policy == "health":
            self.hp = min(HEALTH, self.hp + 1)
            return
        if self.exhausted:
            self.recover("next", 1)
        else:
            self.hp = min(HEALTH, self.hp + 1)

    def clause(self, name):
        """Is the card named `name` granting its Imposter clause right now?

        A clause runs from the moment the card is spent to the end of that
        session, so for sixteen of the eighteen this asks whether the card
        was spent THIS session. The two in SPEND_CLAUSES say how the card may
        be spent and are therefore asked while it is still in the Pool.

        This is the one gate every clause goes through, which is what lets
        coverage.py count call sites rather than table entries.
        """
        if not CLAUSES:
            return False
        if name in SPEND_CLAUSES:
            return any(c.name == name for c in self.pool)
        if name not in self.live:
            return False
        # EVERY GATE IN THIS MODULE ASKS THIS LAST, after the cheap tests, so
        # a True here means the clause did something rather than merely being
        # in play. audit.py counts these: a clause spent often and never
        # recorded is printed, reachable and doing nothing, which is how
        # Cross-Species Compatibility's BAT side was caught one tier up.
        self.bit[name] += 1
        return True

    def short_handed(self):
        """Can the dice this window allows cover what is standing? The same
        question every Imposter gate asks, asked at spend time."""
        ok = window(self.colour())
        return (sum(EV_REROLL[c] for c in self.available if c in ok)
                < sum(e.left for e in self.active))

    def answerable(self, e):
        """The retained cards that may be spent on this Exhibit."""
        want = ANSWERS[e.domain]
        out = [c for c in self.pool if c.game == want]
        # THE ARCHIVIST, Cross-Referenced: "A retained card may answer an
        # Exhibit at Target 5 of ANY domain, not only its own." Gated to the
        # Target 5s on the card, and the gate is load-bearing - ungated it
        # reads -3.4. No use limit: a Dossier holds about four 5s, so a limit
        # never bound and the card reads shorter without one.
        if not out and self.hero == "archivist_a" and e.target >= BIG:
            out = list(self.pool)
        # NOBULOUS OWES YOU ONE: "Spend this on an Exhibit of any domain."
        # The licence is the clause, so it is read off a card still in hand.
        #
        # ONLY WHEN THE DOMAIN HAS RUN OUT, which is the same gate the
        # Archivist's card above gets and for the same reason: offered on
        # every Exhibit it is spent on the first one that comes up and the
        # wild card is gone by session 2, which reads -2.58. A wild card is
        # worth having because of the Exhibit it answers LAST.
        if not out and self.clause("Nobulous Owes You One"):
            out = [c for c in self.pool if c.name == "Nobulous Owes You One"]
        return out

    def table(self):
        """What a player can see, which is all CLAUSE_WORTH is allowed."""
        return {"tired": len(self.exhausted), "hand": len(self.available),
                "deck": len(self.deck), "pressure": self.pressure(),
                "short": self.short_handed(),
                "standing": [e for e in self.active if e.left > 0],
                "fresh": len(self.active)}

    def pick_card(self, cands, policy):
        """Which of them to spend. Every card takes the same CARD_VALUE off
        the Target, so before the clauses this was a coin flip."""
        if CARD_PICK == "any" or not CLAUSES:
            return sorted(cands, key=lambda c: (-c.value if policy == "big"
                                                else c.value))[0]
        s = self.table()
        return max(cands, key=lambda c: CLAUSE_WORTH.get(c.name, _nil)(self, s))

    def hold(self, c, e):
        """Keep this card for a later session instead of spending it now.

        WHEN to spend was never a policy in this file, and that turns out
        to have been the gap that mattered. "small" empties the Pool onto
        the first Exhibits of the right domain, so all seven cards are gone
        by about session 4 - the half of the scenario with the fewest
        Exhibits standing, the most dice to throw at them and the least need
        of help. Holding is legal: Deploy takes "any number, including
        none", Strategy says "Nothing is compulsory", and nothing anywhere
        makes answering an Exhibit mandatory.

        IT DOES NOT ASK WHETHER THE CLAUSES ARE ON, AND THAT IS A
        LIABILITY WITH THEM OFF. The timing was found as a fact about the
        policy grid - worth +13.3 on a pool of flat -2s with nothing
        exhausted - but the ladder was then re-cut twice, and at the Easy
        rung that ships, holding a FLAT pool reads 13.6% against 26.3% for
        spending at once. Holding pays because CLAUSE_WORTH can tell a
        card worth saving from one worth spending now; with CLAUSES =
        False this returns True for everything and loses 12.7 points. So
        the control that reproduces the pre-2026-11-14 model is BOTH
        dials - CLAUSES = False and res = "small" - which is the baseline
        row section 9 prints. (CARD_PICK is the third dial for the figures
        published after it, but not for this baseline: with CLAUSES =
        False, pick_card short-circuits and the hand is unscored whatever
        CARD_PICK says. "+19" stood here until 2026-11-14 and was never
        measured at all: a first reading taken while Damage was still
        being recomputed from the Target.)

        THIS IS THE DEFAULT SINCE 2026-11-14, and the ladder is cut against
        it: res = "small" with CARD_PICK = "any" reproduces every figure
        published before that.

        A card is never stranded. Past HOLD_LAST the policy spends
        everything, and an Exhibit at BIG or above is always worth
        answering now.
        """
        if self.sessions_left() <= HOLD_LAST or e.target >= BIG:
            return False
        if not CLAUSES:
            return True
        return CLAUSE_WORTH.get(c.name, _nil)(self, self.table()) < HOLD_FLOOR

    def fire_clause(self, e, fresh):
        """The clauses that act the moment the card is spent.

        Each is guarded by its own session counter rather than by which card
        was just spent: the question is "has this clause gone off yet this
        session", and `clause()` is the only thing that says whether it is
        live at all. The other eleven are read where they bite.
        """
        s = self.sess
        # RESOURCE FORK: "Recover 2 exhausted dice." AoS prints this one word
        # for word as a Reward, which is why it needed no translating.
        if not s["fork"] and self.exhausted and self.clause("Resource Fork"):
            s["fork"] = 1
            self.recover("next", 2)
        # ACCEPTABLE LOSSES: "Lose 1 Health to recover 2 exhausted dice."
        # Never down to 1 Health: the Exhibits still standing deal their
        # Damage at the end of this same session.
        if (not s["loss"] and self.hp > 2 and len(self.exhausted) >= 2
                and self.clause("Acceptable Losses")):
            s["loss"] = 1
            self.hp -= 1
            self.recover("next", 2)
        # BORROW THE MASTER'S NOTES: "Exhaust 2 available dice of any color to
        # place 2 successes on an Exhibit you just deployed." The two weakest
        # dice, since the successes are certain and a roll is not.
        # NOT UNCONDITIONALLY: ungated this reads -1.15, because two dice go
        # down to place successes on an Exhibit that was going to fall
        # anyway. Paid only with a deep hand and only where 2 successes are
        # all needed - e.target is what is left after the card's own -2.
        if (not s["borrow"] and len(self.available) >= 4 and e.target >= 2
                and self.clause("Borrow the Master's Notes")):
            s["borrow"] = 1
            for c in sorted(self.available, key=lambda c: EV_REROLL[c])[:2]:
                self.available.remove(c)
                self.exhausted.append(c)
            e.dealt += 2
        # PACKET SNIFFER: "Look at the top 3 cards of the Dossier and return
        # them in any order." The Dossier is popped from the end, so the
        # smallest Target goes last and is deployed first.
        # THE BIGGEST TARGET FIRST, not the smallest. Damage on a standing
        # Exhibit carries over, so a 5 met early is chipped over several
        # sessions while a 5 turned up last has one session to fall in -
        # and the Dossier sits one Exhibit above a cliff. Sorted the
        # comfortable way round it reads -0.88.
        if (not s["sniff"] and len(self.deck) >= 2
                and self.clause("Packet Sniffer")):
            s["sniff"] = 1
            top = self.deck[-3:]
            top.sort(key=lambda x: x.target)
            self.deck[-len(top):] = top
        # CROSS-SPECIES COMPATIBILITY: "Move the dice lying on one standing
        # Exhibit to another standing Exhibit, successes and all." Progress
        # stranded on the Exhibit furthest from falling goes to the one
        # nearest it, which is how a stalled card gets finished.
        if not s["xspec"]:
            got = [x for x in self.active if x.dealt > 0 and x.left > 0]
            src = max(got, key=lambda x: x.left) if got else None
            rest = [x for x in self.active
                    if src is not None and x is not src and x.left > 0]
            if rest and self.clause("Cross-Species Compatibility"):
                s["xspec"] = 1
                dst = min(rest, key=lambda x: x.left)
                dst.dealt += src.dealt
                dst.locked += src.locked
                src.dealt, src.locked = 0, []
        # CONTROLLED FAILURE: "Place a different Exhibit you just deployed on
        # the bottom of the Dossier." The biggest of the others, so this
        # session's Damage and this session's dice both get easier.
        # THE MOST DANGEROUS CLAUSE IN THE POOL, and the one that needed the
        # hardest gate: ungated it reads -7.45. An Exhibit put back is not
        # an Exhibit avoided, it is an Exhibit moved to the END of a 9-session
        # clock that already sits one Exhibit above a cliff. So it is only
        # worth taking when this session cannot cover what is on the table
        # AND there are sessions enough to meet it again.
        if not s["ctrl"] and self.short_handed() and self.sessions_left() > 2:
            others = [x for x in fresh
                      if x is not e and x in self.active and x.dealt == 0]
            if others and self.clause("Controlled Failure"):
                s["ctrl"] = 1
                back = max(others, key=lambda x: x.target)
                fresh.remove(back)
                self.active.remove(back)
                self.deck.insert(0, back)
        # EXTRA CREDIT?: "Deploy 1 more Exhibit now, recovering 2 dice for it
        # rather than 1. You may answer it as well." It joins `fresh`, so the
        # loop that called this comes back round to it.
        if not s["extra"] and self.deck and self.clause("Extra Credit?"):
            s["extra"] = 1
            x = self.deck.pop()
            if self.discount:
                x.target = max(1, x.target - self.discount)
                self.discount = 0
            self.active.append(x)
            fresh.append(x)
            if self.exhausted:
                self.recover("next", 2)
            else:
                self.hp = min(HEALTH, self.hp + 1)

    def spend_research(self, fresh_exhibits, policy):
        """A retained card removes 1 from an Exhibit of its own domain, or 2
        if it was never spent in its own game. Only just-deployed Exhibits
        can be answered: once the Council has heard the evidence, producing
        your credentials is too late.
        """
        if policy == "none" or not self.pool:
            return
        # A WORKLIST RATHER THAN A SORTED PASS, because two clauses change
        # what is on the table while it is being answered: Extra Credit? adds
        # an Exhibit you may then answer, and Controlled Failure takes one
        # away. Over an unchanging list this is the pass it replaces, since
        # the Exhibits it has not reached yet still hold their dealt Targets.
        done = set()
        while self.pool:
            todo = [x for x in fresh_exhibits
                    if x in self.active and id(x) not in done and x.target > 1]
            if not todo:
                break
            e = max(todo, key=lambda x: x.target)
            done.add(id(e))
            while e.target > 1:
                cands = self.answerable(e)
                if not cands:
                    break
                if policy == "big" and e.target < BIG:
                    break          # hoard everything for the Target 5s
                c = self.pick_card(cands, policy)
                if policy == "time" and self.hold(c, e):
                    break          # its session has not come up yet
                if c.game != ANSWERS[e.domain] and c.name in SPEND_CLAUSES:
                    # The wild card actually used as one. `clause()` cannot
                    # record this: for a SPEND_CLAUSE it answers "held", and
                    # held is not used.
                    self.bit[c.name] += 1
                e.target = max(1, e.target - c.value)
                self.pool.remove(c)
                self.live.add(c.name)
                self.fire_clause(e, fresh_exhibits)
                if policy != "dump":
                    break          # one card an Exhibit unless told otherwise
        # PRIVILEGE ESCALATION: "Spend this on an Exhibit deployed in an
        # earlier session." The only card that reaches a standing Exhibit at
        # all - everything else in the Pool is too late the moment the
        # Council has heard the evidence.
        # ONLY WHEN IT HAS NOWHERE ELSE TO GO. The licence is for a card the
        # ordinary rule strands - no Exhibit of its own domain deployed this
        # session - and spending it on a standing Exhibit the moment one
        # exists throws the -2 at a card that was going to fall anyway: -0.98
        # ungated. The Exhibit has to need the whole 2, as well.
        held = [x for x in self.pool if x.name == "Privilege Escalation"]
        if held and policy != "big":
            c = held[0]
            own = [x for x in fresh_exhibits
                   if x in self.active and ANSWERS[x.domain] == c.game
                   and x.target > 1]
            older = [x for x in self.active
                     if x not in fresh_exhibits and x.left >= 2]
            if older and not own and self.clause("Privilege Escalation"):
                e = max(older, key=lambda x: x.left)
                e.target = max(1, e.target - c.value)
                self.pool.remove(c)
                self.live.add(c.name)
                self.bit[c.name] += 1


def how_many(g, pace):
    """Rose's decision: how many Exhibits to take on this session."""
    room = len(g.deck)
    if not room:
        return 0
    if pace in ("one", "two", "three"):
        return min(room, {"one": 1, "two": 2, "three": 3}[pace])
    if pace == "all":
        return room
    # "ceil" never leaves more behind than the sessions that are left can
    # clear. "clock" rounds the same quantity instead, which looks equivalent
    # and is not - at a pressure just over 1 it deploys one a session, falls
    # quietly behind, and meets the whole remainder in the last session. That
    # made the win rate fall as the clock got LONGER, which is how the
    # rounding was caught; proto/finale10.py's pacing figures carry it.
    if pace == "ceil":
        n = int(math.ceil(len(g.deck) / float(max(1, g.sessions_left()))))
        n -= len(g.active)
    else:
        n = int(round(g.pressure() - len(g.active)))
    if pace == "throttle":
        if g.hp <= 2 and n > 1:
            n -= 1
        if g.hp >= HEALTH and not g.active and room:
            n += 1
    return min(room, max(0, n))


def want_dice(g, pool, policy):
    """How many of the usable dice to commit. An allowed die you commit and
    do not need is simply burned, so this is a lever in its own right - and
    the reason to hold dice back is that next session's colour is already
    visible on the wheel."""
    pool = sorted(pool, key=lambda c: -EV_REROLL[c])
    if policy == "all":
        return pool
    need = sum(e.left for e in g.active)
    margin = 1.0 if (policy == "adaptive" and g.hp <= 2) else 0.0
    out, got = [], 0.0
    for c in pool:
        if got >= need + margin:
            break
        out.append(c)
        got += EV_REROLL[c]
    return out


def session(g, pace, recov, rew, commit, res):
    g.sess.clear()
    g.live.clear()          # a clause lasts to the end of the session, no more
    taken = []
    for _ in range(how_many(g, pace)):
        e = g.deck.pop()
        if g.discount:                      # The Narrow Stair, if one is owed
            e.target = max(1, e.target - g.discount)
            g.discount = 0
        taken.append(e)
        g.active.append(e)
        g.reward(rew)
    g.spend_research(taken, res)

    ok = window(g.colour())
    # Every gate below asks the same question - can the dice this window
    # allows cover what is on the table? - because that is the session a
    # player holds a once-a-Scenario ability for.
    def short():
        return (sum(EV_REROLL[c] for c in g.available if c in ok)
                < sum(e.left for e in g.active))

    # THE USHER, Double Doors: "For one session, the attention covers a THIRD
    # color - one step beyond its usual two."
    if g.hero == "usher_b" and not g.once["dd"] and g.active and short():
        g.once["dd"] = 1
        ok = ok | {g.next_colour(WINDOW)}
    # THE USHER, Early Admittance: "Apply 1 die of the color ONE STEP BEYOND
    # the attention's two colors." One die, not a window.
    outside = 0
    if g.hero == "usher_a" and not g.once["adm"] and g.active and short():
        g.once["adm"] = 1
        outside = 1
    phases = STRAT
    # THE STEWARD, Standing Order: "Take a third Strategy phase this session."
    if g.hero == "steward_b" and not g.once["str"] and g.active and short():
        g.once["str"] = 1
        phases += 1
    spent = collections.Counter()       # committed from the pool this session
    applied = collections.Counter()     # ...of which these landed on a card
    requisitioned = []                  # the Steward's, already exhausted
    unapplied = []

    for _ in range(phases):
        if not g.active or all(e.left <= 0 for e in g.active):
            break
        # RAID THE SUPPLY CABINET: "Before a Strategy roll, recover 3 dice,
        # or all of one non-Red color." The colour branch only beats the
        # three when more than three of one colour are down, which is what
        # makes it a choice instead of a bigger number.
        if (not g.sess["raid"] and g.exhausted and short()
                and g.clause("Raid the Supply Cabinet")):
            g.sess["raid"] = 1
            most = max(COLORS, key=g.exhausted.count)
            if g.exhausted.count(most) > 3:
                for c in [c for c in g.exhausted if c == most]:
                    g.exhausted.remove(c)
                    g.available.append(c)
            else:
                g.recover(recov, 3)
        # DEFINITELY CURRICULUM-APPROVED: "Ignore the attention's color
        # restriction for one Strategy roll this session." Held for a phase
        # the window cannot cover, which is the phase it is printed for.
        allow = ok
        if (not g.sess["curric"] and short()
                and g.clause("Definitely Curriculum-Approved")):
            g.sess["curric"] = 1
            allow = set(FACES)
        usable = [c for c in g.available if c in allow]
        take = want_dice(g, usable, commit)
        for c in take:
            g.available.remove(c)
            spent[c] += 1
        # THE ARCHIVIST, Precedent: "Apply 1 die of ANY color, ignoring the
        # attention entirely."
        if g.hero == "archivist_b" and not g.once["prec"]:
            pick = [c for c in g.available if c not in ok]
            if pick:
                g.once["prec"] = 1
                c = max(pick, key=lambda c: EV_REROLL[c])
                g.available.remove(c)
                spent[c] += 1
                take = take + [c]
        if outside:
            # Not a free choice of colour: the one the attention reaches
            # next, which is the one the player can see coming.
            soon = g.next_colour(WINDOW)
            extra = [c for c in g.available if c == soon][:outside]
            for c in extra:
                g.available.remove(c)
                spent[c] += 1
            take = take + extra
            outside = 0
        # THE STEWARD, Requisition: "Commit 1 EXHAUSTED die of a color the
        # attention allows. It remains exhausted afterward." `spent` carries
        # it without `applied`, so the bookkeeping below puts it back.
        if g.hero == "steward_a" and not g.once["req"] and short():
            pick = [c for c in g.exhausted if c in ok]
            if pick:
                g.once["req"] = 1
                c = max(pick, key=lambda c: EV_REROLL[c])
                g.exhausted.remove(c)
                spent[c] += 1
                requisitioned.append(c)
                take = take + [c]
        rolling = unapplied + take
        if not rolling:
            break
        unapplied = []
        hits = []
        for c in rolling:
            v = roll(c, g.rng)
            if v:
                hits.append((c, v))
            else:
                unapplied.append(c)
        # DIAGNOSTIC PORT: "Reroll one entire Strategy roll." The WHOLE roll,
        # hits and all, so it is only worth taking when most of it missed -
        # which is the gate, and the difference between this and the two
        # Understudy sides that reroll misses alone.
        if (not g.sess["diag"] and len(unapplied) * 2 > len(rolling)
                and g.clause("Diagnostic Port")):
            g.sess["diag"] = 1
            hits, again, unapplied = [], list(rolling), []
            for c in again:
                v = roll(c, g.rng)
                if v:
                    hits.append((c, v))
                else:
                    unapplied.append(c)
        # THE UNDERSTUDY, Open Audition: "Discard 4 Candidates to reroll EVERY
        # committed die that applied nothing this Strategy phase." Held for a
        # phase with something to reroll.
        if (g.hero == "understudy_a" and not g.once["aud"]
                and len(unapplied) >= 2 and g.candidates >= 4):
            g.candidates -= 4
            g.once["aud"] = 1
            again, unapplied = unapplied, []
            for c in again:
                v = roll(c, g.rng)
                if v:
                    hits.append((c, v))
                else:
                    unapplied.append(c)
        # THE UNDERSTUDY, Second Chair: "Discard 2 Candidates to reroll one
        # committed die that applied nothing." Twice a Scenario.
        if (g.hero == "understudy_b" and g.once["chair"] < 2
                and unapplied and g.candidates >= 2):
            g.candidates -= 2
            g.once["chair"] += 1
            c = max(unapplied, key=lambda c: EV_REROLL[c])
            unapplied.remove(c)
            v = roll(c, g.rng)
            if v:
                hits.append((c, v))
            else:
                unapplied.append(c)
        # HELPFUL TEST SUBJECT: "After a Strategy roll, reroll any number of
        # misses." All of them: a miss rerolled costs nothing.
        if (not g.sess["helpful"] and unapplied
                and g.clause("Helpful Test Subject")):
            g.sess["helpful"] = 1
            again, unapplied = unapplied, []
            for c in again:
                v = roll(c, g.rng)
                if v:
                    hits.append((c, v))
                else:
                    unapplied.append(c)
        # ROOT ACCESS: "Treat one missed die as a Crit." Last of the four, so
        # it is not spent on a die one of the rerolls above would have saved.
        if not g.sess["root"] and unapplied and g.clause("Root Access"):
            g.sess["root"] = 1
            c = max(unapplied, key=lambda c: EV_REROLL[c])
            unapplied.remove(c)
            hits.append((c, 2))
        # Spend the biggest results on whatever is closest to falling, so a
        # Crit is not stranded on a card that needed one success.
        for c, v in sorted(hits, key=lambda x: -x[1]):
            tgt = None
            for e in sorted(g.active, key=lambda e: e.left):
                if e.left > 0:
                    tgt = e
                    break
            if tgt is None:
                # A HIT WITH NOWHERE TO GO, which happens when the last
                # standing Exhibit fell earlier in this same loop. It
                # joins `unapplied` and is NEVER rethrown: the phase
                # loop's own guard breaks the moment nothing is
                # standing, so the die is simply exhausted below.
                #
                # This is why nrj.html says "take up the dice that
                # missed": the sentence used to say "any dice you have
                # not applied", which is broader than 20 Strong AND
                # broader than this - measured 2026-11-10 over 4000
                # finales, 15,812 hits had nowhere to go and not one
                # was rethrown. The book was reworded to match rather
                # than the model to match the book.
                unapplied.append(c)
                continue
            tgt.dealt += v
            tgt.locked.append(c)
            applied[c] += 1

    # Every Exhibit still standing deals its Damage.
    standing = [e for e in g.active if e.left > 0]
    dmg = sum(e.damage for e in standing)
    # SUCCESSFUL INTEGRATION: "Ignore the Damage of one standing Exhibit at
    # this session's Resolve." The one that deals most, which is the whole of
    # the choice.
    if standing and g.clause("Successful Integration"):
        dmg -= max(e.damage for e in standing)
    g.hp -= dmg
    # UNEXPECTED RESILIENCE: "The first time Damage would take you to 0 Health
    # this session, you remain at 1." Once, and it does not stop the NEXT
    # session's Damage, which is why it is worth less than a Health.
    if g.hp <= 0 and not g.sess["resil"] and g.clause("Unexpected Resilience"):
        g.sess["resil"] = 1
        g.hp = 1
    if g.hp <= 0:
        return False

    # Exhaust committed dice that did not land, plus every die held on an
    # Exhibit that has now fallen. Dice on something still standing are
    # neither exhausted nor available - the published rule.
    #
    # GARBAGE COLLECTION: "At this session's Resolve, committed dice that
    # applied nothing do not exhaust." RED MEANS GO: "Red does not exhaust
    # this session." Both are read here because this is the only place a die
    # in this model ever exhausts.
    leftover = list((spent - applied).elements())
    keep_missed = bool(leftover) and g.clause("Garbage Collection")
    for c in requisitioned:
        # The Steward's Requisition die was ALREADY exhausted when it was
        # committed and stays exhausted. No clause hands that one back.
        if c in leftover:
            leftover.remove(c)
            g.exhausted.append(c)
    for c in leftover:
        if keep_missed or (c == "red" and g.clause("Red Means Go")):
            g.available.append(c)
        else:
            g.exhausted.append(c)
    buried = [e for e in g.active if e.left <= 0]
    g.active = [e for e in g.active if e.left > 0]
    for e in buried:
        for c in e.locked:
            if c == "red" and g.clause("Red Means Go"):
                g.available.append(c)
            else:
                g.exhausted.append(c)
        e.locked = []
    # Rewards pay AFTER the dice come back, so "recover 2" can take the
    # very dice that just buried the card.
    for e in buried:
        g.pay_reward(e)
    # THE PORTER, Heavy Lifting: "Exhaust 1 available die, then recover 2
    # exhausted dice." The SIGN of the conversion is what makes it an ability
    # rather than a difficulty dial - paying 1 to get 2 reads +1.2, while
    # paying 1 to apply 1 out-of-colour die reads -10.1 even gated, because it
    # nets a die DOWN. See proto/imposters.py.
    if (g.hero == "porter_b" and not g.once["lift"]
            and len(g.exhausted) >= 2 and g.available):
        g.once["lift"] = 1
        drop = min(g.available, key=lambda c: EV_REROLL[c])
        g.available.remove(drop)
        g.exhausted.append(drop)
        g.recover(recov, 2)
    # THE PORTER, Sleight of Hand: "Take 1 die lying on a standing Exhibit and
    # exhaust it. That Exhibit keeps its successes." In time for this
    # session's recovery, which is the whole point of it.
    if g.hero == "porter_a":
        for e in g.active:
            if e.locked:
                g.exhausted.append(e.locked.pop())
                break
    if not CARRY:
        for e in g.active:                  # the control: progress resets
            g.exhausted += e.locked
            e.locked = []
            e.dealt = 0

    g.recover(recov)
    g.dial += 1
    g.at += 1
    return True


def play(rng, pace="clock", recov="horizon", rew="dice", commit="adaptive",
         res="time"):
    g = Game(rng)
    for _ in range(SESSIONS):
        if not g.deck and not g.active:
            return True
        if not session(g, pace, recov, rew, commit, res):
            return False
    return not g.deck and not g.active


KW = ("pace", "recov", "rew", "commit", "res")
DIALS = ("SESSIONS", "DEAL", "HEALTH", "STRAT", "REC_BASE", "BIG", "CARRY",
         "RESEARCH", "RETAIN", "CARD_VALUE", "LAID_OUT", "HERO",
         "START_TIRED", "TARGET_OFFSET", "WINDOW", "PAY_REWARDS",
         "CLAUSES", "CARD_PICK", "FORCE_CLAUSE", "DAMAGE_TRACKS_TARGET",
         "HOLD_FLOOR", "HOLD_LAST")


def run(games=GAMES, seed=11, **over):
    kw = {k: over.pop(k) for k in list(over) if k in KW}
    bad = [k for k in over if k not in DIALS]
    if bad:
        raise TypeError("unknown dial(s): %s" % ", ".join(bad))
    saved = {k: globals()[k] for k in over}
    globals().update(over)
    rng = random.Random(seed)
    try:
        return 100.0 * sum(1 for _ in range(games) if play(rng, **kw)) / games
    finally:
        globals().update(saved)


def check_components():
    """The printed Targets this module assumes are the ones on the cards."""
    import ast
    import io
    src = os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "generator", "build_nrj.py")
    with io.open(src, encoding="utf-8") as f:
        tree = ast.parse(f.read())
    scen = None
    for node in tree.body:
        if (isinstance(node, ast.Assign) and len(node.targets) == 1
                and getattr(node.targets[0], "id", "") == "SCEN"):
            scen = [[e.value for e in row.elts[:4]
                     if isinstance(e, ast.Constant)] for row in node.value.elts]
    if scen is None:
        return "SCEN not found in generator/build_nrj.py"
    by = collections.defaultdict(list)
    for row in scen:
        by[row[1]].append(row[3])
    out = []
    for d in DOMAINS:
        got = sorted(by[d])
        out.append("%s %s" % (d, "ok" if got == PRINTED else "MISMATCH %s" % got))
    return "; ".join(out)


PACES = ("one", "two", "three", "all", "clock", "ceil", "throttle")
RECOVS = ("best", "now", "next", "horizon")
COMMITS = ("all", "adaptive")
RESES = ("none", "small", "big", "dump", "time")


if __name__ == "__main__":
    def band(w):
        return "*" if 47.0 <= w <= 57.0 else " "

    total = sum(DEAL) if isinstance(DEAL, tuple) else DEAL * 3
    print("THE IMPOSTER FINALE - the attention rotates, and you set the pace")
    print("=" * 74)
    print("%d finales a cell. %d Exhibits, %d sessions, 17 dice, "
          "Targets %d/%d/%d." % (GAMES, total, SESSIONS, 8 - TARGET_OFFSET,
                                 9 - TARGET_OFFSET, 10 - TARGET_OFFSET))
    print("printed Targets: %s" % check_components())
    print("* marks the 47-57% community band, whose mean is 53.0%.")

    print()
    print("1. THE PITCH")
    print("   Five seeds, because one is not a pitch: a single %d-game cell"
          % GAMES)
    print("   lands about a point either side of the mean.")
    seeds = SEEDS
    for lab, over in (("as it ships", {}),
                      ("without the five Reward cards", {"PAY_REWARDS": False}),
                      ("without the Research Pool", {"RESEARCH": False}),
                      ("played blind", dict(recov="best", pace="two",
                                            commit="all", res="none"))):
        ws = [run(seed=sd, **over) for sd in seeds]
        mean = sum(ws) / len(ws)
        print("   %-32s %6.1f%%%s  [%s]"
              % (lab, mean, band(mean),
                 " ".join("%.1f" % w for w in ws)))
        sys.stdout.flush()

    print()
    print("2. THE SKILL LAYER - every input face-up, none of it remembered")
    prev = None
    # EVERY STEP BUT THE LAST PINS CARD_PICK = "any". The steps are
    # cumulative, so once "clause" became the default on 2026-11-16 they
    # would all have inherited a scored hand and the ladder would have
    # measured the same thing six times with a different label on it.
    # Choosing WHICH card is a skill step of its own, and it is the one
    # the shipped policy ends on.
    for lab, kw in (("played as the old finale was", dict(
                         recov="best", pace="two", commit="all", res="none",
                         CARD_PICK="any")),
                    ("+ spend the Research Pool", dict(
                         recov="best", pace="two", commit="all", res="small",
                         CARD_PICK="any")),
                    ("+ keep pace with the clock", dict(
                         recov="best", pace="clock", commit="all",
                         res="small", CARD_PICK="any")),
                    ("+ recover the colour coming up", dict(
                         recov="next", pace="clock", commit="all",
                         res="small", CARD_PICK="any")),
                    ("+ commit only what you need", dict(
                         recov="next", pace="clock", commit="adaptive",
                         res="small", CARD_PICK="any")),
                    ("+ hold it for the session it pays", dict(
                         recov="next", pace="clock", commit="adaptive",
                         res="time", CARD_PICK="any")),
                    ("+ spend the card the table wants", dict(
                         recov="next", pace="clock", commit="adaptive",
                         res="time", CARD_PICK="clause"))):
        w = run(**kw)
        print("   %-32s %7.1f%%%s%s"
              % (lab, w, band(w),
                 "" if prev is None else "  %+.1f" % (w - prev)))
        prev = w
        sys.stdout.flush()

    print()
    print("3. IS THE PACE A LIVE DECISION? the replay question.")
    print("   A fixed pace is what a solved scenario looks like.")
    paced = {}
    for p in PACES:
        w = paced[p] = run(pace=p)
        print("   %-32s %7.1f%%%s" % ("pace: " + p, w, band(w)))
        sys.stdout.flush()

    print()
    print("4. THE OTHER THREE DECISIONS")
    gaps = {}
    for lab, key, vals in (("recover", "recov", RECOVS),
                           ("commit", "commit", COMMITS),
                           ("Research", "res", RESES)):
        ws = [run(**{key: v}) for v in vals]
        gaps[lab] = max(ws) - min(ws)
        print("   %-10s" % lab + "  ".join("%s %.1f%%" % (v, w)
                                           for v, w in zip(vals, ws))
              + "   gap %.1f" % gaps[lab])
        sys.stdout.flush()

    print()
    print("5. THE DIALS - one step each")
    dial = {}
    for lab, over in (("as it ships", {}),
                      ("8 sessions (ends on blue)", {"SESSIONS": 8}),
                      ("10 sessions (ENDS ON RED)", {"SESSIONS": 10}),
                      ("12 Exhibits, 4 per domain", {"DEAL": 4}),
                      ("13 Exhibits (5/4/4)", {"DEAL": (5, 4, 4)}),
                      ("14 Exhibits (5/5/4)", {"DEAL": (5, 5, 4)}),
                      ("16 Exhibits (6/5/5)", {"DEAL": (6, 5, 5)}),
                      ("18 Exhibits, 6 per domain", {"DEAL": 6}),
                      ("3 Health", {"HEALTH": 3}),
                      ("4 Health", {"HEALTH": 4}),
                      ("6 Health", {"HEALTH": 6}),
                      ("REC 2", {"REC_BASE": 2}),
                      ("REC 4", {"REC_BASE": 4}),
                      ("REC 5", {"REC_BASE": 5}),
                      ("STR 3", {"STRAT": 3}),
                      ("one-colour attention", {"WINDOW": 1}),
                      ("three-colour attention", {"WINDOW": 3}),
                      ("Targets 2/3/4", {"TARGET_OFFSET": 6}),
                      ("Damage 2 at Target 4+", {"BIG": 4}),
                      ("damage resets each session", {"CARRY": False}),
                      ("no Reward cards", {"PAY_REWARDS": False})):
        w = dial[lab] = run(**over)
        print("   %-32s %7.1f%%%s" % (lab, w, band(w)))
        sys.stdout.flush()

    print()
    print("6. THE RESEARCH POOL")
    print("   A card is retained or it is not, and every retained card takes")
    print("   %d off one Exhibit's Target. The spent/unspent split was dropped"
          % CARD_VALUE)
    print("   on 2026-10-30: nothing on the table records which a card is,")
    print("   and a campaign can sit for weeks between games. So the pool is")
    print("   now just a COUNT, and seven is the count that reads 50%.")
    print("   %-26s %8s %8s" % ("NAP/BAT/AoS retained", "worth 1", "worth 2"))
    for r in ((1, 1, 1), (2, 2, 1), (2, 2, 2), (3, 2, 2), (3, 3, 2),
              (3, 3, 3)):
        a = sum(run(seed=sd, RETAIN=r, CARD_VALUE=1)
                for sd in seeds) / len(seeds)
        b = sum(run(seed=sd, RETAIN=r, CARD_VALUE=2)
                for sd in seeds) / len(seeds)
        print("   %-26s %7.1f%% %7.1f%%%s"
              % ("%d/%d/%d" % r, a, b,
                 "   <- shipped" if r == RETAIN else ""))
        sys.stdout.flush()
    w0 = sum(run(seed=sd, RESEARCH=False) for sd in seeds) / len(seeds)
    print("   %-26s %7s  %7.1f%%" % ("no retained cards", "", w0))
    print()
    print("   Eight cards worth 1.5 each beat six worth 2, on the same total")
    print("   reduction: spreading across more Exhibits pays better than")
    print("   concentrating, and more cards cover the three domains better.")
    print("   That is why dropping to one value needed the COUNTS re-derived")
    print("   rather than the values doubled.")

    print()
    print("7. THE FIVE IMPOSTERS - who you are pretending to be")
    print("   Ported in from proto/imposters.py on 2026-11-06; before that")
    print("   this module had no hero code, so every figure above was")
    print("   measured with no Imposter chosen. HERO = None still is the")
    print("   pitch - a side is quoted as a DELTA against it - but the ten")
    print("   printed abilities are now in the shipping simulator.")
    nohero = sum(run(seed=sd) for sd in seeds) / len(seeds)
    print("   %-12s %-18s %-14s %7s %7s"
          % ("Imposter", "side", "when", "win", "delta"))
    print("   %-12s %-18s %-14s %6.1f%%" % ("-", "no Imposter", "", nohero))
    for h in HEROES:
        who, side, when = HERO_TEXT[h]
        w = sum(run(seed=sd, HERO=h) for sd in seeds) / len(seeds)
        print("   %-12s %-18s %-14s %6.1f%%%s  %+.1f"
              % (who.replace("The ", ""), side, when, w, band(w), w - nohero))
        sys.stdout.flush()

    print()
    print("8. THE DIFFICULTY LADDER - dice exhausted at setup")
    print("   The rules name the dice, so there is no choice to model. The")
    print("   counts are spread across the colours on purpose: taking whole")
    print("   ones collides with the wheel, which opens Yellow+Green, and")
    print("   '4 yellow 4 green' reads 28.7% against 38.4% for the same")
    print("   eight dice taken off the purple end. The red is never taken.")
    print("   AND SINCE 2026-11-16 THE DICE ARE NOT THE WHOLE DIAL. They")
    print("   stop at fourteen, because the attention opens Yellow+Green")
    print("   and a rung that takes every yellow AND every green opens")
    print("   with nothing it may apply - at sixteen you hold one red die")
    print("   and session 1 is skipped rather than hard. Every rung keeps")
    print("   a yellow and a green. Health carries the last two: a")
    print("   ceiling, not a point of damage, since recovery caps on it.")
    print("   %-10s %-14s %4s %3s %8s %7s" % ("level", "y  g  b  p", "n",
                                              "HP", "win", "aim"))
    aims = {"easy": 50, "standard": 40, "hard": 30, "nobulous": 20}
    for lab in ("easy", "standard", "hard", "nobulous"):
        c = LADDER[lab]
        x = sum(run(seed=sd, START_TIRED=c, HEALTH=LADDER_HEALTH[lab])
                for sd in seeds) / len(seeds)
        print("   %-10s %-14s %4d %3d %7.1f%%%s  %3d%%  %+.1f"
              % (lab.title(), "%d  %d  %d  %d" % c, sum(c),
                 LADDER_HEALTH[lab], x, band(x), aims[lab], x - aims[lab]))
        sys.stdout.flush()
    print()
    print("   AND WHETHER THE RUNGS ARE STILL GAMES OF SKILL. A tier where")
    print("   no policy beats another is not a harder puzzle, it is a worse")
    print("   one, so every rung is measured with its own gaps. This is the")
    print("   property that chose this dial: the RECOVERY decision, which is")
    print("   what the attention wheel exists to create, pays MORE as the")
    print("   ladder gets harder.")
    print("   CARDS is the gap this dial gained on 2026-11-16: how much")
    print("   scoring the hand beats spending whatever came up. It is the")
    print("   one lever that rests on a table this project invented, so")
    print("   section 9 tests it by dealing that table to the wrong cards.")
    print("   RESEARCH IS THE ONE THAT CHANGES SIGN, and a negative figure")
    print("   there is not a typo: it is how much spending the Pool at once")
    print("   would BEAT the policy this module plays at that rung. Holding")
    print("   is worth most at Easy and turns negative by Nobulous, so no")
    print("   single res is best on all four rungs - see THE LADDER in the")
    print("   header. Nothing exhausted is not a rung any more, so the")
    print("   +17.3 this is often quoted at is off the ladder now.")
    for lab in ("easy", "standard", "hard", "nobulous"):
        c, hp = LADDER[lab], LADDER_HEALTH[lab]

        def g(**kw):
            return sum(run(seed=sd, START_TIRED=c, HEALTH=hp, **kw)
                       for sd in seeds) / len(seeds)
        base = g()
        print("   %-10s %5.1f%%   pace %+5.1f   recover %+5.1f"
              "   commit %+5.1f\n              "
              "research %+5.1f   clauses %+5.1f   cards %+5.1f"
              % (lab.title(), base, base - g(pace="two"),
                 base - g(recov="best"), base - g(commit="all"),
                 base - g(res="small"), base - g(CLAUSES=False),
                 base - g(CARD_PICK="any")))
        sys.stdout.flush()
    print()
    print("   AND WHETHER COMMITTING IS STILL A DECISION. The pool lowers")
    print("   Targets, so it could have done what REC 5 does and made")
    print("   throwing every allowed die simply correct. It did the")
    print("   opposite - the gap is wider than it was on the old pool.")
    recgap = {}
    for rec in (2, 3, 4, 5):
        a = sum(run(seed=sd, REC_BASE=rec, commit="adaptive")
                for sd in seeds) / len(seeds)
        b = sum(run(seed=sd, REC_BASE=rec, commit="all")
                for sd in seeds) / len(seeds)
        recgap[rec] = a - b
        print("   REC %d  adaptive %5.1f%%  all %5.1f%%   gap %+5.1f%s"
              % (rec, a, b, a - b,
                 "   <- shipped" if rec == REC_BASE else ""))
        sys.stdout.flush()

    print()
    print("9. THE EIGHTEEN IMPOSTER CLAUSES - and whether they are a choice")
    print("   Implemented 2026-11-14. Each Tier III card prints a clause")
    print("   used only here; you get it as well as the -%d, from the moment"
          % CARD_VALUE)
    print("   you spend the card to the end of that session.")
    print("   The baseline is the model as it stood on 2026-11-13: a pool")
    print("   of flat -2s spent the session it is dealt. BOTH of the things")
    print("   that moved since are on this table, because the clauses and")
    print("   the timing are separate findings and the second is the bigger")
    print("   one.")
    base = sum(run(seed=sd, CLAUSES=False, res="small")
               for sd in seeds) / len(seeds)
    rows = [("the flat pool, spent at once", dict(CLAUSES=False,
                                                  res="small")),
            ("the flat pool, held", dict(CLAUSES=False)),
            ("clauses, spent at once", dict(res="small", CARD_PICK="any")),
            ("clauses, held, spend what came up", dict(CARD_PICK="any")),
            ("clauses, held, hand scored - SHIPS", {})]
    shipped = anyhand = 0.0
    for lab, over in rows:
        w = sum(run(seed=sd, **over) for sd in seeds) / len(seeds)
        print("   %-34s %6.1f%%%s  %+.1f" % (lab, w, band(w), w - base))
        if over == {}:
            shipped = w
        elif over == dict(CARD_PICK="any"):
            anyhand = w
        sys.stdout.flush()
    print()
    print("   WHICH SESSION TO DUMP ON. HOLD_LAST is the default policy's")
    print("   one free parameter and it is NOT a smooth preference: it")
    print("   names a session, and the wheel is five long with the red")
    print("   session - one die, the hard one - in the middle at 5. Two")
    print("   local maxima, at the last session and at the red one.")
    for last in (0, 1, 2, 3, 4, 5, 6):
        w = sum(run(seed=sd, HOLD_LAST=last) for sd in seeds) / len(seeds)
        print("   dump with %d session(s) left        %6.1f%%%s%s"
              % (last, w, band(w),
                 "   <- shipped" if last == HOLD_LAST else ""))
        sys.stdout.flush()
    print()
    print("   ONE CLAUSE AT A TIME, forced into the hand in place of one of")
    print("   its own game's picks, so the delta is a better card and not a")
    print("   bigger pool. Five seeds a cell; a delta under about 0.4 is")
    print("   inside the noise.")
    on = sum(run(seed=sd) for sd in seeds) / len(seeds)
    deltas = []
    for game in ("NAP", "BAT", "AoS"):
        for name in TIER3[game]:
            w = sum(run(seed=sd, FORCE_CLAUSE=name)
                    for sd in seeds) / len(seeds)
            deltas.append(w - on)
            print("   %-4s %-32s %6.1f%%  %+.2f" % (game, name, w, w - on))
            sys.stdout.flush()
    print()
    # COMPUTED, NOT TYPED. Both of these were literals in this print
    # until 2026-11-14 and the second one was already a tenth wrong: a
    # derived figure written into a print goes stale every time the model
    # moves, which it did twice on the day they were written.
    print("   WHICH CARD WAS NOT A DECISION THIS MODEL COULD FIND UNTIL")
    print("   2026-11-14, and it is the policy since 2026-11-16. Scoring")
    print("   the hand measured +0.4 against a Pool spent the session it")
    print("   was dealt and measures %+.1f against one held, and the spread"
          % (shipped - anyhand))
    print("   between the best and worst single clause went from 2.6")
    print("   points to %.1f. Choosing WHEN gave choosing WHICH something"
          % (max(deltas) - min(deltas)))
    print("   to decide, which is what the clauses were printed for.")
    print("   See THE EIGHTEEN CLAUSES in the header, and audit.py for how")
    print("   often each one actually goes off.")

    print()
    print("   AND HOW MUCH OF THAT IS THE SCORING TABLE BEING RIGHT. This")
    print("   is the test the default rests on, because CLAUSE_WORTH is a")
    print("   guess this file wrote rather than a rule printed on")
    print("   anything. It deals the SAME eighteen scoring functions to the")
    print("   WRONG cards - the same numbers, no information - and re-reads")
    print("   the rung. If a permuted table kept the gain, the gain would")
    print("   be the act of scoring and the guess would not matter.")
    perm = []
    for i in range(5):
        prng = random.Random(1000 + i)
        shuf = sorted(CLAUSE_WORTH)
        prng.shuffle(shuf)
        table = dict(zip(sorted(CLAUSE_WORTH),
                         [CLAUSE_WORTH[n] for n in shuf]))
        saved = CLAUSE_WORTH
        globals()["CLAUSE_WORTH"] = table
        try:
            w = sum(run(seed=sd) for sd in seeds) / len(seeds)
        finally:
            globals()["CLAUSE_WORTH"] = saved
        perm.append(w)
        print("   dealt to the wrong cards #%d        %6.1f%%%s  %+.1f"
              % (i + 1, w, band(w), w - anyhand))
        sys.stdout.flush()
    pm = sum(perm) / len(perm)
    print("   %-34s %6.1f%%%s  %+.1f" % ("   their mean", pm, band(pm),
                                         pm - anyhand))
    print("   AGAINST %+.1f FOR THE TRUE TABLE. A permuted one is worth"
          % (shipped - anyhand))
    print("   %+.1f, and %d of the 5 read WORSE than spending what came to"
          % (pm - anyhand, sum(1 for w in perm if w < anyhand)))
    print("   hand. So the gain is the table's CONTENT, all of it, and the")
    print("   four printed rungs are pegged to it being approximately")
    print("   right. Every term in it reads something FACE-UP, which is")
    print("   what makes that bearable rather than what makes it untrue.")

    print()
    # COMPUTED, NOT TYPED, for the same reason section 9's figures are:
    # every number in this block was a literal until 2026-11-16 and three
    # of the four had gone stale, one of them by naming the wrong REC.
    print("THE PROTOTYPE'S ERRATA - four finale10 claims that the real")
    print("components did not support:")
    print("  1 'the pace cannot be memorised'. The schedule rule IS the")
    print("    winning pace and it is one formula, so the depth is in")
    print("    execution. finale10 said as much in its honest-limit note;")
    print("    what is new is that its own throttled variant measures WORSE")
    print("    than the plain schedule here, %.1f%% against %.1f%%."
          % (paced["throttle"], paced["clock"]))
    print("  2 'a three-colour window'. At three colours the finale reads")
    print("    %.1f%% and this module's own recovery policy is no longer the"
          % dial["three-colour attention"])
    print("    best one, so the window has to be TWO for the dial's central")
    print("    decision to pay at all.")
    print("  3 its pacing figures. `clock` rounds the schedule and so falls")
    print("    quietly behind at a pressure just over 1 - see how_many().")
    print("  4 'commit only the dice you need', its LARGEST lever at +35.1.")
    print("    Worth %+.1f here - and it is the lever most sensitive to the"
          % gaps["commit"])
    print("    recovery economy. At REC 4 the gap is down to %+.1f, and by"
          % recgap[4])
    print("    REC 5 it INVERTS: throwing every allowed die wins by %.1f,"
          % -recgap[5])
    print("    which is why REC is 3 - the Rewards ARE the fourth point of")
    print("    recovery, and they have to be earned.")
