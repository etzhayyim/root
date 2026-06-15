;; ported from /Users/junkawasaki/github/com-junkawasaki/orgs/etzhayyim/root/20-actors/danjo/methods/analyze.py (unit_refactor stage 0)
;; danjo 弾正 — non-adjudicating discrepancy-observation analyzer (R0/R1, offline).
(ns root.danjo.methods.analyze
  (:require [clojure.string :as str]
            [clojure.set :as set]
            [clojure.edn :as edn]))

(declare here load-json method-cid months-between detect-single-bidder-streak build-observation run-all render-edn main)

;; TODO: port-failed unit _HERE (assembled-lint error)
;; _HERE = pathlib.Path(__file__).resolve().parent.parent
;; _CORPUS = _HERE / "data" / "corpus.seed.json"
;; _METHODS = _HERE / "methods" / "v1-jp-seed.json"
;; _FORBIDDEN_VERDICT_FIELDS = ("verdict", "guilt", "guilty", "wrongdoing", "finding",
;;                              "culprit", "illegal", "crime", "sanction")
(def here nil) ;; TODO: port-failed const

;; TODO: port-failed unit load_json (bb-compile error)
;; def load_json(path: pathlib.Path) -> dict:
;;     return json.loads(path.read_text(encoding="utf-8"))
(defn load-json [& _]
  (throw (ex-info "TODO: port-failed" {:from "load_json"})))

(defn method-cid [method]
  (throw (ex-info "TODO: port" {:from "method_cid"})))

;; TODO: port-failed unit _months_between (assembled-lint error)
;; def _months_between(d1: str, d2: str) -> int:
;;     y1, m1 = int(d1[:4]), int(d1[5:7])
;;     y2, m2 = int(d2[:4]), int(d2[5:7])
;;     return abs((y2 - y1) * 12 + (m2 - m1))
(defn months-between [& _]
  (throw (ex-info "TODO: port-failed" {:from "_months_between"})))

;; TODO: port-failed unit detect_single_bidder_streak (levi: timed out)
;; def detect_single_bidder_streak(records: list[dict], params: dict) -> list[dict]:
;;     """Find (authority, awardee) pairs with ≥minConsecutive consecutive single-bid awards
;;     inside a rolling windowMonths. Returns hit dicts {authority, awardee, cids, count}.
;;     A FACT about the public record — single-bid procurement is lawful (see false positives)."""
;;     min_consec = int(params.get("minConsecutive", 5))
;;     window = int(params.get("windowMonths", 24))
;;     require_flag = bool(params.get("requireSingleBidFlag", True))
;; 
;;     by_pair: dict[tuple, list[dict]] = {}
;;     for r in records:
;;         key = (r.get("contractingAuthority"), r.get("awardeeLei"))
;;         by_pair.setdefault(key, []).append(r)
;; 
;;     hits: list[dict] = []
;;     for (auth, awardee), recs in by_pair.items():
;;         recs = sorted(recs, key=lambda x: x.get("awardDate", ""))
;;         run: list[dict] = []
;; 
;;         def _flush(run_recs: list[dict]) -> None:
;;             if len(run_recs) >= min_consec:
;;                 if _months_between(run_recs[0]["awardDate"], run_recs[-1]["awardDate"]) <= window:
;;                     hits.append({"authority": auth, "awardee": awardee,
;;                                  "cids": [r["cid"] for r in run_recs], "count": len(run_recs)})
;; 
;;         for r in recs:
;;             is_single = (r.get("bidCount") == 1) and (r.get("singleBidFlag", False) if require_flag else True)
;;             if is_single:
;;                 run.append(r)
;;             else:
;;                 _flush(run)
;;                 run = []
;;         _flush(run)
;;     return hits
(defn detect-single-bidder-streak [& _]
  (throw (ex-info "TODO: port-failed" {:from "detect_single_bidder_streak"})))

