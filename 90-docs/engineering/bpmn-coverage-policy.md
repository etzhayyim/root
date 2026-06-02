---
id: bpmn-coverage-policy
title: "BPMN Coverage Policy"
status: active
doc_type: engineering-policy
topic: bpmn-coverage
authoritative: true
last_verified: 2026-04-25
authoritative_for:
  - BPMN-as-actor coverage checks
  - BPMN XML / lexicon / graph seed binding requirements
related:
  - 90-docs/adr/0056-bpmn-as-actor.md
  - adr-0061
---

# BPMN Coverage Policy

## Rule

Every covered BPMN actor must have all three contract surfaces:

- BPMN XML under `etzhayyim-root/00-contracts/bpmn/com/etzhayyim/**`
- Lexicon NSID under `00-contracts/lexicons/com/etzhayyim/apps/**`
- Graph seed binding into `vertex_bpmn_process_def` and `vertex_bpmn_lexicon_binding`

This prevents a BPMN file from existing only as a static artifact without an XRPC route
or dispatcher-visible process registry row.

## Current Coverage Gate

`70-tools/config/bpmn-coverage-manifest.json` currently guards 264 bindings:

| Area | Count | Scope |
|---|---:|---|
| `open-org` | 3 | Takeda GMP batch release, Toyota line stop escalation, Yamato cold-chain exception |
| `projector` | 3 | project message routing, Tree-of-Thoughts exploration, and Self-Consistency answers |
| `industry-classification` | 4 | ISIC entity, concordance, dual-use, and arms-manufacturing classification |
| `occupation-classification` | 2 | ISCO worker classification and concordance recording |
| `open-seiyaku` | 4 | batch registration, batch amendment, purge, export-control screening |
| `pharma-supply` | 3 | product registration, shortage flagging, countermeasure supply gap flagging |
| `pharma-price-policy` | 2 | drug price negotiation round recording and access-gap flagging |
| `patent-expired-pharma` | 11 | expired drug-patent seiyaku progress summary, seiyaku start acknowledgement, seiyaku start queueing, seiyaku batch draft validation, seiyaku batch draft, seiyaku handoff, blocker recording, pipeline execution, backlog collection, screening, and generic manufacturing candidate creation |
| `jp-mhlw-pharma-policy` | 4 | MHLW action recording, policy concern flagging, narcotics control, influenza vaccine administration |
| `ops-logistics` | 2 | last-mile dispatch and delivery confirmation |
| `ops-machinery` | 2 | maintenance plan and downtime flagging |
| `ops-industrial-safety` | 2 | safety assessment and major accident flagging |
| `infra-power` | 2 | power feeder definition and outage reporting |
| `infra-water` | 2 | water main definition and leak reporting |
| `infra-gas` | 2 | gas pipe segment definition and leak reporting |
| `infra-network` | 2 | network link definition and change request |
| `infra-transit` | 2 | transit route definition and delay reporting |
| `infra-rail` | 2 | rail line definition and incident reporting |
| `infra-road` | 2 | road definition and incident reporting |
| `infra-ports` | 2 | vessel call scheduling and port incident reporting |
| `infra-air` | 2 | flight scheduling and air incident reporting |
| `infra-power-market` | 2 | electricity market mechanism recording and missing-money flagging |
| `infra-power-grid-interconnect` | 2 | cross-border power flow recording and curtailment flagging |
| `infra-water-scarcity` | 2 | basin metric recording and treaty dispute flagging |
| `infra-water-stewardship` | 2 | stewardship plan recording and basin stress flagging |
| `infra-wastewater-reuse` | 2 | reuse facility registration and monitoring metric recording |
| `infra-telecom` | 2 | telecom cable registration and cable fault flagging |
| `infra-rural-broadband` | 2 | rural broadband deployment registration and divide-gap flagging |
| `infra-rail-cross-border` | 2 | corridor flow recording and interoperability failure flagging |
| `fund-ma` | 2 | fund manager discovery and M&A deal workflow orchestration |
| `telecom` | 142 | subscriber, SIM, service, usage, billing, SLA, spectrum, cell-site, RAN, network asset, incident, maintenance, RMA, OSS, NFV, MEC, O-RAN, NTN, TSN, WLAN, lawful intercept, and TMF operations |
| `tsukuru-euv` | 5 | EUV lithography manufacturing flow, supplier exchange package normalization and validation, order package preparation, and implementation coverage reporting |
| `coverage` | 6 | census, LDA, fission, and incremental coverage inference |
| `generation` | 7 | ComfyUI and Mangaka image/storyboard/layout generation flows |
| `legal-entity` | 16 | GLEIF, EDGAR, national registry collection, disclosure ingest, and DID registration |
| `media` | 5 | news, social arbitrage, media-gamers guide, and evaluation flows |
| `natural-person` | 1 | cohort batch generation |
| `security` | 1 | smishing message analysis |
| `talent` | 2 | shigotoba job ingest and summarization |
| `vision` | 1 | livecam camera analysis |

