# Simulation

Balance models for all four Nobulous Set games, written 2026-09-20.

```
python table.py              # the full cross-tab, 20,000 games per cell, ~3min
python table.py 4000         # quicker pass
python run_all.py            # same thing; kept as the documented entry point
python bat.py                # one game on its own
```

`RESULTS.txt` holds the last full run.

Pure standard library. No dependencies.

## Why this exists

The win rates printed in `rules/bat.html` and quoted in `README.md` and
`HANDOFF.md` came from simulations run before this repo, and **that code was
never committed anywhere**. A search of every Claude Code transcript, the CLI
history, and a full claude.ai data export turned up nothing: the models lived
in a browser conversation and did not survive. `AGENTS.md` warns against
changing simulation-calibrated numbers, which is untenable when nothing can
re-derive them. These models replace that missing tooling.

They are **not** a reconstruction of the originals and do not reproduce their
figures. Read the fidelity notes before quoting anything here.

## Files

| file | what it models |
|---|---|
| `dice.py` | the shared 20 Strong dice; face distributions taken verbatim from the playtest engines |
| `cards.py` | hero rosters and the NRJ tier modules - the axes a balance table gets asked for |
| `bat.py` | Build-a-Tyrant: Splice Phase and Tyrant Battle |
| `nap.py` | Apprenticeship: the Assignment row, Demand penalties, the Final Exam |
| `aos.py` | Automaton of Shale: Element allocation, Programs, cycles, Advanced |
| `nrj.py` | Imposter Scenario: Council attempts, Suspicion, the Research Pool |
| `table.py` | the cross-tab: difficulty x NRJ tier x hero card |
| `run_all.py` | thin wrapper over `table.py` |
| `healthsweep.py` | tunes the Tyrant's Health against a target ladder |
| `aoseconomy.py` | whether AoS can be given a dice economy, and what it costs |
| `sweep.py` | every game, every difficulty, every hero, every NRJ tier |
| `dicetension.py` | whether running out of dice is actually the pressure, per game |
| `audit.py` | per card: how often it reaches the table, and whether its text does anything |
| `imposter.py` | the finale's dice economy: pool, Targets, the failure trade, the dials |
| `proto/fix.py` | candidate repairs for the finale, and which of them do nothing |
| `supply.py` | whether the campaign's 18 cards can actually be banked, and whether standalone matches |
| `protocols.py` | per-Protocol tuning sweep for BAT's NRJ Tier I |
| `proto/` | a proposed rewrite of the BAT battle, kept out of the shipping model - see `proto/README.md` |

Card data is transcribed from canonical sources, never retyped from memory:
Program targets and Element counts from `playtest/dist/app.js`; NAP Tasks,
Setbacks and Council Scenarios from `playtest/dist/suite.js`; Upgrade Values,
Rat statlines, Final Exams, Demand penalties and hero rosters from
`generator/build_*.py`; tier modules from `rules/nrj.html`.

## How the simulation works

Each model plays complete games, one at a time, and counts wins. No formulas
or closed-form odds - it deals the real decks, rolls the real dice and follows
each game's own round structure. 20,000 games a cell.

**The dice.** `dice.py` holds the five unit dice. Each is a d6 whose faces are
MISS (0), BASIC HIT (1 damage) or CRIT (2 damage), with one crit per color:

| | Yellow | Green | Blue | Purple | Red |
|---|---|---|---|---|---|
| quantity | 4 | 4 | 4 | 4 | 1 |
| hit sides | 2 | 3 | 4 | 5 | 6 |
| of which crits | 1 | 1 | 1 | 1 | 1 |
| miss sides | 4 | 3 | 2 | 1 | 0 |

That is the table on page 7 of `20-Strong_Rulebook.pdf`, and the five entries
in `FACES` match it exactly. 17 dice in total.

**The round**, from the core rulebook's Game Flow (pp. 10-16):

1. *Commit* dice from the pool into the active area.
2. *Roll* every unapplied die in the active area.
3. *Apply* hits to active cards.
4. Repeat 1-3 up to STR times, re-rolling everything still unapplied.
5. *Resolve*: suffer damage from undefeated cards, exhaust the dice, recover
   up to REC of them.

