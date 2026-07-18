;; etzhayyim.test-actor-mesh — actor-mesh pure-helper invariants (cljc port).
;; Run: bb test:actor-mesh
;; Covers the pure manifest-generation helpers (cell scanning / file IO deferred):
;; cell-name-from-path · trigger-spec · component-spec · generate-app-edn.
(ns etzhayyim.test-actor-mesh
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [clojure.edn :as edn]
            [etzhayyim.actor-mesh :as mesh]))

(deftest cell-name-from-path-conversion
  (is (= "intake-qa" (mesh/cell-name-from-path "cells/intake_qa/state_machine.cljc")))
  (is (= "my-cell" (mesh/cell-name-from-path
                    "20-actors/foo/cells/my_cell/state_machine.cljc")))
  (is (= "a-b-c" (mesh/cell-name-from-path "cells/a_b_c/state_machine.cljc"))))

(deftest trigger-spec-by-kind
  (is (= {:type :http :route "/foo/bar"} (mesh/trigger-spec :on-http "foo" "bar")))
  (is (= {:type :kse :topic "etzhayyim/actor/foo"} (mesh/trigger-spec :on-kse "foo" "bar")))
  (is (= {:type :cron :schedule "0 * * * *"} (mesh/trigger-spec :on-tick "foo" "bar")))
  (testing "unknown trigger falls back to http"
    (is (= {:type :http :route "/foo/bar"} (mesh/trigger-spec :wat "foo" "bar")))))

(deftest component-spec-assembly
  (let [c (mesh/component-spec
           "myactor"
           "/repo/20-actors/myactor/cells/intake_qa/state_machine.cljc"
           :on-http
           "/repo/20-actors/myactor")]
    (is (= "myactor-intake-qa" (:name c)))
    (is (= "cells/intake_qa/state_machine.cljc" (:src c)))   ;; relative to actor-dir
    (is (= 1 (:scale c)))
    (is (= [{:type :http :route "/myactor/intake-qa"}] (:triggers c)))
    (is (= #{:cap/kqe} (:requires c)))))

(deftest generate-app-edn-manifest
  (let [edn (mesh/generate-app-edn
             "myactor"
             ["/repo/20-actors/myactor/cells/intake_qa/state_machine.cljc"]
             :on-http
             "/repo/20-actors/myactor")]
    (testing "valid EDN string carrying the app manifest"
      (is (string? edn))
      (let [m (edn/read-string edn)]
        (is (= "myactor" (:kotoba.app/name m)))
        (is (= "0.1.0" (:kotoba.app/version m)))
        (is (= 1 (count (:kotoba.app/components m))))
        (is (= "myactor-intake-qa" (:name (first (:kotoba.app/components m)))))))))

(defn -main [& _]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.test-actor-mesh)]
    (#?(:clj System/exit :cljs js/process.exit)
     (if (pos? (+ fail error)) 1 0))))
