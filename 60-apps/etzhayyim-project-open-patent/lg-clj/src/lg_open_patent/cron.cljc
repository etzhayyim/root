(ns lg-open-patent.cron
  "Cron schedule registry — clj port of `lg/lg_open_patent/cron.py` (ADR-2606280030).

  The Python `cron.py` reads the `crons` array from `langgraph.json` and registers
  APScheduler `CronTrigger` jobs that call `graph.ainvoke()`. This namespace ports
  the SCHEDULE PARSING + spec validation (the load-bearing, testable part) as pure
  fns. Wiring a concrete scheduler is left to the deployment layer; the Python
  server remains the deployed cron runtime and COEXISTS.

  Source of truth is the SAME `../lg/langgraph.json` the Python reads — so a drift
  between the two stays a single edit (parity guard, like cron.py's _load_cron_specs)."
  (:require [clojure.string :as str]
            #?(:clj [cheshire.core :as json])))

(def langgraph-json-path
  "Relative to lg-clj/ (where bb runs); the python config two dirs over in ../lg/."
  "../lg/langgraph.json")

(defn read-langgraph-json
  "Parse ../lg/langgraph.json (the deployed Python config). Returns a map or nil."
  []
  #?(:clj
     (try
       (json/parse-string (slurp langgraph-json-path) true)
       (catch Exception _ nil))
     :cljs nil))

(defn cron-specs
  "Valid cron specs from langgraph.json: entries with both :schedule and :graph
  (mirrors cron.py `_load_cron_specs`)."
  ([] (cron-specs (read-langgraph-json)))
  ([cfg]
   (->> (or (:crons cfg) [])
        (filter (fn [c] (and (map? c) (:schedule c) (:graph c))))
        vec)))

(defn cron-graphs
  "Set of graph names that have a cron schedule."
  ([] (cron-graphs (cron-specs)))
  ([specs] (set (map (comp str :graph) specs))))

(defn valid-crontab?
  "Loose 5-field crontab validation (min hour dom mon dow)."
  [schedule]
  (= 5 (count (remove str/blank? (str/split (str schedule) #"\s+")))))
