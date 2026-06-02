#!/usr/bin/env python3
"""tsutae-factory-r0 — engineering passes (a step up from "representative boxes").

Runs three engineering checks over the scene + BOM SSoT and emits verifiable
results + kotoba datoms:

  1. CLASH DETECTION   — utility routes vs structure (柱/梁/壁) hard interference,
                         and utility-vs-utility proximity (coordination clash,
                         < clearance). → clashes.json (consumed by the 3-D viewer).
  2. SIZING            — electrical (load schedule → feeder current → %voltage-drop
                         → cable adequacy), water (fixture units → design flow →
                         pipe Ø) and drainage (slope / fall) — computed by formula,
                         compared to the representative spec, pass/fail.
  3. CODE CHECKS       — 建ぺい率 / 容積率 / 避難距離 / 屋内消火栓カバー / 駐車台数,
                         computed from scene geometry vs a code limit, pass/fail.

HONEST SCOPE: these are SIMPLIFIED engineering models with documented assumptions
(loads, fixture units, code limits embedded below). They turn "plausible boxes"
into "computed + checked design figures" — but they are NOT a licensed engineer's
stamped 構造計算書 / 設備計算書 / 確認申請. They flag problems; they do not certify.

`run_engineering(scene, parts, meta) -> {report, entities, clashes}`.
"""
import json
import math
import sys
from pathlib import Path


# ── geometry helpers ──────────────────────────────────────────────────────────
def _structure_boxes(scene):
    """All structural members as (id, kind, (minx,miny,minz), (maxx,maxy,maxz))."""
    out = []
    for c in scene.get("columns", []):
        hw = c["w"] * 0.5
        out.append((c["id"], "column",
                    (c["x"] - hw, c["y"] - hw, 0.0), (c["x"] + hw, c["y"] + hw, c["height"])))
    for b in scene.get("beams", []):
        hs = b["section"] * 0.5
        y0, y1 = sorted(b["span_y"])
        out.append((b["id"], "beam",
                    (b["x"] - hs, y0, b["z"] - hs), (b["x"] + hs, y1, b["z"] + hs)))
    for w in scene.get("walls", []):
        a = w["aabb"]
        out.append((w["id"], "wall", (a[0], a[1], 0.0), (a[2], a[3], w["height"])))
    return out


def _family(kind):
    if kind.startswith("electrical"):
        return "電気"
    if kind in ("water-supply", "hot-water"):
        return "給水"
    if kind == "drainage":
        return "排水"
    if kind == "storm-drain":
        return "雨水"
    if kind == "gas-supply":
        return "ガス"
    if kind == "compressed-air":
        return "圧空"
    if kind == "data-backbone":
        return "通信"
    if kind == "fire-main":
        return "消火"
    return kind


def _utility_segments(scene):
    """Each utility segment as a fattened AABB at its design z (incl. negative)."""
    segs = []
    for u in scene.get("utilities", []):
        hw = max(u["width"], 0.12) * 0.5
        z = u["z"]
        for i in range(len(u["path"]) - 1):
            (x0, y0), (x1, y1) = u["path"][i], u["path"][i + 1]
            mn = (min(x0, x1) - hw, min(y0, y1) - hw, z - hw)
            mx = (max(x0, x1) + hw, max(y0, y1) + hw, z + hw)
            segs.append({
                "uid": u["id"], "kind": u["kind"], "family": _family(u["kind"]),
                "min": mn, "max": mx, "z": z,
                "mid": (0.5 * (x0 + x1), 0.5 * (y0 + y1), z),
            })
    return segs


def _overlap_1d(amin, amax, bmin, bmax):
    return min(amax, bmax) - max(amin, bmin)  # >0 = overlap depth


def _aabb_clash(a_min, a_max, b_min, b_max):
    """Return (ox, oy, oz, cx, cy, cz) overlap depths + centre, or None."""
    ox = _overlap_1d(a_min[0], a_max[0], b_min[0], b_max[0])
    oy = _overlap_1d(a_min[1], a_max[1], b_min[1], b_max[1])
    oz = _overlap_1d(a_min[2], a_max[2], b_min[2], b_max[2])
    if ox > 0 and oy > 0 and oz > 0:
        cx = 0.5 * (max(a_min[0], b_min[0]) + min(a_max[0], b_max[0]))
        cy = 0.5 * (max(a_min[1], b_min[1]) + min(a_max[1], b_max[1]))
        cz = 0.5 * (max(a_min[2], b_min[2]) + min(a_max[2], b_max[2]))
        return (ox, oy, oz, cx, cy, cz)
    return None


