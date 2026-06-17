#!/usr/bin/env bb
;; Clojure port of py/test_agent.py (organizer actor test harness).
(ns organizer.py.test-agent
  "organizer — test harness (babashka clojure.test; no kotoba host needed).

  Verifies the structural invariants of ADR-2606072400:
    G4 content-addressed dedup — identical Blake3 in a vault → one item (deduped)
    G3 vault-isolation         — cross-vault read refused
    G2 no-mining               — classification has no profile/ad field; labels owner-facing
    G6 no-server-key           — only a member signature finalizes upload
    auto-organize              — organize-rule maps category → collection"
  (:require [clojure.test :refer [deftest testing is run-tests]]
            [organizer.py.agent :as agent]))

(def VA "did:web:organizer.etzhayyim.com:vault:alice")
(def VB "did:web:organizer.etzhayyim.com:vault:bob")

(defn- ingest
  ([vault blake3]
   (ingest vault blake3 "doc.pdf" "application/pdf" []))
  ([vault blake3 fn ct existing]
   (agent/ingest-item vault blake3 "com.etzhayyim.encrypted:blob1" fn ct 1024
                      "did:plc:alice" existing)))

;; ── Dedup ─────────────────────────────────────────────────────────────────────
(deftest test-content-addressed-id
  (testing "content_item_id returns cid. + first 16 chars"
    (is (= "cid.abcdef0123456789"
           (agent/content-item-id "abcdef0123456789ff")))))

(deftest test-new-item-staged
  (testing "new item is staged with deduped=false"
    (let [out (ingest VA (apply str (repeat 40 "a")))]
      (is (= "staged" (get out "state")))
      (is (false? (get out "deduped"))))))

(deftest test-identical-content-dedups
  (testing "identical blake3 in same vault → deduped (G4)"
    (let [existing [{"vaultDid" VA "blake3" (apply str (repeat 40 "a")) "itemId" "cid.aaaaaaaaaaaaaaaa"}]
          out      (ingest VA (apply str (repeat 40 "a")) "doc.pdf" "application/pdf" existing)]
      (is (true? (get out "deduped")))
      (is (= "cid.aaaaaaaaaaaaaaaa" (get-in out ["item" "itemId"]))))))

(deftest test-same-content-different-vault-not-deduped
  (testing "same blake3 in different vault is NOT deduped (G3 vault isolation)"
    (let [existing [{"vaultDid" VB "blake3" (apply str (repeat 40 "a")) "itemId" "x"}]
          out      (ingest VA (apply str (repeat 40 "a")) "doc.pdf" "application/pdf" existing)]
      (is (false? (get out "deduped"))))))

;; ── Upload / authorize ────────────────────────────────────────────────────────
(deftest test-member-finalizes
  (testing "member-origin signature finalizes upload (G6)"
    (let [staged (ingest VA (apply str (repeat 40 "b")))
          out    (agent/authorize-upload staged {"origin" "member" "ref" "sig-1"})]
      (is (= "stored" (get out "state")))
      (is (= "sig-1" (get-in out ["item" "postedSig"]))))))

(deftest test-server-signature-refused
  (testing "server-origin signature is refused (G6 no-server-key)"
    (let [staged (ingest VA (apply str (repeat 40 "b")))
          out    (agent/authorize-upload staged {"origin" "server" "ref" "x"})]
      (is (true? (get out "refused")))
      (is (clojure.string/includes? (get out "reason") "G6")))))

;; ── Classify ──────────────────────────────────────────────────────────────────
(deftest test-pdf-is-document
  (testing "application/pdf content-type → category document, source rule"
    (let [c (agent/classify {"itemId" "i" "vaultDid" VA "filename" "a.pdf" "contentType" "application/pdf"})]
      (is (= "document" (get c "category")))
      (is (= "rule" (get c "source"))))))

(deftest test-extension-fallback
  (testing "octet-stream with .png extension → category image via ext fallback"
    (let [c (agent/classify {"itemId" "i" "vaultDid" VA "filename" "pic.png" "contentType" "application/octet-stream"})]
      (is (= "image" (get c "category"))))))

