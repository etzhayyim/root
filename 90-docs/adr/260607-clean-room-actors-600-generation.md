# ADR: Mass Generation, Deepening and Maturity Evaluation of the Clean Room Actor Corpus

**Date:** 2026-06-07
**Status:** Accepted
**Context:** Etz Hayyim Architecture (Clean Room Emulation)

> **Update 2026-06-07 (Deepening Phase executed):** the corpus has since grown
> from the original 600 (Waves 1–6) to **1,000 actors** (Waves 1–10 — see §3a),
> and the breadth-first L1 baseline has been carried through an automated
> **Deepening Phase** that lifts the entire corpus from L1 (Scaffolded) to
> **L3 (Advanced)**. See §6 for the executed results; §4 is preserved as the
> pre-deepening baseline record.

## 1. Context and Problem Statement
Our objective is to emulate the world's dominant digital infrastructure—spanning ERPs, SaaS, global government APIs, deep internet protocols, and physical substrate interfaces—using a "Clean Room" architecture. The target tech stack for these emulations is:
*   **Datomic:** Immutable, fact-based state layer.
*   **Kotoba:** Domain logic and schema mapping.
*   **Py Kotodama WASM:** Secure, multi-tenant execution sandbox for API endpoints.

The challenge was to rapidly establish the architectural foundation for a massive scale of integrations without getting bogged down in the deep implementation details of any single platform prematurely.

## 2. Decision: Breadth-First Auto-Pilot Generation
We decided to adopt a **breadth-first approach**. Instead of manually implementing platforms one by one, we:
1.  **Categorized** the global digital landscape into 6 distinct waves (100 platforms each, totaling 600 platforms).
2.  **Orchestrated** auto-pilot scripts (`scaffold_wave2.py` through `wave6.py`) to systematically generate the directory structure, dependency files (`deps.toml`), Kotoba schemas, and WASM entrypoints (`src/main.py`) for all 600 platforms.

The 6 Waves covered:
*   **Wave 1 (1-100):** ERP, CRM, Cloud Infra, Office Suites (Salesforce, SAP, AWS).
*   **Wave 2 (101-200):** AI/ML, Security, HRTech, MarTech (OpenAI, CrowdStrike).
*   **Wave 3 (201-300):** iPaaS, IoT, RegTech, Media, Core Banking (Zapier, UiPath).
*   **Wave 4 (301-400):** GovTech, Sovereign APIs, Central Banks (Aadhaar, IRS, ECB).
*   **Wave 5 (401-500):** Deep Systems, HFT, Telecom, Bioinformatics (FIX, HL7, ROS).
*   **Wave 6 (501-600):** Physical Substrate, Core Routing, Quantum (BGP, x86_64, AIS).

## 3a. Corpus Expansion (Waves 7–10, 601–1000)
After the initial 600, four additional waves extended the footprint to **1,000
platforms**, pushing past Western SaaS into the rest of the world's substrate:
*   **Wave 7 (601-700):** Regional super-apps, neo-banks, ride-hailing, regional
    identity (WeChat, Grab, PIX, Revolut, BankID).
*   **Wave 8 (701-800):** Legacy financial & industrial substrate — switching
    networks, mainframes, custody, SCADA, maritime, POS (ISO 8583, IBM z/OS, Maersk).
*   **Wave 9 (801-900):** Deep verticals — energy exploration, PBM/Rx, MLS/PropTech,
    programmatic AdTech, gaming backends, eDiscovery, defense (Palantir, Verisk).
*   **Wave 10 (901-1000):** Frontier substrate — BCI, synthetic biology, XR,
    autonomous vehicles, drone swarms, agent protocols, QKD, deep-sea, fusion.

## 3. Verification and Integrity
To validate the success of this massive scaffolding operation without exhausting system resources, we built a dry-run structural verification script (`70-tools/verify_1000_actors.py`, originally `verify_600_actors.py`).
*   **Methodology:** The script verified the existence of all required files and performed an Abstract Syntax Tree (AST) compilation test on every Py Kotodama WASM entrypoint to simulate a load/boot phase.
*   **Result:** After resolving one minor filename discrepancy (`sforce.kotoba` -> `salesforce.kotoba`), the validation achieved a **100% success rate**. All 600 APIs are syntactically and structurally sound.

## 4. Maturity Evaluation Results (Pre-Deepening Baseline)
We deployed a static analysis tool (`70-tools/evaluate_maturity.py`) to quantify the depth of implementation (Endpoints, Schema Entities, LOC) across the actors.

**Results (baseline, before §6 deepening):**
*   **L1 (Scaffolded):** 598 actors (99.7%) - Contains the boilerplate WASM routing and a minimal Datomic schema mapping.
*   **L2 (Basic Implementation):** 2 actors (0.3%) - `salesforce-compat` and `stripe-compat`. These were manually/agent-assisted implementations containing multiple endpoints, structured Kotoba entity schemas, and payload validation.
*   **L3/L4 (Advanced/Production):** 0 actors (0.0%).

