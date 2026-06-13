(ns yoro-ui.state.search
  "Search state — actor + post search via AT Protocol XRPC + etzhayyim actor registry."
  (:require [re-frame.core :as rf]
            [yoro-ui.kotoba.actor :as kactor]))

(def page-size 50)

(rf/reg-sub :search/query (fn [db _] (get-in db [:search :query] "")))
(rf/reg-sub :search/tab (fn [db _] (get-in db [:search :tab] :actors)))
(rf/reg-sub :search/actors (fn [db _] (get-in db [:search :actors] [])))
(rf/reg-sub :search/posts (fn [db _] (get-in db [:search :posts] [])))
(rf/reg-sub :search/loading? (fn [db _] (get-in db [:search :loading?] false)))
(rf/reg-sub :search/actor-cursor (fn [db _] (get-in db [:search :actor-cursor])))
(rf/reg-sub :search/end? (fn [db _] (get-in db [:search :end?] false)))

(rf/reg-event-db
 :search/set-tab
 (fn [db [_ tab]] (assoc-in db [:search :tab] tab)))

(rf/reg-event-db
 :search/set-query
 (fn [db [_ q]] (assoc-in db [:search :query] q)))

(rf/reg-event-fx
 :search/run
 (fn [{:keys [db]} [_ q]]
   (let [tab (get-in db [:search :tab] :actors)]
     {:db (-> db
              (assoc-in [:search :query] q)
              (assoc-in [:search :actors] [])
              (assoc-in [:search :posts] [])
              (assoc-in [:search :actor-cursor] nil)
              (assoc-in [:search :end?] false)
              (assoc-in [:search :loading?] true))
      :dispatch (if (= tab :actors)
                  [:search/fetch-actors q nil]
                  [:search/fetch-posts q])})))

(rf/reg-event-fx
 :search/load-more-actors
 (fn [{:keys [db]} _]
   (let [q (get-in db [:search :query])
         cursor (get-in db [:search :actor-cursor])
         loading? (get-in db [:search :loading?])
         end? (get-in db [:search :end?])]
     (if (or loading? end? (nil? cursor) (empty? q))
       {}
       {:db (assoc-in db [:search :loading?] true)
        :dispatch [:search/fetch-actors q cursor]}))))

(rf/reg-event-fx
 :search/fetch-actors
 (fn [_ [_ q cursor]]
   {:atproto/public-query
    {:nsid "app.bsky.actor.searchActors"
     :params (cond-> {:q q :limit page-size}
               cursor (assoc :cursor cursor))
     :on-success [:search/actors-success (nil? cursor)]
     :on-failure [:search/failure]}}))

(rf/reg-event-fx
 :search/actors-success
 (fn [{:keys [db]} [_ first-page? resp]]
   (let [actors (or (:actors resp) [])
         cursor (:cursor resp)]
     {:db (-> db
              (update-in [:search :actors]
                         (if first-page? (constantly actors) into) actors)
              (assoc-in [:search :actor-cursor] cursor)
              (assoc-in [:search :end?] (nil? cursor))
              (assoc-in [:search :loading?] false))})))

(rf/reg-event-fx
 :search/fetch-posts
 (fn [_ [_ q]]
   {:atproto/public-query
    {:nsid "app.bsky.feed.searchPosts"
     :params {:q q :limit 25 :sort "latest"}
     :on-success [:search/posts-success]
     :on-failure [:search/failure]}}))

(rf/reg-event-fx
 :search/posts-success
 (fn [{:keys [db]} [_ resp]]
   {:db (-> db
            (assoc-in [:search :posts] (or (:posts resp) []))
            (assoc-in [:search :loading?] false))}))

(rf/reg-event-db
 :search/failure
 (fn [db _]
   (assoc-in db [:search :loading?] false)))

;; ---------------------------------------------------------------------------
;; etzhayyim actor registry — fetched once from /actors.json

