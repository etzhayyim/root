"""End-to-end: run the real plc-control component under wasmtime (ADR §D2/§D3).

Builds the guest component, then builds + runs the native wasmtime host runner,
and asserts the control history + N3 fault-atomicity observed through ACTUAL WASM
execution. Skips cleanly when the toolchain is unavailable. Slow (~cold wasmtime
build); subsequent runs are cached.

Run: `python3 -m unittest test_plc_host_e2e -v`
"""

import pathlib
import shutil
import subprocess
import unittest

_HERE = pathlib.Path(__file__).resolve().parent
_GUEST_BUILD = _HERE / "plc-control-guest" / "build.sh"
_HOST = _HERE / "plc-host-runner"


def _toolchain_ready() -> bool:
    if not all(shutil.which(t) for t in ("rustup", "wasm-tools", "cargo")):
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
class PlcHostEndToEnd(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        b = subprocess.run(["bash", str(_GUEST_BUILD)], capture_output=True,
                           text=True, timeout=600)
        if b.returncode != 0:
            raise AssertionError(f"guest build failed:\n{b.stdout}\n{b.stderr}")
        r = subprocess.run(["cargo", "run", "--release"], cwd=str(_HOST),
                           capture_output=True, text=True, timeout=900)
        cls.out = r.stdout
        cls.rc = r.returncode
        if r.returncode != 0:
            raise AssertionError(f"host runner failed:\n{r.stdout}\n{r.stderr}")

    def test_e2e_ok(self):
        self.assertEqual(self.rc, 0)
        self.assertIn("E2E OK", self.out)

    def test_control_history_through_real_wasm(self):
        self.assertIn("CYCLE 0 pv=3 cmd=ON", self.out)
        self.assertIn("CYCLE 1 pv=20 cmd=OFF", self.out)
        self.assertIn("CYCLE 2 pv=8 cmd=ON", self.out)

    def test_n3_fault_atomicity_through_real_wasm(self):
        # faulted sensor read -> guest returns Err -> nothing committed
        self.assertIn("CYCLE 3 FAULTED", self.out)
        self.assertIn("no commit", self.out)
        # exactly 6 datoms (3 committed cycles x 2), faulted cycle added none
        self.assertIn("DATOMS=6", self.out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
