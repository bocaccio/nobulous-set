# The Nobulous Set

A fan expansion for **20 Strong** — three standalone solo games plus a campaign
that ties them together.

> *Three games. One terrible idea.*

| | | |
|---|---|---|
| **BAT** — Build-a-Tyrant | 60 cards | *Four scientists, one boss, and every failure makes it stronger.* |
| **NAP** — Nobulous Apprenticeship Program | 57 cards | *A prestigious opportunity. Terms and conditions apply.* |
| **AoS** — Automaton of Shale | 51 cards | *Commit everything before you know anything.* |
| **NRJ** — Nobulous Research Journal | 74 cards | Optional overlay for each game, plus the Imposter finale. |

Requires the dice from **20 Strong**: 4 Purple, 4 Blue, 4 Green, 4 Yellow,
1 Red, plus the Health, Strategy and Recovery stat dice and the Chip.

This is an unofficial fan project. It is not affiliated with or endorsed by
Chip Theory Games.

---

## Browser playtest lab

`playtest/` contains the complete BAT, NAP, AoS and NRJ browser interface. It
is self-contained and works without internet access after the repository has
been downloaded.

On Windows with Miniforge or Python installed, double-click
`Start_Playtest.bat`. It finds common Miniforge installations automatically,
starts the local server, and opens the playtest in your browser. Keep its
window open while playing.

You can instead run the server manually from a Miniforge Prompt:

```bat
python -m http.server 8000 -d playtest/dist
```

Then open `http://localhost:8000/`. To stop the server without closing the
terminal, press **Ctrl+C**. Progress is stored locally in that browser. If the
launcher encounters a problem, it now keeps the window open and displays the
specific error.

To use an iPad on the same Wi-Fi network, leave the server running and open
`http://COMPUTER-IP:8000/` in Safari, replacing `COMPUTER-IP` with the Windows
computer's IPv4 address from `ipconfig`.

The interface uses the generated card sheets in `playtest/dist/assets/`. When
changing interface code, edit `playtest/dist/index.html`, `styles.css`,
`app.js`, or `suite.js`. Card and rules masters remain in `generator/` and
`rules/`; do not edit the copied browser assets as authoritative source files.

---

## Play it in Tabletop Simulator

The mod is generated from the same sources as the print-and-play, so the two
can never drift apart.

**[Workshop link — add once published]**

To build it yourself:

```bash
cd tts
python3 build_mod.py --user YOUR-GITHUB-USERNAME --repo nobulous-set
```

That writes `NobulousSet.json` with every image URL pointing at this repo's
`images/` folder through jsDelivr. Drop the file into

```
Documents/My Games/Tabletop Simulator/Saves/
```

load it, and check the decks resolve before uploading to the Workshop.

Options:

| flag | effect |
|---|---|
| `--user NAME` | GitHub account that owns the repo |
| `--repo NAME` | repository name, default `nobulous-set` |
| `--ref REF` | branch or tag, default `main` — see *Pinning* below |
| `--raw` | use `raw.githubusercontent.com` instead of the jsDelivr CDN |
| `--local` | `file:///` URLs for checking layout on your own machine |

### Pinning

`--ref main` means every player picks up image changes as you push them, which
is what you want during playtesting. Once the set is stable, tag a release and
build against the tag so a live game can't change under someone mid-session:

```bash
git tag v1.0 && git push --tags
python3 build_mod.py --user YOU --ref v1.0
```

---

## Print and play

`print-and-play/` holds one PDF per game, Letter, poker size (63.5 × 88.9 mm),
**9 cards to a page**. Pages of landscape cards are themselves landscape, so
print at 100% with scale-to-fit **off** and let the printer auto-rotate. Faint
ticks in the margins mark every cut line.

These decks are **genuinely two-sided** and their pages alternate front /
mirrored back for long-edge duplex printing:

- BAT Lab Rats — Side A / Side B
- NAP Apprentices and AoS Technicians — two characters per card
- AoS Routine, Specialized, Unstable and Advanced Programs — Stable / Overheated

`print-and-play/PNP_CONTENTS.txt` gives the page range of every section and
flags the duplex runs. `CARD_MANIFEST.txt` lists every deck with its grid,
orientation and card back.

---

## Rules

`rules/` holds a short player-facing rulebook for each game plus the campaign
supplement. They are written for someone who has never seen the design notes —
components, setup, turn sequence, and the specific things that trip people up.

`rules/RULES_CHANGELOG.txt` records the audit of all four books against the
design compendium, the printed cards and the simulators, and lists the two
questions that audit left open.

`rules/AoS_FLAVOR_TEXT.md` lists all 64 Stable/Overheated Program lines and all
6 Limitation lines in one place. The same text is printed directly on the AoS
card images and print-and-play sheets.

To change the rules text, edit the HTML sources — `bat.html`, `nap.html`,
`aos.html`, `nrj.html`, all sharing `style.css` — and run `python3 build.py`
to regenerate the PDFs. `Nobulous_Set_Rules_EDITABLE.docx` is all four books
flattened into one Word file for marking up away from the toolchain;
`make_editable.py` regenerates it from the HTML. The HTML is the master —
edits made in the .docx have to come back to it.

---

## Repository layout

```
images/          card sheets and backs — what the TTS mod points at
rules/           four player rulebooks (PDF)
print-and-play/  four PnP PDFs
playtest/        local browser playtest interface and launch instructions
tts/             mod generator, table script, dice objects
generator/       the card generator that produces images/ and print-and-play/
CARD_MANIFEST.txt
```

Nothing in `images/` is hand-edited. To change a card, edit the relevant
`generator/build_*.py` and re-run it; both the sheet and the PnP page are
regenerated together.

---

## Status and feedback

Prototype. All three games and the campaign have been simulated end to end, but
**table play is thin** — the balance figures are model output, not play reports.
Two things to know going in:

- **AoS Unstable is under-tuned.** It currently wins roughly one game in seven.
  Treat it as experimental rather than as a peer of Routine and Specialized.
- **NRJ tiers are not difficulty levels.** Tier I introduces interference,
  Tier II is the pressure peak, Tier III hands you tools to exploit the mess.

Feedback most wanted:

1. Is AoS's pre-allocation a satisfying puzzle or fiddly bookkeeping?
2. Does the Imposter's Suspicion row feel like a spiral, or does avoidance
   defuse it?
3. A Tier II campaign takes roughly five replayed chapters. Escalating stakes,
   or grind?
4. Is an 18-card Research Pool readable on the table?

Open an issue, or comment on the Workshop item.
