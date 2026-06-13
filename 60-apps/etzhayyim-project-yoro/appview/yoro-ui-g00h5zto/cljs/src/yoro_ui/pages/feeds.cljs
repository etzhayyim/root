(ns yoro-ui.pages.feeds
  "Custom feeds directory — stub page."
  (:require [re-frame.core :as rf]
            [yoro-ui.router :as router]))

(defn feeds-page []
  [:div {:class "flex flex-col pb-20"}
   [:div {:class "px-4 py-3 border-b border-gv2-border sticky top-0 z-10 bg-gv2-bg-base"}
    [:h2 {:class "text-[17px] font-bold text-gv2-text-primary"} "カスタムフィード"]]
   [:div {:class "flex flex-col items-center justify-center py-20 text-center px-6"}
    [:div {:class "text-5xl mb-4"} "📋"]
    [:h3 {:class "text-[16px] font-bold text-gv2-text-primary mb-2"}
     "カスタムフィード"]
    [:p {:class "text-[13px] text-gv2-text-muted mb-6"}
     "まだフォローしているカスタムフィードはありません"]
    [:button {:class    "px-4 py-2 rounded-xl bg-[#1CB0F6] text-white text-[13px] font-bold"
              :on-click #(router/navigate! "/")}
     "ホームに戻る"]]])
