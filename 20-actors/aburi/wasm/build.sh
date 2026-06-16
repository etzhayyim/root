#!/usr/bin/env bash
# Build the aburi 炙り actor as a WASI Component-Model component with componentize-py, and report
# its IPFS CID (ADR-2606161630 + ADR-2606014600). OPERATOR STEP — not run in CI.
# Requires: python3 (componentize-py via venv), node/npx (jco), ipfs, wasm-tools.
set -euo pipefail
cd "$(dirname "$0")"

ACTOR=".."
# bundle the pure methods + the representative seed beside app.py (the sandbox has no FS)
cp "$ACTOR/methods/analyze.py" "$ACTOR/methods/datom_emit.py" "$ACTOR/methods/coverage_report.py" .
python3 - "$ACTOR/data/seed-tracker-exposure.kotoba.edn" <<'PY'
import sys, pathlib, json
seed = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")
pathlib.Path("_seed.py").write_text("SEED_EDN = " + json.dumps(seed) + "\n", encoding="utf-8")
print(f"_seed.py generated ({len(seed)} bytes embedded)")
PY

# offline sanity — own_data + reciprocity_restoring must be true before we build
python3 -c "import app, json; r=json.loads(app.compute()); assert r['own_data'] and r['reciprocity_restoring'] and r['non_adjudicating'], r; print('python sanity OK —', len(r['who_tracks_you']), 'trackers ranked')"

VENV="${CPY_VENV:-/tmp/cpy-venv}"
if [ ! -x "$VENV/bin/componentize-py" ]; then
  python3 -m venv "$VENV"
  "$VENV/bin/pip" install --quiet componentize-py
fi

"$VENV/bin/componentize-py" -d wit -w aburi-actor componentize app -o aburi-actor.wasm
wasm-tools validate aburi-actor.wasm
npx -y @bytecodealliance/jco@latest transpile aburi-actor.wasm -o transpiled --name aburi

CID="$(ipfs add -Q --only-hash --cid-version=1 aburi-actor.wasm)"
SIZE="$(wc -c < aburi-actor.wasm | tr -d ' ')"
printf 'aburi-actor.wasm  %s bytes  CID=%s\n' "$SIZE" "$CID"
echo "If the CID changed, set :actor/wasm-cid in 00-contracts/schemas/actor-profile-seed.kotoba.edn"
echo "  and wasmCid in 50-infra/etzhayyim-did-web/src/registry/infra-actors.ts + public/actor/aburi/."
echo "NOTE: dag-pb (multi-block, bundles CPython) → T2 donated-mesh tier per ADR-2606014500."
