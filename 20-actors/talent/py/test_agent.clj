#!/usr/bin/env bb
;; Test harness for talent.py.agent — port of test_agent.py (unittest → clojure.test).
;;
;; Run:  bb --classpath 20-actors 20-actors/talent/py/test_agent.clj
(ns talent.py.test-agent
  "talent — test harness (clojure.test; no kotoba host needed).

  Verifies the structural invariants of ADR-2606072600:
    G1 self-sovereign       — third-party register refused; prohibited source ingest refused
    G3 signal-e2e           — plaintext identifying field refused; ciphertext accepted
    G2 cohort-first k-anon  — cohort below k suppressed; ≥k returns aggregate only
    G4 hard-delete          — forget_self removes the profile entirely (no soft-delete flag)"
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [talent.py.agent :as agent]))

(def ALICE "did:plc:alice")
(def BOB   "did:plc:bob")

(defn- _profile
  "Base profile matching test_agent.py's _profile(**kw)."
  [& {:as kw}]
  (merge {"isco" "2512" "country" "JP" "skills" ["python" "rust"]} kw))

;; ── SelfSovereign ─────────────────────────────────────────────────────────────

(deftest test-self-register-ok
  (let [out (agent/register_self ALICE ALICE (_profile))]
    (is (= "registered" (get out "state")))
    (is (= ALICE (get-in out ["profile" "registeredBy"])))
    (is (= (agent/subject_hash ALICE) (get-in out ["profile" "subjectDidHash"])))))

(deftest test-third-party-refused
  (let [out (agent/register_self BOB ALICE (_profile))]
    (is (= "refused" (get out "state")))
    (is (.contains ^String (get out "reason") "G1"))))

(deftest test-prohibited-source-ingest-refused
  (doseq [src ["linkedin" "indeed" "scraped-db" "purchased-list"]]
    (is (= "refused" (get (agent/ingest_external src) "state")))))

(deftest test-allowed-enrichment
  (is (= "allowed" (get (agent/ingest_external "orcid") "state"))))

(deftest test-prohibited-enrichment-on-profile-refused
  (let [out (agent/register_self ALICE ALICE (_profile "enrichmentSource" "linkedin"))]
    (is (= "refused" (get out "state")))))

;; ── SignalE2E ─────────────────────────────────────────────────────────────────

(deftest test-plaintext-pii-refused
  (let [out (agent/register_self ALICE ALICE (_profile "email" "alice@example.com"))]
    (is (= "refused" (get out "state")))
    (is (.contains ^String (get out "reason") "G3"))))

(deftest test-ciphertext-pii-ok
  (let [out (agent/register_self ALICE ALICE (_profile "email" "signal:v1:deadbeef"))]
    (is (= "registered" (get out "state")))))

(deftest test-is-encrypted
  (is (true?  (agent/is_encrypted "signal:v1:abc")))
  (is (false? (agent/is_encrypted "plain"))))

;; ── CohortKAnon ───────────────────────────────────────────────────────────────

(deftest test-below-k-suppressed
  (let [profiles (repeatedly 3 #(_profile))
        out      (agent/cohort_stats "2512" "JP" (vec profiles))]
    (is (true? (get out "suppressed")))
    (is (nil?  (get out "count")))))

(deftest test-at-or-above-k-aggregate
  (let [profiles (repeatedly 5 #(_profile))
        out      (agent/cohort_stats "2512" "JP" (vec profiles))]
    (is (false? (get out "suppressed")))
    (is (= 5 (get out "count")))
    (is (some #{"python"} (get out "topSkills")))))

(deftest test-no-individual-field-in-output
  (let [profiles (repeatedly 6 #(_profile "email" "signal:v1:x"))
        out      (agent/cohort_stats "2512" "JP" (vec profiles))]
    (doseq [k (keys out)]
      (is (not (.contains (.toLowerCase ^String (name k)) "email")))
      (is (not (.contains (.toLowerCase ^String (name k)) "profile")))
      (is (not (.contains (.toLowerCase ^String (name k)) "name"))))))

;; ── HardDelete ────────────────────────────────────────────────────────────────

(defn- make-store []
  [{"subjectDidHash" (agent/subject_hash ALICE) "isco" "2512"}
   {"subjectDidHash" (agent/subject_hash BOB)   "isco" "2512"}])

(deftest test-forget-removes-entirely
  (let [store (make-store)
        out   (agent/forget_self ALICE ALICE store)]
    (is (= "forgotten" (get out "state")))
    (is (= 1 (get out "hardDeleted")))
    (let [hashes (map #(get % "subjectDidHash") (get out "store"))]
      (is (not (some #{(agent/subject_hash ALICE)} hashes))))
    (doseq [p (get out "store")]
      (is (not (contains? p "_alive"))))))

(deftest test-forget-others-refused
  (let [out (agent/forget_self BOB ALICE (make-store))]
    (is (= "refused" (get out "state")))))

;; ── Enrichment ────────────────────────────────────────────────────────────────

(defn- _prof [] {"isco" "2512" "country" "JP" "skills" ["python"]})

(deftest test-self-enrich-merges-skills
  (let [out (agent/attach_enrichment ALICE ALICE (_prof) "github-public"
                                     {"skills" ["rust" "python"]})]
    (is (= "enriched" (get out "state")))
    (is (= ["python" "rust"] (sort (get-in out ["profile" "skills"]))))
    (is (= ["github-public"] (get-in out ["profile" "enrichmentProvenance"])))))

(deftest test-third-party-enrich-refused
  (let [out (agent/attach_enrichment BOB ALICE (_prof) "orcid" {"skills" ["x"]})]
    (is (= "refused" (get out "state")))
    (is (.contains ^String (get out "reason") "G1"))))

(deftest test-prohibited-source-refused
  (let [out (agent/attach_enrichment ALICE ALICE (_prof) "linkedin" {"skills" ["x"]})]
    (is (= "refused" (get out "state")))))

(deftest test-plaintext-pii-enrichment-refused
  (let [out (agent/attach_enrichment ALICE ALICE (_prof) "orcid" {"email" "a@b.com"})]
    (is (= "refused" (get out "state")))
    (is (.contains ^String (get out "reason") "G3"))))

;; ── ListOccupations ───────────────────────────────────────────────────────────

(deftest test-below-k-cohort-not-listed
  (let [profiles (vec (repeatedly 3 (fn [] {"isco" "2512" "country" "JP" "skills" []})))
        out      (agent/list_occupations profiles)]
    (is (= [] out))))

(deftest test-at-or-above-k-listed
  (let [profiles (vec (concat (repeatedly 5 (fn [] {"isco" "2512" "country" "JP"}))
                              (repeatedly 2 (fn [] {"isco" "2512" "country" "US"}))))
        out      (agent/list_occupations profiles)]
    (is (= [{"isco" "2512" "country" "JP" "count" 5}] out))))

;; ── runner ────────────────────────────────────────────────────────────────────

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (clojure.test/run-tests 'talent.py.test-agent)]
    (System/exit (if (zero? (+ fail error)) 0 1))))
