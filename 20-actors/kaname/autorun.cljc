(ns kaname.autorun
  "kaname 要 — autonomous heartbeat (ADR-2606172100 R1; busshi/ugachi pattern).

  One beat = invoke the langgraph-clj actor (kaname.graph): perceive the cross-domain WORLD MODEL
  (世界認識, joining every committed mirror — optionally refreshing the web mirror by fetching live in
  clj, G7) → compute the 要 → route to OPENING → おせっかい proposal → persist the readout to the
  kotoba Datom-log commit-DAG. Idempotent-by-content (no append when the readout is unchanged),
  resume-safe (cycle = log length; no wall clock, no randomness), no-server-key.

  Portable .cljc — the heartbeat is a thin deterministic wrapper over the graph + kotoba persistence."
  (:require [clojure.string :as str]
            [kaname.graph :as graph]
            [kaname.methods.kotoba :as kkot]
            [kotoba.datom :as kd]
            #?(:clj [clojure.java.io :as io])))

(defn beat
  "Run one perceive→…→persist cycle. input keys: {:base-dir :log-path :tx-id :as-of :live?
  :sources-path}. Returns a compact status map."
  [{:keys [base-dir log-path] :as input}]
  (let [out (graph/run input)]
    {:head      (:head out)
     :appended  (get-in out [:persist :appended])
     :reason    (get-in out [:persist :reason])
     :datoms    (get-in out [:persist :count])
     :point     (some-> (:point out) second)
     :mirrors   (:loaded out)
     :world     {:nodes (count (get-in out [:world :nodes]))
                 :edges (count (get-in out [:world :edges]))}}))

#?(:clj
   (defn -main
     "Resume-safe heartbeat: derive the cycle from the log length, run one beat. Args:
     [base-dir] [log-path] [--live]. --live refreshes the web mirror by fetching in clj (G7)."
     [& argv]
     (let [pos  (vec (remove #(str/starts-with? (str %) "--") argv))
           live? (boolean (some #{"--live"} argv))
           base (or (first pos) "20-actors")
           log  (or (second pos) (str (io/file base "kaname" kkot/default-log)))
           n    (count (kd/read-log log))
           r    (beat {:base-dir base :log-path log
                       :tx-id (str "kaname-" n) :as-of (str "as-of:" n)
                       :live? live?
                       :sources-path (str (io/file base "kaname" "data" "ingest-sources.edn"))})]
       (println (str "kaname beat #" n ": 要=" (:point r)
                     " world=" (:world r) " mirrors=" (pr-str (:mirrors r))
                     " appended=" (:appended r) (when (:reason r) (str " (" (:reason r) ")"))
                     " head=" (:head r)))
       0)))

#?(:clj
   (when (= *file* (System/getProperty "babashka.file"))
     (apply -main *command-line-args*)))
