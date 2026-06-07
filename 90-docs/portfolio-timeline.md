---
id: portfolio-timeline
title: "DoDAF PV-2 — Project Timeline & Portfolio Roadmap"
status: active
doc_type: reference
topic: portfolio-management
authoritative: true
last_verified: 2026-05-20
authoritative_for:
  - dodaf-pv2
  - project-timeline
  - phase-gates
related:
  - adr-2605180000-lawfirm-product-focus-bmc-lean
  - adr-2605190000-yatabase-bmc-lean
  - adr-2605190100-defense-cluster-topology
  - adr-2605200000-nist-csf-respond-irp
  - adr-2605200200-nist-csf-recover-rto-rpo
  - deps.toml [etzhayyim_agent.product_portfolio]
---

# DoDAF PV-2 — Project Timeline & Portfolio Roadmap

**Framework**: DoDAF v2 / PV-2 Project Timeline viewpoint
**Operating entity**: etzhayyim (alias: etzhayyim / 天御柱 / עץ חיים)
**Vendor**: etzhayyim Japan株式会社
**Baseline date**: 2026-05-20 (iter 160)

---

## 1. Portfolio Priority Allocation

| Priority | Product | Domain | Revenue Weight | Status |
|---|---|---|---|---|
| **P1** | lawfirm.etzhayyim.com | Legal-tech SaaS (India intake + JP lawfirm) | 70% | D-Day execution — Scenario A active |
| **P2** | lawyer.etzhayyim.com | Attorney portal (bar-member access) | 20% | Design approved (ADR-2605180600) |
| **P3** | animeka.etzhayyim.com | Team anime creation pipeline | 5% | Prototype in-progress |
| **P4** | yatabase.etzhayyim.com | Platform-layer product projector | 5% | BMC approved (ADR-2605190000) |

SSoT: `deps.toml [etzhayyim_agent.product_portfolio]` + `90-docs/adr/2605180000-lawfirm-product-focus-bmc-lean.md`

---

## 2. Phase Gate Timeline

### Phase 0 — Foundation (Complete)

| Milestone | Date | Artifact |
|---|---|---|
| 8-Layer Shannon-Optimal Architecture | 2026-04-25 | ADR-2604251830 |
| AT Protocol / XRPC framework | 2026-04-23 | ADR-2604231811 |
| F-Plan: Lexicon JSON dual-wire SSoT | 2026-05-15 | ADR-2605091400 |
| LangGraph Server + Granian L3 runtime | 2026-05-08 | ADR-2605080600 |
| Bonsai Cultivar ecosystem model | 2026-05-09 | ADR-2605091300 |
| MCP-as-Cell-Membrane | 2026-05-09 | ADR-2605091400 |
| Kotoba/Datomic Vultr+B2 primary (LAX) | 2026-04-22 | ADR-0048 |
| CF Worker edge-only (no RW connection) | 2026-05-11 | ADR-2605111200 |
| PDS-to-Pod migration scaffolding | 2026-05-11 | ADR-2605111300 |
| etzhayyim GitHub org boundary | 2026-05-15 | ADR-2605152100 |
| Pyright + Pydantic v2 repo-wide | 2026-05-15 | ADR-2605151550 |

### Phase 1 — P1 Execution (Now — 2026-05-23)

| Milestone | Deadline | Owner | Status |
|---|---|---|---|
| k-bakshi BCI/foreign bar approval | **2026-05-23** (Rule 36) | k-bakshi | Awaiting reply |
| D-Day XRPC send pipeline | Running | etzhayyim agent | 5 mails sent (iter115-119) |
| y-nishino RW migration apply (D2) | Unblocked after auth | y-nishino | 3 migrations pending |
| Track C K8s delegation | Post-auth | a-nakamura | Deferred |
| etzhayyim auth login (PKCE session) | Immediate | operator | **BLOCKED** |
| NIST CSF DETECT/RESPOND/RECOVER | 2026-05-20 | etzhayyim IC | ✅ Complete (today) |

**Active blockers** (as of iter 160):

1. `etzhayyim auth login` — PKCE session expired; run `! etzhayyim auth login`
2. k-bakshi BCI reply — Rule 36 deadline 2026-05-23
3. y-nishino workstation RW network access (45.32.79.245:4566 unreachable from claude host)
4. Vultr GPU unlock — RunPod 6000 Ada compute (ADR-2605010000)
5. Alembic multi-head corruption — new migrations applied via psycopg2 direct only

### Phase 2 — P2 Ramp (2026-Q3)

| Milestone | Target | ADR |
|---|---|---|
| lawyer.etzhayyim.com attorney portal MVP | 2026-Q3 | ADR-2605180600 |
| Bar-member auth topology (ADR-2605152100 GitHub boundary) | 2026-Q3 | ADR-2605152100 |
| LangGraph attorney onboarding flow | 2026-Q3 | — |
| Open LEI bridge full verification (5 India lawfirm rows) | 2026-Q3 | ADR-2605130900 |
| animeka P3 prototype shipment | 2026-Q3 | — |

