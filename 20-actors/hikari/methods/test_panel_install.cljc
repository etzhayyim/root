(ns hikari.methods.test-panel-install
  "test_panel_install.py — hikari panel-install robot motion loop tests.
  1:1 Clojure port of methods/test_panel_install.py (pytest → clojure.test)."
  (:require [clojure.test :refer [deftest is run-tests testing]]
            [hikari.methods.substrate :as sub]
            [hikari.methods.panel-install :as pi]))

(def WITNESS ["did:web:etzhayyim.com:kuniumi:robot:otete-01"
              "did:web:etzhayyim.com:kuniumi:robot:mimi-01"])

(deftest test-reachable-target-plans-clean-motion
  (let [plan (pi/plan-panel-install [1.5 0.4] "m:ed25519:demo" WITNESS)]
    (is (get plan "reachable"))
    (is (some? (get plan "joints_goal")))
    (is (get plan "envelope_ok"))
    (is (get plan "witness_ok"))
    (is (= false (get plan "server_held_key")))
    (is (= true (get plan "dry_run")))))

(deftest test-unreachable-target-reports-not-reachable
  (let [far [(+ (:max-reach pi/OTETE-ARM) 1.0) 0.0]
        plan (pi/plan-panel-install far "m:sig" WITNESS)]
    (is (= false (get plan "reachable")))
    (is (nil? (get plan "joints_goal")))
    (is (= 0 (get plan "trajectory_steps")))))

(deftest test-non-civilian-use-refused
  (doseq [use ["weapon" "interdiction" "smelting"]]
    (testing use
      (is (thrown? clojure.lang.ExceptionInfo
                   (pi/plan-panel-install [1.0 0.2] "m:sig" WITNESS :use use))))))

(deftest test-server-signature-refused
  (is (thrown? clojure.lang.ExceptionInfo
               (pi/plan-panel-install [1.0 0.2] "m:sig" WITNESS :server-sig "s:sig"))))

(deftest test-missing-member-signature-refused
  (is (thrown? clojure.lang.ExceptionInfo
               (pi/plan-panel-install [1.0 0.2] "" WITNESS))))

(deftest test-witness-quorum-below-two-recorded-not-raised
  (let [plan (pi/plan-panel-install [1.2 0.3] "m:sig" ["did:r:a"])]
    (is (= false (get plan "witness_ok"))))) ; escalation Datom, not a hard raise

(deftest test-human-proximity-forces-slower-envelope
  ;; A fast 60-step move that is fine far from humans violates the slow ceiling
  ;; when a person may be present.
  (let [target [1.8 0.6]
        fast (pi/plan-panel-install target "m:sig" WITNESS :human-present false :steps 15)
        slow-ceiling (pi/plan-panel-install target "m:sig" WITNESS :human-present true :steps 15)]
    (is (= true (get fast "envelope_ok")))
    (is (= false (get slow-ceiling "envelope_ok")))
    (is (seq (get slow-ceiling "envelope_violations")))))

(deftest test-datoms-dry-run-and-keyless
  (let [plan (pi/plan-panel-install [1.5 0.4] "m:sig" WITNESS)
        d (pi/to-datoms plan "install-001")]
    (is (= false (get d ":install/server-held-key")))
    (is (= true (get d ":install/dry-run")))
    (is (= true (get d ":install/reachable")))))

#?(:clj (defn -main [& _] (run-tests 'hikari.methods.test-panel-install)))
