(ns etzhayyim.pds.account-test
  "PDS account + session-auth invariants: the HS256 session JWT (issue → verify →
  reject forged/expired) that gates write methods when PDS_REQUIRE_AUTH is set, and
  the PBKDF2 password store. A forged or expired Bearer MUST NOT authorize a write."
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [clojure.string :as str]
            [etzhayyim.pds.account :as account]))

(defn- secret ^bytes [s] (.getBytes ^String s "UTF-8"))
(defn- tmp-file []
  (str (System/getProperty "java.io.tmpdir") "/pds-accounts-" (System/nanoTime) ".edn"))

(deftest jwt-round-trips-and-rejects-tampering
  (let [sec (secret "node-secret")
        did "did:web:etzhayyim.com:actor:unspsc-1"
        tok (account/make-jwt sec did)]
    (testing "a freshly issued JWT verifies back to its subject did"
      (is (= did (account/verify-jwt sec tok))))
    (testing "the `Bearer ` prefix is accepted"
      (is (= did (account/verify-jwt sec (str "Bearer " tok)))))
    (testing "a DIFFERENT secret does not verify (forged-issuer rejected)"
      (is (nil? (account/verify-jwt (secret "other-secret") tok))))
    (testing "a tampered token (flipped payload byte) does not verify"
      (let [[h p s] (str/split tok #"\.")
            forged (str h "." (str/reverse p) "." s)]
        (is (nil? (account/verify-jwt sec forged)))))
    (testing "garbage / non-JWT input returns nil, never throws"
      (is (nil? (account/verify-jwt sec "not-a-jwt")))
      (is (nil? (account/verify-jwt sec ""))))))

(deftest jwt-honours-expiry
  (let [sec (secret "node-secret")
        did "did:web:etzhayyim.com:actor:unspsc-2"]
    (testing "an already-expired token (negative ttl) is rejected"
      (is (nil? (account/verify-jwt sec (account/make-jwt sec did -10)))))
    (testing "a token with ample ttl is accepted"
      (is (= did (account/verify-jwt sec (account/make-jwt sec did 3600)))))))

(deftest secret-from-key-is-stable-and-key-bound
  (let [k1 (.getBytes "signing-key-material-A" "UTF-8")
        k2 (.getBytes "signing-key-material-B" "UTF-8")]
    (testing "the same key bytes derive the same HMAC secret (stable across boots)"
      (is (= (seq (account/secret-from-key k1)) (seq (account/secret-from-key k1)))))
    (testing "a different key derives a different secret"
      (is (not= (seq (account/secret-from-key k1)) (seq (account/secret-from-key k2)))))
    (testing "a JWT issued under one derived secret does NOT verify under the other"
      (let [tok (account/make-jwt (account/secret-from-key k1) "did:web:x")]
        (is (= "did:web:x" (account/verify-jwt (account/secret-from-key k1) tok)))
        (is (nil? (account/verify-jwt (account/secret-from-key k2) tok)))))))

(deftest password-store-round-trips
  (let [path (tmp-file)]
    (try
      (testing "create-account → verify-password returns the did for the right password"
        (let [{:keys [did handle]} (account/create-account path {:handle "alice" :password "s3cret"
                                                                 :did "did:web:etzhayyim.com:actor:alice"})]
          (is (= "alice" handle))
          (is (= did (account/verify-password path "alice" "s3cret")))
          (is (= did (account/account-did path "alice")))))
      (testing "a wrong password does not verify; an unknown handle is nil"
        (is (nil? (account/verify-password path "alice" "wrong")))
        (is (nil? (account/verify-password path "nobody" "s3cret"))))
      (testing "a default did is derived from the handle when none is supplied"
        (account/create-account path {:handle "bob.etzhayyim.com" :password "pw"})
        (is (= "did:web:bob.etzhayyim.com" (account/account-did path "bob.etzhayyim.com"))))
      (testing "registering a taken handle throws"
        (is (thrown? Exception (account/create-account path {:handle "alice" :password "x"}))))
      (finally (clojure.java.io/delete-file path true)))))

(defn -main [& _]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.pds.account-test)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
