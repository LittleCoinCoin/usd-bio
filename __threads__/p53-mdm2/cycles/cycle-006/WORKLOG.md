# WORKLOG — p53-mdm2 cycle-006

## Decision record

Cycle opened on a `pi-reviewed` topic with **four new INBOX entries** (all four
acked, commit `624b313`, archived to `INBOX-consumed.md`). Two were already
pending from cycle-005 (GROMACS engine choice; ack of reports 07+08) and two are
new and directive:

1. **2026-07-25T07:58** — PI **authorizes the PI-gated mutating cluster steps**:
   native singularity on banyan first, CUDA 12.9 for dgx1 compatibility, GROMACS
   2025.3, smoke test first before the p53-mdm2 variants.
2. **2026-07-25T08:04** — PI added `extras/DDMut-PPI-API.pdf` (commit `362559c`)
   and directs: convert via `/pdf-to-md`, make it searchable, **retry the live
   ddMut-PPI server** against the documented API.

Plus the standing cycle-005 recommendation: **P5 integrated demo**.

Plan: four parallel sub-agent tracks — (A0) read-only cluster state refresh,
(A1) resolve the `[assumption]` blanks in `cluster/gromacs.def`, (A2) the
authorized banyan build + smoke test, (B) ddMut-PPI live retry, (C) P5
integrated demo.

### Blocker hit at dispatch: track A2 refused by the harness

**Track A2 (the cluster-mutating build the PI explicitly authorized) never ran.**
Both dispatch attempts were refused by Claude Code's auto-mode permission
classifier, which gates cluster-mutating actions in unattended sessions. The
PI's authorization lives in project files (`INBOX.md`), and the harness
classifier does not read project files as permission — so a written PI
authorization inside the thread cannot unblock an unattended session. Retried
once with tighter scoping, then stopped; a third attempt would have been an
attempt to evade the denial rather than to satisfy it.

Consequences, recorded honestly:
- **Nothing was built, uploaded, or submitted on any cluster this cycle.** The
  `⚠️ NOTHING HAS BEEN BUILT` banner in `examples/p53_mdm2/cluster/README.md`
  remains literally true.
- p1b Step 2 could only advance on its non-mutating half (A0 + A1), which makes
  the build turnkey for an attended session.
- Filed as **Q-006 (soft)** with three concrete options for the PI: run it
  attended, pre-allow the cluster MCP tools in `settings.local.json`, or make
  the build attended-only by policy. Soft rather than hard because the rest of
  the cycle had real work to do.

This is a *tooling* boundary, not a scope change: the PI's decision stands, the
async runtime just cannot execute it.

## Work executed

### Track A1 — `cluster/gromacs.def` made build-ready (commits `3f731c3`, `a16bcc2`)

Verified every `[assumption]` in the container definition against upstream, and
**found two latent build-breakers no prior cycle had caught**:

1. **Ubuntu jammy's apt `cmake` is 3.22.1, but GROMACS 2025.3 requires ≥ 3.28** —
   the old recipe's `apt-get install cmake` would have died at configure time.
   `%post` now installs pinned CMake 4.0.3 from Kitware's tarball, checked
   against Kitware's own published sha256.
2. **The 22.04-vs-24.04 base-image choice was an unstated compiler decision.**
   noble would have fixed the CMake gap but handed GROMACS gcc 13, which
   upstream lists under "known issues with GCC 12 and newer". jammy's gcc 11.x
   sits inside the recommended 9.x–11.x range. Now documented with sources.

Verified: GROMACS 2025.3 tarball URL; the official **md5**; CUDA ≥ 12.1 minimum;
that `nvidia/cuda:12.9.1-devel-ubuntu22.04` actually exists (with digest); the
`GMX_*` flag spellings; the Ubuntu/gcc fit.

**The CUDA-12.9-for-Volta pin held up under checking, and was confirmed at the
toolkit level rather than from the announcement**: nvcc 12.9.1's SM list
contains `sm_70` and `sm_90`; nvcc 13.0.0's list *starts at* `sm_75`. The pin is
correct and load-bearing.

