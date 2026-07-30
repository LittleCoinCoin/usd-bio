# ============================================================================
# Dockerfile — Route B twin of ./gromacs.def
#
# This is a FAITHFUL TRANSLATION of ./gromacs.def, not an independent recipe.
# `gromacs.def` is the SOURCE OF TRUTH for every pinned value here; its pins
# were verified against upstream in cycle-006 (commits 3f731c3, a16bcc2,
# e66d60a, 899810f) and carry inline source URLs. The comments below port those
# citations across so this file stands on its own audit trail — but where the
# two files disagree, `gromacs.def` is right and this file is a bug.
#
# ⚠️ KEEP THE TWO FILES IN SYNC. They are PARALLEL IMPLEMENTATIONS of the same
#    image. Editing one without the other is the obvious failure mode: it
#    silently produces two different containers from one directory. Any change
#    to a version, URL, checksum, apt package, or `GMX_*` flag must land in
#    BOTH ./gromacs.def and ./Dockerfile in the same commit.
#
# STATUS: BUILT. `docker build` ran attended on banyan 2026-07-29 (Slurm job 30,
#         exit 0, 5m27s) and produced `gromacs-p53mdm2:latest`
#         (`70659e395c53`, 10.6 GB) — see ./README.md gated step 1 and
#         __reports__/p53-mdm2/13-route_b_build_observed_v0.md. Still not done:
#         no `.sif` conversion, no GPU execution, no SASS verification, no
#         cleanup — those are the sibling roadmap leaves. Any FUTURE
#         `docker build` on banyan remains a PI-GATED mutating step (shared
#         node, `docker` group ≈ root there).
#
# WHY THIS FILE EXISTS (Route B):
#   ./README.md's Route B says `docker build -t gromacs-p53mdm2 .`, which needs a
#   Dockerfile. Route B is the RECOMMENDED build path because this user has NO
#   /etc/subuid + /etc/subgid mapping on EITHER cluster, so `singularity build`'s
#   --fakeroot (which gromacs.def's %post requires) is unavailable
#     [source: __reports__/p53-mdm2/10-cluster_state_refresh_v0.md §3
#              (read-only live refresh, cycle-006, commit c8f2cc2)].
#   The Docker daemon builds as root, so the apt-get + compile below just work.
#
# HOW IT IS CONSUMED (docker is the BUILDER; singularity is the RUNTIME):
#     docker build -t gromacs-p53mdm2 .
#     docker save gromacs-p53mdm2 -o gromacs.tar
#     singularity build gromacs.sif docker-archive://gromacs.tar
#     singularity exec --nv gromacs.sif gmx --version
#   Nothing is COPYed from the build context, so the context is irrelevant to the
#   result; `docker build -t gromacs-p53mdm2 - < Dockerfile` also works and
#   uploads nothing to the daemon.
#
# DISK-SPACE CONSTRAINT (banyan): the root filesystem fell 586 G -> 439 G free
#   between 2026-07-21 and 2026-07-27, but then HELD at 439 G free across four
#   further days, and the 2026-07-29 build itself only cost ~9 G net — read as
#   a one-off event, not an ongoing drain, though its original cause remains
#   uninvestigated [source: __reports__/p53-mdm2/13-route_b_build_observed_v0.md
#   §6]. `/tmp` is on `/` [report 10 §5]. Layer hygiene below is therefore
#   load-bearing, not cosmetic: apt lists are dropped, the CMake tarball is
#   deleted in the layer that created it, and the GROMACS source+build tree is
#   fetched, compiled, installed and deleted inside ONE `RUN` so the removal
#   actually reclaims space instead of being masked by an upper layer.
#   ⚠️ Note what this does NOT fix: `docker build` writes its layers to the
#   DAEMON's data-root, not to `$TMPDIR`. The README's SINGULARITY_TMPDIR/TMPDIR
#   redirection does not move them.
#     OBSERVED 2026-07-29 (was an assumption, now confirmed):
#       $ docker info | grep -i 'Docker Root Dir'
#       Docker Root Dir: /var/lib/docker
#     `/var/lib/docker` is on `/`, holding 213 G (mostly other users'
#     pre-existing images — not ours to prune). Only an admin can move the
#     daemon's data-root; the client cannot redirect it. `docker image rm` +
#     `docker builder prune` after the `.sif` exists is still pending.
#     [source: __reports__/p53-mdm2/13-route_b_build_observed_v0.md §5]
#
# SINGLE-STAGE, DELIBERATELY (this was the one design call available here):
#   ./gromacs.def already decided it — "`-devel` (not `-runtime`) is required: it
#   carries nvcc + headers to COMPILE GROMACS. Slimming to a multi-stage
#   -runtime image is a later optimization." Going multi-stage here would strand
#   the two files against each other for a size win, so it is NOT taken. The
#   supporting reasons:
#     * A `-runtime` final stage would have to receive, by hand, every shared
#       library the gmx binary links: the CUDA runtime + cuFFT (in -runtime, but
#       NOT in -base), libgomp1 for OpenMP, libfftw3, and libopenblas. Getting
#       that list wrong produces an image that builds fine and then fails at
#       `gmx --version` with a missing .so.
#     * That list cannot be verified from here — NOTHING IS BEING BUILT this
#       cycle, so `ldd $(which gmx)` has never been run against a real build. A
#       size optimization whose correctness is unverifiable is the wrong trade on
#       the recommended path.
#     * Multi-stage does not even reduce PEAK build-time disk on banyan: both
#       stages live in the daemon's layer store during the build. It shrinks the
#       final image and the `docker save` tarball, which is real but secondary.
#   Revisit only AFTER a green smoke test, with `ldd` output in hand.
# ============================================================================

