(ns yoro-ui.state.notifications
  "Notification state — app.bsky.notification.listNotifications + unread count."
  (:require [re-frame.core :as rf]
            [yoro-ui.interop.atproto :as at]))

(rf/reg-sub :notifs/items    (fn [db _] (get-in db [:notifs :items] [])))
(rf/reg-sub :notifs/loading? (fn [db _] (get-in db [:notifs :loading?] false)))
(rf/reg-sub :notifs/unread   (fn [db _] (get-in db [:notifs :unread] 0)))
(rf/reg-sub :notifs/end?     (fn [db _] (get-in db [:notifs :end?] false)))

(rf/reg-event-db
 :notifs/loaded
 (fn [db [_ {:keys [notifications cursor]}]]
   (-> db
       (assoc-in [:notifs :loading?] false)
       (update-in [:notifs :items] into (or notifications []))
       (assoc-in [:notifs :cursor] cursor)
       (assoc-in [:notifs :end?] (nil? cursor)))))

(rf/reg-event-db
 :notifs/unread-count
 (fn [db [_ n]] (assoc-in db [:notifs :unread] n)))

(rf/reg-event-fx
 :notifs/fetch
 (fn [{:keys [db]} _]
   {:db (-> db (assoc-in [:notifs :loading?] true)
               (assoc-in [:notifs :items] []))
    :atproto/query {:nsid "app.bsky.notification.listNotifications"
                    :params {:limit 50}
                    :on-success [:notifs/loaded]
                    :on-failure [:notifs/load-failed]}}))

(rf/reg-event-fx
 :notifs/load-more
 (fn [{:keys [db]} _]
   (let [cursor (get-in db [:notifs :cursor])]
     (when cursor
       {:db (assoc-in db [:notifs :loading?] true)
        :atproto/query {:nsid "app.bsky.notification.listNotifications"
                        :params {:limit 50 :cursor cursor}
                        :on-success [:notifs/loaded]
                        :on-failure [:notifs/load-failed]}}))))

(rf/reg-event-fx
 :notifs/fetch-unread
 (fn [_ _]
   {:atproto/query {:nsid "app.bsky.notification.getUnreadCount"
                    :on-success (fn [res] (rf/dispatch [:notifs/unread-count (or (:count res) 0)]))
                    :on-failure nil}}))

(rf/reg-event-fx
 :notifs/mark-read
 (fn [_ _]
   {:atproto/procedure {:nsid "app.bsky.notification.updateSeen"
                        :body {:seenAt (.toISOString (js/Date.))}
                        :on-success (fn [_] (rf/dispatch [:notifs/unread-count 0]))
                        :on-failure nil}}))

(rf/reg-event-db
 :notifs/load-failed
 (fn [db [_ err]]
   (js/console.error "notifs load failed" err)
   (assoc-in db [:notifs :loading?] false)))
