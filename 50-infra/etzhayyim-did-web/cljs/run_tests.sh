#!/usr/bin/env bash
# Pure-routing unit tests for the did:web Worker cljs core, run under babashka.
# These exercise the SAME .cljc (did-web.router) that shadow-cljs compiles into
# the deployed Worker — no browser, no wrangler deploy needed.
#
#   ./run_tests.sh
set -euo pipefail
cd "$(dirname "$0")"

bb --classpath "src:test" \
   -e '(require (quote did-web.router-test))
       (let [{:keys [fail error]} (clojure.test/run-tests (quote did-web.router-test))]
         (System/exit (if (pos? (+ fail error)) 1 0)))'
