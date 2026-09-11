(ns etzhayyim.ecl
  "Reusable ECL objective function J (ADR-2606172300 / 2606182359) — the SAME
  J / catastrophe / route as 90-docs/licenses/ecl/evaluate.bb, exposed as a library
  so the content floor is the REAL objective function, not a standalone deny-list.

  J = Σ_dim (weight · score), score ∈ [-2,+2]. The catastrophe term (a property of
  the function, NOT a screen list) vetoes maximal harm to 子 (ko) / 孫 (mago)
  wellbecoming (dim ≤ threshold) — '固定するのは priority', ADR-2606182359. route:
  catastrophe → :non-aligned; else J ≥ aligned → :aligned / ≤ non-aligned →
  :non-aligned / else :hold. Loads the Tier-0/1 spec (objective-function.edn);
  fail-open: `available?` is false if the spec can't be read."
  (:require [clojure.edn :as edn]))

(def ^:private spec-path "90-docs/licenses/ecl/objective-function.edn")

(def spec
  (delay (try (edn/read-string (slurp spec-path)) (catch Exception _ nil))))

(defn available? [] (some? @spec))

(defn objective
  "J = Σ_dim (weight · score). Missing dim score = 0 (neutral)."
  [scores]
  (reduce (fn [acc d] (+ acc (* (double (:weight d)) (double (get scores (:key d) 0)))))
          0.0 (:dimensions @spec)))

(defn catastrophe?
  "The severity term: maximal harm to 子/孫 wellbecoming (dim ≤ threshold) is
  non-negotiable (the priority is absolute)."
  [scores]
  (let [c (:catastrophe @spec)]
    (boolean (some (fn [d] (<= (double (get scores d 0)) (double (:threshold c)))) (:dims c)))))

(defn route
  "Evaluate content-derived :scores → {:route :aligned|:hold|:non-aligned :J :reason}.
  nil if the spec is unavailable (caller falls open to the deny-list floor)."
  [scores]
  (when (available?)
    (let [J  (objective scores)
          th (:thresholds @spec)]
      (if (catastrophe? scores)
        {:route :non-aligned :J J :reason :catastrophe}
        {:route (cond (>= J (:aligned th))     :aligned
                      (<= J (:non-aligned th)) :non-aligned
                      :else                    :hold)
         :J J :reason :objective}))))
