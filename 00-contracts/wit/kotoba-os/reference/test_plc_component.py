"""Build + verify the real plc-control WASM Component (ADR-2606031600 §D2/§D3).

This actually compiles `plc-control-guest/` to a WASM Component-Model component
and asserts the extracted world matches the `kotoba:os` `plc-control` contract:
it must export `scan(cycle) -> scan-report` and import only the device/Datom
interfaces it uses. Skips cleanly when the toolchain (rustup wasm32 std +
wasm-tools) is unavailable, so the fast suites still run everywhere.

Run: `python3 -m unittest test_plc_component -v`  (slow: ~8 s cold build)
"""

import pathlib
import shutil
import subprocess
import unittest

_HERE = pathlib.Path(__file__).resolve().parent
_GUEST = _HERE / "plc-control-guest"
_BUILD = _GUEST / "build.sh"


def _toolchain_ready() -> bool:
    if not shutil.which("rustup") or not shutil.which("wasm-tools"):
        return False
    try:
        tc = subprocess.run(["rustup", "show", "active-toolchain"],
                            capture_output=True, text=True, timeout=30)
        name = tc.stdout.split()[0] if tc.stdout else ""
        core = (pathlib.Path.home() / ".rustup" / "toolchains" / name
                / "lib" / "rustlib" / "wasm32-unknown-unknown" / "lib")
        return name != "" and any(core.glob("libcore-*.rlib"))
    except Exception:
        return False


@unittest.skipUnless(_toolchain_ready(), "wasm32 toolchain / wasm-tools unavailable")
class PlcControlComponent(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        r = subprocess.run(["bash", str(_BUILD)], capture_output=True, text=True,
                           timeout=600)
        cls.proc = r
        if r.returncode != 0:
            raise AssertionError(f"build.sh failed:\nSTDOUT{r.stdout}\nSTDERR{r.stderr}")
        cls.world = r.stdout

    def test_component_was_produced_and_valid(self):
        comp = _GUEST / "plc-control.component.wasm"
        self.assertTrue(comp.exists(), "component binary not produced")
        self.assertGreater(comp.stat().st_size, 1000)
        # build.sh runs `wasm-tools validate` and would have non-zero exit on fail
        self.assertEqual(self.proc.returncode, 0)

    def test_exports_scan_with_scan_report(self):
        self.assertIn("export scan: func(cycle: u64) -> result<scan-report, string>",
                      self.world)
        self.assertIn("record scan-report", self.world)

    def test_imports_are_capability_minimized(self):
        # The bang-bang controller uses exactly analog-read, digital-write, datom.
        self.assertIn("import kotoba:os/io-analog", self.world)
        self.assertIn("import kotoba:os/io-digital", self.world)
        self.assertIn("import kotoba:os/datom", self.world)
        # wit-bindgen tree-shakes unused imports: fieldbus/gpio must NOT appear.
        self.assertNotIn("fieldbus", self.world)
        self.assertNotIn("io-gpio", self.world)


if __name__ == "__main__":
    unittest.main(verbosity=2)
