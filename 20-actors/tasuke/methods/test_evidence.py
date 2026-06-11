#!/usr/bin/env python3
"""Tests for 助 (tasuke) evidence preservation — G6 PII-by-reference + chain-of-custody."""
from __future__ import annotations

from evidence import custody_intact, index, preserve, sha256_hex


def _item(**over):
    base = {":evidence/id": "e1", ":evidence/case": "c1", ":evidence/kind": ":screenshot",
            ":evidence/envelope-ref": "ipfs://bafyX", ":evidence/bytes": "abc",
            ":evidence/captured-at": 100}
    base.update(over)
    return base


# ── G6 plaintext PII is unrepresentable ──────────────────────────────────────
def test_plaintext_pii_field_refused():
    for f in (":evidence/plaintext", ":evidence/raw", ":evidence/pii"):
        try:
            preserve({**_item(), f: "secret data"})
            assert False, f"{f} should be refused (G6)"
        except ValueError as e:
            assert "G6" in str(e)


def test_envelope_ref_required():
    try:
        preserve(_item(**{":evidence/envelope-ref": ""}))
        assert False
    except ValueError as e:
        assert "envelope-ref" in str(e)


# ── chain-of-custody hash ────────────────────────────────────────────────────
def test_preserve_hashes_bytes():
    r = preserve(_item())
    assert r[":evidence/sha256"] == sha256_hex(b"abc")
    assert ":evidence/bytes" not in r  # raw bytes discarded, never stored


def test_precomputed_hash_kept():
    r = preserve(_item(**{":evidence/sha256": "deadbeef", ":evidence/bytes": None}))
    assert r[":evidence/sha256"] == "deadbeef"


def test_unknown_kind_refused():
    try:
        preserve(_item(**{":evidence/kind": ":telepathy"}))
        assert False
    except ValueError as e:
        assert "unknown evidence kind" in str(e)


def test_index_sorts_by_capture_time():
    rows = index([_item(**{":evidence/id": "b", ":evidence/captured-at": 200}),
                  _item(**{":evidence/id": "a", ":evidence/captured-at": 100})])
    assert [r[":evidence/id"] for r in rows] == ["a", "b"]


def test_custody_intact_detects_tamper():
    r = preserve(_item())
    assert custody_intact(r, b"abc") is True
    assert custody_intact(r, b"tampered") is False


if __name__ == "__main__":
    import sys
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in fns:
        try:
            fn()
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"FAIL {fn.__name__}: {e}")
    print(f"{len(fns) - failed}/{len(fns)} passed in test_evidence.py")
    sys.exit(1 if failed else 0)
