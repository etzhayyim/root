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
    # no fee-model in the fake → quote_node falls back to per-item base fees
    state = {"jurisdiction": "us.sf", "accepted_items": ["furniture", "bedding"]}
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
# 4. R1 — per-jurisdiction fee models
# --------------------------------------------------------------------------- #
class FakeJuris:
    """Stub for jurisdiction fee-model + item-attr queries."""

    def __init__(self, model, per_sticker=0, per_kg=0, flat=0, weights=None, base=None):
        self.model, self.per_sticker, self.per_kg, self.flat = model, per_sticker, per_kg, flat
        self.weights, self.base = weights or {}, base or {}
        self.transacted = []

    def q(self, query, *a):
        if "jurisdiction/bulky-fee-model" in query:
            return [[self.model]] if self.model is not None else []
        if "jurisdiction/fee-per-sticker" in query:
            return [[self.per_sticker]]
        if "jurisdiction/fee-per-kg" in query:
            return [[self.per_kg]]
        if "jurisdiction/fee-flat" in query:
            return [[self.flat]]
        if "item-category/est-weight-kg" in query:
            return [[self.weights.get(a[0], 0)]]
        if "item-category/base-fee" in query:
            return [[self.base.get(a[0], 0)]]
        return []

    def transact(self, d):
        self.transacted.extend(d)


def _quote_with(fake, state):
    saved = agent.datalog
    agent.datalog = fake
    try:
        return agent.quote_node(state)["fee"]
    finally:
        agent.datalog = saved


def test_fee_model_per_sticker():
    fake = FakeJuris(":per-sticker", per_sticker=400)
    assert _quote_with(fake, {"jurisdiction": "jp.shibuya", "accepted_items": ["a", "b"]}) == 800


def test_fee_model_per_weight():
    fake = FakeJuris(":per-weight", per_kg=100, weights={"furniture": 35, "bedding": 25})
    assert _quote_with(fake, {"jurisdiction": "gb.camden", "accepted_items": ["furniture", "bedding"]}) == 6000


def test_fee_model_flat_and_free():
    assert _quote_with(FakeJuris(":flat", flat=5000), {"jurisdiction": "de.berlin", "accepted_items": ["x", "y", "z"]}) == 5000
    assert _quote_with(FakeJuris(":free"), {"jurisdiction": "us.nyc", "accepted_items": ["x", "y"]}) == 0


def test_fee_model_per_item_default():
    fake = FakeJuris(":per-item", base={"furniture": 1000, "bedding": 1500})
    assert _quote_with(fake, {"jurisdiction": "us.sf", "accepted_items": ["furniture", "bedding"]}) == 2500


# --------------------------------------------------------------------------- #
# 5. R1 — capacity-honest slot scheduling
# --------------------------------------------------------------------------- #
class FakeSlots:
    def __init__(self):
        self.transacted = []

    def q(self, query, *a):
        if "collection-point/service-area" in query:
            return [["shibuya-north"]]
        if ":slot/jurisdiction" in query:
            # (id, date, capacity, booked, window)
            return [["s-pm", "2026-06-05", 20, 0, ":pm"],
                    ["s-am", "2026-06-05", 20, 3, ":am"],
                    ["s-full", "2026-06-04", 2, 2, ":am"]]
        return []

    def transact(self, d):
        self.transacted.extend(d)


def test_schedule_picks_earliest_open_slot_and_books():
    saved = agent.datalog
    agent.datalog = FakeSlots()
    try:
        out = agent.schedule_node({"jurisdiction": "jp.shibuya", "collection_point": "cp", "scheduled_date": ""})
        assert out["slot_id"] == "s-am"          # full earlier slot skipped, am before pm
        assert out["scheduled_date"] == "2026-06-05"
        assert agent.datalog.transacted[0][":slot/booked"] == 4   # booked it (G15)
    finally:
        agent.datalog = saved


