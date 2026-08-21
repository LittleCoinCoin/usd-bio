#!/usr/bin/env python3
"""
Build self-contained copies of the templates for publishing to Claude Design.

    ./sync.py            -> writes dist/
    ./sync.py --check    -> verifies dist/ is current, writes nothing (exit 1 if stale)

WHY THIS EXISTS
A Claude Design canvas component is ONE self-contained file. The templates
link tokens.css and components.css relatively, which is correct for local
work and single-source-of-truth — but a published component whose <link>
404s renders as an unstyled skeleton: every var() resolves to nothing, the
120pt takeaway collapses, colours vanish, the grid dies. Only the @page
literal survives, so the geometry check would still pass while the poster is
destroyed.

So we do not choose between "one source of truth" and "self-contained file".
The CSS stays in one place and is INLINED at publish time.

Properties that matter:
  * idempotent — the fenced <style data-inlined> block is replaced, not
    appended, so re-syncing any number of times is safe
  * hashed — each block records the sha256 of its source, so --check can
    tell you dist/ is stale without diffing whole files
  * @dsCard first — the Design System pane indexes cards from the FIRST
    line, and locally that line has to be <!DOCTYPE html>. dist/ drops the
    doctype (the platform supplies its own wrapper) and promotes @dsCard.

The toggles live on a .sheet wrapper rather than <body> precisely so the
markup survives being wrapped by the platform.
"""

from __future__ import annotations

import argparse
import hashlib
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
DIST = HERE / "dist"
SHEETS = ["tokens.css", "components.css"]

FENCE_RE = re.compile(
    r'<style data-inlined="[^"]*"[^>]*>.*?</style>\n?', re.S)
LINK_RE = re.compile(
    r'[ \t]*<link rel="stylesheet" href="(tokens|components)\.css">\n')


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def build(src: pathlib.Path) -> str:
    html = src.read_text(encoding="utf-8")

    # Strip any previous inline fence so this is a replace, not an append.
    html = FENCE_RE.sub("", html)

    blocks = []
    for name in SHEETS:
        css = (HERE / name).read_text(encoding="utf-8")
        blocks.append(
            f'<style data-inlined="{name}" data-hash="sha256:{sha(css)}">\n'
            f"/* inlined by sync.py — edit {name}, not this copy */\n"
            f"{css}\n</style>"
        )
    inlined = "\n".join(blocks)

    # Replace the first <link> with the inlined blocks; drop the rest.
    if LINK_RE.search(html):
        html = LINK_RE.sub(lambda m, seen=[]: (seen.append(1) or "") if seen else inlined + "\n", html, count=1)
        html = LINK_RE.sub("", html)
    else:
        html = html.replace("<style>", inlined + "\n<style>", 1)

    # Promote @dsCard to the first line; the platform supplies the doctype.
    html = html.replace("<!DOCTYPE html>\n", "", 1)
    return html


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true",
                    help="verify dist/ is current without writing")
    a = ap.parse_args()

    srcs = sorted(p for p in HERE.glob("*.html")
                  if "@dsCard" in p.read_text(encoding="utf-8")[:400])
    if not srcs:
        sys.exit("no @dsCard templates found")

    DIST.mkdir(exist_ok=True)
    stale = []
    for s in srcs:
        built = build(s)
        out = DIST / s.name
        current = out.read_text(encoding="utf-8") if out.exists() else None
        if current == built:
            print(f"  {s.name:28s} up to date")
            continue
        stale.append(s.name)
        if a.check:
            print(f"  {s.name:28s} STALE")
        else:
            out.write_text(built, encoding="utf-8")
            first = built.splitlines()[0] if built else ""
            ok = "@dsCard" in first
            print(f"  {s.name:28s} -> dist/{s.name}   "
                  f"{len(built)//1024}KB  dsCard-first={'yes' if ok else 'NO'}")

    if a.check and stale:
        print(f"\ndist/ is stale ({', '.join(stale)}). Run ./sync.py", file=sys.stderr)
        return 1
    if not a.check:
        print(f"\ndist/ ready. Publish it with /design-sync (point it at {DIST}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
