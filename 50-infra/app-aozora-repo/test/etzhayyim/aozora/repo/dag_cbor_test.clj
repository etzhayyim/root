(ns etzhayyim.aozora.repo.dag-cbor-test
  "dag-cbor decoder coverage: `decode` round-trips `encode` across the value
  space (scalars / strings / bytes / arrays / maps / CID links), and reverses
  the record/commit block bytes (`cid/block`). Pairs with repo-test's
  ipfs-verified encode side."
  (:require [clojure.test :refer [deftest is testing]]
            [etzhayyim.aozora.repo.dag-cbor :as dc]
            [etzhayyim.aozora.repo.cid :as cid]))

(def LINK "bafyreigbtj4x7ip5legnfznufuopl4sg4knzc2cof6duas4b3q2fy6swua")

(def values
  [{} {"hello" "world"} {"a" 1 "b" [1 2 3] "c" "x"} {"n" 1000000} {"neg" -5}
   {"t" true "f" false "z" nil} {"a" [] "o" {}} {"x" {"y" "z"}}
   [] [1 2 3] {"deep" {"a" [{"b" 2} {"c" [3 4]}]}}])

(deftest decode-round-trips-encode
  (testing "decode(encode v) == v across the dag-cbor value space"
    (doseq [v values]
      (is (= v (dc/decode (dc/encode v))) (str "round-trip " (pr-str v))))))

(deftest decode-cid-link
  (testing "a CID link round-trips through CBOR tag 42"
    (is (= (dc/cid-link LINK)
           (get (dc/decode (dc/encode {"l" (dc/cid-link LINK)})) "l")))))

(deftest decode-bytes
  (testing "byte strings round-trip"
    (let [bs (.getBytes "shalom-bytes" "UTF-8")]
      (is (= (seq bs) (seq (get (dc/decode (dc/encode {"b" bs})) "b")))))))

(deftest decode-reverses-block
  (testing "decode reverses cid/block (record/commit block bytes)"
    (let [{:keys [bytes]} (cid/block {"text" "hi" "n" 7 "ok" true})]
      (is (= {"text" "hi" "n" 7 "ok" true} (dc/decode bytes))))))

(deftest binary-cid-roundtrip
  (testing "binary->cid-str reverses cid-str->binary"
    (is (= LINK (dc/binary->cid-str (dc/cid-str->binary LINK))))))