(rf/reg-fx
 :http/get-json
 (fn [{:keys [url on-success on-failure]}]
   (-> (js/fetch url)
       (.then (fn [^js r]
                (if (.-ok r)
                  (.json r)
                  (throw (js/Error. (str "HTTP " (.-status r)))))))
       (.then (fn [data]
                (rf/dispatch (conj on-success (js->clj data :keywordize-keys true)))))
       (.catch (fn [err]
                 (when on-failure
                   (rf/dispatch (conj on-failure (.-message err)))))))))

(rf/reg-event-fx
 :etzhayyim/load-actors
 (fn [{:keys [db]} _]
   (if (seq (get-in db [:etzhayyim :actors]))
     {}
     {:http/get-json {:url        "/actors.json"
                      :on-success [:etzhayyim/actors-loaded]}})))

(rf/reg-event-db
 :etzhayyim/actors-loaded
 (fn [db [_ actors]]
   (assoc-in db [:etzhayyim :actors] (vec actors))))

(rf/reg-sub
 :etzhayyim/actors-all
 (fn [db _] (get-in db [:etzhayyim :actors] [])))

(rf/reg-sub
 :etzhayyim/actors-filtered
 :<- [:etzhayyim/actors-all]
 :<- [:search/query]
 (fn [[actors q] _]
   (if (empty? q)
     actors
     (let [lq (clojure.string/lower-case q)]
       (filter (fn [a]
                 (or (clojure.string/includes? (clojure.string/lower-case (or (:displayName a) "")) lq)
                     (clojure.string/includes? (clojure.string/lower-case (or (:handle a) "")) lq)
                     (clojure.string/includes? (clojure.string/lower-case (or (:description a) "")) lq)))
               actors)))))

;; ---------------------------------------------------------------------------
;; etzhayyim actor profile — kotoba datom pull
;;
;; Load path:
;;   1. Check local datom log for eid → return immediately if present
;;   2. Else fetch /actor/{shortname}/profile.json → ingest datoms → pull entity
;;   The DISPLAY always comes from the local datom log (kotoba pull pattern).

(rf/reg-event-fx
 :ez-actor/load-profile
 (fn [{:keys [db]} [_ handle]]
   (let [shortname (kactor/handle->shortname handle)
         eid       (str "did:web:etzhayyim.com:actor:" shortname)
         existing  (kactor/pull-entity eid)]
     (if (seq existing)
       ;; already in local datom log — surface straight to db
       {:db (-> db
                (assoc-in [:ez-actor handle :loading] false)
                (assoc-in [:ez-actor handle :entity] existing))}
       ;; not yet ingested — fetch profile.json → datoms → log → db
       {:db (assoc-in db [:ez-actor handle :loading] true)
        :http/get-json {:url        (str "/actor/" shortname "/profile.json")
                        :on-success [:ez-actor/profile-fetched handle]
                        :on-failure [:ez-actor/profile-fetch-failed handle]}}))))

(rf/reg-event-db
 :ez-actor/profile-fetched
 (fn [db [_ handle profile]]
   (let [eid (or (when (seq (:did profile)) (:did profile))
               (str "did:web:etzhayyim.com:actor:" (kactor/handle->shortname handle)))]
     ;; Synchronous ingest into localStorage-backed datom log, then pull
     (kactor/ingest-profile! profile)
     (let [entity (kactor/pull-entity eid)]
       (-> db
           (assoc-in [:ez-actor handle :loading] false)
           (assoc-in [:ez-actor handle :entity] entity))))))

(rf/reg-event-db
 :ez-actor/profile-fetch-failed
 (fn [db [_ handle err]]
   (-> db
       (assoc-in [:ez-actor handle :loading] false)
       (assoc-in [:ez-actor handle :error] (str err)))))

(rf/reg-sub
 :ez-actor/profile-loading?
 (fn [db [_ handle]] (get-in db [:ez-actor handle :loading] false)))

(rf/reg-sub
 :ez-actor/profile-error
 (fn [db [_ handle]] (get-in db [:ez-actor handle :error])))

(rf/reg-sub
 :ez-actor/profile
 (fn [db [_ handle]] (get-in db [:ez-actor handle :entity])))
