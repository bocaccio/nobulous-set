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
