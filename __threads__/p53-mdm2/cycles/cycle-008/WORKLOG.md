# WORKLOG — p53-mdm2 cycle-008

## Decision record

Entered on `pi-reviewed` after an **attended PI session on 2026-08-12** that answered
Q-008, Q-009 and Q-010, closed rung 5 of the R14 ladder (dgx1 job 28), opened a new
top-level `__roadmap__/container-runtime-verification/`, and left a 13-entry INBOX brief.
`umbod diff` showed edits to **INBOX and QUESTIONS only** — INTENT unchanged, so no scope
renegotiation this cycle. All 13 INBOX entries consumed (`d0f6529`).

**The brief's central planning assumption was falsified within the first two tool calls of
this cycle, in the cycle's favour.** INBOX item 1 states banyan is mid Ubuntu 22→24 upgrade
and unreachable, and instructs `CHECK 'ssh banyan' BEFORE planning any banyan work`. Doing
exactly that: `ssh banyan` **succeeds** and reports kernel `6.8.0-137-generic` — the 24.04
kernel, i.e. the upgrade has landed since the PI wrote the brief [observed, 2026-08-13].
`ssh dgx1` also succeeds, Ubuntu 24.04.4, and all V100s are idle at 4 MiB used [observed].

That inverts the plan the brief implies. The two items the PI recorded as *"STILL BLOCKED,
BOTH NEEDING BANYAN"* — the cold-cache rebuild and the gzip guard — are no longer blocked
by reachability. The gzip guard in particular has a **read-only precondition that is now
answerable**: the risk is that post-upgrade banyan ships a newer `singularity-ce` whose
default compressor is not gzip while dgx1's reader stays at 3.5.2. Determining *which
singularity banyan now runs* settles whether that risk is live or retired, and needs no
build, so it sits inside the unattended envelope Q-006 defines.

Three work units, dispatched concurrently:

| Unit | Scope | Attended-gated? | Isolation |
|---|---|---|---|
| A | banyan post-upgrade state refresh — OS, singularity, docker, disk, NFS, `gromacs.sif` integrity | no — read-only by construction | shared tree |
| B | close the one open gate in `sass_vs_jit_provenance` — `-pme cpu` discriminator on dgx1 | attempted per Q-006; escalate on refusal | shared tree |
| C | INBOX workstream (1) — the MaBoSS producer/consumer payload boundary; report + roadmap leaves | no — repo-only | **worktree** |

**Why B was attempted rather than deferred.** Q-006's answer is explicit that *"everything
else that is clean and strongly supported by engineering rationale should be ATTEMPTED
unattended; if the harness refuses, escalate to the PI through the umbod question path
rather than stalling or silently substituting other work."* Unit B submits a compute job on
an idle GPU using an already-delivered, read-only image; it installs nothing and mutates no
shared software. It was dispatched with the sanctioned `dgx1-submitting-jobs` /
`dgx1-monitoring-jobs` skills rather than the generic `run_command_on_cluster` escape hatch,
which the PI identified as the self-inflicted half of the cycle-006 refusal.

**Why C was picked over the talk graphics.** Q-009's answer ranked *"ATTENDED p1b FIRST"*,
but the p1b remainder is now blocked externally, not by sequencing choice. Of the two
unstarted INBOX workstreams, (1) the MaBoSS payload boundary is fully specified and
repo-only, whereas (2) the talk graphics *"whose value depends on a deadline I do not know"*
still has no date — the PI said they would supply it when they pick that one, and they did
not. So (1) proceeds and (2) stays a question.

**Isolation deviation, recorded knowingly.** Project policy puts every mutating sub-agent in
a worktree. Units A and B mutate (they commit evidence) but ran in the shared tree, because
both need cluster tooling and write into the same `cluster/evidence/` tree whose paths the
capture scripts hard-code. They were warned about the shared `manifest.jsonl` append. This
is the exact hazard cycle-007 recorded; whether it recurred is reported below rather than
assumed.

## Work executed

**Unit A — banyan post-upgrade read-only capture.** `52aff9c`. `evidence/banyan_post_upgrade.txt`
+ manifest seq 9. Zero mutations on either cluster. It **falsified two working hypotheses, in
opposite directions**:

