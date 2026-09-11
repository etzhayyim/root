;; etzhayyim.test-evangelism-visit-record — household visit record + crypto-shred
;; erasure invariants (ADR-2607111500). Run via the aggregate: bb test:helpers
;; Covers: real AEAD round-trip (record-visit!/read-visit, not a mock), the
;; ledger/keystore separation, crypto-shred erasure (post-erase read → :sealed,
;; tombstone recorded), and pending-followups filtering.
(ns etzhayyim.test-evangelism-visit-record
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [etzhayyim.evangelism-visit-record :as evr]))

(def ^:private now "2026-07-11T10:00:00Z")
(def ^:private founder-did "did:key:z6MkfounderPlaceholder")

(defn- fresh [] [(evr/seed-ledger) (evr/seed-keystore)])

(deftest record-visit-round-trips-through-real-encryption
  (testing "record-visit! encrypts; read-visit decrypts back the exact plaintext"
    (let [[ledger ks] (fresh)
          envelope (evr/record-visit! ledger ks {:household-ref "123 Main St, Apt 4"
                                                 :status "interested"
                                                 :note "asked for a return visit"
                                                 :now now :sender founder-did})
          plaintext (evr/read-visit ks envelope)]
      (is (= "123 Main St, Apt 4" (:household-ref plaintext)))
      (is (= "interested" (:status plaintext)))
      (is (= "asked for a return visit" (:note plaintext)))
      (is (= now (:visited-at plaintext))))))

(deftest envelope-carries-no-plaintext-household-data
  (testing "the stored envelope itself has no plaintext household-ref/status field — only ciphertext"
    (let [[ledger ks] (fresh)
          envelope (evr/record-visit! ledger ks {:household-ref "123 Main St" :status "not-home" :now now :sender founder-did})]
      (is (not (contains? envelope :household-ref)))
      (is (not (contains? envelope :status)))
      (is (string? (:ciphertext envelope)))
      (is (= 1 (count (evr/all-envelopes ledger)))))))

(deftest record-rejects-unknown-status
  (testing "a status outside known-statuses throws, not silently accepted"
    (let [[ledger ks] (fresh)]
      (is (thrown? #?(:clj AssertionError :cljs js/Error)
                   (evr/record-visit! ledger ks {:household-ref "1 A St" :status "annoyed" :now now :sender founder-did}))))))

(deftest each-record-gets-a-distinct-key
  (testing "two records for two households get independently-keyed envelopes (no key reuse)"
    (let [[ledger ks] (fresh)
          e1 (evr/record-visit! ledger ks {:household-ref "1 A St" :status "not-home" :now now :sender founder-did})
          e2 (evr/record-visit! ledger ks {:household-ref "2 B St" :status "declined" :now now :sender founder-did})]
      (is (not= (:keyId e1) (:keyId e2)))
      (is (= "1 A St" (:household-ref (evr/read-visit ks e1))))
      (is (= "2 B St" (:household-ref (evr/read-visit ks e2)))))))

(deftest erase-household-crypto-shreds-and-tombstones
  (testing "erase-household! makes the record permanently unreadable and records a sealed tombstone"
    (let [[ledger ks] (fresh)
          envelope (evr/record-visit! ledger ks {:household-ref "9 Z Ave" :status "interested" :now now :sender founder-did})]
      (is (map? (evr/read-visit ks envelope)) "sanity: readable before erasure")
      (evr/erase-household! ledger ks envelope {:actor-did founder-did :now "2026-08-01T09:00:00Z"})
      (is (= :sealed (evr/read-visit ks envelope)) "unreadable after key destruction")
      (is (= 1 (count (evr/all-envelopes ledger))) "the envelope itself is never deleted (permanent memory)")
      (let [ts (first (evr/all-tombstones ledger))]
        (is (= "sealed" (:tombstoneType ts)))
        (is (= "consent-revocation-flush" (:reason ts)))
        (is (= (:keyId envelope) (:supersededKeyId ts)))
        (is (= founder-did (:actorDid ts)))))))

(deftest pending-followups-filters-and-sorts
  (testing "only interested/return-visit/bible-study surface, oldest-visited first; not-home/declined are excluded"
    (let [[ledger ks] (fresh)]
      (evr/record-visit! ledger ks {:household-ref "A" :status "not-home" :now "2026-07-01T09:00:00Z" :sender founder-did})
      (evr/record-visit! ledger ks {:household-ref "B" :status "interested" :now "2026-07-15T09:00:00Z" :sender founder-did})
      (evr/record-visit! ledger ks {:household-ref "C" :status "declined" :now "2026-07-10T09:00:00Z" :sender founder-did})
      (evr/record-visit! ledger ks {:household-ref "D" :status "bible-study" :now "2026-07-05T09:00:00Z" :sender founder-did})
      (let [followups (evr/pending-followups ledger ks)]
        (is (= ["D" "B"] (mapv :household-ref followups)))))))

(deftest pending-followups-skips-sealed-records
  (testing "a crypto-shredded record never surfaces in the followup list, even though it was 'interested'"
    (let [[ledger ks] (fresh)
          envelope (evr/record-visit! ledger ks {:household-ref "E" :status "interested" :now now :sender founder-did})]
      (evr/erase-household! ledger ks envelope {:actor-did founder-did :now "2026-08-01T09:00:00Z"})
      (is (= [] (evr/pending-followups ledger ks))))))

(defn -main [& _]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.test-evangelism-visit-record)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
