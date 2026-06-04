"""Tests for the entity mirror-actor timeline projector (ADR-2606042330 D4).

    python3 -m pytest 70-tools/scripts/entity-actors/test_project_timeline.py
    (or)  python3 70-tools/scripts/entity-actors/test_project_timeline.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from project_timeline import project, GateError, MIRROR_PREFIX  # noqa: E402


def test_projects_a_dry_run_post():
    p = project(
        actor_handle="corp-tw-tsmc",
        datom_tx_cid="bafyreitsmc1",
        as_of="2026-05-01T00:00:00Z",
        change_kind="filing",
        narrated_text="TSMC filed Q1 FY26 results: revenue up YoY.",
    )
    assert p.isMirror is True            # G1
    assert p.narrator == "murakumo"      # G6
    assert p.published is False          # G8
    assert p.asOf == "2026-05-01T00:00:00Z"
    assert p.text.startswith(MIRROR_PREFIX)  # G1 unspoofable framing
    rec = p.to_record()
    assert rec["$type"] == "com.etzhayyim.mirror.mirrorPost"


def test_publish_request_is_refused():
    try:
        project(
            actor_handle="gov-jp",
            datom_tx_cid="bafy1",
            as_of="2026-05-01T00:00:00Z",
            change_kind="procedure",
            narrated_text="updated window hours",
            request_publish=True,
        )
    except GateError as e:
        assert "gated" in str(e).lower()  # G8
    else:
        raise AssertionError("expected GateError on request_publish=True")


def test_person_or_unknown_namespace_is_refused():
    for bad in ["jun-kawasaki", "member-001", "watari", "noNamespace"]:
        try:
            project(
                actor_handle=bad,
                datom_tx_cid="bafy1",
                as_of="2026-05-01T00:00:00Z",
                change_kind="x",
                narrated_text="y",
            )
        except GateError:
            pass
        else:
            raise AssertionError(f"expected GateError for non-entity handle {bad!r}")


def test_missing_tx_cid_is_refused():
    try:
        project(
            actor_handle="cable-jupiter",
            datom_tx_cid="",
            as_of="2026-05-01T00:00:00Z",
            change_kind="fault",
            narrated_text="shunt fault reported",
        )
    except GateError as e:
        assert "audit" in str(e).lower() or "datom" in str(e).lower()
    else:
        raise AssertionError("expected GateError on empty datomTxCid")


def test_prefix_not_doubled():
    p = project(
        actor_handle="cable-jupiter",
        datom_tx_cid="bafy1",
        as_of="2026-05-01T00:00:00Z",
        change_kind="fault",
        narrated_text=f"{MIRROR_PREFIX} already-framed",
    )
    assert p.text.count(MIRROR_PREFIX) == 1


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"{len(fns)}/{len(fns)} green")
