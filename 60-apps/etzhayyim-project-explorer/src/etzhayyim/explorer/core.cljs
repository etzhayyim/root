(ns etzhayyim.explorer.core
  "Entry point for the etzhayyim apex SPA (ADR-2606201610).

   Stack: Reagent 1.2 + re-frame 1.4 + shadow-cljs :browser (mirrors the yoro
   cljs harness). Serverless: every read is a content-addressed/static snapshot
   served by the apex etzhayyim-did-web Worker; all decode/compute/layout happens
   here, in the browser."
  (:require [reagent.dom.client :as rdc]
            [re-frame.core :as rf]
            ;; side-effecting requires register re-frame events/subs/fx
            [etzhayyim.explorer.state]
            [etzhayyim.explorer.live]
            [etzhayyim.explorer.router :as router]
            [etzhayyim.explorer.shell :refer [app]]))

(rf/reg-event-fx
 :app/initialize
 (fn [{:keys [db]} _]
   (if (seq db)
     {}
     {:db {:route :organism
           :resources {}
           :live {:on? false :events []}}})))

(defonce react-root
  (delay (rdc/create-root (.getElementById js/document "app"))))

(defn mount-root []
  (rdc/render @react-root [app]))

(defn init! []
  (rf/dispatch-sync [:app/initialize])
  (router/init!)
  (mount-root))
