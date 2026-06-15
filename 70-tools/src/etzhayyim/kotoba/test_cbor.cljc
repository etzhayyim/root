;; etzhayyim.kotoba.test-cbor — canonical CBOR + CBOR-encoded envelope.
;; KATs are RFC 8949 Appendix A. Run: bb test:kotoba

(ns etzhayyim.kotoba.test-cbor
  (:require [clojure.test :refer [deftest is testing]]
            [etzhayyim.kotoba.cbor :as cbor]
            [etzhayyim.kotoba.encrypted :as enc]))

(defn- hx [v] (apply str (map #(format "%02x" (bit-and % 0xff)) (cbor/encode v))))
(defn- hex->b ^bytes [s]
  (let [n (/ (count s) 2) a (byte-array n)]
    (dotimes [i n] (aset a i (unchecked-byte (Integer/parseInt (subs s (* 2 i) (+ 2 (* 2 i))) 16))))
    a))

(deftest rfc8949-vectors
  (testing "RFC 8949 Appendix A encodings (canonical)"
    (doseq [[v exp] [[0 "00"] [1 "01"] [10 "0a"] [23 "17"] [24 "1818"]
                     [100 "1864"] [1000 "1903e8"]
                     [-1 "20"] [-10 "29"] [-100 "3863"] [-1000 "3903e7"]
                     ["a" "6161"] ["IETF" "6449455446"]
                     [[1 2 3] "83010203"] [false "f4"] [true "f5"] [nil "f6"]
                     [{:a 1 :b [2 3]} "a26161016162820203"]]]
      (is (= exp (hx v)) (str "encode " (pr-str v))))))

(deftest canonical-key-order
  (testing "map keys are emitted in bytewise-lexicographic order regardless of insertion"
    (is (= (hx {:a 2 :b 1}) (hx {:b 1 :a 2})))
    (is (= "a2616102616201" (hx {:b 1 :a 2})))))    ; :a then :b

(deftest roundtrip
  (doseq [v [{:msg "covenant proposal #1" :n 7}
             {:a 1 :b [2 3] :c {:d true :e nil}}
             "hi" 42 -5 [1 "two" false] {}]]
    (is (= v (cbor/decode (cbor/encode v))) (str "round-trip " (pr-str v)))))

(deftest decode-known-bytes
  (testing "decode RFC vectors back to values"
    (is (= 1000 (cbor/decode (hex->b "1903e8"))))
    (is (= {:a 1 :b [2 3]} (cbor/decode (hex->b "a26161016162820203"))))
    (is (= [1 2 3] (cbor/decode (hex->b "83010203"))))))

(deftest cbor-envelope-frozen
  ;; The production-wire path: plaintext encoded as CBOR (not EDN). Locks the
  ;; CBOR-sealed envelope so a Rust kotoba-crypto (CBOR) reproduces it byte-exact.
  (binding [enc/*encode-plaintext* cbor/encode
            enc/*decode-plaintext* cbor/decode]
    (let [key (hex->b "808182838485868788898a8b8c8d8e8f909192939495969798999a9b9c9d9e9f")
          n24 (hex->b "404142434445464748494a4b4c4d4e4f5051525354555657")
          env (enc/seal key n24 {:msg "covenant proposal #1" :n 7}
                        {:sender "did:web:etzhayyim.com"
                         :innerType "com.etzhayyim.governance.proposal"
                         :createdAt "2026-06-14T00:00:00Z"})]
      (testing "frozen CBOR ciphertext + cid"
        (is (= "U20d8zidhz2PcRilk8D8O0ZnAhxqNPOfq9bVL3MmadaidVWo6JWrcMkaV/mN"
               (:ciphertext env)))
        (is (= "bafkreiaxmz3olrkkufyddnnibybp2vxfokq7ll4agxwpksmjuiytdpm3ee"
               (enc/envelope-cid env))))
      (testing "round-trips under the CBOR codec"
        (is (= {:msg "covenant proposal #1" :n 7} (enc/open key env)))))))