CLEARANCE_M = 0.30  # min vertical separation between crossing services


def detect_clashes(scene):
    structs = _structure_boxes(scene)
    segs = _utility_segments(scene)
    clashes = []

    # (a) utility vs structure — hard interference
    for s in segs:
        for sid, skind, smin, smax in structs:
            r = _aabb_clash(s["min"], s["max"], smin, smax)
            if r:
                _ox, _oy, _oz, cx, cy, cz = r
                clashes.append({
                    "id": f"clash:{s['uid']}__{sid}",
                    "kind": "hard",
                    "systems": [s["family"], skind],
                    "a": s["uid"], "b": sid,
                    "x": round(cx, 2), "y": round(cy, 2), "z": round(cz, 2),
                    "clearance_m": round(-max(_ox, _oy, _oz), 3),
                    "note": f"{s['family']}配管/配線が{skind}({sid})を貫通",
                })

    # (b) utility vs utility — coordination (plan overlap + Δz < clearance)
    for i in range(len(segs)):
        for j in range(i + 1, len(segs)):
            a, b = segs[i], segs[j]
            if a["family"] == b["family"]:
                continue
            ox = _overlap_1d(a["min"][0], a["max"][0], b["min"][0], b["max"][0])
            oy = _overlap_1d(a["min"][1], a["max"][1], b["min"][1], b["max"][1])
            if ox <= 0 or oy <= 0:
                continue
            dz = abs(a["z"] - b["z"])
            if dz >= CLEARANCE_M:
                continue
            cx = 0.5 * (max(a["min"][0], b["min"][0]) + min(a["max"][0], b["max"][0]))
            cy = 0.5 * (max(a["min"][1], b["min"][1]) + min(a["max"][1], b["max"][1]))
            clashes.append({
                "id": f"clash:{a['uid']}__{b['uid']}@{round(cx)}_{round(cy)}",
                "kind": "coordination",
                "systems": [a["family"], b["family"]],
                "a": a["uid"], "b": b["uid"],
                "x": round(cx, 2), "y": round(cy, 2), "z": round(0.5 * (a["z"] + b["z"]), 2),
                "clearance_m": round(dz, 3),
                "note": f"{a['family']}×{b['family']} 交差 Δz={round(dz,2)}m < {CLEARANCE_M}m 要調整",
            })

    # de-dup coordination clashes that share a corridor cell
    seen, uniq = set(), []
    for c in clashes:
        key = (c["kind"], frozenset(c["systems"]), round(c["x"]), round(c["y"]))
        if key in seen:
            continue
        seen.add(key)
        uniq.append(c)
    return uniq


# ── electrical sizing ─────────────────────────────────────────────────────────
# Connected loads (kW) keyed by building.edn part id (engineering assumption).
# Truck-plant line loads: a 1600t servo press + waterborne paint booth/oven +
# Class-8 chassis dyno dominate the schedule (representative R0 figures).
_EQUIP_KW = {
    "bld:F1-framejig": 40.0, "bld:F2-press": 400.0, "bld:F3-weldjig": 50.0,
    "bld:F4-paintbooth": 250.0, "bld:F5-conveyor": 30.0, "bld:F7-dyno": 200.0,
    "bld:F8-cell": 0.5, "bld:F11-marriage": 25.0, "bld:F12-cmm": 5.0,
    "bld:E1-lighting": 0.2, "bld:E3-air": 75.0, "bld:E4-hvac": 120.0,
    "bld:G10-wiringdev": 0.0, "bld:H3-pump": 5.5, "bld:H5-heater": 5.0,
}
_DEMAND_FACTOR = 0.65
_SYS_V = 415.0    # 3φ line voltage
_PF = 0.85
_CV325_R = 0.0601  # Ω/km, 325sq Cu
_CV325_X = 0.0903  # Ω/km
_AMP_PER_SET = 400.0  # ampacity of one 600V CV 3C-325sq set (representative)
_VD_LIMIT_PCT = 3.0
_TX_KVA = 1500.0   # G2 mould transformer rating


