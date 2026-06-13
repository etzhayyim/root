(ns yoro-ui.state.search
  "Search state — actor + post search via AT Protocol XRPC."
  (:require [re-frame.core :as rf]))

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
   {:atproto/query
    {:nsid "com.etzhayyim.yoro.actor.searchActors"
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
   {:atproto/query
    {:nsid "app.bsky.feed.searchPosts"
     :params {:q q :limit 25}
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
