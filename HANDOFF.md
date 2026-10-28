# Handoff — The Nobulous Set

**For a fresh Codex or Claude Code session.** You have no prior context on this project;
everything you need is here. Read this file first, then `README.md`.

---

## 1. What this is

A finished fan expansion for the board game **20 Strong**, consisting of three
standalone solo games and a campaign overlay. The design work is done and the
balance is calibrated by simulation. Your job is **infrastructure, not design**:
publish the repo, host the images, and get the Tabletop Simulator mod working.

**Do not change card text, targets, or rules wording.** Those numbers came from
tens of thousands of simulated games; edits will silently break the calibration.
If something looks wrong, raise it rather than fixing it.

---

## 2. What Jon will have done before you start

- Downloaded `nobulous-set-repo.zip` and unpacked it to a local folder.

The zip ships the working tree only, **not** a `.git` directory — the packed
history pushed it over the upload limit. So your first move is:

```bash
git init -b main && git add -A && git commit -m "The Nobulous Set"
```

Run `git log --oneline` first in case Jon already did it.

---

## 3. Repository layout

```
images/           49 PNGs — card sheets and backs. The TTS mod points here.
rules/            4 player rulebooks (PDF) + RULES_CHANGELOG.txt
print-and-play/   4 PnP PDFs, Letter, 9 cards/page + PNP_CONTENTS.txt
playtest/         browser playtest lab for BAT, NAP, AoS and the NRJ finale
tts/              build_mod.py, decks.py, lua.lua, dice_objects.json
generator/        the card generator that produced images/ and print-and-play/
                  (gen.py builds the decks, pack.py merges them per game)
README.md         public-facing
SETUP.md          the short version of this file
CARD_MANIFEST.txt every deck: grid, orientation, which back it uses
CONTENT_NOTICE.md fan-content disclaimer — keep it
```

The browser interface runs from the repository root with
`python -m http.server 8000 -d playtest/dist`. Its HTML, CSS and JavaScript are
editable source files; the card sheets and rule PDFs copied into its `assets/`
folder are deployment copies, not the authoritative masters.

`images/` is **build output**, not hand-edited. Never edit a PNG directly.

---

## 4. Task one — publish the repo

Ask Jon for his GitHub username. Then:

```bash
gh repo create USER/nobulous-set --public --source=. --push
```

Without the `gh` CLI, create the repo on github.com and:

```bash
git remote add origin https://github.com/USER/nobulous-set.git
git push -u origin main
```

The repo is ~28 MB, well inside normal limits. No LFS needed.

**Verify hosting before going further.** Open this in a browser, substituting
the username:

```
https://cdn.jsdelivr.net/gh/USER/nobulous-set@main/images/BAT_Encounters_TTS.png
```

jsDelivr caches on first request and can take a few minutes to warm. A 404
immediately after pushing is normal; wait and retry before debugging. If you
need instant feedback, the same file is at
`https://raw.githubusercontent.com/USER/nobulous-set/main/images/...`.

---

## 5. Task two — build the TTS mod

```bash
cd tts
python3 build_mod.py --user USER
```

Only `json`, `os`, `sys`, `random` are used — no dependencies. It writes
`NobulousSet.json` and `REQUIRED_IMAGES.txt` next to itself. Both are
gitignored; they are build output.

Flags:

| flag | effect |
|---|---|
| `--user NAME` | GitHub account, required |
| `--repo NAME` | default `nobulous-set` |
| `--ref REF` | branch or tag, default `main` |
| `--raw` | raw.githubusercontent instead of jsDelivr |
| `--local` | `file:///` URLs, layout testing on one machine only |

Check the tail of the run: `REQUIRED_IMAGES.txt` must show `ok` on every line.
Any `MISSING` means an image did not make it into `images/`.

Then copy the save into place. On Windows:

```
%USERPROFILE%\Documents\My Games\Tabletop Simulator\Saves\NobulousSet.json
```

---

## 6. Task three — verify in TTS

Load the save and check, in this order:

1. **Every deck resolves.** A deck showing a grey question mark means its URL
   404s. Check the exact filename against `REQUIRED_IMAGES.txt` — matching is
   case-sensitive.
2. **The Control Panel shows buttons.** If not, the Lua failed to load; open
   Scripting and look for an error.
3. **Two-sided decks flip correctly.** Seven decks use `UniqueBack`. Take a card
   from `Specialized Programs` and flip it: it must show *the same Program*
   Overheated, with one element's Target one higher. If flipping shows a generic
   back, `UniqueBack` did not apply.
4. **Landscape cards sit correctly.** Eleven decks are `SidewaysCard`. NAP Tasks
   and Apprentices, AoS Technicians, BAT Lab Rats and the NRJ NAP decks should
   all be wider than tall in hand.
5. **The dice are present** at the left edge: 4 Purple, 4 Blue, 4 Green,
   4 Yellow, 1 Red, plus Health / Strategy / Recovery and the Chip. These reuse
   Jon's existing Steam-hosted images and need no upload.
6. **Press each setup button.** BAT, NAP, AoS and Imposter should each deal a
   sensible table and print a chat message. Cycle NRJ Tier to III first and
   confirm the extra module decks appear.

---

