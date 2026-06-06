#!/usr/bin/env bash
# suji (筋) — one-command test runner. Pure stdlib; PYTEST_DISABLE_PLUGIN_AUTOLOAD
# avoids the tree's langgraph/langsmith pytest plugin (broken pydantic in this env).
set -euo pipefail
cd "$(dirname "$0")"
export PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
echo "== methods =="; ( cd methods && python3 -m pytest -q --noconftest )
echo "== cells ==";   ( cd cells   && python3 -m pytest -q --noconftest )
echo "== analyze (smoke) =="; ( cd methods && python3 analyze.py >/dev/null && echo "ok" )
