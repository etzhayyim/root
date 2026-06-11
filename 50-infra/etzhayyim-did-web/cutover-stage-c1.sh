#!/usr/bin/env bash
# Stage C-1 cutover script for `did:web:etzhayyim.com`.
#
# Per ADR-2605231525 + STAGE-C1-DID-CUTOVER.md. This script automates
# Steps 2 – 5 of the cutover: it substitutes the Council Safe address
# into `did-multi-controller.json`, computes the canonical hash, and
# emits the attestation envelope. Steps 4 (Council signing) and 6
# (git commit + wrangler deploy) are operator actions.
#
# Usage:
#     ./cutover-stage-c1.sh <safe-address> [<rpc-url>]
#
# Example:
#     ./cutover-stage-c1.sh 0xAbCd...1234 https://mainnet.base.org

set -euo pipefail

SAFE_ADDR="${1:-}"
RPC_URL="${2:-https://mainnet.base.org}"

if [ -z "$SAFE_ADDR" ]; then
  echo "usage: $0 <safe-address> [<rpc-url>]" >&2
  exit 2
fi
if ! echo "$SAFE_ADDR" | grep -qE '^0x[a-fA-F0-9]{40}$'; then
  echo "✘ safe-address must be a 0x-prefixed 20-byte hex string" >&2
  exit 2
fi

cd "$(dirname "$0")"

if [ ! -f did-multi-controller.json ]; then
  echo "✘ did-multi-controller.json missing in $(pwd)" >&2
  exit 2
fi

command -v jq >/dev/null || { echo "✘ jq required" >&2; exit 2; }
command -v sha256sum >/dev/null \
  || command -v shasum >/dev/null \
  || { echo "✘ sha256sum or shasum required" >&2; exit 2; }

sha256_of() {
  if command -v sha256sum >/dev/null; then
    sha256sum "$1" | cut -d' ' -f1
  else
    shasum -a 256 "$1" | cut -d' ' -f1
  fi
}

echo "Step 2 — substituting Council Safe address into did-multi-controller.json …"
sed -i.bak \
  -e "s/0x0000000000000000000000000000000000000000/$SAFE_ADDR/g" \
  did-multi-controller.json
rm -f did-multi-controller.json.bak

echo "Step 3 — stripping _comment_* fields → canonical document …"
jq 'walk(if type == "object" then with_entries(select(.key | startswith("_comment_") | not)) else . end)' \
  did-multi-controller.json > did-multi-controller.canonical.json

DOC_HASH=$(sha256_of did-multi-controller.canonical.json)
echo "$DOC_HASH" > did-multi-controller.attestation.hash

echo "    canonical sha256: $DOC_HASH"

echo "Step 3 — emitting attestation envelope (signatures: empty) …"
NOW=$(date -u +%Y-%m-%dT%H:%M:%SZ)
cat > did-multi-controller.attestation.json <<EOF
{
  "version": 1,
  "purpose": "did:web:etzhayyim.com Stage C-1 cutover attestation",
  "adr": "ADR-2605231525",
  "document_hash_sha256": "$DOC_HASH",
  "council_safe": "$SAFE_ADDR",
  "chain_id": 8453,
  "rpc_url": "$RPC_URL",
  "valid_after": "$NOW",
  "signatures": []
}
EOF

cat <<NEXT

Stage C-1 prep complete.

  written:
    did-multi-controller.canonical.json      (JCS-stripped, ready to publish)
    did-multi-controller.attestation.json    (signatures: empty)
    did-multi-controller.attestation.hash    ($DOC_HASH)

  next:
    Step 4 (Council off-line):
      Each of ≥5 Council signers signs the literal message
        "etzhayyim DID Stage C-1 cutover | sha256:$DOC_HASH"
      with their own EOA. Append each signature to the
      attestation.signatures array.

    Step 5:  ./verify-stage-c1-attestation.sh
    Step 6:  mv did.json did.json.prev-c1
             mv did-multi-controller.canonical.json did.json
             git add did.json did.json.prev-c1 did-multi-controller.attestation.json
             git commit -m "stage-c1: cutover did:web:etzhayyim.com to Council Safe (5-of-7)"
             wrangler deploy

  ADR: ../../90-docs/adr/2605231525-no-server-key-religious-corp-architecture.md
  Runbook: ./STAGE-C1-DID-CUTOVER.md
NEXT
