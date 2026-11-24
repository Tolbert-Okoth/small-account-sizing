"""lotsizing: risk-based lot sizing for small accounts, and how much of the intended risk profile survives lot granularity."""
from .analysis import fundamental_law_ir, implied_ic, ir_retention, realised_vs_target, tc_by_capital, transfer_coefficient
from .sizing import Size, SymbolSpec, loss_per_lot, size_trade

__all__ = ["SymbolSpec", "Size", "loss_per_lot", "size_trade", "realised_vs_target", "transfer_coefficient", "ir_retention",
           "tc_by_capital", "fundamental_law_ir", "implied_ic"]
__version__ = "0.1.0"
