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
  is a 12-space track; the Health die sits on it. It is never shuffled or drawn.
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

---

## 10. Known open items

Not your job to fix, but worth knowing if Jon raises them:

- **AoS Unstable is under-tuned** — roughly a 1-in-7 win rate against a ~30%
  design target. Labelled experimental in the rulebook.
- **NAP Impostor Tasks have no recovery-colour dot**, unlike every other
  Assignment. A rules decision is pending.
- **Two rules questions are open**, both recorded at the end of
  `rules/RULES_CHANGELOG.txt`: whether the Red die joins the BAT battle pool,
  and what NAP's Slacker means by "voluntarily draw an additional Assignment".
  Neither blocks anything you are doing.
- Card art is 200 DPI (633 × 886 px). Fine on screen; would want 300 for print
  production.

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
