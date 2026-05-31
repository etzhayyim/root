"""Shared test fixtures.

Anchors the canonical ``fleet.toml`` path and gates the live-fleet smoke
tests behind ``KOTOBA_MURAKUMO_LIVE_FLEET=1``.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest


def repo_root() -> Path:
    # tests/ → kotoba_murakumo/ → py/ → kotoba/ → 40-engine/ → repo root
    return Path(__file__).resolve().parents[3]


@pytest.fixture(scope="session")
def fleet_path() -> Path:
    return repo_root() / "50-infra/murakumo/fleet.toml"


@pytest.fixture(autouse=True)
def _ndjson_in_tmp(tmp_path, monkeypatch) -> Path:
    """Redirect invocation NDJSON to tmp so tests don't pollute ~/."""
    p = tmp_path / "invocations.ndjson"
    monkeypatch.setenv("KOTOBA_MURAKUMO_LOG", str(p))
    # The ndjson module reads the env var at import time; patch the
    # already-evaluated default too so the redirect actually takes effect.
    from kotoba_murakumo._internal import ndjson as nd
    monkeypatch.setattr(nd, "_DEFAULT_PATH", p)
    return p


@pytest.fixture(autouse=True)
def _charter_advisory_by_default(monkeypatch) -> None:
    """Most tests assume advisory mode; opt-in to enforce via the env var."""
    monkeypatch.delenv("KOTOBA_MURAKUMO_CHARTER_ENFORCE", raising=False)


def pytest_collection_modifyitems(config, items) -> None:
    """Skip ``live_fleet`` tests unless ``KOTOBA_MURAKUMO_LIVE_FLEET=1``."""
    if os.environ.get("KOTOBA_MURAKUMO_LIVE_FLEET") in {"1", "true", "yes"}:
        return
    skip_marker = pytest.mark.skip(
        reason="set KOTOBA_MURAKUMO_LIVE_FLEET=1 to run live-fleet smoke",
    )
    for item in items:
        if "live_fleet" in item.keywords:
            item.add_marker(skip_marker)