## 7. Task four — publish to the Workshop

Before uploading, **pin the images to a tag** so a published mod cannot change
under a player mid-game:

```bash
git tag v1.0 && git push --tags
python3 tts/build_mod.py --user USER --ref v1.0
```

Reload that save, then Games → Save & Play → Workshop Upload. Put the repo URL
in the description. Add the Workshop link back into `README.md`.

---

## 8. If Jon asks you to change a card

The card art is generated. The flow is:

```bash
cd generator
python3 build_bat.py      # or build_nap.py / build_aos.py / build_nrj.py
python3 pack.py           # re-merges the per-game PnP PDFs afterwards
```

Each script writes its sheets and PnP pages into an output directory. **Check
the paths at the top of `gen.py` first** — they point at the original authoring
machine (`/home/claude/cards/out`) and will need repointing to `../images`.

Dependencies: `weasyprint`, `pillow`, `reportlab`, `pypdf`, and `pdftoppm` from
poppler-utils. **WeasyPrint on Windows needs GTK installed separately** and is
genuinely awkward; WSL or a Linux container is far easier. The shipped PNGs are
prebuilt precisely so nobody has to do this to play.

After regenerating: commit the changed PNGs, push, and only rebuild
`NobulousSet.json` if a deck's **card count, grid size or back** changed. Pure
art changes need no new save file — players pick them up when jsDelivr's cache
expires.

---

## 9. Things that will look like bugs and are not

- **The BAT Buff HP card is a one-card deck and a mat, not a playing card.** It
  is a 15-space track laid out 5 rows by 3 columns with square spaces, so a die
  sits on it as the marker. It is never shuffled or drawn. Difficulty only
  chooses the starting space, so re-tuning the dial never changes the card.
- **AoS Program decks have 8 cards, not 16.** Stable and Overheated are two
  faces of one card.
- **NAP Task cards look upside-down at the bottom.** The Demand half is printed
  rotated 180°; you turn the card over on the table. This is one-sided.
- **NRJ cards have base-game colors.** Deliberate — a Corrupted Limitation is
  meant to look like a Limitation. The dark blue foot band reading NOBULOUS
  RESEARCH JOURNAL is how you sort them out afterwards.
- **Some NRJ cards use a base-game card back.** Also deliberate: cards shuffled
  into a base deck must be indistinguishable face-down. `CARD_MANIFEST.txt` has
  the mapping.
- **The Lua enforces no rules.** Intentional. It deals and counts only.

---

## 9b. BAT turn-flow invariants (four deadlocks came from breaking these)

`playtest/dist/bat.js` gates the Experiment turn on two flags, and every gate
needs an escape or the game locks with no route out but a new game. All four
of these were live bugs, found and fixed together:

- **`state.turnLocked` must clear on any Recover, not only a Recover that
  moved a die.** Recovering nothing is a legal turn end. While it stayed set,
  no other Rat could be activated and the notice told the player to "finish it
  with Recover selected" - the button that could not finish it.
- **A set-aside Red must only block the roll while some Rat may legally take
  it.** `redTakers()` is the single source of truth: normally any standing Rat
  other than the active one, and under Restricted Materials (Experiment 10) the
  active Rat itself. An empty list must not block. Both the buttons and the
  move handler read that one list.
- **Unbanked successes count. `resolve()` applies them, it does not refuse.**
  rules/bat.html asks only for "successes greater than or equal to the Target
  value" - there is no apply-to-the-Experiment step in the printed game. The
  Add selected dice button exists so dice can be locked before a reroll, and
  it had quietly become a gate: leave a hit unbanked and `canSucceed()` saw a
  total under the Target, so every Success button went dark while Failure
  stayed live and refused with "Add your hits to the Experiment first" - a
  dead end built out of a convenience. `totalSuccesses()` = banked + loose
  now drives `canSucceed()` and the roller headline, and resolving banks
  whatever is still loose so the Resolve row keeps the record.
  `dueActions()` had to follow: it called resolve due only when nothing was
  loose, which - once loose dice counted - silently suppressed the halo on
  BOTH the Success buttons and Failure whenever a die was left unbanked.
  Resolve is due as soon as no roll remains, and "allocate" is prompted only
  while a throw is still coming, that being the only time banking protects
  anything.
  (The older hazard still stands: exhausting does not clear a die's face, so
  anything that exhausts before reading `pending` strands scoring dice.
  Exhausting is the last thing `resolve()` does, at step 8.)
- **`allocateSelected()` keys off the pending list, not the "rolled" zone.** The
  pending list is already scoped to the current Experiment, and this is what
  lets a save stuck by the bug above be rescued.

- **A selected die is fully vibrant, everywhere.** One rule at the END of
  styles.css owns it, carrying four classes on the hardest case so it outranks
  every dimmer without `!important`. Anything added later that dims a die must
  exclude `.selected` or it will simply lose to that rule. Note the idle Rat
  box fades its own CHILDREN, not itself: opacity on an ancestor composites
  the subtree as a group, so while `.bat-rat.idle` carried `opacity:.74` no
  rule on a die inside it could ever restore full strength.
