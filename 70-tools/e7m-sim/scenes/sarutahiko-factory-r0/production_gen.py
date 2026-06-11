#!/usr/bin/env python3
"""sarutahiko-factory-r0 — production line expansion (生産工程 → 製造op + 4D order).

`production.edn` is the SSoT for HOW a truck is MADE: the ordered line stations a
body flows through. This tool validates it against the scene (every :station/cell
is a real scene cell or loader; every :station/consumes is a real building part)
and emits:

  - production.order.json   — flat ordered station list (seq / op / x / y / cell /
                              cycle_s / layer / name), consumed by the kami-app
                              `run_sarutahiko_factory_produce_v1` entry.
  - production_ingest.json  — kotoba EAVT datoms: one prod/* entity per station,
                              plus one mfgop/* entity per manufacturing operation
                              (供給→搬送→加工→検査→搬出) expanded from each station.

HONEST: this is an R0 production-flow PLAN (takt list + op graph), not a balanced
line / cycle-time study. It makes "how a truck is made" executable-as-data and
drivable by the physics sim; it does not certify a real line can hold the takt.

Usage:  python3 production_gen.py [scene_dir]
"""
import json
import sys
from pathlib import Path


# station op → ordered manufacturing primitives (+ Japanese label)
_OP_STEPS = {
    "receive":     [("supply", "部品供給 (受入)"), ("convey", "搬送 (コンベア)")],
    "frame-weld":  [("supply", "フレーム材供給"), ("weld", "MIG/MAG溶接 (arm6)"),
                    ("inspect", "溶接検査"), ("convey", "次工程搬送")],
    "cab-weld":    [("supply", "キャブパネル供給 (プレス)"), ("weld", "スポット溶接 (arm6)"),
                    ("inspect", "リーク検査"), ("convey", "次工程搬送")],
    "paint":       [("mask", "マスキング"), ("coat", "塗装 KTL→base→clear (arm6)"),
                    ("bake", "焼付乾燥"), ("convey", "次工程搬送")],
    "marriage":    [("supply", "パワートレイン合流 (L2)"), ("join", "結合 (gantry)"),
                    ("torque", "締結トルク witness>=2 (G4)"), ("convey", "次工程搬送")],
    "eol-test":    [("dyno", "ローラーダイナモ"), ("align", "アライメント (CMM)"),
                    ("emit", "排ガス計測 (G8)"), ("convey", "ステージング搬送")],
    "stage":       [("park", "完成車ステージング")],
    "ship":        [("pick", "完成車 跨ぎ持上げ (積込ロボット)"), ("carry", "運搬"),
                    ("lower", "carrier deck 着座"), ("ship", "出荷")],
}

_DUR = {"supply": 4, "convey": 6, "weld": 14, "inspect": 5, "mask": 6, "coat": 18,
        "bake": 12, "join": 16, "torque": 8, "dyno": 12, "align": 8, "emit": 6,
        "park": 4, "pick": 6, "carry": 8, "lower": 6, "ship": 4}


def station_ops(st):
    """Expand one line station into ordered manufacturing-op rows."""
    sid = st["station/id"]
    op = st.get("station/op", "")
    cell = st.get("station/cell", "")
    consumes = st.get("station/consumes", [])
    rows = []
    for k, (action, label) in enumerate(_OP_STEPS.get(op, [("work", "加工")]), start=1):
        rows.append({
            "id": f"mfgop:{sid}:{k:02d}", "station": sid, "seq": k,
            "action": action, "label": label,
            "robot": cell if action in ("weld", "coat", "join", "pick", "carry", "lower") else "",
            "materials": list(consumes) if action in ("supply", "mask") else [],
            "dur_s": _DUR.get(action, 8),
        })
    return rows


def order_json(meta, stations):
    rows = []
    for s in sorted(stations, key=lambda x: x["station/seq"]):
        rows.append({
            "seq": s["station/seq"],
            "id": s["station/id"],
            "name": s.get("station/name", s["station/id"]),
            "layer": s.get("station/layer", "—"),
            "op": s.get("station/op", ""),
            "x": float(s.get("station/x", 0)),
            "y": float(s.get("station/y", 0)),
            "cell": s.get("station/cell", ""),
            "cycle_s": float(s.get("station/cycle-s", 10)),
        })
    return {"of": meta.get("prod/of", "sarutahiko-factory-r0"),
            "takt_s": meta.get("prod/takt-s", 0), "stations": rows}