# --- Base image: CUDA 12.9.1 devel on Ubuntu 22.04 ---------------------------
# CUDA 12.9 is the CROSS-CLUSTER portability pivot of the whole recipe:
#   * dgx1  = 8x Tesla V100-SXM2-16GB -> compute capability 7.0 (Volta, sm_70),
#             driver 580.159.03  [live: __reports__/p53-mdm2/07-cluster_liveverify_v1.md]
#   * banyan= 2x H100 NVL ~94GB       -> compute capability 9.0 (Hopper, sm_90),
#             driver 595.71.05   [same]
# CUDA 13.0 REMOVES offline compilation for compute capability < 7.5, i.e. it
# drops Volta. NVIDIA, verbatim: "If you're writing applications that support
# GPUs of CC earlier than 7.5, then you'll want to install and remain on the
# following: NVIDIA Driver: Remain on branch 580 [...] CUDA Toolkit: Remain on
# 12.9."
#   [verified 2026-07-27: https://developer.nvidia.com/blog/navigating-gpu-architecture-support-a-guide-for-nvidia-cuda-developers/]
# Confirmed against the toolkits' own nvcc manuals — the removal shipped, it was
# not merely announced:
#   * 12.9.1 nvcc SM list CONTAINS sm_70 and sm_90
#     [verified: https://docs.nvidia.com/cuda/archive/12.9.1/cuda-compiler-driver-nvcc/index.html]
#   * 13.0.0 nvcc's same list STARTS AT sm_75 — sm_70 is absent
#     [verified: https://docs.nvidia.com/cuda/archive/13.0.0/cuda-compiler-driver-nvcc/index.html]
# dgx1 is on driver branch 580 exactly => 12.9 is the single toolkit covering
# BOTH clusters (sm_70 + sm_90).
#
# Runtime note (singularity --nv): the CONTAINER ships the CUDA runtime, the HOST
# driver is bind-mounted in. An older CUDA runtime under a newer host driver is
# forward-compatible, so 12.9 runs under host drivers 580 (dgx1) and 595 (banyan).
#
# TAG EXISTS — verified, not assumed. `nvidia/cuda:12.9.1-devel-ubuntu22.04` is
# published on Docker Hub, last updated 2025-07-25, manifest digest
#   sha256:bd4e2680a261c212f1e2fea241606f71497dc67a417f73175d794ec8212b5ba8
#   [verified 2026-07-27: https://hub.docker.com/v2/repositories/nvidia/cuda/tags/12.9.1-devel-ubuntu22.04]
# To pin IMMUTABLY, replace the tag below with that digest:
#   FROM nvidia/cuda@sha256:bd4e2680a261c212f1e2fea241606f71497dc67a417f73175d794ec8212b5ba8
# (`12.9.2-devel-ubuntu22.04` also exists, updated 2026-05-20 — bump deliberately
#  if wanted, but 12.9.1 is what EasyBuild's own GROMACS 2025.3 CUDA easyconfig
#  targets, so 12.9.1 is the better-corroborated combination.)
#
# WHY ubuntu22.04 AND NOT ubuntu24.04 — a compiler decision, not inertia:
#   * jammy's `build-essential` gives gcc 11.x (apt `gcc` = 4:11.2.0-1ubuntu1)
#     [verified: https://packages.ubuntu.com/jammy/gcc]. GROMACS 2025.3, verbatim:
#     "We recommend to use the GCC compiler, version 9.x to 11.x. Note: there are
#     known issues with GCC 12 and newer."
#     [verified: https://manual.gromacs.org/documentation/2025.3/install-guide/index.html]
#   * noble ships gcc 13.2 [verified: https://packages.ubuntu.com/noble/gcc] —
#     squarely inside GROMACS' "known issues" range.
#   * Ubuntu 22.04 LTS is a natively supported distro for CUDA 12.9
#     [verified: https://docs.nvidia.com/cuda/archive/12.9.1/cuda-installation-guide-linux/index.html]
# COST of that choice, paid below: jammy's apt `cmake` is 3.22.1
# [verified: https://packages.ubuntu.com/jammy/cmake] but GROMACS 2025.3 "builds
# with the CMake build system, requiring at least version 3.28" [verified: install
# guide, same URL]. So CMake must NOT come from apt — a pinned upstream CMake is
# installed instead.
FROM nvidia/cuda:12.9.1-devel-ubuntu22.04