### Phase 3 — Defense Cluster (2026-Q3/Q4)

| Milestone | Target | ADR |
|---|---|---|
| **T0 SaaS** (CF+Vultr, clearance L0-L2) | 2026-Q3 | ADR-2605190100 |
| Defense personnel/access graph tables live | 2026-Q3 | Migration 20260520040000 |
| ITAR/ECCN classifier agent | 2026-Q3 | pydefense metrics.py |
| Supply chain risk scoring | 2026-Q3 | defense-alerts.yaml |
| **T1 Sovereign** (Sakura Internet IaaS, clearance L3) | 2026-Q4 | ADR-2605190100 §Phase 2 |
| **T2 Air-Gap** (bare-metal, clearance L4) | 2027-Q1 | ADR-2605190100 §Phase 3 |

### Phase 4 — P4 Platform & Scale (2026-Q4 / 2027)

| Milestone | Target | ADR |
|---|---|---|
| yatabase BMC launch | 2026-Q4 | ADR-2605190000 |
| etzhayyim 登記変更 + 220-file sed cutover | Post-登記 | deps.toml [[migrations]] |
| PDS-to-Pod migration complete (bun container + CF Tunnel) | 2027-Q1 | ADR-2605111300 |
| Ecosystem-as-Model FP8 substrate | 2027-Q1 | ADR-2605092000 |
| Continuous Metabolic Training online | 2027 | ADR-2605092200 |

---

## 3. Infrastructure Evolution

```
2026-04-22  Vultr VKE LAX live (ADR-0048)
            Kotoba/Datomic Vultr+B2 primary — B2 us-west-004
            Linode Object Storage 全廃止

2026-04-25  B2 SlowDown incident — Foyer cold-start storm
            → defense-in-depth 移植: cache_refill, insert_rate_limit
            → dml_rate_limit convention established

2026-05-08  LangGraph Server + Granian L3 standardized
            5-agent defense LangGraph fleet seeded

2026-05-11  CF Worker edge-only (ADR-2605111200)
            Worker HYPERDRIVE binding 全削除

2026-05-15  F-Plan complete
            Lexicon JSON = dual-wire SSoT (XRPC + MCP)
            etzhayyim.com domain live (did:web:etzhayyim.com)

2026-05-20  NIST CSF 2.0 adoption complete
            DETECT: PrometheusRule CRDs deployed
            RESPOND: IRP ADR + severity taxonomy
            RECOVER: RTO/RPO SLAs + DR drill CronJob
            Defense cluster personnel/access tables

2026-Q3     RunPod 6000 Ada unlock (pending Vultr GPU)
            T0 defense cluster production

2026-Q4     T1 Sovereign (Sakura)
            yatabase launch

2027-Q1     T2 Air-Gap bare-metal
            PDS-to-Pod complete
            FP8 train+inference colocation
```

---

## 4. Migration Backlog Status

### By Category (in-progress)

| Category | Count | Examples |
|---|---|---|
| `graph` / `db-schema` | 6 | vertex-to-edge-table-rewrite, authority-column-promotion |
| `infra` | 4 | hyperdrive-pg-adapter, linode-object-storage-backup-audit |
| `sdk` | 4 | legacy-host-sdk-factory, handlehttp-wit-compat, cli-lmstudio-api-defaults, cli-etzhayyim-json-manifest |
| `ui` | 3 | legacy-panel-genimage, legacy-actor-profile, svelte-slot-migration |
| `design` | 2 | maps-forward-topology-raw-to-webgpu, maps-google-earth-3d-topology |
| `naming` | 1 | pds-magatamaapp-rename |
| `read-path` | 1 | r2sql-archive |

### Blocked

| Migration | Blocker |
|---|---|
| `authority-column-promotion` | Downstream RW schema impact analysis |
| `hyperdrive-pg-adapter` | Hyperdrive/Kotoba/Datomic compatibility validation |
| `etzhayyim-org-monorepo-cutover-2026-05-17` | 登記変更 (宗教法人) |
| `murakumo-fleet-lan-dnsmasq-ethernet-unification` | Vultr GPU unlock |
| y-nishino RW migrations (3) | Network access from claude host |

### Recently Completed (2026-05)

| Migration | Closed |
|---|---|
| crm-open-lei-bridge-review-loop | 2026-05-13 |
| defense cluster graph tables (personnel/access) | 2026-05-20 |
| NIST CSF DETECT alert rules | 2026-05-20 |
| NIST CSF RECOVER DR drill (Vultr port) | 2026-05-20 |

---

## 5. Quarterly DR Drill Schedule

Per ADR-2605200200 (RECOVER):

