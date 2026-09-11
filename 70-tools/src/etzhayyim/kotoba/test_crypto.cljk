;; etzhayyim.kotoba.test-crypto — XChaCha20-Poly1305 + encrypted-record vectors.
;; Run: bb test:kotoba
;;
;; The KATs are the Phase-5 bit-identical acceptance basis (ADR-2605262130 D6):
;; kotoba-crypto / kotoba-signal MUST reproduce these exact bytes. Sources:
;;   - ChaCha20 permutation  : RFC 8439 §2.3.2
;;   - HChaCha20             : draft-irtf-cfrg-xchacha-00 §2.2.1
;;   - ChaCha20-Poly1305 AEAD: RFC 8439 §2.8.2

(ns etzhayyim.kotoba.test-crypto
  (:require [clojure.edn :as edn]
            [clojure.test :refer [deftest is testing]]
            [clojure.java.io :as io]
            [cheshire.core :as json]
            [etzhayyim.kotoba.crypto :as c]
            [etzhayyim.kotoba.encrypted :as enc])
  (:import (java.util Arrays)))

(defn- hex->b ^bytes [s]
  (let [n (/ (count s) 2) a (byte-array n)]
    (dotimes [i n]
      (aset a i (unchecked-byte (Integer/parseInt (subs s (* 2 i) (+ 2 (* 2 i))) 16))))
    a))
