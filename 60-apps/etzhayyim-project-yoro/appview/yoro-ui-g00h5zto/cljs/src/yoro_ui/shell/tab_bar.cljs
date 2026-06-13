(ns yoro-ui.shell.tab-bar
  "Bottom tab bar — mirrors SuperAppTabBar / BottomNav from the Svelte app."
  (:require [re-frame.core :as rf]
            [yoro-ui.router :as router]))

(def tabs
  [{:key :home   :path "/"            :label "ホーム"   :icon "🏠"}
   {:key :search :path "/search"      :label "検索"     :icon "🔍"}
   {:key :convo  :path "/convo"       :label "DM"       :icon "💬"}
   {:key :notifs :path "/notifications" :label "通知"   :icon "🔔"}
   {:key :profile :path "/profile"   :label "プロフィール" :icon "👤"}])

(defn- route->tab [route]
  (case route
    :home      :home
    :search    :search
    (:convo-list :convo-detail) :convo
    :notifications :notifs
    (:own-profile :profile) :profile
    :home))

(defn tab-bar []
  (let [route @(rf/subscribe [:router/route])]
    [:nav {:class "fixed bottom-0 inset-x-0 z-50 bg-[var(--gv2-bg-primary,#0a0a0a)] border-t border-gv2-border"
           :style {:box-shadow "0 -2px 8px rgba(0,0,0,0.1)"
                   :padding-bottom "env(safe-area-inset-bottom)"}}
     [:div {:class "flex items-stretch"}
      (for [{:keys [key path label icon]} tabs]
        ^{:key (name key)}
        (let [active? (= key (route->tab route))]
          [:button {:class (str "flex-1 flex flex-col items-center justify-center py-2 gap-0.5 "
                                "touch-manipulation transition-all duration-75 "
                                (if active?
                                  "text-[#1CB0F6]"
                                  "text-gv2-text-muted hover:text-gv2-text-primary"))
                    :on-click #(router/navigate! path)
                    :aria-label label
                    :aria-current (when active? "page")}
           [:span {:class (str "text-[22px] " (when active? "scale-110 transition-transform"))}
            icon]
           [:span {:class "text-[10px] font-semibold"} label]]))]]))
