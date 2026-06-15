;; test_sign_capability.clj — matsurigoto no-server-key sign layer: external-proof attach + verify
;; + principal A/B legitimacy + tamper detection. Run via `bb test:matsurigoto`. ADR-2606142300.
(ns matsurigoto.methods.test-sign-capability
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [matsurigoto.methods.sign-capability :as sc]
            [matsurigoto.methods.modules.credential-issue :as ci]))

(def ^:private doc
  (:document (ci/issue-passport {:doc-number "L898902C3" :issuing-state "UTO" :nationality "UTO"
                                 :surname "ERIKSSON" :given-names "ANNA" :dob-yymmdd "740812"
                                 :sex "F" :expiry-yymmdd "120415" :subject-did "did:x"})))

(deftest no-server-key
  (testing "matsurigoto holds no key and signs nothing (ADR-2605231525)"
    (is (false? sc/signer-held-private-key))
    (is (thrown? Exception (sc/sign-server-side doc)))))

(deftest principal-a-council-sign-and-verify
  (testing "principal A — a Council organ signs externally; structure verifies"
    (let [signed (sc/attach-external-proof doc {:signer-did "did:web:etzhayyim.com:council:safe"
                                                :authority-mode :sovereign-governance
                                                :signature "0xCOUNCIL_SAFE_SIG" :signed-at "2026-06-06T00:00:00Z"})]
      (is (= "issued-signed" (:status signed)))             ; unsigned → signed
      (is (= "did:web:etzhayyim.com:council:safe" (get-in signed [:proof :signer-did])))
      (is (false? (:server-held-authority signed)))          ; still no operator key
      (is (true? (sc/verify-proof signed))))))

(deftest principal-b-state-key
  (testing "principal B — the adopting state's OWN (non-etzhayyim) key signs"
    (let [signed (sc/attach-external-proof doc {:signer-did "did:web:mof.go.jp:pki"
                                                :authority-mode :supplied-to-state
                                                :signature "0xSTATE_SIG" :signed-at "2026-06-06"})]
      (is (true? (sc/verify-proof signed))))))

(deftest illegitimate-signers-rejected
  (testing "principal A needs a Council did; principal B must NOT be an etzhayyim did"
    (is (thrown? Exception (sc/attach-external-proof doc {:signer-did "did:web:random.example"
                                                          :authority-mode :sovereign-governance
                                                          :signature "x" :signed-at "t"})))     ; A not council
    (is (thrown? Exception (sc/attach-external-proof doc {:signer-did "did:web:etzhayyim.com:council:safe"
                                                          :authority-mode :supplied-to-state
                                                          :signature "x" :signed-at "t"})))     ; B is etzhayyim
    (is (thrown? Exception (sc/attach-external-proof doc {:signer-did "did:x" :authority-mode :nonsense
                                                          :signature "x" :signed-at "t"})))))   ; unknown mode

(deftest attach-guards
  (testing "unsigned-on-arrival (G1) + a real external signature required"
    (is (thrown? Exception (sc/attach-external-proof doc {:signer-did "did:web:etzhayyim.com:council:s"
                                                          :authority-mode :sovereign-governance
                                                          :signature "" :signed-at "t"})))      ; empty sig
    (let [signed (sc/attach-external-proof doc {:signer-did "did:web:etzhayyim.com:council:s"
                                                :authority-mode :sovereign-governance
                                                :signature "0xSIG" :signed-at "t"})]
      (is (thrown? Exception (sc/attach-external-proof signed {:signer-did "did:web:etzhayyim.com:council:s"
                                                               :authority-mode :sovereign-governance
                                                               :signature "0xSIG2" :signed-at "t"}))))))  ; already signed

(deftest tamper-detection
  (testing "mutating a substantive field after signing breaks the payload digest"
    (let [signed (sc/attach-external-proof doc {:signer-did "did:web:etzhayyim.com:council:s"
                                                :authority-mode :sovereign-governance
                                                :signature "0xSIG" :signed-at "t"})]
      (is (true?  (sc/verify-proof signed)))
      (is (false? (sc/verify-proof (assoc signed :credential-subject {:id "did:forged"}))))   ; field tampered
      (is (false? (sc/verify-proof (dissoc signed :proof))))                                   ; no proof
      (is (false? (sc/verify-proof (assoc-in signed [:proof :signature] "")))))))               ; empty sig

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (run-tests 'matsurigoto.methods.test-sign-capability)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
