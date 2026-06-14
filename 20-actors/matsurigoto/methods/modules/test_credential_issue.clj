;; test_credential_issue.clj — matsurigoto credential-issue: ICAO 9303 TD3 MRZ + 7-3-1 check-digit
;; parity with credential_issue.py. Run via `bb test:matsurigoto`. ADR-2606142300.
(ns matsurigoto.methods.modules.test-credential-issue
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [matsurigoto.methods.modules.credential-issue :as ci]))

(def ^:private eriksson
  {:doc-number "L898902C3" :issuing-state "UTO" :nationality "UTO" :surname "ERIKSSON"
   :given-names "ANNA MARIA" :dob-yymmdd "740812" :sex "F" :expiry-yymmdd "120415"
   :subject-did "did:web:example" :personal-number "ZE184226B"})

(deftest icao-worked-example-check-digits
  (testing "ICAO Doc 9303 7-3-1 check digits (canonical worked example)"
    (is (= "6" (ci/mrz-check-digit "L898902C3")))   ; ICAO 9303 worked example
    (is (= "2" (ci/mrz-check-digit "740812")))       ; DOB
    (is (= "9" (ci/mrz-check-digit "120415")))))     ; expiry

(deftest eriksson-specimen-byte-identical
  (testing "ERIKSSON TD3 specimen reproduced byte-for-byte (golden from credential_issue.py)"
    (let [mrz (:mrz (ci/issue-passport eriksson))]
      (is (= "P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<" (:line1 mrz)))
      (is (= "L898902C36UTO7408122F1204159ZE184226B<<<<<10" (:line2 mrz)))
      (is (= 44 (count (:line1 mrz))))
      (is (= 44 (count (:line2 mrz))))
      (is (= {:doc "6" :dob "2" :expiry "9" :personal "1" :composite "0"} (:check-digits mrz)))
      (is (true? (ci/validate-td3-line2 (:line2 mrz)))))))

(deftest validation-detects-corruption
  (testing "a flipped MRZ line-2 digit fails the check"
    (let [l2 "L898902C36UTO7408122F1204159ZE184226B<<<<<10"]
      (is (true?  (ci/validate-td3-line2 l2)))
      (is (false? (ci/validate-td3-line2 (str (subs l2 0 9) "7" (subs l2 10)))))   ; doc check flipped
      (is (false? (ci/validate-td3-line2 (subs l2 0 43))))                          ; wrong length
      (is (false? (ci/validate-td3-line2 "नहीं"))))))                                 ; non-MRZ chars

(deftest unsigned-document-discipline
  (testing "G1 — document SOD/proof unsigned; G6 — only MRZ fields"
    (let [doc (:document (ci/issue-passport eriksson))]
      (is (nil? (:sod doc)))                                 ; G1 — issuing state signs the SOD
      (is (nil? (:proof doc)))                               ; G1
      (is (false? (:server-held-authority doc)))             ; G1
      (is (= "issued-unsigned" (:status doc)))
      (is (= ["VerifiableCredential" "Passport"] (:type doc))))))

(deftest build-and-issue-guards
  (testing "MRZ field guards + G1 live-issuance gate"
    (is (thrown? Exception (ci/build-td3-mrz (assoc eriksson :issuing-state "JP"))))   ; not 3-letter
    (is (thrown? Exception (ci/build-td3-mrz (assoc eriksson :dob-yymmdd "7408"))))    ; not YYMMDD
    (is (thrown? Exception (ci/build-td3-mrz (assoc eriksson :sex "X"))))              ; bad sex
    (is (thrown? Exception (ci/issue-passport (assoc eriksson :doc-number ""))))       ; no doc number
    (is (thrown? Exception (ci/issue-passport (assoc eriksson :surname ""))))          ; no surname
    (is (thrown? Exception (ci/solve)))                                                ; live issuance gated
    (is (false? ci/server-held-authority))))

(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (run-tests 'matsurigoto.methods.modules.test-credential-issue)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
