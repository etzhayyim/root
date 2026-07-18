#!/usr/bin/env python3
"""tsutae-factory-r0 — production line expansion (生産工程 → 製造op + 4D order).

`production.edn` is the SSoT for HOW a 伝え handheld is MADE: the ordered line stations a
body flows through. This tool validates it against the scene (every :station/cell
is a real scene cell or loader; every :station/consumes is a real building part)
and emits:

  - production.order.json   — flat ordered station list (seq / op / x / y / cell /
                              cycle_s / layer / name), consumed by the kami-app
                              `run_tsutae_factory_produce_v1` entry.
  - production_ingest.json  — kotoba EAVT datoms: one prod/* entity per station,
                              plus one mfgop/* entity per manufacturing operation
                              (供給→搬送→加工→検査→搬出) expanded from each station.

HONEST: this is an R0 production-flow PLAN (takt list + op graph), not a balanced
line / cycle-time study. It makes "how a handheld is made" executable-as-data and
drivable by the physics sim; it does not certify a real line can hold the takt.

Usage:  python3 production_gen.py [scene_dir]
"""
import json
import sys
from pathlib import Path


# station op → ordered manufacturing primitives (+ Japanese label).
# tsutae handheld line (ADR-2605261300): SMT → 筐体 → ディスプレイ → FW → QC → 梱包 → 認証 / EOL.
# Each station maps to one of the 8 tsutae Pregel cells (orgs/etzhayyim/com-etzhayyim-tsutae/cells).
_OP_STEPS = {
    "receive":   [("supply", "部品受入 (SoC/PMIC/PCB/受動)"), ("convey", "搬送 (ESDコンベア)")],
    "smt-print": [("supply", "PCB供給 + ペースト"), ("print", "ソルダーペースト印刷 (ステンシル)"),
                  ("inspect", "印刷検査 (SPI)"), ("convey", "次工程搬送")],
    "smt-place": [("supply", "部品供給 (フィーダ)"), ("place", "実装 pick-and-place (Tedama)"),
                  ("inspect", "実装後検査"), ("convey", "次工程搬送")],
    "reflow":    [("reflow", "リフローはんだ付け (N2 10ゾーン)"), ("cool", "冷却"),
                  ("convey", "次工程搬送")],
    "aoi":       [("aoi", "AOI光学検査 (Mimi)"), ("xray", "X線BGAボイド検査"),
                  ("gate", "G9 open-SoC ゲート判定"), ("convey", "次工程搬送")],
    "chassis":   [("supply", "筐体+電池+カメラ+モジュール供給"), ("fasten", "ねじ締結 (Otete)"),
                  ("gate", "G6 マイクKS + G3 修理性ゲート"), ("convey", "次工程搬送")],
    "display":   [("supply", "パネル+デジタイザ供給"), ("laminate", "貼合 ガスケットクリップ (Hitogata)"),
                  ("calib", "タッチ較正"), ("convey", "次工程搬送")],
    "firmware":  [("verify", "イメージ検証 (SHA-256, IPFS)"), ("flash", "書込 (open, unlock-default G2)"),
                  ("gate", "G7 blob比率ゲート"), ("convey", "次工程搬送")],
    "qc":        [("calib", "センサ較正"), ("rf", "RF適合 (cellular-off, G6)"),
                  ("ux", "G8 反依存UX監査"), ("func", "機能セルフテスト"), ("convey", "次工程搬送")],
    "pack":      [("manual", "日英 iFixit 手引同梱 (G5)"), ("pack", "梱包 molded-pulp (脱プラ)"),
                  ("seal", "封緘")],
    "attest":    [("lineage", "BoM系譜集約"), ("sign", "ロボ署名 witness>=2 (G4)"),
                  ("mint", "デバイスDID発行 (G14)")],
    "eol":       [("dismantle", "手工具解体 (非破壊)"), ("sort", "材料分別"),
                  ("route", "Al→kanayama / 電池→recycler (G10)")],
}

_DUR = {"supply": 4, "convey": 4, "print": 12, "place": 30, "inspect": 5, "reflow": 16,
        "cool": 4, "aoi": 8, "xray": 6, "gate": 2, "fasten": 18, "laminate": 14, "calib": 6,
        "verify": 4, "flash": 14, "rf": 8, "ux": 3, "func": 6, "manual": 4, "pack": 6,
        "seal": 2, "lineage": 4, "sign": 4, "mint": 3, "dismantle": 10, "sort": 6, "route": 4}


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
            "robot": cell if action in ("place", "fasten", "laminate", "aoi", "xray", "flash", "sign", "dismantle") else "",
            "materials": list(consumes) if action in ("supply", "verify", "manual") else [],
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
    return {"of": meta.get("prod/of", "tsutae-factory-r0"),
            "takt_s": meta.get("prod/takt-s", 0), "stations": rows}


def _camel(tail):
    parts = tail.split('-')
    return parts[0] + ''.join(w.capitalize() for w in parts[1:])


def entities(meta, stations):
    of = meta.get("prod/of", "tsutae-factory-r0")
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
        ents.append({"id": s["station/id"], "type": "TsutaeLineStation",
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
            ents.append({"id": o["id"], "type": "TsutaeMfgOp",
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
    n_ops = sum(1 for e in ents if e["type"] == "TsutaeMfgOp")

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
