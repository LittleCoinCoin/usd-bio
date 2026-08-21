#!/usr/bin/env python3
"""
make_poster_figures.py -- shared harness for the PRIMe Poster P-14 figures.

THIS FILE IS THE HARNESS ONLY. It defines the registry, CLI, theme
resolution, provenance printer, and matplotlib figure factory that the six
poster figures plug into. It intentionally implements no figure content of
its own beyond ``nothing``, a no-op placeholder registered purely so the CLI
is exercisable (``--list`` / ``--only`` / ``--theme``) before the real figure
functions exist.

Canvas contract (measured; see examples/p53_mdm2/figures/README.md for the
full record -- do not re-derive these numbers):
    slot:      214.94 x 64.48 mm   (ratio 3.3336 : 1)
    raster:    2560 x 768 px for any figure saved as a raster
    type floor: 22 pt minimum anywhere in any figure (enforced in code below)
    SVG background: transparent -- the poster tile behind a figure is the
        theme's ``--field`` token, which changes with theme, so a painted
        background would show as an opaque slab that does not track theme
        switches.
    monospace: DejaVu Sans Mono (matplotlib-bundled). The canon calls for
        JetBrains Mono, but it is not installed on this machine and is not
        among matplotlib's resolvable families, so every figure that needs a
        monospace face uses DejaVu Sans Mono instead. This is a deliberate,
        recorded substitution, not an oversight.

Usage:
    PYTHONPATH="$PYTHONPATH:<repo-root>/examples" \\
        /path/to/forOUSD/bin/python3 make_poster_figures.py --list
    ... make_poster_figures.py --only nothing --theme canon
    ... make_poster_figures.py --only mod-text --only mod-usd --theme slate

Adding a real figure (for the agents who own the other six):
    from make_poster_figures import figure, make_figure, save_figure, \\
        type_pt, prov, Theme

    @figure("mod-text", ext="svg")
    def build_mod_text(theme: Theme, out_dir: str) -> str:
        fig, ax = make_figure()
        size = type_pt(prov(24, note="caption size, poster type scale"))
        ax.text(0.5, 0.5, "...", fontsize=size, color=theme.ink)
        out_path = os.path.join(out_dir, "mod-text.svg")
        save_figure(fig, out_path, ext="svg")
        return out_path
"""

from __future__ import annotations

import argparse
import dataclasses
import inspect
import json
import os
import sys
from typing import Callable, Optional

import matplotlib

# Headless-safe backend. Must be set before pyplot is imported anywhere,
# including inside figure modules that import this harness first.
matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402  (after matplotlib.use)

# ---------------------------------------------------------------------------
# Canvas contract -- measured values, not re-derived. See figures/README.md.
#
# CANVAS_MM[1] (height) is PIXEL-DERIVED, not the raw measured 64.48 mm.
# Two of the six poster figures are rendered by usdrecord at exactly
# RASTER_WIDTH_PX x RASTER_HEIGHT_PX (integers, by construction -- usdrecord
# cannot emit a fractional-pixel height either). If matplotlib's figures were
# sized from the raw 64.48 mm instead, float rounding at the save boundary
# (2.538583...in * 302.5217...dpi = 767.98, which floors to 767 px) would
# make the two families of figures land on different pixel heights, and a
# poster-side ``fit="contain"`` scale-to-tile would then rescale them by two
# different factors -- silently breaking the cross-figure type-size parity
# the 22pt floor exists to guarantee. So: derive the figure height from the
# integer RASTER_HEIGHT_PX instead of from the mm measurement. The resulting
# height is 64.4823 mm against the measured 64.48 mm -- a 0.0023 mm
# difference, four orders of magnitude below anything printable -- while the
# raster save now lands on RASTER_HEIGHT_PX exactly, by construction rather
# than by luck. Width is unaffected: RASTER_WIDTH_PX / _DPI is identically
# CANVAS_MM[0] / 25.4, so the width stays exactly the measured 214.94 mm.
# ---------------------------------------------------------------------------
CANVAS_MM = (214.94, 64.48)          # (width, height) of the poster slot, AS MEASURED
CANVAS_RATIO = 3.3336                # width : height, as measured
RASTER_WIDTH_PX = 2560
RASTER_HEIGHT_PX = 768
MIN_TYPE_PT = 22                     # hard floor, enforced in type_pt()

