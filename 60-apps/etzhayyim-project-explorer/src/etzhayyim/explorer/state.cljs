(ns etzhayyim.explorer.state
  "re-frame app-db: data fetching for the three views + a generic promise effect.

   db shape:
     {:route       :organism|:explorer|:nodes
      :resources   {<key> {:status :loading|:ok|:error, :data .., :error ..}}
      :live        {:on? bool, :events [..]}        ; libp2p Datom tail (R0)
      :chain       {:cid \"..\", :block {..}}}        ; explorer block inspector"
  (:require [re-frame.core :as rf]
            [clojure.string]
            [etzhayyim.explorer.data :as data]
            [etzhayyim.explorer.wire :as wire]
            [etzhayyim.explorer.chain.datom :as kdatom]
            [etzhayyim.explorer.chain.agent :as kagent]))

;; ── generic promise effect ──────────────────────────────────────────────────
;; {:promise {:call (fn [] js/Promise), :on-success [evt..], :on-failure [evt..]}}
(rf/reg-fx
 :promise
 (fn [{:keys [call on-success on-failure]}]
   (-> (call)
       (.then (fn [res] (rf/dispatch (conj on-success res))))
       (.catch (fn [err] (rf/dispatch (conj on-failure (.-message err))))))))

;; ── resource loading ────────────────────────────────────────────────────────
(rf/reg-event-fx
 :resource/load
 (fn [{:keys [db]} [_ key call]]
   {:db (assoc-in db [:resources key :status] :loading)
    :promise {:call call
              :on-success [:resource/ok key]
              :on-failure [:resource/error key]}}))

(rf/reg-event-db
 :resource/ok
 (fn [db [_ key res]]
   (update-in db [:resources key] merge {:status :ok :data res :error nil})))

(rf/reg-event-db
 :resource/error
 (fn [db [_ key msg]]
   (update-in db [:resources key] merge {:status :error :error msg})))

(rf/reg-sub
 :resource
 (fn [db [_ key]] (get-in db [:resources key])))

;; Convenience: load several named resources at once.
(rf/reg-event-fx
 :resources/ensure
 (fn [{:keys [db]} [_ specs]]
   ;; specs = [[key call] ...]; only (re)load ones not already :ok.
   {:fx (for [[key call] specs
              :when (not= :ok (get-in db [:resources key :status]))]
          [:dispatch [:resource/load key call]])}))

;; ── per-view bootstrap ──────────────────────────────────────────────────────
(def organism-resources
  [[:vitals      #(data/fetch-edn "/organism/vitals.kotoba.edn")]
   [:trajectory  #(data/fetch-json "/organism/trajectory.json")]
   [:pulse       #(data/fetch-json "/organism/pulse.json")]
   [:joucho      #(data/fetch-json "/organism/joucho.json")]
   [:health      #(data/fetch-json "/organism/health.json")]])

;; /nodes is built by QUERYING kotoba Datoms (ADR-2605312345), not the baked
;; organism.json: the living-cell mesh comes from the vitals EAVT snapshot, the
;; actor census from a kotoba Datom commit-log — both materialized + queried in
;; the browser.
(def nodes-resources
  [[:vitals      #(data/fetch-edn "/organism/vitals.kotoba.edn")]
   [:census-log  #(data/fetch-text "/kotoba/log/actor-census.kotoba.edn")]
   [:health      #(data/fetch-json "/organism/health.json")]])

;; The kotoba Datom log is the canonical state (ADR-2605312345); the explorer
;; fetches it as text and verifies/materializes it in-browser (chain.datom).
(def default-log "/kotoba/log/mimamori.kotoba.edn")

(def explorer-resources
  [[:root-ptr    #(data/root-pointer)]
   [:datom-log   #(data/fetch-text default-log)]])

(rf/reg-event-fx
 :organism/init
 (fn [_ _] {:dispatch [:resources/ensure organism-resources]}))

(rf/reg-event-fx
 :nodes/init
 (fn [_ _] {:fx [[:dispatch [:resources/ensure nodes-resources]]
                 [:dispatch [:registry/load]]]}))

(rf/reg-event-fx
 :explorer/init
 (fn [_ _] {:fx [[:dispatch [:resources/ensure explorer-resources]]
                 [:dispatch [:registry/load]]
                 [:dispatch [:wire/load-cells]]]}))

;; ── Transit (transit+json) query/sync wire — Datomic-client standard ────────
;; A Datom query RESPONSE fetched over the wire and decoded with transit-cljs
;; (keywords/types preserved). On-disk snapshots stay EDN; CID stays canon-JSON.
(rf/reg-event-fx
 :wire/load-cells
 (fn [{:keys [db]} _]
   (if (get-in db [:wire :cells])
     {}
     {:promise {:call #(wire/fetch-transit (data/url "/kotoba/wire/cells.transit.json"))
                :on-success [:wire/cells-ok]
                :on-failure [:wire/cells-err]}})))

(rf/reg-event-db
 :wire/cells-ok
 (fn [db [_ resp]] (assoc-in db [:wire :cells] resp)))

(rf/reg-event-db
 :wire/cells-err
 (fn [db [_ msg]] (assoc-in db [:wire :error] msg)))

(rf/reg-sub :wire (fn [db _] (:wire db)))

;; ── Holochain-iso agent registry: load the emergent MV, verify each agent's
;; self-published genesis source-chain in-browser (chain + ed25519 + membrane) ─
;; Load the emergent MV + the membrane context (roster + validator set), then
;; independently re-verify each agent's vouch + quorum in-browser.
(rf/reg-event-fx
 :registry/load
 (fn [{:keys [db]} _]
   (if (get-in db [:registry :mv])
     {}
     {:promise {:call #(js/Promise.all
                        #js [(data/fetch-edn "/kotoba/agents/registry-mv.kotoba.edn")
                             (data/fetch-edn "/kotoba/agents/member-roster.kotoba.edn")
                             (data/fetch-edn "/kotoba/agents/validator-set.kotoba.edn")])
                :on-success [:registry/loaded]
                :on-failure [:registry/mv-err]}})))

(rf/reg-event-fx
 :registry/loaded
 (fn [{:keys [db]} [_ [mv roster vset]]]
   (let [roster-set (set (:roster/members roster))
         validators (set (map :did (:validators/set vset)))]
     {:db (assoc db :registry {:mv mv :roster roster-set :validators validators :verified {}})
      :fx (for [{:keys [file]} (:mv/index mv)]
            [:dispatch [:registry/verify-agent file roster-set validators]])})))

(rf/reg-event-db
 :registry/mv-err
 (fn [db [_ msg]] (assoc-in db [:registry :error] msg)))

(rf/reg-event-fx
 :registry/verify-agent
 (fn [_ [_ file roster validators]]
   {:promise {:call #(-> (data/fetch-edn (str "/kotoba/agents/" file ".agent.kotoba.edn"))
                         (.then (fn [doc] (kagent/verify-doc doc {:roster roster :validators validators}))))
              :on-success [:registry/verified file]
              :on-failure [:registry/verify-err file]}}))

(rf/reg-event-db
 :registry/verified
 (fn [db [_ file result]] (assoc-in db [:registry :verified file] result)))

(rf/reg-event-db
 :registry/verify-err
 (fn [db [_ file msg]] (assoc-in db [:registry :verified file] {:error msg})))

(rf/reg-sub :registry (fn [db _] (:registry db)))

;; ── explorer block inspector ────────────────────────────────────────────────
(rf/reg-event-fx
 :chain/fetch-block
 (fn [{:keys [db]} [_ cid]]
   {:db (assoc db :chain {:cid cid :status :loading})
    :promise {:call #(data/block-bytes cid)
              :on-success [:chain/block-ok cid]
              :on-failure [:chain/block-error]}}))

(rf/reg-event-db
 :chain/block-ok
 (fn [db [_ cid bytes]]
   (assoc db :chain {:cid cid :status :ok :len (.-length bytes)})))

(rf/reg-event-db
 :chain/block-error
 (fn [db [_ msg]]
   (update db :chain merge {:status :error :error msg})))

(rf/reg-sub :chain (fn [db _] (:chain db)))

;; ── REAL kotoba Datom-log derivations (parse/verify/materialize in-browser) ──
;; Layer-3 subs over the fetched log text — memoized, recompute only when the
;; log changes. This is where the canonical kotoba.datom codec actually runs.
(rf/reg-sub
 :chain/txs
 :<- [:resource :datom-log]
 (fn [res _]
   (when (= :ok (:status res)) (kdatom/parse-log (:data res)))))

(rf/reg-sub
 :chain/verify
 :<- [:chain/txs]
 (fn [txs _] (when txs (kdatom/verify-chain txs))))

(rf/reg-sub
 :chain/eavt
 :<- [:chain/txs]
 (fn [txs _] (when txs (kdatom/materialize-eavt txs))))

(rf/reg-sub
 :chain/attributes
 :<- [:chain/txs]
 (fn [txs _] (when txs (kdatom/attributes txs))))

;; ── /nodes: living-cell mesh QUERIED from the vitals kotoba EAVT snapshot ────
(defn- green? [reflex]
  (= "green" (some-> reflex name clojure.string/lower-case)))

(defn- classify
  "Faithful port of etzhayyim.vitals/classify (the heartbeat's 生/休眠/死 rule)."
  [{:keys [reflex integrates bsky port-ratio]}]
  (cond
    (and (green? reflex) (pos? (or integrates 0)) bsky) "alive"
    (or (green? reflex) (pos? (or port-ratio 0)))       "dormant"
    :else                                               "stub"))

(defn- vitals->node
  "One materialized vitals entity → the node shape the mesh renders."
  [attrs]
  (let [reflex (get attrs :vitals.clj/reflex)
        integrates (get attrs :vitals.actor/integrates)
        bsky (get attrs :vitals.atproto/bsky-post)
        port-ratio (get attrs :vitals.clj/port-ratio)]
    {:id (get attrs :vitals.actor/name)
     :cells (or (get attrs :vitals.actor/cells) 0)
     :score (+ (or (get attrs :vitals.score/actor) 0)
               (or (get attrs :vitals.score/clj) 0)
               (or (get attrs :vitals.score/atproto) 0))
     :reflex (some-> reflex name)
     :inDeg (or (get attrs :vitals.actor/in-degree) 0)
     :outDeg (or integrates 0)
     :heartbeatDays (get attrs :vitals.bio/heartbeat-days)
     :status (get attrs :vitals.actor/status)
     :class (classify {:reflex reflex :integrates integrates
                       :bsky bsky :port-ratio port-ratio})}))

(rf/reg-sub
 :nodes/cells
 :<- [:resource :vitals]
 (fn [res _]
   (when (= :ok (:status res))
     (->> (kdatom/materialize-snapshot (:data res))
          vals
          (filter :vitals.actor/name)
          (map vitals->node)
          (sort-by :id)
          vec))))

(rf/reg-sub
 :nodes/summary
 :<- [:nodes/cells]
 (fn [cells _]
   (when cells
     (let [f (frequencies (map :class cells))]
       {:cells (count cells) :alive (get f "alive" 0)
        :dormant (get f "dormant" 0) :stub (get f "stub" 0)}))))

;; ── actor census, QUERIED from a kotoba Datom commit-log ────────────────────
(rf/reg-sub
 :census
 :<- [:resource :census-log]
 (fn [res _]
   (when (= :ok (:status res))
     (let [txs (kdatom/parse-log (:data res))
           eavt (kdatom/materialize-snapshot
                 (vec (mapcat (fn [tx]
                                (map (fn [[_op e a v]] [e a v (:tx/id tx) :add])
                                     (:tx/datoms tx)))
                              txs)))]
       ;; parse-log normalizes datom keywords to ":…" strings, so query by string
       {:verified (:ok (kdatom/verify-chain txs))
        :tiers (->> (kdatom/entities-where eavt ":census/tier")
                    (map (fn [[_ a]] {:tier (get a ":census/tier")
                                      :count (get a ":census/count")
                                      :source (get a ":census/source")}))
                    (sort-by :count >)
                    vec)}))))

;; query box state + result
(rf/reg-event-db
 :chain/set-query
 (fn [db [_ k v]] (assoc-in db [:chain-query k] v)))

(rf/reg-sub :chain-query (fn [db _] (:chain-query db {})))

(rf/reg-sub
 :chain/query-result
 :<- [:chain/txs]
 :<- [:chain-query]
 (fn [[txs q] _]
   (when (and txs (not (clojure.string/blank? (:attr q))))
     (kdatom/query txs {:attr (:attr q)
                        :value (when-not (clojure.string/blank? (:value q)) (:value q))}))))

;; ── live tail (libp2p Datom SSE, R0 progressive enhancement) ────────────────
(rf/reg-event-db
 :live/toggle
 (fn [db _] (update-in db [:live :on?] not)))

(rf/reg-event-db
 :live/event
 (fn [db [_ ev]]
   (update-in db [:live :events] (fnil #(->> (cons ev %) (take 50) vec) []))))

(rf/reg-sub :live (fn [db _] (:live db {:on? false :events []})))
