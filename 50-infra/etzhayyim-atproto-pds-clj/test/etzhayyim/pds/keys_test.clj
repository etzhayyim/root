(ns etzhayyim.pds.keys-test
  "actor-sealed key invariants: structure of the multikey, sign/verify round-trip,
  low-S, at-rest sealing, and the no-private-scalar-accessor posture."
  (:require [clojure.test :refer [deftest is testing]]
            [etzhayyim.pds.keys :as keys])
  (:import [java.util Base64]
           [java.math BigInteger]))

(defn- bytes->vec [^bytes b] (mapv #(bit-and % 0xff) b))

(deftest base58btc-known-vector
  (testing "base58btc matches the canonical 'hello world' vector"
    ;; private fn — exercised through multikey below; here we pin the well-known vector
    (let [b58 (#'etzhayyim.pds.keys/base58btc (.getBytes "hello world" "UTF-8"))]
      (is (= "StV1DL6CwTryKyV" b58)))))

(deftest multikey-structure
  (testing "multikey is z-prefixed, decodes to p256 multicodec + 33-byte compressed point"
    (let [k  (keys/new-actor-key)
          mk (:multikey k)]
      (is (string? mk))
      (is (= \z (first mk)))
      ;; decode the base58 body and check the multicodec prefix + compressed length
      (let [body (subs mk 1)
            ;; reuse the namespace's alphabet to decode
            alpha "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
            n    (reduce (fn [acc c] (.add (.multiply acc (BigInteger/valueOf 58))
                                          (BigInteger/valueOf (.indexOf alpha (int c)))))
                         BigInteger/ZERO body)
            raw  (.toByteArray n)
            v    (bytes->vec raw)
            ;; strip a possible BigInteger sign byte
            v    (if (and (> (count v) 1) (zero? (first v))) (vec (rest v)) v)]
        ;; multicodec p256-pub varint = [0x80 0x24], then 33 compressed bytes
        (is (= [0x80 0x24] (take 2 v)))
        (is (= 35 (count v)))                       ; 2 prefix + 33 point
        (is (contains? #{0x02 0x03} (nth v 2)))))))  ; compressed parity byte

(deftest sign-verify-roundtrip
  (testing "a signature verifies; a tampered message does not"
    (let [k    (keys/new-actor-key)
          msg  (.getBytes "観測を続けている。 [mirror, not advice]" "UTF-8")
          sig  (keys/sign k msg)]
      (is (= 64 (alength sig)) "compact signature is 64 bytes")
      (is (true?  (keys/verify (:public k) msg sig)))
      (is (false? (keys/verify (:public k) (.getBytes "tampered" "UTF-8") sig))))))

(deftest low-s-normalised
  (testing "s is always in the lower half (s <= n/2) across many signatures"
    (let [k (keys/new-actor-key)
          n-half (BigInteger. "7FFFFFFF800000007FFFFFFFFFFFFFFFDE737D56D38BCF4279DCE5617E3192A8" 16)]
      (doseq [i (range 25)]
        (let [sig (keys/sign k (.getBytes (str "msg-" i) "UTF-8"))
              s   (BigInteger. 1 (java.util.Arrays/copyOfRange sig 32 64))]
          (is (<= (.compareTo s n-half) 0) (str "sig " i " has high S")))))))

(deftest verification-method-shape
  (testing "verificationMethod is a did:web Multikey entry for #atproto"
    (let [k   (keys/new-actor-key)
          did "did:web:etzhayyim.com:actor:unspsc-10101500"
          vm  (keys/verification-method did (:public k))]
      (is (= (str did "#atproto") (get vm "id")))
      (is (= "Multikey" (get vm "type")))
      (is (= did (get vm "controller")))
      (is (= (:multikey k) (get vm "publicKeyMultibase"))))))

(deftest seal-unseal-roundtrip
  (testing "sealing hides the private key; unsealing restores signing; wrong secret fails"
    (let [k      (keys/new-actor-key)
          secret "node-naphtali-sealing-secret"
          blob   (keys/seal k secret)
          js     (keys/seal->json blob)]
      ;; on-disk JSON carries NO plaintext private material — only ciphertext + public
      (is (re-find #"\"ct\"" js))
      (is (re-find #"\"multikey\"" js))
      (is (not (re-find #"(?i)privatekey|scalar|pkcs8\":\s*\"0" js)))
      (let [back (keys/unseal (keys/json->seal js) secret)
            msg  (.getBytes "after-unseal" "UTF-8")
            sig  (keys/sign back msg)]
        (is (= (:multikey k) (:multikey back)) "public identity preserved across seal")
        (is (true? (keys/verify (:public k) msg sig)) "unsealed key still signs for the same identity"))
      ;; a wrong node secret cannot unseal (AES-GCM auth tag fails)
      (is (thrown? Exception (keys/unseal (keys/json->seal js) "wrong-secret"))))))

(deftest verify-from-multikey-alone
  (testing "a signature verifies through the PUBLISHED multikey only — the remote-verifier path"
    (let [k    (keys/new-actor-key)
          k2   (keys/new-actor-key)
          msg  (.getBytes "did:web:etzhayyim.com:actor:unspsc-10101500 観測" "UTF-8")
          sig  (keys/sign k msg)]
      ;; reconstructing the pubkey from the multikey yields the SAME identity bytes
      (is (= (:multikey k) (keys/multikey (keys/pubkey-from-multikey (:multikey k)))))
      ;; verify with no access to k's key object, only its multikey string
      (is (true?  (keys/verify-multikey (:multikey k) msg sig)))
      ;; tamper + wrong-actor multikey both fail
      (is (false? (keys/verify-multikey (:multikey k) (.getBytes "tampered" "UTF-8") sig)))
      (is (false? (keys/verify-multikey (:multikey k2) msg sig))))))

(deftest multikey-decompress-roundtrip
  (testing "decompress(compress(P)) preserves the point across many keys"
    (dotimes [_ 30]
      (let [k  (keys/new-actor-key)
            mk (:multikey k)]
        ;; round-trips through base58 + multicodec + point decompression
        (is (= mk (keys/multikey (keys/pubkey-from-multikey mk))))))))

(deftest record-signer-attests-and-verifies
  (testing "record-signer signs a payload; verify-b64 confirms it via the multikey only"
    (let [k       (keys/new-actor-key)
          k2      (keys/new-actor-key)
          sign    (keys/record-signer k)
          cid     "bzdj227… (a record content id)"
          payload (.getBytes cid "UTF-8")
          {:keys [sig multikey]} (sign payload)]
      (is (= (:multikey k) multikey))
      (is (string? sig))
      (is (true?  (keys/verify-b64 multikey payload sig)))
      ;; tampered payload + wrong actor's multikey both fail
      (is (false? (keys/verify-b64 multikey (.getBytes "other-cid" "UTF-8") sig)))
      (is (false? (keys/verify-b64 (:multikey k2) payload sig))))))

(deftest no-private-scalar-accessor
  (testing "the public API exposes no way to read the private scalar as bytes"
    (let [api (->> (ns-publics 'etzhayyim.pds.keys) keys (map name) set)]
      ;; structural: there is no scalar/private-bytes/export accessor in the public API
      (is (not-any? #(re-find #"(?i)scalar|private-bytes|export-priv|raw-priv" %) api)))))
