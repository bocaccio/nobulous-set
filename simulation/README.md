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
| `buffsweep.py` | sweeps BAT's Buff HP against the published ladder |
| `sweep.py` | every game, every difficulty, every hero, every NRJ tier |
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

After this pass's BAT fixes, BAT reproduces the easy end of its published
ladder closely - Standard 62.9% against ~63% - and drifts high at the hard end.
AoS and NAP still sit well below the band.

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
| +3 | 15.7% | 16.1% | 10.8% | 10.7% |
| +2 | 15.9% | 15.9% | 11.0% | 11.2% |
| +1 | 16.9% | 16.3% | 11.3% | 11.3% |
| **−1** *(Standard)* | **18.2%** | 17.9% | 11.9% | 13.3% |
| −2 | 19.0% | 18.3% | 12.6% | 13.6% |
| −3 | 19.3% | 18.3% | 12.4% | 13.4% |

Tier I is close to a wash - the Following Setbacks it swaps in are harsher
per card but displace base Setbacks of similar weight. Tier II is the trough,
as designed: 4 Impostor Tasks that are Mandatory and grant no Credits remove
four Credit chances and force four clears. Tier III recovers 1-2 points.

### BAT - difficulty x NRJ tier

| difficulty | no NRJ | Tier I | Tier II | Tier III | published |
|---|---|---|---|---|---|
| Easy | 68.3% | 71.3% | 75.1% | 77.0% | ~70% |
| Standard | 62.4% | 67.1% | 70.6% | 73.6% | ~63% |
| Hard | 58.9% | 62.6% | 66.0% | 69.7% | ~56% |
| Brutal | 54.5% | 58.7% | 62.1% | 65.9% | ~49% |
| Nobulous | 50.8% | 55.2% | 58.0% | 62.3% | ~42% |

Track order is Buff HP, the five Splices in random order, then the Health
dial; damage runs left to right.

#### The leftmost-Splice effect, and why it is switched off

The Tyrant track is **Buff HP, then the five Splices in random order, then the
Health dial**. Damage chews left to right, and the leftmost surviving Splice
supplies its printed effect free on every Tyrant attack; when it is destroyed
the next one takes over. That is implemented, behind `card_effects=True`.

All 30 cards are encoded individually from their printed text - 16 Upgrades,
8 Specimens, 6 Modifications - as a 4-tuple of (damage added to the Tyrant's
attack, damage blocked off the Rats' attack, successes removed, Rat dice
exhausted). Of the Splices that actually reach the Tyrant in play, **51% add
damage, 38% block, and 12% are inert** (pure dice-recovery cards, which do
nothing for a Tyrant whose six dice never exhaust).

It is **off by default**, because switching it on gives:

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
3. **Damage ignored the Defense-first order.** The track runs Buff HP, then
   Defense Splices, then the rest, then Health.

All six fixes together moved Standard from 85.3% to 62.9% - onto the
published ~63%.

### BAT - the Tyrant dice rule

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

| deck | no NRJ | Tier I | Tier II | Tier III |
|---|---|---|---|---|
| Routine | 43.3% | 32.5% | 21.0% | 39.7% |
| Specialized | 9.3% | 6.6% | 3.2% | 6.7% |
| Unstable | 2.2% | 2.0% | 0.8% | 1.9% |

This is the cleanest tier response of the three and matches the design intent
exactly: Tier II is the trough (Routine 43.3% -> 21.0%) and Tier III claws most
of it back (39.7%). Routine is the only cell in the community band; Specialized
and Unstable sit far below it.

### NRJ - the finale

9.3%. The tiers apply to the three games above, not to the finale, and the
finale has no difficulty dial. **The earlier 100% figure was an artifact and is
gone**: that model treated all 18 Research Pool cards as spendable at a flat
-3, when only 9 of the 18 reduce anything - "Candidate or damaged card" is
worth 0 - and retained values are -2 to -5 on a category match, -2 off it.

## The hero axis

It is not in the tables because it cannot move a number here. Every game's
heroes share one statline and differ only in ability text, which the rulebooks
state outright:

- AoS - "All six begin at 2 HP / 2 STR / 3 REC and differ only in ability."
- NAP - "All six begin at 2 HP / 2 STR / 2 REC; they differ only in abilities."
- BAT - both sides of each Lab Rat print the same HP/STR/REC.

Ability text is exactly what these models omit, so the heroes come out
identical *in the model* and certainly are not identical *in play*. All twenty
are listed in `cards.py`. BAT's is not even a pick of one card: all four Rats
always play, so it is 16 side-combinations, and Rat abilities do not apply in
the Tyrant Battle at all.

## Fidelity

What every model implements: exact die faces, printed Targets, the dice economy
(commit, exhaust, recover), STR rerolls, HP and failure tracking, and each
game's win condition.

**The BAT tier row is not usable.** In this model the tier modules make BAT
easier, contradicting the intent that Tier II is the pressure peak. AoS and NAP
both reproduce that intent, so the fault is specific to the BAT model, and it is
structural: BAT's only real loss channel is Rats being knocked out, and Upgrades
are armor that stops damage outright, so adding six Upgrade-class cards to the
deck raises the armor supply. The modules' hostile clauses live in content the
model omits - the Tyrant Attack deck, the frontmost-Splice effect, and the
Protocol clauses that turn on die-borrowing between Rats. Both Modification
sides *are* modeled (the Tyrant may tap one for +2 damage, and all six printed
"while held" drawbacks apply to a Rat holder); it is not enough to flip the
sign.

What none implements is the bulk of **per-card text**, which is the largest
source of divergence from the published figures:

- **BAT** - the 20 Experiment effects, 16 Upgrade abilities, 7 Tyrant Attack
  cards, and the frontmost-Splice effect. Hostile on net, so BAT reads high.
- **NAP** - Apprentice abilities, the 26 Request effects, Opportunity effects
  and subject-icon wilds. Player-favorable on net, so NAP reads low. The
  printed Demand penalties, Setback blocking and the Final Exam *are*
  implemented.
- **AoS** - Technician abilities and the 6 Limitations.
- **NRJ** - 18 of the 24 Scenario effects. The 6 that drive the dice economy or
  Suspicion are implemented.

**Policy sensitivity is large.** Each model plays one fixed greedy policy. NRJ
measured the size of this: rationing the Research Pool evenly across the nine
attempts scored 3.4%, and spending it to close whichever Targets it could reach
scored 9.2% - with no change to the rules being modeled. Single figures here
are policy-dependent, so prefer the *shape* of a column to its level.

## If you find the original simulations

They would be worth keeping beside these. Two questions they could settle:
whether the published ~63% Standard reflects card effects this model omits,
and whether the current BAT dice rule was ever simulated at all.
