"""Tests for the e7m_dataset.pii canonical wrapper.

Mirrors test_charter.py — verifies direct-load works, strict mode
raises when unavailable, warn-only path returns the input unchanged.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from e7m_dataset import pii


REPO_ROOT = Path(__file__).resolve().parents[3]
PYKOTODAMA_SRC = REPO_ROOT / "20-actors" / "kotodama" / "py" / "src"
PII_FILTER_PRESENT = (
    PYKOTODAMA_SRC / "kotodama" / "organism" / "sensors" / "pii_filter.py"
).is_file()


def _drop_pii_module_cache():
    """Reset the cached load between tests so each test exercises the loader."""
    pii._LOADED_MODULES.clear()
    for k in list(sys.modules):
        if k.startswith("_e7m_dataset_pii_direct_") or k == "kotodama" or k.startswith("kotodama."):
            del sys.modules[k]


def _drop_kotodama_from_path():
    for entry in list(sys.path):
        if entry.endswith("40-engine/kotoba/crates/kotoba-kotodama/py/src"):
            sys.path.remove(entry)


@pytest.fixture
def with_pii(monkeypatch):
    """Force the redactor to be importable via repo-root walk-up."""
    if not PII_FILTER_PRESENT:
        pytest.skip("pii_filter.py not present in this checkout")
    _drop_pii_module_cache()
    _drop_kotodama_from_path()
    monkeypatch.chdir(REPO_ROOT)
    yield
    _drop_pii_module_cache()
    _drop_kotodama_from_path()


@pytest.fixture
def without_pii(monkeypatch, tmp_path):
    """Make the redactor unimportable by chdir-ing outside the monorepo."""
    _drop_pii_module_cache()
    _drop_kotodama_from_path()
    monkeypatch.delenv(pii.SRC_OVERRIDE_ENV, raising=False)
    monkeypatch.chdir(tmp_path)
    yield
    _drop_pii_module_cache()


def test_warn_only_when_unavailable(without_pii, monkeypatch):
    monkeypatch.delenv(pii.STRICT_ENV, raising=False)
    payload = {"email": "alice@example.com"}
    redacted, stats = pii.redact_payload(payload)
    assert redacted == payload  # no-op
    assert stats.total == 0


def test_strict_raises_when_unavailable(without_pii, monkeypatch):
    monkeypatch.setenv(pii.STRICT_ENV, "1")
    with pytest.raises(pii.PiiFilterUnavailable):
        pii.redact_payload({"email": "alice@example.com"})


def test_redact_payload_works(with_pii):
    payload = {
        "url": "https://carol@example.com/page",
        "type": "TXT",
        "country": "JP",
    }
    redacted, stats = pii.redact_payload(payload, fields=["url"])
    assert "carol@example.com" not in redacted["url"]
    assert redacted["country"] == "JP"
    assert stats.total >= 1


def test_redact_text_works(with_pii):
    redacted, stats = pii.redact_text("ops contact bob@example.com pls")
    assert "bob@example.com" not in redacted
    assert "[redacted-pii]" in redacted
    assert stats.total >= 1


def test_redact_payload_auto_detect_strings(with_pii):
    """fields=None ⇒ auto-detect every string-valued column."""
    payload = {
        "email": "dave@example.com",
        "phone": "+1-415-555-2671",
        "count": 42,
    }
    redacted, stats = pii.redact_payload(payload)
    assert "dave@example.com" not in redacted["email"]
    assert "+1-415-555-2671" not in redacted["phone"]
    assert redacted["count"] == 42  # untouched
