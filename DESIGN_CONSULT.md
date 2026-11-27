# The Nobulous Set — experience design brief

A self-contained brief for an outside reader. No repo access needed.

## What this is

*The Nobulous Set* is a fan expansion for **20 Strong**, a solo/co-op dice
game. The core loop across the whole system: you own a small pool of coloured
dice, you **allocate dice to tasks before rolling them**, you roll, and you
either meet a printed Target or you don't. Resources are dice, Health (HP),
and a per-turn recovery allowance. 20 Strong scenarios are meant to be
**puzzles with semi-mitigated luck** — not optimisation problems. The
intended feeling is *figuring out how to survive under diminishing
resources*, while being fun.

The expansion has four scenario families. Three are discussed here.

| | theme | core verb |
|---|---|---|
| **BAT** — Build-a-Tyrant | you build the boss that then fights you | Experiments, then one big battle |
| **NAP** — Nobulous Apprenticeship Program | a year of a brutal graduate program | work an Assignment row, then sit Final Exams |
| **AoS** — Automaton of Shale | program a machine | allocate dice across a Program's Elements |

All numbers below come from a Python simulation of the printed rules
(20,000-game runs unless stated; a competent-play policy, not optimal).
The win rates are calibrated and **not** the subject of this brief — the
designer's concern is *engagement*, not the difficulty ladder.

---

## 1. BAT — Build-a-Tyrant

### Mechanics

Two phases. In the **Splice Phase** you repeatedly attempt *Experiments*:
commit dice, hit a Target, and on success take one of two revealed Upgrade
cards. On **failure the Tyrant eats the stronger revealed card** as a
"Splice". **Five Splices and the Tyrant wakes up**, which ends the phase and
begins the battle. If the Experiment deck runs out first, the track is topped
up to exactly five from unused Upgrades. Then you fight the thing you built.

A Splice's Value (2–5) is a **threshold a single blow must meet or exceed** —
a blow that falls short is wasted entirely. A Rat's Upgrade, by contrast,
"blocks one attack and is spent" regardless of its Value.

### Designer's target

> "The splice phase doesn't provide much of a puzzle, particularly if you know
> you will get your dice back before the tyrant battle. It should almost be a
> forgone conclusion that EVERY upgrade will get spliced onto the tyrant. The
> challenge then, for the rats, is figuring out how to get some of these
> upgrades for themselves. Then, when the tyrant awakens, they say 'oh shit.
> Do we have enough capability to defeat it?'"

### Measured (Standard, 4,000 games)

- **The phase costs nothing permanent in 60% of games.** Rat HP when the
  Tyrant wakes: **6.00 of 6, sd 0.000** — nothing in the phase can touch
  Health in any game. Dice banished (the only lasting loss): mean 0.49, and
  **zero in 60% of games**. Every exhausted die is returned at battle start.
- **47% of the cards shown go in the bin.** 16.4 Upgrades are revealed per
  game. The Tyrant gets 5 — **always exactly 5, sd 0.00**. The players keep
  3.6. **7.8 reach neither side.**
- **It is the same boss every game.** Wall total 20.86, sd 1.88 (p10–p90 =
  18–23). The number that actually gates the battle — its **biggest single
  Splice** — is **5 in 99.9% of games** (sd 0.06).
- Why that last number won't move: 2.75 of the 5 Splices are value-5 cards,
  92.7% of games hold two or more, and every 5 is a *Specimen* (Specimens are
  all value 5; ordinary Upgrades run 2–4). A random five of the 24 cards would
  hold 1.67 — the excess arrives **by selection**, because the failure rule
  hands the Tyrant the *strongest* revealed card and a Specimen is always
  strongest.

### Diagnosis

Three structural causes, in order of importance:

1. **Nothing is spent.** Dice return, HP is untouchable. There is no
   diminishing-resource arc, so the luck is not semi-mitigated — it is
   fully refunded. A failed Experiment costs nothing you keep.
