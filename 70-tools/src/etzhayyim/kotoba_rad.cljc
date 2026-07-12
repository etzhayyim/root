;; etzhayyim.kotoba-rad — sovereign per-actor repo identity on the kotoba substrate.
;;
;; ADR-2606231200. Implements the Radicle-shaped identity model (RID / did:key /
;; sigref / identity commit-DAG) DIRECTLY on the existing kotoba primitives —
;; `etzhayyim.kotoba.{cid,datom,log}` — rather than running a separate
;; radicle-node. The actor's three identities are cross-linked:
;;
;;   B-web    did:web:etzhayyim.com:actor:<name>  (served by the etzhayyim.com
;;            CF Worker; ADR-2606231200 addendum 2026-07-02 supersedes the
;;            2026-06-24 github.io-only addendum — GitHub Pages was never
;;            enabled for 171/175 actors in practice. Already-published actors
;;            keep their original did:web:etzhayyim.github.io:... value in
;;            genesis and migrate via update-did-web!/latest-did-web below, an
;;            RID-preserving append, not a genesis rewrite. The AT handle
;;            <name>.etzhayyim.com is a SEPARATE id resolved by a DNS TXT
;;            _atproto record, needing no web host.)
;;   B-rad    rad:<RID>  +  did:key:z<hex>          (sovereign, this file)
;;   A-repo   github.com/etzhayyim/com-etzhayyim-<name>
;;
;; RID = the CIDv1 of the canonical genesis identity block (Radicle's
;; "Repository Identity" = genesis hash). Updates (delegate add / key rotation)
;; are appended to the same append-only Datom journal; `log/head-cid` is the
;; signed head (Radicle's `rad/sigrefs`).
;;
;; no-server-key (Charter substrate rule + ADR-2605231525): this namespace NEVER
;; mints a signature itself. Signing is an injected seam (`:sign-fn`) fed by the
;; MEMBER's Ed25519 key (macOS Keychain / 1Password). Absent a signer, identity
;; is published UNSIGNED (`:rad/sig nil`) with a warning — fine for the pilot /
;; --no-network degenerate case, refused for a real aozora registration.
;;
;; did:key convention: we follow the EXISTING `50-infra/etzhayyim-did-web/cljs/
;; src/did_web/kotoba.cljs` verifier, which parses `did:key:z<hex pubkey>` (NOT
;; the W3C multibase base58 form). Interop with the in-repo verifier is preferred
;; over external did:key resolvers; a reversible converter is a later add.

(ns etzhayyim.kotoba-rad
  (:require [clojure.string :as str]
            [etzhayyim.kotoba.cid :as cid]
            [etzhayyim.kotoba.datom :as d]
            [etzhayyim.kotoba.log :as log]))

(def journal-dir
  "Per-actor sovereign-identity journal lives under 80-data (NEVER in a subrepo)."
  "80-data/kotoba-rad")

(defn journal-path [actor]
  (str journal-dir "/" actor ".identity.journal.edn"))

;; ── identity / RID ──────────────────────────────────────────────────────────

(defn did-key
  "did:key:z<hex> for an Ed25519 public key given as a lowercase hex string.
   Matches kotoba.cljs's `did:key:z<hex pubkey>` verifier convention."
  [pubkey-hex]
  (when (and pubkey-hex (re-matches #"(?i)[0-9a-f]+" pubkey-hex))
    (str "did:key:z" (str/lower-case pubkey-hex))))

(defn genesis-block
  "Canonical genesis identity block. Its `cid/cid-of-edn` IS the RID, so the
   key set + value shapes here are load-bearing — keep them stable & sorted."
  [{:keys [name did-web delegates threshold repo pds collection]}]
  {:rad/type      :identity
   :rad/name      name
   :rad/did-web   did-web
   :rad/delegates (vec (sort (or delegates [])))
   :rad/threshold (or threshold 1)
   :rad/repo      repo
   :rad/aozora    {:pds pds :collection collection}})

(defn rid
  "Repository Identity = CIDv1 of the canonical genesis block."
  [genesis]
  (cid/cid-of-edn genesis))

(defn rad-uri [genesis] (str "rad:" (rid genesis)))

;; ── genesis → Datoms (entity = the RID) ─────────────────────────────────────

(defn identity-datoms
  "Flatten a genesis block into EAVT datoms keyed on the RID, at tx `tx`."
  [genesis tx]
  (let [e (rid genesis)
        aozora (:rad/aozora genesis)]
    (->> [(d/datom e :rad/type      (:rad/type genesis) tx)
          (d/datom e :rad/name      (:rad/name genesis) tx)
          (d/datom e :rad/did-web   (:rad/did-web genesis) tx)
          (d/datom e :rad/threshold (:rad/threshold genesis) tx)
          (d/datom e :rad/repo      (:rad/repo genesis) tx)
          (d/datom e :rad/aozora-pds        (:pds aozora) tx)
          (d/datom e :rad/aozora-collection (:collection aozora) tx)]
         (into (mapv #(d/datom e :rad/delegate % tx) (:rad/delegates genesis)))
         (filterv (fn [dm] (some? (d/d-v dm)))))))

(defn holding-datoms
  "Flatten a seq of dataset-holding maps into EAVT datoms at tx — one
   RID-side `:rad/holds-dataset` datom per holding plus a `dataset:<id>`
   sub-entity (mirrors the `sigref:<RID>` precedent at sigref-datom). The
   genesis block is NOT touched (holdings are a post-genesis tx, like
   add-delegate!), so the **RID stays stable** (ADR-2606231200). Returns []
   when holds is nil/empty → existing journals untouched (backward-compatible,
   same posture as the accepted :rad/age-recipient attribute, ADR-2606241500).
   ADR-2607010001 (actor data-ownership model). Each holding map:
     {:dataset-id :layer :source :cidv1 :freshness-days :retrieved
      :counts-toward-world-coverage} — nil-valued fields are dropped."
  [rid* holds tx]
  (into []
        (mapcat
         (fn [h]
           (let [e (str "dataset:" (:dataset-id h))]
             (->> [(d/datom rid* :rad/holds-dataset (:dataset-id h) tx)
                   (d/datom e :rad/type :dataset-holding tx)
                   (d/datom e :rad/holder rid* tx)
                   (d/datom e :rad/dataset-id (:dataset-id h) tx)
                   (d/datom e :rad/layer (:layer h) tx)
                   (d/datom e :rad/source (:source h) tx)
                   (d/datom e :rad/cidv1 (:cidv1 h) tx)
                   (d/datom e :rad/freshness-days (:freshness-days h) tx)
                   (d/datom e :rad/retrieved (:retrieved h) tx)
                   (d/datom e :rad/counts-toward-world-coverage
                            (:counts-toward-world-coverage h) tx)]
                  (filterv #(some? (d/d-v %))))))
         (filter :dataset-id holds))))

(defn sigref-datom
  "Signed-head datom (Radicle `rad/sigrefs`). `sig` is hex of the member's
   Ed25519 over the head-cid bytes; nil when published unsigned."
  [rid* head by sig tx]
  (let [e (str "sigref:" rid*)]
    (cond-> [(d/datom e :rad/type :sigref tx)
             (d/datom e :rad/rid  rid* tx)
             (d/datom e :rad/head head tx)]
      by  (conj (d/datom e :rad/by by tx))
      sig (conj (d/datom e :rad/sig sig tx)))))

;; ── publish (append-only, idempotent by content) ────────────────────────────

(defn publish-identity!
  "Append `genesis`'s identity datoms + a sigref to actor's journal.
   Idempotent: if the genesis datoms are already present (same RID), only a
   fresh sigref is appended (head re-attest). `sign-fn` (optional) is
   (fn [head-cid-string] -> {:by did-key :sig hex}); absent => unsigned + warn.
   Returns {:rid :head :rad-uri :datoms-appended :signed?}."
  [actor genesis {:keys [sign-fn holds]}]
  (let [path (journal-path actor)
        existing (log/read-log path)
        rid* (rid genesis)
        already? (some (fn [dm] (and (= (d/d-e dm) rid*)
                                     (= (d/d-a dm) :rad/type)
                                     (= (d/d-v dm) :identity)))
                       existing)
        tx (inc (log/max-tx existing))
        id-dms (when-not already? (identity-datoms genesis tx))
        ;; holdings ride the SAME genesis tx on first publish (post-genesis, the
        ;; genesis block is untouched → RID stable). Use add-holding! to attach
        ;; holdings to an already-published identity (ADR-2607010001).
        hold-dms (when-not already? (holding-datoms rid* holds tx))
        all-id (into (vec id-dms) (vec hold-dms))
        ;; head AFTER the identity + holding datoms land, so the sigref attests them
        head (log/head-cid (into (vec existing) all-id))
        {:keys [by sig]} (when sign-fn (sign-fn head))
        _ (when-not sign-fn
            (binding [*out* *err*]
              (println "WARN kotoba-rad: no :sign-fn — publishing UNSIGNED identity"
                       "(ok for pilot/--no-network; NOT for aozora registration)")))
        sig-dms (sigref-datom rid* head (or by (:rad/did-web genesis)) sig tx)
        all (into all-id sig-dms)]
    (log/append! path all)
    {:rid rid* :rad-uri (str "rad:" rid*) :head head
     :datoms-appended (count all) :signed? (boolean sig)}))

(defn genesis-rid-in
  "The RID (genesis identity entity) recorded in an existing journal log, or nil."
  [existing]
  (some (fn [dm] (when (and (= (d/d-a dm) :rad/type) (= (d/d-v dm) :identity))
                   (d/d-e dm)))
        existing))

(defn add-delegate!
  "Register a member `did:key` (from raw Ed25519 `pubkey-hex`) as a `:rad/delegate`
   of an EXISTING actor identity by APPENDING to the journal — the genesis block is
   left untouched, so the **RID is stable** (ADR-2606231200: 'delegate 追加・rotation
   は新しい identity Datom + 旧 head 参照として追記', ADR-2606251200 A-2/§Remaining).
   This is the retrofit path for the delegate-less pilot journals; once present, the
   kotoba-server `rad_registry` reads the delegate and the node roots that repo's git
   push authority in it (sovereign push).

   Idempotent by value: a delegate already present adds no datom (only a fresh
   sigref re-attesting the head). `sign-fn` (optional) is the no-server-key member
   signing seam (fn [head-cid] -> {:by did-key :sig hex}); absent => unsigned + warn.
   Returns {:rid :did-key :head :added? :signed?}."
  [actor pubkey-hex {:keys [sign-fn]}]
  (let [path     (journal-path actor)
        existing (log/read-log path)
        rid*     (genesis-rid-in existing)
        _        (when-not rid*
                   (throw (ex-info (str "no genesis identity in journal for " actor
                                        " — run actor:publish first")
                                   {:actor actor :path path})))
        dk       (did-key pubkey-hex)
        _        (when-not dk
                   (throw (ex-info (str "invalid pubkey-hex for " actor)
                                   {:actor actor :pubkey-hex pubkey-hex})))
        present? (some (fn [dm] (and (= (d/d-e dm) rid*)
                                     (= (d/d-a dm) :rad/delegate)
                                     (= (d/d-v dm) dk)))
                       existing)
        tx       (inc (log/max-tx existing))
        del-dms  (when-not present? [(d/datom rid* :rad/delegate dk tx)])
        ;; head AFTER the delegate datom lands, so the sigref attests it
        head     (log/head-cid (into (vec existing) (vec del-dms)))
        {:keys [by sig]} (when sign-fn (sign-fn head))
        _        (when-not sign-fn
                   (binding [*out* *err*]
                     (println "WARN kotoba-rad add-delegate!: no :sign-fn —"
                              "sigref attesting the new delegate is UNSIGNED")))
        sig-dms  (sigref-datom rid* head (or by dk) sig tx)
        all      (into (vec del-dms) sig-dms)]
    (log/append! path all)
    {:rid rid* :did-key dk :head head
     :added? (boolean (seq del-dms)) :signed? (boolean sig)}))

(defn add-holding!
  "Register a dataset holding on an EXISTING actor identity by APPENDING to the
   journal — the genesis block is left untouched, so the **RID is stable** (the
   same retrofit path as add-delegate!). Emits a RID-side :rad/holds-dataset
   datom + a `dataset:<id>` sub-entity at a new tx, then re-attests the head via
   a fresh sigref. This is the **backfill entry-point** for the existing pilot
   journals (no history rewrite; ADR-2607010001 actor data-ownership model).

   Idempotent by :dataset-id: a holding already present adds no datom (only a
   fresh sigref re-attesting the head). `sign-fn` (optional) is the no-server-key
   member signing seam (fn [head-cid] -> {:by did-key :sig hex}); absent =>
   unsigned + warn. `holding` keys: :dataset-id (required) :layer :source :cidv1
   :freshness-days :retrieved :counts-toward-world-coverage.
   Returns {:rid :dataset-id :head :added? :signed?}."
  [actor holding {:keys [sign-fn]}]
  (let [path     (journal-path actor)
        existing (log/read-log path)
        rid*     (genesis-rid-in existing)
        _        (when-not rid*
                   (throw (ex-info (str "no genesis identity in journal for " actor
                                        " — run actor:publish first")
                                   {:actor actor :path path})))
        _        (when-not (:dataset-id holding)
                   (throw (ex-info (str "add-holding! requires :dataset-id for " actor)
                                   {:actor actor :holding holding})))
        present? (some (fn [dm] (and (= (d/d-e dm) rid*)
                                     (= (d/d-a dm) :rad/holds-dataset)
                                     (= (d/d-v dm) (:dataset-id holding))))
                       existing)
        tx       (inc (log/max-tx existing))
        hold-dms (when-not present? (holding-datoms rid* [holding] tx))
        ;; head AFTER the holding datoms land, so the sigref attests them
        head     (log/head-cid (into (vec existing) (vec hold-dms)))
        {:keys [by sig]} (when sign-fn (sign-fn head))
        _        (when-not sign-fn
                   (binding [*out* *err*]
                     (println "WARN kotoba-rad add-holding!: no :sign-fn —"
                              "sigref attesting the new holding is UNSIGNED")))
        sig-dms  (sigref-datom rid* head (or by rid*) sig tx)
        all      (into (vec hold-dms) sig-dms)]
    (log/append! path all)
    {:rid rid* :dataset-id (:dataset-id holding) :head head
     :added? (boolean (seq hold-dms)) :signed? (boolean sig)}))

(defn- did-web-datoms-for [existing rid*]
  (filter (fn [dm] (and (= (d/d-e dm) rid*) (= (d/d-a dm) :rad/did-web))) existing))

(defn first-did-web
  "The ORIGINAL (genesis-tx, immutable) `:rad/did-web` value on `rid*` within
   `existing` — the value genesis was minted with, forever, regardless of any
   later `update-did-web!` appends. This is what genesis's RID was computed
   over, so it never changes for a given RID."
  [existing rid*]
  (->> (did-web-datoms-for existing rid*) (sort-by d/d-tx) first d/d-v))

(defn latest-did-web
  "The most-recently-appended `:rad/did-web` datom value on `rid*` within
   `existing` (the tx-ordered journal), i.e. the CURRENT did:web for that
   identity — genesis's original value if `update-did-web!` was never called,
   else the latest update. Genesis itself is never touched (see
   `update-did-web!`), so this is the only place \"current DID\" is computed."
  [existing rid*]
  (->> (did-web-datoms-for existing rid*) (sort-by d/d-tx) last d/d-v))

(defn identity-status
  "One-read summary of an actor's published identity, or nil if the actor has
   no journal / no genesis yet. `:genesis-did-web` is the ORIGINAL, immutable,
   RID-determining value; `:current-did-web` is the latest (possibly
   `update-did-web!`-migrated) value — identical to `:genesis-did-web` if no
   update has ever been appended. Callers (e.g. actor_publish.cljc's
   step-did-web) use this to decide new-actor vs. existing-actor handling
   WITHOUT ever recomputing genesis for an already-published actor (that
   would mint a new RID)."
  [actor]
  (let [existing (log/read-log (journal-path actor))
        rid* (genesis-rid-in existing)]
    (when rid*
      {:rid rid*
       :genesis-did-web (first-did-web existing rid*)
       :current-did-web (latest-did-web existing rid*)})))

(defn update-did-web!
  "Record a NEW did:web value for an EXISTING actor identity by APPENDING to
   the journal — the genesis block is left untouched, so the **RID is stable**
   (same retrofit path as add-delegate!/add-holding!). This is the RID-safe
   way to migrate an already-published actor to a new DID hosting scheme
   (ADR-2606231200 addendum 2026-07-02): genesis's original
   `:rad/did-web` stays as a historical record; `latest-did-web` resolves the
   CURRENT value from the append log.

   Idempotent by value: if `did-web` already equals the latest recorded value,
   adds no datom (only a fresh sigref re-attesting the head). `sign-fn`
   (optional) is the no-server-key member signing seam (fn [head-cid] ->
   {:by did-key :sig hex}); absent => unsigned + warn.
   Returns {:rid :did-web :head :added? :signed?}."
  [actor did-web {:keys [sign-fn]}]
  (let [path     (journal-path actor)
        existing (log/read-log path)
        rid*     (genesis-rid-in existing)
        _        (when-not rid*
                   (throw (ex-info (str "no genesis identity in journal for " actor
                                        " — run actor:publish first")
                                   {:actor actor :path path})))
        current  (latest-did-web existing rid*)
        tx       (inc (log/max-tx existing))
        dw-dms   (when (not= current did-web)
                   [(d/datom rid* :rad/did-web did-web tx)])
        ;; head AFTER the did-web datom lands, so the sigref attests it
        head     (log/head-cid (into (vec existing) (vec dw-dms)))
        {:keys [by sig]} (when sign-fn (sign-fn head))
        _        (when-not sign-fn
                   (binding [*out* *err*]
                     (println "WARN kotoba-rad update-did-web!: no :sign-fn —"
                              "sigref attesting the new did-web is UNSIGNED")))
        sig-dms  (sigref-datom rid* head (or by did-web) sig tx)
        all      (into (vec dw-dms) sig-dms)]
    (log/append! path all)
    {:rid rid* :did-web did-web :head head
     :added? (boolean (seq dw-dms)) :signed? (boolean sig)}))

;; ── did:web did.json (github.io path form, static — cross-linked to rad+repo) ─
;; ADR-2606231200 addendum (2026-06-24): the actor did.json is a STATIC file at
;; the repo's Pages root (/.well-known/did.json), served by GitHub Pages over
;; github.io's own TLS. No custom domain, no CF Worker, no dynamic generation —
;; key rotation is a commit/PR, which is the no-server-key + self-evolution path.
;; SUPERSEDED for the `id`/service default by the later addendum migrating to
;; did:web:etzhayyim.com:actor:<name> (RID-preserving; see update-did-web!
;; above) — existing actors are migrated via update-did-web!/latest-did-web,
;; not by rewriting genesis.

(defn did-web-doc
  "W3C DID Document for did:web:etzhayyim.com:actor:<name> (or whatever
   `did-web` the caller passes — see update-did-web!/latest-did-web for the
   RID-preserving migration path), cross-linking the sovereign rad: identity,
   the AT handle, and the GitHub mirror in alsoKnownAs. Pass either `genesis`
   (a full genesis map, for a brand-new actor) or `rid-str` (a raw RID
   string, for an already-published actor whose genesis is never
   recomputed) to add the `rad:<RID>` alsoKnownAs entry. `legacy-did-web`
   (optional) adds a prior did:web value (e.g. the original
   did:web:etzhayyim.github.io:... form) into alsoKnownAs, so resolvers still
   recognize an actor's earlier identity after a scheme migration.
   `pubkey-hex` (optional) adds an Ed25519 verificationMethod. `data-graph`
   (optional, {:root :car :head}) adds a KotobaDataGraph service so resolving
   the DID locates the CID-queryable Pages data tier (ADR-2606242400)."
  [{:keys [name did-web genesis rid-str legacy-did-web pubkey-hex data-graph]}]
  (let [did (or did-web (str "did:web:etzhayyim.com:actor:" name))
        dk  (some-> pubkey-hex did-key)
        rad-str (cond genesis (rad-uri genesis) rid-str (str "rad:" rid-str) :else nil)
        services (cond-> [{"id" (str did "#atproto_pds")
                           "type" "AtprotoPersonalDataServer"
                           "serviceEndpoint" "https://pds.aozora.app"}
                          {"id" (str did "#aozora")
                           "type" "AozoraAppView"
                           "serviceEndpoint" "https://aozora.app"}]
                   data-graph
                   (conj {"id" (str did "#kotoba-data")
                          "type" "KotobaDataGraph"
                          "serviceEndpoint" {"root" (:root data-graph)
                                             "car" (or (:car data-graph) "data/")
                                             "head" (or (:head data-graph) "data/head.json")}}))]
    (cond-> {"@context" ["https://www.w3.org/ns/did/v1"
                         "https://w3id.org/security/suites/ed25519-2020/v1"]
             "id" did
             "alsoKnownAs" (cond-> [(str "at://" name ".etzhayyim.com")
                                    (str "https://github.com/etzhayyim/com-etzhayyim-" name)]
                             rad-str (conj rad-str)
                             (and legacy-did-web (not= legacy-did-web did))
                             (conj legacy-did-web))
             "service" services}
      dk (assoc "verificationMethod"
                [{"id" (str did "#key-0")
                  "type" "Ed25519VerificationKey2020"
                  "controller" did
                  ;; multibase form left to the operator key tool; we expose the
                  ;; same hex the rad did:key uses so the two identities pin to
                  ;; one key. (publicKeyMultibase is the W3C field; filled by the
                  ;; sign tool that owns the key, per no-server-key.)
                  "publicKeyHex" pubkey-hex}])
      dk (assoc "assertionMethod" [(str did "#key-0")]))))
