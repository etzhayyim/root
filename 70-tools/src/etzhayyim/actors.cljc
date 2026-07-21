;; etzhayyim.actors — Actor lifecycle commands (Clojure/bb port of actors.py).
;;
;; IO-REWRITE of 70-tools/etzhayyim-py/src/etzhayyim/actors.py
;; The .py is KEPT (additive port — both co-exist).
;;
;; PURE-vs-IO split:
;;   PURE (parity-verifiable, unit-tested offline):
;;     build-prompt           — build the LLM domain-knowledge prompt for an actor
;;     parse-result           — extract ShinkaResult from raw LLM text (JSON extraction)
;;     sanitize-path          — URL-safe slug from a string
;;     stable-rkey            — SHA-256-based 16-char rkey
;;     score-jokyo            — compute score + grade for a jokyo actor result map
;;
;;   IO (request-shaping verified via injectable HTTP fn / proc fn, not live calls):
;;     build-actor-list-request       — shape for com.etzhayyim.actor.list POST
;;     build-apply-writes-request     — shape for com.atproto.repo.applyWrites POST
;;     build-ollama-generate-request  — shape for Ollama /api/generate POST
;;     build-murakumo-generate-request — shape for Murakumo OpenAI-compat POST
;;     build-health-request           — shape for actor /{nanoid}.etzhayyim.com/health GET
;;     build-heartbeat-request        — shape for actor /_heartbeat POST
;;     build-migrate-request          — shape for com.etzhayyim.plc.migrateActor POST
;;     fetch-actors (paginating)      — IO: fetch actor list from PDS
;;     write-result                   — IO: write ShinkaResult to PDS
;;     check-health                   — IO: health + heartbeat check per actor
;;
;; INJECTABLE HTTP CLIENT:
;;   Every IO fn that makes network calls accepts an optional :http-fn in opts.
;;   Default = real babashka.http-client; tests inject a fake that records calls
;;   WITHOUT touching the network.
;;
;; bb load check:
;;   bb --classpath 70-tools/src -e "(require 'etzhayyim.actors)(println :ok)"

