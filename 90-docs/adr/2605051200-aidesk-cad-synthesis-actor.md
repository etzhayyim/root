---
id: aidesk-cad-synthesis-actor
title: "ADR-2605051200: aidesk — AI Design Desk CAD Synthesis Actor"
status: active
doc_type: adr
topic: aidesk-cad-synthesis-actor
authoritative: true
last_verified: 2026-05-06
authoritative_for:
  - aidesk actor design
  - Zero-To-CAD inference pipeline
  - CAD synthesis license gate
related:
  - cf-worker-edge-layer-zeebe-rw-udf-business-logic
  - bpmn-as-actor
  - worker-direct-hyperdrive-persistence
  - atproto-native-identifier-topology
  - simplified-3layer-identity-rw-vault
supersedes: []
superseded_by: []
---

# ADR-2605051200: aidesk — AI Design Desk CAD Synthesis Actor

**Date**: 2026-05-05
**Status**: proposed
**Supersedes**: —
**Superseded by**: —

---

## Context

`tsukuru.etzhayyim.com` は B2B factory-direct OEM 製造プラットフォームとして、AutoCAD / Fusion 360 / STEP ファイルを `supplierExchange` パッケージとして受け入れる。しかし設計者が 3D CAD ファイルを手元に持っていない場合 — 製品のスケッチ写真、多視点画像、テキスト説明 — から tsukuru RFQ に直接繋ぐ経路がなかった。

**ADSKAILab (Autodesk AI Lab / HuggingFace)** が 2026-04〜05 にかけて公開したモデル群がこのギャップを埋める:

| モデル | ライセンス | タスク | 用途 |
|---|---|---|---|
| Zero-To-CAD-Qwen3-VL-2B | **Apache 2.0** | 画像 (8-view) → CadQuery Python → STEP | **商用 B2B フロー可** |
| Make-A-Shape-single/multi-view-20m | Autodesk Non-Commercial v1.0 | 画像 → 3D mesh | 研究・デモのみ |
| Make-A-Shape-point-cloud-20m | Autodesk Non-Commercial v1.0 | Point cloud → 3D mesh | 研究・デモのみ |
| WaLa-PC-1B | Autodesk Non-Commercial v1.0 | Point cloud → 3D | 研究・デモのみ |
| WaLa-MVDream-RGB4/DM6 | Autodesk Non-Commercial v1.0 | Text → 3D (MVDream) | 研究・デモのみ |

**ライセンス境界** はこの設計の第一軸:
- Zero-To-CAD (Apache 2.0) のみが tsukuru 商用 supplierExchange フローに繋がれる
- Non-Commercial モデル群は Phase 2 `research` namespace 限定、tsukuru handoff handler から構造的到達不能

---

## Decisions

### D1: アクター名・識別子

| 属性 | 値 |
|---|---|
| Domain | `aidesk.etzhayyim.com` |
| Nanoid | `a1d3sk00` |
| Primary DID | `did:erc725:etzhayyim:260505:{identityContract}` |
| AT facade DID | `did:web:aidesk.etzhayyim.com` |
| NSID prefix (商用) | `com.etzhayyim.apps.aidesk.*` |
| NSID prefix (研究) | `com.etzhayyim.apps.aidesk.research.*` (Phase 2) |
| AT Protocol layer | L3 Dispatcher (CF Worker) + L7 BPMN (pymagatama) |
| Tier | T2 inference/orchestration + T3 CF Worker facade |

### D2: 推論ホスティング (Phase 1)

**Zero-To-CAD-Qwen3-VL-2B (2B params, ~4GB)** を既存 `mitama-udf-pool` AMD64 node で CPU 非同期推論。
- 設計ジョブは BPMN 非同期キュー処理 → 30-60s CPU 推論レイテンシ許容
- B2 に対する モデルウェイト DL + キャッシュ戦略: pod 内 `/model-cache/zero-to-cad` マウント
- Phase 2 GPU フェーズ: `g2-gpu-rtx4000a1-l` (RTX 4000, 20 GiB VRAM) Vultr GPU node 追加時に切替

