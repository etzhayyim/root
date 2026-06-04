#!/usr/bin/env bash
# karute end-to-end deploy orchestrator.
#
# Stages (per ADR-2605231900):
#   1. DID Worker  (karute.etzhayyim.com)        — CF Worker
#   2. audit DID Worker (audit.etzhayyim.com)    — CF Worker
#   3. lg-karute Pod                              — k8s
#   4. CF Tunnel to k8s service                   — cloudflared
#   5. Svelte SuperApp static bundle              — CF Pages
#   6. Smoke + verify
#
# Each stage is idempotent. Use `--only <stage>` to run a single stage.

set -euo pipefail

usage() {
  cat <<EOF
Usage: $0 [--only <stage>] [--skip-keygen] [--dry-run]

Stages:
  did-worker          DID Worker for karute.etzhayyim.com
  audit-worker        DID Worker for audit.etzhayyim.com
  k8s-pod             lg-karute Deployment (build + push image + apply)
  cf-tunnel           cloudflared tunnel for karu7t3e.etzhayyim.com
  pages-deploy        Cloudflare Pages deploy of dist/
  smoke               curl probes + Universal Resolver check

Without --only, all stages run in order.

Environment:
  WRANGLER_LOGIN       Skip "wrangler login" if set
  GITHUB_USER          For ghcr.io pull secret
  GITHUB_PAT           For ghcr.io pull secret
EOF
}

STAGE=""
SKIP_KEYGEN=false
DRY_RUN=false
while [ $# -gt 0 ]; do
  case "$1" in
    --only) STAGE="$2"; shift 2 ;;
    --skip-keygen) SKIP_KEYGEN=true; shift ;;
    --dry-run) DRY_RUN=true; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown flag: $1" >&2; usage; exit 2 ;;
  esac
done

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

run() {
  echo "→ $*"
  if [ "$DRY_RUN" = true ]; then return 0; fi
  "$@"
}

stage_did_worker() {
  echo "━━ Stage 1: karute DID Worker ━━"
  if [ "$SKIP_KEYGEN" != true ] && ! security find-generic-password \
       -s etzhayyim -a DID_PRIVATE_KEY_ED25519_KARUTE > /dev/null 2>&1; then
    echo "✘ Ed25519 keypair not found in Keychain. Generate via:"
    echo "  cat 50-infra/karute-did-web/README.md | sed -n '/keygen/,/security add-generic-password/p'"
    exit 1
  fi
  cd "$REPO_ROOT/50-infra/karute-did-web"
  run pnpm install --frozen-lockfile 2>/dev/null || run pnpm install
  run wrangler deploy
  cd "$REPO_ROOT"
}

stage_audit_worker() {
  echo "━━ Stage 2: audit DID Worker ━━"
  cd "$REPO_ROOT/50-infra/audit-did-web"
  run pnpm install --frozen-lockfile 2>/dev/null || run pnpm install
  run wrangler deploy
  cd "$REPO_ROOT"
}

stage_k8s_pod() {
  echo "━━ Stage 3: lg-karute Pod ━━"
  bash "$REPO_ROOT/50-infra/k8s/lg-karute/build.sh" --push
  run kubectl create namespace mitama-udf --dry-run=client -o yaml | kubectl apply -f -
  if [ -n "${GITHUB_USER:-}" ] && [ -n "${GITHUB_PAT:-}" ]; then
    run kubectl create secret docker-registry ghcr-pull \
      --namespace mitama-udf \
      --docker-server=ghcr.io \
      --docker-username="$GITHUB_USER" \
      --docker-password="$GITHUB_PAT" \
      --dry-run=client -o yaml | kubectl apply -f -
  else
    echo "ℹ GITHUB_USER/GITHUB_PAT unset — skipping ghcr-pull secret (assumes already configured)"
  fi
  run kubectl apply -f "$REPO_ROOT/50-infra/k8s/lg-karute/deployment.yaml"
  run kubectl -n mitama-udf rollout status deploy/lg-karute --timeout=180s
}

stage_cf_tunnel() {
  echo "━━ Stage 4: CF Tunnel (karu7t3e.etzhayyim.com → lg-karute) ━━"
  if ! command -v cloudflared > /dev/null 2>&1; then
    echo "✘ cloudflared not installed. brew install cloudflared"
    exit 1
  fi
  if ! cloudflared tunnel list 2>/dev/null | grep -q "lg-karute"; then
    run cloudflared tunnel create lg-karute
    run cloudflared tunnel route dns lg-karute karu7t3e.etzhayyim.com
  fi
  echo "ℹ Configure ~/.cloudflared/lg-karute-config.yaml then:"
  echo "   cloudflared tunnel run lg-karute &"
}

stage_pages_deploy() {
  echo "━━ Stage 5: Cloudflare Pages (Svelte SuperApp) ━━"
  cd "$REPO_ROOT/60-apps/etzhayyim-project-karute/appview/etzhayyim-wasm-karute-karu7t3e/svelte"
  run pnpm install
  run pnpm build
  run wrangler pages deploy dist --project-name karute --branch main
  cd "$REPO_ROOT"
}

stage_smoke() {
  echo "━━ Stage 6: Smoke ━━"
  echo "→ karute DID"
  run curl -fsS https://karute.etzhayyim.com/.well-known/did.json | jq .id || true
  echo "→ audit DID"
  run curl -fsS https://audit.etzhayyim.com/.well-known/did.json | jq .id || true
  echo "→ Universal Resolver"
  run curl -fsS https://dev.uniresolver.io/1.0/identifiers/did:web:karute.etzhayyim.com | jq '.didDocument.id' || true
  echo "→ XRPC health"
  run curl -fsS https://karute.etzhayyim.com/xrpc/com.etzhayyim.apps.karute.healthKarute || true
  echo "→ Static bundle"
  run curl -fsS -o /dev/null -w "%{http_code}\n" https://karute.etzhayyim.com/ || true
}

case "$STAGE" in
  did-worker) stage_did_worker ;;
  audit-worker) stage_audit_worker ;;
  k8s-pod) stage_k8s_pod ;;
  cf-tunnel) stage_cf_tunnel ;;
  pages-deploy) stage_pages_deploy ;;
  smoke) stage_smoke ;;
  "") stage_did_worker; stage_audit_worker; stage_k8s_pod; stage_cf_tunnel; stage_pages_deploy; stage_smoke ;;
  *) echo "Unknown stage: $STAGE" >&2; usage; exit 2 ;;
esac

echo "✓ Done"