Each model implements this with its own game's overrides, because a deck's
rules take precedence over the general ones:

- **AoS** replaces blanket exhaustion with the printed exhaustion gradient -
  dice past Target + 1 exhaust, beating a Target by 2+ exhausts one, failing
  an element exhausts all of them, an extra STR roll exhausts that element's
  dice, and hitting a Target exactly recovers 2.
- **NAP** lets successes be *stored* on an unresolved Assignment, locking
  those dice to the card until it resolves, and adds Special Recovery, which
  returns every exhausted die of the queued color.
- **BAT** exhausts committed dice each Experiment and recovers REC; in the
  battle it recovers REC + 1 and the rest are gone for good.

**STR** is modeled as "apply every hit, re-roll the misses once", which is
optimal play of the repeat rule rather than a separate mechanic.

**The policies.** Every model plays one fixed greedy line - commit the
strongest dice, commit just enough to clear the Target, chase the nearest
objective. It does not play well, and it never plays the per-card text.

## Verification against the rulebooks

Checked 2026-09-20 against `20-Strong_Rulebook.pdf` and each game's own rules:

| check | result |
|---|---|
| die faces, all five colors | match p.7 exactly |
| 17 dice, 4 per color plus Red | match |
| crit = 2 damage but still one hit | match |
| Health below 1 loses; stats capped 1-6 | match |
| AoS exhaustion gradient | matches `rules/aos.html` |
| NAP stored progress, Special Recovery | matches `rules/nap.html` |
| NAP Demand penalties, per card | matches `build_nap.py` |
| BAT commit 6 / reroll misses / REC + 1 | matches `rules/bat.html` |
| BAT Red die ownership and hand-off | fixed this pass |
| BAT borrowing, banish risk by Upgrade count | added this pass |
| BAT Upgrade-deck reshuffle, Malfunction top-up | fixed this pass |

Six BAT rules were **found wrong and fixed** in this pass; all six had made the
game too easy. See the BAT section below.

## Calibration

The 20 Strong Community Game Stats sheet records the published titles at
**47-57%, and 53% across 955 games** (Solar Sentinels 49%, Too Many Bones 55%,
Hoplomachus 53%, Tanglewoods Red/White/Gold 47/53/57%). A finished game in this
system sits near 50%, and that is the yardstick for everything below. The BAT
ladder published in `rules/bat.html` (~70/63/56/49/42) straddles that band.

Against that band the three games now read Easy 62.7 / 56.8 / 79.6% and
Standard 53.2 / 49.8 / 71.2% (BAT / NAP / AoS) on the no-NRJ axis, with the
finale at 61.5%. BAT and NAP are in the band at Standard. AoS is in it at
Standard on the campaign axis (54.2% at Tier III) but still reads high played
on its own.

Two changes on 2026-10-28 moved NAP and AoS there, and neither was a
difficulty dial. **NAP had every printed Target raised by 1** - the 26 Task
Requests, the 6 Opportunities and the 12 Final Exam bases, with the Task
Demands deliberately left alone - which took Standard from 76.0% to 49.8%.
**AoS gained a rule**: on a Catastrophic Failure you may exhaust 2 misses on
failed Elements to negate the Health loss, which took Standard at Tier III
from 27.9% to 54.2%. The calibration block `table.py` prints carries the
reasoning for both, including why NAP's Demands did not move.

**The retune is the headline and it inverts the old conclusion.** These
models played one fixed policy, and in three of the four games it was 6 to
34 points below the best setting of its own dials - NAP most of all, because
it threw one expected success PAST each requirement when a short roll banks
its progress for free. So "the set reads low" was mostly a statement about
the player. AoS is the control: its policy was already optimal, Target + 1
being a rules cap, and it did not move. Every difficulty dial in the set was
calibrated against the old play and none has been re-pitched; see the CAVEATS
block in `RESULTS.txt`. The rulebooks no longer print win rates at all, so
that file is the only place they live.

## Results

