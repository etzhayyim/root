(ns etzhayyim.observatory-diddoc-test
  "Tests for the first-party did.json generator (ADR-2606302205 D4)."
  (:require [clojure.test :refer [deftest is testing]]
            [etzhayyim.observatory-diddoc :as dd]))

(deftest first-party-disclosure-honest-doc
  (testing "the did doc is first-party + disclosure-honest, NOT a keyless mirror"
    (let [d (dd/did-doc {:handle "corp-7203" :subject "Toyota Motor Corp" :glyph "兜" :ns "corp"})]
      (is (= "did:web:etzhayyim.com:actor:corp-7203" (get d "id")))
      (is (= false (get-in d ["etzhayyim" "isMirror"])))          ; not a mirror
      (is (= true (get-in d ["etzhayyim" "isObservatory"])))
      (is (= "etzhayyim" (get-in d ["etzhayyim" "voiceOf"])))     ; disclosure
      (is (= "Toyota Motor Corp" (get-in d ["etzhayyim" "subject"])))
      (is (= "https://aozora.app" (get-in d ["service" 0 "serviceEndpoint"]))))))

(deftest no-key-yields-pending-not-server-key
  (testing "without a member key: verificationMethod [] + pendingMemberKey (NO server key)"
    (let [d (dd/did-doc {:handle "gov-jp-kokkai" :subject "国会" :glyph "公" :ns "gov"})]
      (is (= [] (get d "verificationMethod")))
      (is (= true (get d "pendingMemberKey"))))))

(deftest member-key-populates-verification-method
  (testing "with the member's did:key: first-party verificationMethod + auth (present-only)"
    (let [d (dd/did-doc {:handle "cable-marea" :subject "MAREA" :glyph "綿津綱" :ns "cable"
                         :did-key "did:key:z6MkExampleMultibaseKeyMaterial"})]
      (is (not (contains? d "pendingMemberKey")))
      (is (= "Ed25519VerificationKey2020" (get-in d ["verificationMethod" 0 "type"])))
      (is (= "z6MkExampleMultibaseKeyMaterial" (get-in d ["verificationMethod" 0 "publicKeyMultibase"])))
      (is (= ["did:web:etzhayyim.com:actor:cable-marea#key-1"] (get d "authentication")))
      (is (some #{"did:key:z6MkExampleMultibaseKeyMaterial"} (get d "alsoKnownAs"))))))
