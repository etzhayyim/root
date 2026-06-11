---
id: adr-2605091400-mcp-as-cell-membrane-lexicon-xrpc-demotion
title: "MCP-as-Cell-Membrane — Lexicon = Dual-Wire Contract (MCP + XRPC)"
status: active
doc_type: adr
topic: mcp-membrane-lexicon-demotion
authoritative: true
last_verified: 2026-05-15
implementation_notes: |
  - media-gamers first impl (2026-05-13): capability_worker=a7m8oocs, 4 tools in vertex_capability, NSID alias in app.ts, profile.tools[] in kotodama.jsonld
  - malak.surveillance dual-wire impl (2026-05-15): 4 chains in `00-contracts/lexicons/com/etzhayyim/apps/malak/` simultaneously power (a) MCP tools at mcp.etzhayyim.com/mcp and (b) internal XRPC at dispatcher.etzhayyim.com/xrpc/com.etzhayyim.apps.malak.*. Same lexicon JSON, two wires. SvelteKit `/mcp` route + `bpmn-dispatcher` both derive routing/validation from the lexicon.
authoritative_for:
  - MCP as sole external API surface (external = cell membrane)
  - Lexicon = dual-wire contract SSoT (drives MCP tool schema AND internal XRPC contract)
  - kotodama MCP facade as SSoT for outward capability
  - MCP tool names use Lexicon NSID (verbatim, no translation)
  - Internal XRPC remains active for cytoplasmic (cohort-internal) wire
priority: 9.4
axis: protocol
weight: 0.94
priority_note: "CRITICAL — external surface = MCP only; lexicon JSON drives both MCP and internal XRPC wires."
depends_on:
  - adr-2605091300-bonsai-cultivar-layer-above-myco-yeast
  - adr-0087-kotodama-mcp-tool-facade
  - adr-2604231828-appview-domain-separation-bsky-etzhayyim-ai
  - adr-2605131600-malak-orchestration-langgraph-pregel-langserve
related:
  - adr-2604282300
  - adr-2605091600-plasmid-graft-horizontal-tool-acquisition
  - adr-2605111200-cf-worker-edge-only-no-rw-connection
supersedes: []
superseded_by: []
---

# Context

これまでの規約 (root CLAUDE.md `XRPC = sole API`) では、
agent も human も同じ XRPC wire で edge worker を叩いていた。
artificial organism ecosystem の文脈では、external 境界は
**膜 (membrane)** であり、生体内部の wire とは性質が異なる。
膜は **選択的透過性** + **能動輸送** が要件で、これは MCP の
tool capability negotiation と一致する。

XRPC + lexicon は、cohort 内 (cytoplasm) の細胞間通信としては
依然有効だが、**外部 organism (human / org / external service) との接続点**
としては抽象度が低すぎる (record-shape を露出してしまう)。

# Decision

> **Amendment 2026-05-13 — MCP router API contract.**
> For edge BFFs and appviews, MCP is the runtime transport to pod-side
> business logic, but tool names MUST remain Lexicon NSIDs. MCP `tools/list`
> exposes `inputSchema` generated from Lexicon parameters. Tool results MUST
> conform to the Lexicon output schema. Direct external XRPC remains demoted;
> XRPC/NSID compatibility is preserved by naming, schema, and optional internal
> `/xrpc/{nsid}` facades.

> **Amendment 2026-05-15 — Lexicon = dual-wire contract.**
> Lexicon JSON in `00-contracts/lexicons/` is **first-class contract SSoT**
> and explicitly serves **two wires simultaneously**:
>
> 1. **External wire = MCP** (`mcp.etzhayyim.com/mcp`). Lexicon → `tools/list`
>    inputSchema / `tools/call` result validation. External callers
>    (Claude desktop, partner AI ecosystem, human operator) consume this.
> 2. **Internal wire = XRPC** (`dispatcher.etzhayyim.com/xrpc/<nsid>` →
>    bpmn-dispatcher → K8s pod-side LangServer). Same lexicon, same NSID,
>    used for cytoplasmic cohort-internal traffic. `x-internal-trust`
>    strict-mode gated.
>
> "demotion" of XRPC means it is no longer a **public** API surface, NOT
> that lexicon is subordinate. **Lexicon is the SSoT for both wires.**
> Adding a new lexicon JSON gives you both MCP tool AND internal XRPC for
> free — no separate registration needed beyond the cohort wiring (CF Worker
> route, dispatcher routing branch, langserver chain).
>
> Reference implementation: malak.surveillance 4 chains (2026-05-15).
> Same `bitnestExitPursuit.json` lexicon drives `malak.bitnestExitPursuit`
> at `mcp.etzhayyim.com/mcp` and `com.etzhayyim.apps.malak.bitnestExitPursuit` at
> `dispatcher.etzhayyim.com/xrpc/...`.