Full run in `RESULTS.txt`. 20,000 games per cell. Tier columns are cumulative,
and are *not* difficulty levels - Tier II is the documented pressure peak and
Tier III hands tools back.

Three tables below still carry a **Brutal** row and a `published` column. Both
are historical: each of those runs was made to diagnose a specific modelling
bug against the ladder published at the time, before BAT was re-tuned onto
5/6/7/8 Specimens against 3/4/7/11 Buff HP and before Brutal was dropped so
all four games share Easy / Standard / Hard / Nobulous. The rows are left as
measured - they are the evidence for the fixes described with them, not the
current ladder. For that, see `table.py`.

### NAP - FINF dial x NRJ tier

| FINF | no NRJ | Tier I | Tier II | Tier III |
|---|---|---|---|---|
| +3 | 41.6% | 37.8% | 25.6% | 30.5% |
| +2 | 42.7% | 40.5% | 26.6% | 32.1% |
| +1 | 43.9% | 41.3% | 27.2% | 33.5% |
| **−1** *(Standard)* | **48.0%** | **44.3%** | **31.8%** | **39.8%** |
| −2 | 50.4% | 46.5% | 32.8% | 41.7% |
| −3 | 51.8% | 48.0% | 35.5% | 44.7% |

Measured 2026-10-27, 7,200 games a cell, BEFORE the policy retune later the
same day - so these cells are about 30 points low and are kept only for the
shape of the dial, which is what the section is about. The retuned Credit
goal curve, at 4 Setbacks, runs 76.3% at 6 Credits, 65.8% at 8, 55.6% at 10,
then 52.4 / 50.1 / 48.0% at 12 / 14 / 16: raising the goal looks like the
obvious lever for re-pitching NAP, and on its own it bottoms out near 48%.

It is not the lever that was used. The Credit goal could not put both axes in
band at any value, because the no-NRJ game leans on the Final Exam Targets
and the goal does not touch them. Raising every printed Target by 1 did, and
unlike the goal it also narrowed the per-Apprentice spread. See the
calibration block in `table.py`.

Every cell here used to read 15-19%, from before the Primary-choice policy
was corrected - it took the cheaper of the two revealed Assignments and
ignored what the card paid. The dial spans 10 points end to end and Standard
sits in the middle of it.

Tier I is close to a wash - the Following Setbacks it swaps in are harsher
per card but displace base Setbacks of similar weight. Tier II is the trough,
as designed: 4 Impostor Tasks that are Mandatory and grant no Credits remove
four Credit chances and force four clears. Tier III recovers 6-9 points, more
than the other two games get back.

These cells run above the cross-tab's NAP row (Standard 42.1%) because this
table holds the Credit goal at 6 and moves only the FINF dial, while the
cross-tab moves the goal and the Setback count together.

### BAT - difficulty x NRJ tier

Difficulty is **Specimens added to the Upgrade deck / the Tyrant's Health**.
The track is the five Splices in random order, then the Health dial; damage
runs left to right. The current numbers are in `RESULTS.txt`.

| difficulty | Specimens | Health | no NRJ |
|---|---|---|---|
| Easy | 5 | 9 | 62.7% |
| Standard | 6 | 10 | 53.2% |
| Hard | 7 | 12 | 40.1% |
| Nobulous | 8 | 14 | 28.1% |

#### The battle was rewritten

The Tyrant battle this model describes is not the one in the older sections
below. Jon played the original and found it tedious, and the model agreed:
the correct play was to commit only what recovery returned, so the dice pool
was a per-round income rather than a budget. The battle ran 9.1 rounds and
ended with **7.1 of about 10 dice unspent**; its trough equalled its mean,
meaning the pool did not move at all. Committing freely was 14.5 points
WORSE than hoarding.

Five changes, measured in `proto/` and now the rules:

1. **A Splice must be met in one attack or the blow bounces.** The rule a
   Rat's Upgrades already used, applied to the Tyrant. Overflow from a broken
   Splice carries on and may break the next; nothing is ever part-damaged.
2. **A breaking Splice banishes a die of its own color** (`BREAK_BANISH`).
   Its printed effect is never used - see below for why the old aura went.
