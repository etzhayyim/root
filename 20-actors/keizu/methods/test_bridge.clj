#!/usr/bin/env bb
;; Working Clojure port of methods/test_bridge.py.
(ns keizu.methods.test-bridge
  "Tests for the 系図 (keizu) cross-actor compose bridge (methods/bridge.clj). ADR-2606066000.

  Pins parity with `python3 test_bridge.py` (10/10).

  Run:  bb --classpath 20-actors 20-actors/keizu/methods/test_bridge.clj"
  (:require [keizu.methods.bridge :as bridge]
            [keizu.methods.weave :as w]
            [clojure.test :refer [deftest is run-tests]]))

;; ── test fixtures (mirrors test_bridge.py) ────────────────────────────────────

(def ^:private KANAE-OK
  {"id" "f1" "flowType" "appropriation" "donor" "jp-mof" "recipient" "jp-meti"
   "amount" 1.0e9 "currency" "JPY" "asOf" 20250401
   "sources" ["https://a.gov/" "https://b.gov/"]})

(def ^:private DANJO-OK
  {"id" "x1" "linkType" "awardee-officer-ubo-link" "from" "jp-vendor-x"
   "to" "jp-fsc-biz-1" "sourceRecordCids" ["cid:a" "cid:b"]})

;; ── tests ────────────────────────────────────────────────────────────────────

(deftest test-kanae-flow-maps-to-money
  ;; bridge_kanae_flow(_KANAE_OK): kind=":budget-outlay", payer="jp-mof", payee="jp-meti", id starts "kanae:"
  (let [m (bridge/bridge-kanae-flow KANAE-OK)]
    (is (= ":budget-outlay" (get m ":money/kind")))
    (is (= "jp-mof"         (get m ":money/payer")))
    (is (= "jp-meti"        (get m ":money/payee")))
    (is (clojure.string/starts-with? (get m ":money/id") "kanae:"))))

(deftest test-kanae-unknown-flowtype-refused
  ;; bridge_kanae_flow with flowType="mystery" → raises containing "unknown kanae flowType"
  (let [bad (assoc KANAE-OK "flowType" "mystery")]
    (is (thrown-with-msg? clojure.lang.ExceptionInfo #"unknown kanae flowType"
                          (bridge/bridge-kanae-flow bad)))))

(deftest test-kanae-under-sourced-refused-by-keizu-gate
  ;; sources=["only-one"] → validate-money raises with "G3" (≥2 sources required)
  (let [bad (assoc KANAE-OK "sources" ["only-one"])]
    (is (thrown-with-msg? clojure.lang.ExceptionInfo #"G3"
                          (bridge/bridge-kanae-flow bad)))))

(deftest test-danjo-crossref-maps-to-rel
  ;; bridge_danjo_crossref(_DANJO_OK): kind=":co-membership", non-adjudicating-notice=true, id starts "danjo:"
  (let [r (bridge/bridge-danjo-crossref DANJO-OK)]
    (is (= ":co-membership" (get r ":rel/kind")))
    (is (true? (get r ":rel/non-adjudicating-notice")))
    (is (clojure.string/starts-with? (get r ":rel/id") "danjo:"))))

(deftest test-danjo-verdict-category-refused-at-import
  ;; linkType="corruption" is in VERDICT-TOKENS → raises containing "verdict"
  (let [bad (assoc DANJO-OK "linkType" "corruption")]
    (is (thrown-with-msg? clojure.lang.ExceptionInfo #"verdict"
                          (bridge/bridge-danjo-crossref bad)))))

(deftest test-danjo-unmapped-linktype-refused
  ;; linkType="some-new-thing" not in map → raises containing "unmapped"
  (let [bad (assoc DANJO-OK "linkType" "some-new-thing")]
    (is (thrown-with-msg? clojure.lang.ExceptionInfo #"unmapped"
                          (bridge/bridge-danjo-crossref bad)))))

(deftest test-danjo-under-sourced-refused
  ;; sourceRecordCids=["only-one"] → validate-rel raises with "G3"
  (let [bad (assoc DANJO-OK "sourceRecordCids" ["only-one"])]
    (is (thrown-with-msg? clojure.lang.ExceptionInfo #"G3"
                          (bridge/bridge-danjo-crossref bad)))))

(deftest test-batch-composes-both
  ;; bridge_batch with one kanae + one danjo → {"money" [1] "rels" [1]}
  (let [out (bridge/bridge-batch {"kanae" [KANAE-OK] "danjo" [DANJO-OK]})]
    (is (= 1 (count (get out "money"))))
    (is (= 1 (count (get out "rels"))))))

(deftest test-batch-fails-whole-on-one-violation
  ;; a second danjo with linkType="bribe" (VERDICT-TOKEN) → the whole batch raises
  (let [bad (assoc DANJO-OK "linkType" "bribe")]
    (is (thrown-with-msg? clojure.lang.ExceptionInfo #"verdict"
                          (bridge/bridge-batch {"danjo" [DANJO-OK bad]})))))

(deftest test-bridged-records-weave-clean
  ;; the bridged datoms must pass the SAME validation the seed does
  (let [out (bridge/bridge-batch {"kanae" [KANAE-OK] "danjo" [DANJO-OK]})]
    ;; validate-money and validate-rel must not throw (they were called inside bridge already,
    ;; but we call them again to confirm idempotence — matching what test_bridge.py does)
    (is (nil? (w/validate-money (first (get out "money")))))
    (is (nil? (w/validate-rel   (first (get out "rels")))))))

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (clojure.test/run-tests 'keizu.methods.test-bridge)]
    (System/exit (if (zero? (+ fail error)) 0 1))))
