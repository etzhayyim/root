(ns iryo.methods.handoff
  "handoff.cljc — the karute -> iryo hand-off boundary (ADR-2605231401 Pattern 2
  'etzhayyim <-> vendor bridge (insurance billing)' / ADR-2606074000 G1/G2/G3/G5).

  karute's `com.etzhayyim.apps.karute.requestIryoBilling` procedure forwards a
  billing request to iryo via `agent.invoke` naming the method
  `ingestKaruteEncounterForBilling` (see karute/actor-manifest.jsonld
  'requestIryoBilling' pipeline, forwardToIryo step). Until this namespace, iryo
  had no receiving implementation for that hand-off at all — this is the boundary
  karute/MATURITY.md item 11 ('iryo(レセプト)への hand-off boundary テスト') tracks.

  Scope of THIS boundary (deliberately narrow, matches the ADR's phased rollout):
    - structural PHI-free gate on the wire request (G2) — the request may carry
      only DIDs / AT-URIs, never plaintext identity or free text;
    - consent-capability structural gate (G1/G7) — purpose / grantee / granter /
      revocation / expiry / scope, checked against the resolved capability record
      the caller supplies (ADR-2605231401's step 1 'Resolves the capability
      record' — PDS resolution itself is cross-repo / karute-side, out of scope
      here);
    - G3 no-server-key / G5 non-adjudicating: on success this only ACCEPTS the
      intake into a `:pending` draft queue (`iryoStatus \"pending\"`) — it never
      submits online and never adjudicates. On a gate failure it returns
      `iryoStatus \"needs-info\"`, NEVER `\"rejected\"` or `\"accepted\"` — those
      two values are reserved for the 審査支払機関's own adjudication (G5); an
      iryo-side intake-gate failure is not a claim decision.

  Explicitly NOT in scope (tracked separately, do not conflate):
    - Ed25519 signature verification of the capability (karute/MATURITY.md #8);
    - PDS/AT-URI resolution of records (needs `@etzhayyim/sdk`, cross-repo);
    - actual レセプト computation from the referenced encounter (that is
      `iryo.methods.agent/handle-rezept`, unchanged — this boundary only governs
      whether the intake is even accepted into iryo's queue)."
  (:require [clojure.string :as str]
            [clojure.set :as set]
            [iryo.methods.karte :as karte])
  (:import [java.time Instant]
           [java.security MessageDigest]))

(def iryo-did
  "iryo's own DID (manifest.edn :actor/did) — the only valid consentCapabilityUri
  granteeDid for this hand-off."
  "did:web:iryo.etzhayyim.com")

(def billing-purpose
  "The only consent.capability purpose this hand-off honors (ADR-2605231401)."
  "insurance-billing")

(def request-fields
  "The exact wire shape karute's requestIryoBilling forwards to
  ingestKaruteEncounterForBilling (karute/actor-manifest.jsonld forwardToIryo
  step args) — the ONLY keys allowed on the intake request. Anything else is a
  smuggled field and fails the PHI gate closed, not open."
  #{"patientDid" "encounterDid" "facilityDid"
    "serviceRequestUris" "medicationRequestUris" "consentCapabilityUri"})

(def ^:private uri-array-fields ["serviceRequestUris" "medicationRequestUris"])
(def ^:private did-fields ["patientDid" "facilityDid"])

(defn- ascii-only?
  "Real DIDs and AT-URIs are always ASCII. Any non-ASCII byte in a field this
  boundary is supposed to be codes/identifiers-only is treated as a smuggled-PHI
  signal (e.g. a Japanese patient name) — a cheap, structural defense-in-depth
  check alongside the field allow-list."
  [s]
  (every? #(< (int %) 128) (str s)))

(defn- check-ascii! [field-label s]
  (when-not (ascii-only? s)
    (karte/phi-leak! (str field-label " contains non-ASCII characters — looks like smuggled PHI, not an identifier: " s))))

(defn assert-request-phi-free!
  "Structural PHI gate for the karute -> iryo intake request (G2). Request MUST
  be `(select-keys state request-fields)` shaped — only identifiers, never
  plaintext PHI (name / dob / address / SOAP free text). Throws
  (karte/phi-leak!) on any violation; returns the request unchanged on success."
  [request]
  (doseq [k (keys request)]
    (when-not (contains? request-fields k)
      (karte/phi-leak! (str "unexpected field in iryo hand-off intake (not on the codes/DID/URI allow-list): " k))))
  (doseq [k did-fields]
    (when-let [v (get request k)]
      (check-ascii! k v)
      (when-not (str/starts-with? (str v) "did:")
        (karte/phi-leak! (str k " is not a DID: " v)))))
  (when-let [v (get request "encounterDid")]
    (check-ascii! "encounterDid" v)
    (when (str/blank? v)
      (karte/phi-leak! "encounterDid is blank"))
    (when-not (or (str/starts-with? v "did:") (str/starts-with? v "at://"))
      (karte/phi-leak! (str "encounterDid is neither a DID nor an AT-URI: " v))))
  (when-let [v (get request "consentCapabilityUri")]
    (check-ascii! "consentCapabilityUri" v)
    (when-not (str/starts-with? v "at://")
      (karte/phi-leak! (str "consentCapabilityUri is not an AT-URI: " v))))
  (doseq [field uri-array-fields]
    (doseq [uri (get request field [])]
      (check-ascii! field uri)
      (when-not (str/starts-with? (str uri) "at://")
        (karte/phi-leak! (str field " entry is not an AT-URI (PHI must never travel as inline data): " uri)))))
  request)

(defn required-scope
  "The consent.capability `scope` NSIDs this request needs, derived from which
  resource references are actually present (least-privilege check — a
  capability scoped ONLY to encounter data cannot authorize forwarding
  serviceRequest/medicationRequest records too)."
  [request]
  (cond-> #{"com.etzhayyim.karute.encounter"}
    (seq (get request "serviceRequestUris")) (conj "com.etzhayyim.karute.serviceRequest")
    (seq (get request "medicationRequestUris")) (conj "com.etzhayyim.karute.medicationRequest")))

(defn- blank-or-nil? [v] (or (nil? v) (and (string? v) (str/blank? v))))

(defn- instant-before? [a b]
  (.isBefore (Instant/parse a) (Instant/parse b)))

(defn capability-gate
  "Structural consent-capability check (G1/G7 — the licensed clinic's patient
  consented, iryo does not originate a claim on its own key). Deliberately does
  NOT verify the Ed25519 signature (karute/MATURITY.md #8, tracked separately) —
  this is the purpose/grantee/granter/revocation/expiry/scope gate only.
  `capability` is the ALREADY-RESOLVED com.etzhayyim.consent.capability record
  (string-keyed, camelCase — resolution of consentCapabilityUri itself is
  karute/PDS-side and out of scope here). Returns {:ok? true} or
  {:ok? false :reason \"...\"}."
  [capability request now]
  (cond
    (nil? capability)
    {:ok? false :reason "no consent capability resolved for consentCapabilityUri"}

    (not= billing-purpose (get capability "purpose"))
    {:ok? false :reason (str "consent capability purpose is not '" billing-purpose "': " (get capability "purpose"))}

    (not= iryo-did (get capability "granteeDid"))
    {:ok? false :reason (str "consent capability granteeDid is not iryo: " (get capability "granteeDid"))}

    (not= (get request "patientDid") (get capability "granterDid"))
    {:ok? false :reason "consent capability granterDid does not match the billed patientDid"}

    (not (blank-or-nil? (get capability "revokedAt")))
    {:ok? false :reason (str "consent capability was revoked at " (get capability "revokedAt"))}

    (blank-or-nil? (get capability "expiresAt"))
    {:ok? false :reason "consent capability has no expiresAt"}

    (not (instant-before? now (get capability "expiresAt")))
    {:ok? false :reason (str "consent capability expired at " (get capability "expiresAt"))}

    (not (set/subset? (required-scope request) (set (get capability "scope" []))))
    {:ok? false :reason (str "consent capability scope " (get capability "scope") " does not cover required scope " (required-scope request))}

    (let [allowlist (set (get capability "resourceUris" []))]
      (and (seq allowlist)
           (not (set/subset? (set (concat (get request "serviceRequestUris" [])
                                           (get request "medicationRequestUris" [])))
                              allowlist))))
    {:ok? false :reason "requested resource URIs are outside the consent capability's resourceUris allowlist"}

    :else
    {:ok? true}))

(defn- sha256-hex [^String s]
  (let [b (.digest (MessageDigest/getInstance "SHA-256") (.getBytes s "UTF-8"))]
    (apply str (map #(format "%02x" (bit-and (int %) 0xff)) b))))

(defn- claim-ref [request]
  (str "iryo-req-" (subs (sha256-hex (str (get request "patientDid") "|"
                                           (get request "encounterDid") "|"
                                           (get request "consentCapabilityUri")))
                          0 16)))

(def intent "member-principal-claim-substrate; non-adjudicating")

(def ^:private cell-only-keys
  "Keys the cell wiring adds on top of the actual karute wire payload — never
  part of the intake request itself, so they're excluded before the PHI/
  allow-list gate runs (otherwise `assert-request-phi-free!` would flag its own
  plumbing as a smuggled field)."
  #{"capability" "now"})

(defn handle-ingest
  "The `ingestKaruteEncounterForBilling` cell handler karute's requestIryoBilling
  forwards to (state is string-keyed, matching the other iryo.methods.agent
  handlers). `state` carries the wire request fields PLUS `\"capability\"` (the
  already-resolved consent.capability record) and optionally `\"now\"`
  (ISO-8601 instant string; defaults to the real current time).

  Returns a map matching com.etzhayyim.apps.karute.requestIryoBilling's output
  shape (`ack` / `iryoClaimRef` / `iryoStatus` / `error`) since the karute
  bridge's forwardToIryo step reads `iryoClaimRef`/`iryoStatus` straight through
  into its IryoBillingRequest record."
  [state]
  (let [request (apply dissoc state cell-only-keys)
        now (get state "now" (str (Instant/now)))]
    (try
      (assert-request-phi-free! request)
      (let [gate (capability-gate (get state "capability") request now)]
        (if (:ok? gate)
          {"ack" true "iryoStatus" "pending" "iryoClaimRef" (claim-ref request) "intent" intent}
          {"ack" false "iryoStatus" "needs-info" "error" (:reason gate) "intent" intent}))
      (catch #?(:clj clojure.lang.ExceptionInfo :cljs ExceptionInfo) e
        {"ack" false "iryoStatus" "needs-info" "error" (ex-message e) "intent" intent}))))
