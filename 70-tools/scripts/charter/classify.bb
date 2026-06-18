#!/usr/bin/env bb
;; classify.bb — score substrate-boundary items as 憲法(Tier-0) / Tier-1 / 実装.
;;
;;   bb classify.bb            # ranked table + self-test (asserts :expect band)
;;   bb classify.bb --md       # markdown table
;;   bb classify.bb --edn      # machine-readable verdicts
;;
;; J = Σ_axis (weight · score). Band by :bands thresholds. Σweight asserted = 1.0.

(require '[clojure.edn :as edn] '[clojure.string :as str])

(def here (-> *file* (java.io.File.) .getAbsoluteFile .getParent))
(def card (edn/read-string (slurp (str here "/layer-classification.edn"))))
(def criteria (:criteria card))
(def axes (mapv :key criteria))
(def weight (into {} (map (juxt :key :weight) criteria)))
(def bands (:bands card))

(let [s (reduce + (map :weight criteria))]
  (when (> (abs (- s 1.0)) 1e-9)
    (binding [*out* *err*] (println (format "FATAL: Σweight = %.4f ≠ 1.0" s)))
    (System/exit 1)))

(defn total [item]
  (reduce (fn [a k] (+ a (* (weight k) (get-in item [:scores k] 0)))) 0.0 axes))

(defn band [j]
  (cond (>= j (:tier-0 bands)) :tier-0
        (>= j (:tier-1 bands)) :tier-1
        :else                  :impl))

(def ranked (->> (:items card)
                 (map #(let [j (total %)] (assoc % :J j :band (band j))))
                 (sort-by :J >) vec))

(defn r2 [x] (/ (Math/round (* x 100.0)) 100.0))
(def mode (cond (some #{"--edn"} *command-line-args*) :edn
                (some #{"--md"} *command-line-args*)  :md
                :else :selftest))

(case mode
  :edn
  (prn {:bands bands
        :verdicts (mapv (fn [i] {:key (:key i) :J (r2 (:J i)) :band (:band i)}) ranked)})

  :md
  (do
    (println "| 項目 | J | band | expect |")
    (println "|---|---|---|---|")
    (doseq [i ranked]
      (println (format "| %s | %.2f | **%s** | %s |"
                       (:label i) (:J i) (name (:band i)) (name (:expect i))))))

  :selftest
  (do
    (println "charter layer-classification — 憲法(Tier-0) / Tier-1 / 実装\n")
    (println (format "  bands: tier-0 ≥ %.1f · tier-1 ≥ %.1f · else 実装  (Σweight = %.2f)\n"
                     (:tier-0 bands) (:tier-1 bands) (reduce + (map :weight criteria))))
    (let [results (for [i ranked]
                    (let [ok (= (:band i) (:expect i))]
                      (println (format "  %-3s %-46s J=%.2f → %-7s (expect %s)"
                                       (if ok "ok" "FAIL")
                                       (subs (:label i) 0 (min 45 (count (:label i))))
                                       (:J i) (name (:band i)) (name (:expect i))))
                      ok))
          fails (count (remove true? results))]
      (println (format "\n%d/%d passed" (- (count results) fails) (count results)))
      (System/exit (if (pos? fails) 1 0)))))
