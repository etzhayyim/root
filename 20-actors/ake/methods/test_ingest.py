#!/usr/bin/env python3
"""Tests for ingest.py — genesis revision history over the REAL actor-profile SSoT.

This is the membrane-over-real-data proof (mitooshi-bridge pattern): ake parses the actual repo
SSoT the DID-web Worker publishes from, and a member edit appends on top without losing the genesis.
"""
from __future__ import annotations

from ingest import GENESIS_AS_OF_BASE, genesis_revisions
from revision import append_revision, as_of, current, history_of


def test_genesis_covers_every_seeded_actor():
    res = genesis_revisions()
    assert res["records"] >= 19                      # the real seed has ≥19 actor profiles
    # every actor got at least a description genesis revision
    for h in res["actors"]:
        assert history_of(res["history"], h, "description"), f"no genesis for {h}"


def test_known_actors_present_with_authoritative_genesis():
    res = genesis_revisions()
    # incl. mitooshi + noroshi — added to the profile seed this iteration to close the
    # INFRA_ACTORS↔profile-seed drift that ake's ingest bridge surfaced (drift-locked here)
    for h in ("ake", "kamado", "hotaru", "ooyake", "kabuto", "mitooshi", "noroshi"):
        cur = current(res["history"], h, "description")
        assert cur is not None, f"{h} missing"
        assert cur[":revision/sourcing"] == ":authoritative"
        assert cur[":revision/value"]                    # non-empty description


def test_genesis_is_append_only_member_edit_layers_on_top():
    res = genesis_revisions()
    h = res["history"]
    base_n = len(history_of(h, "ake", "description"))
    genesis_at = current(h, "ake", "description")[":revision/as-of"]

    # a later member edit (representative) appends — genesis is NOT overwritten
    member_edit = {
        ":edit/target-entity": "ake", ":edit/target-attr": ":actor/description",
        ":edit/proposed-value": "(member-proposed tweak)", ":edit/sourcing": ":representative",
        ":edit/author": "did:web:etzhayyim.com:member:abel", ":edit/op": ":assert",
    }
    h2 = append_revision(h, member_edit, genesis_at + 1000)
    assert len(history_of(h2, "ake", "description")) == base_n + 1     # grew by one
    assert current(h2, "ake", "description")[":revision/value"] == "(member-proposed tweak)"
    # time-travel: before the member edit, the genesis value is still current
    assert as_of(h2, "ake", "description", genesis_at)[":revision/sourcing"] == ":authoritative"


def test_report_renders():
    from ingest import _report
    md = _report(genesis_revisions())
    assert "genesis revision history" in md and "| ake |" in md


def test_as_of_base_is_deterministic():
    a = genesis_revisions(as_of_base=GENESIS_AS_OF_BASE)
    b = genesis_revisions(as_of_base=GENESIS_AS_OF_BASE)
    assert [r[":revision/as-of"] for r in a["history"]] == [r[":revision/as-of"] for r in b["history"]]


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
    print(f"{len(fns) - failed}/{len(fns)} passed in test_ingest.py")
    sys.exit(1 if failed else 0)
