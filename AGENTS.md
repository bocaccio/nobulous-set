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
- For browser-interface work, run `python playtest/serve.py` from the
  repository root and verify the affected game flow. Do NOT use
  `python -m http.server`: it sends no cache headers, so the browser caches
  `index.html`, and since that file is what names every `?v=` token a cached
  copy pins you to an old build however often you bump them. The symptom is a
  feature that is simply absent with no error, which reads exactly like code
  that was never written.
- Keep BAT, NAP, AoS and NRJ card data synchronized with the authoritative
  generator and rule sources.

## Useful commands

```bash
# Local playtest lab (sends honest cache headers; see above)
python playtest/serve.py

# Rebuild rule PDFs after editing rules HTML
cd rules && python build.py

# Rebuild a card family, then merge PnP output
cd generator
python build_bat.py   # or build_nap.py / build_aos.py / build_nrj.py
python pack.py

# Promote out/ into images/, playtest/dist/assets/ and print-and-play/,
# and cut release/tts (scaled for TTS) and release/print (300 DPI)
cd generator
python deploy.py --prune --release

# Check the playtest lab still matches the generators (exit code = failures)
cd generator && python check_app_sync.py
python check_cards.py
```

Nothing copies `generator/out/` into the shipping trees except `deploy.py`, so
run it after any rebuild; `--prune` removes output a renamed or dropped deck
left behind. Rendering is byte reproducible — re-rendering a family with
nothing changed rewrites nothing in `out/` — so a noisy diff means you really
did change something.

The card generator has environment-specific output paths; inspect `gen.py`
before rebuilding on a new machine.

## Dependencies

`requirements.txt` lists them and says which script needs which. Two cannot be
installed by pip and both fail without naming themselves:

- **WeasyPrint's GTK libraries** are found through `PATH`, not through Python.
  Without them any script that imports WeasyPrint - `build_*.py`,
  `check_cards.py`, `rules/build.py` - dies with `OSError: cannot load library
  'libgobject-2.0-0'`, which reads as a broken install. On this machine:

  ```bash
  PATH="/c/Users/weeks/miniforge3/Library/bin:$PATH"
  ```

- **`pdftoppm`** (poppler-utils) must be on `PATH`; `gen.py` shells out to it.

Nothing a player touches needs any of this. The lab is static files, the
sheets and PDFs are committed, and `simulation/` is pure Python.

Run `build_nap.py` before `build_nrj.py` into a fresh output directory: NRJ's
Imposter Tasks and Devious Opportunities print NAP's Assignment back and
`make_back` has to have built it first.

Card geometry has ONE owner, `gen.py` - `PORTRAIT`, `LANDSCAPE`, `DPI` and
`CARD_INSET_MM`. `build_catalog.py` publishes each deck's real cell size and
gutter into `catalog.json`, and the lab reads them from there. Do not
reintroduce a pixel literal anywhere else; `check_app_sync.py` now checks all
three agree.

So does the header: `gen.HDR_STYLES` says what each family really prints
(title sizes, subtitle size, extra side padding) and `gen.HDR_H_MM` is the one
depth every card's colour band gets. If a build script overrides a header size
or padding in its own stylesheet, add a style there and pass its name to
`title_cls`/`hdr_fit` - otherwise titles are measured against a card that does
not exist, and they wrap.
