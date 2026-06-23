;; etzhayyim.test-kotoba-rad — kotoba-rad sovereign-identity invariants (ADR-2606231200).
;; Run: bb test:kotoba-rad
(ns etzhayyim.test-kotoba-rad
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [clojure.java.io :as io]
            [etzhayyim.kotoba-rad :as rad]
            [etzhayyim.kotoba.datom :as d]
            [etzhayyim.kotoba.log :as log]))

(def pk "9f3a7c2e1b4d5a6f8090a1b2c3d4e5f60718293a4b5c6d7e8f9012345678abcd")

(defn g [] (rad/genesis-block
            {:name "cargo" :did-web "did:web:cargo.etzhayyim.com"
             :delegates [(rad/did-key pk)] :threshold 1
             :repo "github.com/etzhayyim/com-etzhayyim-cargo"
             :pds "https://pds.etzhayyim.com" :collection "com.etzhayyim.apps.cargo"}))

(deftest did-key-convention
  (testing "did:key:z<hex> matches kotoba.cljs verifier form"
    (is (= (str "did:key:z" pk) (rad/did-key pk)))
    (is (nil? (rad/did-key "not-hex!!")))))

(deftest rid-is-deterministic-and-content-addressed
  (is (= (rad/rid (g)) (rad/rid (g))) "same genesis -> same RID")
  (is (.startsWith (rad/rid (g)) "b") "CIDv1 base32 multibase")
  (testing "RID changes when identity content (delegate key) changes"
    (is (not= (rad/rid (g))
              (rad/rid (assoc (g) :rad/delegates ["did:key:zdeadbeef"]))))))

(deftest did-doc-cross-links-three-identities
  (let [doc (rad/did-web-doc {:name "cargo" :genesis (g) :pubkey-hex pk})
        aka (set (get doc "alsoKnownAs"))]
    (is (= "did:web:cargo.etzhayyim.com" (get doc "id")))
    (is (contains? aka "at://cargo.etzhayyim.com"))
    (is (contains? aka "https://github.com/etzhayyim/com-etzhayyim-cargo"))
    (is (contains? aka (rad/rad-uri (g))) "sovereign rad: URI present")
    (is (= pk (get-in doc ["verificationMethod" 0 "publicKeyHex"])))))

(deftest publish-is-append-only-and-idempotent
  (let [a "__test_kotoba_rad__"
        path (rad/journal-path a)]
    (io/delete-file path true)
    (try
      (let [r1 (rad/publish-identity! a (g) {:sign-fn nil})
            n1 (count (log/read-log path))
            r2 (rad/publish-identity! a (g) {:sign-fn nil})
            n2 (count (log/read-log path))]
        (is (= (:rid r1) (:rid r2)) "RID stable across publishes")
        (is (false? (:signed? r1)) "unsigned when no :sign-fn (no-server-key)")
        (is (> n1 0))
        (is (< (:datoms-appended r2) (:datoms-appended r1))
            "re-publish appends only a fresh sigref, not the identity again")
        (is (> n2 n1) "append-only: log only grows")
        (testing "sigref attests a head AFTER the identity datoms"
          (let [logv (log/read-log path)
                sigrefs (filter #(and (= :sigref (d/d-v %)) (= :rad/type (d/d-a %))) logv)]
            (is (>= (count sigrefs) 2)))))
      (finally (io/delete-file path true)))))

(defn -main [& _]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.test-kotoba-rad)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
