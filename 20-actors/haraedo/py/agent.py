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


def _or_opt(order, coords, start):
    """Or-opt local move: relocate chains of length 1..3 to a better position.
    Complements 2-opt (which only reverses segments) — together they escape more
    local minima than 2-opt alone (R2, ADR-2606010200 §R2)."""
    best = order[:]
    best_len = _route_length(best, coords, start)
    improved = True
    while improved:
        improved = False
        n = len(best)
        for seg in (1, 2, 3):
            if seg >= n:
                break
            for i in range(n - seg + 1):
                chain = best[i:i + seg]
                rest = best[:i] + best[i + seg:]
                for j in range(len(rest) + 1):
                    cand = rest[:j] + chain + rest[j:]
                    cand_len = _route_length(cand, coords, start)
                    if cand_len + 1e-9 < best_len:
                        best, best_len, improved = cand, cand_len, True
            if improved:
                break
    return best, best_len


def _local_search(order, coords, start):
    """R2 route polish: alternate 2-opt and Or-opt until neither improves.
    Strictly ≥ R1's 2-opt-only quality (2-opt is the first move it runs)."""
    cur = order[:]
    cur_len = _route_length(cur, coords, start)
    while True:
        cur, _ = _two_opt(cur, coords, start)
        cur, new_len = _or_opt(cur, coords, start)
        if new_len + 1e-9 >= cur_len:
            return cur, new_len
        cur_len = new_len


def _route_eta(order, coords, depot, start_min, speed_kmh=20.0, service_min=10):
    """VRPTW arrival clock (R2): minutes-from-midnight ETA at each stop, leaving
    the depot at `start_min`, travelling at `speed_kmh`, `service_min` per stop."""
    etas, cur, t = [], depot, float(start_min)
    for s in order:
        nxt = coords[s]
        t += _haversine_km(cur[0], cur[1], nxt[0], nxt[1]) / speed_kmh * 60.0
        etas.append((s, round(t, 1)))
        t += service_min
        cur = nxt
    return etas


def _clarke_wright(stops, demand, coords, depot, cap):
    """Capacitated VRP (Clarke-Wright savings) → list of capacity-feasible 2-opt routes.

    R1 (ADR-2606010200): replaces the R0 single-vehicle NN tour. Each returned
    route's summed demand is ≤ cap, except a lone stop whose own demand exceeds
    cap (surfaced as over-capacity by the caller — G15, never silently dropped).
    """
    if not stops:
        return []

    def dij(a, b):
        return _haversine_km(coords[a][0], coords[a][1], coords[b][0], coords[b][1])

    def ddep(a):
        return _haversine_km(depot[0], depot[1], coords[a][0], coords[a][1])

    def rload(r):
        return sum(demand.get(s, 0) for s in r)

    routes = [[s] for s in stops]
    savings = []
    for i in range(len(stops)):
        for j in range(i + 1, len(stops)):
            a, b = stops[i], stops[j]
            savings.append((ddep(a) + ddep(b) - dij(a, b), a, b))
    savings.sort(key=lambda x: x[0], reverse=True)

    def find_route(x):
        for r in routes:
            if x in r:
                return r
        return None

    for _, a, b in savings:
        ra, rb = find_route(a), find_route(b)
        if ra is None or rb is None or ra is rb:
            continue
        if a not in (ra[0], ra[-1]) or b not in (rb[0], rb[-1]):
            continue
        if rload(ra) + rload(rb) > cap:
            continue
        if ra[0] == a:
            ra.reverse()
        if rb[-1] == b:
            rb.reverse()
        merged = ra + rb
        routes.remove(ra)
        routes.remove(rb)
        routes.append(merged)

    return [_local_search(r, coords, depot)[0] for r in routes]


# --------------------------------------------------------------------------- #
# kotoba entity-attribute helpers (R1)
# --------------------------------------------------------------------------- #
def _q1(query, *args):
    if datalog is None:
        return None
    rows = datalog.q(query, *args)
    return rows[0][0] if rows else None


def _attr(id_attr, id_val, attr):
    """Fetch one attribute value of the entity identified by id_attr=id_val."""
    return _q1(f"[:find ?v :in $ ?k :where [?e :{id_attr} ?k] [?e :{attr} ?v]]", id_val)