## A. 三層境界

```
外界 (human, other org, external AI ecosystem)
   ↕  MCP (tool call, server↔server)            ← ★ 唯一の公開境界 (細胞膜)
─────────────────────────────────────────────────
細胞質 (kobo cell ⇄ kabi mycelium ⇄ kinoko)
   ↕  XRPC + atproto wire + lexicon JSON         ← 内膜 (内部のみ)
─────────────────────────────────────────────────
化学反応 (RW row, BPMN, LangGraph node)
   ↕  Kysely + Hyperdrive (ADR-0036)
```

## B. MCP = 公開 SSoT

- `kotodama MCP facade` (ADR-0087) を **唯一の外向き API surface** とする
- 全 external integration (human client, partner org, external AI agent) は
  MCP server-to-server で接続
- agent code は MCP client SDK のみ知る。XRPC は kotodama facade 内部と
  PDS 内部だけが触れる

## C. Lexicon の役割再定義 (2026-05-15 改訂: dual-wire SSoT)

lexicon JSON は `00-contracts/lexicons/` に置く **first-class contract SSoT**。
2 つの wire を同一定義から駆動する:

| 用途 | wire | endpoint | 駆動部分 |
|---|---|---|---|
| 外部 API (membrane) | MCP JSON-RPC | `mcp.etzhayyim.com/mcp` | `tools/list[].inputSchema` ← lexicon `parameters` / `input.schema`、`tools/call.result` validation ← lexicon `output.schema` |
| 内部 RPC (cytoplasm) | XRPC | `dispatcher.etzhayyim.com/xrpc/<nsid>` → bpmn-dispatcher → K8s langserver pod | NSID = lexicon path、handler input/output validation = lexicon schema |

ルール:

- **1 lexicon = 2 wires**。Adding `00-contracts/lexicons/<path>.json` MUST
  surface the capability at both wires (external = MCP, internal = XRPC).
- `params.name` MUST be the Lexicon NSID, **without translation** for both
  wires. External MCP clients call `name: "com.etzhayyim.apps.malak.bitnestExitPursuit"`
  (or short alias `malak.bitnestExitPursuit` if registered) — same NSID.
- 外部 surface でも内部 wire でも、validation source は同じ lexicon JSON。
  drift は禁止。
- `Permission-Set 追加時に Lexicon JSON 必須` 規約 (root CLAUDE.md) は維持。
  `PDS bundle 再生成` 手順も維持。

「demotion」は **外部公開からの降格** であって SSoT 性ではない。lexicon は
internal record shape の宣言とは別格の **wire-format-independent contract SSoT**。

### 旧 (2026-05-13 まで) と新 (2026-05-15 から) の対比

| | 旧 (2026-05-13 v1) | 新 (2026-05-15 dual-wire) |
|---|---|---|
| Lexicon 立ち位置 | "MCP tool が wrap する内部 record shape" | first-class dual-wire contract SSoT |
| 外部公開可能性 | MCP のみ (lexicon は wire 詳細) | MCP (membrane) + XRPC 内部のみ (cytoplasm)。lexicon が両 wire の SSoT |
| 直接呼出 | 内部のみ | 内部 XRPC = OK / 外部 XRPC = 禁止 |
| 新規追加コスト | lexicon → MCP tool registry 登録 + wire 詳細別途 | lexicon 1 個追加 = 2 wire 同時に capability surface (cohort wiring を整えれば) |

## D. 外向き capability negotiation

partner org / external service との初回接続:

```
1. Discovery — partner が MCP server endpoint を broadcast (DNS / well-known)
2. Handshake — DID-bound OAuth + DPoP で双方認証
3. Capability list — MCP tools/list で利用可能 tool 列挙
4. Selective grant — owner (cohort 鉢主) が個別 tool に scope+TTL grant
5. Plasmid acquisition — 受領した tool を vertex_kobo_plasmid に登録 (ADR-2605091600)
```

