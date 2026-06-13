(ns yoro-ui.core
  "Entry point for the yoro ClojureScript SPA.

   Stack: Reagent 1.2 + re-frame 1.4 + shadow-cljs
   Router: minimal HTML5 push-state (router.cljs)
   Data:   AT Protocol XRPC → atproto.etzhayyim.com (Candidate C topology)
   Auth:   CACAO session read from localStorage (no XRPC on bootstrap)"
  (:require [reagent.dom.client :as rdc]
            [re-frame.core :as rf]
            ;; State namespaces — side-effectful require registers subs/events
            [yoro-ui.state.auth]
            [yoro-ui.state.feed]
            [yoro-ui.state.search]
            [yoro-ui.state.history]
            [yoro-ui.state.hitl]
            [yoro-ui.state.convos]
            [yoro-ui.state.topology]
            [yoro-ui.state.inference-consent]
            ;; Router
            [yoro-ui.router :as router]
            ;; App shell
            [yoro-ui.shell.app :refer [app]]))

;; ---------------------------------------------------------------------------
;; App bootstrap

(rf/reg-event-fx
 :app/initialize
 (fn [{:keys [db]} _]
   (if (seq db)
     {}
     {:db {}
      :fx [[:dispatch [:auth/bootstrap]]
           [:dispatch [:hitl/start]]]})))

;; ---------------------------------------------------------------------------
;; React 18 root — defonce so shadow-cljs hot reload reuses the same root

(defonce react-root
  (delay (rdc/create-root (.getElementById js/document "app"))))

(defn mount-root []
  (rdc/render @react-root [app]))

(defn init! []
  (rf/dispatch-sync [:app/initialize])
  (router/init!)
  (mount-root))