# DPI chosen so that CANVAS_MM[0] (in inches) times dpi lands exactly on
# RASTER_WIDTH_PX -- i.e. a raster save at this dpi is exactly 2560 px wide.
_DPI = RASTER_WIDTH_PX / (CANVAS_MM[0] / 25.4)
# Figure size derived FROM the integer pixel targets (not from CANVAS_MM),
# so width_in * dpi == RASTER_WIDTH_PX and height_in * dpi == RASTER_HEIGHT_PX
# exactly, by construction, rather than approximately, by luck.
_FIGSIZE_IN = (RASTER_WIDTH_PX / _DPI, RASTER_HEIGHT_PX / _DPI)

# Deliberate substitution for the canon's --font-mono (JetBrains Mono is not
# installed on this machine and is not a matplotlib-resolvable family).
MONO_FONT = "DejaVu Sans Mono"

_HERE = os.path.dirname(os.path.abspath(__file__))
THEMES_PATH = os.path.join(_HERE, "themes.json")


# ---------------------------------------------------------------------------
# Deterministic-SVG matplotlib configuration
# ---------------------------------------------------------------------------
def _configure_matplotlib() -> None:
    """Apply the rcParams that make figure output deterministic and portable.

    - svg.fonttype = 'path': text becomes outline paths in the SVG, so a
      print shop that lacks a font cannot silently substitute one.
    - svg.hashsalt: matplotlib's SVG backend hashes glyph clip-path ids with
      a random salt per process by default, so the same figure would produce
      byte-different SVGs on every run. Pinning the salt makes those ids
      reproducible.
    - font.monospace: resolves any 'monospace' family request to the
      matplotlib-bundled DejaVu Sans Mono (see MONO_FONT above).
    """
    matplotlib.rcParams["svg.fonttype"] = "path"
    matplotlib.rcParams["svg.hashsalt"] = "usd-bio-p53-mdm2-poster-figures"
    matplotlib.rcParams["font.monospace"] = [MONO_FONT]
    matplotlib.rcParams["font.family"] = "sans-serif"


_configure_matplotlib()


# ---------------------------------------------------------------------------
# Theme resolution
# ---------------------------------------------------------------------------
@dataclasses.dataclass(frozen=True)
class Theme:
    """One resolved poster theme -- the subset of roles figures read directly.

    ``panel``, ``panel_ink`` and ``accent_on_panel`` are also carried (some
    figures draw on a panel background rather than the field), but the
    six names the harness contract calls out explicitly are exposed as the
    primary attributes below.
    """

    name: str
    paper: str
    field: str
    ink: str
    ink_soft: str
    panel: str
    panel_ink: str
    accent: str
    accent_on_panel: str
    rule: str


def load_themes(path: str = THEMES_PATH) -> dict:
    """Load and return the raw themes.json document."""
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def available_themes(path: str = THEMES_PATH) -> list:
    """Return the list of theme names defined in themes.json."""
    return sorted(load_themes(path)["themes"].keys())


def resolve_theme(name: str, path: str = THEMES_PATH) -> Theme:
    """Resolve a theme name to a :class:`Theme` of the roles figures need.

    Raises:
        KeyError: if ``name`` is not a theme defined in themes.json. The
            message lists the themes that ARE defined.
    """
    doc = load_themes(path)
    themes = doc["themes"]
    if name not in themes:
        raise KeyError(
            f"unknown theme '{name}'; available themes: "
            f"{', '.join(sorted(themes.keys()))}"
        )
    roles = themes[name]
    return Theme(
        name=name,
        paper=roles["paper"],
        field=roles["field"],
        ink=roles["ink"],
        ink_soft=roles["ink-soft"],
        panel=roles["panel"],
        panel_ink=roles["panel-ink"],
        accent=roles["accent"],
        accent_on_panel=roles["accent-on-panel"],
        rule=roles["rule"],
    )


# ---------------------------------------------------------------------------
# Provenance printer
# ---------------------------------------------------------------------------
# Every value a figure function reads (a measurement, a constant, a USD
# attribute) should be wrapped in prov() so a reviewer can see exactly where
# every number in the poster came from. The log is per-figure: run_figure()
# clears it before calling the figure function and prints+clears it after.
_PROVENANCE_LOG: list = []


