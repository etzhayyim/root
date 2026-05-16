# etzhayyim/root

Monorepo for religious-corp open activities operated by **etzhayyim** (宗教法人; 任意団体).

## Identity

| Property | Value |
|---|---|
| Operating entity | etzhayyim (canonical) |
| Aliases | amanomibashira / 天御柱 / עץ חיים (Tree of Life) / etz hayim / etzhayim / etz chaim |
| Form | 宗教法人 (任意団体 / unincorporated religious voluntary association) |
| Registry | On-chain (blockchain-registered constitution and member roster) |
| Domain | https://etzhayyim.com |
| DID | `did:web:etzhayyim.com` |
| License | Apache 2.0 |
| Boundary ADR | [`gftdcojp/ai-gftd-apps-gftdcojp` `90-docs/adr/2605152100-etzhayyim-github-org-boundary.md`](https://github.com/gftdcojp/ai-gftd-apps-gftdcojp/blob/main/90-docs/adr/2605152100-etzhayyim-github-org-boundary.md) |

## Status

**Scaffolding** (2026-05). Monorepo content seed pending — open scope (9 領域) will be extracted from the vendor monorepo `gftdcojp/ai-gftd-apps-gftdcojp` via `git filter-repo` with history preservation.

## Layout (Shannon-Optimal 8-Layer Architecture)

Mirrors the layered structure of the vendor monorepo. See [ADR 2604251830 — Shannon-Optimal Layered Architecture](https://github.com/gftdcojp/ai-gftd-apps-gftdcojp/blob/main/90-docs/adr/2604251830-shannon-optimal-layered-architecture.md).

```
etzhayyim/root/
├── 00-contracts/        # open lexicons / bpmn / dmn / Rego policies
├── 10-protocol/         # atproto, xrpc, lexicons-bundle, signal, did-etzhayyim
├── 20-actors/           # magatama actor framework + Pregel-pattern SDK
├── 30-graph/            # open graph schemas + RisingWave migrations
├── 50-infra/            # geth, holochain, ipfs, blockscout, etzhayyim-pds
├── 60-apps/             # open-* (22), public-* (2), atproto, ameno, baien
├── 90-docs/             # open-relevant ADRs
├── CLAUDE.md
├── deps.toml
├── LICENSE
└── README.md
```

## 9 領域 (planned content)

| 領域 | Description | Source path in vendor monorepo |
|---|---|---|
| **blockchain** | Private ethereum (geth), Holochain, IPFS, Blockscout, DID method | `50-infra/{geth-private,holochain,ipfs,blockscout}`, `10-protocol/did-gftd` |
| **baien** | BitNet b1.58 1-bit multimodal CPU/edge/browser LLM | `60-apps/ai-gftd-project-baien*`, `90-docs/baien/` |
| **bpmn** | Open BPMN 2.0 process definitions + DMN decision tables | `00-contracts/bpmn/`, `00-contracts/dmn/`, `60-apps/ai-gftd-project-open-bpmn` |
| **lexicon** | AT Protocol Lexicon schemas + XRPC framework | `00-contracts/lexicons/`, `10-protocol/lexicons-bundle`, `10-protocol/xrpc` |
| **pregel** | Magatama actor framework + Pregel-pattern host SDK | `20-actors/magatama/` |
| **atproto** | PDS reference impl + AT clients | `10-protocol/atproto`, `60-apps/ai-gftd-project-atproto`, `50-infra/k8s/atproto-pds` |
| **ameno** | Browser inference platform | `60-apps/ai-gftd-project-ameno` |
| **open data** | 22 public-data wrappers (airplane, banking, isco, isic, jpn-gov, ...) | `60-apps/ai-gftd-project-open-*` |
| **public governance** | Cyber crime tracking (malak) + global resource flow | `60-apps/ai-gftd-project-public-*` |

## Boundary

This monorepo is the **principal-owned** half of the source-control boundary established by ADR 2605152100. The **vendor-owned** half is `gftdcojp/ai-gftd-apps-gftdcojp` (proprietary; Gftd Japan株式会社 SOW; `did:web:gftd.co.jp`).

- **etzhayyim** (this repo's owner) = principal / sole decision-maker / payer / beneficiary
- **Gftd Japan株式会社** = vendor / contractor (corporate number 9007-2846)

Payoff attribution, governance decisions, and ownership of all artifacts in this repo belong to etzhayyim. Gftd Japan provides engineering capacity under SOW; vendor risk is internalized via SOW / SLA / termination rights / IP ownership.

## Related

- Vendor monorepo SSoT: https://github.com/gftdcojp/ai-gftd-apps-gftdcojp
- DID document: `https://etzhayyim.com/.well-known/did.json` (pending publish)
- Domain registrar: Cloudflare Registrar (2026-05-15)
