"""State-machine tests for the karakuri export_roundtrip cell (R0). .solve() is NOT called."""

import pytest

from export_roundtrip.cell import ExportRoundtripCell
from export_roundtrip.state_machine import (
    ExportPhase,
    transition_export_plan,
    transition_format_select,
    transition_owner_check,
)


def _export(service="google", fmt="kotoba-edn", owner="member"):
    s = transition_owner_check({"service": service, "fmt": fmt, "owner": owner})
    if s["next_node"] == "end":
        return s
    s = transition_format_select(s)
    if s["next_node"] == "end":
        return s
    s = transition_export_plan(s)
    return s


def test_member_export_is_encrypted_and_roundtrips():
    e = _export()["cell_state"]["payload"]["export"]
    assert e["owner"] == "member"            # G9
    assert e["encrypted"] is True            # G9
    assert e["secretRef"].startswith("encref:")
    assert e["dryRun"] is True               # G6
    assert e["roundtripOk"] is True


def test_non_member_owner_refused():
    s = _export(owner="someone-else")
    cs = s["cell_state"]
    assert cs["phase"] == ExportPhase.REFUSED.value
    assert cs["payload"]["outcome"] == "g9-non-member-owner-refused"
    assert "export" not in cs["payload"]


def test_unknown_format_refused():
    s = _export(fmt="pdf")
    cs = s["cell_state"]
    assert cs["phase"] == ExportPhase.REFUSED.value
    assert cs["payload"]["outcome"].startswith("unknown-format")


def test_solve_raises_at_r0():
    with pytest.raises(RuntimeError, match="R0 scaffold"):
        ExportRoundtripCell().solve({})
