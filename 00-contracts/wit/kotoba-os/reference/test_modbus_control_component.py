"""Modbus control component — fieldbus coverage + hikari authorization
(ADR-2606031600 §D3 + §D1).

This is the first component exercising a `fieldbus-*` interface. Its tree-shaken
imports are {io-analog, fieldbus-modbus, datom} — exactly what the hikari
grid-edge manifest grants, so this test ALSO closes the loop from
test_manifest_authorizes_component: the hikari manifest authorizes a REAL built
component (the bang-bang guest needed io-digital, which hikari does not grant).

Skips cleanly without the wasm32 toolchain / wasm-tools.

Run: `python3 -m unittest test_modbus_control_component -v`
"""

import json
import pathlib
import re
import shutil
import subprocess
import unittest

_HERE = pathlib.Path(__file__).resolve().parent
_GUEST = _HERE / "modbus-control-guest"
_BUILD = _GUEST / "build.sh"
_COMPONENT = _GUEST / "modbus-control.component.wasm"
_HIKARI = _HERE / "examples" / "genesis-hikari-pv-controller.json"


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
class ModbusControlComponent(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        b = subprocess.run(["bash", str(_BUILD)], capture_output=True, text=True,
                           timeout=600)
        if b.returncode != 0:
            raise AssertionError(f"build.sh failed:\n{b.stdout}\n{b.stderr}")
        w = subprocess.run(["wasm-tools", "component", "wit", str(_COMPONENT)],
                           capture_output=True, text=True, timeout=60).stdout
        cls.imports = set(re.findall(r"import kotoba:os/([a-z0-9-]+)@", w))

    def test_uses_fieldbus_modbus(self):
        # first component to exercise a fieldbus-* interface
        self.assertIn("fieldbus-modbus", self.imports)

    def test_imports_are_exactly_the_modbus_triple(self):
        self.assertEqual(self.imports, {"io-analog", "fieldbus-modbus", "datom"})
        self.assertNotIn("io-digital", self.imports)  # modbus, not discrete I/O

    def test_hikari_manifest_authorizes_this_component(self):
        granted = set(json.loads(_HIKARI.read_text())["capabilities"]["interfaces"])
        ungranted = self.imports - granted
        self.assertEqual(ungranted, set(),
                         msg=f"hikari should authorize the modbus controller; "
                             f"ungranted={ungranted}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
