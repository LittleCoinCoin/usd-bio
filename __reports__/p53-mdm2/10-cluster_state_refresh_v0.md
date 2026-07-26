# p53-MDM2 — Cluster State Refresh (banyan + dgx1), delta vs report 07 — Observation (v0)

Date: 2026-07-27

---
type: observation
topic: p53-mdm2
spotted-during: cycle-006 read-only state refresh of banyan/dgx1 ahead of the PI-attended GROMACS container build (p1b Step 2)
date: 2026-07-27
domain: other
confidence: confirmed
urgency: high
deferred-because: Every remedy is a cluster-mutating or file-writing action; this pass was mandated read-only, so findings are recorded rather than acted on.
---

## What Was Noticed

Three things changed since report 07 (cycle-004), and one of them blocks the
build route the runbook recommends:

1. **`singularity build gromacs.sif gromacs.def` (Route A) cannot work for user
   `eliott` on banyan.** `--fakeroot` needs a `/etc/subuid` + `/etc/subgid`
   mapping, and `eliott` has none on either cluster. The runbook asserts banyan
   "has singularity-ce 4.2.2 + fakeroot"; the fakeroot half was never verified
   and is false.
2. **banyan GPU 0 is no longer free.** Another user's vLLM process holds
   86061 MiB of 95830 MiB, and Slurm reports the node `idle` — so Slurm can hand
   a GPU job the already-occupied card.
3. **Both clusters' CPUs support AVX-512**, which report 07 never recorded and
   which makes `gromacs.def`'s `[assumption] GMX_SIMD=AVX2_256` a conservative
   guess rather than the required value.

Newly recorded this pass (absent from report 07): CPU/SIMD inventory, the rsync
resolution, outbound-internet status, and registry/tarball reachability.

**The CPU/SIMD data directly answers the one open `[assumption]` left in
`gromacs.def`.** A sibling agent's cycle-006 upstream-verification pass reduced
that file to a single unverified value and named this exact gap as the reason:

> "Exactly ONE item remains `[assumption]` — GMX_SIMD — because the cluster CPU
> models were never recorded by the live recon (report 07 has GPUs, drivers,
> Slurm and singularity versions, but NO `lscpu` output)."

and prescribed the resolution: "On BOTH clusters run: `lscpu | grep -E 'Model
name|Flags' …`; Set GMX_SIMD to the highest level supported by BOTH machines
(the least common denominator), NOT by the build host alone."
`[source: examples/p53_mdm2/cluster/gromacs.def lines 24-28 and 257-270, as committed at a16bcc2/3f731c3]`
Section 4 below supplies that data.

## Context

Cycle-006, read-only refresh. Report 07's baseline was 6 days old and two
PI-side changes had landed (Q-005: a `~/.banyan/config.json` was added; an
rsync ≥ 3.0 "is installed but you have to search and adapt the PATH for it").
A future PI-attended session needs trustworthy facts before running the gated
build in `examples/p53_mdm2/cluster/README.md`. No command in this pass wrote,
created, installed, submitted, or downloaded anything; the heaviest calls were
HTTP `HEAD` requests and a registry manifest `HEAD`.

Deferred because every fix (creating `~/p53mdm2/`, building a `.sif`, changing
`gromacs.def`) is either cluster-mutating or outside this pass's file scope
(`__reports__/p53-mdm2/` only). Q-006 already records that the harness refuses
cluster-mutating dispatches in unattended sessions.

## Location Map

