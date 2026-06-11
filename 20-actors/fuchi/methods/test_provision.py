#!/usr/bin/env python3
"""Tests for 扶持 (fuchi) provision.py — R1(a) in-kind provisioning intents.

Standalone-runnable: python3 test_provision.py
"""
from __future__ import annotations

import sys

from provision import PROVIDER_REGISTRY, ProvisioningIntent, provision
from route import route_envelope


def _env(line, imputed):
    return {":envelope/line": ":" + line, ":envelope/imputed-usd-micros-yr": imputed,
            ":envelope/cash-usd-micros": 0}


def test_every_rail_has_a_provider():
    rails = route_envelope([_env(l, 1_000_000) for l in
                            ("housing", "food", "energy", "compute", "tooling", "care", "liquidity")])
    intents = provision(rails, "alloc-1")
    assert len(intents) == 7
    providers = {i.provider_did for i in intents}
    assert "did:web:etzhayyim.com:actor:mitsuho" in providers
    assert "commons-land" in providers and "murakumo" in providers


def test_provider_kinds_are_classified():
    rails = route_envelope([_env("housing", 1), _env("food", 1), _env("compute", 1)])
    by = {i.rail_kind: i for i in provision(rails, "a")}
    assert by["housing-commons"].provider_kind == "commons"
    assert by["food-mitsuho"].provider_kind == "actor"
    assert by["compute-murakumo"].provider_kind == "infra"


def test_liquidity_is_member_principal():
    rails = route_envelope([_env("liquidity", 5), _env("food", 5)])
    by = {i.rail_kind: i for i in provision(rails, "a")}
    assert by["liquidity-warifu"].member_principal is True
    assert by["liquidity-warifu"].provider_did.endswith("warifu")
    assert by["food-mitsuho"].member_principal is False


def test_intent_is_dry_run_cashless_keyless():
    for i in provision(route_envelope([_env("food", 1)]), "a"):
        assert i.cash_usd_micros == 0
        assert i.server_held_key is False
        assert i.published is False


def test_published_true_is_refused():
    try:
        ProvisioningIntent("a", "food-mitsuho", "did:..:mitsuho", "actor", 1, published=True)
    except ValueError as e:
        assert "G10" in str(e)
        return
    raise AssertionError("published=true must be refused (G10)")


def test_cash_intent_is_refused():
    try:
        ProvisioningIntent("a", "food-mitsuho", "did:..:mitsuho", "actor", 1, cash_usd_micros=5)
    except ValueError as e:
        assert "cash" in str(e).lower()
        return
    raise AssertionError("nonzero cash intent must be refused (G2)")


def test_server_key_intent_is_refused():
    try:
        ProvisioningIntent("a", "food-mitsuho", "did:..:mitsuho", "actor", 1, server_held_key=True)
    except ValueError as e:
        assert "no-server-key" in str(e)
        return
    raise AssertionError("server-held-key intent must be refused (G9)")


def test_registry_covers_every_route_rail():
    # PROVIDER_REGISTRY must cover exactly the 7 rail kinds
    from route import LINE_TO_RAIL
    rail_kinds = {k for k, _ in LINE_TO_RAIL.values()}
    assert set(PROVIDER_REGISTRY) == rail_kinds


def _run():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
    print(f"test_provision.py: {len(fns)} passed")
    return 0


if __name__ == "__main__":
    sys.exit(_run())
