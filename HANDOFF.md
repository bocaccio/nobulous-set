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

Each script writes its sheets and PnP pages into `gen.py`'s `OUT`, which
defaults to `generator/out` and is overridden by the `NOBULOUS_CARD_OUT`
environment variable. The `sys.path.insert(0, '/home/claude/cards')` at the top
of each `build_*.py` names the original authoring machine; it is dead weight,
not a blocker, because the script's own directory is already on `sys.path`.

Dependencies: `weasyprint`, `pillow`, `reportlab`, `pypdf`, and `pdftoppm` from
poppler-utils. The shipped PNGs are prebuilt precisely so nobody has to do this
to play.

**This DOES run on the Windows machine, and WSL is not needed.** Every
dependency is already installed; the only trick is that WeasyPrint's GTK
libraries live in the conda tree and are found through `PATH`, not through
Python. Verified 2026-10-28 by rendering all four families and diffing against
the committed art: 40 of 50 sheets came back BYTE-IDENTICAL, including sheets
generated on the original Linux machine, so the environment is exact and not
merely close.

```bash
# from generator/ - the Library/bin entry is what WeasyPrint needs
PATH="/c/Users/weeks/miniforge3/Library/bin:$PATH"   NOBULOUS_CARD_OUT=/some/scratch/dir   C:/Users/weeks/miniforge3/python.exe build_nap.py
```

`pdftoppm` is already on `PATH` from MiKTeX (poppler 24.04), so it needs
nothing. **`pack.py` is not reproducible**: reportlab stamps a
`/CreationDate`, a `/ModDate` and a random `/ID` into each PnP PDF, so all
four rewrite on every run whether or not a card changed. Never read a PnP
diff as evidence of a content change — check the PNGs. `canvas.Canvas(path,
invariant=1)` in `gen.py`'s `write_pnp` would fix it; not done, because it
rewrites all four files and is Jon's call. Render to a scratch directory first and diff against `images/` before
copying anything out — that is how the stale backs below were caught. The same
`PATH` prefix is all `rules/build.py` needs; its docstring still recommends WSL
and no longer has to.

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

