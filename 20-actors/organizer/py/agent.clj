#!/usr/bin/env bb
;; Working Clojure port of py/agent.py (organizer personal content/file organizer actor).
(ns organizer.py.agent
  "organizer — kotoba-native auto-organize file commons langgraph actor (kotoba WASM cell).

  ADR-2606072400. Replaces the legacy RisingWave-backed Worker with content-addressed,
  vault-isolated items on the kotoba Datom log.

  Hard invariants:
    G4 content-addressed dedup   identical Blake3 in a vault → one item (deduped)
    G3 vault-isolation           cross-vault read refused; collection ↔ item must share vault
    G2 no-mining                 classification emits category/labels for the OWNER only
    G6 no-server-key             only a member signature finalizes upload
    G7 Murakumo-only fallback    LLM used only when rule layer unsure; offline → 'unknown'

  Run:  bb --classpath 20-actors 20-actors/organizer/py/agent.clj"
  (:require [clojure.string :as str]))

;; ── content addressing (G4) ───────────────────────────────────────────────────
(defn content-item-id
  "Content-addressed item id. Identical content → identical id → dedup (G4).
  Matches agent.py: 'cid.' + first 16 chars of blake3_hex."
  [blake3-hex]
  (str "cid." (subs blake3-hex 0 16)))

;; ── ingest (G4 dedup, G5 encrypted ref, G6 unsigned-until-authorized) ────────
(defn ingest-item
  "Ingest an upload. If content with the same Blake3 already exists IN THIS VAULT, return
  the existing item flagged deduped (G4) — no new storage. Otherwise stage a new, unsigned
  item (member finalizes via authorize-upload, G6). Blob referenced as encrypted envelope (G5)."
  [vault-did blake3-hex blob-ref filename content-type size-bytes posted-by existing-items]
  (let [item-id (content-item-id blake3-hex)
        dup     (first (filter (fn [it]
                                 (and (= (get it "vaultDid") vault-did)
                                      (= (get it "blake3") blake3-hex)))
                               existing-items))]
    (if dup
      {"state" "deduped" "item" dup "deduped" true}
      {"state"   "staged"
       "deduped" false
       "item"    {"itemId"      item-id
                  "vaultDid"   vault-did
                  "blake3"      blake3-hex
                  "blobRef"    blob-ref          ; encrypted envelope ref (G5)
                  "filename"   filename
                  "contentType" content-type
                  "sizeBytes"  (int size-bytes)
                  "postedBy"   posted-by
                  "postedSig"  nil}})))          ; G6: unsigned until member authorizes

;; ── authorize upload (G6 no-server-key) ──────────────────────────────────────
(defn authorize-upload
  "Finalize a staged upload. ONLY a member-origin signature finalizes (G6 no-server-key)."
  [staged signature]
  (cond
    (not= (get staged "state") "staged")
    (merge staged {"refused" true "reason" "upload is not in :staged state"})

    (not= (get signature "origin") "member")
    (merge staged {"refused" true
                   "reason" "only a member passkey/wallet signature finalizes upload (G6 no-server-key)"})

    :else
    (let [item (merge (get staged "item") {"postedSig" (get signature "ref")})]
      {"state" "stored" "item" item})))

;; ── classification dictionaries (G2 owner-only) ───────────────────────────────
(def ^:private type-category
  {"application/pdf" "document"
   "text/plain"      "document"
   "image/jpeg"      "image"
   "image/png"       "image"
   "video/mp4"       "media"
   "audio/mpeg"      "media"
   "application/zip" "archive"})

(def ^:private ext-category
  {"pdf"  "document" "txt"  "document" "doc"  "document" "docx" "document"
   "jpg"  "image"    "jpeg" "image"    "png"  "image"    "heic" "image"
   "mp4"  "media"    "mov"  "media"    "mp3"  "media"
   "zip"  "archive"  "tar"  "archive"  "gz"   "archive"})

(defn- murakumo-category
  "Murakumo-only fallback (G7). In offline/local-dev returns 'unknown' — no real LLM call."
  [_item]
  "unknown")

