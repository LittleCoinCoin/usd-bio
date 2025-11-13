# USD-Bio: OpenUSD Extensions for Biology Data

[![CI](https://github.com/LittleCoinCoin/usd-bio/actions/workflows/ci.yml/badge.svg)](https://github.com/LittleCoinCoin/usd-bio/actions)
[![Documentation](https://github.com/LittleCoinCoin/usd-bio/actions/workflows/documentation.yml/badge.svg)](https://github.com/LittleCoinCoin/usd-bio/actions)
[![License](https://img.shields.io/badge/License-AGPL--3.0-blue.svg)](LICENSE.md)
[![Version](https://img.shields.io/badge/version-0.1.0-green.svg)](https://github.com/LittleCoinCoin/usd-bio)

**OpenUSD extensions for representing and manipulating biology data in scientific metaverses.**

Following the success of OpenUSD's physics extensions (UsdPhysics), USD-Bio enables biology-specific data representation, from molecular to organism scales, within the Universal Scene Description ecosystem.

---

## What is USD-Bio?

USD-Bio is a C++ extension library for [Pixar's OpenUSD](https://openusd.org/) that provides:

- **Biology-specific USD schemas** for molecular, cellular, tissue, and organism data
- **Data import/export pipelines** for common biology file formats
- **Integration with USD stage manipulation** for 3D visualization workflows
- **Performance-optimized** operations for large-scale biological datasets

**Status**: v0.1.0 - Foundation setup complete, core features in development (Phase 2+)

---

## Why USD-Bio?

### Problem
Modern computational biology generates massive 3D datasets (protein structures, cellular imaging, tissue scans), but lacks standardized representation for collaborative visualization and analysis in metaverse environments.

### Solution
USD-Bio extends OpenUSD's proven architecture to biology data, enabling:
- **Interoperability** across biology visualization tools
- **Scalability** for massive datasets (millions of atoms, billions of cells)
- **Collaboration** through standardized scene descriptions
- **Integration** with existing USD workflows (rendering, animation, simulation)

### Value Proposition
Researchers can visualize, analyze, and collaborate on biological data using industry-standard USD tooling, without custom format converters or proprietary platforms.

---

## Quick Start

### Prerequisites

- **CMake** 3.20 or higher
- **C++20** compatible compiler (MSVC 2019+, GCC 10+, Clang 12+)
- **vcpkg** for dependency management
- **Git** with submodule support

### Installation

**1. Clone the repository with submodules:**
```bash
git clone --recursive https://github.com/LittleCoinCoin/usd-bio.git
cd usd-bio
```

**2. Bootstrap vcpkg (if not already installed):**
```bash
# Windows
.\vcpkg\bootstrap-vcpkg.bat

# Linux/macOS
./vcpkg/bootstrap-vcpkg.sh
```

**3. Configure and build:**
```bash
# Windows (MSVC)
cmake --preset=MSVC-x64
cmake --build out/build/MSVC-x64 --config Release

# Linux (GCC)
cmake --preset=GCC
cmake --build out/build/GCC --config Release

# macOS (Clang)
cmake --preset=Clang
cmake --build out/build/Clang --config Release
```

**4. Run tests (optional):**
```bash
cd out/build/<preset>
ctest --output-on-failure
```

### Basic Usage

```cpp
#include <usd_bio/extension.h>
#include <iostream>

int main() {
    // Verify USD-Bio is loaded
    std::cout << "USD-Bio Extension v" 
              << usd_bio::GetVersion() 
              << std::endl;
    
    // More examples coming in Phase 2+
    return 0;
}
```

---

## Documentation

- **[User Guide](docs/user_guide/)** - Installation, quick start, examples
- **[Developer Guide](docs/developer_guide/)** - Architecture, building, contributing
- **[API Reference](docs/api/)** - Complete C++ API documentation
- **[Roadmap](__design__/usd_bio_roadmap_v0.1.0.md)** - Project phases and milestones

**Build documentation locally:**
```bash
pip install -r docs/requirements.txt
doxygen Doxyfile
sphinx-build docs docs/_build/html
```

Open `docs/_build/html/index.html` in your browser.

---

## Project Structure

```
usd-bio/
├── src/                    # Extension library source code
│   ├── include/usd_bio/    # Public API headers
│   └── core/               # Implementation files
├── tests/                  # Google Test test suite
├── examples/               # Example programs
├── docs/                   # Sphinx + Doxygen documentation
├── __design__/             # Permanent design documents (roadmap, architecture)
├── __reports__/            # Temporary work reports (analysis, implementation)
└── OpenUSD-setup-vcpkg/    # Template reference (preserved for validation)
```

---

## Development Status

**Current Phase**: Phase 1 - Foundation Setup ✅ Complete (v0.1.0)

**Completed Milestones**:
- ✅ Directory structure and build system
- ✅ Documentation framework (Doxygen + Sphinx + Breathe)
- ✅ Testing framework (Google Test + CI/CD)
- ✅ Project documentation and contribution guidelines

See [Roadmap](__design__/usd_bio_roadmap_v0.1.0.md) for an overview.

---

## Contributing

We welcome contributions! Please read our [Contributing Guide](CONTRIBUTING.md) before submitting PRs.

### Development Workflow

1. Fork the repository
2. Create a branch: `task/<task-id>-<description>` (following milestone structure)
3. Make changes following our [Code Style Guide](CONTRIBUTING.md)
4. Run tests: `ctest --output-on-failure`
5. Build documentation to verify changes
6. Submit a pull request to `dev` branch

### Code Standards

- **C++20** standard with modern idioms
- **OpenUSD conventions** for naming and structure
- **Doxygen comments** for all public APIs
- **Unit tests** for new features (>90% coverage goal)
- **Conventional commits** (see [Git Workflow](cracking-shells-playbook/instructions/git-workflow.md))

---

## License

USD-Bio is licensed under the [MIT License](LICENSE.md).

This project builds on [Pixar's OpenUSD](https://github.com/PixarAnimationStudios/OpenUSD), used under the Modified Apache 2.0 License.

---

## Acknowledgments

- **Pixar Animation Studios** - OpenUSD foundation
- **PRIMe Collaboration** - Research support and domain expertise
- **OpenUSD Community** - Patterns and best practices

---

## Citation

If you use USD-Bio in your research, please cite:

```bibtex
@software{usd_bio_2025,
  title={USD-Bio: OpenUSD Extensions for Biology Data},
  author={PRIMe Collaboration},
  year={2025},
  url={https://github.com/LittleCoinCoin/usd-bio},
  version={0.1.0}
}
```

---

**Status**: v0.1.0 | **License**: MIT | **Community**: PRIMe Collaboration
