(ns yoro-ui.router
  "Minimal HTML5 push-state router for the yoro ClojureScript SPA.
   Routes mirror the Svelte route table (CLAUDE.md §Routing)."
  (:require [re-frame.core :as rf]))

;; ---------------------------------------------------------------------------
;; Route matching

(defn- match-route [path]
  (let [segments (vec (filter seq (clojure.string/split path #"/")))]
    (cond
      (or (= path "/") (= path "/vibes"))
      {:route :home :params {}}

      (= path "/search")
      {:route :search :params {}}

      (= (first segments) "convo")
      (if (= (count segments) 1)
        {:route :convo-list :params {}}
        {:route :convo-detail :params {:convo-id (second segments)}})

      (= path "/notifications")
      {:route :notifications :params {}}

      (= path "/profile")
      {:route :own-profile :params {}}

      (and (= (first segments) "profile") (= (count segments) 1))
      {:route :own-profile :params {}}

      (and (= (first segments) "profile") (= (count segments) 2))
      {:route :profile :params {:handle (second segments)}}

      (and (= (first segments) "profile") (= (count segments) 4)
           (= (nth segments 2) "post"))
      {:route :post-thread
       :params {:handle (second segments) :rkey (nth segments 3)}}

      (= path "/feeds")
      {:route :feeds :params {}}

      (= path "/history")
      {:route :history :params {}}

      (= path "/credits")
      {:route :credits :params {}}

      (= path "/messages")
      {:route :convo-list :params {}} ; backward compat redirect

      :else
      {:route :not-found :params {:path path}})))

;; ---------------------------------------------------------------------------
;; re-frame integration

(rf/reg-sub
 :router/route
 (fn [db _]
   (get-in db [:router :route] :home)))

(rf/reg-sub
 :router/params
 (fn [db _]
   (get-in db [:router :params] {})))

(rf/reg-sub
 :router/location
 (fn [db _]
   (get-in db [:router :location] "/")))

(rf/reg-event-db
 :router/navigate-to
 (fn [db [_ path]]
   (let [matched (match-route path)]
     (assoc db :router (assoc matched :location path)))))

(defn navigate!
  "Push a new URL and update the router state."
  [path]
  (when (exists? js/window)
    (.pushState js/history nil "" path))
  (rf/dispatch [:router/navigate-to path]))

(defn replace!
  "Replace the current URL without adding a history entry."
  [path]
  (when (exists? js/window)
    (.replaceState js/history nil "" path))
  (rf/dispatch [:router/navigate-to path]))

(defn current-path []
  (if (exists? js/window)
    (.-pathname js/window.location)
    "/"))

(defn init!
  "Wire up the browser popstate listener and dispatch the initial route."
  []
  (when (exists? js/window)
    (.addEventListener js/window "popstate"
                       (fn [_]
                         (rf/dispatch [:router/navigate-to (current-path)]))))
  (rf/dispatch [:router/navigate-to (current-path)]))