```yaml
# 50-infra/vultr/mitama-udf-pool/values.yaml への追記 (Phase 2)
aideskWorker:
  enabled: false   # Phase 1 = pymagatama 同居, Phase 2 = dedicated pod
  image: ghcr.io/etzhayyim/pymagatama:{tag}
  resources:
    requests: { cpu: "4", memory: "12Gi" }
    limits:   { cpu: "8", memory: "16Gi" }
  modelCache:
    volume: aidesk-model-cache
    mountPath: /model-cache
```

### D3: Tier 選択 (ADR-2604282300 準拠)

```
[User / tsukuru]
      │  upload images / STEP / text
      ▼
 T3 CF Worker (aidesk.etzhayyim.com, thin L3 Dispatcher)
   - XRPC facade: submitDesignJob / getDesignJob / listDesignJobs / exportToTsukuru
   - Blob upload → B2 (SHA-256 content-addressed, ADR-0036)
   - Hyperdrive Kysely INSERT vertex_aidesk_design_job (status=queued)
   - Zeebe publishMessage → trigger BPMN
      │
      ▼
 L7 Zeebe BPMN (T2 pymagatama worker, K8s-internal)
   aidesk_synthesize_cad_from_image:
     1. generic.db.select  → fetch job + input blob from B2
     2. aidesk.cad.synthesize → Zero-To-CAD inference
                                  - 8-view render preparation (CadQuery stub)
                                  - Qwen3-VL-2B vision inference → CadQuery Python code
                                  - execute() → STEP file
     3. generic.db.insert  → vertex_aidesk_artifact (license_tier="apache2")
     4. [optional] aidesk.tsukuru.handoff → submit to tsukuru supplierExchange
```

### D4: tsukuru BPMN 再利用 (DRY)

aidesk BPMN の handoff step は以下 K8s-internal call:
```
generic.pds.dispatch (K8s-internal bpmn-dispatcher ClusterIP)
  NSID: com.etzhayyim.apps.tsukuru.supplierExchange.normalizePackage
  variables: { stepB2Key, cadqueryCode, licenseTier, originJobId }
```

**aidesk 側では normalize / validate を再実装しない。** tsukuru の `normalize-supplier-exchange-package.bpmn` + `validate-supplier-exchange-package.bpmn` に委譲。

### D5: ライセンス強制ゲート

```python
# pymagatama/primitives/aidesk.py
COMMERCIAL_LICENSE_TIERS = {"apache2"}

def _tsukuru_handoff_gate(artifact: dict) -> None:
    """tsukuru handoff requires Apache 2.0 license. Structural gate — not a check."""
    if artifact["license_tier"] not in COMMERCIAL_LICENSE_TIERS:
        raise ValueError(
            f"Artifact license_tier={artifact['license_tier']!r} cannot be "
            "forwarded to tsukuru commercial supplier exchange. "
            "Only Apache 2.0 artifacts are permitted."
        )
```

- `vertex_aidesk_artifact.license_tier` は INSERT 時に model 由来で固定、変更不可
- tsukuru handoff BPMN step は `license_tier` を SELECT → gate 関数 → pass/fail
- Non-Commercial モデル出力は `com.etzhayyim.apps.aidesk.research.*` NSID のみ、`vertex_aidesk_research_artifact` table (別テーブル, tsukuru JOIN 不可)

---

## XRPC Commands (Phase 1)

### Commercial (Apache 2.0 only)

| NSID | Kind | Input | Output |
|---|---|---|---|
| `com.etzhayyim.apps.aidesk.submitDesignJob` | procedure | `{ inputImages: BlobRef[], inputType: "multi-view"\|"single-view", notes?: string }` | `{ jobId: string, status: "queued" }` |
| `com.etzhayyim.apps.aidesk.getDesignJob` | query | `{ jobId: string }` | `DesignJob` |
| `com.etzhayyim.apps.aidesk.listDesignJobs` | query | `{ actorDid?: string, status?: string, limit?: int, offset?: int }` | `{ jobs: DesignJob[], total: int, offset: int, limit: int }` |
| `com.etzhayyim.apps.aidesk.exportToTsukuru` | procedure | `{ artifactId: string, rfqNotes?: string }` | `{ tsukuruPackageId: string, status: "submitted" }` |
| `com.etzhayyim.apps.aidesk.designJob` | record | — | DesignJob record |
| `com.etzhayyim.apps.aidesk.artifact` | record | — | Artifact record |

### Research (Phase 2, Non-Commercial — aidesk.research.* namespace)