- **A pick in another Rat's pool replaces the previous pick.** Only one die
  may be borrowed per Experiment, so `chooseDie` deselects that Rat's other
  available dice rather than letting a second one stack up and then having
  `lendDie` complain. If the die being dropped is the one already lent AND it
  is still in hand, `borrowedId` is released with it - but a die that has been
  THROWN stays committed, because only the return check can send it home. The
  active Rat's own pool is untouched by this: it still multi-selects.
- **Borrowing is not timed, and "Return die" keys off the die, not the phase.**
  The rules allow one borrowed die per Experiment before either Strategy roll,
  so phase number is not a test for anything here. A die is returnable while
  its zone is still `available`; once thrown, only the banished-die check can
  send it home. `c.phase === 0` used to stand in for "not yet thrown" and is
  wrong as soon as a die can be borrowed between rolls.

## 9a00000000. Four difficulties, and the files that outlived Brutal

BAT had five difficulty levels; the other three games had four. BAT now has
the same four as everything else - **Easy / Standard / Hard / Nobulous**.

Difficulty is TWO numbers, not one. An older design used a single number for
both Specimen count and Buff HP, and that sentence survived in places long
after it stopped being true:

The dial is now **Tyrant Health**, not Buff HP. Buff HP was an ad-hoc fix
for a chip that only read to 20; folding it into Health removed a component
and a lookup, and the card survives as an optional track on which any space
is a legal start.

| | Specimens | Tyrant Health | win rate |
|---|---|---|---|
| Easy | 5 | 9 | 62.7% |
| Standard | 6 | 10 | 53.2% |
| Hard | 7 | 12 | 40.1% |
| Nobulous | 8 | 14 | 28.1% |

Win rates are the no-NRJ column of the cross-tab in `simulation/RESULTS.txt`
(rerun 2026-10-27 after the policy retune, 20,000 games a cell): the
difficulty dial alone, with no tier module, which is what these rows are.
The tier columns and the per-Rat spread are in that file. A point of Tyrant
Health is worth about 6 points of win rate, so the dial is far flatter than
the finale's Health, where a point is worth 19 to 41.

**These rose about 7 points in the retune and the dial was never re-pitched.**
BAT's battle policy had been sitting on the wrong side of a threshold cliff
(`THRESHOLD_MARGIN` 1.16 measures 46.3%, 1.17 measures 54.1%). Standard now
lands inside the 47-57% community band, which is the first time any game in
the set has, but Easy at 62.7% is above it. See the CAVEATS block in
RESULTS.txt.

These are about 4 points above the ladder the model reported before the
rerun, because the +1 it carried in `TARGET_DELTA` had been adopted onto the
cards at b57eedd and was then being charged twice. `rules/bat.html` no
longer prints win rates - that column came out of all four rulebooks - so
there is no printed figure to contradict these, and no second opinion
either: the Health dial was tuned against this model.

Five places carry the ladder, and the first pass at removing Brutal missed
four of them. If you change it again, change all five:

1. `simulation/bat.py` - `DIFFICULTY`, the authority.
2. `simulation/healthsweep.py` - `SPEC` and the Health loop.
3. `playtest/dist/bat.js` - `specimenCount` AND `HEALTH_BY_DIFFICULTY`, which
   are separate literals at opposite ends of the file (lines ~20 and ~315).
4. `playtest/dist/index.html` - the `#batDifficulty` options.
5. `rules/bat.html` - the difficulty table, then rebuild the PDF.

`simulation/table.py` and `generator/build_bat.py` used to carry it too and
no longer do: table.py reads the difficulty names off `bat.DIFFICULTY`, and
the gold spaces came off the Buff HP card when it became optional.

Number 7 is the one that bites. The card is a 15-space track and `track()`
marks the difficulty starts in gold; those marks were still `{15, 12, 9, 7,
5}`, a dial two re-tunes out of date, of which only `7` is still a real
starting value. The printed card was telling players to start on numbers the
rulebook no longer lists. Rebuild with `build_bat.py` then `pack.py`, and
copy the PnP, `BAT_BuffHP_TTS.png` and `CardBack_BAT_BuffHP.png` out to
`print-and-play/`, `images/` and `playtest/dist/assets/`.

**The track runs 15 down to 1, not 1 up to 15.** `build_bat.py` lays it out
`range(15, 0, -1)`, so 15 is top-left and 1 is bottom-right and damage walks
the die forward through the grid. The app had it the other way round, which
put the starting space in the opposite corner from the card in a player's
hands. The app now follows the card, and marks the same four gold spaces.

In the app's CSS, `.marked` is restated after `.gold` on purpose: a gold
space is where some difficulty STARTS, `.marked` is where the die IS, and at
Easy and Hard those are the same space. Appending a gold rule at the end of
the file silently took the die's own highlight away.

Three tables in `simulation/README.md` still show a Brutal row. Leave them.
They are the recorded evidence for specific modelling fixes, measured against
the ladder published at the time; the Results section says so.

## 9a0000000. A Rat's Health is correctable, and a knockout is undoable

`rat.down` was set on a knockout and cleared NOWHERE, so a Rat put out by a
misread attack stayed out for the rest of the game. There was no way back
because there was no way to touch its Health either: `data-rat-hp` appeared
only in the click guard's allow-list and in a handler, with no markup
anywhere rendering such a button. A handler nobody could reach.

