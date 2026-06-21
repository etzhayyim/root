(ns etzhayyim.explorer.live
  "Live Datom tail — R0 progressive enhancement over the static node snapshot
   (ADR-2606201610, decided 2026-06-20). The snapshot is always the baseline
   render; this layers a real-time stream on top and degrades *silently* to the
   snapshot on any failure.

   Transport: browser-native Server-Sent Events against the kotoba sync endpoint
     GET /xrpc/com.etzhayyim.apps.kotoba.sync.subscribe?cursor=N
   The longer-term path dials a kotoba node directly over libp2p from the browser
   (no edge in the trust path); SSE is the R0 stand-in over the same content-
   addressed Datom events. Toggle is off until the user opts in (no surprise
   connections, keeps the page fully serverless by default)."
  (:require [re-frame.core :as rf]
            [etzhayyim.explorer.data :as data]
            [etzhayyim.explorer.wire :as wire]))

(defonce ^:private source (atom nil))

(def ^:const endpoint "/xrpc/com.etzhayyim.apps.kotoba.sync.subscribe?cursor=0")

(defn sync-base
  "Base URL of the kotoba sync node. Same-origin in production (the apex Worker
   proxies the XRPC endpoint); override for local dev via window.__SYNC_BASE__
   (e.g. \"http://localhost:8720\" to hit the local sync node)."
  []
  (let [win (.-__SYNC_BASE__ js/window)]
    (if (and (string? win) (pos? (.-length win))) win (data/data-base))))

(defn decode-frame
  "Decode one SSE frame. The kotoba sync wire is transit+json (the Datomic-client
   standard); fall back to plain JSON, then to a raw wrapper, so the tail is
   robust to whatever a node emits."
  [data]
  (or (try (wire/decode data) (catch :default _ nil))
      (try (js->clj (js/JSON.parse data) :keywordize-keys true) (catch :default _ nil))
      {:raw data}))

(defn- close! []
  (when-let [es @source]
    (.close es)
    (reset! source nil)))

(defn- open! []
  (close!)
  (try
    (let [es (js/EventSource. (str (sync-base) endpoint))]
      (set! (.-onmessage es)
            (fn [ev] (rf/dispatch [:live/event (decode-frame (.-data ev))])))
      (set! (.-onerror es)
            (fn [_]
              ;; Degrade silently: turn the live tier off, keep the snapshot.
              (close!)
              (rf/dispatch [:live/degraded])))
      (reset! source es))
    (catch :default _
      (rf/dispatch [:live/degraded]))))

;; Side-effect: open/close the SSE source in response to the toggle.
(rf/reg-fx :live/connect (fn [on?] (if on? (open!) (close!))))

(rf/reg-event-fx
 :live/start
 (fn [{:keys [db]} _]
   {:db (assoc-in db [:live :on?] true)
    :live/connect true}))

(rf/reg-event-fx
 :live/stop
 (fn [{:keys [db]} _]
   {:db (assoc-in db [:live :on?] false)
    :live/connect false}))

(rf/reg-event-fx
 :live/degraded
 (fn [{:keys [db]} _]
   {:db (-> db (assoc-in [:live :on?] false) (assoc-in [:live :degraded?] true))}))

;; ── UI bits ─────────────────────────────────────────────────────────────────
(defn tail-bar []
  (let [{:keys [on? degraded?]} @(rf/subscribe [:live])]
    [:div {:style {:display "flex" :align-items "center" :gap "10px" :margin-bottom "12px"}}
     [:span {:class (str "live-dot " (if on? "on" "off"))}]
     [:button.btn {:class (when-not on? "ghost")
                   :on-click #(rf/dispatch [(if on? :live/stop :live/start)])}
      (if on? "live · streaming Datoms" "go live · libp2p/SSE tail")]
     (when degraded?
       [:span.muted {:style {:font-size "12px"}}
        "live tail unavailable — showing the static snapshot"])]))

(defn tail-feed []
  (let [{:keys [on? events]} @(rf/subscribe [:live])]
    (when (or on? (seq events))
      [:div.card
       [:h3 "live · Datom tail"]
       (if (seq events)
         [:ul.pulse
          (for [[i ev] (map-indexed vector (take 20 events))]
            [:li {:key i} [:span.mono (pr-str ev)]])]
         [:div.loading "waiting for Datoms…"])])))
