#!/usr/bin/env bash
# test-kotoba-murakumo.sh — Run the kotoba_murakumo Python test suite.
#
# kotoba_murakumo is the Modal-compatible facade for the Murakumo Mac mini
# fleet (ADR-2605282000 + ADR-2605282100). It lives at the monorepo path
# 40-engine/kotoba_murakumo/ as a religious-corp downstream consumer of the
# kotoba substrate (NOT inside the kotoba git-subrepo; see
# ADR-2605282200 for the relocation rationale).
#
# Usage:
#   ./70-tools/scripts/test-kotoba-murakumo.sh
#   KOTOBA_MURAKUMO_LIVE_FLEET=1 ./70-tools/scripts/test-kotoba-murakumo.sh
#   KOTOBA_MURAKUMO_CHARTER_ENFORCE=1 ./70-tools/scripts/test-kotoba-murakumo.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PKG_DIR="$REPO_ROOT/40-engine/kotoba_murakumo"

# Some dev boxes have a global-site-packages langsmith plugin that fails to
# import due to a pydantic-core / pydantic version mismatch; disable plugin
# auto-load. Harmless in clean CI envs.
export PYTEST_DISABLE_PLUGIN_AUTOLOAD="${PYTEST_DISABLE_PLUGIN_AUTOLOAD:-1}"

PYTHON="${PYTHON:-python3}"

echo "test-kotoba-murakumo.sh: running pytest in $PKG_DIR"
cd "$PKG_DIR"
"$PYTHON" -m pytest tests/ -q "$@"
