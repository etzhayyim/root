(ns etzhayyim.pds.leash-test
  "Member CACAO leash: member-issued → PDS-verified → attributed to the consenting
  member; expiry / audience / scope / tamper all rejected; garbage never throws."
  (:require [clojure.test :refer [deftest is testing]]
            [clojure.string :as str]
            [clojure.java.io :as io]
            [etzhayyim.pds.leash :as leash]
            [etzhayyim.pds.store :as store]
            [etzhayyim.pds.xrpc :as xrpc]
            [etzhayyim.pds.config :as cfg]))

(def pds "did:web:atproto.etzhayyim.com")
(def now 1782000000)

(deftest didkey-roundtrip
  (testing "Ed25519 pub → did:key:z6Mk… → pub is lossless"
    (let [m (leash/gen-member-key)]
      (is (str/starts-with? (:did m) "did:key:z6Mk"))
      (is (= (:did m) (leash/pubkey->did-key (leash/did-key->pubkey (:did m))))))))

(deftest valid-leash-verifies-and-names-the-member
  (testing "a member-signed, in-audience, unexpired, in-scope leash verifies + yields the member"
    (let [m (leash/gen-member-key)
          l (leash/issue-leash m {:aud pds :exp (+ now 3600)})
          v (leash/verify-leash l {:aud pds :now now})]
      (is (true? (:valid? v)))
      (is (= (:did m) (:member v)) "the consenting human is named")
      (is (= :ok (:reason v))))))

