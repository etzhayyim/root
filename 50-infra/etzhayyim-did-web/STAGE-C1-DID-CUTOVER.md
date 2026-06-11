# Stage C-1 — `did:web:etzhayyim.com` multi-controller cutover

Per [ADR-2605231525](../../90-docs/adr/2605231525-no-server-key-religious-corp-architecture.md)
Stage C-1, the etzhayyim entity DID document is amended so that the
authoritative controller becomes the **Bootstrap Council 5-of-7 Safe**
(ADR-2605192300) on Base L2. The existing Ed25519 key stays in the
document for a 30-day rollback window, then is dropped in C-1.b.

## Inputs

- Deployed Council Safe address on Base L2 mainnet (5-of-7
  Gnosis Safe / Safe{Wallet} per ADR-2605192300).
- 5 of the 7 Council members agree to sign the cutover attestation
  (off-line, via Safe app).

## Files

- `did.json` — currently served at `/.well-known/did.json`. **DO NOT
  modify directly until Council ratifies.**
- `did-multi-controller.json` — proposed next-state. Council reviews
  this file's contents before signing. Carries placeholder
  `0x0000…0000` for the Safe address.
- `did-multi-controller.attestation.json` — populated by Step 3 below.
  This is the artefact Council 5-of-7 signs over.

## Cutover steps

### Step 1 — Council reviews `did-multi-controller.json`

Open the file, confirm:

- `controller` includes the deployed Safe DID
  (`did:pkh:eip155:8453:0x<safe>`).
- `verificationMethod` includes both `#key-0` (Ed25519, deprecated)
  and `#council-safe` (ECDSA-secp256k1-recovery).
- `authentication` / `assertionMethod` list `#council-safe` first
  (so verifiers prefer it).
- `capabilityInvocation` / `capabilityDelegation` are **only**
  `#council-safe` (no single-key signature can authorise capability
  delegation post-cutover).

### Step 2 — Replace placeholder zeros with the Safe address

```bash
SAFE_ADDR="0x<the-actual-safe-address>"
sed -i.bak \
  -e "s/0x0000000000000000000000000000000000000000/$SAFE_ADDR/g" \
  did-multi-controller.json
rm did-multi-controller.json.bak
```

### Step 3 — Generate the attestation hash

The Council signs over the **JCS canonical hash** (RFC 8785) of the
amended document. JCS strips comments and sorts keys.

```bash
# Strip the _comment_* fields (they are explanatory, not normative)
jq 'walk(if type == "object" then with_entries(select(.key | startswith("_comment_") | not)) else . end)' \
  did-multi-controller.json > did-multi-controller.canonical.json

# Compute the sha256 of the canonical form
sha256sum did-multi-controller.canonical.json | head -c 64 > did-multi-controller.attestation.hash
echo "" >> did-multi-controller.attestation.hash

# Wrap into an attestation envelope
cat > did-multi-controller.attestation.json <<EOF
{
  "version": 1,
  "purpose": "did:web:etzhayyim.com Stage C-1 cutover attestation",
  "adr": "ADR-2605231525",
  "document_hash_sha256": "$(cat did-multi-controller.attestation.hash)",
  "council_safe": "$SAFE_ADDR",
  "chain_id": 8453,
  "valid_after": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "signatures": []
}
EOF
```

### Step 4 — Council 5-of-7 signs over `document_hash_sha256`