## E. 内部 XRPC は維持 (cytoplasmic wire として first-class)

- bsky federation (`app.bsky.*`) は引き続き XRPC + AT Protocol 経由
- etzhayyim 内部 service (`com.etzhayyim.apps.*`) も内部 RPC 用 XRPC は維持
- 内部 caller (CF Worker edge BFF → dispatcher、cohort 内 pod 間、operator CLI) は
  XRPC を直接使ってよい。strict `x-internal-trust` 認証 (`DISPATCHER_AUTH_MODE=strict`) で gate
- **外部 caller** (Claude desktop, partner AI ecosystem, public API consumer) は MCP のみ。
  外部 XRPC 公開は禁止
- **agent 実装** (external AI agent = MCP client) は MCP only。内部 agent
  (cohort 内 pod, langserver chain) は XRPC OK

ルール: 「`x-internal-trust` を持つ」=「cohort 内 cytoplasmic caller」と定義。
external boundary は cell membrane (MCP) で必ず handshake する。

## F. MCP router wire format and Lexicon binding

MCP router 呼び出しは JSON-RPC 2.0 の `tools/call` を標準形とする。

```json
{
  "jsonrpc": "2.0",
  "id": "req-001",
  "method": "tools/call",
  "params": {
    "name": "com.etzhayyim.apps.shinshi.getCategorySummary",
    "arguments": {
      "limit": 5000
    }
  }
}
```

**Tool name rule**:

- `params.name` MUST be the Lexicon NSID, unchanged.
- Example: `com.etzhayyim.apps.shinshi.listActresses`.
- Server-side aliases using `_` or path fragments are non-canonical and may only
  exist as client compatibility shims.

**Schema rule**:

- Lexicon remains the contract source for params, output, and errors.
- MCP `tools/list[].inputSchema` MUST be generated from Lexicon `parameters`.
- MCP `tools/call.result` MUST carry JSON that conforms to Lexicon `output`.
- If MCP client libraries only validate `inputSchema`, output validation remains
  server-side and CI responsibility.

Example `tools/list` entry:

```json
{
  "name": "com.etzhayyim.apps.shinshi.listActresses",
  "description": "List Shinshi character DID identities.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "limit": {
        "type": "integer",
        "minimum": 1,
        "maximum": 5000,
        "default": 1000
      }
    }
  }
}
```

## G. SvelteKit edge BFF contract

Cloudflare / SvelteKit appviews are thin edge BFFs:

```
Browser
  -> same-origin SvelteKit route (/api/* or /xrpc/* facade)
  -> MCP router tools/call
  -> K8s pod tool / LangGraph / Granian
  -> Kotoba/Datomic / business logic
```

Rules:

- SvelteKit edge MUST NOT connect to Kotoba/Datomic, Hyperdrive, or other DB
  bindings.
- Page-specific `/api/*` routes may exist, but only as unwrap/aggregation
  facades over MCP tools.
- New domain operations SHOULD expose a Lexicon NSID first, then generate the
  MCP tool metadata from it.
- For appview reads, prefer pod-side aggregate tools over shipping raw records
  to the browser and re-aggregating in Svelte.

For Shinshi category pages, the canonical next read is:

```text
com.etzhayyim.apps.shinshi.getCategorySummary
```

returning pre-aggregated totals, series, genres, and letter counts from the pod.
`com.etzhayyim.apps.shinshi.listActresses` remains a lower-level list tool.

## H. Wire efficiency decision

MCP JSON-RPC over JSON is accepted for edge-to-pod appview reads. Protobuf/gRPC
is not the default for this boundary.

Observed Shinshi `listActresses(limit=5000)` payload on 2026-05-13:

| Format | Size |
|---|---:|
| JSON response | 150,973 bytes |
| gzip JSON response | 17,860 bytes |
| DID string characters only | 78,418 bytes |
| protobuf-like estimate, current fields | ~137 KB raw |

The raw binary saving is mostly erased by gzip/Brotli for this payload class.
For count/summary endpoints, MCP/JSON overhead is sub-millisecond and dominated
by network RTT plus pod/database latency. Therefore:

