(ns yoro-ui.shell.header
  "Top header bar — YORO logo + auth status + compose FAB."
  (:require [re-frame.core :as rf]
            [yoro-ui.router :as router]
            [yoro-ui.components.header-yoro-animation :refer [header-yoro-animation]]
            [yoro-ui.components.streak-badge :refer [streak-badge]]))

(defn- compose-btn []
  [:button {:class    "w-8 h-8 flex items-center justify-center rounded-full bg-[#1CB0F6] text-white shadow-md hover:bg-[#1CB0F6]/90 active:scale-95 transition-transform touch-manipulation"
            :aria-label "投稿を作成"
            :on-click #(rf/dispatch [:composer/open])}
   [:svg {:width 16 :height 16 :viewBox "0 0 24 24" :fill "none" :stroke "currentColor" :stroke-width 2.5}
    [:path {:d "M12 5v14M5 12h14"}]]])

(defn- auth-area []
  (let [signed-in?   @(rf/subscribe [:auth/signed-in?])
        display-name @(rf/subscribe [:auth/display-name])
        avatar       @(rf/subscribe [:auth/avatar])]
    (if signed-in?
      [:div {:class "flex items-center gap-2"}
       [compose-btn]
       [:button {:class    "flex items-center gap-2 touch-manipulation"
                 :on-click #(router/navigate! "/profile")}
        (if avatar
          [:img {:src avatar :class "w-8 h-8 rounded-full object-cover"}]
          [:div {:class "w-8 h-8 rounded-full bg-[#1CB0F6] flex items-center justify-center text-white text-[13px] font-bold"}
           (first (or display-name "?"))])]]
      [:button {:class    "px-3 py-1.5 rounded-xl bg-[#1CB0F6] text-white text-[13px] font-bold hover:opacity-90 active:translate-y-px touch-manipulation"
                :on-click #(rf/dispatch [:auth-modal/open])}
       "ログイン"])))

(defn app-header []
  [:header {:class "sticky top-0 z-40 bg-[var(--gv2-bg-primary,#0a0a0a)]/95 backdrop-blur-sm border-b border-gv2-border"
            :style {:padding-top "env(safe-area-inset-top)"}}
   [:div {:class "flex items-center justify-between px-4 h-14"}
    ;; Logo
    [:div {:class "flex items-center gap-1 cursor-pointer"
           :on-click #(router/navigate! "/")}
     [:span {:class "text-[20px] font-black text-gv2-text-primary tracking-tight"} "YORO"]
     [header-yoro-animation {:class "text-[16px]"}]]

    ;; Right side: streak + auth
    [:div {:class "flex items-center gap-3"}
     [streak-badge {:class "scale-90"}]
     [auth-area]]]])
