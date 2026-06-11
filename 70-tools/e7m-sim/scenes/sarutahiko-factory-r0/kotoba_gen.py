#!/usr/bin/env python3
"""sarutahiko-factory-r0 — generate SBOM + kotoba ingest + 4D order from the EDN SSoT.

Two Datomic-style EDN ledgers are the SSoT:
  - building.edn     — 建材 + 設備 (building materials + production equipment)
  - construction.edn — 建築手順 (4D construction sequence)

This tool parses them (with the same self-contained EDN reader used by the
giemon-kabitori `sbom_gen.py`) and emits:
  - factory.cdx.json        — CycloneDX 1.5 SBOM of the building + equipment
  - kotoba_ingest.json      — body for POST .../kg.ingest_batch: one entity per
                              building part (kg/claim/part/*) AND one per
                              construction step (kg/claim/step/*); step
                              depends-on / consumes are emitted as entity-ref
                              claims so the critical path is recoverable by VAET
                              reverse lookup (ADR-2605312345).
  - construction.order.json — flat ordered step list (seq / reveals / duration)
                              consumed by kami-app-sarutahiko-factory's 4D build
                              viewer (run_sarutahiko_factory_build_v1).

Cross-checks: seq is 1..N contiguous, depends-on is acyclic and references real
steps, every :step/consumes is a real building part, and every :step/reveals is
a real render-element id in factory.scene.json.

Usage:  python3 kotoba_gen.py [scene_dir]
"""
import json
import sys
from pathlib import Path


# ── minimal EDN reader (controlled subset: maps, vectors, keywords, strings,
#    ints, bool, nil; `;` line comments; `,` is whitespace) — same reader as
#    giemon_kabitori/sbom_gen.py ───────────────────────────────────────────────
class _EdnReader:
    def __init__(self, text):
        self.s = text
        self.i = 0
        self.n = len(text)

    def _err(self, msg):
        raise ValueError(f"edn parse error at {self.i}: {msg}")

    def _skip_ws(self):
        while self.i < self.n:
            c = self.s[self.i]
            if c == ';':  # line comment
                while self.i < self.n and self.s[self.i] != '\n':
                    self.i += 1
            elif c in ' \t\r\n,':
                self.i += 1
            else:
                break

    def read(self):
        self._skip_ws()
        if self.i >= self.n:
            self._err("unexpected EOF")
        c = self.s[self.i]
        if c == '{':
            return self._read_map()
        if c == '[':
            return self._read_vec()
        if c == '"':
            return self._read_str()
        if c == ':':
            return self._read_kw()
        return self._read_atom()

    def _read_map(self):
        self.i += 1  # {
        d = {}
        while True:
            self._skip_ws()
            if self.i >= self.n:
                self._err("unterminated map")
            if self.s[self.i] == '}':
                self.i += 1
                return d
            k = self.read()
            v = self.read()
            d[k] = v

    def _read_vec(self):
        self.i += 1  # [
        out = []
        while True:
            self._skip_ws()
            if self.i >= self.n:
                self._err("unterminated vector")
            if self.s[self.i] == ']':
                self.i += 1
                return out
            out.append(self.read())

    def _read_str(self):
        self.i += 1  # opening quote
        buf = []
        while self.i < self.n:
            c = self.s[self.i]
            if c == '\\':
                self.i += 1
                esc = self.s[self.i]
                buf.append({'n': '\n', 't': '\t', 'r': '\r'}.get(esc, esc))
            elif c == '"':
                self.i += 1
                return ''.join(buf)
            else:
                buf.append(c)
            self.i += 1
        self._err("unterminated string")

    def _read_kw(self):
        self.i += 1  # leading colon
        start = self.i
        while self.i < self.n and (self.s[self.i].isalnum() or self.s[self.i] in '/-.*_'):
            self.i += 1
        return self.s[start:self.i]  # keyword name without the colon

    def _read_atom(self):
        start = self.i
        while self.i < self.n and (self.s[self.i].isalnum() or self.s[self.i] in '-.+'):
            self.i += 1
        tok = self.s[start:self.i]
        if tok == 'true':
            return True
        if tok == 'false':
            return False
        if tok == 'nil':
            return None
        try:
            return int(tok)
        except ValueError:
            return tok


def parse_edn(text):
    return _EdnReader(text).read()


def _camel(tail):
    parts = tail.split('-')
    return parts[0] + ''.join(w.capitalize() for w in parts[1:])


def _claim_pred(k):
    # part/mass-kg -> part/massKg ; step/depends-on -> step/dependsOn
    head, tail = k.split('/', 1)
    return f"{head}/{_camel(tail)}"


