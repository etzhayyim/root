;; ported from /Users/junkawasaki/github/com-junkawasaki/orgs/etzhayyim/root/20-actors/hakoniwa/methods/datom_emit.py (unit_refactor stage 0)
;; hakoniwa 箱庭 — kotoba Datom-log emitter (canonical EAVT state, ADR-2605312345).
(ns root.hakoniwa.methods.datom-emit
  (:require [clojure.string :as str]
            [clojure.set :as set]
            [clojure.edn :as edn]))

(declare node-attrs fmt emit main)

(def NODE_ATTRS (set [":sim/kind" ":sim/label" ":sim/sourcing" ":entity/public-ref"
                       ":persona/synthetic" ":persona/cohort" ":persona/susceptibility"
                       ":persona/initial-stance" ":persona/weight"
                       ":signal/push" ":signal/at-step"
                       ":outcome/measures" ":outcome/statistic" ":outcome/use"]))

(def EDGE_ATTRS (set [":en/from" ":en/to" ":en/kind" ":en/weight" ":en/sourcing"]))

;; TODO: port-failed unit _fmt (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmp5nahcb0x/scratch.clj:14:1: e)
;; def _fmt(v) -> str:
;;     if v is True:
;;         return "true"
;;     if v is False:
;;         return "false"
;;     if v is None:
;;         return "nil"
;;     if isinstance(v, str):
;;         return v if v.startswith(":") else '"' + v.replace('\\', '\\\\').replace('"', '\\"') + '"'
;;     if isinstance(v, float):
;;         return f"{v:g}"
;;     return str(v)
(defn fmt [& _]
  (throw (ex-info "TODO: port-failed" {:from "_fmt"})))

;; TODO: port-failed unit emit (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmpbsbrsk9l/scratch.clj:3:8: er)
;; def emit(nodes: dict, edges: list, dist: dict, meta: dict, tx: int = 1) -> str:
;;     L = []
;;     L.append(";; hakoniwa 箱庭 — GENERATED kotoba Datom log (ADR-2606111500). DO NOT hand-edit.")
;;     L.append(";; Canonical EAVT state (ADR-2605312345). [e a v tx op].")
;;     L.append(";; GROUND op :add = durable world. DERIVED :bond/is-transient = distribution on read (N1/G2).")
;;     L.append(";; G1: every :persona is SYNTHETIC (:persona/synthetic true) — the box holds no real people.")
;;     L.append("[")
;; 
;;     # ── GROUND: node datoms (EDN insertion order → deterministic)
;;     for nid in nodes:
;;         n = nodes[nid]
;;         for a in NODE_ATTRS:
;;             if a in n and n[a] is not None:
;;                 L.append(f"[{_fmt(nid)} {a} {_fmt(n[a])} {tx} :add]")
;; 
;;     # ── GROUND: edge datoms (content-stable edge id en.<from>.<kind>.<to>)
;;     for e in edges:
;;         eid = f"en.{e[':en/from']}.{e[':en/kind'].lstrip(':')}.{e[':en/to']}"
;;         for a in EDGE_ATTRS:
;;             if a in e and e[a] is not None:
;;                 L.append(f"[{_fmt(eid)} {a} {_fmt(e[a])} {tx} :add]")
;; 
;;     # ── GROUND: the simulation run configuration (reproducibility provenance)
;;     run = "run.hakoniwa"
;;     for a, v in [(":run/steps", meta["steps"]), (":run/replicas", meta["replicas"]),
;;                  (":run/seed", meta["seed"]), (":run/jitter", meta["jitter"]),
;;                  (":run/kernel", ":friedkin-johnsen")]:
;;         L.append(f"[{_fmt(run)} {a} {_fmt(v)} {tx} :add]")
;; 
;;     # ── DERIVED (transient — the DISTRIBUTION; N1/G2). NO point datom exists.
;;     L.append(";; ── DERIVED outcome distribution (transient; computed on read from the ensemble) ──")
;;     for qk, qv in dist["quantiles"].items():
;;         L.append(f"[outcome.adoption :bond/distribution-{qk.lstrip(':')} {qv:g} {tx} :derived] "
;;                  ";; :bond/is-transient true")
;;     L.append(f"[outcome.adoption :bond/distribution-mean {dist['mean']:g} {tx} :derived] "
;;              ";; :bond/is-transient true")
;;     L.append(f"[outcome.adoption :bond/point-asserted false {tx} :derived] "
;;              ";; G2: distribution-only — never a point")
;; 
;;     L.append("]")
;;     return "\n".join(L) + "\n"
(defn emit [& _]
  (throw (ex-info "TODO: port-failed" {:from "emit"})))

;; TODO: port-failed unit main (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmpzn8xi84p/scratch.clj:20:10: )
;; def main(argv):
;;     here = pathlib.Path(__file__).resolve().parent.parent
;;     scenario = pathlib.Path(argv[1]) if len(argv) > 1 and not argv[1].startswith("--") \
;;         else here / "data" / "seed-scenario.kotoba.edn"
;;     outdir = here / "out"
;;     if "--out" in argv:
;;         outdir = pathlib.Path(argv[argv.index("--out") + 1])
;; 
;;     def opt(flag, default, cast):
;;         return cast(argv[argv.index(flag) + 1]) if flag in argv else default
;; 
;;     tx = opt("--tx", 1, int)
;;     steps = opt("--steps", S.DEFAULT_STEPS, int)
;;     replicas = opt("--replicas", S.DEFAULT_REPLICAS, int)
;;     seed = opt("--seed", S.DEFAULT_SEED, int)
;;     outdir.mkdir(parents=True, exist_ok=True)
;; 
;;     nodes, edges = W.load(scenario)
;;     results, meta = S.ensemble(nodes, edges, steps=steps, replicas=replicas, seed=seed)
;;     dist = D.distribution(results)
;;     out = outdir / "scenario-datoms.kotoba.edn"
;;     out.write_text(emit(nodes, edges, dist, meta, tx), encoding="utf-8")
;;     print(f"hakoniwa datom log → {out} ({len(nodes)} nodes + {len(edges)} 縁, tx={tx})")
;;     return 0
(defn main [& _]
  (throw (ex-info "TODO: port-failed" {:from "main"})))

