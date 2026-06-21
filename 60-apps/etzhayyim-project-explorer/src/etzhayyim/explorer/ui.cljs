(ns etzhayyim.explorer.ui
  "Shared view helpers: a loading gate over re-frame resources and the heartbeat
   staleness badges (from /organism/health.json). ADR-2606201610."
  (:require [re-frame.core :as rf]
            [clojure.string :as str]))

(defn loading-gate
  "Renders `child` once all `keys` resources are :ok; otherwise a loading/error
   placeholder. Keeps each view honest about partial/failed snapshots."
  [keys child]
  (let [resources (map (fn [k] [k @(rf/subscribe [:resource k])]) keys)
        errored   (filter (fn [[_ r]] (= :error (:status r))) resources)
        pending   (filter (fn [[_ r]] (not= :ok (:status r))) resources)]
    (cond
      (seq errored)
      [:div.card.err
       [:h3 "data unavailable"]
       [:div "Could not load: "
        (str/join ", " (map (comp name first) errored))]
       [:div.muted {:style {:margin-top "6px" :font-size "12px"}}
        "These are content-addressed snapshots served by the apex Worker "
        "(/organism, /kotoba). In local dev set "
        [:span.mono "window.__DATA_BASE__ = \"https://etzhayyim.com\""] "."]]

      (seq pending)
      [:div.loading "computing the organism in your browser…"]

      :else
      child)))

(defn staleness-badges
  "Heartbeat layer freshness from health.json — surfaces snapshot age so 'live'
   is never implied when it is stale (the snapshot is the baseline; the libp2p
   tail is the live tier)."
  []
  (let [h (:data @(rf/subscribe [:resource :health]))
        layers (:layers h)]
    (when layers
      [:div {:style {:margin-bottom "14px"}}
       (for [[k {:keys [stale ageMs]}] layers]
         (let [age-s (when ageMs (Math/round (/ ageMs 1000)))]
           [:span.badge {:key (name k)
                         :class (if stale "stale" "fresh")
                         :style {:margin-right "8px"}}
            (name k) " · " (if stale "stale" "fresh")
            (when age-s [:span.muted (str " " age-s "s")])]))])))
