# Nobulous Playtest Lab

This folder contains the complete offline browser interface for BAT, NAP, AoS
and the NRJ Imposter finale.

From the repository root, run:

```bash
python -m http.server 8000 -d playtest/dist
```

Then open `http://localhost:8000/`. Windows users can instead double-click the
top-level `Start_Playtest.bat` file. The launcher recognizes common Miniforge
install locations and opens the browser automatically. Press Ctrl+C in the
launcher window to stop the server.

The `dist/` directory is a complete static web application. Browser progress is
stored locally on the device and is not written back into the repository.

BAT Experiment names, Targets, effects, and flavor text are authored in
`generator/build_bat.py`. After editing them, run
`python generator/export_bat_experiments.py` to refresh the browser data in
`dist/bat_experiments.js`. Run `python generator/render_bat_experiments.py` to
refresh the printable Experiment pages and TTS sprite. The latter uses
ReportLab, pypdf, Pillow, and Poppler's `pdftoppm`; it leaves the other BAT card
families and the remaining print-and-play pages intact.
