#!/usr/bin/env bb
;; score.bb — weighted Charter-fit scoring over scorecard.edn
;;
;;   bb score.bb            # console ranking + per-criterion matrix
;;   bb score.bb --md       # emit GitHub-flavoured markdown tables (paste into paper)
;;   bb score.bb --edn      # emit computed results as EDN (machine-readable)
;;
;; Weighted total = Σ_axis (weight_axis · score_axis), scores 0..10, Σweight = 1.0,
;; so the total stays on the 0..10 scale. Weights are asserted to sum to 1.0.

(require '[clojure.edn :as edn]
         '[clojure.string :as str])

(def here (-> *file* (java.io.File.) .getAbsoluteFile .getParent))
(def card (edn/read-string (slurp (str here "/scorecard.edn"))))

(def criteria (:criteria card))
(def axes     (mapv :key criteria))
(def weight   (into {} (map (juxt :key :weight) criteria)))

;; ── invariant: weights sum to 1.0 ───────────────────────────────────────────
(let [s (reduce + (map :weight criteria))]
  (when (> (abs (- s 1.0)) 1e-9)
    (binding [*out* *err*]
      (println (format "FATAL: criteria weights sum to %.4f, expected 1.0" s)))
    (System/exit 1)))

(defn weighted-total [lic]
  (reduce (fn [acc k] (+ acc (* (weight k) (get-in lic [:scores k] 0))))
          0.0 axes))

(def ranked
  (->> (:licenses card)
       (map #(assoc % :total (weighted-total %)))
       (sort-by :total >)
       vec))

(defn r2 [x] (/ (Math/round (* x 100.0)) 100.0))

;; ── output modes ─────────────────────────────────────────────────────────────
(def mode (cond (some #{"--md"} *command-line-args*)  :md
                (some #{"--edn"} *command-line-args*) :edn
                :else :console))

(case mode
  :edn
  (prn {:meta (:meta card)
        :weights weight
        :ranking (mapv (fn [l] {:key (:key l) :label (:label l)
                                :total (r2 (:total l))}) ranked)})

  :md
  (do
    (println "### 加重ランキング\n")
    (println "| # | License | family | Σ (加重合計, 0–10) |")
    (println "|---|---|---|---|")
    (doseq [[i l] (map-indexed vector ranked)]
      (println (format "| %d | %s | %s | **%.2f** |"
                       (inc i) (:label l) (name (:family l)) (:total l))))
    (println "\n### 軸別マトリクス\n")
    (print "| License |")
    (doseq [c criteria] (print (format " %s |" (name (:key c)))))
    (println " **Σ** |")
    (print "|---|")
    (doseq [_ criteria] (print "---|")) (println "---|")
    (doseq [l ranked]
      (print (format "| %s |" (:label l)))
      (doseq [c criteria] (print (format " %d |" (get-in l [:scores (:key c)]))))
      (println (format " **%.2f** |" (:total l))))
    (println "\n### 軸の重み\n")
    (println "| axis | label | weight |")
    (println "|---|---|---|")
    (doseq [c criteria]
      (println (format "| %s | %s | %.2f |" (name (:key c)) (:label c) (:weight c)))))

  :console
  (do
    (println "── 軸の重み (Σ = 1.0) ──────────────────────────────")
    (doseq [c criteria]
      (println (format "  %-4s %.2f  %s" (name (:key c)) (:weight c) (:label c))))
    (println "\n── 加重ランキング ──────────────────────────────────")
    (doseq [[i l] (map-indexed vector ranked)]
      (println (format "  %2d. %-52s %5.2f" (inc i) (:label l) (:total l))))
    (println "\n── 軸別スコア ──────────────────────────────────────")
    (print (format "  %-46s" "License"))
    (doseq [k axes] (print (format "%-5s" (name k)))) (println "  Σ")
    (doseq [l ranked]
      (print (format "  %-46s" (subs (:label l) 0 (min 45 (count (:label l))))))
      (doseq [k axes] (print (format "%-5d" (get-in l [:scores k]))))
      (println (format "  %.2f" (:total l))))))
