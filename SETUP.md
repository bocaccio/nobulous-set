# Creating the repository

One-time setup. Replace `YOU` with your GitHub username.

```bash
cd nobulous-set
git init -b main
git add .
git commit -m "The Nobulous Set: cards, rules, print-and-play, TTS mod"

gh repo create YOU/nobulous-set --public --source=. --push
# or, without the gh CLI: create the repo on github.com, then
#   git remote add origin https://github.com/YOU/nobulous-set.git
#   git push -u origin main
```

## Check the image URLs before building the mod

After the push, open one image in a browser to confirm it serves:

```
https://cdn.jsdelivr.net/gh/YOU/nobulous-set@main/images/BAT_Encounters_TTS.png
```

jsDelivr caches for a few minutes on first request. If it 404s, wait and retry
before assuming something is wrong. `raw.githubusercontent.com` works too and
updates instantly, but is slower and rate-limited — fine for testing, worse for
a published mod.

## Build the mod

```bash
cd tts
python3 build_mod.py
```

`--user` defaults to `bocaccio`, this repo's own remote, so the plain command
is right unless you have forked it.

`NobulousSet.json` and `REQUIRED_IMAGES.txt` are written next to the script and
are gitignored, since they are build output.

## Updating a card later

1. Edit the relevant `generator/build_*.py`.
2. Re-run it. It writes into `generator/out/` and nowhere else.
3. `cd generator && python deploy.py --prune`. This is the only thing that
   copies `out/` into `images/`, `playtest/dist/assets/` and
   `print-and-play/`. Skipping it is how the shipped art drifted behind the
   generator twice.
4. `git commit` and `git push`.

Run `build_nap.py` before `build_nrj.py` into a fresh output directory: the
NRJ Imposter Tasks and Devious Opportunities print NAP's Assignment back, and
`make_back` has to have built it. A rebuild into the existing `out/` finds it
already there, which is why the order rarely comes up.

Players on `@main` pick up the new art the next time jsDelivr's cache expires;
the mod JSON does not need rebuilding for a redrawn card. It **does** need
rebuilding when a deck's card count, grid or back changes, and also when
`lua.lua` or the Notebook text changes — both are baked into the save, so a
rules correction reaches nobody until the save is rebuilt and re-uploaded.
That is how the mod came to be teaching a superseded finale; see HANDOFF §6b.

## Releasing

```bash
git tag v1.0 && git push --tags
python3 tts/build_mod.py --user YOU --ref v1.0
```

Building against a tag freezes the images for that Workshop version, so a live
game cannot change under a player mid-session.

## Run the browser playtest interface

From the repository root:

```bash
python -m http.server 8000 -d playtest/dist
```

Open `http://localhost:8000/`. On Windows, `Start_Playtest.bat` performs the
same command, recognizes common Miniforge install locations, and opens the
browser automatically. If it cannot start, it keeps the window open and shows
the error. Press Ctrl+C to stop the server.
