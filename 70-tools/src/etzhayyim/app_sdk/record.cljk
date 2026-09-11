(ns etzhayyim.app-sdk.record
  "etzhayyim shared app-SDK — the AT-Proto **record** module (ADR-2606251200 §Decision 4).

  Pure, app-agnostic record helpers every `60-apps` app currently reimplements in
  TypeScript: NSID shape, record `$type`, at-uri build/parse. Portable .cljc — runs
  on bb/clj (actor/PDS side) and compiles under squint (app/edge side), so an app's
  record validation is written once and shared with the actor + PDS code (mirrors
  `etzhayyim.pds.store/at-uri` + `etzhayyim.identifier-audit` did/nsid checks).

  This is the SECOND shared-SDK module; the FIRST is the charter payment math
  (`etzhayyim.tithe`: split-tithe / parse-micros / order-total-micros / order-tithe).
  As the migration advances, the SDK grows here — apps import one `etzhayyim.app-sdk.*`
  surface instead of re-deriving these shapes per app.")

;; ── NSID (reverse-DNS lexicon id, e.g. com.etzhayyim.apps.cargo.profile) ──────
(def ^:private nsid-re
  #"^[a-z][a-z0-9]*(?:\.[a-z][a-z0-9]*){2,}$")

(defn nsid?
  "True iff `s` is a syntactically valid AT-Proto NSID: ≥3 reverse-DNS segments,
  each starting with a letter, lower-alnum. (Syntax only — not registry lookup.)"
  [s]
  (boolean (and (string? s) (re-matches nsid-re s))))

;; ── record $type ──────────────────────────────────────────────────────────────
(defn record-type
  "The record's `$type` (its lexicon NSID), or nil."
  [record]
  (when (map? record) (get record "$type")))

(defn valid-record?
  "True iff `record` is a map carrying a syntactically valid NSID `$type`
  (the atproto requirement the PDS createRecord enforces)."
  [record]
  (and (map? record) (nsid? (record-type record))))

;; ── at-uri (at://<did>/<collection>/<rkey>) ──────────────────────────────────
(defn at-uri
  "Build the canonical record at-uri. Mirrors etzhayyim.pds.store/at-uri."
  [did collection rkey]
  (str "at://" did "/" collection "/" rkey))

(def ^:private at-uri-re
  #"^at://([^/]+)/([^/]+)/(.+)$")

(defn parse-at-uri
  "Parse an at-uri into {:did :collection :rkey}, or nil if it doesn't match."
  [uri]
  (when (string? uri)
    (when-let [[_ did collection rkey] (re-matches at-uri-re uri)]
      {:did did :collection collection :rkey rkey})))
