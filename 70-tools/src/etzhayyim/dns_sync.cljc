;; etzhayyim.dns-sync — ADR-0013 Phase 3: sync deps.toml [[mitama_actors]] +
;; [[legacy_nanoids]] to Cloudflare DNS records.
;;
;; IO-REWRITE of 70-tools/etzhayyim-py/src/etzhayyim/dns_sync.py
;; The .py is KEPT (additive port — both co-exist).
;;
;; PURE-vs-IO split:
;;   PURE (parity-verifiable, unit-tested offline):
;;     parse-identifier-tables  — extract [[mitama_actors]]/[[legacy_nanoids]] from map
;;     build-desired-records    — compute the set of DNS records etzhayyim wants
;;     diff-records             — produce an apply-plan (create/update/delete/keep)
;;     emit-routing-map-ts      — generate routing-gateway legacy-nanoid-map.ts
;;     emit-yoro-mirror-ts      — generate yoro-mirror variant of the above
;;     find-services-range      — locate "services": [...] in JSONC source
;;     patch-wrangler-bindings  — patch wrangler.jsonc Service Bindings section
;;
;;   IO (request-shaping verified via injectable HTTP fn, not live calls):
;;     resolve-cf-token         — read env / wrangler OAuth toml
;;     cf-get                   — GET via injectable http-fn
;;     resolve-zone             — find CF zone ID by name
;;     list-managed-records     — paginate CF DNS records (etzhayyim-managed only)
;;     build-apply-request      — construct request map for one plan item (TESTABLE)
;;     apply-one                — execute CREATE / PATCH / DELETE one CF DNS record
;;     sync-dns (entry point)   — orchestrate the full sync
;;
;; INJECTABLE HTTP CLIENT:
;;   Every IO fn that makes network calls accepts an optional :http-fn in opts.
;;   Default = real babashka.http-client; tests inject a fake that records calls
;;   WITHOUT touching the network.  This makes request-shaping verifiable offline.
;;
;; SECURITY:
;;   No secrets at load-time.  resolve-cf-token is called only when live CF mode
;;   is explicitly requested.  Token env vars read lazily.
;;
;; bb load check:
;;   bb --classpath 70-tools/src -e "(require 'etzhayyim.dns-sync)(println :ok)"

