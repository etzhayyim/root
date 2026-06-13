(ns yoro-ui.shell.tab-bar
  "Bottom tab bar — SVG icons matching SuperAppTabBar design."
  (:require [re-frame.core :as rf]
            [yoro-ui.router :as router]
            [yoro-ui.interop.sound :as snd]))

;; ---------------------------------------------------------------------------
;; SVG icons — filled when active, outline when inactive

(defn- icon-home [active?]
  [:svg {:class "w-7 h-7" :viewBox "0 0 24 24"
         :fill (if active? "currentColor" "none")
         :stroke "currentColor"
         :stroke-width (if active? "0" "2")
         :stroke-linecap "round" :stroke-linejoin "round"}
   [:polygon {:points "5 3 19 12 5 21 5 3"}]])

(defn- icon-search [active?]
  [:svg {:class "w-7 h-7" :viewBox "0 0 24 24"
         :fill "none"
         :stroke "currentColor"
         :stroke-width (if active? "2.5" "2")
         :stroke-linecap "round" :stroke-linejoin "round"}
   [:circle {:cx 11 :cy 11 :r 8}]
   [:path {:d "M21 21l-4.35-4.35"}]])

(defn- icon-convo [active?]
  [:svg {:class "w-7 h-7" :viewBox "0 0 24 24"
         :fill (if active? "currentColor" "none")
         :stroke "currentColor"
         :stroke-width (if active? "0" "2")
         :stroke-linecap "round" :stroke-linejoin "round"}
   [:path {:d "M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"}]])

(defn- icon-notifs [active?]
  [:svg {:class "w-7 h-7" :viewBox "0 0 24 24"
         :fill (if active? "currentColor" "none")
         :stroke "currentColor"
         :stroke-width (if active? "0" "2")
         :stroke-linecap "round" :stroke-linejoin "round"}
   [:path {:d "M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"}]
   [:path {:d "M13.73 21a2 2 0 0 1-3.46 0"}]])

(defn- icon-profile [active?]
  [:svg {:class "w-7 h-7" :viewBox "0 0 24 24"
         :fill (if active? "currentColor" "none")
         :stroke "currentColor"
         :stroke-width (if active? "0" "2")
         :stroke-linecap "round" :stroke-linejoin "round"}
   [:circle {:cx 12 :cy 8 :r 4}]
   [:path {:d "M20 21a8 8 0 1 0-16 0"}]])

;; ---------------------------------------------------------------------------
;; Tab definitions

(def ^:private tabs
  [{:key :home    :path "/"              :label "ホーム"       :icon icon-home}
   {:key :search  :path "/search"        :label "検索"         :icon icon-search}
   {:key :convo   :path "/convo"         :label "DM"           :icon icon-convo    :badge :notifs/unread}
   {:key :notifs  :path "/notifications" :label "通知"         :icon icon-notifs   :badge :notifs/unread}
   {:key :profile :path "/profile"       :label "プロフィール" :icon icon-profile}])

(defn- route->tab [route]
  (case route
    :home                       :home
    :search                     :search
    (:convo-list :convo-detail) :convo
    :notifications              :notifs
    (:own-profile :profile)     :profile
    :home))

(defn- badge-pill [n]
  (when (pos? n)
    [:span {:class "absolute -top-1.5 -right-1.5 min-w-[16px] h-[16px] px-1 flex items-center justify-center rounded-full bg-red-500 text-white text-[10px] font-bold leading-none"}
     (if (> n 99) "99+" (str n))]))

;; ---------------------------------------------------------------------------
;; Component

(defn tab-bar []
  (let [route  @(rf/subscribe [:router/route])
        unread @(rf/subscribe [:notifs/unread])]
    [:nav {:class "fixed bottom-0 inset-x-0 z-50 border-t border-gv2-border"
           :style {:background-color "var(--gv2-bg-primary, #0a0a0a)"
                   :box-shadow       "0 -2px 8px rgba(0,0,0,0.1)"
                   :padding-bottom   "env(safe-area-inset-bottom)"}}
     [:div {:class "flex items-stretch"}
      (for [{:keys [key path label icon badge]} tabs]
        ^{:key (name key)}
        (let [active? (= key (route->tab route))
              n       (when badge (or unread 0))]
          [:button {:class     (str "flex-1 flex flex-col items-center justify-center py-2 gap-0.5 "
                                    "touch-manipulation transition-colors duration-75 "
                                    (if active?
                                      "text-[#1CB0F6]"
                                      "text-gv2-text-muted hover:text-gv2-text-primary"))
                    :on-click  #(do (snd/play-tap-soft!) (router/navigate! path))
                    :aria-label label
                    :aria-current (when active? "page")}
           [:div {:class "relative"}
            [icon active?]
            (when (and n badge) [badge-pill n])]
           [:span {:class "text-[10px] font-semibold tracking-wide"} label]]))]]))
