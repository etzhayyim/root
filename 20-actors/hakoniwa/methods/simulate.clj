;; ported from /Users/junkawasaki/github/com-junkawasaki/orgs/etzhayyim/root/20-actors/hakoniwa/methods/simulate.py (unit_refactor stage 0)
;; hakoniwa 箱庭 — forward simulation kernel (Friedkin-Johnsen opinion dynamics over the box).
(ns root.hakoniwa.methods.simulate
  (:require [clojure.string :as str]
            [clojure.set :as set]
            [clojure.edn :as edn]))

(declare default-steps clamp01 jitter build-topology anchor-at-step run-replica population-statistic ensemble kernel-step run-replica-swarm swarm-ensemble main)

(def default-steps 12)
(def default-replicas 64)
(def default-seed 7)
(def default-jitter 0.10)
(def max-iter 200)
(def tol 1.0e-6)

(defn _clamp01 [x]
  (if (< x 0.0)
    0.0
    (if (> x 1.0)
      1.0
      x)))

(defn _jitter [seed replica pid amp]
  "Deterministic per-(replica, persona) anchor jitter in [-amp, amp]. No Math.random."
  (let [input (str seed ":" replica ":" pid)
        hash-bytes (.digest (java.security.MessageDigest/new "SHA-256") (.getBytes input java.nio.charset.StandardCharsets/UTF_8))
        ;; Extract first 4 bytes as a big-endian unsigned integer
        unsigned-int (let [b1 (nth hash-bytes 0)
                             b2 (nth hash-bytes 1)
                             b3 (nth hash-bytes 2)
                             b4 (nth hash-bytes 3)]
                    (let [v1 (if (< b1 0) (+ b1 256) b1)
                         v2 (if (< b2 0) (+ b2 256) b2)
                         v3 (if (< b3 0) (+ b3 256) b3)
                         v4 (if (< b4 0) (+ b4 256) b4)]
                      (+ (* v1 16777216) (* v2 65536) (* v3 256) v4)))
        u (/ unsigned-int 4294967296.0)]
    (* (* (- (* u 2.0) 1.0) amp))))

;; TODO: port-failed unit build_topology (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmp3_t_ib0r/scratch.clj:32:26: )
;; def build_topology(nodes: dict, edges: list):
;;     """Return (pids, susceptibility, base_anchor, weight, incoming, signal_push_by_persona).
;; 
;;     incoming[i] = list of (j, w_ij) row-normalised so Σ_j w_ij == 1 (empty → fully anchored).
;;     signal_push_by_persona[step] applied additively to anchors from a signal's at-step onward.
;;     """
;;     P = W.personas(nodes)
;;     pids = list(P.keys())  # EDN insertion order → deterministic
;;     sus = {i: float(P[i].get(":persona/susceptibility", 0.5)) for i in pids}
;;     base_anchor = {i: _clamp01(float(P[i].get(":persona/initial-stance", 0.5))) for i in pids}
;;     weight = {i: float(P[i].get(":persona/weight", 1.0)) for i in pids}
;; 
;;     raw_in = {i: [] for i in pids}
;;     for e in edges:
;;         if e.get(":en/kind") == ":influences":
;;             j, i = e.get(":en/from"), e.get(":en/to")
;;             if j in sus and i in sus:
;;                 raw_in[i].append((j, float(e.get(":en/weight", 1.0))))
;;     incoming = {}
;;     for i, lst in raw_in.items():
;;         tot = sum(w for _, w in lst)
;;         incoming[i] = [(j, w / tot) for j, w in lst] if tot > 0 else []
;; 
;;     # signals: persona → list of (push, at_step) it is exposed to
;;     sig = W.signals(nodes)
;;     exposure = {i: [] for i in pids}
;;     for e in edges:
;;         if e.get(":en/kind") == ":exposed-to":
;;             i, s = e.get(":en/from"), e.get(":en/to")
;;             if i in exposure and s in sig:
;;                 exposure[i].append((float(sig[s].get(":signal/push", 0.0)),
;;                                     int(sig[s].get(":signal/at-step", 0))))
;;     return pids, sus, base_anchor, weight, incoming, exposure
(defn build-topology [& _]
  (throw (ex-info "TODO: port-failed" {:from "build_topology"})))

