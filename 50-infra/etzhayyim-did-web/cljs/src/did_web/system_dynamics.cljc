(ns did-web.system-dynamics
  "Pure CLJC system-dynamics model + static HTML/SVG renderer for etzhayyim.com.

  This is deliberately data-first: stocks, flows, and feedback loops are plain
  EDN so the same model can be rendered in the Worker (CLJS) and asserted in bb
  tests. No JS interop, no network, no runtime state."
  (:require [clojure.string :as str]
            [did-web.shell :as shell]))

(def stocks
  [{:id :trust
    :label "Trust"
    :ja "信頼"
    :x 96 :y 86
    :note "public DID, ADRs, donation policy, no-cookie surface"}
   {:id :donation
    :label "Donation"
    :ja "寄付"
    :x 332 :y 70
    :note "cash, crypto, fiat-in-kind, compute gifts"}
   {:id :capacity
    :label "Capacity"
    :ja "容量"
    :x 554 :y 118
    :note "Murakumo compute, kotoba blocks, operator attention"}
   {:id :actors
    :label "Actors"
    :ja "アクター"
    :x 626 :y 304
    :note "com-etzhayyim-* organism actors and entity mirrors"}
   {:id :observations
    :label "Observations"
    :ja "観測"
    :x 406 :y 418
    :note "joucho, vitals, issues, PR outcomes, public facts"}
   {:id :decisions
    :label "Decisions"
    :ja "判断"
    :x 152 :y 386
    :note "ADR posterior, patches, pruning, boundary updates"}])

(def flows
  [{:from :trust :to :donation :label "gives rise to"}
   {:from :donation :to :capacity :label "funds / supplies"}
   {:from :capacity :to :actors :label "runs"}
   {:from :actors :to :observations :label "emit"}
   {:from :observations :to :decisions :label "inform"}
   {:from :decisions :to :trust :label "make legible"}])

(def feedback-loops
  [{:id :r1
    :name "R1 metabolism / 産霊"
    :kind :reinforcing
    :path [:trust :donation :capacity :actors :observations :decisions :trust]
    :description "More legible public state increases gift capacity; more capacity lets actors observe and repair more, which makes the public state more legible."}
   {:id :b1
    :name "B1 boundary / 和"
    :kind :balancing
    :path [:actors :observations :decisions :actors]
    :description "Actor activity is bounded by ADRs, pruning, no-server-key, and the app-aozora boundary so growth does not collapse into an opaque platform."}
   {:id :b2
    :name "B2 anti-class"
    :kind :balancing
    :path [:donation :trust]
    :description "Donations grant no perks, tiers, priority, or leaderboard; gift flow supports capacity without creating donor class pressure."}])

(def constraints
  ["etzhayyim.com is identity + observation, not PDS/AppView"
   "AT Protocol runtime is app-aozora / aozora.app"
   "no ads, no trackers, no cookies"
   "no server-held actor signing key"
   "donation earns no benefit"])

(defn- h [s]
  (-> (str s)
      (str/replace "&" "&amp;")
      (str/replace "<" "&lt;")
      (str/replace ">" "&gt;")
      (str/replace "\"" "&quot;")))

