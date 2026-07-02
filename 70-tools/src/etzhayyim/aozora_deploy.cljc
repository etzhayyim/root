;; etzhayyim.aozora-deploy — `bb aozora:deploy <name>` — write an actor's
;; profile record to the app-aozora PDS via com.atproto.repo.createRecord.
;;
;; Per-repo deploy: each com-etzhayyim-* repo has its own artificial-organism
;; identity (kotoba-rad genesis with :rad/aozora {:pds :collection}). This task
;; reads that genesis + the actor's manifest, builds the profile record body,
;; and writes it under the actor's OWN did:key session.
;;
;; Auth (proven live 2026-07-02, tashikame/kouhou PR #3 each; ADR-2607022300
;; identify facet): the CLI loads (or first-run generates) the actor's
;; self-sovereign Ed25519 did:key (etzhayyim.aozora-identity), mints a CACAO,
;; exchanges it at com.atproto.server.createSession for an HS256 session JWT,
;; then createRecord(Bearer JWT, repo = did:key) — the PDS enforces session
;; DID == repo DID. The aozora repo is keyed by the did:key; :rad/did-web is
;; the public handle. no-server-key: the key is the actor's own, held
;; off-platform (gitignored identity.edn), never a custodial platform key.
;; An optional member CACAO leash (LEASH env) is still forwarded for
;; attribution (the revocable off-switch, ADR-2606111400).
;;
;; clj/bb per the repo "Operational code = clj/bb" rule.
;; Idempotent: rkey=self → re-deploy overwrites the same profile record.

(ns etzhayyim.aozora-deploy
  (:require [clojure.string :as str]
            [clojure.java.io :as io]
            [clojure.edn :as edn]
            [cheshire.core :as json]
            [etzhayyim.actor-publish :as pub]
            [etzhayyim.aozora-identity :as aid]
            [etzhayyim.kotoba-rad :as rad]))

(def canonical-pds "https://pds.aozora.app")

(def legacy-pds-endpoints
  ;; https://aozora.app is the AppView/canonical handle domain — XRPC writes
  ;; live on pds.aozora.app (aozora.app serves the app HTML, no /xrpc).
  #{"https://aozora.app"
    "https://pds.etzhayyim.com"
    "https://atproto.etzhayyim.com"
    "https://etzhayyim.com"})

(defn canonicalize-pds [pds]
  (let [pds (or (not-empty pds) canonical-pds)]
    (if (contains? legacy-pds-endpoints pds)
      canonical-pds
      pds)))

