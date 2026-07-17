#!/usr/bin/env nbb
;; --- nbb shims (auto, ADR-2607173000) ---------------------------------
(def ^:private __fs (js/require "node:fs"))
(def ^:private __path (js/require "node:path"))
(def ^:private __cp (js/require "node:child_process"))
(def ^:private __os (js/require "node:os"))
(def ^:private __crypto (js/require "node:crypto"))
(defn- __sh [& args]
  (let [opts (when (map? (last args)) (last args))
        cmd (if opts (butlast args) args)
        r (.spawnSync __cp (first cmd) (to-array (rest cmd))
                      (clj->js (merge {:encoding "utf8"} (when opts {:cwd (:dir opts)}))))]
    {:exit (or (.-status r) 1) :out (or (.-stdout r) "") :err (or (.-stderr r) "")}))
(defn- __shell [& args]
  (let [opts (when (map? (first args)) (first args))
        cmd (if opts (rest args) args)
        r (.spawnSync __cp (first cmd) (to-array (rest cmd))
                      (clj->js (merge {:stdio "inherit" :encoding "utf8"}
                                      (when opts {:cwd (:dir opts)}))))]
    (when-not (zero? (or (.-status r) 1))
      (throw (js/Error. (str "shell failed: " (pr-str cmd)))))
    {:exit (or (.-status r) 0) :out "" :err ""}))
;; -----------------------------------------------------------------------
;; evaluate.nbb — the ECL objective function J, evaluated dynamically.
;;
;;   nbb evaluate.nbb                 # run all fixtures as a self-test (asserts :expect)
;;   nbb evaluate.nbb <fixture-key>   # evaluate one fixture, show the breakdown
;;   nbb evaluate.nbb --edn           # emit per-fixture verdicts as EDN
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
    (.exit js/process 1)))

(defn objective [scores]
  "J = Σ_dim (weight · score). Missing dim score = 0 (neutral)."
  (reduce (fn [acc d] (+ acc (* (:weight d) (get scores (:key d) 0)))) 0.0 dims))

(def cata (:catastrophe spec))

(defn catastrophe? [scores]
  "目的関数自身の severity 項: 子・孫 priority への最大級の害(dim ≤ threshold)は非交渉。
   外部の掟リストでなく『priority は absolute』の表現 (ADR-2606182359)。"
  (some (fn [d] (<= (get scores d 0) (:threshold cata))) (:dims cata)))

(defn route [cand]
  "All-objective-function evaluation: compute J always; the catastrophe term (a
   property of the function, not a screen list) vetoes max-harm-to-子孫; else J bands."
  (let [J (objective (:scores cand))]
    (if (catastrophe? (:scores cand))
      {:route :non-aligned :J J :reason {:catastrophe true}}
      {:route (cond (>= J (:aligned th))     :aligned
                    (<= J (:non-aligned th)) :non-aligned
                    :else                    :hold)
       :J J :reason {:objective true}})))

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
      (do (println "unknown fixture:" k) (.exit js/process 2))
      (let [v (route f)]
        (println (format "候補: %s — %s\n" (name (:key f)) (:label f)))
        (println "目的関数 J の内訳 (基準 = 子孫 wellbecoming):")
        (doseq [d dims]
          (let [sc (get (:scores f) (:key d) 0)]
            (println (format "  %-26s w=%.2f · score=%+.1f = %+.3f   %s"
                             (name (:key d)) (:weight d) (double sc) (* (:weight d) sc)
                             (:label d)))))
        (println (format "\n  J = %+.3f" (:J v)))
        (if (:catastrophe (:reason v))
          (println (format "  catastrophe 項発火 (ko/mago ≤ %.1f, priority 非交渉) → route = %s"
                           (:threshold cata) (name (:route v))))
          (println (format "  → route = %s (aligned≥%.1f / non-aligned≤%.1f)"
                           (name (:route v)) (:aligned th) (:non-aligned th)))))))

  :selftest
  (do
    (println "ECL 目的関数 self-test (基準 = 子・孫の動的 wellbecoming)\n")
    (println (format "  Σweight = %.2f  (子=%.2f + 孫=%.2f = %.2f が基準を担う)\n"
                     (reduce + (map :weight dims))
                     (weight :ko-wellbecoming) (weight :mago-wellbecoming)
                     (+ (weight :ko-wellbecoming) (weight :mago-wellbecoming))))
    (let [results (for [f (:fixtures spec)]
                    (let [v (route f) ok (= (:route v) (:expect f))]
                      (println (format "  %-3s %-38s J=%+.2f → %-12s%s"
                                       (if ok "ok" "FAIL") (name (:key f))
                                       (:J v) (name (:route v))
                                       (if (:catastrophe (:reason v)) " ⚠catastrophe" "")))
                      ok))
          fails (count (remove true? results))]
      (println (format "\n%d/%d passed" (- (count results) fails) (count results)))
      (.exit js/process (if (pos? fails) 1 0)))))
