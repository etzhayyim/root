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

(deftest actors-index-enumerates-without-secret
  (testing "actors-index lists every registered actor + multikey, readable WITHOUT the secret"
    (let [dir (tmp-dir)
          a1  "did:web:etzhayyim.com:actor:unspsc-10101500"
          a2  "did:web:etzhayyim.com:actor:unspsc-50221000"]
      (try
        (let [k1 (ak/load-or-create! dir a1 secret)
              k2 (ak/load-or-create! dir a2 secret)
              idx (ak/actors-index dir)              ; NOTE: no secret passed
              by-did (into {} (map (juxt #(get % "did") #(get % "multikey")) (get idx "actors")))]
          (is (= 2 (count (get idx "actors"))))
          (is (= [a1 a2] (mapv #(get % "did") (get idx "actors"))) "sorted by did")
          (is (= (:multikey k1) (by-did a1)))
          (is (= (:multikey k2) (by-did a2)))
          ;; the listed key actually verifies a signature that actor makes
          (let [msg (.getBytes "x" "UTF-8")]
            (is (true? (keys/verify-b64 (by-did a1) msg (keys/sign-b64 k1 msg))))))
        (finally (rm-rf dir)))))
  (testing "absent / empty dir → empty index (never throws)"
    (is (= {"actors" []} (ak/actors-index (str (System/getProperty "java.io.tmpdir") "/nope-" (hash (str (gensym)))))))))

(deftest refuses-without-node-secret
  (testing "no sealing secret → refuse (the platform holds no fallback key)"
    (let [dir (tmp-dir)]
      (is (thrown? Exception (ak/load-or-create! dir actor nil)))
      (is (thrown? Exception (ak/load-or-create! dir actor ""))))))

;; ── slice 3 (apex layer): seal-free P-256 verificationMethod export ──────────
;; The apex (the did:web resolution authority consumers actually hit) must publish
;; the SAME P-256 key the PDS signs each actor's commits with, or post-cutover
;; verification fails. export-verification-methods is the bridge the apex ingests.

(deftest export-vm-carries-the-p256-signing-key
  (testing "the export publishes each actor's #atproto P-256 vm == the key the registry signs with"
    (let [dir (tmp-dir)
          a2 "did:web:etzhayyim.com:actor:unspsc-99999999"]
      (try
        ;; seal two actors (writes need the secret) …
        (ak/load-or-create! dir actor secret)
        (ak/load-or-create! dir a2 secret)
        (let [exp (get (ak/export-verification-methods dir) "actors")
              by-did (into {} (map (juxt #(get % "did") identity) exp))
              vm-of (fn [did] (-> (by-did did) (get "verificationMethod") first))
              signer (ak/registry-signer dir secret)]
          (is (= 2 (count exp)) "every registry actor is exported")
          (doseq [d [actor a2]]
            (let [vm (vm-of d)]
              (is (= (str d "#atproto") (get vm "id")) "the canonical #atproto vm id")
              (is (= "Multikey" (get vm "type")))
              ;; THE BINDING: the published multibase == the actor's actual signing key
              (is (= (ak/multikey-for dir d secret) (get vm "publicKeyMultibase")))
              (is (= (:multikey (signer d (.getBytes "x" "UTF-8")))
                     (get vm "publicKeyMultibase"))
                  "a consumer resolving this vm can verify what the PDS actually signs"))))
        (finally (rm-rf dir))))))

(deftest export-vm-is-seal-free
  (testing "export reads ONLY public multikeys — it never needs MURAKUMO_SEAL_KEY"
    (let [dir (tmp-dir)]
      (try
        (ak/load-or-create! dir actor secret)            ; sealing needs the secret …
        ;; … but the export takes NO secret arg and must still produce the vm
        (let [vm (-> (ak/export-verification-methods dir) (get "actors") first
                     (get "verificationMethod") first)]
          (is (= (ak/multikey-for dir actor secret) (get vm "publicKeyMultibase"))
              "public key recovered without the seal — safe to run in CI / the apex build"))
        (finally (rm-rf dir)))))
  (testing "absent / empty dir → empty export (never throws)"
    (is (= {"actors" []}
           (ak/export-verification-methods
            (str (System/getProperty "java.io.tmpdir") "/nope-vm-" (hash (str (gensym)))))))))