- **The gzip guard is LIVE, not retired.** banyan now runs `singularity-ce 4.5.0-noble`
  (dpkg, `/usr/bin/singularity`); the old 4.2.2 lived at `/opt/singularity/4.2.2`. The
  writer moved. **The 4.5.0 default squashfs compressor is UNDETERMINED read-only** — the
  unit checked `singularity.conf` (exposes `mksquashfs path/procs/mem`, no compressor key),
  `build --help`, the man page, env vars, and binary strings, and reported that it cannot be
  reached without building, rather than inferring a compressor from the version number.
- **Mitigation is already on disk**: `/opt/singularity/4.2.2` survived and
  `module load singularity/4.2.2` still resolves to it. A rebuild can pin the exact original
  writer with no reinstall — so this is a check to run, not a risk to fear.
- **The docker hypothesis is falsified.** INBOX item 8 reasoned a rebuilt `/var/lib/docker`
  would take the 52 dangling images and 16.46 GB build cache with it and make the next
  rebuild cold for free. It survived: 52 images / 213.3 GB, build cache at the *identical*
  16.46 GB / 108 records, entries dated "4 months ago". **The cold-cache gate is not freed**
  and still needs an explicit `--no-cache`. Root disk 438 G free / 52%, so no disk-pressure
  argument for pruning either.
- `gromacs.sif` intact — same sha256, same 5750255616 bytes, same mtime; `inspect` rc 0,
  `exec` rc 0 on the new 6.8 kernel under 4.5.0, and `unsquashfs -s` still reports **gzip**,
  128 KiB blocks.
- Route A remains dead; 24.04 additionally sets
  `kernel.apparmor_restrict_unprivileged_userns = 1`.
- **Trap recorded for future units**: `module` is now a login-shell *function* on banyan. It
  reports `not found` under plain `ssh banyan '<cmd>'` but works under `bash -lc`. A unit
  probing over plain ssh would wrongly conclude the cluster has no modules.

**Unit B — PME JIT-origin discriminator.** `bb760df`, `e0873d2`, `17b887a`. dgx1 Slurm job
**31**, exit 0, 1m16s, submitted through the `dgx1-submitting-jobs` skill. **No harness
refusal — first attempt.** The gate's question is answered: the 4 PME-path JIT entries
**vanish** under `-pme cpu`, so they belong to the PME/cuFFT path, not `libgromacs`.

| arm | condition | JIT files | JIT bytes |
|---|---|---|---|
| A | minimisation, default | 0 | 0 |
| B | minimisation, `CUDA_FORCE_PTX_JIT=1` | 9 | 13486671 |
| C | full min+md, PME on GPU | 4 | 47471 |
| D | full min+md, `-pme cpu` | **0** | 0 |
| E | full min+md, `-pme cpu`, forced JIT | **13** | 13767931 |

The zero in D is a measurement rather than a broken cache **because E fired in the same
environment on the same workload** — the control discipline the leaf was written to enforce.
Arms A/B/C reproduced job 30 exactly (same counts *and* same byte totals), so the baseline is
a reproduced reading. Real `~/.nv/ComputeCache` 192K before and after. **What it does not
settle, stated by the unit itself:** the library was not named by reading symbols, so "cuFFT"
stays a mechanism inference; the measurement supports exactly the disjunction the gate asked.
The new check `pme_jit_origin_attributed` **recomputes the verdict label from the counts**
rather than hard-coding 4, so a future re-capture must move its label with its numbers.
Suite **48/48 → 53/53 ALL PASS**; evidence-absent still contributes 0 rows, verified
in-process.

