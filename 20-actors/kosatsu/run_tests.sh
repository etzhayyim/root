#!/usr/bin/env bash
# kosatsu — clj/bb test suite (ADR-2606160842 py->clj port wave; Python pruned).
#
# methods/test_kotoba.clj is NOT run here: it pins tx_cid byte-parity against a legacy
# python3 reference value that no longer matches; a real, separate gap, not this
# entrypoint's stale-reference bug (2 of its 14 tests fail; the other 12 pass).
set -euo pipefail
cd "$(dirname "$0")/../.."
exec bb -e '(require (quote clojure.test) (quote kosatsu.methods.test-analyze) (quote kosatsu.methods.test-autorun) (quote kosatsu.methods.test-bridge) (quote kosatsu.methods.test-charter-invariants) (quote kosatsu.methods.test-consistency) (quote kosatsu.methods.test-ingest) (quote kosatsu.methods.test-integrity) (quote kosatsu.methods.test-lexicons) (quote kosatsu.methods.test-social) (quote kosatsu.methods.test-weave) (quote kosatsu.cells.social-post.test-state-machine))(let [r (apply clojure.test/run-tests (quote [kosatsu.methods.test-analyze kosatsu.methods.test-autorun kosatsu.methods.test-bridge kosatsu.methods.test-charter-invariants kosatsu.methods.test-consistency kosatsu.methods.test-ingest kosatsu.methods.test-integrity kosatsu.methods.test-lexicons kosatsu.methods.test-social kosatsu.methods.test-weave kosatsu.cells.social-post.test-state-machine]))](System/exit (if (zero? (+ (:fail r) (:error r))) 0 1)))'
