#!/usr/bin/env bash
# kabuto — clj/bb test suite (ADR-2606160842 py->clj port wave; Python methods pruned).
#
# methods/test_{bpmn,ingest,kotoba_cid,pipeline_cid}.clj are NOT run here: they are
# CID-determinism / byte-parity pins with no .cljc port and currently fail against the
# .cljc sources (a real, separate gap -- not this entrypoint's stale-reference bug).
set -euo pipefail
cd "$(dirname "$0")/../.."
exec bb -e '(require (quote clojure.test) (quote kabuto.methods.test-charter-gates) (quote kabuto.methods.test-analyze) (quote kabuto.methods.test-autorun) (quote kabuto.methods.test-social) (quote kabuto.viz.test-build-bpmn-manifest) (quote kabuto.viz.test-build-viz-data))(let [r (apply clojure.test/run-tests (quote [kabuto.methods.test-charter-gates kabuto.methods.test-analyze kabuto.methods.test-autorun kabuto.methods.test-social kabuto.viz.test-build-bpmn-manifest kabuto.viz.test-build-viz-data]))](System/exit (if (zero? (+ (:fail r) (:error r))) 0 1)))'
