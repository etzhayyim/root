(ns yoro-ui.pages.history
  "Browsing history — stub page (kotoba Datom log backed, R1)."
  (:require [re-frame.core :as rf]
            [yoro-ui.router :as router]))

(defn history-page []
  [:div {:class "flex flex-col pb-20"}
   [:div {:class "px-4 py-3 border-b border-gv2-border sticky top-0 z-10 bg-gv2-bg-base"}
    [:h2 {:class "text-[17px] font-bold text-gv2-text-primary"} "閲覧履歴"]]
   [:div {:class "flex flex-col items-center justify-center py-20 text-center px-6"}
    [:div {:class "text-5xl mb-4"} "🕐"]
    [:h3 {:class "text-[16px] font-bold text-gv2-text-primary mb-2"}
     "閲覧履歴"]
    [:p {:class "text-[13px] text-gv2-text-muted mb-2"}
     "閲覧した投稿はローカルの kotoba ログに記録されます"]
    [:p {:class "text-[11px] text-gv2-text-muted mb-6 font-mono"}
     (str "head: " @(rf/subscribe [:kotoba/head-cid]))]
    [:button {:class    "px-4 py-2 rounded-xl bg-[#1CB0F6] text-white text-[13px] font-bold"
              :on-click #(router/navigate! "/")}
     "ホームに戻る"]]])
