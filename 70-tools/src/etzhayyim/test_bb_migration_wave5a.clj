;; test_bb_migration_wave5a.clj — Wave-5 Batch-A bb migration tests
;;
;; Covers: auth / authn / authz / agent-token / agent-runtime / identity
;; Run:    bb --classpath 70-tools/src 70-tools/src/etzhayyim/test_bb_migration_wave5a.clj
;; Parity verified: Python values in comments match clj output (see parity-smoke tests).

(ns etzhayyim.test-bb-migration-wave5a
  (:require [clojure.test :refer [deftest testing is run-tests]]
            [etzhayyim.auth         :as auth]
            [etzhayyim.authn        :as authn]
            [etzhayyim.authz        :as authz]
            [etzhayyim.agent-token  :as at]
            [etzhayyim.agent-runtime :as ar]
            [etzhayyim.identity     :as id]))

;; ── auth ─────────────────────────────────────────────────────────────────────

(deftest test-auth-constants
  (testing "auth constants present and non-empty"
    (is (string? auth/default-pds))
    (is (string? auth/service-auth-nsid))
    (is (pos? auth/scoped-jwt-ttl))
    (is (pos? auth/scoped-jwt-skew))))

(deftest test-scoped-cache-key
  ;; PARITY: Python hashlib.sha256("mytoken".encode()).hexdigest()[:16] + ":com.atproto.server.getServiceAuth"
  ;;         => "1a17ea3569204d6c:com.atproto.server.getServiceAuth"
  (testing "scoped-cache-key matches Python parity"
    (is (= "1a17ea3569204d6c:com.atproto.server.getServiceAuth"
           (auth/scoped-cache-key "mytoken" "com.atproto.server.getServiceAuth")))
    (is (= "2cf24dba5fb0a30e:test.nsid"
           (auth/scoped-cache-key "hello" "test.nsid"))))
  (testing "scoped-cache-key format: 16-hex-chars:nsid"
    (let [k (auth/scoped-cache-key "any" "ns")]
      (is (re-matches #"[0-9a-f]{16}:ns" k)))))

(deftest test-scoped-auth-enabled
  ;; PARITY: Python disables on ('off','0','false'), enables otherwise
  (testing "disabled values"
    (is (false? (auth/scoped-auth-enabled? "off")))
    (is (false? (auth/scoped-auth-enabled? "OFF")))
    (is (false? (auth/scoped-auth-enabled? "0")))
    (is (false? (auth/scoped-auth-enabled? "false")))
    (is (false? (auth/scoped-auth-enabled? "  false  "))))
  (testing "enabled values"
    (is (true? (auth/scoped-auth-enabled? nil)))
    (is (true? (auth/scoped-auth-enabled? "")))
    (is (true? (auth/scoped-auth-enabled? "on")))
    (is (true? (auth/scoped-auth-enabled? "1")))
    (is (true? (auth/scoped-auth-enabled? "true")))))

(deftest test-audience-from-pds-url
  ;; PARITY: Python urlparse("https://atproto.etzhayyim.com").hostname => "atproto.etzhayyim.com"
  (testing "audience extraction"
    (is (= "did:web:atproto.etzhayyim.com"
           (auth/audience-from-pds-url "https://atproto.etzhayyim.com")))
    (is (= "did:web:atproto.etzhayyim.com"
           (auth/audience-from-pds-url "https://atproto.etzhayyim.com/")))
    (is (= ""  (auth/audience-from-pds-url nil)))
    (is (= ""  (auth/audience-from-pds-url "")))))

(deftest test-resolve-pds
  (testing "strips trailing slash"
    (is (= "https://atproto.etzhayyim.com"
           (auth/resolve-pds "https://atproto.etzhayyim.com/")))
    (is (= auth/default-pds (auth/resolve-pds nil)))
    (is (= auth/default-pds (auth/resolve-pds "")))))

(deftest test-resolve-org-hint
  (testing "org env takes precedence"
    (is (= "did:plc:xyz" (auth/resolve-org-hint "did:plc:xyz" "did:plc:abc"))))
  (testing "did:plc fallback"
    (is (= "did:plc:abc" (auth/resolve-org-hint nil "did:plc:abc")))
    (is (= "did:plc:abc" (auth/resolve-org-hint "" "did:plc:abc"))))
  (testing "non-plc DID returns nil"
    (is (nil? (auth/resolve-org-hint nil "did:web:example.com")))
    (is (nil? (auth/resolve-org-hint nil nil)))))

(deftest test-auth-headers
  (testing "full headers map"
    (let [h (auth/auth-headers "mytoken" "did:plc:abc" "did:plc:abc")]
      (is (= "Bearer mytoken" (get h "Authorization")))
      (is (= "did:plc:abc" (get h "X-Active-DID")))
      (is (= "did:plc:abc" (get h "X-etzhayyim-Org-Id")))))
  (testing "nil token omitted"
    (let [h (auth/auth-headers nil "did:plc:abc" nil)]
      (is (nil? (get h "Authorization")))
      (is (= "did:plc:abc" (get h "X-Active-DID")))
      (is (nil? (get h "X-etzhayyim-Org-Id")))))
  (testing "empty token omitted"
    (let [h (auth/auth-headers "" "did:plc:abc" nil)]
      (is (nil? (get h "Authorization"))))))

(deftest test-build-token-request
  (testing "with audience"
    (let [p (auth/build-token-request "did:web:host" "com.atproto.server.getServiceAuth" 1750000000)]
      (is (= "com.atproto.server.getServiceAuth" (get p "lxm")))
      (is (= 1750000000 (get p "exp")))
      (is (= "did:web:host" (get p "aud")))))
  (testing "without audience"
    (let [p (auth/build-token-request "" "my.nsid" 42)]
      (is (not (contains? p "aud"))))))

;; ── authn ────────────────────────────────────────────────────────────────────

(deftest test-b64url-encode
  (testing "empty bytes"
    (is (= "" (authn/b64url-encode (byte-array 0)))))
  (testing "known vector (no padding)"
    ;; base64url("hello") = "aGVsbG8" (no padding)
    (is (= "aGVsbG8" (authn/b64url-encode (.getBytes "hello" "UTF-8"))))))

(deftest test-parse-jwt-claims
  ;; PARITY: Python _parse_jwt_claims returns (sub, email) from payload segment
  (testing "valid JWT with sub and email"
    ;; payload = base64url({"sub": "did:plc:abc", "email": "a@b.com"})
    (let [result (authn/parse-jwt-claims
                   "eyJhbGciOiJFUzI1NiJ9.eyJzdWIiOiAiZGlkOnBsYzphYmMiLCAiZW1haWwiOiAiYUBiLmNvbSJ9.sig")]
      (is (= "did:plc:abc" (:sub result)))
      (is (= "a@b.com" (:email result)))))
  (testing "invalid token returns empty strings"
    (let [result (authn/parse-jwt-claims "notavalidtoken")]
      (is (= "" (:sub result)))
      (is (= "" (:email result)))))
  (testing "nil token returns empty strings"
    (let [result (authn/parse-jwt-claims nil)]
      (is (= "" (:sub result)))
      (is (= "" (:email result)))))
  (testing "result always has :sub and :email keys"
    (let [r (authn/parse-jwt-claims "a.b.c")]
      (is (contains? r :sub))
      (is (contains? r :email)))))

(deftest test-prefer-token
  (testing "api_key preferred"
    (is (= "tok_api"
           (authn/prefer-token {"api_key" "tok_api" "id_token" "tok_id" "access_token" "tok_acc"}))))
  (testing "id_token over access_token"
    (is (= "tok_id"
           (authn/prefer-token {"id_token" "tok_id" "access_token" "tok_acc"}))))
  (testing "access_token fallback"
    (is (= "tok_acc"
           (authn/prefer-token {"access_token" "tok_acc"}))))
  (testing "all empty returns nil"
    (is (nil? (authn/prefer-token {})))))

(deftest test-build-auth-store
  (testing "api key path"
    (let [store (authn/build-auth-store {} "did:plc:abc" "a@b.com" "key123" 0)]
      (is (= "key123" (get store "api_key")))
      (is (= "did:plc:abc" (get store "sub")))
      (is (not (contains? store "access_token")))))
  (testing "session token path"
    (let [store (authn/build-auth-store
                  {"access_token" "at" "id_token" "it" "refresh_token" "rt" "expires_in" 3600}
                  "did:plc:abc" "a@b.com" nil 1750000000)]
      (is (= "at" (get store "access_token")))
      (is (= 1750003600 (get store "expires_at")))))
  (testing "session token without expiry"
    (let [store (authn/build-auth-store
                  {"access_token" "at" "id_token" "it"}
                  "did:plc:abc" "a@b.com" nil 0)]
      (is (not (contains? store "expires_at"))))))

;; ── authz ────────────────────────────────────────────────────────────────────

(deftest test-controlled-dids
  (testing "primary prepended when absent"
    (is (= ["did:plc:abc" "did:plc:xyz"]
           (authz/controlled-dids {"did" "did:plc:abc" "controlledDids" ["did:plc:xyz"]}))))
  (testing "primary not duplicated when already present"
    (is (= ["did:plc:abc" "did:plc:xyz"]
           (authz/controlled-dids {"did" "did:plc:abc" "controlledDids" ["did:plc:abc" "did:plc:xyz"]}))))
  (testing "empty controlled dids"
    (is (= ["did:plc:abc"]
           (authz/controlled-dids {"did" "did:plc:abc"}))))
  (testing "no primary"
    (is (= ["did:plc:xyz"]
           (authz/controlled-dids {"controlledDids" ["did:plc:xyz"]})))))

(deftest test-format-key-row
  (testing "basic row format"
    (is (= "  k1  main  read,write"
           (authz/format-key-row {"id" "k1" "label" "main" "scopes" "read,write"}))))
  (testing "nil fields become empty strings"
    (is (= "    label  "
           (authz/format-key-row {"label" "label"}))))
  (testing "active DID marker"
    (is (= "  did:plc:abc (active)"
           (authz/format-did-row "did:plc:abc" "did:plc:abc")))
    (is (= "  did:plc:xyz"
           (authz/format-did-row "did:plc:xyz" "did:plc:abc")))))

;; ── agent-token ──────────────────────────────────────────────────────────────

(deftest test-build-agent-token-payload
  (testing "basic payload"
    (let [p (at/build-agent-token-payload "com.etzhayyim.myLex" 1750000000)]
      (is (= "com.etzhayyim.myLex" (get p "lxm")))
      (is (= 1750000000 (get p "exp")))
      (is (not (contains? p "aud")))))
  (testing "with audience"
    (let [p (at/build-agent-token-payload "com.etzhayyim.myLex" 1750000000
                                           "did:web:atproto.etzhayyim.com" nil)]
      (is (= "did:web:atproto.etzhayyim.com" (get p "aud")))))
  (testing "empty audience omitted"
    (let [p (at/build-agent-token-payload "nsid" 1 "" nil)]
      (is (not (contains? p "aud"))))))

(deftest test-agent-token-xrpc-url
  (testing "builds URL"
    (is (= "https://atproto.etzhayyim.com/xrpc/com.atproto.server.getServiceAuth"
           (at/agent-token-xrpc-url "https://atproto.etzhayyim.com"))))
  (testing "strips trailing slash"
    (is (= "https://atproto.etzhayyim.com/xrpc/com.atproto.server.getServiceAuth"
           (at/agent-token-xrpc-url "https://atproto.etzhayyim.com/")))))

;; ── agent-runtime ────────────────────────────────────────────────────────────

(deftest test-agent-runtime-constants
  (testing "schema URL present"
    (is (string? ar/agent-runtime-schema))
    (is (.contains ar/agent-runtime-schema "etzhayyim.com")))
  (testing "default registry is 0x-prefixed hex"
    (is (.startsWith ar/default-registry "0x"))))

(deftest test-build-runtime-doc
  (testing "builds doc with correct structure"
    (let [doc (ar/build-runtime-doc "prod" [{"path" "a.yaml" "content" "data"}])]
      (is (= ar/agent-runtime-schema (get doc "$schema")))
      (is (= "prod" (get doc "cluster")))
      (is (= "k8s-runtime" (get doc "kind")))
      (is (= 1 (count (get doc "manifests")))))))

(deftest test-build-publish-result
  (testing "dry run result"
    (let [r (ar/build-publish-result "prod" "0xabc123" 512 true "https://ipfs.etzhayyim.com")]
      (is (true? (get r "ok")))
      (is (true? (get r "dryRun")))
      (is (= "0xabc123" (get r "sha256")))
      (is (= 512 (get r "bytes")))
      (is (false? (get r "published")))))
  (testing "strips trailing slash from ipfs-base"
    (let [r (ar/build-publish-result "x" "0x" 0 false "https://ipfs.etzhayyim.com/")]
      (is (= "https://ipfs.etzhayyim.com" (get r "ipfsBase"))))))

(deftest test-build-register-result
  (testing "register result structure"
    (let [r (ar/build-register-result "ipfs://baf..." "did:web:x" "0xowner"
                                       "0xhash" ar/default-registry ar/default-rpc ar/default-chain-id true)]
      (is (true? (get r "ok")))
      (is (true? (get r "dryRun")))
      (is (false? (get r "submitted")))
      (is (= "did:web:x" (get r "rootDid"))))))

(deftest test-build-holochain-plan
  (testing "required fields present"
    (let [plan (ar/build-holochain-plan {:agent-did "did:web:etzhayyim.com"
                                         :happ-uri  "ipfs://baf..."
                                         :dna-hash  "bafy..."})]
      (is (= "did:web:etzhayyim.com" (get plan "agentDid")))
      (is (= "ipfs://baf..." (get-in plan ["hApp" "uri"])))
      (is (= "bafy..." (get-in plan ["hApp" "dnaHash"])))
      (is (vector? (get-in plan ["k8s" "env"])))
      (is (pos? (count (get-in plan ["k8s" "env"]))))))
  (testing "env contains AGENT_DID"
    (let [plan (ar/build-holochain-plan {:agent-did "did:web:x" :happ-uri "u" :dna-hash "h"})
          env  (get-in plan ["k8s" "env"])]
      (is (some #(= "AGENT_DID" (get % "name")) env)))))

;; ── identity ─────────────────────────────────────────────────────────────────

(deftest test-compute-path-did
  ;; PARITY verified against Python:
  ;;   _compute_path_did("abc123nanoid") => "did:etzhayyim:qdgsei7znoc6jumlomfewfw4"
  ;;   _compute_path_did("hello")        => "did:etzhayyim:5u7lmmk4pnkh2lau3sxedqkh"
  (testing "parity against Python _compute_path_did"
    (is (= "did:etzhayyim:qdgsei7znoc6jumlomfewfw4"
           (id/compute-path-did "abc123nanoid")))
    (is (= "did:etzhayyim:5u7lmmk4pnkh2lau3sxedqkh"
           (id/compute-path-did "hello")))
    (is (= "did:etzhayyim:ovlhk5g3ncg5w5r3ub4ihw5e"
           (id/compute-path-did "test_nanoid_123")))
    (is (= "did:etzhayyim:fimgbmxqt43gp4ejbnn2bbxd"
           (id/compute-path-did (apply str (repeat 32 "x"))))))
  (testing "format: did:etzhayyim:<24 lowercase b32 chars>"
    (let [did (id/compute-path-did "any_nanoid")]
      (is (.startsWith did "did:etzhayyim:"))
      (let [suffix (subs did (count "did:etzhayyim:"))]
        (is (= 24 (count suffix)))
        (is (re-matches #"[a-z2-7]+" suffix))))))

(deftest test-resolve-endpoint
  (testing "DID routes to describeRepo"
    (let [[url params] (id/resolve-endpoint "did:plc:abc" "https://atproto.etzhayyim.com")]
      (is (.contains url "describeRepo"))
      (is (= "did:plc:abc" (get params "repo")))))
  (testing "handle routes to resolveHandle"
    (let [[url params] (id/resolve-endpoint "alice.bsky.social" "https://atproto.etzhayyim.com")]
      (is (.contains url "resolveHandle"))
      (is (= "alice.bsky.social" (get params "handle")))))
  (testing "strips trailing slash from base"
    (let [[url _] (id/resolve-endpoint "did:plc:abc" "https://atproto.etzhayyim.com/")]
      (is (not (.contains url "//xrpc"))))))

(deftest test-format-identity-row
  (testing "formats k/v pair"
    (is (= "  sub: did:plc:abc"
           (id/format-identity-row [:sub "did:plc:abc"])))
    (is (= "  handle: alice"
           (id/format-identity-row [:handle "alice"])))))

;; ── run ───────────────────────────────────────────────────────────────────────

(run-tests 'etzhayyim.test-bb-migration-wave5a)
