"""
dg_correlation.py -- the ΔΔG <-> MaBoSS-parameter correlation (Pipeline 3).

Pure, dependency-free (stdlib ``math`` only). Implements the logistic
correlation designed in R02 and its closed-form logit inverse:

    S(ΔΔG)  = 1 / (1 + exp(-k * (ΔΔG - m)))        (logistic; ΔΔG in kcal/mol)
    ΔΔG(S)  = m + (1/k) * ln( S / (1 - S) )         (logit inverse)

``S`` is the p53-Mdm2N antagonism strength written into the MaBoSS hill
parameters ``$KMn_pMCD`` / ``$KMn_pMC`` (WT = 1). The logistic is strictly
monotone increasing in ΔΔG, so the inverse is single-valued on (0, 1); the
forward output is clamped to ``[EPS, 1 - EPS]`` to keep the logit finite at the
saturating tails.

Design source: __reports__/p53-mdm2/02-dg_maboss_correlation_v0.md
  Defaults m = -3.0 kcal/mol, k = 1.5 /(kcal/mol) are the R02 placeholders
  (explicitly ad-hoc per PI Q-002); both are PARAMETERS here, never inlined at
  the call sites, so any re-fit is a data edit rather than a code change.
"""

from __future__ import annotations

import math

# R02 defaults (placeholders, ad-hoc by PI design; parameterized everywhere).
DEFAULT_MIDPOINT_KCAL_PER_MOL = -3.0     # m: ΔΔG at which S = 0.5
DEFAULT_STEEPNESS_PER_KCAL = 1.5         # k: logistic steepness

# Clamp bound: keeps S strictly inside (0, 1) so the logit inverse stays finite
# at the saturating tails (R02 invariant "reject S in {0,1} exactly").
EPS = 1e-9

CORRELATION_FORM = "logistic"


def _sigmoid(x: float) -> float:
    """Numerically stable 1 / (1 + exp(-x)) (no overflow at large |x|)."""
    if x >= 0.0:
        return 1.0 / (1.0 + math.exp(-x))
    e = math.exp(x)
    return e / (1.0 + e)


def s_from_ddg(
    ddg: float,
    m: float = DEFAULT_MIDPOINT_KCAL_PER_MOL,
    k: float = DEFAULT_STEEPNESS_PER_KCAL,
) -> float:
    """Logistic map ΔΔG (kcal/mol) -> antagonism strength S in (0, 1).

    Args:
        ddg: binding free-energy change; negative = destabilizing (weaker
            p53:MDM2 binding).
        m: midpoint ΔΔG (S = 0.5).
        k: steepness (1/(kcal/mol)); must be > 0 for monotone increasing S.

    Returns:
        S clamped to ``[EPS, 1 - EPS]``.
    """
    if k <= 0.0:
        raise ValueError(f"steepness k must be > 0, got {k}")
    s = _sigmoid(k * (ddg - m))
    # Clamp to keep the inverse single-valued / finite at the tails.
    return min(1.0 - EPS, max(EPS, s))


def ddg_from_s(
    s: float,
    m: float = DEFAULT_MIDPOINT_KCAL_PER_MOL,
    k: float = DEFAULT_STEEPNESS_PER_KCAL,
) -> float:
    """Logit inverse S in (0, 1) -> ΔΔG (kcal/mol).

    The PI's "ΔG is the inverse of the correlation": recovers ΔΔG from any
    parameter value S. ``s`` is clamped into ``[EPS, 1 - EPS]`` before the
    logit so boundary values do not diverge.

    Args:
        s: antagonism strength (the value written into ``$KMn_*``).
        m: midpoint ΔΔG (same m used in the forward map).
        k: steepness (same k used in the forward map).
    """
    if k <= 0.0:
        raise ValueError(f"steepness k must be > 0, got {k}")
    s = min(1.0 - EPS, max(EPS, s))
    return m + (1.0 / k) * math.log(s / (1.0 - s))
