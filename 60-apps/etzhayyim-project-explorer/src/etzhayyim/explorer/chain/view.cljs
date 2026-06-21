(ns etzhayyim.explorer.chain.view
  "kotoba blockchain explorer — the CommitDag (append-only, content-addressed
   Datom ledger). ADR-2606201610 + ADR-2605312345.

   This view runs the REAL canonical kotoba.datom codec in the browser
   (chain.datom): it fetches a kotoba Datom log, VERIFIES the content-addressed
   chain by recomputing every :tx/cid (tamper-evident, no server in the loop),
   materializes the EAVT, and runs a small Datalog-shaped query — all client-
   side. The static /kotoba/<genesis>.root.json head pointer + raw-block CAR
   decode (kotoba-wasm Prolly) remain alongside; full kqe Datalog is R1."
  (:require [re-frame.core :as rf]
            [reagent.core :as r]
            [clojure.string :as str]
            [etzhayyim.explorer.data :as data]
            [etzhayyim.explorer.ui :as ui]))

;; ── chain verification (the real thing) ─────────────────────────────────────
(defn- verify-card []
  (let [v @(rf/subscribe [:chain/verify])
        txs @(rf/subscribe [:chain/txs])]
    [:div.card
     [:h3 "commit-DAG · chain verification"]
     (cond
       (nil? v) [:div.loading "verifying in your browser…"]
       (:ok v)
       [:div
        [:div {:style {:margin-bottom "8px"}}
         [:span.badge.fresh "✓ chain verified"]
         [:span.muted {:style {:margin-left "8px" :font-size "12px"}}
          (:length v) " tx · every :tx/cid recomputed via kotoba.datom"]]
        [:table.kv
         [:tbody
          [:tr [:td "transactions"] [:td.mono (:length v)]]
          [:tr [:td "datoms"] [:td.mono (reduce + 0 (map :tx/count txs))]]
          [:tr [:td "head CID"] [:td.mono (:head v)]]]]
        [:div.muted {:style {:font-size "12px" :margin-top "6px"}}
         "Content-addressed: a tamper of any earlier tx breaks every later CID. "
         "Recomputed here with the canonical codec — byte-compatible with the "
         "clj/Python writers, no edge trusted."]]
       :else
       [:div
        [:span.badge.stale "✗ chain broken at tx " (:broken-at v)]
        [:div.mono {:style {:margin-top "8px" :font-size "12px"}}
         "expected " (:expected v) [:br] "actual   " (:actual v)]])]))

(defn- tx-card []
  (let [txs @(rf/subscribe [:chain/txs])]
    [:div.card
     [:h3 "transactions · oldest → newest"]
     (if (seq txs)
       [:table.kv
        [:tbody
         (for [tx txs]
           [:tr {:key (:tx/id tx)}
            [:td (str "tx " (:tx/id tx))]
            [:td [:div.mono {:style {:font-size "11.5px"}} (:tx/cid tx)]
             [:div.muted (:tx/count tx) " datoms · prev "
              (if (str/blank? (:tx/prev tx)) "∅" (subs (:tx/prev tx) 0 (min 12 (count (:tx/prev tx)))))]]])]]
       [:div.loading "loading the Datom log…"])]))

