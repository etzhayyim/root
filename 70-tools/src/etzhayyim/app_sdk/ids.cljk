(ns etzhayyim.app-sdk.ids
  "etzhayyim shared app-SDK — AT-Proto **identifier** helpers (ADR-2606251200 §Decision 4).

  Pure, app-agnostic id syntax every `60-apps` app re-derives in TypeScript:
  record-key (rkey) validity, the TID-shape check, and NSID authority/name split.
  Portable .cljc (bb/clj + squint/cljs). The SDK's 4th module alongside record
  (validation), xrpc (transport) and etzhayyim.tithe (payment).")

;; ── rkey (record key) ─────────────────────────────────────────────────────────
(def ^:private rkey-re #"^[a-zA-Z0-9._~:-]{1,512}$")

(defn valid-rkey?
  "True iff `s` is a valid AT-Proto record key: 1–512 chars of [A-Za-z0-9._~:-],
  and not the reserved `.` or `..`."
  [s]
  (boolean (and (string? s)
                (re-matches rkey-re s)
                (not= s ".")
                (not= s ".."))))

;; ── TID-shaped rkey (sortable timestamp id) ──────────────────────────────────
(def ^:private tid-re #"^[234567abcdefghijklmnopqrstuvwxyz]{13}$")

(defn tid-rkey?
  "True iff `s` looks like a TID: exactly 13 chars of the sortable base32 alphabet
  (`234567a–z`). (Shape only — not a clock-validity check.)"
  [s]
  (boolean (and (string? s) (re-matches tid-re s))))

;; ── NSID authority / name split ──────────────────────────────────────────────
(defn nsid-name
  "The last segment of an NSID (the record/lexicon name), or nil. e.g.
  `com.etzhayyim.apps.cargo.profile` → `\"profile\"`."
  [nsid]
  (when (string? nsid)
    (let [i (.lastIndexOf nsid ".")]
      (when (pos? i) (subs nsid (inc i))))))

(defn nsid-authority
  "The reverse-DNS authority of an NSID (everything before the last segment), or
  nil. e.g. `com.etzhayyim.apps.cargo.profile` → `\"com.etzhayyim.apps.cargo\"`."
  [nsid]
  (when (string? nsid)
    (let [i (.lastIndexOf nsid ".")]
      (when (pos? i) (subs nsid 0 i)))))
