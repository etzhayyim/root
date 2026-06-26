#!/usr/bin/env bash
# ibuki 息吹 — cljc test suite (ADR-2606261200 py->cljc port wave). All cljc test namespaces.
# NOTE: test-ecosystem is a heavy multi-cycle integration sim (~minutes); the suite is correct but slow.
set -euo pipefail
cd "$(dirname "$0")/../.."   # repo root
exec bb -cp "20-actors/ibuki:20-actors/ibuki/methods:20-actors:20-actors/kotodama/src" -e '
(require (quote clojure.test)
         (quote ibuki.methods.test-autorun)
         (quote ibuki.methods.test-charter-invariants)
         (quote ibuki.methods.test-coscientist)
         (quote ibuki.methods.test-datoms)
         (quote ibuki.methods.test-delegation)
         (quote ibuki.methods.test-digest)
         (quote ibuki.methods.test-drainer)
         (quote ibuki.methods.test-ecosystem)
         (quote ibuki.methods.test-fleet)
         (quote ibuki.methods.test-health)
         (quote ibuki.methods.test-heartbeat)
         (quote ibuki.methods.test-infer)
         (quote ibuki.methods.test-integration)
         (quote ibuki.methods.test-joucho)
         (quote ibuki.methods.test-kaizen-feedback)
         (quote ibuki.methods.test-kaizen-outcomes)
         (quote ibuki.methods.test-kotoba-bridge)
         (quote ibuki.methods.test-member-submit)
         (quote ibuki.methods.test-metabolism)
         (quote ibuki.methods.test-perception)
         (quote ibuki.methods.test-quorum)
         (quote ibuki.methods.test-react-loop)
         (quote ibuki.methods.test-sick-colony)
         (quote ibuki.methods.test-symbiosis)
         (quote ibuki.methods.test-wellbecoming))
(let [r (apply clojure.test/run-tests
                (quote [ibuki.methods.test-autorun
             ibuki.methods.test-charter-invariants
             ibuki.methods.test-coscientist
             ibuki.methods.test-datoms
             ibuki.methods.test-delegation
             ibuki.methods.test-digest
             ibuki.methods.test-drainer
             ibuki.methods.test-ecosystem
             ibuki.methods.test-fleet
             ibuki.methods.test-health
             ibuki.methods.test-heartbeat
             ibuki.methods.test-infer
             ibuki.methods.test-integration
             ibuki.methods.test-joucho
             ibuki.methods.test-kaizen-feedback
             ibuki.methods.test-kaizen-outcomes
             ibuki.methods.test-kotoba-bridge
             ibuki.methods.test-member-submit
             ibuki.methods.test-metabolism
             ibuki.methods.test-perception
             ibuki.methods.test-quorum
             ibuki.methods.test-react-loop
             ibuki.methods.test-sick-colony
             ibuki.methods.test-symbiosis
             ibuki.methods.test-wellbecoming]))]
  (System/exit (if (zero? (+ (:fail r) (:error r))) 0 1)))'