;; TODO: port-failed unit _anchor_at_step (assembled-lint error)
;; def _anchor_at_step(base: float, exposures: list, step: int, jit: float) -> float:
;;     a = base + jit
;;     for push, at in exposures:
;;         if step >= at:
;;             a += push
;;     return _clamp01(a)
(defn anchor-at-step [& _]
  (throw (ex-info "TODO: port-failed" {:from "_anchor_at_step"})))

;; TODO: port-failed unit run_replica (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmpuwatxmrs/scratch.clj:4:25: e)
;; def run_replica(pids, sus, base_anchor, incoming, exposure, steps, seed, replica, jitter):
;;     """One deterministic forward run; returns final stance vector x[i]."""
;;     jit = {i: _jitter(seed, replica, i, jitter) for i in pids}
;;     # initial state = anchor at step 0
;;     x = {i: _anchor_at_step(base_anchor[i], exposure[i], 0, jit[i]) for i in pids}
;;     for step in range(1, steps + 1):
;;         anchor = {i: _anchor_at_step(base_anchor[i], exposure[i], step, jit[i]) for i in pids}
;;         # iterate the FJ map to its fixed point within this step (inner relaxation)
;;         for _ in range(MAX_ITER):
;;             nx = {}
;;             for i in pids:
;;                 nbr = sum(w * x[j] for j, w in incoming[i])
;;                 lam = sus[i] if incoming[i] else 0.0  # no neighbours → fully anchored
;;                 nx[i] = _clamp01(lam * nbr + (1.0 - lam) * anchor[i])
;;             delta = max(abs(nx[i] - x[i]) for i in pids)
;;             x = nx
;;             if delta < TOL:
;;                 break
;;     return x
(defn run-replica [& _]
  (throw (ex-info "TODO: port-failed" {:from "run_replica"})))

;; TODO: port-failed unit population_statistic (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmpb40exz1s/scratch.clj:3:8: er)
;; def population_statistic(x: dict, weight: dict, member_ids=None) -> float:
;;     """Aggregate-first readout: population weighted-mean final stance (G1 — never per-persona)."""
;;     ids = member_ids if member_ids is not None else list(x.keys())
;;     wsum = sum(weight[i] for i in ids)
;;     if wsum <= 0:
;;         return 0.0
;;     return sum(weight[i] * x[i] for i in ids) / wsum
(defn population-statistic [& _]
  (throw (ex-info "TODO: port-failed" {:from "population_statistic"})))

;; TODO: port-failed unit ensemble (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmpaiou3kr9/scratch.clj:15:10: )
;; def ensemble(nodes: dict, edges: list, steps=DEFAULT_STEPS, replicas=DEFAULT_REPLICAS,
;;              seed=DEFAULT_SEED, jitter=DEFAULT_JITTER):
;;     """Return (outcomes_per_replica, meta). outcomes is a list[float] of the town-wide statistic."""
;;     pids, sus, base_anchor, weight, incoming, exposure = build_topology(nodes, edges)
;;     # which personas the outcome measures (default :all)
;;     outs = W.outcomes(nodes)
;;     member_ids = None
;;     if outs:
;;         first = next(iter(outs.values()))
;;         if first.get(":outcome/measures") != ":all":
;;             member_ids = pids  # only :all is wired in R0; named-population is a future facet
;;     results = []
;;     for r in range(replicas):
;;         x = run_replica(pids, sus, base_anchor, incoming, exposure, steps, seed, r, jitter)
;;         results.append(population_statistic(x, weight, member_ids))
;;     meta = {"personas": len(pids), "edges": len(edges), "steps": steps,
;;             "replicas": replicas, "seed": seed, "jitter": jitter}
;;     return results, meta
(defn ensemble [& _]
  (throw (ex-info "TODO: port-failed" {:from "ensemble"})))

(defn kernel-step [stance neighbour-mean susceptibility anchor]
  "Default per-persona step = one Friedkin-Johnsen update over the neighbour mean."
  (clamp01 (+ (* susceptibility neighbour-mean) (* (- 1.0 susceptibility) anchor))))

(defn clamp01 [val]
  (if (< val 0.0)
    0.0
    (if (> val 1.0)
      1.0
      val)))

