(ns etzhayyim.pds.leash-test
  "Member CACAO leash: member-issued → PDS-verified → attributed to the consenting
  member; expiry / audience / scope / tamper all rejected; garbage never throws."
  (:require [clojure.test :refer [deftest is testing]]
            [clojure.string :as str]
            [etzhayyim.pds.leash :as leash]))

(def pds "did:web:atproto.etzhayyim.com")
(def now 1782000000)

(deftest didkey-roundtrip
  (testing "Ed25519 pub → did:key:z6Mk… → pub is lossless"
    (let [m (leash/gen-member-key)]
      (is (str/starts-with? (:did m) "did:key:z6Mk"))
      (is (= (:did m) (leash/pubkey->did-key (leash/did-key->pubkey (:did m))))))))

(deftest valid-leash-verifies-and-names-the-member
  (testing "a member-signed, in-audience, unexpired, in-scope leash verifies + yields the member"
    (let [m (leash/gen-member-key)
          l (leash/issue-leash m {:aud pds :exp (+ now 3600)})
          v (leash/verify-leash l {:aud pds :now now})]
      (is (true? (:valid? v)))
      (is (= (:did m) (:member v)) "the consenting human is named")
      (is (= :ok (:reason v))))))

(deftest expiry-audience-scope-and-tamper-are-rejected
  (let [m (leash/gen-member-key)]
    (testing "expired → invalid"
      (let [l (leash/issue-leash m {:aud pds :exp (- now 1)})]
        (is (= {:valid? false :member (:did m) :reason :expired}
               (leash/verify-leash l {:aud pds :now now})))))
    (testing "wrong audience (a leash for another PDS) → invalid"
      (let [l (leash/issue-leash m {:aud "did:web:other.example" :exp (+ now 3600)})]
        (is (= :wrong-audience (:reason (leash/verify-leash l {:aud pds :now now}))))))
    (testing "wrong scope → invalid"
      (let [l (leash/issue-leash m {:aud pds :exp (+ now 3600) :scope "blob:write"})]
        (is (= :wrong-scope (:reason (leash/verify-leash l {:aud pds :now now}))))))
    (testing "tampered payload (sig no longer matches) → bad-signature"
      (let [l (leash/issue-leash m {:aud pds :exp (+ now 3600)})
            [_ s64] (str/split l #"\." 2)
            ;; swap in a DIFFERENT member's payload but keep the old signature
            m2 (leash/gen-member-key)
            other (leash/issue-leash m2 {:aud pds :exp (+ now 3600)})
            forged (str (first (str/split other #"\." 2)) "." s64)]
        (is (false? (:valid? (leash/verify-leash forged {:aud pds :now now}))))))))

(deftest garbage-never-throws
  (testing "malformed leashes return {:valid? false}, never throw (untrusted input)"
    (doseq [bad ["" "no-dot" "a.b" "...." "x.y.z"
                 "did:key:znotreal.sig" (str "abc" "." "def")]]
      (is (false? (:valid? (leash/verify-leash bad {:aud pds :now now})))))))