def size_electrical(parts):
    by_id = {p["part/id"]: p for p in parts}
    connected = 0.0
    rows = []
    for pid, kw in _EQUIP_KW.items():
        p = by_id.get(pid)
        if not p:
            continue
        qty = int(p.get("part/qty", 1) or 1)
        item_kw = kw * qty
        connected += item_kw
        if item_kw > 0:
            rows.append((p.get("part/name", pid), qty, item_kw))
    demand_kw = connected * _DEMAND_FACTOR
    demand_kva = demand_kw / _PF
    current = demand_kva * 1000.0 / (math.sqrt(3) * _SYS_V)
    # feeder length from the CV cable line item (cubicle → MDB)
    length = 90.0
    for p in parts:
        if p["part/id"] == "bld:G6-cvcable":
            length = float(p.get("part/length-m", 90) or 90)
    # parallel 325sq sets sized to the feeder current; impedance divides by sets.
    n_sets = max(1, math.ceil(current / _AMP_PER_SET))
    vd = (math.sqrt(3) * (current / n_sets)
          * (_CV325_R * _PF + _CV325_X * math.sin(math.acos(_PF))) * (length / 1000.0))
    vd_pct = vd / _SYS_V * 100.0
    cubicle_ok = demand_kva <= _TX_KVA
    return {
        "discipline": "電気 (低圧幹線)",
        "connected_kw": round(connected, 1),
        "demand_factor": _DEMAND_FACTOR,
        "demand_kw": round(demand_kw, 1),
        "demand_kva": round(demand_kva, 1),
        "feeder_current_a": round(current, 1),
        "feeder_cable": f"600V CV 3C-325sq x{n_sets} (parallel)",
        "feeder_sets": n_sets,
        "feeder_length_m": length,
        "voltage_drop_pct": round(vd_pct, 2),
        "vd_limit_pct": _VD_LIMIT_PCT,
        "transformer_kva": _TX_KVA,
        "verdict": "OK" if (cubicle_ok and vd_pct <= _VD_LIMIT_PCT) else "NG",
        "checks": [
            f"需要 {round(demand_kva,1)}kVA <= 変圧器 {_TX_KVA}kVA: {'OK' if cubicle_ok else 'NG'}",
            f"幹線 {round(current,1)}A → 325sq x{n_sets} 並列 (1条 {int(_AMP_PER_SET)}A)",
            f"電圧降下 {round(vd_pct,2)}% <= {_VD_LIMIT_PCT}%: {'OK' if vd_pct<=_VD_LIMIT_PCT else 'NG (要 太線化/分割)'}",
        ],
        "loads": rows,
    }


# ── water / drainage sizing ───────────────────────────────────────────────────
# Water-supply fixture units (WSFU-ish) per sanitary group (assumption).
_FU_PER_SANITARY = 4.0  # 大便器FV/手洗/流し平均
_V_TARGET = 1.5         # m/s design velocity in supply pipe


def size_water(parts):
    by_id = {p["part/id"]: p for p in parts}
    n_fix = int(by_id.get("bld:H6-sanitary", {}).get("part/qty", 8) or 8)
    units = n_fix * _FU_PER_SANITARY
    # simultaneous flow (simplified Hunter-curve approximation), L/min
    q_lpm = 12.0 * math.sqrt(units) + 6.0
    q_m3s = q_lpm / 1000.0 / 60.0
    area = q_m3s / _V_TARGET
    dia_mm = math.sqrt(4.0 * area / math.pi) * 1000.0
    spec_mm = 50.0  # PPR 50A main
    return {
        "discipline": "給水 (主管)",
        "fixtures": n_fix,
        "fixture_units": round(units, 1),
        "design_flow_lpm": round(q_lpm, 1),
        "required_dia_mm": round(dia_mm, 1),
        "spec_dia_mm": spec_mm,
        "verdict": "OK" if dia_mm <= spec_mm else "NG",
        "checks": [f"必要管径 {round(dia_mm,1)}mm <= 計画 PPR{int(spec_mm)}A: "
                   f"{'OK' if dia_mm<=spec_mm else 'NG (要 サイズアップ)'}"],
    }


_DRAIN_SLOPE = {100: 1.0 / 100.0}  # VP100 minimum slope


def size_drainage(scene):
    # total horizontal drainage run length
    run = 0.0
    for u in scene.get("utilities", []):
        if u["kind"] != "drainage":
            continue
        for i in range(len(u["path"]) - 1):
            (x0, y0), (x1, y1) = u["path"][i], u["path"][i + 1]
            run += math.hypot(x1 - x0, y1 - y0)
    min_slope = _DRAIN_SLOPE[100]
    required_fall = run * min_slope
    available_fall = 0.6  # invert depth band -0.6..0.0 at outfall (assumption)
    return {
        "discipline": "排水 (横主管 VP100)",
        "run_length_m": round(run, 1),
        "min_slope": "1/100",
        "required_fall_m": round(required_fall, 2),
        "available_fall_m": available_fall,
        "verdict": "OK" if required_fall <= available_fall else "NG",
        "checks": [f"必要落差 {round(required_fall,2)}m <= 確保落差 {available_fall}m: "
                   f"{'OK' if required_fall<=available_fall else 'NG (要 中継ポンプ/深さ確保)'}"],
    }


