#!/usr/bin/env python3
"""haraedo 祓戸 — verification harness (langgraph-independent).

ADR-2606010200. Runs the pure route-optimization helpers and the node functions
(with the kotoba `datalog` host binding stubbed) plus constitutional-gate checks
over the kotoba seed EDN. Mirrors the toritsugi pytest-invariant precedent.

Run standalone:   python3 test_agent.py
Or via pytest:    pytest test_agent.py
"""
from __future__ import annotations

import os
import re

import agent

SEED = os.path.join(os.path.dirname(__file__), "..", "kotoba", "seed.edn")


# --------------------------------------------------------------------------- #
# 1. pure route-optimization helpers
# --------------------------------------------------------------------------- #
COORDS = {
    "jinnan": (35.6645, 139.6975),
    "udagawa": (35.6615, 139.6980),
    "dogenzaka": (35.6575, 139.6960),
    "ebisu": (35.6465, 139.7100),
}
DEPOT = (35.6600, 139.7020)


def test_haversine_symmetric_and_zero():
    assert agent._haversine_km(35.0, 139.0, 35.0, 139.0) == 0.0
    a = agent._haversine_km(35.66, 139.70, 35.6465, 139.71)
    b = agent._haversine_km(35.6465, 139.71, 35.66, 139.70)
    assert abs(a - b) < 1e-9
    assert a > 0


def test_two_opt_never_worse_than_nn():
    pts = list(COORDS)
    nn = agent._nearest_neighbour(pts, COORDS, DEPOT)
    order, length = agent._two_opt(nn, COORDS, DEPOT)
    nn_len = agent._route_length(nn, COORDS, DEPOT)
    assert set(order) == set(pts)          # no stop dropped (G15)
    assert length <= nn_len + 1e-9         # 2-opt cannot worsen


def test_route_visits_every_stop():
    pts = list(COORDS)
    nn = agent._nearest_neighbour(pts, COORDS, DEPOT)
    assert sorted(nn) == sorted(pts)


# --------------------------------------------------------------------------- #
# 2. node functions with a stubbed kotoba datalog binding
# --------------------------------------------------------------------------- #
class FakeDatalog:
    """Minimal stand-in for the kotoba `datalog` host binding."""

    HAZARD = {"battery", "appliance-recycle-law"}
    FEES = {"furniture": 1000, "bedding": 1500, "bicycle": 800}

    def __init__(self):
        self.transacted = []

    def q(self, query, *args):
        if ":item-category/hazardous" in query:
            return [[args[0] in self.HAZARD]]
        if ":item-category/base-fee" in query:
            return [[self.FEES.get(args[0], 0)]]
        if ":vehicle/capacity-kg" in query and ":vehicle/status :available" in query:
            return [["veh-small", 1000], ["veh-big", 4000]]
        return []

    def transact(self, datoms):
        self.transacted.extend(datoms)
        return True


def _with_fake(fn, *a, **k):
    saved = agent.datalog
    agent.datalog = FakeDatalog()
    try:
        return fn(*a, **k), agent.datalog
    finally:
        agent.datalog = saved


def test_classify_splits_hazardous_g3():
    state = {"items": ["furniture", "battery", "bedding", "appliance-recycle-law"]}
    out, _ = _with_fake(agent.classify_node, state)
    assert out["accepted_items"] == ["furniture", "bedding"]
    assert out["rejected_items"] == ["battery", "appliance-recycle-law"]


def test_quote_sums_accepted_fees():
    state = {"accepted_items": ["furniture", "bedding"]}
    out, _ = _with_fake(agent.quote_node, state)
    assert out["fee"] == 2500


def test_sticker_requires_consent_g1():
    # no consent → no sticker, no transaction
    state = {"member_did": "did:x", "consent_sig": "", "jurisdiction": "jp.shibuya",
             "accepted_items": ["furniture"], "collection_point": "cp", "fee": 1000,
             "scheduled_date": "2026-06-05"}
    out, fake = _with_fake(agent.sticker_node, state)
    assert out["sticker_id"] == ""
    assert fake.transacted == []


