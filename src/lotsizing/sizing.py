"""Risk-based lot sizing with discrete lot steps, a hard risk cap and an explicit below-minimum policy. Pure functions."""
from __future__ import annotations

import math
from dataclasses import dataclass

EPS = 1e-9


@dataclass(frozen=True)
class SymbolSpec:
    """Contract description as most retail platforms report it."""
    tick_size: float      # price units per tick
    tick_value: float     # account currency per tick per 1.0 lot
    min_lot: float = 0.01
    lot_step: float = 0.01


@dataclass(frozen=True)
class Size:
    lots: float           # 0.0 means do not trade
    risk: float           # account currency lost if the stop is hit
    risk_frac: float      # risk / equity
    status: str           # ok | ok_capfloor | forced_min | skip_cap | skip_min | skip_invalid


def loss_per_lot(spec: SymbolSpec, stop_distance: float) -> float:
    """Account currency lost per 1.0 lot over `stop_distance` price units."""
    return stop_distance / spec.tick_size * spec.tick_value


def size_trade(equity: float, risk_frac: float, stop_distance: float, spec: SymbolSpec, cap_frac: float,
               rounding: str = "floor", below_min: str = "force") -> Size:
    """Lots that risk `risk_frac` of equity over `stop_distance`, on the platform's lot grid.

    rounding  "floor"   : always round down (never exceeds target, systematically under-risks small accounts)
              "nearest" : round to the nearest step; if that would exceed `cap_frac`, fall back to floor (status ok_capfloor)
    below_min "force"   : trade the minimum lot unless it alone risks more than `cap_frac` (then skip_cap)
              "skip"    : never trade below the size the target implies (skip_min)
    """
    if rounding not in ("floor", "nearest") or below_min not in ("force", "skip"):
        raise ValueError("rounding must be floor|nearest and below_min force|skip")
    if not (equity > 0 and risk_frac > 0 and stop_distance > 0):
        return Size(0.0, 0.0, 0.0, "skip_invalid")
    lpl = loss_per_lot(spec, stop_distance); cap = cap_frac * equity * (1 + EPS)
    raw = equity * risk_frac / lpl
    floor_lots = math.floor(raw / spec.lot_step + EPS) * spec.lot_step

    def ok(lots, status="ok"):
        lots = round(lots, 8); return Size(lots, lots * lpl, lots * lpl / equity, status)

    if rounding == "nearest":
        near = math.floor(raw / spec.lot_step + 0.5 + EPS) * spec.lot_step     # +EPS: exact half steps round up despite float noise
        if near >= spec.min_lot - 1e-12:
            if near * lpl <= cap:
                return ok(near)
            if floor_lots >= spec.min_lot - 1e-12:
                return ok(floor_lots, "ok_capfloor")
    if floor_lots >= spec.min_lot - 1e-12:
        return ok(floor_lots)
    one = spec.min_lot * lpl
    if below_min == "skip":
        return Size(0.0, one, one / equity, "skip_min")
    if one > cap:
        return Size(0.0, one, one / equity, "skip_cap")
    return ok(spec.min_lot, "forced_min")
