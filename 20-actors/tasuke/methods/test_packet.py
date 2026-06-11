#!/usr/bin/env python3
"""Tests for 助 (tasuke) packet generator — the usable "誰でも使える" surface."""
from __future__ import annotations

import pathlib
import tempfile

import packet
from _edn import load_edn

_SEED = pathlib.Path(__file__).resolve().parents[1] / "data" / "seed-cybercrime-cases.kotoba.edn"


def _cases():
    return load_edn(_SEED)[":case/batch"]


# ── the packet is free + complete for every seed case ────────────────────────
def test_build_packet_every_case_free_and_documented():
    for c in _cases():
        p = packet.build_packet(c)
        assert p["cost"] == 0
        assert p["documents"], f"{p['caseId']} produced no documents"
        for d in p["documents"]:
            assert d[":doc/authored-by"] == ":member"
            assert d[":doc/support-cost-jpy"] == 0
            assert d[":doc/needs-member-signature"] is True
            assert d[":doc/published"] is False


def test_document_selection_by_kind():
    cases = {c[":case/id"]: c for c in _cases()}
    fund = packet.build_packet(cases["c-fund-1"])
    kinds = [d[":doc/kind"].lstrip(":") for d in fund["documents"]]
    assert "bank-freeze-request" in kinds          # money moved → bank組戻し
    to = packet.build_packet(cases["c-takeover-1"])
    tkinds = [d[":doc/kind"].lstrip(":") for d in to["documents"]]
    assert "recovery-plan" in tkinds and "platform-request" in tkinds


def test_police_core_always_present():
    core = {"damage-report", "incident-statement", "evidence-index", "damage-calculation"}
    for c in _cases():
        kinds = {d[":doc/kind"].lstrip(":") for d in packet.build_packet(c)["documents"]}
        assert core <= kinds


# ── regression: the seed registry must be reachable (the stray-brace bug) ─────
def test_windows_are_populated_from_registry():
    p = packet.build_packet(_cases()[0])
    assert p["windows"]
    # every window resolves to a real registry name, not just the bare code
    for w in p["windows"]:
        assert w["name"] and w["name"] != w["code"]


# ── the cover restates the charter promises ──────────────────────────────────
def test_cover_states_free_and_member_submitted():
    cover = packet._cover(packet.build_packet(_cases()[0]))
    assert "¥0" in cover and "全て無料" in cover
    assert "本人が作成・署名・提出" in cover


# ── write_packet emits printable files ───────────────────────────────────────
def test_write_packet_emits_cover_and_docs():
    p = packet.build_packet(_cases()[0])
    with tempfile.TemporaryDirectory() as td:
        out = packet.write_packet(p, pathlib.Path(td) / "pk")
        files = sorted(x.name for x in out.iterdir())
        assert "00-COVER.md" in files
        assert len([f for f in files if f.endswith(".txt")]) == len(p["documents"])


# ── G1/G7 gate still bites through the packet path ───────────────────────────
def test_packet_refuses_non_consented_case():
    bad = dict(_cases()[0]); bad[":case/consent"] = False
    try:
        packet.build_packet(bad)
        assert False, "G7 should refuse a non-consented case"
    except ValueError as e:
        assert "G7" in str(e)


def test_packet_refuses_priced_case():
    bad = dict(_cases()[0]); bad[":case/support-cost-jpy"] = 1000
    try:
        packet.build_packet(bad)
        assert False, "G1 should refuse a priced case"
    except ValueError as e:
        assert "G1" in str(e)


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
    print(f"{len(fns) - failed}/{len(fns)} passed in test_packet.py")
    sys.exit(1 if failed else 0)