## Commands

Run the focused gate:

```sh
pnpm lint:bpmn:coverage
```

Run the manifest quality gate:

```sh
pnpm lint:bpmn:manifest
```

Run the full local BPMN contract gate:

```sh
pnpm lint:bpmn:contracts
```

Run the structural BPMN validation gate:

```sh
pnpm lint:bpmn:structural
```

Run the BPMN/lexicon contract gate:

```sh
pnpm lint:bpmn:lexicon-contract
```

Run the worker task implementation gate:

```sh
pnpm lint:bpmn:worker-tasks
```

Emit the same gate as a machine-readable report:

```sh
pnpm --silent lint:bpmn:coverage:json
pnpm --silent lint:bpmn:manifest:json
pnpm --silent lint:bpmn:contracts:json
pnpm --silent lint:bpmn:structural:json
pnpm --silent lint:bpmn:lexicon-contract:json
pnpm --silent lint:bpmn:worker-tasks:json
```

Run the related NSID existence gate:

```sh
pnpm lint:nsid:exists
```

For Zeebe deploy validation, use a temporary Zeebe 8 broker and deploy the affected BPMN
with the Camunda SDK or equivalent `deployResource` client. The target version used for
the current gate is Zeebe `8.6.39`.

## CI

`lefthook.yml` runs the full BPMN contract gate in `pre-push`:

```sh
lefthook run pre-push
```

The hook delegates to:

```sh
printf '%s\n' <changed-files> | pnpm --silent lint:bpmn:contracts:changed
```

Use `pnpm lint:bpmn:contracts` to force the full gate locally. The changed-file
mode skips when no BPMN-related paths changed and otherwise runs only the
affected gate subset.

The repo `build` script runs `bpmn-coverage-manifest-lint.mjs`,
`bpmn-coverage.mjs`,
`bpmn-structural-validation.mjs`, `bpmn-lexicon-contract.mjs`, and
`bpmn-worker-task-coverage.mjs` before the broader build. The structural gate
parses every covered BPMN with `bpmn-moddle` and checks executable process
shape. The lexicon contract gate checks `defs.main` input/output schemas and
verifies required lexicon inputs are referenced by the BPMN. The worker task
gate verifies that every `zeebe:taskDefinition` used by a covered BPMN has a
registered worker task type.
`.github/workflows/bpmn-coverage.yml` remains limited to the legacy registry
coverage report. New BPMN structural, lexicon-contract, and worker-task gates
belong to lefthook rather than GitHub workflow steps.
The `coverage-site` workflow also runs every 6 hours and writes the same BPMN
coverage gate into `coverage.etzhayyim.com` as `/bpmn-coverage/latest.json`.

Generate the site snapshot locally:

```sh
pnpm coverage:bpmn:site
```

## Adding A Covered BPMN Actor

1. Add or update the BPMN XML.
2. Add the lexicon file whose `id` is the NSID used by the dispatcher.
3. Add a graph migration that seeds both:
   - `vertex_bpmn_process_def`
   - `vertex_bpmn_lexicon_binding`
4. Extend `bindings` in `70-tools/config/bpmn-coverage-manifest.json`.
5. Ensure every `zeebe:taskDefinition` type used by the BPMN is registered by
   worker code.
6. Run:

```sh
pnpm lint:bpmn:contracts
```

## Notes

- Generated seed migrations are allowed to build `sourcePath` from `project` and `proc`;
  the coverage lint accepts both explicit `sourcePath` strings and generated seed entries.
- Use optional `bindingNsid` only when the graph dispatcher binding deliberately differs from
  the lexicon contract NSID; `nsid` remains the lexicon file's `id`.
- `70-tools/config/bpmn-coverage-manifest.json` is the shared source of truth for
  covered BPMN bindings and seed migration files.
- Do not add a BPMN to the coverage gate until it has a stable process id and NSID.
- Organization-specific BPMN files should describe a public actor surface for that
  organization, not private operational facts.