3. **A Rat's Upgrade is spent whenever it blocks**, whatever the blow.
4. **The Tyrant breaks containment after 8 rounds** (`ROUND_LIMIT`).
5. **Buff HP folded into Health**, so difficulty is one number again, and
   the 6-dice commit cap was removed after measuring that an uncapped pool
   opens nothing.

Spending now beats hoarding by **+7.2**, the fight is 7.2 rounds, and the
pool troughs at 3.0 with 36% of games dropping to two dice or fewer - ahead
of NAP's 20% on `dicetension.py`'s measure.

**The campaign rule had to move with it.** Because an Upgrade is spent to
block, a winning party ends holding a median of ZERO; only 2% of wins left
the 3 the old carry-forward rule asked for. BAT now retains from the
Upgrades held when the battle BEGAN, which 86% of wins have 3 or more of.

#### HISTORY: the leftmost-Splice aura, and why it was cut

*This section describes the battle as it was BEFORE the rewrite above. It is
kept because it is the measurement that motivated the change.*

The old track was **Buff HP, then the five Splices in random order, then the
Health dial**, and the leftmost surviving Splice supplied its printed effect
free on every Tyrant attack. Firing every round compounded: with the effects
on the win rate collapsed from 62% to 16%, with nothing usable in between.
Inert or lethal. A Splice now does nothing while it stands and banishes one
die when it breaks, which is a cost you can feel without a compounding one.

All 30 cards are encoded individually from their printed text - 16 Upgrades,
8 Specimens, 6 Modifications - as a 4-tuple of (damage added to the Tyrant's
attack, damage blocked off the Rats' attack, successes removed, Rat dice
exhausted). Of the Splices that actually reach the Tyrant in play, **51% add
damage, 38% block, and 12% are inert** (pure dice-recovery cards, which do
nothing for a Tyrant whose six dice never exhaust).

It is **off by default**. The table below is historical - it has a Brutal
row and a `published` column - and the collapse it shows was an artifact of
two model faults since fixed: the adopted +1 on Experiment Targets charged
twice, and Upgrade cards leaking out of a deck the rules make inexhaustible.
Measured now at Standard with no tier module, the effects are worth **+3.7**
(42.8% off, 46.5% on), not -52. The historical figures:

| difficulty | effects on | effects off | published |
|---|---|---|---|
| Easy | 16.1% | 68.3% | ~70% |
| Standard | 10.2% | 62.4% | ~63% |
| Hard | 7.2% | 58.9% | ~56% |
| Brutal | 6.2% | 54.5% | ~49% |
| Nobulous | 6.4% | 50.8% | ~42% |

**Both kinds of effect hurt the Rats, which is the core problem.** Attack
effects kill Rats faster; blocking effects stretch the fight out, so the
Tyrant simply gets more attacks. There is no leftmost Splice that is good news
for the player. Rats knocked out per game goes from 2.47 of 4 to 3.80 of 4.

A sensitivity probe - overriding every card with a flat bonus - shows how
narrow the margin is: +0 gives 62.2% at Standard, +1 gives 43.5%, +2 gives
5.5%. **One point of extra Tyrant damage per attack costs roughly 19 points of
win rate.** That is worth keeping regardless of whose numbers are right: BAT
sits on a knife edge about one damage point wide.

So either the printed effects are worth far less in play than their text
reads, or they are not meant to fire on every attack, or the published ladder
predates the rule. This model cannot tell which, so it reports the
effects-off column and says so rather than picking the flattering number.

**The tier row still runs the wrong way - do not use it.** See the caveat
below.

#### Rules this pass found wrong

A second read of `rules/bat.html`, after the first round of fixes below, found
three more - and these were the ones that mattered:

4. **The Red die was available every turn.** Red belongs to one Rat at a time.
   Only the active Rat may commit it, and only if it is the Rat holding it;
   after use it is set aside and placed on a **non-active** Rat at the start of
   the next turn. So it is available every *other* turn at best. The model gave
   the active Rat a free Red - the strongest die in the game, with no miss face
   - on every single Experiment.
