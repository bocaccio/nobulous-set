"""Serve playtest/dist with cache headers that tell the truth.

    python serve.py            # http://localhost:8000
    python serve.py 8080

`python -m http.server 8000 -d playtest/dist` sends no Cache-Control at all,
so the browser is free to guess, and it guesses badly for exactly the file
that must never go stale. Every asset the lab loads carries a ?v= token and
may be cached forever - but index.html is what NAMES those tokens, so a
cached copy of it pins a playtester to the old build however many times the
tokens are bumped.

That is not hypothetical. On 2026-10-31 a fresh tab against the plain
http.server was served ?v=dpi300 - several builds behind - and the Imposter
picker simply was not in the page. The symptom is the worst kind: nothing
errors, a feature is just absent, and the obvious reading is that the code
was never written.

So: HTML and catalog.json revalidate every load, and the versioned assets
(the card sheets, the PDFs, the JS and CSS) cache for a year, which is what
their tokens are for. index.html also carries a no-cache meta, but a meta
cannot evict an entry cached before it existed - only the header can, which
is the whole reason this file exists. If a browser is already holding a
stale page from the plain server, one hard reload (Ctrl+Shift+R, or Cmd+Shift+R)
clears it, and this server keeps it from happening again.
"""
import functools
import http.server
import os
import sys

DIST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist")
# Everything else is fingerprinted by a ?v= token in the page that links it.
ALWAYS_FRESH = (".html", ".json")


class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        path = self.path.split("?", 1)[0]
        if path.endswith("/") or path.endswith(ALWAYS_FRESH):
            self.send_header("Cache-Control",
                             "no-cache, no-store, must-revalidate")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
        else:
            self.send_header("Cache-Control", "public, max-age=31536000")
        http.server.SimpleHTTPRequestHandler.end_headers(self)

    def log_message(self, fmt, *args):
        # One line a request is noise when a page pulls fifty sheets; only
        # say something when it is not a plain 200.
        if args and str(args[1]) != "200":
            http.server.SimpleHTTPRequestHandler.log_message(
                self, fmt, *args)


class Server(http.server.ThreadingHTTPServer):
    """Threaded, and that is not a detail.

    The first cut of this file used socketserver.TCPServer, which handles one
    request at a time. `python -m http.server` has used ThreadingHTTPServer
    since Python 3.7, so the server written to replace it was strictly worse
    at the one thing a page full of card sheets needs: a browser opens six
    connections at once, and a single-threaded server that is mid-request -
    or holding a connection a browser opened and never used - accepts none of
    them. The port stays open and listening while every request times out,
    which looks like the machine refusing the lab rather than the server
    being busy.

    daemon_threads so Ctrl+C does not wait on a half-read connection.
    """

    daemon_threads = True
    allow_reuse_address = True


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    handler = functools.partial(Handler, directory=DIST)
    with Server(("", port), handler) as httpd:
        print("playtest lab -> http://localhost:%d" % port)
        print("  %s" % DIST)
        print("  HTML and catalog.json revalidate; versioned assets cache.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nstopped")


if __name__ == "__main__":
    main()