# ── building.edn (建材 + 設備) → kotoba part entities + CycloneDX ───────────────
_PART_KEYS = [
    "part/group", "part/procurement", "part/manufacturer", "part/product",
    "part/mpn", "part/purl", "part/spec", "part/rating", "part/composition",
    "part/qty", "part/unit", "part/length-m", "part/area-m2", "part/mass-kg",
    "part/material", "part/sim-feature", "part/fab-process", "part/sourcing", "part/note",
]
# Procurement claims (調達もと/原産国/リードタイム/channel) are derived from
# procurement.py and appended at generation time (representative).
_PROC_KEYS = ["part/supplier", "part/origin", "part/leadTime", "part/channel"]


def part_entities(meta, parts):
    from procurement import enrich_part
    bom_of = meta.get("bom/of", "sarutahiko-factory-r0")
    out = []
    for p in parts:
        claims = [{"pred": "part/bom", "value": bom_of}]
        for k in _PART_KEYS:
            if k in p and p[k] is not None:
                claims.append({"pred": _claim_pred(k), "value": str(p[k])})
        # derived procurement layer (調達もと / 原産国 / リードタイム / channel)
        for k, v in enrich_part(p).items():
            claims.append({"pred": _claim_pred(k), "value": str(v)})
        out.append({
            "id": p["part/id"],
            "type": "SarutahikoFactoryPart",
            "labelEn": p.get("part/name", p["part/id"]),
            "claims": claims,
        })
    return out


def to_cyclonedx(meta, parts):
    from procurement import enrich_part
    components = []
    for p in parts:
        proc = enrich_part(p)
        props = [{"name": f"sarutahiko:{_claim_pred(k).replace('part/', '')}", "value": str(p[k])}
                 for k in _PART_KEYS if k in p and p[k] is not None]
        props += [{"name": f"sarutahiko:{_claim_pred(k).replace('part/', '')}", "value": str(v)}
                  for k, v in proc.items()]
        comp = {
            "type": "device",
            "bom-ref": p["part/id"],
            "name": p.get("part/name", p["part/id"]),
            "properties": props,
        }
        if p.get("part/manufacturer"):
            comp["publisher"] = p["part/manufacturer"]  # 企業名 (manufacturer)
        # CycloneDX supplier = 調達もと (distributor / 商社), distinct from publisher
        if proc.get("part/supplier"):
            comp["supplier"] = {"name": proc["part/supplier"]}
        elif p.get("part/manufacturer"):
            comp["supplier"] = {"name": p["part/manufacturer"]}
        if p.get("part/product"):
            comp["version"] = str(p["part/product"])  # 機器名/型番
        if p.get("part/purl"):
            comp["purl"] = p["part/purl"]
        components.append(comp)
    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "version": 1,
        "metadata": {
            "component": {
                "type": "device",
                "name": meta.get("bom/title", "Sarutahiko factory"),
                "version": meta.get("bom/revision", "v1"),
            },
            "properties": [
                {"name": "sarutahiko:bomOf", "value": meta.get("bom/of", "sarutahiko-factory-r0")},
                {"name": "sarutahiko:sourcing", "value": meta.get("bom/sourcing", "representative")},
                {"name": "sarutahiko:note", "value": meta.get("bom/note", "")},
            ],
        },
        "components": components,
    }


# ── construction.edn (建築手順) → kotoba step entities + flat 4D order ──────────
_STEP_SCALAR_KEYS = ["step/seq", "step/name", "step/trade", "step/zone", "step/duration-d"]


def step_entities(meta, steps):
    proc_of = meta.get("proc/of", "sarutahiko-factory-r0")
    out = []
    for s in steps:
        claims = [{"pred": "step/proc", "value": proc_of}]
        for k in _STEP_SCALAR_KEYS:
            if k in s and s[k] is not None:
                claims.append({"pred": _claim_pred(k), "value": str(s[k])})
        if s.get("step/robot"):
            claims.append({"pred": "step/robot", "value": s["step/robot"]})  # entity ref
        # entity-ref claims (resolved to Value::Cid on ingest, ADR-2605312345)
        for dep in s.get("step/depends-on", []):
            claims.append({"pred": "step/dependsOn", "value": dep})
        for c in s.get("step/consumes", []):
            claims.append({"pred": "step/consumes", "value": c})
        # render-target ids (kept as plain strings — render elements, not entities)
        for r in s.get("step/reveals", []):
            claims.append({"pred": "step/reveals", "value": r})
        out.append({
            "id": s["step/id"],
            "type": "SarutahikoFactoryStep",
            "labelEn": s.get("step/name", s["step/id"]),
            "claims": claims,
        })
    return out


