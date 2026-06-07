"""Tests for the in-repo `e7m verify` constitutional gate (ADR-2606061500).

These guard the e7m-verify pre-commit hook refactor:
  - the verify() contract (the 9 hard invariants, incl. `no_server_key`),
  - and that the machine path (`python3 -m e7m --json verify`) runs on a BARE
    stdlib python3 — i.e. the lazy `rich` import — so the hook reliably enforces
    instead of skipping or hard-failing with `unknown command: verify`.

Run: PYTHONPATH=src python3 -m pytest tests/  (or `python3 tests/test_verify.py`).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

_SRC = str(Path(__file__).resolve().parents[1] / "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

# The full set of constitutional hard-invariants e7m verify must surface
# (ADR-2605192100 §1). `no_server_key` is the one the CACAO-only migration
# (ADR-2606061500) strengthens — its presence + green state is load-bearing.
EXPECTED_INVARIANT_KEYS = {
    "non_profit_only",
    "no_advertising",
    "tithe_ten_percent",
    "land_inalienable",
    "transparent_force",
    "non_eschatological",
    "anti_individualist",
    "charter_rider_required",
    "no_server_key",
}


def test_verify_contract_shape() -> None:
    from e7m import commands

    out = commands.verify()
    assert isinstance(out["ok"], bool)
    assert isinstance(out["total"], int) and out["total"] >= len(EXPECTED_INVARIANT_KEYS)
    assert 0 <= out["passed"] <= out["total"]
    assert out["ok"] == (out["passed"] == out["total"])
    keys = {c["key"] for c in out["checks"]}
    assert EXPECTED_INVARIANT_KEYS.issubset(keys), f"missing invariants: {EXPECTED_INVARIANT_KEYS - keys}"
    for c in out["checks"]:
        assert isinstance(c["key"], str) and c["key"]
        assert isinstance(c["passed"], bool)
        assert isinstance(c["description"], str) and c["description"]
        assert isinstance(c["evidence"], list)
    assert out["constitutional_anchor"].startswith("ADR-2605192100")


def test_no_server_key_invariant_present_and_green() -> None:
    """The CACAO-only migration must not have introduced a server-held key."""
    from e7m import commands

    out = commands.verify()
    nsk = next((c for c in out["checks"] if c["key"] == "no_server_key"), None)
    assert nsk is not None, "no_server_key invariant missing from verify()"
    assert nsk["passed"] is True, f"no_server_key VIOLATED: {nsk['evidence']}"


def test_json_verify_cli_runs_and_exit_code_tracks_ok() -> None:
    """`python3 -m e7m --json verify` emits valid JSON and exits 0 iff ok."""
    env = dict(os.environ, PYTHONPATH=_SRC)
    proc = subprocess.run(
        [sys.executable, "-m", "e7m", "--json", "verify"],
        capture_output=True, text=True, env=env, cwd=str(Path(_SRC).parents[2]),
    )
    payload = json.loads(proc.stdout)  # must be valid JSON (no rich/log noise on stdout)
    assert set(payload) >= {"ok", "passed", "total", "checks"}
    assert proc.returncode == (0 if payload["ok"] else 1)


def test_main_imports_and_verifies_without_rich() -> None:
    """The hook path must work on a workstation with no `rich` installed:
    `e7m.__main__` imports (lazy rich → console is None) and `--json verify`
    still produces JSON + the correct exit code."""
    script = (
        "import sys, json\n"
        # Block `rich` so the import falls into the stdlib-only except branch.
        "sys.modules['rich'] = None\n"
        "for m in list(sys.modules):\n"
        "    if m == 'rich' or m.startswith('rich.'):\n"
        "        if m != 'rich': del sys.modules[m]\n"
        "import e7m.__main__ as main\n"
        "assert main.console is None, 'rich should be unavailable in this subprocess'\n"
        "class A:\n"
        "    json = True\n"
        "rc = main.cmd_verify(A())\n"
        "assert rc in (0, 1), rc\n"
        "print('RICHLESS_OK', rc)\n"
    )
    env = dict(os.environ, PYTHONPATH=_SRC)
    proc = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True, text=True, env=env, cwd=str(Path(_SRC).parents[2]),
    )
    assert "RICHLESS_OK" in proc.stdout, f"stdout={proc.stdout!r} stderr={proc.stderr!r}"


if __name__ == "__main__":  # plain-python runnable (no pytest required)
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)} passed")
