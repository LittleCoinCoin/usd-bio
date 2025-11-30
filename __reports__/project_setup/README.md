# Project Setup

Repository reorganization planning and initial roadmap development for transforming usd-bio from an OpenUSD template into a production-ready C++ extension for biology data in scientific metaverses.

## Documents

### Phase 1: Planning & Architecture
- **[00-repository_reorganization_planning_v0.md](./00-repository_reorganization_planning_v0.md)** ⭐ **CURRENT** - Comprehensive planning report
  - Technical stack research and decisions (Sphinx+Doxygen+Breathe, Google Test)
  - Repository structure analysis and reorganization plan
  - Documentation and testing strategy
  - Implementation roadmap with success criteria

## Quick Summary

### Critical Findings

**Documentation Stack**:
- **Decision**: Doxygen + Sphinx + Breathe (C++ industry standard)
- **Rationale**: Used by LLVM, Boost, OpenUSD; ReadTheDocs-compatible; superior C++ API documentation
- **Alternative**: MkDocs (rejected: poor C++ support)

**Testing Framework**:
- **Decision**: Google Test (GTest)
- **Rationale**: OpenUSD-aligned, industry standard, rich assertion library, mock support
- **Alternative**: CMake `enable_testing()` only (rejected: not a testing framework, just a test runner)

**Code Organization**:
- **Decision**: New `src/` directory for production code
- **Rationale**: Clear separation from template artifacts, enables future template archival
- **Preserved**: `OpenUSD-setup-vcpkg/` as reference and sanity check

### Recommended Approach

**Directory Structure**:
```
usd-bio/
├── src/              # Production extension code
├── tests/            # Google Test suite
├── docs/             # Sphinx + Doxygen documentation
├── examples/         # Tutorial code
├── __design__/       # Permanent design docs (roadmap, architecture)
├── __reports__/      # Temporary work reports
└── OpenUSD-setup-vcpkg/  # Preserved template reference
```

**Phased Implementation**:
1. **Phase 1**: Foundation Setup (infrastructure, build, docs, tests)
2. **Phase 2**: Core Architecture & Schema Definition
3. **Phase 3**: Biology Data Integration
4. **Phase 4**: Testing & Validation
5. **Phase 5**: Production Release (v1.0.0)

### Implementation Status

- ✅ Planning report complete
- ✅ Initial roadmap drafted (`__design__/usd_bio_roadmap_v0.1.0.md`)
- ⏳ Awaiting user approval
- ⏳ Phase 1 implementation pending

## Status
- ✅ Phase 1: Planning - Complete
- ⏳ Phase 2: Implementation - Awaiting Approval

---

**Last Updated**: 2025-11-13
