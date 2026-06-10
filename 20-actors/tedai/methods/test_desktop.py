"""Tests for the tedai DesktopOp parser/planner (methods/desktop.py) — ADR-2606101400."""

from __future__ import annotations

import pytest

from desktop import (
    MUTATE_AWAIT_SIG,
    MUTATE_AWAIT_SIG_OUTWARD,
    MUTATE_READ_ALLOWED,
    ROUTE_KARAKURI,
    SAFETY_CREATE,
    SAFETY_DELETE,
    SAFETY_OUTWARD,
    SAFETY_READ,
    SAFETY_UPDATE,
    STANCE_OK,
    STANCE_REFUSED,
    T2_ENGINE,
    TIER_T1,
    TIER_T2,
    TIER_T3,
    UNKNOWN_APP,
    classify_safety,
    parse_command,
    plan,
    resolve_app,
    select_tier,
    stance_gate,
    t2_stance,
)


# ── parsing (G8: never guesses the shape) ──────────────────────────────────────────────

def test_parse_basic():
    assert parse_command("tedai finder files.list") == ("finder", "files", "list", {})


def test_parse_without_prefix_and_flags():
    app, noun, verb, args = parse_command("mail message.send --to friend --draft")
    assert (app, noun, verb) == ("mail", "message", "send")
    assert args == {"to": "friend", "draft": True}


@pytest.mark.parametrize("bad", ["", "tedai", "tedai finder", "tedai finder fileslist",
                                 "tedai finder .list", "tedai finder files."])
def test_parse_malformed_raises(bad):
    with pytest.raises(ValueError):
        parse_command(bad)


# ── safety classification incl. the OS-layer :outward class (G5) ───────────────────────

@pytest.mark.parametrize("verb,safety", [
    ("list", SAFETY_READ), ("read", SAFETY_READ), ("export", SAFETY_READ),
    ("create", SAFETY_CREATE), ("save", SAFETY_CREATE),
    ("move", SAFETY_UPDATE), ("rename", SAFETY_UPDATE), ("fill", SAFETY_UPDATE),
    ("delete", SAFETY_DELETE), ("trash", SAFETY_DELETE),
    ("send", SAFETY_OUTWARD), ("pay", SAFETY_OUTWARD), ("upload", SAFETY_OUTWARD),
])
def test_classify_safety(verb, safety):
    assert classify_safety(verb) == safety


def test_unknown_verb_is_conservatively_mutating():
    assert classify_safety("frobnicate") == SAFETY_UPDATE


# ── tier selection (G2: T1 scripting API first; default-deny synthetic input) ──────────

def test_t1_app_selects_scripting_api():
    assert select_tier(resolve_app("finder")) == TIER_T1


def test_no_t1_permitted_input_selects_vision_pointer():
    assert select_tier(resolve_app("legacy-win-app")) == TIER_T2


def test_prohibited_input_falls_to_file_level():
    assert select_tier(resolve_app("anticheat-game")) == TIER_T3
    assert select_tier(resolve_app("banking-app")) == TIER_T3


def test_missing_t2_stance_defaults_to_prohibited():
    assert t2_stance({}) == "prohibited"
    assert select_tier({"t1": False}) == TIER_T3


# ── stance gate (G2: T2 refused by construction on a prohibited app) ───────────────────

def test_stance_gate_refuses_t2_on_prohibited_app():
    rec = resolve_app("anticheat-game")
    assert stance_gate(rec, TIER_T2) == STANCE_REFUSED


def test_stance_gate_ok_on_permitted_t2():
    rec = resolve_app("legacy-win-app")
    assert stance_gate(rec, TIER_T2) == STANCE_OK


def test_forced_t2_on_anticheat_game_is_refused_in_plan():
    op = plan("tedai anticheat-game inventory.list", prefer_tier=TIER_T2)
    assert op.stance_gate == STANCE_REFUSED
    assert op.t2_engine == ""
    assert "G2" in op.note


# ── end-to-end plans (G5/G6 invariants) ────────────────────────────────────────────────

def test_read_plan_is_dry_run_read_allowed():
    op = plan("tedai finder files.list")
    assert op.dry_run is True                      # G6: R0 never actuates
    assert op.adapter_tier == TIER_T1
    assert op.mutate_gate == MUTATE_READ_ALLOWED
    assert not op.destructive


def test_mutating_plan_awaits_member_sig():
    op = plan("tedai finder files.rename --from a --to b")
    assert op.mutate_gate == MUTATE_AWAIT_SIG       # G5


def test_destructive_delete_is_flagged():
    op = plan("tedai finder files.trash --path junk")
    assert op.safety == SAFETY_DELETE
    assert op.destructive is True


def test_outward_op_carries_outward_gate():
    op = plan("tedai mail message.send --to friend")
    assert op.safety == SAFETY_OUTWARD
    assert op.mutate_gate == MUTATE_AWAIT_SIG_OUTWARD   # G5: effect leaves the device


def test_permitted_t2_plan_selects_on_device_vision_engine():
    op = plan("tedai legacy-win-app records.list")
    assert op.adapter_tier == TIER_T2
    assert op.t2_engine == T2_ENGINE                # G4: on-device vision only


def test_t1_plan_has_no_t2_engine():
    op = plan("tedai excel sheet.update --cell A1")
    assert op.adapter_tier == TIER_T1
    assert op.t2_engine == ""


# ── honest degradation + karakuri route (G8 / N7) ──────────────────────────────────────

def test_unknown_app_degrades_honestly():
    op = plan("tedai mystery-app thing.list")
    assert op.app_known is False
    assert op.adapter_tier == ""
    assert op.note == UNKNOWN_APP


@pytest.mark.parametrize("browser", ["chrome", "safari", "firefox"])
def test_browser_apps_route_to_karakuri(browser):
    op = plan(f"tedai {browser} tabs.list")
    assert op.route == "karakuri"                   # N7: one owner per surface
    assert op.adapter_tier == ""
    assert op.note == ROUTE_KARAKURI


def test_unknown_prefer_tier_raises():
    with pytest.raises(ValueError):
        plan("tedai finder files.list", prefer_tier="t9-magic")
