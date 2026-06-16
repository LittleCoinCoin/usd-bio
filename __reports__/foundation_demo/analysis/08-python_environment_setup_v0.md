# Report: Python Environment Setup for OpenUSD (v0)

**Topic**: Critical Environment Configuration for `usd-bio` Development
**Source**: Troubleshooting SegFault 11 in OpenUSD Python Bindings
**Date**: 2026-01-20
**Status**: Documented

---

## Executive Summary

To develop and run OpenUSD-based scripts on this system, a specific Python interpreter and environment configuration must be used. Failure to use these settings results in immediate **Segmentation fault: 11** due to ABI mismatches between the system Python and the OpenUSD C++ extensions.

---

## 1. Required Python Interpreter

The OpenUSD libraries are linked against a specific Python environment. The system `python3` is incompatible.

*   **Verified Path**: `/Users/hacker/Documents/src/AOUSD/forOUSD/bin/python3`

---

## 2. Mandatory Environment Variables

Before executing any script importing the `pxr` module, the following environment must be established:

```bash
# Set Python module search path
export PYTHONPATH="/Users/hacker/Documents/bin/OpenUSD/lib/python:$PYTHONPATH"

# Add USD binaries to path (for tools like usdview)
export PATH="/Users/hacker/Documents/bin/OpenUSD/bin:$PATH"
```

---

## 3. Verified Execution Command

The standardized command for running `usd-bio` examples is:

```bash
export PYTHONPATH=/Users/hacker/Documents/bin/OpenUSD/lib/python:$PYTHONPATH && \
/Users/hacker/Documents/src/AOUSD/forOUSD/bin/python3 <script_name>.py
```

---

## 4. Troubleshooting Context

| Error | Cause | Resolution |
| :--- | :--- | :--- |
| **Segmentation fault: 11** | ABI mismatch (System Python vs USD Build) | Use the interpreter in `AOUSD/forOUSD/bin/` |
| **ImportError: No module named pxr** | Missing `PYTHONPATH` | Point to `OpenUSD/lib/python` |
| **AttributeError: 'Prim' has no child...** | Legacy/Specific API Version | Use `stage.DefinePrim(path.AppendChild("name"))` |

---

## 5. Next Steps

All future development for the **Foundation Demo** will utilize these constants to ensure stability. This report serves as a "context anchor" for the implementation phase.

```