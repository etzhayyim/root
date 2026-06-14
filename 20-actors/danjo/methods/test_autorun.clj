;; test_autorun.clj — the autonomous heartbeat: deterministic, resume-safe, commit-DAG verified.
;; Run: bb test_autorun.clj   (or: clojure -M test_autorun.clj)   from methods/.
(ns root.danjo.methods.test-autorun
  (:require [clojure.java.io :as io]))

(load-file "autorun.clj")
(alias 'a  'root.danjo.methods.autorun)
(alias 'rl 'root.danjo.methods.revenue-ledger)

(def checks (atom 0)) (def fails (atom 0))
(defn check [l p] (swap! checks inc) (if p (println "  ok  " l) (do (swap! fails inc) (println "  FAIL" l))))
(defn tmp [] (str (System/getProperty "java.io.tmpdir") "/danjo-autorun-" (rand-int 1000000) ".edn"))

;; ── a heartbeat composes the whole pipeline into one tx/cycle ──
(let [log (tmp)
      r (a/heartbeat! {:cycles 2 :fresh true :log-path log})]
  (check "2 cycles → 2 txs"                 (= 2 (:length (:chain r))))
  (check "chain verifies (commit-DAG)"      (:ok (:chain r)))
  (check "heartbeat composes the full datom set (>600/cycle)" (> (:datoms-per-cycle r) 600))

  ;; ── resume-safe: re-running (not fresh) appends, never corrupts ──
  (let [r2 (a/heartbeat! {:cycles 1 :fresh false :log-path log})]
    (check "resume appends a 3rd tx"        (= 3 (:length (:chain r2))))
    (check "chain still verifies after resume" (:ok (:chain r2))))
  (.delete (io/file log)))

;; ── deterministic: two fresh runs produce a byte-identical head CID ──
(let [l1 (tmp) l2 (tmp)
      h1 (:head-cid (a/heartbeat! {:cycles 2 :fresh true :log-path l1}))
      h2 (:head-cid (a/heartbeat! {:cycles 2 :fresh true :log-path l2}))]
  (check "deterministic head-cid across fresh runs" (= h1 h2))
  (.delete (io/file l1)) (.delete (io/file l2)))

;; ── tamper-evidence: editing a persisted datom breaks verify-chain ──
(let [log (tmp)]
  (a/heartbeat! {:cycles 1 :fresh true :log-path log})
  (let [orig (slurp log)
        tampered (clojure.string/replace orig "14500000000000" "14500000000001")]
    (spit log tampered)
    (check "tampered amount fails verify-chain" (not (:ok (rl/verify-chain log)))))
  (.delete (io/file log)))

(println (format "── autorun: %d checks, %d failures ──" @checks @fails))
(when (pos? @fails) (System/exit 1))
