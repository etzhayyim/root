#!/usr/bin/env python3
"""kotoba_local — an in-memory EAVT/AVET reference store for the maps spatial substrate.

ADR-2606064500 §2. This is NOT the production kotoba engine — it is a small, dependency-free
REFERENCE implementation of the two arrangements the maps read hot-path relies on, so the
H3-cell-as-Datom + AVET design can be EXECUTED and TESTED offline (no live kotoba endpoint),
and so it documents the exact query contract `src/kotoba-spatial.ts` issues to real kotoba.

It ingests `kg.ingest_batch`-shaped entities (the output of methods/ingest.py /
buildIngestBatch) and answers `query_by_cells(...)` exactly as the TS adapter does:

    for each requested cell C at res = lod:
        subjects ← AVET( :feature.cell/r{lod} , C )      # one index probe
        keep subjects whose :feature/label ∈ labels      # ∩ AVET( :feature/label , … )
        materialize the feature row

Parity with the production path is the point: if this returns the right features for a cell,
the production AVET query returns the right features for that cell.

stdlib only.
"""
from __future__ import annotations
from collections import defaultdict


class KotobaLocal:
    def __init__(self):
        # EAVT: subject -> {pred -> [values]}
        self.eavt: dict[str, dict[str, list]] = {}
        # AVET: (pred, object) -> set(subjects)   — the spatial index when pred is a cell attr
        self.avet: dict[tuple[str, str], set[str]] = defaultdict(set)

    def ingest_batch(self, batch: dict) -> int:
        """Ingest a kg.ingest_batch body: {"entities": [{id, claims:[{pred,value}], ...}]}."""
        n = 0
        for ent in batch.get("entities", []):
            sid = ent.get("id")
            if not sid:
                continue
            attrs = self.eavt.setdefault(sid, {})
            for c in ent.get("claims", []):
                pred, val = c.get("pred"), c.get("value")
                if pred is None or val is None:
                    continue
                attrs.setdefault(pred, []).append(val)
                self.avet[(pred, str(val))].add(sid)
            n += 1
        return n

    def _first(self, sid: str, pred: str):
        vals = self.eavt.get(sid, {}).get(pred)
        return vals[0] if vals else None

    def query_by_cells(self, cells, lod: int, labels=None, limit: int = 500):
        """The getChunk hot-path (§2), as AVET probes. Returns rows grouped by owning cell:
        { cell: { label_keyword: [ {id, label, name, lat, lon, ...}, ... ] } }."""
        cell_pred = f"feature.cell/r{int(lod)}"
        label_set = None
        if labels:
            label_set = {l if str(l).startswith(":") else f":{l}" for l in labels}
        out: dict[str, dict[str, list]] = {}
        for cell in cells:
            subjects = self.avet.get((cell_pred, str(cell)), set())  # AVET probe — the index
            bucket = out.setdefault(cell, {})
            for sid in subjects:
                lab = self._first(sid, "feature/label")
                if label_set is not None and lab not in label_set:
                    continue
                lst = bucket.setdefault(lab, [])
                if len(lst) >= limit:
                    continue
                lst.append(self._materialize(sid))
        return out

    def _materialize(self, sid: str) -> dict:
        a = self.eavt.get(sid, {})
        row = {"id": sid}
        for pred in ("feature/label", "feature/name", "feature/display-name",
                     "feature/category", "feature/status", "feature/source-did",
                     "feature/lat", "feature/lon", "feature/height-m", "feature/levels",
                     "feature/geometry"):
            v = a.get(pred)
            if v:
                key = pred.split("/", 1)[1]
                row[key] = v[0]
        return row

    def avet_query(self, predicate: str, objects, filter_pred=None, filter_in=None,
                   limit: int = 500) -> list[dict]:
        """The wire-level AVET query the TS adapter (kotoba-spatial.ts queryByCells) issues:
        probe AVET(predicate, obj) for each obj, optionally ∩ AVET(filter_pred, v) for v in
        filter_in, and return matching subjects as entity dicts {id, claims:[{pred,value}]}.
        This is what a real kotoba graph.sparql endpoint returns; the adapter re-materializes."""
        allow = set(filter_in) if filter_in else None
        seen: set[str] = set()
        out: list[dict] = []
        for obj in objects:
            for sid in self.avet.get((predicate, str(obj)), set()):
                if sid in seen:
                    continue
                if allow is not None and self._first(sid, filter_pred) not in allow:
                    continue
                seen.add(sid)
                claims = [{"pred": p, "value": v} for p, vs in self.eavt.get(sid, {}).items() for v in vs]
                out.append({"id": sid, "claims": claims})
                if len(out) >= limit:
                    return out
        return out

    def entity(self, sid: str) -> dict | None:
        a = self.eavt.get(sid)
        if not a:
            return None
        return {"id": sid, "claims": [{"pred": p, "value": v} for p, vs in a.items() for v in vs]}

    # ── introspection (for tests / coverage) ──
    def feature_count(self) -> int:
        return sum(1 for s, a in self.eavt.items() if "feature/label" in a)

    def cells_at_res(self, res: int) -> set[str]:
        pred = f"feature.cell/r{int(res)}"
        return {obj for (p, obj) in self.avet if p == pred}