- `__reports__/p53-mdm2/07-cluster_liveverify_v1.md` — the superseded baseline this report deltas against
- `examples/p53_mdm2/cluster/README.md` — runbook; §"PI-gated mutating steps" step 1 Route A is the invalidated claim; "banyan (has singularity-ce 4.2.2 + fakeroot)" at gated step 1 and open sub-decision (b)
- `examples/p53_mdm2/cluster/gromacs.def` — **as revised by a sibling this cycle** (`a16bcc2`, `3f731c3`): line 94 `From: nvidia/cuda:12.9.1-devel-ubuntu22.04` (tag now registry-verified, §10); line 122 `GROMACS_URL` (now HTTP-verified, §10); lines 125-140 `GROMACS_MD5` + corroborated SHA256 (**resolved by the sibling, not by me**); line 254 `-DGMX_SIMD=AVX2_256` + lines 257-275 the sole remaining `[assumption]`, which §4 below resolves
- `examples/p53_mdm2/cluster/smoke_submit.sbatch` — the GPU-selection concern in finding 2 lands here
- `__threads__/p53-mdm2/QUESTIONS.md` — Q-005 (PI config/rsync note, lines 27-34), Q-006 (harness permission block, lines 36-39)
- banyan `/etc/subuid`, `/etc/subgid` — the fakeroot blocker
- banyan `/opt/singularity/4.2.2/etc/singularity/singularity.conf` — runtime policy (permissive)
- Cluster home (shared): `/home/eliott` on `ts2:/export/home`, identical from both hosts

## Evidence

### 1. Reachability + the PI's banyan config — WORKS

`~/.banyan/config.json` is a **client-side** file on the laptop, not on the
cluster. It is present, and all cluster tools succeeded on both hosts with zero
rsync errors across ~14 calls.

```
-rw-r--r--  1 hacker staff   32 Jul 21 00:51 /Users/hacker/.banyan/config.json
-rw-r--r--  1 hacker staff   30 Jun 25 15:33 /Users/hacker/.dgx1/config.json
```
`[source: local ls -la ~/.banyan/ ~/.dgx1/]`

> Caution for future readers: report 07 recorded `[live: test -f ~/.banyan/config.json → present]` without stating *which side*. Running `test -f ~/.banyan/config.json` **on banyan** returns `config ABSENT` — that is a different, irrelevant file. `[source: banyan run_command_on_cluster: test -f ~/.banyan/config.json && echo "config present" || echo "config ABSENT" → "config ABSENT"]`

### 2. Singularity — UNCHANGED (skew persists)

| | banyan | dgx1 |
|---|---|---|
| version | `singularity-ce version 4.2.2` | `singularity version 3.5.2` |
| path | `/opt/singularity/4.2.2/bin/singularity` (module, loaded) | `/usr/local/bin/singularity` |
| apptainer | `apptainer: not found` | `apptainer: not found` |
| mksquashfs | `mksquashfs version 4.5 (2021/07/22)` | `mksquashfs version 4.6.1 (2023/03/25)` |

`[source: singularity --version; command -v apptainer; command -v singularity; mksquashfs -version — both clusters]`

banyan runtime policy is permissive:
```
allow setuid = yes
allow user ns = yes
allow container sif = yes
allow container squashfs = yes
mksquashfs path = /usr/bin/mksquashfs
```
`[source: banyan grep -E '^(allow setuid|allow user ns|allow container|mksquashfs)' /opt/singularity/4.2.2/etc/singularity/singularity.conf]`

### 3. THE BUILD BLOCKER — no fakeroot for `eliott` on either cluster (NEW)

```
=== subuid file exists? ===
-rw-r--r-- 1 root root 36 Feb 21  2025 /etc/subgid
-rw-r--r-- 1 root root 36 Feb 21  2025 /etc/subuid
=== contents (all) ===
user:100000:65536
test:165536:65536
--- subgid ---
user:100000:65536
test:165536:65536
```
`[source: banyan cat /etc/subuid /etc/subgid]` — no `eliott` line.

```
lxd:100000:65536
root:100000:65536
```
`[source: dgx1 cat /etc/subuid]` — no `eliott` line.

Unprivileged user namespaces are otherwise enabled on banyan
(`kernel.unprivileged_userns_clone = 1`, `max_user_namespaces = 4125984`)
`[source: banyan sysctl kernel.unprivileged_userns_clone; cat /proc/sys/user/max_user_namespaces]`,
so the constraint is specifically the **missing subuid/subgid range**, not a
kernel lockdown.

`gromacs.def` has a `%post` that runs `apt-get install` and compiles — that
requires root-in-container, i.e. `--fakeroot`. Route A therefore cannot run as
`eliott`. `[assumption: singularity's documented requirement that unprivileged --fakeroot builds need an /etc/subuid mapping for the invoking user; I did NOT attempt a build (mutating), so this is inference from the missing mapping, not an observed build failure.]`

