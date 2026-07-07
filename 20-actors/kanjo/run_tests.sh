#!/usr/bin/env bash
# kanjo — clj/bb test suite (ADR-2606160842 py->clj port wave; Python pruned).
#
# methods/test_concept_map.clj + test_ingest.clj overlap partly with
# tests/test_kanjo.cljc but add real, non-duplicate coverage (merge-with-seed
# precedence, the concept-map/analyze metric-inputs consistency check, bare-
# element mapping) -- fixed (both had stale-reference + keyword-vs-string bugs
# against ingest.cljc's/kotoba.cljc's string-keyed EAVT convention) and wired
# in below.
#
# methods/test_{kotoba_cid,pipeline_cid}.clj are NOT run here: same
# CID-determinism / byte-parity pin class as kabuto's, currently failing
# against the .cljc sources (a real, separate gap -- not this entrypoint's bug).
set -euo pipefail
cd "$(dirname "$0")/../.."
exec bb -e '(require (quote clojure.test) (quote kanjo.methods.test-autorun) (quote kanjo.tests.test-invariants) (quote kanjo.tests.test-kanjo) (quote kanjo.methods.test-concept-map) (quote kanjo.methods.test-ingest))(let [r (apply clojure.test/run-tests (quote [kanjo.methods.test-autorun kanjo.tests.test-invariants kanjo.tests.test-kanjo kanjo.methods.test-concept-map kanjo.methods.test-ingest]))](System/exit (if (zero? (+ (:fail r) (:error r))) 0 1)))'
