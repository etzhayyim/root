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
    (testing "default did:web falls back to the etzhayyim.com actor PATH form (ADR-2606231200 addendum 2026-07-02)"
      (is (= "did:web:etzhayyim.com:actor:cargo" (get doc "id"))))
    (is (contains? aka "at://cargo.etzhayyim.com"))
    (is (contains? aka "https://github.com/etzhayyim/com-etzhayyim-cargo"))
    (is (contains? aka (rad/rad-uri (g))) "sovereign rad: URI present")
    (is (= pk (get-in doc ["verificationMethod" 0 "publicKeyHex"])))))

(deftest did-doc-rid-str-and-legacy-did-web
  (testing "rid-str (a raw RID, not a full genesis map) also produces the rad: alsoKnownAs entry"
    (let [rid* (rad/rid (g))
          doc (rad/did-web-doc {:name "cargo" :did-web "did:web:etzhayyim.com:actor:cargo"
                                :rid-str rid*})]
      (is (contains? (set (get doc "alsoKnownAs")) (str "rad:" rid*)))))
  (testing "legacy-did-web is added to alsoKnownAs when it differs from the current did"
    (let [doc (rad/did-web-doc {:name "cargo" :did-web "did:web:etzhayyim.com:actor:cargo"
                                :legacy-did-web "did:web:etzhayyim.github.io:com-etzhayyim-cargo"})]
      (is (contains? (set (get doc "alsoKnownAs")) "did:web:etzhayyim.github.io:com-etzhayyim-cargo"))))
  (testing "legacy-did-web is NOT added to alsoKnownAs when it equals the current did (it's already the id)"
    (let [doc (rad/did-web-doc {:name "cargo" :did-web "did:web:etzhayyim.com:actor:cargo"
                                :legacy-did-web "did:web:etzhayyim.com:actor:cargo"})]
      (is (= 0 (count (filter #(= "did:web:etzhayyim.com:actor:cargo" %) (get doc "alsoKnownAs"))))))))

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

(deftest holding-datoms-shape-and-empty-default
  (let [rid* (rad/rid (g))]
    (testing "no holdings → [] (existing 312 journals untouched, RID-stable)"
      (is (= [] (rad/holding-datoms rid* nil 3)))
      (is (= [] (rad/holding-datoms rid* [] 3))))
    (testing "a holding emits a RID-side :rad/holds-dataset + dataset:<id> sub-entity"
      (let [dms (rad/holding-datoms
                 rid*
                 [{:dataset-id "gleif-lei" :layer :repo :source "gleif"
                   :cidv1 "bafkreiTEST" :freshness-days 0 :retrieved "2026-07-01"
                   :counts-toward-world-coverage true}]
                 3)
            by-e (group-by d/d-e dms)]
        (is (some #(and (= :rad/holds-dataset (d/d-a %)) (= "gleif-lei" (d/d-v %)))
                  (get by-e rid*)))
        (let [sub (get by-e "dataset:gleif-lei")]
          (is (some #(and (= :rad/type (d/d-a %)) (= :dataset-holding (d/d-v %))) sub))
          (is (some #(and (= :rad/holder (d/d-a %)) (= rid* (d/d-v %))) sub))
          (is (some #(and (= :rad/layer (d/d-a %)) (= :repo (d/d-v %))) sub))
          (is (some #(and (= :rad/cidv1 (d/d-a %)) (= "bafkreiTEST" (d/d-v %))) sub)))))
    (testing "nil-valued fields are dropped"
      (let [dms (rad/holding-datoms rid* [{:dataset-id "x" :cidv1 nil}] 1)]
        (is (not (some #(and (= :rad/cidv1 (d/d-a %)) (nil? (d/d-v %))) dms)))))))

(deftest add-holding-is-append-only-idempotent-rid-stable
  (let [a "__test_kr_hold__"
        path (rad/journal-path a)
        h {:dataset-id "jinushi-land-wdqs-r2" :layer :repo :source "wikidata:WDQS"
           :cidv1 "bafybeiTEST" :freshness-days 0 :retrieved "2026-07-01"}
        rid0 (rad/rid (g))]
    (io/delete-file path true)
    (try
      (rad/publish-identity! a (g) {:sign-fn nil})
      (let [n0 (count (log/read-log path))
            r1 (rad/add-holding! a h {:sign-fn nil})
            n1 (count (log/read-log path))
            r2 (rad/add-holding! a h {:sign-fn nil})
            n2 (count (log/read-log path))]
        (is (= rid0 (:rid r1)) "RID stable across add-holding!")
        (is (:added? r1) "first add appends holding + sigref")
        (is (> n1 n0) "append-only: log grows")
        (is (false? (:added? r2)) "idempotent by dataset-id: second add adds no holding datom")
        (is (> n2 n1) "but a fresh sigref still attests the head")
        (let [logv (log/read-log path)
              sub (filter #(= "dataset:jinushi-land-wdqs-r2" (d/d-e %)) logv)]
          (is (some #(and (= :rad/type (d/d-a %)) (= :dataset-holding (d/d-v %))) sub)
              "the dataset sub-entity is queryable from the log")))
      (finally (io/delete-file path true)))))

(deftest publish-with-holds-attaches-on-genesis-tx-rid-stable
  (let [a "__test_kr_wh__"
        path (rad/journal-path a)
        h {:dataset-id "d1" :layer :repo :cidv1 "bafkreiX"}]
    (io/delete-file path true)
    (try
      (let [r (rad/publish-identity! a (g) {:sign-fn nil :holds [h]})
            logv (log/read-log path)]
        (is (= (rad/rid (g)) (:rid r)) "RID is the genesis RID (holds don't touch genesis)")
        (is (some #(and (= :rad/holds-dataset (d/d-a %)) (= "d1" (d/d-v %))) logv)
            "holding datom present when :holds passed on publish")
        (is (some #(and (= (d/d-e %) "dataset:d1") (= :rad/cidv1 (d/d-a %))) logv)
            "dataset sub-entity present"))
      (finally (io/delete-file path true)))))

(deftest update-did-web-preserves-rid-and-is-idempotent
  (let [a "__test_kr_didweb__"
        path (rad/journal-path a)
        rid0 (rad/rid (g))]
    (io/delete-file path true)
    (try
      (rad/publish-identity! a (g) {:sign-fn nil})
      (let [n0 (count (log/read-log path))
            r1 (rad/update-did-web! a "did:web:etzhayyim.com:actor:cargo" {:sign-fn nil})
            n1 (count (log/read-log path))
            r2 (rad/update-did-web! a "did:web:etzhayyim.com:actor:cargo" {:sign-fn nil})
            n2 (count (log/read-log path))]
        (testing "the core regression guard for this whole migration: RID never changes"
          (is (= rid0 (:rid r1) (:rid r2))))
        (is (:added? r1) "first update appends a did-web datom + sigref")
        (is (> n1 n0) "append-only: log grows")
        (is (false? (:added? r2)) "idempotent by value: same target adds no datom")
        (is (> n2 n1) "but a fresh sigref still attests the head")
        (testing "genesis's original :rad/did-web is untouched"
          (let [logv (log/read-log path)]
            (is (= "did:web:etzhayyim.github.io:com-etzhayyim-cargo"
                   (rad/first-did-web logv rid0)))
            (is (= "did:web:etzhayyim.com:actor:cargo"
                   (rad/latest-did-web logv rid0))))))
      (finally (io/delete-file path true)))))

(deftest update-did-web-throws-without-existing-genesis
  (let [a "__test_kr_didweb_nogenesis__"
        path (rad/journal-path a)]
    (io/delete-file path true)
    (try
      (is (thrown? #?(:clj clojure.lang.ExceptionInfo :cljs js/Error)
                   (rad/update-did-web! a "did:web:etzhayyim.com:actor:x" {:sign-fn nil})))
      (finally (io/delete-file path true)))))

(deftest identity-status-reports-genesis-and-current-separately
  (let [a "__test_kr_status__"
        path (rad/journal-path a)]
    (io/delete-file path true)
    (try
      (is (nil? (rad/identity-status a)) "no journal yet -> nil")
      (rad/publish-identity! a (g) {:sign-fn nil})
      (testing "before any update: genesis == current"
        (let [s (rad/identity-status a)]
          (is (= (rad/rid (g)) (:rid s)))
          (is (= "did:web:etzhayyim.github.io:com-etzhayyim-cargo"
                 (:genesis-did-web s) (:current-did-web s)))))
      (rad/update-did-web! a "did:web:etzhayyim.com:actor:cargo" {:sign-fn nil})
      (testing "after an update: genesis stays original, current reflects the migration"
        (let [s (rad/identity-status a)]
          (is (= "did:web:etzhayyim.github.io:com-etzhayyim-cargo" (:genesis-did-web s)))
          (is (= "did:web:etzhayyim.com:actor:cargo" (:current-did-web s)))))
      (finally (io/delete-file path true)))))

(defn -main [& _]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.test-kotoba-rad)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
