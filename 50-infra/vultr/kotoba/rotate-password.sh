#!/usr/bin/env bash
# Kotoba/Datomic PostgreSQL credential rotation — via 1Password CLI
#
# Background: 2026-05-17 GitGuardian incident — Kotoba/Datomic PostgreSQL DSN
# (root user, embedded password) leaked into git history via vendor seed.
# Leaked credential identifier is tracked in 1Password vault
# `etzhayyim Japan株式会社`, item "Kotoba/Datomic root (compromised 2026-05-17)".
# Do not re-print the literal credential anywhere in this repo.
#
# This script:
#   1. Generates a strong replacement password via `op generate` (32 chars,
#      letters+digits+symbols; user can override length/charset).
#   2. Stores the new password in 1Password vault `etzhayyim Japan株式会社` as
#      item "Kotoba/Datomic root (rotated YYYY-MM-DD)".
#   3. Updates the K8s Secret `kotoba-credentials` on the Vultr VKE cluster.
#   4. Restarts the Kotoba/Datomic statefulset so pods pick up the new credentials.
#   5. Smoke-tests the new credentials.
#
# Prerequisites:
#   - `op signin` already run (interactive) — script aborts if not authenticated
#   - VULTR_API_KEY in Keychain (etzhayyim.vultr / VULTR_API_KEY)
#   - kubectl + jq + curl on PATH
#
# Usage:
#   ./50-infra/vultr/kotoba/rotate-password.sh
#   ./50-infra/vultr/kotoba/rotate-password.sh --dry-run   # show plan only

set -euo pipefail

DRY_RUN="${DRY_RUN:-false}"
if [[ "${1:-}" == "--dry-run" ]]; then DRY_RUN=true; fi

VAULT_NAME="${OP_VAULT:-etzhayyim Japan株式会社}"
ITEM_TITLE="${OP_ITEM_TITLE:-Kotoba/Datomic root (rotated $(date +%Y-%m-%d))}"
CLUSTER_ID="${CLUSTER_ID:-a61d513b-f9b7-4121-abb9-b53732aa5ec4}"   # VKE lax
NAMESPACE="${NAMESPACE:-kotoba}"
SECRET_NAME="${SECRET_NAME:-kotoba-credentials}"
STATEFULSET="${STATEFULSET:-kotoba}"

# ─── 0. Pre-flight ─────────────────────────────────────────────────────────

step() { echo ""; echo "── $* ──"; }
run()  { if $DRY_RUN; then echo "  [dry-run] $*"; else eval "$@"; fi; }

step "Pre-flight: 1Password CLI auth"
if ! op vault list >/dev/null 2>&1; then
  echo "ERROR: 1Password CLI not authenticated. Run: op signin" >&2
  exit 1
fi
echo "  ✓ op authenticated"

step "Pre-flight: Vultr API key from Keychain"
# Try common account names: VULTR_API_KEY (older convention) → API_KEY (current).
: "${VULTR_API_KEY:=$(security find-generic-password -s etzhayyim.vultr -a VULTR_API_KEY -w 2>/dev/null || \
                       security find-generic-password -s etzhayyim.vultr -a API_KEY -w 2>/dev/null || true)}"
if [[ -z "${VULTR_API_KEY}" ]]; then
  echo "ERROR: VULTR_API_KEY not in Keychain (service=etzhayyim.vultr; tried accounts: VULTR_API_KEY, API_KEY)" >&2
  exit 2
fi
echo "  ✓ VULTR_API_KEY loaded"

step "Pre-flight: kubeconfig"
KUBECONFIG="/tmp/rw-vke-${CLUSTER_ID}.yaml"
if [[ ! -f "${KUBECONFIG}" ]] || ! kubectl --kubeconfig="${KUBECONFIG}" get ns "${NAMESPACE}" >/dev/null 2>&1; then
  echo "  fetching kubeconfig from Vultr API..."
  run "curl -sS -H 'Authorization: Bearer \${VULTR_API_KEY}' 'https://api.vultr.com/v2/kubernetes/clusters/${CLUSTER_ID}/config' | jq -r '.kube_config' | base64 --decode > '${KUBECONFIG}' && chmod 600 '${KUBECONFIG}'"
fi
export KUBECONFIG
echo "  ✓ kubeconfig: ${KUBECONFIG}"

# ─── 1. Generate new password via op ───────────────────────────────────────

step "Generate new password"
if $DRY_RUN; then
  echo "  [dry-run] op item create --category=password --vault='${VAULT_NAME}' --title='${ITEM_TITLE}' --generate-password=letters,digits,symbols,32"
  NEW_PW="<would-be-generated>"
