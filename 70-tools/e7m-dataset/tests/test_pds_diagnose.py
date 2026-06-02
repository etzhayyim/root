"""Tests for the PDS resolver operator-diagnostic CLI."""

from __future__ import annotations

import json

import httpx
import pytest


from e7m_dataset import pds_diagnose as diag


_AT_URI = (
    "at://did:web:dataset-pinner.etzhayyim.com/"
    "com.etzhayyim.substrate.datasetPin/3kpqab"
)


# ─── check ──────────────────────────────────────────────────────────


def test_check_with_skip_network(monkeypatch, capsys):
    monkeypatch.delenv("ETZ_E7M_PDS_URL", raising=False)
    rc = diag.main(["check", "--skip-network"])
    assert rc == 0   # no critical missing; --skip-network bypasses reach probe
    captured = capsys.readouterr()
    assert "httpx" in captured.out
    assert "(skipped)" in captured.out


def test_check_json_with_skip_network(monkeypatch, capsys):
    monkeypatch.delenv("ETZ_E7M_PDS_URL", raising=False)
    rc = diag.main(["check", "--skip-network", "--json"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["deps"]["httpx"]["available"] is True
    assert payload["reachable"] is None


# ─── parse ──────────────────────────────────────────────────────────


def test_parse_canonical_at_uri(capsys):
    rc = diag.main(["parse", _AT_URI])
    assert rc == 0
    captured = capsys.readouterr()
    assert "repo:       did:web:dataset-pinner.etzhayyim.com" in captured.out
    assert "collection: com.etzhayyim.substrate.datasetPin" in captured.out
    assert "rkey:       3kpqab" in captured.out


def test_parse_json_output(capsys):
    rc = diag.main(["parse", _AT_URI, "--json"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["repo"] == "did:web:dataset-pinner.etzhayyim.com"
    assert payload["collection"] == "com.etzhayyim.substrate.datasetPin"
    assert payload["rkey"] == "3kpqab"


def test_parse_malformed_returns_2(capsys):
    rc = diag.main(["parse", "https://not-an-at-uri"])
    assert rc == 2
    captured = capsys.readouterr()
    assert "bad at-uri shape" in captured.err


def test_parse_wrong_collection_warns(capsys):
    """A valid at-uri with non-datasetPin collection parses OK but warns."""
    rc = diag.main(["parse", "at://repo/app.bsky.feed.post/abc"])
    assert rc == 0
    captured = capsys.readouterr()
    assert "collection differs from expected" in captured.out


# ─── resolve (uses real pds.resolve_datasetpin; we monkey-patch httpx) ──


def test_resolve_happy_path(monkeypatch, capsys):
    """Monkey-patch httpx.Client to return a synthetic record."""
    from e7m_dataset import pds as pds_mod

    def fake_resolve_datasetpin(at_uri, **kwargs):
        return {
            "cid": "bafyactualpin12345",
            "name": "test-dataset",
            "revision": "sha256:abc",
            "sizeBytes": 12345,
        }
    monkeypatch.setattr(pds_mod, "resolve_datasetpin", fake_resolve_datasetpin)
    # Re-import to pick up the patch.
    monkeypatch.setattr(diag, "_cmd_resolve", diag._cmd_resolve)

    rc = diag.main(["resolve", _AT_URI])
    assert rc == 0
    captured = capsys.readouterr()
    assert "cid:        bafyactualpin12345" in captured.out
    assert "revision:   sha256:abc" in captured.out


def test_resolve_json(monkeypatch, capsys):
    from e7m_dataset import pds as pds_mod

    def fake(at_uri, **kwargs):
        return {"cid": "bafy123", "name": "x"}
    monkeypatch.setattr(pds_mod, "resolve_datasetpin", fake)

    rc = diag.main(["resolve", _AT_URI, "--json"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["cid"] == "bafy123"


def test_resolve_pds_error_returns_1(monkeypatch, capsys):
    from e7m_dataset import pds as pds_mod

    def fake(at_uri, **kwargs):
        raise pds_mod.PdsError("getRecord failed: 404")
    monkeypatch.setattr(pds_mod, "resolve_datasetpin", fake)

    rc = diag.main(["resolve", _AT_URI])
    assert rc == 1
    captured = capsys.readouterr()
    assert "getRecord failed: 404" in captured.err
