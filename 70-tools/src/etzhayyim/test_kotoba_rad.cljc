;; etzhayyim.test-kotoba-rad — kotoba-rad sovereign-identity invariants (ADR-2606231200).
;; Run: bb test:kotoba-rad
(ns etzhayyim.test-kotoba-rad
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [clojure.java.io :as io]
            [etzhayyim.kotoba-rad :as rad]
            [etzhayyim.kotoba-rad-sign :as sign]
            [etzhayyim.kotoba.cid :as cid]
            [etzhayyim.kotoba.datom :as d]
            [etzhayyim.kotoba.log :as log]))

(def pk "9f3a7c2e1b4d5a6f8090a1b2c3d4e5f60718293a4b5c6d7e8f9012345678abcd")

(defn g [] (rad/genesis-block
            {:name "cargo" :did-web "did:web:etzhayyim.github.io:com-etzhayyim-cargo"
             :delegates [(rad/did-key pk)] :threshold 1
             :repo "github.com/etzhayyim/com-etzhayyim-cargo"
             :pds "https://pds.etzhayyim.com" :collection "com.etzhayyim.apps.cargo"}))

(deftest did-key-convention
  (testing "did:key:z<hex> matches kotoba.cljs verifier form"
    (is (= (str "did:key:z" pk) (rad/did-key pk)))
    (is (nil? (rad/did-key "not-hex!!")))))

(deftest rid-is-deterministic-and-content-addressed
  (is (= (rad/rid (g)) (rad/rid (g))) "same genesis -> same RID")
  (is (.startsWith (rad/rid (g)) "b") "CIDv1 base32 multibase")
  (testing "RID changes when identity content (delegate key) changes"
    (is (not= (rad/rid (g))
              (rad/rid (assoc (g) :rad/delegates ["did:key:zdeadbeef"]))))))

(deftest did-doc-cross-links-three-identities
  (let [doc (rad/did-web-doc {:name "cargo" :genesis (g) :pubkey-hex pk})
        aka (set (get doc "alsoKnownAs"))]
    (is (= "did:web:etzhayyim.github.io:com-etzhayyim-cargo" (get doc "id")))
    (is (contains? aka "at://cargo.etzhayyim.com"))
    (is (contains? aka "https://github.com/etzhayyim/com-etzhayyim-cargo"))
    (is (contains? aka (rad/rad-uri (g))) "sovereign rad: URI present")
    (is (= pk (get-in doc ["verificationMethod" 0 "publicKeyHex"])))))

(deftest did-doc-data-graph-service
  (testing "a KotobaDataGraph service points the DID at its CID-queryable Pages tier (ADR-2606242400)"
    (let [doc (rad/did-web-doc {:name "cargo" :genesis (g)
                                :data-graph {:root "bafkreiROOTcid" :car "data/cargo.car"
                                             :head "data/head.json"}})
          svc (->> (get doc "service") (filter #(= "KotobaDataGraph" (get % "type"))) first)]
      (is (some? svc) "service entry present")
      (is (= "bafkreiROOTcid" (get-in svc ["serviceEndpoint" "root"])))
      (is (= "data/cargo.car" (get-in svc ["serviceEndpoint" "car"]))))
    (testing "absent by default (no :data-graph) — existing callers unchanged"
      (let [doc (rad/did-web-doc {:name "cargo" :genesis (g)})]
        (is (nil? (->> (get doc "service") (filter #(= "KotobaDataGraph" (get % "type"))) first)))))))

(deftest publish-is-append-only-and-idempotent
  (let [a "__test_kotoba_rad__"
        path (rad/journal-path a)]
    (io/delete-file path true)
    (try
      (let [r1 (rad/publish-identity! a (g) {:sign-fn nil})
            n1 (count (log/read-log path))
            r2 (rad/publish-identity! a (g) {:sign-fn nil})
            n2 (count (log/read-log path))]
        (is (= (:rid r1) (:rid r2)) "RID stable across publishes")
        (is (false? (:signed? r1)) "unsigned when no :sign-fn (no-server-key)")
        (is (> n1 0))
        (is (< (:datoms-appended r2) (:datoms-appended r1))
            "re-publish appends only a fresh sigref, not the identity again")
        (is (> n2 n1) "append-only: log only grows")
        (testing "sigref attests a head AFTER the identity datoms"
          (let [logv (log/read-log path)
                sigrefs (filter #(and (= :sigref (d/d-v %)) (= :rad/type (d/d-a %))) logv)]
            (is (>= (count sigrefs) 2)))))
      (finally (io/delete-file path true)))))

(deftest base32-decode-matches-cid-framing
  (testing "decoding a real CIDv1 yields the canonical raw/sha2-256 frame"
    (let [c (cid/cid-of-edn {:hello "world"})       ; b + base32(frame)
          frame (vec (sign/cid->bytes c))]
      (is (= 36 (count frame)) "4 header + 32 sha2-256 digest")
      (is (= [1 0x55 0x12 0x20] (mapv #(bit-and % 0xff) (take 4 frame)))
          "version=1 codec=raw=0x55 mh=sha2-256=0x12 len=0x20"))))

(deftest sign-fn-is-verifier-compatible
  (testing "sign over base32-decoded CID bytes; verify with raw-hex pubkey (kotoba.cljs convention)"
    (let [{:keys [priv-b64 pub-hex did-key]} (sign/gen-keypair)
          head (rad/rid (g))
          {:keys [by sig]} ((sign/make-sign-fn {:priv-b64 priv-b64 :pub-hex pub-hex}) head)
          msg (sign/cid->bytes head)]
      (is (= did-key by) "signer reports its did:key")
      (is (= 128 (count sig)) "64-byte Ed25519 sig as hex")
      (is (true? (sign/verify-bytes pub-hex msg (sign/unhex sig))))
      (is (false? (sign/verify-bytes pub-hex (.getBytes "tampered") (sign/unhex sig)))))))

(deftest publish-signed-attaches-sig
  (let [a "__test_kr_signed__"
        path (rad/journal-path a)
        {:keys [priv-b64 pub-hex]} (sign/gen-keypair)]
    (io/delete-file path true)
    (try
      (let [r (rad/publish-identity! a (g) {:sign-fn (sign/make-sign-fn {:priv-b64 priv-b64 :pub-hex pub-hex})})
            sigs (filter #(= :rad/sig (d/d-a %)) (log/read-log path))]
        (is (true? (:signed? r)))
        (is (= 1 (count sigs)))
        (is (string? (d/d-v (first sigs)))))
      (finally (io/delete-file path true)))))

(defn -main [& _]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.test-kotoba-rad)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
