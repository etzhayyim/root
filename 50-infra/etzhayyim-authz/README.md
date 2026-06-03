# etzhayyim-authz — ERC725 root identity issuance

**Status**: Phase α P0 landed (contract + tests + lexicons) — Base L2 deploy + XRPC handler pending
**Design**: ADR-2605212030 (chain / DID format / cutover / namespace)
**Tracking**: ADR-2605211950 Open Item (1)
**Originating ADR**: vendor ADR-0074 (ethereum-identity-bridge-cacao-webauthn) + ADR-0095 (3-layer identity rw-vault)

## Phase α P0 — what landed

- `contracts/src/EtzhayyimAuthz.sol` — Council-owned root registry, ERC725-shape data with `dwebHandleHash` + `activeKey` + optional vendor predecessor link + key-rotation digest signed by current active key. Solidity 0.8.27, via_ir, optimizer 1M runs.
- `contracts/script/Deploy.s.sol` — Forge deploy script. `run(councilSafe)` for Base Sepolia / mainnet; `runLocal()` for Anvil smoke.
- `contracts/test/EtzhayyimAuthz.t.sol` — 17 tests, all passing locally.
- `00-contracts/lexicons/org/etzhayyim/authz/{beginRootProvision,completeRootProvision,resolveRoot,mirrorVendorRoot,getProvenance}.json` — 5 lexicons defining the XRPC contract surface (per ADR-2605212030 §D4).

## Phase α P1+ — what's next

- Base Sepolia testnet deploy (run `script/Deploy.s.sol:Deploy` with `--rpc-url base_sepolia`, Council multisig as owner).
- XRPC handler implementation in `src/` (k8s pod or CF Worker, TBD).
- did:web facade serving extended in `50-infra/etzhayyim-did-web/` to embed `did:erc725:base:<this-contract>#<rootIdHex>` per-handle.
- Council multisig SOP for provisioning approval and mirrorVendorRoot off-chain verification.
- Per-actor opt-in migration tooling for the ~96 vendor-issued roots.

## Why this directory exists

Per ADR-2605211950 (substrate centralization axis), decentralization
primitives — including **ERC725 root identity issuance** — are
etzhayyim-exclusive. The current implementation lives in the vendor
repo at `etzhayyim-root/60-apps/etzhayyim-project-auth/worker-authz/`
and is reachable via the `com.etzhayyim.authz.linkEthereum{Begin,Verify}`
lexicons (now marked `[DEPRECATED — migration target]` in the vendor
repo).

This directory will hold the etzhayyim service that takes over root
identity issuance once migration is scheduled.

## Migration scope

| Vendor source (to be relocated) | etzhayyim target |
|---|---|
| `60-apps/etzhayyim-project-auth/worker-authz/src-ts/sign-up.ts` (Ethereum branch — `rootDidFromIdentity`, `rootDidHashFromIdentity`, `ETH_PRIVATE_CHAIN_ID` reads) | `etzhayyim-authz/src/erc725-root-issuer.ts` |
| `70-tools/scripts/provision-actors-erc725.mjs` (batch root provisioning) | `etzhayyim-authz/scripts/provision-root.ts` |
| `00-contracts/lexicons/com/etzhayyim/authz/linkEthereumBegin.json` | new etzhayyim lexicon under `00-contracts/lexicons/org/etzhayyim/authz/` (NSID TBD) |
| `00-contracts/lexicons/com/etzhayyim/authz/linkEthereumVerify.json` | same as above (verify side) |
| Internal RPC binding (`ETH_PRIVATE_CHAIN_ID`) | etzhayyim-managed Base L2 RPC endpoint |

## Out of scope

- Vendor `actor_did` / `org_did` RisingWave column convention (ADR-0095)
  — that side stays vendor-owned as a **reference** to the etzhayyim-
  issued DID. Vendor reads the etzhayyim chain; vendor does not write.
- Vendor session JWT issuance (`authz.etzhayyim.com` ordinary login) —
  stays vendor (centralized primitive, ADR-2605211950 allows it).

## Open design questions (defer to follow-up ADR)

1. **DID format** — keep `did:erc725:` or migrate to a chain-agnostic
   `did:web:` + on-chain anchor pattern. The etzhayyim mission charter
   already commits to `did:web:etzhayyim.com` for the entity itself;
   individual actor roots may differ.
2. **Chain selection** — vendor uses a private chain
   (`ETH_PRIVATE_CHAIN_ID`). etzhayyim payments are already on **Base
   L2 public mainnet** per ADR-2605172100. Either align root identity
   to Base L2 (consolidates chains) or keep a separate private chain
   for identity privacy. Decision pending.
3. **Cutover protocol** — how to migrate existing vendor-issued
   ERC725 roots (≈ 96 mitama actors + N orgs) without invalidating
   their downstream `vault_members` / `vertex_signal_identity` rows.
4. **Lexicon namespace** — `org/etzhayyim/authz/*` or extend
   `com/etzhayyim/authz/*` with `etzhayyim:` prefix.

## Hand-off path

When this scaffold is filled in:

1. Author etzhayyim ADR documenting the resolved design questions above.
2. Land code in `etzhayyim-authz/src/`.
3. Vendor ADR-0074 / ADR-0095 get `superseded_by: etzhayyim:adr-XXXXXXXXX`.
4. Vendor lexicons (`linkEthereum{Begin,Verify}.json`) get `status: deprecated` at the lexicon level (not just description prefix).
5. Vendor `sign-up.ts` Ethereum branch is removed; vendor calls etzhayyim authz via XRPC for any residual integration.
