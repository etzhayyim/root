#!/usr/bin/env python3
"""haraedo 祓戸 — bulky-waste disposal langgraph actor (kotoba WASM cell).

ADR-2606010200. Runs in-WASM on kotoba :8077. Two graphs over one kotoba EAVT
graph:

  intake   (citizen side):   classify → quote → match-facility → schedule → sticker
  dispatch (operator side):  gather → cluster → assign-vehicle → assign-crew
                             → optimize-route (NN + 2-opt) → select-facility → emit-plan

LLM access is Murakumo-only via KotobaLLM (127.0.0.1:4000, gemma3:4b). State is
written back to the kotoba Datom log. All outward action is gated by G11 (design
only at R0): handlers compute and return plans; they do not dispatch real crews.
"""
from __future__ import annotations

import json
import math
from typing import TypedDict

# kotoba-provided host bindings (WASM Component Model imports)
try:
    from kotoba import datalog, llm  # type: ignore
except ImportError:  # local dev fallback
    datalog = llm = None  # type: ignore


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def _haversine_km(a_lat: float, a_lon: float, b_lat: float, b_lon: float) -> float:
    """Great-circle distance in km (stand-in for road distance, R0)."""
    r = 6371.0
    p1, p2 = math.radians(a_lat), math.radians(b_lat)
    dphi = math.radians(b_lat - a_lat)
    dlmb = math.radians(b_lon - a_lon)
    h = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def _route_length(order, coords, start) -> float:
    """Total tour length from `start` through `order` (list of point ids)."""
    total, cur = 0.0, start
    for pid in order:
        nxt = coords[pid]
        total += _haversine_km(cur[0], cur[1], nxt[0], nxt[1])
        cur = nxt
    return total


def _nearest_neighbour(points, coords, start):
    """Greedy NN tour over point ids starting nearest to `start`."""
    remaining = list(points)
    order, cur = [], start
    while remaining:
        nxt = min(remaining, key=lambda p: _haversine_km(cur[0], cur[1], coords[p][0], coords[p][1]))
        order.append(nxt)
        cur = coords[nxt]
        remaining.remove(nxt)
    return order


def _two_opt(order, coords, start):
    """2-opt local search to shorten an NN tour (G15: real, not silently capped)."""
    best = order[:]
    best_len = _route_length(best, coords, start)
    improved = True
    while improved:
        improved = False
        for i in range(len(best) - 1):
            for k in range(i + 1, len(best)):
                cand = best[:i] + best[i:k + 1][::-1] + best[k + 1:]
                cand_len = _route_length(cand, coords, start)
                if cand_len + 1e-9 < best_len:
                    best, best_len, improved = cand, cand_len, True
    return best, best_len


# --------------------------------------------------------------------------- #
# intake graph (citizen side)
# --------------------------------------------------------------------------- #
class IntakeState(TypedDict):
    member_did: str
    consent_sig: str
    jurisdiction: str
    items: list           # item-category codes requested
    collection_point: str
    accepted_items: list  # classify writes once (no reducer needed)
    rejected_items: list  # hazardous → G3 licensed-handler boundary
    fee: int
    facility: str
    scheduled_date: str
    sticker_id: str


def classify_node(state: IntakeState) -> dict:
    """G3 hazardous-boundary: split requested items into accepted vs licensed-handler."""
    accepted, rejected = [], []
    for code in state["items"]:
        hazardous = False
        if datalog is not None:
            rows = datalog.q(
                "[:find ?h :in $ ?c :where [?e :item-category/code ?c] [?e :item-category/hazardous ?h]]",
                code,
            )
            hazardous = bool(rows and rows[0][0])
        (rejected if hazardous else accepted).append(code)
    return {"accepted_items": accepted, "rejected_items": rejected}


def quote_node(state: IntakeState) -> dict:
    """Quote fee = sum of per-category base fees (jurisdiction override TODO)."""
    fee = 0
    if datalog is not None:
        for code in state["accepted_items"]:
            rows = datalog.q(
                "[:find ?f :in $ ?c :where [?e :item-category/code ?c] [?e :item-category/base-fee ?f]]",
                code,
            )
            fee += int(rows[0][0]) if rows else 0
    return {"fee": fee}


def match_facility_node(state: IntakeState) -> dict:
    """G14/G15: choose a facility in-jurisdiction that accepts all items & has capacity."""
    if datalog is None:
        return {"facility": ""}
    facs = datalog.q(
        "[:find ?id ?cap ?load :in $ ?j :where "
        "[?f :facility/jurisdiction ?j] [?f :facility/id ?id] "
        "[?f :facility/capacity-tonnes-day ?cap] [?f :facility/load-tonnes-today ?load]]",
        state["jurisdiction"],
    )
    for fid, cap, load in facs:
        accepts = datalog.q(
            "[:find ?cat :in $ ?id :where [?f :facility/id ?id] [?f :facility/accepted-categories ?cat]]",
            fid,
        )
        accepted_set = {c[0] for c in accepts}
        if cap > load and all(it in accepted_set for it in state["accepted_items"]):
            return {"facility": fid}
    return {"facility": ""}


