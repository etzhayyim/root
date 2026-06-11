# Shinka Coverage Healing — Actor Information Completeness via Autonomous Evolution

**Date**: 2026-04-09
**Status**: `[IMPLEMENTING]`
**Depends**: `90-docs/260408-actor-executor-p5p3-architecture-design.md`

## Problem

1,096 actors in graph (`graphar.vertex_actor`), η=0.935。残り 6.5% は主に:
- `wit_imports/exports`: 282 actors (26%) — 削除前に WIT が存在しなかった
- `convo_system_prompt`: 208 actors (19%) — prompt 未設定
- `capabilities`: 7 actors — MCP capability 未宣言
- `performer_type/operator`: 一部 actor — kotodama.jsonld 不完全

## Hinshitsu (品質) Grades

| Grade | Count | Avg Score | Description |
|---|---|---|---|
| **critical** | 7 | 0.679 | 3+ critical fields missing (WIT + prompt + caps) |
| **incomplete** | 276 | 0.822 | 1-2 critical fields missing (WIT or prompt) |
| **complete** | 813 | 0.973 | All critical fields present |

Data: `80-data/shannon/snapshots/snap-20260409-actor-hinshitsu.parquet`

## Solution: Shinka Autonomous Healing Loop

```
shinka cron (*/5 min)
  ↓
1. Coverage Query: SELECT actors WHERE coverage_score < 1.0 ORDER BY score ASC LIMIT 10
  ↓
2. Priority Queue: critical → incomplete → complete (by score ascending)
  ↓
3. Per-Actor Healing (Murakumo LLM):
   ├── Missing WIT?      → etzhayyim wit-gen (generate from name + description + capabilities)
   ├── Missing prompt?    → agent.chat("Generate convo system prompt for: {displayName} - {description}")
   ├── Missing caps?      → agent.chat("List capabilities for: {displayName}") → parse JSON
   ├── Missing performer? → infer from project type (service/system)
   └── Missing operator?  → default "etzhayyim.com"
  ↓
4. Graph UPDATE (Stream Load or XRPC registerManifest)
  ↓
5. Score Recalculation → next cycle
```

## Architecture

### etzhayyim coverage Command

```bash
# Show per-actor coverage scores
etzhayyim coverage list [--grade critical|incomplete|complete] [--limit 20]

# Show system-wide η
etzhayyim coverage eta

# Show missing fields for specific actor
etzhayyim coverage inspect <did>

# Trigger healing for worst N actors
etzhayyim coverage heal [--limit 10] [--dry-run]
```

### etzhayyim hinshitsu Command

```bash
# Quality dashboard (coverage + staleness + consistency)
etzhayyim hinshitsu report

# Per-field coverage breakdown
etzhayyim hinshitsu fields

# Actor ranking by quality score
etzhayyim hinshitsu rank [--worst 20]

# Validate actor data consistency (graph ↔ manifest ↔ WIT)
etzhayyim hinshitsu validate <did>
```

### Shinka Healing Pipeline (T1 MCP-Compose)