def _to_int(v, default=0):
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return default


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
    slot_id: str
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
    """Quote fee per the jurisdiction's fee model (R1, G14): free / per-item /
    per-sticker / per-weight / flat. Falls back to per-item base fees."""
    if datalog is None:
        return {"fee": 0}
    juris, items = state.get("jurisdiction", ""), state["accepted_items"]
    model = _attr("jurisdiction/id", juris, "jurisdiction/bulky-fee-model")
    model = (model or "").lstrip(":")
    if model == "free":
        fee = 0
    elif model == "per-sticker":
        fee = len(items) * _to_int(_attr("jurisdiction/id", juris, "jurisdiction/fee-per-sticker"))
    elif model == "per-weight":
        kg = sum(_to_int(_attr("item-category/code", c, "item-category/est-weight-kg")) for c in items)
        fee = kg * _to_int(_attr("jurisdiction/id", juris, "jurisdiction/fee-per-kg"))
    elif model == "flat":
        fee = _to_int(_attr("jurisdiction/id", juris, "jurisdiction/fee-flat"))
    else:  # per-item (default / unknown)
        fee = sum(_to_int(_attr("item-category/code", c, "item-category/base-fee")) for c in items)
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
    """Resolve + book the earliest open collection slot for the collection point's
    service area on/after the desired date (R1, G15 capacity-honest). No open slot
    → empty date (caller re-offers)."""
    if datalog is None:
        return {"scheduled_date": state.get("scheduled_date", ""), "slot_id": ""}
    area = _attr("collection-point/id", state["collection_point"], "collection-point/service-area")
    desired = state.get("scheduled_date") or ""
    rows = datalog.q(
        "[:find ?id ?date ?cap ?booked ?win :in $ ?j ?a :where "
        "[?s :slot/jurisdiction ?j] [?s :slot/service-area ?a] [?s :slot/id ?id] "
        "[?s :slot/date ?date] [?s :slot/capacity ?cap] [?s :slot/booked ?booked] [?s :slot/window ?win]]",
        state["jurisdiction"], area,
    )
    winrank = {":am": 0, "am": 0, ":allday": 0, "allday": 0, ":pm": 1, "pm": 1}
    cand = sorted(
        (d, winrank.get(w, 2), sid, _to_int(b))
        for sid, d, cap, b, w in rows
        if _to_int(b) < _to_int(cap) and (not desired or d >= desired)
    )
    if not cand:
        return {"scheduled_date": "", "slot_id": ""}
    d, _, sid, booked = cand[0]
    datalog.transact([{":slot/id": sid, ":slot/booked": booked + 1}])  # book it (G15)
    return {"scheduled_date": d, "slot_id": sid}


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
            ":application/slot-id": state.get("slot_id", ""),
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
    demand: dict           # collection_point_id -> kg (R1, per-stop)
    window_of: dict        # collection_point_id -> {window,start,end} (R2 VRPTW)
    load_kg: int
    vehicle: str
    crew: list
    stop_order: list
    distance_km: float
    facility: str
    routes: list           # R1: capacitated multi-vehicle plan
    unassigned: list       # R1: routes with no feasible vehicle (G15)
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
    """Cluster stops; load coordinates + per-stop demand (kg) + each stop's booked
    time window (R2 VRPTW, via application→slot-id→slot)."""
    coords, demand, window_of, load_kg = {}, {}, {}, 0
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
            items = datalog.q(
                "[:find ?w :in $ ?aid :where [?a :application/id ?aid] "
                "[?a :application/items ?c] [?e :item-category/code ?c] [?e :item-category/est-weight-kg ?w]]",
                app["app_id"],
            )
            kg = int(sum(w[0] for w in items))
            demand[cp] = demand.get(cp, 0) + kg
            load_kg += kg
            srow = datalog.q(
                "[:find ?win ?ws ?we :in $ ?aid :where [?a :application/id ?aid] "
                "[?a :application/slot-id ?sid] [?s :slot/id ?sid] [?s :slot/window ?win] "
                "[?s :slot/window-start ?ws] [?s :slot/window-end ?we]]",
                app["app_id"],
            )
            if srow:
                window_of[cp] = {"window": str(srow[0][0]), "start": int(srow[0][1]), "end": int(srow[0][2])}
    return {"coords": coords, "demand": demand, "window_of": window_of, "load_kg": load_kg}