;; TODO: port-failed unit build_observation (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmpeg_2uuzh/scratch.clj:9:14: e)
;; def build_observation(hit: dict, method: dict) -> dict:
;;     """Assemble a danjo.discrepancyObservation. RAISES if the structural invariants
;;     (≥2 source cids, method ref present) are not met — non-adjudication is structural."""
;;     cids = hit["cids"]
;;     if len(cids) < 2:
;;         raise ValueError("G5: discrepancyObservation requires ≥2 sourceRecordCids")
;;     mcid = method_cid(method)
;;     if not mcid:
;;         raise ValueError("G6: discrepancyObservation requires a methodNoteCid")
;;     obs = {
;;         "type": "danjo.discrepancyObservation",
;;         "category": method.get("appliesToCategory", method.get("methodId")),
;;         "nonAdjudicatingNotice": True,                       # G4 — always, never a verdict
;;         "observedPattern": (f"{hit['count']} consecutive single-bid awards from "
;;                             f"{hit['authority']} to {hit['awardee']} within the method window"),
;;         "sourceRecordCids": cids,                            # G5 — ≥2
;;         "methodNoteCid": mcid,                               # G6
;;         "knownFalsePositiveModes": method.get("knownFalsePositiveModes", []),  # G4 honesty
;;         "sourcing": ":representative",
;;     }
;;     # G4 structural self-check: no verdict field may have crept in.
;;     for k in obs:
;;         assert not any(b in k.lower() for b in _FORBIDDEN_VERDICT_FIELDS), \
;;             f"G4: verdict field {k!r} is unrepresentable in a discrepancyObservation"
;;     return obs
(defn build-observation [& _]
  (throw (ex-info "TODO: port-failed" {:from "build_observation"})))

;; TODO: port-failed unit run_all (bb-compile error)
;; def run_all(corpus: dict, methodpack: dict) -> list[dict]:
;;     """Run every IMPLEMENTED detector over the corpus. (R0/R1: single-bidder-streak.)"""
;;     records = corpus.get("procurementRecords", [])
;;     by_id = {m["methodId"]: m for m in methodpack.get("methods", [])}
;;     observations: list[dict] = []
;;     if "single-bidder-streak" in by_id:
;;         m = by_id["single-bidder-streak"]
;;         params = json.loads(m.get("thresholdParams", "{}"))
;;         for hit in detect_single_bidder_streak(records, params):
;;             observations.append(build_observation(hit, m))
;;     return observations
(defn run-all [& _]
  (throw (ex-info "TODO: port-failed" {:from "run_all"})))

;; TODO: port-failed unit render_edn (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmps9zh62y0/scratch.clj:9:19: e)
;; def render_edn(observations: list[dict]) -> str:
;;     L = [";; danjo-observations.kotoba.edn — danjo.discrepancyObservation records.",
;;          ";; G4 nonAdjudicatingNotice=true (FACT, never a verdict) · G5 ≥2 sourceRecordCids",
;;          ";; · G6 methodNoteCid. The censor's EYE, never the SWORD. Named-party publication",
;;          ";; G10 + 1 SBT=1 vote gated. DERIVED :representative. ADR-2605301600.", "", "["]
;;     for o in observations:
;;         cids = " ".join(f'"{c}"' for c in o["sourceRecordCids"])
;;         L.append(
;;             f' {{:danjo.obs/category :{o["category"]} :danjo.obs/non-adjudicating true '
;;             f':danjo.obs/pattern "{o["observedPattern"]}" '
;;             f':danjo.obs/source-record-cids [{cids}] '
;;             f':danjo.obs/method-note-cid "{o["methodNoteCid"]}" '
;;             f':danjo.obs/sourcing :representative}}')
;;     L.append("]")
;;     return "\n".join(L) + "\n"
(defn render-edn [& _]
  (throw (ex-info "TODO: port-failed" {:from "render_edn"})))

;; TODO: port-failed unit main (assembled-lint error)
;; def main(argv: list[str]) -> int:
;;     corpus = load_json(pathlib.Path(argv[argv.index("--corpus") + 1]) if "--corpus" in argv else _CORPUS)
;;     methods = load_json(pathlib.Path(argv[argv.index("--methods") + 1]) if "--methods" in argv else _METHODS)
;;     obs = run_all(corpus, methods)
;;     if "--out" in argv:
;;         outdir = pathlib.Path(argv[argv.index("--out") + 1])
;;         outdir.mkdir(parents=True, exist_ok=True)
;;         (outdir / "danjo-observations.kotoba.edn").write_text(render_edn(obs))
;;     print(f"danjo: {len(corpus.get('procurementRecords', []))} procurement records, "
;;           f"{len(methods.get('methods', []))} open methods → {len(obs)} discrepancy observation(s)")
;;     for o in obs:
;;         print(f"  [{o['category']}] {o['observedPattern']} "
;;               f"({len(o['sourceRecordCids'])} sources, non-adjudicating)")
;;     return 0
(defn main [& _]
  (throw (ex-info "TODO: port-failed" {:from "main"})))

