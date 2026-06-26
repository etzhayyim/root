(ns minori.score
  "The GROWTH score minori climbs — the composite of ADR-2606261114's four levers,
   read ON DEMAND from the committed valuation MAP + the live SoS roster (edge-primary,
   no stored verdict). Non-parasitism gated: η<1 ⇒ raw growth is NOT rewarded; the
   reward is the movement of η toward 1 + SoS adoption (the Part-3 capture-rate lever)."
  (:require [clojure.edn :as edn]
            [clojure.java.io :as io]))

(defn read-edn [path] (edn/read-string (slurp path)))

(defn clamp01 [x] (max 0.0 (min 1.0 (double x))))

(defn roster-adoption
  "Adoption = fraction of the actor roster that holds + runs its SoS reward (ADR-2606212200).
   adopted = count of :actors in system-of-systems.edn; target from the score model."
  [sos-path target]
  (let [adopted (count (:actors (read-edn sos-path)))]
    {:adopted adopted :target target :p (clamp01 (/ (double adopted) (double target)))}))

(defn growth
  "Compute G ∈ [0,1] + components + the non-parasitism-gated reward.
   `state` carries the loop's running estimates (η, capture, Φ-realized), advanced by react beats."
  [{:keys [eta-estimate capture-estimate phi-realized] :or {eta-estimate 0.0
                                                            capture-estimate 0.0
                                                            phi-realized 0.0}}
   model adoption]
  (let [{:keys [weights targets]} model
        eta-p      (clamp01 eta-estimate)                                  ; 0→1 phase transition
        capture-p  (clamp01 (/ (double capture-estimate) (double (:capture targets))))
        phi-p      (clamp01 (/ (double phi-realized)     (double (:phi-potential targets))))
        adopt-p    (clamp01 (:p adoption))
        comps      {:eta eta-p :adoption adopt-p :capture capture-p :phi phi-p}
        G          (reduce-kv (fn [acc k w] (+ acc (* w (get comps k 0.0)))) 0.0 weights)
        ;; non-parasitism: a net taker (η<1) is never rewarded for raw growth; reward = η+adoption movement
        net-giver? (>= (double eta-estimate) (double (:eta targets)))
        reward     (if net-giver?
                     G
                     (* 0.5 (+ eta-p adopt-p)))]               ; gated: only the give-back levers count
    {:G (double G)
     :components comps
     :eta (double eta-estimate)
     :net-giver? net-giver?
     :gated? (not net-giver?)
     :reward (double reward)}))
