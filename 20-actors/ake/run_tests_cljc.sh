#!/usr/bin/env bash
# 朱 (ake) — run the CANONICAL Clojure (.cljc) test suite via babashka.
#
# The .cljc methods are the canonical port; the .py files mirror them (test_consistency
# locks the two against drift). This runner EXECUTES the Clojure path so it is proven green,
# not merely asserted to match Python — closing the "canonical but never run" maturity gap.
#
# Skips gracefully (exit 0) when babashka is unavailable, so a checkout without `bb` still
# passes its Python suite. When bb IS present, a red .cljc suite fails loudly (exit 1).
set -uo pipefail

if ! command -v bb >/dev/null 2>&1; then
  echo "── ake cljc: babashka (bb) not found — skipping canonical Clojure suite (py mirror still ran) ──"
  exit 0
fi

# The seed paths inside the .cljc tests are REPO-ROOT-relative (e.g.
# "20-actors/ake/data/seed-edit-graph.kotoba.edn"), and the namespaces are ake.methods.*,
# so the classpath root is 20-actors and the cwd must be the repo root.
HERE="$(cd "$(dirname "$0")" && pwd)"   # 20-actors/ake
ACTORS="$(dirname "$HERE")"             # 20-actors
REPO="$(dirname "$ACTORS")"             # repo root (or worktree root)
cd "$REPO"

bb --classpath 20-actors -e '
(require (quote [clojure.test :as t]))
(def nss (quote [ake.methods.test--edn
                 ake.methods.test-triage ake.methods.test-revision ake.methods.test-editwar
                 ake.methods.test-contributor ake.methods.test-ingest
                 ake.methods.test-charter-invariants ake.methods.test-analyze
                 ake.methods.test-lexicons ake.methods.test-consistency]))
(doseq [n nss] (require n))
(let [r (apply t/run-tests nss)]
  (println "── ake cljc:" (:test r) "tests /" (:pass r) "assertions green,"
           (:fail r) "fail," (:error r) "error ──")
  (when (or (pos? (:fail r)) (pos? (:error r))) (System/exit 1)))
'
