# gov-municipality — Regulatory & Permitting Tier-B Actor

**DID**: `did:web:etzhayyim.com:gov-municipality`
**Namespace**: `app.etzhayyim.gov.*`
**ADR**: ADR-2605250800 (R0 scaffold), ADR-2605250815 (R1), ADR-2605250830 (R2), ADR-2605250845 (R3)
**Status**: R0 scaffold (2026-05-26) — all cells import-time RuntimeError

## Overview

Phase 0 actor: coordinates building permit submission, inspections, and sign-off across jurisdictions.

**Input**: Project scope (site, BOM, construction drawings)  
**Output**: permitsApprovedRecord (witness-signed by municipal authority)

## 3 Pregel Cells (Phase 0 regulatory sequence)

### permit_submission
- **Murakumo node**: judah (regulatory specialist)
- **Input**: `projectScope` (site location, building type, cost, GFA)
- **Output**: `permitApplicationId` (jurisdiction RPC → building department)
- **Status**: R0 scaffold

### inspection_scheduling
- **Murakumo node**: benjamin (schedule coordinator)
- **Input**: `permitApplicationId`, `constructionPhases` (foundation, structural, MEP, finishing, commissioning)
- **Output**: `inspectionSchedule` (jurisdiction RPC → inspection slots)
- **Status**: R0 scaffold

### final_sign_off
- **Murakumo node**: dan (authority liaison)
- **Input**: `inspectionResults` (pass/conditional/fail), defect walkdown
- **Output**: `permitsFinalizedRecord` (municipal signature, occupancy clearance)
- **Status**: R0 scaffold

## Jurisdictional Templates

- **Japan**: 建築確認申請 (local kyoku approval), 電気工事士免状 (licensed electrician), ガス工事 (LPG/city gas inspector)
- **US**: IBC + state-specific amendments, electrical/plumbing/mechanical stamps, building department final inspection
- **EU**: EN standards + national building code variant, CE mark verification (MEP systems)

## Non-Goals (N1–N5)

- N1: Zoning variance negotiation (user handles)
- N2: Environmental impact assessment (separate ecosystem actor)
- N3: Historical preservation review (separate actor)
- N4: Utility company approvals (→ infra-utility-connect actor)
- N5: Financing/cost estimation (capital domain)

## Constitutional Gates

- G1: All jurisdiction RPC calls open-source (no proprietary government APIs)
- G2: Permit documents IPFS-pinned (transparency)
- G3: Municipal authority witness signature (≥1 jurisdiction, ≥1 signature)
- G5: Charter Rider compliance (no bribe detection, no gatekeeping)
- G9: 30-day public notice period before permit approval (mesh transparency)

## 4-Phase Roadmap

- **R0** (this wave): Scaffold, stub RPC endpoints
- **R1**: Japan 建築確認申請 template + US IBC routing
- **R2**: 10+ jurisdiction templates (Japan prefectures, US states, EU countries)
- **R3**: Real municipal RPC integration (pilot cities)
