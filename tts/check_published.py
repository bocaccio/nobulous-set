"""Does every URL the mod bakes in actually resolve?

    python3 check_published.py             # every image and rulebook
    python3 check_published.py --quick     # only the ones git says are new
    python3 check_published.py --purge     # ...and clear STALE bytes too
    python3 check_published.py --no-purge  # read-only: change nothing

Run it after pushing and BEFORE loading the mod in Tabletop Simulator.

IT REPAIRS A MISS BY ITSELF, since 2026-11-16, and that is not what --purge
is for. jsdelivr caches 404s, so a file asked for seconds after the push can
be cached MISSING for the rest of the session; the cure is to purge that one
path and ask again, which this now does without being told. A cached miss is
never the right answer about a file that is sitting in the tree, so there is
nothing to opt into. --purge still gates the other repair, where the CDN
answers 200 with the WRONG bytes, because that can also mean you forgot to
push and purging would hide it for a pass.

AND A HEAD IS NOT THE LAST WORD. Measured 2026-11-16 on three freshly
pushed overlays: the same URL answered GET 200 with the right
Content-Length while HEAD answered 503, two calls a minute apart disagreed
with each other, and this script read "1 missing" in the same minute a curl
read three 404s - jsdelivr's answer is per-edge and per-method while it is
pulling a file from origin. So a non-200 HEAD is re-asked with a GET, which
is what TTS will do, and a GET returning the local byte count is the only
thing counted as proof.

A 404 IS TWO FAULTS WITH DIFFERENT CURES, so it asks GitHub which one it is.
raw.githubusercontent.com is the authority jsdelivr fetches FROM: if it
serves the path at that ref the miss is a cache and purging clears it, and
if it does not then the file was never pushed and no amount of purging will
help. The report says which.

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
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SAVE = os.path.join(HERE, "NobulousSet.json")
TIMEOUT = 30
# After a purge, how many times to ask again and how long to wait between.
# A purge is answered at once but the next fetch can take minutes: jsdelivr
# pulls the file from origin while answering 503, and the biggest overlay in
# this set (1.6 MB) took three passes on 2026-11-16. Four tries over a
# minute covers the usual case without making a clean run slow; a file still
# 503 after that is being fetched and the next run will find it.
RETRIES = 4
BACKOFF = 15


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
GH_URL = re.compile(r"https://cdn\.jsdelivr\.net/gh/"
                    r"([^@/]+)/([^@/]+)@([^/]+)/(.+)")


def purge(url):
    """Ask jsdelivr to drop its copy. Returns True when it says finished."""
    path = url.split("?")[0].split("cdn.jsdelivr.net/", 1)[-1]
    try:
        with urllib.request.urlopen(PURGE + path, timeout=TIMEOUT) as r:
            body = json.loads(r.read().decode("utf-8"))
            return body.get("status") == "finished"
    except Exception:                                      # noqa: BLE001
        return False


def ask(url, method="HEAD"):
    """(status, bytes) for one URL, by Content-Length and not by body.

    A GET returns as soon as the headers are in, so this costs the same as
    a HEAD and is believed where a HEAD is not - see the header.
    """
    req = urllib.request.Request(url, method=method,
                                 headers={"User-Agent": "nobulous-set/1"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return r.status, int(r.headers.get("Content-Length") or 0)
    except urllib.error.HTTPError as ex:
        return ex.code, 0
    except Exception as ex:                                # noqa: BLE001
        return 0, str(ex)


def head(url):
    """(status, bytes) from a HEAD. The cheap first question."""
    return ask(url, "HEAD")


def get(url):
    """(status, bytes) from a GET. The one TTS will ask."""
    return ask(url, "GET")


def on_github(url):
    """(status, bytes) for the same path on raw.githubusercontent.

    None when the URL is not a jsdelivr /gh/ one, so a rulebook served from
    anywhere else is simply not second-guessed.
    """
    m = GH_URL.match(url.split("?")[0])
    if not m:
        return None
    return get("https://raw.githubusercontent.com/%s/%s/%s/%s" % m.groups())


def restore(url, want):
    """Clear a cached miss and ask again. (status, bytes, one line why).

    The line is for the report: what was wrong, and whether this fixed it.

    IT PURGES ONCE AND THEN ONLY ASKS, deliberately. A purge drops the
    entry jsdelivr is filling, so purging again while a pull is in flight
    appears to restart it: on 2026-11-16 the largest overlay in the set
    (1.6 MB) was purged by hand three times over forty minutes and never
    finished, the two files purged once each landed, and the third served
    200 at its exact byte count five minutes after the purging stopped.
    That is an observation and not a documented rule, which is exactly why
    the retry loop asks rather than purges - the cheap behaviour is also
    the safe one.
    """
    gh = on_github(url)
    if gh is not None and gh[0] != 200:
        return (404, 0, "and GitHub does not serve it either (%s) - "
                        "NOT PUSHED, purging cannot help" % gh[0])
    if not purge(url):
        return 404, 0, "and the purge API would not take it"
    status, size = 0, 0
    for _ in range(RETRIES):
        time.sleep(BACKOFF)
        status, size = get(url)
        if status == 200 and (want is None or size == want):
            return status, size, "purged, now ok"
    if status == 200:
        return status, size, ("purged, now 200 but %s bytes, local is %d"
                              % (size, want))
    return status, size, ("purged, still %s after %d tries - jsdelivr is "
                          "pulling it from origin, so run this again"
                          % (status, RETRIES))


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
    repairing = "--no-purge" not in sys.argv
    if not os.path.exists(SAVE):
        print("no %s - run build_mod.py first" % SAVE)
        return 1
    published = untracked() if quick else None
    bad, stale, checked, mended = [], [], 0, 0
    for u in urls():
        name = u.split("?")[0].rsplit("/", 1)[-1]
        if quick and published is not None and name in published:
            continue
        checked += 1
        note = "ok"
        status, size = head(u)
        if status != 200:
            # ASK AGAIN THE WAY TTS WILL. A HEAD answers 503 for a file a
            # GET serves, and a timeout here reads as 0 rather than as a
            # status, so neither is evidence of a missing file on its own.
            first, (status, size) = status, get(u)
            if status == 200:
                # Worth printing: the CDN is mid-pull on this path, which
                # is why a pass that reads clean can be followed by a curl
                # that 404s and neither one is lying.
                note = "ok (HEAD said %s)" % first
        if status != 200 and repairing:
            status, size, note = restore(u, local_size(u))
            if status == 200:
                mended += 1
        if status != 200:
            bad.append((name, status, size))
            print("  %-46s %s%s"
                  % (name, status, "" if note == "ok" else " " + note))
            continue
        want = local_size(u)
        # A SIZE MATCH IS THE SECOND HALF. A sheet that keeps its filename
        # resolves whether or not the new bytes were pushed, so "200" alone
        # would pass while the table showed last week's cards.
        if want is not None and size and size != want:
            if purging and purge(u):
                status, size = get(u)
                if size == want:
                    print("  %-46s purged, now ok" % name)
                    mended += 1
                    continue
            stale.append((name, size, want))
            print("  %-46s 200 but %d bytes, local is %d"
                  % (name, size, want))
        else:
            print("  %-46s %s" % (name, note))
    print()
    print("%d URL(s) checked, %d missing, %d serving older bytes"
          % (checked, len(bad), len(stale)))
    if mended:
        print("%d repaired here: a purge and a re-ask, which is the CDN's "
              "cache and not your push." % mended)
    if bad or stale:
        if stale and not purging:
            print("Serving older bytes is the CDN's cache, not a missing "
                  "push: re-run with --purge.")
        if bad and not repairing:
            print("Missing ones were NOT repaired, because --no-purge: "
                  "re-run without it to purge and re-ask.")
        print("Until this is clean the mod will show blank tiles or last "
              "build's art.")
    return 1 if (bad or stale) else 0


if __name__ == "__main__":
    sys.exit(main())
