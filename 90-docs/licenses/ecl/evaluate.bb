#!/usr/bin/env bb
;; evaluate.bb — the ECL objective function J, evaluated dynamically.
;;
;;   bb evaluate.bb                 # run all fixtures as a self-test (asserts :expect)
;;   bb evaluate.bb <fixture-key>   # evaluate one fixture, show the breakdown
;;   bb evaluate.bb --edn           # emit per-fixture verdicts as EDN
;;
;; ECL は固定ルールでなく目的関数で動的評価する。screens(確定フロア)が発火すれば
;; scoring せず :non-aligned。さもなくば J = Σ(weight·score) を子孫-wellbecoming 基準で
;; 計算し、閾値で {:aligned :hold :non-aligned} に route する。

(require '[clojure.edn :as edn] '[clojure.string :as str])

(def here (-> *file* (java.io.File.) .getAbsoluteFile .getParent))
(def spec (edn/read-string (slurp (str here "/objective-function.edn"))))

(def dims   (:dimensions spec))
(def weight (into {} (map (juxt :key :weight) dims)))
(def th     (:thresholds spec))

;; invariant: Σweight = 1.0
(let [s (reduce + (map :weight dims))]
  (when (> (abs (- s 1.0)) 1e-9)
    (binding [*out* *err*] (println (format "FATAL: Σweight = %.4f ≠ 1.0" s)))
    (System/exit 1)))

(defn objective [scores]
  "J = Σ_dim (weight · score). Missing dim score = 0 (neutral)."
  (reduce (fn [acc d] (+ acc (* (:weight d) (get scores (:key d) 0)))) 0.0 dims))

(defn route [cand]
  "Dynamic evaluation: hard-floor screens first, else objective-function bands."
  (let [screens (seq (:screens cand))]
    (if screens
      {:route :non-aligned :J nil :reason {:screens (vec screens)}}
      (let [J (objective (:scores cand))
            r (cond (>= J (:aligned th))     :aligned
                    (<= J (:non-aligned th)) :non-aligned
                    :else                    :hold)]
        {:route r :J J :reason {:objective true}}))))

(defn r2 [x] (when x (/ (Math/round (* x 100.0)) 100.0)))

(def mode (cond (some #{"--edn"} *command-line-args*) :edn
                (first (remove #(str/starts-with? % "--") *command-line-args*)) :one
                :else :selftest))

(case mode
  :edn
  (prn {:meta (:meta spec)
        :verdicts (mapv (fn [f] (let [v (route f)]
                                  {:key (:key f) :route (:route v) :J (r2 (:J v))}))
                        (:fixtures spec))})

  :one
  (let [k (keyword (first (remove #(str/starts-with? % "--") *command-line-args*)))
        f (first (filter #(= (:key %) k) (:fixtures spec)))]
    (if-not f
      (do (println "unknown fixture:" k) (System/exit 2))
      (let [v (route f)]
        (println (format "候補: %s — %s\n" (name (:key f)) (:label f)))
        (if (:screens (:reason v))
          (println (format "確定フロア発火: %s → route = %s"
                           (str/join ", " (map name (get-in v [:reason :screens])))
                           (name (:route v))))
          (do (println "目的関数 J の内訳 (基準 = 子孫 wellbecoming):")
              (doseq [d dims]
                (let [sc (get (:scores f) (:key d) 0)]
                  (println (format "  %-26s w=%.2f · score=%+d = %+.3f   %s"
                                   (name (:key d)) (:weight d) sc (* (:weight d) sc)
                                   (:label d)))))
              (println (format "\n  J = %+.3f   → route = %s (aligned≥%.1f / non-aligned≤%.1f)"
                               (:J v) (name (:route v)) (:aligned th) (:non-aligned th))))))))

  :selftest
  (do
    (println "ECL 目的関数 self-test (基準 = 子・孫の動的 wellbecoming)\n")
    (println (format "  Σweight = %.2f  (子=%.2f + 孫=%.2f = %.2f が基準を担う)\n"
                     (reduce + (map :weight dims))
                     (weight :ko-wellbecoming) (weight :mago-wellbecoming)
                     (+ (weight :ko-wellbecoming) (weight :mago-wellbecoming))))
    (let [results (for [f (:fixtures spec)]
                    (let [v (route f) ok (= (:route v) (:expect f))]
                      (println (format "  %-3s %-24s J=%-6s → %-12s (expect %s)"
                                       (if ok "ok" "FAIL") (name (:key f))
                                       (if (:J v) (format "%+.2f" (:J v)) "n/a")
                                       (name (:route v)) (name (:expect f))))
                      ok))
          fails (count (remove true? results))]
      (println (format "\n%d/%d passed" (- (count results) fails) (count results)))
      (System/exit (if (pos? fails) 1 0)))))
