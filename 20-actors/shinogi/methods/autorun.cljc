#!/usr/bin/env bb
;; shinogi 鎬 — autonomous heartbeat: analyze → append findings to the local ledger.
(ns shinogi.methods.autorun
  "autorun.cljc — shinogi 鎬 deterministic heartbeat (ADR-2606291200).

  One beat: load the exam-involution drivers, run the analysis-only system-dynamics
  read-off (analyze.cljc), and APPEND the findings datoms as one content-addressed
  transaction to the append-only LOCAL findings ledger (kotoba.cljc). prev-cid
  chaining keeps the ledger tamper-evident + resume-safe.

  Deterministic by construction: the caller supplies tx-id + as-of (no wall clock,
  no Math/random) → resume-safe. IDEMPOTENT-BY-CONTENT: a beat whose findings datoms
  equal the previous beat's is a NO-OP (nothing appended) — the ledger records
  CHANGES (a new driver, a flipped regime), not a wall-clock liveness tick, so a
  loop over a static seed never bloats the chain with identical snapshots.

  G4 ANALYSIS-ONLY: no-server-key — appends to a local file only, no network I/O,
  no outward/dispatch path (enforced by absence). shinogi never touches."
  (:require [shinogi.methods.shinogi-edn :as se]
            [shinogi.methods.analyze :as az]
            [shinogi.methods.kotoba :as k]
            #?(:clj [clojure.edn :as edn])))

(defn beat
  "Run one heartbeat. opts:
     :drivers   vector of driver maps (required)
     :tx-id     deterministic tx id (required)
     :as-of     deterministic as-of stamp (required)
     :log-path  ledger path (required)
   IDEMPOTENT-BY-CONTENT: if the new findings datoms equal the last beat's datoms,
   the beat is a NO-OP — nothing is appended.
   Returns {:head <cid> :count <n> :regimes <map> :appended <bool> :reason <kw|nil>}."
  [{:keys [drivers tx-id as-of log-path]}]
  (let [analysis (az/analyze drivers)
        ds (az/datoms drivers analysis)
        prev (k/head-cid log-path)
        last-ds (let [txs (k/read-log log-path)]
                  (when (seq txs) (get (last txs) ":tx/datoms")))
        unchanged? (= ds last-ds)
        regimes (into {} (map (fn [[s sp]] [s (name (:regime sp))]) (get analysis "stocks")))
        base {:count (count ds) :regimes regimes
              :drivers (count drivers)
              :jurisdictions (get-in analysis ["coverage" :jurisdictions])
              :failure-gap (get-in analysis ["failure_cycle" :relief-gap])}]
    (if unchanged?
      (assoc base :head prev :appended false :reason :no-change)
      (let [tx (k/make-tx ds tx-id as-of prev)
            head (k/append-tx tx log-path)]
        (assoc base :head head :appended true :reason nil)))))

#?(:clj
   (defn -main [& args]
     (let [seed (or (first args) "20-actors/shinogi/kotoba/seed.exam-involution.edn")
           log-path (or (second args)
                        (-> (clojure.java.io/file *file*) .getParentFile .getParentFile
                            (clojure.java.io/file "data" "persisted" "shinogi.exam.kotoba.edn") str))
           drivers (vec (filter #(= (:type %) :driver) (edn/read-string (slurp seed))))
           r (beat {:drivers drivers
                    :tx-id "shinogi-beat-manual" :as-of "manual" :log-path log-path})]
       (println (str "findings ledger head=" (:head r)
                     " datoms=" (:count r)
                     " drivers=" (:drivers r)
                     " jurisdictions=" (:jurisdictions r)
                     " failure-relief-gap=" (:failure-gap r)
                     " appended=" (:appended r)
                     (when (:reason r) (str " (" (name (:reason r)) ")"))))
       (println (str "stock regimes=" (:regimes r)))
       (println (str "chain=" (k/verify-chain log-path))))))

#?(:clj
   (when (= *file* (System/getProperty "babashka.file"))
     (apply -main *command-line-args*)))
