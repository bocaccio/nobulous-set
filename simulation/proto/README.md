# BAT battle prototype

A proposed replacement for the Tyrant battle, kept apart from the shipping
model. `simulation/bat.py` is untouched and still authoritative; this
directory holds a copy of it with the changes behind flags.

`proto/bat.py` imports the real `simulation/dice.py` rather than copying it,
so the dice cannot drift. Everything else is a fork and **will** drift - if
`simulation/bat.py` changes in a way that matters, re-fork rather than
patching both.

## Why

The shipping battle has no resource tension, and the cause is one line of
the model's own commit policy:

```python
if self.commit_policy == "conserve":
    # Commit only what will come back, so nothing is lost for good.
    cap = min(cap, rat.effective_rec() + self.battle_rec_bonus)
```

You may commit up to 6 dice and you recover REC + 2, about 3. Committing
exactly what comes back is worth **43.2%**; committing fully is **36.1%**.
Hoarding is 7 points better, so the correct play is a risk-free trickle and
the pool is never a budget - it is a per-round income. The battle runs 9.1
rounds and ends with 7.1 of about 10 dice still unspent.

Worse, the dice and the loss condition are different economies. You lose
when all four Rats are knocked out; running the pool dry is not a loss
condition at all. The resource you manage is not the one that kills you.

## The changes

All five are flags in `bat.PROTO`, default off, so the original behaviour is
reachable in the same process and the two can be compared directly.

| flag | what it does |
|---|---|
| `threshold` | A blow must MEET a Splice's printed Value in one attack or it bounces off entirely - the rule `rules/bat.html` already uses for a Rat's Upgrades, applied symmetrically. |
| `overflow` | A broken Splice passes the remainder on, so a big hit can chain through several. On by default; without it, over-committing is wasted. |
| `break_banish` | Splice effects stop being per-round auras and fire once, when that Splice breaks, banishing a die of the card's own color. |
| `armor_spend` | A Rat's Upgrade is spent when it blocks, instead of blocking free forever whenever the blow is under its Value. |
| `health` | The Tyrant's Health, cut from 20 so the five Splices carry the fight rather than bulk. |
| `round_cap` | The Tyrant breaks containment after this many rounds. |

Plus a `commit_policy="threshold"` that can actually play the new game: read
what the front wall needs and commit enough to clear it, with a 15% margin
for the spread on the roll. It is a heuristic, not optimal play - treat the
policy gap as "does deliberate spending pay", not as a skill ceiling.

## Result

| | shipping | prototype |
|---|---|---|
| Standard win rate | 43.1% | 41.6% |
| battle length | 9.1 rounds | 7.2 rounds |
| dice left at the end | 7.1 | 3.5 |
| **spending vs hoarding** | **-7.1** | **+9.3** |

### The re-tuned dial

Buff HP had to be found again - the old 3 / 4 / 7 / 11 was calibrated
against a battle that no longer exists. Specimen count is unchanged.

| | Specimens | Buff HP | win rate | step |
|---|---|---|---|---|
| Easy | 5 | **5** | 49.9% | |
| Standard | 6 | **6** | 41.6% | -8.3 |
| Hard | 7 | **8** | 30.5% | -11.0 |
| Nobulous | 8 | **10** | 18.9% | -11.6 |

Two things worth noting. The ladder lands within about two points of the
shipping one (49.1 / 43.1 / 32.1 / 21.0) at every level, so the difficulty
*feel* is preserved while the texture changes completely. And the choice
between the two candidate ladders in `buffsweep.py` turned out not to
matter: the rows are flat enough that both target sets pick the same four
values, so the uneven Easy-to-Standard step is a property of the Buff HP
lever rather than of the targets. It improved on its own, from -6.0 to
-8.3, but the two hard drops at the bottom are still there.

## The trap, which cost two rounds of work to find

The obvious design is "the Tyrant eats dice instead of knocking Rats out,
so running dry is how you lose." It is implemented here as
`attrition` + `bite`, and it works exactly as intended: **100% of losses
become dice exhaustion.** It also makes the game worse. Hoarding comes back
*stronger* than in the shipping rules:

```
attrition, Health 4, REC+4     conserve 44.9%   threshold 37.4%   gap -7.5
```

**If dice are your life total, hoarding extends your life.** Making the
resource into the loss condition makes conserving it correct by
construction. An escalating bite (`bite_ramp`) to punish stalling does not
help either - it changes the difficulty without changing the ordering.

So: you can have "running out of dice is how you lose", or you can have
"spending aggressively is correct", but not both. What makes spending
correct is a deadline you do **not** control, which is what `round_cap` is
for, and which is probably why NAP has the tension BAT lacks - its Credit
goal is an independent finish line that dice scarcity bites against.

The felt question "am I going to run out of dice?" therefore has to stay a
near-miss: Standard wins finish with a median of 3 dice and 19% finish with
2 or fewer. It is not the thing that actually kills you.

## Not done

- **Rat abilities are not in the battle.** All eight (`careful_borrower`,
  `jury_rig`, `tool_keeper`, ...) are written against borrowing and Target
  numbers, neither of which exists in the battle, so switching them on means
  designing eight new abilities. A design job, not a simulation one.
- Nothing here has touched `rules/`, `generator/` or `playtest/`. The dial
  has to settle first.

## Running it

```bash
cd simulation/proto
python trial.py          # the policy gap, the ladder, how close the wins are
python buffsweep.py      # re-tune Buff HP against these rules
```
