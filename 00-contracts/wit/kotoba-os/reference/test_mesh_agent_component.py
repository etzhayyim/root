"""Build + verify the real mesh-agent WASM Component (ADR-2606031600 §D2/§D5).

Proves the SECOND L5 world compiles to a real WASM Component-Model component and
that a mesh agent has ZERO device authority — its world imports only `datom`, no
`io-*`/`fieldbus-*`. Same artifact kind as plc-control-guest, different world.
Skips cleanly when the toolchain is unavailable.

Run: `python3 -m unittest test_mesh_agent_component -v`
"""

import pathlib
import shutil
import subprocess
import unittest

_HERE = pathlib.Path(__file__).resolve().parent
_GUEST = _HERE / "mesh-agent-guest"
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
class MeshAgentComponent(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        r = subprocess.run(["bash", str(_BUILD)], capture_output=True, text=True,
                           timeout=600)
        if r.returncode != 0:
            raise AssertionError(f"build.sh failed:\n{r.stdout}\n{r.stderr}")
        cls.world = r.stdout

    def test_component_produced_and_valid(self):
        comp = _GUEST / "mesh-agent.component.wasm"
        self.assertTrue(comp.exists())
        self.assertGreater(comp.stat().st_size, 1000)

    def test_exports_step(self):
        self.assertIn("export step: func() -> result<u32, string>", self.world)

    def test_agent_has_zero_device_authority(self):
        # an agent's only capability is the Datom log — no io/fieldbus imports.
        self.assertIn("import kotoba:os/datom", self.world)
        self.assertNotIn("io-", self.world)
        self.assertNotIn("fieldbus", self.world)


if __name__ == "__main__":
    unittest.main(verbosity=2)
