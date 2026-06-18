#!/usr/bin/env bb
;; test_autorun.clj — keizu autonomous government-power-relations heartbeat + kotoba
;; Datom-log invariants. ADR-2606066000. Babashka port of test_autorun.py.
;; Stdlib only, hermetic.
;;
;; Guards the autonomy + persistence + accountability-not-target-list contract for the fleet:
;;
;;   - the loop persists one content-addressed tx per heartbeat to an append-only log;
;;   - the log is a verifiable commit-DAG (every CID recomputes; tamper is detected);
;;   - determinism / resume-safe: persisted datoms are canonically ordered → CID reproducible
;;     across processes regardless of concentration's set-iteration order;
;;   - it is append-only; derived :keizu.conc/* signals are flagged :keizu.conc/derived;
;;   - G4 edge-primary / non-adjudicating: revolving-door + award-and-fund datoms carry
;;     `:keizu.conc/non-adjudicating true` (a co-occurrence of disclosed flows, NOT an allegation);
;;   - G1 no-doxxing: NO PII node attr (email/phone/address/dob/…) appears in the log;
;;   - it does NO external I/O (offline seed, local persist — G7/G8 stay gated).
(ns keizu.methods.test-autorun
  (:require [keizu.methods.autorun :as autorun]
            [keizu.methods.kotoba :as kotoba]
            [keizu.methods.weave :as weave]
            [clojure.test :refer [deftest is testing run-tests]]
            [clojure.java.io :as io]
            [clojure.string :as str]))

;; ── temp-log helper ───────────────────────────────────────────────────────────

(defn- tmp-log
  "Create a temp file path (file does not exist yet — mirrors Python _tmp_log).
  Returns a java.io.File."
  []
  (let [f (java.io.File/createTempFile "keizu-test" ".datoms.kotoba.edn")]
    (.delete f)  ;; remove it — tests start fresh
    f))

(defn- delete-if-exists [f]
  (when f
    (let [file (io/file f)]
      (when (.exists file)
        (.delete file)))))

;; ── test_heartbeat_persists ───────────────────────────────────────────────────

(deftest test-heartbeat-persists
  (let [log (tmp-log)]
    (try
      (let [res (autorun/run-autonomous 3 (autorun/default-seed*) log)]
        (is (= 3 (:log-length res)) "one tx per heartbeat")
        (is (every? #(> (:datoms %) 0) (:beats res)) "every heartbeat persisted datoms")
        (is (get (:chain res) :ok) "commit-DAG verifies (chain OK)")
        (is (str/starts-with? (:head-cid res) "b") "head CID is content-addressed"))
      (finally
        (delete-if-exists log)))))

;; ── test_canonical_order_deterministic ───────────────────────────────────────

(deftest test-canonical-order-deterministic
  (let [log (tmp-log)]
    (try
      (do
        (autorun/run-cycle 1 (autorun/default-seed*) log)
        (let [datoms (get (first (kotoba/read-log log)) ":tx/datoms")
              ;; Build the same JSON sort key as Python:
              ;; json.dumps(d, ensure_ascii=False, sort_keys=True) for a list d
              keyed (mapv (fn [d]
                            (str "[" (str/join "," (map autorun/json-val-sk* d)) "]"))
                          datoms)]
          (is (= keyed (sort keyed))
              "persisted datoms are in canonical sorted order (cross-process deterministic)")))
      (finally
        (delete-if-exists log)))))

;; ── test_deterministic_resume_safe ───────────────────────────────────────────

(deftest test-deterministic-resume-safe
  (let [log-a (tmp-log)
        log-b (tmp-log)]
    (try
      (let [ra (autorun/run-autonomous 3 (autorun/default-seed*) log-a)
            rb (autorun/run-autonomous 3 (autorun/default-seed*) log-b)]
        (is (= (mapv :cid (:beats ra)) (mapv :cid (:beats rb)))
            "same cycles → same CIDs (deterministic / resume-safe)"))
      (finally
        (delete-if-exists log-a)
        (delete-if-exists log-b)))))

;; ── test_append_only_and_tamper ───────────────────────────────────────────────

(deftest test-append-only-and-tamper
  (let [log (tmp-log)]
    (try
      (do
        (autorun/run-cycle 1 (autorun/default-seed*) log)
        (let [first-log (kotoba/read-log log)]
          (autorun/run-cycle 2 (autorun/default-seed*) log)
          (let [second-log (kotoba/read-log log)]
            (is (= (inc (count first-log)) (count second-log))
                "second heartbeat appends, does not rewrite")
            (is (= (get (second second-log) ":tx/prev")
                   (get (first first-log) ":tx/cid"))
                "tx 2 links tx 1's CID (commit-DAG)")
            ;; tamper: flip one :keizu.conc/derived true → false in tx 1
            (let [content (slurp log :encoding "UTF-8")
                  lines   (str/split-lines content)
                  patched (loop [ls lines found? false out []]
                            (if (empty? ls)
                              out
                              (let [ln (first ls)]
                                (if (and (not found?) (str/includes? ln ":tx/id 1 "))
                                  (recur (rest ls) true
                                         (conj out (str/replace-first
                                                    ln ":keizu.conc/derived true"
                                                    ":keizu.conc/derived false")))
                                  (recur (rest ls) found? (conj out ln))))))]
              (spit log (str (str/join "\n" patched) "\n") :encoding "UTF-8"))
            (let [v (kotoba/verify-chain log)]
              (is (and (not (:ok v)) (= 0 (:broken-at v)))
                  "tampering an earlier tx breaks the chain")))))
      (finally
        (delete-if-exists log)))))

;; ── test_g4_non_adjudicating_co_occurrence ───────────────────────────────────

(deftest test-g4-non-adjudicating-co-occurrence
  ;; revolving-door + award-and-fund are co-occurrences of disclosed flows, NEVER allegations.
  (let [log (tmp-log)]
    (try
      (do
        (autorun/run-cycle 1 (autorun/default-seed*) log)
        (let [datoms     (get (first (kotoba/read-log log)) ":tx/datoms")
              flagged-ents (into #{} (keep (fn [d]
                                             (when (and (= (nth d 2) ":keizu.conc/non-adjudicating")
                                                        (true? (nth d 3)))
                                               (nth d 1)))
                                           datoms))
              award-ents   (into #{} (keep (fn [d]
                                             (when (= (nth d 2) ":keizu.conc/award-and-fund-node")
                                               (nth d 1)))
                                           datoms))
              revolving-ents (into #{} (keep (fn [d]
                                               (when (= (nth d 2) ":keizu.conc/revolving-from")
                                                 (nth d 1)))
                                             datoms))
              attrs        (into #{} (map #(str/lower-case (str (nth % 2))) datoms))]
          ;; every award + revolving entity carries :keizu.conc/non-adjudicating true
          (doseq [entity (clojure.set/union award-ents revolving-ents)]
            (is (contains? flagged-ents entity)
                (str entity " carries :keizu.conc/non-adjudicating true (G4)")))
          ;; no verdict/allegation attr anywhere
          (doseq [tok ["verdict" "guilt" "corrupt" "bribe" "illegal" "wrongdoing" "allegation"]]
            (is (not (some #(str/includes? % tok) attrs))
                (str "no verdict token `" tok "` in any attr (G4)")))))
      (finally
        (delete-if-exists log)))))

;; ── test_g1_no_doxxing ───────────────────────────────────────────────────────

(deftest test-g1-no-doxxing
  ;; G1: NO PII node attr may reach the log — keizu maps power entities, never private persons.
  (let [log (tmp-log)]
    (try
      (do
        (autorun/run-cycle 1 (autorun/default-seed*) log)
        (let [datoms (get (first (kotoba/read-log log)) ":tx/datoms")
              attrs  (into #{} (map #(str/lower-case (str (nth % 2))) datoms))]
          ;; PII_FORBIDDEN_NODE_ATTRS from weave.cljc
          (doseq [pii weave/PII-FORBIDDEN-NODE-ATTRS]
            (is (not (some (fn [a]
                             (let [local (last (str/split a #"/"))]
                               (str/includes? local pii)))
                           attrs))
                (str "no PII attr containing `" pii "` in the log (G1 no-doxxing)")))
          (let [ops (into #{} (map #(nth % 0) datoms))]
            (is (= #{":db/add"} ops)
                "every datom is append-only :db/add (no :db/retract)"))))
      (finally
        (delete-if-exists log)))))

;; ── test_no_external_io ───────────────────────────────────────────────────────

(deftest test-no-external-io
  ;; Read the source text of autorun.clj and kotoba.clj and confirm no banned I/O symbols.
  (let [here        (-> *file* io/file .getAbsoluteFile .getParentFile)
        autorun-src (slurp (io/file here "autorun.clj") :encoding "UTF-8")
        kotoba-src  (slurp (io/file here "kotoba.clj") :encoding "UTF-8")
        src         (str autorun-src kotoba-src)]
    (doseq [banned ["urllib" "http.client" "socket" "requests" "subprocess"]]
      (is (not (str/includes? src banned))
          (str "autorun/kotoba does no external I/O (no `" banned "`)")))))

;; ── test runner ──────────────────────────────────────────────────────────────

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (clojure.test/run-tests 'keizu.methods.test-autorun)]
    (System/exit (if (zero? (+ fail error)) 0 1))))
