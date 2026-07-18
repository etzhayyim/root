#!/usr/bin/env bash
# Promote a materialized ActorRecord into CF KV as `actor:<handle>` (ADR-2606013800).
#
# Why this exists: the publisher's `--put-kv` shells out to wrangler; this is a
# wrangler-free path over the Cloudflare KV REST API (curl + python3 only), so it works
# without installing wrangler into the pnpm/node_modules symlink tree.
#
# BOUNDARY NOTE (CRITICAL): etzhayyim.com's CF edge (Worker + this ACTOR_KV namespace) is
# currently operated on etzhayyim's Cloudflare account (managed-host). etzhayyim owns the DOMAIN
# (CF Registrar) and the DID doc is content-addressed + TLS-anchored + keyless (vm:[]), and
# the Worker serves a compiled INFRA_ACTORS fallback — so this is an EDGE CACHE promotion,
# reversible via KV delete, NOT a canonical-state write. Canonical Datom state is a separate,
# etzhayyim-sovereign path (see orgs/etzhayyim/com-etzhayyim-kamado/methods/ingest.py --push + oil-refining
# MIGRATION-NOTES). Dedicated-etzhayyim-CF-account separation is a tracked follow-up.
#
# Usage (the operator supplies the CF token, e.g. from 1Password):
#   CLOUDFLARE_API_TOKEN="$(op item get <cf-token-item> --fields label=password --reveal)" \
#     [CLOUDFLARE_ACCOUNT_ID=<id>] bash scripts/put-actor-kv.sh <handle>
#
# TOKEN SCOPE (verified 2026-06-06): the token MUST carry "Workers KV Storage:Edit" on the
# account that owns namespace d33de8e0… . The etzhayyim 1Password CF tokens (etzhayyim.cloudflare/API_TOKEN
# etc.) authenticate (accounts list OK) but LACK KV scope → PUT returns 401 code 10000. Mint a
# KV-scoped token in the CF dashboard of that account first, or this exits 401. The kamado DID
# already resolves via the compiled INFRA_ACTORS fallback, so this promotion is optional + reversible.
#
# NOTE (anti-pattern caveat): the resolver (worker.ts resolveActorRecordTiered) uses KV only as a
# 300 s auto-cache of the kotoba pull (tier-2 writes it with expirationTtl: 300). This script's PUT
# has NO TTL → a PERMANENT entry that SHADOWS future kotoba/compiled updates until hand-deleted.
# Prefer wiring tier-2 KOTOBA_ENDPOINT and letting KV self-fill; reach for this only for the
# documented general promotion case (ADR-2606013800), never as part of an actor migration.
set -euo pipefail

HANDLE="${1:?usage: put-actor-kv.sh <handle>}"
: "${CLOUDFLARE_API_TOKEN:?set CLOUDFLARE_API_TOKEN (e.g. from 1Password)}"
NS="d33de8e083874cf5b8e2dbdb637ccdb4"   # ACTOR_KV namespace id (see wrangler.toml)

cd "$(dirname "$0")/.."
npx nbb scripts/publish-actor-records.cljs --actor "$HANDLE" >/dev/null
REC="out/actor-records/${HANDLE}.record.json"
[ -f "$REC" ] || { echo "no materialized record: $REC" >&2; exit 1; }

api() { curl -s -H "authorization: Bearer $CLOUDFLARE_API_TOKEN" "$@"; }

ACCT="${CLOUDFLARE_ACCOUNT_ID:-}"
if [ -z "$ACCT" ]; then
  ACCT="$(api https://api.cloudflare.com/client/v4/accounts \
    | python3 -c 'import sys,json;r=(json.load(sys.stdin) or {}).get("result") or [];print(r[0]["id"] if r else "")')"
fi
[ -n "$ACCT" ] || { echo "could not resolve CF account id; set CLOUDFLARE_ACCOUNT_ID" >&2; exit 1; }

BASE="https://api.cloudflare.com/client/v4/accounts/$ACCT/storage/kv/namespaces/$NS/values/actor:$HANDLE"
echo "account=$ACCT namespace=$NS key=actor:$HANDLE record=$REC"
echo "── PUT ──"
api -X PUT "$BASE" -H 'content-type: text/plain' --data-binary @"$REC" -w '\n  http=%{http_code}\n'
echo "── verify GET ──"
api "$BASE" -w '\n  http=%{http_code}\n'
