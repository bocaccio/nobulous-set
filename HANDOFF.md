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
images/           53 PNGs — card sheets and backs. The TTS mod points here.
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
| `--user NAME` | GitHub account; defaults to `bocaccio`, which is this repo's own remote |
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

1. **Every deck resolves.** Press a setup button first: the cards start
   inside the four boxes, so nothing is visible until one deals. A deck
   showing a grey question mark means its URL 404s. Check the exact filename
   against `REQUIRED_IMAGES.txt` — matching is case-sensitive.
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
   confirm the extra module cards are dealt. Then press **Pack up**: every
   card, including singles dealt out of a deck, must go back in its box and
   leave the table bare except the dice and the panel.
7. **Cycle Difficulty through all four.** Easy, Standard, Hard, Nobulous. Each
   setup message must name that level's own numbers — BAT's Specimens and
   Tyrant Health, NAP's Credit goal and Setbacks, AoS's Program mix, the
   finale's exhausted dice. A level that prints nothing is a missing table row.
8. **Read the Notebook.** Six tabs. They are the only rules a Workshop
   subscriber gets, so they are checked against `rules/*.html` by
   `check_app_sync.py` — see §6b.
9. **Count what a setup dealt** - or let `tts/test_setup.py` do it. The
   Upgrade deck is 16 + your difficulty's Specimens, the Assignment deck is
   26 + 6 + your Setbacks, the Program deck is exactly 8, and the Dossier is
   exactly 15. A count that is right at Standard and wrong at Nobulous is a
   difficulty table being read once and ignored once.

   ```bash
   cd tts && python test_setup.py   # 416 assertions over 64 setups
   ```

   It embeds a real Lua through `lupa`, stubs the slice of the TTS object
   API the setups use, and presses every setup button at all four
   difficulties and all four tiers. It cannot test the sequencer's frame
   delays, which is exactly what steps 1-8 above are for, and `lupa` bundles
   Lua 5.5 where TTS runs MoonSharp, a 5.2 dialect - so a clean run proves
   the card arithmetic, not that TTS will accept every construct.

---

## 6c. Four boxes, and setup that actually sets up (2026-11-09)

The mod used to spill all 31 decks into a parking row 68 units wide at
`z -22`, wrapping to a second row at `z -28` - which is past the front edge
of the table, so eleven decks shipped sitting on the floor. The setup
buttons then pushed those decks around and printed a paragraph telling the
player which cards to shuffle together by hand.

Now **every card starts in its game's box** - BAT, NAP, AoS and NRJ, with
the Imposter finale's two decks in the NRJ box because the finale is NRJ's,
not a fifth game - and a setup button takes out what the printed setup asks
for, performs it, and leaves the rest inside:

- **BAT** deals the four Lab Rats, shuffles the Experiments and the Tyrant
  Attacks, and shuffles the difficulty's Specimens into the 16 Upgrades.
- **NAP** builds and shuffles the Assignment deck, draws one FINF card and
  makes Morning the active Time Slot.
- **AoS** builds the 8-card Program deck from the difficulty's mix, shuffles
  the Limitations, sets the Advanced Programs aside and lays out the mats.
- **Imposter** deals the 15-card Dossier - 5 Knowledge, 5 Physical, 5
  Cover-Up - and puts the Research Pool out face-up.
- **The tier swaps happen too.** BAT Tier II removes 6 **ordinary**
  Upgrades by NAME rather than taking six off the top, and NAP Tier I is
  one base Setback out per Following Setback in, not four for three.

  That naming replaced a claim that did not survive its own test. The
  comment said the removal had to precede the Specimen mix or it would eat
  Specimens; the harness below could not tell the two orders apart, and was
  right not to - both cut from the top of the deck, and a merged-in
  Specimen lands at the bottom, so neither order could have eaten one. The
  guarantee rested on deck order that nothing enforced. Named, it holds
  whatever order the steps run in, and the harness asserts both halves: the
  Specimen count survives, and the six that left were ordinary.

**Two card-index tables are generated, never typed.** NAP Tier II has to
name individual cards - each Imposter Task replaces a Credit Task of the
same subject - and the finale deals by Exhibit domain. `build_mod.py` reads
both out of `generator/build_nap.py` and `generator/build_nrj.py` with an
AST walk and emits them into the Lua, so a reordered card table cannot
leave a stale index behind. The Exhibit reader refuses a domain that is not
one contiguous run rather than dealing the wrong cards quietly.

**The control panel now fits on the control panel.** `ControlPanel.png` is
1473x520 and the tile is `"Stretch": true`, so the tile's local space is
about `z +/-1` by `x +/-2.8`. The layout ran from `z -4.3` to `z -0.6` in
rows 0.9 apart: four of its five rows hung in the air off the top edge, and
the buttons overlapped each other. The row that repeated the title the tile
art already prints is gone, and `check_app_sync.py` now computes the tile's
extent from the PNG's own aspect ratio and fails any button outside it.

**The deck-label check had to be rewritten, not kept.** It matched
`findDeck('...')` call sites against `decks.py`; the setups call
`deckOut('...')` now, and an empty set is a subset of anything, so a rename
would have left it passing while matching nothing. It counts what it
matched, and a second check runs the other direction: every deck in a box
must be named by some setup, because a deck no button deals is cardboard a
player can only reach by opening a box and guessing.

**Twelve new checks plus one rewritten**, 298 to 310, and all thirteen are
proven to fail when the defect is put back. Four did not, first time round - three because the mutation was too
weak to violate the claim, and one because the claim itself was too weak -
and that is the whole reason for running the proof.

---

## 6b. The mod had drifted a whole design generation (FIXED 2026-11-09)

`tts/` carried no checks at all until this date, and every number in it was a
hand copy of a rulebook table. Four were wrong, two deck lookups matched
nothing, and the Notebook still taught a superseded game:

- **`lua.lua` dealt a flat-20-Health Tyrant** with per-difficulty Buff HP of
  4 / 5 / 6 and Specimens of 2 / 3 / 4. The dial has been *Specimens and the
  Tyrant's Health* — 5/9, 6/10, 7/12, 8/14 — since the Splices started
  carrying the fight, and the Buff HP card has been optional since.
- **Two `findDeck` labels matched nothing in `decks.py`**: `'Time Slots + FINF'`
  (the labels are `'Time Slots'` and `'FINF'`) and `'Impostor Tasks'` (one `s`).
  So NAP's Time Slots were never dealt and Tier II dealt nothing at all —
  silently, because `findDeck` returns nil and `park` ignores nil.
- **AoS picked one Program deck by difficulty.** Difficulty is a *mix* of all
  three: 3-3-2, 2-3-3, 1-3-4, 0-3-5. One deck is a game nothing describes.
- **Three difficulties where the set has four.** `btnDiff` cycled mod 3, and
  `btnAoS` indexed a 3-entry table, so Nobulous was unreachable and would have
  indexed nil.
- **The Imposter Scenario was the old finale**: 4+4+4 into 12, 4 HP, and a
  Suspicion row adding +1 Target. It is 5+5+5 of 24 into a 15-card Dossier,
  5 HP / 2 STR / 3 REC, nine sessions, and the Council's attention — which the
  panel now *derives* from the session count rather than tracking by hand.
- **The Notebook** had a half-finished BAT edit with a duplicated sentence, no
  AoS allocation floor, nothing about the Program Reward being the only healing
  in the game, and NAP's Credit goal as a flat 6. It has six tabs now; the
  finale got its own.

**Eleven checks hold it there**, and all eleven are proven to fail when the
defect is put back: the four Lua tables against `bat.DIFFICULTY`, `nap.LEVELS`,
`aos.LEVELS` and the finale table in `rules/nrj.html`; every `findDeck` label
against `decks.py`; the Notebook's dials derived from the models rather than
matched as prose; and a check that the superseded finale's vocabulary
(`Suspicion`, `Impostor`, `4 HP / 2 STR`) never comes back.

