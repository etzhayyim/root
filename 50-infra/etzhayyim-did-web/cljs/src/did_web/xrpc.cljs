(ns did-web.xrpc
  "XRPC dispatch (/xrpc/<nsid>) — faithful cljs port of worker.ts §3. The cljs
  core owns the routing + the registry-backed short-circuits (kotobaWriteConfig,
  searchActors/getSuggestions, getProfile), the substrate alias routing, and the
  generic GET→POST-normalizing proxy. The TWO same-origin auth short-circuits
  (verifyCacao / registerAccount) are DELEGATED to the legacy TS handler via
  `fallback` — their CACAO/SIWE/ed25519 signature verification is security-
  critical crypto that stays in the audited TS leaf (re-implementing it in cljs
  would risk an auth bypass); the cljs core still owns the dispatch decision.

  Registry data + actor resolution arrive through the injected `deps` (string
  keys, rename-safe); env bindings (YORO_XRPC, upstream URLs) via goog.object."
  (:require [goog.object :as gobj]))

;; ── header sets (faithful to worker.ts) ──────────────────────────────────────
(def ^:private permissions-policy "interest-cohort=(), browsing-topics=()")

(def ^:private same-origin-auth-cors
  {"content-type" "application/json; charset=utf-8"
   "cache-control" "no-store"
   "x-etzhayyim-no-cookie" "1"
   "x-etzhayyim-auth" "cacao-verify-only"
   "access-control-allow-origin" "*"})

(def ^:private actor-json-headers
  {"content-type" "application/json; charset=utf-8"
   "cache-control" "public, max-age=60, must-revalidate"
   "access-control-allow-origin" "*"
   "x-content-type-options" "nosniff"
   "strict-transport-security" "max-age=31536000; includeSubDomains"
   "x-etzhayyim-no-cookie" "1"})

(def ^:private stripped-response-headers
  ["set-cookie" "content-security-policy" "content-security-policy-report-only"
   "strict-transport-security" "alt-svc"])

(defn- d  [deps k] (gobj/get deps k))
(defn- d* [deps k & args] (apply (gobj/get deps k) args))
(defn- e  [env k] (gobj/get env k))

