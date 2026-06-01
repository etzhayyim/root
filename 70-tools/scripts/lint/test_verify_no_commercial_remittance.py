"""Tests for verify_no_commercial_remittance.py.

Validates that the ADR-2605282200 G7 build-time gate (a) treats unguarded
paths as clean (R0 path-reserved), (b) catches violation patterns in each
of the 15 vendor name forms, (c) does NOT match the same names when they
appear in non-import contexts (docstrings, comments, README), and (d)
respects the explicit allow-list (the lint script itself + the ADR doc).
"""

from __future__ import annotations

import importlib.util
import sys
import textwrap
from pathlib import Path

import pytest


_SCRIPT = Path(__file__).resolve().parent / "verify_no_commercial_remittance.py"


@pytest.fixture(scope="module")
def verifier():
    spec = importlib.util.spec_from_file_location(
        "verify_no_commercial_remittance", _SCRIPT
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["verify_no_commercial_remittance"] = mod
    spec.loader.exec_module(mod)
    return mod


def _make_guarded_tree(tmp_path: Path) -> Path:
    """Create the kawase-yui guarded directory inside tmp_path."""
    pkg = tmp_path / "20-actors" / "kawase-yui"
    pkg.mkdir(parents=True)
    return pkg


def test_r0_path_reserved_is_clean(verifier, tmp_path):
    """With no guarded directory present, the hook returns no findings."""
    findings = verifier.find_violations(tmp_path)
    assert findings == []


def test_clean_file_is_clean(verifier, tmp_path):
    """A kawase-yui source file with no vendor reference returns no findings."""
    pkg = _make_guarded_tree(tmp_path)
    (pkg / "client.py").write_text(
        textwrap.dedent(
            """
            from __future__ import annotations

            from chainlink_oracle import PriceFeed
            from base_l2 import KawaseYuiPool

            def send_intent(): ...
            """
        ).lstrip(),
        encoding="utf-8",
    )
    findings = verifier.find_violations(tmp_path)
    assert findings == []


@pytest.mark.parametrize(
    "import_line, expected_match",
    [
        ("from wise import api", "wise"),
        ("from western_union import Wire", "western_union"),
        ("from western-union import x", "western-union"),
        ("import moneygram", "moneygram"),
        ("from remitly_sdk import Client", "remitly"),
        ("import worldremit", "worldremit"),
        ("from xoom import Xfer", "xoom"),
        ("from revolut import Wallet", "revolut"),
        ("from ofx_money import Quote", "ofx_money"),
        ("from currencies_direct import API", "currencies_direct"),
        ("from ria_money import Send", "ria_money"),
        ("import paysend", "paysend"),
        ("from atlantic_money import Quote", "atlantic_money"),
        ("from sendwave import Tx", "sendwave"),
        ("from boss_revolution import Card", "boss_revolution"),
        ("from paypal_xoom import Bridge", "paypal_xoom"),
        ("from transferwise import LegacyApi", "transferwise"),
    ],
)
def test_each_vendor_caught_in_import(verifier, tmp_path, import_line, expected_match):
    """Every documented vendor must be caught in a python `from X import` line."""
    pkg = _make_guarded_tree(tmp_path)
    (pkg / "violator.py").write_text(import_line + "\n", encoding="utf-8")
    findings = verifier.find_violations(tmp_path)
    assert len(findings) == 1
    rel_path, line_no, match = findings[0]
    assert "kawase-yui" in str(rel_path)
    assert line_no == 1
    assert expected_match.lower().replace("_", "").replace("-", "") in (
        match.lower().replace("_", "").replace("-", "")
    )


def test_vendor_in_comment_is_clean(verifier, tmp_path):
    """References inside comments / docstrings are not violations.

    The vendor name in a comment or docstring is documenting the
    prohibition, not implementing an integration.
    """
    pkg = _make_guarded_tree(tmp_path)
    (pkg / "documented.py").write_text(
        textwrap.dedent(
            '''
            """ADR-2605282200 G7 forbids Wise / Western Union / MoneyGram.

            This module enforces that prohibition; it does NOT integrate them.
            """

            # Vendor list (forbidden): Wise, Revolut, Xoom, Remitly.
            FORBIDDEN = "wise, revolut, xoom, remitly"
            '''
        ).lstrip(),
        encoding="utf-8",
    )
    findings = verifier.find_violations(tmp_path)
    assert findings == []


def test_url_reference_is_violation(verifier, tmp_path):
    """A bare URL reference to a vendor host is treated as integration intent."""
    pkg = _make_guarded_tree(tmp_path)
    (pkg / "url.py").write_text(
        "BASE_URL = 'https://wise.com/api/v3/transfers'\n",
        encoding="utf-8",
    )
    findings = verifier.find_violations(tmp_path)
    assert len(findings) == 1


def test_allow_listed_self_is_clean(verifier, tmp_path):
    """The lint script itself is allow-listed even when it names vendors."""
    # Copy the actual verify_no_commercial_remittance.py into the tree and
    # confirm it does NOT trigger when scanned (it is allow-listed by path).
    # Allow-list keys are anchored to the repo root, so we mirror the layout.
    target = tmp_path / "70-tools" / "scripts" / "lint"
    target.mkdir(parents=True)
    (target / "verify_no_commercial_remittance.py").write_text(
        _SCRIPT.read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    findings = verifier.find_violations(tmp_path)
    assert findings == []


def test_unguarded_path_is_ignored(verifier, tmp_path):
    """A vendor import OUTSIDE the guarded roots is not a kawase-yui violation."""
    # This hook intentionally only guards kawase-yui paths; other actors
    # may legitimately reference commercial software for their own
    # purposes (e.g., interoperability research). The G7 prohibition is
    # kawase-yui-specific.
    other_pkg = tmp_path / "60-apps" / "some-other-app"
    other_pkg.mkdir(parents=True)
    (other_pkg / "violator.py").write_text(
        "from wise import api\n", encoding="utf-8"
    )
    findings = verifier.find_violations(tmp_path)
    assert findings == []


# ---------------------------------------------------------------------
#  End-to-end subprocess tests — exercise the hook the way lefthook +
#  GitHub Actions invoke it (not via library import) so a regression
#  in the CLI entry point can't sneak past the function-level tests.
# ---------------------------------------------------------------------


def test_e2e_subprocess_exits_zero_when_clean(tmp_path):
    """Run the script as a subprocess with --root pointed at a clean
    tmpfs tree. Must exit 0 with the clean banner on stdout.
    """
    import subprocess
    import sys

    # Create the guarded directory so the script has something to walk
    # but with no violator content.
    pkg = tmp_path / "20-actors" / "kawase-yui"
    pkg.mkdir(parents=True)
    (pkg / "clean.py").write_text("def noop(): return None\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(_SCRIPT), "--root", str(tmp_path)],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, (
        f"Expected exit 0 on clean tree. stdout={result.stdout!r} "
        f"stderr={result.stderr!r}"
    )
    assert "gate: clean" in result.stdout


def test_e2e_subprocess_exits_one_when_violator_present(tmp_path):
    """Run the script as a subprocess with --root pointed at a tmpfs
    tree containing a synthetic Wise import in a guarded path. Must
    exit 1 with the G7-violation banner on stderr.

    This catches regressions in the CLI-side error-formatting + exit
    code logic that the function-level find_violations tests would
    miss. lefthook + GitHub Actions invoke the script via subprocess,
    not via library import, so this is the higher-fidelity test.
    """
    import subprocess
    import sys

    # Plant the synthetic violator in the actor root (one of the
    # canonical guarded paths declared in _GUARDED_ROOTS).
    pkg = tmp_path / "20-actors" / "kawase-yui"
    pkg.mkdir(parents=True)
    (pkg / "evil.py").write_text(
        "from wise import api\n# G7 violator for the e2e test\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(_SCRIPT), "--root", str(tmp_path)],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 1, (
        f"Expected exit 1 on violator. stdout={result.stdout!r} "
        f"stderr={result.stderr!r}"
    )
    assert "ADR-2605282200 G7 violation" in result.stderr, (
        f"Expected G7 violation banner in stderr; got {result.stderr!r}"
    )
    # Violation message should name the file + the matched vendor token.
    assert "evil.py" in result.stderr
    assert "wise" in result.stderr.lower()


def test_e2e_subprocess_exits_one_on_url_in_guarded_path(tmp_path):
    """URL-literal violator (string-assignment style) also exits 1 via
    subprocess. Complements test_url_reference_is_violation by
    covering the CLI entry point.
    """
    import subprocess
    import sys

    pkg = tmp_path / "50-infra" / "etzhayyim-kawase-pool"
    pkg.mkdir(parents=True)
    (pkg / "url_violator.py").write_text(
        "BASE_URL = 'https://moneygram.com/api/v1/send'\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(_SCRIPT), "--root", str(tmp_path)],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 1
    assert "G7 violation" in result.stderr
    assert "moneygram" in result.stderr.lower()
