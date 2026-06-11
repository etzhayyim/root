# etzhayyim-membership-contract

**Smart contract for etzhayyim 信者 (follower / member) registration on Base L2.** Implements ADR-2605172600 — joining the religious-corp via a dual-permanent record (Base L2 tx + github commit) bound by a signed oath.

Foundry Solidity project. Scaffold v0.0.0; tested logic + deploy script, not yet deployed.

## What it does

```
aspirant Smart Wallet ──▶ EtzhayyimMembership.join(oathHash, githubUsername)
                          │
                          ├─ emit Joined(member, oathHash, githubUsername)
                          ├─ store in mapping(address => Member)
                          └─ append to allMembers[] (enumeration)
                                       ▲
                                       │
                          any reader ──┘  via members(addr), memberCount(), listMembers(offset, limit)
```

## Why immutable, no admin

The contract has **no admin function**. No `setOwner`, no `pause`, no `upgrade`, no `expel`. Same governance posture as `EtzhayyimAnchor` (ADR-2605171800).

The social meaning of membership comes from:
1. the **oath text** the aspirant explicitly signs (off-chain, recorded as `com.etzhayyim.apps.etzhayyim.oath` AT Record);
2. the **public roster** (anyone can read);
3. the **github commit** added to `MEMBERS.md` (dual-permanence with on-chain).

It does **not** come from an authority approving the joining. Anyone with a valid Smart Account on Base L2 + the courage to make the public commitment can join. There is no waitlist.

If a member misbehaves: there is no on-chain expulsion, by design. Community signal happens through separate records (a future `censure` record type, observable but non-binding) and through the natural social cost of having one's name permanently in the public roster.

## Status

**Scaffold v0.0.0**. Solidity source + Foundry config + 5 unit tests. Not yet deployed.

## Layout

```
etzhayyim-membership-contract/
├── README.md
├── foundry.toml
├── src/
│   └── EtzhayyimMembership.sol
├── test/
│   └── EtzhayyimMembership.t.sol
├── script/
│   └── Deploy.s.sol
└── .gitignore
```

## Deploy

```bash
forge install
forge build
forge test -vv

# Testnet first
forge script script/Deploy.s.sol:Deploy \
  --rpc-url https://sepolia.base.org \
  --broadcast --private-key $DEPLOYER_PRIVATE_KEY \
  --verify --etherscan-api-key $BASESCAN_KEY

# Mainnet (after testnet + Safe-controlled deploy key)
forge script script/Deploy.s.sol:Deploy \
  --rpc-url https://mainnet.base.org \
  --broadcast --private-key $DEPLOYER_PRIVATE_KEY \
  --verify --etherscan-api-key $BASESCAN_KEY
```

After deploy, record the address in `deps.toml [platform.l2.membership_contract].address_*`, then add the contract to the Paymaster allowlist via `EtzhayyimPaymaster.setAllowedTarget(membership, true)`.

## Joining ritual (per ADR-2605172600)

For aspirants — the full 6-step ritual lives in ADR-2605172600. Programmatic flow once the SDK lands `join()`:

```typescript
import { Etzhayyim } from "@etzhayyim/sdk";

const e = new Etzhayyim({ /* ... */ });

const receipt = await e.join({
  language: "ja",               // or "en"
  githubUsername: "junkawasaki", // optional
});
// → { txHash, recordUri, blockNumber, smartWalletAddress, joinedAt }
//
// Now open a PR to https://github.com/etzhayyim/root/MEMBERS.md
// adding your row referencing receipt.txHash.
```

## See also

- [ADR-2605172600](../../90-docs/adr/2605172600-etzhayyim-membership-ritual.md)
- [Oath Lexicon](../../00-contracts/lexicons/com/etzhayyim/apps/etzhayyim/oath.json)
- [`MEMBERS.md`](../../MEMBERS.md) — github-side ledger
- `../l2-anchor-contract/` — sister contract, same immutability posture
- `../etzhayyim-paymaster/` — sponsors the `join()` gas via allowlist
