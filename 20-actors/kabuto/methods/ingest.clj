#!/usr/bin/env bb
;; Working Clojure port of methods/ingest.py.
(ns kabuto.methods.ingest
  "kabuto 兜 — public-company ingest bridge (ADR-2606022000; offline default).

  Normalizes PUBLIC company registries into the kotoba EAVT :company/* vocabulary and dedup-merges
  with the curated seed (seed wins). Full-universe sources (GLEIF LEI / SEC EDGAR / exchange
  listings — millions of LEIs) are G7 Council + operator gated: a NO-OP unless KABUTO_OPERATOR_GATE
  is set. Default offline run re-emits the seed as the merged graph. Bridged records are forced to
  :representative (G5 — not first-party verified).

  Run:  bb --classpath 20-actors 20-actors/kabuto/methods/ingest.clj [--source file --in PATH]"
  (:require [kabuto.methods.kabuto-edn :as e]
            [cheshire.core :as json]
            [clojure.java.io :as io]
            [clojure.string :as str]))

(def ^:private this-file *file*)
(defn- actor-root [] (-> this-file io/file .getAbsoluteFile .getParentFile .getParentFile))

(def sources
  {"gleif" "https://leidata.gleif.org/api/v1/lei-records (GLEIF Golden Copy)"
   "edgar" "https://www.sec.gov/files/company_tickers.json (SEC EDGAR)"
   "exchange" "per-exchange listing directories (TWSE/TSE/KRX/Euronext/HKEX/LSE/…)"})

(defn bridge-public-json
  "Map a public-dataset-shaped record list → :company/* datom maps. Sourcing forced to
  :representative (G5). Unknown fields dropped."
  [records & {:keys [sourcing] :or {sourcing "representative"}}]
  (mapv (fn [r]
          (let [cid (or (:id r)
                        (str "org.corp." (str/lower-case (or (:country r) "xx")) "."
                             (str/lower-case (or (:ticker r) (:lei r) "unknown"))))]
            (cond-> {:company/id cid
                     :company/name (or (:name r) cid)
                     :company/status (keyword (or (:status r) "listed"))
                     :company/sourcing (keyword sourcing)}
              (:ticker r)   (assoc :company/ticker (:ticker r))
              (:exchange r) (assoc :company/exchange (keyword (str/lower-case (str (:exchange r)))))
              (:country r)  (assoc :company/country (:country r))
              (:sector r)   (assoc :company/sector (keyword (str/lower-case (str (:sector r)))))
              (:lei r)      (assoc :company/lei (:lei r)))))
        records))

(defn merge-bridged
  "Return the bridged companies NOT already present in the seed (seed wins on :company/id)."
  [seed-companies bridged]
  (let [ids (set (keys seed-companies))]
    (vec (remove #(contains? ids (:company/id %)) bridged))))

(defn gated-source?
  "True iff `source` is a full-universe live source AND the operator gate is not set (G7)."
  [source operator-gate]
  (and (contains? sources source) (not operator-gate)))

(defn main [& argv]
  (let [args (vec argv)
        opidx (fn [f] (let [i (.indexOf args f)] (when (>= i 0) (nth args (inc i)))))
        source (opidx "--source")
        infile (opidx "--in")
        operator-gate (= "1" (System/getenv "KABUTO_OPERATOR_GATE"))
        bridged (cond
                  (gated-source? source operator-gate)
                  (do (println (str "kabuto.ingest: source '" source "' = " (sources source)))
                      (println "  → G7 GATED: live full-universe fetch requires KABUTO_OPERATOR_GATE=1 (Council). Emitting seed only.")
                      [])
                  (and (= source "file") infile)
                  (let [recs (let [parsed (json/parse-string (slurp (io/file infile)) true)]
                               (if (map? parsed) (get parsed :companies parsed) parsed))
                        b (bridge-public-json recs)]
                    (println (format "kabuto.ingest: bridged %d records from %s (:representative)" (count b) infile))
                    b)
                  source (do (println (str "kabuto.ingest: unknown source '" source "'. Known: "
                                           (str/join ", " (keys sources)) ", file")) [])
                  :else [])
        seed-rows (e/load-edn (io/file (actor-root) "data" "seed-public-companies.kotoba.edn"))
        seed-companies (:companies (e/classify seed-rows))
        extra (merge-bridged seed-companies bridged)]
    (println (format "kabuto.ingest: %d seed + %d bridged companies (merge writes are the operator/R1 step)"
                     (count seed-companies) (count extra)))))

(when (= *file* (System/getProperty "babashka.file"))
  (apply main *command-line-args*))
