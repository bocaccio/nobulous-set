"""Does every URL the mod bakes in actually resolve?

    python3 check_published.py          # every image and rulebook
    python3 check_published.py --quick  # only the ones git says are new
    python3 check_published.py --purge  # ...and clear the CDN's copy

Run it after pushing and BEFORE loading the mod in Tabletop Simulator.

GIVE THE PUSH A MINUTE. jsdelivr caches 404s too, so a file asked for
seconds after the push can report missing and be fine on the next pass.

AND THE ?v= TOKEN DOES NOT REACH jsdelivr. It defeats TTS's cache, which is
what it is for; jsdelivr keys on the PATH. So a file that keeps its name -
every card sheet, every rulebook - can be pushed and still arrive as last
build's bytes, which is why this script compares Content-Length rather than
settling for a 200.

--purge CLEARS A FILE AND CANNOT FIX A STALE BRANCH. jsdelivr resolves @main
to a commit and caches THAT for hours; purging the file re-fetches from the
commit it still thinks main is. Measured 2026-11-12: @main served a rulebook
two commits old while @<sha> served the right bytes. The cure is not to use
a branch at all -

    git push && python build_mod.py --ref "$(git rev-parse HEAD)"

- which bakes immutable @<sha> URLs, served at once and cached for good.

WHY THIS EXISTS. On 2026-11-12 the AoS table overlay was regenerated. It is
named by content hash, so regenerating it renamed AoS_Table_8c12fa89.jpg to
AoS_Table_e0fd8d3d.jpg; the mod was rebuilt to point at the new name, the
work was committed locally and not pushed, and the tile 404'd. TTS does not
report a failed image - it opens the Custom Tile dialog with a blank face,
which reads as a broken object rather than a missing file.

Nothing in check_app_sync.py could have caught it. That script is offline and
checks the local tree: the file existed, its hash matched its URL, and
REQUIRED_IMAGES.txt listed it. Every local invariant held. The thing that was
wrong was off the machine.

A `git ls-tree origin/main` check would be closer but still wrong, because it
fails for the whole normal window between a rebuild and a push - and a check
that is red during ordinary work is a check people learn to ignore. This asks
the only question that matters, of the only authority that can answer it, and
it is run deliberately rather than on every pass.
"""
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SAVE = os.path.join(HERE, "NobulousSet.json")
TIMEOUT = 30


def urls():
    """Every distinct http(s) URL in the save, in the order found."""
    with open(SAVE, encoding="utf-8") as fh:
        blob = fh.read()
    seen, out = set(), []
    for u in re.findall(r"https?://[^\"\\ ]+", blob):
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


def untracked():
    """Filenames git does not have on origin/main, as a hint for --quick.

    Only a hint: the remote-tracking ref can be behind the real remote, so
    this narrows what to test and never decides anything.
    """
    try:
        have = subprocess.run(
            ["git", "-c", "safe.directory=" + ROOT, "ls-tree", "-r",
             "--name-only", "origin/main"],
            cwd=ROOT, capture_output=True, text=True, check=True).stdout
    except Exception:                                      # noqa: BLE001
        return None
    return set(os.path.basename(p) for p in have.splitlines())


PURGE = "https://purge.jsdelivr.net/"


def purge(url):
    """Ask jsdelivr to drop its copy. Returns True when it says finished."""
    path = url.split("?")[0].split("cdn.jsdelivr.net/", 1)[-1]
    try:
        with urllib.request.urlopen(PURGE + path, timeout=TIMEOUT) as r:
            return json.loads(r.read().decode("utf-8")).get("status")                 == "finished"
    except Exception:                                      # noqa: BLE001
        return False


def head(url):
    """(status, bytes) for one URL. jsdelivr answers HEAD, so no body."""
    req = urllib.request.Request(url, method="HEAD",
                                 headers={"User-Agent": "nobulous-set/1"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return r.status, int(r.headers.get("Content-Length") or 0)
    except urllib.error.HTTPError as ex:
        return ex.code, 0
    except Exception as ex:                                # noqa: BLE001
        return 0, str(ex)


def local_size(url):
    """How big that file is in this tree, or None if it is not here."""
    name = url.split("?")[0].rsplit("/", 1)[-1]
    for where in ("images", "rules"):
        f = os.path.join(ROOT, where, name)
        if os.path.exists(f):
            return os.path.getsize(f)
    return None


def main():
    quick = "--quick" in sys.argv
    purging = "--purge" in sys.argv
    if not os.path.exists(SAVE):
        print("no %s - run build_mod.py first" % SAVE)
        return 1
    published = untracked() if quick else None
    bad, stale, checked = [], [], 0
    for u in urls():
        name = u.split("?")[0].rsplit("/", 1)[-1]
        if quick and published is not None and name in published:
            continue
        checked += 1
        status, size = head(u)
        if status != 200:
            bad.append((name, status, size))
            print("  %-46s %s" % (name, status))
            continue
        want = local_size(u)
        # A SIZE MATCH IS THE SECOND HALF. A sheet that keeps its filename
        # resolves whether or not the new bytes were pushed, so "200" alone
        # would pass while the table showed last week's cards.
        if want is not None and size and size != want:
            if purging and purge(u):
                status, size = head(u)
                if size == want:
                    print("  %-46s purged, now ok" % name)
                    continue
            stale.append((name, size, want))
            print("  %-46s 200 but %d bytes, local is %d"
                  % (name, size, want))
        else:
            print("  %-46s ok" % name)
    print()
    print("%d URL(s) checked, %d missing, %d serving older bytes"
          % (checked, len(bad), len(stale)))
    if bad or stale:
        if stale and not purging:
            print("Serving older bytes is the CDN's cache, not a missing "
                  "push: re-run with --purge.")
        print("Until this is clean the mod will show blank tiles or last "
              "build's art.")
    return 1 if (bad or stale) else 0


if __name__ == "__main__":
    sys.exit(main())