(defn- json+nl [obj headers status]
  (js/Response. (str (js/JSON.stringify obj) "\n")
                #js {:status status :headers (clj->js headers)}))

;; The error responses in worker.ts §3 use bare JSON.stringify (NO trailing
;; newline), unlike the success bodies; keep that byte-for-byte.
(defn- json-err [obj headers status]
  (js/Response. (js/JSON.stringify obj)
                #js {:status status :headers (clj->js headers)}))

;; ── substrate alias map (faithful) ───────────────────────────────────────────
(def ^:private substrate-aliases
  {"app.bsky.actor.searchActors" "com.etzhayyim.yoro.actor.searchActors"
   "app.bsky.graph.getFollowers" "com.etzhayyim.yoro.graph.getFollowers"
   "app.bsky.graph.getFollows"   "com.etzhayyim.yoro.graph.getFollows"})

(def ^:private substrate-passthrough-prefixes ["com.etzhayyim.apps.unispsc."])

(def ^:private xrpc-routes
  [["com.etzhayyim.apps.unispsc."  "XRPC_UNISPSC_UPSTREAM"]
   ["app.bsky."                    "XRPC_ATPROTO_UPSTREAM"]
   ["com.atproto."                 "XRPC_ATPROTO_UPSTREAM"]
   ["chat.bsky."                   "XRPC_CHAT_UPSTREAM"]
   ["com.etzhayyim.apps.kotoba."   "XRPC_KOTOBA_UPSTREAM"]
   ["com.etzhayyim.apps.kotobase." "XRPC_KOTOBA_UPSTREAM"]
   ["com.etzhayyim."               "XRPC_etzhayyim_UPSTREAM"]])

(defn- find-xrpc-route [nsid]
  (some (fn [[prefix k]] (when (.startsWith nsid prefix) k)) xrpc-routes))

(defn- strip-incoming-cookies! [headers]
  (.delete headers "cookie") (.delete headers "host"))

(defn- apply-apex-security! [headers]
  (.set headers "strict-transport-security" "max-age=31536000; includeSubDomains")
  (.set headers "permissions-policy" permissions-policy))

;; ── kotobaWriteConfig (sync) ─────────────────────────────────────────────────
(defn- kotoba-write-config [env]
  (json+nl #js {:operatorDid (or (e env "KOTOBA_OPERATOR_DID") nil)
                :writeEnabled (boolean (and (e env "KOTOBA_WRITE_ENDPOINT")
                                            (e env "KOTOBA_OPERATOR_DID")))}
           same-origin-auth-cors 200))

;; ── searchActors / getSuggestions (async; faithful merge) ────────────────────
(defn- clamp-limit [s]
  (let [n (js/parseInt (or s "25") 10)]
    (if (js/Number.isFinite n) (js/Math.min (js/Math.max n 1) 100) 25)))

(defn- named-actors [deps q offset]
  (if-not (zero? offset)
    #js []
    (let [ql (.toLowerCase (.trim q))
          out #js []]
      (doseq [h (d deps "compiledActorHandlesList")]
        (when-let [rec (d* deps "compiledActorRecord" h)]
          (let [name (.toLowerCase (or (gobj/get rec "displayNameEn")
                                       (gobj/get rec "displayNameJa")
                                       (gobj/get rec "handle")))]
            (when (or (empty? ql) (.includes h ql) (.includes name ql))
              (.push out (d* deps "toGetProfileView" rec))))))
      out)))

(defn- upstream-merge [request env q is-suggest? offset entity-count limit]
  (let [yoro (e env "YORO_XRPC")]
    (if (and yoro (not is-suggest?) (zero? offset) (< entity-count limit))
      (let [su (js/URL. (.-url request))]
        (set! (.-pathname su) "/xrpc/com.etzhayyim.yoro.actor.searchActors")
        (let [fwd (js/Headers. (.-headers request))]
          (strip-incoming-cookies! fwd)
          (.set fwd "x-forwarded-host" "etzhayyim.com")
          (-> (.call (gobj/get yoro "fetch") yoro
                     (js/Request. (.toString su) #js {:method "GET" :headers fwd}))
              (.then (fn [ur]
                       (if-not (.-ok ur)
                         #js []
                         (.then (.json ur)
                                (fn [j]
                                  (let [acts (gobj/get j "actors")]
                                    (if (array? acts)
                                      (.slice acts 0 (- limit entity-count))
                                      #js [])))))))
              (.catch (fn [_] #js [])))))
      (js/Promise.resolve #js []))))

(defn- search-actors [request env nsid deps]
  (let [url (js/URL. (.-url request))
        sp (.-searchParams url)
        is-suggest? (or (= nsid "app.bsky.actor.getSuggestions")
                        (= nsid "com.etzhayyim.yoro.actor.getSuggestions"))
        q (if is-suggest? "" (or (.get sp "q") (.get sp "term") ""))
        limit (clamp-limit (.get sp "limit"))
        off-param (js/parseInt (or (.get sp "cursor") "0") 10)
        offset (if (and (js/Number.isFinite off-param) (> off-param 0)) off-param 0)
        page (d* deps "searchEntityActors" q limit offset)
        records (gobj/get page "records")
        entity-actors (.map records (fn [r] (d* deps "toGetProfileView" r)))
        named (named-actors deps q offset)
        entity-total (d deps "entityTotalCount")]
    (-> (upstream-merge request env q is-suggest? offset (.-length entity-actors) limit)
        (.then (fn [upstream-actors]
                 (let [actors (.concat named entity-actors upstream-actors)
                       total (+ (if (seq (.trim q)) (gobj/get page "total") entity-total)
                                (if (zero? offset) (.-length named) 0))
                       body #js {:actors actors :totalActors total}
                       next-off (gobj/get page "nextOffset")]
                   (when (not (nil? next-off)) (gobj/set body "cursor" (str next-off)))
                   (json+nl body
                            (assoc actor-json-headers
                                   "x-etzhayyim-actor-source" "entity-mirror+pds"
                                   "x-etzhayyim-entity-total" (str entity-total)
                                   "permissions-policy" permissions-policy)
                            200)))))))

;; ── getProfile short-circuit (async; returns Response or ::continue) ─────────
(defn- get-profile [request env ctx nsid deps]
  (let [url (js/URL. (.-url request))
        actor-param (or (.get (.-searchParams url) "actor") "")
        is-actor-did (.startsWith actor-param "did:web:etzhayyim.com:actor:")
        handle (d* deps "actorHandleFromParam" actor-param)]
    (if (and handle
             (or is-actor-did
                 (d* deps "compiledActorHas" handle)
                 (d* deps "isEntityHandle" handle)))
      (.then (d* deps "resolveActorRecord" handle env ctx)
             (fn [rec]
               (if rec
                 (json+nl (d* deps "toGetProfileView" rec)
                          (assoc actor-json-headers
                                 "x-etzhayyim-actor-source" (gobj/get rec "source")
                                 "permissions-policy" permissions-policy)
                          200)
                 ::continue)))
      (js/Promise.resolve ::continue))))

;; ── substrate routing + generic proxy ────────────────────────────────────────
(defn- substrate-route [request env nsid substrate-nsid]
  (let [yoro (e env "YORO_XRPC")
        su (js/URL. (.-url request))]
    (set! (.-pathname su) (str "/xrpc/" substrate-nsid))
    (let [fwd (js/Headers. (.-headers request))
          method (.-method request)]
      (strip-incoming-cookies! fwd)
      (.set fwd "x-forwarded-host" "etzhayyim.com")
      (.set fwd "x-forwarded-proto" "https")
      (.set fwd "x-etzhayyim-nsid" nsid)
      (.set fwd "x-etzhayyim-substrate-nsid" substrate-nsid)
      (-> (.call (gobj/get yoro "fetch") yoro
                 (js/Request. (.toString su)
                              #js {:method method :headers fwd
                                   :body (if (or (= method "GET") (= method "HEAD"))
                                           js/undefined (.-body request))
                                   :redirect "manual"}))
          (.then (fn [resp]
                   (let [h (js/Headers. (.-headers resp))]
                     (doseq [x stripped-response-headers] (.delete h x))
                     (.set h "x-proxied-by" "etzhayyim-did-web")
                     (.set h "x-proxied-upstream" "service:yoro-xrpc-adapter")
                     (.set h "x-etzhayyim-substrate" "mst-ipfs-l2")
                     (.set h "x-etzhayyim-no-cookie" "1")
                     (apply-apex-security! h)
                     (js/Response. (.-body resp)
                                   #js {:status (.-status resp)
                                        :statusText (.-statusText resp)
                                        :headers h}))))
          (.catch (fn [err]
                    (json-err #js {:error "SubstrateUnreachable"
                                   :message (if (instance? js/Error err) (.-message err)
                                                "yoro-xrpc-adapter service binding fetch failed")
                                   :nsid nsid :substrateNsid substrate-nsid}
                              {"content-type" "application/json; charset=utf-8"
                               "x-proxied-by" "etzhayyim-did-web"
                               "x-proxied-upstream" "service:yoro-xrpc-adapter"}
                              502)))))))

(defn- proxy-xrpc [request upstream nsid]
  (let [incoming (js/URL. (.-url request))
        target (js/URL. upstream)
        read? (or (= (.-method request) "GET") (= (.-method request) "HEAD"))]
    (set! (.-pathname target) (str "/xrpc/" nsid))
    (set! (.-search target) (.-search incoming))
    (let [fwd (js/Headers. (.-headers request))
          method (if read? "POST" (.-method request))
          body (if read?
                 (let [params #js {}]
                   (.forEach (.-searchParams incoming)
                             (fn [v k]
                               (let [ex (gobj/get params k)]
                                 (cond (undefined? ex) (gobj/set params k v)
                                       (array? ex) (.push ex v)
                                       :else (gobj/set params k #js [ex v])))))
                   (js/JSON.stringify params))
                 (.-body request))]
      (when read?
        (.set fwd "content-type" "application/json")
        (.delete fwd "content-length"))
      (strip-incoming-cookies! fwd)
      (.set fwd "x-forwarded-host" "etzhayyim.com")
      (.set fwd "x-forwarded-proto" "https")
      (.set fwd "x-forwarded-method" (.-method request))
      (.set fwd "x-etzhayyim-nsid" nsid)
      (-> (js/fetch (.toString target)
                    #js {:method method :headers fwd
                         :body (if (or (= method "GET") (= method "HEAD")) js/undefined body)
                         :redirect "manual"})
          (.then (fn [resp]
                   (let [h (js/Headers. (.-headers resp))]
                     (doseq [x stripped-response-headers] (.delete h x))
                     (.set h "x-proxied-by" "etzhayyim-did-web")
                     (.set h "x-proxied-upstream" upstream)
                     (.set h "x-etzhayyim-no-cookie" "1")
                     (apply-apex-security! h)
                     (js/Response. (.-body resp)
                                   #js {:status (.-status resp)
                                        :statusText (.-statusText resp)
                                        :headers h}))))
          (.catch (fn [err]
                    (json-err #js {:error "UpstreamUnreachable"
                                   :message (if (instance? js/Error err) (.-message err)
                                                "xrpc upstream fetch failed")
                                   :nsid nsid}
                              {"content-type" "application/json; charset=utf-8"
                               "x-proxied-by" "etzhayyim-did-web"}
                              502)))))))

(defn- route-after-shortcircuits [request env nsid deps]
  (let [aliased (get substrate-aliases nsid)
        passthrough? (and (not aliased)
                          (some #(.startsWith nsid %) substrate-passthrough-prefixes))
        substrate-nsid (or aliased (when passthrough? nsid))]
    (if (and substrate-nsid (e env "YORO_XRPC"))
      (substrate-route request env nsid substrate-nsid)
      (let [route-key (find-xrpc-route nsid)]
        (cond
          (nil? route-key)
          (json-err #js {:error "MethodNotImplemented"
                         :message (str "no upstream registered for NSID '" nsid "'")}
                    {"content-type" "application/json; charset=utf-8"} 501)
          (let [up (e env route-key)] (or (nil? up) (= up "")))
          (json-err #js {:error "UpstreamNotConfigured"
                         :message (str "env." route-key " is empty") :nsid nsid}
                    {"content-type" "application/json; charset=utf-8"} 503)
          :else (proxy-xrpc request (e env route-key) nsid))))))

(defn handle
  "Dispatch /xrpc/<nsid>. `fallback` is the legacy TS handler (used only for the
  CACAO-crypto auth short-circuits). Returns Response | Promise<Response>."
  [request env ctx deps fallback nsid]
  (let [method (.-method request)
        post? (= method "POST")
        read? (or (= method "GET") (= method "HEAD"))]
    (cond
      ;; CACAO crypto stays in the audited TS leaf
      (and post? (= nsid "com.etzhayyim.authz.verifyCacao"))     (fallback request env ctx)
      (and post? (= nsid "com.etzhayyim.authz.registerAccount")) (fallback request env ctx)
      ;; kotoba-write config (public, no secret)
      (and read? (= nsid "com.etzhayyim.authz.kotobaWriteConfig")) (kotoba-write-config env)
      ;; entity-mirror search / suggestions
      (and read? (or (= nsid "app.bsky.actor.searchActors")
                     (= nsid "com.etzhayyim.yoro.actor.searchActors")
                     (= nsid "app.bsky.actor.getSuggestions")
                     (= nsid "com.etzhayyim.yoro.actor.getSuggestions")))
      (search-actors request env nsid deps)
      ;; registered-actor profile (else fall through to substrate/proxy)
      (and read? (or (= nsid "app.bsky.actor.getProfile")
                     (= nsid "com.etzhayyim.actor.getProfile")))
      (.then (get-profile request env ctx nsid deps)
             (fn [r] (if (= r ::continue)
                       (route-after-shortcircuits request env nsid deps)
                       r)))
      ;; AT-repo content-addressed edge serving (ADR-2606272300): serve the
      ;; actor repo CAR statelessly from ACTOR_KV (`at-repo:<did>`) — the AT-repo
      ;; read off the Cloudflare edge with no operated server (the canonical
      ;; browser-complete / no-server-state architecture). A repo not yet
      ;; published to the edge falls through to the PDS proxy (route-after-…).
      (and read? (= nsid "com.atproto.sync.getRepo"))
      (let [did (or (.get (.-searchParams (js/URL. (.-url request))) "did") "")
            kv  (e env "ACTOR_KV")]
        (if (and (not= did "") kv)
          (-> (.get kv (str "at-repo:" did) #js {:type "arrayBuffer"})
              (.then (fn [car]
                       (if car
                         (js/Response. car
                                       #js {:status 200
                                            :headers #js {"content-type" "application/vnd.ipld.car; version=1"
                                                          "cache-control" "public, max-age=60"
                                                          "x-proxied-by" "etzhayyim-did-web"
                                                          "x-etzhayyim-substrate" "edge-content-addressed"}})
                         (route-after-shortcircuits request env nsid deps))))
              (.catch (fn [_] (route-after-shortcircuits request env nsid deps))))
          (route-after-shortcircuits request env nsid deps)))
      :else (route-after-shortcircuits request env nsid deps))))