| Cadence | Type | Executor | Pass Criterion |
|---|---|---|---|
| Monthly (1st 02:00 UTC) | `--dry-run` | CronJob `rw-dr-drill-monthly` | snapshot readable + exit 0 |
| Quarterly (manual) | `--full` | IC (etzhayyim) | catalog table count ≥ baseline (1211) |

Script: `50-infra/vultr/kotoba/dr-restore-drill.sh`
Log: `90-docs/irp/dr-drill-log.md`
Baseline: 2026-04-15, Snapshot ID=3, tables=1211 (Linode full drill)

---

## 6. ADR Recency Map (last 30 days)

| Date | ADR | Topic |
|---|---|---|
| 2026-05-20 | 2605200200 | NIST CSF RECOVER — RTO/RPO SLAs |
| 2026-05-20 | 2605200100 | NIST CSF DETECT — Prometheus alerts |
| 2026-05-20 | 2605200000 | NIST CSF RESPOND — IRP adoption |
| 2026-05-19 | 2605190100 | Defense cluster topology (T0/T1/T2) |
| 2026-05-19 | 2605190000 | yatabase BMC + Lean canvas |
| 2026-05-18 | 2605181200 | lawfirm NRI backend dispatcher |
| 2026-05-18 | 2605180600 | lawyer attorney portal design |
| 2026-05-18 | 2605180000 | lawfirm product focus BMC |
| 2026-05-18 | 2605180000 | mamoru git-secret guardian |
| 2026-05-17 | 2605172000 | malak onion frontier ransomware tracking |
| 2026-05-17 | 2605171300 | open-unispsc generative agent fleet |
| 2026-05-17 | 2605170000 | deai spirit-physics matching |
| 2026-05-16 | 2605160800 | itonami lifecycle dashboard pregel UI |
| 2026-05-15 | 2605152300 | jukyu MCP query surface |
| 2026-05-15 | 2605152200 | Svelte + Tailwind 3-file setup |
| 2026-05-15 | 2605152100 | etzhayyim GitHub org boundary |
| 2026-05-15 | 2605152100 | auth unified topology |
| 2026-05-15 | 2605152000 | wallet deep-inspect + address label pregelss |
| 2026-05-15 | 2605151600 | maps langserver direct call |
| 2026-05-15 | 2605151550 | Pyright + Pydantic v2 repo-wide |

---

## 7. Active Project Roster (Tier-1, 16 projects)

| Project | Domain | Phase |
|---|---|---|
| etzhayyim-project-lawfirm | Legal SaaS P1 | Production / D-Day |
| etzhayyim-project-lawyer | Attorney portal P2 | Design |
| etzhayyim-project-animeka | Anime creation P3 | Prototype |
| etzhayyim-project-yoro | Social (Bluesky-compat) | Production |
| etzhayyim-project-malak | Ransomware/threat intel | Production |
| etzhayyim-project-mamoru | Secret guardian | Production |
| etzhayyim-project-shinshi | Assistant platform | In-progress |
| etzhayyim-project-deai | Spirit-physics matching | Design |
| etzhayyim-project-yatabase | Platform projector P4 | BMC approved |
| etzhayyim-project-keiei | Business ops | In-progress |
| etzhayyim-project-mailer | Email automation | In-progress |
| etzhayyim-project-microsoft | MS Graph integration | Production |
| etzhayyim-project-flight-offer | Travel-tech | In-progress |
| etzhayyim-project-warehouse | Logistics | In-progress |
| etzhayyim-project-yard-ops | Yard operations | In-progress |
| etzhayyim-project-intel | Open-source intel | In-progress |

---

## 8. DoDAF PV-2 Alignment Notes

This document satisfies PV-2 (Project Timeline View) requirements:

| PV-2 Element | Coverage |
|---|---|
| Project phases and milestones | §2 Phase Gate Timeline |
| Dependencies between projects | §4 Migration Backlog (blocked_by) |
| Resource/capability allocation | §1 Portfolio Priority + §3 Infrastructure |
| Risk and constraint tracking | §2 Active blockers |
| Schedule baseline | §5 DR Drill Schedule |

Related DoDAF views:
- **AV-1** (Overview): `deps.toml [platform]`
- **CV-1** (Capability Vision): `90-docs/adr/2605080000-distributed-cognitive-actor-system.md`
- **OV-1** (High-Level Op Concept): `90-docs/adr/2604251830-shannon-optimal-layered-architecture.md`
- **PV-1** (Project Portfolio): `deps.toml [[projects]]` (129 projects roster)
- **PV-3** (Project to Standards Mapping): `90-docs/adr/2605200100-nist-csf-detect-prometheus-alerts.md`
- **StdV-1** (Standards Profile): `NIST CSF 2.0`, `DoDAF v2`, `AT Protocol`, `LangGraph`