# ── code checks (建築基準法 / 消防法 — simplified) ────────────────────────────
def code_checks(scene):
    bb = scene["bbox_m"]
    sb = scene.get("site_bbox_m", [bb[0] - 12, bb[1] - 12, bb[2] + 12, bb[3] + 12])
    footprint = (bb[2] - bb[0]) * (bb[3] - bb[1])
    site_area = (sb[2] - sb[0]) * (sb[3] - sb[1])
    stories = 1
    floor_area = footprint * stories
    rows = []

    bcr = footprint / site_area * 100.0
    rows.append(("建ぺい率", f"{bcr:.1f}%", "<= 60% (準工業/工業)", bcr <= 60.0))

    far = floor_area / site_area * 100.0
    rows.append(("容積率", f"{far:.1f}%", "<= 200%", far <= 200.0))

    # 避難距離: farthest interior corner to nearest exit (exit_lights as proxies)
    exits = []
    for fx in scene.get("fixtures", []):
        if fx["id"] == "exit_lights":
            exits = [(p[0], p[1]) for p in fx["points"]]
    worst = 0.0
    for cx in (bb[0], bb[2]):
        for cy in (bb[1], bb[3]):
            d = min((math.hypot(cx - ex, cy - ey) for ex, ey in exits), default=999)
            worst = max(worst, d)
    rows.append(("歩行避難距離(直線近似)", f"{worst:.1f}m", "<= 50m (準耐火+SP)", worst <= 50.0))

    # 屋内消火栓カバー: 1号 半径25m — center to perimeter fire ring
    cover_r = max((bb[2] - bb[0]) * 0.5, (bb[3] - bb[1]) * 0.5)
    rows.append(("屋内消火栓 包含半径(近似)", f"{cover_r:.1f}m", "<= 25m/栓 (要 複数栓)",
                 cover_r <= 25.0))

    # parking: 工場 1台/200m2 (附置義務の代表値)
    req_stalls = math.ceil(floor_area / 200.0)
    prov_area = 0.0
    for p in scene.get("site_pavements", []):
        if p["id"] == "site_parking":
            a = p["rect"]
            prov_area = (a[2] - a[0]) * (a[3] - a[1])
    prov_stalls = int(prov_area / 12.5)  # 12.5m2/台
    rows.append(("駐車台数", f"{prov_stalls}台 計画", f">= {req_stalls}台 (1台/200m2)",
                 prov_stalls >= req_stalls))

    return {
        "site_area_m2": round(site_area, 0),
        "building_footprint_m2": round(footprint, 0),
        "rows": [{"rule": r, "value": v, "limit": lim, "verdict": "OK" if ok else "NG/要検討"}
                 for (r, v, lim, ok) in rows],
    }


