;; etzhayyim.test-actor-publish — actor-publish profile→genesis pure invariants.
;; Run via the aggregate: bb test:helpers
;; Covers the pure derivation (gh/git/fs steps deferred): repo-name · prefix ·
;; manifest->genesis (did:web github.io path form + collection-NSID derivation).
(ns etzhayyim.test-actor-publish
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [clojure.string :as str]
            [etzhayyim.actor-publish :as ap]))

(deftest repo-name-and-prefix
  (is (= "com-etzhayyim-cargo" (ap/repo-name "cargo")))
  (is (= "20-actors/kaname" (ap/prefix "kaname"))))

(deftest genesis-did-web-and-repo
  (let [g (ap/manifest->genesis "cargo" {})]
    (testing "did:web is normalised to the github.io PATH form (ADR-2606231200)"
      (is (= "did:web:etzhayyim.github.io:com-etzhayyim-cargo" (:rad/did-web g))))
    (is (= "cargo" (:rad/name g)))
    (is (= "github.com/etzhayyim/com-etzhayyim-cargo" (:rad/repo g)))
    (is (= "https://pds.etzhayyim.com" (get-in g [:rad/aozora :pds])))
    (is (= 1 (:rad/threshold g)))))

(deftest genesis-collection-derivation
  (testing "actor-manifest.jsonld: collection from :triggers/:subscribeRepos, minus record segment"
    (is (= "com.etzhayyim.apps.cargo"
           (get-in (ap/manifest->genesis
                    "cargo"
                    {:triggers {:subscribeRepos {:collections ["com.etzhayyim.apps.cargo.profile"]}}})
                   [:rad/aozora :collection]))))
  (testing "flagship manifest.jsonld: collection from :lexicons, minus record segment"
    (is (= "com.etzhayyim.kaname.thought"
           (get-in (ap/manifest->genesis "kaname" {:lexicons ["com.etzhayyim.kaname.thought.record"]})
                   [:rad/aozora :collection]))))
  (testing "no declared collection → default com.etzhayyim.apps.<actor>"
    (is (= "com.etzhayyim.apps.foo"
           (get-in (ap/manifest->genesis "foo" {}) [:rad/aozora :collection])))))

(deftest genesis-delegates
  (testing "no pubkey → empty delegate set"
    (is (= [] (:rad/delegates (ap/manifest->genesis "foo" {})))))
  (testing "pubkey-hex → a single did:key delegate"
    (let [g (ap/manifest->genesis "foo" {} :pubkey-hex "deadbeef")]
      (is (= 1 (count (:rad/delegates g))))
      (is (str/starts-with? (first (:rad/delegates g)) "did:key:")))))

(defn -main [& _]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.test-actor-publish)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
