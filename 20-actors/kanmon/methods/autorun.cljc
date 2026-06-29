#!/usr/bin/env bb
;; kanmon 関門 — autonomous heartbeat: assess → append OPENING routes to the ledger.
(ns kanmon.methods.autorun
  "autorun.cljc — kanmon 関門 deterministic heartbeat (ADR-2606291500).

  One beat: load the exam systems, run the barrier-load → OPENING route engine, and
  APPEND the route datoms as one content-addressed transaction to the append-only
  observation ledger (kotoba.cljc). prev-cid chaining keeps the ledger tamper-evident
  + resume-safe — this is the 持続永続化 leg.

  Deterministic by construction: the caller supplies tx-id + as-of (no wall clock,
  no Math/random) → resume-safe. IDEMPOTENT-BY-CONTENT: a beat whose route datoms
  equal the previous beat's is a NO-OP (nothing appended) — the ledger records
  CHANGES, not a wall-clock liveness tick. No-server-key: appends to a local file
  only, no network I/O. OBSERVATION ONLY — kanmon mirrors the gate, it does not
  prep students or score anyone."
  (:require [kanmon.methods.analyze :as az]
            [kanmon.methods.kotoba :as k]
            #?(:clj [clojure.edn :as edn])))

(defn beat
  "Run one heartbeat. opts:
     :exams     vector of exam maps (required)
     :tx-id     deterministic tx id (required)
     :as-of     deterministic as-of stamp (required)
     :log-path  ledger path (required)
   IDEMPOTENT-BY-CONTENT: if the new route datoms equal the last beat's datoms,
   the beat is a NO-OP — nothing is appended.
   Returns {:head <cid> :count <n> :routes <tally> :appended <bool> :reason <kw|nil>}."
  [{:keys [exams tx-id as-of log-path]}]
  (let [assessment (az/assess exams)
        ds (az/datoms assessment)
        prev (k/head-cid log-path)
        last-ds (let [txs (k/read-log log-path)]
                  (when (seq txs) (get (last txs) ":tx/datoms")))
        unchanged? (= ds last-ds)
        base {:count (count ds) :routes (get assessment "tally")}]
    (if unchanged?
      (assoc base :head prev :appended false :reason :no-change)
      (let [tx (k/make-tx ds tx-id as-of prev)
            head (k/append-tx tx log-path)]
        (assoc base :head head :appended true :reason nil)))))

#?(:clj
   (defn -main [& args]
     (let [seed (or (first args) "20-actors/kanmon/kotoba/seed.edn")
           log-path (or (second args)
                        (-> (clojure.java.io/file *file*) .getParentFile .getParentFile
                            (clojure.java.io/file "data" "persisted" "kanmon.observations.kotoba.edn") str))
           exams (vec (filter #(= (:type %) :exam)
                              (edn/read-string (slurp seed))))
           r (beat {:exams exams
                    :tx-id "kanmon-beat-manual" :as-of "manual" :log-path log-path})]
       (println (str "observation ledger head=" (:head r)
                     " datoms=" (:count r)
                     " appended=" (:appended r)
                     (when (:reason r) (str " (" (name (:reason r)) ")"))))
       (println (str "routes=" (:routes r)))
       (println (str "chain=" (k/verify-chain log-path))))))

#?(:clj
   (when (= *file* (System/getProperty "babashka.file"))
     (apply -main *command-line-args*)))
