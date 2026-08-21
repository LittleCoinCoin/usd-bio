#!/usr/bin/env python3
"""
Render conference_assets templates to print-ready PDF at their true page size.

    ./render.py poster-a0-portrait.html
    ./render.py poster-a0-landscape.html out/landscape.pdf
    ./render.py --all

Why this exists instead of `chrome --print-to-pdf`:
that flag IGNORES the CSS `@page { size: ... }` rule and always emits US
Letter (215.9 x 279.4 mm). An A0 poster rendered that way is silently scaled
to a quarter size, and you find out at the print shop. The DevTools Protocol's
Page.printToPDF accepts `preferCSSPageSize`, which honours @page, so we drive
Chrome over CDP instead.

Three gates run on every render. Page geometry alone is NOT sufficient — it
comes from the hard-coded @page literal, so a template whose token layer
failed to load still reports a perfect A0 while being visually destroyed:

    1. token attach  — did tokens.css/components.css actually apply?
    2. font presence — did the display face resolve, or silently fall back?
                       (fallback shifts metrics and can reflow a 2-line
                       billboard to 3)
    3. page geometry — is the PDF a sanctioned canvas?
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import collections
import json
import pathlib
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request

try:
    import websockets
except ImportError:
    sys.exit("render.py needs the 'websockets' package:  pip install websockets")

HERE = pathlib.Path(__file__).resolve().parent

CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    shutil.which("google-chrome") or "",
    shutil.which("chromium") or "",
]

# The only page geometries this design system sanctions, in mm.
SANCTIONED = {
    (841.0, 1189.0): "A0 portrait",
    (1189.0, 841.0): "A0 landscape",
    (338.7, 190.5): "16:9 slide",
}

MM_PER_IN = 25.4
LOAD_TIMEOUT = 30.0


class RenderError(RuntimeError):
    """A single template failed; the batch continues."""


def find_chrome() -> str:
    for c in CHROME_CANDIDATES:
        if c and pathlib.Path(c).is_file():
            return c
    raise RenderError("No Chrome/Chromium found. Set CHROME=/path/to/chrome.")


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def page_size_mm(pdf: pathlib.Path) -> tuple[float, float]:
    # Assumes a Chrome/Skia-produced PDF: single page, uncompressed page dict,
    # so the first /MediaBox is the page box. Not general to all producers.
    m = re.search(rb"/MediaBox\s*\[([^\]]*)\]", pdf.read_bytes())
    if not m:
        raise RenderError("no /MediaBox in output PDF")
    v = [float(x) for x in m.group(1).split()]
    return ((v[2] - v[0]) * MM_PER_IN / 72, (v[3] - v[1]) * MM_PER_IN / 72)


async def cdp_render(ws_url: str, file_url: str) -> tuple[bytes, dict]:
    async with websockets.connect(ws_url, max_size=None) as ws:
        counter = 0
        events: collections.deque = collections.deque()

        async def recv(timeout: float) -> dict:
            return json.loads(await asyncio.wait_for(ws.recv(), timeout=timeout))

        async def call(method: str, params: dict | None = None, timeout: float = 30.0) -> dict:
            nonlocal counter
            counter += 1
            mid = counter
            await ws.send(json.dumps({"id": mid, "method": method, "params": params or {}}))
            deadline = asyncio.get_event_loop().time() + timeout
            while True:
                remaining = deadline - asyncio.get_event_loop().time()
                if remaining <= 0:
                    raise RenderError(f"{method}: timed out")
                msg = await recv(max(remaining, 0.1))
                if msg.get("id") == mid:
                    if "error" in msg:
                        raise RenderError(f"{method}: {msg['error']}")
                    return msg.get("result", {})
                # Buffer events so a loadEventFired arriving mid-call is not
                # swallowed — that race used to hang the loop below forever.
                if "method" in msg:
                    events.append(msg)

        await call("Page.enable")
        await call("Runtime.enable")
        await call("Page.navigate", {"url": file_url})

        # Wait for load, draining anything already buffered by call().
        deadline = asyncio.get_event_loop().time() + LOAD_TIMEOUT
        loaded = any(e.get("method") == "Page.loadEventFired" for e in events)
        while not loaded:
            remaining = deadline - asyncio.get_event_loop().time()
            if remaining <= 0:
                raise RenderError("page never fired load event")
            try:
                msg = await recv(max(remaining, 0.1))
            except asyncio.TimeoutError:
                raise RenderError("page never fired load event")
            loaded = msg.get("method") == "Page.loadEventFired"

        # Deterministic font wait instead of a blind sleep.
        await call(
            "Runtime.evaluate",
            {"expression": "document.fonts.ready.then(() => true)", "awaitPromise": True},
        )

        probe = """(() => {
          const cs = getComputedStyle(document.body);
          const tokenOk = cs.getPropertyValue('--ink').trim() !== '';
          // components.css declares no tokens (it is behaviour, not
          // vocabulary), so probe an actual component RULE instead. .qr
          // exists on all three surfaces and only components.css rounds it.
          const qr = document.querySelector('.qr');
          const compOk = !!qr && parseFloat(getComputedStyle(qr).borderRadius) > 0;
          const h = document.querySelector('.takeaway, .assertion');
          const fam = h ? getComputedStyle(h).fontFamily : '';
          const want = (fam.split(',')[0] || '').replace(/["']/g, '').trim();
          const fontOk = want ? document.fonts.check('900 120pt "' + want + '"') : false;
          // The config-error host is .sheet, not <body>: toggles live on a
          // wrapper so a published Design component survives being wrapped.
          const sheet = document.querySelector('.sheet') || document.body;
          const err = getComputedStyle(sheet, '::before').content || '';
          return JSON.stringify({
            tokenOk, compOk, fontOk, want,
            configError: err.includes('CONFIG ERROR'),
            lines: h ? Math.round(h.getBoundingClientRect().height /
                     (parseFloat(getComputedStyle(h).lineHeight) || 1)) : 0
          });
        })()"""
        res = await call("Runtime.evaluate", {"expression": probe, "returnByValue": True})
        diag = json.loads(res.get("result", {}).get("value") or "{}")

        pdf = await call(
            "Page.printToPDF",
            {
                "preferCSSPageSize": True,   # the whole point
                "printBackground": True,
                "marginTop": 0, "marginBottom": 0, "marginLeft": 0, "marginRight": 0,
                "transferMode": "ReturnAsBase64",
            },
            timeout=120.0,
        )
        return base64.b64decode(pdf["data"]), diag


def render(src: pathlib.Path, out: pathlib.Path) -> bool:
    chrome = find_chrome()
    port = free_port()
    profile = tempfile.mkdtemp(prefix="confassets-render-")

    proc = subprocess.Popen(
        [
            chrome, "--headless=new",
            f"--remote-debugging-port={port}", f"--user-data-dir={profile}",
            "--no-first-run", "--no-default-browser-check", "--disable-gpu",
            "--allow-file-access-from-files", "--hide-scrollbars", "about:blank",
        ],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    try:
        ws_url = None
        for _ in range(150):  # ~15s
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/list", timeout=0.5) as r:
                    pages = [t for t in json.load(r)
                             if t.get("type") == "page" and t.get("webSocketDebuggerUrl")]
                if pages:
                    ws_url = pages[0]["webSocketDebuggerUrl"]
                    break
            except Exception:
                pass
            time.sleep(0.1)
        if not ws_url:
            raise RenderError("Chrome did not expose a page debugging target")

        pdf, diag = asyncio.run(cdp_render(ws_url, src.as_uri()))
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
        shutil.rmtree(profile, ignore_errors=True)

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(pdf)

    w, h = page_size_mm(out)
    canvas = next((n for (kw, kh), n in SANCTIONED.items()
                   if abs(w - kw) < 2 and abs(h - kh) < 2), None)

    problems = []
    if not canvas:
        problems.append(f"UNSANCTIONED CANVAS {w:.1f}x{h:.1f}mm")
    if not diag.get("tokenOk"):
        problems.append("tokens.css did not apply")
    if not diag.get("compOk"):
        problems.append("components.css did not apply")
    if not diag.get("fontOk"):
        problems.append(f"font fell back (wanted {diag.get('want') or '?'}) — metrics shifted")
    if diag.get("configError"):
        problems.append("invalid data-take")
    if diag.get("lines", 0) > 2:
        problems.append(f"headline wrapped to {diag['lines']} lines (max 2)")

    status = "ok" if not problems else "FAIL"
    print(f"  {src.name:28s} -> {out.name:26s} {w:7.1f}x{h:7.1f}mm  {canvas or '?':13s} {status}")
    for p in problems:
        print(f"      ! {p}")
    return not problems


def is_template(p: pathlib.Path) -> bool:
    """Templates self-identify with an @dsCard marker in their first lines."""
    try:
        with p.open(encoding="utf-8") as f:
            return any("@dsCard" in next(f, "") for _ in range(3))
    except OSError:
        return False


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src", nargs="?", help="template .html")
    ap.add_argument("out", nargs="?", help="output .pdf")
    ap.add_argument("--all", action="store_true", help="render every @dsCard template here")
    a = ap.parse_args()

    if a.all:
        if a.out or a.src:
            ap.error("--all takes no positional arguments")
        srcs = sorted(p for p in HERE.glob("*.html") if is_template(p))
        if not srcs:
            ap.error("no @dsCard templates found")
    elif a.src:
        p = pathlib.Path(a.src)
        srcs = [(p if p.is_file() else HERE / a.src).resolve()]
    else:
        ap.error("give a template, or --all")

    ok = True
    for s in srcs:
        if not s.is_file():
            print(f"  missing: {s}", file=sys.stderr)
            ok = False
            continue
        out = pathlib.Path(a.out) if (a.out and not a.all) else HERE / "out" / f"{s.stem}.pdf"
        try:
            ok &= render(s, out)
        except RenderError as e:
            print(f"  {s.name:28s} -> FAILED: {e}", file=sys.stderr)
            ok = False
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