**Route B remains open** — `eliott` is in the `docker` group on banyan and the
daemon answers:
```
uid=1000011(eliott) gid=1000000(Domain Users) groups=1000000(Domain Users),999(docker),1000013(eliott),1000018(www-data-ldap)
docker:x:999:test,user,su,knishida,eliott,isobe
29.4.3 containers=20 running=11 images=51
```
`[source: banyan id; getent group docker; docker info --format ...]`

dgx1 is unchanged — still no docker group membership:
```
uid=1000011(eliott) ... groups=1000000(Domain Users),1000013(eliott),1000018(www-data-ldap)
docker:x:999:ochiai,kotone,shafi,knishida,isobe,ntanaka,su
```
`[source: dgx1 id; getent group docker]`

`podman version 3.4.4` is installed on banyan and reports rootless `true`
`[source: banyan podman --version; podman info --format '{{.Host.Security.Rootless}}']`,
but rootless podman builds also consume subuid ranges, so I do not claim it as
a working route. `proot: NOT FOUND` `[source: banyan command -v proot]`.

### 4. CPU / SIMD — NEWLY RECORDED (both support AVX-512)

| | banyan | dgx1 |
|---|---|---|
| Model | `INTEL(R) XEON(R) GOLD 6530` | `Intel(R) Xeon(R) Gold 6130 CPU @ 2.10GHz` |
| family/model/stepping | 6 / 207 / 2 | 6 / 85 / 4 |
| CPUs (threads) | 128 (2 sock × 32 core × 2 SMT) | 64 (2 sock × 16 core × 2 SMT) |
| NUMA nodes | 4 | 2 |
| RAM (Slurm) | 1031000 MB | 754000 MB |

banyan SIMD flags:
`avx avx2 avx512_bf16 avx512_bitalg avx512bw avx512cd avx512dq avx512f avx512_fp16 avx512ifma avx512vbmi avx512_vbmi2 avx512vl avx512_vnni avx512_vpopcntdq avx_vnni f16c fma sse4_1 sse4_2`
(plus `amx_bf16 amx_tile amx_int8`)

dgx1 SIMD flags:
`avx avx2 avx512bw avx512cd avx512dq avx512f avx512vl f16c fma sse4_1 sse4_2`

`[source: lscpu on both clusters; flags extracted via lscpu | grep '^Flags' | tr ' ' '\n' | grep -E 'avx|sse4|fma|f16c']`

**Common denominator = AVX-512 core set** (`avx512f`, `avx512dq`, `avx512bw`,
`avx512vl`, `avx512cd`) present on both. banyan adds VNNI/BF16/FP16/IFMA/VBMI
and AMX; dgx1 (Skylake-SP) has only the core set.
`[assumption: GROMACS's GMX_SIMD=AVX_512 requires only that core F/DQ/BW/VL set, so a single .sif built with AVX_512 would run on both CPUs. I did not compile or run GROMACS to confirm, and did not consult the GROMACS docs in this pass.]`

### 5. Shared home + free space — MOSTLY UNCHANGED; banyan root disk shrank

| | banyan | dgx1 |
|---|---|---|
| `/home` | `ts2:/export/home  29T  16T  13T  56%` | `ts2:/export/home  29T  16T  13T  56%` |
| root disk | `/dev/nvme0n1p4  900G  461G  439G  52%` | `/dev/mapper/dgx1--vg-root  1.7T  881G  772G  54%` |

`[source: df -h /home /home/eliott /tmp / — both clusters]`

Home is confirmed still one shared NFS: `ls -la ~` returned byte-identical
33-entry listings from both hosts `[source: ls -la ~ | head -40 on both clusters — identical output]`.

**Neither `~/p53mdm2/` nor any `.sif` exists:**
```
ls: cannot access '/home/eliott/p53mdm2': No such file or directory
=== any .sif in home ===
(end sif search)
```
`[source: ls -la ~/p53mdm2; find ~ -maxdepth 3 -name '*.sif' — both clusters, no hits]`

Home free space is unchanged at 13 T. banyan's root disk dropped from 586 G to
**439 G** available (−147 G) since report 07; dgx1's went 769 G → 772 G. `/tmp`
still collapses onto the root filesystem on both — report 07's finding holds.

