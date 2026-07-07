;; etzhayyim.test-actor-publish — actor-publish profile→genesis pure invariants.
;; Run via the aggregate: bb test:helpers
;; Covers the pure derivation (gh/git/fs steps deferred): repo-name · prefix ·
;; manifest->genesis (did:web etzhayyim.com actor PATH form, ADR-2606231200
;; addendum 2026-07-02 + collection-NSID derivation).
(ns etzhayyim.test-actor-publish
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [clojure.string :as str]
            [etzhayyim.actor-publish :as ap]))

(deftest repo-name-and-prefix
  (is (= "com-etzhayyim-cargo" (ap/repo-name "cargo")))
  (is (= "20-actors/kaname" (ap/prefix "kaname"))))

(deftest default-did-web-scheme
  (testing "brand-new actors default to the etzhayyim.com actor PATH form (ADR-2606231200 addendum 2026-07-02)"
    (is (= "did:web:etzhayyim.com:actor:cargo" (ap/default-did-web "cargo")))))

(deftest genesis-did-web-and-repo
  (let [g (ap/manifest->genesis "cargo" {})]
    (testing "a brand-new actor's genesis did:web defaults to default-did-web"
      (is (= (ap/default-did-web "cargo") (:rad/did-web g))))
    (testing "an explicit :did-web override is honored (RID-preserving migration path)"
      (is (= "did:web:etzhayyim.github.io:com-etzhayyim-cargo"
             (:rad/did-web (ap/manifest->genesis "cargo" {}
                            :did-web "did:web:etzhayyim.github.io:com-etzhayyim-cargo")))))
    (is (= "cargo" (:rad/name g)))
    (is (= "github.com/etzhayyim/com-etzhayyim-cargo" (:rad/repo g)))
    (is (= ap/canonical-aozora-pds (get-in g [:rad/aozora :pds])))
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

(deftest manifest->holds-extracts-and-coerces-layer
  (testing "reads :substrate :datasets and coerces a JSON-LD string :layer → keyword"
    (let [m {:substrate {:datasets [{:dataset-id "jinushi-land-wdqs-r2" :layer "repo"
                                     :source "wikidata:WDQS" :cidv1 "bafy1"
                                     :freshness-days 0 :retrieved "2026-07-01"}
                                    {:dataset-id "kanjo-graph" :layer :graph :cidv1 "bafy2"}]}}]
      (is (= [{:dataset-id "jinushi-land-wdqs-r2" :layer :repo
               :source "wikidata:WDQS" :cidv1 "bafy1"
               :freshness-days 0 :retrieved "2026-07-01"}
              {:dataset-id "kanjo-graph" :layer :graph :cidv1 "bafy2"}]
             (ap/manifest->holds m)))))
  (testing "absent :substrate :datasets → [] (no holdings declared)"
    (is (= [] (ap/manifest->holds {})))
    (is (= [] (ap/manifest->holds {:substrate {}})))))

(defn -main [& _]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.test-actor-publish)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