;; TODO: port-failed unit run_replica_swarm (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmppkslivrn/scratch.clj:21:39: )
;; def run_replica_swarm(pids, sus, base_anchor, incoming, exposure, steps, seed, replica, jitter,
;;                       step_fn=None):
;;     """One forward run where EACH persona steps via step_fn (LLM or kernel). Genuine agent-wise
;;     dynamics: per step, every agent updates from its weighted-neighbour mean + anchor."""
;;     step_fn = step_fn or (lambda st, nm, su, an: {"stance": _kernel_step(st, nm, su, an),
;;                                                   "via": ":kernel"})
;;     jit = {i: _jitter(seed, replica, i, jitter) for i in pids}
;;     x = {i: _anchor_at_step(base_anchor[i], exposure[i], 0, jit[i]) for i in pids}
;;     vias = set()
;;     for step in range(1, steps + 1):
;;         anchor = {i: _anchor_at_step(base_anchor[i], exposure[i], step, jit[i]) for i in pids}
;;         nx = {}
;;         for i in pids:
;;             nbr = sum(w * x[j] for j, w in incoming[i]) if incoming[i] else anchor[i]
;;             r = step_fn(x[i], nbr, sus[i] if incoming[i] else 0.0, anchor[i])
;;             nx[i] = _clamp01(float(r["stance"]))
;;             vias.add(r.get("via", ":kernel"))
;;         x = nx
;;     return x, vias
(defn run-replica-swarm [& _]
  (throw (ex-info "TODO: port-failed" {:from "run_replica_swarm"})))

;; TODO: port-failed unit swarm_ensemble (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmpubbun_d_/scratch.clj:2:83: e)
;; def swarm_ensemble(nodes, edges, steps=DEFAULT_STEPS, replicas=DEFAULT_REPLICAS,
;;                    seed=DEFAULT_SEED, jitter=DEFAULT_JITTER, step_fn=None):
;;     """Ensemble using the per-agent swarm step. Returns (outcomes, meta) like ensemble(); meta
;;     carries the set of step `via` channels actually used (e.g. :murakumo / :kernel-fallback)."""
;;     pids, sus, base_anchor, weight, incoming, exposure = build_topology(nodes, edges)
;;     results, vias = [], set()
;;     for r in range(replicas):
;;         x, v = run_replica_swarm(pids, sus, base_anchor, incoming, exposure,
;;                                  steps, seed, r, jitter, step_fn)
;;         results.append(population_statistic(x, weight))
;;         vias |= v
;;     meta = {"personas": len(pids), "edges": len(edges), "steps": steps, "replicas": replicas,
;;             "seed": seed, "jitter": jitter, "swarm_via": sorted(vias)}
;;     return results, meta
(defn swarm-ensemble [& _]
  (throw (ex-info "TODO: port-failed" {:from "swarm_ensemble"})))

;; TODO: port-failed unit main (/var/folders/31/st4xq0g12v3cn1b9yg5zcrsm0000gn/T/tmpb9lbf3vw/scratch.clj:3:8: er)
;; def main(argv):
;;     here = pathlib.Path(__file__).resolve().parent.parent
;;     scenario = pathlib.Path(argv[1]) if len(argv) > 1 and not argv[1].startswith("--") \
;;         else here / "data" / "seed-scenario.kotoba.edn"
;; 
;;     def opt(flag, default, cast):
;;         return cast(argv[argv.index(flag) + 1]) if flag in argv else default
;; 
;;     steps = opt("--steps", DEFAULT_STEPS, int)
;;     replicas = opt("--replicas", DEFAULT_REPLICAS, int)
;;     seed = opt("--seed", DEFAULT_SEED, int)
;; 
;;     nodes, edges = W.load(scenario)
;;     if "--swarm" in argv:
;;         import murakumo as _M
;;         step_fn = lambda st, nm, su, an: _M.persona_step(st, nm, su, an, prefer_fleet=True)  # noqa: E731
;;         results, meta = swarm_ensemble(nodes, edges, steps=steps, replicas=replicas,
;;                                        seed=seed, step_fn=step_fn)
;;         via = ",".join(meta["swarm_via"])
;;         print(f"hakoniwa SWARM: {meta['personas']} synthetic personas (LLM-per-agent), "
;;               f"{meta['edges']} 縁, {steps}×{replicas} → mean {sum(results)/len(results):.4f} "
;;               f"[via {via}]")
;;     else:
;;         results, meta = ensemble(nodes, edges, steps=steps, replicas=replicas, seed=seed)
;;         print(f"hakoniwa: {meta['personas']} synthetic personas, {meta['edges']} 縁, "
;;               f"{steps} steps × {replicas} replicas → ensemble mean {sum(results)/len(results):.4f}")
;;     print("  (distribution-only output via distribution.py — never a point assertion, G2)")
;;     return 0
(defn main [& _]
  (throw (ex-info "TODO: port-failed" {:from "main"})))

