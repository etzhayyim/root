#!/usr/bin/env bash
# Push the geth-private sealer key + keystore + password + address into
# the etzhayyim Vault, closing the "team backup (manual followup)" item from
# `50-infra/vultr/geth-private/CLAUDE.md` § Sealer key custody.
#
# This is the L3 leg of the 3-tier custody:
#   L1 .local-secrets/sealer.priv   (working copy, gitignored)
#   L2 macOS Keychain `etzhayyim.private-chain`           (iCloud sync)
#   L3 etzhayyim Vault `etzhayyim-private-chain`               ← THIS SCRIPT
#
# Loss of all three = unrecoverable chain.
#
# Usage:
#   etzhayyim authn signin                       # ensure session is fresh
#   bash 50-infra/vultr/geth-private/scripts/vault-investiture.sh
#
# Idempotent: skips Vault create if the folder already exists, skips
# `vault add` for items that already have a non-empty entry. Safe to
# re-run after sealer key rotation.
set -euo pipefail

DIR="$(cd "$(dirname "$0")/.." && pwd)"
LOCAL="$DIR/.local-secrets"
VAULT_NAME="etzhayyim-private-chain"

for f in sealer.priv sealer.address sealer.password sealer-keystore.json; do
  if [ ! -f "$LOCAL/$f" ]; then
    echo "fatal: $LOCAL/$f missing — run scripts/gen-sealer.mjs first" >&2
    exit 1
  fi
done

# Sanity: do we have a fresh etzhayyim session?
if ! etzhayyim authn whoami >/dev/null 2>&1; then
  echo "fatal: not signed in. Run \`etzhayyim authn signin\` first." >&2
  exit 1
fi

# Step 1 — ensure the Vault folder exists.
if etzhayyim vault list 2>/dev/null | awk '{print $2}' | grep -qx "$VAULT_NAME"; then
  echo "==> vault \"$VAULT_NAME\" already exists — reuse"
  VAULT_ID="$(etzhayyim vault list | awk -v n="$VAULT_NAME" '$2 == n {print $1; exit}')"
else
  echo "==> creating vault \"$VAULT_NAME\""
  etzhayyim vault create "$VAULT_NAME" \
    --description "etzhayyim 260425 Clique sealer key + keystore (L3 backup; loss of all three tiers = chain frozen)"
  VAULT_ID="$(etzhayyim vault list | awk -v n="$VAULT_NAME" '$2 == n {print $1; exit}')"
fi

if [ -z "${VAULT_ID:-}" ]; then
  echo "fatal: failed to resolve vault id for \"$VAULT_NAME\"" >&2
  exit 1
fi
echo "    vault id: $VAULT_ID"

# Step 2 — upload each item. `etzhayyim vault add --file` reads the local
# bytes, encrypts client-side under the operator's vaultKey, and uploads
# only ciphertext.
add_if_missing() {
  local item="$1" path="$2"
  if etzhayyim vault list-items "$VAULT_ID" 2>/dev/null | awk '{print $2}' | grep -qx "$item"; then
    echo "==> \"$item\" already in vault — skip"
  else
    echo "==> uploading \"$item\""
    etzhayyim vault add "$VAULT_ID" "$item" --file "$path"
  fi
}

add_if_missing "sealer.priv"           "$LOCAL/sealer.priv"
add_if_missing "sealer.address"        "$LOCAL/sealer.address"
add_if_missing "sealer.password"       "$LOCAL/sealer.password"
add_if_missing "sealer-keystore.json"  "$LOCAL/sealer-keystore.json"

# Step 3 — share with co-owners. Comma-separated DIDs are read from
# .vault-coowners (one DID per line). Lines starting with # are ignored.
COOWNERS="$DIR/.vault-coowners"
if [ -f "$COOWNERS" ]; then
  while IFS= read -r did; do
    [ -z "$did" ] && continue
    [[ "$did" =~ ^# ]] && continue
    echo "==> sharing with $did"
    etzhayyim vault share "$VAULT_ID" --member-did "$did" --role admin || true
  done < "$COOWNERS"
else
  echo "==> note: $COOWNERS not present — single-owner vault. Drop one DID per line into that file and re-run to add co-owners."
fi

echo
echo "==> done. Verify:  etzhayyim vault list-items $VAULT_ID"
echo "    Recover later with: etzhayyim vault get $VAULT_ID sealer.priv -o /tmp/recovered-sealer.priv"
