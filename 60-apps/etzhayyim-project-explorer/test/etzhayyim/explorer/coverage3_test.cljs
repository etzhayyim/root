(ns etzhayyim.explorer.coverage3-test
  "Coverage for the re-frame state layer: resource lifecycle, the bounded live
   Datom-tail buffer, and the explorer query state — the app's data-flow logic."
  (:require [cljs.test :refer-macros [deftest is testing]]
            [re-frame.core :as rf]
            ;; side-effecting requires register the events/subs under test
            [etzhayyim.explorer.state]
            [etzhayyim.explorer.live]))

(deftest resource-lifecycle
  (testing ":resource/ok stores data + clears error; :resource/error sets error"
    (rf/dispatch-sync [:resource/ok :probe {:a 1}])
    (let [r @(rf/subscribe [:resource :probe])]
      (is (= :ok (:status r)))
      (is (= {:a 1} (:data r)))
      (is (nil? (:error r))))
    (rf/dispatch-sync [:resource/error :probe "boom"])
    (let [r @(rf/subscribe [:resource :probe])]
      (is (= :error (:status r)))
      (is (= "boom" (:error r))))))

(deftest live-tail-buffer-is-bounded
  (testing "the live Datom tail keeps the 50 most-recent events, newest first"
    ;; reset the buffer deterministically
    (rf/dispatch-sync [:resource/ok :_noop {}])      ; harmless db touch
    (dotimes [i 60] (rf/dispatch-sync [:live/event {:n i}]))
    (let [evs (:events @(rf/subscribe [:live]))]
      (is (= 50 (count evs)))
      (is (= {:n 59} (first evs)))                   ; most recent first
      (is (= {:n 10} (last evs))))))                 ; oldest retained

(deftest live-degraded-turns-off
  (testing ":live/degraded turns the tail off and records the degradation"
    (rf/dispatch-sync [:live/degraded])
    (let [live @(rf/subscribe [:live])]
      (is (false? (:on? live)))
      (is (true? (:degraded? live))))))

(deftest chain-query-state
  (testing ":chain/set-query updates the query map read by :chain-query"
    (rf/dispatch-sync [:chain/set-query :attr ":vitals.actor/cells"])
    (rf/dispatch-sync [:chain/set-query :value "0"])
    (let [q @(rf/subscribe [:chain-query])]
      (is (= ":vitals.actor/cells" (:attr q)))
      (is (= "0" (:value q))))))

(deftest chain-block-inspector-state
  (testing ":chain/fetch-block sets loading; block-ok/-error update status"
    (rf/dispatch-sync [:chain/block-ok "bcid" #js {:length 42}])
    (is (= :ok (:status @(rf/subscribe [:chain]))))
    (rf/dispatch-sync [:chain/block-error "nope"])
    (is (= :error (:status @(rf/subscribe [:chain]))))))