(defn- b->hex [b] (apply str (map #(format "%02x" (bit-and % 0xff)) b)))
(defn- w->hex [ws] (apply str (map #(format "%08x" %) ws)))

(def key-80-9f "808182838485868788898a8b8c8d8e8f909192939495969798999a9b9c9d9e9f")

(deftest chacha20-permutation-rfc8439
  (testing "ChaCha20 20-round permutation == RFC 8439 §2.3.2 after-20-rounds state"
    (is (= "837778abe238d763a67ae21e5950bb2fc4f2d0c7fc62bb2f8fa018fc3f5ec7b7335271c2f29489f3eabda8fc82e46ebdd19c12b4b04e16de9e83d0cb4e3c50a2"
           (w->hex (c/chacha-permuted-state
                    (hex->b "000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f")
                    1 (hex->b "000000090000004a00000000")))))))

(deftest hchacha20-draft-kat
  (testing "HChaCha20 == draft-irtf-cfrg-xchacha-00 §2.2.1"
    (is (= "82413b4227b27bfed30e42508a877d73a0f9e4d58a74a853c12ec41326d3ecdc"
           (b->hex (c/hchacha20
                    (hex->b "000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f")
                    (hex->b "000000090000004a0000000031415927")))))))

(deftest chacha20poly1305-aead-rfc8439
  (testing "IETF ChaCha20-Poly1305 == RFC 8439 §2.8.2 (ciphertext + tag)"
    ;; XChaCha collapses to IETF AEAD on the derived subkey; here we feed a
    ;; 24-byte nonce whose HChaCha20 path we cross-check via the round-trip below,
    ;; and pin the inner IETF AEAD through the JDK on the documented 12-byte nonce.
    (let [pt (.getBytes "Ladies and Gentlemen of the class of '99: If I could offer you only one tip for the future, sunscreen would be it." "UTF-8")
          ;; reach the inner cipher through a 24-byte nonce that makes n12 = the
          ;; RFC nonce 07000000|4041424344454647 and subkey = the RFC key.
          ;; Simpler: validate via the public JDK path used by crypto/*.
          out (let [ci (javax.crypto.Cipher/getInstance "ChaCha20-Poly1305")]
                (.init ci javax.crypto.Cipher/ENCRYPT_MODE
                       (javax.crypto.spec.SecretKeySpec. (hex->b key-80-9f) "ChaCha20")
                       (javax.crypto.spec.IvParameterSpec. (hex->b "070000004041424344454647")))
                (.updateAAD ci (hex->b "50515253c0c1c2c3c4c5c6c7"))
                (.doFinal ci pt))]
      (is (= "d31a8d34648e60db7b86afbc53ef7ec2a4aded51296e08fea9e2b5a736ee62d63dbea45e8ca9671282fafb69da92728b1a71de0a9e060b2905d6a5b67ecd3b3692ddbd7f2d778b8c9803aee328091b58fab324e4fad675945585808b4831d7bc3ff4def08e4b7a9de576d26586cec64b6116"
             (b->hex (Arrays/copyOfRange out 0 (- (alength out) 16)))))
      (is (= "1ae10b594f09e26a7e902ecbd0600691"
             (b->hex (Arrays/copyOfRange out (- (alength out) 16) (alength out))))))))

(deftest xchacha20poly1305-roundtrip
  (let [key (hex->b key-80-9f)
        n24 (hex->b "404142434445464748494a4b4c4d4e4f5051525354555657")
        aad (hex->b "50515253c0c1c2c3c4c5c6c7")
        pt (.getBytes "kotoba encrypted record" "UTF-8")
        ct+tag (c/xchacha20-poly1305-encrypt key n24 aad pt)]
    (testing "decrypt recovers plaintext"
      (is (= (b->hex pt) (b->hex (c/xchacha20-poly1305-decrypt key n24 aad ct+tag)))))
    (testing "wrong AAD => AEAD failure"
      (is (thrown? Exception (c/xchacha20-poly1305-decrypt key n24 (hex->b "00") ct+tag))))
    (testing "flipped ciphertext byte => AEAD failure"
      (let [bad (aclone ct+tag)]
        (aset bad 0 (unchecked-byte (bit-xor (aget bad 0) 1)))
        (is (thrown? Exception (c/xchacha20-poly1305-decrypt key n24 aad bad)))))))

;; ── envelope (com.etzhayyim.encrypted.record) ──
(def env-key (hex->b key-80-9f))
(def env-nonce (hex->b "404142434445464748494a4b4c4d4e4f5051525354555657"))
(def env-opts {:sender "did:web:etzhayyim.com"
               :innerType "com.etzhayyim.governance.proposal"
               :createdAt "2026-06-14T00:00:00Z"})
(def env-plaintext {:msg "covenant proposal #1" :n 7})

(deftest encrypted-record-envelope
  (let [env (enc/seal env-key env-nonce env-plaintext env-opts)]
    (testing "round-trip"
      (is (= env-plaintext (enc/open env-key env))))
    (testing "deterministic wire (FROZEN vector — kotoba-crypto must match)"
      (is (= "ijYehzzQ1jmUZBK9l8DpdUI1HR5qN/2A6pnELm51N6YgC23dwdf+eudmyYWW5O4UmamF"
             (:ciphertext env)))
      (is (= "82d86408530b765e" (:keyId env)))
      (is (= 1 (:v env)))
      (is (= "xchacha20poly1305" (:alg env))))
    (testing "envelope CID is over the ciphertext envelope (leaks no plaintext)"
      (is (= "bafkreialexhkbn4fr5ujm33p7ykc23dexnekiemplruu3kpuyohei7ldvm"
             (enc/envelope-cid env))))
    (testing "swap-resistance: tampering the bound header fails the open"
      (is (thrown? Exception (enc/open env-key (assoc env :sender "did:web:attacker.example")))))
    (testing "wrong key fails"
      (is (thrown? Exception (enc/open (byte-array 32) env))))))

(deftest encrypted-plaintext-decoder-rejects-reader-eval
  (is (thrown? RuntimeException
               (enc/*decode-plaintext*
                (.getBytes "#=(System/getProperty \"user.home\")" "UTF-8")))))

(def ^:private vectors-path
  "00-contracts/lexicons/com/etzhayyim/encrypted/test-vectors.json")

(deftest frozen-vectors-file-in-sync
  ;; The 00-contracts vectors file is the language-neutral bit-identical gate for
  ;; kotoba-crypto. Re-derive it from the reference impl so the JSON and the code
  ;; can never silently drift. Skips if the file is absent.
  (when (.exists (io/file vectors-path))
    (let [v (json/parse-string (slurp vectors-path) true)
          prim (:primitives v)
          env-v (:envelope v)]
      (testing "primitive KATs match the file"
        (is (= (get-in prim [:hchacha20 :subkey])
               (b->hex (c/hchacha20 (hex->b (get-in prim [:hchacha20 :key]))
                                    (hex->b (get-in prim [:hchacha20 :nonce16]))))))
        (is (= (get-in prim [:chacha20_permutation :after20_words_le])
               (w->hex (c/chacha-permuted-state
                        (hex->b (get-in prim [:chacha20_permutation :key]))
                        (get-in prim [:chacha20_permutation :counter])
                        (hex->b (get-in prim [:chacha20_permutation :nonce12])))))))
      (testing "envelope re-derivation matches the file"
        (let [env (enc/seal (hex->b (:sym_key env-v))
                            (hex->b (:nonce24 env-v))
                            (edn/read-string (:plaintext_edn env-v))
                            (:opts env-v))]
          (is (= (get-in env-v [:expected_record :ciphertext]) (:ciphertext env)))
          (is (= (get-in env-v [:expected_record :keyId]) (:keyId env)))
          (is (= (:envelope_cid env-v) (enc/envelope-cid env))))))))

(deftest keywrap-structure
  (let [kw (enc/key-wrap env-key {:sender "did:web:etzhayyim.com"
                                  :recipient "did:web:alice.example"
                                  :signalSessionId "sess-1"
                                  :createdAt "2026-06-14T00:00:00Z"})]
    (is (= 1 (:v kw)))
    (is (= "82d86408530b765e" (:keyId kw)))
    (is (= "did:web:alice.example" (:recipient kw)))))
