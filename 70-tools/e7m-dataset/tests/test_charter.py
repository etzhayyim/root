"""charter.scan_sample — gate integration semantics.

The scanner module itself (kotodama.organism.sensors.charter_rider)
lives in the kotodama tree and is imported via three fallback paths:

  1. installed `kotodama` (production)
  2. ETZ_PYKOTODAMA_SRC env override
  3. monorepo auto-discovery via cwd ascent

We exercise (2) here for determinism.
"""

from __future__ import annotations

import sys
import textwrap
from pathlib import Path

import pytest

from e7m_dataset import charter


REPO_ROOT = Path(__file__).resolve().parents[3]
PYKOTODAMA_SRC = REPO_ROOT / "20-actors" / "kotodama" / "py" / "src"
CHARTER_RIDER_PRESENT = (
    PYKOTODAMA_SRC / "kotodama" / "organism" / "sensors" / "charter_rider.py"
).is_file()


def _drop_kotodama_imports():
    for k in list(sys.modules):
        if k == "kotodama" or k.startswith("kotodama."):
            del sys.modules[k]


def _drop_kotodama_from_path():
    for entry in list(sys.path):
        if entry.endswith("40-engine/kotoba/crates/kotoba-kotodama/py/src"):
            sys.path.remove(entry)


@pytest.fixture
def with_scanner(monkeypatch):
    """Force the scanner to be importable via ETZ_PYKOTODAMA_SRC."""
    if not CHARTER_RIDER_PRESENT:
        pytest.skip("kotodama charter_rider not present in this checkout")
    _drop_kotodama_imports()
    _drop_kotodama_from_path()
    monkeypatch.setenv("ETZ_PYKOTODAMA_SRC", str(PYKOTODAMA_SRC))
    monkeypatch.chdir(REPO_ROOT.parent)  # ensure auto-discover doesn't accidentally find it
    yield
    _drop_kotodama_imports()
    _drop_kotodama_from_path()


@pytest.fixture
def without_scanner(monkeypatch, tmp_path):
    """Make the scanner unimportable."""
    _drop_kotodama_imports()
    _drop_kotodama_from_path()
    monkeypatch.delenv("ETZ_PYKOTODAMA_SRC", raising=False)
    monkeypatch.chdir(tmp_path)  # cwd is outside monorepo → auto-discovery fails
    yield


def test_warn_only_when_scanner_unavailable(without_scanner, monkeypatch):
    monkeypatch.delenv(charter.STRICT_ENV, raising=False)
    r = charter.scan_sample([], kind="reference")
    assert r["passed"] is True
    assert "scanner-unavailable" in r["note"]


def test_strict_raises_when_scanner_unavailable(without_scanner, monkeypatch):
    monkeypatch.setenv(charter.STRICT_ENV, "1")
    with pytest.raises(ImportError):
        charter.scan_sample([], kind="reference")


def test_clean_content_passes(with_scanner, tmp_path):
    f = tmp_path / "ok.md"
    f.write_text("This dataset documents historical treaties on disarmament.\n", encoding="utf-8")
    r = charter.scan_sample([f], kind="reference")
    assert r["passed"] is True
    assert r["sampledRows"] == 1


def test_violation_raises(with_scanner, tmp_path):
    f = tmp_path / "bad.md"
    f.write_text(textwrap.dedent("""\
        Our product: a high-frequency trading bot using pump and dump
        strategies, with payday loan financing for retail users.
    """), encoding="utf-8")
    with pytest.raises(charter.CharterViolation) as exc:
        charter.scan_sample([f], kind="reference")
    assert "2b" in str(exc.value)
