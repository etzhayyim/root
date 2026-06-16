;; ported from 20-actors/hakoniwa/methods/simulate.py — real port replacing the unit_refactor
;; stage-0 "TODO: port-failed" stubs. NS fixed root.hakoniwa.* → hakoniwa.* (20-actors source root).
(ns hakoniwa.methods.simulate
  "simulate.py — hakoniwa 箱庭 forward-simulation kernel (Friedkin-Johnsen opinion dynamics).
  1:1 Clojure port of `methods/simulate.py` (ADR-2606111500).

  Runs a CONTAINED miniature world of FICTIONAL synthetic personas forward in discrete steps and
  produces an ENSEMBLE of replica trajectories; the spread of the ensemble's population statistic
  IS the forecast distribution (computed in distribution.cljc) — never a single foretold future
  (G2 / 非終末論). Per-(replica, persona) anchor jitter is a DETERMINISTIC sha256 seed — no RNG.

  Self-contained sha-256 (for the jitter); house style = string-keyed maps + ':kw' strings, pure
  fns, portable .cljc. The Python `__main__` CLI printer is omitted."
  (:require [hakoniwa.methods.world :as w]))

(def default-steps 12)
(def default-replicas 64)
(def default-seed 7)
(def default-jitter 0.10)
(def ^:private max-iter 200)
(def ^:private tol 1.0e-6)

(defn- clamp01 ^double [^double x]
  (cond (< x 0.0) 0.0 (> x 1.0) 1.0 :else x))

(defn- as-double ^double [v default]
  (cond (nil? v) (double default)
        (number? v) (double v)
        :else (double default)))

;; ── sha-256 → 4-byte unsigned big-endian int (mirrors int.from_bytes(h[:4],"big")) ──────────
(defn- sha256-digest ^bytes [^String s]
  (.digest (java.security.MessageDigest/getInstance "SHA-256") (.getBytes s "UTF-8")))

(defn- jitter
  "Deterministic per-(replica, persona) anchor jitter in [-amp, amp]. No RNG (mirrors _jitter)."
  ^double [seed replica pid ^double amp]
  (let [d (sha256-digest (str seed ":" replica ":" pid))
        u (/ (double (bit-and (bit-or (bit-shift-left (bit-and (long (aget d 0)) 0xff) 24)
                                      (bit-shift-left (bit-and (long (aget d 1)) 0xff) 16)
                                      (bit-shift-left (bit-and (long (aget d 2)) 0xff) 8)
                                      (bit-and (long (aget d 3)) 0xff))
                              0xffffffff))
           (double (bit-shift-left 1 32)))]
    (* (- (* u 2.0) 1.0) amp)))

(defn build-topology
  "Return {:pids :sus :base-anchor :weight :incoming :exposure} (mirrors build_topology).
  incoming[i] = list of [j w_ij] row-normalised (Σ = 1, empty → fully anchored).
  exposure[i] = list of [push at-step] the persona is exposed to."
  [nodes edges]
  (let [P    (w/personas nodes)
        pids (vec (keys P))                       ;; insertion order → deterministic
        sus  (into {} (map (fn [i] [i (as-double (get (P i) ":persona/susceptibility") 0.5)]) pids))
        base-anchor (into {} (map (fn [i] [i (clamp01 (as-double (get (P i) ":persona/initial-stance") 0.5))]) pids))
        weight (into {} (map (fn [i] [i (as-double (get (P i) ":persona/weight") 1.0)]) pids))
        pid-set (set pids)
        raw-in (reduce (fn [acc e]
                         (if (= (get e ":en/kind") ":influences")
                           (let [j (get e ":en/from"), i (get e ":en/to")]
                             (if (and (contains? pid-set j) (contains? pid-set i))
                               (update acc i (fnil conj []) [j (as-double (get e ":en/weight") 1.0)])
                               acc))
                           acc))
                       (into {} (map (fn [i] [i []]) pids))
                       edges)
        incoming (into {} (map (fn [[i lst]]
                                 (let [tot (reduce + 0.0 (map second lst))]
                                   [i (if (> tot 0) (mapv (fn [[j wv]] [j (/ wv tot)]) lst) [])]))
                               raw-in))
        sig (w/signals nodes)
        exposure (reduce (fn [acc e]
                           (if (= (get e ":en/kind") ":exposed-to")
                             (let [i (get e ":en/from"), s (get e ":en/to")]
                               (if (and (contains? acc i) (contains? sig s))
                                 (update acc i conj [(as-double (get (sig s) ":signal/push") 0.0)
                                                     (long (as-double (get (sig s) ":signal/at-step") 0))])
                                 acc))
                             acc))
                         (into {} (map (fn [i] [i []]) pids))
                         edges)]
    {:pids pids :sus sus :base-anchor base-anchor :weight weight
     :incoming incoming :exposure exposure}))

(defn- anchor-at-step
  ^double [^double base exposures ^long step ^double jit]
  (let [a (+ base jit)
        a (reduce (fn [a [push at]] (if (>= step at) (+ a push) a)) a exposures)]
    (clamp01 a)))