def test_schedule_no_open_slot_returns_empty():
    class AllFull:
        def q(self, query, *a):
            if "collection-point/service-area" in query:
                return [["shibuya-north"]]
            if ":slot/jurisdiction" in query:
                return [["s1", "2026-06-05", 5, 5, ":am"]]
            return []
        def transact(self, d):
            pass
    saved = agent.datalog
    agent.datalog = AllFull()
    try:
        out = agent.schedule_node({"jurisdiction": "jp.shibuya", "collection_point": "cp", "scheduled_date": ""})
        assert out["slot_id"] == "" and out["scheduled_date"] == ""
    finally:
        agent.datalog = saved


# --------------------------------------------------------------------------- #
# 6. R1 — capacitated VRP (Clarke-Wright)
# --------------------------------------------------------------------------- #
VRP_COORDS = {
    "a": (35.660, 139.700), "b": (35.665, 139.701),
    "c": (35.670, 139.702), "d": (35.700, 139.750),
}
VRP_DEPOT = (35.659, 139.700)


def test_clarke_wright_respects_capacity_and_covers_all():
    demand = {"a": 2000, "b": 2000, "c": 2000, "d": 2000}
    routes = agent._clarke_wright(list(VRP_COORDS), demand, VRP_COORDS, VRP_DEPOT, 4000)
    for r in routes:                                   # every route ≤ capacity (G15)
        assert sum(demand[s] for s in r) <= 4000
    flat = [s for r in routes for s in r]
    assert sorted(flat) == sorted(VRP_COORDS)          # every stop covered exactly once
    assert len(routes) >= 2                             # 8000 total / 4000 cap → split


def test_clarke_wright_single_route_when_it_all_fits():
    demand = {k: 100 for k in VRP_COORDS}
    routes = agent._clarke_wright(list(VRP_COORDS), demand, VRP_COORDS, VRP_DEPOT, 4000)
    assert len(routes) == 1
    assert sorted(routes[0]) == sorted(VRP_COORDS)


# --------------------------------------------------------------------------- #
# 7. R1 — seed completeness for fee params + slot capacity honesty
# --------------------------------------------------------------------------- #
def test_every_jurisdiction_has_currency_and_fee_params():
    for m in _top_level_maps(_load_seed()):
        if ":jurisdiction/id" in m:
            assert ":jurisdiction/currency" in m, f"jurisdiction missing currency:\n{m}"
            assert ":jurisdiction/bulky-fee-model" in m


def test_slots_booked_within_capacity():
    import re as _re
    for m in _top_level_maps(_load_seed()):
        if ":slot/id" in m:
            cap = int(_re.search(r":slot/capacity (\d+)", m).group(1))
            booked = int(_re.search(r":slot/booked (\d+)", m).group(1))
            assert booked <= cap, f"slot overbooked:\n{m}"


# --------------------------------------------------------------------------- #
# 8. R2 — solver upgrade (Or-opt + local search) and VRPTW ETA
# --------------------------------------------------------------------------- #
def test_or_opt_never_worse():
    pts = list(VRP_COORDS)
    base = agent._route_length(pts, VRP_COORDS, VRP_DEPOT)
    order, length = agent._or_opt(pts, VRP_COORDS, VRP_DEPOT)
    assert set(order) == set(pts)
    assert length <= base + 1e-9


def test_local_search_at_least_as_good_as_two_opt():
    pts = list(VRP_COORDS)
    _, two_opt_len = agent._two_opt(pts, VRP_COORDS, VRP_DEPOT)
    ls_order, ls_len = agent._local_search(pts, VRP_COORDS, VRP_DEPOT)
    assert set(ls_order) == set(pts)
    assert ls_len <= two_opt_len + 1e-9        # local search starts with 2-opt → never worse


def test_route_eta_monotonic_and_window_flag():
    order = ["a", "b", "c", "d"]
    etas = agent._route_eta(order, VRP_COORDS, VRP_DEPOT, start_min=480, speed_kmh=20.0, service_min=10)
    times = [t for _, t in etas]
    assert times == sorted(times)              # ETAs strictly increase along the route
    assert all(t >= 480 for t in times)        # never before window open
    # a tight window end forces a violation on the later stops
    violations = [s for s, t in etas if t > 485]
    assert len(violations) >= 1                 # G15: late stops are detectable, not hidden


