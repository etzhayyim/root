;; ported from /Users/junkawasaki/github/com-junkawasaki/orgs/etzhayyim/root/20-actors/hakoniwa/methods/distribution.py (unit_refactor stage 0)
;; hakoniwa 箱庭 — ensemble → outcome DISTRIBUTION + mitooshi-shaped forecast record.
(ns root.hakoniwa.methods.distribution
  (:require [clojure.string :as str]
            [clojure.set :as set]
            [clojure.edn :as edn]))

(declare allowed-use quantile histogram distribution forecast-record report-md fmt-edn forecast-edn main)

(def ALLOWED_USE (set [":resilience" ":preparedness" ":robustness" ":research"]))
(def HIST_BINS 10)

(defn quantile [sorted-vals q]
  "Linear-interpolated quantile of an already-sorted list."
  (if (empty? sorted-vals)
    0.0
    (let [len (count sorted-vals)]
      (if (= len 1)
        (first sorted-vals)
        (let [pos (* q (- len 1))
              lo (int pos)
              frac (- pos lo)]
          (if (>= (+ lo 1) len)
            (last sorted-vals)
            (+ (* (nth sorted-vals lo) (- 1 frac))
               (* (nth sorted-vals (inc lo)) frac))))))))

;; TODO: port-failed unit histogram (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmphu4ohda0/scratch.clj:5:12: e)
;; def histogram(vals, bins=HIST_BINS):
;;     counts = [0] * bins
;;     for v in vals:
;;         b = min(bins - 1, max(0, int(v * bins)))
;;         counts[b] += 1
;;     return counts
(defn histogram [& _]
  (throw (ex-info "TODO: port-failed" {:from "histogram"})))

(defn distribution [results]
  (let [s (sort results)
        n (count s)
        mean (if (> n 0) (/ (reduce + s) n) 0.0)
        var (if (> n 0) (/ (reduce (fn [acc v] (+ acc (Math/pow (- v mean) 2))) 0.0 s) n) 0.0)]
    {:n n
     :mean mean
     :stdev (Math/sqrt var)
     :quantiles {:p10 (quantile s 0.10)
                 :p25 (quantile s 0.25)
                 :p50 (quantile s 0.50)
                 :p75 (quantile s 0.75)
                 :p90 (quantile s 0.90)}
     :min (if (> n 0) (first s) 0.0)
     :max (if (> n 0) (last s) 0.0)
     :histogram (histogram s)}))

;; TODO: port-failed unit forecast_record (assembled-lint error)
;; def forecast_record(nodes: dict, dist: dict, meta: dict, as_of: str, use: str = ":preparedness"):
;;     """mitooshi-shaped forecast record — DISTRIBUTION-ONLY (G2), resilience-USE-only (G3)."""
;;     if use not in ALLOWED_USE:
;;         raise ValueError(f"G3 violation: :forecast/use {use} is not a resilience use "
;;                          f"({sorted(ALLOWED_USE)}); steering/speculation is unrepresentable")
;;     outs = W.outcomes(nodes)
;;     target = "outcome"
;;     if outs:
;;         o = next(iter(outs.values()))
;;         target = o.get(":sim/label", o.get(":sim/id", "outcome"))
;;     return {
;;         ":forecast/actor": ":hakoniwa",
;;         ":forecast/target": target,
;;         ":forecast/kind": ":distribution",
;;         ":forecast/point-asserted": False,        # G2 — structural; there is no point field
;;         ":forecast/horizon-steps": meta.get("steps"),
;;         ":forecast/replicas": meta.get("replicas"),
;;         ":forecast/quantiles": dist["quantiles"],
;;         ":forecast/histogram": dist["histogram"],
;;         ":forecast/mean": dist["mean"],
;;         ":forecast/stdev": dist["stdev"],
;;         ":forecast/use": use,                     # G3 — resilience-only enum
;;         ":forecast/as-of": as_of,                 # G7 — leak-free boundary (mitooshi scores it)
;;         ":forecast/sourced-from": ":hakoniwa-synthetic-ensemble",
;;     }
(defn forecast-record [& _]
  (throw (ex-info "TODO: port-failed" {:from "forecast_record"})))

