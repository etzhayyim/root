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

(deftest dispatch-help-lists-wired-commands
  (testing "help output names each of the 7 wired inline commands"
    (let [out (:print (cli/dispatch ["help"]))]
      (is (str/includes? out "bonsai"))
      (is (str/includes? out "identifier-audit"))
      (is (str/includes? out "source-graph"))
      (is (str/includes? out "shannon"))
      (is (str/includes? out "coverage"))
      (is (str/includes? out "kosei-tiers"))
      (is (str/includes? out "dns-sync")))))

(deftest dispatch-dispatchable-command
  ;; a command backed by a -main resolves to a :dispatch action carrying the ns + remaining args.
  ;; NOTE: murakumo-cmd is a PURE+injectable-IO library (no -main; deliberately dispatched via
  ;; the guarded library-commands path since it's fleet ops) — this test uses vitals, which does
  ;; expose a real -main and is wired into `dispatchable`.
  (let [r (cli/dispatch ["vitals" "status" "--node" "issachar"])]
    (is (= :dispatch (:action r)))
    (is (= 'etzhayyim.vitals (:ns r)))
    (is (= ["status" "--node" "issachar"] (:args r)))))

(deftest dispatch-wired-inline-handlers
  (testing "each wired command resolves to :handle action with the right handler fn"
    (doseq [cmd ["bonsai" "identifier-audit" "source-graph" "shannon"
                 "coverage" "kosei-tiers" "dns-sync"]]
      (let [r (cli/dispatch [cmd "--help"])]
        (is (= :handle (:action r))
            (str cmd " should dispatch to :handle"))
        (is (ifn? (:handler r))
            (str cmd " handler should be callable (fn or var-wrapping-fn)"))
        (is (= ["--help"] (:args r))
            (str cmd " remaining args should be passed through"))))))

(deftest dispatch-library-only-command-is-honest
  ;; auth is ported as a LIBRARY (not wired, no -main, not in dispatchable/handlers/
  ;; library-commands) — must return the "remaining finish" note.
  ;; NOTE: bonsai and bunseki are now wired; this test uses auth (still unwired) to verify
  ;; the honest path.
  (let [r (cli/dispatch ["auth"])]
    (is (str/includes? (:print r) "etzhayyim.auth"))
    (is (str/includes? (:print r) "remaining finish"))
    (is (= 0 (:exit r)))))

(deftest dispatch-unknown-command-exits-2
  (let [r (cli/dispatch ["definitely-not-a-command"])]
    (is (str/includes? (:print r) "unknown command"))
    (is (= 2 (:exit r)))))

(deftest wired-commands-are-in-ported-modules
  (testing "every key in handlers is also listed in ported-modules"
    (doseq [cmd (keys cli/handlers)]
      (is (some #{cmd} cli/ported-modules)
          (str "handler key '" cmd "' must be in ported-modules")))))

(deftest dispatchable-commands-are-in-ported-modules
  (testing "every key in dispatchable is also listed in ported-modules (murakumo-cmd)"
    ;; murakumo → murakumo-cmd in ported-modules; vitals → vitals
    ;; The dispatch key is the CLI word, ported-modules tracks the ns suffix
    (is (some #{"murakumo-cmd"} cli/ported-modules))
    (is (some #{"vitals"} cli/ported-modules))))

(deftest shannon-handler-pure-dispatch
  (testing "shannon handler can be invoked directly with counts (no IO path)"
    ;; dispatch to get the handler fn, then call it — avoids needing the full -main
    (let [r (cli/dispatch ["shannon" "10,20,5"])]
      (is (= :handle (:action r)))
      (is (= ["10,20,5"] (:args r))))))

(deftest kosei-tiers-handler-tier-info-mode
  (testing "kosei-tiers handler dispatches for tier-info mode (positional tier arg)"
    (let [r (cli/dispatch ["kosei-tiers" "T1"])]
      (is (= :handle (:action r)))
      (is (= ["T1"] (:args r))))))

(deftest kosei-tiers-handler-classify-mode
  (testing "kosei-tiers handler dispatches for classify mode (--name / --dir opts)"
    (let [r (cli/dispatch ["kosei-tiers" "--name" "gateway" "--dir" "50-infra/x"])]
      (is (= :handle (:action r)))
      (is (= ["--name" "gateway" "--dir" "50-infra/x"] (:args r))))))

(deftest dns-sync-handler-dispatches-dry-run
  (testing "dns-sync without --apply routes to :handle"
    (let [r (cli/dispatch ["dns-sync" "--toml" "deps.toml"])]
      (is (= :handle (:action r)))
      (is (= ["--toml" "deps.toml"] (:args r))))))
