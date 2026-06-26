;; etzhayyim.kotoba-rad — sovereign per-actor repo identity on the kotoba substrate.
;;
;; ADR-2606231200. Implements the Radicle-shaped identity model (RID / did:key /
;; sigref / identity commit-DAG) DIRECTLY on the existing kotoba primitives —
;; `etzhayyim.kotoba.{cid,datom,log}` — rather than running a separate
;; radicle-node. The actor's three identities are cross-linked:
;;
;;   B-web    did:web:etzhayyim.github.io:com-etzhayyim-<name>  (static did.json,
;;            GitHub Pages — no custom domain, no dynamic generation; ADR addendum
;;            2026-06-24. The AT handle <name>.etzhayyim.com is a SEPARATE id
;;            resolved by a DNS TXT _atproto record, needing no web host.)
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
  [actor genesis {:keys [sign-fn]}]
  (let [path (journal-path actor)
        existing (log/read-log path)
        rid* (rid genesis)
        already? (some (fn [dm] (and (= (d/d-e dm) rid*)
                                     (= (d/d-a dm) :rad/type)
                                     (= (d/d-v dm) :identity)))
                       existing)
        tx (inc (log/max-tx existing))
        id-dms (when-not already? (identity-datoms genesis tx))
        ;; head AFTER the identity datoms land, so the sigref attests them
        head (log/head-cid (into (vec existing) (vec id-dms)))
        {:keys [by sig]} (when sign-fn (sign-fn head))
        _ (when-not sign-fn
            (binding [*out* *err*]
              (println "WARN kotoba-rad: no :sign-fn — publishing UNSIGNED identity"
                       "(ok for pilot/--no-network; NOT for aozora registration)")))
        sig-dms (sigref-datom rid* head (or by (:rad/did-web genesis)) sig tx)
        all (into (vec id-dms) sig-dms)]
    (log/append! path all)
    {:rid rid* :rad-uri (str "rad:" rid*) :head head
     :datoms-appended (count all) :signed? (boolean sig)}))

(defn- genesis-rid-in
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

;; ── did:web did.json (github.io path form, static — cross-linked to rad+repo) ─
;; ADR-2606231200 addendum (2026-06-24): the actor did.json is a STATIC file at
;; the repo's Pages root (/.well-known/did.json), served by GitHub Pages over
;; github.io's own TLS. No custom domain, no CF Worker, no dynamic generation —
;; key rotation is a commit/PR, which is the no-server-key + self-evolution path.

(defn did-web-doc
  "W3C DID Document for did:web:etzhayyim.github.io:com-etzhayyim-<name>,
   cross-linking the sovereign rad: identity, the AT handle, and the GitHub
   mirror in alsoKnownAs. `pubkey-hex` (optional) adds an Ed25519
   verificationMethod. `data-graph` (optional, {:root :car :head}) adds a
   KotobaDataGraph service so resolving the DID locates the CID-queryable Pages
   data tier (ADR-2606242400). Served STATICALLY from the repo's Pages root."
  [{:keys [name did-web genesis pubkey-hex data-graph]}]
  (let [did (or did-web (str "did:web:etzhayyim.github.io:com-etzhayyim-" name))
        dk  (some-> pubkey-hex did-key)
        services (cond-> [{"id" (str did "#atproto_pds")
                           "type" "AtprotoPersonalDataServer"
                           "serviceEndpoint" "https://pds.etzhayyim.com"}
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
                             genesis (conj (rad-uri genesis)))
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