- **All 24 Exhibits print a Reward band; nineteen of them are COURTESIES
  and do nothing.** Asked for on 2026-11-02, after "shouldn't all the
  imposter exhibits have rewards". The answer to that as a mechanic is no -
  the five that pay are worth +7.8 points and are the reason REC is 3
  rather than 4, so a sixth is a balance change - but the complaint behind
  it was sound: nineteen cards read Target and Damage over an inch of white
  space and looked unfinished, and a Reward band on only five of them told
  everyone at the table which five mattered before a card was turned over.

  So the band is on all 24 and the other nineteen carry flavour.
  `build_nrj.EXHIBIT_COURTESY` holds them, `EXHIBIT_REWARD` still holds the
  five that pay, and the two tables may not overlap. NOTHING MECHANICAL
  MOVED: no Target, no Damage, no Reward text, and `simulation/` was not
  touched. The whole diff in the generator is one comment and one branch.

  THE RISK IS A PLAYER READING A COURTESY AS A RULE, and three things
  guard against it:

  - A real Reward is BOLD upright; a courtesy is italic, in the set's own
    flavour style (7.4pt, #6f675a, centred). Weight is the signal that
    survives distance - across a table you can see which Exhibit pays
    without being able to read it, which italics alone do not give you.
  - All five real Rewards open "When this Exhibit falls". No courtesy may
    contain that phrase.
  - No courtesy may NAME A THING THE GAME HAS. The first version of this
    entry said "none is imperative" and that was the wrong rule: Jon's
    final wording includes "Help yourself to anything that isn't
    smoking", which is imperative and plainly flavour, while "the next
    Exhibit you deploy has its Target reduced by 1" is a flat statement
    and plainly a rule. Mood is not the test. Having nothing in the line
    that can be acted on is - a brooch, a candlestick and a moth are not
    components. `build_nrj.COURTESY_FORBIDDEN` lists the words;
    `build_nrj.py` refuses to build on a hit and `check_app_sync.py`
    reads the same list, so it fails the check people actually run.
  - The rulebook says it twice: at setup, and under "What the Council lets
    slip".

  Sixteen of the nineteen were never Reward cards - they were Constraints,
  Aggravators and Reliefs, and the rework drops every Scenario clause. The
  other three (An Unwelcome Embrace, The Night Watchman's Account, Across
  the Chamber) WERE printed Rewards, of a kind this finale has no unit for.
  finale.py puts restoring them at +1.3 points, which is outside the
  one-point tolerance the four rungs hold to, so they get a courtesy too.
  If Jon ever wants them real, that +1.3 needs a compensating change
  somewhere, not just a rewording.

  While here: suite.js said the five Rewards were measured at +3.8 points.
  finale.py says +7.8 in two places and prints 50.5 against 42.7. The
  comment was stale and is corrected; nothing read it.

- **A card is 750x1050 at 300 DPI everywhere, and the per-game PnP pages
  used to be gridded on 714x1000.** Reported on 2026-11-02 as "NAP page 6,
  something is off", then as "the opportunity and setback cards are too
  large". The Opportunities and Setbacks were the correct size. The Tasks
  and the Final Exams were small, and the page grid followed them.

  `fit_tts` shrinks any sheet over TTS's 10000px ceiling. NAP's Tasks (26)
  and Final Exams (12) are the only two decks in the set that trip it: they
  are LANDSCAPE, so ten to a row is 10500px where ten portrait cards are
  7500. Their TTS cells came out 1000x714.

  That was supposed to be harmless, on the grounds gen.py recorded - "the
  PnP pages are built from the full-resolution card images, not from this".
  True of each deck's own `<deck>_PnP.pdf`, FALSE of the four files that
  actually ship: `pack.py` cuts its cards back out of the TTS sheets. So
  21 of NAP's 59 cards were 750x1050 in a 714x1000 grid. `paginate` strides
  by the first card's size and pastes each card at its own, so every
  full-size card landed 36px right and 50px low of its cell and overlapped
  its neighbour. NAP pages 3-7 were unusable on both sides. BAT, AoS and
  NRJ were never affected - no deck of theirs trips the ceiling.

  Four changes, because one of them alone would only have moved the fault:

  - `gen.tts_grid(n, card_px)` picks the widest grid up to 10 columns that
    TTS will still load, so Tasks are 9x3 and Final Exams 9x2 and NOTHING
    IS RESAMPLED. Those two decks now print at their rendered resolution
    for the first time.
  - The manifest records `card`, the cell size BEFORE fit_tts, and pack.py
    scales a shrunk deck back up to it. fit_tts stays as a backstop, so a
    future deck that fits no grid degrades in sharpness instead of
    breaking the page.
  - `paginate` refuses a page whose cards are not all one size. That is the
    invariant the stride has always assumed and never stated.
  - `build_catalog.grid()` reads cols/rows from the manifest `render_deck`
    wrote. It had been recomputing them from a hand-kept copy of gen.py's
    rule, which is exactly what went stale the moment the rule changed.

  A DECK'S GRID IS REGISTERED IN FOUR PLACES and only one of them is
  derived: `gen.tts_grid`, the manifest (written), `CARD_MANIFEST.txt` and
  `tts/decks.py` (both by hand). `check_app_sync.py` caught the two hand
  ones on the first run after the regrid, which is what it is for -
  `tts/build_mod.py` writes `w`/`h` straight into the saved object as
  NumWidth, so a stale 10 there mis-cuts every NAP face in Tabletop
  Simulator. `tts/NobulousSet.json` is gitignored and rebuilt from
  `decks.py`; it reproduces byte-for-byte, so regenerate rather than
  hand-editing NumWidth.

  Anyone with the mod loaded must re-import those two sheets: the image
  changed shape, not just content.

- **Every header in the set is one depth, `gen.HDR_H_MM` = 11.86mm, and
  every title is sized by MEASUREMENT rather than by counting characters.**
  Asked for in two steps on 2026-11-02: first make the colour band the same
  height on every card, nudging font sizes if that is what it takes; then
  make the titles the count had been over-shrinking bigger too. The band
  used to follow the title's size - 135px at 11pt, 127px at 9.2, ~123px at
  8.2 - so a row of face-up cards stepped up and down.

  The depth is derived, not chosen: top padding + ONE line at the largest
  title size + the subtitle gap + the subtitle + bottom padding. None of
  those terms depends on the card's width, so portrait and landscape come
  out to the same number. A title below its style's top rung leaves a
  little more clear band under its subtitle instead of making the card a
  different shape.

  **It has to be the DEEPEST style's one-line header, and the first
  version got that wrong.** `min-height` is a floor, not a ceiling -
  WeasyPrint grows a header whose content does not fit. `build_aos.py`
  renders with its own `BIG` stylesheet, which sets `.hdr .t` to 11.6pt
  and `.hdr .s` to 6.8pt (the `.long` and `.xlong` rules still win on
  specificity, so only AoS's TOP rung moves). So AoS's short-titled cards
  pushed their own headers out to 11.86mm and that family shipped three
  pixels deeper than the rest of the set - the exact unevenness the
  constant exists to remove. It was reported as verified because the
  verification checked only what `hdr_fit` EMITS, which was the same
  string on all 240 cards.

  `gen.HDR_STYLES` now records what each family really prints, and
  `HDR_H_MM` is the max over it:

  | style | top rung | subtitle | extra side padding | printed by |
  |---|---|---|---|---|
  | `''` | 11.0pt | 6.4pt | - | everything else |
  | `'aos'` | 11.6pt | 6.8pt | - | every deck `build_aos.py` renders |
  | `'dot'` | 11.0pt | 6.4pt | 7.6mm | BAT Tyrant Attacks |

  The `'dot'` entry is the other thing a title can be measured wrong
  against: a dotted card sets `padding-right:10mm` on its header to clear
  the colour dot, leaving the title 7.6mm less room than `HDR_PAD` says.
  **If you override header sizes or padding in a build script, add a style
  here.** `build_catalog.py` publishes each deck's choice so
  `check_app_sync.py` can measure a title the way the card really sets it;
  the lab ignores the field.

  Title size was being picked by CHARACTER COUNT, in five copies of the
  same expression, and a count is the wrong instrument in both directions.
  It cannot know that "Undocumented Dependencies" sets wider than
  "Emergency Specimen Handling" despite being three characters shorter, so
  three titles printed at a size they did not fit. And it cannot know that
  a landscape card is 88.9mm wide where a portrait one is 63.5, so it also
  shrank titles with room to spare. `gen.title_cls` replaces all five and
  simply takes the largest rung the title fits on.

  **57 card faces got a bigger title** (44 of them 9.2 -> 11.0, ten AoS
  faces 9.2 -> 11.6, three landscape faces 8.2 -> 11.0: `Following in
  Nobulous' Footsteps`). **Three titles got smaller**, 9.2 -> 8.2:
  Undocumented Dependencies, Independent Performance Trial, The Night
  Watchman's Account - those are the three that were clipping. Nothing
  else moved.

  **Sizing by measurement cost the safety margin its justification, so
  the margin was measured too.** `TITLE_SAFETY` was 0.98 because the set
  happened to have an empty band between 96.1% and 99.86% of the line, so
  anything inside it caught the one title that wrapped and touched nothing
  else. Measured titles sit wherever they fit, which fills that band - two
  now land at 97.1% and 97.2%. So every multi-word title in the set was
  laid out by WeasyPrint itself in a box of known width in mm, narrowing
  until it wrapped: the narrowest box a title survives IS Pango's width
  for it. **Pango needs at most 1.014x PIL's estimate** (`Rapid Approach`,
  `Maintain Balance`, `Climb an Incline`, all at 11.6pt), so 0.98 is safe
  with about 0.6% in hand. `gen.TITLE_PANGO_RATIO` records it and
  `check_app_sync.py` holds the margin against it.

  Two traps if you re-measure that. One-word titles cannot wrap at any
  width, so including them makes the disagreement look like an 18% spread.
  And reading widths out of WeasyPrint's box tree gives numbers ~12% under
  what the shipped art plainly shows - ask whether the title WRAPPED, not
  how wide it is.

  An earlier count of "82 titles" was wrong and worth knowing why: it came
  from walking `catalog.json`, and 26 of those were NAP Assignments, which
  have no `.hdr` band at all - their name is set vertically down a spine
  at its own computed size. Count what the BUILD does, by wrapping
  `gen.title_cls` and recording its real calls, not what the catalog
  lists.

  The AoS Element mats hand-roll their header outside the normal helper
  and have to be given the depth and the style explicitly, or they are the
  one odd card in the set. Note how: as a `%s` FORMAT ARGUMENT, not by `+`
  concatenation - `%` binds tighter than `+`, so a `+` there applies the
  format to the last fragment alone and the accent colour lands on `%d`.

  Verified three ways, none of them by eye:

  - From the generator: all 240 titles emit `min-height:11.86mm`, none
    needs a second line, and the sizes in use are 11.6pt x35, 11.0pt x180,
    9.2pt x22, 8.2pt x3. `check_app_sync.py` asserts the first two, plus
    that every deck names a style `gen.py` defines.
  - Against the old art, for overflow: raising `HDR_H_MM` starts every
    non-AoS body 5px lower, so the question is whether any card had less
    than 5px of slack in its `.spacer`. One number per card face - the
    lowest row holding ink - compared old render to new, across 309 faces.
    One moved: `BAT_BuffHP`, whose track layout has no spacer, by 4px, and
    it still clears the bottom of the face by 31px.
  - By re-render diff: 36 sheets changed, 16 unchanged (the 14 card backs
    carry no title; NAP Assignments and NRJ Imposter Tasks use the spine
    layout).

  Do not reach for a pixel clipping detector here. The one used earlier
  reports 62 false positives on this art - cards with a second colour
  strip under the header (SPECIMEN, UNAUTHORIZED) and the Element mats'
  tinted body - and a single-column probe stops at the first title glyph.
  That is four pixel heuristics that have lied about this. Ask the
  generator, not the image; where an image is the only witness, make it a
  DIFFERENTIAL test on one number, as the overflow check above is.

- **A card title wrapped, the header did not grow, and the subtitle was cut
  in half.** Reported 2026-11-02 as "text is being cut off at the top" on
  the Interference card **Undocumented Dependencies**, and it was real, on
  the printed card and not only on screen.

  `hdr_fit` exists for exactly this: WeasyPrint sizes the flex header from
  one line, so when a title wraps the body rides up and covers the
  subtitle, and `hdr_fit` reserves the height to stop it. It measures the
  title with **PIL**. WeasyPrint lays it out with **Pango**. The two agree
  to about a percent, and a percent is not enough: this title measured
  **99.86%** of the available width, `hdr_fit` returned no min-height, and
  Pango wrapped it anyway.

  Two corrections in `gen.py`. `title_lines` now subtracts `CARD_BORDER_MM`,
  because `.card` draws a 0.5pt border and `box-sizing: border-box` takes it
  out of the content width - correct, but on its own it still left the title
  fitting by 0.8px. The one that matters is `TITLE_SAFETY = 0.98`: a title
  within 2% of the edge is treated as wrapping.

  **2% is not a guess.** Measured across all 240 card titles in the set,
  two already wrap and are reserved (`The Night Watchman's Account` 104.7%,
  `Independent Performance Trial` 104.7%), this one sat at 99.86%, and the
  next is `Methodological Optimization` at **96.1%**. The band between 96.1
  and 99.86 is empty, so any margin from 1% to 4% catches this card and no
  other. Re-rendering all four families confirmed it: **1 sheet changed out
  of 52**, and the other 51 came back byte-identical.

  `check_app_sync.py` now fails if a new card name lands in the 1% below
  the cut, where neither the measurement nor the margin can be trusted.
  It also prints the margin - today 1.9%. If it ever reports a title at
  97.5%, rename the card or widen `TITLE_SAFETY` and re-render; do not
  assume it is fine because it rendered correctly once.

  **How NOT to look for this.** Three pixel detectors were written before
  one worked, and the first two produced confident, entirely wrong lists of
  clipped cards - a centre-column probe stops at the first letter of the
  title, and a row-composition probe stops where a long title covers half
  the row. The detector that worked finds the band's foot as the first row
  that is mostly body cream and the subtitle's foot by ink coverage. But
  the answer that actually settled it came from the renderer: change the
  measurement, re-render everything, and diff. The sheets that move ARE the
  affected cards. Reach for that first.

- **The card preview cropped a 300 DPI card by a 200 DPI margin, and the
  geometry now has one owner.** Found 2026-11-02 while chasing the clipped
  subtitle above - a second, unrelated fault on the same screen, and the
  reason that one looked worse than it was. The preview clipped nothing: it
  was
  cropping away the card's entire 2mm cream margin, its printed border and
  its rounded corner, which puts the title hard against the frame and reads
  exactly like clipped text.

  `suite.js` carried `CELL_LONG=700, CELL_SHORT=500, GUTTER=15` with a
  comment stating them as fact. Those are 200 DPI pixels. The art moved to
  300 DPI on 2026-10-30 and nothing caught it, because 15/500 and 23.6/750
  are near enough the same ratio that the preview stayed *almost* right -
  it cropped 22.5px of a 23.6px margin instead of breaking outright. A
  wrong number that is 95% right survives any amount of looking.

  The geometry is **published** now, not assumed. `gen.py` owns `PORTRAIT`,
  `LANDSCAPE`, `DPI` and the new `CARD_INSET_MM`, and its own CSS reads the
  last of those rather than repeating `2.0mm`. `build_catalog.py` writes
  each deck's real `cell` and `gutter` into `catalog.json`, reading the cell
  from the finished sheet. The lab reads both and shows the WHOLE cell, so a
  card looks like a card. `check_app_sync.py` holds the three together.

  **It had to be published, because it was never one number.** `fit_tts`
  shrinks any sheet that would pass Tabletop Simulator's ceiling, so
  `NAP_Tasks` is 10000x2142 - cells of 1000x714 with a 22px gutter - where
  every other portrait deck is 750x1050 with 24. No single constant could
  have been right for both, and the old code used 700x500 for it.

  `build_catalog.py` had also been keeping its own copy of `PORTRAIT` and
  `LANDSCAPE` to stub `gen` with; it reads them out of `gen.py`'s source
  now. Re-rendering NRJ after the CSS change gave 9 of 9 sheets
  byte-identical, so the change is inert on the art.

- **`serve.py` was single-threaded, and wedged.** Found 2026-11-02 when the
  lab stopped answering on port 8000: the port was still LISTENING and every
  request timed out, which looks like the machine refusing the lab rather
  than the server being stuck. The first cut used `socketserver.TCPServer`,
  which handles one request at a time - and `python -m http.server`, the
  thing serve.py was written to replace, has used `ThreadingHTTPServer`
  since Python 3.7. So the replacement was strictly worse at exactly what
  the lab does: a browser opens six connections at once for a page pulling
  fifty card sheets, and one stuck or idle-held connection starves the rest.
  It subclasses `ThreadingHTTPServer` now, with `daemon_threads` so Ctrl+C
  does not wait on a half-read connection. If it ever stops answering again,
  check for a LISTENING socket with no accept behind it before assuming the
  port is taken.

- **The dependencies are written down, in `requirements.txt`.** There was no
  manifest of any kind. HANDOFF section 8 listed four packages in prose for
  the card generator only and missed `beautifulsoup4`, which
  `rules/make_editable.py` imports. The file says which script needs which,
  and spells out the two that pip cannot install - WeasyPrint's GTK
  libraries, found through `PATH` and not through Python, and `pdftoppm`.
  Both fail without naming themselves: the first dies with `OSError: cannot
  load library 'libgobject-2.0-0'`, which reads as a broken install rather
  than a missing `PATH` entry, and it is what `check_cards.py` does when run
  exactly as AGENTS.md documented it.

  Two other undocumented orderings, both now written down: `build_nap.py`
  must run before `build_nrj.py` into a fresh output directory, because NRJ's
  Imposter Tasks and Devious Opportunities print NAP's Assignment back; and
  `SETUP.md` claimed re-running a build script "rewrites the sheet in
  `images/` and the PnP pages together", which has not been true since
  `deploy.py` became the only thing that promotes `out/`. That false
  sentence is the documented version of the drift recorded further down.

- **`Start_Playtest.bat` served the lab with `python -m http.server`.** So
  did `README.md` and `playtest/README.md`, after `AGENTS.md` had been
  changed to forbid it. The launcher is the one a playtester double-clicks,
  so every playtester was getting the cache trap that hid the Imposter
  picker on 2026-10-31. All three now run `playtest/serve.py`.

- **`generator/out/python_deps` is 48 MB of vendored packages that nothing
  references.** Pillow, fontTools, cffi, pydyf, pyphen, cssselect2 and more,
  sitting inside the gitignored `out/`, so it has never been committed and a
  clone has never had it. Nothing puts it on `sys.path`. It is almost
  certainly the leftovers of an attempt to run the generator without a real
  environment. Left alone - deleting 48 MB that might be load-bearing on
  some other machine is Jon's call, not a cleanup to do in passing.

- **Five Imposters, ten abilities, and the two rules they obey.** Added
  2026-10-31. You choose one Imposter card and one of its two sides at setup;
  all five print the finale's own 5 HP / 2 STR / 3 REC, because the house rule
  across the set is that heroes differ only in ability text. Every side was
  measured at Easy and at a handicapped rung and had to pass BOTH a level test
  (0.8 to 4.3 points, so the choice is how you play rather than how hard it is)
  and a uniformity test (worth about the same at both, so no side becomes the
  only pick at Nobulous). Seven designs were cut on measurement, and the
  reasons generalise: nothing may touch STR, REC, the width of the attention
  window or the wheel's PHASE; nothing may hand dice back every session,
  because nine sessions of one die IS the Nobulous handicap; and nothing may be
  paid in Damage or Health, because a sensible pace never spends either -
  soaking a Damage a session and moving successes between Exhibits both
  measured exactly +0.0. The full table and every rejected design is in
  `simulation/proto/imposters.py`. The ladder now runs 2-4 points hot with an
  Imposter chosen and was deliberately NOT re-pegged, since Easy is already at
  zero dice exhausted and pegging it would cost the meaning of "Easy".

- **The lab plays all ten Imposter sides.** Added 2026-10-31; before that the
  card browser listed the deck and the finale lab had no picker at all. Pick an
  Imposter beside the difficulty and Build - it is a setup decision, so it takes
  effect on Build and says so if you change it mid-Scenario. Four points worth
  knowing before you touch `renderNRJImposter` or `nrjUseImposter`:

  1. **Three sides are ARMED rather than spent by their button**, because they
     need a target chosen afterwards. Precedent and Early Admittance are spent
     inside `nrjApply`, where the barred die actually goes through, so an Apply
     with nothing barred in it leaves them armed and unspent. Sleight of Hand
     and Requisition are spent when you tap the die.
  2. **Requisition has to be tapped and cannot be "selected"**, because an
     exhausted die is not selectable in the dice row outside a recovery. That
     was a real bug in the first cut and the browser caught it.
  3. **One counter serves all ten** - `impCount` and `impSession` - since you
     only ever hold one side.
  4. **`nrjAllowed(s)` stays pure.** Double Doors widens the CURRENT session
     only, through `nrjAllowedNow()`, because the Rewards look ahead with
     `nrjAllowed(n.session + 1)` when they pay out after a session ends.

  `NRJ_IMPOSTERS` carries build_nrj.py's `when` and `text` strings verbatim -
  they are rendered as innerHTML, so the `<i>` tags and entities stay - and
  `check_app_sync.py` compares all ten sides to the printed cards field for
  field. Change a card and the check tells you which field drifted.

- **The Candidates answer nothing, and there is now exactly one measured way
  to change that, and it was MEASURED AND DROPPED on 2026-10-31.** The
  Research Pool is the 18 Tier III
  cards each game lays out. The 7 you claimed are retained and take 2 off an
  Exhibit's Target; the 11 you did not are Candidates, and since the Exhibits
  were reprinted on 2026-10-30 - which removed Rope Burns' random discard, the
  last card text that touched them - they do nothing at all.

  A global job was designed, priced and rejected on 2026-10-31, then
  re-measured the same day, and the rejection turned out to be **half wrong**.
  Two corrections:

  1. **Those were not six prices. They were four use-caps.** A claiming
     campaign carries 11 Candidates, so a job costing 4 can be done twice and
     one costing 6 once, whatever the rules say. The price never bound - the
     POOL SIZE did. With the cap as its own dial, 3-a-use twice, 4-a-use
     twice, 4-a-use three times and 5-a-use three times all return the SAME
     four numbers, because on 11 Candidates all four ARE two uses.
  2. **A Target is a die by another name**, so dice and Targets are one
     currency, and it is the one the difficulty ladder itself spends. That,
     and not "no job can be uniform", is the whole of the non-uniformity.

  Priced in the **attention wheel** - the one scarcity the ladder never
  touches, since nine sessions of Yellow-Green-Blue-Purple-Red are identical
  at Easy and at Nobulous - the same job goes flat:

  | job | Easy | r11 | r13 | r16 | spread |
  | --- | --- | --- | --- | --- | --- |
  | 4 Candidates a die (the best rejected) | +1.1 | +8.4 | +9.3 | +8.7 | 8.2 |
  | **4 Candidates, apply 1 forbidden colour** | **+2.5** | **+3.2** | **+2.9** | **+3.2** | **0.7** |

  A spread of 0.7 across a forty-point ladder is flatter than any card in the
  set. It is flat because the job needs an AVAILABLE DIE OF A FORBIDDEN
  COLOUR: the handicap removes available dice and so limits how often the job
  can be taken, while the wheel's restriction is the same at every rung, and
  the two cancel. The cap is load-bearing - uncapped it is as bad as the dice
  job - and at 4 Candidates the pool supplies the cap without a printed
  clause (11 cards affords it twice).

  What shipping it would cost, measured: **not the ladder** (the job and the
  Imposters compete for the same spare wrong-colour die, so they do not stack
  - with the strongest Imposter the rungs read 55.8 / 39.6 / 32.0 / 20.2
  against today's 55.1 / 41.0 / 32.2 / 19.6, so Easy moves +0.7 and Standard
  and Hard move TOWARDS aim); **not the policy** (`pace: clock` still wins);
  **not the claim decision** (claiming is worth 42 points, not 6 - a campaign
  that claims nothing reads 8.4% at Easy - and the gap widens). What it does
  cost is **Precedent**: the Archivist's side B is the same ability for free,
  so if the job ships that side needs replacing.

  Also recorded there: a Candidate job **cannot be a catch-up mechanic**, which
  was the original rationale. The job pays a full claimer +5.3 and a
  claim-nothing campaign +0.6, because 15 Exhibits at undiminished Targets are
  lost whatever you are holding.

  **Aim it BACKWARD and it costs no Imposter its job.** At "any color" the job
  degrades the whole attention lane - Precedent and both Usher sides go
  negative at the handicapped rungs, because all of them compete for the same
  spare wrong-color die. But nobody occupies backward: Precedent takes any
  color, Early Admittance one step forward, Double Doors a third color
  forward. Aimed at the color the attention has just LEFT, the job reads
  54.3 / 33.4 / 24.8 / 14.3 - worth +2.6 to +3.8, spread 1.1 - and Precedent
  keeps its job, so no Imposter side needs replacing.

  Three replacement Archivist sides were drafted and measured before that was
  found, and all three failed: Filed Twice (split a retained card into two 1s)
  is +5.5 at Easy and -0.8 at Nobulous even capped at one use, because the
  pool's REACH is bounded by its card count rather than its total value, so
  splitting buys tempo and tempo is what Easy already has; Certified Copy
  scales because it adds Target reduction, which is dice by another name; and
  Duplicate Filed is worth +7.5 to +11.3, three times the band.

  **And then it failed on the rungs the set actually prints, which is what
  closed the question.** Every number above was measured on the prototype's
  own rungs - Easy / r11 / r13 / r16 - where the backward job reads spread 1.1
  and looks like the one job that works. The set does not print r11, r13 or
  r16. On Easy / Standard / Hard / Nobulous, across all ten Imposter sides
  (`python candidates.py shipped`), the job is worth **+2.65 at Easy and -0.15
  at Nobulous**. It is INVERSE-SCALING on the shipped ladder - the same fault
  as the dice-priced jobs with the sign flipped, and the one thing the whole
  investigation existed to avoid. The flatness was an artifact of the rungs.

  The band settles it. The Easy row is the hot end of the matrix:

  | | hottest Easy cell | Easy cells outside the 47-57% band |
  | --- | --- | --- |
  | no job | 55.1% (Double Doors) | **0 of 11** |
  | with the job | 58.2% (Standing Order) | **3 of 11** |

  Early Admittance, Requisition and Standing Order all leave the band at Easy
  once the job is in, and every one of the eleven is inside it today. The
  no-Imposter ladder reads 50.6 / 39.0 / 30.6 / 19.4 against aims of
  50 / 40 / 30 / 20 - as close as it has ever been.

  **No price fixes it, because the price is not a dial.** Sweeping 4, 5, 6, 7
  and 8 Candidates returns exactly TWO distinct results, and "4 a use capped at
  one" is byte-identical to the 6/7/8 row: cost 4 or 5 is 54.3 / 40.6 / 33.3 /
  20.3 (affordable twice) and cost 6, 7 or 8 is 53.5 / 41.2 / 33.8 / 21.3
  (affordable once). One use is still worth +3.5, because a policy with one use
  spends it at the moment of maximum value. The only configuration left is
  zero.

  **And the reason is the reason it was chosen.** Backward was picked because
  it collides with no Imposter side - Precedent takes any colour, Early
  Admittance one step forward, Double Doors a third colour forward, and nobody
  goes back. But non-collision and non-stacking are the same property seen
  twice. The any-color job left the ladder alone only because it CANNIBALISED
  Precedent, the two fighting over one spare die. The backward job competes
  with nothing, so it ADDS to all ten sides - which is exactly why Easy reaches
  58.2%.

  Nothing has been changed in the cards or the rules, and nothing should be.
  `finale.py` is still the calibrated build with no Candidate job; the dials
  and the full tables are in `simulation/proto/candidates.py`
  (`python candidates.py currencies`, `python candidates.py shipped`) and
  `simulation/proto/imposters.py`. The Candidates stay a record of what you
  could not afford, and the Understudy stays the one Imposter who spends them.

  **If this is ever reopened**, measure on `LADDER` and against all ten sides
  from the start. A mechanic that looks flat on three handicapped rungs can be
  inverse across the four that ship, and a mechanic that collides with nothing
  stacks with everything.

- **The AoS lab could not finish an ordinary Program.** `completeProgram` in
  `playtest/dist/app.js` looked the card's prose up as
  `PROGRAM_FLAVOR[state.deck]`, but `state.deck` holds the DIFFICULTY
  (`Easy`/`Standard`/`Hard`/`Nobulous`) while `PROGRAM_FLAVOR` is keyed by deck
  (`Routine`/`Specialized`/`Unstable`/`Advanced`), so the lookup was always
  `undefined` and the handler threw every time. It is the one site missed when
  decks moved from one-deck-per-game to a per-Program `src`; the render path
  two hundred lines below already went through `programSource()`. Fixed to use
  the same accessor, and reproduced and re-verified in the browser - COMPLETED
  went 0 to 1 and the Catastrophic Failure took its HP. Found 2026-10-31 by
  auditing, not by playing: the crash leaves no visible trace except that the
  button does nothing.

- **NAP_SlotsFINF was registered as 4 cards and is 6.** The deck is 3 Time
  Slots + 3 FINF cards on a 6300x750 sheet, which is six 1050x750 cells, but
  `CARD_MANIFEST.txt` and `tts/decks.py` still said 4x1 from when FINF was one
  card. `tts/build_mod.py` writes `NumWidth` straight into the saved object, so
  TTS sliced the sheet into four 1575px columns: every face mis-cut and two
  cards never created. The lab was right throughout, because
  `build_catalog.py` counts the generator's own tables. Fixed, and
  `check_app_sync.py` now compares all five registries for all 30 decks so it
  cannot drift again.

- **Serve the lab with `playtest/serve.py`, not `python -m http.server`.**
  The plain server sends no Cache-Control at all, so the browser guesses, and
  it guesses badly for the one file that must never go stale: every asset
  carries a `?v=` token and may cache forever, but `index.html` is what NAMES
  those tokens, so a cached copy pins you to the old build however many times
  they are bumped. On 2026-10-31 a fresh tab was served `?v=dpi300`, several
  builds behind, and the Imposter picker simply was not in the page - no error,
  just an absent feature, which reads exactly like code that was never written.
  `serve.py` revalidates HTML and `catalog.json` and caches the rest for a year:

  ```bash
  python playtest/serve.py        # or: python playtest/serve.py 8080
  ```

  `index.html` also carries a no-cache meta now, but a meta cannot evict an
  entry cached before it existed - only the header can. If a browser is already
  holding a stale page, one hard reload (Ctrl+Shift+R) clears it.

- **The Time Slots were getting the FINF card back in TTS.** The same sheet,
  found the same day. `NAP_SlotsFINF` is 3 Time Slots + 3 FINF, and the two
  halves want different backs, but a TTS deck carries exactly one `BackURL`, so
  as one deck three of the six were always wrong. It is now two decks over one
  face sheet: `tts/decks.py` entries may name a `sheet` other than their key and
  a `first` offset into it, since TTS addresses a card as `deck_id * 100 + its
  index in the grid`. `w` and `h` stay the WHOLE grid in both, because NumWidth
  is what slices the image. The generator had been saying so all along - the
  `NAP_SlotsFINF_cards.json` manifest records `back` as a LIST of six when the
  cards do not share one, which is exactly the 3 + 3 the split is cut to.

- **`tts/build_mod.py` could not run anywhere but the machine it was written
  on.** It read `dice_objects.json` from a hardcoded `/home/claude/cards/` path
  though the file is checked in beside the script. Fixed 2026-10-31; the mod now
  builds here, 53 objects and 240 cards, with no missing images.

- **Nothing performed the copy into `images/` and `playtest/dist/assets/`, so
  it was done by hand.** That is the root cause of the drift recorded below, and
  it is now `generator/deploy.py`:

  ```bash
  cd generator
  python deploy.py              # promote out/, and report anything stale
  python deploy.py --prune      # also delete the stale files
  python deploy.py --release    # also cut release/tts and release/print
  ```

  It takes the list of sheets from the `*_cards.json` manifests rather than a
  hardcoded list, so a deck that is renamed, added or dropped is picked up
  without editing it - which is what makes `--prune` safe, and `--prune` is
  what the Imposter rename needed. It is idempotent: a second run reports
  nothing written.

  **The two releases differ only in resolution.** `release/print` is 300 DPI
  exactly as rendered. `release/tts` scales every sheet so neither side exceeds
  4096 px, which is all Tabletop Simulator will draw - a 10000 px `NAP_Tasks`
  sheet is 1000 px a card where TTS shows about 400.

  One trap if you change that scaling. **Resizing ALONE made the TTS folder
  BIGGER than the 300 DPI one** - 174% of it. The art is flat colour over large
  areas, which is why a 21-megapixel sheet is under 3 MB: PNG's filters predict
  a flat run almost perfectly, and LANCZOS puts an interpolated ramp on every
  edge and destroys that. Quantising back to a 256-colour palette restores the
  flat runs and costs nothing visible at 400 px a card. With it the folder is
  8.0 MB against 12.0 MB of sheets. `release/` is gitignored, since it is
  entirely derivable from `images/`, `print-and-play/` and `rules/`.

- **It is spelled "Imposter" everywhere, as of 2026-10-31.** One deck used to
  spell it "Impostor" - NAP's Tier II `NRJ_NAP_ImpostorTasks` - and the
  Exhibits deck was worse, titled "Impostor Scenarios" in the catalog while its
  own sheet was named `NRJ_ImposterScenarios_TTS.png`. Both spellings are good
  American English, which is why it survived so long; having both in one set is
  not. The rename touched the deck key, the sheet filenames, the manifest,
  `pack.py`, `tts/decks.py`, `catalog.json`, the rules, the simulation and the
  rendered card faces, and the NAP base card "Final Impostor Examination" with
  them.

  The table identifier did NOT simply become `IMPOSTER`: `build_nrj.py` already
  has `IMPOSTERS`, the five hero cards, and two names a letter apart for two
  unrelated decks is worse than the original fault. It is `IMPOSTER_TASKS`.

  What made the rename safe to do at all is that **rendering is byte
  reproducible** - re-rendering a family with nothing changed rewrites nothing
  in `generator/out/` - so the only diffs were the intended ones.

- **`images/` had drifted BEHIND `playtest/dist/assets/`, and both behind the
  generator.** Caught 2026-10-28 on the first full render this repo has had in
  one pass. Six `*_TTS_back.png` sheets were stale: the four AoS back grids,
  `BAT_Rats_TTS_back.png` and `NAP_Apprentices_TTS_back.png`. The AoS ones were
  badly stale — the current `build_aos.py` moves the flavour text to the foot of
  the card and spells the Catastrophic Failure consequence out in the footer
  (`OVER_FTR`, `STABLE_FTR`), and none of that had ever been rendered. Worse,
  `playtest/dist/assets/` already held the CORRECT AoS backs while `images/`
  held older ones, so the copy was ahead of the tree AGENTS.md calls generated
  output. All three trees are now in sync. **Re-render everything and diff, not
  just the deck you touched** — `e54fbcc` re-rendered only the Technicians deck
  after editing `build_aos.py`, which is how the other four AoS sheets were
  missed.

- **Two deployment traps in `playtest/dist/`, both of which hide a change
  rather than break it.** First, `index.html` loads the scripts with cache
  tokens — `app.js?v=...`, `suite.js?v=...` — so **editing a script without
  bumping its token ships stale code to every client that has the page
  cached.** Both tokens were bumped on 2026-10-28; bump them again on the next
  edit. Second, `load()` restores a saved game with
  `state = { ...freshState(), ...saved }`, which takes the saved `metrics`
  whole, so any counter added later is `undefined` in an old save and renders
  as "undefined" the moment it is incremented. `load()` now merges
  `freshMetrics()` under the saved metrics; keep that if you add a counter.

- **AoS ran low from Standard down, and this is now addressed.** It read
  35.0% at Standard and 18.0% at Nobulous against a 47-57% community band,
  the lowest of the three games, and was the only game the 2026-10-27 policy
  retune did not move at all — its policy was already the best available, so
  it was the game and not the player. On 2026-10-28 it gained a rule rather
  than a dial: **on a Catastrophic Failure you may exhaust 2 misses on failed
  Elements to negate the Health loss.** Standard at Tier III went 27.9% to
  54.2% and it fires on 68% of Catastrophic Failures. `MISSES_TO_NEGATE` in
  `aos.py` is the switch; set it to 0 to recover the rule as printed before
  that date. What is left is the SOLO axis — AoS reads 71.2% played without
  NRJ against 54.2% at Tier III, the widest such gap in the set. Those
  Tier III figures were measured against the finale that has since been
  replaced; the AoS game itself is unchanged, but any campaign-axis number
  that leans on the finale needs re-running against `finale.py`.
  The old entry here called out "AoS Unstable" at a 1-in-7 win rate; that
  was a whole-deck difficulty, and difficulty is now the Routine /
  Specialized / Unstable MIX, so the hard end is the Nobulous 2/3/3 mix.
  Still labelled experimental in the rulebook.
- **The Imposter finale was rebuilt on 2026-10-29, and this closes the
  finale items above.** The nine-attempt Suspicion scenario is gone;
  `rules/nrj.html`, `rules/NRJ_Campaign_Supplement.pdf` and the lab's NRJ
  tab now carry the design `proto/finale10.py` prototyped — a **Dossier** of
  15 **Exhibits**, the Council's **attention** rotating through the die
  colours, and a pace you set yourself against a nine-session clock.
  `simulation/finale.py` is the calibrated model and reads **53.1%** against
  a band whose mean is 53.0%; `simulation/finale.txt` is its report.
  `simulation/nrj.py` and `simulation/imposter.py` now describe rules that
  no longer ship and say so at the top.

  **No card was reprinted.** An Exhibit's Target is its printed Target minus
  5, and every domain of the Council Test library already prints
  8 8 8 9 9 9 10 10, so the deck supplies Targets of 3, 4 and 5 as dealt.
  `finale.py`'s `check_components()` asserts that against `build_nrj.py`, so
  the day someone edits a Scenario Target the model will say so.

  Three things are worth knowing before touching it:

  1. **The clock is not monotonic, and that is the design.** The attention
     window is two colours and the wheel is five, so the clock's LENGTH
     decides which colour the last session lands on. Nine sessions puts red
     in the middle and ends on purple; ten ends ON red and reads 17.8%,
     eight reads 24.4%. Changing the session count without checking the
     phase will look like a balance change and will not be one.
  2. **The attention window must stay at two colours.** One is unplayable
     (0.0%); three reads 90.6% AND inverts the recovery decision, so
     reading the wheel — worth +19.5 at two — stops paying at three. The
     window is the design, not a difficulty knob.
  3. **REC is still a cliff**: REC 3 reads 33.0% against REC 4's 53.1%, and
     STR 3 reads 88.5%. The finale did not escape the binomial knife edge
     `imposter.py` diagnosed; it escaped being out of band. The Dossier is
     the gentler dial, about 10 points an Exhibit, and 12 Exhibits at REC 2
     and 14 at REC 3 also measure in band if the economy ever needs moving.

  **Five of the printed Rewards were restored later the same day**, which
  cost a point of REC. Eight Council Tests print a Reward; the five that
  pay in a currency this finale still has are live again, worth +17.1
  points, and at REC 4 they tipped the economy over - burying evidence
  paid dice back fast enough that throwing every allowed die beat holding
  any back and the commit decision vanished. REC 3 put it back in band
  (49.4%) and gave that decision back. Treat the Rewards as the fourth
  point of recovery, earned rather than given, and do not raise REC
  without re-checking whether `commit: all` has taken over again.

  And the Dossier sits ONE EXHIBIT above a cliff: 12 / 13 / 14 / 15 / 16 /
  18 Exhibits read 79.3 / 74.0 / 65.1 / 49.0 / 21.1 / 0.2%. Adding a
  sixteenth is not a difficulty step.

  **A confidence mechanic was priced and not applied** -
  `simulation/proto/confidence.py`, with its table in `confidence.txt`.
  The question was whether burying evidence should pay in the one currency
  the finale is short of, the clock. It can: a buried Reward Exhibit
  discarding one Dossier card reads 55.9% at the shipped 15 Exhibits, in
  band with no re-pitch. Two things argue against taking it as it stands.
  It cannot be paid for with a bigger Dossier (18 Exhibits reads 4.2%, 21
  reads 0.1%) and REC cannot trim it (REC 2 is 20.2%), so it would ship
  pinned near the top of the band with nothing left to centre it with. And
  it taxes the attention dial: what reading the wheel is worth falls from
  9.2 to 5.6, about 40%, buying pacing pressure the finale already has at
  17.2. The confidence TRACK version, every third burial, reads 67.0% and
  is out of band outright. **DROPPED on Jon's call, 2026-10-31.** The
  prototype and its table stay as the record of what it would have cost;
  nothing in the shipped rules, cards or simulators refers to it.

  **RE-PITCHED 2026-10-30 AGAINST THE TIER III POOL, and this supersedes
  every finale figure above.** `research()` was still dealing the pool the
  Tier III rework replaced - a NAP card always worth 1, a BAT card worth 2
  only on a 1-in-4 Specimen, an AoS card worth 2 on a coin flip - so the
  model had been measuring against a pool that no longer existed. At the
  same time `nrj.html`'s standalone mode dealt 3 retained from each six,
  which no campaign can reach: AoS may only claim 2 Routines a game, so 8
  is the cap in practice and 9 reads 57.6%. Both fixed; `RETAIN` and
  `SPENT` are dials now, and `check_app_sync.py` compares the counts in
  `finale.py`, `suite.js` and `nrj.html` against each other.

  The pitch is **50.6%**, 6000 finales x 5 seeds, and it is still the best
  cell of the 224-cell policy grid - clock / horizon / adaptive / small,
  the cell the module models. The two corrections nearly cancel, which is
  why nothing downstream needed re-tuning. What could have broken did not:
  **the commit lever got STRONGER**, 12.3 points against 7.7, because a
  pool that lowers Targets makes committing exactly enough pay more. REC 3
  is confirmed and the reason is sharper - at REC 4 the commit decision
  INVERTS, throwing every allowed die winning by 10.0 and the best policy
  reaching 65.8%, out of band. The gap by REC is +19.1 / +11.0 / -10.0 /
  -11.6 for REC 2 / 3 / 4 / 5.

  Read the current numbers from `simulation/finale.txt`, whose section 6
  is the pool, not from the figures earlier in this bullet: those are
  from before the Rewards were restored (53.1%) and from before the
  re-pitch (49.4%).

  **THE DECK IS REPRINTED AS EXHIBITS, 2026-10-30.** Target and Damage are
  on the face, the five live Rewards are reworded to "When this Exhibit
  falls", and the other nineteen print nothing. The printed 8/9/10 could
  not simply be used as the Target - that measures 0.0%, because fifteen
  Exhibits at those values need about 135 successes against a nine-session
  budget of roughly 60. Three setup steps in `nrj.html` collapsed into one.
  The deck is called **Exhibits** in `pack.py`, `tts/decks.py`,
  `tts/lua.lua` and `CARD_MANIFEST.txt`; the deck KEY
  `NRJ_ImposterScenarios` is deliberately unchanged, because it names the
  sheet files deployed in `images/` and the lab.

  That rebuild also finally shipped the **12 BAT and AoS Tier III cards**
  whose claim-cost clause had been in `build_nrj.py` since 2026-10-29 and
  never rendered. Exactly three sheets changed and every other NRJ sheet
  came out byte-identical, so the card renderer IS reproducible here - the
  PnP non-reproducibility noted elsewhere is in `pack.py`'s assembly.

  **THE CARRYOVER IS RETAINED-OR-NOT.** The spent/unspent split is gone: it
  was a fact about a session weeks earlier that nothing on the table
  records. Every retained card takes 2 off a Target, and the pool is a
  count - NAP 3, BAT 2, AoS 2, which is the seven that reads 50%.

  **THE DIFFICULTY LADDER SHIPPED**, cut with named dice rather than a
  dial. Easy none, Standard 3/2/2/2, Hard 3/3/3/2, Nobulous 3/3/4/4
  (yellow/green/blue/purple), measuring 50.6 / 39.2 / 30.6 / 19.4. Two
  things to know before touching it:

  1. **The dice are NAMED, not chosen.** An earlier version let the player
     pick and the model picked worse than random at the hard end, because
     all four colours come four to a pool and "spend the commonest" broke
     the tie on purple. Do not reintroduce a player choice here.
  2. **The counts are SPREAD on purpose.** Whole colours collide with the
     attention wheel: 4 yellow + 4 green reads 28.7% against 38.4% for the
     same eight dice taken off the purple end, because the wheel opens on
     Yellow+Green. Weakest-first has a 14.6-point cliff between 6 and 8
     dice; spread, the largest step in the curve is 6.1. The wheel's phase
     is already chosen for where sessions 5 and 9 land, so the ladder has
     to stay independent of it.

  The rungs still reward play, which is why this dial was chosen over REC
  or Dossier size: recovery is worth +4.8 at Easy and +14.1 at Hard.
  Reprinting that deck as Exhibits — Target and Damage on the face, no
  Scenario clause — is the obvious follow-up, and it is a `build_nrj.py`
  and `pack.py` job, not a rules one.
- **Every difficulty dial in the set now needs re-pitching.** The policy
  retune of 2026-10-27 moved NAP from 42.1% to 76.0% at Standard, the
  finale from 50.9% to 61.6% and BAT from 46.5% to 53.2%, because the
  models had been playing three of the four games 6 to 34 points below
  their own best available policy. Every Credit goal, Health value and
  Target was calibrated against the old play.

  **Two of the four have now been re-pitched, both on 2026-10-28, and
  neither through a difficulty dial.** AoS gained the misses-negate rule
  above. NAP had every printed Target raised by 1 — the 26 Task Requests,
  the 6 Opportunities and the 12 Final Exam bases — which took Standard from
  76.0% to 49.8% solo and 51.4% at Tier III, with all six Apprentices in
  band on both axes and the per-Apprentice spread NARROWING, 10.8 to 8.4.
  The Task Demands were left alone: raising them widens that spread to about
  10 and drops three Apprentices out of band, whether all 26 rise or only
  the 14 whose Request-to-Demand gap the change collapsed to zero.
  The finale was re-pitched on 2026-10-29, by replacing it outright rather
  than by moving a dial — see the item above. BAT has not been.
- **NAP has little dice pressure, though the +1 pass helped.** Under the
  retuned policy 2% of its commit decisions happened at two dice or fewer,
  against 32% before, with a mean pool of 10.9 dice — it won 76% and never
  felt the pool. Since every printed Target rose by 1 it wins 49.8% and each
  check costs one more success, so the mean pool is 9.5, the per-game trough
  5.1, and 16% of games touch two dice or fewer at their worst point against
  8% before. Still the slackest in the set: `dicetension.py` puts BAT's
  battle at a mean of 4.6 and the finale at 5.0.
- **NAP Imposter Tasks print a recovery-colour dot as of 2026-10-31**:
  Anatomy P, Engineering B, Procedure Y, Theory G. They had none, and three
  printed NAP rules read "that Assignment's color dot" - Required Effort,
  completing or storing progress, and the colour the Primary queues - so
  every reference dangled. Worse, nothing agreed what the dot was: the
  model inherited the replaced Credit Task's (a different colour each
  game), the lab fell back to "P", and the card printed none, which is why
  NAP's Tier II and III calibration had been measured against dots that
  were never printed. Printing them is free: +-0.1 at every tier and the
  per-Apprentice spread unchanged, over 4000 games x 4 seeds. check_app_sync
  now compares the four dots across all three files.
