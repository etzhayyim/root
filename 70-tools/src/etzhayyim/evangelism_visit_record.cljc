(ns etzhayyim.evangelism-visit-record
  "Founder-only, ENCRYPTED household/individual visit-follow-up record for
  interpersonal evangelism (door-to-door etc.) — per ADR-2607111500, a
  narrow carve-out of ADR-2606281500 rule 4 ('never a target-list') and a
  clarification of ADR-2607061700 Alternatives C (whose permanent rejection
  targeted MANDATORY quota/assignment, not a founder's own voluntary
  tracking capability).

  This is a DIFFERENT lexicon from `etzhayyim.evangelism-journal`
  (`evangelismActivityAttestation`, unchanged, still carries no recipient
  data at all). This namespace's `com.etzhayyim.apps.etzhayyim.
  evangelismVisitRecord` DOES carry a household-ref + response status —
  encrypted at rest via the existing `etzhayyim.kotoba.encrypted` /
  `etzhayyim.kotoba.crypto` envelope (ADR-2605181100, real working
  XChaCha20-Poly1305 AEAD — not reimplemented here).

  Single-reader design: unlike ADR-2605181100's Signal key-wrap (built for
  multiple mutually-distrusting recipients), the founder is the only
  reader, so each record gets its own fresh symmetric key stored in a
  Keystore that is SEPARATE from the permanent ciphertext ledger. Erasure
  (a real-world data-subject request, or the founder's own choice) is
  crypto-shred: destroy the key via `destroy-key!` and append a
  `com.etzhayyim.encrypted.tombstone` (`tombstoneType: \"sealed\"`, per the
  ALREADY-DEFINED lexicon at ADR-2605231603 — not a new erasure mechanism).
  The ciphertext + tombstone remain permanently in the ledger (Tier-0
  'permanent memory' is satisfied literally) but become permanently
  unreadable — the practical effect of erasure without deleting the record.

  R0 here: pure record/read/erase logic + in-process MemKeystore +
  MemVisitLedger. R1+ (not done here): Keychain-backed Keystore (matching
  the founder's own identity-key convention) + kotobase(`IStore`)-backed
  VisitLedger for real persistence to net-kotobase."
  (:require [etzhayyim.kotoba.encrypted :as enc])
  #?(:clj (:import (java.security SecureRandom))))

(def known-statuses
  #{"not-home" "declined" "interested" "return-visit" "bible-study"})

(def followup-statuses
  "Statuses that imply the founder intends to go back — the working list
  `pending-followups` surfaces."
  #{"interested" "return-visit" "bible-study"})

(def inner-type "com.etzhayyim.apps.etzhayyim.evangelismVisitRecord")

(defn- random-bytes
  [n]
  #?(:clj (let [b (byte-array n)] (.nextBytes (SecureRandom.) b) b)
     :cljs nil))

(defn fresh-sym-key [] (random-bytes 32))
(defn fresh-nonce [] (random-bytes 24))

(defprotocol Keystore
  (get-key [ks key-id] "the symmetric key for key-id, or nil if destroyed/unknown")
  (put-key! [ks key-id sym-key] "store a fresh symmetric key")
  (destroy-key! [ks key-id] "crypto-shred: irrecoverably forget this key"))

(defrecord MemKeystore [a]
  Keystore
  (get-key [_ key-id] (get @a key-id))
  (put-key! [ks key-id sym-key] (swap! a assoc key-id sym-key) ks)
  (destroy-key! [ks key-id] (swap! a dissoc key-id) ks))

(defn seed-keystore
  "An empty MemKeystore. R1+: swap for a macOS-Keychain-backed Keystore —
  same protocol, no rewrite of callers."
  []
  (->MemKeystore (atom {})))

(defprotocol VisitLedger
  (all-envelopes [vl] "every encrypted visit envelope, oldest first")
  (append-envelope! [vl envelope] "append one immutable ciphertext envelope")
  (all-tombstones [vl] "every tombstone (rekey/redact/sealed), oldest first")
  (append-tombstone! [vl tombstone] "append one immutable tombstone"))

(defrecord MemVisitLedger [a]
  VisitLedger
  (all-envelopes [_] (:envelopes @a))
  (append-envelope! [vl envelope] (swap! a update :envelopes conj envelope) vl)
  (all-tombstones [_] (:tombstones @a))
  (append-tombstone! [vl tombstone] (swap! a update :tombstones conj tombstone) vl))

(defn seed-ledger
  "An empty MemVisitLedger. R1+: swap for a kotobase (`IStore` `-append`/
  `-read`)-backed VisitLedger — same protocol, no rewrite of callers."
  []
  (->MemVisitLedger (atom {:envelopes [] :tombstones []})))

(defn record-visit!
  "Encrypt one household visit record and append it. Generates a fresh
  per-record symmetric key + nonce (no key reuse across records), stores
  the key in `keystore`, and appends the ciphertext envelope to `ledger`.
  Returns the envelope. `now` is caller-supplied (ISO-8601 string) to keep
  this testable without a system clock read inside."
  [ledger keystore {:keys [household-ref status note now sender]}]
  {:pre [(contains? known-statuses status)
         (string? household-ref) (seq household-ref)
         (string? now) (seq now)]}
  (let [sym-key (fresh-sym-key)
        nonce (fresh-nonce)
        plaintext (cond-> {:household-ref household-ref :status status :visited-at now}
                    note (assoc :note note))
        envelope (enc/seal sym-key nonce plaintext
                           {:sender sender :innerType inner-type :createdAt now})]
    (put-key! keystore (:keyId envelope) sym-key)
    (append-envelope! ledger envelope)
    envelope))

(defn read-visit
  "Decrypt one envelope via `keystore`. Returns the plaintext map, or the
  keyword :sealed if the record's key has been crypto-shredded (erased)."
  [keystore envelope]
  (if-let [sym-key (get-key keystore (:keyId envelope))]
    (enc/open sym-key envelope)
    :sealed))

(defn erase-household!
  "Crypto-shred an erasure request (real-world data-subject request, or the
  founder's own choice): destroy the record's symmetric key, then append a
  com.etzhayyim.encrypted.tombstone (tombstoneType=\"sealed\", reason=
  \"consent-revocation-flush\", per the existing ADR-2605231603 lexicon —
  not a new mechanism). The envelope is never deleted (Tier-0 permanent
  memory) but becomes permanently unreadable, including to the founder."
  [ledger keystore envelope {:keys [actor-did now]}]
  (destroy-key! keystore (:keyId envelope))
  (append-tombstone! ledger
                      {:version 1
                       :supersededCid (enc/envelope-cid envelope)
                       :supersededKeyId (:keyId envelope)
                       :tombstoneType "sealed"
                       :reason "consent-revocation-flush"
                       :actorDid actor-did
                       :tombstoneAt now}))

(defn pending-followups
  "The founder's own working list: decrypt every envelope in `ledger` and
  return the plaintexts whose status implies a planned return visit,
  oldest-visited first. Crypto-shredded (:sealed) envelopes are silently
  skipped, never surfaced as an error — this is the entire 'evangelism
  list' this namespace supports; it is read from the founder's own
  decrypted records, never a separately-maintained target list."
  [ledger keystore]
  (->> (all-envelopes ledger)
       (keep (fn [envelope]
               (let [plaintext (read-visit keystore envelope)]
                 (when (and (map? plaintext) (contains? followup-statuses (:status plaintext)))
                   plaintext))))
       (sort-by :visited-at)))
