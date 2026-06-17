#!/usr/bin/env bb
;; Clojure mirror of methods/test_request.py — himotoki 繙き disclosure-request gates.
(ns himotoki.methods.test-request
  "1:1 port of the request.py gate suite: registry load + stable ids, DSAR vs FOIA
  classification, G3 own-data-only, G4 true-requester + no-pretext, G6 PII-as-encrypted
  -envelope (never plaintext), G8 no mass-filing, G14 verify-before-dispatch, G10
  outbound-gated, and render-edn invariant markers.

  Run:  bb --classpath 20-actors 20-actors/himotoki/methods/test_request.clj"
  (:require [himotoki.methods.request :as r]
            [clojure.java.io :as io]
            [clojure.string :as str]
            [clojure.test :refer [deftest is run-tests]]))

(def ^:private this-file *file*)
(defn- actor-root [] (-> this-file io/file .getAbsoluteFile .getParentFile .getParentFile))
(defn- registry [] (r/load-registry (str (io/file (actor-root) "registry" "targets.seed.json"))))

(def MEMBER {"requesterDid" "did:web:etzhayyim.com:member:alice" "ownDataOnly" true
             "subjectEnvelopeRef" "com.etzhayyim.encrypted:env:alice"})

(defn- raises? [f] (try (f) false (catch Exception _ true)))
(defn- a-dsar-target [reg] (first (filter r/is-dsar (vals reg))))

(deftest registry-loads-with-stable-ids
  (let [reg (registry)]
    (is (seq reg))
    (is (contains? reg "Discord Inc.:ccpa-110"))))

(deftest dsar-classification
  (is (r/is-dsar {"regime" "ccpa-110"}))
  (is (r/is-dsar {"regime" "gdpr-15"}))
  (is (r/is-dsar {"regime" "appi-33"}))
  (is (not (r/is-dsar {"regime" "us-foia"}))))

(deftest dsar-requires-own-data-only-g3
  (let [t (a-dsar-target (registry))]
    (is (raises? #(r/build-request t (assoc MEMBER "ownDataOnly" false))))))

(deftest request-requires-true-requester-g4
  (let [t (a-dsar-target (registry))]
    (is (raises? #(r/build-request t {"ownDataOnly" true
                                      "subjectEnvelopeRef" "com.etzhayyim.encrypted:env:x"})))))

(deftest pretext-field-refused-g4
  (let [t (a-dsar-target (registry))]
    (is (raises? #(r/build-request t (assoc MEMBER "sockpuppet" "fake-alice"))))))

(deftest plaintext-pii-refused-g6
  (let [t (a-dsar-target (registry))]
    (is (raises? #(r/build-request t (assoc MEMBER "email" "alice@example.com"))))))

(deftest non-envelope-subject-ref-refused-g6
  (let [t (a-dsar-target (registry))]
    (is (raises? #(r/build-request t (assoc MEMBER "subjectEnvelopeRef" "alice plaintext"))))))

(deftest valid-draft-carries-envelope-not-plaintext
  (let [d (r/build-request (a-dsar-target (registry)) MEMBER)]
    (is (str/starts-with? (get d "subjectEnvelopeRef") "com.etzhayyim.encrypted:"))
    (is (not (contains? d "name")))
    (is (not (contains? d "email")))
    (is (false? (get d "dispatchReady")))))

(deftest dispatch-refused-against-unverified-target-g14
  (let [[allowed reason] (r/can-dispatch (a-dsar-target (registry)) true)]
    (is (false? allowed))
    (is (str/includes? reason "G14"))))

(deftest dispatch-refused-without-operator-gate-g10
  (let [t (assoc (a-dsar-target (registry)) "verificationStatus" "verified")
        [allowed reason] (r/can-dispatch t false)]
    (is (false? allowed))
    (is (str/includes? reason "G10"))))

(deftest dispatch-allowed-when-verified-and-gated
  (let [t (assoc (a-dsar-target (registry)) "verificationStatus" "verified")
        [allowed _] (r/can-dispatch t true)]
    (is (true? allowed))))

(deftest mass-filing-refused-g8
  (let [reg (registry)
        ids (take (inc r/MAX-BATCH) (keys reg))]
    (is (raises? #(r/build-batch ids MEMBER reg)))))

(deftest render-edn-marks-invariants
  (let [edn (r/render-edn [(r/build-request (a-dsar-target (registry)) MEMBER)])]
    (is (str/includes? edn ":himotoki.req/own-data-only"))
    (is (str/includes? edn ":himotoki.req/dispatch-ready false"))
    (is (str/includes? edn "encrypted"))
    (is (str/includes? edn "gated"))))

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (run-tests 'himotoki.methods.test-request)]
    (System/exit (if (zero? (+ fail error)) 0 1))))
