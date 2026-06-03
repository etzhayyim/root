"""Boot the minimal kotoba-os unikernel PoC under QEMU (ADR-2606031600 L1/L2).

Builds the no_std aarch64 image and boots it on qemu-system-aarch64 `virt`,
asserting it reaches `KOTOBA-OS BOOT OK` over the real PL011 UART. This is the
reference's only *actual boot* — a genuine (minimal) unikernel-boot + MMIO I/O
demonstration. Skips cleanly without the aarch64-unknown-none target or QEMU.

Run: `python3 -m unittest test_boot_poc -v`  (slow: builds + boots)
"""

import pathlib
import shutil
import subprocess
import unittest

_HERE = pathlib.Path(__file__).resolve().parent
_RUN = _HERE / "boot-poc" / "run.sh"


def _ready() -> bool:
    if not shutil.which("rustup") or not shutil.which("qemu-system-aarch64"):
        return False
    try:
        tc = subprocess.run(["rustup", "show", "active-toolchain"],
                            capture_output=True, text=True, timeout=30)
        name = tc.stdout.split()[0] if tc.stdout else ""
        core = (pathlib.Path.home() / ".rustup" / "toolchains" / name
                / "lib" / "rustlib" / "aarch64-unknown-none" / "lib")
        return name != "" and any(core.glob("libcore-*.rlib"))
    except Exception:
        return False


@unittest.skipUnless(_ready(), "aarch64-unknown-none target / qemu-system-aarch64 unavailable")
class BootPoc(unittest.TestCase):
    def test_unikernel_boots_and_does_mmio_uart(self):
        r = subprocess.run(["bash", str(_RUN)], capture_output=True, text=True,
                           timeout=300)
        out = r.stdout + r.stderr
        self.assertIn("KOTOBA-OS BOOT OK", out, msg=out[-2000:])
        self.assertIn("PL011 UART @ 0x09000000 written via volatile MMIO", out)
        # the kotoba-os scan-cycle model runs INSIDE the booted unikernel:
        # 3 cycles -> 6 Datoms; the faulted cycle (N3) commits 0.
        self.assertIn("KOTOBA-OS SCAN OK", out, msg=out[-2000:])
        self.assertIn("faulted_datoms=0 total_datoms=6", out)
        self.assertIn("DATOM t=2 ctrl :ctrl/command=1", out)
        # a REAL core-wasm module runs under the wasmi interpreter IN-KERNEL,
        # calling host funcs to produce Datoms.
        self.assertIn("KOTOBA-OS WASM OK", out, msg=out[-2000:])
        self.assertIn("interpreter=wasmi, in-unikernel", out)
        self.assertIn("WASM DATOM t=2 ctrl :ctrl/command=1", out)
        # host reads a command STRING from the wasm guest's linear memory
        # (the primitive real Component-Model components need for Fact strings).
        self.assertIn("KOTOBA-OS WASMEM OK", out, msg=out[-2000:])
        self.assertIn('WASMEM t=0 ctrl :ctrl/command="ON" (read from guest memory)', out)
        self.assertIn('WASMEM t=1 ctrl :ctrl/command="OFF"', out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
