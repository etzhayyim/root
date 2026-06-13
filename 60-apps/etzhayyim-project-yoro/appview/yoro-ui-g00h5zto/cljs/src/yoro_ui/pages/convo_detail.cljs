(ns yoro-ui.pages.convo-detail
  "DM conversation detail view — chat.bsky.convo.getMessages / sendMessage."
  (:require [reagent.core :as r]
            [re-frame.core :as rf]))

;; ---------------------------------------------------------------------------
;; State

(rf/reg-sub :convo/current     (fn [db _] (get-in db [:convo :current])))
(rf/reg-sub :convo/messages    (fn [db _] (get-in db [:convo :messages] [])))
(rf/reg-sub :convo/loading?    (fn [db _] (get-in db [:convo :loading?] false)))
(rf/reg-sub :convo/sending?    (fn [db _] (get-in db [:convo :sending?] false)))

(rf/reg-event-fx
 :convo/load
 (fn [{:keys [db]} [_ convo-id]]
   {:db (-> db
            (assoc-in [:convo :loading?] true)
            (assoc-in [:convo :messages] [])
            (assoc-in [:convo :current-id] convo-id))
    :atproto/query {:nsid "chat.bsky.convo.getMessages"
                    :params {:convoId convo-id :limit 50}
                    :on-success [:convo/messages-loaded]
                    :on-failure [:convo/load-failed]}}))

(rf/reg-event-db
 :convo/messages-loaded
 (fn [db [_ {:keys [messages]}]]
   (-> db
       (assoc-in [:convo :loading?] false)
       (assoc-in [:convo :messages] (vec (reverse (or messages [])))))))

(rf/reg-event-db
 :convo/load-failed
 (fn [db [_ err]]
   (js/console.error "convo load failed" err)
   (assoc-in db [:convo :loading?] false)))

(rf/reg-event-fx
 :convo/send
 (fn [{:keys [db]} [_ {:keys [convo-id text]}]]
   {:db (assoc-in db [:convo :sending?] true)
    :atproto/procedure {:nsid "chat.bsky.convo.sendMessage"
                        :body {:convoId convo-id
                               :message {:text text}}
                        :on-success [:convo/message-sent]
                        :on-failure [:convo/send-failed]}}))

(rf/reg-event-db
 :convo/message-sent
 (fn [db [_ msg]]
   (-> db
       (assoc-in [:convo :sending?] false)
       (update-in [:convo :messages] conj msg))))

(rf/reg-event-db
 :convo/send-failed
 (fn [db [_ err]]
   (js/console.error "convo send failed" err)
   (assoc-in db [:convo :sending?] false)))

;; ---------------------------------------------------------------------------
;; Time formatting

(defn- fmt-time [^string iso]
  (when iso
    (let [d (js/Date. iso)]
      (str (.toString (.getHours d)) ":"
           (.padStart (.toString (.getMinutes d)) 2 "0")))))

;; ---------------------------------------------------------------------------
;; Message bubble

(defn- message-bubble [{:keys [text sender sentAt]} my-did]
  (let [is-mine? (= (get-in sender [:did]) my-did)]
    [:div {:class (str "flex mb-2 " (if is-mine? "justify-end" "justify-start"))}
     (when-not is-mine?
       (if-let [av (get-in sender [:avatar])]
         [:img {:src av :class "w-8 h-8 rounded-full mr-2 mt-1 flex-shrink-0"}]
         [:div {:class "w-8 h-8 rounded-full bg-[#1CB0F6] flex items-center justify-center text-white text-[11px] font-bold mr-2 mt-1 flex-shrink-0"}
          (first (or (get-in sender [:displayName]) "?"))]))
     [:div {:class "max-w-[70%]"}
      [:div {:class (str "px-3 py-2 rounded-2xl text-[14px] leading-relaxed "
                         (if is-mine?
                           "bg-[#1CB0F6] text-white rounded-br-sm"
                           "bg-gv2-bg-card text-gv2-text-primary rounded-bl-sm"))}
       (get-in (if (map? text) text {:text (str text)}) [:text] (str text))]
      [:p {:class (str "text-[10px] mt-0.5 text-gv2-text-muted "
                       (if is-mine? "text-right" "text-left"))}
       (fmt-time sentAt)]]]))

