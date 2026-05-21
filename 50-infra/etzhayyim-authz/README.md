# etzhayyim-authz — migration target for ERC725 root identity issuance

**Status**: scaffold (no code yet)
**Tracking**: ADR-2605211950 Open Item (1)
**Originating ADR**: vendor ADR-0074 (ethereum-identity-bridge-cacao-webauthn) + ADR-0095 (3-layer identity rw-vault)

## Why this directory exists

Per ADR-2605211950 (substrate centralization axis), decentralization
primitives — including **ERC725 root identity issuance** — are
etzhayyim-exclusive. The current implementation lives in the vendor
repo at `ai-gftd-apps-gftdcojp/60-apps/ai-gftd-project-auth/worker-authz/`
and is reachable via the `ai.gftd.authz.linkEthereum{Begin,Verify}`
lexicons (now marked `[DEPRECATED — migration target]` in the vendor
repo).

This directory will hold the etzhayyim service that takes over root
identity issuance once migration is scheduled.

## Migration scope

| Vendor source (to be relocated) | etzhayyim target |
|---|---|
| `60-apps/ai-gftd-project-auth/worker-authz/src-ts/sign-up.ts` (Ethereum branch — `rootDidFromIdentity`, `rootDidHashFromIdentity`, `ETH_PRIVATE_CHAIN_ID` reads) | `etzhayyim-authz/src/erc725-root-issuer.ts` |
| `70-tools/scripts/provision-actors-erc725.mjs` (batch root provisioning) | `etzhayyim-authz/scripts/provision-root.ts` |
| `00-contracts/lexicons/ai/gftd/authz/linkEthereumBegin.json` | new etzhayyim lexicon under `00-contracts/lexicons/org/etzhayyim/authz/` (NSID TBD) |
| `00-contracts/lexicons/ai/gftd/authz/linkEthereumVerify.json` | same as above (verify side) |
| Internal RPC binding (`ETH_PRIVATE_CHAIN_ID`) | etzhayyim-managed Base L2 RPC endpoint |

## Out of scope

- Vendor `actor_did` / `org_did` RisingWave column convention (ADR-0095)
  — that side stays vendor-owned as a **reference** to the etzhayyim-
  issued DID. Vendor reads the etzhayyim chain; vendor does not write.
- Vendor session JWT issuance (`authz.gftd.ai` ordinary login) —
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
   `ai/gftd/authz/*` with `etzhayyim:` prefix.

## Hand-off path

When this scaffold is filled in:

1. Author etzhayyim ADR documenting the resolved design questions above.
2. Land code in `etzhayyim-authz/src/`.
3. Vendor ADR-0074 / ADR-0095 get `superseded_by: etzhayyim:adr-XXXXXXXXX`.
4. Vendor lexicons (`linkEthereum{Begin,Verify}.json`) get `status: deprecated` at the lexicon level (not just description prefix).
5. Vendor `sign-up.ts` Ethereum branch is removed; vendor calls etzhayyim authz via XRPC for any residual integration.
