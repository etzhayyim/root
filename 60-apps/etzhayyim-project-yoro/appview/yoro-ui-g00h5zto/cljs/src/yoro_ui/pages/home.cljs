(ns yoro-ui.pages.home
  "Home / Vibes feed page — port of svelte/src/lib/superapp/VibesPanel.svelte."
  (:require [reagent.core :as r]
            [re-frame.core :as rf]
            [yoro-ui.components.post-card :refer [post-card post-skeleton]]))

(defn- empty-state []
  [:div {:class "flex flex-col items-center justify-center py-20 text-center px-6"}
   [:div {:class "text-5xl mb-4"} "🌱"]
   [:h3 {:class "text-[16px] font-bold text-gv2-text-primary mb-2"}
    "フィードを読み込み中..."]
   [:p {:class "text-[13px] text-gv2-text-muted"}
    "もう少しお待ちください"]])

(defn- error-state [err]
  [:div {:class "flex flex-col items-center justify-center py-20 text-center px-6"}
   [:div {:class "text-5xl mb-4"} "🌧️"]
   [:h3 {:class "text-[16px] font-bold text-gv2-text-primary mb-2"}
    "読み込みに失敗しました"]
   [:p {:class "text-[13px] text-gv2-text-muted mb-4"} (str err)]
   [:button {:class "px-4 py-2 rounded-xl bg-[#1CB0F6] text-white text-[13px] font-bold"
             :on-click #(rf/dispatch [:feed/refresh])}
    "再試行"]])

(defn home-page []
  (r/create-class
   {:display-name "home-page"

    :component-did-mount
    (fn [_]
      (let [posts @(rf/subscribe [:feed/posts])]
        (when (empty? posts)
          (rf/dispatch [:feed/load]))))

    :reagent-render
    (fn []
      (let [posts @(rf/subscribe [:feed/posts])
            loading? @(rf/subscribe [:feed/loading?])
            error @(rf/subscribe [:feed/error])
            end? @(rf/subscribe [:feed/end?])]
        [:div {:class "flex flex-col"}

         ;; Feed header tabs (Discover / Following)
         [:div {:class "flex border-b border-gv2-border sticky top-0 z-10 bg-gv2-bg-base"}
          [:button {:class "flex-1 py-3 text-[14px] font-bold text-[#1CB0F6] border-b-2 border-[#1CB0F6]"}
           "おすすめ"]
          [:button {:class "flex-1 py-3 text-[14px] font-semibold text-gv2-text-muted hover:text-gv2-text-primary"
                    :on-click #(rf/dispatch [:feed/load])}
           "フォロー中"]]

         ;; Posts
         (cond
           (and loading? (empty? posts))
           [:div
            (for [i (range 5)]
              ^{:key i} [post-skeleton])]

           error
           [error-state error]

           (empty? posts)
           [empty-state]

           :else
           [:div
            (for [post posts]
              ^{:key (:uri post)}
              [post-card post])

            ;; Load more trigger
            (cond
              loading?
              [:div {:class "py-6 text-center"}
               [:div {:class "inline-block w-5 h-5 border-2 border-[#1CB0F6] border-t-transparent rounded-full animate-spin"}]]

              end?
              [:div {:class "py-8 text-center text-[13px] text-gv2-text-muted"}
               "すべて表示しました"]

              :else
              [:button {:class "w-full py-4 text-[13px] text-[#1CB0F6] font-semibold hover:bg-gv2-bg-card/30"
                        :on-click #(rf/dispatch [:feed/load-more])}
               "さらに表示"])])]))}))