- Use MCP JSON-RPC for browser/edge/appview business APIs.
- Use Lexicon schema to keep the contract typed and generated.
- Consider protobuf only for high-volume binary payloads, streaming, or
  pod-to-pod paths where compression and JSON parse costs are proven material.

## I. root CLAUDE.md 改訂 (2026-05-15 v2)

`### XRPC / Lexicon` セクションの `XRPC = sole API` を以下に置換:

> **MCP = sole external API; XRPC = internal cytoplasmic wire;
> Lexicon JSON = dual-wire contract SSoT.**
>
> - External-facing tools MUST be exposed via kotodama MCP facade (`mcp.etzhayyim.com/mcp`).
> - Direct XRPC exposure to external principals is prohibited.
> - Internal XRPC remains active for cytoplasmic (cohort-internal) wire.
>   `x-internal-trust`-gated callers (CF Worker edge BFF, K8s pods, operator CLI)
>   use `dispatcher.etzhayyim.com/xrpc/<nsid>` freely.
> - **Lexicon JSON drives both wires from one source**: MCP `tools/list`/`tools/call`
>   schemas AND internal XRPC NSID + validation. Adding 1 lexicon = 2-wire surface.

# Consequences

## Positive
- 外部統合 (other AI ecosystem, partner org) が標準 MCP で完結
- 内部 record shape 露出が止まる → forward compatibility 向上
- agent 実装が MCP-only でモデル横断 (Claude/GPT 等) 可搬

## Negative
- 既存 external XRPC consumer (もしあれば) を MCP wrapper 経由に migrate 必要
- MCP facade が単一接点 → SLA / cache 設計が厚くなる
- lexicon の "意味" が 2 つ並走 (旧 = 公開 / 新 = 内部) — 移行期の学習コスト

## Reversibility
半-不可逆。lexicon を再公開する path は技術的には残るが、
agent 実装が MCP に揃った後の roll-back は agent 改修コストが高い。

# Alternatives Considered

- **XRPC 維持 + MCP 並設**: rejected。両 surface 維持で contract drift
- **GraphQL 採用**: rejected。schema 単一化は魅力的だが LLM agent 親和性で MCP に劣る
- **gRPC 採用**: rejected。binary wire は edge constraint で LLM 連携性が低い

# J. capability_worker Naming Convention (2026-05-13)

`vertex_capability.capability_worker` は MCP adapter が
`https://{capability_worker}.etzhayyim.com/xrpc/com.etzhayyim.apps.{capability_worker}.{method}`
の形式でルーティングするため、**DNS-safe な値 (ハイフン・英数字のみ) が必須**。
アンダースコアは RFC 1123 hostname として無効。

**Rule**: `capability_worker` には nanoid (例: `a7m8oocs`) または
ハイフン区切りのスラッグ (例: `abuse`) を使用する。
アンダースコアを含む app 名 (例: `media_gamers`) は禁止。

**NSID alias pattern** (app.ts 側の対処):
app 内 NSID prefix が `com.etzhayyim.apps.media_gamers.*` のように
アンダースコアを含む場合、Worker の fetch handler に alias を追加する:

```ts
const NSID_PREFIX_ALIAS = "com.etzhayyim.apps.a7m8oocs.";  // nanoid prefix
if (nsid.startsWith(NSID_PREFIX_ALIAS)) {
  nsid = NSID_PREFIX + nsid.slice(NSID_PREFIX_ALIAS.length);
}
```

こうすることで MCP adapter が `a7m8oocs` でディスパッチした呼び出しが
Worker 内部の `media_gamers` ルーティングロジックに届く。

**First implementation**: `media-gamers` (nanoid `a7m8oocs`, 2026-05-13)
- `vertex_capability` に 4 tool 登録: `health`, `ingestCharts`, `generateGuide`, `autopilot`
- `capability_worker = 'a7m8oocs'` (DNS-safe)
- `kotodama.jsonld` `profile.tools[]` に 4 エントリ追加
- `app.ts` に `NSID_PREFIX_ALIAS` alias handler 追加

# Known Issue: atproto.etzhayyim.com MCP router 522 (2026-05-13)