### 6. Slurm — versions UNCHANGED, queues empty, but GPU accounting is blind

| | banyan | dgx1 |
|---|---|---|
| version | `slurm 22.05.2` | `slurm-wlm 23.11.4` |
| partition | `all*  up  5-00:00:00  1 node` (default, `AllowGroups=ALL`, no account) | same shape |
| GRES | `gpu:nvidiah100nvl:2,mps:nvidiah100nvl:200` | `gpu:nvidiav100sxm2:8` |
| CPUs A/I/O/T | `0/128/0/128` | `0/64/0/64` |
| node state | `IDLE`, `CPULoad=0.71`, `FreeMem=505908` | `IDLE`, `CPULoad=0.02`, `FreeMem=725219` |
| queue depth | `0` | `0` |
| limits | `MaxTime=5-00:00:00`, `DefMemPerNode=UNLIMITED`, `MaxMemPerNode=UNLIMITED`, `OverSubscribe=NO`, `PreemptMode=OFF` | same |

`[source: sinfo --version; sinfo -o '%P %a %l %D %T %C %G %m %N'; squeue -o ...; squeue -h | wc -l; scontrol show partition; scontrol show node — both clusters]`
`[source: get_resources both clusters → allocated 0 / idle 1 / total 1; get_job_statuses([]) → [] on both]`

### 7. banyan GPU 0 is occupied by another user — CHANGED

```
|   0  NVIDIA H100 NVL   On  | 00000000:27:00.0 Off |    0 |
| N/A  48C  P0   98W / 400W  |  86061MiB / 95830MiB |   0%  Default |
|   1  NVIDIA H100 NVL   On  | 00000000:38:00.0 Off |    0 |
| N/A  40C  P0   62W / 400W  |      0MiB / 95830MiB |   0%  Default |
...
|    0   N/A  N/A   227186   C   VLLM::EngineCore        86052MiB |
```
`[source: banyan nvidia-smi]` — PID 227186 is owned by `ntanaka`
`[source: banyan ps -o user= -p 227186 → ntanaka]`.

Only ~9.7 GB is free on GPU 0; GPU 1 is fully free. Slurm nonetheless reports
the node `IDLE` with `AllocTRES=` empty — the vLLM process is unscheduled, so
**Slurm can assign a `--gres=gpu:1` job to GPU 0.** The docs confirm isolation
is soft: "GPU isolation is soft: `nvidia-smi` still lists all eight cards even
in a one-GPU job" `[source: dgx1-docs search_docs → dgx1_guide.md#using-the-gpus]`.

dgx1 is fully idle — 8× V100, `4MiB / 16384MiB` used per card, "No running
processes found" `[source: dgx1 nvidia-smi]`.

Drivers and compute capabilities (UNCHANGED from report 07, now with compute_cap
recorded explicitly):

| | banyan | dgx1 |
|---|---|---|
| driver | `595.71.05` | `580.159.03` |
| max CUDA runtime | `CUDA Version: 13.2` | `CUDA Version: 13.0` |
| GPUs | 2× `NVIDIA H100 NVL`, `compute_cap 9.0`, 95830 MiB | 8× `Tesla V100-SXM2-16GB`, `compute_cap 7.0`, 16384 MiB |

`[source: nvidia-smi --query-gpu=index,name,compute_cap,memory.total,memory.used,utilization.gpu,driver_version --format=csv — both clusters]`

This confirms the runbook's `GMX_CUDA_TARGET_SM="70;90"` choice against live
`compute_cap` values rather than inferred ones.

### 8. Modules and host toolchain — UNCHANGED in shape; no CUDA 12.9 module

