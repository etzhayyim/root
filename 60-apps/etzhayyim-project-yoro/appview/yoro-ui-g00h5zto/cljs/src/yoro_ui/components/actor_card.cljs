(ns yoro-ui.components.actor-card
  "Actor card for search results / suggestions."
  (:require [re-frame.core :as rf]
            [yoro-ui.router :as router]
            [yoro-ui.components.post-card :refer [avatar]]))

(defn actor-card
  "Props: {:did :handle :displayName :description :avatar :indexedAt}"
  [{:keys [did handle display-name description avatar-url indexed-at]}]
  [:div {:class "flex items-start gap-3 px-4 py-3 border-b border-gv2-border/40 hover:bg-gv2-bg-card/30 transition-colors cursor-pointer"
         :on-click #(router/navigate! (str "/profile/" (or did handle)))}
   [avatar {:src avatar-url :display-name (or display-name handle) :size 48}]
   [:div {:class "flex-1 min-w-0"}
    [:div {:class "flex items-center gap-1.5"}
     [:span {:class "font-bold text-[14px] text-gv2-text-primary truncate"}
      (or display-name handle)]
     [:span {:class "text-[12px] text-gv2-text-muted"}
      (when handle (str "@" handle))]]
    (when description
      [:p {:class "text-[12px] text-gv2-text-muted mt-0.5 line-clamp-2 leading-relaxed"}
       description])]])

(defn actor-skeleton []
  [:div {:class "flex items-start gap-3 px-4 py-3 border-b border-gv2-border/40"}
   [:div {:class "w-12 h-12 rounded-full bg-gv2-border/40 animate-pulse flex-shrink-0"}]
   [:div {:class "flex-1"}
    [:div {:class "h-3 bg-gv2-border/40 rounded w-1/3 mb-2 animate-pulse"}]
    [:div {:class "h-3 bg-gv2-border/40 rounded w-3/4 animate-pulse"}]]])
