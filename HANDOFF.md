# Handoff — The Nobulous Set

**For a fresh Claude Code session.** You have no prior context on this project;
everything you need is here. Read this file first, then `README.md`.

---

## 0. Status as of 2026-08-24

Tasks one and two are **done**. The repo is public and the TTS mod is built and
installed. What remains needs a human in Tabletop Simulator and on Steam.

| | task | state |
|---|---|---|
| 1 | Publish the repo | **done** — https://github.com/bocaccio/nobulous-set |
| 2 | Build the TTS mod | **done** — save installed, all 47 images resolve |
| 3 | Verify in TTS | **partly** — static checks pass, buttons need pressing |
| 4 | Publish to the Workshop | **not started** — tag `v1.0` not yet created |

Jon's GitHub account is **bocaccio**. Skip the "ask Jon for his username" step.

---

## 1. What this is

A finished fan expansion for the board game **20 Strong**, consisting of three
standalone solo games and a campaign overlay. The design work is done and the
balance is calibrated by simulation. Your job is **infrastructure, not design**:
host the images and get the Tabletop Simulator mod working.

**Do not change card text, targets, or rules wording.** Those numbers came from
tens of thousands of simulated games; edits will silently break the calibration.
If something looks wrong, raise it rather than fixing it.

---

## 2. Environment on this machine

- **Python is not on `PATH`.** `python` / `python3` hit the Microsoft Store alias
  stub and fail. Use miniforge directly:
  `C:\Users\weeks\miniforge3\python.exe` (3.13.13). `build_mod.py` needs no
  third-party packages, so nothing else has to be installed.
- WSL is **not** installed. Relevant only if you ever regenerate card art (§8).
- `gh` CLI is installed and authenticated as `bocaccio`.
- The repo has two commits on `main`, both pushed. `git log --oneline` to confirm.

---

## 3. Repository layout

```
images/           47 PNGs — card sheets and backs. The TTS mod points here.
rules/            4 player rulebooks (PDF)
print-and-play/   4 PnP PDFs, Letter, poker size
tts/              build_mod.py, decks.py, lua.lua, dice_objects.json
generator/        the card generator that produced images/ and print-and-play/
README.md         public-facing
SETUP.md          the short version of this file
CARD_MANIFEST.txt every deck: grid, orientation, which back it uses
CONTENT_NOTICE.md fan-content disclaimer — keep it
.gitattributes    marks *.pdf and *.png binary — see the warning below
```

`images/` is **build output**, not hand-edited. Never edit a PNG directly.

> **Do not delete `.gitattributes`.** This machine has `core.autocrlf=true`, and
> git classifies the four PnP PDFs as *text*. Without the binary markings, a
> clone or checkout rewrites LF→CRLF **inside the PDFs** and corrupts all four.
> The PNGs are detected as binary on their own; the PDFs are not.

---

## 4. Task one — publish the repo — DONE

The repo is public at **https://github.com/bocaccio/nobulous-set**.

Both hosting paths are verified live — all 47 images return `200 image/png`:

```
https://cdn.jsdelivr.net/gh/bocaccio/nobulous-set@main/images/BAT_Encounters_TTS.png
https://raw.githubusercontent.com/bocaccio/nobulous-set/main/images/...
```

jsDelivr warmed immediately. If you ever push new images and get a 404, that is
normal on first request — wait and retry before debugging.

---

## 5. Task two — build the TTS mod — DONE

```bash
cd tts
C:/Users/weeks/miniforge3/python.exe build_mod.py --user bocaccio
```

Writes `NobulousSet.json` and `REQUIRED_IMAGES.txt` next to itself. Both are
gitignored; they are build output. The build is deterministic — the RNG is
seeded, so rebuilding the same inputs gives a byte-identical file.

Last run: **50 objects, 232 cards, 47/47 images `ok`, 0 `MISSING`**.

Flags:

| flag | effect |
|---|---|
| `--user NAME` | GitHub account, required |
| `--repo NAME` | default `nobulous-set` |
| `--ref REF` | branch or tag, default `main` |
| `--raw` | raw.githubusercontent instead of jsDelivr |
| `--local` | `file:///` URLs, layout testing on one machine only |

The save is already copied to:

```
%USERPROFILE%\Documents\My Games\Tabletop Simulator\Saves\NobulousSet.json
```

Rebuilding does **not** update that copy — copy it across again yourself.

### Path fix applied 2026-08-24

`build_mod.py` had three paths hardcoded to the machine the set was authored on
(`/home/claude/...`). They are now resolved from the script's own directory,
which is what this document already described:

- `dice_objects.json` — was a hard `FileNotFoundError` on any other machine
- `OUT` and `SHEETS` — silently pointed outside the repo unless `TTS_OUT` /
  `TTS_SHEETS` were set

The env vars still override the defaults. See commit `577a6f6`.

---

## 6. Task three — verify in TTS — PARTLY DONE

Everything checkable without launching the game has been checked against the
built save and passes:

| check | expected | found |
|---|---|---|
| decks | 28 | 28 ✓ |
| image URLs resolve | 47 | 47 ✓ (all `200`) |
| `UniqueBack` decks | 7 | 7 ✓ incl. Specialized Programs |
| `SidewaysCard` decks | 11 | 11 ✓ |
| dice | 4 Purple / 4 Blue / 4 Green / 4 Yellow / 1 Red | ✓ |
| tokens | Health, Strategy, Recovery, Chip | ✓ |
| Lua | non-empty + Control Panel tile | ✓ 10,623 chars |