**The card faces were never the problem.** `images/` is `deploy.py` output and
was current; `REQUIRED_IMAGES.txt` reports `ok` on all 52 lines and is
byte-identical after the rebuild. What had rotted was everything the mod
*says*.

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
Upgrade stops the attack dead whatever the blow was worth and is spent for
it either way. It never takes partial damage and nothing spills past it to
Health (except Crushing Blow's 1, which is printed to bypass armor).

That is rules/bat.html's "Two kinds of armor" box, and the end of this
paragraph used to read "the Tyrant's Splices accumulate damage, a Rat's
Upgrades do not". **NEITHER KIND CHIPS.** That sentence was written before
the Tyrant battle was reworked - `b57eedd` is the checkpoint taken just
before it - and has been wrong ever since. The two armors are NOT mirror
images of each other, which is the thing to get right if this comes up
again (checked against rules/bat.html and playtest/dist/bat.js, which
agree, on 2026-11-03):

| | Tyrant Splice | Rat Upgrade |
|---|---|---|
| threshold | the blow must MEET its printed Value in this one attack, or it bounces off and the whole attack is wasted | none - it stops any blow dead, "whatever the blow was worth" |
| when it is lost | only to a blow that meets the Value | the moment it blocks |
| the excess | CARRIES ON - may break the next Splice, and what survives all five comes off Health, which does chip | NOTHING carries over; at most one Upgrade is lost |
| left part-damaged | never | never |

So "a blow of at least the Value removes it, and nothing partial carries"
is two different rules welded together: the threshold is the Splice's, the
no-carryover is the Rat's. Only the last row is true of both. Health is the
one thing in the battle that chips.

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

- **NAP'S SETBACK COUNTS CAME DOWN ONE AT EVERY RUNG on 2026-11-06: 4/4/5/6
  became 3/3/4/5.** The Credit goals did not move and no card was reprinted —
  the count has never been on a card. See `rules/RULES_CHANGELOG.txt` for the
  player-facing entry.

  This is the ladder catching up with a model fix, not a difficulty decision.
  The colour rule now applies to the **successes** rather than to the commit,
  which is what `rules/nap.html` prints, and the old model was about 5 points
  more generous than the cards at every rung. One Setback is worth about the
  same 5, so the published ladder is back where it was with the printed game
  underneath it — 20,000 games a cell:

  | level | no NRJ | Tier I | Tier II | Tier III |
  |---|---|---|---|---|
  | Easy (5 Cr, 3 Sb) | 56.3% <sub>was 55.5</sub> | 52.6% <sub>51.9</sub> | 42.9% <sub>41.7</sub> | 46.9% <sub>46.5</sub> |
  | **Standard (6 Cr, 3 Sb)** | **48.6%** <sub>48.8</sub> | 46.5% <sub>44.2</sub> | 36.4% <sub>36.1</sub> | 40.9% <sub>40.0</sub> |
  | Hard (7 Cr, 4 Sb) | 38.4% <sub>37.5</sub> | 35.1% <sub>33.1</sub> | 28.5% <sub>28.1</sub> | 33.2% <sub>31.8</sub> |
  | Nobulous (8 Cr, 5 Sb) | 29.4% <sub>29.7</sub> | 27.2% <sub>25.5</sub> | 22.6% <sub>22.1</sub> | 28.4% <sub>25.8</sub> |

  **Four sources carried the count and nothing compared them.** `nap.LEVELS`;
  the difficulty table *and* the setup step in `rules/nap.html`; the
  `NAP_SETBACK_COUNT` table in `playtest/dist/suite.js`; and the lab's own
  difficulty dropdown labels, which name it in prose. `check_app_sync.py` now
  compares all of them, numbers and prose — the same gap that let the
  End-of-Day burn sit unplayed in the model for weeks while the rules and the
  lab both played it. Verified in the browser: the lab deals 3/3/4/5.

  ### The three-way disagreement the re-peg uncovered — FIXED 2026-11-07

  `rules/nrj.html` said a tier sets the 6 base Setbacks **aside** and shuffles
  in exactly 3 Following ones, *"never both kinds together"*; the Following
  Setback card said *"These 4 replace the 3 base Setbacks"*; the lab played
  both. All three had the **3 hard-coded**, which matched only while every
  difficulty carried 3 Setbacks. `simulation/nap.py` mixed them instead — 3
  Following plus whatever the difficulty's count leaves over — and was the
  only owner that was right. The two readings **agree at Easy and Standard**,
  where the count is 3, and from the re-peg the printed one **inverted the
  tier** at the two hard rungs:

  | | solo | Tier I, printed reading | Tier I, as modelled |
  |---|---|---|---|
  | Hard | 38.6% | **40.1%** — easier than solo | 35.8% |
  | Nobulous | 30.3% | **34.7%** — easier than solo | 27.2% |

  Turning an overlay on must not make a rung easier, so the **card, the
  rulebook and the lab moved to the model**: one base Setback leaves for each
  Following Setback that arrives, the count the difficulty asks for is
  preserved, and **no published NAP figure changed**.
  `nap.FOLLOWING_REPLACE_ALL = True` reproduces the printed reading, and
  `check_app_sync.py` now holds the four owners together — nothing compared
  them before, which is the whole reason the 3 could sit in three places.

- **THE AUDIT OF 2026-11-06 WAS FIXED THE SAME DAY. Read this before the
  audit entry below it, which this supersedes in part.** `coverage.py` now
  reads **2 of 255 printed effects unmodelled, in 2 decks**, against 68 in 13
  when the audit was written — the third was Neural Response Screening, which
  turned out to be a card-text problem and was reworded on 2026-11-08 rather
  than modelled. The two that remain are argued at the bottom of this
  entry.

  ```bash
  cd simulation
  python coverage.py     # is the printed text implemented at all?
  python audit.py        # does it reach the table, and does it fire?
  ```

  **Both exit non-zero now.** `audit.py` had four `PROBLEM` sites and no exit
  code until 2026-11-08, so a run could print one and still pass: every
  PROBLEM now goes through one `problem()` helper and the file exits 1 if any
  fired. It is 0 today at 400, 600 and 1500 games. Its BAT Research Notes
  section also grew the `met` / `held` / `spent` columns the AoS Backdoor
  Routines got the same day — the old column read `g.claimed`, which is the
  set of **conditions that fired**, while `grant_note` declines past the
  claim cap and before a claim can be paid for, so "claimed 93%" was a *met*
  figure under the *held* name. What that exposed: the conditions fire in
  77–95% of games but you hold about 1.2 Notes, so the **cap decides which
  card you get** (`losses` 68% held because it fires late, `compatibility` 9%
  because it fires early); `resilience` is held in a quarter of games and
  **spent in none**, which is its printed timing working as priced
  (`RESILIENCE_TRIGGER = "short"` is the unrestricted card at 57.9% against
  47.9%); and Controlled Failure's condition is met in **0%**, named in
  `NOTE_DECLARED` so that any *other* card under the 5% floor is a PROBLEM
  rather than another line of prose. **Both figures in that declaration were
  wrong and are corrected** — it priced the card at −0.5 and the sacrifice
  as unaffordable, from one 2500-game cell. At 12,000 games a cell the card
  is worth **+0.9** granted free, every setting of its one dial reads zero
  (+0.0 / −0.6 / +0.9 / −0.2, and a *sighted* swap +0.3), and **one thrown
  Experiment is free**: 0/1/2/3/4 thrown reads 38.0 / 38.8 / 36.2 / 33.4 /
  25.4%, so +0.7 then −1.8, −4.6, −12.6. The claim is affordable and the
  reward is small, so what declines the card is the **claim cap of 2** —
  all six Notes are face up and a card worth +1 is the sixth pick of six
  against Acceptable Losses at +12.7. Reaching it would change nothing,
  which is why it stays declared. Two reward rewrites were priced and both
  miss the band: *recover the dice committed to a failed Experiment* +1.3,
  *a failed Experiment Splices nothing* +1.2. The band is the open
  question, and the band is Acceptable Losses.

  **THE AUDIT ITSELF WAS WRONG IN THREE PLACES**, and those corrections
  matter more than the count:

  1. **The 19 "unmodelled" Council Tests print nothing to model.** The audit
     read the dropped Scenario clauses in `build_nrj.SCEN` as 19 unmodelled
     effects and called the deck "the regression in the set". The shipping
     Exhibit face prints Target, Damage and a Reward band; only the five in
     `EXHIBIT_REWARD` print a rule in that band, and the other nineteen carry
     an italic courtesy that may not name a thing the game has. The deck
     reads 24 of 24, and `coverage.exhibit_faces()` asserts the partition
     rather than trusting a paragraph.
  2. **The "six left-behind dice restrictions" do not exist** on the shipping
     cards either, for the same reason. Nothing was abandoned by the rework;
     six clauses were deliberately dropped.
  3. **"Not one of the five Imposter names appears anywhere in
     `simulation/`"** was true of the shipping modules and misleading:
     `proto/imposters.py` is under `simulation/` and implements all ten
     sides, calibrated. The gap was real — the shipping simulator had no hero
     code — but it was a **port**, not a write.

  The same over-count ran through the NAP Setbacks: six cards printing one
  shared rule, both clauses of which are modelled, counted as six gaps. **A
  card with no printed effect is not an unmodelled effect.**

  ### What was fixed

  | | what | moved |
  |---|---|---|
  | 1 | **The five Imposters** ported from `proto/imposters.py` — all ten sides with their gates | `HERO = None` still reads **50.1 50.4 50.1 50.6 51.0**, the published pitch to the decimal, and the ladder is unmoved at 50.5 / 39.2 / 30.6 / 19.4 |
  | 2 | **The six Backdoor Routines** — claiming is EARNED off each card's printed condition, and costs the next Program Reward as all six print | AoS Tier II and III move several points; see below |
  | 3 | **Eleven of the twelve Final Exam restrictions**, which made Definitely Curriculum-Approved payable | earned in 690 games and spent in 390, against 153 and **0** before |
  | 4 | **The Devious coupons are named cards again** — the three off-card levers take a tuple of coupon names, not a boolean | `audit.py` reads 0% off-card against 27% |
  | 5 | **Redundant Organs** is paid for what it prints | fires in 12.6% of Tier II games, worth **0.0** points |

  On 5: `MOD_EFFECTS[4]` stays all-zero and is right to. `damage_tyrant`
  walks surviving Splices only and a blow under a card's Value bounces, so
  Health is reached only once every Splice is destroyed — a Spliced Redundant
  Organs cannot be alive when the Tyrant would fall. Unreachable there, not
  unwritten. `drop_mod()` is also keyed on the card now instead of its Value:
  Adrenal Gland and Redundant Organs both print Value 5, and `resolve_attack`
  did not check that the Upgrade it lost was a Modification at all.

  ### Three more of the same family, found while fixing those five

  Each is a printed effect with no implementation and no error — the
  Unexpected Resilience shape.

  6. **"Banish 1 Limitation from the game" did nothing.** One of the six
     Program Reward names, printed on one Program of each deck, with no
     branch in `Game.reward` — so three of the 24 Programs paid out silently
     nothing. `coverage.py` waved all three Program decks through at 8 of 8
     because its predicate was `len()` of the reward table. **A name in a
     table is not an implementation**, which is the exact lesson `fires` was
     written for, applied everywhere in that file except there.
  7. **The six Corrupted Limitations**, the deck the audit called the only
     one the model never drew. Five constrain the allocation, which this
     model builds explicitly, so they apply to the plan after allocation and
     before the roll; Deprecated Function is a scoring corruption.
     **The stand-in turned out to be close, and finding that out took a
     second look at the implementation.** Applied as written first — the
     constraint checked against a plan built *without* it, surplus dice
     simply deleted — the six read 27.4% at Standard against the stand-in's
     33.6%, which would have made them savage. That 3.5 points was a **model
     artefact**: a player allocating under "the first element must receive
     more dice than the last" arranges the same dice differently rather than
     throwing three away, so `corrupt_plan` now *moves* a shed die to any
     element that will legally take it and only leaves it uncommitted when
     none will. Rearranged, the printed cards read **31.7%** against 33.6% —
     1.9 points harsher, a well-calibrated replacement rather than a
     re-pitch. An allocation constraint applied *after* allocation is not
     the same card as one applied during it, and the difference ran the
     wrong way by twice the real effect.
  8. **Prodigy had no ability for the whole life of `nap.py`** — the clearest
     case in the set of a card that cannot be modelled by itself. It relaxes
     a rule the model did not have: `rules/nap.html` wants "a successful die
     matching its color dot, Red as wild, or two **successful** dice of the
     same other color", and `nap.py` enforced that on the commit and never
     asked whether those dice succeeded. So `ABILITIES` mapped Prodigy to
     `None` — and Prodigy is the default in `nap.run` and the Apprentice
     `audit.py` audits NAP with, so **the default Apprentice was the one with
     nothing to do.** With `COLOR_RULE_ON_SUCCESS` in, its ability is worth
     **+4.4 points**, the largest of the six.

  The four Imposter Tasks and four Following Setbacks now carry their printed
  effects too. `nap.FOLLOWING` was wrong three ways at once: a flat 1-die
  upkeep on all four when only Minor Laboratory Fire prints one, four
  interchangeable effects, and a dot drawn at random from PBGY when all four
  print one.

  ### What moved

  - **BAT** — the published grid is unchanged.
  - **NAP** — everything except the colour rule is **net neutral**. With
    `COLOR_RULE_ON_SUCCESS` off the grid reads 54.8 / 52.8 / 40.6 / 45.2 at
    Easy and 48.4 / 44.7 / 34.9 / 40.3 at Standard, against a published 54.9
    / 51.5 / 41.3 / 45.8 and 48.9 / 44.3 / 35.5 / 39.5 — every cell within
    about a point, with eleven exam restrictions, eight tier-deck effects,
    two Task effects and the coupon fix all in. That is the strongest
    evidence the implementations are faithful rather than lopsided.
  - **The colour rule costs about 5 points everywhere**, and it is the
    printed rule, so the published column was never a measurement of NAP as
    printed.
  - **AoS** — the Corrupted Limitations and the Backdoor claim cost both
    bite, and the Tier columns move several points.
  - **NRJ** — the finale pitch is unmoved to the decimal.

  ### The re-peg NAP needs — RAISED, NOT APPLIED

  `SETBACKS_IN_DECK` is the second half of NAP's difficulty dial, and taking
  one Setback off each rung restores the published solo column almost
  exactly. Already measured:

  | level | Cr / Sb now | reads | Cr / Sb | reads | published |
  |---|---|---|---|---|---|
  | Easy | 5 / 4 | 51.6% | 5 / 3 | 56.2% | 55.5% |
  | Standard | 6 / 4 | 43.8% | 6 / 3 | **48.8%** | 48.8% |
  | Hard | 7 / 5 | 34.4% | 7 / 4 | 38.1% | 37.5% |
  | Nobulous | 8 / 6 | 26.0% | 8 / 5 | 29.4% | 29.7% |

  The Setback count is printed in `rules/nap.html`, so it is a rules change
  and not a model one. It needs a decision before anything is edited.

  ### Also raised — two of the three are fixed, one is still a design call

  - **One Backdoor claim condition was effectively unreachable — FIXED ON
    THE CARD 2026-11-08.** Re-measured, the six fired in 68.2 / 65.7 / 61.5 /
    41.9 / 18.8 / **0.1%** of games — the old note in `aos.py` said "five of
    the six fire in 76-100%", which the required-colour dots and the Target+1
    cap had long since made false. Diagnostic Port wanted "no element
    over-allocated" and `allocate()` fills every element to Target + 1
    because the free die is worth having, so the condition was false by
    construction — and it was a **strict subset of Resource Fork**, so there
    was no game in which it was the card you claimed *for*. It now asks for
    **at least two** elements holding no more than their Target: 19.5 / 17.3
    / 15.9 / 14.0% up the ladder, beside Resource Fork's 19.6%, which
    co-fires on 77.7% of the Programs that meet it. The whole AoS grid came
    back **bit-identical**, because `BACKDOOR_WHEN = "value"` claims only the
    two recovery Routines — that is the reward-spread question below, not
    this one. `aos.DIAG_RESTRAINT = None` restores the printed condition, and
    `audit.py` now prints how often each condition is **met** beside how
    often the card is held, flagging any under 5%.
  - **AoS Tier III is not a recovery tier any more.** It read 46.6% at
    Standard against a Tier II of 33.6% — a +13.0 rebound, the shape the tier
    structure intends — because the model was granting two Routines free.
    Charged what the cards print, Tier III against Tier II reads never +0.0,
    always −0.5, and **+3.7** claiming only what beats a Program Reward
    (+3.6 on the 12,000-game grid). The whole Tier III column falls 10–12
    points and Tier II 1–1.9. Four of the six Routines are worth less than
    the Reward they cost, so the best line declines them. The six Routines
    are a *campaign* mechanic — the finale retains 2 AoS cards and each
    takes 2 off an Exhibit's Target — and
    a standalone AoS game now gets almost nothing from Tier III. Whether that
    is the intent is a design call, not a model one.
  - **Neural Response Screening's Crit clause was in the wrong idiom —
    REWORDED 2026-11-08.** It printed "at least 1 Crit must contribute to
    **complete this Assignment**"; a Final Exam has no completion step, it
    charges 1 Health per success short. Read as a gate it dealt the card's
    whole Target in **23%** of the sittings it got, **−4.6 points** on one
    card of twelve, which no other exam's restriction comes near; read as a
    commit rule it said nothing, because there is no way to commit *for* a
    Crit. It now prints **"Each Crit counts as 1 success instead of 2"** —
    the idiom the other two Crit cards already use, and the only one of the
    three covering every colour, deliberately: a single-colour clause on a
    Green-dot exam would often find no Green die committed and be the same
    dead clause again. A Crit contributes to **78%** of sittings, so it is
    engaged nearly every time the card is drawn. These are **the first NAP
    figures measured with all twelve restrictions** — the old column was the
    game with one exam unrestricted.
  - **And the card's base Target came down from 6 to 5, the same day**, which
    is the other half of that decision. The clause cost 1–3 points and left
    **three of six Apprentices below the 47% band floor** at Standard where
    all six had been inside it. A restriction has to be priced against the
    Target on the card that prints it, and both levers in `nap.LEVELS` are
    worth 4–6 points a step — one Setback off Standard reads 52.1%, one
    Credit off 53.0% — so either would have overshot and both are printed in
    `rules/nap.html`. At Target 5 the grid is **within 0.7 of the pre-clause
    column in all sixteen cells** (56.4 / 53.7 / 42.8 / 47.2 at Easy, 49.5 /
    47.0 / 37.3 / 41.7 at Standard) and all six Apprentices are back in band
    at Standard. It is the only Target-5 exam of the twelve.
    `EXAM_CRIT_VALUE = 2` reproduces the pre-clause column and
    `EXAM_CRIT_GATE` the printed gate.

  ### The two that remain, and neither is an oversight

  Both are printed rewards that pay in **information**, in models with no
  decision that information would change.

  - **Diagnostic Trial** (BAT) — "look at the next Experiment and **return it
    to the top**", so it cannot reorder anything, and the Experiment policy
    already commits the minimum expected to reach the Target. Nothing to hold
    back.
  - **Packet Sniffer** (AoS) — "look at the next Limitation before selecting
    a Program", and `play()` takes Programs off a shuffled queue because the
    rules deal them in order. No selection; and the dice a Limitation
    withholds already leave the pool before this model allocates.

  Modelling either would mean inventing a decision the game does not offer,
  which is worse than a declared gap. Both reasons are recorded at the code,
  and `coverage.py` fails if the claim around them goes stale. The third
  entry here until 2026-11-08 was Neural Response Screening, and it was a
  different kind of gap: not a reward paying in information but a clause in
  the wrong game's idiom, which is why it was answered on the card.

- **THE CARD AND EFFECT AUDIT, 2026-11-06 — read this first; the five items
  under it are new and the rest of this section predates them.** Every card
  in the set and every printed effect on it, checked against the model that
  publishes the figures: 255 faces in 30 decks. Two tools, answering
  different questions, and the first has to run first:

  ```bash
  cd simulation
  python coverage.py     # is the printed text implemented at all?
  python audit.py        # does it reach the table, and does it fire?
  ```

  `coverage.py` is new and holds **no prose claims** — every row carries a
  predicate over the live modules and the script exits non-zero when the
  code and the claim disagree. That is the whole point of it. Every coverage
  claim in this repository has gone stale at least once and **four were
  stale on the morning of the audit**: `bat.py` said the 20 Experiment
  effects were not implemented (19 are, in a table 30 lines below),
  `aos.py` said base Limitations were not modelled (all six are), `nrj.py`
  said none of the Scenario dice clauses was modelled (all seven are, 20
  lines down), and `nap.py` denied Apprentice abilities, Request effects
  and Opportunity effects. `audit.py` carried two of the same lies in its
  own report. All corrected, and all now derived rather than typed.

  **68 of 255 printed effects are not modelled, across 13 of the 30 decks.**
  Most is deliberate and documented. Five things are not:

  1. **The finale is the least-covered part of the set.** The five Imposters
     print **ten abilities** and not one of the five names appears anywhere
     in `simulation/`. `finale.py` has no Imposter card at all, so every
     finale figure — the **50.6% pitch included** — is measured with no hero
     ability whatever. On the same deck the shipping finale models 5 of the
     24 Council Tests. Most of the other 19 name Suspicion or a nine-attempt
     structure the rework removed — but **six do not**: the dice
     restrictions on An Old Injury, The Ceremonial Seal, Order of
     Precedence, An Open Window, The Long Session and The Darkened Corridor
     still mean what they print, and **`nrj.py` already implements all six**.
     The superseded model reads 23 of 24 on this deck and the shipping one
     reads 5. Six of that gap is working code left behind.

  2. **Four of the six Backdoor Routines never reach the table.**
     `BACKDOOR_CLAIMS` is 2 and the policy takes the first two of
     `BACKDOOR_ORDER` — which are exactly the only two worth anything.
     Priced against a 33.6% Tier III floor (claiming none), AoS cells
     averaged over the six Technicians:

     | Backdoor Routine | alone |
     |---|---|
     | Resource Fork | **+7.4** |
     | Garbage Collection | **+6.8** |
     | Root Access | +1.0 |
     | Packet Sniffer | +0.0 |
     | Privilege Escalation | −0.0 |
     | Diagnostic Port | −0.2 |

     Packet Sniffer is not implemented (a look at the next Limitation, and
     there is no Program-selection choice to inform — `aos.py` declares
     it). The other three **do** fire and are worth nothing. AoS Tier III
     is two cards and four pieces of decoration.

  3. **One Tier III card cannot pay out at all.** Definitely
     Curriculum-Approved prints *"ignore one exam's printed restriction"*.
     All twelve Final Exams print a restriction and `nap.EXAMS` carries
     `(subject, dot, Target)` only, so there is nothing to ignore. Earned in
     153 of 6000 Tier III games; its printed reward fired in **0** of them.

  4. **The third fungible-token defect, and it runs backwards.** AoS's
     Backdoor Routines and BAT's Research Notes each had six cards sharing
     one counter, and both were fixed by naming the cards. NAP's Devious
     Opportunities have the opposite fault: `devious_coupons` *is* a list of
     named payouts, but `ignore_setback()` and `move_setback()` pop
     whichever coupon is on the **end**, so a coupon earned by any of the
     six can be spent on an ability **none of them prints** — ignoring a
     Setback. **27% of every coupon earned** leaves the hand that way.
     Measured at **−0.7 points**, because the policy spends on a Setback a
     coupon worth more at an exam: this pool is not inflating Tier III, it
     is mis-spending it. `DEVIOUS_IGNORE_SETBACK = False` is the printed
     cards.

  5. **Redundant Organs is charged its cost and paid nothing.** Its drawback
     is modelled (`no_streak` — cannot be active on consecutive turns). Its
     benefit — *"the first time the holder would be knocked out, discard
     this card instead; the holder remains at 1 Health"* — is not, and the
     knockout in `resolve_attack` has no check for it. `MOD_EFFECTS[4]` is
     the only all-zero row in the three effect tables. The mirror image of
     Unexpected Resilience: there a reward was implemented and never fired,
     here a cost is charged for a reward never written.

  **BAT Tier I priced for the first time.** `FORCE_PROTOCOL` existed and had
  never been used, and it carried the `INTF_PICK` bug — it short-circuited
  the `rng.choice`, so a forced protocol ran on a shifted stream. Fixed the
  same way; the six cells now average to the drawn-at-random cell (50.2
  against 50.1), which is the check.

  | Experimental Protocol | win | vs solo 53.2% |
  |---|---|---|
  | Accelerated Trials | 53.3% | **+0.1** |
  | Questionable Methodology | 52.8% | −0.4 |
  | Cross-Contamination | 50.1% | −3.1 |
  | Independent Funding | 49.6% | −3.6 |
  | Questionable Procurement | 49.5% | −3.7 |
  | Shared Equipment Budget | 45.7% | **−7.5** |

  **Tier I is a penalty and two of the six are not one.** AoS Tier I has the
  same shape — six cards spanning 17.9 points against a 52.2% solo column,
  five of them within 7.4 points and Nobulous Was Here at −0.4. Raised, not
  fixed.

  **The six Corrupted Limitations are the only deck the model never draws.**
  There is no per-card index at all: Tier II applies one generic corruption
  (`CORRUPT_CHANCE = 0.50`, then withhold 2 dice of a random non-required
  colour) and each of the six prints a distinct *allocation* corruption
  instead. Six cards, one effect, six names, nothing for `audit.py` to
  count. AoS Tier II is the −7.2 column.

  **What is healthy**, since an audit that only lists faults is not a
  measurement: BAT's Experiments are 19 of 20, and its Upgrades, Specimens,
  Tyrant Attacks and all eight Lab Rat sides are complete. AoS's 32
  Programs, 6 base Limitations and 6 Technicians are complete. NAP's
  Assignments are 24 of 26, its Opportunities 6 of 6. All six Protocols, all
  six Interference cards and all six Research Notes fire, each drawn at the
  one-in-six rate it should be. **No printed card text changed in this audit
  and no published figure moved.**

- **AoS: SINGLE-ELEMENT SACRIFICE BEATS REWARD-SEEKING PLAY BY 10 TO 30
  POINTS, AND THE MODEL CANNOT PRICE IT PROPERLY.** Read this before the
  entry below it, which is narrower than it sounds.

  Measured 2026-11-03 (`aos.ALLOC_MODE = "sacrifice"`): write off the single
  most expensive element on purpose and spend its dice on the rest, and AoS
  goes 79.9 -> 88.9 at Easy, 70.8 -> 87.6 at Standard, 62.7 -> 84.6 at Hard,
  52.6 -> 82.3 at Nobulous. **The ladder collapses to 89/88/85/82** - the
  difficulty dial stops working. The printed rules bless it twice, in
  adjacent sentences: "An element may be left with no dice at all - it then
  simply fails" and "Failing exactly one element in a Program costs no
  Health." A bare element exhausts no dice either, so the sacrifice is free
  in Health AND in dice; the only price is the Program Reward.

  **So the calibrated allocation policy is far from optimal.** `allocate()`
  fills every element to Target + 1 left to right, and a thinking player
  beats it by 10 to 30 points. Every AoS number in RESULTS.txt was taken
  against that policy.

  **AND REQUIRED COLOURS ARE NOT IN THE MODEL AT ALL.** `grep -i required
  simulation/aos.py` returns nothing; `PROGRAM_TARGETS` holds bare integers
  per element and no colours. So the model is missing: the required-colour
  dot that must be funded on a named element before allocation, Red being
  unable to satisfy one, the 2 dots on Specialized and Advanced Programs
  against 1 on Routine and Unstable, and the whole "if you cannot supply a
  required colour, do not execute, lose 1 Health" branch. That is why the
  30-point figure above is an upper bound rather than a measurement of the
  printed game: in the real game 1 or 2 elements per Program CANNOT be left
  bare, and if the expensive one carries the dot the sacrifice is not free.

  **Do not re-pitch AoS until required colours are implemented.** The gap
  cuts both ways - it removes a constraint AND a failure mode - so the sign
  of the correction is not obvious, and no AoS figure can be called a
  measurement of the printed game until it is closed.

- **AoS: MASS DUMPING is shut, and not by the negate rule.** (Narrower than
  it reads - see the entry above: the SINGLE-element version is not shut.)
  A 2026-11-03 review worked out that failing Programs shortens the deck,
  an empty deck advances the game, and Advanced Programming is won by
  surviving three Programs rather than completing them - so dumping
  Programs looks like an efficient route. It is not: measured, it is
  strictly worse the more of it you do, and 99.4% of those games are dead of
  Health before Advanced Programming is reached at all.

  (The figures first written here - 0.2% against 70.8% honest - predate
  required colours, the allocation floor and the corruption exclusion, so
  this model cannot produce them any more. Re-measured 2026-11-04 at the mix
  then called Standard: 52.7% honest against 0.1% for dumping everything.
  The conclusion came out stronger; the numbers did not survive. The current
  ones live in the ALLOC_MODE block of `simulation/aos.py`, which is their
  one owner - do not restate them here.)

  **The brake is the Program Reward.** Health is only ever regained by a
  Reward, and a Reward requires ZERO failed elements - so failing on
  purpose forfeits the only healing in the game. Do not "fix" this by
  capping the Catastrophic Failure negate rule: measured at one per cycle
  it costs honest play 13.7 to 18.3 points, because honest play leans on
  that save about 3.2 times a game, and it costs the dumping line nothing.
  `aos.ALLOC_MODE` and `aos.NEGATES_PER_CYCLE` are the levers, both off,
  with the numbers beside them; RESULTS.txt has the table.

  **The wording was the one real defect, and it was FIXED 2026-11-03** in
  `e812c7e` — eighteen minutes after this paragraph was written calling it
  open, which is why the paragraph then sat wrong for five days. "Complete
  all three with Health remaining" was the loose phrase, because *complete*
  reads as *succeed at*; it is now "work through all three", Object of the
  game states the survival condition outright ("whether or not you completed
  them"), and a box says plainly why failing on purpose is no shortcut.
  Checked 2026-11-08: no owner anywhere — rulebooks, lab, generators — still
  carries the loose phrasing, and `aos.play()` ends `return self.hp > 0`
  after the third Advanced Program, which is what the rulebook now says.

  **Three `check_app_sync.py` checks now hold it there**, because this is
  the failure mode prose has and numbers do not: a sentence that was true
  when written, fixed by the next commit, and re-read five days later as a
  live defect. The checks hold the rulebook's survival clause against the
  model's win test and require the Program-Reward brake to stay printed. A
  "still open" note with no predicate under it is a note that will rot —
  this one rotted in under twenty minutes.

  **FOUR LEVERS WERE TRIED AGAINST IT AND NONE SHIPPED** (2026-11-03), so
  do not reach for a fifth before reading RESULTS.txt. Capping the negate
  rule costs honest play 14-18 points and the exploit nothing. Retiring the
  card on a Catastrophic Failure (`CF_SETS_ASIDE`) reads like a discount for
  dumpers but actually deletes the Stable->Overheated escalation, so it
  flattens the ladder AND makes dumping the best line at Standard. A
  declared abandon priced in Health (`ABANDON_MODE`) is a dead button,
  because failing costs the same 1 Health with a ~68% save attached.
  Replaying the failed card at once (`RETRY_IMMEDIATE`) is the best behaved
  of the four and still should not ship: it IMPROVES the dumping lines,
  because forcing a real retry drags a dumper back to playing properly. It
  confiscates a choice instead of punishing a strategy, and charges the
  honest player ~7 points for it.

  The pattern across all four: Health is the wrong currency to charge in,
  because the negate rule already makes a failure nearly free in Health.
  Dice are what AoS is short of. A dice-priced abandon is the one variant
  nobody has measured.

Not your job to fix, but worth knowing if Jon raises them:

- **NAVIGATION PROMPTS ARE SHARED NOW: `playtest/dist/steps.js`.** BAT had
  numbered step chips for the Tyrant battle and the other three screens had
  nothing. Asked for on 2026-11-03: give NAP, AoS and the Imposter Scenario
  the same thing.

  **A chip's button is a PROXY, not a copy.** A step names a CSS selector
  for a control that already exists on the page; the strip reads that
  control's label, is enabled exactly when it is, and a click on the chip
  clicks the real element. So the strip cannot drift from the game or
  disagree with it about what is legal - it does not decide anything, it
  reports. Add a step by naming a control, never by restating a rule. The
  thing that silently breaks a step is therefore RENAMING A CONTROL, and
  `check_app_sync.py` now holds every `ctrl:"#id"` against index.html.

  A step whose action belongs to a particular card (apply dice to an
  Assignment, assign dice to an Element) has no control to point at and
  passes `ready` instead; it renders as a label, because those buttons
  belong on the cards. `ready` ALSO forces a step live when its proxy is
  spent but the step is not finished - NAP's Choose the Primary, where
  Reveal is disabled but choosing is still step 1. Without that the strip
  walked past step 1 and lit "End time slot" while a choice was open.

  **"Now" is the first step you can act on, not a cursor.** A NAP Time Slot
  and an AoS Program are loops - roll, apply, roll again - so a marker
  marching 1-2-3-4 would be lying.

  Two things fell out of building it:

  - **Hidden SCREENS are not hidden panels.** A game renders at least once
    while its screen is off-stage, and judging availability by whether the
    control is visible made every AoS step read dead until something
    re-rendered. `steps.js` asks whether a control is shut away *within*
    its screen and ignores the screen itself.
  - **`napReveal` and `napAdvance` were never disabled** - they just
    returned early. A strip that mirrors `disabled` showed Reveal as
    available forever. `canRevealNAP()` is now the single owner of that
    question, used by both the handler and the button.

  The strip's CSS was `bat-*` and is now `.step`, `.step-row`, `.step-num`,
  `.step-stack`, `.step-dice`, shared by all four screens. BAT emits the
  new names and renders identically; verified by measuring `.step.now`
  against `--gold` rather than by reaching a battle.

- **An Assignment Task prints half of itself upside down, and in the choice
  panel there is now a button to turn it.** Asked for on 2026-11-03 after
  the Demand half of a card in "Choose the Primary" turned out to be
  unreadable. Nothing was wrong with the card: its data matches
  `build_nap.py`, the art the lab draws is pixel-identical to the
  generator's, and the sprite box is 357x255 against a cell of 1.400, so
  nothing is stretched. The Demand half is *meant* to be upside down - you
  turn the card on the table.

  A card sitting in a Time Slot already turned itself, through
  `#screen-nap .nap-demand{transform:rotate(180deg)}`, once it flipped to
  Demand. The choice panel had no equivalent, and that is the one place you
  have to read BOTH halves before committing. The button reuses the same
  class: the rotation is the class, the game state is not.

  **It is view state and must stay that way.** `napTurned` lives beside
  `revealNAP`, not in `state.nap`; the handler calls `renderNAP()` and
  deliberately not `save()`; and `revealNAP` resets it when a new pair is
  dealt, so a turn left on card A cannot carry into the next pair.
  `chooseNAP` is untouched and still takes the Request side.

  **Only Tasks are two-sided.** Opportunities, Setbacks and Final Exams are
  single-faced cards that happen to be landscape too - every NAP deck
  publishes a 1050x750 cell - so the control is hidden for them.

  Worth knowing why it mattered: **Recalibrate the Bone Saw has Demand 9,
  and upside down a 9 reads as a 6**, right next to its Request 5. That is a
  hazard on the printed card too.

- **`demandSide` MEANS TWO DIFFERENT THINGS, and only one of them is a
  rotation.** On a Task it means "flipped to the Demand half". On an
  Opportunity it means LAST CHANCE: `advanceNAP` sets `a.demandSide=true`
  on every unresolved card when a Time Slot ends, and an Opportunity that
  already had it is discarded - "Last chance expired: ... discarded". On a
  Setback it is bookkeeping with no face to show.

  `renderNAPSlots` used to rotate on the flag whatever the type, so an
  Opportunity in its second slot was drawn UPSIDE DOWN with no Demand half
  to show. Fixed on 2026-11-03 in two parts, because removing the rotation
  alone would have removed information:

  - the rotation is gated on `a.type==="t"`, since only a Task is printed
    with a second half;
  - an Opportunity on its last slot now says so, in the card's OWN PRINTED
    WORD - its footer reads "Last chance: if unresolved again, discard this
    Opportunity", so the label is "Last chance" and not an invention.

  If you ever need the flag to carry a fourth meaning, split it rather than
  adding another `a.type===` test: three readings of one boolean is already
  the reason this bug existed.

- **BODY TEXT, SUBHEADS, FOOTERS AND FLAVOUR NOW HAVE ONE OWNER - `gen.py`'s
  base stylesheet - and the sizes are the ones AoS had been keeping to
  itself.** Asked for on 2026-11-03: the main text, the flavour text and the
  below-the-line text on an AoS card are the right size and colour, so print
  them that way everywhere.

  `build_aos.py` renders through its own `BIG` stylesheet, and `BIG` had been
  quietly carrying four rules that are not AoS-specific at all. So three
  quarters of the set printed smaller than the quarter Jon was reading:

  | | BAT, NAP, NRJ printed | everybody now prints |
  |---|---|---|
  | `.txt` main text | 8.4pt | **9.4pt** |
  | `.sub` subhead | 6.6pt | **7.2pt** |
  | `.ftr` below the line | 6.2pt | **6.8pt** |
  | flavour | four different inline styles | **`.flavor` 7.1pt italic #6f675a** |

  Flavour was the worse half. There was no class outside AoS: `build_bat.C`,
  `build_nap.C`, `build_nrj.C`, `build_nrj.exhibit_body` and
  `build_nrj.impcard` each hand-rolled a `<div style=...>` at 8.6, 7.4, 7.6,
  7.4 and 7.4pt. **BAT's set no colour at all**, so the one family whose
  flavour was biggest also printed it in near-black body colour instead of
  grey - it read as a rule. All five now emit `class="flavor c"`.
  `.flavor` carries size, colour, italics and the margins; `.c` centres it,
  because three families centre their flavour and AoS sets it flush left.
  Where flavour sits MID-BODY rather than above the footer (the Exhibit
  courtesy under its Reward subhead, and the Imposter cards) the call still
  passes a `style="margin:..."` - the margin is that site's business, the
  size and colour are not.

  **`.txt.sm` deliberately did NOT scale with `.txt`.** It stayed at 7.4pt,
  so the gap to `.txt` went from 1.0pt to 2.0pt. Its two users are the NAP
  Credit note and the NRJ Exhibit Reward, and the Exhibit Reward is the line
  Jon had just signed off in bold - growing it would have re-opened a card
  that was finished. `check_app_sync.py` asserts the 7.4 so that scaling it
  later is a decision rather than a tidy-up.

  **Headers were not touched.** `HDR_STYLES['aos']` still carries AoS's
  11.6pt/6.8pt top rung, `HDR_H_MM` is unchanged, and no title moved - which
  is why none of this disturbed the title-measurement machinery above.

  Verified three ways, none by eye:

  - **AoS is byte-identical.** All of its sheets, and its PnP PDF, reproduce
    exactly. The family Jon picked as the reference did not move, which is
    the strongest statement available that the base now IS what AoS printed.
    24 sheets changed, every one of them BAT, NAP or NRJ.
  - **Nothing was clipped.** Bigger text makes bodies taller; a card with
    slack absorbs it in the `.spacer{flex:1}` and a card without has its
    footer pushed past the card edge, where `overflow:hidden` eats it. One
    number per face - rows between the lowest inked row and the card's
    bottom inner edge - old render against new, over all 287 faces. 212 did
    not move; 74 lost 1px; the six NRJ Corrupted Limitations lost 6px
    (0.51mm) because their footers now wrap to three lines, and still clear
    the foot band by 2.8mm. **No face went from having clearance to having
    none.** Exclude the NRJ foot band (`.nrjtag`) when redoing this or it
    is ink at clearance zero on every NRJ card in the set, and exclude empty
    grid cells or they report as clipped.
  - `check_app_sync.py` has a new section: no build script may set a size
    for `.txt`/`.sub`/`.ftr`/`.flavor` again, no card may hand-roll
    `font-style:italic`, and all four families must use the class.

- **THE LAB KEEPS ITS OWN COPY OF SOME FLAVOUR TEXT, and nothing used to
  notice when it went stale.** `playtest/dist/app.js` carries all 32 AoS
  programs with BOTH sides and the 6 Limitations; `bat_experiments.js`
  carries all 20 Experiments. They are hand-kept, not generated, and the
  lab does not read `aos.FLAVOR` or `build_bat.EXPERIMENTS` at all.

  This surfaced on 2026-11-02 when a 57-line flavour revision landed in
  the generators: 26 of those lines also existed in the lab and had to be
  walked across by hand. `check_app_sync.py` now holds all four tables
  against the generators, so the next revision fails the check instead of
  shipping two different jokes on the same card.

  The other decks do NOT duplicate flavour - BAT Upgrades and Specimens,
  the NRJ Imposters, the Exhibit courtesies and the Tyrant Attack and
  Modification lines exist only in the generators, and the lab shows them
  by displaying the card sprite. If you add a flavour field to the lab,
  add it to that check in the same commit.

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

  - A real Reward is BOLD upright `.txt.sm` at 7.4pt; a courtesy is
    italic, in the set's own flavour class (`.flavor c` - 7.1pt, #6f675a,
    centred; it was an inline 7.4pt before gen.py took it over on
    2026-11-03). Weight is the signal that
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
  `simulation/finale.py` is the calibrated model and `simulation/finale.txt`
  is its report, which is where to read the current figure rather than here.
  It read **53.1%** when this entry was written and reads **50.5%** since the
  five Reward cards were restored, against a band whose mean is 53%.
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

- **READ THE CAMPAIGN TIERS AS STEPS, NOT AS LEVELS.** This is the frame that
  found both of the 2026-11-06 changes, and it is worth keeping. At Standard,
  what each tier DOES to its own game reads:

  | | solo | → Tier I | → Tier II | → Tier III | III/solo |
  |---|---|---|---|---|---|
  | BAT *(morning)* | 53.2% | −3.1 | −11.4 | +4.7 | 81.6% |
  | BAT *(now, Notes modelled)* | 53.2% | −3.1 | −11.4 | **+9.2** | **90.0%** |
  | NAP *(before)* | 48.8% | −4.6 | −8.1 | +16.2 | **107.2%** |
  | NAP *(now)* | 48.8% | −4.6 | −8.1 | +3.9 | **82.0%** |
  | AoS *(morning)* | 52.0% | −17.3 | −6.3 | +1.3 | **57.1%** |
  | AoS *(Tier III modelled)* | 52.0% | −17.3 | −6.3 | +12.3 | 78.3% |
  | AoS *(now, Tier I capped)* | 52.0% | **−11.2** | −7.2 | +13.0 | **89.6%** |

  **The reference moved on 2026-11-06, and it was the bug.** BAT's 81.6% was
  the shape this table called correct, and the figure NAP's Devious
  Opportunities were re-priced to match — and it was measured through the
  pooled-token defect in BAT's own Tier III. Honest, BAT reads **90.0%**, so
  no game in the set has the 81–85% shape any more. All three still obey the
  rule — Tier III beats Tier II and stays under solo — but by rung BAT runs
  86.4 / 90.0 / 92.8 / **97.2%**, which is flat at Nobulous, and NAP at
  82–87% is now the one furthest from the others. **What the campaign axis
  should cost is a decision that has not been made**; until today it was
  being read off a number that was wrong. Read as levels, AoS looked like a Tier III
  problem; read as steps, the hole was dug at Tier I — so "Tier II is the
  trough" was true of the level and false of the cause. Both ends are now
  fixed, and the remaining complaint has swapped ends: AoS's Tier III is the
  *shallowest* campaign penalty of the three at 89.6% of its own solo cell,
  and 95.5% at Easy. It still obeys BAT's rule, so that is a shape question
  rather than a defect.

- **Two cards changed on 2026-11-06, both in Tier III, and only one of them
  is a card.** NAP's six Devious Opportunities had their Targets raised to
  what the cards they replace cost; AoS's Tier III was not changed at all,
  its MODEL was. See the two bullets below, and `simulation/RESULTS.txt`.

- **NAP's Devious Opportunities now cost what they displace.** They were
  Targets `3 3 3 3 4 3`, a mean of 3.17, and they REPLACE the six base
  Opportunities at `4 4 5 5 4 5`, a mean of 4.50 — so Tier III was handing
  out six cards that were both stronger *and* cheaper than the ones they
  displaced. It showed: Tier III read **above the solo column at every rung**
  (Standard 52.3% against 48.8% solo, and 121.9% of solo at Nobulous), which
  is the one shape the design says a tier must not have.

  Tier I's own note already states the principle — the Following Setbacks
  "displace base Setbacks of similar weight" — so this is that rule applied
  to Tier III, and a cost correction rather than a re-pitch. Nothing else on
  the cards moved: the dots, the effects and the dual use are untouched, and
  `rules/nrj.html` prints no Targets so it needed no edit. The dual use
  ("discard it during the apprenticeship to ignore one Setback's
  restrictions") was measured first and is worth **0.2 points** — it was
  never the problem.

  Three source sites carry these numbers and `check_app_sync.py` compares two
  of them: `DEVIOUS` in `generator/build_nrj.py`, `DEVIOUS` in
  `simulation/nap.py`, and `NAP_DEVIOUS` in `playtest/dist/suite.js`
  (consumed at `suite.js:720` as `target: c[2]`, swapped in for the base
  Opportunities at `suite.js:759` when the tier is 3).

- **AoS Tier III was never measured; the model implemented one sixth of it.**
  No AoS card changed. `simulation/aos.py` gave Tier III two *fungible*
  charges and spent every one on a single reward — Root Access, "treat one
  failed element as successful" — in any cycle. That was wrong twice, in
  opposite directions: Root Access prints "**During Advanced Programming**",
  so the one modelled card was too strong, and the other five rewards did
  nothing at all, so the module was five-sixths absent. This is the defect
  `RESULTS.txt` already records against BAT's Tier III, "six separate
  once-per-game cards modelled as one fungible token spent on two of them".

  Each claim is now a named card doing what it prints. Standard Tier III goes
  **29.7% → 40.7%** on the published 20,000-game grid, so the figure before
  2026-11-06 was not a measurement of the module — it was a measurement of
  part of one card. The solo, Tier I and Tier II columns do not move at all,
  which is the check that the change is contained: only Tier III grants a
  Routine. The pooled model is still reachable with `BACKDOOR_REWARDS =
  False`, which is what every figure before this date was measured on.

  **The open question this raises is the SPREAD, and it is not settled.**
  Priced one at a time at 6,000 games a cell against a 28.2% trough: Resource
  Fork +6.2, Garbage Collection +5.8, Root Access +1.6, Diagnostic Port +1.4,
  Privilege Escalation +1.0, Packet Sniffer +0.0. The two recovery Routines
  are worth four times the other four, so with only 2 claims a game "claim
  the best two" is solved rather than chosen — Tier III reads 77.0% of solo
  on fork+garbage and 65.5% on root+diag. Packet Sniffer's 0.0 is by
  construction, not measurement: its reward is information and the model has
  no Program-selection choice for it to inform. The published grid takes the
  best pair, which is what a player takes.

  **The claim cap is NOT the constraint and was not touched.** Under the old
  pooled model even 6 charges reached only 66.2% of solo, and 1 charge scored
  the same as 2, because the second was always spent on a Catastrophic
  Failure the free miss-negation would have absorbed for nothing.

- **FIXED 2026-11-06: AoS's Tier I, the biggest thing on the campaign axis.**
  One Nobulous Interference card is drawn at setup, and priced alone at
  Standard **"I Don't Have Time for This" read 1.2%** against a 51.8% solo
  column — not a difficulty setting, a loss, in a sixth of all AoS campaign
  games. Its two clauses were split: clause one (begin all Programs
  Overheated) is worth roughly nothing, and clause two ("when an
  already-Overheated Program fails, cycle it to the bottom of its deck
  instead of setting it aside") was the whole −50. The mechanism is the
  interaction and it is invisible on the card: normal escalation is stable →
  overheated → aside, clause one starts everything at the second step, so
  clause two replaced the *third* and nothing could ever leave the deck. The
  clause that reads as mercy was the trap.

  Capping the recycle read 3 → 19.3%, 2 → 24.3%, **1 → 34.9%**, deleted →
  52.1%. Deleting puts the card above the solo column, so it wanted capping.
  The card now prints **"The first time each already-Overheated Program
  fails"** and the model carries `RECYCLE_LIMIT` / `RECYCLE_SCOPE` in
  `aos.py`, where `-1` restores the uncapped card every earlier figure used.

  **The wording had to choose a scope.** *Each* Program gets one reprieve and
  reads 34.9%, which puts the card second only to Memory Leak. Once per
  *game* reads 49.8% — the harshest-sounding card in the deck would have
  become the second mildest in it. Per Program is the one that lands in band.

  The deck now reads 33.3 / **34.9** / 36.6 / 40.1 / 40.5 / 51.3, a 0.5-to-18.4
  spread where it was 0.7-to-50.5. The card left outside the deck is now
  **Nobulous Was Here at −0.5, too mild** — raised, not fixed.

  **Two knobs and four checks came with it.** `INTF_PICK` forces the draw so
  the per-card table is reproducible from the shipped model rather than from
  a scratch harness — and it *makes* the draw and discards it, so each cell
  runs the stream a real game would. `check_app_sync.py` now compares the
  whole **Interference and Corrupted Limitation** decks against the
  generator, and asserts the card and `aos.py` agree on the cap. **Nothing
  was checking either deck**, which is exactly how a change that has to be
  made in two places drifts — and this one had to be made in three.

- **FIXED 2026-11-06: BAT's Research Notes were one pooled token.** The six
  Tier III cards shared one counter, `self.notes`, spendable on two of the
  six printed rewards; the other four did nothing. Same defect as AoS's
  Backdoor Routines, found by going looking for it. **And it was worse than
  the count suggests: of the two implemented, one never fired.** Unexpected
  Resilience was reached for only when a Rat could not attack at all — 0%
  spent against a 91% claim rate — so BAT's published Tier III column was
  measuring *one card*, Successful Integration. Standard **43.4% → 47.9%**;
  `NOTE_REWARDS = False` reproduces the old grid exactly.

  Priced one at a time with `NOTE_PICK` (claim / spend rates from 20,000
  ordinary Tier III games; the no-Note floor is 38.7%, which is Tier II):

  | Research Note | claimed | spent | alone |
  |---|---|---|---|
  | Acceptable Losses | 74% | 45% | **+11.9** |
  | Successful Integration | 81% | 78% | +2.4 |
  | Red Means Go | 81% | 75% | +2.3 |
  | Cross-Species Compatibility | 96% | 46% | +1.7 |
  | Unexpected Resilience | 91% | 0% | +0.0 |
  | Controlled Failure | 0% | 0% | +0.0 |

  **Acceptable Losses carries the module** at +11.9 against +1.7 to +2.4 —
  and it was one of the four that did nothing. Same band complaint the
  Backdoor rewards draw: which to claim is solved, not chosen. Raised.

- **ONE CARD CHANGED WITH IT: Unexpected Resilience took its restriction
  onto the card.** It printed "Once per game, recover all of that Rat's
  dice" with no timing, and the restriction `bat.py` assumed existed nowhere
  else. Played at any competent moment the unrestricted card is **+10.2
  alone and puts Tier III at 57.9%, above the 53.2% solo column**. Capping
  the *dice* does not fix it — 1 die reads 55.0%, 2 reads 57.4%, 3 reads
  58.5% — because the battle's binding constraint is the shared pool, so the
  value is in the timing. It now prints *"Once per game, when a Rat has no
  available dice, recover all of them."* `RESILIENCE_TRIGGER = "short"` is
  the unrestricted card, kept because it prices the restriction: 47.9%
  against 57.9%.

  A bug fell out of fixing it: the recovery re-picked the battle pool with a
  raw EV sort instead of `commit_for_splice`, ignoring the leftmost Splice's
  colour requirement. Present from the start, harmless only because the
  branch never fired. Corrected; it moves no published figure.

- **NOW THE OTHER END OF THE SAME AXIS: AoS Tier III is too shallow.** The
  Tier I repair lifted all three tier columns by 5-6 points, because all
  three draw that card, so Tier III went 40.7% → 46.6% without anything in
  Tier III changing. At Standard that is **89.6% of its own solo column**,
  and at Easy 95.5% — nearly flat. It read that way against BAT's 81.6%;
  BAT re-measured at 90.0% the same day, so the complaint is shared rather
  than AoS's alone. Both still obey the rule (above Tier II, below solo), so
  this is a shape question rather than a defect. Raised, not touched.

- **Two cards changed on 2026-11-05, the Optimizer and the Debugger.** They
  are the only AoS card text changed since the set was calibrated. The
  Optimizer kept its ability and had its cadence slowed; the Debugger kept
  its name and had its ability replaced outright. The difference between
  those two outcomes is the lesson, and it is spelled out below.

  **Optimize now reads "Once per cycle and once in Advanced Programming,
  Target +1 successes may count as Optimal Implementation."** It was once
  per Program, which read 67.8% at Standard against a six-Technician mean
  of 51.4% — Optimal Implementation hands back 2 exhausted dice and dice
  are the binding resource, so how often it fires is the strongest dial a
  Technician has. Per cycle gives about three uses a game, so it stays a
  decision; it now reads 53.8% with a 25.0-point slope, both mid-pack. The
  second clause is not padding: `rules/aos.html` defines a cycle as one
  pass through the **Program deck**, and Advanced Programming is explicitly
  after the last one, so a bare "once per cycle" would hand the Optimizer
  nothing across the three Advanced Programs — the part of the game that
  decides it. Both terms are already bolded, defined, player-facing
  vocabulary, so **no rulebook edit was needed**. The lab implements the
  cadence as well as printing it: `state.optimizerUsed` is no longer
  cleared in `drawProgram()` and is cleared at the cycle turn and in
  `beginAdvanced()`. `check_app_sync.py` now asserts all three, and the
  assertion was confirmed to fail when the per-Program reset is put back.

  **The Debugger kept its name and lost its ability.** Debug now reads
  **"Once per Program, before rolling an element, swap 1 of its dice for a
  die from your available pool."** One clause, 99 characters, three printed
  lines. It replaced "Once per Program, after failing by exactly 1 success,
  reroll 1 allocated die. If it still fails, exhaust that die."

  **The trigger was the problem, not the frequency — this is the part worth
  carrying forward.** A reroll only pays when you are short by exactly 1.
  Harder rungs produce more near misses, so the ability grew with the
  difficulty it is supposed to be graded by and cancelled it: **88.4%** at
  Standard against five cards inside 47.1–54.3, and a slope of **10.2**
  where the other five lose 23–26. A card that flattens the ladder is a
  worse problem than a card that is strong, because the ladder is the only
  thing the campaign axis has to say.

  Metering it *does* work — "once per cycle and once in Advanced
  Programming", the Optimizer's clause word for word, reads 62.7% on a 25.5
  slope — and that version was built, verified in the lab and then backed
  out, because it buys a second cadence clause and still leaves the card 8.4
  clear of the roster. Frequency is only a brake on a bad trigger. **An
  ability whose payout does not depend on having missed needs no metering at
  all**, which is why the swap needs one clause where the reroll needed
  three (and the third of those, "exhaust that die", was a no-op: a failed
  element already exhausts every die on it).

  The swap is a colour upgrade worth about half a success every Program
  whatever the rung, so it inherits the no-ability floor's slope. **54.6%,
  slope 24.0**, 0.3 above the Architect, and adding it to the other five
  widens the roster spread from 7.2 to **7.5** — a sixth Technician that
  distorts nothing, where the reroll left 15.6 even after metering and 41.3
  before it. Eight alternatives were measured; the table is in
  `RESULTS.txt` and every variant is still selectable in `aos.py`
  (`dbg_reroll`, `dbg_reroll_cycle`, `dbg_cycle_strict`, `dbg_cost`,
  `cache`, `dbg_rec`, `dbg_clean`, `dbg_trace`, `link`, `optimize`).
  `link` — carry a surplus success onward — is the same disease from another
  angle at slope 16.5, so the rule generalises: **anything that pays you for
  falling short will flatten this ladder.**

  In the lab Debug is a *mode*, like Reconfigure, because selecting an
  allocated die on an element that has not rolled otherwise means "take it
  back". `Use Debug` arms it, you pick 1 die on the element and 1 from the
  pool, and the element's own button — which reads `Swap selected here` —
  is the confirm, so one gesture serves both Technicians. The reroll route
  is gone rather than disabled: `debugElement` and `data-debug` no longer
  exist, and `check_app_sync.py` asserts that, asserts the card text says
  swap and not reroll, and asserts that Optimize and Debug get **opposite**
  answers at all three reset sites (Optimize survives `drawProgram()` and
  comes back at the cycle turn and in `beginAdvanced()`; Debug does the
  reverse). Verified by driving the real UI: the swap moved the chosen die
  both ways with the element count unchanged, locked for the rest of the
  Program, and came back on the next one, with all 17 dice still accounted
  for at the end of the game.

- **Two AoS abilities were being MISPLAYED by the model, in opposite
  directions, and had been hiding each other.** Neither was a card problem.
  Fixing them moved the published AoS row from 51.7% to 57.4% on 2026-11-05
  without the game changing at all; replacing the Debugger's ability later
  the same day brought it back down to 52.0% — within 0.3 of where the row
  started the day, because the game never changed.

  `Debug` only ever fired on the POST-reroll total, because the model spent
  the extra STR roll whenever an element came up short. That is wrong play:
  an extra roll is a full reroll that stands "better or worse" **and**
  exhausts that element's dice regardless of outcome, while Debug is one
  die and free. A player on Target-1 declines the roll and Debugs, and may
  still spend the roll if Debug misses too. 68.0% → 88.4%.

  `Reconfigure` prints "move **up to** 2 allocated dice", and up to 2
  includes zero — it is a may. The model had no way to decline and moved
  dice whenever one element sat above its Target and another below, which
  under `sacrifice_short` is self-harm: triage leaves survivors on Target+1
  (so "rich") and the abandoned element on its one floor die (so "short"),
  so it stripped the buffer off elements that were going to pass to load
  the element it had deliberately given up. 32.4%, against 47.2% for having
  no ability at all.

  **Reconfigure cannot be judged by any pre-roll rule.** The card says
  "before rolling AN element" and elements roll one at a time, so it is an
  option held open across the Program and the model has to choose *when*.
  It now enumerates the legal redistributions and scores each against an
  exact success distribution (`succ_dist`), weighing a Catastrophic Failure
  at `ARCH_HP_WEIGHT` dice. Played that way it is worth +7 over no ability:
  54.3%, slope 23.0, mid-pack. **Do not "improve" this by making it wait
  for information** — holding the use until a failure has happened measures
  *worse*, 50.7%, because waiting shrinks the set of unresolved elements
  faster than the information is worth. `architect_hold` keeps that rule so
  the comparison stays in the file, and `ARCH_HP_WEIGHT` — the one free
  parameter in that decision — was swept 4→40 with Standard reading 54.5 /
  54.4 / 54.3 / 55.2 / 54.9%, a spread inside the sampling noise.

  A die is **not** worth 1 success, which is where the intuition fails
  here: purple is 1.0 but blue is 0.83, green 0.67, yellow 0.5, and the
  pool is 4/4/4/4/1, so the average die is 0.77 and an element on Target+1
  dice is nowhere near safe.

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
