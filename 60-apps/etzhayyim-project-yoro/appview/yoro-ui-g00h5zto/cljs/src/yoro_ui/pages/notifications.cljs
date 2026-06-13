(ns yoro-ui.pages.notifications
  "Notifications page — app.bsky.notification.listNotifications."
  (:require [reagent.core :as r]
            [re-frame.core :as rf]
            [yoro-ui.state.notifications]))

(defn- notif-icon [reason]
  (case reason
    "like"      "❤️"
    "repost"    "🔁"
    "follow"    "👤"
    "mention"   "💬"
    "reply"     "↩️"
    "quote"     "🗣️"
    "🔔"))

(defn- notif-label [reason]
  (case reason
    "like"   "があなたの投稿をいいねしました"
    "repost" "があなたの投稿をリポストしました"
    "follow" "があなたをフォローしました"
    "mention" "があなたをメンションしました"
    "reply"  "が返信しました"
    "quote"  "があなたの投稿を引用しました"
    "が通知しました"))

(defn- notif-card [{:keys [reason author isRead indexedAt record]}]
  (let [display-name (or (get-in author [:displayName]) (get-in author [:handle]) "?")
        avatar       (get-in author [:avatar])]
    [:div {:class (str "flex items-start gap-3 px-4 py-3 border-b border-gv2-border "
                       (when-not isRead "bg-[#1CB0F6]/5"))}
     ;; Reason icon
     [:div {:class "text-[20px] w-6 flex-shrink-0 mt-0.5"}
      (notif-icon reason)]

     ;; Avatar + text
     [:div {:class "flex-1 min-w-0"}
      [:div {:class "flex items-center gap-2 mb-1"}
       (if avatar
         [:img {:src avatar :class "w-8 h-8 rounded-full object-cover flex-shrink-0"}]
         [:div {:class "w-8 h-8 rounded-full bg-[#1CB0F6] flex items-center justify-center text-white text-[11px] font-bold flex-shrink-0"}
          (first display-name)])
       [:span {:class "text-[13px] font-semibold text-gv2-text-primary truncate"}
        display-name]
       [:span {:class "text-[13px] text-gv2-text-muted"}
        (notif-label reason)]]

      ;; Post text snippet (if reply/mention/quote)
      (when-let [text (get-in record [:text])]
        [:p {:class "text-[12px] text-gv2-text-muted line-clamp-2 mt-0.5"}
         text])]

     ;; Time
     [:span {:class "text-[11px] text-gv2-text-muted flex-shrink-0 mt-0.5"}
      (when indexedAt
        (let [d (js/Date. indexedAt)
              now (js/Date.)
              diff-ms (- now d)
              diff-h  (/ diff-ms 3600000)]
          (cond
            (< diff-h 1)  (str (int (/ diff-ms 60000)) "分前")
            (< diff-h 24) (str (int diff-h) "時間前")
            :else         (str (int (/ diff-h 24)) "日前"))))]]))

(defn notifications-page []
  (r/with-let [_ (rf/dispatch [:notifs/fetch])]
    (let [signed-in? @(rf/subscribe [:auth/signed-in?])
          items      @(rf/subscribe [:notifs/items])
          loading?   @(rf/subscribe [:notifs/loading?])
          end?       @(rf/subscribe [:notifs/end?])]
      [:div {:class "flex flex-col"}

       ;; Header
       [:div {:class "flex items-center justify-between px-4 py-3 border-b border-gv2-border sticky top-0 z-10 bg-gv2-bg-base"}
        [:h2 {:class "text-[17px] font-bold text-gv2-text-primary"} "通知"]
        (when (seq items)
          [:button {:class "text-[13px] text-[#1CB0F6] font-semibold"
                    :on-click #(rf/dispatch [:notifs/mark-read])}
           "すべて既読"])]

       (cond
         ;; Not signed in
         (not signed-in?)
         [:div {:class "flex flex-col items-center justify-center py-20 text-center px-6"}
          [:div {:class "text-5xl mb-4"} "🔔"]
          [:p {:class "text-[14px] text-gv2-text-muted mb-4"} "通知を見るにはログインが必要です"]
          [:button {:class "px-6 py-2.5 bg-[#1CB0F6] text-white rounded-xl text-[14px] font-bold"}
           "ログイン"]]

         ;; Loading (first fetch)
         (and loading? (empty? items))
         [:div {:class "divide-y divide-gv2-border"}
          (for [i (range 8)]
            ^{:key i}
            [:div {:class "flex items-start gap-3 px-4 py-3"}
             [:div {:class "w-6 h-6 rounded bg-gv2-bg-card animate-pulse flex-shrink-0"}]
             [:div {:class "flex-1 space-y-2"}
              [:div {:class "h-3 bg-gv2-bg-card rounded animate-pulse w-3/4"}]
              [:div {:class "h-3 bg-gv2-bg-card rounded animate-pulse w-1/2"}]]])]

         ;; Empty
         (and (not loading?) (empty? items))
         [:div {:class "flex flex-col items-center justify-center py-20 text-center px-6"}
          [:div {:class "text-5xl mb-4"} "🔔"]
          [:p {:class "text-[14px] text-gv2-text-muted"} "通知はまだありません"]]

         ;; List
         :else
         [:div {:class "divide-y divide-gv2-border"}
          (for [n items]
            ^{:key (or (:uri n) (:indexedAt n))}
            [notif-card n])

          (cond
            loading?
            [:div {:class "py-4 text-center text-[13px] text-gv2-text-muted"} "読み込み中…"]

            (not end?)
            [:button {:class "w-full py-4 text-[13px] text-[#1CB0F6] font-semibold hover:bg-gv2-bg-card/30"
                      :on-click #(rf/dispatch [:notifs/load-more])}
             "さらに表示"]

            :else
            [:div {:class "py-6 text-center text-[12px] text-gv2-text-muted"} "すべて表示済み"])])])))
