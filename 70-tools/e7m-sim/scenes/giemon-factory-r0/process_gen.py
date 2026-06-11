#!/usr/bin/env python3
"""giemon-factory-r0 — robotics process expansion (建築手順 → ロボット操作列).

The 4D `construction.edn` says WHAT is built in WHAT order. This module says HOW
each step is executed as a ROBOTICS PROCEDURE — decomposing every construction
step into an ordered sequence of robot operations covering the whole flow:

  procure (調達) → deliver (搬入) → stage/AGV (搬送・仮置き)
    → build (建方/据付/敷設/打設/塗装/植栽)  → fasten (締結/溶接/養生)
    → inspect (検査 scan-to-BIM)

Each op records the robot, the materials drawn (→ building.edn part + 調達もと from
procurement.py), the logistics from→to, the material process, and a nominal
duration. Emits `process.json` (consumed by kami-app-tatekata to drive the
op-phase animation) + `op/*` kotoba datoms (the executable robot task graph).

HONEST: this is an R0 robotic process PLAN (task graph), not a validated motion
plan / cycle-time study / safety case. It makes the build executable-as-data;
it does not certify that a real robot fleet can perform it unattended.
"""
import json
import sys
from pathlib import Path


# trade → primary build-action primitive (+ Japanese label)
_BUILD_ACTION = {
    "earthworks": ("grade", "造成・転圧"),
    "utility-service": ("connect", "引込接続"),
    "underground-mep": ("route", "埋設敷設"),
    "concrete": ("pour", "打設・均し"),
    "steel-erection": ("erect", "建方・位置決め"),
    "roofing": ("place", "屋根葺き"),
    "cladding": ("place", "パネル設置"),
    "interior": ("place", "間仕切り設置"),
    "electrical": ("route", "配線・敷設"),
    "mechanical": ("route", "配管・敷設"),
    "finishes": ("coat", "塗装・仕上げ"),
    "plumbing": ("install", "衛生器具据付"),
    "fire-protection": ("route", "消火配管・機器"),
    "machine-install": ("install", "機械据付・芯出し"),
    "material-handling": ("install", "コンベア敷設"),
    "robotics": ("install", "ロボットセル据付"),
    "civil-paving": ("pave", "舗装"),
    "civil-finishes": ("mark", "区画線・動線"),
    "site-electrical": ("place", "外灯・フェンス設置"),
    "landscape": ("plant", "植栽・サイン"),
    "commissioning": ("test", "試運転・通電通水"),
}

# whether the trade needs a discrete fastening/joining op after placement
_FASTEN = {
    "steel-erection": ("weld", "溶接・本締め"),
    "roofing": ("fix", "防水・固定"),
    "cladding": ("fix", "ファスナ固定"),
    "interior": ("fix", "ビス固定"),
    "concrete": ("cure", "養生"),
    "machine-install": ("anchor", "アンカー固定"),
    "material-handling": ("anchor", "据付固定"),
    "robotics": ("anchor", "ベース固定"),
    "civil-paving": ("compact", "転圧・締固め"),
}

# nominal op durations (minutes) for pacing the animation (NOT a cycle study)
_DUR = {"procure": 5, "deliver": 8, "stage": 6, "build": 18, "fasten": 10, "inspect": 6}

_STAGING = "受入 (zone_recv)"


def _supplier_of(parts_by_id, consumes):
    """Pick a representative 調達もと + max lead time over the consumed materials."""
    from procurement import enrich_part
    if not consumes:
        return "—", "—"
    leads = []
    sup = None
    for pid in consumes:
        p = parts_by_id.get(pid)
        if not p:
            continue
        e = enrich_part(p)
        if sup is None:
            sup = e.get("part/supplier", "")
        leads.append(e.get("part/leadTime", ""))
    multi = "（他）" if len(consumes) > 1 else ""
    return (sup or "要選定") + multi, (max(leads, default="—") if leads else "—")


