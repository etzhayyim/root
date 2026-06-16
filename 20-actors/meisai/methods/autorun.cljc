(ns meisai.methods.autorun
  "autorun.py — meisai 明細 AUTONOMOUS statement-intake heartbeat on the kotoba Datom log.
  ADR-2606122400. 1:1 Clojure port of `methods/autorun.py`.

  Each heartbeat the actor sweeps the LOCAL intake directory (`data/intake/*.edn` — statement
  EDN files the member-principal fetch leg already wrote), ingests every intake whose content
  CID is not yet in the log, and persists ONE content-addressed transaction per new intake to
  the append-only local kotoba Datom log, linking the previous CID into a verifiable commit-DAG.

  Constitutional posture holds by construction (member-own G1, credential/PAN unrepresentable
  G2, local-only G3, provenance + dedup G5). NO external I/O. Deterministic (no wall clock).

  The __main__ argparse demo is OMITTED (CLI entrypoint, host-only)."
  (:require [clojure.string :as str]
            [meisai.methods.ingest :as ingest]
            [meisai.methods.kotoba :as kotoba])
  #?(:clj (:import [java.io File])))

(def base-as-of 20260612)

#?(:clj
   (def here
     (-> (or *file* "20-actors/meisai/methods/autorun.cljc")
         (File.) .getAbsoluteFile .getParentFile)))

#?(:clj
   (def data (File. ^File here "../data"))
   :cljs
   (def data nil))

#?(:clj
   (def intake (File. ^File data "intake"))
   :cljs
   (def intake nil))

(defn ingested-cids
  "Every intake content CID already persisted (the dedup set)."
  [log-path]
  (reduce
   (fn [out tx]
     (reduce
      (fn [out d]
        (if (and (= (count d) 4) (= (nth d 2) ":meisai.stmt/intake-cid"))
          (conj out (nth d 3))
          out))
      out
      (get tx ":tx/datoms" [])))
   #{}
   (kotoba/read-log log-path)))

(defn sweep
  "Deterministic intake worklist (sorted; no set iteration). Returns sorted paths."
  [intake-dir]
  #?(:clj
     (let [d (File. (str intake-dir))]
       (if-not (.isDirectory d)
         []
         (->> (.listFiles d)
              (filter (fn [^File p] (and (.isFile p)
                                         (str/ends-with? (.getName p) ".edn"))))
              (map (fn [^File p] (.getAbsolutePath p)))
              sort
              vec)))
     :cljs []))

(defn- file-name [path]
  #?(:clj (.getName (File. (str path)))
     :cljs (last (str/split (str path) #"/"))))

(defn run-cycle
  "One heartbeat: sweep intake → ingest every NEW statement (one tx each). Deterministic:
  tx ids continue from the log length; as-of derives from base-as-of + cycle (no wall clock).
  Returns {\"cycle\" \"appended\" \"skipped\" \"head\"}."
  [cycle intake-dir log-path]
  (loop [paths (sweep intake-dir)
         seen (ingested-cids log-path)
         appended []
         skipped 0]
    (if (empty? paths)
      {"cycle" cycle "appended" appended "skipped" skipped
       "head" (kotoba/head-cid log-path)}
      (let [path (first paths)
            [doc cid] (ingest/load-statement path)]
        (if (contains? seen cid)
          (recur (rest paths) seen appended (inc skipped))
          (let [datoms (ingest/statement-datoms doc cid)
                tx (kotoba/make-tx datoms
                                   {:tx-id (inc (count (kotoba/read-log log-path)))
                                    :as-of (+ base-as-of cycle)
                                    :prev-cid (kotoba/head-cid log-path)})]
            (kotoba/append-tx tx log-path)
            (recur (rest paths)
                   (conj seen cid)
                   (conj appended {"intake" (file-name path)
                                   "cid" (:tx/cid tx)
                                   "datoms" (count datoms)})
                   skipped)))))))