banyan `module avail` (Environment Modules; `/opt/modulefiles`):
`bazel/5.3.0  cmake/3.25.3  cuda/11.8.0  cuda/12.5.1  cudnn/8.6.0.163/cuda-11
ffmpeg/5.1.3  Frameworks/4.0/{opencv,openmpi/4.1.4,python/3.10.9-*,pytorch-2.0.1,tensorflow*}
gcc/{10.5.0,11.3.0,11.4.0,12.3.0}  go/1.23.3  lmdb/0.9.29  nccl/2.17.1/cuda-11.0
python/3.10.9/base  singularity/4.2.2 <L>  slurm/22.05.2 <L>  TensorRT/8.5.3.1
TurboVNC/3.0.3` + `nvhpc/24.7` variants + Intel oneAPI (`compiler/2023.1.0`,
`mkl/2023.1.0`, `mpi/2021.9.0`, …)
`[source: banyan module avail]`
Loaded by default: `go/1.23.3 <aL>, singularity/4.2.2, slurm/22.05.2`
`[source: banyan module list]`

dgx1: `module: NOT FOUND` — no module system, as documented
`[source: dgx1 command -v module → not found; dgx1-docs → dgx1_guide.md#software-no-module-system]`.

Host toolchain on PATH (relevant only to a *host-side* build; the container
supplies its own):

| tool | banyan | dgx1 |
|---|---|---|
| gcc/g++ | 12.3.0 | 13.3.0 |
| cmake | 3.22.1 | **NOT FOUND** |
| nvcc | **NOT FOUND** (needs `module load cuda/…`) | 12.0.140 at `/usr/bin/nvcc` |
| mpicc / mpirun | NOT FOUND | NOT FOUND |
| **gmx** | **NOT FOUND** | **NOT FOUND** |
| python3 | 3.9.6 | 3.9.6 |
| libfftw3f | `/lib/x86_64-linux-gnu/libfftw3f.so.3` | same |

`[source: for t in gcc g++ cmake make nvcc mpicc mpirun gmx python3; command -v; ldconfig -p | grep fftw — both clusters]`

**Max CUDA module on banyan is `cuda/12.5.1`** — there is no 12.9 module. The
`.def`'s CUDA 12.9 comes from the container base image, so this is not a
blocker, but it rules out a host-side 12.9 build. No MD engine on either host,
so report 07's "containerizing is genuinely required" premise still holds.

### 9. rsync ≥ 3.0 — RESOLVED (PI's Q-005 item)

The PI's note ("`rsync` >= 3.0 IS installed but you have to search and adapt the
PATH for it") concerns the **laptop**, not the clusters. It is already correct on
the default PATH — no export needed:

```
-- default PATH resolution:
/opt/homebrew/bin/rsync
rsync  version 3.4.4  protocol version 32
-- all candidates:
/opt/homebrew/bin/rsync -> rsync  version 3.4.4  protocol version 32
/usr/bin/rsync -> openrsync: protocol version 29
-- brew prefix:
/opt/homebrew/opt/rsync
```
`[source: local which rsync; rsync --version; per-prefix loop; brew --prefix rsync]`

**The canonical path is `/opt/homebrew/bin/rsync` (3.4.4), brew prefix
`/opt/homebrew/opt/rsync`.** `/opt/homebrew/bin` precedes `/usr/bin` in the
current PATH, so `rsync` resolves to 3.4.4 already. The only ≥3.0-failing binary
is macOS's `/usr/bin/rsync` (openrsync, protocol 29). Repair line if a future
session lands on a PATH where openrsync wins:
`export PATH=/opt/homebrew/bin:$PATH`.

Cluster-side rsync is fine and was never the issue — **3.2.7 on both**:
```
/usr/bin/rsync -> rsync  version 3.2.7  protocol version 31
/bin/rsync -> rsync  version 3.2.7  protocol version 31
```
`[source: which -a rsync; rsync --version; prefix loop; find /usr /opt /snap ~/bin ~/.local -name rsync -type f -perm -u+x — both clusters. No other rsync binary exists on either.]`

### 10. Outbound internet — WORKS on both (NEW)

DNS and HTTPS both succeed; **no proxy variables are set**.