def schedule_node(state: IntakeState) -> dict:
    """Offer the next collection slot for the chosen collection point (R0 stub)."""
    # R0: caller supplies a desired date; production resolves against route calendar.
    return {"scheduled_date": state.get("scheduled_date", "")}


def sticker_node(state: IntakeState) -> dict:
    """Issue a deterministic sticker id and persist the application (G1 consent required)."""
    if not state.get("consent_sig"):
        return {"sticker_id": ""}  # G1: no consent → no application
    juris = state["jurisdiction"].split(".")[-1][:3].upper()
    date = (state.get("scheduled_date") or "").replace("-", "")
    sticker = f"{juris}-{date}-{abs(hash(state['member_did'])) % 100000:05d}"
    if datalog is not None:
        app_id = f"{state['jurisdiction']}.app.{date}-{sticker}"
        datalog.transact([{
            ":application/id": app_id,
            ":application/member-did": state["member_did"],
            ":application/jurisdiction": state["jurisdiction"],
            ":application/items": list(state["accepted_items"]),
            ":application/collection-point": state["collection_point"],
            ":application/scheduled-date": state.get("scheduled_date", ""),
            ":application/fee": state["fee"],
            ":application/sticker-id": sticker,
            ":application/consent-sig": state["consent_sig"],
            ":application/state": ":scheduled",
        }])
    return {"sticker_id": sticker}


def build_intake_graph():
    from langgraph.graph import StateGraph, END
    g = StateGraph(IntakeState)
    g.add_node("classify", classify_node)
    g.add_node("quote", quote_node)
    g.add_node("match_facility", match_facility_node)
    g.add_node("schedule", schedule_node)
    g.add_node("sticker", sticker_node)
    g.set_entry_point("classify")
    g.add_edge("classify", "quote")
    g.add_edge("quote", "match_facility")
    g.add_edge("match_facility", "schedule")
    g.add_edge("schedule", "sticker")
    g.add_edge("sticker", END)
    return g.compile()


# --------------------------------------------------------------------------- #
# dispatch graph (operator side) — 受付/配車/ルート/担当者
# --------------------------------------------------------------------------- #
class DispatchState(TypedDict):
    jurisdiction: str
    date: str
    service_area: str
    applications: list     # [{app_id, collection_point, items}]
    coords: dict           # collection_point_id -> (lat, lon)
    load_kg: int
    vehicle: str
    crew: list
    stop_order: list
    distance_km: float
    facility: str
    plan: dict


def gather_node(state: DispatchState) -> dict:
    """Gather scheduled applications for jurisdiction + date."""
    if datalog is None:
        return {"applications": []}
    rows = datalog.q(
        "[:find ?id ?cp :in $ ?j ?d :where "
        "[?a :application/jurisdiction ?j] [?a :application/scheduled-date ?d] "
        "[?a :application/id ?id] [?a :application/collection-point ?cp]]",
        state["jurisdiction"], state["date"],
    )
    apps = [{"app_id": r[0], "collection_point": r[1]} for r in rows]
    return {"applications": apps}


def cluster_node(state: DispatchState) -> dict:
    """Cluster stops by service-area; load coordinates + estimate total load (kg)."""
    coords, load_kg = {}, 0
    if datalog is not None:
        for app in state["applications"]:
            cp = app["collection_point"]
            rows = datalog.q(
                "[:find ?lat ?lon :in $ ?cp :where [?p :collection-point/id ?cp] "
                "[?p :collection-point/lat ?lat] [?p :collection-point/lon ?lon]]",
                cp,
            )
            if rows:
                coords[cp] = (rows[0][0], rows[0][1])
            # estimate load from each application's item weights
            items = datalog.q(
                "[:find ?w :in $ ?aid :where [?a :application/id ?aid] "
                "[?a :application/items ?c] [?e :item-category/code ?c] [?e :item-category/est-weight-kg ?w]]",
                app["app_id"],
            )
            load_kg += int(sum(w[0] for w in items))
    return {"coords": coords, "load_kg": load_kg}


def assign_vehicle_node(state: DispatchState) -> dict:
    """G15: pick the smallest available vehicle whose capacity covers the load."""
    if datalog is None:
        return {"vehicle": ""}
    vehs = datalog.q(
        "[:find ?id ?cap :in $ ?j :where [?v :vehicle/jurisdiction ?j] "
        "[?v :vehicle/status :available] [?v :vehicle/id ?id] [?v :vehicle/capacity-kg ?cap]]",
        state["jurisdiction"],
    )
    feasible = sorted([(c, vid) for vid, c in vehs if c >= state["load_kg"]])
    return {"vehicle": feasible[0][1] if feasible else ""}