(ns etzhayyim.actors
  (:require [clojure.string :as str]
            [cheshire.core  :as json]
            #?(:bb [babashka.http-client :as http])))

;; ---------------------------------------------------------------------------
;; Constants (no env reads at load time)
;; ---------------------------------------------------------------------------

(def ^:private default-ollama-base  "http://127.0.0.1:11434")
(def ^:private default-model        "gemma3:4b")
(def ^:private default-murakumo-url "https://murakumo.etzhayyim.com")

(def ^:private re-json-block #"\{[\s\S]+\}")

(def ^:private valid-relations
  #{"EXPERTISE_IN" "DEPENDS_ON" "PRODUCES" "CONSUMES"
    "REGULATES" "SERVES" "MONITORS" "ANALYZES"})

;; ---------------------------------------------------------------------------
;; Pure: sanitize-path
;; ---------------------------------------------------------------------------

(defn sanitize-path
  "Convert a string to a URL-safe slug (lowercase, hyphens for spaces,
  only alnum + hyphen).
  Mirrors Python _sanitize_path()."
  [path]
  (let [lower (str/lower-case (str path))
        hyphenated (str/replace lower " " "-")]
    (apply str (filter (fn [c] (or (Character/isLetterOrDigit c) (= c \-))) hyphenated))))

;; ---------------------------------------------------------------------------
;; Pure: stable-rkey
;; ---------------------------------------------------------------------------

(defn stable-rkey
  "SHA-256 of key (UTF-8), hex-encoded, first 16 characters.
  Mirrors Python _stable_rkey()."
  [key]
  (let [md  (java.security.MessageDigest/getInstance "SHA-256")
        _   (.update md (.getBytes (str key) "UTF-8"))
        hex (apply str (map #(format "%02x" (bit-and % 0xff))
                            (seq (.digest md))))]
    (subs hex 0 16)))

;; ---------------------------------------------------------------------------
;; Pure: build-prompt
;; ---------------------------------------------------------------------------

(defn build-prompt
  "Build the LLM domain-knowledge prompt string for an actor.
  actor is a map with keys :nanoid :handle :display-name :description.
  Mirrors Python _build_prompt()."
  [{:keys [nanoid handle display-name description]}]
  (let [parts (cond-> [(str "nanoid=" (pr-str nanoid))
                       (str "handle=" (pr-str (or handle "")))]
                (seq display-name) (conj (str "displayName=" (pr-str display-name)))
                (seq description)  (conj (str "description=" (pr-str description))))
        ctx   (str/join ", " parts)]
    (str "You are a domain knowledge architect for an AI agent platform called etzhayyim.com.\n"
         "Given an AI agent's identity metadata, generate structured domain knowledge as JSON.\n\n"
         "Actor metadata: " ctx "\n\n"
         "Output a JSON object with exactly these keys:\n"
         "- \"domain_summary\": 2-3 sentences describing this agent's domain, purpose, and key capabilities\n"
         "- \"sub_dids\": array of 3-5 sub-entities this agent manages, each with \"path\" (URL-safe slug), \"display_name\", \"description\"\n"
         "- \"knowledge_edges\": array of 5-8 edges, each with \"from\": \"" nanoid "\", \"relation\", \"to\" (specific concept)\n\n"
         "Relations available: EXPERTISE_IN, DEPENDS_ON, PRODUCES, CONSUMES, REGULATES, SERVES, MONITORS, ANALYZES\n\n"
         "Output ONLY valid JSON:")))

;; ---------------------------------------------------------------------------
;; Pure: parse-result
;; ---------------------------------------------------------------------------

(defn parse-result
  "Parse LLM text response into a structured result map.
  Returns {:did :nanoid :domain-summary :sub-dids :knowledge-edges :error}.
  Mirrors Python _parse_result()."
  [{:keys [did nanoid] :as _actor} llm-text]
  (let [m (re-find re-json-block (str llm-text))]
    (if-not m
      {:did did :nanoid nanoid
       :domain-summary "" :sub-dids [] :knowledge-edges []
       :error "no JSON in LLM response"}
      (try
        (let [parsed (json/parse-string m true)
              sub-dids (for [s (get parsed :sub_dids [])
                             :let [path (sanitize-path (get s :path ""))]
                             :when (seq path)]
                         {:path         path
                          :display-name (get s :display_name "")
                          :description  (get s :description "")})
              edges    (for [e (get parsed :knowledge_edges [])
                             :when (and (seq (get e :relation ""))
                                        (seq (get e :to "")))]
                         {:from     (or (get e :from) nanoid)
                          :relation (get e :relation "")
                          :to       (get e :to "")})]
          {:did            did
           :nanoid         nanoid
           :domain-summary (get parsed :domain_summary "")
           :sub-dids       (vec sub-dids)
           :knowledge-edges (vec edges)
           :error          ""})
        (catch Exception e
          {:did did :nanoid nanoid
           :domain-summary "" :sub-dids [] :knowledge-edges []
           :error (str "JSON parse: " (ex-message e))})))))

;; ---------------------------------------------------------------------------
;; Pure: score-jokyo
;; ---------------------------------------------------------------------------

(defn score-jokyo
  "Compute numeric score (0-100) and grade for a jokyo result map.
  result must have :health-ok, :heartbeat-ok, :health-ms, :heartbeat-ms.
  Mirrors Python analyze() scoring in actors.py."
  [{:keys [health-ok heartbeat-ok health-ms heartbeat-ms]}]
  (let [score (cond-> 0
                health-ok       (+ 40)
                heartbeat-ok    (+ 40)
                (< health-ms 200)     (+ 10)
                (< heartbeat-ms 500)  (+ 10))
        grade (cond
                (>= score 90) "S"
                (>= score 70) "A"
                (>= score 50) "B"
                (>= score 30) "C"
                :else         "D")]
    {:total-score score :grade grade}))

;; ---------------------------------------------------------------------------
;; Pure: build apply-writes bodies
;; ---------------------------------------------------------------------------

(defn build-apply-writes-body
  "Build the body map for com.atproto.repo.applyWrites given a ShinkaResult.
  now is an ISO-8601 string.
  Returns {:repo :writes} for passing to applyWrites.
  Mirrors the write construction in Python _write_result()."
  [{:keys [did nanoid display-name domain-summary sub-dids knowledge-edges]} now]
  (let [writes (atom [])]
    ;; domain summary → actor.app record
    (when (seq domain-summary)
      (swap! writes conj
             {"action"     "update"
              "collection" "com.etzhayyim.actor.app"
              "rkey"       nanoid
              "value"      {"nanoid"      nanoid
                            "did"         did
                            "displayName" (or display-name "")
                            "description" domain-summary}}))
    ;; sub-dids
    (doseq [{:keys [path display-name description]} sub-dids
            :when (seq path)]
      (swap! writes conj
             {"action"     "update"
              "collection" "com.etzhayyim.identity.did"
              "rkey"       (stable-rkey (str "did:" path))
              "value"      {"id"          (str did ":" path)
                            "display_name" (or display-name "")
                            "description"  (or description "")
                            "status"       "active"
                            "controller"   did
                            "actorDid"     did
                            "sourceType"   "shinka"
                            "sourceId"     (str "shinka:" nanoid)
                            "created_at"   now}}))
    ;; knowledge edges
    (doseq [{:keys [from relation to]} knowledge-edges]
      (let [key (str from ":" relation ":" to)]
        (swap! writes conj
               {"action"     "update"
                "collection" "com.etzhayyim.actor.knowledgeEdge"
                "rkey"       (stable-rkey key)
                "value"      {"from"      from
                              "relation"  relation
                              "to"        to
                              "createdAt" now}})))
    {:repo   did
     :writes @writes}))

;; ---------------------------------------------------------------------------
;; IO request-shaping: all return {:method :url :headers :body?}
;; ---------------------------------------------------------------------------

(defn build-actor-list-request
  "Build the HTTP request map for com.etzhayyim.actor.list.
  opts: :token :cursor :batch-limit
  Mirrors Python _fetch_actors() request construction."
  [pds-url {:keys [token cursor batch-limit]
             :or   {batch-limit 50}}]
  (let [hdrs (cond-> {"Content-Type" "application/json"}
               (seq token) (assoc "Authorization" (str "Bearer " token)))
        body (cond-> {"status" "active" "batchLimit" batch-limit}
               (seq cursor) (assoc "cursor" cursor))]
    {:method  :post
     :url     (str pds-url "/xrpc/com.etzhayyim.actor.list")
     :headers hdrs
     :body    body}))

(defn build-apply-writes-request
  "Build the HTTP request map for com.atproto.repo.applyWrites.
  writes-body is the map from build-apply-writes-body.
  Mirrors Python _write_result() request construction."
  [pds-url token writes-body]
  {:method  :post
   :url     (str pds-url "/xrpc/com.atproto.repo.applyWrites")
   :headers {"Content-Type"  "application/json"
             "Authorization" (str "Bearer " token)}
   :body    writes-body})

(defn build-ollama-generate-request
  "Build the HTTP request map for Ollama /api/generate.
  Mirrors Python _ollama_generate() request construction."
  [ollama-base model prompt]
  {:method  :post
   :url     (str (or ollama-base default-ollama-base) "/api/generate")
   :headers {"Content-Type" "application/json"}
   :body    {"model"   model
             "prompt"  prompt
             "stream"  false
             "format"  "json"
             "options" {"temperature" 0.3 "num_predict" 2048}}})

(defn build-murakumo-generate-request
  "Build the HTTP request map for Murakumo OpenAI-compat /api/openai/v1/chat/completions.
  Mirrors Python _murakumo_generate() request construction."
  [murakumo-url api-key model prompt]
  (let [base-url (or murakumo-url default-murakumo-url)]
    {:method  :post
     :url     (str base-url "/api/openai/v1/chat/completions")
     :headers (cond-> {"Content-Type" "application/json"}
                (seq api-key) (assoc "Authorization" (str "Bearer " api-key)))
     :body    {"model"       model
               "messages"    [{"role"    "system"
                                "content" "You are a domain knowledge architect. Always respond with valid JSON only. No markdown fences, no explanations, no preamble — just the JSON object."}
                               {"role"    "user"
                                "content" prompt}]
               "temperature"     0.3
               "max_tokens"      8192
               "response_format" {"type" "json_object"}}}))

(defn build-health-request
  "Build the HTTP request map for actor /health GET.
  Mirrors Python analyze() health-check."
  [nanoid]
  {:method  :get
   :url     (str "https://" nanoid ".etzhayyim.com/health")
   :headers {}})

(defn build-heartbeat-request
  "Build the HTTP request map for actor /_heartbeat POST.
  Mirrors Python analyze() heartbeat."
  [nanoid token]
  {:method  :post
   :url     (str "https://" nanoid ".etzhayyim.com/_heartbeat")
   :headers (cond-> {"Content-Type" "application/json"}
              (seq token) (assoc "Authorization" (str "Bearer " token)))
   :body    {"feed" "[]" "engagement" "{}"}})

(defn build-migrate-request
  "Build the HTTP request map for com.etzhayyim.plc.migrateActor.
  Mirrors Python actors_migrate_to_plc() request construction."
  [pds-url actor handle token dry-run?]
  {:method  :post
   :url     (str pds-url "/xrpc/com.etzhayyim.plc.migrateActor")
   :headers {"Content-Type"  "application/json"
             "Authorization" (str "Bearer " token)}
   :body    {"actor"  actor
             "handle" handle
             "dryRun" dry-run?}})

;; ---------------------------------------------------------------------------
;; IO default-http-fn
;; ---------------------------------------------------------------------------

(defn- default-http-fn
  "Real babashka.http-client dispatch."
  [{:keys [method url headers body]}]
  #?(:bb
     (let [opts (cond-> {:headers (or headers {}) :timeout 30000}
                  body (assoc :body (json/generate-string body)))
           resp (case method
                  :get    (http/get    url opts)
                  :post   (http/post   url opts)
                  :patch  (http/patch  url opts)
                  :delete (http/delete url opts))]
       {:status (:status resp) :body (:body resp)})
     :default
     (throw (ex-info "babashka.http-client only available under bb"
                     {:method method :url url}))))

