(ns yoro-ui.shell.header
  "Top header bar — YORO logo + auth status + menu."
  (:require [re-frame.core :as rf]
            [yoro-ui.router :as router]
            [yoro-ui.components.header-yoro-animation :refer [header-yoro-animation]]
            [yoro-ui.components.streak-badge :refer [streak-badge]]))

(defn- auth-area []
  (let [signed-in? @(rf/subscribe [:auth/signed-in?])
        display-name @(rf/subscribe [:auth/display-name])
        avatar @(rf/subscribe [:auth/avatar])
        handle @(rf/subscribe [:auth/handle])]
    (if signed-in?
      [:button {:class "flex items-center gap-2 touch-manipulation"
                :on-click #(router/navigate! "/profile")}
       (if avatar
         [:img {:src avatar :class "w-8 h-8 rounded-full object-cover"}]
         [:div {:class "w-8 h-8 rounded-full bg-[#1CB0F6] flex items-center justify-center text-white text-[13px] font-bold"}
          (first (or display-name "?"))])]
      [:button {:class "px-3 py-1.5 rounded-xl bg-[#1CB0F6] text-white text-[13px] font-bold hover:opacity-90 active:translate-y-px touch-manipulation"}
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
