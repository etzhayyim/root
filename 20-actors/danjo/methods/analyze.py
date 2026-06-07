#!/usr/bin/env python3
"""danjo 弾正 — non-adjudicating discrepancy-observation analyzer (R0/R1, offline).

ADR-2605301600. Runs the OPEN detector heuristics in the method-pack (v1-jp-seed.json)
over a PUBLIC procurement corpus and emits danjo.discrepancyObservation records — FACTUAL
cross-reference patterns over the public record, NEVER a finding of wrongdoing.

The censor's EYE, never the censor's SWORD. Every observation, by construction:
  G4 — nonAdjudicatingNotice = true (no verdict / guilt / wrongdoing field is representable);
  G5 — sourceRecordCids ≥ 2 (a primary-public-record citation is mandatory);
  G6 — methodNoteCid present (the public audits the open detector, not only its output);
  G4 — carries the method's knownFalsePositiveModes (why a hit is NOT, by itself, evidence
       of a crime / 不正). Legal characterization, if ever sought, routes to external
       counsel via chigiri + Public Fund — never inside danjo.

This R0/R1 implements the `single-bidder-streak` detector concretely; the other six method
notes are carried as metadata (their detectors land in later R-cycles). Live ingest of real
pinned gov.dataset.* records and named-party publication are G3/G10-gated.

stdlib only. Usage:  python3 analyze.py [--corpus FILE] [--methods FILE] [--out OUTDIR]
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys

_HERE = pathlib.Path(__file__).resolve().parent.parent
_CORPUS = _HERE / "data" / "corpus.seed.json"
_METHODS = _HERE / "methods" / "v1-jp-seed.json"

# fields that would make an observation a VERDICT — must NEVER appear (G4, structural).
_FORBIDDEN_VERDICT_FIELDS = ("verdict", "guilt", "guilty", "wrongdoing", "finding",
                             "culprit", "illegal", "crime", "sanction")


def load_json(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def method_cid(method: dict) -> str:
    """Deterministic content id for an open method note (G6 reference)."""
    blob = json.dumps(method, sort_keys=True, separators=(",", ":")).encode()
    return "method:" + method.get("methodId", "?") + ":" + hashlib.sha256(blob).hexdigest()[:12]


def _months_between(d1: str, d2: str) -> int:
    y1, m1 = int(d1[:4]), int(d1[5:7])
    y2, m2 = int(d2[:4]), int(d2[5:7])
    return abs((y2 - y1) * 12 + (m2 - m1))


def detect_single_bidder_streak(records: list[dict], params: dict) -> list[dict]:
    """Find (authority, awardee) pairs with ≥minConsecutive consecutive single-bid awards
    inside a rolling windowMonths. Returns hit dicts {authority, awardee, cids, count}.
    A FACT about the public record — single-bid procurement is lawful (see false positives)."""
    min_consec = int(params.get("minConsecutive", 5))
    window = int(params.get("windowMonths", 24))
    require_flag = bool(params.get("requireSingleBidFlag", True))

    by_pair: dict[tuple, list[dict]] = {}
    for r in records:
        key = (r.get("contractingAuthority"), r.get("awardeeLei"))
        by_pair.setdefault(key, []).append(r)

    hits: list[dict] = []
    for (auth, awardee), recs in by_pair.items():
        recs = sorted(recs, key=lambda x: x.get("awardDate", ""))
        run: list[dict] = []

        def _flush(run_recs: list[dict]) -> None:
            if len(run_recs) >= min_consec:
                if _months_between(run_recs[0]["awardDate"], run_recs[-1]["awardDate"]) <= window:
                    hits.append({"authority": auth, "awardee": awardee,
                                 "cids": [r["cid"] for r in run_recs], "count": len(run_recs)})

        for r in recs:
            is_single = (r.get("bidCount") == 1) and (r.get("singleBidFlag", False) if require_flag else True)
            if is_single:
                run.append(r)
            else:
                _flush(run)
                run = []
        _flush(run)
    return hits


def build_observation(hit: dict, method: dict) -> dict:
    """Assemble a danjo.discrepancyObservation. RAISES if the structural invariants
    (≥2 source cids, method ref present) are not met — non-adjudication is structural."""
    cids = hit["cids"]
    if len(cids) < 2:
        raise ValueError("G5: discrepancyObservation requires ≥2 sourceRecordCids")
    mcid = method_cid(method)
    if not mcid:
        raise ValueError("G6: discrepancyObservation requires a methodNoteCid")
    obs = {
        "type": "danjo.discrepancyObservation",
        "category": method.get("appliesToCategory", method.get("methodId")),
        "nonAdjudicatingNotice": True,                       # G4 — always, never a verdict
        "observedPattern": (f"{hit['count']} consecutive single-bid awards from "
                            f"{hit['authority']} to {hit['awardee']} within the method window"),
        "sourceRecordCids": cids,                            # G5 — ≥2
        "methodNoteCid": mcid,                               # G6
        "knownFalsePositiveModes": method.get("knownFalsePositiveModes", []),  # G4 honesty
        "sourcing": ":representative",
    }
    # G4 structural self-check: no verdict field may have crept in.
    for k in obs:
        assert not any(b in k.lower() for b in _FORBIDDEN_VERDICT_FIELDS), \
            f"G4: verdict field {k!r} is unrepresentable in a discrepancyObservation"
    return obs


def run_all(corpus: dict, methodpack: dict) -> list[dict]:
    """Run every IMPLEMENTED detector over the corpus. (R0/R1: single-bidder-streak.)"""
    records = corpus.get("procurementRecords", [])
    by_id = {m["methodId"]: m for m in methodpack.get("methods", [])}
    observations: list[dict] = []
    if "single-bidder-streak" in by_id:
        m = by_id["single-bidder-streak"]
        params = json.loads(m.get("thresholdParams", "{}"))
        for hit in detect_single_bidder_streak(records, params):
            observations.append(build_observation(hit, m))
    return observations


def render_edn(observations: list[dict]) -> str:
    L = [";; danjo-observations.kotoba.edn — danjo.discrepancyObservation records.",
         ";; G4 nonAdjudicatingNotice=true (FACT, never a verdict) · G5 ≥2 sourceRecordCids",
         ";; · G6 methodNoteCid. The censor's EYE, never the SWORD. Named-party publication",
         ";; G10 + 1 SBT=1 vote gated. DERIVED :representative. ADR-2605301600.", "", "["]
    for o in observations:
        cids = " ".join(f'"{c}"' for c in o["sourceRecordCids"])
        L.append(
            f' {{:danjo.obs/category :{o["category"]} :danjo.obs/non-adjudicating true '
            f':danjo.obs/pattern "{o["observedPattern"]}" '
            f':danjo.obs/source-record-cids [{cids}] '
            f':danjo.obs/method-note-cid "{o["methodNoteCid"]}" '
            f':danjo.obs/sourcing :representative}}')
    L.append("]")
    return "\n".join(L) + "\n"


def main(argv: list[str]) -> int:
    corpus = load_json(pathlib.Path(argv[argv.index("--corpus") + 1]) if "--corpus" in argv else _CORPUS)
    methods = load_json(pathlib.Path(argv[argv.index("--methods") + 1]) if "--methods" in argv else _METHODS)
    obs = run_all(corpus, methods)
    if "--out" in argv:
        outdir = pathlib.Path(argv[argv.index("--out") + 1])
        outdir.mkdir(parents=True, exist_ok=True)
        (outdir / "danjo-observations.kotoba.edn").write_text(render_edn(obs))
    print(f"danjo: {len(corpus.get('procurementRecords', []))} procurement records, "
          f"{len(methods.get('methods', []))} open methods → {len(obs)} discrepancy observation(s)")
    for o in obs:
        print(f"  [{o['category']}] {o['observedPattern']} "
              f"({len(o['sourceRecordCids'])} sources, non-adjudicating)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
