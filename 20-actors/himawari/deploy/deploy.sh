#!/usr/bin/env bash
# himawari 向日葵 — kotoba deploy
# ADR-2606021200 + ADR-2606015000 (PDS write path on kotoba-server)
#
# Ingests the seven com.etzhayyim.himawari.* lexicon records into a running kotoba
# node and (optionally) builds the langgraph WASM actor (7-cell manufacturing
# chain). Writes to the canonical Datom journal require a verified operator session
# Proof-of-Possession (KOTOBA_SESSION_POP) — no-server-key posture, substrate
# boundary. Without it the ingest is a DRY RUN. LLM access is Murakumo-only (G5).
#
# Usage:
#   KOTOBA_URL=http://127.0.0.1:8077 \
#   KOTOBA_SESSION_POP=<operator-session-pop-jws> \
#     ./deploy.sh
set -euo pipefail

KOTOBA_URL="${KOTOBA_URL:-http://127.0.0.1:8077}"
GRAPH="${HIMAWARI_GRAPH:-com.etzhayyim.himawari}"
DEPLOY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ACTOR_DIR="$(cd "${DEPLOY_DIR}/.." && pwd)"
ACTORS_ROOT="$(cd "${ACTOR_DIR}/.." && pwd)"          # 20-actors/ — Python path for himawari.cells.*
KOTOBA_DIR="$(cd "${ACTORS_ROOT}/../40-engine/kotoba" && pwd)"

echo "==> himawari kotoba deploy → ${KOTOBA_URL} (graph ${GRAPH})"

if ! curl -fsS -m 5 "${KOTOBA_URL}/health" >/dev/null 2>&1; then
  echo "!! kotoba node not reachable at ${KOTOBA_URL} — start it with: kotoba serve" >&2
  exit 1
fi

# 1. Record ingest via the PDS write path (session-PoP-gated; ADR-2606015000).
if [[ -z "${KOTOBA_SESSION_POP:-}" ]]; then
  echo "--> KOTOBA_SESSION_POP unset → DRY RUN (no writes). Set an operator session PoP to ingest."
  python3 "${DEPLOY_DIR}/ingest_records.py" --url "${KOTOBA_URL}" --graph "${GRAPH}" --dry-run
else
  echo "--> ingesting himawari records via PDS kg.ingest (operator session PoP present)"
  KOTOBA_SESSION_POP="${KOTOBA_SESSION_POP}" python3 "${DEPLOY_DIR}/ingest_records.py" \
    --url "${KOTOBA_URL}" --graph "${GRAPH}"
  echo "--> sealing hot arrangement (kotoba commit)"
  kotoba --url "${KOTOBA_URL}" --token "${KOTOBA_SESSION_POP}" commit
fi

# 2. langgraph actor build (componentize-py → 7-cell manufacturing chain WASM).
#
# componentize-py is invoked directly here (not via scripts/build-pywasm.sh) because
# himawari needs THREE extra import roots on the build path simultaneously:
#   - ${ACTORS_ROOT}      → himawari.cells.* (the seven manufacturing cells)
#   - ${KOTOBA_DIR}/py    → kotoba_langgraph (StateGraph / KotobaLLM / handle_invoke)
#   - real site-packages  → langgraph / typing_extensions
# build-pywasm.sh's single KOTOBA_SITE_PKG override can carry only one of these.
# -d MUST point at the wit DIRECTORY (not world.wit) so componentize-py loads the
# vendored deps/ packages (wasi:http@0.2.0 etc. that the kotoba-node world imports);
# pointing it at the file alone fails with "package 'wasi:http@0.2.0' not found".
WIT_DIR="${KOTOBA_DIR}/crates/kotoba-runtime/wit"
BINDINGS_DIR="${KOTOBA_DIR}/target/himawari-pywasm-bindings"
SITE_PKG="$(python3 -c 'import site; print(site.getsitepackages()[0])' 2>/dev/null || true)"

echo "--> langgraph actor build (componentize-py)"
if command -v componentize-py >/dev/null 2>&1; then
  # WIT bindings (cached): regenerate if absent.
  if [[ ! -d "${BINDINGS_DIR}" ]]; then
    echo "    generating WIT bindings → ${BINDINGS_DIR}"
    mkdir -p "${BINDINGS_DIR}"
    componentize-py -d "${WIT_DIR}" -w kotoba-node bindings "${BINDINGS_DIR}"
  fi
  componentize-py \
    -d "${WIT_DIR}" \
    -w kotoba-node \
    componentize agent \
    -p "${DEPLOY_DIR}" \
    -p "${BINDINGS_DIR}" \
    -p "${KOTOBA_DIR}/py" \
    -p "${ACTORS_ROOT}" \
    ${SITE_PKG:+-p "${SITE_PKG}"} \
    -o "${DEPLOY_DIR}/agent.wasm"
  echo "    built deploy/agent.wasm ($(du -sh "${DEPLOY_DIR}/agent.wasm" | cut -f1)) —"
  echo "    deploy via the node's invoke.run / kotoba_wasm_run with an operator session PoP"
else
  echo "    (componentize-py absent — skipping wasm build; see deploy/README.md for the venv recipe)"
fi

echo "==> done"