def prov(value, source: Optional[str] = None, note: str = ""):
    """Record *value*'s provenance and return *value* unchanged.

    Call this at the point a figure function reads a number, string, or
    other datum it did not just invent, e.g.:

        width = prov(214.94, "figures/README.md", "measured poster slot mm")
        s = prov(stage.GetPrimAtPath(p).GetAttribute("bio:ddgKcalPerMol").Get(),
                 f"output/p53_mdm2_topology.usda:<{p}>.bio:ddgKcalPerMol")

    If *source* is omitted, the caller's own file:line is captured
    automatically via the call stack -- convenient for constants defined
    inline in the figure module itself.

    Returns:
        *value*, unchanged, so ``prov(...)`` can wrap an expression in place.
    """
    if source is None:
        caller = inspect.stack()[1]
        rel = os.path.relpath(caller.filename)
        source = f"{rel}:{caller.lineno}"
    _PROVENANCE_LOG.append((value, source, note))
    return value


def usd_source(layer_path: str, prim_path: str, attr_name: str) -> str:
    """Build a provenance source string for a USD attribute read.

    Produces the ``file:<prim path>.<attr>`` form the harness contract asks
    for, e.g. ``usd_source("output/p53_mdm2_topology.usda", "/p53_MDM2_complex/atom_12",
    "bio:element")`` -> ``"output/p53_mdm2_topology.usda:</p53_MDM2_complex/atom_12>.bio:element"``.
    """
    return f"{layer_path}:<{prim_path}>.{attr_name}"


def clear_provenance() -> None:
    """Discard any recorded provenance entries. Called between figure runs."""
    _PROVENANCE_LOG.clear()


def print_provenance_block(figure_name: str) -> None:
    """Print every provenance entry recorded since the last clear.

    Format per line: ``value <- source (note)``. Printing an empty block
    (e.g. for the ``nothing`` placeholder, which reads nothing) is fine and
    expected.
    """
    print(f"--- provenance: {figure_name} ---")
    if not _PROVENANCE_LOG:
        print("  (no provenance recorded)")
    for value, source, note in _PROVENANCE_LOG:
        suffix = f" ({note})" if note else ""
        print(f"  {value!r} <- {source}{suffix}")


# ---------------------------------------------------------------------------
# Type-size floor
# ---------------------------------------------------------------------------
def type_pt(size_pt: float) -> float:
    """Validate a type size given in points at final print size.

    Every figure must specify text sizes through this function (or
    :func:`pt_to_data`, which calls it) rather than passing a raw number to
    matplotlib's ``fontsize=``, so the 22 pt floor cannot be silently
    violated.

    Raises:
        ValueError: if ``size_pt`` is below :data:`MIN_TYPE_PT`. This is a
            hard failure, not a warning -- a figure that cannot meet the
            floor must change its layout, not shrink past the limit.
    """
    if size_pt < MIN_TYPE_PT:
        raise ValueError(
            f"type size {size_pt}pt is below the {MIN_TYPE_PT}pt minimum "
            f"enforced for every poster figure; increase the size or "
            f"redesign the layout instead of going under the floor"
        )
    return size_pt


def pt_to_data(size_pt: float, ax, axis: str = "y") -> float:
    """Convert a point size (validated against the 22pt floor) to data units.

    Useful when a figure needs to size a non-text element (a marker, an
    arrowhead, a bracket) to visually match a given type size. Because
    :func:`make_figure` picks the figure's dpi so that the physical canvas
    (214.94 x 64.48 mm) maps exactly onto the raster contract (2560 x 768 px),
    a matplotlib point size here is a real physical point on the printed
    poster, not an arbitrary on-screen unit.

    Args:
        size_pt: the type size in points at final print size.
        ax: the Axes whose data coordinate system to convert into.
        axis: 'x' or 'y' -- which axis's data scale to use for the
            points-per-data-unit conversion (they can differ if the axes
            are not square).

    Raises:
        ValueError: via :func:`type_pt`, if ``size_pt`` is below the floor.
    """
    type_pt(size_pt)
    fig = ax.figure
    inches = size_pt / 72.0
    px = inches * fig.dpi
    inv = ax.transData.inverted()
    if axis == "y":
        (_, y0), (_, y1) = inv.transform((0, 0)), inv.transform((0, px))
        return abs(y1 - y0)
    elif axis == "x":
        (x0, _), (x1, _) = inv.transform((0, 0)), inv.transform((px, 0))
        return abs(x1 - x0)
    else:
        raise ValueError(f"axis must be 'x' or 'y', got {axis!r}")