```
=== DNS ===
2600:1f18:2148:bc01:... registry-1.docker.io
2001:6b0:1:1191:216:3eff:fec7:6e30 gromacs-ftp.biophysics.kth.se ftp.gromacs.org
=== HTTPS HEAD docker registry ===
HTTP/2 401
docker-distribution-api-version: registry/2.0
=== HTTPS HEAD gromacs tarball ===
HTTP/1.1 200 OK
Last-Modified: Fri, 29 Aug 2025 14:21:27 GMT
Content-Length: 44407119
Content-Type: application/x-gzip
=== proxy env ===
(no proxy vars)
```
`[source: getent hosts registry-1.docker.io ftp.gromacs.org; curl -sS -I -m 20 https://registry-1.docker.io/v2/; curl -sS -I -m 20 https://ftp.gromacs.org/gromacs/gromacs-2025.3.tar.gz; env | grep -i proxy — identical results on BOTH clusters]`

The `HTTP/2 401` from the registry is the expected unauthenticated-probe
response (it proves reachability, not failure). **A container build can pull its
base image and fetch the GROMACS tarball from either cluster.**

This independently confirms two of `gromacs.def`'s pinned values are *fetchable*
from the clusters themselves (the sibling agent verified them against upstream
docs; I verified the endpoints answer from banyan and dgx1):

| `.def` value | Verdict | Evidence |
|---|---|---|
| `nvidia/cuda:12.9.1-devel-ubuntu22.04` tag exists | **VERIFIED** | manifest `HEAD` → `200` (and `12.9.0-devel-ubuntu22.04` → `200`) `[source: banyan authenticated curl HEAD on registry-1.docker.io/v2/nvidia/cuda/manifests/<tag>]` |
| `GROMACS_URL` reachable, correct pattern | **VERIFIED** | `HTTP/1.1 200 OK`, 44407119 bytes, `Last-Modified: Fri, 29 Aug 2025` `[source: curl -I https://ftp.gromacs.org/gromacs/gromacs-2025.3.tar.gz — from BOTH clusters]` |
| `GROMACS_MD5` / SHA256 | **already resolved by the sibling agent** — not by me | `GROMACS_MD5=5a2315b6f6e13b091bbbbfddee9eb62b` from the official download page, plus a Spack/EasyBuild-corroborated sha256 `[source: examples/p53_mdm2/cluster/gromacs.def lines 125-140]`. I did **not** download the tarball, so I contribute no independent hash check. |

---

## Delta Summary vs Report 07

| # | Fact | Report 07 | Now | Status |
|---|---|---|---|---|
| 1 | banyan client config works | present | present + all calls clean | **unchanged** |
| 2 | Singularity versions | 3.5.2 / 4.2.2 | 3.5.2 / 4.2.2 | **unchanged** |
| 3 | Drivers | 580.159.03 / 595.71.05 | same | **unchanged** |
| 4 | GPU inventory | 8×V100-16GB / 2×H100-95830MiB | same | **unchanged** |
| 5 | **banyan GPU utilisation** | "both idle" | **GPU 0: 86061/95830 MiB (ntanaka vLLM); GPU 1 free** | **CHANGED** |
| 6 | Slurm versions | 23.11.4 / 22.05.2 | same | **unchanged** |
| 7 | Queue depth | 0 / 0 | 0 / 0 | **unchanged** |
| 8 | Shared home `ts2:/export/home` | 29T, 13T avail | 29T, 13T avail | **unchanged** |
| 9 | **banyan root-disk free** | 586 G | **439 G (−147 G)** | **CHANGED** |
| 10 | dgx1 root-disk free | 769 G | 772 G | ~unchanged |
| 11 | `~/p53mdm2/`, `gromacs.sif` | absent | still absent | **unchanged** |
| 12 | docker group split | banyan yes / dgx1 no | same | **unchanged** |
| 13 | No MD engine anywhere | none | none | **unchanged** |
| 14 | **`--fakeroot` availability** | asserted (never tested) | **NO subuid mapping on either cluster** | **CORRECTED — false** |
| 15 | **CPU model + SIMD** | not recorded | **Gold 6530 / Gold 6130; AVX-512 on BOTH** | **NEW** |
| 16 | **rsync ≥ 3.0 location** | "already correct, unexplained" | **`/opt/homebrew/bin/rsync` 3.4.4 (local); 3.2.7 on both clusters** | **NEW / resolved** |
| 17 | **Outbound internet** | not tested | **works on both, no proxy** | **NEW** |
| 18 | **CUDA base tag + tarball URL** | assumed | **both verified reachable from the clusters** | **NEW** |
| 19 | Max CUDA module on banyan | (implied 12.5.1) | `cuda/12.5.1`, no 12.9 | clarified |
| 20 | podman on banyan | not recorded | `3.4.4`, rootless `true` | **NEW** |