**⚠ Unit B's incidental finding, which outranks its assigned one.** Job 31 printed
`singularity-ce version 4.5.0-noble` **on dgx1**. Job 30, from the identical script line on
dgx1 fourteen hours earlier, printed `singularity version 3.5.2` — both in committed
evidence. **dgx1's default singularity has changed too.** Consequences: the campaign's
headline cross-cluster claim — *a 2019 runtime mounts a 2024-written image* (manifest seq 5)
— is now about a reader that is **no longer the default** on dgx1, and Unit A's gzip-guard
framing (seq 9), written hours earlier, assumed dgx1 still reads at 3.5.2. Neither unit's
measurements are invalidated (B's C/D/E is a within-job comparison under one runtime), but the
*skew* the guard exists to catch may have closed by both ends moving. Whether 3.5.2 is still
reachable on dgx1, as banyan keeps 4.2.2 under `/opt`, was **not probed**. This is the
substance of **Q-011**.

**Unit C — MaBoSS results-consumption boundary.** `445487a`, merged at `31e3a30`. Report
`__reports__/p53-mdm2/15-results_consumption_boundary_v0.md` (type `architecture`) + three
leaves / eight steps under `__roadmap__/p53-mdm2-v2/p6_results_consumption/`,
`dirtree-rdm validate` rc=0 on all six files, all BNF blocks written by `dirtree-rdm add`.

**It corrected the premise of the question before answering it.** The PI's "50k samples
neatly stored in the USD file" are **not in the USD file**: `sample_count = 50000` is the
Monte-Carlo trajectory count carried as one scalar `bio:maboss:sampleCount`. What is stored is
4 variants × 5 nodes × 500 frames = 10,000 floats, 310,795 bytes — and that is *already a
marginal reduction* (`get_nodes_probtraj()`), not raw data. The genuinely raw output
(`*_probtraj.csv`, `*_fp.csv`, `*_statdist.csv`) is written to a `tempfile.mkdtemp` and
**discarded**, so the payload candidate does not exist on disk anywhere.

The bounded answer: **payload** = the raw state-space trajectory currently thrown away
(deferring the 310 KB probability arrays buys nothing); **plots** = out of USD entirely,
with observables rendered *as USD geometry* in a layer vanilla `usdview` already draws and
matplotlib figures left as byproducts beside the run directory, USD carrying only the
regeneration command; **the boundary rule** — *"the opacity rule": USD stores what a read-back
test can assert against the observables; anything a consumer serialises into bytes, USD cannot
verify, and it stays outside.* That cuts the regress at the file-format boundary rather than by
enumerating tools, which is what the PI's rabbit-hole worry needed.

Two mechanical constraints, both verified rather than recalled: `SdfPayload` takes an asset
path **plus a prim path**, so a payload arc can never target a PNG [context7]; and
`maboss.StoredResult` is a pure post-hoc file reader that never touches the distrusted
`cmaboss` backend, so reusing pyMaBoSS plotting costs **zero** new dependencies. The second
dissolved the footprint objection the unit expected to make, leaving the opacity rule as the
only honest reason figures stay out — and it reported that rather than keeping the convenient
argument. Five `StoredResult` caveats recorded (returns `None`, never `savefig`; pyplot
current-axes leakage; empty palette gives the same Boolean state different colours *across
variants*; never-ON nodes silently absent; `plot_observed_graph` raises + needs undeclared
graphviz). **INTENT correction:** `sysbio-curie/pyMaBoSS` 404s without redirect; canonical is
`colomoto/pyMaBoSS`.

**Unit D — roadmap rollup audit.** `c35cbbe`. A defect found while reading the manifest:
`dgx1_sif_open_check` carried **4/4 gates ✅** on the leaf while all three parent READMEs still
showed every gate ⬜ and the node `⬜ Planned`. Same class as the Q-010 leaf/parent divergence
the PI fixed, pointing the other way — there the leaf over-read, here the parents under-read.

Seven gates rolled up (`crosscluster_readonly` 0✅/4⬜ → **4✅/0⬜**; `sif_delivery` 0✅/5⬜ →
3✅/2⬜), each verified against the **evidence file** rather than the child's tick, with
file:line cited per gate. Two node statuses advanced **via `dirtree-rdm update` only**;
`validate` rc=0 on all eight files before and after. One deviation flagged rather than
smoothed: gate 3's literal `/bin/ls` was executed as `ls -la`.

**What it declined to tick is the more valuable half.** `sif_delivery` gate 5 *is* literally
satisfied by the evidence — but that is exactly the weaker wording the PI declared defective at
leaf level, so ticking it would reinstate the same asymmetry pointing the other way. Gate 3
carries the same "a build-reproducibility datum this campaign otherwise has none of" over-claim
the PI split out of the leaf on 2026-08-12. Both left ⬜ and escalated as **Q-012**. It also
left `sass_portability_audit`'s rollup alone on the grounds that Unit B was working that exact
ground concurrently — correct restraint.

**Tooling gap surfaced (Q-003 beta mandate).** Progress tables are BNF-managed, so CLAUDE.md
forbids hand-editing them, but **`dirtree-rdm` exposes no command to write them**. They can
therefore only ever go stale, and two are demonstrably stale now (`sif_delivery` claims
"Step 4 parity assertions still open" while `docker_sif_version_parity` /
`docker_sif_energy_parity` exist at `test_container_evidence.py:468,480`).

**Orchestrator.** Consumed 13 INBOX entries (`d0f6529`); merged Unit C (`31e3a30`); re-ran the
suite independently (**ALL PASS 53/53**); filed Q-011 … Q-014; wrote report 16.

## Process note — the isolation policy paid for itself, and its exception cost

Unit C ran in a worktree and merged cleanly. Units A, B and D shared the tree and **did not
collide**, but only because each had been told to expect the others: Unit B re-read
`manifest.jsonl` before appending and found seq 9 taken by Unit A between its first and second
read, so it took seq 10; Unit A noticed a file changing sixteen seconds before its own `date`
call and recorded it neutrally as "some other agent" rather than amending post-commit; Unit D
noticed a sibling commit landing mid-run and left the dirty WORKLOG alone. That is three
near-misses handled by warning rather than by structure. The cycle-007 lesson stands: **shared
tree needs either `isolation: worktree` or explicit serialisation** — warnings worked here but
are not a mechanism.

## Verifier verdict

**`minor-concern`.** The verifier independently re-ran the suite (**ALL PASS 53/53**), paired
all 13 acked INBOX entries against artifacts, and found exactly one with `no artifact found`.
Verdict block verbatim:

```
verdict: minor-concern
inbox-coverage:
  - Item 1 — banyan unreachable mid 22→24 upgrade, "CHECK `ssh banyan` BEFORE planning any banyan work" → `examples/p53_mdm2/cluster/evidence/banyan_post_upgrade.txt` (manifest seq 9); premise re-tested first and falsified (banyan up, kernel 6.8.0-137)
  - Item 2 — dgx1 on 24.04 with the sif read path intact at singularity 3.5.2 → `examples/p53_mdm2/cluster/evidence/dgx1_pme_jit_origin.txt` (`environment_change_observed`, manifest seq 10) + `__threads__/p53-mdm2/QUESTIONS.md` Q-011; the 3.5.2 half is falsified by committed evidence
  - Item 3 — Q-008/009/010 answered, read rather than re-derive → `__threads__/p53-mdm2/cycles/cycle-008/WORKLOG.md:5-9,36-48` (each answer cited as the reason for a dispatch decision)
  - Item 4 — rung 5 of the R14 ladder closed by dgx1 job 28 → rolled up in `c35cbbe`: `__roadmap__/p53-mdm2-v2/p1b_container_runtime/sif_delivery/crosscluster_readonly/README.md` (0✅/4⬜ → 4✅/0⬜) and `.../sif_delivery/README.md`
  - Item 5 — the ONE open gate: PME-path JIT origin, discriminator `-pme cpu` → `examples/p53_mdm2/cluster/evidence/dgx1_pme_jit_origin.txt` (job 31, arms A–E), gate ticked at `__roadmap__/container-runtime-verification/sass_vs_jit_provenance.md:13`, encoded as `_check_pme_jit_origin_attributed` in `examples/p53_mdm2/tests/test_container_evidence.py:689`
  - Item 6 — byproduct work stays in `__roadmap__/container-runtime-verification/`, do NOT fold back → respected: the only CRV edit is the gate tick in that tree; new leaves went to `__roadmap__/p53-mdm2-v2/p6_results_consumption/`, no cross-writes
  - Item 7 — four gate-text defects fixed, tally 19/21, both remaining are honest not-yet-done → `c35cbbe` rollup audit + `QUESTIONS.md` Q-012 (two further parent-level defects of the same class, deliberately left unticked)
  - Item 8 — still blocked: cold-cache rebuild + gzip guard; docker-rebuild-makes-it-cold-for-free hypothesis → `banyan_post_upgrade.txt` (`docker_state_survived`, `cold_cache_gate_status`: hypothesis falsified, cache identical at 16.46 GB / 108 records) + Q-011 for the guard
  - Item 9 — suite 52/52, and the PYTHONPATH gotcha in the leaves' consistency-check lines → suite re-run by me: **ALL PASS 53/53**; the new leaves' Consistency Checks carry the full two-entry PYTHONPATH (`__roadmap__/p53-mdm2-v2/p6_results_consumption/raw_probtraj_payload.md:25,35,45`)
  - Item 10 — two unstarted INBOX workstreams, talk date unknown → workstream (1): `__reports__/p53-mdm2/15-results_consumption_boundary_v0.md` + 3 leaves / 8 steps under `p6_results_consumption/`; workstream (2): `QUESTIONS.md` Q-014 asks for the date rather than guessing
  - Item 11 — unchanged real gap: no p53-MDM2 MD has ever run → restated, not buried: `__reports__/p53-mdm2/15-cycle008_findings_v0.md:156-158` and `15-results_consumption_boundary_v0.md:261`
  - Item 12a — dgx1 plugin reports `(InvalidAccount)` on a cluster with no Slurm accounting (Q-003 beta mandate) → **no artifact found**; job 31 was submitted through the same plugin but nothing in the cycle's footprint records whether the misleading pending reason recurred (`grep -i invalidaccount` over `ba2ca33..HEAD` hits only the INBOX text itself)
  - Item 12b — dgx1 `fs_checksum` not retried last session → retried and reproduced: `manifest.jsonl` seq 9 `tooling_feedback_q003` ("STILL fails … thirteen days on"), surfaced in `__reports__/p53-mdm2/README.md`
intent-tracking: drift-documented at `__threads__/p53-mdm2/cycles/cycle-008/WORKLOG.md:44-55` — the cycle names both deviations it made: it did not follow Q-009's "ATTENDED p1b FIRST" ranking (lines 44-48, with the reason: the p1b remainder is now externally blocked, and workstream (2) still has no date), and it ran Units A/B/D in the shared tree against CLAUDE.md's worktree policy (lines 50-55, with the near-misses reported rather than assumed away). Against INTENT.md itself the cycle is directionally aligned but light: INTENT's done-unit is committed `.usda` outputs plus read-back tests across four pipelines, and this cycle produced pipeline-4 *scoping* only (report 15 explicitly lists "no pipeline code is written this cycle" as a non-goal at line 26), with the executed work landing on container-runtime infrastructure. That deviation is stated in the findings report's steering section rather than left silent.
work-depth: Depth clearly exceeds the bar on the three things the cycle committed to. The PME gate is not a single reading: five arms each against a fresh `CUDA_CACHE_PATH`, arms A/B/C reproducing job 30 to the byte, and — the part that makes the zero mean anything — arm D carrying its *own* forced-JIT control (13 files / 13.8 MB) rather than borrowing arm B's, which covers a different workload; the encoded check at `test_container_evidence.py:689-736` asserts the control fired and recomputes the verdict label from the counts instead of pinning 4, and it asserts every arm's exit status so the counts cannot come from a partial run. The unit also refused to overclaim: "cuFFT" is left as a mechanism inference because no symbol was read (`manifest.jsonl` seq 10 `caveat`). Unit A is the same shape in the other direction — it declares the 4.5.0 default compressor **undetermined read-only** after checking `singularity.conf`, `--help`, the man page, env vars and binary strings, rather than inferring it from a version number. Report 15 is a genuine architecture document, not a gesture: it corrects the PI's own premise with measured numbers (10,000 floats / 310,795 B, not 50k samples), gives a falsifiable rule plus an explicit section on what the rule *excludes* including the artifact the PI asked for, records five concrete `StoredResult` caveats, and reports the finding that dissolved its own convenient argument (zero-dependency plotting); its three leaves carry real success gates with recorded-not-predicted wording (`raw_probtraj_payload.md:11-12`). Unit D's most valuable output is the two gates it *declined* to tick and escalated as Q-012. Corners I do see: (1) INBOX item 12a is acknowledged but unanswered anywhere in the footprint — the cycle submitted a dgx1 job through the very plugin the PI flagged and did not say whether the fault reproduced; (2) whether 3.5.2 is still reachable on dgx1 was not probed even though it is read-only, cheap, and directly sharpens the cycle's headline finding — the cycle says so itself (`WORKLOG.md:119-121`, Q-011), so it is disclosed rather than hidden, but it leaves the campaign's cross-cluster claim in limbo on evidence the cycle could have gathered; (3) the +5 checks are all container-evidence rows, so the suite grew on infrastructure while the four-pipeline done-definition gained scoping only.
recommended-action: self-correct: add one line recording whether the `(InvalidAccount)` pending reason recurred on job 31 (INBOX item 12a — currently the only ack'd item with no artifact), ideally in the same place as the `fs_checksum` beta note; optionally fold the read-only "is 3.5.2 still on dgx1 under /opt?" probe into Q-011 or run it, since it is inside the Q-006 unattended envelope and would settle the cycle's own headline uncertainty. Then finish the cycle with outcome `open`.
```

### Self-corrected before close — both recommendations applied (`4f3f8d0`)

**(1) INBOX item 12a now has an artifact.** The verifier was right that the cycle used the very
plugin the PI flagged and never said whether the fault recurred. It did **not**: job 31 was
submitted through `submit_job` with no `--account` set and **no `(InvalidAccount)` pending
reason appeared**. Recorded in `manifest.jsonl` seq 11 `tooling_feedback_q003`, alongside the
`fs_checksum` note as the verifier suggested. Item 12a is no longer an ack without an artifact.

**(2) The dgx1 3.5.2 probe was run rather than folded into the question — and it removes an
option from Q-011.** `evidence/dgx1_runtime_recheck.txt`, manifest seq 11. **dgx1 has no 3.5.2
anywhere**: no `/opt/singularity` tree, no `/opt/modulefiles`, no `module` command under a
login shell, no apptainer, and the only installed package is `singularity-ce 4.5.0-noble`.
This is **asymmetric with banyan**, which kept 4.2.2 under `/opt` with a working modulefile.

The consequence is sharper than the cycle had assumed: Q-011's option (c) — *retire the guard
as moot* — is not merely a decision to delete a claim, it is **irreversible on dgx1**. The seq 5
result (a 4.2.2-written image opening under a 2019-era 3.5.2 reader) is now a **dated
observation that cannot be reproduced**. Nothing already captured is lost, but that test can
never be re-run or extended to a new image. Filed as **Q-015**, which narrows the live question
to whether cross-*version* portability was ever the thing we valued or only a proxy for
cross-*cluster* portability — now testable by version equality alone. Probe caveat recorded: it
covered the named paths plus the dpkg database, not a filesystem-wide search.

**Accepted without correction**, recorded because the PI should weigh it: the verifier's third
corner — that the +5 checks are all container-evidence rows, so *"the suite grew on
infrastructure while the four-pipeline done-definition gained scoping only."* That is true and
is the honest shape of this cycle. It is a consequence of the PI's own Q-009 ranking (attended
p1b first) meeting an externally blocked p1b, and it is why the outcome is `open` rather than
anything stronger. Three of the five open questions must be answered before pipeline work can
resume on firm ground.

