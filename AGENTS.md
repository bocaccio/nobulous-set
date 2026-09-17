# Working on The Nobulous Set

Read `HANDOFF.md` and `README.md` before making changes.

## Authoritative sources

- Card text and card construction live in `generator/build_*.py`.
- Player-facing rules live in `rules/*.html`; the PDFs are generated output.
- Full print-and-play files live in `print-and-play/`.
- The browser playtest interface lives in `playtest/dist/`.
- `images/` and the card/rule copies under `playtest/dist/assets/` are generated
  or deployment output. Do not treat copied assets as masters.

## Safety and workflow

- Do not casually change card text, targets, or rules wording. The existing
  numbers were simulation-calibrated; raise suspected design errors first.
- Preserve unrelated user edits and create a Git checkpoint before substantial
  work.
- For browser-interface work, run `python -m http.server 8000 -d playtest/dist`
  from the repository root and verify the affected game flow.
- Keep BAT, NAP, AoS and NRJ card data synchronized with the authoritative
  generator and rule sources.

## Useful commands

```bash
# Local playtest lab
python -m http.server 8000 -d playtest/dist

# Rebuild rule PDFs after editing rules HTML
cd rules && python build.py

# Rebuild a card family, then merge PnP output
cd generator
python build_bat.py   # or build_nap.py / build_aos.py / build_nrj.py
python pack.py
```

The card generator has environment-specific output paths; inspect `gen.py`
before rebuilding on a new machine.
