#!/usr/bin/env python3
"""post_quantum-compat — suite/migration registry tests (ADR-2606111300).

Asserts the paper's §7 coverage empirically instead of by belief:
  - every Shor-vulnerable layer carries an explicit, accounted status
  - FIPS 203/204 constants and draft multicodecs match the implementations
    that landed in @etzhayyim/sdk + did-web (PR 1616/1621/1625/1630)
  - Mosca/Grover helpers reproduce the paper's headline numbers
  - Datom emit is deterministic, ground/derived strata separated
"""
import sys
import pathlib

ACTOR_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ACTOR_DIR / "methods"))

from suite import (  # noqa: E402
    LAYERS, SUITES, GATED, MIGRATION_DONE,
    coverage_report, grover_effective_bits, mosca, shor_applies,
)
import datom_emit  # noqa: E402


def test_registry_nontrivial_and_fully_accounted():
    assert len(LAYERS) >= 10
    for layer in LAYERS:
        status = layer[":layer/status"]
        assert status in MIGRATION_DONE | GATED, \
            f"{layer[':layer/id']} has unaccounted status {status}"


def test_every_shor_layer_is_migrated_or_explicitly_gated():
    for layer in LAYERS:
        if shor_applies(layer):
            s = layer[":layer/status"]
            assert s == ":migrated" or s in GATED, layer[":layer/id"]
            if s in GATED:
                # a gated layer must say WHY (honesty: no silent debt)
                assert layer.get(":layer/note"), layer[":layer/id"]


def test_migrated_layers_carry_provenance():
    for layer in LAYERS:
        if layer[":layer/status"] == ":migrated":
            assert layer.get(":layer/adr"), layer[":layer/id"]
            assert layer.get(":layer/pr"), layer[":layer/id"]


def test_fips_constants_match_landed_implementation():
    kem = SUITES[":suite/pqh-v1"][":suite/kem"]
    sig = SUITES[":suite/pqh-v1"][":suite/sig"]
    # FIPS 203 ML-KEM-768 / FIPS 204 ML-DSA-65 — same numbers the SDK tests
    # assert (MLKEM768_PUBLIC_BYTES etc.) and the paper's size-cost table uses.
    assert kem[":kem/pq-public-bytes"] == 1184
    assert kem[":kem/pq-ciphertext-bytes"] == 1088
    assert sig[":sig/pq-public-bytes"] == 1952
    assert sig[":sig/pq-signature-bytes"] == 3309
    # draft multicodec registrations (multiformats table)
    assert kem[":kem/pq-multicodec"] == 0x120C
    assert sig[":sig/pq-multicodec"] == 0x1211


def test_grover_bound():
    assert grover_effective_bits(256) == 128
    assert grover_effective_bits(128) == 64


def test_mosca_inequality_matches_paper():
    # etzhayyim parameters from §6: x≈30 (permanent public ciphertext),
    # y≈4 (50+ actor rollout), z≈15 (median CRQC) → act now.
    r = mosca(30, 4, 15)
    assert r[":mosca/act-now"] is True
    assert r[":mosca/slack-years"] == -19
    # sanity inversion: a distant CRQC removes the urgency
    assert mosca(5, 2, 100)[":mosca/act-now"] is False


def test_coverage_readout_is_honest():
    cov = coverage_report()
    assert cov[":coverage/unknown"] == 0
    assert cov[":coverage/shor-vulnerable"] >= 6
    assert cov[":coverage/migrated"] >= 3
    assert 0.0 < cov[":coverage/migrated-fraction"] < 1.0, \
        "claiming 100% would be dishonest while gated layers remain"
    assert cov[":coverage/gated-ids"], "gated layers must be enumerated, not hidden"


def test_datom_emit_deterministic_and_stratified():
    a = datom_emit.emit(tx=7)
    b = datom_emit.emit(tx=7)
    assert a == b, "emit must be byte-identical across runs"
    assert "[:layer/key-wrap :layer/status :migrated 7 :add]" in a
    ground, _, derived = a.partition(";; ── DERIVED")
    assert ":pq/coverage" not in ground, "derived readouts must not be ground datoms"
    assert ":pq/is-transient true" in derived
