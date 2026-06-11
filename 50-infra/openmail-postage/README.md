# `50-infra/openmail-postage` — Postage contract for Open Email

Foundry project deploying **`Postage.sol`** to Base L2. Sender pays USDC per
recipient before publishing an `app.openmail.message` record; AppView indexers
reject records lacking a valid Paid event whose `messageHash` matches the
record's canonical CBOR hash.

Per **ADR-2605172200** (Open Email — atproto MST-native mail with bidirectional
SMTP bridge and on-chain postage).

## Design

Stateless beyond rate + owner + treasury. History lives in the event log; the
chain is the canonical record. Same ethos as `CheckpointAnchor.sol`
(ADR-2605171800).

```
sender → approve(USDC) → payPostage(messageHash, recipientCount)
                              │
                              ▼
                       usdc.transferFrom(sender → treasury, rate × count)
                              │
                              ▼
                       emit Paid(sender, messageHash, count, amount, ts)
```

- **No pause, no proxy, no upgrade.** Policy changes beyond rate = deploy v2 at
  new address + update SDK / AppView config.
- **USDC + treasury are immutable.** To migrate either, redeploy.
- **Owner is a Safe multisig.** Per ADR-2605172100, the etzhayyim treasury Safe
  on Base controls rate and ownership rotation.

## Rate schedule (v1 default)

| Recipient class | Per-recipient rate | Notes |
|---|---|---|
| openmail-native (`did:plc:` / `did:web:`) | 0.01 USDC | 10_000 base units |
| SMTP-out (`smtp:<rfc5322>`) | 0.02 USDC | enforced at outbound bridge, not contract |
| Self (sender ∈ recipients) | 0 USDC | enforced at AppView, not contract |

Contract is mix-blind: it charges `rate × recipientCount` uniformly. The
0.02 USDC for SMTP-out is enforced by the outbound bridge refusing to relay
unless the postage payment covered the inflated rate. This keeps the contract
minimal.

## Layout

```
50-infra/openmail-postage/
├── README.md
├── foundry.toml
├── src/Postage.sol
├── test/Postage.t.sol      # 10 forge tests + MockUsdc
└── script/Deploy.s.sol     # Base + Base Sepolia
```

## Build & test

```sh
cd 50-infra/openmail-postage
forge install foundry-rs/forge-std  # if not already
forge build
forge test -vv
```

## Deploy

```sh
# Base Sepolia (test)
export USDC_ADDR=0x036CbD53842c5426634e7929541eC2318f3dCF7e   # Base Sepolia USDC
export TREASURY_ADDR=0x...                                     # etzhayyim treasury Safe (Sepolia)
export PRIVATE_KEY=0x...                                       # deployer EOA
export SET_OWNER_TO_TREASURY=1                                 # rotate owner immediately
export INITIAL_RATE=10000                                      # 0.01 USDC

forge script script/Deploy.s.sol \
  --rpc-url base_sepolia \
  --broadcast --verify

# Base mainnet (production — chain 8453)
export USDC_ADDR=0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913   # Base mainnet USDC
export TREASURY_ADDR=0x...                                     # etzhayyim treasury Safe (mainnet)
# ... same as above, --rpc-url base
```

## ABI / events (for AppView indexer)

```solidity
event Paid(
    address indexed sender,
    bytes32 indexed messageHash,
    uint16  recipientCount,
    uint256 amount,        // USDC base units (6 decimals)
    uint64  paidAtMs       // block.timestamp * 1000
);
event RateUpdated(uint256 oldRate, uint256 newRate);
event OwnerRotated(address indexed oldOwner, address indexed newOwner);
```

AppView verification for an openmail record:

1. Read `record.postage` → `{chain, contract, txHash, messageHash, ...}`.
2. Fetch the tx receipt; locate the Paid event from `contract`.
3. Verify `event.messageHash == keccak256(canonicalCbor(record - postage))`.
4. Verify `event.amount >= configured_rate * event.recipientCount`.
5. Verify `event.recipientCount >= record.to.length`.

If any check fails → record is filtered out of inbox queries.

## Related

- `00-contracts/lexicons/app/openmail/postageReceipt.json` — the lexicon that
  carries postage references in records.
- `00-contracts/lexicons/app/openmail/message.json` — the parent record type.
- ADR-2605172200 — Open Email design (this contract is § 4).
- ADR-2605172100 — etzhayyim payments-on-chain-only (USDC + Safe + ERC-4337).
- ADR-2605171800 — Anchor pipeline (same "stateless event-only contract" pattern).
