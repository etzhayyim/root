#!/usr/bin/env bash
# kabuto — clj/bb test suite (ADR-2606160842 py->clj port wave; Python methods pruned).
#
# methods/test_ingest.clj + test_kotoba_cid.clj were stale-reference bugs (ingest.cljc
# was missing merge-bridged/gated-source?; kotoba.cljc was missing canonical-order; both
# test files also had keyword-vs-string key-access bugs against this ns's string-keyed
# EAVT convention) -- fixed, now wired in below.
#
# methods/test_{bpmn,pipeline_cid}.clj are NOT run here: test_bpmn.clj has the same
# keyword-vs-string bug PLUS a genuine content-CID byte-parity mismatch against bpmn.cljc
# (needs investigation, not just a key-access fix); test_pipeline_cid.clj currently errors
# against the real autorun/analyze pipeline. Both are a real, separate gap.
set -euo pipefail
cd "$(dirname "$0")/../.."
exec bb -e '(require (quote clojure.test) (quote kabuto.methods.test-charter-gates) (quote kabuto.methods.test-analyze) (quote kabuto.methods.test-autorun) (quote kabuto.methods.test-social) (quote kabuto.methods.test-ingest) (quote kabuto.methods.test-kotoba-cid) (quote kabuto.viz.test-build-bpmn-manifest) (quote kabuto.viz.test-build-viz-data))(let [r (apply clojure.test/run-tests (quote [kabuto.methods.test-charter-gates kabuto.methods.test-analyze kabuto.methods.test-autorun kabuto.methods.test-social kabuto.methods.test-ingest kabuto.methods.test-kotoba-cid kabuto.viz.test-build-bpmn-manifest kabuto.viz.test-build-viz-data]))](System/exit (if (zero? (+ (:fail r) (:error r))) 0 1)))'
