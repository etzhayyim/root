# ai-gftd-project-bpmn

BPMN repository for bpmn.gftd.ai — publish, search, and generate BPMN diagrams from resources, tsukuru, isco, and apqc domains.

## Architecture

```
Browser → bpmn.gftd.ai (static delivery)
       → API → /gftd.bpmn.v1.BpmnCommandService/... + /gftd.bpmn.v1.BpmnQueryService/...
                  ↓
           App: ai-gftd-wasm-bpmn-bx7qm9p4
             ├─ publish_bpmn / update_bpmn / archive_bpmn
             ├─ generate_bpmn (murakumo.gftd.ai LLM)
             ├─ list_bpmns / search_bpmns / get_bpmn
             └─ SQL graph → bpmn_definitions_current
```

## Component

| Component | Folder | Role |
|---|---|---|
| bpmn-api | `wasm/ai-gftd-wasm-bpmn-bx7qm9p4/` | XRPC API + static SPA |

## Source Domains

| Domain | 意味 |
|---|---|
| `resources` | resources.gftd.ai の entity/resource BPMN |
| `tsukuru` | tsukuru.gftd.ai の製造・RFQ プロセス BPMN |
| `isco` | isco の職業・業務フロー BPMN |
| `apqc` | APQC Process Classification Framework BPMN |

## Arrow Tables

| Table | 用途 |
|---|---|
| `bpmn_definitions_current` | BPMN ドキュメント (xml, source_domain, category, status, tags_json) |

## Build & Deploy

```bash
cd 60-apps/ai-gftd-project-bpmn/wasm/ai-gftd-wasm-bpmn-bx7qm9p4/svelte
pnpm install && pnpm build
cd ..
gftd build
gftd deploy --smoke-url https://bx7qm9p4.gftd.ai/health
```