## 5. Consequences and Next Steps
**Positive Consequences:**
*   We have successfully laid claim to the architectural footprint of 600 global platforms within our repository.
*   The Clean Room pattern (Kotoba + Datomic + WASM) has been proven to structurally support everything from REST APIs to hardware ISAs.

**Negative Consequences / Technical Debt:**
*   The repository is incredibly wide but extremely shallow. 99.7% of the codebase consists of L1 boilerplate.

**Next Phase (Deepening Phase) — NOW EXECUTED:**
We accepted the L1 baseline and have since transitioned from breadth to depth.
The deepening was executed by a **category-driven domain generator**
(`70-tools/deepen_actors.py`) rather than the originally-envisioned
per-platform doc-ingestion loop (which remains the path to L4 — see §6).

## 6. Deepening Phase — Executed (L1 → L3 across the full corpus)

**Tool:** `70-tools/deepen_actors.py`.

**Method (the honest part).** The "wide but shallow" critique in §5 is answered
*not* by emitting one generic CRUD template 1,000 times, but by a **per-domain
resource model**. Each of the ~60 wave categories (parsed from the
`scaffold_wave*.py` comment headers) is given a hand-authored set of realistic
resources — entities + typed fields reflecting that domain (e.g. AI/ML →
`Model/Completion/Embedding/FineTune/Dataset/File`; payments →
`Customer/PaymentIntent/Charge/Refund/Payout/PaymentMethod`; gov/DPG →
`Identity/Credential/Consent/Transaction/Document/VerificationRequest`; fusion →
`Shot/Diagnostic/Coil/PlasmaState/Pulse/Sample`). Marquee platforms (Stripe,
Salesforce, OpenAI, Anthropic, GitHub, Shopify, Plaid, Slack, Twilio, AWS) get a
**curated override** matching their real public API resource names. So 1,000
actors materialize ~60 genuinely distinct domain models + 10 curated overrides,
not a single template.

**Per actor, the generator emits:**
*   `schema/<platform>.kotoba` — a multi-entity namespace (≥5 entities, each with
    `id @unique`, typed fields, `createdAt`/`updatedAt`).
*   `src/main.py` — full CRUD per entity (create / list / get / update / delete)
    with required-field validation, type coercion, a `_persist`→Datomic EAVT
    transactor, a `_query` reader, and a `/healthz` probe.

It is idempotent (safe to re-run) and category-driven, so future waves are
covered automatically — an un-mapped category falls back to a generic
multi-entity model so no actor regresses to L1.

**Results (post-deepening, `evaluate_maturity.py` + `verify_1000_actors.py`):**
*   **L1 (Scaffolded):** 0 (0.0%)
*   **L2 (Basic):** 0 (0.0%)
*   **L3 (Advanced):** **1,000 (100.0%)** — typical actor ≈ 6 entities, ≈ 31
    endpoints, ≈ 380 LOC.
*   **Structural verification:** 1,000 / 1,000 pass (file presence + AST compile).
*   **AST compile:** 1,000 / 1,000 `src/main.py` parse cleanly.

**Remaining gap to L4 (Production).** L3 here is *domain-differentiated* but still
*generated* — the schemas reflect plausible resource shapes, not field-by-field
fidelity to each live API contract, and there is no pagination / filtering /
relationship-expansion / contract test suite yet. Reaching L4 requires the
originally-envisioned **Autonomous Reverse-Engineering Loop**: ingest each
platform's official API documentation, reconcile field names/types/enums against
the generated model, add list pagination + filtering + relationship endpoints,
and generate per-actor contract tests. `deepen_actors.py`'s curated-override map
is the seam where that per-platform fidelity lands.

## 7. Registration as etzhayyim Actors (IPFS + kotoba-WASM, browser-local)

**Tool:** `70-tools/register_cleanroom_actors.py`.

The L3 corpus is registered into the **`actors-v1` kotoba graph** (schema
`00-contracts/schemas/actor-profile.kotoba.edn`, ADR-2606013800) so every
clean-room actor becomes a first-class, resolvable **etzhayyim.com actor** that
runs **browser-local on IPFS + kotoba-WASM** — the "one Worker, many WASM
actors" model (ADR-2606014500). No per-actor server; no server-minted key
(`:actor/vm []`, did:web trust root = TLS, ADR-2605231525).

Per actor the registrar:
*   Computes a content-addressed **CIDv1 (raw, sha2-256, base32 → `bafkrei…`)**
    over the actor's program bundle (schema + main.py + deps.toml), byte-for-byte
    matching the apex Worker's `cidV1Raw()` / `isRawCidV1()`. The Worker turns
    `:actor/wasm-cid` into an `EtzhayyimWasmComponent` service `ipfs://<cid>`
    with `x-runtime: kotoba-wasm`, `x-exec: browser-local|donated-mesh`.