(defn- entity-browser []
  (let [eavt @(rf/subscribe [:chain/eavt])
        selected (r/atom nil)]
    (fn []
      (let [eavt @(rf/subscribe [:chain/eavt])
            ents (when eavt (sort (keys eavt)))]
        [:div.card
         [:h3 "EAVT · entity browser (" (count ents) " entities)"]
         [:div {:style {:display "flex" :gap "12px"}}
          [:div {:style {:flex "1 1 40%" :max-height "260px" :overflow "auto"}}
           (for [e (take 200 ents)]
             [:div.mono {:key e
                         :style {:cursor "pointer" :padding "2px 0"
                                 :fontWeight (when (= e @selected) "700")}
                         :on-click #(reset! selected e)}
              (let [s (str e)] (if (> (count s) 42) (str (subs s 0 42) "…") s))])]
          [:div {:style {:flex "1 1 60%"}}
           (if-let [e @selected]
             [:table.kv [:tbody
                         (for [[a v] (get eavt e)]
                           [:tr {:key (str a)}
                            [:td.mono (str a)]
                            [:td.mono (if (vector? v) (str/join ", " (map str v)) (str v))]])]]
             [:div.muted {:style {:font-size "12px"}} "select an entity"])]]]))))

(defn- query-card []
  (let [q @(rf/subscribe [:chain-query])
        attrs @(rf/subscribe [:chain/attributes])
        result @(rf/subscribe [:chain/query-result])]
    [:div.card
     [:h3 "datalog · query (runs in-browser)"]
     [:div {:style {:display "flex" :gap "8px" :flex-wrap "wrap"}}
      [:select.input {:style {:flex "1 1 60%"}
                      :value (or (:attr q) "")
                      :on-change #(rf/dispatch [:chain/set-query :attr (.. % -target -value)])}
       [:option {:value ""} "— attribute —"]
       (for [a attrs] [:option {:key (str a) :value (str a)} (str a)])]
      [:input.input {:style {:flex "1 1 30%"} :placeholder "value (optional)"
                     :value (or (:value q) "")
                     :on-change #(rf/dispatch [:chain/set-query :value (.. % -target -value)])}]]
     [:div.muted {:style {:font-size "12px" :margin "6px 0"}}
      "≈ [:find ?e ?v :where [?e " (or (:attr q) "?a") " "
      (if (str/blank? (:value q)) "?v" (:value q)) "]]"]
     (when result
       [:div {:style {:max-height "200px" :overflow "auto"}}
        [:div.muted {:style {:font-size "12px"}} (count result) " results"]
        [:table.kv [:tbody
                    (for [[i [e v]] (map-indexed vector (take 100 result))]
                      [:tr {:key i}
                       [:td.mono (let [s (str e)] (if (> (count s) 36) (str (subs s 0 36) "…") s))]
                       [:td.mono (str v)]])]]])]))

;; ── static head pointer (kotoba-publish) — kept alongside ───────────────────
(defn- head-pointer-card []
  (let [r* @(rf/subscribe [:resource :root-ptr])
        root (:data r*)
        head (or (:head root) (:commit root) root)]
    [:div.card
     [:h3 "CommitDag head pointer · /kotoba/" (or (:genesis root) data/default-genesis) ".root.json"]
     (case (:status r*)
       :error [:div.muted {:style {:font-size "12px"}}
               "head pointer not available locally (served by the apex Worker in prod)"]
       :ok [:table.kv [:tbody
                       [:tr [:td "seq"] [:td.mono (str (or (:seq head) "—"))]]
                       [:tr [:td "root CID"] [:td.mono (or (:root head) "—")]]]]
       [:div.loading "…"])
     [:div.muted {:style {:font-size "12px" :margin-top "6px"}}
      "Raw-block CAR decode (Prolly traversal) runs in kotoba-wasm — R1."]]))

;; ── Holochain-iso agent registration (self-published genesis source-chains) ──
(defn- vmark [ok?] (if ok? [:span {:style {:color "var(--leaf)"}} "✓"]
                       [:span {:style {:color "var(--clay)"}} "✗"]))

(defn- registration-card []
  (let [reg @(rf/subscribe [:registry])
        mv (:mv reg)
        verified (:verified reg)]
    [:div.card
     [:h3 "agent registration · Holochain-iso validating membrane"]
     (if mv
       [:div
        [:div.muted {:style {:font-size "12px" :margin-bottom "8px"}}
         (:mv/count mv) " validated · " (:mv/rejected mv) " rejected. Each agent "
         "authored a SIGNED genesis on its own source-chain; an SBT member "
         "vouched (CACAO); a validator quorum attested. Re-verified in-browser:"]
        [:table.kv
         [:tbody
          (for [{:keys [handle did file]} (:mv/index mv)]
            (let [v (get verified file)]
              [:tr {:key file}
               [:td [:b handle]
                [:div.mono {:style {:font-size "10.5px"}} (str (subs did 0 20) "…")]]
               [:td (cond
                      (nil? v) [:span.loading "verifying…"]
                      (:error v) [:span.err (:error v)]
                      (and (:quorum v) (get-in v [:quorum :met?]))
                      [:span.mono
                       (vmark (:cid-ok v)) " chain "
                       (vmark (:self-signed v)) " self-sig "
                       (vmark (:vouch-ok v)) " vouch "
                       [:span {:style {:color "var(--leaf)"}}
                        "✓ quorum " (get-in v [:quorum :valid-count]) "≥"
                        (get-in v [:quorum :threshold])]
                       [:span.muted " · dht×" (:dht-replicas v)]]
                      :else
                      [:span.mono {:style {:color "var(--clay)"}}
                       "✗ REJECTED "
                       (when (seq (:reasons v))
                         (str "[" (str/join "," (:reasons v)) "]"))
                       " · quorum " (get-in v [:quorum :valid-count]) "<"
                       (get-in v [:quorum :threshold])])]]))]]
        [:div.muted {:style {:font-size "11.5px" :margin-top "8px"}}
         "✓ vouch = an SBT member (in the published roster) signed a CACAO "
         "capability for this agent — the Sybil boundary; ✓ quorum = ≥threshold "
         "validators attested. Un-vouched / duplicate agents are "
         [:b "rejected by the membrane"] " (warrants), never folded into the registry."]]
       [:div.loading "loading agent registry…"])]))

(defn- transit-wire-card []
  (let [w @(rf/subscribe [:wire])
        resp (:cells w)
        cells (:result/cells resp)
        sample (first cells)]
    [:div.card
     [:h3 "kotoba query · transit+json wire"]
     (cond
       (:error w) [:div.muted {:style {:font-size "12px"}}
                   "transit wire fixture not generated (run actor-registry " [:span.mono "clojure -M:wire"] ")"]
       (nil? resp) [:div.loading "fetching Datom query response over the wire…"]
       :else
       [:div
        [:span.badge.fresh "transit+json"]
        [:span.muted {:style {:margin-left "8px" :font-size "12px"}}
         "Datomic-client wire standard · decoded by transit-cljs"]
        [:table.kv {:style {:margin-top "8px"}}
         [:tbody
          [:tr [:td "query"] [:td.mono {:style {:font-size "11px"}} (pr-str (:query/find resp))]]
          [:tr [:td "cells returned"] [:td.mono (:result/count resp)]]
          [:tr [:td "type fidelity"]
           [:td.mono
            (vmark (keyword? (:cell/class sample))) " :cell/class is a keyword "
            [:span.muted "(" (pr-str (:cell/class sample)) ")"]]]
          [:tr [:td "sample cell"]
           [:td.mono {:style {:font-size "11px"}}
            (str (:cell/id sample) " · " (:cell/class sample) " · cells " (:cell/cells sample))]]]]
        [:div.muted {:style {:font-size "11.5px" :margin-top "8px"}}
         "Keywords (" [:span.mono ":vitals.actor/*"] ", " [:span.mono ":alive"]
         ") survive the wire and repeated attribute keys are cache-compressed — "
         "what plain JSON loses. CID preimage stays canonical-JSON; on-disk stays EDN."]])]))

(defn view []
  [:div.view
   [ui/loading-gate [:datom-log]
    [:div.row
     [:div.col {:style {:flex "1 1 48%"}}
      [verify-card]
      [transit-wire-card]
      [registration-card]
      [tx-card]
      [head-pointer-card]]
     [:div.col {:style {:flex "1 1 48%"}}
      [query-card]
      [entity-browser]]]]])
