#!/usr/bin/env bb
;; Working Clojure port of methods/ingest.py.
(ns watari.methods.ingest
  "watari 渡り — public AIS/ADS-B broadcast normalizer (ADR-2606041827, R0).

  Normalizes a PUBLIC transponder-broadcast batch (AISStream.io AIS PositionReports / OpenSky
  /states/all state vectors) into kotoba :craft/* + :craft.fix/* records.

  CONSTITUTIONAL (G1 + G4 + G7): ingests ONLY public transponder broadcasts; private-craft
  owner/crew/passenger identity is never derived (G4); military / blocked-from-display craft are
  dropped (G1). LIVE fetch is OUTWARD-GATED — requires WATARI_OPERATOR_GATE=1 AND --live; default
  is OFFLINE, reading a local sample batch and tagging everything :representative (G5).

  Run:  bb --classpath 20-actors 20-actors/watari/methods/ingest.clj --batch <sample.json>"
  (:require [cheshire.core :as json]
            [clojure.java.io :as io]
            [clojure.string :as str]))

(defn- nonblank [s] (let [t (str/trim (str (or s "")))] (when (seq t) t)))

(defn- vessel-fix
  "AISStream-shaped PositionReport → [craft fix] (:representative)."
  [msg ts]
  (let [mmsi (or (:MMSI msg) (:UserID msg))
        cid (str "craft.vessel.mmsi" mmsi)]
    [{:craft/id cid :craft/kind :vessel :craft/name (nonblank (:ShipName msg))
      :craft/mmsi mmsi :craft/sourcing :representative}
     {:craft.fix/id (str "fix." cid "." ts) :craft.fix/craft cid
      :craft.fix/lat (:Latitude msg) :craft.fix/lon (:Longitude msg)
      :craft.fix/speed-kn (:Sog msg) :craft.fix/course (:Cog msg)
      :craft.fix/observed-at ts :craft.fix/source :ais :craft.fix/sourcing :representative}]))

(defn- aircraft-fix
  "OpenSky /states/all state vector → [craft fix] (:representative). Drops on null icao24 or
  null position (a craft not publicly position-broadcasting is not represented, G1)."
  [state ts]
  (let [icao24 (str/lower-case (str/trim (str (or (nth state 0 nil) ""))))]
    (if (or (str/blank? icao24) (nil? (nth state 5 nil)) (nil? (nth state 6 nil)))
      [nil nil]
      (let [cid (str "craft.aircraft." icao24)]
        [{:craft/id cid :craft/kind :aircraft :craft/callsign (nonblank (nth state 1 nil))
          :craft/icao24 icao24 :craft/sourcing :representative}
         {:craft.fix/id (str "fix." cid "." ts) :craft.fix/craft cid
          :craft.fix/lat (nth state 6 nil) :craft.fix/lon (nth state 5 nil)
          :craft.fix/alt-m (nth state 7 nil) :craft.fix/speed-kn (nth state 9 nil)
          :craft.fix/course (nth state 10 nil) :craft.fix/on-ground (boolean (nth state 8 nil))
          :craft.fix/observed-at ts :craft.fix/source :adsb :craft.fix/sourcing :representative}]))))

(defn normalize
  "Accepts {:ais [...] :adsb {:observedAt t :states [...]}} → {:craft {id→rec} :fixes [...]}.
  First craft identity wins on dedup (setdefault)."
  [batch]
  (let [ts-default (or (:observedAt batch) "1970-01-01T00:00:00Z")
        adsb (:adsb batch)
        pairs (concat (map #(vessel-fix % (or (:observedAt %) ts-default)) (:ais batch))
                      (map #(aircraft-fix % (or (:observedAt adsb) ts-default)) (:states adsb)))
        craft (reduce (fn [m [c _]]
                        (if (and c (not (contains? m (:craft/id c)))) (assoc m (:craft/id c) c) m))
                      {} pairs)
        fixes (vec (keep (fn [[c f]] (when c f)) pairs))]
    {:craft craft :fixes fixes}))

(defn live-refusal
  "G7 outward gate: returns the refusal message if --live is requested, else nil."
  [argv env-gate]
  (when (some #{"--live"} argv)
    (if (not= (str env-gate) "1")
      (str "watari G7: live AISStream/OpenSky ingest is Council+operator gated. "
           "Set WATARI_OPERATOR_GATE=1 with attestation to enable. Default offline mode: --batch <sample.json>.")
      "watari R0: live fetch not implemented (design-only). Wire AISStream WS + OpenSky REST here once gated.")))

(defn main [& argv]
  (let [args (vec argv)]
    (when-let [msg (live-refusal args (System/getenv "WATARI_OPERATOR_GATE"))]
      (println msg) (System/exit 2))
    (let [bi (.indexOf args "--batch")]
      (when (neg? bi) (println "usage: ingest.clj --batch <sample.json>") (System/exit 1))
      (let [batch-path (nth args (inc bi))
            batch (json/parse-string (slurp (io/file batch-path)) true)
            {:keys [craft fixes]} (normalize batch)]
        (println (format "watari ingest (offline, :representative): %d craft, %d fixes from %s"
                         (count craft) (count fixes) (.getName (io/file batch-path))))))))

(when (= *file* (System/getProperty "babashka.file"))
  (apply main *command-line-args*))