;; TODO: port-failed unit report_md (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmp2yz_q588/scratch.clj:38:20: )
;; def report_md(nodes: dict, dist: dict, meta: dict, as_of: str) -> str:
;;     L = []
;;     L.append("# hakoniwa 箱庭 — forward-simulation outcome DISTRIBUTION (never a point)\n")
;;     L.append("> **G2 — DISTRIBUTION-ONLY.** hakoniwa asserts a distribution over possible "
;;              "futures, never a single foretold outcome (非終末論). **G1 — every agent is a "
;;              "SYNTHETIC latent persona**, not a real person (no PII). **G3 — routed to "
;;              "RESILIENCE / preparedness**, never to trading, targeting, or persuasion.\n")
;;     outs = W.outcomes(nodes)
;;     target = next(iter(outs.values())).get(":sim/label", "outcome") if outs else "outcome"
;;     L.append(f"**Scenario**: {target}")
;;     L.append(f"**Box**: {meta['personas']} synthetic personas · {meta['edges']} 縁 · "
;;              f"{meta['steps']} steps × {meta['replicas']} replicas (seed {meta['seed']}, "
;;              f"jitter {meta['jitter']}) · as-of {as_of}\n")
;; 
;;     q = dist["quantiles"]
;;     L.append("\n## Outcome distribution — town-wide mean adoption stance\n")
;;     L.append("| statistic | value |")
;;     L.append("|---|---:|")
;;     L.append(f"| mean | {dist['mean']:.4f} |")
;;     L.append(f"| stdev | {dist['stdev']:.4f} |")
;;     L.append(f"| p10 | {q[':p10']:.4f} |")
;;     L.append(f"| p25 | {q[':p25']:.4f} |")
;;     L.append(f"| **p50 (median, a quantile — NOT 'the prediction')** | {q[':p50']:.4f} |")
;;     L.append(f"| p75 | {q[':p75']:.4f} |")
;;     L.append(f"| p90 | {q[':p90']:.4f} |")
;;     L.append(f"| min / max | {dist['min']:.4f} / {dist['max']:.4f} |")
;; 
;;     L.append("\n## Histogram (10 bins over [0,1])\n")
;;     L.append("| bin | range | count |")
;;     L.append("|---:|---|---:|")
;;     for b, c in enumerate(dist["histogram"]):
;;         L.append(f"| {b} | [{b/10:.1f}, {(b+1)/10:.1f}) | {c} |")
;; 
;;     L.append("\n## Handoff to mitooshi 見通し\n")
;;     L.append("_This distribution is handed to mitooshi (ADR-2606051800) as a "
;;              "`:forecast/kind :distribution` record (`:forecast/point-asserted false`, "
;;              "`:forecast/use :preparedness`) for leak-free proper-scoring against the realised "
;;              "outcome. hakoniwa generates the ensemble; mitooshi scores the skill._\n")
;;     L.append("\n---\n_hakoniwa 箱庭 · ADR-2606111500 · synthetic-persona forward simulation · "
;;              "distribution-only · resilience-routed · transparent (相互監視). Live large-swarm "
;;              "runs + any social emission are G8/Council-gated._\n")
;;     return "\n".join(L)
(defn report-md [& _]
  (throw (ex-info "TODO: port-failed" {:from "report_md"})))

;; TODO: port-failed unit _fmt_edn (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmp5d69rwr2/scratch.clj:21:1: e)
;; def _fmt_edn(v) -> str:
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
;;     if isinstance(v, dict):
;;         return "{" + " ".join(f"{k} {_fmt_edn(val)}" for k, val in v.items()) + "}"
;;     if isinstance(v, list):
;;         return "[" + " ".join(_fmt_edn(x) for x in v) + "]"
;;     return str(v)
(defn fmt-edn [& _]
  (throw (ex-info "TODO: port-failed" {:from "_fmt_edn"})))

(defn forecast-edn [rec]
  (let [body (clojure.string/join "\n "
                (for [[k v] rec]
                  (str k " " (fmt-edn v))))]
    (str ";; hakoniwa 箱庭 — GENERATED mitooshi-shaped forecast record (ADR-2606111500).\n"
         ";; DISTRIBUTION-ONLY (G2): no :forecast/point field exists. resilience-USE-only (G3).\n"
         "{" body "}\n")))

;; TODO: port-failed unit main (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmpv40fmtyp/scratch.clj:3:9: wa)
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
;;     steps = opt("--steps", S.DEFAULT_STEPS, int)
;;     replicas = opt("--replicas", S.DEFAULT_REPLICAS, int)
;;     seed = opt("--seed", S.DEFAULT_SEED, int)
;;     as_of = opt("--as-of", "2026-06-11T00:00:00Z", str)
;;     outdir.mkdir(parents=True, exist_ok=True)
;; 
;;     nodes, edges = W.load(scenario)
;;     results, meta = S.ensemble(nodes, edges, steps=steps, replicas=replicas, seed=seed)
;;     dist = distribution(results)
;;     rec = forecast_record(nodes, dist, meta, as_of)
;; 
;;     (outdir / "distribution-report.md").write_text(report_md(nodes, dist, meta, as_of), encoding="utf-8")
;;     (outdir / "forecast-record.kotoba.edn").write_text(forecast_edn(rec), encoding="utf-8")
;;     print(f"hakoniwa distribution → {outdir/'distribution-report.md'}")
;;     print(f"  p10/p50/p90 = {dist['quantiles'][':p10']:.4f} / "
;;           f"{dist['quantiles'][':p50']:.4f} / {dist['quantiles'][':p90']:.4f} "
;;           f"(distribution-only, G2)")
;;     return 0
(defn main [& _]
  (throw (ex-info "TODO: port-failed" {:from "main"})))

