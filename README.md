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

## Status

**Seeded + ADR-canonical** (2026-05-17).

## Layout (Shannon-Optimal 8-Layer Architecture)

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

| 領域 | Description | Layer path in this repo |
|---|---|---|
| **blockchain** | Private ethereum (geth), Holochain, IPFS, Blockscout, DID method | `50-infra/{geth-private,holochain,ipfs,blockscout}`, `10-protocol/did-etzhayyim` |
| **baien** | BitNet b1.58 1-bit multimodal CPU/edge/browser LLM | `60-apps/*-baien*`, `90-docs/baien/` |
| **bpmn** | Open BPMN 2.0 process definitions + DMN decision tables | `00-contracts/bpmn/`, `00-contracts/dmn/`, `60-apps/*-open-bpmn` |
| **lexicon** | AT Protocol Lexicon schemas + XRPC framework | `00-contracts/lexicons/`, `10-protocol/lexicons-bundle`, `10-protocol/xrpc` |
| **pregel** | Magatama actor framework + Pregel-pattern host SDK | `20-actors/magatama/` |
| **atproto** | PDS reference impl + AT clients | `10-protocol/atproto`, `60-apps/*-atproto`, `50-infra/k8s/atproto-pds` |
| **ameno** | Browser inference platform | `60-apps/*-ameno` |
| **open data** | 22 public-data wrappers (airplane, banking, isco, isic, jpn-gov, ...) | `60-apps/*-open-*` |
| **public governance** | Global resource flow intelligence (open subset) | `60-apps/*-public-*` |

## Governance

- **etzhayyim** = principal / sole decision-maker / payer / beneficiary for all artifacts in this repo.
- Payoff attribution, governance decisions, and IP ownership belong to etzhayyim.

## Related

- DID document: `https://etzhayyim.com/.well-known/did.json` (LIVE)
- Domain registrar: Cloudflare Registrar (2026-05-15)
