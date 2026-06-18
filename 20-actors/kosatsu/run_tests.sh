#!/usr/bin/env bash
# kosatsu — clj/bb test suite (ADR-2606160842 py->clj port wave; Python pruned).
set -euo pipefail
cd "$(dirname "$0")/../.."
exec bb test:kosatsu
