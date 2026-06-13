(ns yoro-ui.pages.credits
  "Credits / moyai wallet — stub page (warifu R1)."
  (:require [re-frame.core :as rf]
            [yoro-ui.router :as router]))

(defn credits-page []
  (let [signed-in? @(rf/subscribe [:auth/signed-in?])]
    [:div {:class "flex flex-col pb-20"}
     [:div {:class "px-4 py-3 border-b border-gv2-border sticky top-0 z-10 bg-gv2-bg-base"}
      [:h2 {:class "text-[17px] font-bold text-gv2-text-primary"} "舫い / クレジット"]]
     (if signed-in?
       [:div {:class "flex flex-col items-center justify-center py-20 text-center px-6"}
        [:div {:class "text-5xl mb-4"} "⚓"]
        [:h3 {:class "text-[16px] font-bold text-gv2-text-primary mb-2"}
         "舫い (moyai) クレジット"]
        [:p {:class "text-[13px] text-gv2-text-muted mb-2"}
         "相互推論への貢献で non-monetary な信頼クレジットを獲得できます"]
        [:p {:class "text-[11px] text-gv2-text-muted"}
         "cash≡0 · non-transferable · decaying · governance-weight なし"]]
       [:div {:class "flex flex-col items-center justify-center py-20 text-center px-6"}
        [:div {:class "text-5xl mb-4"} "⚓"]
        [:p {:class "text-[14px] text-gv2-text-muted mb-4"}
         "クレジットを確認するにはサインインが必要です"]
        [:button {:class    "px-4 py-2 rounded-xl bg-[#1CB0F6] text-white text-[13px] font-bold"
                  :on-click #(rf/dispatch [:auth-modal/open])}
         "サインイン"]])]))
