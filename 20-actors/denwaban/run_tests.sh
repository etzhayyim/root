#!/usr/bin/env bash
# denwaban contract test (R0): pipeline composition + G2 booking-delegation + G7 gate.
set -euo pipefail
cd "$(dirname "$0")"
bb --classpath cells \
   -e "(require 'denwaban.test-session)
       (let [{:keys [fail error]} (clojure.test/run-tests 'denwaban.test-session)]
         (System/exit (if (pos? (+ fail error)) 1 0)))"
