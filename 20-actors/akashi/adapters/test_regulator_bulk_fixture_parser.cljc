(ns akashi.adapters.test-regulator-bulk-fixture-parser
  "Tests for the akashi regulator-bulk fixture parser (ADR-2606071600 port). Verifies the canonical-
  JSON encoder (sorted keys / compact / escaping) that backs the CIDs, the spend/impression range
  mapping with nil-drop, and a full parse of the real sample fixture with golden CIDs pinned to the
  Python output (byte-for-byte verified: payloadCid / payloadSha256 / snapshotCid / creativeText*
  / domain) so the port is provably 1:1."
  (:require [clojure.test :refer [deftest is]]
            [cheshire.core :as json]
            [akashi.adapters.regulator-bulk-fixture-parser :as p]))

(def ^:private opts
  {:attesting-did "did:web:etzhayyim.com:actor:akashi"
   :source-policy-cid "cid:akashi:source-policy:fixed"
   :method-note-cid "cid:akashi:method-note:fixed"})

(defn- sample [] (json/parse-string (slurp "20-actors/akashi/fixtures/regulator_bulk/sample.json")))

(deftest test-canon-json-sorted-compact-escaped
  (is (= "{\"a\":2,\"b\":1}" (p/canon-json {"b" 1 "a" 2})))   ; keys sorted, no spaces
  (is (= "[1,2,3]" (p/canon-json [1 2 3])))
  (is (= "true" (p/canon-json true)))
  (is (= "false" (p/canon-json false)))
  (is (= "null" (p/canon-json nil)))
  (is (= "\"a\\\"b\"" (p/canon-json "a\"b")))                 ; quote escaped
  (is (= "\"a\\nb\"" (p/canon-json "a\nb")))                  ; newline escaped
  (is (= "{}" (p/canon-json {})))
  (is (= "\"\\u00e9\"" (p/canon-json "é"))))                  ; ensure_ascii (non-ASCII → \uXXXX lowercase)

(deftest test-sha256-json-stable
  ;; canonical → sorted keys means key order does not change the digest
  (is (= (p/sha256-json {"a" 1 "b" 2}) (p/sha256-json {"b" 2 "a" 1}))))

(deftest test-parse-sample-golden-cids
  (let [out (p/parse-regulator-bulk-fixture (sample) opts)
        snap (first (get out "adDisclosureSnapshot"))
        adv (first (get out "advertiserIdentity"))
        cre (first (get out "creativeDisclosure"))
        dl (first (get out "deliveryDisclosure"))]
    ;; golden CIDs/hashes pinned to the Python parser output (byte-for-byte verified)
    (is (= "cid:akashi:payload:98480ae55ad0b0df05d167ecdfbe5e19" (get snap "payloadCid")))
    (is (= "98480ae55ad0b0df05d167ecdfbe5e1913328aabe7217d2e14005e6895a655f5" (get snap "payloadSha256")))
    (is (= "cid:akashi:snapshot:80ad8264f5c71a85d04c4fac328fcc5a" (get adv "sourceSnapshotCid")))
    (is (= "88d0c69341e65567031a86b363ed2f292a16fc5cd7e8f7952bb8daa42ce5edb6" (get cre "creativeTextSha256")))
    (is (= "cid:akashi:creative-text:a9fd548c7961710ab27f68205b2a4e42" (get cre "creativeTextCid")))
    ;; structure
    (is (= "example.org" (get (first (get out "landingEvidence")) "domain")))
    (is (= true (get adv "nonInferred")))
    (is (= "source-verified" (get adv "verifiedStatus")))
    (is (= {"min" 1000 "max" 4999 "currency" "EUR"} (get dl "spendRange")))
    (is (= {"min" 10000 "max" 49999} (get dl "impressionRange")))   ; no currency → dropped
    (is (= ["EU"] (get dl "regionSummary")))))

(deftest test-method-note-and-source-policy
  (let [out (p/parse-regulator-bulk-fixture (sample) opts)
        mn (get out "methodNote")
        sp (get out "sourcePolicySnapshot")]
    (is (= "regulator-bulk-fixture-r1.0" (get mn "version")))
    (is (= p/SOURCE-CODE-CID (get mn "sourceCodeCid")))
    (is (= 3 (count (get mn "limits"))))
    (is (= "public-bulk-export" (get sp "accessMode")))
    (is (= "multi-platform" (get sp "platform")))
    (is (= "cid:akashi:method-note:fixed" (get sp "methodNoteCid")))))

(deftest test-verified-status-and-political-flag-defaults
  ;; advertiser without verifiedStatus → "not-disclosed"; creative without flag → "not-applicable"
  (let [payload {"capturedAt" "2026-01-01T00:00:00Z"
                 "source" {"platform" "p" "sourceUrl" "https://x.test/s" "jurisdiction" "US"}
                 "records" [{"sourceRecordId" "r1" "sourceUrl" "https://x.test/r1"
                             "advertiser" {"displayName" "A"}
                             "creativeText" "hello" "landingUrl" "https://land.test/p"}]}
        out (p/parse-regulator-bulk-fixture payload opts)]
    (is (= "not-disclosed" (get (first (get out "advertiserIdentity")) "verifiedStatus")))
    (is (= "not-applicable" (get (first (get out "creativeDisclosure")) "sourceIssuePoliticalFlag")))
    (is (= "unknown" (get (first (get out "deliveryDisclosure")) "status")))
    ;; absent optional fields dropped (no spendRange / language keys)
    (is (not (contains? (first (get out "deliveryDisclosure")) "spendRange")))
    (is (not (contains? (first (get out "creativeDisclosure")) "language")))
    (is (= "land.test" (get (first (get out "landingEvidence")) "domain")))))
