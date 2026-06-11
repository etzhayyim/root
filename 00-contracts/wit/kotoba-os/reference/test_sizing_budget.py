"""Consistency checks for the kotoba-os sizing budget (ADR-2606031600 §D6).

The budget numbers are ENGINEERING ESTIMATES (the file says so). These tests do
NOT assert the estimates are *true* — only that the budget is internally
CONSISTENT and that its central claim holds under its own low-end estimates:
the minimal bootable PLC node (wasmi runtime + minimal substrate + 1 actor) fits
the T1 RAM/flash floor. R2 measurement either confirms the estimates or corrects
this file; the test then re-checks the conclusion automatically.

Run: `python3 -m unittest test_sizing_budget -v`
"""

import json
import pathlib
import unittest

_HERE = pathlib.Path(__file__).resolve().parent
_BUDGET = _HERE.parent / "sizing-budget.json"


def _load():
    return json.loads(_BUDGET.read_text())


class SizingBudget(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.b = _load()
        cls.ram = {c["id"]: c for c in cls.b["ram_components"]}
        cls.flash = {c["id"]: c for c in cls.b["flash_components"]}

    def test_every_estimate_is_a_valid_low_high_range(self):
        """Each component is a [low, high] MiB range with low <= high and a source."""
        for c in self.b["ram_components"] + self.b["flash_components"]:
            lo, hi = c["mib"]
            self.assertLessEqual(lo, hi, msg=f"{c['id']} range inverted")
            self.assertGreaterEqual(lo, 0, msg=f"{c['id']} negative")
            self.assertTrue(c.get("source"), msg=f"{c['id']} missing source/assumption")

    def test_tiers_are_ordered_and_T0_is_not_a_target(self):
        """Device tiers ascend in RAM; the MCU tier is honestly excluded."""
        tiers = self.b["device_tiers"]
        floors = [t["ram_mib"][0] for t in tiers]
        self.assertEqual(floors, sorted(floors), msg="tiers not ascending by RAM floor")
        t0 = next(t for t in tiers if t["id"] == "T0-mcu")
        self.assertFalse(t0["kotoba_os_target"], msg="T0 must not be claimed as a target")
        self.assertTrue(t0["note"], msg="T0 exclusion must be justified")

    def test_minimal_profile_references_real_components(self):
        prof = self.b["minimal_resident_profile"]
        for cid in prof["ram_components"]:
            self.assertIn(cid, self.ram, msg=f"unknown ram component {cid}")
        for cid in prof["flash_components"]:
            self.assertIn(cid, self.flash, msg=f"unknown flash component {cid}")
        # the minimal profile must use the SMALL runtime (wasmi), not the JIT
        self.assertIn("wasm-runtime-wasmi", prof["ram_components"])
        self.assertNotIn("wasm-runtime-wasmtime", prof["ram_components"])

    def test_minimal_low_end_RAM_fits_T1_floor(self):
        """THE central claim: low-end minimal resident set < T1 RAM floor (64 MiB)."""
        prof = self.b["minimal_resident_profile"]
        low_sum = sum(self.ram[c]["mib"][0] for c in prof["ram_components"])
        self.assertLess(
            low_sum, prof["ram_floor_target_mib"],
            msg=f"minimal low-end RAM {low_sum} MiB does not fit "
                f"{prof['ram_floor_target_mib']} MiB T1 floor",
        )
        # and the T1 tier floor must actually be >= the target we assert against
        t1 = next(t for t in self.b["device_tiers"] if t["id"] == "T1-constrained-soc")
        self.assertGreaterEqual(t1["ram_mib"][0], prof["ram_floor_target_mib"])

    def test_minimal_low_end_flash_fits_T1_floor(self):
        prof = self.b["minimal_resident_profile"]
        low_sum = sum(self.flash[c]["mib"][0] for c in prof["flash_components"])
        self.assertLess(low_sum, prof["flash_floor_target_mib"])

    def test_high_end_minimal_may_exceed_T1_floor(self):
        """Honesty check: the HIGH-end minimal estimate is allowed to blow the T1
        floor — that is exactly why T2 exists. We assert the budget is not
        secretly claiming the worst case also fits (which would be dishonest)."""
        prof = self.b["minimal_resident_profile"]
        high_sum = sum(self.ram[c]["mib"][1] for c in prof["ram_components"])
        # not an assertion of failure — just confirm the spread is real (high > low)
        low_sum = sum(self.ram[c]["mib"][0] for c in prof["ram_components"])
        self.assertGreater(high_sum, low_sum, msg="estimate range collapsed to a point")

    def test_disclaimer_present(self):
        """The estimate disclaimer must be present so no reader mistakes these
        for measured numbers."""
        self.assertIn("ESTIMATE", self.b["estimate_disclaimer"].upper())
        self.assertIn("ESTIMATE", self.b["_about"].upper())


if __name__ == "__main__":
    unittest.main(verbosity=2)
