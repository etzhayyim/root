(ns yoro-ui.shell.app
  "Top-level App component — wires header + page router + tab bar."
  (:require [re-frame.core :as rf]
            [yoro-ui.shell.header :refer [app-header]]
            [yoro-ui.shell.tab-bar :refer [tab-bar]]
            [yoro-ui.pages.home :refer [home-page]]
            [yoro-ui.pages.search :refer [search-page]]
            [yoro-ui.pages.convo :refer [convo-list-page]]
            [yoro-ui.pages.notifications :refer [notifications-page]]
            [yoro-ui.pages.convo-detail :refer [convo-detail-page]]
            [yoro-ui.pages.profile :refer [profile-page]]
            [yoro-ui.pages.feeds :refer [feeds-page]]
            [yoro-ui.pages.history :refer [history-page]]
            [yoro-ui.pages.credits :refer [credits-page]]
            [yoro-ui.pages.post-thread :refer [post-thread-page]]
            [yoro-ui.components.inference-consent :refer [inference-consent]]
            [yoro-ui.components.no-cookie-banner :refer [no-cookie-banner]]
            [yoro-ui.components.auth-modal :refer [auth-modal]]
            [yoro-ui.components.post-composer :refer [post-composer]]
            [yoro-ui.components.ambient-background :refer [ambient-background]]
            [yoro-ui.components.splash-screen :refer [splash-screen]]))

(defn- not-found-page [path]
  [:div {:class "flex flex-col items-center justify-center py-20 text-center px-6"}
   [:div {:class "text-5xl mb-4"} "🤔"]
   [:h2 {:class "text-[18px] font-bold text-gv2-text-primary mb-2"} "ページが見つかりません"]
   [:p {:class "text-[13px] text-gv2-text-muted font-mono"} (str "404 " path)]])

(rf/reg-event-fx
 :nav/back
 (fn [_ _]
   {:fx [[:dispatch [:router/navigate-to "/"]]]}))

(defn- page-content []
  (let [route  @(rf/subscribe [:router/route])
        params @(rf/subscribe [:router/params])]
    (case route
      :home           [home-page]
      :search         [search-page]
      :convo-list     [convo-list-page]
      :convo-detail   [convo-detail-page {:id (:convo-id params)}]
      :notifications  [notifications-page]
      :own-profile    [profile-page {:handle @(rf/subscribe [:auth/handle])}]
      :profile        [profile-page {:handle (:handle params)}]
      :feeds          [feeds-page]
      :history        [history-page]
      :credits        [credits-page]
      :post-thread    [post-thread-page {:handle (:handle params) :rkey (:rkey params)}]
      :not-found      [not-found-page (:path params)]
      [home-page])))  ; default → home

(defn app []
  [:div {:class "relative min-h-screen bg-gv2-bg-base text-gv2-text-primary overflow-hidden"}

   ;; Ambient background canvas — sits behind all content
   [:div {:class "fixed inset-0 pointer-events-none z-0"}
    [ambient-background]]

   ;; Main UI — above ambient layer
   [:div {:class "relative z-10"}
    [app-header]

    ;; Main scrollable content, padded for bottom tab bar
    [:main {:class "pb-20"}
     [page-content]]

    [tab-bar]]

   ;; Overlays (above everything)
   [auth-modal]
   [post-composer]
   [inference-consent]
   [no-cookie-banner]

   ;; Splash screen — topmost, dismissed after 2.5 s
   [splash-screen]])