(defn- stock-by-id [id]
  (some #(when (= id (:id %)) %) stocks))

(defn- flow-line [{:keys [from to label]}]
  (let [{x1 :x y1 :y} (stock-by-id from)
        {x2 :x y2 :y} (stock-by-id to)
        mx (/ (+ x1 x2) 2)
        my (/ (+ y1 y2) 2)]
    (str "<path class=\"flow\" d=\"M" x1 " " y1 " L" x2 " " y2 "\" marker-end=\"url(#arrow)\"/>"
         "<text class=\"flow-label\" text-anchor=\"middle\" x=\"" mx "\" y=\"" (- my 8) "\">" (h label) "</text>")))

(defn- stock-node [{:keys [label ja x y note]}]
  (str "<g class=\"stock\" transform=\"translate(" x "," y ")\">"
       "<rect x=\"-78\" y=\"-34\" width=\"156\" height=\"68\" rx=\"8\"/>"
       "<text class=\"stock-label\" text-anchor=\"middle\" y=\"-4\">" (h label) "</text>"
       "<text class=\"stock-ja\" text-anchor=\"middle\" y=\"14\">" (h ja) "</text>"
       "<title>" (h note) "</title>"
       "</g>"))

(defn diagram-svg []
  (str "<svg class=\"diagram\" viewBox=\"0 0 740 500\" role=\"img\" aria-label=\"etzhayyim system dynamics stock and flow diagram\">"
       "<defs><marker id=\"arrow\" markerWidth=\"10\" markerHeight=\"10\" refX=\"8\" refY=\"3\" orient=\"auto\"><path d=\"M0,0 L8,3 L0,6 Z\" fill=\"currentColor\" opacity=\".72\"/></marker></defs>"
       "<rect class=\"boundary\" x=\"26\" y=\"32\" width=\"688\" height=\"428\" rx=\"14\"/>"
       "<text class=\"boundary-label\" x=\"46\" y=\"58\">etzhayyim.com public root boundary</text>"
       (apply str (map flow-line flows))
       (apply str (map stock-node stocks))
       "</svg>"))

(defn loop-card [{:keys [name kind description]}]
  (str "<article class=\"card\"><h2>" (h name) "</h2>"
       "<p><span class=\"tag\">" (if (= kind :reinforcing) "reinforcing" "balancing") "</span></p>"
       "<p>" (h description) "</p></article>"))

(declare round1)
(declare actor-mode actor-diagram-svg)

(defn- actor-summary-card [{:keys [handle display-name description glyph source kind status
                                   performer-type ui-type primary-lexicon
                                   primary-schema service-count vm-count wasm-cid
                                   adr service-types flow-score flow-source flow-proxy]}]
  (let [title (or display-name handle)
        mode (actor-mode {:kind kind
                          :performer-type performer-type
                          :wasm-cid wasm-cid})
        runtime (cond
                  wasm-cid (str "content-addressed runtime " wasm-cid)
                  (> (or service-count 0) 0) (str service-count " service endpoint" (when (> service-count 1) "s"))
                  :else "scaffolded runtime")
        work-label (cond
                     primary-lexicon (str "lexicon " primary-lexicon)
                     primary-schema (str "schema " primary-schema)
                     :else "no primary lexicon/schema yet")
        adr-text (if (seq adr) (str/join " · " adr) "none")
        score-pct (Math/max 0 (Math/min 100 (Math/round (* 10 (double (or flow-score 0))))))
        tags (remove nil?
                     [(when glyph (str "<span class=\"tag\">" (h glyph) "</span>"))
                      (when source (str "<span class=\"tag\">" (h source) "</span>"))
                      (when kind (str "<span class=\"tag\">" (h kind) "</span>"))
                      (when status (str "<span class=\"tag\">" (h status) "</span>"))
                      (when performer-type (str "<span class=\"tag\">" (h performer-type) "</span>"))
                      (when ui-type (str "<span class=\"tag\">" (h ui-type) "</span>"))])
        service-tags (if (seq service-types)
                       (apply str (map #(str "<span class=\"tag\">" (h %) "</span>") service-types))
                       "<span class=\"tag\">none</span>")]
    (str "<article class=\"card actor-card\">"
         "<div class=\"actor-head\"><div>"
         "<p class=\"actor-handle\">" (h handle) "</p>"
         "<h2>" (h title) "</h2>"
         "</div><a class=\"btn\" href=\"/actor/" (h handle) "/system-dynamics\">open</a></div>"
         "<p class=\"actor-desc\">" (h (or description "No actor description available yet.")) "</p>"
         "<div class=\"tag-row\">" (apply str tags) "</div>"
         "<div class=\"actor-grid-meta\">"
         "<div><strong>Role lens</strong><span>" (h (:title mode)) "</span></div>"
         "<div><strong>Runtime</strong><span>" (h runtime) "</span></div>"
         "<div><strong>Surface</strong><span>" (h (or primary-lexicon primary-schema "none")) "</span></div>"
         "<div><strong>ADR</strong><span>" (h adr-text) "</span></div>"
         "</div>"
         "<div class=\"actor-flow\">"
         "<div class=\"actor-flow-head\"><strong>Energy flow</strong><span>" (h (str flow-score "/10")) "</span></div>"
         "<div class=\"scorebar\"><span style=\"width:" score-pct "%\"></span></div>"
         "<p class=\"actor-flow-note\">" (h (or flow-source "runtime + surface proxy")) "</p>"
         "</div>"
         (actor-diagram-svg {:handle handle
                             :source source
                             :kind kind
                             :status status
                             :performer-type performer-type
                             :ui-type ui-type
                             :service-count service-count
                             :vm-count vm-count
                             :wasm-cid wasm-cid
                             :primary-lexicon primary-lexicon
                             :primary-schema primary-schema
                             :adr adr
                             :service-types service-types})
         "<div class=\"actor-services\">" service-tags "</div>"
         "</article>")))

(defn page-html
  ([]
   (page-html []))
  ([actors]
   (let [sorted-actors (sort-by (fn [a] [(- (double (or (:flow-score a) 0))) (or (:handle a) "")]) actors)
         total-score (reduce + 0.0 (map #(double (or (:flow-score %) 0)) sorted-actors))
         avg-score (if (seq sorted-actors) (/ total-score (count sorted-actors)) 0.0)
         main (str "<p class=\"eyebrow\">cljc system dynamics model</p><h1>System Dynamics</h1>"
                   "<p class=\"lead\">A stock/flow view of etzhayyim as a living public root, followed by one mini system per first-party actor. The overview explains the shared boundary; the cards below show each actor's own loop and energy-flow score.</p>"
                   (diagram-svg)
                   "<section class=\"grid\">" (apply str (map loop-card feedback-loops)) "</section>"
                   "<section class=\"card\"><h2>Actor dynamics</h2><p>Showing " (h (count sorted-actors)) " first-party actor snapshots, scored as energy-flow proxies.</p>"
                   "<p><strong>Total score:</strong> " (h (str (Math/round (* 10.0 total-score)) "/100")) " · "
                   "<strong>Average:</strong> " (h (str (round1 avg-score) "/10")) "</p></section>"
                   "<section class=\"grid\">" (apply str (map actor-summary-card sorted-actors)) "</section>"
                   "<section class=\"card\"><h2>Boundary Conditions</h2><ul class=\"constraints\">"
                   (apply str (map #(str "<li>" (h %) "</li>") constraints))
                   "</ul></section>")]
     (shell/page-html
      {:title "System Dynamics · etzhayyim"
       :lang "en"
       :description "System dynamics stock/flow and feedback-loop view of etzhayyim and its actors."
       :active "/system-dynamics"
       :main main
       :footer-html "Rendered from <code>did_web/system_dynamics.cljc</code>. Static HTML/SVG only: no script, no external assets, no cookies."}))))

(defn- round1 [x]
  (/ (Math/round (* 10.0 (double x))) 10.0))

(defn- actor-mode [{:keys [kind performer-type wasm-cid]}]
  (cond
    (= kind "entity-mirror")
    {:id :mirror
     :title "Mirror loop / 公共記録"
     :summary "Public facts enter as observations, normalize into a keyless mirror, and stay bounded by the no-impersonation rule."
     :work-label "Mirror"
     :work-verb "mirrors"}

    wasm-cid
    {:id :wasm
     :title "Local execution / content-addressed runtime"
     :summary "The actor's executable face is pinned by CID; reach comes from content-addressed code, not a hidden server."
     :work-label "WASM"
     :work-verb "executes"}

    (= performer-type "service")
    {:id :service
     :title "Service loop / substrate routing"
     :summary "Requests flow through service endpoints, stabilize into outputs, and feed the registry or proxy boundary."
     :work-label "Service"
     :work-verb "routes"}

    (= kind "tier-b")
    {:id :operator
     :title "Operator loop / 産霊"
     :summary "Operator identity, registry state, and public outputs reinforce each other when the actor stays legible."
     :work-label "Operator"
     :work-verb "operates"}

    :else
    {:id :scaffold
     :title "Scaffold loop / handle"
     :summary "A valid handle still gets a public shape: resolve, inspect, and keep the boundary explicit until richer state lands."
     :work-label "Scaffold"
     :work-verb "resolves"}))

(defn- actor-stocks [actor]
  (let [{:keys [handle did description source kind status performer-type ui-type
               primary-lexicon primary-schema service-count vm-count wasm-cid]}
        actor
        mode (actor-mode actor)
        source-label (case source
                       "kv" "materialized from KV"
                       "kotoba" "materialized from kotoba"
                       "compiled" "compiled fallback"
                       "derived")
        runtime-label (cond
                        wasm-cid (str "content-addressed runtime " wasm-cid)
                        (> service-count 0) (str service-count " service endpoint" (when (> service-count 1) "s"))
                        :else "scaffolded runtime")
        work-label (cond
                     primary-lexicon (str "lexicon " primary-lexicon)
                     primary-schema (str "schema " primary-schema)
                     :else "no primary lexicon/schema yet")
        reach-label (cond
                      (= kind "entity-mirror") "searchActors / mirror visibility"
                      (= ui-type "appview") "profile + appview presence"
                      :else "DID resolution + profile view")
        feedback-label (str "status " status " / adr " (count (:adr actor)) " entries")]
    [{:id :identity
      :label "Identity"
      :ja "同定"
      :x 96 :y 86
      :note (str handle " / did:web:etzhayyim.com:actor:" handle " / " source-label)}
     {:id :runtime
      :label "Runtime"
      :ja "実行"
      :x 332 :y 70
      :note runtime-label}
     {:id :work
      :label (mode :work-label)
      :ja "仕事"
      :x 554 :y 118
      :note work-label}
     {:id :reach
      :label "Reach"
      :ja "可視性"
      :x 626 :y 304
      :note reach-label}
     {:id :feedback
      :label "Feedback"
      :ja "応答"
      :x 406 :y 418
      :note feedback-label}
     {:id :boundary
      :label "Boundary"
      :ja "境界"
      :x 152 :y 386
      :note (str "no server-held key; " kind "; " performer-type "; " ui-type)}]))

(defn- actor-flows [actor]
  (let [mode (actor-mode actor)]
    [{:from :identity :to :runtime :label "resolves"}
     {:from :runtime :to :work :label (case (:id mode)
                                        :mirror "normalizes"
                                        :wasm "loads"
                                        :service "serves"
                                        :operator "executes"
                                        "scaffolds")}
     {:from :work :to :reach :label (case (:id mode)
                                      :mirror "mirrors"
                                      :wasm "publishes"
                                      :service "routes"
                                      :operator "projects"
                                      "exposes")}
     {:from :reach :to :feedback :label "observes"}
     {:from :feedback :to :boundary :label "stabilizes"}
     {:from :boundary :to :identity :label "reasserts"}]))

(defn- actor-diagram-svg [actor]
  (let [nodes (actor-stocks actor)
        flows (actor-flows actor)
        index (into {} (map (juxt :id identity) nodes))]
    (str "<svg class=\"diagram\" viewBox=\"0 0 740 500\" role=\"img\" aria-label=\"actor system dynamics diagram\">"
         "<defs><marker id=\"arrow-actor\" markerWidth=\"10\" markerHeight=\"10\" refX=\"8\" refY=\"3\" orient=\"auto\"><path d=\"M0,0 L8,3 L0,6 Z\" fill=\"currentColor\" opacity=\".72\"/></marker></defs>"
         "<rect class=\"boundary\" x=\"26\" y=\"32\" width=\"688\" height=\"428\" rx=\"14\"/>"
         "<text class=\"boundary-label\" x=\"46\" y=\"58\">" (h (str (:handle actor) " public actor boundary")) "</text>"
         (apply str
                (map (fn [{:keys [from to label]}]
                       (let [{x1 :x y1 :y} (get index from)
                             {x2 :x y2 :y} (get index to)
                             mx (/ (+ x1 x2) 2)
                             my (/ (+ y1 y2) 2)]
                         (str "<path class=\"flow\" d=\"M" x1 " " y1 " L" x2 " " y2 "\" marker-end=\"url(#arrow-actor)\"/>"
                              "<text class=\"flow-label\" x=\"" mx "\" y=\"" (- my 8) "\">" (h label) "</text>")))
                     flows))
         (apply str (map stock-node nodes))
         "</svg>")))

(defn- actor-loop-card [title kind description]
  (str "<article class=\"card\"><h2>" (h title) "</h2>"
       "<p><span class=\"tag\">" (h kind) "</span></p>"
       "<p>" (h description) "</p></article>"))

(defn actor-page-html
  [{:keys [handle did display-name description kind status source performer-type ui-type
           glyph primary-lexicon primary-schema service-count vm-count wasm-cid adr
           service-types flow-score flow-source flow-proxy]
    :as actor}]
  (let [mode (actor-mode actor)
        title (or display-name handle)
        services (cond
                   wasm-cid (str "WASM + " service-count " service endpoint" (when (> service-count 1) "s"))
                   (> service-count 0) (str service-count " service endpoint" (when (> service-count 1) "s"))
                   :else "no service endpoints yet")
        vm-text (str vm-count " verification method" (when (not= vm-count 1) "s"))
        adr-text (if (seq adr) (str/join " · " adr) "none")
        service-tags (if (seq service-types)
                       (apply str (map #(str "<span class=\"tag\">" (h %) "</span>") service-types))
                       "<span class=\"tag\">none</span>")
        tags (remove nil?
                     [(when glyph (str "<span class=\"tag\">" (h glyph) "</span>"))
                      (when kind (str "<span class=\"tag\">" (h kind) "</span>"))
                      (when source (str "<span class=\"tag\">" (h source) "</span>"))
                      (when performer-type (str "<span class=\"tag\">" (h performer-type) "</span>"))
                      (when ui-type (str "<span class=\"tag\">" (h ui-type) "</span>"))])
        score-pct (Math/max 0 (Math/min 100 (Math/round (* 10 (double (or flow-score 0))))))
        loop-cards [(actor-loop-card (:title mode) "reinforcing" (:summary mode))
                    (actor-loop-card "Boundary / no-server-key"
                                     "balancing"
                                     (str "The actor stays inside the charter boundary: no server-held key, no hidden impersonation, and no unbounded authority. Source = " source ", status = " status "."))
                    (actor-loop-card "Repair / drift control"
                                     "balancing"
                                     (str "ADR coverage " adr-text ", services " services ", vm " vm-text ", primary surface " (or primary-lexicon primary-schema "none") "."))]
        main (str "<p class=\"eyebrow\">actor-specific system dynamics</p><h1>" (h title) "</h1>"
                  "<p class=\"lead\">" (h (or description "No actor description available yet.")) "</p>"
                  "<p class=\"next\"><strong>Role lens:</strong> " (h (:title mode)) ".</p>"
                  "<div class=\"grid\">"
                  "<div class=\"card\"><h2>Identity</h2><p>" (h handle) "</p><p class=\"tag-row\">" (apply str tags) "</p></div>"
                  "<div class=\"card\"><h2>Runtime</h2><p>" (h services) "</p><p>" (h (str "source " source " · status " status " · vm " vm-text)) "</p><p>" service-tags "</p></div>"
                  "<div class=\"card\"><h2>Surface</h2><p>" (h (or primary-lexicon primary-schema "none")) "</p><p>" (h (str "performer " performer-type " · ui " ui-type " · adr " adr-text)) "</p></div>"
                  "</div>"
                  "<section class=\"card\"><h2>Energy flow</h2><div class=\"actor-flow-head\"><strong>Flow score</strong><span>" (h (str (or flow-score 0) "/10")) "</span></div><div class=\"scorebar\"><span style=\"width:" score-pct "%\"></span></div><p class=\"actor-flow-note\">" (h (or flow-source "runtime + surface proxy")) "</p></section>"
                  (actor-diagram-svg actor)
                  "<section class=\"grid\">" (apply str loop-cards) "</section>"
                  "<section class=\"card\"><h2>Boundary Conditions</h2><ul class=\"constraints\">"
                  (apply str
                         (map #(str "<li>" (h %) "</li>")
                              [did
                               (str "profile handle " handle ".etzhayyim.com")
                               (str "source: " source)
                               (str "services: " services)
                               "no server-held key"
                               "no external assets"
                               "no cookies"]))
                  "</ul></section>")]
    (shell/page-html
     {:title (str (h title) " · actor dynamics · etzhayyim")
      :lang "en"
      :description (str "Actor-specific system dynamics for etzhayyim handle " (h handle))
      :active "/actors"
      :main main
      :footer-html "Rendered from <code>did_web/system_dynamics.cljc</code>. Actor page is static HTML/SVG only; it reflects the actor record, not a live runtime."})))