# ---------------------------------------------------------------------------
# Matplotlib figure factory
# ---------------------------------------------------------------------------
def make_figure(theme: Optional[Theme] = None):
    """Create a (fig, ax) pair sized to the exact poster canvas.

    - figsize is CANVAS_MM converted to inches (mm / 25.4), so a physical
      point in matplotlib is a physical point on the printed poster.
    - dpi is chosen so a raster save is exactly RASTER_WIDTH_PX wide.
    - the figure and axes patches are made fully transparent, per the
      transparent-SVG-background requirement -- the poster tile behind the
      figure is the theme's `field` token and must show through.

    Args:
        theme: optional; if given, the axes spines/ticks are tinted with
            ``theme.rule`` as a sensible default a figure can override.

    Returns:
        (fig, ax): a single-axes figure filling the whole canvas. Figures
        needing multiple axes should call ``fig.add_axes`` / subplots
        themselves starting from a bare ``fig`` -- use
        ``plt.figure(figsize=_FIGSIZE_IN, dpi=_DPI)`` directly for that case.
    """
    fig = plt.figure(figsize=_FIGSIZE_IN, dpi=_DPI)
    fig.patch.set_alpha(0.0)
    ax = fig.add_axes((0, 0, 1, 1))
    ax.patch.set_alpha(0.0)
    if theme is not None:
        for spine in ax.spines.values():
            spine.set_color(theme.rule)
        ax.tick_params(colors=theme.rule)
    return fig, ax


def save_figure(fig, out_path: str, ext: str = "svg") -> str:
    """Save *fig* to *out_path*, honoring the transparency + determinism
    contract.

    - ext == 'svg': written with a transparent background and no embedded
      timestamp/metadata, so two runs against unchanged inputs produce
      byte-identical files.
    - any raster ext (e.g. 'png'): written at the figure's own dpi
      (set by make_figure() to land on RASTER_WIDTH_PX), also transparent.

    Returns:
        out_path, unchanged, for convenience chaining.
    """
    ext = ext.lower().lstrip(".")
    save_kwargs = dict(transparent=True)
    if ext == "svg":
        # Suppress the SVG backend's default embedded creation date so
        # output is reproducible byte-for-byte across runs.
        save_kwargs["metadata"] = {"Date": None}
    fig.savefig(out_path, format=ext, **save_kwargs)
    return out_path


# ---------------------------------------------------------------------------
# Figure registry
# ---------------------------------------------------------------------------
@dataclasses.dataclass(frozen=True)
class FigureEntry:
    name: str
    ext: str
    fn: Callable


FIGURES: "dict[str, FigureEntry]" = {}


def figure(name: str, ext: str = "svg"):
    """Decorator registering a figure-building function under *name*.

    The decorated function's signature must be
    ``fn(theme: Theme, out_dir: str) -> Optional[str]``, returning the path
    it wrote (or None, for a placeholder that writes nothing).

    Example:
        @figure("mod-text", ext="svg")
        def build_mod_text(theme, out_dir):
            ...
            return out_path
    """

    def _register(fn: Callable) -> Callable:
        if name in FIGURES:
            raise ValueError(f"figure '{name}' is already registered")
        FIGURES[name] = FigureEntry(name=name, ext=ext, fn=fn)
        return fn

    return _register


@figure("nothing", ext="svg")
def build_nothing(theme: Theme, out_dir: str) -> Optional[str]:
    """Placeholder registration. Writes no file.

    Exists solely so the CLI (--list / --only / --theme) is exercisable
    before the six real figure functions are added by other agents. Reads
    nothing, so its provenance block is expected to be empty.
    """
    return None


