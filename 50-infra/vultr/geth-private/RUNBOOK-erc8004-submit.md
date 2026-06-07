# RUNBOOK — ERC-8004 chain submit (close `chain_submit_status: pending`)

> **HISTORICAL** — drove the legacy `etzhayyim agent-runtime publish-agent`
> command, which was removed along with `70-tools/etzhayyim/` on 2026-05-20.
> The IPFS pin + on-chain `registerAgent` flow needs to be re-implemented
> (e.g. as `e7m agent publish` or a Foundry script) before this runbook
> can be exercised again. Retained as design reference.

`deps.toml [geth_private.agent_runtime_publication]` carries
`chain_submit_status = "pending; publish-agent --dry-run=false pinned IPFS documents, but --submit-chain has not been enabled"`.
This runbook is the operator-side checklist that previously drove flipping
it to `"completed"`.

**Outcome**: yoro becomes the first on-chain registered agent on
`etzhayyimAgentRegistry` (chainId 260425), `vertex_agent_publication` gets a
real `tokenId`, and `geth-private.agent_runtime_publication.chain_submit_status`
moves to `"completed"`.

**Prereqs (in order, do not skip)**

1. PR #1145 merged (✅ done — `acdf88caf01`).
2. Sealer key custody confirmed:
   - `ls 50-infra/vultr/geth-private/.local-secrets/sealer.priv` — exists
   - `security find-generic-password -s "etzhayyim.private-chain" -a "SEALER_PRIV" -w | head -c 4` — prints `0x` (Keychain L2)
   - **L3 Vault**: run `bash 50-infra/vultr/geth-private/scripts/vault-investiture.sh` first if not already done. This runbook continues with L1 + L2 only as fallback, but L3 is required for prod.
3. `geth.etzhayyim.com` healthy:
   ```bash
   curl -sS -X POST https://geth.etzhayyim.com \
     -H 'Content-Type: application/json' \
     -d '{"jsonrpc":"2.0","id":1,"method":"eth_chainId"}'
   # → {"result":"0x3f949"}
   ```
4. `ipfs.etzhayyim.com` healthy:
   ```bash
   curl -sS https://ipfs.etzhayyim.com/api/v0/version
   ```

## Step 1 — render + dry-run

```bash
cd /path/to/etzhayyim-root
# etzhayyim agent-runtime publish-agent \  (removed 2026-05-20)
  --dry-run \
  --cluster murakumo-vke \
  --registration 50-infra/multicluster/murakumo-vke/yoro-actors/public-agent-registration.template.json \
  50-infra/multicluster/murakumo-vke/yoro-actors/actor-workers.yaml
```

Verify:
- `runtime.cid == "DRY_RUN_RUNTIME_CID"` (placeholder confirmed)
- `agentRegistration.sha256` is `0x` + 64 hex chars (deterministic)
- no error about missing `rootIdentity.rootDid` / `rootIdentity.address`

## Step 2 — publish to IPFS (no chain yet)

```bash
# etzhayyim agent-runtime publish-agent \  (removed 2026-05-20)
  --dry-run=false \
  --ipfs http://144.202.126.131 \
  --cluster murakumo-vke \
  --registration 50-infra/multicluster/murakumo-vke/yoro-actors/public-agent-registration.template.json \
  --registration-out /tmp/yoro-agent-registration.json \
  50-infra/multicluster/murakumo-vke/yoro-actors/actor-workers.yaml
```

Capture the printed `agentRegistration.cid` — call it `$AGENT_CID` for the
next step.

## Step 3 — submit on-chain `registerAgent` (the actual cutover)

```bash
ROOT_DID="$(security find-generic-password -s "etzhayyim.private-chain" -a "YORO_ROOT_DID" -w 2>/dev/null \
  || jq -r '.rootIdentity.rootDid' /tmp/yoro-agent-registration.json)"
OWNER="$(jq -r '.rootIdentity.address' /tmp/yoro-agent-registration.json)"

# etzhayyim agent-runtime publish-agent \  (removed 2026-05-20)
  --dry-run=false \
  --submit-chain \
  --ipfs http://144.202.126.131 \
  --cluster murakumo-vke \
  --registration 50-infra/multicluster/murakumo-vke/yoro-actors/public-agent-registration.template.json \
  --registration-out /tmp/yoro-agent-registration.published.json \
  --root-did "$ROOT_DID" \
  --owner "$OWNER" \
  50-infra/multicluster/murakumo-vke/yoro-actors/actor-workers.yaml
```

Expected stdout includes:
```json
{
  "ok": true,
  "submitChain": true,
  "registerAgent": {
    "tokenId": "1",
    "txHash": "0x…",
    "blockNumber": "…"
  }
}
```

Sealer key access went through `cast send` under the hood (the legacy
reference pattern was `70-tools/etzhayyim/etzhayyim/eth_deploy_receipt.go`, removed
2026-05-20). The sealer pre-funded balance (~$10^41 NETH-equiv, see
`50-infra/vultr/geth-private/CLAUDE.md`) covers the gas trivially.

## Step 4 — verify on chain + Kotoba/Datomic projection

```bash
# 4a. eth_call AgentRegistry
cast call 0xbfe74a0D3BBB3D77bCd16fDe2C64741eF4472F8E \
  'agentByRootDidHash(bytes32)(uint256)' \
  "$(cast keccak "$ROOT_DID")" \
  --rpc-url https://geth.etzhayyim.com
# → 1   (token id)

# 4b. Kotoba/Datomic projection (chain event sync runs every minute)
pnpm --filter @etzhayyim/graph-schema sync:agent-runtime-events -- --apply --flush

# 4c. count
cd 30-graph/graph-schema
pnpm tsx scripts/sync-rw-agent-runtime-events.mjs --status
# → verified_agent_publications: 1
```

## Step 5 — flip the deps.toml flag

```toml
# 50-infra/vultr/geth-private/deps.toml — [geth_private.agent_runtime_publication]
chain_submit_status = "completed; first_published_agent=yoro tokenId=1 (2026-04-XX)"
```

Commit with `refs ADR-2604262100`.

## Rollback / failure cases

| Symptom | Cause | Fix |
|---|---|---|
| `--submit-chain requires --dry-run=false` | flag combo | drop `--dry-run` in Step 3 |
| `--root-did is required` | rootIdentity.rootDid empty in template | check `public-agent-registration.template.json` |
| `eth_sendRawTransaction` 401 | privileged path on geth-rpc-proxy | NOT this case — `eth_sendRawTransaction` is **public** per `geth-rpc-proxy/DEPLOY.md` Auth model |
| `nonce too low` | concurrent sealer use (etzhayyim deploy + this) | wait 10s, retry |
| chain tx mined but registry returns 0 | wrong `--registry` | confirm address matches `[geth_private.contracts] etzhayyim_agent_registry = 0xbfe74a0D3BBB3D77bCd16fDe2C64741eF4472F8E` (V2) |

## Why this is the next phase

`agent_runtime_publication` is the `did:erc725` ↔ `did:web` ↔ ERC-8004
bridge described in ADR-2604262100. Until step 5 runs, every
`vertex_agent_publication` row from Kotoba/Datomic is a **dry-run** record —
useful for schema validation but not federable. Closing this loop
unlocks: (a) external agents querying `etzhayyimAgentRegistry.agentByRootDidHash`
for trust-anchored `agentURI`, (b) `ActorRuntimeRegistry` execution
receipts referencing a real `tokenId`, (c) the platform's first
end-to-end "ERC-725 root → ERC-8004 agent → IPFS runtime → on-chain
receipt" attestation chain.
