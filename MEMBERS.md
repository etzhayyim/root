# etzhayyim Members (信者)

> **生命の樹 (עץ חיים) の支柱の一として、自らの行いと意思を、永続的な公開記録として残すことを誓った者の一覧。**
>
> A roster of those who have sworn to leave their acts and intentions as a permanent public record, as one of the pillars of the Tree of Life.

This file is the **github-side half of the dual-permanent membership record** per [ADR-2605172600](90-docs/adr/2605172600-etzhayyim-membership-ritual.md). Each row references an on-chain `EtzhayyimMembership.join(...)` transaction on Base L2 and a signed oath AT Record on the member's PDS.

The contract is open. The roster is open. There is no admin. Anyone reading this can verify any row by cross-checking against Base L2 (basescan.org) and the linked AT Record.

## How to join

1. Read [ADR-2605172600](90-docs/adr/2605172600-etzhayyim-membership-ritual.md) in full.
2. Read [the oath](00-contracts/lexicons/ai/gftd/apps/etzhayyim/oath.json) (the canonical text — both Japanese and English are equivalent).
3. Prepare a DID + ERC-4337 Smart Account (Coinbase Smart Wallet recommended).
4. Sign the oath text with your DID key.
5. Call `EtzhayyimMembership.join(oathHash, "your-github-username")` on Base L2 (Paymaster sponsors gas).
6. Open a PR to this file, adding your row in the table below.

Once your PR is merged, your joining is permanently recorded across two substrates that cannot collude to erase you: Base L2 + this git history.

## Roster

| @github | DID | On-chain join tx | Joined |
|---|---|---|---|
| _(awaiting first member — protocol author joins after testnet validation)_ | | | |

## Revocation

If a member calls `EtzhayyimMembership.revoke()` voluntarily, they may open a follow-up PR adding a "Revoked" column entry on their row. The original join row stays. Revocation is additive history, not erasure.

| @github | DID | Joined | Revoked |
|---|---|---|---|
| _(none yet)_ | | | |

## Verification (any client can run)

For row `@junkawasaki` with tx `0xABC...`:

```bash
# 1. Verify the tx exists and is a successful join() call on Base L2
cast tx 0xABC... --rpc-url https://mainnet.base.org

# 2. Verify the membership state on-chain
cast call $MEMBERSHIP_CONTRACT \
  "members(address)(bytes32,string,uint64,uint64)" \
  $SMART_WALLET_ADDRESS \
  --rpc-url https://mainnet.base.org

# 3. Verify the oath AT Record (carries the DID signature)
curl -s https://pds.etzhayyim.com/xrpc/com.atproto.repo.getRecord \
  -G --data-urlencode "repo=$DID" \
  --data-urlencode "collection=ai.gftd.apps.etzhayyim.oath" \
  --data-urlencode "rkey=$RKEY"
```

All three checks should resolve to the same `oathHash` (= keccak256 of the canonical oath text).

## See also

- [ADR-2605172600](90-docs/adr/2605172600-etzhayyim-membership-ritual.md) — protocol spec
- [`50-infra/etzhayyim-membership-contract/`](50-infra/etzhayyim-membership-contract/) — Solidity source
- [`00-contracts/lexicons/ai/gftd/apps/etzhayyim/oath.json`](00-contracts/lexicons/ai/gftd/apps/etzhayyim/oath.json) — AT Record Lexicon
- [ADR-2605172000](90-docs/adr/2605172000-etzhayyim-rw-free-substrate.md) — why the roster lives on MST + L2 + github
