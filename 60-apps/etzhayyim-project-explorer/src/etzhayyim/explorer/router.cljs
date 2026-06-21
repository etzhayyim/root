(ns etzhayyim.explorer.router
  "Minimal HTML5 push-state router (ADR-2605311310 lesson: route-first, no nested
   SPA frame). Three top-level routes; default landing is the organism."
  (:require [re-frame.core :as rf]
            [clojure.string :as str]))

(def routes
  ;; path → view keyword
  {"/"          :organism
   "/organism"  :organism
   "/explorer"  :explorer
   "/nodes"     :nodes})

(defn path->view [path]
  (get routes (or path "/") :organism))

(rf/reg-event-db
 :router/navigated
 (fn [db [_ view]]
   (assoc db :route view)))

(rf/reg-sub
 :route
 (fn [db _] (get db :route :organism)))

(defn- dispatch-path! [path]
  (rf/dispatch [:router/navigated (path->view path)]))

(defn navigate!
  "Programmatic navigation — pushes state and updates the view."
  [path]
  (.pushState js/history nil "" path)
  (dispatch-path! path))

(defn- on-click [e]
  ;; Intercept same-origin <a data-nav> clicks for SPA navigation.
  (let [target (.-currentTarget e)
        href (.getAttribute target "href")]
    (when (and href (str/starts-with? href "/"))
      (.preventDefault e)
      (navigate! href))))

(defn link
  "Hiccup helper for an in-app nav link with active styling."
  [path label]
  (fn []
    (let [active? (= (path->view path) @(rf/subscribe [:route]))]
      [:a {:href path
           :class (when active? "active")
           :on-click on-click}
       label])))

(defn init! []
  (.addEventListener js/window "popstate"
                     (fn [_] (dispatch-path! (.. js/window -location -pathname))))
  (dispatch-path! (.. js/window -location -pathname)))