| NSID | Model | License |
|---|---|---|
| `com.etzhayyim.apps.aidesk.research.synthesizeFromText` | WaLa-MVDream | Autodesk Non-Commercial |
| `com.etzhayyim.apps.aidesk.research.reconstructFromPointCloud` | WaLa-PC-1B | Autodesk Non-Commercial |
| `com.etzhayyim.apps.aidesk.research.synthesizeFromSingleView` | Make-A-Shape-single-view | Autodesk Non-Commercial |

Research NSID は tsukuru handler から **import 不可** (BPMN 依存なし、JOIN 不可)。

---

## RisingWave Schema

```sql
-- Commercial artifacts (Apache 2.0 only, tsukuru-joinable)
CREATE TABLE vertex_aidesk_design_job (
    vertex_id       VARCHAR PRIMARY KEY,   -- at://did:web:aidesk.etzhayyim.com/com.etzhayyim.apps.aidesk.designJob/{rkey}
    actor_did       VARCHAR NOT NULL,      -- did:erc725:... (ADR-0095)
    org_did         VARCHAR NOT NULL,
    at_did          VARCHAR,               -- nullable, federation alias
    input_type      VARCHAR NOT NULL,      -- "multi-view" | "single-view"
    model_id        VARCHAR NOT NULL,      -- "ADSKAILab/Zero-To-CAD-Qwen3-VL-2B"
    license_tier    VARCHAR NOT NULL,      -- "apache2" | "adsk-noncommercial"
    status          VARCHAR NOT NULL,      -- "queued" | "running" | "done" | "failed"
    input_b2_keys   TEXT[],               -- SHA-256 B2 blob keys for input images
    error_message   VARCHAR,
    created_at      VARCHAR NOT NULL
);

CREATE TABLE vertex_aidesk_artifact (
    vertex_id       VARCHAR PRIMARY KEY,   -- at://did:web:aidesk.etzhayyim.com/com.etzhayyim.apps.aidesk.artifact/{rkey}
    job_id          VARCHAR NOT NULL,
    actor_did       VARCHAR NOT NULL,
    org_did         VARCHAR NOT NULL,
    at_did          VARCHAR,
    format          VARCHAR NOT NULL,      -- "step" | "cadquery" | "glb"
    b2_key          VARCHAR NOT NULL,      -- STEP/CadQuery file in B2
    license_tier    VARCHAR NOT NULL,      -- IMMUTABLE at INSERT
    cadquery_code   TEXT,                  -- CadQuery Python code (text column)
    tsukuru_package_id VARCHAR,           -- set after exportToTsukuru
    created_at      VARCHAR NOT NULL
);

CREATE TABLE edge_aidesk_job_artifact (
    src_vertex_id   VARCHAR NOT NULL,     -- vertex_aidesk_design_job.vertex_id
    dst_vertex_id   VARCHAR NOT NULL,     -- vertex_aidesk_artifact.vertex_id
    created_at      VARCHAR NOT NULL,
    PRIMARY KEY (src_vertex_id, dst_vertex_id)
);

-- Streaming MV for job monitoring
CREATE MATERIALIZED VIEW mv_aidesk_job_status AS
SELECT
    j.actor_did,
    j.status,
    j.license_tier,
    COUNT(*) AS job_count,
    MAX(j.created_at) AS last_activity
FROM vertex_aidesk_design_job j
GROUP BY j.actor_did, j.status, j.license_tier;

-- Research artifacts (Non-Commercial — isolated, NOT joinable with vertex_aidesk_artifact)
CREATE TABLE vertex_aidesk_research_artifact (
    vertex_id       VARCHAR PRIMARY KEY,
    actor_did       VARCHAR NOT NULL,
    org_did         VARCHAR NOT NULL,
    at_did          VARCHAR,
    model_id        VARCHAR NOT NULL,
    license_tier    VARCHAR NOT NULL DEFAULT 'adsk-noncommercial',
    input_type      VARCHAR NOT NULL,
    b2_key          VARCHAR NOT NULL,
    created_at      VARCHAR NOT NULL
);
```

---

## BPMN Processes

### `aidesk_synthesize_cad_from_image.bpmn` (timer: event-triggered via Zeebe message)

