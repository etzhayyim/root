(ns yoro-ui.pages.convo
  "Convo (DM) list page — port of svelte routes/convo/+page.svelte."
  (:require [reagent.core :as r]
            [re-frame.core :as rf]
            [yoro-ui.router :as router]
            [yoro-ui.components.post-card :refer [avatar]]))

(defn- relative-time [iso-str]
  (when iso-str
    (let [now (.now js/Date)
          then (try (.-getTime (js/Date. iso-str)) (catch js/Error _ now))
          diff-ms (- now then)
          diff-m (/ diff-ms 60000)
          diff-h (/ diff-m 60)
          diff-d (/ diff-h 24)]
      (cond
        (< diff-m 1) "今"
        (< diff-m 60) (str (js/Math.floor diff-m) "分")
        (< diff-h 24) (str (js/Math.floor diff-h) "時間")
        :else (str (js/Math.floor diff-d) "日")))))

(defn- convo-row [{:keys [id members last-message unread-count muted]}]
  (let [peer (first (remove #(= (:did %) @(rf/subscribe [:auth/did])) members))
        display-name (or (:displayName peer) (:handle peer) "Unknown")
        last-text (get-in last-message [:message :text] "")]
    [:div {:class "flex items-center gap-3 px-4 py-3 border-b border-gv2-border/40 hover:bg-gv2-bg-card/30 cursor-pointer"
           :on-click #(router/navigate! (str "/convo/" id))}
     [avatar {:src (:avatar peer)
              :display-name display-name
              :size 48}]
     [:div {:class "flex-1 min-w-0"}
      [:div {:class "flex items-center justify-between"}
       [:span {:class "font-bold text-[14px] text-gv2-text-primary truncate"}
        display-name]
       [:span {:class "text-[11px] text-gv2-text-muted flex-shrink-0 ml-2"}
        (relative-time (get-in last-message [:message :sentAt]))]]
      [:div {:class "flex items-center justify-between mt-0.5"}
       [:p {:class "text-[13px] text-gv2-text-muted truncate"}
        (or last-text "メッセージなし")]
       (when (pos? (or unread-count 0))
         [:span {:class "flex-shrink-0 ml-2 min-w-[18px] h-[18px] rounded-full bg-[#1CB0F6] text-white text-[11px] font-bold flex items-center justify-center px-1"}
          (str unread-count)])]]]))

(defn- skeleton-row []
  [:div {:class "flex items-center gap-3 px-4 py-3 border-b border-gv2-border/40"}
   [:div {:class "w-12 h-12 rounded-full bg-gv2-border/40 animate-pulse flex-shrink-0"}]
   [:div {:class "flex-1"}
    [:div {:class "h-3 bg-gv2-border/40 rounded w-1/3 mb-2 animate-pulse"}]
    [:div {:class "h-3 bg-gv2-border/40 rounded w-2/3 animate-pulse"}]]])

(defn convo-list-page []
  (r/create-class
   {:display-name "convo-list-page"

    :component-did-mount
    (fn [_]
      (when (empty? @(rf/subscribe [:convos/list]))
        (rf/dispatch [:convos/refresh])))

    :reagent-render
    (fn []
      (let [convos @(rf/subscribe [:convos/list])
            loading? @(rf/subscribe [:convos/is-loading?])
            signed-in? @(rf/subscribe [:auth/signed-in?])]
        [:div {:class "flex flex-col"}

         ;; Header
         [:div {:class "px-4 py-3 border-b border-gv2-border flex items-center justify-between sticky top-0 z-10 bg-gv2-bg-base"}
          [:h2 {:class "text-[17px] font-bold text-gv2-text-primary"} "メッセージ"]
          [:button {:class "text-[#1CB0F6] font-semibold text-[14px]"} "新規作成"]]

         (cond
           (not signed-in?)
           [:div {:class "flex flex-col items-center justify-center py-20 text-center px-6"}
            [:div {:class "text-5xl mb-4"} "💬"]
            [:p {:class "text-[14px] text-gv2-text-muted"} "メッセージを見るにはサインインが必要です"]]

           (and loading? (empty? convos))
           (for [i (range 5)] ^{:key i} [skeleton-row])

           (empty? convos)
           [:div {:class "flex flex-col items-center justify-center py-20 text-center px-6"}
            [:div {:class "text-5xl mb-4"} "✉️"]
            [:h3 {:class "text-[16px] font-bold text-gv2-text-primary mb-2"} "メッセージなし"]
            [:p {:class "text-[13px] text-gv2-text-muted"} "プロフィールからDMを送ってみよう"]]

           :else
           (for [c convos]
             ^{:key (:id c)} [convo-row c]))]))}))
