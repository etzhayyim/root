#!/usr/bin/env python3
"""Tests for ingest.py — genesis revision history over the actor-profile SSoT.

HERMETIC by design: the mechanism is asserted against a committed FIXTURE
(20-actors/ake/data/sample-profile-seed.kotoba.edn) with exact, known counts, so ake's suite is
green in ANY checkout — independent of whether the shared repo seed has yet been
(coordinated-)committed with ake's record. A separate SOFT test runs the bridge over the REAL repo
SSoT and validates the membrane-over-real-data property only when ake is actually registered there
(it never fails the suite if the shared seed is uncommitted).
"""
from __future__ import annotations

import pathlib

from ingest import GENESIS_AS_OF_BASE, genesis_revisions
from revision import append_revision, as_of, current, history_of

_FIXTURE = pathlib.Path(__file__).resolve().parents[1] / "data" / "sample-profile-seed.kotoba.edn"


# ── hermetic: exact behaviour on the committed fixture (3 records / 7 revisions) ──
def test_fixture_record_and_revision_counts_are_exact():
    res = genesis_revisions(_FIXTURE)
    assert res["records"] == 3
    assert len(res["history"]) == 7      # ake 3 + sample-corp 3 + sample-svc 1


def test_fixture_covers_every_record_with_a_description_genesis():
    res = genesis_revisions(_FIXTURE)
    for h in ("ake", "sample-corp", "sample-svc"):
        assert history_of(res["history"], h, "description"), f"no genesis for {h}"


def test_fixture_ake_genesis_is_authoritative_with_value():
    res = genesis_revisions(_FIXTURE)
    cur = current(res["history"], "ake", "description")
    assert cur is not None and cur[":revision/sourcing"] == ":authoritative"
    assert "community-edit membrane" in cur[":revision/value"]


def test_fixture_description_only_record_yields_one_revision():
    res = genesis_revisions(_FIXTURE)
    # sample-svc has no display-name fields → exactly one (description) genesis revision
    assert len(history_of(res["history"], "sample-svc", "description")) == 1
    assert current(res["history"], "sample-svc", "display-name-ja") is None


def test_genesis_is_append_only_member_edit_layers_on_top():
    res = genesis_revisions(_FIXTURE)
    h = res["history"]
    base_n = len(history_of(h, "ake", "description"))
    genesis_at = current(h, "ake", "description")[":revision/as-of"]
    member_edit = {
        ":edit/target-entity": "ake", ":edit/target-attr": ":actor/description",
        ":edit/proposed-value": "(member-proposed tweak)", ":edit/sourcing": ":representative",
        ":edit/author": "did:web:etzhayyim.com:member:abel", ":edit/op": ":assert",
    }
    h2 = append_revision(h, member_edit, genesis_at + 1000)
    assert len(history_of(h2, "ake", "description")) == base_n + 1          # grew by one
    assert current(h2, "ake", "description")[":revision/value"] == "(member-proposed tweak)"
    # time-travel: before the member edit, the authoritative genesis is still current
    assert as_of(h2, "ake", "description", genesis_at)[":revision/sourcing"] == ":authoritative"


def test_as_of_base_is_deterministic():
    a = genesis_revisions(_FIXTURE, as_of_base=GENESIS_AS_OF_BASE)
    b = genesis_revisions(_FIXTURE, as_of_base=GENESIS_AS_OF_BASE)
    assert [r[":revision/as-of"] for r in a["history"]] == [r[":revision/as-of"] for r in b["history"]]


def test_report_renders_from_fixture():
    from ingest import _report
    md = _report(genesis_revisions(_FIXTURE))
    assert "genesis revision history" in md and "| ake |" in md


# ── soft: membrane-over-REAL-data, validated only when ake is registered in the shared seed ──
def test_real_repo_seed_integration_when_registered():
    res = genesis_revisions()        # default = the REAL 00-contracts/.../actor-profile-seed
    if "ake" not in res["actors"]:
        # ake's profile record is committed to the shared seed by coordination, separately from
        # ake's own commits — its absence here is not an ake-suite failure (soft pass).
        return
    assert res["records"] >= 19      # the real seed registers the full actor fleet
    cur = current(res["history"], "ake", "description")
    assert cur is not None and cur[":revision/sourcing"] == ":authoritative"


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
