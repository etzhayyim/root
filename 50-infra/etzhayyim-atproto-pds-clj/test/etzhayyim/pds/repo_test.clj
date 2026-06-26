(ns etzhayyim.pds.repo-test
  "atproto repo layer invariants (the Path B verifiable-commit substrate): the MST,
  the Ed25519-signed commit, the did:key multibase publication, and CAR round-trip.
  The crux is the RELAY-side property — a verifier holding ONLY the published
  `publicKeyMultibase` can reconstruct the key and verify the repo commit `sig`."
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [etzhayyim.pds.repo :as repo]))

(deftest multibase-publishes-an-ed25519-did-key
  (testing "pubkey-multibase emits an atproto did:key Multikey (z6Mk…)"
    (let [kp (repo/gen-keypair)
          mb (repo/pubkey-multibase (.getPublic kp))]
      (is (string? mb))
      (is (.startsWith mb "z6Mk") "Ed25519 did:key always begins z6Mk")))
  (testing "multibase->pubkey is the exact inverse a relay derives (round-trips a real sig)"
    (let [kp  (repo/gen-keypair)
          mb  (repo/pubkey-multibase (.getPublic kp))
          pub (repo/multibase->pubkey mb)               ; what a relay reconstructs from did.json
          msg (.getBytes "etzhayyim-path-b" "UTF-8")
          sig (repo/sign (.getPrivate kp) msg)]
      ;; a sig made with the private key verifies against the RECONSTRUCTED public key
      (is (true? (repo/verify pub msg sig)))
      ;; a tampered message does NOT verify
      (is (false? (repo/verify pub (.getBytes "tampered" "UTF-8") sig))))))

(deftest commit-sig-verifies-against-the-published-key
  (testing "make-commit signs the unsigned commit; a relay verifies it from the multibase alone"
    (let [kp   (repo/gen-keypair)
          mb   (repo/pubkey-multibase (.getPublic kp))
          did  "did:web:etzhayyim.com:actor:unspsc-20202000"
          ;; a tiny MST root to anchor the commit's :data
          [root _] (repo/build-mst [["app.bsky.feed.post/r1" (repo/block-cid {"text" "hi"})]])
          [_ _ commit] (repo/make-commit did root "rev-1" nil (.getPrivate kp))
          ;; the relay reconstructs the signed bytes = dag-cbor of the commit WITHOUT :sig
          unsigned-cbor (repo/dag-cbor (dissoc commit :sig))
          relay-pub (repo/multibase->pubkey mb)]
      (is (= did (:did commit)))
      (is (= 3 (:version commit)))
      (is (bytes? (:sig commit)))
      (is (true? (repo/verify relay-pub unsigned-cbor (:sig commit)))
          "the commit sig verifies using only the published did:web Multikey")
      ;; a commit from a DIFFERENT key must not verify against this multibase
      (let [[_ _ other] (repo/make-commit did root "rev-1" nil (.getPrivate (repo/gen-keypair)))]
        (is (false? (repo/verify relay-pub (repo/dag-cbor (dissoc other :sig)) (:sig other))))))))

(deftest build-mst-is-deterministic
  (testing "empty entries → a single empty-node root block"
    (let [[root blocks] (repo/build-mst [])]
      (is (some? root))
      (is (= 1 (count blocks)))))
  (testing "the MST root is content-addressed: same entries → same root, different → different"
    (let [es1 [["c/a" (repo/block-cid {"v" 1})] ["c/b" (repo/block-cid {"v" 2})]]
          es2 [["c/b" (repo/block-cid {"v" 2})] ["c/a" (repo/block-cid {"v" 1})]]   ; reordered = same set
          es3 [["c/a" (repo/block-cid {"v" 1})] ["c/c" (repo/block-cid {"v" 3})]]   ; different
          r1 (repo/cid-str (first (repo/build-mst es1)))
          r2 (repo/cid-str (first (repo/build-mst es2)))
          r3 (repo/cid-str (first (repo/build-mst es3)))]
      (is (= r1 r2) "entry order does not change the MST root (entries are sorted)")
      (is (not= r1 r3) "a different record set yields a different root"))))

(deftest repo-car-round-trips-through-import
  (testing "repo-car → import-records recovers the did + records (CAR + MST + commit walk)"
    (let [kp   (repo/gen-keypair)
          did  "did:web:etzhayyim.com:actor:unspsc-1"
          recs [{:uri (str "at://" did "/app.bsky.feed.post/r1") :value {"text" "alpha" "$type" "app.bsky.feed.post"}}
                {:uri (str "at://" did "/app.bsky.feed.post/r2") :value {"text" "beta"  "$type" "app.bsky.feed.post"}}]
          {:keys [car commit-cid root]} (repo/repo-car did recs "rev-1" (.getPrivate kp))
          back (repo/import-records car)]
      (is (string? commit-cid))
      (is (string? root))
      (is (= did (:did back)))
      (is (= "rev-1" (:rev back)))
      ;; records come back as [collection rkey value], MST-ordered by key
      (is (= [["app.bsky.feed.post" "r1" {"text" "alpha" "$type" "app.bsky.feed.post"}]
              ["app.bsky.feed.post" "r2" {"text" "beta"  "$type" "app.bsky.feed.post"}]]
             (:records back))))))

(deftest keypair-is-stable-across-reload
  (testing "load-or-create-keypair persists present-only; the identity + sig survive a reload"
    (let [dir  (str (System/getProperty "java.io.tmpdir") "/etz-repo-test-" (System/nanoTime))
          path (str dir "/signing-key.edn")
          kp1  (repo/load-or-create-keypair path)            ; created
          kp2  (repo/load-or-create-keypair path)            ; reloaded from disk
          mb1  (repo/pubkey-multibase (:public kp1))
          mb2  (repo/pubkey-multibase (:public kp2))
          msg  (.getBytes "stable" "UTF-8")]
      (is (= mb1 mb2) "the published identity is stable across restart")
      ;; a sig from the RELOADED private key verifies against the ORIGINAL public key
      (is (true? (repo/verify (:public kp1) msg (repo/sign (:private kp2) msg))))
      (clojure.java.io/delete-file path true)
      (clojure.java.io/delete-file dir true))))

(defn -main [& _]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.pds.repo-test)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