def order_json(meta, steps):
    rows = []
    for s in sorted(steps, key=lambda x: x["step/seq"]):
        rows.append({
            "seq": s["step/seq"],
            "id": s["step/id"],
            "name": s.get("step/name", s["step/id"]),
            "trade": s.get("step/trade", ""),
            "robot": s.get("step/robot", ""),
            "zone": s.get("step/zone", "all"),
            "duration_d": s.get("step/duration-d", 0),
            "reveals": list(s.get("step/reveals", [])),
        })
    return {"of": meta.get("proc/of", "sarutahiko-factory-r0"), "steps": rows}


# ── robots.edn (施工ロボット registry) → kotoba entities + baked robots.json ───
_ROBOT_KEYS = ["robot/name", "robot/type", "robot/reach-m", "robot/base", "robot/cycle-min",
               "robot/mobile", "robot/process", "robot/maturity", "robot/sibling"]


def robot_entities(robots, of):
    out = []
    for r in robots:
        claims = [{"pred": "robot/of", "value": of}]
        for k in _ROBOT_KEYS:
            if k in r and r[k] is not None:
                claims.append({"pred": _claim_pred(k), "value": str(r[k])})
        out.append({"id": r["robot/id"], "type": "SarutahikoConstructionRobot",
                    "labelEn": r.get("robot/name", r["robot/id"]), "claims": claims})
    return out


def robots_json(robots):
    rows = []
    for r in robots:
        base = r.get("robot/base", [1.0, 1.0])
        rows.append({
            "id": r["robot/id"], "name": r.get("robot/name", r["robot/id"]),
            "type": r.get("robot/type", ""), "reach_m": float(r.get("robot/reach-m", 1.0)),
            "base": [float(base[0]), float(base[1])],
            "cycle_min": float(r.get("robot/cycle-min", 10)),
            "mobile": bool(r.get("robot/mobile", False)),
            "process": r.get("robot/process", "none"),
            "maturity": r.get("robot/maturity", "?"),
        })
    return {"robots": rows}


# ── render-element id universe (must match kami-app-sarutahiko-factory scene.rs) ────
# `ground` + `floor` are synthetic render elements built by the renderer, not
# entries in the scene arrays.
_SYNTHETIC_IDS = {"ground", "floor"}


def scene_element_ids(scene):
    ids = set(_SYNTHETIC_IDS)
    for key in (
        "walls", "columns", "beams", "zones", "machines", "conveyors", "cells", "agvs",
        "loaders",
        "service_nodes", "utilities", "fixtures",
        "site_pavements", "site_greens", "site_structures", "site_posts",
    ):
        for el in scene.get(key, []):
            ids.add(el["id"])
    return ids


def check_dag(steps):
    by_id = {s["step/id"]: s for s in steps}
    # contiguous seq 1..N
    seqs = sorted(s["step/seq"] for s in steps)
    assert seqs == list(range(1, len(steps) + 1)), f"step seq not contiguous 1..N: {seqs}"
    # depends-on references exist + acyclic (DFS)
    color = {}  # 0=unvisited,1=on-stack,2=done

    def dfs(sid):
        color[sid] = 1
        for dep in by_id[sid].get("step/depends-on", []):
            assert dep in by_id, f"{sid} depends-on unknown step {dep}"
            if color.get(dep, 0) == 1:
                raise AssertionError(f"dependency cycle through {dep}")
            if color.get(dep, 0) == 0:
                dfs(dep)
        color[sid] = 2

    for s in steps:
        if color.get(s["step/id"], 0) == 0:
            dfs(s["step/id"])


