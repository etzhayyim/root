(ns yoro-ui.state.hitl
  (:require [re-frame.core :as rf]))

(def hitl-token-key "etzhayyim:hitl-api-key")
(def poll-ms 10000)

(rf/reg-sub
  :hitl/pending
  (fn [db _]
    (get-in db [:hitl :pending] 0)))

(rf/reg-sub
  :hitl/pregel-pending
  (fn [db _]
    (get-in db [:hitl :pregel-pending] 0)))

(rf/reg-sub
  :hitl/token
  (fn [_ _]
    (if (exists? js/localStorage)
      (try (.getItem js/localStorage hitl-token-key)
           (catch js/Error _ ""))
      "")))

(defn- hitl-headers [token]
  (if (seq token)
    {"Content-Type" "application/json"
     "Authorization" (str "Bearer " token)}
    {"Content-Type" "application/json"}))

(rf/reg-event-db
  :hitl/set-counts
  (fn [db [_ pending pregel-pending]]
    (-> db
        (assoc-in [:hitl :pending] pending)
        (assoc-in [:hitl :pregel-pending] pregel-pending))))

(rf/reg-event-fx
  :hitl/poll
  (fn [{:keys [db]} _]
    (let [token (if (exists? js/localStorage)
                  (try (.getItem js/localStorage hitl-token-key)
                       (catch js/Error _ ""))
                  "")
          headers (hitl-headers token)]
      {:fx [[:dispatch [:hitl/do-fetch "/api/hitl/threads/search" headers :pending]]
            [:dispatch [:hitl/do-fetch "/api/pregel/threads/search" headers :pregel-pending]]]})))

(rf/reg-event-fx
  :hitl/do-fetch
  (fn [{:keys [db]} [_ url headers target-key]]
    ;; Basic fetch implementation for re-frame without http-fx
    ;; Usually we'd use cljs-ajax or re-frame-http-fx
    (let [abort-controller (js/AbortController.)
          signal (.-signal abort-controller)
          timeout-id (js/setTimeout #(.abort abort-controller) 5000)]
      (-> (js/fetch url
                    (clj->js {:method "POST"
                              :headers headers
                              :body (js/JSON.stringify (clj->js {:status "interrupted" :limit 50}))
                              :signal signal}))
          (.then (fn [res]
                   (js/clearTimeout timeout-id)
                   (if (or (not (.-ok res)) (= (.-status res) 401) (= (.-status res) 503))
                     (rf/dispatch [:hitl/fetch-success target-key 0])
                     (-> (.json res)
                         (.then (fn [list-data]
                                  (rf/dispatch [:hitl/fetch-success target-key (if (js/Array.isArray list-data) (.-length list-data) 0)])))))))
          (.catch (fn [_]
                    (js/clearTimeout timeout-id)
                    ;; silently keep last count
                    )))
      {})))

(rf/reg-event-db
  :hitl/fetch-success
  (fn [db [_ target-key count]]
    (assoc-in db [:hitl target-key] count)))

(defonce timer-id (atom nil))

(rf/reg-event-fx
  :hitl/start
  (fn [_ _]
    (when (and (exists? js/window) (not @timer-id))
      (rf/dispatch [:hitl/poll])
      (reset! timer-id (js/setInterval #(rf/dispatch [:hitl/poll]) poll-ms)))
    {}))

(rf/reg-event-fx
  :hitl/stop
  (fn [_ _]
    (when @timer-id
      (js/clearInterval @timer-id)
      (reset! timer-id nil))
    {}))