```
[Start: Message "aidesk.job.queued"]
  → [ServiceTask: aidesk.cad.renderPrepare]     -- validate 8-view layout, prep image tensors
  → [ServiceTask: aidesk.cad.synthesize]         -- Zero-To-CAD inference → CadQuery code
  → [ServiceTask: aidesk.cad.execute]            -- execute CadQuery → STEP file
  → [ServiceTask: generic.db.insert]             -- vertex_aidesk_artifact (license_tier="apache2")
  → [ServiceTask: generic.db.insert]             -- vertex_aidesk_design_job status=done
  → [ExclusiveGateway: auto_export?]
    → [YES] → [ServiceTask: aidesk.tsukuru.handoff] → tsukuru normalizePackage (K8s-internal)
    → [NO]  → [End]
```

### `aidesk_export_to_tsukuru.bpmn` (manual export, triggered by exportToTsukuru XRPC)

```
[Start: Message "aidesk.export.requested"]
  → [ServiceTask: generic.db.select]             -- fetch artifact, assert license_tier="apache2"
  → [ServiceTask: aidesk.tsukuru.handoff]        -- K8s-internal: tsukuru.supplierExchange.normalizePackage
  → [ServiceTask: generic.db.insert]             -- vertex_aidesk_artifact tsukuru_package_id set
  → [End]
```

---

## tsukuru Integration Flow (End-to-End)

```
[設計者]
  → POST com.etzhayyim.apps.aidesk.submitDesignJob
      { inputImages: [B2 blob refs], inputType: "multi-view" }
  → CF Worker: INSERT vertex_aidesk_design_job (status=queued)
               Zeebe.publishMessage("aidesk.job.queued", jobId)

[Zeebe BPMN: aidesk_synthesize_cad_from_image]
  → aidesk.cad.synthesize (Zero-To-CAD inference)
      ↓ CadQuery Python code
  → aidesk.cad.execute    (execute → STEP file → B2)
      ↓ b2_key
  → INSERT vertex_aidesk_artifact (license_tier="apache2")
  → UPDATE vertex_aidesk_design_job (status=done)

[設計者がエクスポート指示]
  → POST com.etzhayyim.apps.aidesk.exportToTsukuru { artifactId }

[Zeebe BPMN: aidesk_export_to_tsukuru]
  → license_tier gate (apache2 only)
  → K8s-internal: com.etzhayyim.apps.tsukuru.supplierExchange.normalizePackage
      { stepB2Key, cadqueryCode, originJobId }
  → tsukuru: normalize-supplier-exchange-package.bpmn
  → tsukuru: validate-supplier-exchange-package.bpmn
  → tsukuru RFQ marketplace

[tsukuru のサプライヤー]
  → STEP ファイル受信 → 見積 → production order
```

---

## pymagatama Primitives

```python
# 20-actors/magatama/py/src/pymagatama/primitives/aidesk.py

from pymagatama.primitives.core import rw_conn
import boto3, subprocess, tempfile, os, json

ZERO_TO_CAD_MODEL = "ADSKAILab/Zero-To-CAD-Qwen3-VL-2B"
COMMERCIAL_LICENSE_TIERS = {"apache2"}

async def task_aidesk_cad_synthesize(variables: dict) -> dict:
    """Zero-To-CAD inference: 8-view images → CadQuery Python code."""
    job_id   = variables["jobId"]
    b2_keys  = variables["inputB2Keys"]   # list of B2 keys

    # 1. download images from B2
    images = [_b2_download(k) for k in b2_keys]

    # 2. run Zero-To-CAD inference (transformers pipeline)
    from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
    model_path = "/model-cache/zero-to-cad"
    processor  = AutoProcessor.from_pretrained(model_path, trust_remote_code=True)
    model      = Qwen2VLForConditionalGeneration.from_pretrained(model_path)
    cadquery_code = _run_zero_to_cad(model, processor, images)

    return {
        "cadqueryCode": cadquery_code,
        "licenseTier": "apache2",
        "modelId": ZERO_TO_CAD_MODEL,
    }

async def task_aidesk_cad_execute(variables: dict) -> dict:
    """Execute CadQuery Python code → STEP file → upload to B2."""
    code   = variables["cadqueryCode"]
    job_id = variables["jobId"]

    with tempfile.TemporaryDirectory() as tmpdir:
        py_path   = os.path.join(tmpdir, "model.py")
        step_path = os.path.join(tmpdir, "model.step")
        with open(py_path, "w") as f:
            f.write(code)
            f.write(f'\nimport cadquery as cq; cq.exporters.export(result, "{step_path}")\n')
        subprocess.run(["python", py_path], timeout=120, check=True, cwd=tmpdir)
        b2_key = _b2_upload(step_path, f"aidesk/{job_id}/model.step")

    return {"stepB2Key": b2_key, "format": "step"}

def _tsukuru_handoff_gate(artifact: dict) -> None:
    if artifact["license_tier"] not in COMMERCIAL_LICENSE_TIERS:
        raise ValueError(
            f"license_tier={artifact['license_tier']!r} cannot be forwarded "
            "to tsukuru commercial supplier exchange. Only Apache 2.0 permitted."
        )

async def task_aidesk_tsukuru_handoff(variables: dict) -> dict:
    """Forward Apache-2.0 artifact to tsukuru normalizePackage via K8s-internal."""
    _tsukuru_handoff_gate(variables)    # structural gate — not a soft check
    # Delegates to generic.pds.dispatch (K8s-internal bpmn-dispatcher ClusterIP)
    # NSID: com.etzhayyim.apps.tsukuru.supplierExchange.normalizePackage
    return {"tsukuruPackageId": variables.get("tsukuruPackageId"), "dispatched": True}
```

