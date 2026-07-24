#!/usr/bin/env bash
# Operator enablement for the actor-record KV (ADR-2606013800 + 2606015200).
# Promotes the dynamic did.json / getProfile source from the compiled
# INFRA_ACTORS fallback to a KV snapshot of the kotoba `actors-v1` graph.
#
# Requires: a Cloudflare-authenticated wrangler (operator runs `wrangler login`).
# Idempotent: skips namespace creation if ACTOR_KV is already bound.
#
#   cd 50-infra/etzhayyim-did-web && npm run enable-kv
set -euo pipefail
cd "$(dirname "$0")/.."

if grep -q '^\[\[kv_namespaces\]\]' wrangler.toml; then
  echo "ACTOR_KV already bound in wrangler.toml — skipping create."
else
  echo "Creating ACTOR_KV namespace…"
  OUT="$(npx wrangler kv namespace create ACTOR_KV)"
  echo "$OUT"
  ID="$(printf '%s' "$OUT" | grep -oE 'id = "[a-f0-9]+"' | head -1 | grep -oE '[a-f0-9]{32}')"
  if [ -z "${ID:-}" ]; then
    echo "Could not parse the namespace id from wrangler output. Paste it into"
    echo "wrangler.toml under a [[kv_namespaces]] block (binding=ACTOR_KV) by hand."
    exit 1
  fi
  printf '\n[[kv_namespaces]]\nbinding = "ACTOR_KV"\nid = "%s"\n' "$ID" >> wrangler.toml
  echo "Appended [[kv_namespaces]] (id=$ID) to wrangler.toml."
fi

echo "Publishing actor records to KV from the canonical seed…"
npx nbb scripts/publish-actor-records.cljs --put-kv

echo "Deploying the Worker…"
npx wrangler deploy

cat <<'NOTE'

Done. did.json + profile now resolve KV-first.
Optional next (kotoba live source):
  1) set IPFS_GATEWAYS / KOTOBA_ENDPOINT in wrangler.toml to the etzhayyim pin
  2) npx nbb scripts/publish-actor-records.cljs --ingest-kotoba   (operator-gated)
NOTE