(ns etzhayyim.dns-sync
  (:require [clojure.string :as str]
            [cheshire.core  :as json]
            #?(:bb [babashka.http-client :as http])))

;; ---------------------------------------------------------------------------
;; Constants
;; ---------------------------------------------------------------------------

(def ^:private dns-comment-prefix "etzhayyim:adr-0013:")
(def ^:private dns-txt-comment    (str dns-comment-prefix "atproto-verify"))
(def ^:private dns-cname-comment  (str dns-comment-prefix "legacy-nanoid"))
(def ^:private cf-api-base        "https://api.cloudflare.com/client/v4")

;; ---------------------------------------------------------------------------
;; Pure: identifier-table parsing
;; ---------------------------------------------------------------------------

(defn parse-identifier-tables
  "Extract [[mitama_actors]] and [[legacy_nanoids]] from an already-parsed
  data map (no file IO).  Returns {:actors [...] :legacies [...]}.
  Mirrors Python _parse_identifier_tables() — pure planning logic."
  [data]
  (let [actors   (for [a (get data "mitama_actors" [])
                       :when (seq (get a "name" ""))]
                   {:name    (get a "name" "")
                    :domain  (get a "domain" "")
                    :nanoid  (get a "nanoid" "")
                    :did     (get a "did" "")
                    :handles (vec (get a "handles" []))})
        legacies (for [l (get data "legacy_nanoids" [])
                       :when (seq (get l "actor" ""))]
                   {:actor  (get l "actor" "")
                    :nanoid (get l "nanoid" "")
                    :handle (get l "handle" "")
                    :did    (get l "did" "")})]
    {:actors (vec actors) :legacies (vec legacies)}))

;; ---------------------------------------------------------------------------
;; Pure: desired-record construction
;; ---------------------------------------------------------------------------

(defn build-desired-records
  "Compute the set of DNS records etzhayyim wants to exist.
  Returns a sorted vector of record maps.
  Mirrors Python _build_desired_records() — pure planning logic."
  [actors legacies include-txt? include-nanoid? zone-name]
  (let [zone-suffix (str "." zone-name)
        txt-recs    (when include-txt?
                      (for [a actors
                            :let [handle (or (when (seq (:domain a)) (:domain a))
                                            (first (:handles a)))]
                            :when (and handle
                                       (str/ends-with? handle zone-suffix)
                                       (seq (:did a)))]
                        {:type    "TXT"
                         :name    (str "_atproto." handle)
                         :content (str "\"did=" (:did a) "\"")
                         :ttl     3600
                         :proxied false
                         :comment dns-txt-comment}))
        cname-recs  (when include-nanoid?
                      (for [l legacies
                            :when (and (seq (:handle l))
                                       (str/ends-with? (:handle l) zone-suffix))]
                        {:type    "CNAME"
                         :name    (str (:nanoid l) zone-suffix)
                         :content (:handle l)
                         :ttl     3600
                         :proxied true
                         :comment dns-cname-comment}))
        all         (concat (or txt-recs []) (or cname-recs []))]
    (vec (sort-by (juxt :name :type) all))))

;; ---------------------------------------------------------------------------
;; Pure: diff / plan construction
;; ---------------------------------------------------------------------------

(defn diff-records
  "Compute a sync plan from desired + existing record lists.
  Each plan item is {:action :create|:update|:delete|:keep :record {...} ...}.
  Mirrors Python _diff_records() — pure planning logic."
  [desired existing]
  (let [existing-map (into {} (map (fn [r] [[(:name r) (:type r)] r]) existing))
        plan         (atom [])
        seen         (atom #{})]
    (doseq [d desired]
      (let [k [(:name d) (:type d)]]
        (swap! seen conj k)
        (if-let [e (get existing-map k)]
          (if (and (= (:content e) (:content d))
                   (= (:comment e) (:comment d)))
            (swap! plan conj {:action :keep :record d :existing e})
            (swap! plan conj {:action   :update
                              :record   (assoc d :id (get e :id ""))
                              :existing e
                              :reason   (str "content " (pr-str (:content e))
                                             " -> " (pr-str (:content d)))}))
          (swap! plan conj {:action :create :record d :reason "missing"}))))
    (doseq [[k e] existing-map]
      (when-not (contains? @seen k)
        (swap! plan conj {:action   :delete
                          :record   e
                          :existing e
                          :reason   "orphan (not in deps.toml)"})))
    @plan))

;; ---------------------------------------------------------------------------
;; Pure: TypeScript code generation
;; ---------------------------------------------------------------------------

(defn emit-routing-map-ts
  "Generate routing-gateway legacy-nanoid-map.ts content.
  Mirrors Python _emit_routing_map_ts() — pure string construction."
  [legacies]
  (let [sorted  (sort-by :nanoid legacies)
        header  (str "// legacy-nanoid-map.ts — Phase 3 grace period mapping table.\n"
                     "//\n"
                     "// Auto-generated by `etzhayyim dns-sync --emit-routing-map`. DO NOT EDIT BY HAND.\n"
                     "// Source: deps.toml [[legacy_nanoids]]\n"
                     "// Phase 4 cutover (2026-10-01, ADR-0021): this file is renamed to\n"
                     "// legacy-nanoid-map.archived.ts and the import in worker.ts is removed.\n\n"
                     "export const LEGACY_NANOID_MAP: Record<string, string> = {\n")
        entries (apply str (map (fn [l]
                                  (str "  " (json/generate-string (:nanoid l))
                                       ": " (json/generate-string (:handle l)) ",\n"))
                                sorted))
        footer  (str "}\n\n"
                     "/**\n"
                     " * Phase 4 deprecation window: when current time exceeds this, every legacy\n"
                     " * lookup logs a high-severity warning. Intended to fire alarms in CF Analytics.\n"
                     " */\n"
                     "export const PHASE4_DEPRECATE_AT = new Date('2026-10-01T00:00:00Z')\n")]
    (str header entries footer)))

(defn emit-yoro-mirror-ts
  "Generate yoro-mirror legacy-nanoid-map.ts content.
  Mirrors Python _emit_yoro_mirror_ts() — pure string construction."
  [legacies]
  (let [sorted  (sort-by :nanoid legacies)
        header  (str "// legacy-nanoid-map.ts — Phase 3 grace period mapping table (yoro mirror).\n"
                     "//\n"
                     "// MIRROR OF: 50-infra/cloudflare/workers/routing-gateway/src/legacy-nanoid-map.ts\n"
                     "// Both files are auto-generated from deps.toml [[legacy_nanoids]] by\n"
                     "// `etzhayyim dns-sync --emit-routing-map`. Keep in sync until Phase 4 cutover\n"
                     "// (2026-10-01, ADR-0021).\n"
                     "//\n"
                     "// Used by: routes/profile/[handle]/+page.server.ts to 301 redirect\n"
                     "// /profile/{nanoid}.etzhayyim.com -> /profile/{handle}.etzhayyim.com\n\n"
                     "export const LEGACY_NANOID_MAP: Record<string, string> = {\n")
        entries (apply str (map (fn [l]
                                  (str "  " (json/generate-string (:nanoid l))
                                       ": " (json/generate-string (:handle l)) ",\n"))
                                sorted))
        footer  (str "};\n\n"
                     "/**\n"
                     " * Resolve `{nanoid}.etzhayyim.com` to canonical handle, or null if not a legacy nanoid.\n"
                     " * Used by /profile/[handle] SSR redirect.\n"
                     " */\n"
                     "export function resolveLegacyHandle(handle: string): string | null {\n"
                     "  const match = handle.match(/^([a-z0-9-]+)\\.etzhayyim\\.ai$/i);\n"
                     "  if (!match) return null;\n"
                     "  const nanoid = match[1].toLowerCase();\n"
                     "  return LEGACY_NANOID_MAP[nanoid] ?? null;\n"
                     "}\n")]
    (str header entries footer)))

;; ---------------------------------------------------------------------------
;; Pure: JSONC services-range finder
;; ---------------------------------------------------------------------------

(defn- safe-char-at
  "Return char at pos in s, or nil when out of range."
  [^String s ^long pos]
  (when (< pos (.length s))
    (.charAt s pos)))

(defn find-services-range
  "Locate the '\"services\": [...]' span in a JSONC string.
  Returns [key-start bracket-close+1] or nil.
  Handles // line comments, /* block comments */, and string escapes.
  Mirrors Python _find_services_range() — pure string analysis."
  [src]
  (let [key       "\"services\""
        key-start (.indexOf src key)]
    (when (>= key-start 0)
      (let [n (count src)]
        ;; skip whitespace to find ':'
        (loop [i (+ key-start (count key))]
          (cond
            (>= i n)
            nil
            (contains? #{\space \tab \return \newline} (.charAt src i))
            (recur (inc i))
            (not= \: (.charAt src i))
            nil
            :else
            ;; skip whitespace to find '['
            (loop [j (inc i)]
              (cond
                (>= j n)
                nil
                (contains? #{\space \tab \return \newline} (.charAt src j))
                (recur (inc j))
                (not= \[ (.charAt src j))
                nil
                :else
                ;; bracket-depth scan with JSONC-awareness
                ;; state: k=pos depth in-str? escaped? in-line-cmt? in-blk-cmt?
                (loop [k            j
                       depth        0
                       in-str?      false
                       escaped?     false
                       in-line-cmt? false
                       in-blk-cmt?  false]
                  (if (>= k n)
                    nil
                    (let [c   (.charAt src k)
                          nxt (safe-char-at src (inc k))]
                      (cond
                        in-line-cmt?
                        (recur (inc k) depth in-str? escaped?
                               (not= c \newline) in-blk-cmt?)

                        in-blk-cmt?
                        (if (and (= c \*) (= nxt \/))
                          (recur (+ k 2) depth in-str? false false false)
                          (recur (inc k) depth in-str? escaped? false true))

                        in-str?
                        (cond
                          escaped?  (recur (inc k) depth false false false false)
                          (= c \\)  (recur (inc k) depth true  true  false false)
                          (= c \")  (recur (inc k) depth false false false false)
                          :else     (recur (inc k) depth true  false false false))

                        ;; start line comment
                        (and (= c \/) (= nxt \/))
                        (recur (+ k 2) depth in-str? false true false)

                        ;; start block comment
                        (and (= c \/) (= nxt \*))
                        (recur (+ k 2) depth in-str? false false true)

                        (= c \")
                        (recur (inc k) depth true false false false)

                        (= c \[)
                        (recur (inc k) (inc depth) in-str? escaped?
                               in-line-cmt? in-blk-cmt?)

                        (= c \])
                        (let [new-depth (dec depth)]
                          (if (zero? new-depth)
                            [key-start (inc k)]
                            (recur (inc k) new-depth in-str? escaped?
                                   in-line-cmt? in-blk-cmt?)))

                        :else
                        (recur (inc k) depth in-str? escaped?
                               in-line-cmt? in-blk-cmt?)))))))))))))

;; ---------------------------------------------------------------------------
;; Pure: wrangler bindings patch
;; ---------------------------------------------------------------------------

(defn patch-wrangler-bindings
  "Patch wrangler.jsonc src string, replacing the 'services' array with one
  derived from actors.  Returns [patched-src count] where count = total bindings.
  Mirrors Python _patch_wrangler_bindings() — pure string transformation."
  [src actors]
  (let [sorted-actors (sort-by :name actors)
        fixed-head    (str "\"services\": [\n"
                           "    { \"binding\": \"PDS_WORKER\",    "
                           "\"service\": \"etzhayyim-pds-2603241700\" },\n"
                           "    { \"binding\": \"PLC_DIRECTORY\", "
                           "\"service\": \"etzhayyim-plc-directory\" }")
        {actor-parts :parts actor-count :cnt}
        (reduce (fn [{:keys [parts cnt]} a]
                  (let [handle (or (when (seq (:domain a)) (:domain a)) (first (:handles a)))]
                    (if-not handle
                      {:parts parts :cnt cnt}
                      (let [label   (first (str/split handle #"\."))
                            binding (str "WORKER_"
                                         (str/upper-case
                                          (str/replace label "-" "_")))
                            service (str "etzhayyim-actor-" label)]
                        {:parts (conj parts
                                      (str ",\n    { \"binding\": "
                                           (json/generate-string binding)
                                           ", \"service\": "
                                           (json/generate-string service)
                                           " }"))
                         :cnt   (inc cnt)}))))
                {:parts [] :cnt 2}
                sorted-actors)
        new-services  (str fixed-head
                           (apply str actor-parts)
                           "\n  ]")
        rng           (find-services-range src)]
    (if rng
      (let [[ks ke] rng]
        [(str (subs src 0 ks) new-services (subs src ke)) actor-count])
      (let [last-brace (.lastIndexOf src "}")]
        (if (neg? last-brace)
          (throw (ex-info "wrangler.jsonc: no closing brace found" {:src src}))
          [(str (subs src 0 last-brace)
                ",\n  " new-services "\n"
                (subs src last-brace))
           actor-count])))))

;; ---------------------------------------------------------------------------
;; IO: token resolution (reads env only when called)
;; ---------------------------------------------------------------------------

(defn resolve-cf-token
  "Resolve Cloudflare API token from environment or wrangler OAuth config.
  Returns {:token str :source str} or {:token \"\" :source \"\"}.
  NEVER called at load/require time.
  Mirrors Python _resolve_cf_token() — IO leg."
  []
  (let [env-keys ["CLOUDFLARE_API_TOKEN" "CF_API_TOKEN" "etzhayyim_CLOUDFLARE_API_TOKEN"]
        from-env  (some (fn [k]
                          (let [v (str/trim (or (System/getenv k) ""))]
                            (when (seq v) {:token v :source k})))
                        env-keys)]
    (or from-env
        (let [home     (System/getProperty "user.home")
              wrangler (str home "/Library/Preferences/.wrangler/config/default.toml")]
          (try
            (when (.exists (java.io.File. wrangler))
              (let [text (slurp wrangler)
                    m    (re-find #"oauth_token\s*=\s*\"([^\"]+)\"" text)]
                (when m {:token (second m) :source "wrangler_oauth"})))
            (catch Exception _ nil)))
        {:token "" :source ""})))

;; ---------------------------------------------------------------------------
;; IO: Cloudflare HTTP helpers — all accept injectable :http-fn
;; ---------------------------------------------------------------------------

(defn- default-http-fn
  "Real babashka.http-client dispatch.
  Expects {:method :url :headers :body?} and returns {:status :body}."
  [{:keys [method url headers body]}]
  #?(:bb
     (let [opts (cond-> {:headers headers :timeout 30000}
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

(defn cf-get
  "GET a Cloudflare API endpoint with Bearer auth.
  Returns the parsed JSON body map.
  Raises ex-info on HTTP error (>=400).
  http-fn is injectable for test request-shaping.
  Mirrors Python _cf_get()."
  ([token url]
   (cf-get token url {}))
  ([token url {:keys [http-fn] :or {http-fn default-http-fn}}]
   (let [req  {:method  :get
               :url     url
               :headers {"Authorization" (str "Bearer " token)
                         "Content-Type"  "application/json"}}
         resp (http-fn req)]
     (when (>= (:status resp) 400)
       (throw (ex-info (str "CF API " (:status resp) " GET " url)
                       {:status (:status resp) :body (:body resp) :url url})))
     (json/parse-string (:body resp) true))))

(defn resolve-zone
  "Find the CF zone-id for zone-name via the CF Zones API.
  Raises ex-info if the zone is not found.
  Mirrors Python _resolve_zone()."
  ([token zone-name]
   (resolve-zone token zone-name {}))
  ([token zone-name opts]
   (let [url  (str cf-api-base "/zones?name="
                   (java.net.URLEncoder/encode zone-name "UTF-8"))
         body (cf-get token url opts)]
     (when (or (not (:success body)) (empty? (:result body)))
       (throw (ex-info (str "zone " (pr-str zone-name) " not found")
                       {:errors (:errors body) :zone zone-name})))
     (-> body :result first :id))))

(defn list-managed-records
  "List all CF DNS records whose comment starts with the etzhayyim prefix.
  Paginates (per_page=1000) until exhausted.
  Mirrors Python _list_managed_records()."
  ([token zone-id]
   (list-managed-records token zone-id {}))
  ([token zone-id opts]
   (loop [page 1 acc []]
     (let [url  (str cf-api-base "/zones/" zone-id
                     "/dns_records?per_page=1000&page=" page)
           body (cf-get token url opts)
           recs (filter (fn [r]
                          (str/starts-with? (or (:comment r) "")
                                            dns-comment-prefix))
                        (:result body))
           all  (concat acc recs)
           ri   (:result_info body)]
       (if (>= (or (:page ri) 1) (or (:total_pages ri) 1))
         (vec all)
         (recur (inc page) all))))))

;; ---------------------------------------------------------------------------
;; IO: request-shaping layer (testable without execution)
;; ---------------------------------------------------------------------------

(defn build-apply-request
  "Build the HTTP request map for one plan item WITHOUT executing it.
  Returns {:method :url :headers :body?} or nil for :keep.
  This is the REQUEST-SHAPING layer — tests call this to verify parity
  with dns_sync.py's _apply_one() request construction.
  Mirrors Python _apply_one() request building."
  [zone-id token plan-item]
  (let [action (:action plan-item)
        rec    (:record plan-item)
        base   (str cf-api-base "/zones/" zone-id "/dns_records")
        hdrs   {"Authorization" (str "Bearer " token)
                "Content-Type"  "application/json"}]
    (case action
      :create {:method :post   :url base                      :headers hdrs :body rec}
      :update {:method :patch  :url (str base "/" (:id rec))  :headers hdrs :body rec}
      :delete {:method :delete :url (str base "/" (:id rec))  :headers hdrs}
      :keep   nil)))

(defn apply-one
  "Execute one plan item against the CF API.
  Raises ex-info on HTTP error (>=400).
  Mirrors Python _apply_one() — IO execution leg."
  ([token zone-id plan-item]
   (apply-one token zone-id plan-item {}))
  ([token zone-id plan-item {:keys [http-fn] :or {http-fn default-http-fn}}]
   (when-let [req (build-apply-request zone-id token plan-item)]
     (let [resp (http-fn req)]
       (when (>= (:status resp) 400)
         (throw (ex-info (str "CF API " (:status resp) " "
                              (name (:method req)) " " (:url req))
                         {:status (:status resp)
                          :body   (:body resp)
                          :action (:action plan-item)})))))))

;; ---------------------------------------------------------------------------
;; IO: dry-run printer
;; ---------------------------------------------------------------------------

(defn print-dry-run-plan
  "Print the sync plan and the CF API requests that WOULD be sent,
  without executing any of them.
  No network calls, no token needed for offline display."
  [desired plan zone-id token]
  (println "etzhayyim dns-sync — dry-run plan (no CF API calls)")
  (println "====================================================")
  (println (str "desired records: " (count desired)))
  (println (str "plan items:      " (count plan)))
  (println)
  (let [by-action (group-by :action plan)]
    (doseq [a [:create :update :delete :keep]]
      (let [items (get by-action a [])]
        (when (seq items)
          (println (str "-- " (str/upper-case (name a)) " (" (count items) ")"))
          (doseq [item items]
            (println (str "  " (get-in item [:record :type])
                          "  " (get-in item [:record :name])
                          "  " (get-in item [:record :content])
                          (when-let [r (:reason item)] (str "  [" r "]")))))
          (println)))))
  (println "-- REQUESTS THAT WOULD BE SENT")
  (doseq [item  plan
          :when (not= :keep (:action item))
          :let  [req (build-apply-request zone-id token item)]
          :when req]
    (println (str "  " (str/upper-case (name (:method req)))
                  "  " (:url req)))
    (when-let [b (:body req)]
      (println (str "    body: " (json/generate-string b)))))
  (println "\ndry-run: no changes applied."))

;; ---------------------------------------------------------------------------
;; IO: full sync entry-point
;; ---------------------------------------------------------------------------

(defn sync-dns
  "Orchestrate a full DNS sync.
  opts keys (all optional):
    :zone-name       (default \"etzhayyim.com\")
    :include-txt?    (default true)
    :include-nanoid? (default true)
    :apply?          (default false) — false = dry-run (no writes)
    :no-cf?          (default false) — true = offline mode (skip CF API)
    :json-out?       (default false)
    :http-fn         injectable HTTP fn for tests

  actors/legacies: already-parsed via parse-identifier-tables.
  NEVER reads a CF token unless actually connecting to CF."
  [actors legacies opts]
  (let [{:keys [zone-name include-txt? include-nanoid?
                apply? no-cf? json-out? http-fn]
         :or   {zone-name       "etzhayyim.com"
                include-txt?    true
                include-nanoid? true
                apply?          false
                no-cf?          false
                json-out?       false
                http-fn         default-http-fn}} opts
        desired (build-desired-records actors legacies
                                       include-txt? include-nanoid? zone-name)]
    (if no-cf?
      ;; offline mode
      (if json-out?
        (do (println (json/generate-string
                      {:zone          zone-name
                       :mode          "offline"
                       :desired_count (count desired)
                       :desired       desired}
                      {:pretty true}))
            {:mode :offline :desired desired})
        (do (println "etzhayyim dns-sync -- offline mode (no Cloudflare API)")
            (println (str "zone: " zone-name "  desired: " (count desired)))
            (doseq [r desired]
              (println (str "  " (:type r) "  " (:name r) "  " (:content r))))
            {:mode :offline :desired desired}))
      ;; CF mode
      (let [{:keys [token source]} (resolve-cf-token)]
        (when (str/blank? token)
          (throw (ex-info
                  "no Cloudflare API token (CLOUDFLARE_API_TOKEN, CF_API_TOKEN, or wrangler OAuth)"
                  {:source source})))
        (let [zone-id  (resolve-zone token zone-name {:http-fn http-fn})
              existing (list-managed-records token zone-id {:http-fn http-fn})
              plan     (diff-records desired existing)
              actions  (frequencies (map :action plan))]
          (if (not apply?)
            (do (print-dry-run-plan desired plan zone-id token)
                {:mode :dry-run :plan plan :actions actions})
            ;; apply
            (let [changes (filter #(not= :keep (:action %)) plan)
                  results (mapv (fn [item]
                                  (try
                                    (apply-one token zone-id item {:http-fn http-fn})
                                    {:ok true :item item}
                                    (catch Exception e
                                      {:ok false :item item :error (ex-message e)})))
                                changes)
                  applied (count (filter :ok results))
                  failed  (count (remove :ok results))]
              (println (str "applied=" applied " failed=" failed))
              (when (pos? failed)
                (doseq [r (remove :ok results)]
                  (println (str "  FAIL " (get-in r [:item :action])
                                " " (get-in r [:item :record :name])
                                ": " (:error r)))))
              {:mode    :applied
               :applied applied
               :failed  failed
               :results results})))))))
