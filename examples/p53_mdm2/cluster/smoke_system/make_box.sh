#!/bin/bash
# ============================================================================
# make_box.sh — build a minimal SPC water box, from inside the container.
#
# Runs `gmx solvate` against GROMACS' own bundled spc216.gro, so this needs no
# network, no repo data files, and no external structure. That is the point:
# the smoke test must not depend on anything that could be missing on a cluster.
#
# USAGE (inside the container):
#   bash make_box.sh <template-dir> <work-dir> [box-nm]
#     template-dir : holds topol.top / min.mdp / md.mdp (read-only)
#     work-dir     : where conf.gro and the mutable topol.top copy are written
#     box-nm       : cubic box edge in nm (default 3.0 -> ~900 waters)
#
# WHY IT COPIES topol.top: `gmx solvate -p` REWRITES the molecule count in
# place. Pointing it at the committed template would mutate a tracked file on
# every run and make the repo dirty from a cluster job. The copy is the mutable
# one; the template stays pristine.
#
# Box size note: 3.0 nm is a compromise. Small enough to run in seconds on a
# shared node, large enough that the GPU nonbonded kernels actually engage and
# get logged. GROMACS may still warn the system is small for a GPU — that
# warning is expected and is not a failure.
# ============================================================================
set -euo pipefail

TEMPLATE_DIR="${1:?usage: make_box.sh <template-dir> <work-dir> [box-nm]}"
WORK_DIR="${2:?usage: make_box.sh <template-dir> <work-dir> [box-nm]}"
BOX="${3:-3.0}"

GMX="${GMX:-/opt/gromacs/bin/gmx}"

for f in topol.top min.mdp md.mdp; do
    [ -f "$TEMPLATE_DIR/$f" ] || { echo "FATAL: missing template $TEMPLATE_DIR/$f" >&2; exit 2; }
done

mkdir -p "$WORK_DIR"
cp "$TEMPLATE_DIR/topol.top" "$TEMPLATE_DIR/min.mdp" "$TEMPLATE_DIR/md.mdp" "$WORK_DIR/"

cd "$WORK_DIR"

echo "=== make_box.sh ==="
echo "box_nm: $BOX"
echo "gmx: $GMX"

# -cs with a bare name resolves against GROMACS' own share/gromacs/top.
"$GMX" solvate -cs spc216.gro -box "$BOX" "$BOX" "$BOX" -o conf.gro -p topol.top

# Fail loudly rather than handing grompp an empty system: a zero count here
# means solvate silently placed nothing, which would otherwise surface as a
# confusing grompp error much later.
#
# SUM every SOL line rather than taking the first. Reading only the first is how
# job 31 reported 0 while solvate had actually placed 884: `solvate -p` APPENDS
# a molecule line instead of rewriting one, so any pre-existing entry stays
# ahead of the real count. The template no longer carries a placeholder, but
# summing is the defensive read either way.
SOL_COUNT="$(awk '/^\[ *molecules *\]/{f=1;next} f && /^[[:space:]]*SOL[[:space:]]/{n+=$2} END{print n+0}' topol.top)"
SOL_LINES="$(awk '/^\[ *molecules *\]/{f=1;next} f && /^[[:space:]]*SOL[[:space:]]/{n++} END{print n+0}' topol.top)"
echo "solvated_molecules: $SOL_COUNT"
echo "sol_lines: $SOL_LINES"
if [ "$SOL_COUNT" -le 0 ]; then
    echo "FATAL: solvate placed no water (summed SOL count = $SOL_COUNT)" >&2
    exit 1
fi
# More than one SOL line means a placeholder leaked back into the template.
# grompp segfaults on a zero-count molblock, so refuse rather than pass it on.
if [ "$SOL_LINES" -ne 1 ]; then
    echo "FATAL: expected exactly 1 SOL line in [ molecules ], found $SOL_LINES." >&2
    echo "       A placeholder in topol.top will produce a zero-molecule block and" >&2
    echo "       segfault grompp. Remove it from the template." >&2
    sed -n '/^\[ *molecules *\]/,$p' topol.top >&2
    exit 1
fi

ATOMS="$(head -2 conf.gro | tail -1 | tr -d ' ')"
echo "atoms_in_conf: $ATOMS"
echo "RESULT: box built OK"