;; ---------------------------------------------------------------------------
;; IO: fetch-actors (paginates)
;; ---------------------------------------------------------------------------

(defn fetch-actors
  "Fetch actors from PDS via com.etzhayyim.actor.list, paginating until limit.
  Returns a vector of actor maps with :did :nanoid :handle :display-name
  :description :project-id.
  Mirrors Python _fetch_actors()."
  [pds-url limit {:keys [token http-fn]
                   :or   {http-fn default-http-fn}}]
  (loop [actors [] cursor ""]
    (if (>= (count actors) limit)
      (vec (take limit actors))
      (let [req  (build-actor-list-request pds-url {:token token :cursor cursor :batch-limit 50})
            resp (http-fn req)]
        (if (>= (:status resp) 400)
          actors ;; stop on error
          (let [data  (json/parse-string (:body resp) true)
                batch (get data :actors [])
                new-actors (concat actors
                                   (map (fn [a]
                                          {:did          (get a :did "")
                                           :nanoid       (get a :nanoid "")
                                           :handle       (get a :handle "")
                                           :display-name (get a :displayName "")
                                           :description  (get a :description "")
                                           :project-id   (get a :projectId "")})
                                        batch))
                new-cursor (get data :cursor "")]
            (if (or (empty? batch) (empty? new-cursor) (< (count batch) 50))
              (vec (take limit new-actors))
              (recur (vec new-actors) new-cursor))))))))

