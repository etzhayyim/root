# kotoba-datomic

Holochain-isomorphic substrate composition over `AT Protocol MST + IPFS + Base L2 anchor`.

Canonical name for the architecture mandated by **[ADR-2605172000](../../90-docs/adr/2605172000-etzhayyim-rw-free-substrate.md)** (RW-free substrate). Specified in **[ADR-2605231400](../../90-docs/adr/2605231400-kotoba-datomic-holochain-iso-substrate.md)**.

> **Status**: spec scaffold v0.0.0. No runtime code yet — kotoba-datomic *is* the
> composition of primitives already implemented across `50-infra/`, `20-actors/`,
> and `00-contracts/`. This directory holds the spec; implementations land in the
> existing layer trees.

## What kotoba-datomic is

The seven layers of Holochain, rebuilt on the etzhayyim substrate stack:

| Holochain primitive | kotoba-datomic term | Implementation |
|---|---|---|
| `agent_pub_key` | kotoba-datomic-agent | DID + WebAuthn + Adherent SBT |
| Source chain | kotoba-datomic-chain | atproto PDS MST repo |
| DHT | kotoba-datomic-dht | IPFS + Base L2 anchor |
| DNA / membrane | kotoba-datomic-membrane | Lexicon + Rego + LangGraph cell catalog |
| Validator witnesses | kotoba-datomic-witnesses | Pregel cells on Murakumo fleet (quorum ≥3-of-5) |
| Capability tokens | kotoba-datomic-cap | atproto JWT-cap + DID-bound passkey |
| Zomes | kotoba-datomic-cells | Pregel cells per ADR-2605192415 |

See **[`SPEC.md`](SPEC.md)** for layer-by-layer detail.

## What kotoba-datomic is not

- **not a blockchain** — `chain` refers to the per-agent MST source chain (Holochain
  layer 2). L2 anchor records only the Merkle root of batched MST commits, not
  every write
- **not a replacement for `@etzhayyim/sdk`** — the SDK is the import seam;
  kotoba-datomic is the architecture pattern the SDK composes
- **not related to `yata` (graph engine in `50-infra/yata/`) or `yatabase`
  (commercial BaaS in `60-apps/etzhayyim-project-yatabase/`)** beyond sharing the
  八- (eight-span / sacred) prefix family
- **not the substrate for hot-path WHERE-bbox / GTFS-RT queries** — those are
  served by kotoba-datomic-projection (a follow-up ADR defines this regenerable
  cache layer)

## Naming rules

- Public spelling: **`kotoba-datomic`** (one token, lowercase)
- Hyphenated `yata-chain` is **prohibited** — it shadows the `yata-*` Cargo
  workspace crate convention in `50-infra/yata/`
- All sub-primitives use `kotoba-datomic-{term}` form (e.g., `kotoba-datomic-witnesses`,
  `kotoba-datomic-dht`)
- Japanese gloss: 八咫鎖. Latin spelling is canonical; kanji appears only in
  explanatory prose

## Relation to other substrate ADRs

```
ADR-2605172000 (RW-free substrate, mandates the stack)
  └─ ADR-2605231400 (kotoba-datomic, names the composition)  ← this directory
     ├─ ADR-2605171800 (mst-projector → ipfs-pinner → anchor-cron pipeline)
     ├─ ADR-2605181100 (encrypted records, witness validates on ciphertext)
     ├─ ADR-2605192100 (mission charter, anti-individualism alignment)
     └─ ADR-2605192415 (Pregel cell catalog, source of witness pool)
```

## Implementation surface (where the code actually lives)

kotoba-datomic is a spec, not a package. Implementations live in their natural layers:

| Layer | Path |
|---|---|
| kotoba-datomic-agent (DID + passkey + SBT) | `50-infra/etzhayyim-did-web/`, `50-infra/etzhayyim-membership-contract/` |
| kotoba-datomic-chain (PDS MST) | `50-infra/k8s/atproto-pds/`, `50-infra/mst-projector/` |
| kotoba-datomic-dht (IPFS + L2) | `50-infra/ipfs/`, `50-infra/l2-anchor-contract/`, `50-infra/anchor-cron/` |
| kotoba-datomic-membrane (Lexicon + Rego + LangGraph) | `00-contracts/lexicons/`, `00-contracts/policies/`, `40-engine/kotoba/crates/kotoba-kotodama/cells/` |
| kotoba-datomic-witnesses (Pregel cells + quorum) | `20-actors/etzhayyim-sdk/src/kotoba-datomic/` (witness-selector + quorum, shipped 2026-05-23); cell-side attestation publishing per-cell |
| kotoba-datomic-cap (JWT-cap + WebAuthn) | atproto standard, `20-actors/etzhayyim-sdk/src/pds.ts` |
| kotoba-datomic-cells (Pregel cells / zomes) | `40-engine/kotoba/crates/kotoba-kotodama/cells/`, `50-infra/murakumo/fleet.toml` |

App-side import remains exclusively via `@etzhayyim/sdk` per ADR-2605172000.

## See also

- [ADR-2605231400](../../90-docs/adr/2605231400-kotoba-datomic-holochain-iso-substrate.md) — this protocol's decision record
- [ADR-2605172000](../../90-docs/adr/2605172000-etzhayyim-rw-free-substrate.md) — substrate hard rules
- [ADR-2605192415](../../90-docs/adr/2605192415-etzhayyim-religious-corp-daemon-architecture.md) — Pregel cell catalog (zome source)
- [`50-infra/holochain/`](../../50-infra/holochain/) — actual Holochain (seeded sibling, not consumed; kotoba-datomic is *isomorphic to* but built independently of Holochain)
- [`20-actors/etzhayyim-sdk/`](../../20-actors/etzhayyim-sdk/) — the SDK that composes kotoba-datomic primitives
- [`10-protocol/wproto/`](../wproto/) — sibling protocol (AT + Signal over wRPC); shares the substrate but has different goals