## Before You Build — the facts that matter

1. **Route A is dead as written.** `singularity build gromacs.sif gromacs.def`
   needs `--fakeroot`; `eliott` has no `/etc/subuid` entry on **either**
   cluster. Use **Route B** (docker build on banyan → `docker save` →
   `singularity build gromacs.sif docker-archive://…`), or ask an admin for a
   subuid range, or build off-cluster. Update the runbook's step-1 recommendation
   and open sub-decision (b) — both currently claim fakeroot is available.
2. **Do the conversion on banyan.** It has the docker daemon (29.4.3, `eliott`
   in group) and singularity 4.2.2. dgx1 has neither docker access nor fakeroot.
3. **Internet works from both clusters, no proxy** — the base image pull and
   tarball fetch will succeed on-cluster.
4. **The two fetchable `.def` pins answer from the clusters**: the
   `12.9.1-devel-ubuntu22.04` manifest returns 200, and the tarball URL returns
   200 (44407119 bytes). Hashes were already resolved by the sibling agent's
   pass; I add no independent hash check.
5. **`gromacs.def`'s last `[assumption]` is now answerable.** Its own
   instruction — "set GMX_SIMD to the highest level supported by BOTH machines
   (the least common denominator)" — evaluates to **`AVX_512`**: both CPUs carry
   `avx512f/dq/bw/vl/cd`. dgx1's Skylake-SP has *only* that core set (banyan
   adds VNNI/BF16/FP16/IFMA/VBMI/AMX), so **dgx1 is the least common
   denominator** and the ceiling for one portable `.sif`. `AVX2_256` remains a
   safe floor. Confirm against the GROMACS 2025.3 install guide before changing
   the flag — and note GROMACS documents AVX-512 being situationally *slower*
   on some Skylake SKUs, so this is a "now decidable", not "obviously raise it".
6. **On banyan, pin the GPU.** GPU 0 holds another user's 86 GB vLLM process
   while Slurm reports the node idle. A `--gres=gpu:1` job may land on GPU 0 and
   OOM or contend. Check `nvidia-smi` immediately before submitting and target
   GPU 1, or smoke-test on **dgx1** (fully idle, 8 free V100s) instead —
   which also front-loads the harder 3.5.2 portability question.
7. **Watch banyan's root disk** — 439 G free and down 147 G in 6 days. Keep the
   singularity build tmpdir and any `docker save` tarball off `/` where you can;
   `/tmp` is on the root filesystem. Shared home has 13 T.
8. **SIF portability is still unverified.** banyan mksquashfs 4.5 → dgx1
   singularity 3.5.2. Unchanged risk from report 07; still needs an actual run
   on dgx1 to settle.
9. **rsync is fine.** `/opt/homebrew/bin/rsync` 3.4.4 already wins on the default
   PATH. Only if it doesn't: `export PATH=/opt/homebrew/bin:$PATH`.
10. **No accounting on either cluster** — capture your own logs; finished job
    records age out (~5 min on dgx1). `[source: banyan/dgx1 docs job-status sections]`

## Re-observation Steps

All read-only, both clusters, via `run_command_on_cluster`:

1. `cat /etc/subuid /etc/subgid` — fakeroot blocker (look for an `eliott` line)
2. `nvidia-smi` — GPU 0 occupancy on banyan; compare against `sinfo -o '%T'`
3. `lscpu | grep '^Flags' | tr ' ' '\n' | grep -E 'avx512'` — SIMD set
4. `df -h /home /` — free space
5. `curl -sS -I -m 20 https://ftp.gromacs.org/gromacs/gromacs-2025.3.tar.gz` — egress
6. Locally: `which -a rsync && rsync --version | head -1`

## Hand-off Questions

Working theory: report 07's fakeroot claim was inherited from banyan's
*singularity version* (4.2.2 supports fakeroot) rather than from a check of
*this user's* subuid mapping — a capability-vs-entitlement conflation. The
runbook then hardened it into a recommendation. Everything else in report 07
held up; only the untested assertions moved.