# ── buildability (施工性: ロボット到達 / サイクルタイム / footprint) ───────────
def _elem_boxes(scene):
    """render-element id → (cx, cy, w, h) for work-zone estimation."""
    box = {}
    bb = scene["bbox_m"]
    sb = scene.get("site_bbox_m", bb)
    box["floor"] = (0.5 * (bb[0] + bb[2]), 0.5 * (bb[1] + bb[3]), bb[2] - bb[0], bb[3] - bb[1])
    box["ground"] = (0.5 * (sb[0] + sb[2]), 0.5 * (sb[1] + sb[3]), sb[2] - sb[0], sb[3] - sb[1])
    for c in scene.get("columns", []):
        box[c["id"]] = (c["x"], c["y"], c["w"], c["w"])
    for b in scene.get("beams", []):
        y0, y1 = sorted(b["span_y"])
        box[b["id"]] = (b["x"], 0.5 * (y0 + y1), b["section"], y1 - y0)
    for key in ("walls", "machines", "service_nodes", "site_structures"):
        for e in scene.get(key, []):
            a = e["aabb"]
            box[e["id"]] = (0.5 * (a[0] + a[2]), 0.5 * (a[1] + a[3]), a[2] - a[0], a[3] - a[1])
    for key in ("zones", "site_pavements", "site_greens"):
        for e in scene.get(key, []):
            a = e["rect"]
            box[e["id"]] = (0.5 * (a[0] + a[2]), 0.5 * (a[1] + a[3]), a[2] - a[0], a[3] - a[1])
    for cv in scene.get("conveyors", []):
        xs = [p[0] for p in cv["path"]]
        ys = [p[1] for p in cv["path"]]
        box[cv["id"]] = (0.5 * (min(xs) + max(xs)), 0.5 * (min(ys) + max(ys)),
                         max(xs) - min(xs) + 1, max(ys) - min(ys) + 1)
    for u in scene.get("utilities", []):
        xs = [p[0] for p in u["path"]]
        ys = [p[1] for p in u["path"]]
        box[u["id"]] = (0.5 * (min(xs) + max(xs)), 0.5 * (min(ys) + max(ys)),
                        max(xs) - min(xs) + 1, max(ys) - min(ys) + 1)
    for fx in scene.get("fixtures", []):
        xs = [p[0] for p in fx["points"]]
        ys = [p[1] for p in fx["points"]]
        box[fx["id"]] = (0.5 * (min(xs) + max(xs)), 0.5 * (min(ys) + max(ys)),
                         max(xs) - min(xs) + 1, max(ys) - min(ys) + 1)
    for c in scene.get("cells", []):
        box[c["id"]] = (c["pos"][0], c["pos"][1], 1.5, 1.5)
    for a in scene.get("agvs", []):
        box[a["id"]] = (a["pos"][0], a["pos"][1], a["size"][0], a["size"][1])
    for p in scene.get("site_posts", []):
        box.setdefault(p["id"], (p["x"], p["y"], 0.5, 0.5))
    return box


def buildability(scene, steps, robots):
    boxes = _elem_boxes(scene)
    reg = {r["robot/id"]: r for r in robots}
    bb = scene["bbox_m"]
    rows = []
    for s in steps:
        rid = s.get("step/robot")
        r = reg.get(rid)
        if not r:
            continue
        reveals = s.get("step/reveals", [])
        # work zone = union bbox of revealed elements (else the whole floor)
        bxs = [boxes[i] for i in reveals if i in boxes]
        if bxs:
            xmin = min(b[0] - b[2] / 2 for b in bxs)
            xmax = max(b[0] + b[2] / 2 for b in bxs)
            ymin = min(b[1] - b[3] / 2 for b in bxs)
            ymax = max(b[1] + b[3] / 2 for b in bxs)
            zw, zh = xmax - xmin, ymax - ymin
        else:
            zw, zh = bb[2] - bb[0], bb[3] - bb[1]
        zmax = max(zw, zh, 0.5)
        reach = float(r.get("robot/reach-m", 1.0))
        mobile = bool(r.get("robot/mobile", False))
        setups = math.ceil(zmax / (2 * reach)) if reach > 0 else 99
        reach_ok = mobile or zmax <= 2 * reach
        # cycle-time vs schedule
        units = max(len(reveals), 1)
        cyc = float(r.get("robot/cycle-min", 10))
        robot_h = units * setups * cyc / 60.0
        cap_h = float(s.get("step/duration-d", 1)) * 8.0  # 1 robot, 8h/day
        n_robots = max(1, math.ceil(robot_h / cap_h)) if cap_h > 0 else 1
        verdict = "OK" if (reach_ok and n_robots <= 2) else "要検討"
        rows.append({
            "step": s["step/id"], "name": s.get("step/name", ""), "robot": rid,
            "robot_name": r.get("robot/name", rid), "maturity": r.get("robot/maturity", "?"),
            "zone_m": f"{zw:.0f}x{zh:.0f}", "reach_m": reach, "setups": setups,
            "robot_hours": round(robot_h, 1), "schedule_h": round(cap_h, 0),
            "robots_needed": n_robots, "verdict": verdict,
        })
    return rows


