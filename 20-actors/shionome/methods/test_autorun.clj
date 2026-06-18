#!/usr/bin/env bb
;; test_autorun.clj — 潮目 (shionome) AUTONOMOUS heartbeat loop tests. ADR-2606072200.
;;
;; Proves the actor runs its full observe→validate→weave→analyze→dry-run-post→persist
;; cycle by ITSELF over the kotoba Datom log, append-only + content-addressed,
;; with NO live external I/O. Port of test_autorun.py.
(ns shionome.methods.test-autorun
  (:require [shionome.methods.autorun :as autorun]
            [shionome.methods.kotoba :as k]
            [clojure.test :refer [deftest is testing run-tests]]
            [clojure.java.io :as io]))

;; ── helpers ───────────────────────────────────────────────────────────────────

(defn- tmp-log []
  (doto (java.io.File/createTempFile "shionome-test-autorun" ".edn")
    (.deleteOnExit)))

;; ── tests (mirrors test_autorun.py, all 6) ───────────────────────────────────

(deftest test-single-cycle-persists-tx
  (let [log (tmp-log)]
    (.delete log)  ; start fresh (createTempFile creates it)
    (let [beat (autorun/run-cycle 1 (autorun/default-seed) log)]
      (is (= "risk-on" (:regime beat)))
      (is (pos? (:datoms beat)))
      (is (= 3 (:posts beat)))
      (is (= 1 (count (k/read-log log)))))))

(deftest test-multi-cycle-grows-append-only
  (let [log (tmp-log)]
    (.delete log)
    (let [res (autorun/run-autonomous 3 (autorun/default-seed) log)]
      (is (= 3 (:cycles res)))
      (is (= 3 (:log-length res)))
      (is (true? (:ok (:chain res)))))))

(deftest test-cycles-link-into-dag
  (let [log (tmp-log)]
    (.delete log)
    (autorun/run-autonomous 2 (autorun/default-seed) log)
    (let [txs (k/read-log log)]
      ;; tx 2's prev is tx 1's cid (a real commit-DAG, not independent snapshots)
      (is (= (get (nth txs 0) ":tx/cid")
             (get (nth txs 1) ":tx/prev"))))))

(deftest test-run-is-deterministic-resume-safe
  (let [a-log (tmp-log)
        b-log (tmp-log)]
    (.delete a-log)
    (.delete b-log)
    (let [a (autorun/run-autonomous 2 (autorun/default-seed) a-log)
          b (autorun/run-autonomous 2 (autorun/default-seed) b-log)]
      ;; same input → same content address
      (is (= (:head-cid a) (:head-cid b))))))

(deftest test-persisted-posts-are-dry-run-only
  (let [log (tmp-log)]
    (.delete log)
    (autorun/run-cycle 1 (autorun/default-seed) log)
    (let [txs     (k/read-log log)
          datoms  (get (first txs) ":tx/datoms")
          ;; datom shape: [op entity attr value] — extract value (idx 3) when attr == ":post/status"
          statuses (map #(nth % 3) (filter #(= (nth % 2) ":post/status") datoms))]
      ;; G8 — never :published
      (is (seq statuses))
      (is (every? #(= ":dry-run" %) statuses)))))

(deftest test-no-published-status-anywhere
  (let [log (tmp-log)]
    (.delete log)
    (autorun/run-autonomous 2 (autorun/default-seed) log)
    (let [blob (slurp log :encoding "UTF-8")]
      ;; outward publication stays G8-gated
      (is (not (clojure.string/includes? blob ":published"))))))

;; ── runner ────────────────────────────────────────────────────────────────────

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (clojure.test/run-tests 'shionome.methods.test-autorun)]
    (System/exit (if (zero? (+ fail error)) 0 1))))
