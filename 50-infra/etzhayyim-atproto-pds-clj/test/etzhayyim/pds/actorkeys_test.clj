(ns etzhayyim.pds.actorkeys-test
  "Per-actor sealed-key registry: stable identity across restart, signer↔doc
  composition (the end-to-end Path B loop), and the no-plaintext-key posture."
  (:require [clojure.test :refer [deftest is testing]]
            [clojure.java.io :as io]
            [etzhayyim.pds.actorkeys :as ak]
            [etzhayyim.pds.store :as store]
            [etzhayyim.pds.xrpc :as xrpc]
            [etzhayyim.pds.util :as util]
            [etzhayyim.pds.keys :as keys]))

(def secret "node-naphtali-sealing-secret")
(def actor "did:web:etzhayyim.com:actor:unspsc-10101500")

(defn- tmp-dir []
  (str (System/getProperty "java.io.tmpdir") "/pds-actorkeys-" (hash (str (gensym)))))

(defn- rm-rf [dir]
  (let [d (io/file dir)]
    (when (.exists d)
      (doseq [f (.listFiles d)] (.delete f))
      (.delete d))))

(deftest stable-identity-across-restart
  (testing "an actor's key is generated once, sealed to disk, and reloaded identically"
    (let [dir (tmp-dir)]
      (try
        (let [k1 (ak/load-or-create! dir actor secret)
              k2 (ak/load-or-create! dir actor secret)]   ; reloads the same sealed key
          (is (.exists (io/file (ak/key-path dir actor))))
          (is (= (:multikey k1) (:multikey k2)) "same published identity across restart")
          ;; a signature from the reloaded key verifies against the original multikey
          (let [msg (.getBytes "after-restart" "UTF-8")]
            (is (true? (keys/verify-b64 (:multikey k1) msg (keys/sign-b64 k2 msg))))))
        (finally (rm-rf dir))))))

(deftest distinct-actors-distinct-keys
  (testing "two different actors get two different keys"
    (let [dir (tmp-dir)]
      (try
        (is (not= (ak/multikey-for dir actor secret)
                  (ak/multikey-for dir "did:web:etzhayyim.com:actor:unspsc-50221000" secret)))
        (finally (rm-rf dir))))))

(deftest signer-and-doc-compose-end-to-end
  (testing "registry signer signs the write; the registry did doc verifies it (Path B loop)"
    (let [dir (tmp-dir)]
      (try
        (let [st   (store/->mem-store (ak/signer-for dir actor secret))
              coll "app.bsky.feed.post"
              rec  {"$type" coll "text" "観測を続けている。 [mirror, not advice]"
                    "createdAt" "2026-06-25T00:00:00Z"}
              body (:body (xrpc/create-record st {:repo actor :collection coll :record rec}))
              doc  (ak/did-document-for dir actor secret "unspsc-10101500.etzhayyim.com")
              vm   (first (get doc "verificationMethod"))
              cid  (util/content-cid rec)]
          (is (= (ak/multikey-for dir actor secret) (get body "signedBy")))
          (is (= (get vm "publicKeyMultibase") (get body "signedBy")) "doc key == signing key")
          ;; verifier with ONLY the resolved doc + the record verifies the write
          (is (true? (keys/verify-b64 (get vm "publicKeyMultibase")
                                      (.getBytes cid "UTF-8") (get body "sig")))))
        (finally (rm-rf dir))))))

