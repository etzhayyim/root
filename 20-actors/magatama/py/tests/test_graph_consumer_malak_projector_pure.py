"""Pure helper tests for graph_consumer, public_malak_ads, projector,
murakumo_fleet, and telecom_ims primitives.

Covers pure functions with no DB/HTTP/LLM dependencies:
- graph_consumer: _utc_now_iso / _camel_to_snake / _maps_entity_label /
                  _convention_candidates / GRAPH_DID / CONSUME_TICK_COLLECTION /
                  DEFAULT_TIMEOUT_SEC / _COLLECTION_TO_TABLE / _MAPS_CONTROL_PLANE
- public_malak_ads: _utc_now / _today / _sha / _run_vid / _advertiser_vid /
                    _creative_vid / _snapshot_vid / _clean_text / _extract_title /
                    _ads_library_url / OWNER_DID / KNOWN_PLATFORMS
- projector: _now_iso / _now_ms / _new_rkey / _strip_reasoning /
             _extract_final_answer / DEFAULT_REPO_PROJECTOR /
             COLLECTION_MESSAGE / COLLECTION_REFLECTION
- murakumo_fleet: _utc_now_iso / _extract_node_name / MURAKUMO_DID /
                  NODE_IP_MAP / FLEET_NODES / DEFAULT_LITELLM_URL
- telecom_ims: _now_iso / _hash_id / _new_id / _join / _vid / _require /
               _caller / TELECOM_DID / ACCESS_NETWORKS / CODECS / RELEASE_CAUSES
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_py_src = Path(__file__).resolve().parents[1] / "src"
if str(_py_src) not in sys.path:
    sys.path.insert(0, str(_py_src))

from pymagatama.primitives import graph_consumer as GC
from pymagatama.primitives import public_malak_ads as PM
from pymagatama.primitives import projector as PR
from pymagatama.primitives import murakumo_fleet as MF
from pymagatama.primitives import telecom_ims as IMS


# ─── graph_consumer — _utc_now_iso ───────────────────────────────────────────

def test_gc_utc_now_iso_returns_string():
    assert isinstance(GC._utc_now_iso(), str)


def test_gc_utc_now_iso_ends_with_z():
    assert GC._utc_now_iso().endswith("Z")


def test_gc_utc_now_iso_contains_t():
    assert "T" in GC._utc_now_iso()


# ─── graph_consumer — _camel_to_snake ────────────────────────────────────────

def test_gc_camel_to_snake_simple():
    result = GC._camel_to_snake("helloWorld")
    assert result == "hello_world"


def test_gc_camel_to_snake_multiple():
    result = GC._camel_to_snake("camelCaseString")
    assert result == "camel_case_string"


def test_gc_camel_to_snake_already_snake():
    result = GC._camel_to_snake("already_snake")
    assert result == "already_snake"


def test_gc_camel_to_snake_single_word():
    result = GC._camel_to_snake("hello")
    assert result == "hello"


def test_gc_camel_to_snake_edge_map_entity():
    result = GC._camel_to_snake("edgeActorHasCapability")
    assert "_actor_has_capability" in result


# ─── graph_consumer — _maps_entity_label ─────────────────────────────────────

def test_gc_maps_entity_label_asset_special():
    result = GC._maps_entity_label("asset")
    assert result == "PhysicalAsset"


def test_gc_maps_entity_label_capitalizes():
    result = GC._maps_entity_label("building")
    assert result == "Building"


def test_gc_maps_entity_label_non_special_passthrough():
    result = GC._maps_entity_label("route")
    assert result == "Route"


# ─── graph_consumer — _convention_candidates ─────────────────────────────────

def test_gc_convention_candidates_vertex_collection():
    result = GC._convention_candidates("ai.gftd.apps.hr.journalEntry")
    assert len(result) >= 1
    assert any("vertex_hr" in c for c in result)


def test_gc_convention_candidates_edge_collection():
    result = GC._convention_candidates("ai.gftd.apps.hr.edgeActorHasCapability")
    assert any("edge_hr" in c for c in result)


def test_gc_convention_candidates_maps_spatial():
    result = GC._convention_candidates("ai.gftd.apps.maps.building")
    assert "vertex_spatial" in result


def test_gc_convention_candidates_non_matching_returns_empty():
    result = GC._convention_candidates("app.bsky.actor.profile")
    assert result == []


def test_gc_convention_candidates_returns_list():
    result = GC._convention_candidates("ai.gftd.apps.foo.barBaz")
    assert isinstance(result, list)


# ─── graph_consumer — constants ──────────────────────────────────────────────

def test_gc_graph_did_starts_with_did():
    assert GC.GRAPH_DID.startswith("did:")


def test_gc_consume_tick_collection_is_nsid():
    assert "ai.gftd.apps.graph" in GC.CONSUME_TICK_COLLECTION


def test_gc_default_timeout_is_positive():
    assert isinstance(GC.DEFAULT_TIMEOUT_SEC, float)
    assert GC.DEFAULT_TIMEOUT_SEC > 0


def test_gc_collection_to_table_is_dict():
    assert isinstance(GC._COLLECTION_TO_TABLE, dict)


def test_gc_collection_to_table_not_empty():
    assert len(GC._COLLECTION_TO_TABLE) > 0


def test_gc_maps_control_plane_is_set():
    assert isinstance(GC._MAPS_CONTROL_PLANE, set)


# ─── public_malak_ads — _utc_now ─────────────────────────────────────────────

def test_pm_utc_now_returns_string():
    assert isinstance(PM._utc_now(), str)


def test_pm_utc_now_ends_with_z():
    assert PM._utc_now().endswith("Z")


# ─── public_malak_ads — _today ───────────────────────────────────────────────

def test_pm_today_returns_date():
    import datetime
    result = PM._today()
    assert isinstance(result, datetime.date)


# ─── public_malak_ads — _sha ─────────────────────────────────────────────────

def test_pm_sha_starts_with_prefix():
    result = PM._sha("run", "meta", "q1")
    assert result.startswith("run-")


def test_pm_sha_is_deterministic():
    a = PM._sha("adv", "meta", "adv-001")
    b = PM._sha("adv", "meta", "adv-001")
    assert a == b


def test_pm_sha_differs_by_parts():
    a = PM._sha("adv", "meta", "001")
    b = PM._sha("adv", "google", "001")
    assert a != b


# ─── public_malak_ads — vid helpers ──────────────────────────────────────────

def test_pm_run_vid_starts_with_at():
    result = PM._run_vid("run-001")
    assert result.startswith("at://")


def test_pm_run_vid_contains_run_id():
    result = PM._run_vid("run-abc")
    assert "run-abc" in result


def test_pm_advertiser_vid_contains_platform():
    result = PM._advertiser_vid("meta", "adv-001")
    assert "meta-adv-001" in result


def test_pm_creative_vid_contains_ad_id():
    result = PM._creative_vid("google", "ad-123")
    assert "google-ad-123" in result


def test_pm_snapshot_vid_contains_parts():
    result = PM._snapshot_vid("linkedin", "ad-1", "run-1")
    assert "linkedin" in result
    assert "ad-1" in result


# ─── public_malak_ads — _clean_text ──────────────────────────────────────────

def test_pm_clean_text_removes_html_tags():
    result = PM._clean_text("<p>Hello <b>world</b></p>")
    assert "<" not in result
    assert "Hello" in result


def test_pm_clean_text_respects_limit():
    result = PM._clean_text("a" * 5000, 100)
    assert len(result) <= 100


def test_pm_clean_text_removes_script():
    result = PM._clean_text("<script>alert(1)</script>text")
    assert "alert" not in result
    assert "text" in result


# ─── public_malak_ads — _extract_title ───────────────────────────────────────

def test_pm_extract_title_from_title_tag():
    result = PM._extract_title("<html><title>Ad Library</title></html>")
    assert result == "Ad Library"


def test_pm_extract_title_from_h1():
    result = PM._extract_title("<html><h1>Main</h1></html>")
    assert result == "Main"


def test_pm_extract_title_empty():
    result = PM._extract_title("")
    assert result == ""


# ─── public_malak_ads — _ads_library_url ─────────────────────────────────────

def test_pm_ads_library_url_meta():
    result = PM._ads_library_url("meta", "nike", "US")
    assert "facebook.com" in result
    assert "nike" in result


def test_pm_ads_library_url_google():
    result = PM._ads_library_url("google", "apple", "GB")
    assert "adstransparency.google.com" in result


def test_pm_ads_library_url_linkedin():
    result = PM._ads_library_url("linkedin", "microsoft", "US")
    assert "linkedin.com" in result


def test_pm_ads_library_url_unknown_platform_returns_empty():
    result = PM._ads_library_url("unknown", "q", "US")
    assert result == ""


# ─── public_malak_ads — constants ────────────────────────────────────────────

def test_pm_owner_did_starts_with_did():
    assert PM.OWNER_DID.startswith("did:")


def test_pm_known_platforms_is_set():
    assert isinstance(PM.KNOWN_PLATFORMS, set)


def test_pm_known_platforms_contains_meta():
    assert "meta" in PM.KNOWN_PLATFORMS


def test_pm_known_query_kinds_is_set():
    assert isinstance(PM.KNOWN_QUERY_KINDS, set)


# ─── projector — _now_iso ────────────────────────────────────────────────────

def test_pr_now_iso_returns_string():
    assert isinstance(PR._now_iso(), str)


def test_pr_now_iso_ends_with_z():
    assert PR._now_iso().endswith("Z")


# ─── projector — _now_ms ─────────────────────────────────────────────────────

def test_pr_now_ms_returns_int():
    assert isinstance(PR._now_ms(), int)


def test_pr_now_ms_positive():
    assert PR._now_ms() > 0


def test_pr_now_ms_increases():
    import time
    a = PR._now_ms()
    time.sleep(0.01)
    b = PR._now_ms()
    assert b >= a


# ─── projector — _new_rkey ───────────────────────────────────────────────────

def test_pr_new_rkey_starts_with_prefix():
    result = PR._new_rkey("msg")
    assert result.startswith("msg-")


def test_pr_new_rkey_unique():
    a = PR._new_rkey("msg")
    b = PR._new_rkey("msg")
    assert a != b


def test_pr_new_rkey_returns_string():
    assert isinstance(PR._new_rkey("ref"), str)


# ─── projector — _strip_reasoning ────────────────────────────────────────────

def test_pr_strip_reasoning_with_tag():
    text = "<reasoning>internal thought</reasoning>Final answer"
    reasoning, cleaned = PR._strip_reasoning(text)
    assert reasoning == "internal thought"
    assert "Final answer" in cleaned
    assert "<reasoning>" not in cleaned


def test_pr_strip_reasoning_no_tag():
    reasoning, cleaned = PR._strip_reasoning("Just a reply")
    assert reasoning == ""
    assert cleaned == "Just a reply"


def test_pr_strip_reasoning_empty():
    reasoning, cleaned = PR._strip_reasoning("")
    assert reasoning == ""
    assert cleaned == ""


# ─── projector — _extract_final_answer ───────────────────────────────────────

def test_pr_extract_final_answer_with_tag():
    text = "some reasoning <answer>42</answer>"
    result = PR._extract_final_answer(text)
    assert result == "42"


def test_pr_extract_final_answer_no_tag():
    result = PR._extract_final_answer("plain response")
    assert result == "plain response"


def test_pr_extract_final_answer_empty():
    result = PR._extract_final_answer("")
    assert result == ""


# ─── projector — constants ───────────────────────────────────────────────────

def test_pr_default_repo_starts_with_did():
    assert PR.DEFAULT_REPO_PROJECTOR.startswith("did:")


def test_pr_collection_message_is_nsid():
    assert "." in PR.COLLECTION_MESSAGE


def test_pr_collection_reflection_is_nsid():
    assert "." in PR.COLLECTION_REFLECTION


# ─── murakumo_fleet — _utc_now_iso ───────────────────────────────────────────

def test_mf_utc_now_iso_returns_string():
    assert isinstance(MF._utc_now_iso(), str)


def test_mf_utc_now_iso_ends_with_z():
    assert MF._utc_now_iso().endswith("Z")


# ─── murakumo_fleet — _extract_node_name ─────────────────────────────────────

def test_mf_extract_node_name_from_url():
    result = MF._extract_node_name("http://192.168.1.10:11434")
    assert isinstance(result, str)


def test_mf_extract_node_name_returns_string():
    result = MF._extract_node_name("http://10.0.0.1:4000")
    assert isinstance(result, str)
    assert len(result) > 0


# ─── murakumo_fleet — constants ──────────────────────────────────────────────

def test_mf_murakumo_did_starts_with_did():
    assert MF.MURAKUMO_DID.startswith("did:")


def test_mf_node_ip_map_is_dict():
    assert isinstance(MF.NODE_IP_MAP, dict)


def test_mf_node_ip_map_not_empty():
    assert len(MF.NODE_IP_MAP) > 0


def test_mf_fleet_nodes_is_list():
    assert isinstance(MF.FLEET_NODES, list)


def test_mf_fleet_nodes_not_empty():
    assert len(MF.FLEET_NODES) > 0


def test_mf_default_litellm_url_starts_with_http():
    assert MF.DEFAULT_LITELLM_URL.startswith("http")


def test_mf_health_timeout_is_positive():
    assert isinstance(MF.HEALTH_TIMEOUT_SEC, float)
    assert MF.HEALTH_TIMEOUT_SEC > 0


# ─── telecom_ims — _now_iso ──────────────────────────────────────────────────

def test_ims_now_iso_returns_string():
    assert isinstance(IMS._now_iso(), str)


def test_ims_now_iso_contains_t():
    assert "T" in IMS._now_iso()


# ─── telecom_ims — _hash_id ──────────────────────────────────────────────────

def test_ims_hash_id_none_returns_none():
    assert IMS._hash_id(None) is None


def test_ims_hash_id_empty_returns_none():
    assert IMS._hash_id("") is None


def test_ims_hash_id_adds_sha256_prefix():
    result = IMS._hash_id("msisdn-001")
    assert result is not None
    assert result.startswith("sha256:")


def test_ims_hash_id_deterministic():
    a = IMS._hash_id("sip:user@example.com")
    b = IMS._hash_id("sip:user@example.com")
    assert a == b


# ─── telecom_ims — _new_id ───────────────────────────────────────────────────

def test_ims_new_id_with_parts_deterministic():
    a = IMS._new_id("imsSession", "call-1", "callee-1")
    b = IMS._new_id("imsSession", "call-1", "callee-1")
    assert a == b


def test_ims_new_id_starts_with_prefix():
    result = IMS._new_id("suppSvc", "sub-1")
    assert result.startswith("suppSvc_")


def test_ims_new_id_without_parts_unique():
    a = IMS._new_id("imsSession")
    b = IMS._new_id("imsSession")
    assert a != b


# ─── telecom_ims — _hash_join ────────────────────────────────────────────────

def test_ims_hash_join_none_returns_none():
    assert IMS._hash_join(None) is None


def test_ims_hash_join_single_hashes():
    result = IMS._hash_join("msisdn-001")
    assert result is not None
    assert result.startswith("sha256:")


def test_ims_hash_join_list_hashes_and_joins():
    result = IMS._hash_join(["msisdn-001", "msisdn-002"])
    assert result is not None
    assert "," in result


def test_ims_hash_join_empty_list_returns_none():
    assert IMS._hash_join([]) is None


# ─── telecom_ims — _vid ──────────────────────────────────────────────────────

def test_ims_vid_starts_with_at():
    result = IMS._vid("imsSession", "sess-001")
    assert result.startswith("at://")


def test_ims_vid_contains_kind():
    result = IMS._vid("suppService", "svc-1")
    assert "suppService" in result


# ─── telecom_ims — _require ──────────────────────────────────────────────────

def test_ims_require_present_does_not_raise():
    IMS._require({"callId": "c1", "accessNetwork": "volte"}, ["callId", "accessNetwork"])


def test_ims_require_missing_raises():
    with pytest.raises(ValueError):
        IMS._require({"callId": "c1"}, ["callId", "accessNetwork"])


# ─── telecom_ims — _caller ───────────────────────────────────────────────────

def test_ims_caller_uses_caller_did():
    result = IMS._caller({"callerDid": "did:web:ims.gftd.ai"})
    assert result == "did:web:ims.gftd.ai"


def test_ims_caller_falls_back_to_telecom_did():
    result = IMS._caller({})
    assert result == IMS.TELECOM_DID


# ─── telecom_ims — constants ─────────────────────────────────────────────────

def test_ims_telecom_did_starts_with_did():
    assert IMS.TELECOM_DID.startswith("did:")


def test_ims_access_networks_is_set():
    assert isinstance(IMS.ACCESS_NETWORKS, set)


def test_ims_access_networks_contains_volte():
    assert "volte" in IMS.ACCESS_NETWORKS


def test_ims_codecs_is_set():
    assert isinstance(IMS.CODECS, set)


def test_ims_codecs_contains_amr_nb():
    assert "AMR-NB" in IMS.CODECS


def test_ims_release_causes_is_set():
    assert isinstance(IMS.RELEASE_CAUSES, set)


def test_ims_release_causes_contains_normal():
    assert "normal" in IMS.RELEASE_CAUSES


def test_ims_released_by_is_set():
    assert isinstance(IMS.RELEASED_BY, set)


def test_ims_supp_service_types_is_set():
    assert isinstance(IMS.SUPP_SERVICE_TYPES, set)
