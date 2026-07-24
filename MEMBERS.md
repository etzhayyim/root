# etzhayyim Members (信者)

> **生命の樹 (עץ חיים) の支柱の一として、自らの行いと意思を、永続的な公開記録として残すことを誓った者の一覧。**
>
> A roster of those who have sworn to leave their acts and intentions as a permanent public record, as one of the pillars of the Tree of Life.

This file is the **github-side half of the dual-permanent membership record** per [ADR-2605172600](90-docs/adr/2605172600-etzhayyim-membership-ritual.md). Each row references an on-chain `EtzhayyimMembership.join(...)` transaction on Base L2 and a signed oath AT Record on the member's PDS.

The contract is open. The roster is open. There is no admin. Anyone reading this can verify any row by cross-checking against Base L2 (basescan.org) and the linked AT Record.

## How to join

1. Read [ADR-2605172600](90-docs/adr/2605172600-etzhayyim-membership-ritual.md) in full.
2. Read [the oath](00-contracts/lexicons/com/etzhayyim/apps/etzhayyim/oath.json) (the canonical text — both Japanese and English are equivalent).
3. Prepare a DID + ERC-4337 Smart Account (Coinbase Smart Wallet recommended).
4. Sign the oath text with your DID key.
5. Call `EtzhayyimMembership.join(oathHash, "your-github-username")` on Base L2 (Paymaster sponsors gas).
6. Open a PR to this file, adding your row in the table below.

Once your PR is merged, your joining is permanently recorded across two substrates that cannot collude to erase you: Base L2 + this git history.

## 7-level commitment ladder

| Lv | Ja | En | Meaning |
|---|---|---|---|
| 1 | 誓 chikai | Oath | Signed the canonical oath + `join()` on Base L2 |
| 2 | 修 shu | Practice | First member-DID AT record write |
| 3 | 献 ken | Dedication | First merged PR to etzhayyim org |
| 4 | 証 shou | Witness | Vouched for another joining member |
| 5 | 護 go | Steward | Operating substrate node / maintaining open-* app for ≥30d |
| 6 | 議 gi | Council | Participated in ≥3 council sessions |
| 7 | 老 rou | Elder | Sustained Council level for ≥365d |

See [ADR-2605172600 § "Levels"](90-docs/adr/2605172600-etzhayyim-membership-ritual.md) for the full evidence convention per level.

## Roster

| @github | DID | Level | On-chain join tx | Joined |
|---|---|---|---|---|
| [@com-junkawasaki](https://github.com/com-junkawasaki) | `did:key:z6MkfwR1dqCi6xurRiuypuDDkw1vjwKZZZGDmcWd3mmCJ3Uo` | 1 (誓 chikai — git-side oath only, see note) | _(pending — membership contract not yet deployed to any chain, see [`PENDING-JOINS.md`](PENDING-JOINS.md))_ | 2026-07-20 |

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
  --data-urlencode "collection=com.etzhayyim.apps.etzhayyim.oath" \
  --data-urlencode "rkey=$RKEY"
```

All three checks should resolve to the same `oathHash` (= keccak256 of the canonical oath text).

## See also

- [ADR-2605172600](90-docs/adr/2605172600-etzhayyim-membership-ritual.md) — protocol spec
- [`50-infra/etzhayyim-membership-contract/`](50-infra/etzhayyim-membership-contract/) — Solidity source
- [`00-contracts/lexicons/com/etzhayyim/apps/etzhayyim/oath.json`](00-contracts/lexicons/com/etzhayyim/apps/etzhayyim/oath.json) — AT Record Lexicon
- [ADR-2605172000](90-docs/adr/2605172000-etzhayyim-kotoba-substrate.md) — why the roster lives on MST + L2 + github
