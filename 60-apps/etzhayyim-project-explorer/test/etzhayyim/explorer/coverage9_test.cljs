(ns etzhayyim.explorer.coverage9-test
  "Full reagent SSR render coverage for the three views. Renders each view to a
   static HTML string via reagent.dom.server (react-dom/server, no DOM needed),
   driving the whole component tree — ui gate, cards, bonsai SVG, force graph,
   census, chain verification — from populated re-frame state."
  (:require [cljs.test :refer-macros [deftest is testing]]
            [clojure.string :as str]
            [reagent.dom.server :as rserver]
            [re-frame.core :as rf]
            [kotoba.datom :as kd]
            [etzhayyim.explorer.organism.view :as organism]
            [etzhayyim.explorer.nodes.view :as nodes]
            [etzhayyim.explorer.chain.view :as chain]
            [etzhayyim.explorer.state]))

(defn- html [component] (rserver/render-to-static-markup component))

;; ── fixtures ────────────────────────────────────────────────────────────────
(def ^:private vitals-eavt
  [["v/busshi" :vitals.actor/name "busshi" 1 :add]
   ["v/busshi" :vitals.actor/cells 12 1 :add]
   ["v/busshi" :vitals.clj/reflex "green" 1 :add]
   ["v/busshi" :vitals.actor/integrates 3 1 :add]
   ["v/busshi" :vitals.atproto/bsky-post true 1 :add]])

(def ^:private datom-log
  (str kd/log-header
       (kd/tx->edn-line (kd/make-tx [[:db/add "e" ":a/x" "v"]]
                                    {:tx-id 1 :as-of 1 :prev-cid ""})) "\n"))

(def ^:private census-log
  (let [ds [[":db/add" "census.living-cells" ":census/tier" "living-cells"]
            [":db/add" "census.living-cells" ":census/count" 104]
            [":db/add" "census.living-cells" ":census/source" "vitals EAVT"]]]
    (str "{:tx/id 1 :tx/prev \"\" :tx/cid " (pr-str (kd/tx-cid ds ""))
         " :tx/count 3 :tx/datoms " (pr-str ds) "}\n")))

;; ── organism view ───────────────────────────────────────────────────────────
(deftest organism-view-loading-then-rendered
  (testing "with no data the loading gate shows its placeholder"
    (rf/dispatch-sync [:resource/error :vitals "x"])     ; force gate's error path
    (let [out (html [organism/view])]
      (is (str/includes? out "data unavailable"))))
  (testing "with data populated the Tree-of-Life + aliveness render"
    (doseq [[k v] {:vitals vitals-eavt
                   :trajectory {:runs [{:run 1 :sum 100 :alive 1 :dormant 1 :stub 1}
                                       {:run 2 :sum 150 :alive 1 :dormant 1 :stub 2}]}
                   :pulse {:sinceHours 48 :stream [{:actor "busshi" :subj "feat: x"}]}
                   :joucho {:mood "neutral"}
                   :health {:layers {:pulse {:stale false :ageMs 4000}}}}]
      (rf/dispatch-sync [:resource/ok k v]))
    (let [out (html [organism/view])]
      (is (str/includes? out "tree of life"))
      (is (str/includes? out "aliveness"))
      (is (str/includes? out "pulse")))))

;; ── nodes view ──────────────────────────────────────────────────────────────
(deftest nodes-view-renders-mesh-and-census
  (doseq [[k v] {:vitals vitals-eavt :census-log census-log
                 :health {:layers {:pulse {:stale false :ageMs 4000}}}}]
    (rf/dispatch-sync [:resource/ok k v]))
  (let [out (html [nodes/view])]
    (is (str/includes? out "living cells"))
    (is (str/includes? out "actor census"))
    (is (str/includes? out "mesh"))))

;; ── chain / explorer view ───────────────────────────────────────────────────
(deftest chain-view-renders-verification
  (rf/dispatch-sync [:resource/ok :datom-log datom-log])
  (let [out (html [chain/view])]
    (is (str/includes? out "chain verification"))
    (is (str/includes? out "EAVT"))
    (is (str/includes? out "transit+json"))))