def test_sticker_with_consent_emits_application():
    state = {"member_did": "did:x", "consent_sig": "sig", "jurisdiction": "jp.shibuya",
             "accepted_items": ["furniture"], "collection_point": "cp", "fee": 1000,
             "scheduled_date": "2026-06-05"}
    out, fake = _with_fake(agent.sticker_node, state)
    assert out["sticker_id"]
    assert len(fake.transacted) == 1
    assert fake.transacted[0][":application/state"] == ":scheduled"


def test_assign_vehicle_respects_capacity_g15():
    # load 1500kg → small (1000) infeasible, must pick big (4000)
    state = {"jurisdiction": "jp.shibuya", "load_kg": 1500}
    out, _ = _with_fake(agent.assign_vehicle_node, state)
    assert out["vehicle"] == "veh-big"
    # load 500kg → smallest feasible is small
    state2 = {"jurisdiction": "jp.shibuya", "load_kg": 500}
    out2, _ = _with_fake(agent.assign_vehicle_node, state2)
    assert out2["vehicle"] == "veh-small"


# --------------------------------------------------------------------------- #
# 3. constitutional-gate checks over the seed EDN
# --------------------------------------------------------------------------- #
def _top_level_maps(edn: str):
    """Yield each top-level {...} map string, brace-aware (handles #{} sets)."""
    maps, depth, start, instr, i = [], 0, None, False, 0
    while i < len(edn):
        c = edn[i]
        if instr:
            if c == "\\":
                i += 2
                continue
            if c == '"':
                instr = False
            i += 1
            continue
        if c == '"':
            instr = True
        elif c == ";":
            while i < len(edn) and edn[i] != "\n":
                i += 1
            continue
        elif c == "{":
            if depth == 0:
                start = i
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0 and start is not None:
                maps.append(edn[start:i + 1])
                start = None
        i += 1
    return maps


def _load_seed():
    with open(SEED, encoding="utf-8") as f:
        return f.read()


def test_hazardous_items_not_charged_g3():
    """G3: hazardous categories route to licensed handlers, never billed as bulky waste."""
    for m in _top_level_maps(_load_seed()):
        if ":item-category/hazardous true" in m:
            assert re.search(r":item-category/base-fee\s+0\b", m), \
                f"hazardous item charged a bulky-waste fee:\n{m}"


def test_every_facility_has_capacity_and_sourcing_g14_g15():
    """G14/G15: facilities are usable only with a declared capacity + provenance flag."""
    for m in _top_level_maps(_load_seed()):
        if ":facility/id" in m:
            assert ":facility/capacity-tonnes-day" in m, f"facility missing capacity:\n{m}"
            assert ":facility/sourcing" in m, f"facility missing sourcing flag:\n{m}"
            assert ":facility/accepted-categories" in m, f"facility missing accepted set:\n{m}"


def test_seed_is_representative_not_authoritative():
    """R0 honesty: every facility seed is flagged :representative (no false authority)."""
    seed = _load_seed()
    assert ":sourcing :authoritative" not in seed, "R0 seed must not claim authoritative coverage"
    facilities = [m for m in _top_level_maps(seed) if ":facility/id" in m]
    assert facilities, "no facilities found in seed"
    for m in facilities:
        assert ":facility/sourcing :representative" in m


def test_route_load_within_vehicle_capacity_g15():
    """The worked-example route must not exceed its assigned vehicle's capacity."""
    seed = _load_seed()
    maps = _top_level_maps(seed)
    vehicles = {}
    for m in maps:
        vid = re.search(r':vehicle/id "([^"]+)"', m)
        cap = re.search(r":vehicle/capacity-kg (\d+)", m)
        if vid and cap:
            vehicles[vid.group(1)] = int(cap.group(1))
    for m in maps:
        if ":route/id" in m:
            veh = re.search(r':route/vehicle "([^"]+)"', m)
            load = re.search(r":route/load-kg (\d+)", m)
            if veh and load:
                assert int(load.group(1)) <= vehicles[veh.group(1)], \
                    f"route load exceeds vehicle capacity:\n{m}"


# --------------------------------------------------------------------------- #
# standalone runner
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = failed = 0
    for t in tests:
        try:
            t()
            passed += 1
            print(f"  PASS  {t.__name__}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"  FAIL  {t.__name__}: {type(e).__name__}: {e}")
    print(f"\n{passed} passed / {failed} failed / {len(tests)} total")
    raise SystemExit(1 if failed else 0)
