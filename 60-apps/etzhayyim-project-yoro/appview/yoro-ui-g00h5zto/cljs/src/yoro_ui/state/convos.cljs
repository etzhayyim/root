(ns yoro-ui.state.convos
  (:require [re-frame.core :as rf]))

;; Since convos rely on the external @etzhayyim/signal logic,
;; we will define a basic wrapper interface using re-frame.
;; In a full port, the logic of $lib/atproto-agent and $lib/w
;; would be implemented via a CLJS interop layer.

(rf/reg-sub
  :convos/list
  (fn [db _]
    (get-in db [:convos :list] [])))

(rf/reg-sub
  :convos/active-id
  (fn [db _]
    (get-in db [:convos :active-id])))

(rf/reg-sub
  :convos/active
  (fn [db _]
    (get-in db [:convos :active])))

(rf/reg-sub
  :convos/active-records
  (fn [db _]
    (get-in db [:convos :active-records] [])))

(rf/reg-sub
  :convos/is-loading?
  (fn [db _]
    (get-in db [:convos :is-loading?] false)))

(rf/reg-sub
  :convos/direct-ids
  (fn [db _]
    (get-in db [:convos :direct-ids] [])))

(rf/reg-event-db
  :convos/set-active
  (fn [db [_ convo-id]]
    (assoc-in db [:convos :active-id] convo-id)))

(rf/reg-event-fx
  :convos/refresh
  (fn [{:keys [db]} _]
    ;; Stub for invoking refresh via interop or porting $lib/w
    {:db (assoc-in db [:convos :is-loading?] true)
     ;; simulate async load
     :dispatch-later [{:ms 500 :dispatch [:convos/refresh-done]}]}))

(rf/reg-event-db
  :convos/refresh-done
  (fn [db _]
    (assoc-in db [:convos :is-loading?] false)))
