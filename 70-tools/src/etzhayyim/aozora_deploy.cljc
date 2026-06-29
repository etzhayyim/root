;; etzhayyim.aozora-deploy — `bb aozora:deploy <name>` — write an actor's
;; profile record to the app-aozora PDS via com.atproto.repo.createRecord.
;;
;; Per-repo deploy: each com-etzhayyim-* repo has its own artificial-organism
;; identity (kotoba-rad genesis with :rad/aozora {:pds :collection}). This task
;; reads that genesis + the actor's manifest, builds the profile record body,
;; and calls etzhayyim.pds.client/create-record! against app-aozora.
;;
;; no-server-key: app-aozora holds no custodial key. The deploy presents a
;; member CACAO leash (LEASH env) so the write is attributed to a consenting
;; member; absent → unattributed (fail-open, back-compat). The actor's own
;; sealed key (PDS-side actorkeys registry) signs the commit — never this tool.
;;
;; clj/bb per the repo "Operational code = clj/bb" rule.
;; Idempotent: rkey=self → re-deploy overwrites the same profile record.

(ns etzhayyim.aozora-deploy
  (:require [clojure.string :as str]
            [clojure.java.io :as io]
            [clojure.edn :as edn]
            [cheshire.core :as json]
            [etzhayyim.actor-publish :as pub]
            [etzhayyim.kotoba-rad :as rad]))

(def canonical-pds "https://aozora.app")

(def legacy-pds-endpoints
  #{"https://pds.etzhayyim.com"
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
          did (:rad/did-web genesis)
          record (profile-record-body actor manifest genesis)]
      (println (format "▶ aozora:deploy %s  (%s)" actor (if apply? "APPLY" "DRY-RUN")))
      (println (format "  PDS:     %s" pds))
      (when (not= raw-pds pds)
        (println (format "  note:    legacy PDS %s is deprecated; using app-aozora canonical endpoint" raw-pds)))
      (println (format "  DID:     %s" did))
      (println (format "  record:  %s rkey=self" profile-coll))
      (println (format "  body:    %s" (json/generate-string record)))
      (if-not apply?
        (do
          (println "  PLAN: createRecord (dry-run — pass --apply to execute)")
          {:actor actor :planned true :pds pds :did did
           :collection profile-coll :record record})
        (do
          (require '[etzhayyim.pds.client :as client])
          (let [client-ns (find-ns 'etzhayyim.pds.client)
                create-fn (ns-resolve client-ns 'create-record!)
                res (create-fn
                     pds {:repo did :collection profile-coll :record record
                          :rkey "self" :leash leash})]
            (println (format "  result:  status=%s uri=%s cid=%s signedBy=%s author=%s"
                             (:status res) (:uri res) (:cid res)
                             (:signedBy res) (:author res)))
            (if (= 200 (:status res))
              (do (println (format "✔ %s deployed" actor))
                  {:actor actor :deployed true :pds pds :did did
                   :collection profile-coll :uri (:uri res) :cid (:cid res)
                   :signedBy (:signedBy res) :author (:author res)})
              (do (println (format "✖ %s FAILED (status=%s)" actor (:status res)))
                  {:actor actor :failed true :status (:status res)
                   :collection profile-coll}))))))))

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
      (println "  env: AOZORA_PDS_URL=<url> (default https://aozora.app)")
      (println "       LEASH=<member CACAO leash> (optional, attributes write to member)")
      (System/exit 2))
    (doseq [a actors]
      (deploy-one a opts))))
