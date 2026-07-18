;; etzhayyim.actor-publish — `bb actor:publish <name>` orchestrator.
;;
;; ADR-2606231200. Idempotent pipeline that takes one actor from
;; a flat west actor repository to a DID-bearing, aozora-registerable unit:
;;
;;   1. verify-repo  orgs/etzhayyim/com-etzhayyim-<name>
;;   2. gh-repo      ensure public github.com/etzhayyim/com-etzhayyim-<name>
;;   3. did-web      generate a STATIC /.well-known/did.json (+ .nojekyll),
;;                   served via the etzhayyim.com Worker as
;;                   did:web:etzhayyim.com:actor:<name> (ADR addendum
;;                   2026-07-02, superseding the 2026-06-24 github.io-only
;;                   addendum — GitHub Pages was never enabled for 171/175
;;                   actors in practice). An already-published actor's did-web
;;                   migrates via the RID-preserving `rad:update-did-web` task
;;                   (etzhayyim.kotoba-rad/update-did-web!), never by
;;                   recomputing genesis.
;;   4. kotoba-rad   mint RID + did:key, append sovereign identity to the log
;;   5. aozora       write the actor profile to the PDS (Option B e.write)
;;
;; DRY-RUN BY DEFAULT. Side-effecting steps (gh/git push/wrangler/pds write) run
;; ONLY with --apply; without it the step is planned + logged, nothing mutates.
;; no-server-key: this tool never holds a signing key — kotoba-rad signing and
;; the PDS write are member/operator-key legs, surfaced as planned commands.
;;
;; clj/bb per the repo "Operational code = clj/bb over the kotoba Datom log"
;; rule; shelling to system binaries (git/gh) via babashka.process is allowed.

(ns etzhayyim.actor-publish
  (:require [clojure.string :as str]
            [clojure.java.io :as io]
            [clojure.edn :as edn]
            [cheshire.core :as json]
            [babashka.process :as p]
            [etzhayyim.kotoba-rad :as rad]
            [etzhayyim.kotoba-rad-sign :as rad-sign]))

(def org "etzhayyim")
(def canonical-aozora-pds "https://aozora.app")
(defn repo-name [actor] (str "com-" org "-" actor))
(defn prefix [actor] (str "orgs/etzhayyim/" (repo-name actor)))

;; ── manifest ────────────────────────────────────────────────────────────────

(defn manifest-path
  "Locate the actor manifest. Utility/older actors use `actor-manifest.jsonld`;
   the clj-native flagship actors (kaname/tsumugi/ibuki…) use `manifest.jsonld`
   (no `triggers`, lexicons listed under `:lexicons`). Gen-3 kotoba-native
   actors may use `manifest.edn`. Prefer jsonld, fall back to edn."
  [actor]
  (let [a (io/file (str (prefix actor) "/actor-manifest.jsonld"))
        m (io/file (str (prefix actor) "/manifest.jsonld"))
        e (io/file (str (prefix actor) "/manifest.edn"))]
    (cond (.exists a) a (.exists m) m (.exists e) e :else a)))

(defn read-manifest [actor]
  (let [f (manifest-path actor)]
    (when (.exists f)
      (if (str/ends-with? (.getName f) ".edn")
        (edn/read-string (slurp f))
        (json/parse-string (slurp f) true)))))

