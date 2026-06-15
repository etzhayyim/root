#!/usr/bin/env bb
;; Working Clojure port of methods/bridge.py.
(ns mitooshi.methods.bridge
  "mitooshi 見通し — watari / watatsuna chokepoint bridge (R0, offline).

  ADR-2606051800. The cross-actor composition the maritime-resilience picture is built on:
  watari 渡り (live moving-craft) and watatsuna 綿津綱 (submarine cables) both emit chokepoint-
  keyed aggregates over the SAME keyword space (:malacca, :luzon-strait, :suez-red-sea,
  :hormuz, …). This bridge maps those aggregates into mitooshi `:series` + `:obs` datoms, so
  mitooshi can FORECAST the very chokepoints watari/watatsuna OBSERVE.

    watari   :movement/chokepoint    + :movement/chokepoint-transit  → kind :transit-load (vessels)
    watatsuna :resilience/chokepoint + :resilience/chokepoint-load   → kind :cable-load   (Tbps)

  Each bridge run is ONE snapshot at --at <ts>. Non-chokepoint records (lanes, craft,
  stations) are ignored. Source-class :public-broadcast (G4). Live wiring is G10-gated.

  Run:  bb --classpath 20-actors 20-actors/mitooshi/methods/bridge.clj
        --watari ../data/bridge/watari-sample.edn
        --watatsuna ../data/bridge/watatsuna-sample.edn --at 1"
  (:require [clojure.java.io :as io]
            [clojure.edn :as edn]
            [clojure.string :as str]))

(def ^:private this-file *file*)
(defn- actor-root [] (-> this-file io/file .getAbsoluteFile .getParentFile .getParentFile))

(defn load-edn [path]
  (edn/read-string (slurp (io/file path))))

;; the shared chokepoint keyword space (watari ∩ watatsuna ∩ mitooshi seed)
(def known-chokepoints
  #{":malacca" ":luzon-strait" ":suez-red-sea" ":hormuz" ":gibraltar"
    ":south-china-sea" ":bab-el-mandeb"})

(defn- slug
  "Strip leading colon from a chokepoint string e.g. \":malacca\" → \"malacca\"."
  [cp]
  (if (str/starts-with? cp ":")
    (subs cp 1)
    cp))

(defn- make-series
  "Build a :series/* map for the given chokepoint, suffix, kind, unit and actor."
  [cp suffix kind unit actor]
  (let [sid (str "s-" (slug cp) "-" suffix)]
    {":series/id"           sid
     ":series/name"         (str (slug cp) " " kind)
     ":series/kind"         (str ":" kind)
     ":series/unit"         unit
     ":series/freq"         ":daily"
     ":series/source"       (str actor " chokepoint roll-up (DERIVED, public)")
     ":series/source-class" ":public-broadcast"
     ":series/sourcing"     ":representative"}))

(defn bridge
  "records-by-actor = {\"watari\" [...], \"watatsuna\" [...]}. Returns {:series, :obs, :skipped}."
  [records-by-actor observed-at]
  (let [series (atom {})
        obs    (atom [])
        skipped (atom 0)]

    ;; watari → transit-load series
    (doseq [rec (get records-by-actor "watari" [])]
      (let [cp (:movement/chokepoint rec)]
        (if-not cp
          (swap! skipped inc)
          (let [s (make-series cp "transit" "transit-load" "vessels" "watari")]
            (swap! series assoc (get s ":series/id") s)
            (swap! obs conj
                   {":obs/id"           (str "obs." (get s ":series/id") "." observed-at)
                    ":obs/series"        (get s ":series/id")
                    ":obs/observed-at"   observed-at
                    ":obs/value"         (double (or (:movement/chokepoint-transit rec) 0))
                    ":obs/source-actor"  "watari"})))))

    ;; watatsuna → cable-load series
    (doseq [rec (get records-by-actor "watatsuna" [])]
      (let [cp (:resilience/chokepoint rec)]
        (if-not cp
          (swap! skipped inc)
          (let [s (make-series cp "cable" "cable-load" "Tbps" "watatsuna")]
            (swap! series assoc (get s ":series/id") s)
            (swap! obs conj
                   {":obs/id"           (str "obs." (get s ":series/id") "." observed-at)
                    ":obs/series"        (get s ":series/id")
                    ":obs/observed-at"   observed-at
                    ":obs/value"         (double (or (:resilience/chokepoint-load rec) 0))
                    ":obs/source-actor"  "watatsuna"})))))

    {"series"  @series
     "obs"     @obs
     "skipped" @skipped}))

(defn emit-edn
  "Render the bridge result to a kotoba EDN string."
  [b observed-at]
  (str/join
   "\n"
   (concat
    [(str ";; chokepoint-observations.kotoba.edn — bridged from watari/watatsuna @ ts=" observed-at ".")
     ";; DERIVED public :representative observations (NOT authoritative). ADR-2606051800."
     ""
     "["]
    (for [s (vals (get b "series"))]
      (str " {:series/id \"" (get s ":series/id") "\" :series/kind " (get s ":series/kind")
           " :series/unit \"" (get s ":series/unit") "\" :series/source-class :public-broadcast"
           " :series/sourcing :representative}"))
    (for [o (get b "obs")]
      (str " {:obs/id \"" (get o ":obs/id") "\" :obs/series \"" (get o ":obs/series") "\""
           " :obs/observed-at " (get o ":obs/observed-at")
           " :obs/value " (get o ":obs/value")
           " :obs/source-actor \"" (get o ":obs/source-actor") "\"}"))
    ["]" ""])))

(defn main [& argv]
  (let [args (vec argv)
        idx-at (.indexOf args "--at")]
    (when (< idx-at 0)
      (println "bridge: --at <ts> is required")
      (System/exit 1))
    (let [observed-at (Long/parseLong (nth args (inc idx-at)))
          by-actor
          (reduce
           (fn [m [actor flag]]
             (let [idx (.indexOf args flag)]
               (if (>= idx 0)
                 (assoc m actor (load-edn (nth args (inc idx))))
                 m)))
           {}
           [["watari" "--watari"] ["watatsuna" "--watatsuna"]])]
      (when (empty? by-actor)
        (println "bridge: provide at least one of --watari <edn> / --watatsuna <edn>")
        (System/exit 1))
      (let [b (bridge by-actor observed-at)
            idx-out (.indexOf args "--out")]
        (when (>= idx-out 0)
          (let [outdir (io/file (nth args (inc idx-out)))]
            (.mkdirs outdir)
            (spit (io/file outdir "chokepoint-observations.kotoba.edn")
                  (emit-edn b observed-at))))
        (let [chokepts (sort (set (keys (get b "series"))))]
          (println (format "mitooshi bridge @ ts=%d: %d series, %d obs from %d actor(s); %d non-chokepoint records ignored"
                           observed-at
                           (count (get b "series"))
                           (count (get b "obs"))
                           (count by-actor)
                           (get b "skipped")))
          (doseq [c chokepts]
            (println (str "  → " c))))))))

(when (= *file* (System/getProperty "babashka.file"))
  (apply main *command-line-args*))
