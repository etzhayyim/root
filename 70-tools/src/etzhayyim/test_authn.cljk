;; etzhayyim.test-authn — authn pure-helper invariants (cljc port).
;; Run: bb test:authn
;; Covers the pure crypto/identity helpers (OAuth/PKCE/HTTP legs are IO-deferred):
;; b64url-encode · parse-jwt-claims (unverified) · prefer-token · build-auth-store.
(ns etzhayyim.test-authn
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [cheshire.core :as json]
            [etzhayyim.authn :as authn]))

(deftest b64url-encode-no-padding
  (testing "URL-safe base64 without '=' padding"
    (is (= "aGVsbG8" (authn/b64url-encode (.getBytes "hello" "UTF-8"))))
    (is (not (re-find #"=" (authn/b64url-encode (.getBytes "any padding?" "UTF-8")))))))

(defn- jwt-of [claims]
  (str "h." (authn/b64url-encode (.getBytes ^String (json/generate-string claims) "UTF-8")) ".sig"))

(deftest parse-jwt-claims-unverified
  (testing "sub + email are extracted from the (unverified) payload segment"
    (let [c (authn/parse-jwt-claims (jwt-of {"sub" "did:plc:abc" "email" "a@example.com"}))]
      (is (= "did:plc:abc" (:sub c)))
      (is (= "a@example.com" (:email c)))))
  (testing "missing claims default to empty strings"
    (is (= {:sub "did:plc:x" :email ""} (authn/parse-jwt-claims (jwt-of {"sub" "did:plc:x"})))))
  (testing "malformed / short / nil tokens are safe (no throw)"
    (is (= {:sub "" :email ""} (authn/parse-jwt-claims "onlyonepart")))
    (is (= {:sub "" :email ""} (authn/parse-jwt-claims "h.!!notbase64!!.s")))
    (is (= {:sub "" :email ""} (authn/parse-jwt-claims nil)))))

(deftest prefer-token-priority
  (testing "api_key > id_token > access_token"
    (is (= "k" (authn/prefer-token {"api_key" "k" "id_token" "i" "access_token" "a"})))
    (is (= "i" (authn/prefer-token {"id_token" "i" "access_token" "a"})))
    (is (= "a" (authn/prefer-token {"access_token" "a"}))))
  (testing "blank tokens are skipped; empty store → nil"
    (is (= "i" (authn/prefer-token {"api_key" "   " "id_token" "i"})))
    (is (nil? (authn/prefer-token {})))))

(deftest build-auth-store-paths
  (testing "explicit api-key → store only api_key + identity"
    (is (= {"sub" "did:s" "email" "e@x" "api_key" "mykey"}
           (authn/build-auth-store {} "did:s" "e@x" "mykey" 1000))))
  (testing "api_key from the token response is used when no explicit key"
    (is (= {"sub" "s" "email" "e" "api_key" "tk"}
           (authn/build-auth-store {"api_key" "tk"} "s" "e" "" 1000))))
  (testing "session-token path stores all tokens + expires_at = now + expires_in"
    (is (= {"sub" "s" "email" "e" "access_token" "at" "id_token" "it"
            "refresh_token" "rt" "expires_at" 4600}
           (authn/build-auth-store {"access_token" "at" "id_token" "it"
                                    "refresh_token" "rt" "expires_in" 3600}
                                   "s" "e" "" 1000))))
  (testing "no/zero expires_in → no expires_at key"
    (is (not (contains? (authn/build-auth-store {"access_token" "at"} "s" "e" "" 1000)
                        "expires_at")))))

(defn -main [& _]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.test-authn)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
