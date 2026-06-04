"""Tests for the karakuri ServiceOp parser/planner (ADR-2606039200). Offline only (G6)."""

import pytest

from command import (
    MUTATE_AWAIT_SIG,
    MUTATE_READ_ALLOWED,
    SAFETY_DELETE,
    SAFETY_READ,
    SAFETY_UPDATE,
    TIER_T1,
    TIER_T2,
    TIER_T3,
    TOS_OK,
    TOS_REFUSED,
    UNKNOWN_SERVICE,
    classify_safety,
    is_destructive,
    mutate_gate,
    parse_command,
    plan,
    resolve_service,
    select_tier,
)


def test_parse_basic_command():
    service, noun, verb, args = parse_command("karakuri squarespace pages.list")
    assert (service, noun, verb) == ("squarespace", "pages", "list")
    assert args == {}


def test_parse_strips_optional_leading_karakuri():
    s1, *_ = parse_command("squarespace pages.list")
    s2, *_ = parse_command("karakuri squarespace pages.list")
    assert s1 == s2 == "squarespace"


def test_parse_flags():
    _, _, _, args = parse_command("karakuri notion database.query --filter status --limit 50")
    assert args == {"filter": "status", "limit": "50"}


def test_parse_boolean_flag():
    _, _, _, args = parse_command("karakuri github repos.list --archived")
    assert args == {"archived": True}


@pytest.mark.parametrize("line", ["", "squarespace", "karakuri", "notion pageslist", "notion ."])
def test_parse_malformed_raises(line):
    with pytest.raises(ValueError):
        parse_command(line)


def test_classify_safety_reads_and_mutations():
    assert classify_safety("list") == SAFETY_READ
    assert classify_safety("get") == SAFETY_READ
    assert classify_safety("export") == SAFETY_READ
    assert classify_safety("update") == SAFETY_UPDATE
    assert classify_safety("delete") == SAFETY_DELETE


def test_unknown_verb_is_conservatively_mutating():
    # G5: never assume an unknown verb is safe.
    assert classify_safety("frobnicate") == SAFETY_UPDATE


def test_is_destructive_only_delete():
    assert is_destructive(SAFETY_DELETE) is True
    assert is_destructive(SAFETY_READ) is False
    assert is_destructive(SAFETY_UPDATE) is False


def test_select_tier_prefers_official_api():
    assert select_tier(resolve_service("squarespace")) == TIER_T1
    assert select_tier(resolve_service("notion")) == TIER_T1


def test_select_tier_headless_when_no_api_but_tos_allows():
    assert select_tier(resolve_service("legacy-portal")) == TIER_T2


def test_select_tier_export_when_automation_prohibited():
    assert select_tier(resolve_service("noauto-saas")) == TIER_T3


def test_mutate_gate_read_allowed_mutate_awaits_sig():
    assert mutate_gate(SAFETY_READ) == MUTATE_READ_ALLOWED
    assert mutate_gate(SAFETY_UPDATE) == MUTATE_AWAIT_SIG
    assert mutate_gate(SAFETY_DELETE) == MUTATE_AWAIT_SIG


def test_plan_read_op_is_allowed_dry_run_t1():
    op = plan("karakuri squarespace pages.list")
    assert op.service_known is True
    assert op.adapter_tier == TIER_T1
    assert op.safety == SAFETY_READ
    assert op.mutate_gate == MUTATE_READ_ALLOWED
    assert op.tos_gate == TOS_OK
    assert op.dry_run is True            # G6 — never executes at R0


def test_plan_mutate_op_awaits_member_sig():
    op = plan("karakuri notion database.update --title Hello")
    assert op.safety == SAFETY_UPDATE
    assert op.mutate_gate == MUTATE_AWAIT_SIG   # G5
    assert op.dry_run is True


def test_plan_delete_is_destructive_and_gated():
    op = plan("karakuri shopify products.delete --id 42")
    assert op.safety == SAFETY_DELETE
    assert op.destructive is True               # G5 — explicit member confirm
    assert op.mutate_gate == MUTATE_AWAIT_SIG


def test_g2_refuses_headless_on_automation_prohibited_service():
    # Forcing the T2 headless adapter on a ToS-automation-prohibited service is refused (G2).
    op = plan("karakuri noauto-saas records.list", prefer_tier=TIER_T2)
    assert op.tos_gate == TOS_REFUSED
    assert "G2" in op.note


def test_g8_unknown_service_degrades_honestly():
    op = plan("karakuri totally-made-up-service things.list")
    assert op.service_known is False
    assert op.note == UNKNOWN_SERVICE
    assert op.adapter_tier == ""               # no guess
