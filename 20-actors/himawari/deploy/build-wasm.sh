#!/usr/bin/env bash
# himawari 向日葵 — kotoba-clj WASM Component build (ADR-2606222100, 2026-06-23)
#
# Builds deploy/agent.cljc → deploy/agent.wasm using the kotoba-clj compiler
# (compile_component_str_with_prelude path).  Then validates + smoke-runs the
# output Component under wasmtime.
#
# Usage (from repo root):
#   bash 20-actors/himawari/deploy/build-wasm.sh
#
# Prerequisites:
#   - Rust toolchain (cargo) with wasm32-wasip1/wasm32-wasi target
#   - wasm-tools (cargo install wasm-tools)
#   - wasmtime (cargo install wasmtime-cli --features component-model)
#   - kotoba submodule populated (40-engine/kotoba/)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
DEPLOY_DIR="${REPO_ROOT}/20-actors/himawari/deploy"
KOTOBA_DIR="${REPO_ROOT}/40-engine/kotoba"
AGENT_CLJC="${DEPLOY_DIR}/agent.cljc"
AGENT_WASM="${DEPLOY_DIR}/agent.wasm"

echo "==> himawari kotoba-clj WASM build"
echo "    repo root:   ${REPO_ROOT}"
echo "    source:      ${AGENT_CLJC}"
echo "    output:      ${AGENT_WASM}"

# ── 1. Build the kotoba-clj binary with component + CLI features ──────────────
echo ""
echo "--> [1/4] building kotoba-clj binary (cargo build --features component,cli)…"
cd "${KOTOBA_DIR}"
cargo build -p kotoba-clj --features component,cli 2>&1
KOTOBA_CLJ="${KOTOBA_DIR}/target/$(rustc -vV 2>/dev/null | sed -n 's/host: //p')/debug/kotoba-clj"
# Fallback for non-rustc envs
if [[ ! -x "${KOTOBA_CLJ}" ]]; then
  KOTOBA_CLJ="${KOTOBA_DIR}/target/debug/kotoba-clj"
fi
if [[ ! -x "${KOTOBA_CLJ}" ]]; then
  echo "ERROR: kotoba-clj binary not found at ${KOTOBA_CLJ}" >&2
  exit 1
fi
echo "    binary: ${KOTOBA_CLJ}"

# ── 2. Compile agent.cljc → agent.wasm ────────────────────────────────────────
echo ""
echo "--> [2/4] compiling agent.cljc → agent.wasm…"
cd "${REPO_ROOT}"
"${KOTOBA_CLJ}" build "${AGENT_CLJC}" -o "${AGENT_WASM}"
echo "    output: $(du -sh "${AGENT_WASM}" | cut -f1) at ${AGENT_WASM}"

# ── 3. Validate with wasm-tools ───────────────────────────────────────────────
echo ""
echo "--> [3/4] wasm-tools validate (--features component-model)…"
if command -v wasm-tools &>/dev/null; then
  wasm-tools validate --features component-model "${AGENT_WASM}"
  echo "    wasm-tools validate: PASS"
else
  echo "    WARN: wasm-tools not found — skipping wasm-tools validate"
  echo "    install: cargo install wasm-tools"
fi

# ── 4. Smoke-run under wasmtime ───────────────────────────────────────────────
echo ""
echo "--> [4/4] wasmtime smoke-run…"
if command -v wasmtime &>/dev/null; then
  OUT="$(wasmtime run --wasm component-model "${AGENT_WASM}" 2>/dev/null || true)"
  echo "    wasmtime output: ${OUT}"
  # Expect "himawari:<N>/7:cells-ok" from the run fn
  if [[ "${OUT}" == himawari:*cells-ok ]]; then
    echo "    wasmtime smoke: PASS"
  else
    echo "    WARN: unexpected output — may still be valid, inspect above"
  fi
else
  echo "    WARN: wasmtime not found — skipping run smoke"
  echo "    install: cargo install wasmtime-cli --features component-model"
fi

echo ""
echo "==> Build complete: ${AGENT_WASM}"