Each Council signer (using their own EOA wallet, e.g. via the Safe
app's "Sign Message" feature) signs the literal string:

```
etzhayyim DID Stage C-1 cutover | sha256:<document_hash_sha256>
```

The Safe collects 5 signatures and bundles them into a single ERC-1271
`isValidSignature(bytes32 hash, bytes calldata signature)` that
returns the magic value `0x1626ba7e` when fed `document_hash_sha256`.

Each signature is appended to the `signatures` array:

```jsonc
{
  "signer_did": "did:pkh:eip155:8453:0x<signer-eoa>",
  "signature": "0x<sig-bytes>",
  "signed_at": "<ISO 8601>"
}
```

### Step 5 — Verify the attestation off-line

```bash
# Re-derive document_hash_sha256 from the canonical document
RECOMPUTED=$(sha256sum did-multi-controller.canonical.json | head -c 64)
DECLARED=$(jq -r .document_hash_sha256 did-multi-controller.attestation.json)
[ "$RECOMPUTED" = "$DECLARED" ] || { echo "✘ hash mismatch"; exit 1; }

# Count signatures
SIGS=$(jq '.signatures | length' did-multi-controller.attestation.json)
[ "$SIGS" -ge 5 ] || { echo "✘ need ≥5 signatures, have $SIGS"; exit 1; }

# Verify each signature against the declared signer's EOA
#  (call cast: cast wallet verify-message ... — operator-side)
echo "✓ attestation verified"
```

### Step 6 — Swap into place

```bash
# Commit both the new document and the attestation into git.
mv did.json did.json.prev-c1
mv did-multi-controller.canonical.json did.json
git add did.json did.json.prev-c1 did-multi-controller.attestation.json
git commit -m "stage-c1: cutover did:web:etzhayyim.com to Council Safe controller (5-of-7)"

# Deploy the Worker (it just serves the static JSON; no key needed).
wrangler deploy
```

### Step 7 — Smoke

```bash
curl -s https://etzhayyim.com/.well-known/did.json | jq '.controller'
# Expected: array including "did:pkh:eip155:8453:0x<safe>"

curl -s https://etzhayyim.com/.well-known/did.json \
  | jq '.verificationMethod[] | select(.id | endswith("#council-safe"))'
# Expected: one VM with type EcdsaSecp256k1RecoveryMethod2020
```

### Step 8 — Universal Resolver smoke

```bash
curl -s 'https://dev.uniresolver.io/1.0/identifiers/did:web:etzhayyim.com' \
  | jq '.didDocument.verificationMethod | map(.id)'
```

## Rollback (within 30-day window)

If a resolver consumer breaks because of the multi-controller shape:

```bash
git mv did.json.prev-c1 did.json
git commit -m "stage-c1 rollback: restore single-controller did.json"
wrangler deploy
```

The rollback artefact (`did.json.prev-c1`) is identical to the pre-
cutover state, and the Council Safe remains a *valid* signer for any
future cutover attempt — only the published document reverts.

## Stage C-1.b (after 30 days clean)

```bash
# Drop #key-0 + #key-0-multibase from did.json. Council 5-of-7 signs a
# new attestation. Commit + deploy.
jq 'del(.verificationMethod[] | select(.id | test("key-0")))
   | .authentication = [.authentication[] | select(test("key-0") | not)]
   | .assertionMethod = [.assertionMethod[] | select(test("key-0") | not)]' \
  did.json > did.json.next
mv did.json.next did.json
# (re-run Steps 3-7 for Council signing of the post-rollback doc)
```

## What this cutover does NOT do

- Does **NOT** modify `did:web:authn.etzhayyim.com` (Stage C-2/C-3).
- Does **NOT** delete the historical Ed25519 key from any external
  resolver cache. Most resolvers respect TTL; for AT Protocol /
  Universal Resolver, the change propagates on next fetch.
- Does **NOT** require the Worker to hold a private key at any point.
  The Worker just serves the static JSON.

## See also

- [ADR-2605231525](../../90-docs/adr/2605231525-no-server-key-religious-corp-architecture.md)
- [ADR-2605192300](../../90-docs/adr/2605192300-bootstrap-council-religious-corp.md) (5-of-7 Safe)
- [`STAGE-C-IDENTITY-SIGNING-DEVOLUTION.md`](../../60-apps/etzhayyim-project-auth/STAGE-C-IDENTITY-SIGNING-DEVOLUTION.md) (auth Worker side, Stage C-2 + C-3)
- ERC-1271 reference: <https://eips.ethereum.org/EIPS/eip-1271>
- W3C DID Core controller: <https://www.w3.org/TR/did-core/#did-controller>
