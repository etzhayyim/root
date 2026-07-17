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
;; evidence-fusion.nbb — fuse DISCLOSED evidence signals into the ECL objective function.
;;
;;   nbb evidence-fusion.nbb [evidence.edn]   # fuse → scores → J → route + provenance digest
;;   nbb evidence-fusion.nbb --edn [file]     # machine-readable verdict + fused scorecard
;;
;; The dynamic half of ECL: observatory actors (shiori/tsumugi/danjo/inochi/kanjo) emit
;; DISCLOSED signals (evidence.edn); this fuses them per dimension into score ∈ [-2,+2],
;; then routes via the SAME objective function as evaluate.bb. Hard-floor screen findings
;; short-circuit to :non-aligned before any scoring. A sha256 digest content-addresses the
;; fused scorecard for Council attestation (real CIDv1 = rasen methods/cid.py).

(require '[clojure.edn :as edn] '[clojure.string :as str])

(def here (-> *file* (java.io.File.) .getAbsoluteFile .getParent))
(def spec (edn/read-string (slurp (str here "/objective-function.edn"))))
(def dims (:dimensions spec))
(def th   (:thresholds spec))
(def valid-dims (set (map :key dims)))
(def cata (:catastrophe spec))

(let [s (reduce + (map :weight dims))]
  (when (> (abs (- s 1.0)) 1e-9)
    (binding [*out* *err*] (println (format "FATAL: Σweight = %.4f ≠ 1.0" s)))
    (.exit js/process 1)))

(def args (vec *command-line-args*))
(def edn-mode (some #{"--edn"} args))
(def ev-path (or (first (remove #(str/starts-with? % "--") args))
                 (str here "/evidence.edn")))
(def ev (edn/read-string (slurp ev-path)))

(defn clamp [lo hi x] (max lo (min hi x)))

(defn fuse-scores [signals]
  "per-dim score = clamp([-2,2], Σ sign·magnitude·confidence). Unknown dim → error."
  (doseq [s signals]
    (when-not (valid-dims (:dim s))
      (binding [*out* *err*] (println "FATAL: unknown dim" (:dim s))) (.exit js/process 2)))
  (into {} (for [d dims
                 :let [raw (reduce + 0.0
                             (for [s signals :when (= (:dim s) (:key d))]
                               (* (:sign s) (:magnitude s) (:confidence s))))]]
             [(:key d) (clamp -2.0 2.0 raw)])))

(defn objective [scores]
  (reduce (fn [acc d] (+ acc (* (:weight d) (get scores (:key d) 0.0)))) 0.0 dims))

(defn sha256-hex [s]
  (let [md nil #_MessageDigest-use-__crypto]
    (->> (.digest md (.getBytes s "UTF-8"))
         (map #(format "%02x" (bit-and % 0xff))) (apply str))))

(defn r3 [x] (when x (/ (Math/round (* x 1000.0)) 1000.0)))

;; ── evaluate ─────────────────────────────────────────────────────────────────
(def scores (fuse-scores (:signals ev)))
(def J (objective scores))
(defn catastrophe? [s] (some (fn [d] (<= (get s d 0) (:threshold cata))) (:dims cata)))
(def cata? (catastrophe? scores))
(def route (cond cata?                   :non-aligned
                 (>= J (:aligned th))    :aligned
                 (<= J (:non-aligned th)) :non-aligned
                 :else                   :hold))

;; content-address the fused scorecard (canonical, sorted) for attestation
(def scorecard {:candidate (get-in ev [:meta :candidate])
                :as-of (get-in ev [:meta :as-of])
                :scores (into (sorted-map) (map (fn [[k v]] [k (r3 v)]) scores))
                :catastrophe cata? :J (r3 J) :route route})
(def digest (sha256-hex (pr-str scorecard)))

(if edn-mode
  (prn (assoc scorecard :scorecard-sha256 digest))
  (do
    (println (format "候補: %s  (as-of %s)\n" (:candidate scorecard) (:as-of scorecard)))
    (println "DISCLOSED 証拠 → per-dim fuse (基準 = 子孫 wellbecoming):")
    (doseq [d dims]
      (let [sigs (filter #(= (:dim %) (:key d)) (:signals ev))
            contrib (str/join " + " (map #(format "%+.2f(%s)"
                                                   (* (:sign %) (:magnitude %) (:confidence %))
                                                   (:source %)) sigs))]
        (println (format "  %-26s = %+.3f   [%s]" (name (:key d))
                         (get scores (:key d)) (if (str/blank? contrib) "—" contrib)))))
    (println (format "\n  J = %+.3f → route = %s%s" J (name route)
                     (if cata? (format " (catastrophe: 子孫への最大級の害 ≤ %.1f, 非交渉)" (:threshold cata))
                         (format " (aligned≥%.1f / non-aligned≤%.1f)" (:aligned th) (:non-aligned th)))))
    (println (format "\n  scorecard sha256: %s" digest))
    (println "  (real CIDv1 = rasen methods/cid.py; Council が 1 SBT=1 vote で bytes 検証)")
    ;; self-test against declared expectation
    (when-let [exp (:expect-route ev)]
      (let [ok (= route exp)]
        (println (format "\n  self-test: %s (expect %s, got %s)"
                         (if ok "ok" "FAIL") (name exp) (name route)))
        (.exit js/process (if ok 0 1))))))