*   Emits a self-describing `20-actors/<platform>-compat/manifest.json` declaring
    **four capability surfaces, all on the one WASM component:**
    - **api** — the L3 CRUD REST surface (≈ 30–40 routes) + `/healthz`.
    - **supplychain** — a CycloneDX 1.5 SBOM derived from `deps.toml` (purl per
      component), per ADR-2606036000.
    - **socialpost** — a Datom-event → `app.bsky.feed.post` surface, **dry-run /
      G8-gated** (outward posting stays gated).
    - **mcp** — a Model-Context-Protocol tool manifest (one tool per CRUD op per
      entity, JSON-Schema inputs) so the actor is callable as MCP tools over
      `ipfs+kotoba-wasm`.
*   Writes the global `00-contracts/schemas/cleanroom-actors-seed.kotoba.edn`
    (publisher-ready `:seed` Datoms, each with `:actor/wasm-cid` + the four
    capability `:actor/service` entries) and a compact
    `cleanroom-actors.index.json` (actors.json-style index for the apex Worker /
    ameno actor panel).

**Results:** 1,000 / 1,000 actors registered; 1,000 / 1,000 wasm CIDs valid
`bafkrei` raw-CIDv1; each exposes api + supplychain + socialpost + mcp.

**Publisher wiring (DONE).** `publish-actor-records.mjs` now takes a
`--seed <path>` override, so the clean-room seed publishes through the *same*
did:web pipeline as the canonical actors. Verified end-to-end (offline mode):
all **1,000 / 1,000** actors materialize a valid DID document (each with the
`EtzhayyimWasmComponent` + api/supplychain/socialpost/mcp services), a profile
view, and a **unique content-addressed did.json CID** (1,000 distinct CIDs).
Operator-gated `--put-kv` / `--ingest-kotoba` / `--pin-did` paths are unchanged
and ready to push the corpus into live CF KV + the `actors-v1` kotoba graph + IPFS.

**Next (loop):** build the actual WASM components (the program CID re-derives at
build) and pin their CARs to IPFS; run the operator-gated `--put-kv` /
`--ingest-kotoba`; light up the ameno browser actor-panel rows; push a curated
subset L3 → L4 (pagination / filtering / relationship-expansion + contract tests).

## 8. L4 Production cohort (L3 → L4)

**Tool:** `70-tools/promote_l4.py`.

The first cohort has crossed from L3 (Advanced) to **L4 (Production)** — the 10
marquee platforms that carry a hand-curated resource model
(`deepen_actors.PLATFORM_OVERRIDES`): **anthropic, aws, github, openai, plaid,
salesforce, shopify, slack, stripe, twilio**. For each, `main.py` is regenerated
with the production features §6 flagged as the L4 gap:

*   **cursor pagination** on list endpoints (`limit` + `starting_after`, returns
    `has_more` / `total`),
*   **filtering** by any schema field via query params,
*   **relationship expansion** (`?expand=<field>`) for `*Id` reference fields,
*   **strict validation** — required fields + type coercion + unknown-field
    rejection + a structured error envelope (`type`),
*   a **runnable contract test** (`tests/test_<platform>_contract.py`, stdlib
    `unittest`, no WASM runtime needed) asserting: all entities present in the
    schema, full CRUD per entity, pagination + filtering + validation wired,
    L4 health marker, and no proprietary imports.

`evaluate_maturity.py` now recognizes **L4** = L3 thresholds + a contract test +
the production surface (`_paginate` / `_apply_filters` / `_reject_unknown` /
`has_more`).

**Broadened to one reference implementation per domain** (`promote_l4.py
--per-category`): the L4 cohort now spans **all ~70 wave categories** — the 10
curated-override marquees plus a recognizable representative per domain
(salesforce, sap, aws, openai, stripe, github, hl7_fhir, bgp_routing, ros_robotics,
iter_data, …). Every domain therefore has a production-tier reference actor.

**Results:** distribution is now **L3 920 (92.0%) / L4 80 (8.0%)**; the L4
cohort runs ≈ 31–41 endpoints, 7–10 entities, 510–650 LOC; **80 / 80 contract
test suites pass** (8 assertions each). The corpus is still 100% ≥ L3.

**Full-corpus L4.** Auto-generated pagination/validation/tests legitimately meet
this rubric's L4 ("extensive validation, comprehensive schema"), so the generator
*could* lift all 1,000. We hold the long tail at L3 deliberately: true production
fidelity (per-API field/enum/contract accuracy) is gated on the Autonomous
Reverse-Engineering Loop, and an L4 label should mean more than mechanical
feature presence. The per-domain cohort gives production coverage without
overclaiming the tail.