Deliberately left under-claimed rather than guessed:
- **sha256 is corroborated, not vendor-published.** GROMACS publishes only md5.
  The sha256 comes from Spack and EasyBuild independently agreeing. Both checks
  stay active in `%post`, labelled as such — a wrong sha256 fails loudly after
  md5 passes, and no integrity check was disabled. The agent did not download
  the 42 MB tarball to compute it itself in an unattended session.
- **`GMX_SIMD` stays `[assumption]` (`AVX2_256`).** Report 07 never recorded
  `lscpu` for either cluster. The def now carries a build-time procedure: read
  `lscpu` on *both* clusters and take the least common denominator — explicitly
  *not* CMake auto-detection, because one `.sif` on the shared NFS home runs on
  two CPU generations and auto-detect would pin it to the build host
  (illegal-instruction risk on the other machine). Track A0 was independently
  tasked with capturing `lscpu`, which closes this.

Known deviations recorded honestly: CUDA 12.9 is above GROMACS' CI-tested set
(12.1/12.5.1/12.6) — unavoidable, since sm_70 requires it; and
`GMX_BUILD_OWN_FFTW=OFF` is a knowing deviation from upstream's recommendation,
kept for a hermetic configure and documented as a performance trade.

The agent also self-corrected one over-claim it had written (`a16bcc2`).
Nothing was built; no cluster was contacted; the README banner remains truthful.

### Track A0 — read-only cluster state refresh (commit `c8f2cc2`, report 10)

`__reports__/p53-mdm2/10-cluster_state_refresh_v0.md`. Strictly observational —
no writes, no submissions, heaviest calls were HTTP `HEAD`. **This track turned
out to be the most valuable thing the cycle did, because it invalidated a
load-bearing assumption in the runbook before anyone tried to build on it.**

**Finding 1 — `--fakeroot` is NOT available; report 07's claim was false.**
`/etc/subuid` and `/etc/subgid` carry **no mapping for this user on either
cluster** (banyan: only `user`/`test`; dgx1: only `lxd`/`root`), though
unprivileged userns is otherwise enabled. `singularity build` from a `.def`
needs root-in-container for `%post`, so **runbook Route A — the *recommended*
route, and the one the PI's authorization names ("native singularity on banyan
first") — is very likely infeasible.** Route B stays open: the user *is* in
banyan's `docker` group and the daemon answers (v29.4.3, 51 images), so
Docker-build → `docker save` → `singularity build docker-archive://…` works,
with the run still under singularity as designed. Filed as **Q-007 (soft)**.
*Honest bound:* this is inference from the absent mapping, **not an observed
build failure** — one attended `singularity build` would settle it in seconds.

Had the harness *not* blocked track A2, the build would very likely have failed
on this. The blocked dispatch and the recon cancelled out to roughly the same
place, minus a wasted multi-GB build attempt on a shared node.

**Finding 2 — the missing `lscpu` data now exists, and it contradicts the def.**
banyan = Xeon Gold 6530 (Emerald Rapids, 128 threads); dgx1 = Xeon Gold 6130
(Skylake-SP, 64 threads). **Both** carry `avx512f/dq/bw/vl/cd`, so the least
common denominator is `AVX_512`, not the `AVX2_256` currently in `gromacs.def`.
Dispatched a follow-up to settle the flag against the GROMACS 2025.3 install
guide before changing it — AVX-512 on Skylake-SP has known clock-throttling
caveats and the higher flag is not automatically the right one.

**Finding 3 — two operational hazards for any future smoke test.**
- **banyan GPU 0 holds another user's ~86 GB `VLLM::EngineCore`** while Slurm
  reports the node `IDLE` with empty `AllocTRES`. Slurm's view and reality
  diverge; a 1-GPU job could land on a full GPU. Needs an `nvidia-smi`
  pre-flight. (Whether Slurm actually hands out GPU 0 is undetermined.)
- **banyan's root disk lost 147 GB in 6 days** (586 G → 439 G free) and `/tmp`
  is on root — build scratch must go to shared home, and free space must be
  re-checked immediately before building.

**Finding 4 — the rsync blocker was a local misdiagnosis, not a cluster fact.**
Both clusters ship rsync 3.2.7 at `/usr/bin/rsync` and were never the problem.
Locally, `/opt/homebrew/bin/rsync` is 3.4.4 and **already precedes** macOS's
openrsync on PATH — no export needed. Closes the Q-005 rsync item.

