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
python3 build_mod.py --user YOU
```

`NobulousSet.json` and `REQUIRED_IMAGES.txt` are written next to the script and
are gitignored, since they are build output.

## Updating a card later

1. Edit the relevant `generator/build_*.py`.
2. Re-run it. It rewrites the sheet in `images/` and the PnP pages together.
3. `git commit` and `git push`.

Players on `@main` pick up the new art the next time jsDelivr's cache expires;
the mod JSON does not need rebuilding unless a deck's card count, grid or back
changed. If it did, re-run `build_mod.py` and re-upload the save.

## Releasing

```bash
git tag v1.0 && git push --tags
python3 tts/build_mod.py --user YOU --ref v1.0
```

Building against a tag freezes the images for that Workshop version, so a live
game cannot change under a player mid-session.
