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

**Seeded + ADR-canonical** (2026-05-17). **Tranche F closure governance complete** (2026-05-21).

### Tranche F Phase 3-6 closure (2026-05-21 session)

ADR-2605152100 6-phase org-split cutover is now **doc-runbook complete end-to-end**:

| Phase | Status | Reference |
|-------|--------|-----------|
| 1. Catalog freeze | ✅ historical | ADR-2605212100 (vendor side) |
| 2. Scaffolding | ✅ historical | this repo seeded 2026-05-15 |
| 3. Content copy (Tranches A-E + Wave 2) | ✅ historical | 26 repos archived 2026-05-17 |
| 3 (Tranche F) gate (a) per-worker re-impl | 🟡 pattern catalogued, execution OPEN | `90-docs/2605211949-gate-a-execution-checklist.md` (42 checkbox rows) |
| 3 (Tranche F) gate (b) DNS cutover runbook | ✅ runbook ready | `90-docs/adr/2605211757-...md` (431 lines) |
| 3 (Tranche F) gate (c) deployment surface | ✅ documented inline | ADR-2605211757 §0 + §3.1 |
| 3 (Tranche F) gate (d) vendor importer survey | ✅ closed + 3 lg relocates + 1 hume inline | `90-docs/2605211800-...md` |
| 4. Vendor business-app dep switch | ✅ runbook ready | `90-docs/adr/2605211913-...md` §1 |
| 5. Vendor open-scope deletion | ✅ runbook ready (execution gated on gate (a)) | ADR-2605211913 §2 |
| 6. Archive markers | ✅ runbook ready (execution gated on Phase 5) | `90-docs/adr/2605211925-...md` |

Operator next-action: tick the 42 rows in the gate (a) checklist as
per-worker SQLite ports land in `20-actors/magatama/py/src/pymagatama/`. When
the checklist reads `42 / 42`, the rest of the runbooks (Wave A-D DNS
cutover → Phase 5 git rm → Phase 6 archive markers) unblock in order.

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

### Bootstrap Council Lv6+ — RFP open until 2026-06-19

5-seat religious evaluation body. Seat 1 (Founder) confirmed; Seats 2-5 open for self-nominations through 2026-06-19 (30-day window).

- Public RFP: [`COUNCIL-BOOTSTRAP-RFP.md`](COUNCIL-BOOTSTRAP-RFP.md)
- Roster: [`COUNCIL.md`](COUNCIL.md)
- Constitutional mechanics: [`ADR-2605192300`](90-docs/adr/2605192300-etzhayyim-bootstrap-council-five.md)
- **Operational mechanics** (selection rubric + objection workflow + failure modes): [`90-docs/2605212036-council-bootstrap-rfp-operational-addendum.md`](90-docs/2605212036-council-bootstrap-rfp-operational-addendum.md)

## Related

- DID document: `https://etzhayyim.com/.well-known/did.json` (LIVE)
- Domain registrar: Cloudflare Registrar (2026-05-15)