(defn read-manifest
  "Read the actor manifest from either the monorepo (20-actors/<name>) or
   the published repo (../../etzhayyim/com-etzhayyim-<name>)."
  [actor]
  (let [candidates [(io/file (str "20-actors/" actor "/actor-manifest.jsonld"))
                    (io/file (str "20-actors/" actor "/manifest.jsonld"))
                    (io/file (str "20-actors/" actor "/manifest.edn"))
                    (io/file (str "../../etzhayyim/com-etzhayyim-" actor "/actor-manifest.jsonld"))
                    (io/file (str "../../etzhayyim/com-etzhayyim-" actor "/manifest.jsonld"))
                    (io/file (str "../../etzhayyim/com-etzhayyim-" actor "/manifest.edn"))]
        f (first (filter #(.exists ^java.io.File %) candidates))]
    (when f
      (if (str/ends-with? (.getName f) ".edn")
        (edn/read-string (slurp f))
        (json/parse-string (slurp f) true)))))

(defn read-genesis
  "Read the kotoba-rad genesis from the identity journal, or derive from manifest."
  [actor manifest]
  (pub/manifest->genesis actor manifest))

(defn profile-record-body
  "Build the atproto profile record body from the actor manifest + genesis.
   Mirrors the fields publish-actor-records.mjs materializes into profile.json."
  [actor manifest genesis]
  (let [display-name (or (:displayName manifest) (:label manifest)
                         (:actor/display-name manifest)
                         (-> manifest :description (str/split #" — ") first)
                         (-> manifest :actor/purpose (str/split #" — ") first)
                         actor)
        description (or (:description manifest) (:purpose manifest)
                        (:actor/purpose manifest) (:label manifest) "")
        lexicon (-> genesis :rad/aozora :collection)
        $type (str lexicon ".profile")]
    (cond-> {"$type" $type
             "displayName" display-name
             "description" description
             "createdAt" (.format (java.time.OffsetDateTime/now)
                                  (java.time.format.DateTimeFormatter/ISO_OFFSET_DATE_TIME))}
      (seq (:lexicons manifest)) (assoc "lexicons" (:lexicons manifest))
      (seq (:actor/lexicons manifest)) (assoc "lexicons" (:actor/lexicons manifest))
      (seq (:adr manifest)) (assoc "adr" (:adr manifest))
      (seq (:actor/adr manifest)) (assoc "adr" (:actor/adr manifest)))))

(defn deploy-one
  "Deploy a single actor's profile to app-aozora.
   Opts: :apply? (false=plan-only), :leash (member CACAO), :pds-override."
  [actor {:keys [apply? leash pds-override] :as opts}]
  (let [manifest (read-manifest actor)]
    (when-not manifest
      (throw (ex-info (str "no manifest for " actor) {:actor actor})))
    (let [genesis (read-genesis actor manifest)
          raw-pds (or pds-override
                      (System/getenv "AOZORA_PDS_URL")
                      (-> genesis :rad/aozora :pds)
                      canonical-pds)
          pds (canonicalize-pds raw-pds)
          coll (-> genesis :rad/aozora :collection)
          profile-coll (str coll ".profile")
          did-web (:rad/did-web genesis)
          record (profile-record-body actor manifest genesis)]
      (println (format "▶ aozora:deploy %s  (%s)" actor (if apply? "APPLY" "DRY-RUN")))
      (println (format "  PDS:     %s" pds))
      (when (not= raw-pds pds)
        (println (format "  note:    %s is not the XRPC write endpoint; using %s" raw-pds pds)))
      (println (format "  did:web: %s (public handle)" did-web))
      (println (format "  record:  %s rkey=self" profile-coll))
      (println (format "  body:    %s" (json/generate-string record)))
      (if-not apply?
        (let [id (aid/existing-identity actor)]
          (println (format "  did:key: %s"
                           (if id
                             (format "%s (identity: %s)" (:did id) (:path id))
                             "(none yet — --apply will generate + persist one)")))
          (println "  PLAN: createSession → createRecord (dry-run — pass --apply to execute)")
          {:actor actor :planned true :pds pds :did-web did-web
           :did-key (:did id) :collection profile-coll :record record})
        (let [id (aid/load-or-create-identity! actor)
              _ (println (format "  did:key: %s%s (identity: %s)"
                                 (:did id)
                                 (if (:created? id) " [NEW — first run]" "")
                                 (:path id)))
              sess (aid/create-session! pds id)
              res (aid/create-record!
                   pds (:jwt sess)
                   {:repo (:did id) :collection profile-coll :rkey "self"
                    :record (assoc record "actor" (:did id)) :leash leash})]
          (println (format "  result:  status=%s uri=%s cid=%s"
                           (:status res) (:uri res) (:cid res)))
          (if (= 200 (:status res))
            (do (println (format "✔ %s deployed" actor))
                {:actor actor :deployed true :pds pds :did-web did-web
                 :did-key (:did id) :collection profile-coll
                 :uri (:uri res) :cid (:cid res)})
            (do (println (format "✖ %s FAILED (status=%s body=%s)"
                                 actor (:status res) (:body res)))
                {:actor actor :failed true :status (:status res)
                 :collection profile-coll})))))))

(defn -main [& args]
  (let [flags (set (filter #(str/starts-with? % "--") args))
        opts {:apply? (contains? flags "--apply")
              :leash (System/getenv "LEASH")
              :pds-override (some->> args
                                     (filter #(str/starts-with? % "--pds="))
                                     first (drop 6) (apply str) not-empty)}
        actors (remove #(str/starts-with? % "--") args)]
    (when (empty? actors)
      (println "usage: bb aozora:deploy <name> [<name>...] [--apply] [--pds=<url>]")
      (println "  env: AOZORA_PDS_URL=<url> (default https://pds.aozora.app)")
      (println "       AOZORA_IDENTITY=<path> (override the actor identity.edn location)")
      (println "       LEASH=<member CACAO leash> (optional, attributes write to member)")
      (System/exit 2))
    (doseq [a actors]
      (deploy-one a opts))))