`POST https://mcp.etzhayyim.com/xrpc/com.etzhayyim.mcp.message` が HTTP 522 を返す。
原因: デプロイ済みの atproto Worker (SvelteKit BFF) の
`AGENTGATEWAY_MCP_ROUTER_URL` が `https://mcp.etzhayyim.com/xrpc/com.etzhayyim.mcp.message`
に設定されており、同一 CF zone 内の自己ループになっている。
`atproto-canary.etzhayyim.com` (実装側) は `x-internal-trust` ヘッダーなしで
アクセス不可。この問題は media-gamers とは無関係の既存 infra rot。

修正方法: `50-infra/cloudflare/workers/atproto/` で `etzhayyim deploy` を実行し
現在のソース (SvelteKit plain proxy → canary) をデプロイする。
追跡: `deps.toml [[migrations]] id = "atproto-mcp-router-522-loopback-fix"`

# K. Reference Implementation: malak.surveillance dual-wire (2026-05-15)

4 chains in `00-contracts/lexicons/com/etzhayyim/apps/malak/` simultaneously expose
both wires from one lexicon JSON each:

| Lexicon path | MCP tool (external) | XRPC NSID (internal) |
|---|---|---|
| `bitnestExitPursuit.json` | `malak.bitnestExitPursuit` at `mcp.etzhayyim.com/mcp` | `com.etzhayyim.apps.malak.bitnestExitPursuit` at `dispatcher.etzhayyim.com/xrpc/...` |
| `exportSurveillanceEvidence.json` | `malak.exportSurveillanceEvidence` | `com.etzhayyim.apps.malak.exportSurveillanceEvidence` |
| `agencyOutreachFullFlow.json` | `malak.agencyOutreachFullFlow` | `com.etzhayyim.apps.malak.agencyOutreachFullFlow` |
| `draftAgencyBriefing.json` | `malak.draftAgencyBriefing` | `com.etzhayyim.apps.malak.draftAgencyBriefing` |

**Wire diagram**:

```
                    cell membrane (external)
                              │
   external caller ──MCP JSON-RPC──▶ mcp.etzhayyim.com/mcp
   (Claude desktop,                   (SvelteKit /mcp route)
    partner AI, ...)                      │
                                          │ DISPATCHER_INTERNAL_SECRET
                                          │ binding → x-internal-trust
                                          ▼
   ═══════════════════════════════════════════════════════════════
                         (membrane crossing)
   ═══════════════════════════════════════════════════════════════
                                          │
                                          ▼
                              dispatcher.etzhayyim.com/xrpc/<nsid>
                              (bpmn-dispatcher, K8s pod)
   ┌──────────────────────────────────────┤
   │                                      │
   │  cytoplasm (internal)                │  same NSID, same lexicon,
   │                                      │  same validation
   │                                      ▼
   │                              malak-langserver pod
   │                              (Granian + LangGraph Pregel)
   │
   ▲
   │
   internal caller (CF Worker, cohort pod, CLI)
   ──XRPC + x-internal-trust──▶ dispatcher.etzhayyim.com/xrpc/<nsid>
```

**Files** (1 lexicon → 2 wires):

- Lexicon (SSoT): `00-contracts/lexicons/com/etzhayyim/apps/malak/bitnestExitPursuit.json`
- MCP wire: `50-infra/cloudflare/workers/atproto/svelte/src/routes/mcp/+server.ts`
  (`MALAK_TOOLS` 静的 list + `tools/call` → dispatcher proxy)
- XRPC wire: `40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/dispatcher_main.py`
  (`MALAK_LANGSERVER_PROXY_NSIDS` + `_proxy_to_lg_pod` to
  `malak-langserver.mitama-udf.svc.cluster.local:8765`)
- Pod handler (both wires terminate here):
  `40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/malak/langgraph/server.py`
  (`/xrpc/{nsid}` alias + `/invoke/{chain_name}` LangServe)

# References

- ADR-0087 kotodama MCP tool facade
- ADR-2604282300 CF Worker edge layer
- ADR-2605111200 CF Worker = edge-only (no RW connection)
- ADR-2605131600 malak orchestration LangGraph Pregel LangServe
- root CLAUDE.md `### XRPC / Lexicon` (本 ADR で改訂、2026-05-15 dual-wire amendment)
- 派生: ADR-2605091600 plasmid acquisition
