import unittest

import numpy as np

import lotsizing as ls

SPEC = ls.SymbolSpec(tick_size=0.01, tick_value=1.0, min_lot=0.01, lot_step=0.01)   # 1 lot = 100 per 1.0 price unit


class Sizing(unittest.TestCase):
    def test_floor_never_exceeds_target(self):
        s = ls.size_trade(10_000, 0.005, 3.0, SPEC, cap_frac=0.02)            # raw 0.1667 lots
        self.assertAlmostEqual(s.lots, 0.16); self.assertLessEqual(s.risk_frac, 0.005)

    def test_nearest_rounds_up_when_closer(self):
        self.assertAlmostEqual(ls.size_trade(10_000, 0.005, 3.0, SPEC, 0.02, rounding="nearest").lots, 0.17)

    def test_exact_half_step_rounds_up(self):
        self.assertAlmostEqual(ls.size_trade(10_000, 0.0015, 1.0, SPEC, 0.02, rounding="nearest").lots, 0.15)  # raw 0.15
        self.assertAlmostEqual(ls.size_trade(10_000, 0.00145, 1.0, SPEC, 0.02, rounding="nearest").lots, 0.15) # raw 0.145

    def test_nearest_respects_cap(self):
        s = ls.size_trade(1_000, 0.0049, 3.0, SPEC, cap_frac=0.005, rounding="nearest")   # raw 0.0163 -> 0.02 would risk 0.6 %
        self.assertEqual(s.status, "ok_capfloor"); self.assertAlmostEqual(s.lots, 0.01)

    def test_below_min_policies(self):
        self.assertEqual(ls.size_trade(1_000, 0.001, 3.0, SPEC, 0.005).status, "forced_min")      # min lot risks 0.3 %
        self.assertEqual(ls.size_trade(1_000, 0.001, 8.0, SPEC, 0.005).status, "skip_cap")        # min lot risks 0.8 %
        self.assertEqual(ls.size_trade(1_000, 0.001, 3.0, SPEC, 0.005, below_min="skip").status, "skip_min")

    def test_invalid(self):
        self.assertEqual(ls.size_trade(0, 0.01, 1.0, SPEC, 0.02).status, "skip_invalid")
        with self.assertRaises(ValueError):
            ls.size_trade(1_000, 0.01, 1.0, SPEC, 0.02, rounding="up")


class Analysis(unittest.TestCase):
    def test_fundamental_law_roundtrip(self):
        ir = ls.fundamental_law_ir(0.05, 400, 0.8); self.assertAlmostEqual(ir, 0.8)
        self.assertAlmostEqual(ls.implied_ic(ir, 400, 0.8), 0.05)

    def test_tc_rises_with_capital(self):
        rng = np.random.default_rng(0); w = rng.choice([0.5, 1.0, 1.5], 400); d = rng.lognormal(np.log(3), 0.4, 400)
        tab = ls.tc_by_capital([2_000, 200_000], w, d, 0.0025, SPEC, 0.01, roundings=("floor",))
        self.assertLess(tab.tc.iloc[0], tab.tc.iloc[1]); self.assertGreater(tab.tc.iloc[1], 0.99)

    def test_ir_retention_perfect_when_equal(self):
        t = np.linspace(1, 2, 300); self.assertAlmostEqual(ls.ir_retention(t, t), 1.0)


if __name__ == "__main__":
    unittest.main()
