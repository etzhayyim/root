(ns etzhayyim.explorer.nodes.view
  "Node distribution (分散状況) view — the living mesh of actors/cells: who is
   alive/dormant/stub, the dependency graph (browser-laid-out), the physical
   fleet, and the optional libp2p live Datom tail. ADR-2606201610."
  (:require [reagent.core :as r]
            [re-frame.core :as rf]
            [clojure.string :as str]
            [etzhayyim.explorer.nodes.graph :as g]
            [etzhayyim.explorer.live :as live]
            [etzhayyim.explorer.ui :as ui]))

(defn- summary-card []
  (let [s @(rf/subscribe [:nodes/summary])]
    [:div.card
     [:h3 "living cells · queried from kotoba vitals EAVT"]
     [:div.summary-cards
      [:div.stat [:div.n (or (:cells s) "—")] [:div.l "cells"]]
      [:div.stat [:div.n {:style {:color "var(--leaf)"}} (or (:alive s) 0)] [:div.l "生 alive"]]
      [:div.stat [:div.n {:style {:color "var(--gold)"}} (or (:dormant s) 0)] [:div.l "休眠 dormant"]]
      [:div.stat [:div.n {:style {:color "var(--absent)"}} (or (:stub s) 0)] [:div.l "死 stub"]]]
     [:div.muted {:style {:margin-top "10px" :font-size "12px"}}
      "These are the organism's heartbeat-bearing cells — materialized + "
      "classified (生/休眠/死) from the "
      [:span.mono ":vitals.*"] " Datoms, not a baked JSON summary."]]))

(defn- census-card []
  (let [c @(rf/subscribe [:census])
        reg @(rf/subscribe [:registry])
        self-n (get-in reg [:mv :mv/count])]
    [:div.card
     [:h3 "actor census · queried from a kotoba Datom log"]
     (if c
       [:div
        [:span.badge {:class (if (:verified c) "fresh" "stale")}
         (if (:verified c) "✓ chain verified" "✗ unverified")]
        [:table.kv {:style {:margin-top "8px"}}
         [:tbody
          (when self-n
            [:tr {:key "self" :style {:background "#ecf6ef"}}
             [:td [:b "self-registered"]]
             [:td [:b.mono (str self-n)]
              [:div.muted {:style {:font-size "11px"}}
               "agent-centric: signed genesis source-chains (emergent fold, "
               "not a constant — ADR-2606011330)"]]])
          (for [{:keys [tier count source]} (:tiers c)]
            [:tr {:key tier}
             [:td (str tier)]
             [:td [:b.mono (str count)]
              [:div.muted {:style {:font-size "11px"}} source]]])]]
        [:div.muted {:style {:font-size "12px" :margin-top "8px"}}
         "The /nodes mesh shows only the "
         [:b "living-cells"] " tier. The "
         [:b "unispsc"] " (18,342) + " [:b "entity-mirror"]
         " actors are the apex materialized-view tier — resolvable via did.json / "
         "/search, but not heartbeat cells, so they are not in the mesh."]]
       [:div.loading "querying census Datoms…"])]))

(defn- mesh-card []
  (let [hovered (r/atom nil)]
    (fn []
      (let [nodes (or @(rf/subscribe [:nodes/cells]) [])
            pos (g/layout nodes)]
        [:div.card
         [:h3 "mesh · " (count nodes) " living cells (kotoba EAVT query)"]
         [:svg.meshgraph {:viewBox g/viewbox :role "img" :aria-label "node mesh"}
          ;; edges: faint pull lines toward centroid give a sense of cohesion
          (for [[id p] pos]
            (let [nd (:node p)]
              [:circle.node-dot
               {:key id :cx (:x p) :cy (:y p) :r (g/node-radius nd)
                :fill (g/reflex-color (:reflex nd))
                :opacity (if (= (:class nd) "dormant") 0.55 0.9)
                :stroke (when (= (:class nd) "alive") "var(--ink)")
                :stroke-width (when (= (:class nd) "alive") 1)
                :on-mouse-over #(reset! hovered nd)
                :on-mouse-out #(reset! hovered nil)}]))]
         (if-let [nd @hovered]
           [:div.mono {:style {:margin-top "8px"}}
            [:b (:id nd)] " · " (:class nd)
            " · reflex " (:reflex nd)
            " · score " (:score nd)
            " · cells " (:cells nd)
            " · ↑" (:outDeg nd) " ↓" (:inDeg nd)
            " · ♥" (:heartbeatDays nd) "d"]
           [:div.muted {:style {:margin-top "8px" :font-size "12px"}} "hover a cell"])
         [:div.legend
          [:span [:i {:style {:background "var(--leaf)"}}] "reflex green"]
          [:span [:i {:style {:background "var(--clay)"}}] "reflex red"]
          [:span [:i {:style {:background "var(--gold)"}}] "unknown"]
          [:span [:i {:style {:background "var(--absent)"}}] "absent"]]]))))

(defn view []
  [:div.view
   [ui/loading-gate [:vitals :census-log :health]
    [:div
     [ui/staleness-badges]
     [live/tail-bar]
     [:div.row
      [:div.col {:style {:flex "2 1 520px"}} [mesh-card]]
      [:div.col [summary-card] [census-card] [live/tail-feed]]]]]])
