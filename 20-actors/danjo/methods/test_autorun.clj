;; test_autorun.clj — danjo autonomous heartbeat: persistence + commit-DAG + determinism + G4.
;; Hermetic (temp log), stdlib + sibling clj methods only. Run: bb test_autorun.clj  (from methods/).
(ns root.danjo.methods.test-autorun
  (:require [clojure.string :as str])
  (:import [java.io File]))

(load-file "autorun.clj")
(alias 'au 'root.danjo.methods.autorun)
(alias 'ko 'root.danjo.methods.kotoba)

(def checks (atom 0)) (def fails (atom 0))
(defn check [l p] (swap! checks inc) (if p (println "  ok  " l) (do (swap! fails inc) (println "  FAIL" l))))

(defn- tmp-log []
  (let [f (File/createTempFile "danjo-autorun-test" ".datoms.kotoba.edn")]
    (.delete f) (.getAbsolutePath f)))

;; ── heartbeat persists one content-addressed tx per cycle ──
(let [log (tmp-log)]
  (try
    (let [res (au/run-autonomous 3 {:log-path log})]
      (check "one tx per heartbeat (3 cycles → log length 3)" (= 3 (:log-length res)))
      (check "every heartbeat persisted datoms (77 graph + 7 derived = 84)"
             (every? #(= 84 (:datoms %)) (:beats res)))
      (check "every heartbeat computed ≥1 discrepancy observation"
             (every? #(>= (:observations %) 1) (:beats res)))
      (check "commit-DAG verifies (chain :ok, length 3)"
             (and (:ok (:chain res)) (= 3 (:length (:chain res)))))
      (check "head CID is content-addressed (\"b\"…)" (str/starts-with? (:head-cid res) "b"))
      (check "as-of advances with cycle (no wall clock)"
             (= [20260610 20260611 20260612] (map #(+ au/base-as-of (:cycle %)) (:beats res)))))
    (finally (.delete (File. log)))))

;; ── deterministic / resume-safe: same cycles → same CIDs ──
(let [log-a (tmp-log) log-b (tmp-log)]
  (try
    (let [a (au/run-autonomous 3 {:log-path log-a})
          b (au/run-autonomous 3 {:log-path log-b})]
      (check "deterministic — two fresh runs produce identical per-cycle CIDs"
             (= (map :cid (:beats a)) (map :cid (:beats b))))
      (check "deterministic — identical head CID" (= (:head-cid a) (:head-cid b))))
    (finally (.delete (File. log-a)) (.delete (File. log-b)))))

;; ── append-only: re-running on an existing log extends the chain, never rewrites ──
(let [log (tmp-log)]
  (try
    (au/run-autonomous 2 {:log-path log})
    (let [after (au/run-autonomous 2 {:log-path log})]
      (check "re-run appends (log grows 2 → 4)" (= 4 (:log-length after)))
      (check "chain still verifies after append" (:ok (:chain after))))
    (finally (.delete (File. log)))))

;; ── G4 over the PERSISTED log: non-adjudicating, no verdict attr ──
(let [log (tmp-log)]
  (try
    (au/run-autonomous 1 {:log-path log})
    (let [txs    (ko/read-log log)
          datoms (mapcat :tx/datoms txs)
          attrs  (map #(str (nth % 2)) datoms)
          obs-attrs (filter #(str/starts-with? % ":danjo.obs/") attrs)]
      (check "log persisted observation datoms" (pos? (count obs-attrs)))
      (check "G4 — no verdict attr in the persisted log"
             (not-any? (fn [a] (some #(str/includes? (str/lower-case a) %) ko/forbidden-verdict-tokens)) attrs))
      (check "G4 — :danjo.obs/non-adjudicating true is persisted"
             (some (fn [[_ _ a v]] (and (= :danjo.obs/non-adjudicating a) (true? v))) datoms))
      (check "G5 — a persisted observation carries ≥2 source-record CIDs"
             (some (fn [[_ _ a v]] (and (= :danjo.obs/source-record-cids a) (>= (count v) 2))) datoms)))
    (finally (.delete (File. log)))))

(println (format "── test_autorun: %d checks, %d failures ──" @checks @fails))
(when (pos? @fails) (System/exit 1))