def main():
    here = Path(__file__).resolve().parent
    sdir = Path(sys.argv[1]) if len(sys.argv) > 1 else here

    building = parse_edn((sdir / "building.edn").read_text(encoding="utf-8"))
    construction = parse_edn((sdir / "construction.edn").read_text(encoding="utf-8"))
    robots_doc = parse_edn((sdir / "robots.edn").read_text(encoding="utf-8"))
    scene = json.loads((sdir / "factory.scene.json").read_text(encoding="utf-8"))

    b_meta, parts = building["bom/meta"], building["bom/parts"]
    p_meta, steps = construction["proc/meta"], construction["proc/steps"]
    robots = robots_doc["robot/registry"]

    # ── self-checks ───────────────────────────────────────────────────────────
    assert isinstance(parts, list) and len(parts) > 0, "no building parts parsed"
    assert isinstance(steps, list) and len(steps) > 0, "no construction steps parsed"
    for p in parts:
        for req in ("part/id", "part/name", "part/group", "part/procurement"):
            assert req in p, f"{p.get('part/id', '?')} missing {req}"
    part_ids = {p["part/id"] for p in parts}
    elem_ids = scene_element_ids(scene)

    robot_ids = {r["robot/id"] for r in robots}
    check_dag(steps)
    for s in steps:
        for c in s.get("step/consumes", []):
            assert c in part_ids, f"{s['step/id']} consumes unknown part {c}"
        for r in s.get("step/reveals", []):
            assert r in elem_ids, f"{s['step/id']} reveals unknown render id {r}"
        if s.get("step/robot"):
            assert s["step/robot"] in robot_ids, \
                f"{s['step/id']} assigns unknown robot {s['step/robot']}"

    n_cots = sum(1 for p in parts if p["part/procurement"] == "cots")
    n_fab = sum(1 for p in parts if p["part/procurement"] == "custom-fab")
    groups = sorted({p["part/group"] for p in parts})

    # ── robotics process expansion (建築手順 → robot op sequences) ─────────────
    import process_gen
    proc = process_gen.run_process(steps, parts, robots)
    (sdir / "process.json").write_text(
        json.dumps({"of": b_meta.get("bom/of", "sarutahiko-factory-r0"), "ops": proc["ops"]},
                   ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    step_id_set = {s["step/id"] for s in steps}
    for o in proc["ops"]:
        assert o["step"] in step_id_set, f"op {o['id']} references unknown step {o['step']}"
        for m in o["materials"]:
            assert m in part_ids, f"op {o['id']} references unknown material {m}"

    # ── engineering passes (clash / sizing / code / buildability) + IFC ────────
    import engineering
    import ifc_export
    eng = engineering.run_engineering(scene, parts, b_meta, steps, robots)
    (sdir / "engineering.json").write_text(
        json.dumps(eng["report"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (sdir / "clashes.json").write_text(
        json.dumps({"of": eng["report"]["of"], "clashes": eng["clashes"]},
                   ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (sdir / "robots.json").write_text(
        json.dumps(robots_json(robots), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    ifc_stats = ifc_export.export_ifc(scene, parts, sdir / "factory.ifc")

    # ── emit ──────────────────────────────────────────────────────────────────
    cdx = to_cyclonedx(b_meta, parts)
    ingest = {"entities": part_entities(b_meta, parts)
              + step_entities(p_meta, steps)
              + robot_entities(robots, b_meta.get("bom/of", "sarutahiko-factory-r0"))
              + proc["entities"]            # robot op-sequence datoms (op/*)
              + eng["entities"]}  # + clash/sizing/code/buildability datoms
    order = order_json(p_meta, steps)

    (sdir / "factory.cdx.json").write_text(
        json.dumps(cdx, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (sdir / "kotoba_ingest.json").write_text(
        json.dumps(ingest, ensure_ascii=False) + "\n", encoding="utf-8")
    (sdir / "construction.order.json").write_text(
        json.dumps(order, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    total_days = sum(s.get("step/duration-d", 0) for s in steps)
    cl = eng["report"]["clashes"]
    sized = {s["discipline"]: s["verdict"] for s in eng["report"]["sizing"]}
    code_ng = [r["rule"] for r in eng["report"]["code_checks"]["rows"] if r["verdict"] != "OK"]
    build_ng = [b["step"] for b in eng["report"]["buildability"] if b["verdict"] != "OK"]
    print(f"building parts={len(parts)}  cots={n_cots}  custom-fab={n_fab}  groups={groups}")
    print(f"construction steps={len(steps)}  robots={len(robots)}  "
          f"nominal_programme_days={total_days}")
    print(f"clashes={cl['count']} (hard={cl['hard']} coord={cl['coordination']})  "
          f"sizing={sized}  code_NG={code_ng}  buildability_NG={build_ng}")
    print(f"robot ops={len(proc['ops'])} (調達→搬入→搬送→建方→締結→検査)")
    print(f"wrote factory.cdx.json ({len(cdx['components'])} components)")
    print(f"wrote kotoba_ingest.json ({len(ingest['entities'])} entities)")
    print(f"wrote construction.order.json ({len(order['steps'])} steps)")
    print(f"wrote engineering.json + clashes.json + robots.json + factory.ifc "
          f"({ifc_stats['entities']} STEP entities, {ifc_stats['elements']} elements)")


if __name__ == "__main__":
    main()