(deftest expiry-audience-scope-and-tamper-are-rejected
  (let [m (leash/gen-member-key)]
    (testing "expired → invalid"
      (let [l (leash/issue-leash m {:aud pds :exp (- now 1)})]
        (is (= {:valid? false :member (:did m) :reason :expired}
               (leash/verify-leash l {:aud pds :now now})))))
    (testing "wrong audience (a leash for another PDS) → invalid"
      (let [l (leash/issue-leash m {:aud "did:web:other.example" :exp (+ now 3600)})]
        (is (= :wrong-audience (:reason (leash/verify-leash l {:aud pds :now now}))))))
    (testing "wrong scope → invalid"
      (let [l (leash/issue-leash m {:aud pds :exp (+ now 3600) :scope "blob:write"})]
        (is (= :wrong-scope (:reason (leash/verify-leash l {:aud pds :now now}))))))
    (testing "tampered payload (sig no longer matches) → bad-signature"
      (let [l (leash/issue-leash m {:aud pds :exp (+ now 3600)})
            [_ s64] (str/split l #"\." 2)
            ;; swap in a DIFFERENT member's payload but keep the old signature
            m2 (leash/gen-member-key)
            other (leash/issue-leash m2 {:aud pds :exp (+ now 3600)})
            forged (str (first (str/split other #"\." 2)) "." s64)]
        (is (false? (:valid? (leash/verify-leash forged {:aud pds :now now}))))))))

(deftest leash-author-glue
  (testing "leash-author returns the member only for a verifying leash, nil otherwise"
    (let [m (leash/gen-member-key)
          good (leash/issue-leash m {:aud pds :exp (+ now 3600)})
          expired (leash/issue-leash m {:aud pds :exp (- now 1)})]
      (is (= (:did m) (leash/leash-author good {:aud pds :now now})))
      (is (nil? (leash/leash-author expired {:aud pds :now now})))
      (is (nil? (leash/leash-author nil {:aud pds :now now})) "no leash → unattributed")
      (is (nil? (leash/leash-author "garbage" {:aud pds :now now}))))))

(deftest write-attributed-to-consenting-member
  (testing "a leash-derived author is persisted as :record/author + surfaced on read"
    (let [m (leash/gen-member-key)
          leash (leash/issue-leash m {:aud pds :exp (+ now 3600)})
          author (leash/leash-author leash {:aud pds :now now})
          s (store/->mem-store)]
      ;; unattributed write (no leash) → no :author
      (store/put-record s "did:web:a.example" "app.bsky.feed.post" "r1" {"text" "hi"})
      (is (nil? (:author (store/get-record s "did:web:a.example" "app.bsky.feed.post" "r1"))))
      ;; leash-attributed write → :record/author = the consenting member
      (let [res (store/put-record s "did:web:a.example" "app.bsky.feed.post" "r2"
                                  {"text" "signed life"} {:author author})]
        (is (= (:did m) (:author res)))
        (is (= (:did m) (:author (store/get-record s "did:web:a.example"
                                                   "app.bsky.feed.post" "r2"))))))))

(deftest create-record-attributes-via-presented-leash
  (testing "xrpc/createRecord with a verifying leash → :record/author = member, echoed in response"
    (let [m (leash/gen-member-key)
          ;; the member signs a leash whose audience IS this PDS
          good (leash/issue-leash m {:aud cfg/pds-did :exp (+ now 3600)})
          s (store/->mem-store)
          rec {"$type" "app.bsky.feed.post" "text" "attributed life"}
          resp (xrpc/create-record s {:repo cfg/pds-did :collection "app.bsky.feed.post"
                                      :rkey "r1" :record rec :leash good} now)]
      (is (= 200 (:status resp)))
      (is (= (:did m) (get (:body resp) "author")) "response echoes the consenting member")
      (is (= (:did m) (:author (store/get-record s cfg/pds-did "app.bsky.feed.post" "r1")))))
    (testing "no leash → unattributed, no \"author\" key (fail-open, unchanged)"
      (let [s (store/->mem-store)
            rec {"$type" "app.bsky.feed.post" "text" "anon life"}
            resp (xrpc/create-record s {:repo cfg/pds-did :collection "app.bsky.feed.post"
                                        :rkey "r2" :record rec} now)]
        (is (= 200 (:status resp)))
        (is (not (contains? (:body resp) "author")))))
    (testing "expired leash → unattributed (write still proceeds)"
      (let [m (leash/gen-member-key)
            stale (leash/issue-leash m {:aud cfg/pds-did :exp (- now 1)})
            s (store/->mem-store)
            rec {"$type" "app.bsky.feed.post" "text" "stale life"}
            resp (xrpc/create-record s {:repo cfg/pds-did :collection "app.bsky.feed.post"
                                        :rkey "r3" :record rec :leash stale} now)]
        (is (= 200 (:status resp)))
        (is (not (contains? (:body resp) "author")))))))

(deftest revocable-leash
  (testing "a leash carries a jti and can be REVOKED before expiry (charter 'revocable')"
    (let [m (leash/gen-member-key)
          l (leash/issue-leash m {:aud pds :exp (+ now 3600)})
          jti (leash/jti-of l)]
      (is (string? jti) "leash names a token id")
      ;; not in the revocation set → still valid
      (is (true? (:valid? (leash/verify-leash l {:aud pds :now now :revoked #{}}))))
      ;; member revokes THIS leash → invalid though unexpired
      (is (= :revoked (:reason (leash/verify-leash l {:aud pds :now now :revoked #{jti}}))))
      (is (false? (:valid? (leash/verify-leash l {:aud pds :now now :revoked #{jti}}))))
      ;; revoking a DIFFERENT jti does not affect this leash
      (is (true? (:valid? (leash/verify-leash l {:aud pds :now now :revoked #{"some-other-jti"}}))))
      ;; leash-author honors revocation too (write goes unattributed)
      (is (nil? (leash/leash-author l {:aud pds :now now :revoked #{jti}})))
      (is (= (:did m) (leash/leash-author l {:aud pds :now now :revoked #{}})))
      ;; a fixed jti round-trips through issue → jti-of
      (is (= "fixed-jti-123"
             (leash/jti-of (leash/issue-leash m {:aud pds :exp (+ now 3600) :jti "fixed-jti-123"})))))))

(deftest author-survives-durable-restart
  (testing "a leash-attributed write's :record/author survives a DurableStore crash/replay"
    (let [m    (leash/gen-member-key)
          path (str (System/getProperty "java.io.tmpdir") "/pds-leash-dur-" (hash (gensym)) ".ndjson")]
      (try
        ;; write through a durable store, attributed to the consenting member
        (let [s1 (store/->durable-store path)]
          (store/put-record s1 cfg/pds-did "app.bsky.feed.post" "d1"
                            {"$type" "app.bsky.feed.post" "text" "durable consent"}
                            {:author (:did m)}))
        ;; simulate a restart: a fresh store replays the on-disk journal
        (let [s2 (store/->durable-store path)
              r  (store/get-record s2 cfg/pds-did "app.bsky.feed.post" "d1")]
          (is (= (:did m) (:author r)) "the consenting member is recovered from the journal"))
        (finally (.delete (io/file path)))))))

(deftest author-is-readable-back-via-getrecord-and-listrecords
  (testing "the consenting member is OBSERVABLE on read (accountability by consent)"
    (let [m (leash/gen-member-key)
          l (leash/issue-leash m {:aud cfg/pds-did :exp (+ now 3600)})
          s (store/->mem-store)
          rec {"$type" "app.bsky.feed.post" "text" "visible consent"}]
      ;; attributed write
      (xrpc/create-record s {:repo cfg/pds-did :collection "app.bsky.feed.post"
                             :rkey "g1" :record rec :leash l} now #{})
      ;; getRecord surfaces the author
      (let [g (xrpc/get-record s {:repo cfg/pds-did :collection "app.bsky.feed.post" :rkey "g1"})]
        (is (= 200 (:status g)))
        (is (= (:did m) (get (:body g) "author"))))
      ;; listRecords surfaces the author per record
      (let [lr (xrpc/list-records s {:repo cfg/pds-did :collection "app.bsky.feed.post"})
            row (first (get (:body lr) "records"))]
        (is (= (:did m) (get row "author"))))
      ;; an UNATTRIBUTED write (no leash) carries no author key on read
      (xrpc/create-record s {:repo cfg/pds-did :collection "app.bsky.feed.post"
                             :rkey "g2" :record rec} now #{})
      (let [g (xrpc/get-record s {:repo cfg/pds-did :collection "app.bsky.feed.post" :rkey "g2"})]
        (is (not (contains? (:body g) "author")))))))

(deftest create-record-enforces-server-side-revocation
  (testing "createRecord attributes a fresh leash but REFUSES attribution once its jti is revoked"
    (let [m (leash/gen-member-key)
          l (leash/issue-leash m {:aud cfg/pds-did :exp (+ now 3600)})
          jti (leash/jti-of l)
          s (store/->mem-store)
          rec {"$type" "app.bsky.feed.post" "text" "revocable consent"}
          mk (fn [rkey revoked]
               (xrpc/create-record s {:repo cfg/pds-did :collection "app.bsky.feed.post"
                                      :rkey rkey :record rec :leash l} now revoked))]
      ;; not revoked → attributed to the member
      (is (= (:did m) (get (:body (mk "a" #{})) "author")))
      ;; server-side revocation of this jti → write proceeds but UNATTRIBUTED
      (let [resp (mk "b" #{jti})]
        (is (= 200 (:status resp)))
        (is (not (contains? (:body resp) "author")) "revoked leash → no author")))))

(deftest member-key-seal-roundtrip-and-issue
  (testing "a member seals their key, re-opens it under their secret, and issues a verifying leash"
    (let [m (leash/gen-member-key)
          secret "member-held-secret"
          blob (leash/seal-member m secret)
          ;; the sealed blob carries the public did + ciphertext only — no clear private
          _ (is (= (:did m) (:did blob)))
          _ (is (not (str/includes? (pr-str blob) "PRIVATE")))
          ;; re-open under the SAME secret → issue a leash → it verifies as the same member
          m2 (leash/unseal-member blob secret)
          _ (is (= (:did m) (:did m2)))
          l (leash/issue-leash m2 {:aud pds :exp (+ now 3600)})
          v (leash/verify-leash l {:aud pds :now now})]
      (is (true? (:valid? v)))
      (is (= (:did m) (:member v)) "issued-from-sealed leash names the original member"))
    (testing "a wrong secret cannot unseal (AES-GCM auth tag fails)"
      (let [m (leash/gen-member-key)
            blob (leash/seal-member m "right-secret")]
        (is (thrown? Exception (leash/unseal-member blob "wrong-secret")))))))

(deftest garbage-never-throws
  (testing "malformed leashes return {:valid? false}, never throw (untrusted input)"
    (doseq [bad ["" "no-dot" "a.b" "...." "x.y.z"
                 "did:key:znotreal.sig" (str "abc" "." "def")]]
      (is (false? (:valid? (leash/verify-leash bad {:aud pds :now now})))))))