def step_ops(step, parts_by_id, robot_process):
    """Expand one construction step into an ordered robot-operation list."""
    sid = step["step/id"]
    robot = step.get("step/robot", "")
    trade = step.get("step/trade", "")
    zone = step.get("step/zone", "all")
    consumes = step.get("step/consumes", [])
    proc = robot_process.get(robot, "none")
    supplier, lead = _supplier_of(parts_by_id, consumes)
    mat_label = (parts_by_id.get(consumes[0], {}).get("part/name", consumes[0])
                 if consumes else "—")
    if len(consumes) > 1:
        mat_label += f" 他{len(consumes) - 1}点"

    ops = []
    n = [0]

    def add(action, label, robot_id, frm, to, dur, process="none", lead_w=None):
        n[0] += 1
        ops.append({
            "id": f"op:{sid}:{n[0]:02d}", "step": sid, "seq": n[0],
            "action": action, "label": label, "robot": robot_id,
            "materials": list(consumes), "supplier": supplier,
            "from": frm, "to": to, "dur_min": dur, "process": process,
            "lead_weeks": lead_w,
        })

    # 1. 調達 (procure) — order from 調達もと
    add("procure", f"調達: {mat_label}", "(発注)", supplier, "工場ゲート",
        _DUR["procure"], lead_w=lead)
    # 2. 搬入 (deliver) — autonomous truck to receiving
    add("deliver", "搬入 (自律トラック)", "robot:doboku", "工場ゲート", _STAGING, _DUR["deliver"])
    # 3. 搬送 (stage) — AGV stages to the work zone
    add("stage", "搬送・仮置き (AGV)", "robot:fitout", _STAGING, zone, _DUR["stage"])
    # 4. 建方/据付/敷設 (build)
    act, alabel = _BUILD_ACTION.get(trade, ("place", "据付"))
    add(act, alabel, robot, zone, zone, _DUR["build"], process=proc)
    # 5. 締結/溶接/養生 (fasten) — when the trade needs it
    if trade in _FASTEN:
        fa, flabel = _FASTEN[trade]
        add(fa, flabel, robot, zone, zone, _DUR["fasten"], process=proc)
    # 6. 検査 (inspect) — scan-to-BIM verify
    add("inspect", "検査 (scan-to-BIM)", "robot:fitout", zone, zone, _DUR["inspect"])
    return ops


def run_process(steps, parts, robots):
    parts_by_id = {p["part/id"]: p for p in parts}
    robot_process = {r["robot/id"]: r.get("robot/process", "none") for r in robots}
    all_ops = []
    for s in steps:
        all_ops.extend(step_ops(s, parts_by_id, robot_process))
    # entities
    ents = []
    for o in all_ops:
        claims = [
            {"pred": "op/of", "value": "giemon-factory-r0"},
            {"pred": "op/step", "value": o["step"]},
            {"pred": "op/seq", "value": str(o["seq"])},
            {"pred": "op/action", "value": o["action"]},
            {"pred": "op/label", "value": o["label"]},
            {"pred": "op/robot", "value": o["robot"]},
            {"pred": "op/from", "value": o["from"]},
            {"pred": "op/to", "value": o["to"]},
            {"pred": "op/durMin", "value": str(o["dur_min"])},
            {"pred": "op/process", "value": o["process"]},
            {"pred": "op/supplier", "value": o["supplier"]},
        ]
        if o.get("lead_weeks"):
            claims.append({"pred": "op/leadTime", "value": str(o["lead_weeks"])})
        for m in o["materials"]:
            claims.append({"pred": "op/material", "value": m})  # entity ref
        ents.append({"id": o["id"], "type": "GiemonRobotOp", "labelEn": o["label"], "claims": claims})
    return {"ops": all_ops, "entities": ents}


def main():
    from kotoba_gen import parse_edn
    here = Path(__file__).resolve().parent
    steps = parse_edn((here / "construction.edn").read_text(encoding="utf-8"))["proc/steps"]
    parts = parse_edn((here / "building.edn").read_text(encoding="utf-8"))["bom/parts"]
    robots = parse_edn((here / "robots.edn").read_text(encoding="utf-8"))["robot/registry"]
    res = run_process(steps, parts, robots)
    (here / "process.json").write_text(
        json.dumps({"of": "giemon-factory-r0", "ops": res["ops"]}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    from collections import Counter
    acts = Counter(o["action"] for o in res["ops"])
    print(f"ops={len(res['ops'])} over {len(steps)} steps")
    print(f"actions={dict(acts)}")
    print("wrote process.json", file=sys.stderr)


if __name__ == "__main__":
    main()