# ── kotoba entities ───────────────────────────────────────────────────────────
def _entities(of, clashes, sizings, code, build):
    ents = []
    for c in clashes:
        ents.append({
            "id": c["id"], "type": "SarutahikoFactoryClash", "labelEn": c["note"],
            "claims": [
                {"pred": "clash/of", "value": of},
                {"pred": "clash/kind", "value": c["kind"]},
                {"pred": "clash/a", "value": c["a"]},
                {"pred": "clash/b", "value": c["b"]},
                {"pred": "clash/systems", "value": " x ".join(c["systems"])},
                {"pred": "clash/clearanceM", "value": str(c["clearance_m"])},
                {"pred": "clash/location", "value": f"{c['x']},{c['y']},{c['z']}"},
            ],
        })
    for s in sizings:
        claims = [{"pred": "sizing/of", "value": of},
                  {"pred": "sizing/discipline", "value": s["discipline"]},
                  {"pred": "sizing/verdict", "value": s["verdict"]}]
        for k, v in s.items():
            if k in ("discipline", "verdict", "checks", "loads"):
                continue
            claims.append({"pred": f"sizing/{k}", "value": str(v)})
        ents.append({"id": f"sizing:{s['discipline']}", "type": "SarutahikoFactorySizing",
                     "labelEn": s["discipline"], "claims": claims})
    for r in code["rows"]:
        ents.append({
            "id": f"code:{r['rule']}", "type": "SarutahikoFactoryCodeCheck", "labelEn": r["rule"],
            "claims": [
                {"pred": "code/of", "value": of},
                {"pred": "code/rule", "value": r["rule"]},
                {"pred": "code/value", "value": r["value"]},
                {"pred": "code/limit", "value": r["limit"]},
                {"pred": "code/verdict", "value": r["verdict"]},
            ],
        })
    for b in build:
        ents.append({
            "id": f"build:{b['step']}", "type": "SarutahikoFactoryBuildability", "labelEn": b["name"],
            "claims": [
                {"pred": "build/of", "value": of},
                {"pred": "build/step", "value": b["step"]},
                {"pred": "build/robot", "value": b["robot"]},
                {"pred": "build/zoneM", "value": b["zone_m"]},
                {"pred": "build/setups", "value": str(b["setups"])},
                {"pred": "build/robotHours", "value": str(b["robot_hours"])},
                {"pred": "build/robotsNeeded", "value": str(b["robots_needed"])},
                {"pred": "build/verdict", "value": b["verdict"]},
            ],
        })
    return ents


def run_engineering(scene, parts, meta, steps=None, robots=None):
    of = meta.get("bom/of", "tsutae-factory-r0")
    clashes = detect_clashes(scene)
    sizings = [size_electrical(parts), size_water(parts), size_drainage(scene)]
    code = code_checks(scene)
    build = buildability(scene, steps, robots) if (steps and robots) else []
    report = {
        "of": of,
        "clashes": {"count": len(clashes),
                    "hard": sum(1 for c in clashes if c["kind"] == "hard"),
                    "coordination": sum(1 for c in clashes if c["kind"] == "coordination"),
                    "items": clashes},
        "sizing": sizings,
        "code_checks": code,
        "buildability": build,
        "disclaimer": "簡略化エンジニアリングモデル (R0)。有資格者の構造/設備計算書・確認申請・消防同意ではない。",
    }
    entities = _entities(of, clashes, sizings, code, build)
    return {"report": report, "entities": entities, "clashes": clashes}


def main():
    from kotoba_gen import parse_edn
    here = Path(__file__).resolve().parent
    scene = json.loads((here / "factory.scene.json").read_text(encoding="utf-8"))
    doc = parse_edn((here / "building.edn").read_text(encoding="utf-8"))
    steps = parse_edn((here / "construction.edn").read_text(encoding="utf-8"))["proc/steps"]
    robots = parse_edn((here / "robots.edn").read_text(encoding="utf-8"))["robot/registry"]
    res = run_engineering(scene, doc["bom/parts"], doc["bom/meta"], steps, robots)
    rep = res["report"]
    (here / "engineering.json").write_text(
        json.dumps(rep, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    # compact clash list for the 3-D viewer
    (here / "clashes.json").write_text(
        json.dumps({"of": rep["of"], "clashes": res["clashes"]}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    cl = rep["clashes"]
    print(f"clashes={cl['count']} (hard={cl['hard']} coordination={cl['coordination']})")
    for s in rep["sizing"]:
        print(f"sizing[{s['discipline']}] = {s['verdict']}")
        for c in s["checks"]:
            print(f"   - {c}")
    for r in rep["code_checks"]["rows"]:
        print(f"code[{r['rule']}] {r['value']} ({r['limit']}) → {r['verdict']}")
    for b in rep["buildability"]:
        print(f"build[{b['step']}] {b['robot']} zone={b['zone_m']}m setups={b['setups']} "
              f"robots={b['robots_needed']} → {b['verdict']}")
    print("wrote engineering.json + clashes.json", file=sys.stderr)


if __name__ == "__main__":
    main()