(defn- lexicon-nsid
  "Normalize a declared lexicon entry to its bare NSID string. Most manifests
   list bare strings; some Gen-3 EDN manifests (ake/fuchi/himawari/kawaraban/
   tasuke) list rich maps {\"id\" nsid \"status\" … \"emittedBy\" […]} — pull
   the id/:id out of those instead of crashing str/split on a map."
  [entry]
  (cond
    (string? entry) entry
    (map? entry) (or (get entry "id") (:id entry))
    :else nil))

(defn default-did-web
  "The did:web an actor is minted with when it has NO existing published
   identity yet (did:web:etzhayyim.com:actor:<name>; ADR-2606231200 addendum
   2026-07-02, superseding the 2026-06-24 github.io-only addendum — GitHub
   Pages was never enabled for 171/175 actors in practice). Single source of
   truth for this template — `manifest->genesis` (new actors) and
   `step-did-web`'s migration path (existing actors) both call this, never
   duplicate the literal string."
  [actor]
  (str "did:web:etzhayyim.com:actor:" actor))

(defn manifest->genesis
  "Derive the kotoba-rad genesis block from the actor manifest. `did-web`
   defaults to `default-did-web` (a brand-new actor's genesis DID) but MUST be
   overridden to the actor's ORIGINAL recorded value when the actor already
   has a published identity (see `step-did-web`) — genesis is never
   recomputed with a different did:web for an already-published actor, since
   the RID is a content hash over the whole genesis block and that would mint
   a new RID.
   The collection NSID is the first declared collection/lexicon minus its final
   record-type segment: `actor-manifest.jsonld` lists it under
   :triggers/:subscribeRepos/:collections, `manifest.jsonld` under :lexicons."
  [actor manifest & {:keys [pubkey-hex did-web]}]
  (let [coll (or (-> manifest :triggers :subscribeRepos :collections first)
                 (lexicon-nsid (-> manifest :lexicons first))
                 (lexicon-nsid (-> manifest :actor/lexicons first))
                 (lexicon-nsid (:actor/primary-lexicon manifest)))
        ns* (when coll (str/join "." (butlast (str/split coll #"\."))))]
    (rad/genesis-block
     {:name actor
      :did-web (or did-web (default-did-web actor))
      :delegates (when pubkey-hex [(rad/did-key pubkey-hex)])
      :threshold 1
      :repo (str "github.com/" org "/" (repo-name actor))
      :pds canonical-aozora-pds
      :collection (or ns* (str "com.etzhayyim.apps." actor))})))

(defn manifest->holds
  "Read the actor's declared datasets from the manifest's :substrate :datasets
   block (ADR-2607010001 §D2) into the holding-map shape `rad/add-holding!` and
   `rad/publish-identity!`'s :holds consume. `:layer` is coerced to a keyword
   (manifests are JSON-LD where it lands as a string; EDN manifests already use
   a keyword). Returns [] when no datasets are declared."
  [manifest]
  (mapv (fn [d] (update d :layer #(if (string? %) (keyword %) %)))
        (or (-> manifest :substrate :datasets) [])))

;; ── step helpers (dry-run aware) ────────────────────────────────────────────

(defn- sh [apply? & args]
  (let [cmd (vec args)]
    (if apply?
      (let [{:keys [exit out err]} (apply p/sh cmd)]
        {:cmd cmd :exit exit :out (str/trim (str out)) :err (str/trim (str err))})
      {:cmd cmd :planned true})))

(defn- log-step [n title m]
  (println (format "  [%d] %s" n title))
  (println "      " (if (:planned m)
                      (str "PLAN: " (str/join " " (:cmd m)))
                      (str "exit=" (:exit m)
                           (when (seq (:out m)) (str " | " (:out m)))
                           (when (seq (:err m)) (str " | err: " (:err m))))))
  m)

;; ── steps ───────────────────────────────────────────────────────────────────

(defn step-josh-split
  "Compatibility name for step 1: verify the independent flat west checkout.
   Numbered-root subtree extraction is retired after the 198/198 drain."
  [actor apply?]
  (let [dir (prefix actor)]
    (if (.exists (io/file dir ".git"))
      (log-step 1 (str "flat west repo present " dir) {:exit 0 :out dir})
      (throw (ex-info (str "flat west actor repository is not checked out: " dir)
                      {:actor actor :path dir :apply? apply?})))))

(defn step-gh-repo [actor apply?]
  (let [r (repo-name actor)
        exists (sh apply? "gh" "repo" "view" (str org "/" r))]
    (if (and apply? (zero? (:exit exists)))
      (log-step 2 (str "gh repo exists " r) exists)
      (log-step 2 (str "gh repo create " r " (public)")
                (sh apply? "gh" "repo" "create" (str org "/" r)
                    "--public" "--description"
                    (str "etzhayyim actor: " actor " (aozora.app)"))))))

(defn step-did-web [actor manifest apply? pubkey-hex]
  (let [status (rad/identity-status actor)
        ;; EXISTING actor: genesis MUST be reconstructed with its ORIGINAL
        ;; recorded did-web (never the fresh default) — the RID is a content
        ;; hash over the whole genesis block, so any other value here would
        ;; mint a new RID and corrupt the journal (two :rad/type :identity
        ;; entities). The served doc still uses the CURRENT did-web (which
        ;; may differ, post update-did-web!) via `:did-web`/`:rid-str` below,
        ;; decoupled from genesis entirely.
        genesis (manifest->genesis actor manifest :pubkey-hex pubkey-hex
                                    :did-web (:genesis-did-web status))
        current-did (or (:current-did-web status) (:rad/did-web genesis))
        legacy-did (when (and status (not= current-did (:genesis-did-web status)))
                     (:genesis-did-web status))
        doc (if status
              (rad/did-web-doc {:name actor :did-web current-did
                                :rid-str (:rid status) :legacy-did-web legacy-did
                                :pubkey-hex pubkey-hex})
              ;; NEW actor: pass the genesis did:web through so the doc `id`
              ;; == the genesis DID (single source of truth — never re-derive
              ;; a divergent string).
              (rad/did-web-doc {:name actor :did-web (:rad/did-web genesis)
                                :genesis genesis :pubkey-hex pubkey-hex}))
        out (str (prefix actor) "/.well-known/did.json")
        ;; .nojekyll: GitHub Pages' Jekyll ignores dot-prefixed paths, so without
        ;; this the static /.well-known/did.json (and the actor's *.wasm) are not
        ;; served. The bytes are served raw — exactly what did:web + wasm need.
        nojekyll (str (prefix actor) "/.nojekyll")]
    (when apply?
      (io/make-parents (io/file out))
      (spit out (str (json/generate-string doc {:pretty true}) "\n"))
      (spit nojekyll ""))
    (log-step 3 (str "static did:web doc -> " out " (+ .nojekyll)")
              {:planned (not apply?) :cmd ["write" out (str (count (str doc)) "B")
                                           "+" nojekyll]})
    {:genesis genesis :did-doc-path out :nojekyll-path nojekyll :did current-did
     :existing-rid (:rid status)}))

(defn step-kotoba-rad [actor genesis apply? pubkey-hex holds existing-rid]
  ;; no-server-key: a signer is built ONLY if the member's key is in Keychain
  ;; (and the pubkey is known); otherwise publish unsigned (pilot/--no-network).
  ;; `holds` (from manifest->holds) rides the genesis tx on first publish — the
  ;; genesis block is untouched, so the RID stays stable (ADR-2607010001).
  (if existing-rid
    ;; EXISTING actor: identity already published — do NOT recompute/rehash
    ;; genesis. `rad/rid` hashes pr-str of a NESTED map (docstring only
    ;; promises determinism for flat [e a v tx op] datom vectors); a
    ;; reconstructed genesis with byte-identical field VALUES can still hash
    ;; to a DIFFERENT RID than the one originally recorded (confirmed
    ;; empirically 2026-07-02 against a real journal). Recomputing here and
    ;; feeding it to publish-identity! would make its `already?` check miss
    ;; and append a corrupting SECOND :rad/type :identity entity. The
    ;; already-recorded RID (from rad/identity-status, read straight off the
    ;; journal's own entity id — no hashing) is used as-is; re-publishing
    ;; identity for an existing actor is not this step's job (see
    ;; rad:update-did-web for the RID-preserving did-web migration path).
    (do (log-step 4 (str "kotoba-rad RID " existing-rid " (already published — not re-minted)")
                  {:exit 0 :out "skipped: existing identity, publish-identity! not called"})
        {:rid existing-rid :rad-uri (str "rad:" existing-rid)})
    (let [sign-fn (when (and pubkey-hex apply?)
                    (rad-sign/sign-fn-for-actor actor pubkey-hex))
          res (when apply? (rad/publish-identity! actor genesis
                                                  {:sign-fn sign-fn :holds holds}))]
      (log-step 4 (str "kotoba-rad RID " (rad/rid genesis)
                       (cond apply? "" pubkey-hex " (will sign if key in Keychain)"
                             :else " (unsigned: no --pubkey)"))
                (if res
                  {:exit 0 :out (str (:rad-uri res) " head=" (:head res)
                                     " signed=" (:signed? res))}
                  {:planned true :cmd ["kotoba-rad/publish-identity!" actor
                                       (rad/rad-uri genesis)
                                       (if pubkey-hex "sign-if-keychain" "unsigned")]}))
      (assoc (or res {}) :rid (rad/rid genesis) :rad-uri (rad/rad-uri genesis)))))

(defn step-aozora
  "Deploy the actor profile to the aozora PDS via createRecord.
   When --apply is set and LEASH env is present, executes the PDS write via
   etzhayyim.pds.client/create-record!. Otherwise plans only (dry-run)."
  [actor genesis apply?]
  (let [coll (-> genesis :rad/aozora :collection)
        profile-coll (str coll ".profile")
        pds (-> genesis :rad/aozora :pds)
        did (:rad/did-web genesis)]
    (if apply?
      (let [deploy-ns (do (require '[etzhayyim.aozora-deploy])
                          (find-ns 'etzhayyim.aozora-deploy))
            deploy-fn (ns-resolve deploy-ns 'deploy-one)
            res (deploy-fn actor {:apply? true
                                  :leash (System/getenv "LEASH")
                                  :pds-override pds})]
        (log-step 5 (str "aozora PDS profile write " profile-coll)
                  (if (:deployed res)
                    {:exit 0 :out (str "uri=" (:uri res) " cid=" (:cid res))}
                    {:exit 1 :err (str "status=" (:status res) " FAILED")}))
        res)
      (do
        (log-step 5 (str "aozora PDS profile write " profile-coll)
                  {:planned true
                   :cmd ["bb" "aozora:deploy" actor "--apply"
                         (str "pds=" pds)
                         (str "did=" did)
                         "rkey=self" "<- member/operator key (no-server-key)"]})
        {:collection profile-coll}))))

;; ── driver ──────────────────────────────────────────────────────────────────

(defn publish-one [actor {:keys [apply? pubkey-hex]}]
  (let [manifest (read-manifest actor)]
    (when-not manifest
      (throw (ex-info (str "no actor-manifest.jsonld for " actor) {:actor actor})))
    (println (format "▶ actor:publish %s  (%s)"
                     actor (if apply? "APPLY" "DRY-RUN")))
    (step-josh-split actor apply?)
    (step-gh-repo actor apply?)
    (let [{:keys [genesis did existing-rid]} (step-did-web actor manifest apply? pubkey-hex)
          holds (manifest->holds manifest)
          rad-res (step-kotoba-rad actor genesis apply? pubkey-hex holds existing-rid)
          aoz (step-aozora actor genesis apply?)]
      (println (format "✔ %s  rad=%s  repo=%s  did=%s\n"
                       actor (:rad-uri rad-res) (repo-name actor) did))
      {:actor actor :rid (:rid rad-res) :rad-uri (:rad-uri rad-res)
       :repo (repo-name actor) :did did
       :aozora-collection (:collection aoz)})))

(defn -add-holding
  "Append a :rad/holds-dataset attestation for each dataset in the actor's
   manifest :substrate :datasets to its EXISTING kotoba-rad identity journal
   (ADR-2607010001). RID-stable, append-only, idempotent by dataset-id
   (rad/add-holding!). DRY-RUN by default; --apply writes the journal. If a
   member key for the actor is in Keychain the new sigref is member-signed;
   otherwise unsigned (no-server-key). Args: <name> [--apply]"
  [& args]
  (let [flags (set (filter #(str/starts-with? % "--") args))
        apply? (contains? flags "--apply")
        actor (first (remove #(str/starts-with? % "--") args))]
    (when-not actor
      (println "usage: bb rad:add-holding <name> [--apply]")
      (System/exit 2))
    (let [manifest (read-manifest actor)]
      (when-not manifest
        (println "error: no manifest for" actor)
        (System/exit 2))
      (let [holds (manifest->holds manifest)
            sign-fn (when apply? (rad-sign/sign-fn-for-actor actor))]
        (println (format "▶ rad:add-holding %s  (%s; %d dataset/s)"
                         actor (if apply? "APPLY" "DRY-RUN") (count holds)))
        (when (and apply? (not sign-fn))
          (println "WARN  no member key in Keychain for" actor
                   "— holding sigrefs will be UNSIGNED"))
        (if (empty? holds)
          (println "  (no :substrate :datasets declared — nothing to hold)")
          (doseq [h holds]
            (if apply?
              (let [res (rad/add-holding! actor h {:sign-fn sign-fn})]
                (println (format "  ✓ %s  added? %s  signed? %s  head %s"
                                 (:dataset-id res) (:added? res)
                                 (:signed? res) (:head res))))
              (println (format "  PLAN add-holding %s  (layer %s, cid %s) — pass --apply to write"
                               (:dataset-id h) (:layer h) (:cidv1 h))))))))))

(defn -update-did-web
  "Migrate an EXISTING actor's did:web to `default-did-web` (or an explicit
   `--did-web=` override) by APPENDING to its kotoba-rad journal
   (rad/update-did-web!, ADR-2606231200 addendum 2026-07-02) — the genesis
   block is left untouched, so the **RID is stable**. Regenerates the STAGING
   `.well-known/did.json` in the flat actor repository. Unlike
   `actor:publish`, this does not create a repository or run aozora deployment;
   it is narrowly scoped to the identity update.
   DRY-RUN by default; --apply writes the journal + file. If a member key for
   the actor is in Keychain the new sigref is member-signed; otherwise
   unsigned (no-server-key). Args: <name> [--apply] [--did-web=<value>]"
  [& args]
  (let [flags (set (filter #(str/starts-with? % "--") args))
        apply? (contains? flags "--apply")
        did-web-override (some->> args (filter #(str/starts-with? % "--did-web=")) first
                                   (drop 10) (apply str) not-empty)
        actor (first (remove #(str/starts-with? % "--") args))]
    (when-not actor
      (println "usage: bb rad:update-did-web <name> [--apply] [--did-web=<value>]")
      (System/exit 2))
    (let [status (rad/identity-status actor)]
      (when-not status
        (println "error: no published kotoba-rad identity for" actor
                 "— run actor:publish first")
        (System/exit 2))
      (let [target (or did-web-override (default-did-web actor))
            sign-fn (when apply? (rad-sign/sign-fn-for-actor actor))]
        (println (format "▶ rad:update-did-web %s  (%s)  %s -> %s"
                         actor (if apply? "APPLY" "DRY-RUN")
                         (:current-did-web status) target))
        (when (and apply? (not sign-fn))
          (println "WARN  no member key in Keychain for" actor
                   "— did-web sigref will be UNSIGNED"))
        (if apply?
          (let [res (rad/update-did-web! actor target {:sign-fn sign-fn})
                doc (rad/did-web-doc {:name actor :did-web target
                                      :rid-str (:rid status)
                                      :legacy-did-web (:genesis-did-web status)})
                out (str (prefix actor) "/.well-known/did.json")]
            (io/make-parents (io/file out))
            (spit out (str (json/generate-string doc {:pretty true}) "\n"))
            (println (format "  ✓ added? %s  signed? %s  head %s  -> %s"
                             (:added? res) (:signed? res) (:head res) out)))
          (println (format "  PLAN update-did-web %s -> %s — pass --apply to write"
                           actor target)))))))

(defn -main [& args]
  (let [flags (set (filter #(str/starts-with? % "--") args))
        opts {:apply? (contains? flags "--apply")
              :pubkey-hex (some->> args (filter #(str/starts-with? % "--pubkey=")) first
                                   (drop 9) (apply str) not-empty)}
        actors (remove #(str/starts-with? % "--") args)]
    (when (empty? actors)
      (println "usage: bb actor:publish <name> [<name>...] [--apply] [--pubkey=<hex>]")
      (System/exit 2))
    (doseq [a actors] (publish-one a opts))))
