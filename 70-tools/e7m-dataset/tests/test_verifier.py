"""verifier — sha256 round-trip semantics + key parsing + report logic."""

from __future__ import annotations

import hashlib
import json

import pytest

from e7m_dataset import ipfs, verifier


def test_sha256_from_sha256e_key():
    sha = "0" * 64
    assert verifier._sha256_from_key(f"SHA256E-s1024--{sha}.bin") == sha
    assert verifier._sha256_from_key(f"SHA256E-s1024--{sha}") == sha


def test_sha256_from_non_sha256e_key():
    assert verifier._sha256_from_key("MD5E-s2048-S67108864-C1--abc.bin") is None


def test_verify_ok_path(tmp_path, monkeypatch):
    # Build a fake annex tree with one object.
    payload = b"hello dataset substrate"
    sha = hashlib.sha256(payload).hexdigest()
    key = f"SHA256E-s{len(payload)}--{sha}.bin"
    obj_dir = tmp_path / "ab" / "cd" / key
    obj_dir.mkdir(parents=True)
    obj_path = obj_dir / key
    obj_path.write_bytes(payload)

    map_doc = {
        "version": 1,
        "subdataset": "TestSub",
        "annexBackend": "SHA256E",
        "entries": [
            {"key": key, "ipfsCid": "bafkrei-test-cid", "leafName": key},
        ],
    }
    map_bytes = json.dumps(map_doc).encode("utf-8")

    def fake_cat(_api, cid):
        if cid == "bafkrei-map":
            return map_bytes
        if cid == "bafkrei-test-cid":
            return payload
        raise AssertionError(f"unexpected cid {cid!r}")

    monkeypatch.setattr(ipfs, "cat", fake_cat)
    report = verifier.verify(
        kubo_api="http://kubo:5001",
        subdataset="TestSub",
        map_cid="bafkrei-map",
        remote_root=tmp_path,
    )
    assert report.ok is True
    assert report.checked == 1
    assert report.ok_count == 1
    assert report.entries[0].expected_sha256 == sha


def test_verify_detects_mismatch(tmp_path, monkeypatch):
    real = b"truthy bytes"
    sha = hashlib.sha256(real).hexdigest()
    key = f"SHA256E-s{len(real)}--{sha}.bin"
    obj_dir = tmp_path / "ab" / "cd" / key
    obj_dir.mkdir(parents=True)
    (obj_dir / key).write_bytes(real)

    map_doc = {
        "entries": [{"key": key, "ipfsCid": "bafkrei-corrupt", "leafName": key}],
    }

    def fake_cat(_api, cid):
        if cid == "bafkrei-map":
            return json.dumps(map_doc).encode("utf-8")
        if cid == "bafkrei-corrupt":
            return b"tampered different bytes"
        raise AssertionError(cid)

    monkeypatch.setattr(ipfs, "cat", fake_cat)
    report = verifier.verify(
        kubo_api="http://kubo:5001",
        subdataset="TestSub",
        map_cid="bafkrei-map",
        remote_root=tmp_path,
    )
    assert report.ok is False
    assert report.fail_count == 1
    assert "sha256 mismatch" in report.entries[0].note


def test_verify_md5e_falls_back_to_size_check(tmp_path, monkeypatch):
    payload = b"smoke seed bytes"
    key = f"MD5E-s{len(payload)}-S67108864-C1--00112233445566778899aabbccddeeff.bin"
    obj_dir = tmp_path / "ab" / "cd" / key
    obj_dir.mkdir(parents=True)
    (obj_dir / key).write_bytes(payload)

    map_doc = {"entries": [{"key": key, "ipfsCid": "bafkrei-md5e", "leafName": key}]}

    def fake_cat(_api, cid):
        if cid == "bafkrei-map":
            return json.dumps(map_doc).encode("utf-8")
        if cid == "bafkrei-md5e":
            return payload
        raise AssertionError(cid)

    monkeypatch.setattr(ipfs, "cat", fake_cat)
    report = verifier.verify(
        kubo_api="http://kubo:5001",
        subdataset="TestSub",
        map_cid="bafkrei-map",
        remote_root=tmp_path,
    )
    assert report.ok is True  # size matches; sha256 fallback note recorded
    assert report.entries[0].expected_sha256 is None
    assert "non-SHA256E" in report.entries[0].note