(deftest test-receipt-label
  (testing "filename containing 'receipt' appends receipt label"
    (let [c (agent/classify {"itemId" "i" "vaultDid" VA "filename" "receipt-202605.pdf" "contentType" "application/pdf"})]
      (is (some #{"receipt"} (get c "labels"))))))

(deftest test-no-profile-or-ad-field
  (testing "classification has no profile/ad field (G2/G3)"
    (let [c (agent/classify {"itemId" "i" "vaultDid" VA "filename" "a.pdf" "contentType" "application/pdf"})]
      (doseq [k (keys c)]
        (is (not (clojure.string/includes? (clojure.string/lower-case k) "profile")))
        (is (not (clojure.string/includes?
                   (clojure.string/replace (clojure.string/lower-case k) "addr" "")
                   "ad"))))
      (is (= VA (get c "vaultDid"))))))  ; stays in owner's vault (G2/G3)

;; ── Organize rules ────────────────────────────────────────────────────────────
(deftest test-rule-assigns-collection
  (testing "rule with matching category assigns the collection"
    (let [cls   {"itemId" "i" "vaultDid" VA "category" "image" "labels" ["image"]}
          rules [{"id" "r1" "condition" {"category" "image"} "collection" "Photos" "priority" 5}]
          out   (agent/apply-rules cls rules)]
      (is (= "Photos" (get out "collection"))))))

(deftest test-no-rule-no-force
  (testing "no matching rule returns nil (no forced bucketing)"
    (let [cls   {"itemId" "i" "vaultDid" VA "category" "archive" "labels" ["archive"]}
          rules [{"id" "r1" "condition" {"category" "image"} "collection" "Photos"}]]
      (is (nil? (agent/apply-rules cls rules))))))

;; ── Vault isolation ───────────────────────────────────────────────────────────
(deftest test-owner-reads
  (testing "owner vault DID can read the item (G3)"
    (is (= "ok" (get (agent/read-item {"vaultDid" VA} VA) "state")))))

(deftest test-cross-vault-refused
  (testing "cross-vault read is refused (G3)"
    (let [out (agent/read-item {"vaultDid" VA} VB)]
      (is (= "refused" (get out "state")))
      (is (clojure.string/includes? (get out "reason") "G3")))))

;; ── Collection membership ─────────────────────────────────────────────────────
(defn- mk-coll
  ([] (mk-coll VA))
  ([vault] {"collectionId" "c1" "vaultDid" vault "name" "Docs" "members" []}))

(defn- mk-item
  ([] (mk-item VA "cid.x"))
  ([vault iid] {"itemId" iid "vaultDid" vault}))

(deftest test-add-same-vault
  (testing "add item to same-vault collection succeeds (G3)"
    (let [out (agent/add-to-collection (mk-coll) (mk-item))]
      (is (= "ok" (get out "state")))
      (is (some #{"cid.x"} (get-in out ["collection" "members"]))))))

(deftest test-add-cross-vault-refused
  (testing "add item from different vault is refused (G3)"
    (let [out (agent/add-to-collection (mk-coll VA) (mk-item VB "cid.x"))]
      (is (= "refused" (get out "state")))
      (is (clojure.string/includes? (get out "reason") "G3")))))

(deftest test-add-idempotent
  (testing "adding the same item twice does not duplicate (idempotent)"
    (let [c  (get (agent/add-to-collection (mk-coll) (mk-item)) "collection")
          c2 (get (agent/add-to-collection c (mk-item)) "collection")]
      (is (= 1 (count (filter #{"cid.x"} (get c2 "members"))))))))

(deftest test-remove-is-noop-for-nonmember
  (testing "removing a non-member is a no-op (idempotent)"
    (let [out (agent/remove-from-collection (mk-coll) "cid.absent")]
      (is (= [] (get-in out ["collection" "members"]))))))

(deftest test-remove-member
  (testing "removing a member removes it from the collection"
    (let [c   (get (agent/add-to-collection (mk-coll) (mk-item)) "collection")
          out (agent/remove-from-collection c "cid.x")]
      (is (= [] (get-in out ["collection" "members"]))))))

;; ── Auto-organize ─────────────────────────────────────────────────────────────
(deftest test-batch-assigns-by-vault-rule
  (testing "batch auto-organize assigns items to vault-matched collections by rule"
    (let [items       [{"itemId" "cid.1" "vaultDid" VA "filename" "a.pdf" "contentType" "application/pdf"}
                       {"itemId" "cid.2" "vaultDid" VA "filename" "p.png" "contentType" "image/png"}]
          collections [{"collectionId" "Docs"   "vaultDid" VA "autoRules" [{"id" "r1" "condition" {"category" "document"}}]}
                       {"collectionId" "Photos" "vaultDid" VA "autoRules" [{"id" "r2" "condition" {"category" "image"}}]}]
          out         (agent/auto-organize items collections)
          got         (into {} (map (juxt #(get % "itemId") #(get % "collection")) out))]
      (is (= {"cid.1" "Docs" "cid.2" "Photos"} got)))))

(deftest test-does-not-cross-vault
  (testing "VB collection is not used for VA item (G3 vault isolation)"
    (let [items       [{"itemId" "cid.1" "vaultDid" VA "filename" "a.pdf" "contentType" "application/pdf"}]
          collections [{"collectionId" "Docs" "vaultDid" VB "autoRules" [{"id" "r1" "condition" {"category" "document"}}]}]
          out         (agent/auto-organize items collections)]
      (is (= [] out)))))

;; ── runner ────────────────────────────────────────────────────────────────────
(when (= *file* (System/getProperty "babashka.file"))
  (let [{:keys [fail error]} (clojure.test/run-tests 'organizer.py.test-agent)]
    (System/exit (if (zero? (+ fail error)) 0 1))))
