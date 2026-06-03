# yatabase /api/donate — operator deploy runbook

Per [ADR-2605231525](../../90-docs/adr/2605231525-no-server-key-religious-corp-architecture.md)
Stage A, the yatabase Worker holds **no signing capability** for
donations. The Worker only verifies member-signed USDC transfers
against a public Base L2 RPC. This runbook walks the operator
through the deploy + verification flow.

## Prerequisites

1. **Bootstrap Council Treasury Safe** (5-of-7 multisig) is deployed
   on Base L2 mainnet. Note the deployed address.
2. **TitheRouter v1** (per ADR-2605202030) is deployed on Base L2.
   Note the deployed address.
3. **wrangler** CLI is authenticated against the Cloudflare account
   that owns the `magatama-y4t4b4se` Worker.

## Step 1 — Edit `wrangler.jsonc` placeholder addresses

Open `60-apps/ai-gftd-project-yatabase/wrangler.jsonc`. Under
`vars`, replace the two zero-address placeholders with the actual
on-chain addresses:

```jsonc
"YATA_DONATE_TREASURY":     "0x<your-treasury-safe-address>",
"YATA_DONATE_TITHE_ROUTER": "0x<your-tithe-router-address>"
```

Both fields carry the `no-server-key: read-only` marker because
they are public on-chain addresses. They do **not** grant the
Worker any signing capability.

If you want a different per-tx cap, edit `YATA_DONATE_MAX_USDC_MICROS`.
The default is 100,000 USDC (100_000_000_000 base units of 6-decimal
USDC).

## Step 2 — (Optional) override the Base L2 RPC

The default is the Coinbase-operated public RPC
(`https://mainnet.base.org`). To use a private RPC (Alchemy / Infura /
self-hosted), override `YATA_DONATE_RPC_URL`. The URL is itself
read-only — there is no key.

## Step 3 — Deploy

```bash
cd 60-apps/ai-gftd-project-yatabase

# (one time) sanity-check no forbidden secrets are leaking in
( cd ../.. && python3 -c "
from pathlib import Path
import sys; sys.path.insert(0, '70-tools/e7m/src')
from e7m.commands import _check_no_server_key
ok, ev = _check_no_server_key(Path('.').resolve())
print('no-server-key:', 'PASS' if ok else 'FAIL')
for line in ev[:5]: print(' ', line)
" )

# typecheck
pnpm typecheck

# build the Svelte Studio bundle
pnpm studio:build

# deploy. The legacy `gftd deploy` wrapper still works; bare
# wrangler also works since this Worker has no internal
# scaffolding hooks.
wrangler deploy
```

## Step 4 — Smoke (verify-only)

```bash
# Submit a tiny test donation FROM YOUR OWN WALLET on Base L2.
# 1. Open https://yatabase.etzhayyim.com/studio/billing
# 2. Click "Upgrade via USDC donation — $33" (or any plan)
# 3. Approve the USDC.transfer in your wallet
# 4. Wait for confirmation; the page polls automatically.
# 5. The Worker returns a verified paymentReceipt.

# Or test the verify endpoint directly with an existing on-chain tx:
curl -X POST https://yatabase.etzhayyim.com/api/donate \
  -H "Authorization: Bearer sk_live_yata_<your-key>" \
  -H "Content-Type: application/json" \
  -d '{
    "txHash": "0x<a-real-confirmed-tx>",
    "purpose": "donation",
    "memo": "smoke test"
  }'
```

Expected response shape on success:

```jsonc
{
  "ok": true,
  "txHash": "0x...",
  "paymentReceipt": {
    "txHash": "0x...",
    "blockNumber": 12345678,
    "from": "0x<donor-wallet>",
    "to":   "0x<treasury>",
    "amountUsdcMicros": "1000000",
    "purpose": "donation"
  },
  "message": "Donation verified. Commit `com.etzhayyim.apps.payment.sent` to your own PDS …"
}
```

Failure cases the Worker explicitly handles:

- `TxNotConfirmed` (HTTP 404) — tx has no receipt yet
- `TxReverted` (400) — tx exists but reverted on-chain
- `TransferNotFound` (400) — receipt has no USDC Transfer log to the configured treasury / TitheRouter
- `ZeroAmount` (400) — transfer amount is 0
- `OverCap` (403) — amount exceeds `YATA_DONATE_MAX_USDC_MICROS`
- `RecipientUnconfigured` (503) — Worker config still has placeholder zero addresses
- `RpcUnavailable` (502) — Base L2 RPC didn't respond

In **none** of these cases does the Worker sign anything — the
on-chain transaction either exists (and is valid or not) or it
doesn't. The Worker just declines to emit the receipt.

## Step 5 — Decommission `YATA_DONATE_PRIVATE_KEY` (if it was ever set)

```bash
wrangler secret delete YATA_DONATE_PRIVATE_KEY
```

The Worker no longer reads this name. `wrangler secret list` after
the delete should not show it; the next deploy proves the Worker
runs without it.

## Step 6 — Verify the e7m invariant

```bash
cd 70-tools/e7m && python3 -c "
import sys
sys.path.insert(0, 'src')
from e7m.commands import verify
import json
r = verify()
print(json.dumps([
  {'key': c['key'], 'passed': c['passed']} for c in r['checks']
], indent=2))
"
```

The `no_server_key` row should not flag the yatabase `wrangler.jsonc`
(treasury / TitheRouter / RPC URL / max-micros / USDC contract are
all read-only and carry the `no-server-key: read-only` marker).

## Rollback

If verification regresses for any reason (e.g. the treasury Safe
address was wrong), reverting Step 1 (zeros) puts the endpoint
into `RecipientUnconfigured` (503) state — no donation gets
accepted, but no donation gets lost either, because the Worker
never signs and the member's on-chain tx is unaffected.

## See also

- [`src/donate.ts`](src/donate.ts) — the verify-only handler
- [`svelte/src/routes/studio/billing/+page.svelte`](svelte/src/routes/studio/billing/+page.svelte) — wallet-sign UI
- [ADR-2605231525](../../90-docs/adr/2605231525-no-server-key-religious-corp-architecture.md) — full architectural posture
- [`CHARTER-RIDER.md` Annex A](../../CHARTER-RIDER.md#annex-a--proposed-1-platform-posture-amendment-pending-council-ratification) — PLATFORM POSTURE pending ratification
