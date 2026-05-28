#!/usr/bin/env bash
# test-py.sh — Run the Python siblings' test suites.
#
# Runs `pytest` against every package under py/ that ships a `tests/`
# directory. Each package keeps its own pyproject.toml; this script does
# not assume a shared workspace umbrella (see py/README.md).
#
# Usage:
#   ./scripts/test-py.sh                    # all packages
#   ./scripts/test-py.sh kotoba_murakumo    # one package
#
# Exit code: non-zero on the first package whose test suite fails.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KOTOBA_DIR="$(dirname "$SCRIPT_DIR")"
PY_DIR="$KOTOBA_DIR/py"

# Some dev boxes have a global-site-packages langsmith plugin that fails to
# import due to a pydantic-core / pydantic version mismatch; disable plugin
# auto-load so pytest does not try to load it. Harmless in clean CI envs.
export PYTEST_DISABLE_PLUGIN_AUTOLOAD="${PYTEST_DISABLE_PLUGIN_AUTOLOAD:-1}"

PYTHON="${PYTHON:-python3}"

# If a positional arg is given, restrict to that package.
if [[ $# -gt 0 ]]; then
  PACKAGES=("$1")
else
  PACKAGES=()
  for pkg_dir in "$PY_DIR"/*/; do
    pkg_name="$(basename "$pkg_dir")"
    if [[ -d "$pkg_dir/tests" && -f "$pkg_dir/pyproject.toml" ]]; then
      PACKAGES+=("$pkg_name")
    fi
  done
fi

if [[ ${#PACKAGES[@]} -eq 0 ]]; then
  echo "test-py.sh: no Python packages with tests/ found under py/" >&2
  exit 0
fi

echo "test-py.sh: running pytest for ${#PACKAGES[@]} package(s): ${PACKAGES[*]}"
echo

overall=0
for pkg in "${PACKAGES[@]}"; do
  pkg_dir="$PY_DIR/$pkg"
  if [[ ! -d "$pkg_dir" ]]; then
    echo "test-py.sh: skip ${pkg} (no such directory)" >&2
    continue
  fi
  echo "─── ${pkg} ──────────────────────────────────────────────"
  if (cd "$pkg_dir" && "$PYTHON" -m pytest tests/ -q); then
    echo "  ${pkg}: PASS"
  else
    rc=$?
    echo "  ${pkg}: FAIL (rc=${rc})"
    overall=$rc
  fi
  echo
done

if [[ "$overall" -ne 0 ]]; then
  echo "test-py.sh: at least one package failed (overall rc=${overall})"
  exit "$overall"
fi
echo "test-py.sh: all green"