# --- Labels (translation of gromacs.def's %labels) ---------------------------
# `singularity build docker-archive://...` carries these into the SIF's labels,
# so `singularity inspect gromacs.sif` shows them the same way it would for a
# native build from the .def.
# NOTE: no `BuildStatus` key here (removed 2026-07-30). A LABEL is baked into
# the image and carried into the .sif by `singularity build docker-archive://`,
# so a literal value here would become a PERMANENT, wrong provenance claim —
# `singularity inspect` would forever report the not-yet-built status this key
# used to carry, even after a real build (as this one now is; see
# ./README.md). Build status is per-build state, not a recipe constant. If
# per-build status is ever wanted,
# the right mechanism is a build-time `--label BuildStatus=...` argument to
# `docker build`, not a literal baked in here.
LABEL Maintainer="usd-bio p53-mdm2 track" \
      Purpose="GPU-enabled GROMACS for p53-MDM2 self-run MD (p1b Step 2)" \
      GromacsVer="2025.3" \
      CudaToolkit="12.9.1" \
      CMakeVer="4.0.3" \
      TargetSM="70;90" \
      SyncWith="./gromacs.def (parallel implementation — keep in sync)"

# Build-time only, so it is NOT baked into the image environment. This is the
# translation of `export DEBIAN_FRONTEND=noninteractive` inside %post.
ARG DEBIAN_FRONTEND=noninteractive

