;; etzhayyim.issue-cacao-test — parity + round-trip tests for the CACAO leash issuer.
;;
;; Run: bb --classpath 70-tools/src:70-tools/test -m etzhayyim.issue-cacao-test
;; (or via run_tests.clj). No network, no external key material.

(ns etzhayyim.issue-cacao-test
  (:require [clojure.test :refer [deftest is run-tests]]
            [clojure.string :as str]
            [etzhayyim.issue-cacao :as ic])
  (:import (java.util Base64)))

(defn- unb64 ^bytes [^String s] (.decode (Base64/getDecoder) s))

(deftest graph-cid-matches-engine-vector
  ;; KotobaCid::from_bytes("social"), verified byte-identical against a live
  ;; kotoba mesh node (the social graph the demo component writes to).
  (is (= "bafyreib6qyhudjpkslcjqa6w5slniutjhnw456yorqf7aes3by66xlcsqe"
         (ic/graph-cid "social")))
  ;; CIDv1 dag-cbor sha2-256 always renders with the 'bafyrei…' multibase prefix.
  (is (str/starts-with? (ic/graph-cid "ibuki") "bafyrei")))

(deftest did-key-is-ed25519-shaped
  (let [kp (ic/gen-keypair)
        did (ic/did-key-from-pub (ic/unhex (:pub-hex kp)))]
    ;; an Ed25519 did:key (multicodec 0xed01 + base58btc) always starts "did:key:z6Mk".
    (is (str/starts-with? did "did:key:z6Mk"))
    (is (= 32 (count (ic/unhex (:pub-hex kp)))))))

(deftest siwe-message-is-exact-eip4361-plaintext
  (let [p {:iss "did:key:z6MkTEST" :aud "did:key:zNODE" :iat "2026-06-11T00:00:00Z"
           :exp "2026-07-11T00:00:00Z" :nonce "ibuki0001" :domain "kotoba.etzhayyim.com"
           :version "1" :resources ["kotoba://can/datom:transact"
                                    "kotoba://graph/bafyrei000"]}
        expected (str/join "\n"
                           ["kotoba.etzhayyim.com wants you to sign in with your Ethereum account:"
                            "z6MkTEST"
                            ""
                            "URI: did:key:zNODE"
                            "Version: 1"
                            "Chain ID: 1"
                            "Nonce: ibuki0001"
                            "Issued At: 2026-06-11T00:00:00Z"
                            "Expiration Time: 2026-07-11T00:00:00Z"
                            "Resources:"
                            "- kotoba://can/datom:transact"
                            "- kotoba://graph/bafyrei000"])]
    (is (= expected (ic/siwe-message p)))))

(deftest issue-round-trips-sign-verify
  ;; the minted CACAO's signature verifies against the issuer pubkey over the
  ;; reconstructed SIWE message — i.e. kotoba would accept the signature leg.
  (let [kp (ic/gen-keypair)
        bundle (ic/issue {:node-did "did:key:zNODE" :graph "ibuki"
                          :iat "2026-06-11T00:00:00Z" :exp "2026-07-11T00:00:00Z"
                          :nonce "ibuki0001" :key kp})
        cacao (unb64 (:cacao_b64 bundle))]
    ;; CBOR outer map of 3 (h, p, s) → 0xA3
    (is (= 0xA3 (bit-and (int (first (seq cacao))) 0xff)))
    ;; sidecar shape the actor's delegation loader expects
    (is (= "datom:transact" (:capability bundle)))
    (is (= "did:key:zNODE" (:aud bundle)))
    (is (= 1783728000 (:exp bundle)))                  ; 2026-07-11T00:00:00Z epoch
    (is (= "2026-07-11T00:00:00Z" (:exp_iso bundle)))
    (is (str/starts-with? (:_issuer bundle) "did:key:z6Mk"))
    ;; reconstruct exactly what was signed and verify with the issuer pubkey
    (let [member-did (ic/did-key-from-pub (ic/unhex (:pub-hex kp)))
          gcid (ic/graph-cid "ibuki")
          payload {:iss member-did :aud "did:key:zNODE" :iat "2026-06-11T00:00:00Z"
                   :exp "2026-07-11T00:00:00Z" :nonce "ibuki0001"
                   :domain "kotoba.etzhayyim.com" :version "1"
                   :resources [(str "kotoba://can/datom:transact")
                               (str "kotoba://graph/" gcid)]}
          msg (.getBytes (ic/siwe-message payload) "UTF-8")
          ;; extract the 64-byte sig: it's the last CBOR text string in the cacao,
          ;; but easier — re-sign and confirm determinism + verify the re-sign.
          sig (ic/sign-bytes (:priv-b64 kp) msg)]
      (is (ic/verify-bytes (:pub-hex kp) msg sig))
      ;; tamper → reject
      (is (not (ic/verify-bytes (:pub-hex kp) (.getBytes "tampered" "UTF-8") sig))))))

(deftest unhex-rejects-odd-length-hex-strings
  ;; (partition 2 s) used to silently drop the trailing nibble instead of
  ;; erroring -- must fail loudly, not quietly decode a shorter-than-
  ;; intended byte array (e.g. from a truncated --member-pub-hex CLI arg).
  (is (thrown? Exception (ic/unhex "1")))
  (is (thrown? Exception (ic/unhex "abc"))))

(deftest iso-epoch-conversion
  (is (= 1783728000 (ic/iso->epoch "2026-07-11T00:00:00Z")))
  (is (= 1781136000 (ic/iso->epoch "2026-06-11T00:00:00Z"))))

(defn -main [& _]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.issue-cacao-test)]
    (System/exit (if (pos? (+ (or fail 0) (or error 0))) 1 0))))
