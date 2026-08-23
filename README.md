# The Nobulous Set

A fan expansion for **20 Strong** — three standalone solo games plus a campaign
that ties them together.

> *Three games. One terrible idea.*

| | | |
|---|---|---|
| **BAT** — Build-a-Tyrant | 59 cards | *Four scientists, one boss, and every failure makes it stronger.* |
| **NAP** — Nobulous Apprenticeship Program | 57 cards | *A prestigious opportunity. Terms and conditions apply.* |
| **AoS** — Automaton of Shale | 51 cards | *Commit everything before you know anything.* |
| **NRJ** — Nobulous Research Journal | 74 cards | Optional overlay for each game, plus the Imposter finale. |

Requires the dice from **20 Strong**: 4 Purple, 4 Blue, 4 Green, 4 Yellow,
1 Red, plus the Health, Strategy and Recovery stat dice and the Chip.

This is an unofficial fan project. It is not affiliated with or endorsed by
Chip Theory Games.

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

`print-and-play/` holds one PDF per game, Letter, poker size (63.5 × 88.9 mm).

Four decks are **genuinely two-sided** and their pages alternate front / mirrored
back for long-edge duplex printing:

- BAT Lab Rats — Side A / Side B
- NAP Apprentices and AoS Technicians — two characters per card
- AoS Routine, Specialized, Unstable and Advanced Programs — Stable / Overheated

`CARD_MANIFEST.txt` lists every deck with its grid, orientation and card back.

---

## Rules

`rules/` holds a short player-facing rulebook for each game plus the campaign
supplement. They are written for someone who has never seen the design notes —
components, setup, turn sequence, and the specific things that trip people up.

---

## Repository layout

```
images/          card sheets and backs — what the TTS mod points at
rules/           four player rulebooks (PDF)
print-and-play/  four PnP PDFs
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
