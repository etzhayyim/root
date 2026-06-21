(ns etzhayyim.explorer.coverage8-test
  "Component-render coverage for ui.cljs — the loading gate that fronts every
   view and the heartbeat staleness badges. The components return hiccup, so we
   set the re-frame resource state and assert on the rendered structure (no DOM
   needed)."
  (:require [cljs.test :refer-macros [deftest is testing]]
            [re-frame.core :as rf]
            [etzhayyim.explorer.ui :as ui]
            [etzhayyim.explorer.state]))

(deftest loading-gate-branches
  (testing "all resources :ok → renders the child verbatim"
    (rf/dispatch-sync [:resource/ok :g-ok {:a 1}])
    (is (= [:span "CHILD"] (ui/loading-gate [:g-ok] [:span "CHILD"]))))
  (testing "any resource :error → renders the error card (names the failure)"
    (rf/dispatch-sync [:resource/error :g-err "boom"])
    (let [r (ui/loading-gate [:g-err] [:span "x"])]
      (is (= :div.card.err (first r)))))
  (testing "a never-loaded resource → the loading placeholder"
    (let [r (ui/loading-gate [:g-pending] [:span "x"])]
      (is (= :div.loading (first r))))))

(deftest staleness-badges-render
  (testing "no health data → renders nothing"
    (rf/dispatch-sync [:resource/error :health "none"])
    (is (nil? (ui/staleness-badges))))
  (testing "health layers → a badge container is rendered"
    (rf/dispatch-sync [:resource/ok :health
                       {:layers {:pulse {:stale false :ageMs 4000}
                                 :vitals {:stale true :ageMs 9000000}}}])
    (let [r (ui/staleness-badges)]
      (is (= :div (first r)))
      ;; the badge list is built from the layers map → non-empty children
      (is (seq (drop 2 r))))))
