#!/usr/bin/env bb
;; test_kotoba.clj — shionome kotoba Datom-log writer + content-addressed DAG. ADR-2606072200.
;; Clojure port of test_kotoba.py (9 tests).
(ns shionome.methods.test-kotoba
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [clojure.java.io :as io]
            [shionome.methods.kotoba :as kotoba]
            [shionome.methods.edn :as sedn]
            [shionome.methods.weave :as weave]))

(def ^:private SEED
  (-> *file* io/file .getAbsoluteFile .getParentFile .getParentFile
      (io/file "data" "seed-capital-flow-graph.kotoba.edn")))

(defn- g []
  (weave/weave (sedn/load-edn SEED)))

(defn- tmp-log []
  (doto (java.io.File/createTempFile "shionome-kotoba-test-" ".edn")
    .deleteOnExit))

;; ── tests ─────────────────────────────────────────────────────────────────────

(deftest test-graph-datoms-are-append-only
  (let [datoms (kotoba/graph-datoms (g))]
    (is (seq datoms) "datoms is non-empty")
    (is (every? #(= ":db/add" (first %)) datoms)
        "no :db/retract (非終末論)")))

(deftest test-tx-cid-deterministic
  (let [d (kotoba/graph-datoms (g))]
    (is (= (kotoba/tx-cid d "") (kotoba/tx-cid d ""))
        "tx-cid is deterministic for same datoms + prev")))

(deftest test-tx-cid-depends-on-prev
  (let [d (kotoba/graph-datoms (g))]
    (is (not= (kotoba/tx-cid d "") (kotoba/tx-cid d "bdeadbeef"))
        "tx-cid changes when prev-cid changes")))

(deftest test-append-and-read-roundtrip
  (let [log (tmp-log)
        log-path (.getAbsolutePath log)
        tx  (kotoba/make-tx (kotoba/graph-datoms (g))
                            :tx-id 1 :as-of 20260607 :prev-cid "")
        cid (kotoba/append-tx tx log-path)
        back (kotoba/read-log log-path)]
    (is (= 1 (count back)) "one tx read back")
    (is (= cid (get (first back) ":tx/cid"))
        "CID round-trips through EDN write+read")))

(deftest test-chain-verifies-ok
  (let [log (tmp-log)
        log-path (.getAbsolutePath log)]
    (loop [prev "" i 1]
      (when (<= i 3)
        (let [tx (kotoba/make-tx (kotoba/graph-datoms (g))
                                 :tx-id i :as-of (+ 20260607 i) :prev-cid prev)
              cid (kotoba/append-tx tx log-path)]
          (recur cid (inc i)))))
    (let [v (kotoba/verify-chain log-path)]
      (is (true? (:ok v)) "chain verifies ok")
      (is (= 3 (:length v)) "length is 3"))))

(deftest test-head-cid-is-last
  (let [log (tmp-log)
        log-path (.getAbsolutePath log)]
    (let [last-cid
          (loop [i 1 last-cid ""]
            (if (> i 2)
              last-cid
              (let [tx  (kotoba/make-tx (kotoba/graph-datoms (g))
                                        :tx-id i :as-of (+ 20260607 i)
                                        :prev-cid (kotoba/head-cid log-path))
                    cid (kotoba/append-tx tx log-path)]
                (recur (inc i) cid))))]
      (is (= last-cid (kotoba/head-cid log-path))
          "head-cid is the last appended CID"))))

(deftest test-tamper-breaks-chain
  (let [log (tmp-log)
        log-path (.getAbsolutePath log)]
    ;; append 2 txs
    (loop [i 1]
      (when (<= i 2)
        (let [tx (kotoba/make-tx (kotoba/graph-datoms (g))
                                 :tx-id i :as-of (+ 20260607 i)
                                 :prev-cid (kotoba/head-cid log-path))]
          (kotoba/append-tx tx log-path)
          (recur (inc i)))))
    ;; tamper: flip "US equities" → "TAMPERED" in the first tx line
    (let [text  (slurp log-path :encoding "UTF-8")
          lines (clojure.string/split-lines text)
          ;; lines[0] = header comment, lines[1] = first tx
          tampered-lines (assoc (vec lines) 1
                                (clojure.string/replace (nth lines 1) "US equities" "TAMPERED"))]
      (spit log-path (str (clojure.string/join "\n" tampered-lines) "\n") :encoding "UTF-8"))
    (is (false? (:ok (kotoba/verify-chain log-path)))
        "tampered chain fails verification")))

(deftest test-post-datoms-status-dry-run
  (let [posts   [{":post/subject" "netflow"
                  ":post/status"  ":dry-run"
                  ":post/body"    "x"}]
        datoms  (kotoba/post-datoms posts)
        statuses (mapv #(nth % 3) (filter #(= ":post/status" (nth % 2)) datoms))]
    (is (= [":dry-run"] statuses)
        "post status is :dry-run")))

(deftest test-post-body-with-newlines-roundtrips
  ;; the bug that broke the DAG: a post body has \n\n; it must survive write→read
  (let [log (tmp-log)
        log-path (.getAbsolutePath log)
        posts [{":post/subject" "regime"
                ":post/status"  ":dry-run"
                ":post/body"    "line one\n\nline two with 日本語"}]
        tx  (kotoba/make-tx (kotoba/post-datoms posts)
                            :tx-id 1 :as-of 20260607 :prev-cid "")]
    (kotoba/append-tx tx log-path)
    (is (true? (:ok (kotoba/verify-chain log-path)))
        "chain with newline body verifies ok")))

;; ── runner ────────────────────────────────────────────────────────────────────

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (run-tests 'shionome.methods.test-kotoba)]
    (System/exit (if (zero? (+ fail error)) 0 1))))