;; ---------------------------------------------------------------------------
;; IO: write-result (batches writes in groups of 50)
;; ---------------------------------------------------------------------------

(defn write-result
  "Write a ShinkaResult to PDS via com.atproto.repo.applyWrites.
  Mirrors Python _write_result()."
  [pds-url actor result now {:keys [token http-fn]
                              :or   {http-fn default-http-fn}}]
  (let [body    (build-apply-writes-body (merge actor result) now)
        all-w   (:writes body)
        repo    (:repo body)]
    (doseq [batch (partition-all 50 all-w)]
      (let [req  (build-apply-writes-request pds-url token {:repo repo :writes (vec batch)})
            resp (http-fn req)]
        (when (>= (:status resp) 400)
          (println (str "[shinka] applyWrites → " (:status resp) ": "
                        (subs (or (:body resp) "") 0 (min 200 (count (or (:body resp) "")))))))))))

;; ---------------------------------------------------------------------------
;; IO: migrate-to-plc (offline mock mode + live)
;; ---------------------------------------------------------------------------

(defn migrate-to-plc
  "Migrate an actor's did:web → did:plc.
  opts: :offline? :dry-run? :token :http-fn
  Returns the response data map.
  Mirrors Python actors_migrate_to_plc()."
  [pds-url actor handle {:keys [offline? dry-run? token http-fn]
                          :or   {dry-run? true http-fn default-http-fn}}]
  (let [resolved-handle (if (seq handle) handle (str actor ".etzhayyim.com"))]
    (if offline?
      (let [mock-did (str "did:plc:" (subs (str actor "aaaaaaaaaaaaaaaaaaaaa") 0 19))]
        {:did          mock-did
         :genesisCid   "bafysimulated000000000000000000000000000"
         :plcUrl       (str "https://plc.etzhayyim.com/" mock-did)
         :handle       resolved-handle
         :legacyDid    (str "did:web:" resolved-handle)})
      (let [req  (build-migrate-request pds-url actor resolved-handle token dry-run?)
            resp (http-fn req)]
        (when (>= (:status resp) 400)
          (throw (ex-info (str "XRPC error: " (:status resp))
                          {:status (:status resp) :body (:body resp)})))
        (json/parse-string (:body resp) true)))))

