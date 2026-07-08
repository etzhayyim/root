(ns iryo.methods.test-handoff
  (:require [clojure.test :refer [deftest is testing]]
            [clojure.set :as set]
            [iryo.methods.handoff :as handoff]))

(def NOW "2026-07-08T00:00:00Z")

(defn- valid-request []
  {"patientDid" "did:web:patient.iryo.etzhayyim.com:e2e1"
   "encounterDid" "at://did:web:karute.etzhayyim.com/com.etzhayyim.karute.encounter/enc1"
   "facilityDid" "did:web:clinic-example.etzhayyim.com"
   "serviceRequestUris" ["at://did:web:karute.etzhayyim.com/com.etzhayyim.karute.serviceRequest/sr1"]
   "medicationRequestUris" ["at://did:web:karute.etzhayyim.com/com.etzhayyim.karute.medicationRequest/mr1"]
   "consentCapabilityUri" "at://did:web:patient.iryo.etzhayyim.com:e2e1/com.etzhayyim.consent.capability/cap1"})

(defn- valid-capability []
  {"granterDid" "did:web:patient.iryo.etzhayyim.com:e2e1"
   "granteeDid" handoff/iryo-did
   "purpose" "insurance-billing"
   "scope" ["com.etzhayyim.karute.encounter" "com.etzhayyim.karute.serviceRequest" "com.etzhayyim.karute.medicationRequest"]
   "resourceUris" []
   "issuedAt" "2026-06-01T00:00:00Z"
   "expiresAt" "2026-08-01T00:00:00Z"})

;; ── Happy path ───────────────────────────────────────────────────────────────

(deftest test-valid-handoff-is-accepted-into-draft-queue
  (let [out (handoff/handle-ingest (assoc (valid-request) "capability" (valid-capability) "now" NOW))]
    (is (= true (get out "ack")))
    (is (= "pending" (get out "iryoStatus")))
    (is (.startsWith (str (get out "iryoClaimRef")) "iryo-req-"))
    (is (nil? (get out "error")))))

(deftest test-claim-ref-is-deterministic-for-same-request
  (let [state (assoc (valid-request) "capability" (valid-capability) "now" NOW)
        a (handoff/handle-ingest state)
        b (handoff/handle-ingest state)]
    (is (= (get a "iryoClaimRef") (get b "iryoClaimRef")))))

;; ── PHI-free intake gate (G2) ────────────────────────────────────────────────

(deftest test-smuggled-plaintext-field-is-rejected
  (let [bad (assoc (valid-request) "patientName" "山田太郎")
        out (handoff/handle-ingest (assoc bad "capability" (valid-capability) "now" NOW))]
    (is (= false (get out "ack")))
    (is (= "needs-info" (get out "iryoStatus")))
    (is (.contains (str (get out "error")) "unexpected field"))))

(deftest test-patient-did-must-be-a-did
  (let [bad (assoc (valid-request) "patientDid" "not-a-did")
        out (handoff/handle-ingest (assoc bad "capability" (valid-capability) "now" NOW))]
    (is (= false (get out "ack")))
    (is (= "needs-info" (get out "iryoStatus")))
    (is (.contains (str (get out "error")) "is not a DID"))))

(deftest test-service-request-uri-must-be-at-uri
  (let [bad (assoc (valid-request) "serviceRequestUris" ["not-an-at-uri"])
        out (handoff/handle-ingest (assoc bad "capability" (valid-capability) "now" NOW))]
    (is (= false (get out "ack")))
    (is (= "needs-info" (get out "iryoStatus")))
    (is (.contains (str (get out "error")) "not an AT-URI"))))

(deftest test-non-ascii-did-shaped-value-is-rejected-as-smuggled-phi
  ;; passes the "did:" prefix check syntactically but carries a kanji name —
  ;; the ASCII-only defense-in-depth must still catch it (G2 fail-closed).
  (let [bad (assoc (valid-request) "facilityDid" "did:web:患者クリニック.example")
        out (handoff/handle-ingest (assoc bad "capability" (valid-capability) "now" NOW))]
    (is (= false (get out "ack")))
    (is (= "needs-info" (get out "iryoStatus")))
    (is (.contains (str (get out "error")) "non-ASCII"))))

;; ── Consent-capability structural gate (G1/G7) ──────────────────────────────