def build_routes_node(state: DispatchState) -> dict:
    """R1 capacitated multi-vehicle plan: Clarke-Wright over per-stop demand →
    assign smallest feasible available vehicle per route + early-shift crew +
    destination facility. Routes with no feasible vehicle go to `unassigned`
    (G15 — never silently dropped)."""
    coords, demand = state["coords"], state.get("demand", {})
    stops = list(coords)
    if not stops:
        return {"routes": [], "unassigned": []}

    vehs, depot, facility = [], (35.66, 139.70), ""
    drivers, loaders = [], []
    if datalog is not None:
        vehs = sorted(
            (int(c), vid) for vid, c in datalog.q(
                "[:find ?id ?cap :in $ ?j :where [?v :vehicle/jurisdiction ?j] "
                "[?v :vehicle/status :available] [?v :vehicle/id ?id] [?v :vehicle/capacity-kg ?cap]]",
                state["jurisdiction"])
        )
        if vehs:
            d = datalog.q(
                "[:find ?lat ?lon :in $ ?v :where [?x :vehicle/id ?v] "
                "[?x :vehicle/depot-lat ?lat] [?x :vehicle/depot-lon ?lon]]", vehs[0][1])
            if d:
                depot = (d[0][0], d[0][1])
        facs = datalog.q(
            "[:find ?id ?cap ?load :in $ ?j :where [?f :facility/jurisdiction ?j] "
            "[?f :facility/id ?id] [?f :facility/capacity-tonnes-day ?cap] "
            "[?f :facility/load-tonnes-today ?load]]", state["jurisdiction"])
        spare = [fid for fid, cap, load in facs if cap > load]
        facility = spare[0] if spare else ""
        crew = datalog.q(
            "[:find ?id ?role :in $ ?j :where [?c :crew/jurisdiction ?j] "
            "[?c :crew/shift :early] [?c :crew/id ?id] [?c :crew/role ?role]]", state["jurisdiction"])
        drivers = [c[0] for c in crew if c[1] in (":driver", "driver")]
        loaders = [c[0] for c in crew if c[1] in (":loader", "loader")]

    cap = vehs[-1][0] if vehs else 4000
    window_of = state.get("window_of", {})
    speed, service = 20.0, 10

    # R2 VRPTW: partition stops by their booked time window, route each window
    # separately so a vehicle serves one window's stops within that window.
    groups = {}
    for s in stops:
        w = window_of.get(s, {"window": "allday", "start": 480, "end": 1020})
        groups.setdefault((w["window"], w["start"], w["end"]), []).append(s)

    # R3 inter-window reuse: vehicles persist in a pool with a `free_at` clock
    # (minute they are next back at the depot). A later window may reuse a vehicle
    # iff it is back by that window's start. Pool stays ascending by capacity.
    pool = [{"cap": c, "vid": v, "free_at": float("-inf")} for c, v in vehs]
    routes, unassigned = [], []
    for (win, w_start, w_end), gstops in sorted(groups.items(), key=lambda kv: kv[0][1]):
        for order in _clarke_wright(gstops, demand, coords, depot, cap):
            load = sum(demand.get(s, 0) for s in order)
            cand = next((p for p in pool if p["cap"] >= load and p["free_at"] <= w_start), None)
            if cand is None:
                unassigned.append({"stop_order": order, "load_kg": int(load), "window": win,
                                   "reason": "no vehicle free (capacity ≥ load AND back by window start) — G15"})
                continue
            reused = cand["free_at"] > float("-inf")
            etas = _route_eta(order, coords, depot, w_start, speed, service)
            return_min = (_haversine_km(coords[order[-1]][0], coords[order[-1]][1], depot[0], depot[1])
                          / speed * 60.0) if order else 0.0
            cand["free_at"] = (etas[-1][1] if etas else w_start) + service + return_min  # back-at-depot clock
            crewset = ([drivers.pop(0)] if drivers else []) + [loaders.pop(0) for _ in range(min(2, len(loaders)))]
            tw_violations = [{"stop": s, "eta_min": e} for s, e in etas if e > w_end]  # G15: surfaced, not hidden
            routes.append({
                "vehicle": cand["vid"], "stop_order": order, "load_kg": int(load),
                "distance_km": round(_route_length(order, coords, depot), 2),
                "facility": facility, "crew": crewset,
                "window": win, "window_start": w_start, "window_end": w_end,
                "etas": etas, "tw_violations": tw_violations, "vehicle_reused": reused,
            })
    return {"routes": routes, "unassigned": unassigned}


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
    """Persist every capacitated route to kotoba (state :planned — G11 design-only)."""
    area = state.get("service_area", "all")
    date_compact = state["date"].replace("-", "")
    written = []
    for n, r in enumerate(state.get("routes", []), 1):
        rid = f"{state['jurisdiction']}.route.{date_compact}-{area}-{n:02d}"
        if datalog is not None and r["vehicle"]:
            datalog.transact([{
                ":route/id": rid,
                ":route/jurisdiction": state["jurisdiction"],
                ":route/date": state["date"],
                ":route/vehicle": r["vehicle"],
                ":route/crew": list(r["crew"]),
                ":route/stops": list(r["stop_order"]),
                ":route/stop-order": json.dumps(r["stop_order"], ensure_ascii=False),
                ":route/facility-destination": r["facility"],
                ":route/distance-km": r["distance_km"],
                ":route/load-kg": int(r["load_kg"]),
                ":route/window": f":{r.get('window', 'allday')}",
                ":route/state": ":planned",
            }])
        written.append({**r, "route_id": rid, "state": ":planned"})
    return {"plan": {"routes": written, "unassigned": state.get("unassigned", [])}}


def build_dispatch_graph():
    """R1 dispatch graph: gather → cluster (coords+demand) → build_routes
    (capacitated Clarke-Wright + vehicle/crew/facility assignment) → emit_plan."""
    from langgraph.graph import StateGraph, END
    g = StateGraph(DispatchState)
    g.add_node("gather", gather_node)
    g.add_node("cluster", cluster_node)
    g.add_node("build_routes", build_routes_node)
    g.add_node("emit_plan", emit_plan_node)
    g.set_entry_point("gather")
    g.add_edge("gather", "cluster")
    g.add_edge("cluster", "build_routes")
    g.add_edge("build_routes", "emit_plan")
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