The eleven `SidewaysCard` decks are Lab Rats, Apprentices, Tasks, Opportunities,
Setbacks, Final Exams, Time Slots + FINF, Technicians, Impostor Tasks, Following
Setbacks, Devious Opportunities.

**Still to do — load the save and check, in this order:**

1. **Every deck renders.** URLs all resolve, so a grey question mark now means a
   TTS-side load failure rather than a bad path.
2. **The Control Panel shows buttons.** If not, the Lua failed to load; open
   Scripting and look for an error.
3. **Two-sided decks flip correctly.** Take a card from `Specialized Programs`
   and flip it: it must show *the same Program* Overheated, with one element's
   Target one higher.
4. **Landscape cards sit correctly.** NAP Tasks and Apprentices, AoS Technicians,
   BAT Lab Rats and the NRJ NAP decks should be wider than tall in hand.
5. **Press each setup button.** BAT, NAP, AoS and Imposter should each deal a
   sensible table and print a chat message. Cycle NRJ Tier to III first and
   confirm the extra module decks appear. **This is the main thing static
   checking cannot cover — it is the real remaining test.**

---

## 7. Task four — publish to the Workshop — NOT STARTED

**The `v1.0` tag has deliberately not been created yet.** Tagging pins the
published mod's images, so it should happen only once §6 step 5 has actually
passed — otherwise the Workshop item points at a build nobody has loaded.

Once TTS checks out:

```bash
git tag v1.0 && git push --tags
C:/Users/weeks/miniforge3/python.exe tts/build_mod.py --user bocaccio --ref v1.0
```

Copy the rebuilt save into the Saves folder again, reload it, then
Games → Save & Play → Workshop Upload. Put the repo URL in the description, and
add the Workshop link back into `README.md`.

---

## 8. If Jon asks you to change a card

The card art is generated. The flow is:

```bash
cd generator
python build_bat.py      # or build_nap.py / build_aos.py / build_nrj.py
```

**All five generator files still carry authoring-machine paths** — this has *not*
been fixed, unlike `tts/build_mod.py`:

- `gen.py` line 6 — `OUT = "/home/claude/cards/out"`, needs repointing to
  `../images`
- `build_aos.py`, `build_bat.py`, `build_nap.py`, `build_nrj.py` line 1 — each
  does `sys.path.insert(0, '/home/claude/cards')`, and `build_aos.py` also
  inserts `/home/claude/nap`

Dependencies: `weasyprint`, `pillow`, `reportlab`, `pypdf`, and `pdftoppm` from
poppler-utils. **WeasyPrint on Windows needs GTK installed separately** and is
genuinely awkward; WSL or a Linux container is far easier, and WSL is not
installed here. The shipped PNGs are prebuilt precisely so nobody has to do this
to play.

After regenerating: commit the changed PNGs, push, and only rebuild
`NobulousSet.json` if a deck's **card count, grid size or back** changed. Pure
art changes need no new save file — players pick them up when jsDelivr's cache
expires, or immediately under a new `--ref`.

---

## 9. Things that will look like bugs and are not

- **AoS Program decks have 8 cards, not 16.** Stable and Overheated are two
  faces of one card.
- **NAP Task cards look upside-down at the bottom.** The Demand half is printed
  rotated 180°; you turn the card over on the table. This is one-sided.
- **NRJ cards have base-game colours.** Deliberate — a Corrupted Limitation is
  meant to look like a Limitation. The dark blue foot band reading NOBULOUS
  RESEARCH JOURNAL is how you sort them out afterwards.
- **Some NRJ cards use a base-game card back.** Also deliberate: cards shuffled
  into a base deck must be indistinguishable face-down. `CARD_MANIFEST.txt` has
  the mapping.
- **The Lua enforces no rules.** Intentional. It deals and counts only.
- **`SidewaysCard` is a top-level property of the deck object**, not a field
  inside `CustomDeck`. Looking for it in the wrong place makes all eleven
  landscape decks appear to be missing the flag.

---

## 10. Known open items

Not your job to fix, but worth knowing if Jon raises them:

- **AoS Unstable is under-tuned** — roughly a 1-in-7 win rate against a ~30%
  design target. Labelled experimental in the rulebook.
- **NAP Impostor Tasks have no recovery-colour dot**, unlike every other
  Assignment. A rules decision is pending.
- Card art is 200 DPI (633 × 886 px). Fine on screen; would want 300 for print
  production.
- The generator paths in §8 are still unfixed.

---

## 11. Definition of done

- [x] Repo pushed and public
- [x] A jsDelivr image URL loads in a browser
- [x] `REQUIRED_IMAGES.txt` shows `ok` on every line
- [x] All 28 decks present and every image URL resolves
- [x] Seven decks carry `UniqueBack`, eleven carry `SidewaysCard`
- [ ] Decks render in TTS with no grey question marks
- [ ] A two-sided Program card flips to its own Overheated face
- [ ] All four setup buttons deal a sensible table
- [ ] Tagged `v1.0` and the mod rebuilt against the tag
- [ ] Workshop item uploaded, link added to `README.md`