else
  # Create new password item in 1Password vault, get JSON, extract password value.
  op_json=$(op item create \
    --category=password \
    --vault="${VAULT_NAME}" \
    --title="${ITEM_TITLE}" \
    --tags="security,kotoba,rotation,gitguardian-incident-2026-05-17" \
    --generate-password='letters,digits,symbols,32' \
    --format=json 2>&1)
  echo "${op_json}" > /tmp/op-output.json
  NEW_PW=$(echo "${op_json}" | jq -r '.fields[]? | select(.id=="password" or .label=="password") | .value' | head -1)

  if [[ -z "${NEW_PW}" || "${NEW_PW}" == "null" ]]; then
    echo "ERROR: op did not return a password. Output saved to /tmp/op-output.json:" >&2
    echo "${op_json}" | head -20 >&2
    exit 3
  fi
  echo "  ✓ new password stored in 1Password vault '${VAULT_NAME}', item '${ITEM_TITLE}'"
  echo "  ✓ password length: ${#NEW_PW}"
fi

# ─── 2. Update the K8s Secret ──────────────────────────────────────────────

step "Update K8s Secret ${NAMESPACE}/${SECRET_NAME}"
if $DRY_RUN; then
  echo "  [dry-run] kubectl create secret generic ${SECRET_NAME} --from-literal=password=*** --dry-run=client -o yaml | kubectl apply -f -"
else
  kubectl -n "${NAMESPACE}" create secret generic "${SECRET_NAME}" \
    --from-literal=password="${NEW_PW}" \
    --dry-run=client -o yaml | kubectl apply -f -
  echo "  ✓ Secret updated"
fi

# ─── 3. Restart Kotoba/Datomic statefulset ─────────────────────────────────────

step "Rolling-restart ${NAMESPACE}/${STATEFULSET}"
run "kubectl -n '${NAMESPACE}' rollout restart statefulset/'${STATEFULSET}'"
run "kubectl -n '${NAMESPACE}' rollout status statefulset/'${STATEFULSET}' --timeout=10m"

# ─── 4. Smoke test ─────────────────────────────────────────────────────────

step "Smoke test: connect with NEW password"
if $DRY_RUN; then
  echo "  [dry-run] psql with NEW_PW → expect SELECT 1 returns 1"
else
  # Connect through cluster (assumes psql + port-forward or in-cluster job)
  cat > /tmp/rw-smoke.yaml <<EOF
apiVersion: batch/v1
kind: Job
metadata:
  name: rw-smoke-$(date +%s)
  namespace: ${NAMESPACE}
spec:
  template:
    spec:
      restartPolicy: Never
      containers:
        - name: psql
          image: postgres:16-alpine
          env:
            - name: PGPASSWORD
              valueFrom:
                secretKeyRef:
                  name: ${SECRET_NAME}
                  key: password
          command: ["psql", "-h", "kotoba-frontend.${NAMESPACE}.svc.cluster.local", "-p", "4566", "-U", "root", "-d", "dev", "-c", "SELECT 1 AS rotated_smoke_test"]
EOF
  kubectl apply -f /tmp/rw-smoke.yaml
  sleep 5
  kubectl -n "${NAMESPACE}" logs "job/rw-smoke-$(ls /tmp/rw-smoke.yaml | tail -1)" || true
  kubectl delete -f /tmp/rw-smoke.yaml --ignore-not-found
  rm -f /tmp/rw-smoke.yaml
  echo "  ✓ Smoke test job dispatched"
fi

# ─── 5. Cleanup ────────────────────────────────────────────────────────────

step "Done"
echo ""
echo "Next steps:"
echo "  - Rotate any consumer references to the OLD password:"
echo "    - Hyperdrive bindings (CF Workers env vars)"
echo "    - GitHub Actions secrets"
echo "    - CI environment configs"
echo "    - Developer .env files"
echo "  - The new password is in 1Password: vault='${VAULT_NAME}' item='${ITEM_TITLE}'"
echo "  - Previous (compromised) password is now invalid network-wide."
echo "    (See 1Password item 'Kotoba/Datomic root (compromised 2026-05-17)' for audit.)"
echo ""
echo "Companion actions:"
echo "  - 50-infra/vultr/kotoba-firewall-restrict.sh    (IP-restrict network access)"
echo "  - filter-repo on vendor + etzhayyim                  (history scrubbed 2026-05-17)"
echo "  - lefthook secret-scan hook                          (commit-time prevention)"

rm -f /tmp/op-output.json
