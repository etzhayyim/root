#!/usr/bin/env bash
# utsushie 写し絵 — the render-plan test suite.
# MIGRATED to Clojure (ADR-2606160842): methods/render_plan.py → methods/render_plan.cljc; the
# Python source + test were pruned once the cljc port was verified. Run the cljc suite via bb
# from the repo root (registered in bb.edn test:pywasm as utsushie.methods.test-render-plan).
set -euo pipefail
cd "$(dirname "$0")/../.."
exec bb -e "(require 'clojure.test 'utsushie.methods.test-render-plan)(let [r (clojure.test/run-tests 'utsushie.methods.test-render-plan)] (System/exit (if (zero? (+ (:fail r) (:error r))) 0 1)))"
