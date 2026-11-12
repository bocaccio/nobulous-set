# Claude continuation handoff — Nobulous Set

## Project

Repository: `C:\Users\weeks\Documents\BoardGame\20 Strong\NobulousSet_repo`

Read `AGENTS.md`, `HANDOFF.md`, and `README.md` before editing. `AGENTS.md` is
the operating manual and wins where this file disagrees with it. The
authoritative sources are:

- Card definitions: `generator/build_*.py`
- Rules: `rules/*.html`
- Browser playtest: `playtest/dist/`
- Generated card sheets and PDFs: `images/`, `print-and-play/`, and `playtest/dist/assets/`

## User preferences and constraints

- Keep BAT, NAP, AoS, and NRJ data synchronized when changing shared behavior.
- Preserve unrelated edits in the working tree, and make a Git checkpoint
  before substantial work.
- Do not change card text, Targets, or rules wording casually — the numbers
  are simulation-calibrated. Raise a suspected design error first.

## Latest change — the NAP Assignment revision, 2026-11-12

All 26 Tasks, the 6 Opportunities and NRJ's 14 NAP cards were revised. The
short version, with the long version in `CARD_MANIFEST.txt` under
*NAP ASSIGNMENTS, CURRENT* and the measurements in `rules/RULES_CHANGELOG.txt`:

- Every exact-success and exact-dice-count condition is gone from the Request
  effects; a reward pays on completion and names a **colour**.
- All 26 **Demand** faces gained a completion reward. A Task pays at most once,
  on the face it was completed on.
- Six Demand Targets came down from 9 to 6, and Suture's Request rose 5 to 6.
- The Final Exam pool is **1 card per subject**, chosen at random, three of the
  four drawn — it was weighted by Credits.
- Each Opportunity prints *when* it is spent; Study Nobulous' Notes now flips a
  Demand back to its Request side.

**`phaseCommittedSuccesses` is gone from `playtest/dist/suite.js`.** It existed
only for Organize the Specimen Cabinet's "exactly 2 successes across all
committed dice this strategy phase", and this revision deleted that condition
along with the other fourteen like it. An earlier copy of this file asked
whether that counter should reset between rolls or span the whole Time Slot;
that question no longer has a card attached to it.

## Running the playtest

From the repository root:

```bash
python playtest/serve.py
```

**Not `python -m http.server`.** It sends no cache headers, so the browser
caches `index.html` — and since that file names every `?v=` token, a cached
copy pins you to an old build however often you bump them. The symptom is a
feature that is simply absent with no error, which reads exactly like code
that was never written.

Open `http://localhost:8000/`. State lives in browser localStorage under
`nobulous-suite-v1`; use the "New NAP test" button for a clean state. When you
change a file under `playtest/dist/`, bump the shared `?v=` token in
`index.html` — one token, used by every script and stylesheet.

## Before you call anything done

```bash
cd generator && python check_app_sync.py && python check_cards.py
cd ../simulation && python coverage.py
cd ../tts && python test_setup.py
```

`coverage.py` is the only thing that can be trusted about what is and is not
modelled; a win rate written in a comment has no predicate at all. And
mutation-test any check you add — a check that cannot fail is worse than none,
and this repo has caught four of them that way, including one added during the
2026-11-12 revision whose regex matched `dic` and `dice` but never `die`.
