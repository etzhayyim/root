(ns matsurigoto.methods.test-sign-capability
  "test_sign_capability.py — tests for the R1.C sign/authority layer.
  1:1 Clojure port (stdlib unittest-style → clojure.test). The __main__ runner is omitted."
  (:require [clojure.test :refer [deftest is run-tests]]
            [clojure.string :as str]
            [matsurigoto.methods.sign-capability :as S]
            [matsurigoto.methods.modules.tax-assess :as T]))

(def COUNCIL "did:web:etzhayyim.com:council:safe")
(def STATE "did:web:gov.example:tax-authority")
(def AT "2026-06-06T00:00:00Z")

(defn- unsigned []
  (get (T/assess-from-return 1000000 0 "FLAT20.income") "receipt"))

(deftest test-module-holds-no-key
  (is (= S/SIGNER-HELD-PRIVATE-KEY false)))

(deftest test-server-side-signing-always-raises
  (is (thrown? #?(:clj Exception :cljs js/Error) (S/sign-server-side (unsigned)))))

(deftest test-principal-a-council-signs
  (let [signed (S/attach-external-proof (unsigned) COUNCIL ":sovereign-governance" "0xSAFE" AT)]
    (is (= (get-in signed ["proof" "signer_did"]) COUNCIL))
    (is (not (str/includes? (get signed "status") "unsigned")))
    (is (= (S/verify-proof signed) true))))

(deftest test-principal-b-state-signs-with-own-key
  (let [signed (S/attach-external-proof (unsigned) STATE ":supplied-to-state" "0xSTATE" AT)]
    (is (= (S/verify-proof signed) true))))

(deftest test-principal-a-rejects-non-council-signer
  (is (thrown? #?(:clj Exception :cljs js/Error)
               (S/attach-external-proof (unsigned) STATE ":sovereign-governance" "0xX" AT))))

(deftest test-principal-b-rejects-etzhayyim-holding-state-key
  (is (thrown? #?(:clj Exception :cljs js/Error)
               (S/attach-external-proof (unsigned) "did:web:etzhayyim.com:worker"
                                        ":supplied-to-state" "0xX" AT))))

(deftest test-empty-signature-refused
  (is (thrown? #?(:clj Exception :cljs js/Error)
               (S/attach-external-proof (unsigned) COUNCIL ":sovereign-governance" "" AT))))

(deftest test-double-sign-refused
  (let [signed (S/attach-external-proof (unsigned) COUNCIL ":sovereign-governance" "0xSAFE" AT)]
    (is (thrown? #?(:clj Exception :cljs js/Error)
                 (S/attach-external-proof signed COUNCIL ":sovereign-governance" "0xAGAIN" AT)))))

(deftest test-tampered-payload-fails-verify
  (let [signed (S/attach-external-proof (unsigned) COUNCIL ":sovereign-governance" "0xSAFE" AT)
        tampered (assoc signed "assessed_amount" 999999)]  ; tamper a SUBSTANTIVE field after signing
    (is (= (S/verify-proof tampered) false))))

(deftest test-unsigned-artifact-does-not-verify
  (is (= (S/verify-proof (unsigned)) false)))

#?(:clj (defn -main [& _] (run-tests 'matsurigoto.methods.test-sign-capability)))
