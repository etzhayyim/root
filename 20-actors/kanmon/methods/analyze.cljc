#!/usr/bin/env bb
;; kanmon 関門 — barrier-load → OPENING route engine (clj-native, pure stdlib).
(ns kanmon.methods.analyze
  "analyze.cljc — kanmon 関門 入試 OBSERVATORY core (ADR-2606291500).

  Edge-primary BARRIER-LOAD computed ON READ over each exam SYSTEM:
    barrier-load = selectivity · (0.5+0.5·single-shot) · (0.5+0.5·stakes)
  then routed to OPENING (開放) by `route` (precedence — a 関門 is mapped to be OPENED):
    1. transparency < 0.4               → :transparency-gap (route to disclosure)
    2. single-shot ≥ 0.7 ∧ stakes ≥ 0.7 → :destake (reduce one-shot life-gating)
    3. equity < 0.4                     → :equity-watch (access disparity)
    4. barrier-load ≥ 0.5 ∧ alt-pathways < 0.4 → :open-pathway (surface alternatives)
    5. else                             → :monitor (already comparatively open)

  OBSERVATION ONLY. There is NO route that captures/entrenches/optimizes-into the gate,
  and NO representation of an individual examinee — barrier-load is a property of the
  GATE, never a score of a person (G1/G2/G4). `datoms` emits the disclosed exam facts +
  the DERIVED factors/route as EAVT, each flagged :kanmon/derived + :kanmon/sourcing."
  (:require [clojure.string :as str]))

;; ── thresholds (mirror kotoba/ontology.kanmon.edn :thresholds) ───────────────
(def transparency-min 0.4)
(def single-shot-min  0.7)
(def stakes-min       0.7)
(def equity-min       0.4)
(def barrier-open     0.5)
(def alt-max          0.4)

(defn- r3 [x] (/ (Math/round (* (double x) 1000.0)) 1000.0))

(defn barrier-load
  "selectivity · (0.5+0.5·single-shot) · (0.5+0.5·stakes), on read, rounded to 3."
  [{:keys [selectivity single-shot stakes]}]
  (r3 (* (double selectivity)
         (+ 0.5 (* 0.5 (double single-shot)))
         (+ 0.5 (* 0.5 (double stakes))))))

(defn route
  "Precedence-routed OPENING verdict for one exam system. Pure function of disclosed
   factors + barrier-load. Returns {:route kw :reason kw :barrier-load n}."
  [exam]
  (let [{:keys [single-shot stakes alt-pathways transparency equity]} exam
        bl (barrier-load exam)
        [rt reason]
        (cond
          (< (double transparency) transparency-min)
          [:transparency-gap :opaque-criteria]
          (and (>= (double single-shot) single-shot-min)
               (>= (double stakes) stakes-min))
          [:destake :one-shot-life-gate]
          (< (double equity) equity-min)
          [:equity-watch :access-disparity]
          (and (>= bl barrier-open) (< (double alt-pathways) alt-max))
          [:open-pathway :few-alternatives]
          :else
          [:monitor :comparatively-open])]
    {:route rt :reason reason :barrier-load bl}))

(defn assess
  "Assess all exam systems. Returns
   {\"exams\" [{:exam … :route … :reason … :barrier-load …} …]
    \"tally\" {route→count} \"by-country\" {country→count}
    \"top\" {…most-exclusive gate…}}."
  [exams]
  (let [rows (mapv (fn [e] (merge {:exam e} (route e))) exams)
        tally (frequencies (map :route rows))
        by-country (frequencies (map (comp :country :exam) rows))
        top (when (seq rows) (apply max-key :barrier-load rows))]
    {"exams" rows "tally" tally "by-country" by-country "top" top}))

;; ── EAVT datom emit (string-keyword attrs, kafun/busshi family shape) ────────
(defn datoms
  "Emit disclosed exam facts + DERIVED factors/route as EAVT [:db/add e a v].
   Derived datoms flagged :kanmon/derived true + :kanmon/sourcing."
  [assessment]
  (let [sourcing ":representative"]
    (vec
     (mapcat
      (fn [{:keys [exam route reason barrier-load]}]
        (let [e (:id exam)]
          [[":db/add" e ":kanmon.exam/name" (:name exam)]
           [":db/add" e ":kanmon.exam/country" (str (:country exam))]
           [":db/add" e ":kanmon.exam/kind" (str (:kind exam))]
           [":db/add" e ":kanmon.exam/annual-candidates" (:annual-candidates exam)]
           [":db/add" e ":kanmon.rem/selectivity" (double (:selectivity exam))]
           [":db/add" e ":kanmon.rem/single-shot" (double (:single-shot exam))]
           [":db/add" e ":kanmon.rem/stakes" (double (:stakes exam))]
           [":db/add" e ":kanmon.rem/alt-pathways" (double (:alt-pathways exam))]
           [":db/add" e ":kanmon.rem/transparency" (double (:transparency exam))]
           [":db/add" e ":kanmon.rem/equity" (double (:equity exam))]
           [":db/add" e ":kanmon.rem/barrier-load" barrier-load]
           [":db/add" e ":kanmon.rem/route" (str route)]
           [":db/add" e ":kanmon.rem/reason" (str reason)]
           [":db/add" e ":kanmon/derived" true]
           [":db/add" e ":kanmon/sourcing" sourcing]]))
      (get assessment "exams")))))

;; ── human-readable report ────────────────────────────────────────────────────
(defn report [assessment]
  (let [rows (sort-by (comp - :barrier-load) (get assessment "exams"))]
    (str/join
     "\n"
     (concat
      ["# kanmon 関門 — 入試 barrier-load → OPENING map (ADR-2606291500)"
       (str "exams: " (count rows)
            "  routes: " (pr-str (get assessment "tally"))
            "  by-country: " (pr-str (get assessment "by-country")))
       "(barrier-load is a property of the GATE, never a score of any person — map-not-target)"
       ""]
      (for [{:keys [exam route reason barrier-load]} rows]
        (str (format "%-14s" (:id exam))
             "  bl=" barrier-load
             "  → " (name route) " (" (name reason) ")"
             "  [" (name (:country exam)) "] " (:name exam)))))))

#?(:clj
   (defn -main [& args]
     (let [seed (or (first args) "20-actors/kanmon/kotoba/seed.edn")
           exams (vec (filter #(= (:type %) :exam)
                              (clojure.edn/read-string (slurp seed))))
           a (assess exams)]
       (println (report a)))))

#?(:clj
   (when (= *file* (System/getProperty "babashka.file"))
     (apply -main *command-line-args*)))
