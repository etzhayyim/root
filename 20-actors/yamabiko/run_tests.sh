#!/usr/bin/env bash
# yamabiko — charter-gate (bb/clj) + cells parse-smoke + agent py (pending port), ADR-2606160842.
set -euo pipefail
cd "$(dirname "$0")/../.."
exec bb -e '(require (quote clojure.test) (quote [babashka.process :as p]) (quote yamabiko.methods.test-charter-gates))
(let [r (clojure.test/run-tests (quote yamabiko.methods.test-charter-gates))
      smoke (p/shell {:dir "20-actors/yamabiko" :continue true} "python3" "-c" "import ast,glob;[ast.parse(open(f).read()) for f in glob.glob('"'"'cells/homologation_binder/*.py'"'"')]")
      agent (p/shell {:dir "20-actors/yamabiko" :continue true} "python3" "py/test_agent.py")]
  (System/exit (if (and (zero? (+ (:fail r) (:error r))) (zero? (:exit smoke)) (zero? (:exit agent))) 0 1)))'