5. **Borrowing and banishing were not modeled at all.** A Rat may borrow one
   non-Red die from another, with the allowed colors narrowing as its Upgrade
   count rises (0 Upgrades: any color, 17% banish risk; 3 Upgrades: Yellow
   only, 67%). The die is rolled by itself afterwards and a miss **banishes it
   from the game permanently**, which shrinks the shared battle pool for the
   rest of the game. Games now banish 1.4 dice on average.
6. **Deck exhaustion was wrong both ways.** Running out of Upgrades is "not a
   malfunction - reshuffle the Upgrade discard instead", but the model ended
   the Splice Phase early. And the Splicing Machine Malfunction tops the Tyrant
   up from *unused Upgrade cards*, where the model was using Specimens.

#### The first three

All three had made BAT too easy. Reading `20-Strong_Rulebook.pdf` and the
battle section of `rules/bat.html` against the code turned them up:

1. **A Rat's Upgrades had no carryover.** The rules say damage that meets an
   Upgrade's Value destroys it "and the rest carries on to the next Upgrade
   under the same test, then to Health"; only damage that can meet *no*
   remaining Upgrade stops dead. The model destroyed one Upgrade and stopped,
   so a big hit could never wipe two Upgrades or reach Health.
2. **The Tyrant drew its dice off damaged Values.** It draws dice equal to the
   highest Value among the Splices it still holds, and Value is printed -
   "damage already marked on that card does not weaken it". The model used the
   damaged remainder, so a wounded Tyrant rolled fewer dice than it should.
3. **Damage ignored the Defense-first order.** The track then ran Buff HP,
   Defense Splices, the rest, then Health. (Buff HP has since been folded
   into Health and the order is now simply the five Splices, then Health.)

All six fixes together moved Standard from 85.3% to 62.9% - onto the
published ~63%.

### HISTORY: BAT - the Tyrant dice rule

*Measured before the battle was rewritten, against the ladder published at
the time. The arrangement it settled - the Tyrant's six dice coming out of
the Rats' own supply - is still what `rules/bat.html` and the model use, so
the conclusion stands even though every number here is superseded.*

| difficulty | playtest UI | rulebook | published ladder | error |
|---|---|---|---|---|
| Easy | 66.2% | 84.3% | ~70% | −3.8 |
| Standard | 62.9% | 81.9% | ~63% | **−0.1** |
| Hard | 58.8% | 78.5% | ~56% | +2.8 |
| Brutal | 55.0% | 75.1% | ~49% | +6.0 |
| Nobulous | 50.8% | 72.6% | ~42% | +8.8 |

*playtest UI* = the Tyrant's six dice are carved out of the Rats' pool.
*rulebook* = the Tyrant keeps its own 2 Purple / 2 Blue / 1 Green / 1 Yellow
that "never exhaust", separate from the shared battle pool swept up from the
Rats - which is what `rules/bat.html` describes.

Two things follow. The gap between the arrangements is **18-22 points**, far
larger than the 6-11 first measured. And the playtest UI column now tracks the
published ladder closely at the easy end - Standard lands on it - while the
rulebook column sits 14-31 points above it everywhere. Whatever produced the
published ladder behaves like the playtest rule, not the printed one.

The residual error is all **slope**: the published ladder spans 28 points from
Easy to Nobulous and this model spans 15. Difficulty is Specimen count, so the
missing steepness is very likely the 8 Specimen abilities, plus the
frontmost-Splice effect, which grows stronger exactly as Specimens accumulate
(it fires free on every Tyrant attack and uses the card's printed Value, and
Specimens are the Value-5 cards).

### AoS - Program deck x NRJ tier

| difficulty | no NRJ | Tier I | Tier II | Tier III |
|---|---|---|---|---|
| Easy 5/3/0 | 79.6% | 68.4% | 61.1% | 65.0% |
| Standard 4/3/1 | 71.2% | 59.1% | 50.7% | 54.2% |
| Hard 3/3/2 | 62.8% | 49.3% | 40.8% | 44.9% |
| Nobulous 2/3/3 | 52.6% | 40.2% | 32.0% | 35.2% |

