#!/bin/bash
# ============================================================================
# p53_md_run.sh — CONTAINER SIDE of the first p53-MDM2 MD run (1YCR).
#
# Runs INSIDE `singularity exec --nv` (launched by p53_md_submit.sbatch). It
# owns every gmx call; the host script owns devices, binds, tee and sentinel.
#
#   USAGE: bash p53_md_run.sh <deck-dir> <pdb> <work-dir> <ntomp>
#     deck-dir : read-only; holds prep.env + <stage>.mdp, ALL emitted from USD
#                by templates/gromacs_deck.py. This script carries NO physics
#                parameters of its own: the force field, water, box, ions and
#                stage list come from prep.env, every mdrun setting from the
#                .mdp files. Change the USD stage and re-emit, never this file.
#     pdb      : the committed 1YCR crystal structure (read-only)
#     work-dir : this run's own output directory (writable)
#     ntomp    : OpenMP threads, pinned by the caller
#
# PIPELINE: clean PDB -> pdb2gmx -> editconf -> solvate -> grompp+genion ->
#           for each stage in $STAGES: grompp -> mdrun.
#
# DEVICE POLICY: minimisers run `-nb gpu` only — PME on GPU supports only
# dynamical integrators (GROMACS 2025.3 user guide, mdrun-performance "Known
# limitations"), so `-pme gpu` on steep would be a fatal error. Dynamics stages
# run `-nb gpu -pme gpu`. `-update` and `-bonded` are left at mdrun's default.
#
# Writes $WORK/summary.txt as KEY=VALUE lines; the host splices it into the
# machine-parseable SUMMARY block. Step logs end in .txt (repo ignores *.log).
# ============================================================================
set -uo pipefail

DECK="${1:?usage: p53_md_run.sh <deck-dir> <pdb> <work-dir> <ntomp>}"
PDB="${2:?usage}"
WORK="${3:?usage}"
NTOMP="${4:?usage}"
GMX="${GMX:-/opt/gromacs/bin/gmx}"
# 0 = grompp warnings are fatal. Raise only after reading the warning text.
MAXWARN="${GROMPP_MAXWARN:-0}"

SUMMARY="$WORK/summary.txt"
mkdir -p "$WORK"
cd "$WORK" || exit 2
: > "$SUMMARY"

kv()    { echo "$1=$2" >> "$SUMMARY"; echo "$1=$2"; }
note()  { echo; echo "-------- $* --------"; }
fatal() { kv CONTAINER_FAILED_AT "$1"; echo "FATAL: $1" >&2; exit 1; }
# run <step> <cmd...> : full output to <step>.txt, tail shown on failure.
run() {
    local step="$1"; shift
    if ! "$@" > "$step.txt" 2>&1; then
        tail -40 "$step.txt"
        fatal "$step"
    fi
}

[ -f "$DECK/prep.env" ] || fatal missing_prep_env
# shellcheck disable=SC1091
. "$DECK/prep.env"
for s in $STAGES; do
    [ -f "$DECK/$s.mdp" ] || fatal "missing_mdp_$s"
done
kv STAGES "$STAGES"
kv FORCE_FIELD "$FORCE_FIELD"
kv WATER_MODEL "$WATER_MODEL"
kv GROMPP_MAXWARN "$MAXWARN"