def _camel(tail):
    parts = tail.split('-')
    return parts[0] + ''.join(w.capitalize() for w in parts[1:])


def entities(meta, stations):
    of = meta.get("prod/of", "sarutahiko-factory-r0")
    ents = []
    for s in stations:
        claims = [{"pred": "prod/of", "value": of}]
        for k in ("station/seq", "station/layer", "station/op", "station/name",
                  "station/x", "station/y", "station/cycle-s"):
            if k in s and s[k] is not None:
                claims.append({"pred": f"station/{_camel(k.split('/', 1)[1])}", "value": str(s[k])})
        if s.get("station/cell"):
            claims.append({"pred": "station/cell", "value": s["station/cell"]})  # entity ref
        for c in s.get("station/consumes", []):
            claims.append({"pred": "station/consumes", "value": c})  # entity ref
        ents.append({"id": s["station/id"], "type": "SarutahikoLineStation",
                     "labelEn": s.get("station/name", s["station/id"]), "claims": claims})
        for o in station_ops(s):
            oc = [
                {"pred": "mfgop/of", "value": of},
                {"pred": "mfgop/station", "value": o["station"]},
                {"pred": "mfgop/seq", "value": str(o["seq"])},
                {"pred": "mfgop/action", "value": o["action"]},
                {"pred": "mfgop/label", "value": o["label"]},
                {"pred": "mfgop/durS", "value": str(o["dur_s"])},
            ]
            if o["robot"]:
                oc.append({"pred": "mfgop/robot", "value": o["robot"]})
            for m in o["materials"]:
                oc.append({"pred": "mfgop/material", "value": m})
            ents.append({"id": o["id"], "type": "SarutahikoMfgOp",
                         "labelEn": o["label"], "claims": oc})
    return ents


def main():
    from kotoba_gen import parse_edn
    here = Path(__file__).resolve().parent
    sdir = Path(sys.argv[1]) if len(sys.argv) > 1 else here

    prod = parse_edn((sdir / "production.edn").read_text(encoding="utf-8"))
    building = parse_edn((sdir / "building.edn").read_text(encoding="utf-8"))
    scene = json.loads((sdir / "factory.scene.json").read_text(encoding="utf-8"))
    meta, stations = prod["prod/meta"], prod["prod/stations"]

    # ── self-checks ───────────────────────────────────────────────────────────
    assert isinstance(stations, list) and stations, "no stations parsed"
    seqs = sorted(s["station/seq"] for s in stations)
    assert seqs == list(range(1, len(stations) + 1)), f"station seq not 1..N: {seqs}"
    part_ids = {p["part/id"] for p in building["bom/parts"]}
    cell_ids = {c["id"] for c in scene.get("cells", [])} | {l["id"] for l in scene.get("loaders", [])}
    for s in stations:
        for c in s.get("station/consumes", []):
            assert c in part_ids, f"{s['station/id']} consumes unknown part {c}"
        cell = s.get("station/cell")
        if cell:
            assert cell in cell_ids, f"{s['station/id']} unknown production robot {cell}"

    order = order_json(meta, stations)
    ents = entities(meta, stations)
    n_ops = sum(1 for e in ents if e["type"] == "SarutahikoMfgOp")

    (sdir / "production.order.json").write_text(
        json.dumps(order, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (sdir / "production_ingest.json").write_text(
        json.dumps({"entities": ents}, ensure_ascii=False) + "\n", encoding="utf-8")

    cycle = sum(float(s.get("station/cycle-s", 0)) for s in stations)
    print(f"stations={len(stations)}  mfg_ops={n_ops}  line_cycle_s={cycle}  "
          f"takt_s={meta.get('prod/takt-s')}")
    print(f"flow: {' → '.join(s['station/op'] for s in sorted(stations, key=lambda x: x['station/seq']))}")
    print(f"wrote production.order.json ({len(order['stations'])} stations) + "
          f"production_ingest.json ({len(ents)} entities)", file=sys.stderr)


if __name__ == "__main__":
    main()
