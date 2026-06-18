#!/usr/bin/env bb
;; test_autorun.clj — kosatsu autonomous competing-claim heartbeat + kotoba Datom-log invariants.
;; ADR-2606072000. Babashka port of test_autorun.py. Stdlib only, hermetic.
;;
;; Guards the autonomy + persistence + neutral-competing-claim contract for the fleet:
;;
;;   - the loop persists one content-addressed tx per heartbeat to an append-only log;
;;   - the log is a verifiable commit-DAG (every CID recomputes; tamper is detected);
;;   - determinism / resume-safe: persisted datoms are canonically ordered → CID reproducible
;;     across processes regardless of report's set-iteration order;
;;   - it is append-only; derived :kosatsu.div/* signals are flagged :kosatsu.div/derived;
;;   - every designation is an ATTRIBUTED event: each carries a :designation/asserter, and the
;;     asserter is NEVER etzhayyim (etzhayyim authors no designation);
;;   - no verdict / no per-subject score: no score/verdict attr is representable; the per-subject
;;     divergence :kosatsu.div/class is one of {contested | unanimous | single-asserter};
;;   - it does NO external I/O (offline seed, local persist — G7/G8 stay gated).
(ns kosatsu.methods.test-autorun
  (:require [kosatsu.methods.autorun :as autorun]
            [kosatsu.methods.kotoba :as kotoba]
            [clojure.test :refer [deftest is testing run-tests]]
            [clojure.java.io :as io]
            [clojure.string :as str]))

;; ── temp-log helper ───────────────────────────────────────────────────────────

(defn- tmp-log
  "Create a temp file path (file does not exist yet — mirrors Python _tmp_log).
  Returns a java.io.File."
  []
  (let [f (java.io.File/createTempFile "kosatsu-test" ".datoms.kotoba.edn")]
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
            ;; tamper: flip one :kosatsu.div/derived true → false in tx 1
            (let [content (slurp log :encoding "UTF-8")
                  lines   (str/split-lines content)
                  patched (loop [ls lines found? false out []]
                            (if (empty? ls)
                              out
                              (let [ln (first ls)]
                                (if (and (not found?) (str/includes? ln ":tx/id 1 "))
                                  (recur (rest ls) true
                                         (conj out (str/replace-first
                                                    ln ":kosatsu.div/derived true"
                                                    ":kosatsu.div/derived false")))
                                  (recur (rest ls) found? (conj out ln))))))]
              (spit log (str (str/join "\n" patched) "\n") :encoding "UTF-8"))
            (let [v (kotoba/verify-chain log)]
              (is (and (not (:ok v)) (= 0 (:broken-at v)))
                  "tampering an earlier tx breaks the chain")))))
      (finally
        (delete-if-exists log)))))

;; ── test_every_designation_attributed ────────────────────────────────────────

(deftest test-every-designation-attributed
  ;; etzhayyim authors NO designation: every designation event carries a non-etzhayyim asserter.
  (let [log (tmp-log)]
    (try
      (do
        (autorun/run-cycle 1 (autorun/default-seed*) log)
        (let [datoms     (get (first (kotoba/read-log log)) ":tx/datoms")
              ;; entities that have at least one :designation/* attribute
              desig-ents (into #{} (keep (fn [d]
                                           (when (str/starts-with? (str (nth d 2)) ":designation/")
                                             (nth d 1)))
                                         datoms))]
          (is (pos? (count desig-ents)) "designation events persisted")
          (doseq [e desig-ents]
            (let [asserters (filterv #(and (= (nth % 1) e)
                                           (= (nth % 2) ":designation/asserter"))
                                     datoms)]
              (is (= 1 (count asserters))
                  (str "designation " e " carries exactly one :asserter"))
              (is (and (seq asserters)
                       (not (str/includes? (str/lower-case (str (nth (first asserters) 3)))
                                           "etzhayyim")))
                  (str "designation " e " asserter is NOT etzhayyim (etzhayyim authors no designation)"))))))
      (finally
        (delete-if-exists log)))))

;; ── test_no_score_no_verdict_neutral_class ────────────────────────────────────

(deftest test-no-score-no-verdict-neutral-class
  (let [log (tmp-log)]
    (try
      (do
        (autorun/run-cycle 1 (autorun/default-seed*) log)
        (let [datoms  (get (first (kotoba/read-log log)) ":tx/datoms")
              attrs   (into #{} (map #(str/lower-case (str (nth % 2))) datoms))]
          (doseq [tok ["score" "rank" "verdict" "guilt" "legitimacy" "true-crime" "trustworthiness"]]
            (is (not (some #(str/includes? % tok) attrs))
                (str "no `" tok "` attr in the log (no verdict / no score)")))
          (let [classes (into #{} (keep #(when (= (nth % 2) ":kosatsu.div/class") (nth % 3))
                                        datoms))]
            (is (and (seq classes)
                     (every? #{":contested" ":unanimous" ":single-asserter"} classes))
                (str "divergence class ∈ {contested,unanimous,single-asserter} (neutral fact), got " classes)))
          (let [ops (into #{} (map #(nth % 0) datoms))]
            (is (= #{":db/add"} ops)
                "every datom is append-only :db/add (no :db/retract)"))))
      (finally
        (delete-if-exists log)))))

;; ── test_no_external_io ───────────────────────────────────────────────────────

(deftest test-no-external-io
  ;; Read the source text of autorun.clj and kotoba.clj and confirm no banned I/O symbols.
  (let [here       (-> *file* io/file .getAbsoluteFile .getParentFile)
        autorun-src (slurp (io/file here "autorun.clj") :encoding "UTF-8")
        kotoba-src  (slurp (io/file here "kotoba.clj") :encoding "UTF-8")
        src         (str autorun-src kotoba-src)]
    (doseq [banned ["urllib" "http.client" "socket" "requests" "subprocess"]]
      (is (not (str/includes? src banned))
          (str "autorun/kotoba does no external I/O (no `" banned "`)")))))

;; ── test runner ──────────────────────────────────────────────────────────────

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (clojure.test/run-tests 'kosatsu.methods.test-autorun)]
    (System/exit (if (zero? (+ fail error)) 0 1))))
