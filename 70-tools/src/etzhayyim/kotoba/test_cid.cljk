;; etzhayyim.kotoba.test-cid — CIDv1 content-address invariants. Run: bb test:kotoba
;; Known-answer tests pin byte-identical parity with
;; `ipfs add --cid-version=1 --raw-leaves` (CIDv1 / raw 0x55 / sha2-256 / base32).
(ns etzhayyim.kotoba.test-cid
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [clojure.string :as str]
            [etzhayyim.kotoba.cid :as cid]))

(deftest sha2-256-digest-shape
  (let [d (cid/sha2-256-digest (.getBytes "x" "UTF-8"))]
    (is (= 32 (alength d)))
    (is (= (vec (cid/sha2-256-digest (.getBytes "x" "UTF-8"))) (vec d)))))  ;; deterministic

(deftest cid-known-answers
  (testing "byte-identical to ipfs add --cid-version=1 --raw-leaves"
    (is (= "bafkreihdwdcefgh4dqkjv67uzcmw7ojee6xedzdetojuzjevtenxquvyku"
           (cid/cid (byte-array 0))))                                  ;; empty content
    (is (= "bafkreibm6jg3ux5qumhcn2b3flc3tyu6dmlb4xa7u5bf44yegnrjhc4yeq"
           (cid/cid "hello"))))                                        ;; 5 bytes "hello"
  (testing "string and equivalent bytes hash identically"
    (is (= (cid/cid "hello") (cid/cid (.getBytes "hello" "UTF-8")))))
  (testing "framing: multibase 'b' + CIDv1 raw prefix 'bafkrei'"
    (is (str/starts-with? (cid/cid "hello") "bafkrei")))
  (testing "deterministic; distinct content → distinct CID"
    (is (= (cid/cid "hello") (cid/cid "hello")))
    (is (not= (cid/cid "hello") (cid/cid "hellp")))))

(deftest cid-of-edn-over-prstr
  (testing "addresses the canonical pr-str bytes of the value"
    (is (= (cid/cid (pr-str [":db/add" "e" ":a" "v"]))
           (cid/cid-of-edn [":db/add" "e" ":a" "v"]))))
  (testing "stable known answer for a Datom-shaped vector"
    (is (= "bafkreid3fhy7jpq4te7qekfbx6j5jocu56xq34smrf5diig7pyai2ak6mi"
           (cid/cid-of-edn [":db/add" "e" ":a" "v"]))))
  (testing "distinct values → distinct CID"
    (is (not= (cid/cid-of-edn [1 2]) (cid/cid-of-edn [2 1])))))

(defn -main [& _]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.kotoba.test-cid)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
