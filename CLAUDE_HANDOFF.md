# Claude continuation handoff — Nobulous Set

## Project

Repository: `C:\Users\weeks\Documents\BoardGame\20 Strong\NobulousSet_repo`

Read `AGENTS.md`, `HANDOFF.md`, and `README.md` before editing. The authoritative sources are:

- Card definitions: `generator/build_*.py`
- Rules: `rules/*.html`
- Browser playtest: `playtest/dist/`
- Generated card sheets and PDFs: `images/`, `print-and-play/`, and `playtest/dist/assets/`

## User preferences and constraints

- The user wants to make several changes before committing.
- Do **not** commit or push to GitHub until the user explicitly says to push.
- Preserve the existing dirty working tree. It contains many intentional changes from earlier UI and rules work.
- Keep BAT, NAP, AoS, and NRJ data synchronized when changing shared behavior.

## Current request and latest change

The user changed the NAP Task card **Organize the Specimen Cabinet** effect to:

> If completed with exactly 2 successes across all committed dice this strategy phase, recover 1 committed die.

Updated files:

- `generator/build_nap.py` — authoritative task text.
- `playtest/dist/suite.js` — playtest effect text and NAP reward logic.
- `playtest/dist/index.html` — bumped the suite cache query to `nap-cabinet-phase-1`.

The playtest now tracks `state.nap.phaseCommittedSuccesses` and uses it for Organize's exact-two-success reward. It also suppresses the reward when an unassigned rolled hit remains, per the immediately preceding user request.

## Important follow-up to verify

The current implementation resets `phaseCommittedSuccesses` when a new Strategy roll is made and at the end of a Time Slot. If “across all committed dice this strategy phase” means the whole Time Slot, it should **not** reset between rolls. Decide whether the intended scope is the complete Strategy phase (all rolls in the active Time Slot) and adjust accordingly. Also ensure successes committed to other Assignments in that phase are included, while stored dice from prior phases are not double-counted.

The generated NAP card sheets/PnP PDFs have not been rebuilt after this wording change because the available Python environment lacks `weasyprint`. If the printed card must reflect the new text, use an environment with the generator dependencies, then run:

```powershell
cd generator
python build_nap.py
python pack.py
```

Copy/update the resulting NAP assets according to the existing project workflow.

## Verification already performed

- `node --check playtest/dist/suite.js` passed.
- `python -m py_compile generator/build_nap.py` passed.
- Browser-style behavior was tested with a temporary Playwright fixture against a local server:
  - Organize completed with an extra unassigned hit: no reward shown.
  - Organize completed with an extra unassigned miss: reward shown.

The temporary fixture was not kept in the repository.

## Running the playtest

From the repository root:

```powershell
python -m http.server 8000 -d playtest/dist
```

Open `http://localhost:8000/`. The app stores state in browser localStorage under `nobulous-suite-v1`; use the “New NAP test” button when a clean state is needed.

## Recent NAP interface work already present

The working tree includes earlier requested changes: card-sized time-slot cards with color bands, horizontal dice area, assignment/discard pile switcher and subject counts, apprentice and FINF cards in the top row, discard-card viewing/hover previews, completed-card rotation and delayed discard, multi-roll selection/rerolling, FINF assignment removal, and recovery-dot handling.

Review the diff before touching these areas; do not overwrite unrelated user edits.
