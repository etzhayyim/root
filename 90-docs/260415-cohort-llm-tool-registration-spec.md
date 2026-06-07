---
id: cohort-llm-tool-registration-spec-260415
title: "Cohort LLM Tool Registration Spec — Murakumo agent から cohort.* を呼び出す"
status: active
doc_type: how-to
topic: cohort-llm
authoritative: false
last_verified: 2026-04-15
related:
  - adr-0026-agent-only-reverse-identity-topology
supersedes: []
superseded_by: []
---

# Goal

Murakumo / Ameno LLM agent が ADR-0026 cohort lifecycle を tool call で操作可能にする。
com.etzhayyim.cohort.* の 4 procedure (seed / emitEvidence / fission / repairEdge) を tool 化。

# Tool Definition (OpenAI tool calling 互換)

## 1. cohort_seed

```json
{
  "type": "function",
  "function": {
    "name": "cohort_seed",
    "description": "Create a new cohort generative actor (ADR-0026 Phase A genesis). Idempotent by segment_hash.",
    "parameters": {
      "type": "object",
      "properties": {
        "pcfL1": {
          "type": "string",
          "description": "APQC L1 slug (1-vision-strategy ... 13-business-capability)"
        },
        "role": {
          "type": "string",
          "description": "Role persona (e.g. salesRep, sreEngineer)"
        },
        "locale": {
          "type": "string",
          "enum": ["jp", "en", "zh", "ko"]
        },
        "industry": { "type": "string" },
        "seniority": { "type": "string", "enum": ["junior", "mid", "senior"] },
        "kAnonymity": { "type": "integer", "minimum": 50, "default": 50 }
      },
      "required": ["pcfL1", "role", "locale"]
    }
  }
}
```

→ host が `etzhayyim cohort gen` 相当の JSON-LD 組立て + POST `/xrpc/com.etzhayyim.cohort.seed`。

## 2. cohort_emit_evidence

```json
{
  "type": "function",
  "function": {
    "name": "cohort_emit_evidence",
    "description": "Append behavioral evidence to a cohort (Phase B). Triggers MV update for fission readiness.",
    "parameters": {
      "type": "object",
      "properties": {
        "cohortDid": { "type": "string" },
        "signalKind": { "type": "string", "description": "e.g. behavior.observation, identity.confirm" },
        "evidencePayload": { "type": "string", "description": "Free-form payload (will be hashed for dedup)" },
        "posterior": { "type": "number", "minimum": 0, "maximum": 1 },
        "judgeAgreement": { "type": "boolean" }
      },
      "required": ["cohortDid", "signalKind", "evidencePayload"]
    }
  }
}
```

## 3. cohort_fission (gated)

```json
{
  "type": "function",
  "function": {
    "name": "cohort_fission",
    "description": "Mint a fissioned individual actor from a cohort (Phase C). REQUIRES posterior>0.95 + judgeAgreement=true + evidence>=1.",
    "parameters": {
      "type": "object",
      "properties": {
        "cohortDid": { "type": "string" },
        "posterior": { "type": "number", "minimum": 0.95, "maximum": 1 },
        "judgeAgreement": { "type": "boolean", "const": true },
        "evidenceUris": {
          "type": "array",
          "items": { "type": "string" },
          "minItems": 1
        }
      },
      "required": ["cohortDid", "posterior", "judgeAgreement", "evidenceUris"]
    }
  }
}
```

LLM が誤って fission を発火しないよう gate を schema 制約として埋め込む (posterior min 0.95、judgeAgreement const true)。

## 4. cohort_list (read)

```json
{
  "type": "function",
  "function": {
    "name": "cohort_list",
    "description": "Enumerate cohorts with optional filters.",
    "parameters": {
      "type": "object",
      "properties": {
        "pcfL1": { "type": "string" },
        "locale": { "type": "string" },
        "kind": { "type": "string", "enum": ["cohort", "fissioned"] },
        "fissionEnabled": { "type": "boolean" },
        "limit": { "type": "integer", "default": 100 }
      }
    }
  }
}
```

# Registration in `kotodama-host-sdk`

`40-engine/kotoba/crates/kotoba-kotodama/sdk/kotodama-host-sdk/src/llm-tools.ts` (新規予定) に上記 4 tool spec をハードコード or `00-contracts/lexicons/com/etzhayyim/cohort/*.json` から自動生成。

```typescript
// 推奨実装パターン
import { cohortToolSpecs } from './llm-tools-cohort';

await llmCall({
  messages: [...],
  tools: [...standardTools, ...cohortToolSpecs],
  toolHandler: async (call) => {
    if (call.name === 'cohort_seed') {
      return await pdsClient.fetch('/xrpc/com.etzhayyim.cohort.seed', {
        method: 'POST',
        body: JSON.stringify({
          segmentJsonld: JSON.stringify(call.args),
          kAnonymity: call.args.kAnonymity ?? 50,
        }),
      });
    }
    // ... other 3 tools
  },
});
```

# Audit / Safety

- 全 tool call は OCEL audit に emit (`com.etzhayyim.cohort.llmToolCall` index)
- `cohort_fission` は posterior min/judgeAgreement const で LLM 誤発火を schema-level に防止
- `cohort_emit_evidence` は signalKind を whitelist 化 (将来) して spam evidence を防止

# Bootstrap Loop (Murakumo 自律 cohort fleet 拡張)

```
1. Murakumo agent 起動 → `cohort_list` で現状 fleet 確認
2. 不足 segment (gap analysis) を判定
3. `cohort_seed` で N 件の新規 cohort 投入
4. 一定期間 evidence 観測 (other agents が `cohort_emit_evidence` 呼出)
5. fission_ready_count > 0 な cohort を `cohort_fission`
6. snapshot diff で 1 週間後の fleet 推移を観察
```

これにより ADR-0026 cohort fleet が **agent-driven 自己拡張** モードに入る。

# References

- `00-contracts/lexicons/com/etzhayyim/cohort/seed.json`
- `00-contracts/lexicons/com/etzhayyim/cohort/emitEvidence.json`
- `00-contracts/lexicons/com/etzhayyim/cohort/fission.json`
- `00-contracts/lexicons/com/etzhayyim/cohort/listCohorts.json`
- `40-engine/kotoba/crates/kotoba-kotodama/sdk/kotodama-host-sdk/src/llm.ts`
- `40-engine/kotoba/crates/kotoba-kotodama/sdk/kotodama-host-sdk/src/cohort.ts`
- `90-docs/adr/0026-agent-only-reverse-identity-topology.md`
