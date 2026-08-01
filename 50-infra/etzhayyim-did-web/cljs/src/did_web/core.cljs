(ns did-web.core
  "Request-handling core for the etzhayyim did:web Worker, compiled to ESM and
  delegated to by the thin TypeScript shell (src/worker.ts).

  Migration stance (operator decision 2026-06-18): the cljs core OWNS the local
  content/identity surface (DID docs, actor records, donation + atlas pages);
  the heavy I/O plumbing (ipfs gateway, kotoba block CAS, xrpc proxy, reverse
  proxy) is routed by the same cljs router but still handled by the legacy TS
  `fallback` until a later batch — so the cut-over is route-by-route and
  rollback-safe. The route DECISION lives in did-web.router (.cljc, bb-tested);
  this namespace only adds Response construction + dependency injection.

  CRITICAL interop rule (caught by the build pilot): under :advanced compilation
  the Closure compiler RENAMES dotted property access on objects it cannot type
  (`(.-didDoc deps)` → `d.Qb`). Built-in Web APIs (Request/URL/Response/Headers)
  have externs so `(.-method request)` etc. are safe — but the injected `deps`
  object is OUR untyped JS, so its fields MUST be read with string access via
  `goog.object/get`. Never use `(.-foo deps)` on the injection object."
  (:require [clojure.string :as str]
            [goog.object :as gobj]
            [did-web.router :as router]
            [did-web.ipfs :as ipfs]
            [did-web.kotoba :as kotoba]
            [did-web.system-dynamics :as system-dynamics]
            [did-web.shell :as shell]
            [did-web.proxy :as proxy]
            [did-web.xrpc :as xrpc]))

;; ─── injected-deps access (rename-safe) ──────────────────────────────────────

(defn dep
  "Read a field from the injected `deps` object by string key (rename-safe)."
  [deps k]
  (gobj/get deps k))

(defn- call
  "Invoke an injected closure `deps[k]` with args (rename-safe)."
  [deps k & args]
  (apply (gobj/get deps k) args))

;; ─── header sets (byte-faithful to worker.ts) ────────────────────────────────

(def ^:private permissions-policy "interest-cohort=(), browsing-topics=()")

;; CORS + the standard security set shared by the local JSON surfaces.
(def ^:private base-sec
  {"access-control-allow-origin" "*"
   "x-content-type-options" "nosniff"
   "strict-transport-security" "max-age=31536000; includeSubDomains"
   "permissions-policy" permissions-policy
   "x-etzhayyim-no-cookie" "1"})

;; HTML pages: no CORS (same-origin), CSP set per-route.
(def ^:private html-sec
  {"x-frame-options" "SAMEORIGIN"
   "x-content-type-options" "nosniff"
   "strict-transport-security" "max-age=31536000; includeSubDomains"
   "permissions-policy" permissions-policy
   "x-etzhayyim-no-cookie" "1"})

;; ACTOR_JSON_HEADERS — note: max-age=60 and NO permissions-policy (matches TS).
(def ^:private actor-json-headers
  {"content-type" "application/json; charset=utf-8"
   "cache-control" "public, max-age=60, must-revalidate"
   "access-control-allow-origin" "*"
   "x-content-type-options" "nosniff"
   "strict-transport-security" "max-age=31536000; includeSubDomains"
   "x-etzhayyim-no-cookie" "1"})