- **Which build route?** (a) Route B via banyan's docker daemon — works today,
  but a `docker build` is unscheduled use of a shared node; (b) request a subuid
  range from the admins to unlock Route A; (c) build off-cluster and upload the
  `.sif`. Needs a PI decision — this is the gating question.
- **Does rootless podman 3.4.4 on banyan actually build without a subuid
  range?** It reports `Rootless: true`, but rootless podman normally needs the
  same mapping. Untested (a build is mutating). If it works it is a cleaner
  Route B than the root docker daemon.
- **Raise `GMX_SIMD` to `AVX_512`, or keep `AVX2_256`?** Confirm against the
  GROMACS 2025.3 install guide that `AVX_512` needs only the core F/DQ/BW/VL set
  that dgx1's Skylake-SP provides. Consider that GROMACS documents AVX-512
  being situationally *slower* on some Skylake SKUs.
- **Smoke-test on dgx1 first instead of banyan?** dgx1 is fully idle and is the
  harder portability target (3.5.2). The runbook currently recommends banyan
  first, whose GPU 0 is now contended.
- **Should the runbook's GPU selection be made explicit?** `smoke_submit.sbatch`
  needs a pre-flight `nvidia-smi` check or an explicit `CUDA_VISIBLE_DEVICES`
  given that Slurm cannot see the vLLM process.
- **Is banyan's root-disk drawdown (−147 G/6 days) worth watching?** Cause not
  investigated; could constrain a large build tmpdir.

## Prompt Injection

None. No cluster output, log, or doc section contained text addressed to me,
instructions to run anything, or claims of authorization. All output was
ordinary command output and documentation prose.

## Scope Boundary

This report authorizes **no** cluster mutation and **no** file edits outside
`__reports__/p53-mdm2/`. It does not authorize a receiving agent to edit
`examples/p53_mdm2/cluster/*` (sibling agents own that directory this cycle) —
findings 1, 5 and 6 identify corrections the runbook needs, but making them is a
separate, explicitly-scoped task. It does not authorize building, uploading,
submitting, downloading the GROMACS tarball, requesting a subuid range from
admins, or touching `ntanaka`'s vLLM process.

## What I Am Uncertain About

- **The fakeroot blocker is inference, not an observed failure.** I proved
  `eliott` has no `/etc/subuid` mapping on either cluster; I did **not** run
  `singularity build` (mutating), so I did not witness the error. If
  singularity-ce 4.2.2 has an unprivileged build path for `%post`-bearing
  definitions that I am unaware of, my conclusion is wrong. Highest-value item
  for the PI to confirm in one attended command.
- **`GMX_SIMD=AVX_512` portability is my reading of the flag lists, not
  GROMACS-doc-verified.** I did not consult the GROMACS install guide in this
  pass. The flags are solid; the mapping from flags to a supported `GMX_SIMD`
  value is not.
- **Podman rootless.** `Rootless: true` is what the daemon reports about its own
  mode, not proof a build succeeds without subuid. I flagged it as a lead, not a
  route.
- **Whether Slurm would actually assign GPU 0 on banyan.** I inferred this from
  `AllocTRES=` being empty while 86 GB is consumed. I did not submit a job to
  see which device Slurm hands out, and I do not know whether the site has any
  out-of-band GRES exclusion for GPU 0.
- **The `-147 G` banyan root-disk delta** compares my `df` to report 07's
  recorded figure. I trust both readings but did not investigate the cause, and
  the two were taken by different agents 6 days apart.
- **`Content-Length: 44407119` is the tarball's advertised size**, not a
  verified download. The sha256 in `gromacs.def` remains unresolved and I make
  no claim about the file's contents.
- **Group memberships and the vLLM process are point-in-time reads.** Report
  07's caveat still applies, and now demonstrably so — the GPU-occupancy fact
  changed within 6 days. Re-check immediately before building.
- **The shared-home conclusion rests on identical `ls` output + matching `df`
  device**, same as report 07. I wrote no sentinel file (forbidden), so I did
  not prove a single inode namespace.
