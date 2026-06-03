"""Manifest <-> component authorization (ADR-2606031600 §D1 + §D2).

The genesis manifest's `capabilities.interfaces` must grant EVERY device/Datom
interface the actor's WASM component actually imports — otherwise the boot path
would load an actor it cannot satisfy / cannot scope. This test extracts the real
imports from the built `plc-control` component and checks two manifests:

  * genesis-plc-bangbang.json  — grants {io-analog, io-digital, datom}  -> AUTHORIZES
  * genesis-hikari-pv-controller.json — grants {io-analog, fieldbus-modbus, datom},
    a modbus controller manifest, so it does NOT authorize the digital-output
    bang-bang guest (missing io-digital). This negative case proves the check has teeth.

Skips cleanly without the wasm32 toolchain / wasm-tools.

Run: `python3 -m unittest test_manifest_authorizes_component -v`
"""

import json
import pathlib
import re
import shutil
import subprocess
import unittest

_HERE = pathlib.Path(__file__).resolve().parent
_GUEST = _HERE / "plc-control-guest"
_BUILD = _GUEST / "build.sh"
_COMPONENT = _GUEST / "plc-control.component.wasm"
_EX = _HERE / "examples"


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


def _component_imports() -> set:
    """The kotoba:os interfaces the built component imports (ground truth)."""
    w = subprocess.run(["wasm-tools", "component", "wit", str(_COMPONENT)],
                       capture_output=True, text=True, timeout=60).stdout
    return set(re.findall(r"import kotoba:os/([a-z0-9-]+)@", w))


def _granted(manifest_name: str) -> set:
    m = json.loads((_EX / manifest_name).read_text())
    return set(m["capabilities"]["interfaces"])


def _authorizes(granted: set, imports: set) -> set:
    """Return the set of imports NOT granted (empty = authorized)."""
    return imports - granted


@unittest.skipUnless(_toolchain_ready(), "wasm32 toolchain / wasm-tools unavailable")
class ManifestAuthorizesComponent(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        b = subprocess.run(["bash", str(_BUILD)], capture_output=True, text=True,
                           timeout=600)
        if b.returncode != 0:
            raise AssertionError(f"guest build failed:\n{b.stdout}\n{b.stderr}")
        cls.imports = _component_imports()

    def test_component_imports_are_the_expected_three(self):
        self.assertEqual(self.imports, {"io-analog", "io-digital", "datom"})

    def test_matching_manifest_authorizes(self):
        missing = _authorizes(_granted("genesis-plc-bangbang.json"), self.imports)
        self.assertEqual(missing, set(), msg=f"unexpectedly missing: {missing}")

    def test_modbus_manifest_does_not_authorize_digital_guest(self):
        # hikari grants io-analog + fieldbus-modbus + datom but NOT io-digital,
        # which the bang-bang guest writes — so it must fail authorization.
        missing = _authorizes(_granted("genesis-hikari-pv-controller.json"), self.imports)
        self.assertIn("io-digital", missing,
                      msg="check has no teeth: hikari should fail to grant io-digital")


if __name__ == "__main__":
    unittest.main(verbosity=2)