# ---------------------------------------------------------------------------
# Harness self-check
# ---------------------------------------------------------------------------
def selfcheck(tmp_dir: str) -> bool:
    """Exercise the two properties the harness promises about its own output,
    using a pair of throwaway files it deletes when done:

    1. raster pixel-exactness -- a PNG saved via make_figure()/save_figure()
       must be exactly (RASTER_WIDTH_PX, RASTER_HEIGHT_PX), not off by one in
       either dimension. This is the gate the coordinator's integration
       review found missing: matplotlib's own float rounding at the save
       boundary can otherwise land one pixel short of the contract, which
       would silently disagree with the usdrecord-rendered figures at the
       exact same nominal size.
    2. SVG determinism -- two independent saves of an identical figure must
       be byte-for-byte identical, so re-running the harness against
       unchanged inputs never perturbs a committed SVG's diff.

    Returns:
        True if both checks pass. Prints a line per check either way, and
        prints any failure detail to stderr.
    """
    import hashlib

    from PIL import Image

    ok = True
    theme = resolve_theme("slate")

    # -- 1. raster pixel-exactness ------------------------------------------------
    png_path = os.path.join(tmp_dir, "_selfcheck_raster.png")
    fig, _ax = make_figure(theme=theme)
    save_figure(fig, png_path, ext="png")
    plt.close(fig)
    try:
        with Image.open(png_path) as im:
            size = im.size
    finally:
        os.remove(png_path)
    want = (RASTER_WIDTH_PX, RASTER_HEIGHT_PX)
    if size == want:
        print(f"OK   raster size: PIL reports {size}")
    else:
        print(
            f"FAIL raster size: PIL reports {size}, want {want}",
            file=sys.stderr,
        )
        ok = False

    # -- 2. SVG determinism --------------------------------------------------
    svg_a = os.path.join(tmp_dir, "_selfcheck_a.svg")
    svg_b = os.path.join(tmp_dir, "_selfcheck_b.svg")
    digests = []
    try:
        for path in (svg_a, svg_b):
            fig, ax = make_figure(theme=theme)
            ax.text(
                0.5, 0.5, "selfcheck", fontsize=type_pt(24),
                color=theme.ink, ha="center", va="center",
            )
            save_figure(fig, path, ext="svg")
            plt.close(fig)
            with open(path, "rb") as fh:
                digests.append(hashlib.sha256(fh.read()).hexdigest())
    finally:
        for path in (svg_a, svg_b):
            if os.path.exists(path):
                os.remove(path)
    if digests[0] == digests[1]:
        print(f"OK   svg determinism: sha256={digests[0]}")
    else:
        print(
            f"FAIL svg determinism: {digests[0]} != {digests[1]}",
            file=sys.stderr,
        )
        ok = False

    return ok


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def run_figure(name: str, theme: Theme, out_dir: str) -> Optional[str]:
    """Run one registered figure, printing the canvas/theme header and the
    per-figure provenance block that follows from it."""
    entry = FIGURES[name]
    clear_provenance()
    print(f"\n=== figure: {name} (ext={entry.ext}) ===")
    print(
        f"canvas: {CANVAS_MM[0]:.2f} x {CANVAS_MM[1]:.2f} mm "
        f"({CANVAS_RATIO:.4f}:1)  raster: {RASTER_WIDTH_PX}x{RASTER_HEIGHT_PX}px"
    )
    print(f"theme: {theme.name}  accent={theme.accent}")
    out_path = entry.fn(theme, out_dir)
    print_provenance_block(name)
    if out_path is not None:
        print(f"wrote: {out_path}")
    else:
        print("wrote: (nothing)")
    return out_path


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="make_poster_figures.py",
        description="Shared harness for the PRIMe Poster P-14 figures.",
    )
    parser.add_argument(
        "--only",
        action="append",
        default=None,
        metavar="NAME",
        help="build only this figure; repeatable for several figures",
    )
    parser.add_argument(
        "--theme",
        default="slate",
        metavar="NAME",
        help="theme to resolve from themes.json (default: slate, the "
        "poster's own live default)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="list registered figures and exit",
    )
    parser.add_argument(
        "--out-dir",
        default=os.path.join(_HERE, "output"),
        metavar="DIR",
        help="directory figures are written into (default: figures/output)",
    )
    parser.add_argument(
        "--selfcheck",
        action="store_true",
        help="run the harness self-check (raster pixel-exactness + SVG "
        "determinism) against throwaway files, then exit",
    )
    return parser


def main(argv: Optional[list] = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    if args.selfcheck:
        os.makedirs(args.out_dir, exist_ok=True)
        return 0 if selfcheck(args.out_dir) else 1

    if args.list:
        for name in sorted(FIGURES):
            print(f"{name}\text={FIGURES[name].ext}")
        return 0

    try:
        theme = resolve_theme(args.theme)
    except KeyError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.only:
        unknown = [n for n in args.only if n not in FIGURES]
        if unknown:
            print(
                f"error: unknown figure name(s): {', '.join(unknown)}; "
                f"available: {', '.join(sorted(FIGURES))}",
                file=sys.stderr,
            )
            return 1
        names = list(args.only)
    else:
        names = sorted(FIGURES)

    os.makedirs(args.out_dir, exist_ok=True)
    for name in names:
        run_figure(name, theme, args.out_dir)

    return 0


if __name__ == "__main__":
    sys.exit(main())