Also newly recorded: outbound internet works on both (no proxy; the CUDA
manifest and the GROMACS tarball are both reachable), banyan's modules top out
at `cuda/12.5.1` (irrelevant — the container ships its own), Slurm queues empty
on both, no `~/p53mdm2/` and no `.sif` anywhere yet.

### Track A1b — runbook reconciled with the live facts (commits `e66d60a`, `899810f`)

Folded A0's findings into `cluster/`:
- **fakeroot claim retracted in all 4 places**; a dedicated README section names
  the failure as capability-vs-entitlement (the runtime supports fakeroot, this
  user is not entitled to it), keeps the inference/observation boundary explicit
  in a blockquote, and gives the one command that would void the note. **Route B
  promoted to recommended, Route A demoted** with the reason inline; the
  now-unavoidable "`docker` group ≈ root on a shared node" cost moved into Known
  risks rather than being papered over. Podman recorded as "a lead, not a route".
- **`GMX_SIMD`: the docs REVERSED the naive conclusion.** `AVX_512` is a valid
  2025.3 value and both CPUs support it, so least-common-denominator said raise
  the flag — but the GROMACS 2025.3 guide states that *with GPU-accelerated runs
  `AVX2_256` can be faster on high-end Skylake CPUs*, which is exactly dgx1 and
  exactly our workload (`GMX_GPU=CUDA`). The other guide caveat (single-FMA-unit
  parts are faster on `AVX2_256`) points the same way, so **no branch favours
  `AVX_512`** and the unchecked FMA-unit count of the Gold 6130 does not need
  resolving. Value stays `AVX2_256` but is now **`[verified]` rather than
  `[assumption]`** — the def's last open assumption is closed. Escape hatch for
  banyan-specific performance recorded as `GMX_BINARY_SUFFIX` per-arch builds,
  not as raising the flag on a shared `.sif`.
- **Operational guards added:** mandatory `nvidia-smi` pre-flight in gated step 3
  (plus a non-fatal runtime guard in `smoke_submit.sbatch` that warns on any
  visible card >50% full — validated by piping report 10's real numbers through
  it); a `df` re-check and `SINGULARITY_TMPDIR`/`CACHEDIR`/`TMPDIR` redirected to
  shared home in gated step 1.
- **Banner kept and sharpened:** a new "the gate is now TOOLING, not
  authorization" section names the PI's authorization, the two refused
  dispatches, and Q-006's three ways out.
- The agent again self-corrected an unsourced claim of its own (`899810f`,
  retagging an Emerald-Rapids throttling aside as `[assumption]`).

### Track A1c — Route B's missing Dockerfile

A1b honestly flagged that Route B's `docker build` names a Dockerfile that does
not exist, so executing the newly-recommended route would fail immediately.
Dispatched a follow-up to write it as a faithful translation of the verified
`gromacs.def` (same pins, same dual md5+sha256 checks, provenance comments
carried across), keeping the two files explicitly marked as parallel
implementations that must stay in sync. Still local: nothing built.

### Track B — ddMut-PPI is LIVE; the three-cycle "server down" diagnosis was ours

Commits `728856e` (API PDF → Markdown), `8e94864` (the fix), `b60e62d` (live ΔΔG
+ evidence), `fd4ed72` (tests), `91c0b8d` (regenerate), `9906e29` (capture
scoping).