---

## T3 CF Worker (aidesk-tsukr8u0 — thin XRPC facade)

```typescript
// 60-apps/etzhayyim-project-aidesk/appview/aidesk-a1d3sk00/src/app.ts
import { createWorkerExport, createKyselyDb } from "@etzhayyim/magatama-host-sdk";
import type { Database } from "@etzhayyim/graph-schema";

export default createWorkerExport((sdk) => {
  const db = createKyselyDb<Database>((sdk.env as any).HYPERDRIVE);

  sdk.app.command("com.etzhayyim.apps.aidesk.submitDesignJob", async ({ input }) => {
    const jobId = `aidesk-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
    await db.insertInto("vertex_aidesk_design_job").values({
      vertex_id:    `at://did:web:aidesk.etzhayyim.com/com.etzhayyim.apps.aidesk.designJob/${jobId}`,
      actor_did:    input.actorDid,
      org_did:      input.orgDid ?? "anon",
      at_did:       input.atDid ?? null,
      input_type:   input.inputType,
      model_id:     "ADSKAILab/Zero-To-CAD-Qwen3-VL-2B",
      license_tier: "apache2",
      status:       "queued",
      input_b2_keys: input.inputImages,
      created_at:   new Date().toISOString(),
    }).execute();

    await sdk.zeebe.publishMessage({
      name: "aidesk.job.queued",
      correlationKey: jobId,
      variables: { jobId, inputB2Keys: input.inputImages, inputType: input.inputType },
    });

    return { jobId, status: "queued" };
  });

  sdk.app.query("com.etzhayyim.apps.aidesk.getDesignJob", async ({ input }) => {
    const job = await db.selectFrom("vertex_aidesk_design_job")
      .where("vertex_id", "like", `%${input.jobId}`)
      .selectAll()
      .limit(1)
      .executeTakeFirst();
    if (!job) return { error: "not found" };
    return job;
  });

  sdk.app.query("com.etzhayyim.apps.aidesk.listDesignJobs", async ({ input }) => {
    const limit  = Math.min(input.limit ?? 50, 200);
    const offset = input.offset ?? 0;
    const jobs = await db.selectFrom("vertex_aidesk_design_job")
      .where("actor_did", "=", input.actorDid ?? "")
      .selectAll()
      .limit(limit)
      .offset(offset)
      .execute();
    return { jobs, offset, limit };
  });

  sdk.app.command("com.etzhayyim.apps.aidesk.exportToTsukuru", async ({ input }) => {
    // Verify artifact exists + license_tier = apache2 (gate enforced in BPMN)
    const artifact = await db.selectFrom("vertex_aidesk_artifact")
      .where("vertex_id", "like", `%${input.artifactId}`)
      .selectAll()
      .limit(1)
      .executeTakeFirstOrThrow();

    await sdk.zeebe.publishMessage({
      name: "aidesk.export.requested",
      correlationKey: input.artifactId,
      variables: { ...artifact, rfqNotes: input.rfqNotes ?? "" },
    });

    return { status: "submitted" };
  });
});
```

---

## Lexicon JSONs (要作成ファイル)

```
00-contracts/lexicons/com/etzhayyim/apps/aidesk/
├── submitDesignJob.json
├── getDesignJob.json
├── listDesignJobs.json
├── exportToTsukuru.json
├── designJob.json       (record)
└── artifact.json        (record)
```

---

## Cross-Project Dependencies

| Project | Integration | 方向 |
|---|---|---|
| `etzhayyim-project-tsukuru` | K8s-internal BPMN `supplierExchange.normalizePackage` | aidesk → tsukuru (handoff) |
| `etzhayyim-project-murakumo` | Murakumo fleet (将来 GPU 化 Phase 2) | aidesk → murakumo |
| `etzhayyim-project-maps` | Factory 位置 `:LOCATED_IN` 関連 | 参照のみ |
| `etzhayyim-project-trust` | 設計者 DID trust score 検証 | aidesk → trust |
| `etzhayyim-project-yabai` | Sanctions screening (商用 export 前) | aidesk → yabai |

---

## Migrations (要作成)

```
30-graph/graph-schema/migrations/
├── 20260505130000_vertex_aidesk_design_job.ts
├── 20260505140000_vertex_aidesk_artifact.ts
└── 20260505150000_mv_aidesk_job_status.ts
```

---

## Phase Plan

| Phase | Scope | License gate |
|---|---|---|
| **Phase 1** (current) | Zero-To-CAD CPU 非同期, tsukuru handoff | Apache 2.0 only in commercial path |
| **Phase 2** | Make-A-Shape / WaLa research namespace; GPU pod | adsk-noncommercial in `aidesk.research.*` only |
| **Phase 3** | GPU pod (RTX 4000 Vultr) for Zero-To-CAD acceleration | — |
| **Phase 4** | KAMI 3D viewer integration (aidesk → maps WASM render) | — |

---

## Files to Create

```
60-apps/etzhayyim-project-aidesk/
├── CLAUDE.md
├── magatama.jsonld
├── magatama.toml
└── appview/
    └── aidesk-a1d3sk00/
        ├── package.json
        ├── wrangler.jsonc
        └── src/
            └── app.ts

