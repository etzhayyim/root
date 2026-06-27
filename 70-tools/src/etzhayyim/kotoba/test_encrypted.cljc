;; etzhayyim.kotoba.test-encrypted — com.etzhayyim.encrypted.record AEAD envelope. Run: bb test:kotoba
;; ADR-2605181100. Reproducible (caller supplies key+nonce, no RNG): seal/open
;; round-trip, AAD header binding (swap-resistance), envelope CID, keyWrap shape.
(ns etzhayyim.kotoba.test-encrypted
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [clojure.string :as str]
            [etzhayyim.kotoba.encrypted :as enc]))

(def key32   (.getBytes "0123456789abcdef0123456789abcdef" "UTF-8"))  ;; 32-byte sym key
(def wrong32 (.getBytes "FEDCBA9876543210FEDCBA9876543210" "UTF-8"))
(def nonce24 (.getBytes "abcdefghijklmnopqrstuvwx" "UTF-8"))          ;; 24-byte XChaCha nonce
(def nonce24b (.getBytes "ABCDEFGHIJKLMNOPQRSTUVWX" "UTF-8"))
(def hdr {:sender "did:web:alice" :innerType "app.bsky.feed.post" :createdAt "2026-01-01T00:00:00Z"})

(deftest key-id-and-aad
  (testing "keyId = 16 hex chars of sha256(key), deterministic"
    (is (re-matches #"[0-9a-f]{16}" (enc/key-id key32)))
    (is (= (enc/key-id key32) (enc/key-id key32)))
    (is (not= (enc/key-id key32) (enc/key-id wrong32))))
  (testing "self-ref-aad is deterministic per header, distinct across headers"
    (let [h {:innerType "t" :sender "s" :createdAt "c" :keyId "k"}]
      (is (= (seq (enc/self-ref-aad h)) (seq (enc/self-ref-aad h))))
      (is (not= (seq (enc/self-ref-aad h)) (seq (enc/self-ref-aad (assoc h :sender "other"))))))))

(deftest seal-open-round-trip
  (let [env (enc/seal key32 nonce24 {"text" "secret"} hdr)]
    (testing "envelope framing: v1 / base64 nonce+ciphertext / cleartext header"
      (is (= 1 (:v env)))
      (is (= (enc/key-id key32) (:keyId env)))
      (is (= "did:web:alice" (:sender env)))
      (is (string? (:ciphertext env))))
    (testing "open recovers the plaintext"
      (is (= {"text" "secret"} (enc/open key32 env))))))

(deftest aead-rejects-tamper
  (let [env (enc/seal key32 nonce24 {"text" "secret"} hdr)]
    (testing "a swapped header breaks the AAD binding"
      (is (thrown? Exception (enc/open key32 (assoc env :sender "did:web:evil")))))
    (testing "the wrong key fails the AEAD tag"
      (is (thrown? Exception (enc/open wrong32 env))))))

(deftest envelope-cid-properties
  (let [env (enc/seal key32 nonce24 {"text" "secret"} hdr)]
    (testing "deterministic 'b' multibase CID over the canonical envelope"
      (is (str/starts-with? (enc/envelope-cid env) "b"))
      (is (= (enc/envelope-cid env) (enc/envelope-cid env))))
    (testing "a different nonce yields a different envelope → different CID"
      (is (not= (enc/envelope-cid env)
                (enc/envelope-cid (enc/seal key32 nonce24b {"text" "secret"} hdr)))))))

(deftest key-wrap-shape
  (let [w (enc/key-wrap key32 {:sender "s" :recipient "r" :createdAt "c"})]
    (is (= 1 (:v w)))
    (is (= (enc/key-id key32) (:keyId w)))
    (is (= "r" (:recipient w)))
    (is (string? (:ciphertext w)))
    (testing ":recordUri only present when supplied"
      (is (not (contains? w :recordUri)))
      (is (= "at://x" (:recordUri (enc/key-wrap key32 {:sender "s" :recipient "r"
                                                       :createdAt "c" :recordUri "at://x"})))))))

(defn -main [& _]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.kotoba.test-encrypted)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
