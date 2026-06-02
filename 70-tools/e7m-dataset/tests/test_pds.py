"""pds.build_record + emit dry-run shape."""

from __future__ import annotations

import json

import pytest

from e7m_dataset import pds


_BASE_KWARGS = dict(
    name="HF:owner/repo",
    revision="git:deadbeef",
    kind="reference",
    cid="bafybeigeput7lc7bthy2zpfxglamzt66nqpxswofgqkogdq6l6q5c2fr7a",
    size_bytes=12345,
    sha256=None,
    providers=["kubo"],
    pinned_at="2026-05-24T00:00:00Z",
    charter_rider_scan={"passed": True, "at": "2026-05-24T00:00:00Z"},
)


def test_build_record_required_only():
    r = pds.build_record(**_BASE_KWARGS)
    assert r["$type"] == "com.etzhayyim.substrate.datasetPin"
    for k in ("name", "revision", "kind", "cid", "sizeBytes", "providers", "pinnedAt", "charterRiderScan"):
        assert k in r
    # optional keys should not appear
    for k in ("sha256", "assignedNodes", "source", "license", "manifestRowRef"):
        assert k not in r


def test_build_record_all_optionals():
    kwargs = {k: v for k, v in _BASE_KWARGS.items() if k != "sha256"}
    r = pds.build_record(
        **kwargs,
        sha256="abc123",
        assigned_nodes=["did:web:x.example"],
        source={"type": "hf-dataset", "url": "https://huggingface.co/..."},
        license="Apache-2.0",
        manifest_row_ref="HF/owner-repo",
    )
    assert r["sha256"] == "abc123"
    assert r["assignedNodes"] == ["did:web:x.example"]
    assert r["source"]["type"] == "hf-dataset"
    assert r["license"] == "Apache-2.0"
    assert r["manifestRowRef"] == "HF/owner-repo"


def test_emit_dry_run_prints(capsys):
    r = pds.build_record(**_BASE_KWARGS)
    result = pds.emit(r, dry_run=True)
    assert result == {"dryRun": True}
    err = capsys.readouterr().err
    assert "DRY RUN" in err
    assert "com.etzhayyim.substrate.datasetPin" in err
    # The record body should be valid JSON inside the diagnostic block.
    body_start = err.find("{")
    assert body_start > 0
    json.loads(err[body_start:])


def test_emit_live_requires_credentials(monkeypatch):
    monkeypatch.delenv("ETZ_E7M_PDS_SESSION", raising=False)
    monkeypatch.delenv("ETZ_E7M_PDS_AUTH", raising=False)
    r = pds.build_record(**_BASE_KWARGS)
    with pytest.raises(pds.PdsError):
        pds.emit(r, dry_run=False)
