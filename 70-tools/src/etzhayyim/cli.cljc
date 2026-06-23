(ns etzhayyim.cli
  "etzhayyim CLI — babashka/Clojure entry point (capstone of the etzhayyim-py → bb
  migration, ADR-2606222000). The Python `cli.py` is a thin click dispatcher that
  registers ~60 subcommands; this is its bb counterpart.

  STATUS (honest): all ~46 command MODULES are ported to `etzhayyim.<name>` cljc — their
  pure logic is parity-verified and their IO legs are injectable/dry-run-safe (see the
  per-module ADR + wave PRs). What this dispatcher provides today:
    - `list`    — the migration record: every ported module ns (the SSoT of what's done)
    - `version` — CLI version
    - `<cmd>`   — for a module that exposes a `-main`, dispatch argv to it
    - otherwise — a module is ported as a LIBRARY (ns `etzhayyim.<cmd>`); its per-command
                  argv-wiring (click options → babashka.cli spec) is the remaining mechanical
                  finish. Until a command is wired here, invoke its fns from a REPL or use the
                  Python `e7m` (which runs alongside). This is documented, not hidden.

  No business logic lives here — it only routes. Run via `bb e7m <command> [args…]`."
  (:require [clojure.string :as str]))

;; ── the migration record: every ported command module (SSoT) ──────────────────────
;; Drop a new `etzhayyim.<name>.cljc` and add it here. Mirrors cli.py's add_command set.
(def ported-modules
  ["actors" "agent-cmd" "agent-runtime" "agent-token" "apps" "auth" "authn" "authz"
   "bonsai" "bunseki" "code-quality" "complex-stubs" "coverage" "cohort" "database"
   "deploy" "deps" "dns-sync" "dodaf" "haisen" "hinshitsu" "identifier-audit" "identity"
   "kagami" "kaizen" "kashika" "kosei" "kosei-tiers" "lint" "logs" "metrics" "mitama"
   "mokuteki" "monitor" "murakumo-cmd" "nono" "organism" "process-mining" "projector"
   "shannon" "shannon-scores" "source-graph" "systemofsystem" "training" "vertex"
   "vitals" "workspace" "xrpc" "yoroshiku"])

;; ── commands that expose a runnable `-main` (argv → action) and can be dispatched today ──
;; command-name → the ns symbol whose `-main` handles it.
(def dispatchable
  {"murakumo" 'etzhayyim.murakumo-cmd
   "vitals"   'etzhayyim.vitals})

(def ^:private version "0.1.0-bb")

(defn- usage []
  (str "etzhayyim — platform CLI (babashka port; ADR-2606222000)\n\n"
       "Usage: bb e7m <command> [args…]\n\n"
       "Built-in:\n"
       "  list           list every ported command module (the migration record)\n"
       "  version        print CLI version\n"
       "  help           this message\n\n"
       "Dispatchable now: " (str/join ", " (sort (keys dispatchable))) "\n"
       "All other commands are ported as libraries (ns etzhayyim.<command>); their\n"
       "per-command argv-wiring is the remaining finish — invoke from a REPL or use the\n"
       "Python e7m meanwhile.\n"))

(defn dispatch
  "Pure router: given argv, return either {:action …} to perform or {:print s}. Kept pure
  (no side effects, no require) so it is unit-testable; -main performs the effect."
  [args]
  (let [[cmd & more] args]
    (cond
      (or (nil? cmd) (= cmd "help") (= cmd "--help") (= cmd "-h")) {:print (usage)}
      (= cmd "version") {:print (str "etzhayyim-cli " version)}
      (= cmd "list") {:print (str "ported command modules (" (count ported-modules) "):\n"
                                  (->> ported-modules sort (map #(str "  " %)) (str/join "\n")))}
      (contains? dispatchable cmd) {:action :dispatch :ns (dispatchable cmd) :args (vec more)}
      (some #{cmd} ported-modules) {:print (str "command '" cmd "' is ported as a LIBRARY (ns etzhayyim."
                                                cmd ").\nIts CLI argv-wiring is the remaining finish (ADR-2606222000);\n"
                                                "invoke its fns from a REPL or use the Python e7m meanwhile.")
                                     :exit 0}
      :else {:print (str "unknown command: " cmd "\n\n" (usage)) :exit 2})))

(defn -main [& args]
  (let [{:keys [print action ns args exit] :or {exit 0}} (dispatch args)]
    (when print (println print))
    (when (= action :dispatch)
      (require ns)
      (apply (resolve (symbol (str ns) "-main")) args))
    (when (and exit (pos? exit)) (System/exit exit))))