(defn classify
  "Classify an item for the OWNER's organization (G2). Rule layer first (content-type, then
  extension); Murakumo only when the rule layer is unsure (G7). Returns category/labels/source
  scoped to the item's vault (G3) — NEVER a profile or ad signal."
  [item]
  (let [ct       (str/lower-case (or (get item "contentType") ""))
        category (get type-category ct)
        [category source]
        (if (some? category)
          [category "rule"]
          (let [fname (or (get item "filename") "")
                ext   (str/lower-case
                        (let [parts (str/split fname #"\." -1)]
                          (if (> (count parts) 1) (last parts) "")))]
            (if-let [c (get ext-category ext)]
              [c "rule"]
              ;; Murakumo-only fallback (G7); deterministic 'unknown' when host absent
              [(murakumo-category item) "rule"])))
        fname    (str/lower-case (or (get item "filename") ""))
        labels   (cond-> [category]
                   (or (str/includes? fname "receipt")
                       (str/includes? fname "invoice"))
                   (conj "receipt"))]
    {"itemId"     (get item "itemId")
     "vaultDid"  (get item "vaultDid")   ; G3: classification stays in the item's vault
     "category"  category
     "labels"    labels
     "confidence" (if (= source "rule") 1.0 0.7)
     "source"    source}))

;; ── apply-rules — auto-organize core ─────────────────────────────────────────
(defn apply-rules
  "Match the first organize-rule (by priority descending) whose condition fits the
  classification and return its collection assignment. Returns nil if no rule fits
  (the item stays uncollected — no forced bucketing)."
  [classification rules]
  (let [cat    (get classification "category")
        labels (set (get classification "labels" []))
        sorted (sort-by (fn [r] (- (int (get r "priority" 0)))) rules)]
    (reduce (fn [_ r]
              (let [cond-map (get r "condition" {})
                    cat-ok   (if (contains? cond-map "category")
                               (= (get cond-map "category") cat)
                               true)
                    lbl-ok   (if (contains? cond-map "label")
                               (contains? labels (get cond-map "label"))
                               true)]
                (when (and cat-ok lbl-ok)
                  (reduced {"itemId"      (get classification "itemId")
                             "vaultDid"  (get classification "vaultDid")
                             "collection" (get r "collection")
                             "ruleMatched" (get r "id" "")}))))
            nil sorted)))

;; ── vault isolation (G3) ──────────────────────────────────────────────────────
(defn read-item
  "Read an item only if the requester owns its vault (G3 own-data-only). A cross-vault
  read is refused — there is no global/admin read path."
  [item requester-vault-did]
  (if (not= (get item "vaultDid") requester-vault-did)
    {"state" "refused" "reason" "cross-vault read refused — own-data-only (G3)"}
    {"state" "ok" "item" item}))

;; ── collection membership (vault-isolated G3; idempotent) ────────────────────
(defn add-to-collection
  "Add an item to a collection. Refuses if item and collection are in different vaults (G3).
  Idempotent: adding a member twice does not duplicate it."
  [collection item]
  (if (not= (get collection "vaultDid") (get item "vaultDid"))
    {"state" "refused" "reason" "item and collection are in different vaults (G3)"}
    (let [members (vec (get collection "members" []))
          item-id (get item "itemId")
          members (if (some #{item-id} members)
                    members
                    (conj members item-id))]
      {"state" "ok" "collection" (merge collection {"members" members})})))

(defn remove-from-collection
  "Remove an item from a collection (idempotent — removing a non-member is a no-op)."
  [collection item-id]
  (let [members (vec (filter #(not= % item-id) (get collection "members" [])))]
    {"state" "ok" "collection" (merge collection {"members" members})}))

;; ── auto-organize — batch classify + assign ───────────────────────────────────
(defn auto-organize
  "Batch auto-organize: classify each item (G2 owner-only), match the vault's organize
  rules, and assign it to the matching collection IN THE SAME VAULT (G3). Returns the list
  of assignments {itemId, vaultDid, collection} (items with no matching rule are skipped)."
  [items collections]
  (let [by-vault (reduce (fn [m c]
                           (update m (get c "vaultDid") (fnil conj []) c))
                         {} collections)]
    (reduce (fn [assignments item]
              (let [cls   (classify item)
                    vault (get item "vaultDid")
                    colls (get by-vault vault [])]
                (or (reduce (fn [_ c]
                              (let [rules (map (fn [r] (merge r {"collection" (get c "collectionId")}))
                                              (get c "autoRules" []))]
                                (when-let [hit (apply-rules cls (vec rules))]
                                  (reduced (conj assignments hit)))))
                            nil colls)
                    assignments)))
            [] items)))

;; ── main (smoke demo) ─────────────────────────────────────────────────────────
(defn main [& _]
  (println "content-item-id:" (content-item-id "abcdef0123456789ff"))
  (println "classify pdf:"
           (get (classify {"itemId" "i" "vaultDid" "did:web:v:a"
                           "filename" "a.pdf" "contentType" "application/pdf"})
                "category"))
  (println "read-item refused:"
           (get (read-item {"vaultDid" "did:web:v:a"} "did:web:v:b") "state")))

(when (= *file* (System/getProperty "babashka.file"))
  (main))