00-contracts/
├── lexicons/com/etzhayyim/apps/aidesk/
│   ├── submitDesignJob.json
│   ├── getDesignJob.json
│   ├── listDesignJobs.json
│   ├── exportToTsukuru.json
│   ├── designJob.json
│   └── artifact.json
└── bpmn/com/etzhayyim/aidesk/
    ├── synthesizeCadFromImage.bpmn
    └── exportToTsukuru.bpmn

20-actors/magatama/py/src/pymagatama/primitives/
└── aidesk.py

30-graph/graph-schema/migrations/
├── 20260505130000_vertex_aidesk_design_job.ts
├── 20260505140000_vertex_aidesk_artifact.ts
└── 20260505150000_mv_aidesk_job_status.ts
```

---

## Conventions Added

- `aidesk-license-tier-immutable` — `vertex_aidesk_artifact.license_tier` は INSERT 時に model 由来で固定。UPDATE 禁止
- `aidesk-tsukuru-gate-structural` — tsukuru handoff は `license_tier not in COMMERCIAL_LICENSE_TIERS` で ValueError。soft check や flag ではなく構造的 gate
- `aidesk-research-namespace-isolated` — `com.etzhayyim.apps.aidesk.research.*` NSID / `vertex_aidesk_research_artifact` table は商用 BPMN から JOIN・import 不可

---

## References

- ADR-2604282300 (CF Worker Edge Layer / T1/T2/T3 Tier)
- ADR-0056 (BPMN-as-actor)
- ADR-0036 (Worker-direct Hyperdrive)
- ADR-0095 (3-Layer Identity — actor_did/org_did/at_did columns)
- ADR-0074 (ERC725 Root Identity)
- ADR-0044 (RisingWave UDF Language Strategy)
- `60-apps/etzhayyim-project-tsukuru/CLAUDE.md`
- https://huggingface.co/ADSKAILab/Zero-To-CAD-Qwen3-VL-2B (arXiv:2604.24479)
- https://huggingface.co/ADSKAILab (Make-A-Shape / WaLa — Non-Commercial)