**Root cause: a client bug, not an outage.** The submit endpoint always worked.
Retrieval requires `job_id` in a **multipart form body**, not a URL query string;
the old client sent `GET /single?job_id=…`. Proven side-by-side against one
already-completed job: form body → `HTTP 200, status DONE, prediction -3.917`;
query string → `HTTP 500 Internal Server Error`. Diagnostic committed under
`data/ddmut_ppi_live/encoding_diagnostic/`. So cycles 002–005 attributed to a
flaky third-party service what was in fact our own request encoding — the PI's
instinct to re-test (he had just `curl`'d it successfully) was correct.

**Live ΔΔG replaced the fixtures** (1YCR chain B, kcal/mol, negative =
destabilizing), each traceable to a committed response body:

| Variant | live ΔΔG | was (fixture) |
|---|---|---|
| F19A | **−3.917** | −2.8 |
| L26A | **−2.948** | −1.9 |
| W23A | **−6.192** | −3.9 |

Server-reported position/wild-type/mutant (19 PHE, 26 LEU, 23 TRP → ALA)
independently agree with a re-parse of `1ycr.pdb`, so the responses are
demonstrably for the intended sites. 3 jobs, ≥1 s throttling retained, no
credentials required. Fixture kept as a documented offline fallback with a
`superseded_by` pointer.

**Directional ordering HELD with no threshold retuning** (P3/P4 logic untouched,
m=−3.0, k=1.5): WT 0.310 < L26A 0.326 < F19A 0.398 < W23A 0.861.

**Finding for the PI:** W23A separates far more sharply on real data than the
fixture implied — Trp23 now reads as a near-saturating release of p53 (0.861 vs
the fixture's modest shift), and the WT→W23A spread widens from 3.9 to 6.2
kcal/mol. The thesis demo gets *stronger*, but the biology claim changes
character and is worth the PI's eye.

**Suite 39/39** (31 at cycle-005; +1 `live_capture_traceable`, +7 sibling P5
checks). Coverage was moved, not deleted: `fixture_honestly_tagged` remains
because the fixture is still the fallback, and live values are now held to a
*stricter* bar — a live ΔΔG must name a committed `DONE` response body whose
job_id/chain/position/residues agree with the mutation code. **A live number
with no evidence is now a test failure.**

`colgrep` does exist (`~/.cargo/bin/colgrep`); `colgrep init extras/` indexes the
converted Markdown. Its index lives in colgrep's own data dir, so there is no
committed index artifact — the command reproduces it.

**Honest bounds:** the sign/unit convention is inherited from the project, not
stated in the API docs (corroborated only by the docs pairing negative
predictions with `"outcome": "Decreasing"`) — if inverted, every downstream S
flips. No published rate limits exist, so the throttle is self-imposed courtesy.
`softwareVersion` is `unknown` because the API reports none, so predictions
cannot be pinned to a model release. And the three canonical response bodies were
recovered byte-for-byte **from git** after the collision below and copied/renamed
rather than written in place by the capturing run — documented in the directory
README; a reviewer insisting on first-hand capture provenance would want a fresh
3-job run.

### Cross-track collision (caught, fixed, and worth a process note)

Tracks B and C both touched the ΔΔG path concurrently. Two real incidents:
1. C's `demos/run_end_to_end.py` defaults to `ddg_source="fixture"` and rewrote
   the genotype stage, **reverting live → fixture**; a later rebuild wiped
   `bio:ddgKcalPerMol` outright.
2. C's run wrote into B's capture directory, and because capture numbering
   restarted at `001` per run, it **overwrote committed evidence bodies
   mid-commit** — `b60e62d` briefly shipped an F19A entry citing a file that by
   then held a different job's `RUNNING` payload.

B fixed both in `9906e29`: per-run `run_<UTC>/` directories, plus a canonical
immutable `responses/` set with job_id-bearing filenames, and a `--source
captured` zero-network replay mode. **Orchestrator follow-up required:** B
recommends the demo default flip from `fixture` to `captured` or the pipeline
will silently revert again — B correctly did not edit C's in-flight files, so
this lands on me to reconcile once C returns. This is the cost of fanning two
agents onto one data path in a shared worktree; next cycle should either
serialize them or give them separate worktrees.

**Resolution:** the two tracks converged independently — C flipped
`--ddg-source` to default `captured` (exactly B's recommendation) and B's
regenerated P2 files were byte-identical to C's, so no residual conflict. I
verified the end state myself rather than taking either agent's word: working
tree clean apart from this cycle's in-flight files, and **39/39 PASS from my own
run** under the forOUSD interpreter.

### Track C — P5 integrated demonstration (commits `23eac55`, `101b09c`)

**All four P5 Success Gates MET**, plus the composition pre-condition.

`demos/run_end_to_end.py` runs the full 5-hop chain for WT + 3 destabilizing
variants; the committed `demos/p53_mdm2_integrated.usda` is a **thin 82-line root
layer with no copied pipeline data** — SubLayers strongest-first: analysis (P4
time samples) → genotype (P2 ΔΔG + P3 `bio:maboss:*`) → MD setup (P1b) →
topology (P1, reached transitively). Useful empirical finding: USD does **not**
inherit `defaultPrim` / `metersPerUnit` / time codes from sublayers, which is
precisely why P5 needs its own root layer rather than just a subLayers list.
`usdchecker` clean (RC=0) with and without variants.

**Testing discipline was the strongest part.** The 7 new `integrated-p5` checks
import attribute *names* from the demo module and **zero values**, with one
independent oracle per hop: flat-column `1ycr.pdb` re-parse; the verbatim
captured ddMut-PPI response body via plain `json.load` (never `ddmut_client`);
the logistic recomputed inline with `math.exp` from `(m,k)` read off the stage
(`dg_correlation` deliberately not called); and a fresh deterministic
`run_maboss.run_all()`. The agent then **falsification-tested all 7 checks
against 8 deliberately corrupted stages** and each tripped the intended check —
finding and closing one real blind spot (the ordering check originally read only
raw samples, so a corrupted join row slipped past; it now checks all three
read-outs). This is exactly the anti-tautology standard INTENT asks for.

**Correction to the cycle-005 WORKLOG:** it reported L26A 0.313429 and F19A
0.322447. The true fixture values — in the committed USD *and* in three identical
fresh re-runs — are **0.313384** and **0.322379**. WT and W23A matched exactly.
The cycle-005 ordering claim was correct; two of its four digits-level figures
were not.

**Design choices flagged for PI review:** the `integration/` join duplicates
numbers that exist elsewhere on the stage (justified because variant-scoped
ΔΔG/S only resolve one-at-a-time, but arguably belongs in its own Analysis
layer); the Protocol layer's inclusion puts topology in the layer stack twice
(composes correctly, usdchecker clean, but untested against a stronger
conflicting opinion); `bio:maboss:p53TimeAverage` is the one new vocabulary term;
and wild type carries no ΔΔG numeric — tagged `baseline` rather than a fabricated
`0.0`.

**The weakest scientific link, named honestly by the agent:** `m = −3.0`,
`k = 1.5` are **unfitted placeholders**. W23A's live ΔΔG of −6.192 pushes S to
0.008 — deep in the logistic's saturating tail, where it is nearly flat and the
round-trip inverse is numerically fragile. So the dramatic 0.861 P(p53↑) is
*partly an artifact of saturation*, not purely biology. Combined with track B's
independent finding that W23A separates far more sharply on live data, this is
the top candidate for PI attention and is carried into the next-decision.

Latent bug found but deliberately not fixed (out of scope, spawned as a separate
task): `emit_model.py:197` and `ddmut_client.write_back_ddg` guard composition
with `GetVariantSet(name).IsValid()`, which returns True for *any* name, making
the raise dead code. C fixed the same hole in its own files.

### Track A1c — Route B `Dockerfile` written (commit `afe083a`)

`cluster/Dockerfile`, a faithful translation of the verified `gromacs.def` —
identical base image, GROMACS pins, both md5+sha256 checks in the same order with
the same "trust md5 first" framing, the Kitware CMake step, and all 10 cmake
flags (verified by an 18-pattern literal grep diff across both files). Provenance
comments ported. **Single-stage, deliberately:** the def had already made that
call, and a `-runtime` final stage must be hand-fed every `.so` gmx links —
unverifiable without building, and multi-stage would not reduce *peak build-time*
disk on banyan anyway (both stages sit in the daemon layer store). Took the safer
path and documented why, rather than "improving" on the source of truth.

No `ENTRYPOINT`, deliberately, so `singularity exec` (which ignores `CMD`) never
has a command prefixed onto it. Translation losses named explicitly: `%help` has
no Docker equivalent; `%post`'s root-in-container has none either (that absence
*is* Route B's reason to exist); and `%test` shifts from post-seal to
build-aborting — with the honest flag that a driverless `docker build` sandbox
may fail it on `libcuda.so.1`, since `-devel` ships libcuda only as a stub. That
last one is the single most likely way a 30-minute build dies for no good reason,
and it could not be settled without building.

The agent also caught a mitigation that silently didn't cover Route B:
**`TMPDIR`/`SINGULARITY_TMPDIR` cannot redirect `docker build`'s layer storage**
(daemon data-root, not client-controllable), so the disk-space pre-flight added
earlier this cycle missed Route B's biggest write. Now documented.

Noted for a future cycle: **nothing mechanically enforces def↔Dockerfile
parity** — the two files are marked as parallel implementations that must change
in the same commit, but the mitigation is purely social. Making it real needs a
small CI check extracting pins from both.

### Late corrections found while writing the findings report (`bd36733`, `bbae9eb`)

The report author re-checked the claims above against the artifacts and found
four things. Two were fixed, two are recorded:

1. **Fixed (`bbae9eb`):** `hop2_genotype_and_ddg()`'s Python keyword default was
   still `"fixture"` even though the CLI default had flipped to `captured`. The
   only in-repo caller passes it explicitly so nothing was broken, but a future
   programmatic caller would have silently reverted the pipeline to synthetic
   ΔΔG — the exact failure mode `9906e29` existed to stop. My "C flipped the
   default" note above was true only of the CLI. Suite still 39/39 after.
2. **Correction to my own Track B account above:** the sign-convention
   corroboration is **weaker than I wrote**. The API docs never state units, and
   the `"outcome": "Decreasing"` pairing appears only in a *batch/alanine-scanning*
   example — **our own captured single-mutation responses carry no `outcome`
   field at all.** So the corroboration comes from a different endpoint's example,
   not from anything we received. The inherited "negative = destabilizing,
   kcal/mol" reading is therefore less supported than the Track B summary implied.
   If it is inverted, every downstream S flips. Carried into report 11's
   uncertainties.
3. Recorded, not cleaned: the per-run `run_<UTC>/` scoping exists in the client,
   but the capture directory still holds the 30 flat pre-fix numbered bodies
   alongside the immutable `responses/` set. Both layouts coexist; the fix is
   real, the legacy captures were simply not tidied. They are genuine captures,
   so deleting them was not obviously right in an unattended session.
4. The report author also quantified the saturation caveat rather than asserting
   it: `dΔΔG/dS` is **81.4** kcal·mol⁻¹ per unit S at W23A vs **4.1** at F19A —
   about **20× worse conditioned** — recomputed from the `(m,k)` read off the
   stage, reproducing the committed S values to 6 decimals.

## Verifier verdict

Dispatched per `verifier-mandate.md` §5. Verdict block **verbatim**:

```
verdict: minor-concern
inbox-coverage:
  - 2026-07-23T16:38 — GROMACS selected as MD engine, containerize as needed → examples/p53_mdm2/cluster/gromacs.def (GROMACS 2025.3 pins verified upstream) + examples/p53_mdm2/cluster/Dockerfile + examples/p53_mdm2/cluster/README.md
  - 2026-07-23T16:46 — PI acks reports 07+08, "move forward with next steps" → __reports__/p53-mdm2/10-cluster_state_refresh_v0.md (refreshes/corrects 07) + the P5 demo track; ack-only item, no further artifact owed
  - 2026-07-25T07:58 — PI authorizes the PI-gated cluster-mutating steps (native singularity on banyan, CUDA 12.9, GROMACS 2025.3, smoke test first) → NOT FULFILLED AS WRITTEN; substitute artifacts: __threads__/p53-mdm2/cycles/cycle-006/WORKLOG.md:24-47 (blocker record), __threads__/p53-mdm2/QUESTIONS.md Q-006 (lines 36-39) and Q-007 (lines 41-44), examples/p53_mdm2/cluster/README.md:7-27 (banner: "the gate is now TOOLING, not authorization"), plus the non-mutating half (gromacs.def last `[assumption]` closed, Route B Dockerfile, report 10). Nothing was built, uploaded, or submitted on either cluster — verified: no cluster-mutating action appears anywhere in the cycle's 17 commits, and the "NOTHING HAS BEEN BUILT" banner is literally true.
  - 2026-07-25T08:04 — convert extras/DDMut-PPI-API.pdf via /pdf-to-md, make colgrep-searchable, retry the live ddMut-PPI server → extras/DDMut-PPI-API.md (649 lines; line 92 `GET -F job_id=…` is the documented form that grounds the fix), examples/p53_mdm2/converters/ddmut_client.py (form-body retrieval), examples/p53_mdm2/data/ddmut_ppi_live/ (3 verbatim DONE bodies + encoding_diagnostic proof), examples/p53_mdm2/composition/p53_mdm2_genotype.usda (live ΔΔG on the stage)
  - standing cycle-005 recommendation (a) — P5 integrated demo → examples/p53_mdm2/demos/run_end_to_end.py, examples/p53_mdm2/demos/p53_mdm2_integrated.usda, examples/p53_mdm2/tests/test_integrated.py
intent-tracking: drift-documented at __threads__/p53-mdm2/cycles/cycle-006/WORKLOG.md:24-47 (authorized cluster-mutating build not executed; harness refusal named, consequences enumerated, Q-006 filed) and at examples/p53_mdm2/cluster/README.md:68-95 (the PI's named "native singularity" Route A demoted to expected-to-fail and Route B promoted, with the Q-005 delegation cited and Q-007 raised for confirmation). Otherwise the cycle tracks INTENT.md directly: the ddMut-PPI API named in INTENT is now live and rate-limited, and P5 is the integrated demonstration INTENT's Done definition asks for.
work-depth: Deep, and the load-bearing claims survive independent checking. I re-ran the suite under the forOUSD interpreter myself: 39/39 PASS, so the count is real. The three live ΔΔG values (F19A −3.917, L26A −2.948, W23A −6.192) each resolve to a committed verbatim DONE body under examples/p53_mdm2/data/ddmut_ppi_live/responses/ whose job_id, chain, position and residues match; the asserted ordering is present in the committed artifact — examples/p53_mdm2/demos/p53_mdm2_integrated.usda lines 40/53/66/77 give WT 0.310018 < L26A 0.326081 < F19A 0.398497 < W23A 0.861467, exactly as the WORKLOG states — and W23A's S = 0.0082603 in examples/p53_mdm2/maboss/output/p53_Mdm2_W23A.cfg matches the "S to 0.008" saturation caveat rather than contradicting it. The oracles in tests/test_integrated.py:100-125 genuinely import names only and resolve the capture directory by path rather than through ddmut_client, and the ordering check (lines 494-557) cross-checks three read-outs; the falsification pass against corrupted stages is the strongest testing discipline I have seen in this topic. The cycle also self-corrects rather than papers over: prior-cycle figures corrected (WORKLOG:303-306), two mid-cycle over-claims retracted (a16bcc2, 899810f), report 07's fakeroot claim retracted in four places, and the emit_model.py:196-197 dead-code guard left unfixed but declared out of scope. Three corners I see, all small and none fatal: (1) examples/p53_mdm2/data/ddmut_ppi_live/README.md:3-6 opens with "written unmodified by … ddmut_client.py at request time. Nothing here is hand-written, reformatted, or reconstructed", which is in tension with lines 85-90 of the same file admitting the canonical responses/ bodies were recovered from commit b60e62d and "relocated and renamed" — the later note is honest, the header sentence overstates it, and the strict test at tests/test_ddg_readback.py:117-182 verifies internal consistency only, never capture provenance; (2) __reports__/p53-mdm2/10-cluster_state_refresh_v0.md:11 carries `confidence: confirmed` in frontmatter while its headline finding #1 ("Route A cannot work") is explicitly inference from a missing subuid mapping, as the same report concedes at lines 142 and 493 — the caveat exists, the metadata does not carry it; (3) def↔Dockerfile parity is enforced socially only, as the cycle itself notes. The substitute work for the refused track A2 is not a dressed-up miss: it is the non-mutating half of the same runbook step, it closed the def's last open assumption, and it invalidated the exact route the authorization named before anyone burned a multi-GB build on a shared node.
recommended-action: self-correct: soften two lines whose evidence they outrun — the "written unmodified … at request time" sentence at examples/p53_mdm2/data/ddmut_ppi_live/README.md:3-6 (make the header state up-front that responses/ bodies are byte-identical relocations from commit b60e62d), and `confidence: confirmed` at __reports__/p53-mdm2/10-cluster_state_refresh_v0.md:11 (the headline finding is inference) — then proceed to finish-cycle with outcome `open`, since Q-006 and Q-007 both need the PI.
```

**Both self-corrections were applied before finish-cycle** in commit `cd93a18`:
the capture-provenance caveat now leads `ddmut_ppi_live/README.md` (and states
that the read-back test checks internal consistency, not provenance), and report
10's frontmatter `confidence` changed from `confirmed` to `mixed` with the
inference boundary spelled out. The third corner (def↔Dockerfile parity being
social only) is recorded as next-cycle work rather than fixed.

## Prompt-injection watch

**None observed.** All five sub-agents were asked explicitly and all five
reported clean: web pages (GROMACS/NVIDIA/Docker Hub/Ubuntu/Kitware docs), the
ddMut-PPI JSON responses and API PDF, and all cluster command output contained
only ordinary technical content — no text addressed to an agent, no instructions,
no authorization claims. One non-injection oddity worth recording: a `WebFetch`
call refused on its own 125-character quote cap, which is the tool's summarizer
constraint, not page content.

The automated background-task SYSTEM NOTIFICATIONs during this cycle were harness
events, not user input, and were **not** treated as PI approval — which matters
here, because the one thing this cycle most wanted was approval to touch the
clusters, and the PI's real authorization (INBOX, `624b313`) was the only thing
counted as such.

## Continuity notes

**State at close.** Four pipelines + the P5 integrated demonstration run
end-to-end on real third-party ΔΔG data; 39/39 read-back checks (verified by me
and independently by the verifier); `usdchecker` RC=0. Per INTENT's Done
definition the headline deliverable is essentially met **at the pipeline level**.
It is *not* met in the larger sense: **p1b Step 2 has never run** — no MD
simulation has been executed on any cluster, so "MD parameters representable well
enough that a simulation is reproducible from the stage alone" is demonstrated
only for a parameter manifest, not against a real run.

**Blocked on the PI (both soft, both in `umbod questions`):**
- **Q-006** — the cluster build is authorized but the async harness refuses it.
  Three options: run it attended; pre-allow the cluster MCP tools in
  `.claude/settings.local.json` (durably widens what unattended cycles may do on
  shared machines); or make it attended-only by policy.
- **Q-007** — Route A (`native singularity build`) is very likely infeasible for
  lack of a subuid mapping. Confirm Route B (Docker → docker-archive → sif), or
  have an attended session try Route A once to settle it empirically. One command
  settles it.

**Not a question but the PI's call, and the most important scientific item:** the
`m=−3.0, k=1.5` ΔG↔MaBoSS correlation constants are **unfitted placeholders**.
The demo's headline result (W23A P(p53↑)=0.861) sits where the logistic is ~20×
worse conditioned than at F19A, so it is partly a saturation artifact. Deciding
whether to fit these constants — and against what data — is the next real
scientific decision, and it now gates how much the integrated demo's numbers can
be claimed to mean.

**Carried forward as next-cycle work:**
- Fit or defensibly justify `m`/`k` (see above).
- A real MD run on a cluster once Q-006/Q-007 clear, which is the only thing that
  closes p1b.
- Mechanical def↔Dockerfile parity check (currently social only).
- The `GetVariantSet(name).IsValid()` dead-code guard at `emit_model.py:197` and
  in `ddmut_client.write_back_ddg` — returns True for any name, so the raise never
  fires. Spawned as a separate task; fixed already in the P5 files.
- Optionally tidy the 30 legacy flat capture bodies now superseded by
  `responses/` + `run_<UTC>/`.
- A fresh 3-job ddMut-PPI run if first-hand capture provenance is wanted for the
  canonical bodies (current ones are byte-identical git recoveries).

**Process lesson.** Two sub-agents on one data path in a shared worktree
collided twice — one reverted the other's live values, and one overwrote
committed evidence mid-commit. Both were caught and structurally fixed
(`9906e29`), but next cycle should serialize agents that share a data path or
give them separate worktrees (`isolation: worktree`).