# --- 1. clean the PDB -------------------------------------------------------
note "1. clean PDB (ATOM/TER/END only; complete missing terminal OXT)"
# 1YCR has no HETATM, altloc or missing side-chain atoms; only termini are
# missing (REMARK 465). Chain B's last residue carries OXT, chain A's (VAL 109)
# does not. Rather than rely on whether the force field's C-terminus database
# rebuilds it, OXT is placed by reflecting C->O through the CA->C axis: planar,
# 120 deg from O, same C-O length. EM relaxes the rest. Chains need TER records.
awk '
    function f(s) { return s + 0 }
    NR == FNR {
        if ($0 ~ /^ATOM/) {
            c = substr($0, 22, 1); r = substr($0, 23, 4) + 0
            a = substr($0, 13, 4); gsub(/ /, "", a)
            last[c] = r; rname[c] = substr($0, 18, 3)
            if (a == "CA" || a == "C" || a == "O" || a == "OXT") {
                k = c SUBSEP r SUBSEP a
                X[k] = f(substr($0, 31, 8)); Y[k] = f(substr($0, 39, 8)); Z[k] = f(substr($0, 47, 8))
                has[k] = 1
            }
        }
        next
    }
    /^TER/ {
        c = substr($0, 22, 1); r = last[c]
        kc = c SUBSEP r SUBSEP "C"; ka = c SUBSEP r SUBSEP "CA"; ko = c SUBSEP r SUBSEP "O"
        if (!((c SUBSEP r SUBSEP "OXT") in has) && (kc in has) && (ka in has) && (ko in has)) {
            vx = X[kc] - X[ka]; vy = Y[kc] - Y[ka]; vz = Z[kc] - Z[ka]
            n = sqrt(vx*vx + vy*vy + vz*vz); vx /= n; vy /= n; vz /= n
            ux = X[ko] - X[kc]; uy = Y[ko] - Y[kc]; uz = Z[ko] - Z[kc]
            d = ux*vx + uy*vy + uz*vz
            printf "ATOM  %5d  OXT %3s %1s%4d    %8.3f%8.3f%8.3f%6.2f%6.2f          %2s\n", \
                f(substr($0, 7, 5)), rname[c], c, r, \
                X[kc] + 2*d*vx - ux, Y[kc] + 2*d*vy - uy, Z[kc] + 2*d*vz - uz, 1.0, 0.0, " O"
            added = added (added == "" ? "" : ",") c r
        }
        print; next
    }
    /^(ATOM|END)/ { print }
    END { print "OXT_ADDED=" (added == "" ? "none" : added) > "/dev/stderr" }
' "$PDB" "$PDB" > clean.pdb 2> clean_pdb.txt || fatal clean_pdb
cat clean_pdb.txt
kv PDB_ATOM_RECORDS_IN "$(grep -c '^ATOM' "$PDB")"
kv PDB_ATOM_RECORDS_CLEAN "$(grep -c '^ATOM' clean.pdb)"
kv OXT_ADDED "$(sed -n 's/^OXT_ADDED=//p' clean_pdb.txt)"

# --- 2. topology -------------------------------------------------------------
note "2. pdb2gmx -ff $FORCE_FIELD -water $WATER_MODEL -ignh"
# Non-interactive: -ff and -water are given; -ter/-his/-lys/... are NOT, so
# pdb2gmx applies its defaults (charged termini, His tautomer by H-bond
# placement). That is the protonationState recorded on the USD stage.
run pdb2gmx "$GMX" pdb2gmx -f clean.pdb -o processed.gro -p topol.top -i posre.itp \
    -ff "$FORCE_FIELD" -water "$WATER_MODEL" -ignh
grep -E "Processing chain|Total charge|There are .* chains" pdb2gmx.txt || true
NCHAINITP=0
QTOT=0
for itp in topol_*chain_*.itp; do
    [ -f "$itp" ] || continue
    NCHAINITP=$((NCHAINITP + 1))
    ch="${itp%.itp}"; ch="${ch##*_}"
    # [ atoms ] columns: nr type resnr residue atom cgnr charge mass
    kv "PROTEIN_RESIDUES_CHAIN_$ch" "$(awk '/^\[ *atoms *\]/{f=1;next} /^\[/{f=0}
        f && $1 !~ /^;/ && NF >= 7 { if (!($3 in s)) { s[$3] = 1; n++ } } END{print n+0}' "$itp")"
    q="$(awk '/^\[ *atoms *\]/{f=1;next} /^\[/{f=0} f && $1 !~ /^;/ && NF >= 7 {q += $7}
        END{printf "%.3f", q}' "$itp")"
    kv "CHARGE_CHAIN_$ch" "$q"
    QTOT="$(awk -v a="$QTOT" -v b="$q" 'BEGIN{printf "%.3f", a + b}')"
done
[ "$NCHAINITP" -gt 0 ] || fatal no_chain_itp
kv PROTEIN_CHAINS "$NCHAINITP"
kv PROTEIN_ATOMS "$(sed -n 2p processed.gro | tr -d ' ')"
kv NET_CHARGE_TOPOLOGY "$QTOT"

# --- 3. box + solvent ---------------------------------------------------------
note "3. editconf -bt $BOX_SHAPE -d $BOX_DISTANCE_NM ; solvate -cs $SOLVENT_BOX"
run editconf "$GMX" editconf -f processed.gro -o box.gro -c -d "$BOX_DISTANCE_NM" -bt "$BOX_SHAPE"
grep -E "new box vectors|new box volume" editconf.txt || true
run solvate "$GMX" solvate -cp box.gro -cs "$SOLVENT_BOX" -o solv.gro -p topol.top