;; ---------------------------------------------------------------------------
;; Page component

(defn convo-detail-page [route-params]
  (let [convo-id (:id route-params)
        input    (r/atom "")]
    (r/create-class
     {:component-did-mount
      (fn [_]
        (when convo-id
          (rf/dispatch [:convo/load convo-id])))

      :reagent-render
      (fn [_]
        (let [messages @(rf/subscribe [:convo/messages])
              loading? @(rf/subscribe [:convo/loading?])
              sending? @(rf/subscribe [:convo/sending?])
              my-did   @(rf/subscribe [:auth/did])
              send!    (fn []
                         (let [txt (clojure.string/trim @input)]
                           (when (seq txt)
                             (rf/dispatch [:convo/send {:convo-id convo-id :text txt}])
                             (reset! input ""))))]
          [:div {:class "flex flex-col h-full"}

           ;; Header
           [:div {:class "flex items-center gap-3 px-4 py-3 border-b border-gv2-border sticky top-0 bg-gv2-bg-base z-10"}
            [:button {:class    "w-8 h-8 flex items-center justify-center rounded-full hover:bg-gv2-bg-card text-gv2-text-muted"
                      :on-click #(rf/dispatch [:nav/back])}
             [:svg {:width 20 :height 20 :viewBox "0 0 24 24" :fill "none" :stroke "currentColor" :stroke-width 2}
              [:path {:d "M19 12H5M12 5l-7 7 7 7"}]]]
            [:h2 {:class "text-[16px] font-bold text-gv2-text-primary"} "メッセージ"]]

           ;; Message list
           [:div {:class "flex-1 overflow-y-auto px-4 py-4 flex flex-col"}
            (cond
              loading?
              [:div {:class "flex justify-center py-8"}
               [:div {:class "w-6 h-6 border-2 border-[#1CB0F6] border-t-transparent rounded-full animate-spin"}]]

              (empty? messages)
              [:div {:class "flex flex-col items-center justify-center flex-1 text-center"}
               [:div {:class "text-4xl mb-3"} "💬"]
               [:p {:class "text-[13px] text-gv2-text-muted"} "まだメッセージはありません"]]

              :else
              (for [msg messages]
                ^{:key (or (:id msg) (:sentAt msg))}
                [message-bubble msg my-did]))]

           ;; Composer
           [:div {:class "flex items-end gap-2 px-4 py-3 border-t border-gv2-border bg-gv2-bg-base"}
            [:div {:class "flex-1 bg-gv2-bg-card rounded-2xl px-3 py-2.5 min-h-[40px] flex items-end"}
             [:textarea {:class       "flex-1 bg-transparent text-[14px] text-gv2-text-primary placeholder:text-gv2-text-muted resize-none outline-none max-h-[120px]"
                         :placeholder "メッセージを入力…"
                         :rows        1
                         :value       @input
                         :on-change   #(reset! input (.. % -target -value))
                         :on-key-down #(when (and (.-metaKey %) (= (.-key %) "Enter"))
                                         (send!))}]]
            [:button {:class    (str "w-9 h-9 flex items-center justify-center rounded-full flex-shrink-0 transition-colors "
                                     (if (and (seq @input) (not sending?))
                                       "bg-[#1CB0F6] text-white"
                                       "bg-gv2-bg-card text-gv2-text-muted cursor-not-allowed"))
                      :disabled (or (empty? @input) sending?)
                      :on-click send!}
             (if sending?
               [:div {:class "w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"}]
               [:svg {:width 18 :height 18 :viewBox "0 0 24 24" :fill "none" :stroke "currentColor" :stroke-width 2}
                [:path {:d "M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"}]])]]]))})))