- **Both of those rules questions are closed, and were already closed
  before 2026-10-31 - only the records were stale.** The Red die plays in
  the BAT battle as a trade: changelog item 3i reads RESOLVED, and
  `rules/bat.html` places it on a random Rat at setup, moves it to a
  non-active Rat each turn, and resolves it separately from personal dice.
  Slacker's passive was reworded in `b57eedd` to "Your Time Slot rows hold a
  maximum of 3 Assignments instead of 4" - a rule that exists, enforced by
  the lab as `napRowMax` and played by `nap.py` as `small_row`. Nothing in
  the set says "voluntarily draw" any more.
- **Card art is 300 DPI (750 × 1050 px) as of 2026-10-30**, raised from 200
  for print production. Everything that lays out a card measures in
  millimetres and `title_lines` scales both its text width and its wrap
  limit with `DPI`, so the bump changed resolution only - no card reflowed.
  Two NAP sheets then exceeded what Tabletop Simulator will load, so
  `gen.py` gained `fit_tts()`: any deck sheet over **10000 px** on a side is
  downscaled with the cells kept integral. The PnP pages are built from the
  full-resolution card images rather than from the sheet, so print is
  unaffected and only the two oversized TTS textures shrink.
- **`pack.py` IS reproducible now.** The drift was never in the card sheets;
  `write_pnp` used reportlab's default canvas, which stamps a `/CreationDate`
  and a fresh document ID per run. With `invariant=1` two packs of identical
  input produce byte-identical PDFs, verified for all four games.
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