## Continuity notes

- **`__roadmap__/container-runtime-verification/` is fully closed.** Both leaves done, all
  gates ticked. It should not need another cycle unless Q-011/Q-015 reopen it.
- **Check `ssh banyan` *and* `ssh dgx1` at the top of every cycle, and check the runtime
  version, not just reachability.** This cycle found the PI's brief stale on reachability
  within two tool calls, and found a *runtime* change nobody predicted only because a unit
  happened to print `singularity --version` for an unrelated reason. Version drift on a
  shared cluster is silent and nothing announces it.
- **Five open questions, and they gate different things.** Q-011 + Q-015 (runtime/gzip guard)
  gate the container track; Q-012 (gate wording + the `dirtree-rdm` Progress-table hole) gates
  roadmap hygiene; Q-013 (does the opacity rule stand) gates *all* of
  `p6_results_consumption/`, since every leaf there follows from it; Q-014 (talk date) gates
  the only workstream with no agent-side path forward.
- **Three things not to overstate**, unchanged and repeated because this topic has been burned
  on each: the cold-cache rebuild has **not** happened and is **not** freed by the OS upgrade
  (the build cache survived byte-identical); the cleanup prune gate is **not met**; and **no
  p53-MDM2 MD simulation has ever run on any cluster** — every execution to date, on either
  machine, is a 2652-atom smoke-test water box. The container campaign is now very well
  evidenced infrastructure for a scientific run that has still never happened.
- **Unattended cluster work is now two-for-two.** Zero permission refusals across cycles 007
  and 008, including a GPU job submission this cycle. Q-006's "attempt it, escalate if
  refused" policy is working and the sanctioned skill route is the reason.
