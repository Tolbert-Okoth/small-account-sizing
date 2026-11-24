"""Reproduce the README figures (synthetic trades only). Run: python examples/headline.py  (needs matplotlib)."""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import lotsizing as ls

DOCS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs"); os.makedirs(DOCS, exist_ok=True)

# A generic CFD-style contract: 1.0 lot moves 100 account units per 1.0 price unit; 0.01 minimum and step.
SPEC = ls.SymbolSpec(tick_size=0.01, tick_value=1.0, min_lot=0.01, lot_step=0.01)
rng = np.random.default_rng(3); n = 1500
weights = rng.choice([0.5, 1.0, 1.5], n, p=[0.3, 0.4, 0.3])          # a strategy that tilts risk by conviction
edge = 0.08 * weights                                                 # ... and the conviction is informative
stops = rng.lognormal(np.log(4.0), 0.45, n)                           # volatility-scaled stop distances (price units)
BASE, CAP = 0.0025, 0.0075                                             # 0.25 % base risk, hard cap 0.75 % per trade

equities = np.geomspace(1_000, 200_000, 25)
tab = ls.tc_by_capital(equities, weights, stops, BASE, SPEC, CAP, edge=edge)
for eq in (1_000, 5_000, 10_000, 50_000):
    sub = ls.tc_by_capital([eq], weights, stops, BASE, SPEC, CAP, edge=edge)
    print(f"${eq:>7,}: " + " | ".join(f"{r.rounding:7s} TC {r.tc:.2f} IR kept {r.ir_retention:.0%} risk taken {r.risk_ratio:.0%} "
                                      f"skipped {r.skipped:.0%} forced {r.forced_min:.0%}" for r in sub.itertuples()))

# 1) transfer coefficient and IR retention vs account size
fig, axes = plt.subplots(1, 2, figsize=(10, 3.8))
for rnd, c in (("floor", "#d9480f"), ("nearest", "#1c7ed6")):
    s = tab[tab.rounding == rnd]
    axes[0].plot(s.equity, s.tc, color=c, marker="o", ms=3, label=f"round {rnd}")
    axes[1].plot(s.equity, s.risk_ratio, color=c, marker="o", ms=3, label=f"round {rnd}")
axes[0].set_ylabel("transfer coefficient"); axes[0].set_title("How faithfully lots express intended risk")
axes[1].axhline(1, color="#333", lw=.8); axes[1].set_ylabel("risk taken / risk intended"); axes[1].set_title("Systematic under- or over-risking")
for ax in axes:
    ax.set_xscale("log"); ax.set_xlabel("account equity"); ax.grid(alpha=.3); ax.legend(fontsize=8)
fig.tight_layout(); fig.savefig(os.path.join(DOCS, "tc_by_capital.png"), dpi=130); plt.close(fig)

# 2) per-trade realised vs target risk at a small account
df_f = ls.realised_vs_target(5_000, weights, stops, BASE, SPEC, CAP, rounding="floor")
df_n = ls.realised_vs_target(5_000, weights, stops, BASE, SPEC, CAP, rounding="nearest")
fig, ax = plt.subplots(figsize=(7, 4))
bins = np.linspace(0.4, 2.0, 49)
for df, lab, c in ((df_f, "floor", "#d9480f"), (df_n, "nearest", "#1c7ed6")):
    ratio = df.realised_risk / df.target_risk
    ax.hist(ratio, bins=bins, alpha=.55, color=c, label=f"round {lab}: mean {ratio.mean():.2f}, TC {ls.transfer_coefficient(df.target_risk, df.realised_risk):.2f}")
ax.axvline(1, color="#333", lw=1); ax.set_xlabel("risk actually taken / risk intended (per trade)"); ax.set_ylabel("trades")
ax.set_title("5,000 account: floor under-risks, nearest centres on target"); ax.legend(fontsize=8); ax.grid(alpha=.3)
fig.tight_layout(); fig.savefig(os.path.join(DOCS, "realised_vs_target.png"), dpi=130); plt.close(fig)
