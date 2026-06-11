"""Device-surface binding coverage (ADR-2606031600 §D3).

Builds a single component that touches EVERY kotoba:os device interface and
asserts all 8 bind into the component's world. This proves the entire WIT device
surface (io-{digital,analog,gpio} + fieldbus-{modbus,opcua,ethercat,canopen} +
datom) compiles to real WASM imports — completing per-interface coverage beyond
the plc-control (digital) and modbus components. HONEST: a completeness smoke
test, not a realistic controller.

Skips cleanly without the wasm32 toolchain / wasm-tools.

Run: `python3 -m unittest test_device_coverage_component -v`
"""

import pathlib
import re
import shutil
import subprocess
import unittest

_HERE = pathlib.Path(__file__).resolve().parent
_GUEST = _HERE / "device-coverage-guest"
_BUILD = _GUEST / "build.sh"
_COMPONENT = _GUEST / "device-coverage.component.wasm"

_ALL_INTERFACES = {
    "io-digital", "io-analog", "io-gpio",
    "fieldbus-modbus", "fieldbus-opcua", "fieldbus-ethercat", "fieldbus-canopen",
    "datom",
}


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
class DeviceCoverageComponent(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        b = subprocess.run(["bash", str(_BUILD)], capture_output=True, text=True,
                           timeout=600)
        if b.returncode != 0:
            raise AssertionError(f"build.sh failed:\n{b.stdout}\n{b.stderr}")
        w = subprocess.run(["wasm-tools", "component", "wit", str(_COMPONENT)],
                           capture_output=True, text=True, timeout=60).stdout
        cls.imports = set(re.findall(r"import kotoba:os/([a-z0-9-]+)@", w))

    def test_every_device_interface_binds(self):
        # the whole kotoba:os device surface compiles into real WASM imports
        self.assertEqual(self.imports, _ALL_INTERFACES,
                         msg=f"missing: {_ALL_INTERFACES - self.imports}; "
                             f"extra: {self.imports - _ALL_INTERFACES}")

    def test_component_is_valid(self):
        self.assertTrue(_COMPONENT.exists())
        self.assertGreater(_COMPONENT.stat().st_size, 1000)


if __name__ == "__main__":
    unittest.main(verbosity=2)
