(ns yoro-ui.shell.app
  "Top-level App component — wires header + page router + tab bar."
  (:require [re-frame.core :as rf]
            [yoro-ui.shell.header :refer [app-header]]
            [yoro-ui.shell.tab-bar :refer [tab-bar]]
            [yoro-ui.pages.home :refer [home-page]]
            [yoro-ui.pages.search :refer [search-page]]
            [yoro-ui.pages.convo :refer [convo-list-page]]
            [yoro-ui.pages.profile :refer [profile-page]]
            [yoro-ui.components.inference-consent :refer [inference-consent]]
            [yoro-ui.components.no-cookie-banner :refer [no-cookie-banner]]))

(defn- not-found-page [path]
  [:div {:class "flex flex-col items-center justify-center py-20 text-center px-6"}
   [:div {:class "text-5xl mb-4"} "🤔"]
   [:h2 {:class "text-[18px] font-bold text-gv2-text-primary mb-2"} "ページが見つかりません"]
   [:p {:class "text-[13px] text-gv2-text-muted font-mono"} (str "404 " path)]])

(defn- notifications-page []
  [:div {:class "flex flex-col items-center justify-center py-20 text-center px-6"}
   [:div {:class "text-5xl mb-4"} "🔔"]
   [:h2 {:class "text-[16px] font-bold text-gv2-text-primary mb-2"} "通知"]
   [:p {:class "text-[13px] text-gv2-text-muted"} "準備中 — 近日公開予定"]])

(defn- page-content []
  (let [route @(rf/subscribe [:router/route])
        params @(rf/subscribe [:router/params])]
    (case route
      :home           [home-page]
      :search         [search-page]
      :convo-list     [convo-list-page]
      :notifications  [notifications-page]
      :own-profile    [profile-page {:handle @(rf/subscribe [:auth/handle])}]
      :profile        [profile-page {:handle (:handle params)}]
      :not-found      [not-found-page (:path params)]
      [home-page])))  ; default → home

(defn app []
  [:div {:class "min-h-screen bg-gv2-bg-base text-gv2-text-primary"}
   [app-header]

   ;; Main scrollable content, padded for bottom tab bar
   [:main {:class "pb-20"}
    [page-content]]

   [tab-bar]
   [inference-consent]
   [no-cookie-banner]])