(defn run-replica
  "One deterministic forward run; returns {i x_i} final stance vector (mirrors run_replica)."
  [pids sus base-anchor incoming exposure steps seed replica jit-amp]
  (let [jit (into {} (map (fn [i] [i (jitter seed replica i jit-amp)]) pids))
        x0  (into {} (map (fn [i] [i (anchor-at-step (base-anchor i) (exposure i) 0 (jit i))]) pids))]
    (loop [step 1, x x0]
      (if (> step steps)
        x
        (let [anchor (into {} (map (fn [i] [i (anchor-at-step (base-anchor i) (exposure i) step (jit i))]) pids))
              x' (loop [iter 0, x x]
                   (if (>= iter max-iter)
                     x
                     (let [nx (into {} (map (fn [i]
                                             (let [nbr (reduce (fn [s [j wv]] (+ s (* wv (x j)))) 0.0 (incoming i))
                                                   lam (if (seq (incoming i)) (sus i) 0.0)]
                                               [i (clamp01 (+ (* lam nbr) (* (- 1.0 lam) (anchor i))))]))
                                           pids))
                           delta (reduce max 0.0 (map (fn [i] (Math/abs (- (double (nx i)) (double (x i))))) pids))]
                       (if (< delta tol) nx (recur (inc iter) nx)))))]
          (recur (inc step) x'))))))

(defn population-statistic
  "Aggregate-first readout: population weighted-mean final stance (mirrors population_statistic)."
  ([x weight] (population-statistic x weight nil))
  ([x weight member-ids]
   (let [ids (or member-ids (keys x))
         wsum (reduce + 0.0 (map weight ids))]
     (if (<= wsum 0)
       0.0
       (/ (reduce + 0.0 (map (fn [i] (* (weight i) (x i))) ids)) wsum)))))

(defn ensemble
  "Return [outcomes-per-replica meta] (mirrors ensemble). outcomes = list of town-wide statistic."
  ([nodes edges] (ensemble nodes edges {}))
  ([nodes edges {:keys [steps replicas seed jitter]
                 :or {steps default-steps replicas default-replicas
                      seed default-seed jitter default-jitter}}]
   (let [{:keys [pids sus base-anchor weight incoming exposure]} (build-topology nodes edges)
         outs (w/outcomes nodes)
         member-ids (when (seq outs)
                      (let [first-o (val (first outs))]
                        (when (not= (get first-o ":outcome/measures") ":all") pids)))
         results (mapv (fn [r]
                         (population-statistic
                          (run-replica pids sus base-anchor incoming exposure steps seed r jitter)
                          weight member-ids))
                       (range replicas))
         meta {"personas" (count pids) "edges" (count edges) "steps" steps
               "replicas" replicas "seed" seed "jitter" jitter}]
     [results meta])))

;; ── LLM-persona swarm variant (G5/G8) ───────────────────────────────────────────────────────
(defn- kernel-step
  ^double [^double _stance ^double neighbour-mean ^double susceptibility ^double anchor]
  (clamp01 (+ (* susceptibility neighbour-mean) (* (- 1.0 susceptibility) anchor))))

(defn run-replica-swarm
  "One forward run where EACH persona steps via step-fn (LLM or kernel). step-fn takes
  [stance neighbour-mean susceptibility anchor] → {\"stance\" v \"via\" \":...\"}.
  Returns [x vias] (mirrors run_replica_swarm)."
  [pids sus base-anchor incoming exposure steps seed replica jit-amp step-fn]
  (let [step-fn (or step-fn
                    (fn [st nm su an] {"stance" (kernel-step st nm su an) "via" ":kernel"}))
        jit (into {} (map (fn [i] [i (jitter seed replica i jit-amp)]) pids))
        x0  (into {} (map (fn [i] [i (anchor-at-step (base-anchor i) (exposure i) 0 (jit i))]) pids))]
    (loop [step 1, x x0, vias #{}]
      (if (> step steps)
        [x vias]
        (let [anchor (into {} (map (fn [i] [i (anchor-at-step (base-anchor i) (exposure i) step (jit i))]) pids))
              [nx vias'] (reduce (fn [[nx vias] i]
                                   (let [nbr (if (seq (incoming i))
                                               (reduce (fn [s [j wv]] (+ s (* wv (x j)))) 0.0 (incoming i))
                                               (anchor i))
                                         r (step-fn (x i) nbr (if (seq (incoming i)) (sus i) 0.0) (anchor i))]
                                     [(assoc nx i (clamp01 (double (get r "stance"))))
                                      (conj vias (get r "via" ":kernel"))]))
                                 [{} vias]
                                 pids)]
          (recur (inc step) nx vias'))))))

(defn swarm-ensemble
  "Ensemble using the per-agent swarm step. Returns [outcomes meta] like ensemble; meta carries
  \"swarm_via\" = sorted set of step `via` channels used (mirrors swarm_ensemble)."
  ([nodes edges] (swarm-ensemble nodes edges {}))
  ([nodes edges {:keys [steps replicas seed jitter step-fn]
                 :or {steps default-steps replicas default-replicas
                      seed default-seed jitter default-jitter}}]
   (let [{:keys [pids sus base-anchor weight incoming exposure]} (build-topology nodes edges)
         [results vias]
         (reduce (fn [[results vias] r]
                   (let [[x v] (run-replica-swarm pids sus base-anchor incoming exposure
                                                  steps seed r jitter step-fn)]
                     [(conj results (population-statistic x weight)) (into vias v)]))
                 [[] #{}]
                 (range replicas))
         meta {"personas" (count pids) "edges" (count edges) "steps" steps "replicas" replicas
               "seed" seed "jitter" jitter "swarm_via" (vec (sort vias))}]
     [results meta])))