# --------------------------------------------------------------------------- #
# 9. R2 — authoritative facility ingestion transform
# --------------------------------------------------------------------------- #
def _load_fetch_module():
    import importlib.util
    p = os.path.join(os.path.dirname(__file__), "..", "kotoba", "fetch_facilities.py")
    spec = importlib.util.spec_from_file_location("fetch_facilities", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_fetch_facilities_transform_is_authoritative_with_provenance():
    fm = _load_fetch_module()
    rows = [{
        "id": "jp.shibuya.fac.auth-01", "jurisdiction": "jp.shibuya",
        "name": "渋谷清掃工場 (official)", "kind": "incinerator",
        "lat": "35.658", "lon": "139.699", "capacity_tonnes_day": "200",
        "accepted_categories": "furniture;bedding", "operating_hours": "Mon-Sat 08:00-17:00",
        "gate_fee_per_tonne": "4000",
    }]
    out = fm.transform(rows, "jp.moe.ippan", fm.SOURCES["jp.moe.ippan"]["url"])
    assert len(out) == 1
    rec = out[0]
    assert ":facility/sourcing :authoritative" in rec     # NOT :representative
    assert ":facility/source-url" in rec and "env.go.jp" in rec
    assert ":facility/source-dataset \"jp.moe.ippan\"" in rec
    assert ":facility/kind :incinerator" in rec
    assert "#{:furniture :bedding}" in rec


def test_fetch_facilities_sources_are_open_license_only():
    fm = _load_fetch_module()
    banned = ("GovWin", "Bloomberg", "Politico", "FiscalNote", "proprietary")
    for k, v in fm.SOURCES.items():
        assert v["url"].startswith("http")
        assert not any(b.lower() in v["license"].lower() for b in banned)


# --------------------------------------------------------------------------- #
# 10. R3 — inter-window vehicle reuse
# --------------------------------------------------------------------------- #
class FakeDispatchDL:
    """Stub for build_routes_node: one small vehicle, one facility, no crew."""

    def q(self, query, *a):
        if ":vehicle/status :available" in query:
            return [["v1", 2000]]
        if ":vehicle/depot-lat" in query:
            return [[35.660, 139.700]]
        if ":facility/jurisdiction" in query and ":facility/capacity-tonnes-day" in query:
            return [["f1", 100.0, 0.0]]
        if ":crew/shift :early" in query:
            return []
        return []

    def transact(self, d):
        pass


def test_inter_window_vehicle_reuse_r3():
    saved = agent.datalog
    agent.datalog = FakeDispatchDL()
    try:
        state = {
            "jurisdiction": "x",
            "coords": {"a": (35.661, 139.701), "b": (35.662, 139.702)},
            "demand": {"a": 500, "b": 500},
            "window_of": {
                "a": {"window": "am", "start": 480, "end": 720},
                "b": {"window": "pm", "start": 780, "end": 1020},
            },
        }
        out = agent.build_routes_node(state)
        routes = out["routes"]
        assert out["unassigned"] == []                 # the one vehicle covers both windows
        assert len(routes) == 2
        by_win = {r["window"]: r for r in routes}
        assert by_win["am"]["vehicle"] == "v1" and by_win["pm"]["vehicle"] == "v1"
        assert by_win["am"]["vehicle_reused"] is False  # first use
        assert by_win["pm"]["vehicle_reused"] is True   # reused across windows (R3)
    finally:
        agent.datalog = saved


def test_no_reuse_when_vehicle_cannot_return_in_time_r3():
    # The AM stop is ~120 km from depot, so the single vehicle is still out (well
    # past the PM window start) and cannot be reused → PM goes unassigned (G15).
    saved = agent.datalog
    agent.datalog = FakeDispatchDL()
    try:
        state = {
            "jurisdiction": "x",
            "coords": {"a": (36.50, 140.60), "b": (35.662, 139.702)},  # 'a' very far
            "demand": {"a": 500, "b": 500},
            "window_of": {
                "a": {"window": "am", "start": 480, "end": 720},
                "b": {"window": "pm", "start": 900, "end": 1020},
            },
        }
        out = agent.build_routes_node(state)
        wins = {r["window"] for r in out["routes"]}
        assert "am" in wins
        assert "pm" not in wins and len(out["unassigned"]) >= 1   # G15: surfaced, not silently served
    finally:
        agent.datalog = saved


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
