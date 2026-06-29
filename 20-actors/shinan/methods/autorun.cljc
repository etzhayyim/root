#!/usr/bin/env bb
;; shinan 指南 — autonomous heartbeat: assess → append coverage routes to the ledger.
(ns shinan.methods.autorun
  "autorun.cljc — shinan 指南 deterministic heartbeat (ADR-2606291501).

  One beat: load the topics + open resources, run the coverage engine, and APPEND the
  route datoms as one content-addressed transaction to the append-only coverage ledger
  (kotoba.cljc). prev-cid chaining keeps the ledger tamper-evident + resume-safe.

  Deterministic by construction: the caller supplies tx-id + as-of (no wall clock,
  no Math/random) → resume-safe. IDEMPOTENT-BY-CONTENT: a beat whose route datoms
  equal the previous beat's is a NO-OP. No-server-key: appends to a local file only,
  no network I/O. 学習解放 — there is no learner in the model; shinan maps open
  scaffolds + gaps, it never scores or predicts anyone."
  (:require [shinan.methods.analyze :as az]
            [shinan.methods.shinan-edn :as se]
            [shinan.methods.kotoba :as k]
            #?(:clj [clojure.edn :as edn])))

(defn beat
  "Run one heartbeat. opts:
     :topics    vector of topic maps (required)
     :resources vector of resource maps (required)
     :tx-id     deterministic tx id (required)
     :as-of     deterministic as-of stamp (required)
     :log-path  ledger path (required)
   IDEMPOTENT-BY-CONTENT: identical coverage datoms → no-op.
   Returns {:head <cid> :count <n> :topic-routes <tally> :resource-routes <tally>
            :appended <bool> :reason <kw|nil>}."
  [{:keys [topics resources tx-id as-of log-path]}]
  (se/validate-open! resources)  ;; 学習解放 — refuse a non-open resource even at the heartbeat
  (let [assessment (az/assess topics resources)
        ds (az/datoms assessment)
        prev (k/head-cid log-path)
        last-ds (let [txs (k/read-log log-path)]
                  (when (seq txs) (get (last txs) ":tx/datoms")))
        unchanged? (= ds last-ds)
        base {:count (count ds)
              :topic-routes (get assessment "topic-tally")
              :resource-routes (get assessment "resource-tally")}]
    (if unchanged?
      (assoc base :head prev :appended false :reason :no-change)
      (let [tx (k/make-tx ds tx-id as-of prev)
            head (k/append-tx tx log-path)]
        (assoc base :head head :appended true :reason nil)))))

#?(:clj
   (defn -main [& args]
     (let [seed (or (first args) "20-actors/shinan/kotoba/seed.edn")
           log-path (or (second args)
                        (-> (clojure.java.io/file *file*) .getParentFile .getParentFile
                            (clojure.java.io/file "data" "persisted" "shinan.coverage.kotoba.edn") str))
           rows (edn/read-string (slurp seed))
           topics (vec (filter #(= (:type %) :topic) rows))
           resources (vec (filter #(= (:type %) :resource) rows))
           r (beat {:topics topics :resources resources
                    :tx-id "shinan-beat-manual" :as-of "manual" :log-path log-path})]
       (println (str "coverage ledger head=" (:head r)
                     " datoms=" (:count r)
                     " appended=" (:appended r)
                     (when (:reason r) (str " (" (name (:reason r)) ")"))))
       (println (str "topic-routes=" (:topic-routes r)))
       (println (str "resource-routes=" (:resource-routes r)))
       (println (str "chain=" (k/verify-chain log-path))))))

#?(:clj
   (when (= *file* (System/getProperty "babashka.file"))
     (apply -main *command-line-args*)))
