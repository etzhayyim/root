#!/usr/bin/env python3
"""kawaraban — tests for the offline outlet normalizer membrane (ingest.py)."""
from __future__ import annotations
import json
import pathlib

from ingest import normalize_batch, normalize_record, live_allowed, IngestRefused

BATCH = pathlib.Path(__file__).resolve().parent.parent / "data" / "ingest" / "sample-batch.json"


def _records():
    return json.loads(BATCH.read_text(encoding="utf-8"))


def test_batch_accepts_clean_refuses_violations():
    ok, refused = normalize_batch(_records())
    assert len(ok) == 2, [a[":news.article/id"] for a in ok]
    assert len(refused) == 3, refused
    blob = " ".join(refused)
    assert "G4" in blob and "G1" in blob  # body/paywall (G4) + verdict (G1)


def test_refuses_full_body():
    try:
        normalize_record({"outlet": "o", "url": "u", "body": "the whole thing"})
        assert False, "expected G4 refusal"
    except IngestRefused as e:
        assert "G4" in str(e)


def test_refuses_paywall():
    try:
        normalize_record({"outlet": "o", "url": "u", "access": "paywall"})
        assert False, "expected G4 refusal"
    except IngestRefused as e:
        assert "G4" in str(e)


def test_refuses_verdict():
    try:
        normalize_record({"outlet": "o", "url": "u", "verdict": True})
        assert False, "expected G1 refusal"
    except IngestRefused as e:
        assert "G1" in str(e)


def test_requires_url():
    try:
        normalize_record({"outlet": "o", "headline": "h"})
        assert False, "expected G4/G5 url refusal"
    except IngestRefused as e:
        assert "url" in str(e).lower()


def test_excerpt_truncated_to_280():
    rec = normalize_record({"outlet": "o", "url": "u", "excerpt": "x" * 500})
    assert len(rec[":news.article/excerpt"]) == 280
    assert rec["_excerpt_truncated"] is True


def test_normalized_is_mirror_kind():
    rec = normalize_record({"outlet": "outlet.nhk", "url": "https://x", "headline": "h", "asOf": 5})
    assert rec[":news.article/kind"] == ":mirror"
    assert rec[":news.article/sourcing"] == ":representative"


def test_live_refused_at_r0():
    assert live_allowed() is False  # no operator gate env set


if __name__ == "__main__":
    import sys
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for t in tests:
        try:
            t()
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"FAIL {t.__name__}: {e}")
    print(f"ingest: {len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