(deftest on-disk-blob-has-no-plaintext-key
  (testing "the sealed file carries ciphertext + public key only — no private scalar"
    (let [dir (tmp-dir)]
      (try
        (ak/load-or-create! dir actor secret)
        (let [js (slurp (ak/key-path dir actor))]
          (is (re-find #"\"ct\"" js))           ; ciphertext present
          (is (re-find #"\"multikey\"" js))     ; public identity present
          (is (not (re-find #"(?i)private|scalar|secret-key" js))))
        (finally (rm-rf dir))))))

(deftest serve-actor-did-publishes-resolvable-doc
  (testing "serve-actor-did returns a did doc whose key verifies the actor's signatures"
    (let [dir (tmp-dir)]
      (try
        (let [k       (ak/load-or-create! dir actor secret)     ; mint the key first
              handle  "unspsc-10101500"
              resp    (ak/serve-actor-did dir secret handle)
              vm      (first (get-in resp [:body "verificationMethod"]))
              payload (.getBytes "a-record-cid" "UTF-8")]
          (is (= 200 (:status resp)))
          (is (= (ak/handle->actor-did handle) (get-in resp [:body "id"])))
          (is (= (:multikey k) (get vm "publicKeyMultibase")))
          ;; resolved doc's key verifies a signature the actor makes
          (is (true? (keys/verify-b64 (get vm "publicKeyMultibase")
                                      payload (keys/sign-b64 k payload)))))
        (finally (rm-rf dir))))))

(deftest serve-actor-did-404-and-passthrough
  (testing "a GET never mints a key (404 when absent), and unconfigured registry → nil passthrough"
    (let [dir (tmp-dir)]
      (try
        ;; key was never created → 404, and (crucially) the file is NOT created by the GET
        (let [resp (ak/serve-actor-did dir secret "never-seen")]
          (is (= 404 (:status resp)))
          (is (not (.exists (io/file (ak/key-path dir (ak/handle->actor-did "never-seen")))))))
        (finally (rm-rf dir))))
    (testing "no dir or no secret → nil (route falls through)"
      (is (nil? (ak/serve-actor-did nil secret "x")))
      (is (nil? (ak/serve-actor-did "/tmp/whatever" nil "x")))
      (is (nil? (ak/serve-actor-did "/tmp/whatever" secret ""))))))

(deftest registry-signer-signs-each-actor-with-its-own-key
  (testing "a multi-actor store signs each actor's write with ITS OWN key (not one shared key)"
    (let [dir   (tmp-dir)
          a1    "did:web:etzhayyim.com:actor:unspsc-10101500"
          a2    "did:web:etzhayyim.com:actor:unspsc-50221000"
          st    (store/->mem-store (ak/registry-signer dir secret))
          coll  "app.bsky.feed.post"
          rec1  {"$type" coll "text" "a1" "createdAt" "2026-06-25T00:00:00Z"}
          rec2  {"$type" coll "text" "a2" "createdAt" "2026-06-25T00:00:00Z"}]
      (try
        (let [b1 (:body (xrpc/create-record st {:repo a1 :collection coll :record rec1}))
              b2 (:body (xrpc/create-record st {:repo a2 :collection coll :record rec2}))]
          ;; each write is signed by a DIFFERENT key (each actor's own)
          (is (not= (get b1 "signedBy") (get b2 "signedBy")) "distinct per-actor keys")
          (is (= (ak/multikey-for dir a1 secret) (get b1 "signedBy")))
          (is (= (ak/multikey-for dir a2 secret) (get b2 "signedBy")))
          ;; each verifies under its own actor's published key; cross-verify fails
          (is (true?  (keys/verify-b64 (get b1 "signedBy") (.getBytes (util/content-cid rec1) "UTF-8") (get b1 "sig"))))
          (is (true?  (keys/verify-b64 (get b2 "signedBy") (.getBytes (util/content-cid rec2) "UTF-8") (get b2 "sig"))))
          (is (false? (keys/verify-b64 (get b2 "signedBy") (.getBytes (util/content-cid rec1) "UTF-8") (get b1 "sig")))))
        (finally (rm-rf dir))))))

(deftest refuses-without-node-secret
  (testing "no sealing secret → refuse (the platform holds no fallback key)"
    (let [dir (tmp-dir)]
      (is (thrown? Exception (ak/load-or-create! dir actor nil)))
      (is (thrown? Exception (ak/load-or-create! dir actor ""))))))