;; ---------------------------------------------------------------------------
;; CLI -main — mirrors the python `actors` click group argv contract:
;;   e7m actors <shinka|jokyo|migrate-to-plc|cc-coverage|common-crawler-coverage> [opts]
;; SAFETY: shinka (LLM + PDS applyWrites) and jokyo (/_heartbeat POST) are
;; side-effecting; they default to a plan/no-op path. migrate-to-plc runs its
;; pure --offline mock for real; live PDS is gated behind explicit flags.
;; ---------------------------------------------------------------------------

(defn- cli-parse
  "Minimal argv parser → [positionals flags]. bool-flags = set of names (no --)."
  [args bool-flags]
  (loop [a (seq args) pos [] flags {}]
    (if-not a
      [pos flags]
      (let [t (first a)]
        (cond
          (and (str/starts-with? t "--") (contains? bool-flags (subs t 2)))
          (recur (next a) pos (assoc flags (subs t 2) true))
          (str/starts-with? t "--")
          (recur (nnext a) pos (assoc flags (subs t 2) (fnext a)))
          :else
          (recur (next a) (conj pos t) flags))))))

(defn -main [& args]
  (let [[pos flags] (cli-parse args #{"json" "dry-run" "offline" "apply"
                                      "live" "no-live" "murakumo" "no-murakumo"})
        sub   (first pos)
        json? (boolean (get flags "json"))]
    (case sub
      "migrate-to-plc"
      (let [actor    (get flags "actor")
            handle   (or (get flags "handle") "")
            offline? (boolean (get flags "offline"))]
        (cond
          (nil? actor)
          (println "usage: actors migrate-to-plc --actor NAME [--handle H] [--offline] [--apply] [--pds URL] [--json]")
          offline?
          (let [res (migrate-to-plc "" actor handle {:offline? true})]
            (if json?
              (println (json/generate-string res {:pretty true}))
              (do (println (str "actor:       " actor))
                  (println (str "current DID: " (:legacyDid res)))
                  (println (str "mode:        offline + dry-run (mock, no write)"))
                  (println (str "new DID:     " (:did res)))
                  (println (str "genesis CID: " (:genesisCid res))))))
          :else
          (println (str "actors migrate-to-plc (live PDS XRPC com.etzhayyim.plc.migrateActor) "
                        "needs a reachable PDS + auth token. Re-run with --offline for the "
                        "dry-run mock, or use the Go CLI for the live migration."))))

      "shinka"
      (let [model   (or (get flags "model") "gemma3:4b")
            limit   (or (get flags "limit") "50")
            filt    (or (get flags "filter") "")
            backend (if (get flags "no-murakumo") "ollama" "murakumo")]
        (println "actors shinka — domain-knowledge generation (LLM + PDS applyWrites).")
        (println (str "  plan: backend=" backend " model=" model " limit=" limit
                      (when (seq filt) (str " filter=" filt))))
        (println "  SIDE-EFFECTING: calls an LLM backend then writes records via")
        (println "  com.atproto.repo.applyWrites. The full parallel loop is not a single")
        (println "  ported fn (build-prompt/parse-result/fetch-actors/write-result are the")
        (println "  building blocks). Run the Go/py CLI for the live loop; not executed here."))

      "jokyo"
      (let [filt (or (get flags "filter") "")
            live (not (get flags "no-live"))]
        (println "actors jokyo — autonomous-agent health scoring.")
        (println (str "  plan: live=" live (when (seq filt) (str " filter=" filt))))
        (println "  SIDE-EFFECTING when live (POST /_heartbeat per actor). score-jokyo +")
        (println "  build-health-request/build-heartbeat-request are ported; the discovery+")
        (println "  fan-out loop is not. Not executed here (no destructive probe)."))

      ("cc-coverage" "common-crawler-coverage")
      (println (str "actors " sub " requires direct Kotoba/Datomic access (pgxpool). "
                    "Use the Go binary: etzhayyim actors " sub))

      (println (str "usage: actors <shinka|jokyo|migrate-to-plc|cc-coverage|"
                    "common-crawler-coverage> [--opts]")))))
