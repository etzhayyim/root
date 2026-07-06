#!/usr/bin/env bash
# Build all 4 matsurigoto egov service modules as WASI Component-Model components with
# componentize-py, transpile with jco, and report each one's IPFS CID (ADR-2606062300 R1.A;
# same componentize-py path as the watatsuna precedent, ADR-2606014600).
# Requires: python3 (for componentize-py via venv), node/npx (jco), ipfs, wasm-tools.
set -euo pipefail
cd "$(dirname "$0")"

WIT_DIR="../../../00-contracts/wit/matsurigoto"

# componentize-py in an isolated venv (PEP-668 environments block global pip).
VENV="${CPY_VENV:-/tmp/cpy-venv}"
if [ ! -x "$VENV/bin/componentize-py" ]; then
  python3 -m venv "$VENV"
  "$VENV/bin/pip" install --quiet componentize-py
fi

# world:module pairs — each WIT world exports exactly one service interface (egov.wit).
declare -A MODULES=(
  [tax-assess]=tax_assess_app
  [civil-registry]=civil_registry_app
  [corp-registry]=corp_registry_app
  [credential-issue]=credential_issue_app
)

for world in "${!MODULES[@]}"; do
  mod="${MODULES[$world]}"
  echo "=== $world ($mod.py) ==="
  "$VENV/bin/componentize-py" -d "$WIT_DIR" -w "$world" componentize "$mod" -o "$world.wasm"
  wasm-tools validate "$world.wasm"
  npx -y @bytecodealliance/jco@latest transpile "$world.wasm" -o "transpiled-$world" \
    --name "$(echo "$world" | sed -E 's/-([a-z])/\U\1/g')"
  CID="$(ipfs add -Q --only-hash --cid-version=1 "$world.wasm")"
  SIZE="$(wc -c < "$world.wasm" | tr -d ' ')"
  printf '%s.wasm  %s bytes  CID=%s\n' "$world" "$SIZE" "$CID"
done

echo "Run 'node verify.mjs' to check all 4 against their reference specs."
echo "If a CID changed, update the matching <world>.meta.json + :egov.module/cid in the standard EDN."