(defn- resp
  "Build a js/Response. `headers` is a Clojure map with string keys (rename-safe
  via clj->js). `body` may be a string or nil."
  [body status headers]
  (js/Response. body #js {:status status :headers (clj->js headers)}))

(defn- json-pretty [x] (str (js/JSON.stringify x nil 2) "\n"))
(defn- json-compact [x] (str (js/JSON.stringify x) "\n"))

(defn- method-not-allowed
  "A fresh 405 Response per call — a Response body is a single-use stream in the
  Workers runtime, so a shared instance must not be returned for two requests."
  []
  (js/Response. "Method Not Allowed"
                #js {:status 405 :headers #js {"allow" "GET, HEAD"}}))

;; ─── local JSON routes ───────────────────────────────────────────────────────

(defn- did-json-route [deps]
  (resp (json-pretty (dep deps "didDoc")) 200
        (assoc base-sec
               "content-type" "application/did+json; charset=utf-8"
               "cache-control" "public, max-age=300, must-revalidate")))

(defn- donation-json-route [deps]
  (resp (json-pretty (dep deps "donationPolicy")) 200
        (assoc base-sec
               "content-type" "application/json; charset=utf-8"
               "cache-control" "public, max-age=300, must-revalidate")))

(defn- actors-json-route
  "Async: buildActorsJson(env) → Promise. Pretty JSON."
  [deps env]
  (.then (call deps "buildActorsJson" env)
         (fn [obj]
           (resp (json-pretty obj) 200
                 (assoc base-sec
                        "content-type" "application/json; charset=utf-8"
                        "cache-control" "public, max-age=300, must-revalidate")))))

(defn- gov-units-route
  "Served from ACTOR_KV (gov-atlas:index). Async kvGet(env, key) → string|nil."
  [deps env]
  (.then (call deps "kvGet" env "gov-atlas:index")
         (fn [raw]
           (let [body (if raw raw "{\"error\":\"gov-atlas index not provisioned (run gen-gov-atlas-index + kv put gov-atlas:index)\"}")
                 status (if raw 200 503)]
             (resp (str body "\n") status
                   (assoc base-sec
                          "content-type" "application/json; charset=utf-8"
                          "cache-control" "public, max-age=300, must-revalidate"))))))

(defn- gov-procedures-route [deps]
  (let [m (dep deps "govProcMeta")]
    (resp (json-compact
           #js {:graph "actors-v1"
                :adr #js ["2606021600" "2606042330"]
                :note "Observational mirror: public administrative procedures grouped by owning gov entity-actor handle. NOT the government, NOT an official channel, never filed on anyone's behalf (→ toritsugi, gated). All rows :representative / :unverified-seed (G5)."
                :generatedAt (gobj/get m "generatedAt")
                :count (gobj/get m "total")
                :owners (gobj/get m "owners")
                :jurisdictions (gobj/get m "jurisdictions")
                :procedures (dep deps "govProcList")})
          200
          (assoc base-sec
                 "content-type" "application/json; charset=utf-8"
                 "cache-control" "public, max-age=300, must-revalidate"))))

;; ─── local HTML routes ───────────────────────────────────────────────────────

(defn- html-resp [body csp]
  (resp body 200
        (assoc html-sec
               "content-type" "text/html; charset=utf-8"
               "cache-control" "public, max-age=300, must-revalidate"
               "content-security-policy" csp)))

;; text/xml discovery-surface routes (robots.txt / sitemap.xml family). Plain
;; text bodies, cacheable, same security header set as the HTML routes minus
;; CSP (not applicable to a non-HTML response).
(defn- text-resp [body content-type]
  (resp body 200
        (assoc html-sec
               "content-type" content-type
               "cache-control" "public, max-age=300, must-revalidate")))

(defn- home-route [deps]
  (html-resp (call deps "homeHtml")
             "default-src 'none'; script-src 'self'; connect-src 'self'; style-src 'self'; img-src 'self' data:; base-uri 'none'; form-action 'none'"))

(defn- donate-route [deps]
  (html-resp (dep deps "donateHtml")
             "default-src 'none'; style-src 'self'; base-uri 'none'; form-action 'none'"))

(defn- tomoshibi-route [deps]
  (html-resp (dep deps "tomoshibiHtml")
             "default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'"))

(defn- actors-html-route [deps]
  (html-resp (call deps "actorsHtml")
             "default-src 'none'; script-src 'self' 'wasm-unsafe-eval'; connect-src 'self'; style-src 'self'; img-src 'self' data:; base-uri 'none'; form-action 'none'"))

(declare actor-system-dynamics-data)

(defn- system-dynamics-route [deps env ctx]
  (let [handles (or (dep deps "infraActorHandles") #js [])]
    (.then
     (js/Promise.all
      (clj->js (map #(call deps "resolveActorRecord" % env ctx)
                    (array-seq handles))))
     (fn [records]
       (let [actors (->> (map vector (array-seq handles) (array-seq records))
                         (keep (fn [[handle rec]]
                                 (when rec
                                   (actor-system-dynamics-data rec handle))))
                         vec)]
         (html-resp (system-dynamics/page-html actors)
                    "default-src 'none'; style-src 'self'; img-src 'self' data:; base-uri 'none'; form-action 'none'"))))))

(defn- organism-route []
  ;; Shared-shell page (header/nav/footer + shell.css), like every other public
  ;; page. The organism body hydrates into #app from same-origin JSON snapshots
  ;; via /_shell/organism.js; styles in /_shell/organism.css (org- scoped). The
  ;; former standalone inline-<style>/<script> document was the lone UIUX outlier
  ;; (ADR: etzhayyim-did-web UIUX unification).
  (let [main (str
              "<div id=\"app\">"
              "<div class=\"org-hd\"><h1>etzhayyim · organism</h1>"
              "<div class=\"sub\">artificial organism / live body loop</div>"
              "<div class=\"org-live\"><span class=\"dot\"></span>live</div></div>"
              "<div class=\"org-pills\">"
              "<div class=\"org-pill a\"><b>—</b> alive</div>"
              "<div class=\"org-pill d\"><b>—</b> dormant</div>"
              "<div class=\"org-pill s\"><b>—</b> stub</div>"
              "<div class=\"org-pill\"><b>—</b> cells</div></div>"
              "<div class=\"org-cols\"><div>"
              "<div class=\"org-card\"><h2>Present state</h2>"
              "<div class=\"org-muted\">last update: loading…</div>"
              "<div class=\"org-narr\"><div class=\"org-narrtext\">organism を読み込み中…</div>"
              "<div class=\"org-muted\">trajectory points: —</div></div>"
              "<div class=\"org-legend\"><span><i style=\"background:var(--alive)\"></i>alive</span>"
              "<span><i style=\"background:var(--dormant)\"></i>dormant</span>"
              "<span><i style=\"background:var(--stub,#5b6472)\"></i>stub</span></div></div>"
              "<div class=\"org-card\"><h2>Live activity</h2><h3>recent actors</h3>"
              "<ul class=\"org-ticks\"><li class=\"org-tick\"><span class=\"org-tsubj\">loading pulse…</span></li></ul></div>"
              "</div><div>"
              "<div class=\"org-card\"><h2>What this shows</h2>"
              "<div class=\"org-wbline\">body summary from <code>organism.json</code></div>"
              "<ul class=\"org-ticks\">"
              "<li class=\"org-tick\"><span class=\"org-tsubj\">heartbeat and mood from <code>pulse.json</code> / <code>joucho.json</code></span></li>"
              "<li class=\"org-tick\"><span class=\"org-tsubj\">system dynamics path: <a href=\"/system-dynamics\">/system-dynamics</a></span></li>"
              "<li class=\"org-tick\"><span class=\"org-tsubj\">resident actor pulse: <a href=\"/murakumo\">/murakumo</a></span></li></ul></div>"
              "<div class=\"org-card\"><h2>System of systems</h2>"
              "<div class=\"org-muted\">system graph</div>"
              "<p class=\"org-hint\">The organism is rendered from local JSON snapshots.</p></div>"
              "</div></div>"
              "</div>")]
    (html-resp
     (shell/page-html
      {:title "etzhayyim — organism · 生命活動"
       :lang "ja"
       :description "etzhayyim artificial organism — per-cell life activity (clj 内部代謝 / actor 細胞間シグナル / atproto 外界代謝) over the kotoba Datom log."
       :active "/organism"
       :main main
       :extra-css ["/_shell/organism.css"]
       :script-src "/_shell/organism.js"
       :footer-html "Live snapshots: <a href=\"/organism/organism.json\">organism.json</a> · <a href=\"/organism/pulse.json\">pulse.json</a> · <a href=\"/organism/health.json\">health.json</a> · <a href=\"/murakumo\">/murakumo</a>."})
     "default-src 'none'; script-src 'self'; connect-src 'self'; style-src 'self'; img-src 'self' data:; base-uri 'none'; form-action 'none'")))

(defn- gov-route []
  (let [main (str "<h1>公 — World Government Atlas</h1>"
                  "<p class=\"sub\">An observational <strong>mirror</strong> + civic wayfinding map of the world's government units — never the government, never an official channel, never a target-list (ADR-2606021600). Data: <a href=\"/.well-known/gov-units.json\">/.well-known/gov-units.json</a>.</p>"
                  "<input id=\"q\" class=\"gov-q\" placeholder=\"search by name, endonym, romanization or id… (try: 国会, Kokkai, Verkhovna, Knesset, 札幌市)\" autocomplete=\"off\">"
                  "<div class=\"gov-row\">"
                  "<select id=\"lvl\"><option value=\"\">all levels</option></select>"
                  "<select id=\"src\"><option value=\"\">all sourcing</option><option value=\"authoritative\">authoritative</option><option value=\"representative\">representative</option></select>"
                  "</div>"
                  "<div id=\"stats\" class=\"sub\">loading…</div>"
                  "<ul id=\"out\" class=\"gov-list\"></ul>")]
    (html-resp
     (shell/page-html
      {:title "公 ooyake — World Government Atlas · etzhayyim"
       :lang "ja"
       :description "Observational mirror + civic wayfinding map of the world's government units. Never the government, never a target-list (ADR-2606021600)."
       :active "/gov"
       :main main
       :footer-html "Data: <a href=\"/.well-known/gov-units.json\">/.well-known/gov-units.json</a> · <a href=\"/actors\">/actors</a> · ADR-2606021600."})
     "default-src 'none'; script-src 'self'; connect-src 'self'; style-src 'self'; img-src 'self' data:; base-uri 'none'; form-action 'none'")))

(defn- murakumo-route []
  (let [main (str "<h1 class=\"mk-h1\">雲 Murakumo — kotoba-wasm 常駐アクター</h1>"
                  "<p class=\"sub\">etzhayyim / <a href=\"https://aozora.app\">aozora.app</a> — Murakumo メッシュ上で kotoba-wasm として常駐稼働するアクターのライブ可視化。グリッド / 時系列 (commit pulse) / 同字 家系 の3ビューを <a href=\"/.well-known/actors.json\">actors.json</a> + <a href=\"/organism/pulse.json\">pulse.json</a> の same-origin JSON から描画。</p>"
                  "<div id=\"mk-app\" class=\"mk\"><p class=\"mk-loading\">loading live pulse…</p></div>")]
    (html-resp
     (shell/page-html
      {:title "雲 Murakumo — kotoba-wasm 常駐アクター · etzhayyim"
       :lang "ja"
       :description "Murakumo メッシュ上で kotoba-wasm として常駐稼働するアクターのライブ可視化。グリッド / commit 時系列 / 同字 家系の3ビュー。"
       :active "/murakumo"
       :main main
       :extra-css ["/_shell/murakumo.css"]
       :script-src "/_shell/murakumo.js"
       :footer-html "Live sources: <a href=\"/.well-known/actors.json\">/.well-known/actors.json</a> · <a href=\"/organism/pulse.json\">/organism/pulse.json</a> · <a href=\"/actors\">/actors</a>."})
     "default-src 'none'; script-src 'self'; connect-src 'self'; style-src 'self'; img-src 'self' data:; base-uri 'none'; form-action 'none'")))

;; ─── discovery surface (robots.txt / sitemap.xml family) ────────────────────
;;
;; Fixed 2026-07-21: these 4 paths previously had no owned route AND no
;; ./public static file, so every request fell through to the reverse proxy
;; (proxy/reverse-proxy) and served the retired YORO app's leftover
;; robots.txt/sitemap.xml verbatim — including a sitemap whose every entry
;; pointed at the dead redirect target of the retired YORO subdomain. That
;; actively mis-taught search crawlers what etzhayyim.com is. These routes
;; are now owned locally with etzhayyim.com's own real content.

(def ^:private robots-txt-body
  (str "# etzhayyim.com — public root / observation surface for etzhayyim,\n"
       "# a religious artificial organism (did:web:etzhayyim.com).\n"
       "# https://etzhayyim.com\n"
       "User-agent: *\n"
       "Allow: /\n"
       "\n"
       "Sitemap: https://etzhayyim.com/sitemap.xml\n"))

(def ^:private sitemap-index-body
  (str "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
       "<sitemapindex xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">\n"
       "  <sitemap><loc>https://etzhayyim.com/sitemaps/static.xml</loc></sitemap>\n"
       "  <sitemap><loc>https://etzhayyim.com/sitemaps/actors/index.xml</loc></sitemap>\n"
       "</sitemapindex>\n"))

;; The 8 real top-level HTML pages this Worker owns per did-web.router's
;; static-path table (:home-html … :murakumo-html + :gov-html). Not an
;; exhaustive route enumeration — a hand-picked, real, human-facing subset.
(def ^:private sitemap-static-body
  (str "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
       "<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">\n"
       "  <url><loc>https://etzhayyim.com/</loc></url>\n"
       "  <url><loc>https://etzhayyim.com/actors</loc></url>\n"
       "  <url><loc>https://etzhayyim.com/organism</loc></url>\n"
       "  <url><loc>https://etzhayyim.com/system-dynamics</loc></url>\n"
       "  <url><loc>https://etzhayyim.com/murakumo</loc></url>\n"
       "  <url><loc>https://etzhayyim.com/gov</loc></url>\n"
       "  <url><loc>https://etzhayyim.com/donate</loc></url>\n"
       "  <url><loc>https://etzhayyim.com/tomoshibi</loc></url>\n"
       "</urlset>\n"))

;; Points at the real, human-browsable actor index page rather than
;; fabricating an exhaustive per-actor sitemap for the several hundred
;; dynamically-registered actor DIDs (a real generator is a follow-up).
(def ^:private sitemap-actors-index-body
  (str "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
       "<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">\n"
       "  <url><loc>https://etzhayyim.com/actors</loc></url>\n"
       "</urlset>\n"))

(defn- robots-txt-route []
  (text-resp robots-txt-body "text/plain; charset=utf-8"))

(defn- sitemap-xml-route []
  (text-resp sitemap-index-body "application/xml; charset=utf-8"))

(defn- sitemap-static-xml-route []
  (text-resp sitemap-static-body "application/xml; charset=utf-8"))

(defn- sitemap-actors-index-xml-route []
  (text-resp sitemap-actors-index-body "application/xml; charset=utf-8"))

(defn- round1 [x]
  (/ (Math/round (* 10.0 (double x))) 10.0))

(defn- actor-flow-score [source kind service-count vm-count wasm-cid adr primary-lexicon primary-schema]
  (let [prior-score (+ (if primary-lexicon 1.2 0.3)
                       (if primary-schema 1.0 0.2)
                       (min 1.5 (* 0.25 (count adr))))
        evidence-score (+ (min 2.6 (* 0.7 service-count))
                          (min 1.6 (* 0.45 vm-count))
                          (case source
                            "kotoba" 0.9
                            "compiled" 0.7
                            "kv" 0.5
                            "derived" 0.4
                            0.3))
        policy-score (+ (case kind
                          "tier-b" 1.8
                          "entity-mirror" 1.3
                          "free-form" 0.7
                          1.0)
                        (case source
                          "kotoba" 0.4
                          "compiled" 0.3
                          "kv" 0.2
                          0.1)
                        (if wasm-cid 1.2 0.0))
        surprise-penalty (+ (if (and (zero? service-count) (zero? vm-count) (nil? wasm-cid)) 1.4 0.4)
                            (if (and (nil? primary-lexicon) (nil? primary-schema)) 0.7 0.0)
                            (case kind
                              "free-form" 0.5
                              0.0))
        score (max 0.0 (min 10.0 (+ prior-score evidence-score policy-score (- surprise-penalty))))]
    {:flow-score (round1 score)
     :flow-source (str "prior " (round1 prior-score)
                       " · evidence " (round1 evidence-score)
                       " · policy " (round1 policy-score)
                       " · surprise " (round1 surprise-penalty))
     :flow-proxy (round1 (/ score 10.0))}))

(defn- actor-system-dynamics-data [rec handle]
  (let [service (or (gobj/get rec "service") #js [])
        vm (or (gobj/get rec "vm") #js [])
        adr (or (gobj/get rec "adr") #js [])
        service-count (if rec (.-length service) 0)
        vm-count (if rec (.-length vm) 0)
        wasm-cid (gobj/get rec "wasmCid")
        source (or (gobj/get rec "source") "scaffold")
        kind (or (gobj/get rec "kind") "free-form")
        status (or (gobj/get rec "status") "scaffold")
        performer-type (or (gobj/get rec "performerType") "system")
        ui-type (or (gobj/get rec "uiType") "none")
        display-name (or (gobj/get rec "displayNameEn")
                         (gobj/get rec "displayNameJa")
                         handle)
        did (or (gobj/get rec "did")
                (str "did:web:etzhayyim.com:actor:" handle))
        description (or (gobj/get rec "description")
                        "No actor record is published yet; this is the scaffold view for the handle.")
        service-types (->> (array-seq service)
                           (map (fn [s] (gobj/get s "type")))
                           (remove nil?)
                           vec)
        score (actor-flow-score source kind service-count vm-count wasm-cid adr
                                (gobj/get rec "primaryLexicon")
                                (gobj/get rec "primarySchema"))]
    {:handle handle
     :display-name display-name
     :did did
     :description description
     :kind kind
     :status status
     :source source
     :performer-type performer-type
     :ui-type ui-type
     :glyph (gobj/get rec "glyph")
     :primary-lexicon (gobj/get rec "primaryLexicon")
     :primary-schema (gobj/get rec "primarySchema")
     :service-count service-count
     :vm-count vm-count
     :wasm-cid (gobj/get rec "wasmCid")
     :adr (vec (array-seq adr))
     :service-types service-types
     :flow-score (:flow-score score)
     :flow-proxy (:flow-proxy score)
     :flow-source (:flow-source score)}))

(defn- actor-system-dynamics-route [deps env ctx raw-handle]
  (let [handle (.toLowerCase (js/decodeURIComponent raw-handle))]
    (cond
      (not (call deps "handleValid" handle))
      (resp (js/JSON.stringify #js {:error "HandleInvalid"}) 400 actor-json-headers)

      :else
      (.then
       (call deps "resolveActorRecord" handle env ctx)
       (fn [rec]
         (html-resp
          (system-dynamics/actor-page-html (actor-system-dynamics-data rec handle))
          "default-src 'none'; style-src 'self'; img-src 'self' data:; base-uri 'none'; form-action 'none'"))))))

;; ─── per-actor routes (async, kotoba-first resolution via injected deps) ──────

(defn- norm-handle [raw] (.toLowerCase (js/decodeURIComponent raw)))

(defn- actor-did-route [deps env ctx raw-handle]
  (let [handle (norm-handle raw-handle)]
    (cond
      (not (call deps "handleValid" handle))
      (resp (js/JSON.stringify
             #js {:error "HandleInvalid"
                  :message "handle must be 1-63 chars, lowercase alnum + hyphen, no leading/trailing hyphen"})
            400 {"content-type" "application/json; charset=utf-8"})

      (not (call deps "isKnownHandle" handle))
      (resp (js/JSON.stringify
             #js {:error "HandleNotInRegistry"
                  :message (str "handle '" handle "' matches a namespaced registry shape but is not registered")
                  :registry "com.etzhayyim.apps.unispsc"
                  :registryTotalCount (dep deps "unispscTotal")})
            404 {"content-type" "application/json; charset=utf-8"
                 "cache-control" "public, max-age=60, must-revalidate"})

      :else
      (.then
       (call deps "resolveActorRecord" handle env ctx)
       (fn [rec]
         (let [doc (if rec
                     (call deps "toDidDoc" rec env)
                     (call deps "buildPerActorDidDoc" handle env))
               source (or (when rec (gobj/get rec "source")) "scaffold")
               base-headers (assoc base-sec
                                   "content-type" "application/did+json; charset=utf-8"
                                   "cache-control" "public, max-age=60, must-revalidate"
                                   "x-etzhayyim-actor-source" source)
               finish (fn [cid]
                        (let [hdrs (if cid
                                     (assoc base-headers
                                            "x-etzhayyim-did-doc-cid" cid
                                            "link" (str "<https://etzhayyim.com/ipfs/" cid ">; rel=\"canonical\"; type=\"application/did+json\""))
                                     base-headers)]
                          (resp (json-pretty doc) 200 hdrs)))]
           (if rec
             (.then (call deps "didDocCid" rec env) finish)
             (finish nil))))))))

(defn- actor-profile-route [deps env ctx raw-handle]
  (let [handle (norm-handle raw-handle)]
    (cond
      (not (call deps "handleValid" handle))
      (resp (js/JSON.stringify #js {:error "HandleInvalid"}) 400 actor-json-headers)

      :else
      (.then
       (call deps "resolveActorRecord" handle env ctx)
       (fn [rec]
         (if-not rec
           (resp (js/JSON.stringify
                  #js {:error "ProfileNotFound"
                       :message (str "'" handle "' is not a registered actor; profiles for free-form handles resolve via the PDS, not the actor registry")})
                 404 actor-json-headers)
           (resp (json-pretty (call deps "toGetProfileView" rec)) 200
                 (assoc actor-json-headers "x-etzhayyim-actor-source" (gobj/get rec "source")))))))))

(defn- actor-procedures-route [deps raw-handle]
  (let [handle (norm-handle raw-handle)]
    (if-not (call deps "handleValid" handle)
      (resp (js/JSON.stringify #js {:error "HandleInvalid"}) 400 actor-json-headers)
      (let [procs (call deps "govProcsByOwner" handle)]
        (resp (json-pretty
               #js {:handle handle
                    :did (str "did:web:etzhayyim.com:actor:" handle)
                    :adr #js ["2606021600" "2606042330"]
                    :note "Observational mirror of public procedures done at this administrative unit. NOT the government, NOT an official channel; never filed on anyone's behalf (→ toritsugi, gated). All rows :representative / :unverified-seed (G5)."
                    :count (.-length procs)
                    :procedures procs})
              200 actor-json-headers)))))

;; ─── dispatcher ──────────────────────────────────────────────────────────────

(defn handle
  "ESM entry. `deps` is the JS injection object from the shell (static data +
  leaf closures); `fallback` is the legacy TS fetch handler. Returns a Response
  or a Promise<Response>. The route decision is the pure did-web.router; this fn
  maps the decided route → its interop handler, enforces GET/HEAD-only where the
  router says so, and hands unowned routes back to the TS fallback."
  [request env ctx deps fallback]
  (let [url    (js/URL. (.-url request))
        method (.-method request)
        {:keys [route handle cid nsid]} (router/route {:method method
                                                       :path   (.-pathname url)})]
    (if-not (router/method-allowed? route method)
      (method-not-allowed)
      (case route
        :home-html          (home-route deps)
        :did-json            (did-json-route deps)
        :donation-json       (donation-json-route deps)
        :donate-html         (donate-route deps)
        :tomoshibi-html      (tomoshibi-route deps)
        :actors-json         (actors-json-route deps env)
        :actors-html         (actors-html-route deps)
        :gov-units-json      (gov-units-route deps env)
        :gov-procedures-json (gov-procedures-route deps)
        :gov-html            (gov-route)
        :organism-html       (organism-route)
        :murakumo-html       (murakumo-route)
        :robots-txt          (robots-txt-route)
        :sitemap-xml         (sitemap-xml-route)
        :sitemap-static-xml  (sitemap-static-xml-route)
        :sitemap-actors-index-xml (sitemap-actors-index-xml-route)
        :system-dynamics-html (system-dynamics-route deps env ctx)
        :actor-system-dynamics-html (actor-system-dynamics-route deps env ctx handle)
        :actor-did           (actor-did-route deps env ctx handle)
        :actor-profile       (actor-profile-route deps env ctx handle)
        :actor-procedures    (actor-procedures-route deps handle)
        :ipfs                (ipfs/handle-ipfs request env cid)
        ;; kotoba member-signed block CAS (ADR-2605312345 / 2605231525)
        :kotoba-block-put    (kotoba/handle-block-put request env)
        :kotoba-block-has    (kotoba/handle-block-has request env)
        :kotoba-root         (kotoba/handle-root-get url env)
        :kotoba-stats        (kotoba/handle-stats-get url env)
        :kotoba-block-get    (.then (kotoba/serve-block-from-kv cid env)
                                    (fn [r] (or r (fallback request env ctx))))
        ;; generic /xrpc dispatch (delegates only CACAO-crypto auth to fallback)
        :xrpc                (xrpc/handle request env ctx deps fallback nsid)
        ;; default site path → cljs reverse proxy to the yoro Worker
        :reverse-proxy       (proxy/reverse-proxy request env)
        ;; :fallback (/gov inline HTML) → legacy TS handler
        (fallback request env ctx)))))
