"""Tests for the karakuri NL→ServiceOp planner (ADR-2606039200, G4). Offline only."""

import pytest

from nl_plan import (
    INFERENCE_MURAKUMO,
    LiveLLMRefused,
    charter_scan,
    heuristic_parse,
    plan_from_brief,
)


def test_heuristic_parses_service_and_verb():
    assert heuristic_parse("list all my gmail messages") == "google messages.list"


def test_heuristic_synonym_maps_to_canonical_service():
    assert heuristic_parse("download my drive files") == "google files.export"


def test_heuristic_facebook_and_delete_verb():
    cmd = heuristic_parse("delete a post on facebook")
    assert cmd.startswith("facebook ") and cmd.endswith(".delete")


def test_heuristic_unknown_service_degrades_to_none():
    assert heuristic_parse("list all my hooli widgets") is None     # G8 — never guesses a service


def test_heuristic_no_verb_degrades():
    assert heuristic_parse("my gmail") is None


def test_plan_from_brief_read_op_is_t1_for_google():
    cp = plan_from_brief("show my gmail messages")
    assert len(cp.ops) == 1
    op = cp.ops[0]
    assert (op.service, op.noun, op.verb) == ("google", "messages", "list")
    assert op.adapter_tier == "t1-official-api"          # G2 — API, not browser
    assert cp.inference == INFERENCE_MURAKUMO            # G4
    assert cp.dry_run is True                            # G6


def test_plan_from_brief_mutate_marks_awaiting_sig():
    cp = plan_from_brief("delete a post on facebook")
    assert cp.ops[0].mutate_gate == "awaiting-member-sig"  # G5


def test_charter_scan_flags_prohibited_brief():
    clean, hits = charter_scan("set up an adsense affiliate banner")
    assert clean is False and hits


def test_plan_refuses_charter_dirty_brief():
    cp = plan_from_brief("list my gmail and add a casino gambling widget")
    assert cp.charter_clean is False
    assert cp.ops == []                                  # N6 — nothing planned for a dirty brief


def test_live_llm_refused_without_operator_gate():
    with pytest.raises(LiveLLMRefused):
        plan_from_brief("list my gmail messages", use_live_llm=True, env={})


def test_live_llm_refused_even_with_flag_but_no_attestation():
    with pytest.raises(LiveLLMRefused):
        plan_from_brief("list my gmail messages", use_live_llm=True,
                        env={"KARAKURI_ALLOW_LIVE_LLM": "1"})   # missing operator attestation
