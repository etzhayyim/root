#!/usr/bin/env bash
# tadori threat-intel kotoba Datomic deploy.
#
# Dry run:
#   ./deploy.sh
#
# Live transact + readback verification:
#   KOTOBA_URL=http://127.0.0.1:8077 \
#   KOTOBA_SESSION_POP=<compact-eddsa-jws> \
#   TADORI_CASE_ID=case:<authorized-case> \
#   ./deploy.sh
set -euo pipefail

KOTOBA_URL="${KOTOBA_URL:-http://127.0.0.1:8077}"
GRAPH="${TADORI_GRAPH:-etzhayyim/tadori/threat-intel}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "==> tadori threat-intel Datomic deploy -> ${KOTOBA_URL} (graph ${GRAPH})"

if ! curl -fsS -m 5 "${KOTOBA_URL}/health" >/dev/null 2>&1; then
  echo "!! kotoba node not reachable at ${KOTOBA_URL} - start it with: kotoba serve" >&2
  exit 1
fi

if [[ -z "${KOTOBA_SESSION_POP:-}" && -z "${KOTOBA_TOKEN:-}" ]]; then
  echo "--> credential unset -> DRY RUN"
  python3 "${SCRIPT_DIR}/ingest_threat_intel.py" --url "${KOTOBA_URL}" --graph "${GRAPH}" --dry-run
else
  echo "--> transacting schema + staged observations, then verifying via com.etzhayyim.apps.kotoba.datomic.datoms"
  python3 "${SCRIPT_DIR}/ingest_threat_intel.py" --url "${KOTOBA_URL}" --graph "${GRAPH}" --verify-readback
fi

echo "==> done"
