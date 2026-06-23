(ns etzhayyim.test-bb-migration-cli
  "Tests for the bb CLI dispatcher capstone (etzhayyim.cli). Verifies the pure router +
  the migration-record registry — the runnable proof that the bb CLI dispatches."
  (:require [clojure.test :refer [deftest is testing]]
            [clojure.string :as str]
            [etzhayyim.cli :as cli]))

(deftest registry-is-the-migration-record
  (testing "every ported module is listed; no test ns or dup"
    (is (= (count cli/ported-modules) (count (distinct cli/ported-modules))) "no dups")
    (is (every? #(not (str/starts-with? % "test")) cli/ported-modules))
    (is (some #{"dns-sync"} cli/ported-modules))
    (is (some #{"murakumo-cmd"} cli/ported-modules))
    (is (>= (count cli/ported-modules) 46))))

(deftest dispatch-builtins
  (is (str/includes? (:print (cli/dispatch nil)) "Usage"))
  (is (str/includes? (:print (cli/dispatch ["help"])) "Usage"))
  (is (str/includes? (:print (cli/dispatch ["version"])) "etzhayyim-cli"))
  (let [out (:print (cli/dispatch ["list"]))]
    (is (str/includes? out "dns-sync"))
    (is (str/includes? out (str (count cli/ported-modules))))))

(deftest dispatch-dispatchable-command
  ;; a command backed by a -main resolves to a :dispatch action carrying the ns + remaining args
  (let [r (cli/dispatch ["murakumo" "status" "--node" "issachar"])]
    (is (= :dispatch (:action r)))
    (is (= 'etzhayyim.murakumo-cmd (:ns r)))
    (is (= ["status" "--node" "issachar"] (:args r)))))

(deftest dispatch-library-only-command-is-honest
  ;; a ported-but-not-yet-wired command tells the truth (library ns + finish note), exit 0
  (let [r (cli/dispatch ["bonsai"])]
    (is (str/includes? (:print r) "etzhayyim.bonsai"))
    (is (str/includes? (:print r) "remaining finish"))
    (is (= 0 (:exit r)))))

(deftest dispatch-unknown-command-exits-2
  (let [r (cli/dispatch ["definitely-not-a-command"])]
    (is (str/includes? (:print r) "unknown command"))
    (is (= 2 (:exit r)))))
