# ai-gftd-project-tsukuru

B2B factory-direct ordering platform for `tsukuru.etzhayyim.com`.

## Canonical IDs and Naming Rules

- Canonical nanoid is `tsukr8u0`.
- `0ljdfw8u` is deprecated (alpha-start violation) and must not be used in new paths, hosts, component names, or deploy commands.
- Canonical app/component name is `tsukuru` (not `tsukuru-api`).

## Runtime and Endpoint Rules

- API base URL: `https://tsukr8u0.etzhayyim.com/xrpc`.
- DID root: `did:web:tsukuru.etzhayyim.com`.
- Manufacturer DID model remains path-based dynamic multi-DID (`performerType=service`).

## Manufacturer Registry Rules

- Active collection name: `ai.gftd.apps.tsukuru.manufacturer`.
- Historical collection for migration/read-compat: `ai.gftd.apps.tsukuru-api.manufacturer`.
- Registry scale assumption: 460+ manufacturer DIDs across 30+ countries.

## Write Buffer Rule

- Use unified batch-flush write-buffer path for graph writes.
- Optimization target and current reference: Shannon efficiency `η = 99.8%`.
- Avoid ad-hoc per-record flush patterns unless explicitly required for correctness.

## Required WIT Packages

- `gftd:tsukuru@0.1.0`
- `gftd:tsukuru-process-registry@1.0.0`
- `gftd:tsukuru-manufacturer-registry@1.0.0`
- `gftd:tsukuru-trade-compliance@1.0.0`
- `gftd:tsukuru-production-order@1.0.0`

## Production Order (BTO/OEM)

**WIT**: `gftd:tsukuru-production-order@1.0.0` — production-order, production-progress, quality-inspection

**Record kinds** (`ai.gftd.apps.tsukuru.*`): `production_order`, `production_progress`, `quality_inspection`

**Flow**: okaimono order (paid) → `create-production-order` → factory DID Invoke → progress updates → QC → ship

**Fulfillment modes**: `bto` (Build-to-Order), `mto` (Made-to-Order), `cto` (Configure-to-Order)

設計: `90-docs/260326-okaimono-bto-oem-manufacturing-design.md`

**Convo Integration**: `yoro.etzhayyim.com/profile/did:web:tsukr8u0.etzhayyim.com` → メッセージ → Murakumo LLM + MCP tool calling で製造プロジェクト実行。`convoSystemPrompt` (magatama.jsonld) でガイダンス。

## CNT / CNT Fiber Process Automation

**WIT surface**: `gftd:tsukuru-process-registry@1.0.0` + `gftd:tsukuru-production-order@1.0.0`

**XRPC**:
- `ai.gftd.apps.tsukuru.cnt.designManufacturingFlow`
- `ai.gftd.apps.tsukuru.cnt.planAutomation`
- `ai.gftd.apps.tsukuru.cnt.prepareOrderPackage`
- `ai.gftd.apps.tsukuru.cnt.getAutomationCoverage`
- `ai.gftd.apps.tsukuru.cnt.getProcessCatalog`
- `ai.gftd.apps.tsukuru.cnt.prepareRunPackage`
- `ai.gftd.apps.tsukuru.cnt.validateRunPackage`

**BPMN**:
- `tsukuru_cnt_fiber_manufacturing_flow`
- `tsukuru_cnt_automation_plan`
- `tsukuru_prepare_cnt_order_package`
- `tsukuru_get_cnt_automation_coverage`
- `tsukuru_prepare_cnt_run_package`
- `tsukuru_validate_cnt_run_package`

**Open signal actors**: `open-chemicals-management`, `open-critical-minerals`,
`open-ai-supply-chain`, `open-hs`, `open-commodity-trade`, `open-cbam-embedded`,
and `open-carbon-tax` are bound as external observation inputs. They do not
replace the Tsukuru manufacturing owner; they feed compliance, supply, customs,
and embedded-carbon context into the CNT flow.

**Catalog/schema data**:
- code: `60-apps/ai-gftd-project-tsukuru/appview/tsukuru-tsukr8u0/src/cnt-process-catalog.ts`
- schema: `00-contracts/schemas/tsukuru-cnt-process-catalog.schema.json`
- data: `00-contracts/catalogs/ai/gftd/tsukuru/cnt/process-catalog.v1.json`
- run package schema: `00-contracts/schemas/tsukuru-cnt-run-package.schema.json`
- run package example: `00-contracts/examples/ai/gftd/tsukuru/cnt/run-package.example.v1.json`
- run validation schema: `00-contracts/schemas/tsukuru-cnt-run-validation.schema.json`
- run validation example: `00-contracts/examples/ai/gftd/tsukuru/cnt/run-validation.example.v1.json`

## Cross-Project Dependencies

| Project | Integration | Purpose |
|---|---|---|
| `ai-gftd-project-cpc` | WIT bidirectional dependency | CPC process resolution and performer linking |
| `ai-gftd-project-resources` | XRPC `CreateResource` | Supplier/resource synchronization |
| `ai-gftd-project-legal-entity` | `Invoke` LEI lookup | Legal entity verification |
| `ai-gftd-project-yabai` | `Invoke` `ScreenEntity` | Sanctions and denied-party screening |
| `ai-gftd-project-trust` | `Invoke` `GetTrustScore` | DID trust scoring |
| `ai-gftd-project-completer` | `Invoke` `EvaluateCompliance` | Trade/regulatory compliance evaluation |
| `ai-gftd-project-treaty` | Authority chain | FTA/EPA trade agreement resolution |
| `ai-gftd-project-industry-standard` | Authority chain follow | ISO and industry standard tracking |
| `ai-gftd-project-maps` | Graph `:LOCATED_IN` relation | Factory geolocation linkage |
| `ai-gftd-project-supply-chain` | Graph `:SUPPLIES` relation | Upstream/downstream risk and supplier graph |
| `ai-gftd-project-okaimono` | Catalog integration | Factory-direct catalog federation |

## Build and Deploy

```bash
cd 60-apps/ai-gftd-project-tsukuru/wasm/tsukuru-tsukr8u0
gftd build
gftd deploy --smoke-url https://tsukr8u0.etzhayyim.com/health
```

## Storage and Access Rules

- Graph access must go through `G()` builder only.
- Keep fallback behavior explicit and minimal when graph is unavailable.