def assign_crew_node(state: DispatchState) -> dict:
    """Assign one driver + loaders on the early shift (G5 labor-dignity)."""
    if datalog is None:
        return {"crew": []}
    crew = datalog.q(
        "[:find ?id ?role :in $ ?j :where [?c :crew/jurisdiction ?j] "
        "[?c :crew/shift :early] [?c :crew/id ?id] [?c :crew/role ?role]]",
        state["jurisdiction"],
    )
    drivers = [c[0] for c in crew if c[1] == ":driver" or c[1] == "driver"]
    loaders = [c[0] for c in crew if c[1] == ":loader" or c[1] == "loader"]
    assigned = (drivers[:1] + loaders[:2]) if drivers else loaders[:2]
    return {"crew": assigned}


def optimize_route_node(state: DispatchState) -> dict:
    """NN + 2-opt over collection points, starting from the vehicle depot."""
    coords = state["coords"]
    points = list(coords.keys())
    if not points:
        return {"stop_order": [], "distance_km": 0.0}
    start = (35.66, 139.70)  # default; replaced by depot below if available
    if datalog is not None and state["vehicle"]:
        d = datalog.q(
            "[:find ?lat ?lon :in $ ?v :where [?x :vehicle/id ?v] "
            "[?x :vehicle/depot-lat ?lat] [?x :vehicle/depot-lon ?lon]]",
            state["vehicle"],
        )
        if d:
            start = (d[0][0], d[0][1])
    nn = _nearest_neighbour(points, coords, start)
    order, length = _two_opt(nn, coords, start)
    return {"stop_order": order, "distance_km": round(length, 2)}


def select_facility_node(state: DispatchState) -> dict:
    """G14/G15: destination facility with spare capacity accepting the loads."""
    if datalog is None:
        return {"facility": ""}
    facs = datalog.q(
        "[:find ?id ?cap ?load :in $ ?j :where [?f :facility/jurisdiction ?j] "
        "[?f :facility/id ?id] [?f :facility/capacity-tonnes-day ?cap] "
        "[?f :facility/load-tonnes-today ?load]]",
        state["jurisdiction"],
    )
    # prefer bulky-dismantle / recycling with spare capacity
    spare = [fid for fid, cap, load in facs if cap > load]
    return {"facility": spare[0] if spare else ""}


def emit_plan_node(state: DispatchState) -> dict:
    """Persist the route plan to kotoba (state :planned — G11 keeps it design-only)."""
    route_id = f"{state['jurisdiction']}.route.{state['date'].replace('-', '')}-{state.get('service_area', 'all')}"
    plan = {
        "route_id": route_id,
        "vehicle": state["vehicle"],
        "crew": state["crew"],
        "stop_order": state["stop_order"],
        "facility_destination": state["facility"],
        "distance_km": state["distance_km"],
        "load_kg": state["load_kg"],
        "state": ":planned",
    }
    if datalog is not None and state["vehicle"]:
        datalog.transact([{
            ":route/id": route_id,
            ":route/jurisdiction": state["jurisdiction"],
            ":route/date": state["date"],
            ":route/vehicle": state["vehicle"],
            ":route/crew": list(state["crew"]),
            ":route/stops": list(state["stop_order"]),
            ":route/stop-order": json.dumps(state["stop_order"], ensure_ascii=False),
            ":route/facility-destination": state["facility"],
            ":route/distance-km": state["distance_km"],
            ":route/load-kg": int(state["load_kg"]),
            ":route/state": ":planned",
        }])
    return {"plan": plan}


def build_dispatch_graph():
    from langgraph.graph import StateGraph, END
    g = StateGraph(DispatchState)
    g.add_node("gather", gather_node)
    g.add_node("cluster", cluster_node)
    g.add_node("assign_vehicle", assign_vehicle_node)
    g.add_node("assign_crew", assign_crew_node)
    g.add_node("optimize_route", optimize_route_node)
    g.add_node("select_facility", select_facility_node)
    g.add_node("emit_plan", emit_plan_node)
    g.set_entry_point("gather")
    g.add_edge("gather", "cluster")
    g.add_edge("cluster", "assign_vehicle")
    g.add_edge("assign_vehicle", "assign_crew")
    g.add_edge("assign_crew", "optimize_route")
    g.add_edge("optimize_route", "select_facility")
    g.add_edge("select_facility", "emit_plan")
    g.add_edge("emit_plan", END)
    return g.compile()


# --------------------------------------------------------------------------- #
# kotoba actor entry points
# --------------------------------------------------------------------------- #
def handle_intake(event: dict) -> dict:
    return build_intake_graph().invoke(event)


def handle_dispatch(event: dict) -> dict:
    return build_dispatch_graph().invoke(event)


# default handler dispatches by event kind
def handle(event: dict) -> dict:
    if event.get("kind") == "dispatch":
        return handle_dispatch(event)
    return handle_intake(event)


if __name__ == "__main__":
    print("intake:", handle_intake({
        "member_did": "did:web:example", "consent_sig": "sig",
        "jurisdiction": "jp.shibuya", "items": ["furniture", "bedding"],
        "collection_point": "jp.shibuya.cp.udagawa-1", "scheduled_date": "2026-06-05",
    }))
    print("dispatch:", handle_dispatch({
        "kind": "dispatch", "jurisdiction": "jp.shibuya",
        "date": "2026-06-05", "service_area": "shibuya-north",
    }))
