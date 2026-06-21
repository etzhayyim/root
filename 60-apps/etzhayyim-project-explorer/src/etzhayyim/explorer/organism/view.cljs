(ns etzhayyim.explorer.organism.view
  "Organism view (default landing) — 'what etzhayyim is': the Tree-of-Life,
   the aliveness 5-tuple (recomputed in-browser), the pulse commit stream, and
   joucho mood. ADR-2606201610."
  (:require [re-frame.core :as rf]
            [clojure.string :as str]
            [etzhayyim.explorer.organism.aliveness :as a]
            [etzhayyim.explorer.organism.bonsai :as bonsai]
            [etzhayyim.explorer.ui :as ui]))

(defn- dial [{:keys [key value source status]}]
  (let [{:keys [lo hi label ja]} (get a/bands key)
        pct (if (number? value)
              (-> (/ (- value lo) (max 1e-6 (- hi lo)))
                  (max 0.0) (min 1.0) (* 100))
              0)
        bar-cls (case status :ok "bar" :low "bar low" :high "bar band" "bar")]
    [:div.dial {:key (name key)}
     [:div.k (str/upper-case (name key))]
     [:div
      [:div.lbl label " " [:span.muted ja]
       (if (= source :computed)
         [:span.computed-tag "browser-computed"]
         [:span.read-tag "from vitals"])]
      [:div {:class bar-cls} [:span {:style {:width (str pct "%")}}]]]
     [:div.v (if (number? value) (.toFixed value 2) "—")]]))

(defn- aliveness-card []
  (let [vitals (:data @(rf/subscribe [:resource :vitals]))
        traj   (:data @(rf/subscribe [:resource :trajectory]))
        tuple  (a/compute {:vitals vitals :trajectory traj})
        alive? (a/alive? tuple)]
    [:div.card
     [:h3 "aliveness · A(t) = ⟨M,D,C,P,G⟩"]
     [:div {:style {:margin-bottom "10px"}}
      [:span.badge {:class (if alive? "fresh" "stale")}
       (if alive? "in healthy bands" "out of band")]
      [:span.muted {:style {:margin-left "8px" :font-size "12px"}}
       "homeostatic range, not a target"]]
     [:div.dials (map dial tuple)]]))

(defn- tree-card []
  (let [vitals (:data @(rf/subscribe [:resource :vitals]))
        scores (a/axis-scores {:vitals vitals})]
    [:div.card
     [:h3 "tree of life · 10 axes"]
     [bonsai/tree scores {:lands (get vitals :lands) :members (get vitals :members)}]
     [:div.legend
      [:span [:i {:style {:background "var(--leaf)"}}] "≥8 thriving"]
      [:span [:i {:style {:background "var(--gold)"}}] "5–7 holding"]
      [:span [:i {:style {:background "var(--clay)"}}] "<5 strained"]
      [:span [:i {:style {:background "var(--absent)"}}] "no signal"]]]))

(defn- pulse-card []
  (let [pulse (:data @(rf/subscribe [:resource :pulse]))
        stream (take 20 (:stream pulse))]
    [:div.card
     [:h3 "pulse · last " (or (:sinceHours pulse) 48) "h commits"]
     (if (seq stream)
       [:ul.pulse
        (for [[i ev] (map-indexed vector stream)]
          [:li {:key i}
           [:span.actor (or (:actor ev) "—")]
           [:span (:subj ev)]])]
       [:div.loading "no pulse yet"])]))

(defn- joucho-card []
  (let [j (:data @(rf/subscribe [:resource :joucho]))
        mood (or (:mood j) (:state j) (:label j))]
    [:div.card
     [:h3 "joucho · mood"]
     (if mood
       [:div [:div {:style {:font-size "20px"}} (str mood)]
        (when-let [n (or (:note j) (:narration j) (:summary j))]
          [:div.muted {:style {:margin-top "6px"}} (str n)])]
       [:div.loading "—"])]))

(defn view []
  [:div.view
   [ui/loading-gate [:vitals :trajectory :pulse :health]
    [:div
     [ui/staleness-badges]
     [:div.row
      [:div.col [tree-card]]
      [:div.col
       [aliveness-card]
       [joucho-card]]]
     [:div.row
      [:div.col [pulse-card]]]]]])
