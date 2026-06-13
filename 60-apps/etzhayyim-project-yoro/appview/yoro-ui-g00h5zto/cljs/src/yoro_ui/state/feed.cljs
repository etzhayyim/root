(ns yoro-ui.state.feed
  "Feed state — Vibes timeline + discover feed loading via AT Protocol XRPC.
   Candidate C topology: all XRPC to atproto.etzhayyim.com."
  (:require [re-frame.core :as rf]))

(def page-size 30)

;; ---------------------------------------------------------------------------
;; Subs

(rf/reg-sub :feed/posts (fn [db _] (get-in db [:feed :posts] [])))
(rf/reg-sub :feed/loading? (fn [db _] (get-in db [:feed :loading?] false)))
(rf/reg-sub :feed/error (fn [db _] (get-in db [:feed :error])))
(rf/reg-sub :feed/cursor (fn [db _] (get-in db [:feed :cursor])))
(rf/reg-sub :feed/end? (fn [db _] (get-in db [:feed :end?] false)))

;; Liked/reposted sets for optimistic UI
(rf/reg-sub :feed/liked-uris (fn [db _] (get-in db [:feed :liked-uris] #{})))
(rf/reg-sub :feed/reposted-uris (fn [db _] (get-in db [:feed :reposted-uris] #{})))

;; ---------------------------------------------------------------------------
;; Events

(rf/reg-event-db
 :feed/set-loading
 (fn [db [_ v]] (assoc-in db [:feed :loading?] v)))

(rf/reg-event-db
 :feed/set-posts
 (fn [db [_ posts cursor]]
   (-> db
       (assoc-in [:feed :posts] posts)
       (assoc-in [:feed :cursor] cursor)
       (assoc-in [:feed :loading?] false)
       (assoc-in [:feed :error] nil)
       (assoc-in [:feed :end?] (nil? cursor)))))

(rf/reg-event-db
 :feed/append-posts
 (fn [db [_ posts cursor]]
   (let [existing (get-in db [:feed :posts] [])
         seen-uris (into #{} (map :uri existing))
         fresh (remove #(seen-uris (:uri %)) posts)]
     (-> db
         (update-in [:feed :posts] into fresh)
         (assoc-in [:feed :cursor] cursor)
         (assoc-in [:feed :loading?] false)
         (assoc-in [:feed :end?] (nil? cursor))))))

(rf/reg-event-db
 :feed/set-error
 (fn [db [_ err]]
   (-> db
       (assoc-in [:feed :error] err)
       (assoc-in [:feed :loading?] false))))

(rf/reg-event-fx
 :feed/load
 (fn [{:keys [db]} _]
   (if (get-in db [:feed :loading?])
     {}
     {:db (-> db
              (assoc-in [:feed :loading?] true)
              (assoc-in [:feed :error] nil))
      :dispatch [:feed/fetch-timeline nil]})))

(rf/reg-event-fx
 :feed/load-more
 (fn [{:keys [db]} _]
   (let [cursor (get-in db [:feed :cursor])
         loading? (get-in db [:feed :loading?])
         end? (get-in db [:feed :end?])]
     (if (or loading? end? (nil? cursor))
       {}
       {:db (assoc-in db [:feed :loading?] true)
        :dispatch [:feed/fetch-timeline cursor]}))))

(rf/reg-event-fx
 :feed/refresh
 (fn [{:keys [db]} _]
   {:db (-> db
            (assoc-in [:feed :posts] [])
            (assoc-in [:feed :cursor] nil)
            (assoc-in [:feed :end?] false)
            (assoc-in [:feed :loading?] true))
    :dispatch [:feed/fetch-timeline nil]}))

(rf/reg-event-fx
 :feed/fetch-timeline
 (fn [{:keys [db]} [_ cursor]]
   (let [signed-in? (get-in db [:auth :session :did])
         ;; Use discover feed for signed-out users, timeline for signed-in
         nsid (if signed-in?
                "app.bsky.feed.getTimeline"
                "com.etzhayyim.yoro.feed.getDiscoverFeed")
         params (cond-> {:limit page-size}
                  cursor (assoc :cursor cursor))]
     {:atproto/query
      {:nsid nsid
       :params params
       :on-success [:feed/fetch-success (nil? cursor)]
       :on-failure [:feed/fetch-failure]}})))

(rf/reg-event-fx
 :feed/fetch-success
 (fn [_ [_ first-page? resp]]
   (let [items (or (:feed resp) [])
         posts (mapv (fn [item]
                       (let [post (:post item)
                             reason (:reason item)]
                         (merge {:uri (:uri post)
                                 :cid (:cid post)
                                 :author (get-in post [:author])
                                 :record (get-in post [:record])
                                 :like-count (get-in post [:likeCount] 0)
                                 :repost-count (get-in post [:repostCount] 0)
                                 :reply-count (get-in post [:replyCount] 0)
                                 :view-count (get-in post [:viewCount] 0)
                                 :indexed-at (get-in post [:indexedAt])}
                               (when reason
                                 {:reason-type (get-in reason [:$type])
                                  :reason-by (get-in reason [:by])}))))
                     items)
         cursor (:cursor resp)]
     {:dispatch (if first-page?
                  [:feed/set-posts posts cursor]
                  [:feed/append-posts posts cursor])})))

(rf/reg-event-fx
 :feed/fetch-failure
 (fn [_ [_ err]]
   {:dispatch [:feed/set-error (or err "フィードの読み込みに失敗しました")]}))

;; ---------------------------------------------------------------------------
;; Optimistic like / repost

(rf/reg-event-fx
 :feed/toggle-like
 (fn [{:keys [db]} [_ {:keys [uri cid]}]]
   (let [liked? (contains? (get-in db [:feed :liked-uris] #{}) uri)
         nsid (if liked? "app.bsky.feed.unlike" "app.bsky.feed.like")]
     {:db (if liked?
            (update-in db [:feed :liked-uris] disj uri)
            (update-in db [:feed :liked-uris] (fnil conj #{}) uri))
      :atproto/procedure
      {:nsid (if liked?
               "com.atproto.repo.deleteRecord"
               "com.atproto.repo.createRecord")
       :body (if liked?
               {:collection "app.bsky.feed.like" :rkey (last (clojure.string/split uri #"/"))}
               {:collection "app.bsky.feed.like"
                :record {:$type "app.bsky.feed.like"
                         :subject {:uri uri :cid cid}
                         :createdAt (.toISOString (js/Date.))}})
       :on-failure [:feed/like-failure uri liked?]}})))

(rf/reg-event-db
 :feed/like-failure
 (fn [db [_ uri was-liked?]]
   ;; revert optimistic update
   (if was-liked?
     (update-in db [:feed :liked-uris] (fnil conj #{}) uri)
     (update-in db [:feed :liked-uris] disj uri))))