Measured after the misses-negate rule of 2026-10-28. Before it the same cells
read 47.0 / 35.2 / 24.9 / 38.7% at Easy and 35.0 / 25.3 / 16.9 / 27.9% at
Standard, which is where every earlier copy of this table sits.

The axis changed. This table used to be indexed by whole Program decks
(Routine 43.3%, Specialized 9.3%, Unstable 2.2%); difficulty is now the MIX
of Routine / Specialized / Unstable in the deck, which is why these rows do
not line up with any earlier copy of this table.

It is still the cleanest tier response of the three and matches the design
intent exactly: Tier II is the trough (Easy 79.6% -> 61.1%) and Tier III claws
most of it back (65.0%). What the negate rule did NOT fix is the gap between
the two axes: AoS now lands in band at Standard on the campaign axis (54.2%)
while reading 71.2% played on its own, so the solo game is the loose end.
NAP's +1 pass closed its own version of that gap - 49.8% against 51.4% - by
raising the Final Exam Targets, and AoS has no equivalent card to lean on.

### NRJ - the finale

61.6% in the cross-tab and 61.7% in imposter.py's own 4,000-game pass, up
from 32.4%, after one line was added to the Imposter card: **"your REC is 3
minus the number of cards in the Suspicion row"**, with 5 starting Health
rather than 4. About 11 of those points are the 2026-10-27 policy retune
rather than the card: the finale rewards committing two expected successes
past the Target, because a failed attempt is gone for good and leaves the
Suspicion row one card taller. The tiers apply to the three games above, not to the
finale.

That was a repair, not a re-tune. `imposter.py` measured the finale on
`dicetension.py`'s scale and found no dice pressure at all - 0% of commit
decisions at two dice or fewer, 0.0% empty - because the pool collapsed to
exactly REC by the fourth attempt and sat on that floor for the remaining
five. It could not run out, so running out was never a worry. With the floor
coupled to the Suspicion row it declines 17.0 -> 3.5 -> 0.4 across the nine
attempts, and the finale leads the set on all six tension columns - 5.0 mean
against NAP's 10.9 and AoS's 13.7, and it is the only game in the set where
the pool runs out at all. An earlier pass here said five of six, reasoning
from figures that had been copied out of dicetension.py and left to go
stale; imposter.py now calls that tool instead of holding a copy.

`proto/fix.py` has the twenty-one candidates and combinations that were
measured and rejected, and the negative
result is the useful part: **nothing that leaves the recovery floor fixed can
create dice tension**, however far it moves the win rate. One candidate
banishes eight of the seventeen dice every game and reads 0% and 0.0%.

Two earlier NRJ figures were artifacts and are gone. **100%** came from
treating all 18 Research Pool cards as spendable at a flat -3, when only 9 of
the 18 reduce anything - "Candidate or damaged card" is worth 0 - and retained
values are -2 to -5 on a category match, -2 off it. **9.3%** came from REC
handing back the *weakest* exhausted dice: `commit()` filled the pile
strongest-first and recovery popped the end of it, an accident of list order
worth 21 points.

The campaign hand-off was audited separately, by running the three games
and reading what each banks: `supply.py`. Supply is sufficient everywhere,
and **standalone is a fair stand-in for a real campaign** - 61.8% against
58.7% to 61.4% across the four difficulties. Two assumptions in `build_pool`
were wrong and are fixed: a retained BAT Specimen is available on 86-96% of
wins rather than the 50% assumed, and the first AoS Advanced Program is
Stable by rule so the flat 50/50 Stable/Overheated was never reachable
(34-38% Overheated in practice).

What is still wrong is the slope. One point of starting Health is worth 19 to
41 points of win rate and one point on all 24 Targets about 32, because nine
pass/fail attempts against a small failure budget amplify any dial about
ninefold. Flattening that means grading each attempt rather than passing or
failing it. The consolation is that one number now serves as the difficulty
ladder the finale has never had: 3/4/5/6 starting Health gives 2.0%, 20.5%,
61.6%, 80.4%, with dice pressure rising along it. The retune made those
rungs WIDER, not narrower - the 4-to-5 step alone is 41 points - so they are
not shippable as a ladder without re-pitching.

## The hero axis

