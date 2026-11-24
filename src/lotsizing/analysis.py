"""How much of a strategy's intended risk profile survives lot granularity: transfer coefficient and the fundamental law."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .sizing import SymbolSpec, size_trade


def fundamental_law_ir(ic: float, breadth: float, tc: float = 1.0) -> float:
    """Grinold-Kahn: IR = IC x sqrt(breadth) x TC (breadth = independent bets per year)."""
    return ic * np.sqrt(breadth) * tc


def implied_ic(ir: float, breadth: float, tc: float = 1.0) -> float:
    """Skill per bet implied by an observed IR."""
    return ir / (np.sqrt(breadth) * tc)


def realised_vs_target(equity: float, weights, stop_distances, base_risk_frac: float, spec: SymbolSpec, cap_frac: float,
                       **kw) -> pd.DataFrame:
    """Size every trade and compare the risk actually taken with the risk intended (base_risk_frac x weight x equity)."""
    rows = []
    for w, d in zip(weights, stop_distances):
        s = size_trade(equity, base_risk_frac * w, d, spec, cap_frac, **kw)
        rows.append((w, d, equity * base_risk_frac * w, s.risk if s.lots > 0 else 0.0, s.status))
    return pd.DataFrame(rows, columns=["weight", "stop_distance", "target_risk", "realised_risk", "status"])


def transfer_coefficient(target, realised) -> float:
    """Correlation between intended and realised risk per trade (1 = sizing expresses every intended bet faithfully)."""
    t, r = np.asarray(target, float), np.asarray(realised, float)
    if t.std() == 0 or r.std() == 0:
        return float("nan")
    return float(np.corrcoef(t, r)[0, 1])


def ir_retention(target, realised, edge=0.1, n_sims: int = 200, seed: int = 0) -> float:
    """Share of the ideal IR kept when each trade's R outcome (mean `edge`, sd 1) is scaled by realised instead of target risk.
    `edge` may be a per-trade array: when conviction weights carry information, mis-sizing them costs IR."""
    t, r = np.asarray(target, float), np.asarray(realised, float); rng = np.random.default_rng(seed); out = []
    mu = np.broadcast_to(np.asarray(edge, float), t.shape)
    for _ in range(n_sims):
        R = rng.normal(mu, 1.0); pt, pr = t * R, r * R
        if pr.std() > 0:
            out.append((pr.mean() / pr.std()) / (pt.mean() / pt.std()))
    return float(np.mean(out)) if out else 0.0


def tc_by_capital(equities, weights, stop_distances, base_risk_frac: float, spec: SymbolSpec, cap_frac: float,
                  roundings=("floor", "nearest"), edge=0.1, **kw) -> pd.DataFrame:
    """Transfer coefficient, risk ratio, skip and forced shares for each account size and rounding rule."""
    rows = []
    for eq in equities:
        for rnd in roundings:
            df = realised_vs_target(eq, weights, stop_distances, base_risk_frac, spec, cap_frac, rounding=rnd, **kw)
            rows.append(dict(equity=eq, rounding=rnd, tc=transfer_coefficient(df.target_risk, df.realised_risk),
                             ir_retention=ir_retention(df.target_risk, df.realised_risk, edge),
                             risk_ratio=float(df.realised_risk.sum() / df.target_risk.sum()),
                             skipped=float(df.status.str.startswith("skip").mean()),
                             forced_min=float(df.status.eq("forced_min").mean())))
    return pd.DataFrame(rows)
