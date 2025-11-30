# Test Fixtures

This directory contains test data files and fixtures for USD-Bio tests.

## Contents

- `*.usd` - USD stage files for testing
- `*.usda` - ASCII USD files for testing
- `biology/` - Biology-specific test data (added in Phase 2+)

## Usage

Tests reference fixtures using relative paths from the test binary location.

Example:
```cpp
const std::string fixturePath = "fixtures/test_stage.usd";
auto stage = UsdStage::Open(fixturePath);
```

## Guidelines

- Keep fixtures minimal (small file sizes)
- Use descriptive names indicating test purpose
- Document complex fixtures with comments