Every game's heroes share one statline and differ only in ability text,
which the rulebooks state outright:

- AoS - "All six begin at 2 HP / 2 STR / 3 REC and differ only in ability."
- NAP - "All six begin at 2 HP / 2 STR / 2 REC; they differ only in abilities."
- BAT - both sides of each Lab Rat print the same HP/STR/REC.

This section used to say ability text was exactly what these models omit, so
the heroes came out identical here. They are modelled now, and because the
statlines really are identical the whole spread is ability text:

| game | best | worst | spread |
|---|---|---|---|
| AoS Technicians | optimizer 43.4% | engineer 26.0% | 17.4 |
| NAP Apprentices | Technician 80.8% | Prodigy 73.5% | 7.3 |
| BAT Lab Rat sides | tool_keeper 53.2% | adaptation 49.6% | 3.6 |

At Standard with no tier module; the full tables are in `RESULTS.txt`, and all
twenty cards are listed in `cards.py`. AoS's 17 points is a lot to rest on one
card choice and is worth a look. BAT's axis is not a pick of one card: all four
Rats always play, so it is 16 side-combinations, and Rat abilities do not apply
in the Tyrant Battle at all - which is why its spread is the narrowest.

## Fidelity

What every model implements: exact die faces, printed Targets, the dice economy
(commit, exhaust, recover), STR rerolls, HP and failure tracking, and each
game's win condition.

**The BAT tier row reads correctly now.** It used to run backwards: the tier
modules made BAT *easier*, contradicting the intent that Tier II is the
pressure peak. That was a model fault, not a design one, and it took three
fixes - the Tyrant Attack deck, the Protocol die-borrowing clauses, and
tier effects that REPLACE base cards instead of adding to them. Tier II is
now the trough in every BAT column, matching AoS and NAP.

What remains unmodelled is **per-card text**, and the list is much shorter
than it was. Verify it against `audit.py` rather than trusting this block;
several claims here have been wrong, including a run of five that all said
BAT content was omitted after it had been implemented.

- **BAT** - 19 of the 20 Experiment effects are implemented. The exception
  is Diagnostic Trial, which buys a look at the next Experiment; the policy
  has no lookahead to spend it on. The 16 Upgrade abilities, all 7 Tyrant
  Attacks, both Modification sides and the Protocol borrowing clauses are
  modelled. The frontmost Splice has no effect *by rule* - on the Tyrant a
  Splice is only its Value - so that is a design decision, not a gap.
- **BAT Research Notes** - the claim conditions are all modelled, but a
  claim goes into one pooled counter that is spent on two of the six printed
  rewards. Four printed rewards do nothing. This is the live limit on BAT's
  Tier III column: Notes are claimed 4.3 times a game and buy very little.
- **NAP** - Apprentice abilities, the 26 Request effects, Opportunity effects
  and subject-icon wilds. Player-favorable on net, so NAP reads low. The
  printed Demand penalties, Setback blocking and the Final Exam *are*
  implemented.
- **AoS** - Technician abilities and the 6 Limitations.
- **NRJ** - 1 of the 24 Scenario effects, down from 18. Across the Chamber
  buys a look at the next Scenario and the policy has no lookahead to spend
  it on. The six clauses that restrict WHICH dice may contribute were the
  last block added. `imposter.py` measures what they do: three of them block
  the majority of the attempts they appear in and the set is worth -1.9
  points, because a blocked attempt was already lost and being blocked saves
  the dice it would have wasted. One of the six - the Yellow ban - blocks
  0%, because a pool recovered strongest-first holds no Yellow to bar.

**Policy sensitivity is large.** Each model plays one fixed greedy policy. NRJ
measured the size of this: rationing the Research Pool evenly across the nine
attempts scored 3.4%, and spending it to close whichever Targets it could reach
scored 9.2% - with no change to the rules being modeled. Single figures here
are policy-dependent, so prefer the *shape* of a column to its level.

## If you find the original simulations

They would be worth keeping beside these. Two questions they could settle:
whether the published ~63% Standard reflects card effects this model omits,
and whether the current BAT dice rule was ever simulated at all.
