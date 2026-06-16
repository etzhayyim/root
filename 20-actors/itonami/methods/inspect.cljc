(ns itonami.methods.inspect
  "itonami 営み — R2 vision-inspection hand-off (ADR-2606082300).
  1:1 Clojure port of `methods/inspect.py`.

  Closes the loop from the R0 quality finding to in-line vision inspection.
    1. REQUEST  — from itonami's quality_target build a vision inspection request routed to a
       manako 眼 on-device detector (ADR-2606034800).
    2. RECONCILE — ingest manako's detection log → defect-class Pareto + scrap/rework
       reconciliation + scan-cycle scrap cross-check.

  CONSTITUTIONAL: G1 inspection INFORMS, never auto-rejects; G2 OBJECT detection only (line
  PART, never a person); G3 non-adjudicating.

  House style: Python ':…' keyword strings stay strings; string-keyed data; pure fns;
  file I/O only at #?(:clj) edges. Reuses itonami.methods.analyze."
  (:require [clojure.string :as str]
            [itonami.methods.analyze :as analyze]
            #?(:clj [clojure.java.io :as io])))

(def PASS ":pass")
(def REWORK ":rework")
(def SCRAP ":scrap")
(def NON-DEFECT-CLASS ":ok")
(def MANAKO-CONSTRAINTS
  ["on-device (no cloud imagery)" "object-only (no biometric / no person)"
   "AGPL-isolated weights" "advisory verdict (no auto-reject, G1)"])

(defn load-detections
  [text]
  (vec (filter #(and (map? %) (contains? % ":detect/unit")) (analyze/read-edn text))))

(defn inspection-request
  "Build a vision-inspection request for the highest-scrap station (the quality_target)."
  ([stations res] (inspection-request stations res nil))
  ([stations res detections]
   (let [target (get-in res ["_recommend" "quality_target" "station"])
         watch (if (seq detections)
                 (vec (sort (distinct (->> detections
                                           (filter #(and (= (get % ":detect/station") target)
                                                         (not= (get % ":detect/class") NON-DEFECT-CLASS)))
                                           (map #(get % ":detect/class"))))))
                 [])
         watch (if (seq watch) watch [":weld-porosity" ":spatter" ":misalignment"])
         scrap-rate (get-in res [target "scrap_rate"])]
     {"station" target
      "label" (get-in stations [target ":station/label"] target)
      "defect_classes" watch
      "sample_rate" (if (>= scrap-rate 0.05) 1.0 0.2)
      "routed_to" "actor:manako"
      "detector" "manako-yolo26-weld-defect-head"
      "constraints" MANAKO-CONSTRAINTS
      "reason_scrap_rate" scrap-rate})))

(defn reconcile
  "Reduce manako detections to a per-station defect-class Pareto + scan-cycle cross-check."
  ([detections] (reconcile detections nil))
  ([detections res]
   (let [;; build by_station preserving first-touch order (Python defaultdict)
         [by-station st-order]
         (reduce (fn [[bs order] d]
                   (let [st (get d ":detect/station")
                         seen? (contains? bs st)
                         order (if seen? order (conj order st))
                         a (get bs st {"inspected" 0 "defect_classes" {} "dc_order" []
                                       "scrap" 0 "rework" 0 "passed" 0})
                         a (update a "inspected" inc)
                         v (get d ":detect/verdict")
                         a (cond (= v SCRAP) (update a "scrap" inc)
                                 (= v REWORK) (update a "rework" inc)
                                 (= v PASS) (update a "passed" inc)
                                 :else a)
                         cls (get d ":detect/class")
                         a (if (and cls (not= cls NON-DEFECT-CLASS))
                             (-> a
                                 (update "dc_order" (fn [o] (if (contains? (get a "defect_classes") cls) o (conj o cls))))
                                 (update-in ["defect_classes" cls] (fnil inc 0)))
                             a)]
                     [(assoc bs st a) order]))
                 [{} []] detections)]
     (reduce
      (fn [out st]
        (let [a (get by-station st)
              dc (get a "defect_classes")
              ;; pareto = sorted by (-count, class)
              pareto (vec (sort-by (fn [[cls n]] [(- n) cls]) (map (fn [cls] [cls (get dc cls)]) (get a "dc_order"))))
              rec (cond-> {"inspected" (get a "inspected") "scrap" (get a "scrap")
                           "rework" (get a "rework") "passed" (get a "passed")
                           "defect_pareto" pareto
                           "top_defect" (if (seq pareto) (first (first pareto)) nil)}
                    (and (some? res) (contains? res st))
                    ;; Python `a["scrap"] == res[st]["scrap"]` is NUMERIC (int == float)
                    (assoc "scancycle_scrap" (get-in res [st "scrap"])
                           "scrap_agrees" (== (get a "scrap") (get-in res [st "scrap"]))))]
          (assoc out st rec)))
      {} st-order))))

(defn- fmt-f [x n]
  (-> (java.math.BigDecimal. (double x))
      (.setScale (int n) java.math.RoundingMode/HALF_EVEN) (.toPlainString)))
(defn- fmt-pct [x] (str (fmt-f (* 100.0 (double x)) 1) "%"))
(defn- fmt-pct0 [x] (str (fmt-f (* 100.0 (double x)) 0) "%"))

(defn- lstrip-colon [s] (if (str/starts-with? s ":") (subs s 1) s))

(defn report-md
  [stations req rec]
  (let [L (transient []) P (fn [s] (conj! L s))]
    (P "# itonami 営み — R2 vision-inspection hand-off\n")
    (P (str "> **G1** inspection INFORMS, never auto-rejects/actuates. **G2** object-only — "
            "the inspected entity is a line PART, never a person (manako is on-device, "
            "no-biometric, no person-reID — ADR-2606034800). **G3** detector outputs are "
            "disclosed facts, not itonami verdicts.\n"))
    (P "\n## Inspection request → manako\n")
    (P (str "- **station**: " (get req "label") " (scrap-rate " (fmt-pct (get req "reason_scrap_rate")) ")"))
    (P (str "- **detector**: " (get req "detector") " · sample " (fmt-pct0 (get req "sample_rate"))))
    (P (str "- **watch classes**: " (str/join ", " (map lstrip-colon (get req "defect_classes")))))
    (P (str "- **constraints**: " (str/join "; " (get req "constraints"))))
    (P "\n## Detection reconciliation (root-cause hint)\n")
    (P "| station | inspected | scrap | rework | top defect | scan-cycle agrees |")
    (P "|---|---:|---:|---:|---|:--:|")
    (doseq [[st r] rec]
      (let [agree (cond (get r "scrap_agrees") "✓"
                        (contains? r "scrap_agrees") "✗"
                        :else "n/a")
            top (or (get r "top_defect") "—")]
        (P (str "| " (get-in stations [st ":station/label"] st) " | " (get r "inspected") " | "
                (get r "scrap") " | " (get r "rework") " | " (lstrip-colon (str top)) " | " agree " |"))))
    (P "\n### Defect Pareto (worst station)\n")
    (when (contains? rec (get req "station"))
      (doseq [[cls n] (get-in rec [(get req "station") "defect_pareto"])]
        (P (str "- " (lstrip-colon cls) ": " n))))
    (P (str "\n---\n_itonami 営み R2 · ADR-2606082300 · vision-informs-not-actuates · "
            "object-only (no person) · root-cause hint, not a worker verdict._\n"))
    (str/join "\n" (persistent! L))))

(defn- fmt-g [v]
  (let [d (double v)]
    (if (and (== d (Math/rint d)) (< (Math/abs d) 1e15))
      (str (long d))
      (let [s (format "%.6g" d)]
        (if (str/includes? s ".") (-> s (str/replace #"0+$" "") (str/replace #"\.$" "")) s)))))

(defn emit
  "Transient EAVT inspection datoms (computed on read, never durable — G3)."
  ([req rec] (emit req rec 1))
  ([req rec tx]
   (let [st (get req "station")
         L (transient [";; itonami R2 vision hand-off — TRANSIENT (:bond/is-transient true), G1/G3." "["])]
     (conj! L (str "[" st " :ops/inspect-sample-rate " (fmt-g (get req "sample_rate"))
                   " " tx " :derived] ;; :bond/is-transient true"))
     (conj! L (str "[" st " :ops/inspect-routed-to :actor.manako " tx " :derived] ;; :bond/is-transient true"))
     (when (and (contains? rec st) (get-in rec [st "top_defect"]))
       (conj! L (str "[" st " :quality/top-defect " (get-in rec [st "top_defect"])
                     " " tx " :derived] ;; :bond/is-transient true"))
       (conj! L (str "[" st " :quality/scrap-agrees " (if (get-in rec [st "scrap_agrees"]) "true" "false")
                     " " tx " :derived] ;; :bond/is-transient true")))
     (conj! L "]")
     (str (str/join "\n" (persistent! L)) "\n"))))

#?(:clj
   (defn -main
     [& argv]
     (let [argv (vec argv)
           here (-> *file* io/file .getParentFile .getParentFile)
           seed (if (and (seq argv) (not (str/starts-with? (first argv) "--")))
                  (io/file (first argv))
                  (io/file here "data" "seed-factory-ops.kotoba.edn"))
           det-path (if (some #{"--detections"} argv)
                      (io/file (nth argv (inc (.indexOf argv "--detections"))))
                      (io/file here "data" "seed-vision-detections.kotoba.edn"))
           outdir (if (some #{"--out"} argv)
                    (io/file (nth argv (inc (.indexOf argv "--out"))))
                    (io/file here "out"))
           tx (if (some #{"--tx"} argv) (Long/parseLong (nth argv (inc (.indexOf argv "--tx")))) 1)
           {:keys [stations ticks]} (analyze/load-file* seed)
           res (analyze/analyze stations ticks)
           detections (load-detections (slurp det-path))
           req (inspection-request stations res detections)
           rec (reconcile detections res)]
       (.mkdirs outdir)
       (spit (io/file outdir "vision-inspection.md") (report-md stations req rec))
       (spit (io/file outdir "itonami-inspect.kotoba.edn") (emit req rec tx))
       0)))