2. **The number 5 does two jobs** — the Tyrant's size *and* the phase clock.
   This is why "every Upgrade gets spliced" cannot be bolted on: splice every
   revealed card and the phase ends in three Experiments.
3. **Taking and splicing are separate streams.** The card you *don't* take is
   discarded, not spliced. So keeping an Upgrade costs the Tyrant nothing, and
   a well-played phase never shows up in the wall.

### Candidate direction (untested)

*Make the wall the residue.* Every revealed Upgrade joins a pool bound for the
Tyrant; the players' job is to claw cards **out** of it; the Tyrant is built
from the best five that are left. The clock becomes the Experiment deck
(already the rules' backup end condition). Then every claw directly lowers the
boss, clawing a Specimen lowers the *gating* number, the wall becomes variable
and legible, and the five slots and battle maths survive. Costs: you lose the
visible clock ticking up during the phase, and it does nothing about (1).

---

## 2. NAP — Nobulous Apprenticeship Program

### Mechanics

You work a row of **Assignment** cards across Time Slots (Morning /
Afternoon / Evening) and Days, committing dice to meet Targets and earning
**Credits** by subject. **Setbacks** lock the row until resolved;
**Opportunities** give relief. Reaching your **Credit goal** does **not**
win — it ends the apprenticeship. You then sit **three mandatory Final
Exams** and must finish all three with at least 1 HP. Arriving short of the
goal doesn't lose either: it costs dice and leaves the exam Targets
unreduced. You start with
**HP 2**.

### Designer's target

> "I want NAP to feel a bit like a crash course in getting through a year of a
> very challenging graduate program. You should feel considerable stress with
> setbacks adding more and opportunities providing some relief. You get to the
> final exams and you have some feeling of preparedness, but still a lot of
> anxiety at the possibility of failing."

### Measured (Standard, 8,000 games)

Overall win **49.0%**. **82.4%** reach the exams; **17.6%** wash out during
the year.

**P(pass the exams | you got there) = 59.5%** — and preparedness is strongly
legible:

| HP at the gate | n | pass |
|---|---|---|
| 1 | 1,417 | 32.7% |
| 2 | 3,369 | 60.2% |
| 3 | 1,803 | 79.3% |

| Credits at the gate | n | pass |
|---|---|---|
| 4 | 386 | 29.0% |
| 5 | 3,938 | 57.7% |
| 6 | 1,688 | 71.3% |
| 7 | 373 | 78.3% |

State at the gate: HP mean 2.06 (sd 0.70, range 1–3); Credits mean **5.26**
(p10 5, p90 6); dice available mean 2.13; Day reached mean 4.16.

**The stress arc, mean HP after each Time Slot** (over games still alive):

```
slot:      1     2     3     4     5     6     7     8     9    10    11    12    13
HP:     2.05  2.10  2.15  2.18  2.17  2.12  2.05  1.98  1.89  1.77  1.68  1.66  1.57
dice:   7.74  3.92  3.92  1.52  0.66  2.40  0.52  0.32  2.28  0.39  0.25  2.27  0.38
```

### Diagnosis

**The exam half already works.** 59.5% is genuinely in doubt, and the
preparedness gradient (32.7% → 79.3% across HP; 29% → 78% across Credits) is
exactly "you can feel how ready you are and you're still scared." Of the three
families this is the closest to its stated target.

**The stress arc does not accumulate.** Mean HP *rises* for the first four
Time Slots (2.05 → 2.18) and only decays in the back half. The first third of
the "brutal year" is the easiest part of it. Dice show a hard sawtooth
(7.74 → 0.66 → 2.40 → 0.52 → 2.28) — that is the per-Day recovery resetting
the pool, so dice pressure is cyclical rather than cumulative.

**Most players don't finish the degree — they run out of year.** Mean Credits
at the gate is **5.26** against a goal of 6, and 5 is the single commonest
value. The year typically ends on deck exhaustion, not achievement. That is
arguably *very* thematic, but it means the 6-Credit goal is aspirational
rather than the thing that paces the scenario, and the moment of leaving is
"time expired" rather than "I made it."

### Open question

The target says "setbacks adding more [stress]". Is a flat-then-declining HP
curve the right shape for that, or should the curve compound — each Setback
making the next one more likely or more costly?

---

## 3. AoS — Automaton of Shale

### Mechanics

A **Program** card shows 3–5 **Elements**, each with its own printed Target.
You **allocate your dice across the Elements up front**, then roll each
Element. An Element that misses its Target fails; **two failed Elements in one
Program is a Catastrophic Failure** costing 1 HP. You start with HP 2.

You work through four decks in a fixed order — **Routine, Specialized,
Unstable, Advanced** — eight Programs each (32 total). Each Program card has
two faces: a **front** (easier targets) and a **back** (harder). Failing can
**overheat** a Program, flipping it to its back face; escalation runs
stable → overheated → set aside. Targets across the whole system are almost
entirely 2s and 3s, with occasional 4s. Some Elements additionally require a
specific die colour.

### Designer's target

> "With AoS, think of it a bit like solving variant sudoku puzzles. There
> shouldn't be the same stress as you get from BAT or NAP, but it should be a
> sequence of puzzles with a non-obvious solution. There is a negative
> feedback loop with the overheated programs, but currently it still feels a
> bit samey and linear. I almost want you to have to 'build' sequences out of
> the cards to create programs and then use these to solve the advanced tasks.
> Kind of like building small functions in code that you can stitch together
> for more complex analyses (I recognize that that could result in a full
> redesign of AoS)."

### Diagnosis (structural; not yet measured)

- **The 32 Programs are independent and the order is fixed.** Nothing carries
  from one to the next except HP and the dice pool. Program 1 cannot change
  what Program 20 is or how you solve it. That is the "linear".
- **Every puzzle has the same shape**: spread N dice over 3–5 thresholds so
  that at most one misses. The targets barely vary (mostly 2s and 3s), so the
  *shape* of the right answer is the same each time. That is the "samey".
- **The overheat loop raises difficulty but doesn't change the puzzle.** The
  back face is the same Elements with bigger numbers — more pressure, not a
  different question.
- A variant-sudoku feel requires **constraints that interact**. Right now each
  Element is scored independently, so the allocation decomposes: there is no
  "if I put the green die here, this other Element becomes impossible," which
  is precisely where sudoku-like insight comes from. The colour requirements
  are the one existing source of interaction and they are sparse.

### The composition idea

The designer's instinct — build small reusable "functions" from cards and
stitch them together for Advanced tasks — would supply both missing properties
at once: state that carries forward (your library of built programs) and
constraints that interact (what you built determines what you can attempt).
It is also, as the designer notes, close to a ground-up redesign of the
family.

---

## What an outside perspective would be most useful on

1. **BAT**: is "the wall is the residue of what you failed to claw" the right
   structure for the stated target, or is there a cheaper change that produces
   the same "oh shit, is this enough?" moment? Separately — what should the
   Splice Phase permanently *cost*, given that today it costs nothing in 60%
   of games and the only persistent loss in the system is a banished die?
2. **NAP**: the exam gate already delivers legible preparedness plus real
   doubt. How do you make the *year* compound without just lowering the
   numbers — i.e. make Setbacks raise the cost of future Setbacks rather than
   simply subtract?
3. **AoS**: is there a way to get interacting constraints and carry-forward
   state — the variant-sudoku feel — **without** a full redesign? Specifically:
   can per-Element independent scoring be replaced by something where
   allocation decisions couple, using the existing card faces and colour
   requirements rather than new components?
4. Across all three: these are **puzzles with semi-mitigated luck**, not
   optimisation problems. Where does each family currently fail that standard?
