;; etzhayyim.test-auth — auth pure-helper invariants (cljc port).
;; Run: bb test:auth
;; Covers the pure helpers (keychain/httpx/threading legs are IO-deferred):
;; scoped-cache-key · scoped-auth-enabled? · resolve-pds · resolve-org-hint ·
;; auth-headers · audience-from-pds-url · cache-hit? · build-token-request.
(ns etzhayyim.test-auth
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [etzhayyim.auth :as auth]))

(deftest scoped-cache-key-shape
  (testing "16 hex SHA-256 prefix + ':' + nsid, deterministic, token-sensitive"
    (let [k (auth/scoped-cache-key "base-token" "com.etzhayyim.x")]
      (is (re-matches #"[0-9a-f]{16}:com\.etzhayyim\.x" k))
      (is (= k (auth/scoped-cache-key "base-token" "com.etzhayyim.x")))
      (is (not= k (auth/scoped-cache-key "other-token" "com.etzhayyim.x"))))))

(deftest scoped-auth-enabled
  (testing "off/0/false (case-insensitive, trimmed) disable; anything else enables"
    (is (false? (auth/scoped-auth-enabled? "off")))
    (is (false? (auth/scoped-auth-enabled? "0")))
    (is (false? (auth/scoped-auth-enabled? "FALSE")))
    (is (false? (auth/scoped-auth-enabled? "  off  ")))
    (is (true? (auth/scoped-auth-enabled? "on")))
    (is (true? (auth/scoped-auth-enabled? "")))
    (is (true? (auth/scoped-auth-enabled? nil)))))

(deftest resolve-pds-strips-and-defaults
  (is (= "https://x.example" (auth/resolve-pds "https://x.example/")))
  (is (= "https://x.example" (auth/resolve-pds "https://x.example///")))
  (is (= "https://atproto.etzhayyim.com" (auth/resolve-pds nil)))
  (is (= "https://atproto.etzhayyim.com" (auth/resolve-pds "   "))))

(deftest resolve-org-hint-logic
  (is (= "myorg" (auth/resolve-org-hint "myorg" "did:plc:abc")))
  (is (= "did:plc:abc" (auth/resolve-org-hint "" "did:plc:abc")))
  (is (nil? (auth/resolve-org-hint nil "did:web:x")))
  (is (nil? (auth/resolve-org-hint nil nil))))

(deftest auth-headers-assembly
  (is (= {"Authorization" "Bearer tok" "X-Active-DID" "did:plc:a" "X-etzhayyim-Org-Id" "org"}
         (auth/auth-headers "tok" "did:plc:a" "org")))
  (is (= {} (auth/auth-headers nil nil nil)))
  (testing "blanks skipped + token trimmed into the Bearer value"
    (is (= {"Authorization" "Bearer tok"} (auth/auth-headers "  tok  " "  " "")))))

(deftest audience-from-pds-url-extract
  (is (= "did:web:pds.example" (auth/audience-from-pds-url "https://pds.example/xrpc")))
  (is (= "did:web:pds.example" (auth/audience-from-pds-url "https://pds.example:8080/")))
  (is (= "" (auth/audience-from-pds-url "not a url")))
  (is (= "" (auth/audience-from-pds-url nil))))

(deftest cache-hit-and-token-request
  (testing "cache-hit? = now < exp"
    (is (true? (auth/cache-hit? 100 50)))
    (is (false? (auth/cache-hit? 100 100)))
    (is (false? (auth/cache-hit? 100 150))))
  (testing "build-token-request adds aud only when non-empty"
    (is (= {"lxm" "com.x" "exp" 123 "aud" "did:web:x"}
           (auth/build-token-request "did:web:x" "com.x" 123)))
    (is (= {"lxm" "com.x" "exp" 123} (auth/build-token-request "" "com.x" 123)))))

(defn -main [& _]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.test-auth)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
