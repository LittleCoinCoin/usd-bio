#!/usr/bin/env python3
"""
Recover DesignSync get_file payloads byte-exactly from the Claude Code session transcript.

    ./_pull.py --list                    what is recoverable
    ./_pull.py --out _pristine           write every payload under _pristine/
    ./_pull.py --diff                    diff recovered originals against what is on disk

WHY THIS EXISTS
`DesignSync.get_file` returns a file's contents into the assistant's context. Writing that
to disk by re-emitting it costs output tokens proportional to the file and risks transcription
errors — on a 41KB studio plate that is pure waste.

But the harness already persists every tool result verbatim in the session transcript
(~/.claude/projects/<slug>/<session>.jsonl). So the correct method is:

    fetch once  ->  payload lands in the transcript  ->  extract to disk with this script

Nothing is retyped, and the bytes are exactly what the server sent.

The transcript is JSONL with tool results embedded as escaped strings, so this brace-matches
the `{"method":"get_file",...}` object out of each line rather than assuming a fixed shape.
"""

from __future__ import annotations

import argparse
import difflib
import json
import os
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
# studio/ -> conference_assets/ ; payload paths are relative to the design project root,
# whose `studio/` maps onto this directory.
PROJECT_ROOT = HERE.parent

START = re.compile(r'\{"method":"get_file","path":"(?:[^"\\]|\\.)*?","content":')


def transcripts() -> list[pathlib.Path]:
    slug = os.environ.get("CLAUDE_PROJECT_SLUG")
    base = pathlib.Path.home() / ".claude" / "projects"
    if slug:
        dirs = [base / slug]
    else:
        cwd = str(PROJECT_ROOT).replace("/", "-")
        dirs = [d for d in base.glob("*") if d.is_dir() and cwd.startswith(str(d.name)[:40])] or list(base.glob("*"))
    out: list[pathlib.Path] = []
    for d in dirs:
        out.extend(d.glob("*.jsonl"))
    return sorted(out, key=lambda p: p.stat().st_mtime, reverse=True)


def extract(paths: list[pathlib.Path]) -> dict[str, str]:
    """Later transcripts win, so a re-fetched file supersedes an earlier copy."""
    found: dict[str, str] = {}
    for tp in reversed(paths):          # oldest first; newest overwrites
        try:
            text = tp.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for line in text.splitlines():
            if "get_file" not in line:
                continue
            for m in START.finditer(line):
                blob = brace_match(line, m.start())
                if not blob:
                    continue
                try:
                    o = json.loads(blob)
                except json.JSONDecodeError:
                    continue
                if "path" in o and "content" in o:
                    found[o["path"]] = o["content"]
    return found


def brace_match(s: str, start: int) -> str | None:
    depth = 0
    instr = False
    esc = False
    for i in range(start, len(s)):
        c = s[i]
        if esc:
            esc = False
        elif c == "\\":
            esc = True
        elif c == '"':
            instr = not instr
        elif not instr:
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    return s[start : i + 1]
    return None


# The design project's README.md is built from PROJECT_README.md locally; the repo's own
# README.md at the same relative path is the canon index and must never be overwritten by it.
PATH_MAP = {"README.md": "PROJECT_README.md"}


def local_path(project_path: str) -> pathlib.Path:
    return PROJECT_ROOT / PATH_MAP.get(project_path, project_path)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--out", help="write every recovered payload under this directory")
    ap.add_argument("--diff", action="store_true", help="compare recovered originals with files on disk")
    ap.add_argument("--place", action="store_true",
                    help="write recovered payloads to their real location, but ONLY where no file exists yet")
    a = ap.parse_args()

    tps = transcripts()
    if not tps:
        sys.exit("no session transcripts found under ~/.claude/projects")
    found = extract(tps)
    if not found:
        sys.exit("no get_file payloads in any transcript — fetch the files first")

    if a.list or not (a.out or a.diff or a.place):
        print(f"{len(found)} payloads recoverable from {len(tps)} transcript(s):\n")
        for p, c in sorted(found.items()):
            dest = local_path(p)
            mark = "on disk" if dest.exists() else "MISSING"
            print(f"  {len(c):8d} chars  {p:52s} {mark}")
        return 0

    if a.out:
        root = HERE / a.out if not os.path.isabs(a.out) else pathlib.Path(a.out)
        for p, c in sorted(found.items()):
            dest = root / p
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(c, encoding="utf-8")
            print(f"  wrote {dest.relative_to(root)}")
        print(f"\n{len(found)} originals under {root}")

    if a.place:
        n = 0
        for p, c in sorted(found.items()):
            dest = local_path(p)
            if dest.exists():
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(c, encoding="utf-8")
            print(f"  placed {p}")
            n += 1
        print(f"\n{n} file(s) placed; existing files left untouched")

    if a.diff:
        clean = drift = missing = 0
        for p, c in sorted(found.items()):
            dest = local_path(p)
            if not dest.exists():
                print(f"  MISSING  {p}")
                missing += 1
                continue
            cur = dest.read_text(encoding="utf-8")
            if cur == c:
                print(f"  identical {p}")
                clean += 1
            else:
                d = list(difflib.unified_diff(c.splitlines(), cur.splitlines(),
                                              "online", "local", lineterm="", n=0))
                adds = sum(1 for x in d if x.startswith("+") and not x.startswith("+++"))
                dels = sum(1 for x in d if x.startswith("-") and not x.startswith("---"))
                print(f"  DRIFT     {p}  (+{adds} / -{dels} lines vs online)")
                drift += 1
        print(f"\n{clean} identical · {drift} locally modified · {missing} not yet on disk")
    return 0


if __name__ == "__main__":
    sys.exit(main())
