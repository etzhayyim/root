(ns etzhayyim.explorer.shell
  "App shell: sticky top nav + route-first view switch (ADR-2605311310: each
   route renders its panel directly, no nested SPA frame). Triggers per-view
   data bootstrap whenever the active route changes."
  (:require [re-frame.core :as rf]
            [etzhayyim.explorer.router :as router]
            [etzhayyim.explorer.organism.view :as organism]
            [etzhayyim.explorer.nodes.view :as nodes]
            [etzhayyim.explorer.chain.view :as chain]))

(defn- ensure-data! [view]
  (case view
    :organism (rf/dispatch [:organism/init])
    :nodes    (rf/dispatch [:nodes/init])
    :explorer (rf/dispatch [:explorer/init])
    nil))

(defn- topbar []
  [:div.topbar
   [:div.brand "etzhayyim" [:small "the living organism"]]
   [:nav.nav
    [(router/link "/organism" "Organism")]
    [(router/link "/explorer" "Explorer")]
    [(router/link "/nodes" "Nodes")]]])

(defn app []
  (let [view @(rf/subscribe [:route])]
    (ensure-data! view)
    [:div.app
     [topbar]
     (case view
       :explorer [chain/view]
       :nodes    [nodes/view]
       [organism/view])]))