(deftest test-missing-capability-is-rejected
  (let [out (handoff/handle-ingest (assoc (valid-request) "now" NOW))]
    (is (= false (get out "ack")))
    (is (= "needs-info" (get out "iryoStatus")))
    (is (.contains (str (get out "error")) "no consent capability"))))

(deftest test-wrong-purpose-is-rejected
  (let [cap (assoc (valid-capability) "purpose" "second-opinion")
        out (handoff/handle-ingest (assoc (valid-request) "capability" cap "now" NOW))]
    (is (= false (get out "ack")))
    (is (.contains (str (get out "error")) "purpose"))))

(deftest test-wrong-grantee-is-rejected
  (let [cap (assoc (valid-capability) "granteeDid" "did:web:some-other-vendor.example")
        out (handoff/handle-ingest (assoc (valid-request) "capability" cap "now" NOW))]
    (is (= false (get out "ack")))
    (is (.contains (str (get out "error")) "granteeDid"))))

(deftest test-granter-patient-mismatch-is-rejected
  (let [cap (assoc (valid-capability) "granterDid" "did:web:patient.iryo.etzhayyim.com:someone-else")
        out (handoff/handle-ingest (assoc (valid-request) "capability" cap "now" NOW))]
    (is (= false (get out "ack")))
    (is (.contains (str (get out "error")) "granterDid"))))

(deftest test-revoked-capability-is-rejected
  (let [cap (assoc (valid-capability) "revokedAt" "2026-07-01T00:00:00Z")
        out (handoff/handle-ingest (assoc (valid-request) "capability" cap "now" NOW))]
    (is (= false (get out "ack")))
    (is (.contains (str (get out "error")) "revoked"))))

(deftest test-expired-capability-is-rejected
  (let [cap (assoc (valid-capability) "expiresAt" "2026-07-01T00:00:00Z")
        out (handoff/handle-ingest (assoc (valid-request) "capability" cap "now" NOW))]
    (is (= false (get out "ack")))
    (is (.contains (str (get out "error")) "expired"))))

(deftest test-insufficient-scope-is-rejected
  (let [cap (assoc (valid-capability) "scope" ["com.etzhayyim.karute.encounter"])
        out (handoff/handle-ingest (assoc (valid-request) "capability" cap "now" NOW))]
    (is (= false (get out "ack")))
    (is (.contains (str (get out "error")) "scope"))))

(deftest test-resource-uri-outside-allowlist-is-rejected
  (let [cap (assoc (valid-capability) "resourceUris" ["at://did:web:karute.etzhayyim.com/com.etzhayyim.karute.serviceRequest/some-other-sr"])
        out (handoff/handle-ingest (assoc (valid-request) "capability" cap "now" NOW))]
    (is (= false (get out "ack")))
    (is (.contains (str (get out "error")) "resourceUris allowlist"))))

(deftest test-resource-uri-allowlist-permits-listed-uris
  (let [req (valid-request)
        cap (assoc (valid-capability) "resourceUris"
                   (vec (concat (get req "serviceRequestUris") (get req "medicationRequestUris"))))
        out (handoff/handle-ingest (assoc req "capability" cap "now" NOW))]
    (is (= true (get out "ack")))
    (is (= "pending" (get out "iryoStatus")))))

;; ── G5 non-adjudicating: iryo's own intake gate never adjudicates ──────────

(deftest test-iryo-status-is-never-an-adjudication-verdict
  (testing "success and every gate-failure path only ever return pending/needs-info,
            never accepted/rejected — those verdicts belong to the 審査支払機関"
    (let [scenarios [(assoc (valid-request) "capability" (valid-capability) "now" NOW)
                     (assoc (valid-request) "now" NOW)
                     (assoc (valid-request) "capability" (assoc (valid-capability) "purpose" "second-opinion") "now" NOW)
                     (assoc (valid-request) "capability" (assoc (valid-capability) "revokedAt" "2026-07-01T00:00:00Z") "now" NOW)
                     (assoc (assoc (valid-request) "patientName" "山田太郎") "capability" (valid-capability) "now" NOW)]
          statuses (set (map #(get (handoff/handle-ingest %) "iryoStatus") scenarios))]
      (is (set/subset? statuses #{"pending" "needs-info"})))))