# --- Build toolchain ---------------------------------------------------------
# NOTE: `cmake` is deliberately ABSENT from this list — apt would give 3.22.1,
# below GROMACS 2025.3's hard 3.28 floor. It is installed from upstream below.
# `rm -rf /var/lib/apt/lists/*` is in the SAME RUN on purpose: in a later layer
# it would hide the lists without reclaiming their space.
RUN set -eu; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
        wget \
        libfftw3-dev \
        libopenblas-dev \
        pkg-config \
        python3; \
    rm -rf /var/lib/apt/lists/*

# --- CMake >= 3.28 from upstream binary tarball ------------------------------
# 4.0.3 is not a guess: EasyBuild's GROMACS-2025.3-foss-2025b-CUDA-12.9.1.eb
# builds this exact GROMACS with ('CMake', '4.0.3') and CUDA 12.9.1, so the
# GROMACS-2025.3 + CMake-4.0.3 + CUDA-12.9.1 triple is known-good upstream
#   [verified: https://github.com/easybuilders/easybuild-easyconfigs/blob/develop/easybuild/easyconfigs/g/GROMACS/GROMACS-2025.3-foss-2025b-CUDA-12.9.1.eb]
# The sha256 IS officially published by Kitware, in the per-release checksum
# asset cmake-4.0.3-SHA-256.txt:
#   585ae9e0...  cmake-4.0.3-linux-x86_64.tar.gz
#   [verified: https://github.com/Kitware/CMake/releases/download/v4.0.3/cmake-4.0.3-SHA-256.txt]
RUN set -eu; \
    CMAKE_VERSION=4.0.3; \
    CMAKE_SHA256=585ae9e013107bc8e7c7c9ce872cbdcbdff569e675b07ef57aacfb88c886faac; \
    cd /opt; \
    wget -q "https://github.com/Kitware/CMake/releases/download/v${CMAKE_VERSION}/cmake-${CMAKE_VERSION}-linux-x86_64.tar.gz"; \
    echo "${CMAKE_SHA256}  cmake-${CMAKE_VERSION}-linux-x86_64.tar.gz" | sha256sum -c -; \
    tar xf "cmake-${CMAKE_VERSION}-linux-x86_64.tar.gz"; \
    mv "cmake-${CMAKE_VERSION}-linux-x86_64" /opt/cmake; \
    rm -f "cmake-${CMAKE_VERSION}-linux-x86_64.tar.gz"; \
    /opt/cmake/bin/cmake --version

# --- Fetch + verify + build + install GROMACS --------------------------------
# ONE RUN on purpose (see the disk-space note in the header): the source tree and
# its build/ subdirectory are tens of GB of intermediates, and deleting them in a
# later layer would reclaim nothing.
#
# GROMACS source pin. 2025.3 exists and its docs/download page is live; the
# tarball is present in the ftp index (gromacs-2025.3.tar.gz, 42 MB, 2025-08-29)
#   [verified: https://manual.gromacs.org/documentation/2025.3/download.html
#              https://ftp.gromacs.org/gromacs/ ]
# NOTE for the PI: 2025.4 and 2026.x also exist upstream by now; 2025.3 is a
# DELIBERATE pin, not "the newest". Bump only with intent — and in both files.
#
# INTEGRITY: GROMACS publishes only an MD5 for the source tarball — there is no
# sha256 on the download page and no .sha256/SHA256SUMS in the ftp index. BOTH
# checks below are ACTIVE, in this order:
#   (1) MD5 — OFFICIAL, straight off the GROMACS 2025.3 download page:
#       "https://ftp.gromacs.org/gromacs/gromacs-2025.3.tar.gz
#        (md5sum 5a2315b6f6e13b091bbbbfddee9eb62b)"
#       [verified: https://manual.gromacs.org/documentation/2025.3/download.html]
#   (2) SHA256 — NOT published by GROMACS. Independently corroborated by TWO
#       unrelated packaging projects that hash the same official tarball and
#       agree byte-for-byte:
#         * Spack:     version("2025.3", sha256="8bdfca02...")
#           https://github.com/spack/spack-packages/blob/develop/repos/spack_repo/builtin/packages/gromacs/package.py
#         * EasyBuild: checksums = [{'gromacs-2025.3.tar.gz': '8bdfca02...'}]
#           (easyconfig URL above)
#       Treat it as strongly corroborated, NOT vendor-published. If it ever
#       mismatches at build time, TRUST THE OFFICIAL MD5 FIRST and re-derive this
#       value; do not silently delete the check.
#
# Configure flags — all spellings checked against the GROMACS 2025.3 install guide
#   [verified: https://manual.gromacs.org/documentation/2025.3/install-guide/index.html]:
#   GMX_GPU=CUDA            : guide, verbatim: "-DGMX_GPU=CUDA to build with
#                             NVIDIA CUDA support enabled." It requires "CUDA
#                             toolkit version 12.1 or newer" and a "GPU with
#                             compute capability 5.0 or higher" — 12.9.1 and
#                             cc 7.0+9.0 both clear it. (Caveat: GROMACS' own CI
#                             tests CUDA 12.1, 12.5.1, 12.6, so 12.9 is above the
#                             CI-tested set though above the documented minimum;
#                             EasyBuild's 2025.3 + CUDA 12.9.1 easyconfig is the
#                             corroboration for it.)
#   GMX_MPI=OFF             : no cross-node MPI. Thread-MPI (intra-node) is ON by
#                             default — "GROMACS can run in parallel on multiple
#                             cores of a single workstation using its built-in
#                             thread-MPI. No user action is required" — and both
#                             clusters are SINGLE-NODE Slurm [live: report 07], so
#                             multi-node MPI buys nothing here.
#   GMX_CUDA_TARGET_SM      : real-arch (SASS) codegen for the two GPUs we own.
#                             "70"=V100 Volta, "90"=H100 Hopper. Guide: these
#                             flags "take a semicolon delimited string with the
#                             two digit suffixes of CUDA (virtual) architectures
#                             names, for instance '60;75;86'" — so "70;90" is the
#                             right shape, and both are in nvcc 12.9.1's SM list.
#                             (Known 2025.3 CMake quirk: gmxManageNvccConfig
#                             strips letter suffixes from CCs, breaking values
#                             like "120f" — see EasyBuild's
#                             GROMACS-2025.3_retain_cuda_cc_suffix.patch. Plain
#                             "70;90" has no suffix, so it is unaffected.)
#   GMX_CUDA_TARGET_COMPUTE : intended to embed PTX for 90 only, so newer GPUs
#                             can JIT while the binary stays lean; PTX for 70
#                             was meant to be omitted since the 70 SASS above
#                             already covers V100 directly.
#                             CORRECTED 2026-07-30: this is NOT what the built
#                             image actually contains. `cuobjdump -lptx` on the
#                             real binary shows PTX embedded for BOTH 70 and 90
#                             (SM_ELF=sm_70;sm_90, SM_PTX=sm_70;sm_90, 98 ELF +
#                             98 PTX records) — GROMACS' CMake evidently emits
#                             PTX for every SM target regardless of
#                             GMX_CUDA_TARGET_COMPUTE. Functionally harmless
#                             (more PTX = more forward-portable, a marginally
#                             larger binary); documentation correction only,
#                             the flag itself is UNCHANGED.
#                             [observed 2026-07-29 via cuobjdump -lptx, sass_portability_audit leaf]
#   GMX_DOUBLE=OFF          : single precision — the standard, GPU-supported build.
#   GMX_BUILD_OWN_FFTW=OFF  : use the distro libfftw3-dev installed above.
#                             HONEST CAVEAT: upstream recommends the OPPOSITE —
#                             "the GROMACS team recommends either that you permit
#                             the GROMACS installation to download and build FFTW
#                             from source automatically for you (use cmake
#                             -DGMX_BUILD_OWN_FFTW=ON)", because distro FFTW is
#                             typically double-precision-first and may miss
#                             AVX/AVX2 codelets. OFF is kept for a hermetic,
#                             download-free configure step; it is a PERFORMANCE
#                             trade, not a correctness one. Flip to ON if
#                             PME-on-CPU throughput matters.
#   GMX_SIMD=AVX2_256       : [verified] see the long note after the cmake call.
#   CUDA_TOOLKIT_ROOT_DIR   : the guide shows exactly
#                             `cmake .. -DGMX_GPU=CUDA -DCUDA_TOOLKIT_ROOT_DIR=/usr/local/cuda`.
#
# `make -j"$(nproc)"` matches gromacs.def. ⚠️ OPERATOR NOTE (behaviour NOT changed
# here, so the two files stay identical): inside `docker build` on banyan, nproc
# reports the whole shared node's core count, so this will saturate it. If that
# is unacceptable courtesy-wise, cap it — but cap it in BOTH files.
RUN set -eu; \
    GROMACS_VERSION=2025.3; \
    GROMACS_URL="https://ftp.gromacs.org/gromacs/gromacs-${GROMACS_VERSION}.tar.gz"; \
    GROMACS_MD5=5a2315b6f6e13b091bbbbfddee9eb62b; \
    GROMACS_SHA256=8bdfca0268f3f10a7ca3c06e59b62f73ea02420c67211c0ff3912f32d7833c65; \
    export PATH=/opt/cmake/bin:$PATH; \
    cmake --version; \
    cd /opt; \
    wget -q "${GROMACS_URL}"; \
    echo "${GROMACS_MD5}  gromacs-${GROMACS_VERSION}.tar.gz" | md5sum -c -; \
    echo "${GROMACS_SHA256}  gromacs-${GROMACS_VERSION}.tar.gz" | sha256sum -c -; \
    tar xf "gromacs-${GROMACS_VERSION}.tar.gz"; \
    cd "gromacs-${GROMACS_VERSION}"; \
    mkdir build; \
    cd build; \
    cmake .. \
        -DCMAKE_BUILD_TYPE=Release \
        -DGMX_GPU=CUDA \
        -DGMX_MPI=OFF \
        -DGMX_CUDA_TARGET_SM="70;90" \
        -DGMX_CUDA_TARGET_COMPUTE="90" \
        -DGMX_DOUBLE=OFF \
        -DGMX_BUILD_OWN_FFTW=OFF \
        -DGMX_SIMD=AVX2_256 \
        -DCMAKE_INSTALL_PREFIX=/opt/gromacs \
        -DCUDA_TOOLKIT_ROOT_DIR=/usr/local/cuda; \
    make -j"$(nproc)"; \
    make install; \
    cd /opt; \
    rm -rf "gromacs-${GROMACS_VERSION}" "gromacs-${GROMACS_VERSION}.tar.gz"
# `make check` (GROMACS regression tests) is deliberately NOT run: it is slow and
# its GPU tests need a GPU at build time, which a `docker build` does not have.
#
# [verified] GMX_SIMD=AVX2_256 — condensed from gromacs.def, which holds the
# canonical write-up (as does ./README.md). Read it before "fixing" this, because
# the resolution is counter-intuitive: BOTH CPUs support AVX-512 and we still keep
# AVX2_256.
#   1. HARDWARE: banyan = Intel Xeon Gold 6530 (Emerald Rapids); dgx1 = Intel Xeon
#      Gold 6130 (Skylake-SP). Both carry the AVX-512 core set (avx512f/dq/bw/vl/
#      cd); banyan adds VNNI/BF16/FP16/IFMA/VBMI + AMX, so dgx1 is the least
#      common denominator.
#        [source: __reports__/p53-mdm2/10-cluster_state_refresh_v0.md §4
#                 (lscpu on both clusters, cycle-006, commit c8f2cc2)]
#   2. `AVX_512` IS a valid 2025.3 value (list: None, SSE2, SSE4.1, AVX_128_FMA,
#      AVX_256, AVX2_128, AVX2_256, AVX_512, AVX_512_KNL, IBM_VSX,
#      ARM_NEON_ASIMD, ARM_SVE), so the naive least-common-denominator rule would
#      say AVX_512 [verified: install guide URL above].
#   3. BUT THE DOCS OVERRIDE THE NAIVE RULE. The 2025.3 guide's AVX_512 entry,
#      verbatim: "With GPU accelerated runs `AVX2_256` can also be faster on
#      high-end Skylake CPUs with both 512-bit FMA units enabled." Our runs ARE
#      GPU-accelerated by construction (-DGMX_GPU=CUDA above; `gmx mdrun -nb gpu`
#      in smoke_submit.sbatch) and dgx1 IS a high-end Skylake. That sentence
#      describes this exact machine and workload [verified: same section].
#   4. ROBUST TO THE ONE UNCHECKED FACT. The guide also says models such as "Xeon
#      Bronze and Silver" have "only one AVX512 FMA unit and therefore on these
#      processors `AVX2_256` is faster" [verified: same section]. The Gold 6130's
#      FMA-unit count was NOT verified — and need not be, because both branches
#      agree: one unit -> AVX2_256 IS faster; two units -> the GPU-accelerated
#      sentence applies, AVX2_256 CAN be faster. No branch makes AVX_512 the
#      documented choice for a GPU-accelerated run on this CPU.
#   SAFETY: AVX2_256 is "Present on Intel Haswell (and later) processors (2013)
#      and AMD Zen3 and later (2020)" [verified: same section]; both CPUs are far
#      newer, so no illegal-instruction risk on either cluster. One image, runs
#      on both.
#   WHAT THIS DOES NOT CLAIM: no benchmark was run, on either CPU. banyan's
#      Emerald Rapids may well be faster with AVX_512
#        [assumption: the 2025.3 guide's AVX_512 caveats are written about
#         Skylake-X/SP and Zen4 and say nothing about Emerald Rapids either way;
#         that later Intel generations narrowed the AVX-512 downside is general
#         industry lore, NOT verified against a citable source here.]
#      If CPU-side PME ever becomes the bottleneck ON BANYAN SPECIFICALLY, the
#      escape hatch is a PER-ARCHITECTURE build (-DGMX_BINARY_SUFFIX, the guide's
#      own advice for heterogeneous fleets), NOT raising this flag on the shared
#      image. The single-image-run-anywhere constraint is what pins this value.
#   DO NOT delete the flag and rely on CMake auto-detection: the guide says it
#      detects "the SIMD instruction set supported by the CPU architecture (on
#      which the configuring is done)" — for one image shared across two CPU
#      generations via one NFS home, that pins the result to the BUILD host.

# --- Build-time sanity check (translation of gromacs.def's %test) ------------
# Singularity runs %test at the end of `singularity build`; Docker has no such
# hook, so the equivalent is just another RUN. Same limitation as %test: this is
# CPU-only — no GPU is present in a `docker build` — so it proves the binary
# links and reports its build config, NOT that GPU execution works. Real GPU
# verification is the PI-gated smoke_submit.sbatch on a GPU node.
# This layer adds no files, so it costs nothing but is a hard build-time gate:
# a GROMACS that silently configured without CUDA fails the build here.
#
# ⚠️ KNOWN FAILURE MODE OF THIS CHECK ITSELF (read before "fixing" the build):
#   a `docker build` container has no NVIDIA driver library. If `gmx --version`
#   aborts with `libcuda.so.1: cannot open shared object file`, that is a
#   DRIVER-LIBRARY absence in the build sandbox, NOT a broken GROMACS — the
#   `-devel` base ships libcuda only as a link-time stub under
#   /usr/local/cuda/lib64/stubs, which is not on the loader path.
#     RESOLVED 2026-07-30, with hard evidence, not inference. Two independent
#     signals now confirm the 2025.3 gmx binary has NO direct DT_NEEDED on
#     libcuda.so.1:
#       (1) the 2026-07-29 build itself reached exit 0 with this exact RUN as a
#           hard gate, in a sandbox with no NVIDIA driver — the build-time
#           version block printed `CUDA driver: 0.0`, precisely the signature
#           of "gate passed without a driver present"
#           [source: __reports__/p53-mdm2/13-route_b_build_observed_v0.md §4, §8].
#       (2) `readelf -d $(which gmx)` on the built image lists the NEEDED
#           entries exactly as: libgromacs.so.10, libstdc++.so.6, libgcc_s.so.1,
#           libc.so.6 — no libcuda.so.1 anywhere in the list. The binary also
#           carries RUNPATH `$ORIGIN/../lib`, which independently corroborates
#           the choice below not to inject LD_LIBRARY_PATH: the binary already
#           resolves its own libs relative to its install prefix.
#           [observed 2026-07-29 via readelf -d, sass_portability_audit leaf]
#     gromacs.def's %test has the same exposure and is resolved the same way —
#     this was always a shared risk, not one Route B introduced, and it is now
#     closed for both files by the same evidence.
#   If it happens: the expensive compile above is already a cached layer, so the
#   retry is cheap. Delete/relax THIS RUN in both files and verify GPU support on
#   a GPU node instead (`singularity exec --nv gromacs.sif gmx --version`).
#   Do NOT "fix" it by weakening the CUDA configure flags.
RUN set -eu; \
    /opt/gromacs/bin/gmx --version; \
    /opt/gromacs/bin/gmx --version | grep -i "GPU support" || \
        { echo "FAIL: gmx reports no GPU support"; exit 1; }

# --- Environment (translation of gromacs.def's %environment) -----------------
# Put gmx on PATH for `singularity exec ... gmx ...` invocations. Docker ENV is
# carried into the SIF by `singularity build docker-archive://...` (it lands in
# /.singularity.d/env/10-docker2singularity.sh), so this is the real equivalent
# of %environment — an ENTRYPOINT that sources GMXRC would NOT be, because
# `singularity exec` never runs the entrypoint.
# GROMACS also ships GMXRC; it is deliberately NOT sourced here, matching
# gromacs.def: PATH alone is enough for `gmx`, GROMACS' installed binaries carry
# an RPATH to their own libs, and injecting LD_LIBRARY_PATH into a container that
# will have host driver libraries bind-mounted by `--nv` is a needless risk.
# If a downstream tool ever needs the full GROMACS env, source it per-command:
#   singularity exec --nv gromacs.sif bash -c '. /opt/gromacs/bin/GMXRC && ...'
ENV PATH=/opt/gromacs/bin:$PATH

# --- No ENTRYPOINT, by design (see gromacs.def's %runscript) -----------------
# The image is consumed as `singularity exec --nv gromacs.sif gmx ...`. An
# ENTRYPOINT would become the SIF's runscript AND would prefix/swallow the
# command for anyone who used `docker run` or `singularity run` — exactly the
# fight this file must not pick. CMD alone is the safe translation of %runscript:
# `singularity exec` ignores it entirely, while `singularity run gromacs.sif` (and
# `docker run gromacs-p53mdm2`) execute it, giving the same "prove the build is
# sane" default action the .def has. Overriding it is a plain
# `docker run gromacs-p53mdm2 gmx mdrun ...`, with nothing prepended.
CMD ["/bin/sh", "-c", "echo '=== GROMACS container (p53-mdm2 / usd-bio) ==='; exec /opt/gromacs/bin/gmx --version"]

# ============================================================================
# NOT TRANSLATED (Docker has no equivalent) — recorded so the gap is visible:
#   * %help  — there is no `docker run-help`. Because this file sets no
#              ENTRYPOINT/%runscript help metadata, `singularity run-help
#              gromacs.sif` on the converted image will have nothing to print.
#              The .def's %help text lives in ./gromacs.def and ./README.md.
#   * %post's implicit root — Docker's daemon gives root for free; that IS the
#              point of Route B, and why this file exists at all.
# ============================================================================
