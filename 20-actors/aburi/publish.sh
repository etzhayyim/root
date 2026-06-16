#!/usr/bin/env bash
# aburi 炙り — one-shot publish orchestrator (ADR-2606161630 + ADR-2606013800 + ADR-2606014600).
#
# Wraps the REAL repo tooling so the OPERATOR can take aburi from "registered in the codebase" to
# "resolvable + executable on etzhayyim.com" in one command. By design it does all the LOCAL,
# reversible prep on a bare run and REPORTS the exact outward commands; the outward, credentialed,
# production steps (IPFS network pin / wrangler deploy / KV promote) only fire behind explicit
# flags AND require the operator's own secrets at runtime. Nothing here holds a key (no-server-key).
#
# Usage:
#   bash 20-actors/aburi/publish.sh                 # local: build + CID drift-check + materialize + readiness
#   bash 20-actors/aburi/publish.sh --pin           # + ipfs add (pin the wasm; needs a local ipfs daemon)
#   bash 20-actors/aburi/publish.sh --deploy        # + wrangler deploy (needs CF auth) → /actor/aburi/ live
#   bash 20-actors/aburi/publish.sh --kv            # + KV promote via put-actor-kv.sh (needs KV-scoped token)
#   bash 20-actors/aburi/publish.sh --pin --deploy --kv --verify   # the full publish
#
# Boundary: per ADR-2606013800 the apex CF edge is a managed-host EDGE CACHE (reversible via KV
# delete + redeploy), NOT canonical state; the DID doc is content-addressed + TLS-anchored + keyless
# (verificationMethod []). Canonical Datom state is the separate kotoba_bridge path (G7/Council).
set -euo pipefail

HANDLE="aburi"
DO_PIN=0; DO_DEPLOY=0; DO_KV=0; DO_VERIFY=0
for a in "$@"; do case "$a" in
  --pin) DO_PIN=1 ;; --deploy) DO_DEPLOY=1 ;; --kv) DO_KV=1 ;; --verify) DO_VERIFY=1 ;;
  --all) DO_PIN=1; DO_DEPLOY=1; DO_KV=1; DO_VERIFY=1 ;;
  *) echo "unknown flag: $a" >&2; exit 2 ;;
esac; done

ACTOR_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$ACTOR_DIR/../.." && pwd)"
WORKER="$ROOT/50-infra/etzhayyim-did-web"
DIDJSON="$WORKER/public/actor/$HANDLE/did.json"
say() { printf '\n\033[1m▸ %s\033[0m\n' "$*"; }

# ── 1. build the WASM component + CID drift guard ────────────────────────────
say "1. build WASM component (componentize-py) + CID drift check"
bash "$ACTOR_DIR/wasm/build.sh" | tee /tmp/aburi-publish-build.log
BUILT_CID="$(grep -oE 'CID=[a-z0-9]+' /tmp/aburi-publish-build.log | tail -1 | cut -d= -f2)"
RECORDED_CID="$(python3 -c "import json;print(json.load(open('$DIDJSON'))['_meta']['wasmCid'] or '')")"
echo "   built    CID: $BUILT_CID"
echo "   recorded CID: $RECORDED_CID"
if [ -n "$RECORDED_CID" ] && [ "$BUILT_CID" != "$RECORDED_CID" ]; then
  echo "   ⚠ CID DRIFT — componentize-py output changed. Update the 3 homes to $BUILT_CID:" >&2
  echo "       did.json + infra-actors.ts (wasmCid) + actor-profile-seed.kotoba.edn (:actor/wasm-cid)" >&2
  echo "   (componentize-py is not always byte-reproducible; re-pin + re-record on a real bump.)" >&2
fi

# ── 2. materialize records from the registry (proves the registry edit is wired) ─
say "2. materialize did/profile/record from the registry (publish-actor-records.mjs)"
( cd "$WORKER" && node scripts/publish-actor-records.mjs --actor "$HANDLE" --emit-dir out/actor-records )
EMITTED="$WORKER/out/actor-records/$HANDLE.did.json"
if [ -f "$EMITTED" ]; then
  if diff -q <(python3 -c "import json,sys;print(json.dumps(json.load(open('$EMITTED')),sort_keys=True))") \
            <(python3 -c "import json,sys;print(json.dumps(json.load(open('$DIDJSON')),sort_keys=True))") >/dev/null; then
    echo "   ✓ emitted did.json matches the committed static did.json"
  else
    echo "   ⚠ emitted did.json differs from the static one (registry vs static drift — reconcile)"
  fi
fi

# ── 3. (outward) pin the WASM artifact to IPFS ───────────────────────────────
if [ "$DO_PIN" = 1 ]; then
  say "3. ipfs add (pin) the WASM artifact"
  ADDED="$(ipfs add -q --cid-version=1 "$ACTOR_DIR/wasm/aburi-actor.wasm")"
  echo "   pinned: $ADDED"
  [ "$ADDED" = "$BUILT_CID" ] || echo "   ⚠ ipfs add CID != build --only-hash CID (expected for dag-pb chunking diffs)"
else
  echo "   (skip pin — pass --pin; needs a running ipfs daemon / kotobase pinner)"
fi

# ── 4. (outward) deploy the Worker (serves /actor/aburi/ + compiled INFRA_ACTORS) ─
if [ "$DO_DEPLOY" = 1 ]; then
  say "4. wrangler deploy (requires CF auth)"
  ( cd "$WORKER" && pnpm install --frozen-lockfile && pnpm test && pnpm deploy )
else
  echo "   (skip deploy — pass --deploy; needs Cloudflare auth. Cmd: cd $WORKER && pnpm deploy)"
fi

# ── 5. (outward) KV promote (optional dynamic cache) ─────────────────────────
if [ "$DO_KV" = 1 ]; then
  say "5. KV promote (put-actor-kv.sh — needs CLOUDFLARE_API_TOKEN with Workers-KV-Storage:Edit)"
  ( cd "$WORKER" && bash scripts/put-actor-kv.sh "$HANDLE" )
else
  echo "   (skip KV — pass --kv; needs a KV-scoped CF token. Optional: resolver self-fills from kotoba.)"
fi

# ── 6. (outward) verify live ─────────────────────────────────────────────────
if [ "$DO_VERIFY" = 1 ]; then
  say "6. verify live resolution"
  curl -s "https://etzhayyim.com/actor/$HANDLE/profile.json" \
    | python3 -c "import sys,json;d=json.load(sys.stdin);print('   live did:',d.get('did','?'),'| handle:',d.get('handle','?'))" \
    || echo "   not resolving yet (deploy + propagate first)"
fi

say "done"
echo "Remaining outward steps you must run with your own CF creds (if not flagged above):"
[ "$DO_PIN"    = 1 ] || echo "  • bash 20-actors/aburi/publish.sh --pin        (pin the 18.9 MB wasm)"
[ "$DO_DEPLOY" = 1 ] || echo "  • bash 20-actors/aburi/publish.sh --deploy     (wrangler deploy → /actor/aburi/ live)"
[ "$DO_KV"     = 1 ] || echo "  • bash 20-actors/aburi/publish.sh --kv         (optional KV cache promote)"
echo "Canonical Datom state (live transact) is the SEPARATE member-gated path:"
echo "  • ABURI_KOTOBA_LIVE=1 ABURI_KOTOBA_OPERATOR_DID=<node pub DID> python3 methods/kotoba_bridge.py"