# --- 4. ions ------------------------------------------------------------------
FIRST="${STAGES%% *}"
note "4. grompp ($FIRST.mdp) + genion -neutral -conc $ION_CONCENTRATION_MOLAR"
run grompp_ions "$GMX" grompp -f "$DECK/$FIRST.mdp" -c solv.gro -p topol.top -o ions.tpr -maxwarn "$MAXWARN"
PRE="$(grep -m1 -oE 'non-zero total charge: *-?[0-9.]+' grompp_ions.txt | grep -oE '\-?[0-9.]+$')"
kv NET_CHARGE_PRE_IONS_GROMPP "${PRE:-0 (no non-zero-charge note)}"
# genion asks for the group to replace; SOL is fed by name on stdin.
if ! echo SOL | "$GMX" genion -s ions.tpr -o ions.gro -p topol.top \
        -pname "$ION_POSITIVE" -nname "$ION_NEGATIVE" -neutral -conc "$ION_CONCENTRATION_MOLAR" \
        > genion.txt 2>&1; then
    tail -40 genion.txt; fatal genion
fi
grep -E "Will try to add|Replacing solvent molecule" genion.txt | head -3 || true
mol() { awk -v m="$1" '/^\[ *molecules *\]/{f=1;next} f && $1 == m {n += $2} END{print n+0}' topol.top; }
kv WATERS "$(mol SOL)"
kv "IONS_$ION_POSITIVE" "$(mol "$ION_POSITIVE")"
kv "IONS_$ION_NEGATIVE" "$(mol "$ION_NEGATIVE")"
kv TOTAL_ATOMS "$(sed -n 2p ions.gro | tr -d ' ')"

# --- 5. stages ----------------------------------------------------------------
prev=ions.gro
cpt=""
for s in $STAGES; do
    mdp="$DECK/$s.mdp"
    S="$(printf '%s' "$s" | tr '[:lower:]' '[:upper:]')"
    note "5. stage $s ($mdp)"
    args=(-f "$mdp" -c "$prev" -p topol.top -o "$s.tpr" -maxwarn "$MAXWARN")
    grep -qE '^define *= *.*-DPOSRES' "$mdp" && args+=(-r "$prev")
    [ -n "$cpt" ] && args+=(-t "$cpt")
    run "grompp_$s" "$GMX" grompp "${args[@]}"
    if grep -qE '^integrator *= *(steep|cg|l-bfgs)' "$mdp"; then
        run "mdrun_$s" "$GMX" mdrun -deffnm "$s" -nb gpu -ntmpi 1 -ntomp "$NTOMP"
        kv "${S}_POTENTIAL_ENERGY" "$(grep -m1 'Potential Energy' "$s.log" | awk '{print $4}')"
        kv "${S}_MAX_FORCE" "$(grep -m1 'Maximum force' "$s.log" | awk '{print $4}')"
        kv "${S}_CONVERGED" "$(grep -qE 'converged to Fmax' "$s.log" && echo yes || echo no)"
        cpt=""
    else
        run "mdrun_$s" "$GMX" mdrun -deffnm "$s" -nb gpu -pme gpu -ntmpi 1 -ntomp "$NTOMP"
        kv "${S}_NS_PER_DAY" "$(grep -m1 '^Performance:' "$s.log" | awk '{print $2}')"
        kv "${S}_NONBONDED_ON_GPU" "$(grep -qE 'Using GPU .* nonbonded' "$s.log" && echo yes || echo no)"
        kv "${S}_PME_ON_GPU" "$(grep -qE 'PME tasks will do all aspects on the GPU' "$s.log" && echo yes || echo no)"
        # Average T / P (/ density). Terms are chosen by name on stdin; the
        # blank line ends the selection. Rows of the result table start with
        # the term name. Density is asked for only under pressure coupling: a
        # fixed box writes no Density term, and asking for one is not a datum.
        terms="Temperature Pressure"
        grep -qE '^pcoupl *= *no' "$mdp" || terms="$terms Density"
        # shellcheck disable=SC2086
        if printf '%s\n' $terms "" \
                | "$GMX" energy -f "$s.edr" -o "${s}_energy.xvg" -xvg none > "energy_$s.txt" 2>&1; then
            for t in $terms; do
                T="$(printf '%s' "$t" | tr '[:lower:]' '[:upper:]')"
                kv "${S}_AVG_${T}" "$(awk -v t="$t" '$1 == t && $2 ~ /^-?[0-9]/ {print $2; exit}' "energy_$s.txt")"
            done
        else
            kv "${S}_ENERGY_EXIT" "failed"
        fi
        cpt="$s.cpt"
    fi
    prev="$s.gro"
done

kv CONTAINER_EXIT 0
exit 0