The Rat box's "2 HP" summary is now a stepper, and `down` follows the Health
(`rat.down = rat.hp <= 0`) instead of latching - so + is the undo, and it
reports "<name> is back on N HP."

Armor, for the record, is already right and should stay that way: a Rat's
Upgrade either meets the blow's damage and shatters, or bounces it off
entirely. It never takes partial damage and nothing spills past it to Health
(except Crushing Blow's 1, which is printed to bypass armor). That is
rules/bat.html's "Two kinds of armor" box - the Tyrant's Splices accumulate
damage, a Rat's Upgrades do not.

## 9a000000. The Buff HP card shows its die

The Buff HP card is the one component in BAT with a physical tracker on it -
15 square spaces, 3 across and 5 down - and the app showed only "4 / 4" in a
spinner. `buffTrack()` now draws the grid with a marker on the current value,
which walks down as damage lands and disappears at 0, when the Health die
moves on to the first Splice.

The track is READ-ONLY; the +/- buttons still set the value. Making the
spaces clickable would be a second way to set the same number, and the two
would have to be kept in agreement for no gain.

**The die shows REMAINING and ticks down** - settled by Jon. When it reaches
the next card it is SET to that card's Value and counts down again. So one
die runs the whole Tyrant: Buff HP first, then each Splice in turn, and the
Health dial takes over at the end (the dial is its own component; the die
does not sit on it).

In the APP the track replaces the Buff HP card art entirely - the art was a
picture of a track with the real readout beside it, so the track itself takes
the slot. It is sized to the card footprint (aspect-ratio 5/7) so the Tyrant
row does not reflow. The printed card is untouched: build_bat.py still makes
it, pack.py still places it (PnP page 6), and images/BAT_BuffHP_TTS.png is
still needed for that - do not delete it just because the app no longer loads
it.

`frontSlot(b)` already knows which card is taking damage, so the marker just
follows it - `healthDie(n)` is shared by the Buff HP grid and the front
Splice cell. A destroyed card has no die, and neither does one the damage has
not reached, which keeps exactly one die on the track at all times.

rules/bat.html used to say the die sits on the card "showing how much that
card has taken", which contradicted both this and the setup line. Corrected
to "has left"; the rulebook has been rebuilt and resynced.

## 9a00000. Starting the Tyrant battle

rules/bat.html, "Setting up the fight", step 4: "Sweep every personal die
still in the game - from all four Rats, available AND exhausted - into one
shared battle pool, all available. Banished dice stay gone." The app never
swept, so the battle opened with most dice exhausted and unusable. The sweep
runs in `ensureBattle()` AFTER `drawTyrantDice()`, because step 3 takes the
Tyrant's six out of the Rats' supply first; those are skipped, as are
banished dice.

It is guarded by `battle.swept`, NOT by sitting inside the
`if(!state.battle)` creation block. A battle created before the sweep existed
would otherwise never get one, and would keep the dice the Experiment phase
left exhausted for the rest of the fight. The flag also stops it firing
again: dice exhausted by battle rounds must stay exhausted.

Two things that followed from the same place:

- **The Tyrant's six dice were invisible outside its own turn.** They are a
  component in a bag on the table, so `renderTyrantSteps()` now shows them
  read-only on the Rats' turn - as spans, NOT buttons, because the
  `data-tyrant-die` handler toggles the bag/rolled split and would corrupt it.
- **Battle dice were dull.** The pool lives in `#batPool`, outside the
  `.bat-rat` boxes, so none of the per-Rat vibrancy rules reached it and every
  die fell through to the app-wide dimmer at saturate(.45). `.bat-pool-panel`
  and `.bat-tyrant-dice-row` now take the same middle vibrancy as every other
  unselected die. Anything else drawn outside a Rat box will need the same.

## 9a0000. Splicing Machine Malfunction (the Experiment deck running out)

rules/bat.html:143 - "If the Experiment deck runs out first, randomly select
enough unused Upgrade cards to bring the Tyrant to exactly 5 Splices, apply
them, and begin the battle. Running out of Upgrade cards is not a malfunction
- reshuffle the Upgrade discard instead."

The app implemented NEITHER half. `draw()` refused with a notice that named
the malfunction but offered no way to perform it, and `inBattle()` is
`splices >= 5`, so with an exhausted deck and fewer than 5 Splices there was
no route forward at all - the game simply stopped.

`machineMalfunction()` and `reshuffleUpgrades()` now do both, and
`ensureExperiment()` no longer gates on `state.deck.length`: that gate was
what let an exhausted deck idle with no Experiment on the table and nothing to
press. draw() owns the decision now.

The malfunction must ALWAYS reach five. A first version stopped when no
unused Upgrade was left anywhere, which left the game at three or four
Splices with no Experiment, no battle and nothing to press - the one outcome
that must not happen, because the Tyrant track is five Splices wide and
cannot be built with fewer. It now falls back to a random Upgrade index, as
simulation/bat.py:1470 already did.

Two things worth remembering:

- **The discard holds NAMES, not cards.** Every `state.discard.push` goes
  through `cardName(card)` or `cards[i].name`, so a card object never enters
  that pile. Both reshuffles filtered it with `typeof x !== "string"` and
  therefore always found nothing - the Upgrade deck could empty and never
  refill. A real game stalled on "The Upgrade deck and its discard are both
  empty" with twelve Upgrades in the discard and eight Experiments still in
  the deck. `reshuffleUpgrades()` now looks each name back up through a
  name -> card map built from `upgrades`, `specimens` and `BAT_MODS`;
  Experiment names match nothing and stay put. This predates the malfunction
  work - `swapUpgrades()` had the same dead filter.
- simulation/bat.py had both halves right all along (splice_turn reshuffles;
  play() applies the malfunction before start_battle). The app was the
  outlier, as with the AoS reroll - so the ladders are unaffected.

## 9a000. The next Experiment must not look like the next turn

Resolving deals the next Experiment immediately, so its card - and its effect
controls - were on the table while the PREVIOUS turn still owed a Recovery.
Seeing "No Purple available" on a fresh Load-Bearing Trial reads as "my turn
has started", and then nothing works: the Rat cannot be changed, because the
old turn is still open.

So the Experiment's controls stay hidden while `state.turnLocked && !c.phase`
- a locked turn with the card still at phase 0 means the board is waiting on
Recover, not on this Experiment. And Recover itself takes `.bat-required`
(red, pink halo) rather than the gold "this is next" pulse: the turn does not
end without it.

Worth noting what this was mistaken for. The report arrived as "I cannot
select a different Rat on Load-Bearing Trial", and the Rat lock, the Reset
turn button and the Purple fallback were all working correctly. The fault was
that the board showed the next Experiment's furniture before its turn, so the
player was answering the wrong question.

## 9a00. BAT messages go to the toast as well as the panel

`#toast` is in index.html already - fixed to the viewport, styled,
role="status". AoS used it 31 times; BAT used it zero. Every BAT message went
only into `#batEffect` at the TOP of the page, while most clicks happen down
among the Rat boxes, so a refusal was printed somewhere the player was not
looking. `setNotice()` now calls a local `toast()` as well as writing the
panel.

This is what made "I cannot select a different Rat" feel like a dead end on
Load-Bearing Trial. Nothing was broken: the refusal names the way out
("press Reset turn"), Reset turn works, and switching Rats afterwards works.
The message was simply off-screen.

NOTE when measuring this: a browser pane that is not painting does not advance
CSS transitions, so `getComputedStyle(toast).transform` stays at the hidden
`translate(-50%,120px)` even with `.show` applied and matching. Set
`style.transition="none"` before measuring, or the toast looks broken when it
is not.

## 9a0. The Experiment effect panel carries BOTH the controls and the notice

`#batEffect` had `display:none` in `.bat-effect`, with nothing anywhere to
turn it back on. The `gap:.7rem` in the same rule gives the intent away - gap
only does anything on flex or grid. The swap prompt beside it shows the
pattern that was meant: a real display value plus a `.hidden` class toggled
from JS.

Two things sat behind it, invisible:

- **Every per-Experiment control.** Nine Experiments have one - 0 Baseline
  Calibration (flip), 1 Fine Motor (yellow fallback), 5 Load-Bearing (purple
  redraw), 6 Diagnostic (peek), 7 Rapid Response (green fallback), 14 Reagent
  Exclusion (exclude), 15 Containment Failure (reduce + yellow roll), 17 Field
  Retrofit (swap selects), 18 Methodological Optimization (reduce to 0). The
  handlers were all correct; they simply could not be reached.
- **`state.notice`.** This panel is the ONLY place BAT renders it, so every
  message the game produced went nowhere on screen.

The other eleven Experiments need no control: 2, 4 resolve in `draw()`, 13 in
`roll()`, 19 in `resolve()`, 8 in `canSucceed()`, 9, 10, 12 in `validateRoll()`,
11 in `borrowProblem()`, 16 in `maxPhase()`, and 3 has its own visible prompt
(`#batSwapPrompt`).

The two jobs are now split. `#batEffect` keeps `state.notice` alone - the
running commentary, which is not about any one card. The CONTROLS render into
`#batEffectActions`, a container inside the Experiment card's own article, so
they sit directly beneath the card whose text they act on, and they need no
caption because the card above already carries the name, Target and effect.

Required effects are red and wear the halo (`.bat-required`, sharing Move
Red's `batRedDue` keyframes - red means "the turn does not go on until you
press this"). Optional ones are ordinary buttons. The split comes straight
from the printed text:

  REQUIRED   0 flip, 3 Contaminated Tissue, 14 Reagent Exclusion, and the
             1 / 5 / 7 colour fallbacks
  OPTIONAL   6 peek ("you MAY"), 15 Containment Failure ("you MAY CHOOSE"),
             17 Field Retrofit ("you MAY"), 18 Methodological ("You MAY")

1, 5 and 7 are required only when their colour cannot be committed. They used
to render regardless and then refuse the press with "A Yellow die is available
to commit"; they now appear only when `!canCommitColor(...)`, which is also
what lets the halo mean something - a red pulsing button is always one you
must press.

The Failure button takes the same red treatment once the roll cannot reach
the Target AND every Strategy roll is spent: failing is the only move then,
not a choice. The test is `c.phase >= maxPhase(c)`, NOT
`dueActions().has("resolve")` - "resolve is due" goes true whenever nothing
happens to be selected, which is not the same as having no roll left, so
Failure used to redden while the Rat still had a throw that could save the
Experiment.

Chasing that turned up a separate bug. `validateRoll()` and the roller button
both hardcoded `c.phase >= 2 || (c.phase === 1 && c.e === 16)` instead of
asking `maxPhase(c)`, which already knew about Experiment 16 AND about
Mottle's Experimental Subject bonus phase. The bonus was granted by one
function and refused by the other, so **Mottle's "+1 STR for that Experiment"
never actually gave a third roll**. Both call `maxPhase(c)` now; any future
source of extra Strategy phases belongs in `maxPhase` and nowhere else.

That column is only about 140px wide. Flex children do not shrink below their
content width without `min-width:0`, and Field Retrofit's two Upgrade
dropdowns are wide enough to push straight out of it - hence the explicit
`flex:1 1 100%; min-width:0` on the controls.

## 9b0. Recovery is once per turn, and gated on turn STATE

Both Recover buttons stay on screen after they are pressed. Neither checked
whether the turn's recovery had been taken, so a second press simply paid out
another REC-worth - Rummage recovered 3 on REC 2, and the Battle phase would
have given 4 per press.

The Experiment phase now requires `state.turnLocked` (set by the roll) and an
unresolved-free board (`!state.current.phase`, i.e. the card showing is the
NEXT Experiment). Recovering clears turnLocked, so a second press fails the
same gate - there is no flag to leave stale. An earlier attempt DID use a
flag and had to be cleared in `draw()`, which is not called when the fifth
Splice lands, so the last Experiment's recovery was refused. Prefer a
condition over a flag wherever the turn state already says it.

The Battle phase has the right flag already in `battle.needRec`; it just
recovered the dice before consulting it.

REC + 2 in the Battle phase is NOT a bug - rules/bat.html:182 prints it. The
Experiment phase is plain REC, per rules/bat.html:72.

Entering the battle clears `turnLocked` and `turnRedPlaced`. `inBattle()` is
`state.splices >= 5`, so it flips the moment the fifth Splice lands, mid
resolve - the Experiment layout (and its Recover button) disappears while
turnLocked was still set, which left the attacker choice stuck behind a
button that no longer existed.

## 9c0. "This turn" bonuses must expire with the turn

`state.recBonus` carries Mottle's +1 recovery from Experimental Subject or
Specimen Adaptation. It used to be cleared only `if(n && extra)` - that is,
only when dice actually came back AND a bonus had applied. End a turn
recovering nothing and it survived, and `recBonusFor()` reads it without
rechecking whether a Specimen is on the table at all. Mottle then recovered 2
on a printed REC of 1, on a turn with no Specimen revealed and none held,
while the notice cheerfully credited "Experimental Subject".

It is now cleared unconditionally when the Rat recovers, which is exactly
what "this turn" means. Anything else granted for one turn should be
cleared the same way, not when it happens to be consumed.

The recovery cap is also enforced and displayed in the Experiment phase now,
not just the Battle phase. Previously you could select four dice, press
Recover, and `.slice(0, rec)` silently returned one - which makes a correct
cap look broken. The Exhausted header reads "n of cap selected to recover".

simulation/bat.py is not affected: it recomputes `recovery` as a local each
turn, so it has nowhere to leak.

## 9d0. The Experiment turn runs in the printed order

rules/bat.html sets it out, and `bat.js` follows it exactly:

  1 select a Rat; 2 place Red (if applicable); 3 commit dice (borrowed
  included); 4 roll selected; 5 add selected dice to the Experiment
  (optional); 6 repeat 3-5 up to STR rolls; 7 resolve; 8 exhaust dice, a
  borrowed die staying in the active Rat's rolled area with its Roll check
  button beside it; 9 recover selected.

Step 2 commits you to step 1. Once Red is placed on a Rat other than the
active one, `state.turnRedPlaced` blocks `changeRat()` - otherwise placing
Red would be a free look: put it somewhere, see how the pools fall, then
switch Rats. The Reset turn button (in the Red stat tile, shown only while
`!state.turnLocked`) undoes the setup instead: Red back to set aside, any
borrowed die home, every selection cleared. It does NOT rewind an ability
already used - those are tracked per Experiment, not per attempt. The flag
clears with the turn, in the same place `turnLocked` does.

Two orderings are easy to get wrong, and both were wrong before:

- **Nothing exhausts until step 8.** `roll()` used to exhaust everything once
  `phase >= maxPhase(c)`, which put step 8 ahead of steps 5 and 7 - you could
  not bank dice that had already been swept away. `exhaustRolled(keepId)` is
  now called only at the end of `resolve()`.
- **The borrowed die's return check is step 8, not step 6.** The rules say
  "After the Experiment resolves, roll the borrowed die by itself", so the
  check has to outlive the Experiment that created it: `state.returnCheck`
  ({dieId, borrower}) survives `state.current = null`, and `borrowCheckDue()`
  just reads it. Recover refuses while it is outstanding, which is what keeps
  step 8 ahead of step 9.

## 9d. One guidance channel: the gold pulse

`dueActions()` in `bat.js` is the single place that decides what the player
can usefully press, and every button in the Experiment flow asks it via
`due(key)`. The keys are `movered`, `roll`, `allocate`, `retcheck`, `resolve`
and `recover`, and the chain runs: place Red -> roll -> bank your hits ->
return check -> resolve -> recover -> next turn.

Two rules keep it honest:

- **A button only glows when it is also enabled.** A glowing disabled button
  is worse than no glow; it tells the player to press something that will not
  respond. The Battle phase's step-1 button used to do exactly that while it
  waited for dice to be committed.
- **But do not DISABLE the main action either - let it refuse out loud.** A
  disabled button swallows the click, so a blocked roll read as "I pressed it
  and nothing happened". The per-Rat Roll button used to disable itself while
  Red was unplaced, while the roller panel's Roll button stayed live and
  answered "Place the Red die on a Rat other than the active one before
  committing" - two buttons for one action, disagreeing about whether to
  explain themselves. Both are live now; `validateRoll` does the refusing and
  carries the words, and a short reason also sits in the action row so the
  block is visible before anything is pressed.
- **One channel, one exception.** Move Red had its own blue `.calling` pulse,
  which competed with the gold `.bat-rec-due` used everywhere else. The blue
  pulse is gone. Gold means "this is next" throughout, except Move Red, which
  is about the Red die itself and so takes the die's own colour with a heavier
  halo (`.bat-move-red.bat-rec-due`, keyframes `batRedDue`). The pulse still
  means "press me next"; only the hue follows the die.
  Note the glow is the LIGHT pink `#ff6f9c`, not the button's dark red
  `#c71054` - a dark-red glow on a dark panel vanishes no matter how wide the
  ring is, which is what made the first attempt look flat.

The Battle phase keeps its own numbered 1/2/3 step list, which is a stronger
signal than a halo there, and `dueActions()` deliberately returns nothing
while `inBattle()`.

## 9e. Banked dice live in the Resolve row

`allocateSelected()` records a SNAPSHOT of each die it banks into
`state.current.banked` - `{id, color, face}` - and `renderBanked()` draws
those into `#batBanked` in the Resolve this Experiment row. The snapshot
matters: the die objects are exhausted at the end of the Experiment, and Red
has its face wiped when it is set aside, so reading the live objects later
would show blanks.

Banked dice are filtered out of the Rat's rolled box by `isBanked(id)`, which
is what stops them being re-selected for a reroll after their value is
already counted. They render as `<span>`, not `<button>`, so they cannot be
clicked at all. `state.current.banked` starts undefined and dies with the
Experiment, so nothing needs resetting.

## 9c. A BAT die can be in five states at once

`.rat-die` can carry `rolled`, `eligible-reroll`, `selected`, `borrowed` and
`banked`. Every one of those is a two-class selector, so they all have equal
specificity and the one declared LAST in `styles.css` simply wins - and the
app-wide dimmer `.rat-die:not(.selected):not(.rolled)` is THREE classes, so
it beats all of them. That ate four separate markers before it was noticed:

- the blue `eligible-reroll` outline painted over the gold `selected` halo, so
  a die picked for a reroll did not look selected;
- it painted over the dashed `borrowed` outline too;
- and `.bat-rat.idle .rat-die.selected` dulled a selected BORROWED die, because
  that die sits in its owner's idle box while belonging to the active Rat;
- and the dimmer washed out the BANKED chips in the Resolve row, because a
  banked die is neither `.selected` nor `.rolled`, so `.rat-die.banked`'s two
  classes lost to its three.

So: `border` carries "borrowed" (inside the die), `outline` carries reroll and
selection state (outside it), `filter` carries vibrancy, and the combinations
that matter have their own explicit rules.

The ladder is APP-WIDE, not a BAT thing: `.die` (AoS), `.roll-die` (NAP and
NRJ) and `.rat-die` (BAT) all run through the same two rules, so a die looks
the same in every game. BAT reached middle vibrancy first through its own
per-Rat rules, which left the other three at saturate(.45) and visibly washed
out beside it; the global dimmer now carries the same value, and BAT's own
rules agree with it rather than overriding it.

Exhausted dice keep their own signal - opacity, not filter - so an exhausted
die is dim but still its own colour, and a SELECTED exhausted die goes to
full strength with opacity 1.

Current vibrancy ladder, all via `filter`:

  saturate(1.2) brightness(1.12)   selected, anywhere; banked chips; the
                                   set-aside Red die; banished chips
  saturate(.75) brightness(.95)    unselected dice, in ANY Rat's box - idle
                                   Rats included, since the pronounced
                                   selection halo carries the distinction
  (none)                           rolled dice

The set-aside Red and banished chips are records rather than controls, but
they are still `.rat-die` spans, so the app-wide dimmer caught them too. When adding another die state, give
it its own visual channel or an explicit combined selector - and check
`getComputedStyle(el)`, not the class list. Classes being right is exactly
what made these look fine in testing.

Bump the `?v=` on **styles.css** in `index.html`, not just the scripts. CSS
added without that bump never loads at all.

When changing this flow, play a full Experiment through to the Battle phase.
Each of these only appears a few turns in.

## 10. Known open items

Not your job to fix, but worth knowing if Jon raises them:

- **AoS runs low from Standard down** — 35.0% at Standard and 18.0% at
  Nobulous against a 47-57% community band, the lowest of the three games,
  and the only game the 2026-10-27 policy retune did not move at all: its
  policy was already the best available, so this is the game and not the
  player.
  The old entry here called out "AoS Unstable" at a 1-in-7 win rate; that
  was a whole-deck difficulty, and difficulty is now the Routine /
  Specialized / Unstable MIX, so the hard end is the Nobulous 2/3/3 mix.
  Still labelled experimental in the rulebook.
- **Every difficulty dial in the set now needs re-pitching.** The policy
  retune of 2026-10-27 moved NAP from 42.1% to 76.0% at Standard, the
  finale from 50.9% to 61.6% and BAT from 46.5% to 53.2%, because the
  models had been playing three of the four games 6 to 34 points below
  their own best available policy. Every Credit goal, Health value and
  Target was calibrated against the old play. Nothing has been re-pitched.
- **NAP has almost no dice pressure left.** Under the retuned policy 2% of
  its commit decisions happen at two dice or fewer, against 32% before,
  with a mean pool of 10.9 dice. It wins 76% and never feels the pool.
- **NAP Impostor Tasks have no recovery-color dot**, unlike every other
  Assignment. A rules decision is pending.
- **Two rules questions are open**, both recorded at the end of
  `rules/RULES_CHANGELOG.txt`: whether the Red die joins the BAT battle pool,
  and what NAP's Slacker means by "voluntarily draw an additional Assignment".
  Neither blocks anything you are doing.
- Card art is 200 DPI (633 × 886 px). Fine on screen; would want 300 for print
  production.
- **The BAT Tyrant battle was rewritten.** Jon played the old one and found
  it tedious, and the simulation agreed: the correct play was to commit only
  what recovery returned, so the dice pool was a per-round income rather than
  a budget, and the fight ran 9.1 rounds and ended with 7.1 of about 10 dice
  unspent. Five changes, measured in `simulation/proto/` and now live in
  `rules/bat.html` and `playtest/dist/bat.js`:

  1. **A Splice must be MET in one attack or the blow bounces** - the rule a
     Rat's Upgrades already used, applied to the Tyrant. Overflow carries and
     may break the next Splice too.
  2. **Splice effects fire once, on break**, and banish a die of that
     Splice's own color. They are no longer per-round auras.
  3. **A Rat's Upgrade is spent whenever it blocks**, whatever the blow was
     worth.
  4. **The Tyrant breaks containment after 8 rounds.**
  5. **Buff HP is gone.** It existed because the Health chip only reads to
     20, so the Tyrant's bulk had to live on a separate card; with the
     Splices carrying the fight those points fit on the dial again.
     Difficulty is one number, **Tyrant Health 9 / 10 / 12 / 14**. The card
     stays in the PnP as an optional tracker with no gold spaces.
  6. **No commit cap.** "Up to 6 dice" is gone. Measured against a policy
     written to exploit an uncapped pool, removing it opens nothing:
     chaining walls uncapped scores WORSE than chaining under the cap, and
     dumping the pool is 7 points worse than playing sensibly. REC+2 is the
     real limiter.

  Spending now beats hoarding by 7.3 points, where it used to lose by 14.5,
  and the fight is 7.2 rounds instead of 9.1. The ladder came out nearly
  even on its own: **50.7 / 40.4 / 29.4 / 19.3**, steps of about ten points
  each, against the old -6 / -11 / -11.

  **The campaign rule had to change with it.** Because an Upgrade is now
  spent whenever it blocks, a winning party holds a MEDIAN OF ZERO Upgrades
  at the end - only 2% of wins left the 3 the old rule asked for. BAT now
  retains from the Upgrades the Rats held when the battle BEGAN, which
  94-96% of wins have 3 or more of (supply.txt, re-measured 2026-10-27 after
  the Upgrade-leak fixes), and which decouples the campaign from the armor
  economy entirely. Thematically it is also the better rule: the Rats are
  not the imposters, they chose what went into one.

  One layout trap: `.box` in rules/style.css is `break-inside: avoid`, so a
  box is an unbreakable block. Adding a fourth box to BAT's last page pushed
  the rulebook to four pages, and no amount of trimming prose elsewhere
  fixed it - the fix was to turn that box back into prose. If the page count
  jumps after an edit, count the boxes before shaving words.

  **`simulation/bat.py` still models the OLD battle.** It was deliberately
  not touched, so `table.py`, `RESULTS.txt` and `simulation/README.md` all
  describe rules that no longer ship. Promoting `proto/bat.py` over it, and
  re-running the cross-tab, is the outstanding job.

---

## 11. Definition of done

- [ ] Repo pushed and public
- [ ] A jsDelivr image URL loads in a browser
- [ ] `REQUIRED_IMAGES.txt` shows `ok` on every line
- [ ] All 28 decks resolve in TTS
- [ ] A two-sided Program card flips to its own Overheated face
- [ ] All four setup buttons deal a sensible table
- [ ] Tagged `v1.0` and the mod rebuilt against the tag
- [ ] Workshop item uploaded, link added to `README.md`