```jsonld
{
  "@context": "https://etzhayyim.com/ns/actor/v1",
  "@id": "did:web:shinka.etzhayyim.com",
  "executionTier": "T2",
  "pipelines": [{
    "trigger": { "type": "cron", "cron": "*/5 * * * *" },
    "steps": [
      {
        "fn": "graph.query",
        "id": "gaps",
        "args": {
          "cypher": "SELECT did, name, display_name, description, capabilities, wit_imports, convo_system_prompt, performer_type FROM graphar.vertex_actor WHERE _alive = true AND (wit_imports IS NULL OR wit_imports = '[]' OR convo_system_prompt IS NULL OR convo_system_prompt = '') ORDER BY CASE WHEN wit_imports IS NULL OR wit_imports = '[]' THEN 0 ELSE 1 END, did LIMIT 10"
        }
      },
      {
        "fn": "custom",
        "id": "heal",
        "handler": "export default async (ctx, input) => {\n  const results = [];\n  for (const actor of input.gaps.rows) {\n    const fixes = {};\n    if (!actor.convo_system_prompt) {\n      const r = await ctx.agent.chat({ message: `Generate a concise system prompt for AI actor: ${actor.display_name} - ${actor.description}. Return only the prompt text.` });\n      fixes.convo_system_prompt = r.text;\n    }\n    if (!actor.wit_imports || actor.wit_imports === '[]') {\n      fixes.wit_imports = JSON.stringify(['kotodama:governance/governance', 'kotodama:identity/capability', 'kotodama:agent/agent']);\n      fixes.wit_exports = JSON.stringify([`etzhayyim:${actor.name}/service`]);\n    }\n    if (!actor.performer_type) fixes.performer_type = 'service';\n    if (Object.keys(fixes).length > 0) {\n      const sets = Object.entries(fixes).map(([k,v]) => `${k} = '${v.replace(/'/g, \"\\\\'\")}'`).join(', ');\n      await ctx.graph.write({ template: `UPDATE graphar.vertex_actor SET ${sets} WHERE did = '${actor.did}'` });\n      results.push({ did: actor.did, fixed: Object.keys(fixes) });\n    }\n  }\n  return { healed: results.length, results };\n}",
        "capabilities": ["agent.chat", "graph.query", "graph.write"]
      },
      {
        "fn": "derive:social",
        "args": { "template": "Shinka: healed {heal.healed} actors ({heal.results[0].did}, ...)" }
      }
    ]
  }]
}
```

### Murakumo Agent Processing Flow

**Model SSoT**: `40-engine/kotoba/crates/kotoba-kotodama/sdk/kotodama-host-sdk/src/llm-model-registry.ts` — `resolveModel(hint, useCase)` で解決。ハードコードモデル名禁止。

```
Murakumo Fleet (resolveModel(undefined, "shinka") → gemma-4-e4b-it)
  ↓
1. WIT Generation (useCase: "structured"):
   Model: resolveModel(undefined, "structured") → gemma-4-e4b-it
   Input:  { name: "isbn", description: "ISBN 書籍識別", capabilities: ["graph.write", "browser.fetch"] }
   Output: { imports: ["kotodama:governance/governance", "kotodama:identity/capability", ...],
             exports: ["etzhayyim:isbn/book-registry", "etzhayyim:isbn/publisher-registry"] }

2. Convo Prompt Generation (useCase: "general"):
   Model: resolveModel(undefined, "general") → gemma-4-e4b-it
   Input:  { name: "hanrei", displayName: "判例・法令・司法 global intelligence" }
   Output: "あなたは判例・法令の AI エキスパートです。83 jurisdictions の判例データベースを管理し、..."

3. Capability Inference (useCase: "json"):
   Model: resolveModel(undefined, "json") → qwen3-30b
   Input:  { name: "yabai", description: "risk intelligence (AML/CTI)" }
   Output: ["graph.query", "graph.write", "agent.chat", "agent.invoke", "browser.fetch"]
```

## Convergence Model

```
Cycle 0:  η = 0.935, critical=7, incomplete=276
Cycle 1:  heal 10 worst → η ≈ 0.940
Cycle 2:  heal 10 more  → η ≈ 0.945
...
Cycle N:  η → 1.000 (asymptotic, ~28 cycles for critical+incomplete)

Rate: 10 actors / 5 min = 120 actors/hour
Time to η=1.0: ~283 actors / 120 = ~2.4 hours
```

## Parquet Snapshots

| File | Content |
|---|---|
| `snap-20260409-actor-unified-graph.parquet` | 1,096 actors × 32 fields (SSoT) |
| `snap-20260409-actor-hinshitsu.parquet` | Per-actor coverage_score + missing_fields + grade |
| `snap-20260409-fs-graph-transfer.parquet` | η progression (0.143 → 0.935) |

## Files

| File | Purpose |
|---|---|
| `80-data/shannon/snapshots/snap-20260409-actor-hinshitsu.parquet` | Per-actor quality scores |
| `70-tools/etzhayyim/etzhayyim/coverage.go` | `etzhayyim coverage` CLI (planned) |
| `70-tools/etzhayyim/etzhayyim/hinshitsu.go` | `etzhayyim hinshitsu` CLI (planned) |
| `50-infra/.../pds/src/actor-executor-shared.ts` | Shinka healing pipeline execution |
| `60-apps/etzhayyim-project-shinka/` | Shinka actor (cron */5 min evolution) |
