;; etzhayyim.test-dns-sync — dns-sync pure planning invariants (cljc port).
;; Run: bb test:dns-sync
;; Covers the pure planning layer (CF API legs deferred): parse-identifier-tables ·
;; build-desired-records · diff-records · build-apply-request.
(ns etzhayyim.test-dns-sync
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [clojure.string :as str]
            [etzhayyim.dns-sync :as dns]))

(deftest parse-identifier-tables-extract
  (let [{:keys [actors legacies]}
        (dns/parse-identifier-tables
         {"mitama_actors"  [{"name" "foo" "domain" "foo.example" "did" "did:x"}
                            {"name" ""}]                ;; blank name dropped
          "legacy_nanoids" [{"actor" "bar" "nanoid" "n2" "handle" "h"}]})]
    (is (= [{:name "foo" :domain "foo.example" :nanoid "" :did "did:x" :handles []}] actors))
    (is (= [{:actor "bar" :nanoid "n2" :handle "h" :did ""}] legacies))))

(deftest build-desired-records-txt-and-cname
  (testing "TXT _atproto record for an actor with a zone-suffixed handle + did"
    (let [recs (dns/build-desired-records
                [{:name "a" :domain "a.etzhayyim.com" :did "did:a" :handles []}]
                [] true false "etzhayyim.com")]
      (is (= 1 (count recs)))
      (let [r (first recs)]
        (is (= "TXT" (:type r)))
        (is (= "_atproto.a.etzhayyim.com" (:name r)))
        (is (= "\"did=did:a\"" (:content r)))
        (is (= 3600 (:ttl r))))))
  (testing "include-txt? false suppresses TXT records"
    (is (= [] (dns/build-desired-records
               [{:name "a" :domain "a.etzhayyim.com" :did "did:a"}] [] false false "etzhayyim.com"))))
  (testing "CNAME for a legacy nanoid with a zone-suffixed handle"
    (let [recs (dns/build-desired-records
                [] [{:nanoid "n1" :handle "h.etzhayyim.com"}] false true "etzhayyim.com")]
      (is (= 1 (count recs)))
      (is (= "CNAME" (:type (first recs))))
      (is (= "n1.etzhayyim.com" (:name (first recs)))))))

(deftest diff-records-plan
  (let [desired [{:name "x" :type "TXT" :content "c1" :comment "cm"}]]
    (testing "missing desired → :create"
      (is (= [:create] (map :action (dns/diff-records desired [])))))
    (testing "matching content + comment → :keep"
      (is (= [:keep] (map :action (dns/diff-records desired
                                                    [{:name "x" :type "TXT" :content "c1" :comment "cm"}])))))
    (testing "different content → :update"
      (is (= [:update] (map :action (dns/diff-records desired
                                                      [{:name "x" :type "TXT" :content "OLD" :comment "cm" :id "i1"}])))))
    (testing "existing not-in-desired → :delete (orphan)"
      (let [plan (dns/diff-records [] [{:name "z" :type "TXT" :content "c" :comment "cm"}])]
        (is (= [:delete] (map :action plan)))))))

(deftest build-apply-request-by-action
  (let [hdr-ok? (fn [r] (= "Bearer tok" (get-in r [:headers "Authorization"])))]
    (testing ":create → POST, body = record"
      (let [r (dns/build-apply-request "z1" "tok" {:action :create :record {:name "x"}})]
        (is (= :post (:method r)))
        (is (str/ends-with? (:url r) "/zones/z1/dns_records"))
        (is (= {:name "x"} (:body r)))
        (is (hdr-ok? r))))
    (testing ":update → PATCH /<id>"
      (let [r (dns/build-apply-request "z1" "tok" {:action :update :record {:id "rid" :name "x"}})]
        (is (= :patch (:method r)))
        (is (str/ends-with? (:url r) "/dns_records/rid"))))
    (testing ":delete → DELETE /<id>, no body"
      (let [r (dns/build-apply-request "z1" "tok" {:action :delete :record {:id "rid"}})]
        (is (= :delete (:method r)))
        (is (nil? (:body r)))))
    (testing ":keep → nil"
      (is (nil? (dns/build-apply-request "z1" "tok" {:action :keep :record {}}))))))

(defn -main [& _]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.test-dns-sync)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
