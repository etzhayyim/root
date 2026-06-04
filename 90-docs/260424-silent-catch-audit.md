# Silent catch-fallthrough audit (atproto Worker)

Date: 2026-04-24
Scope: `50-infra/cloudflare/workers/atproto/src/` (read-only survey)
Context: MST path removal (2026-04-24) uncovered the pattern `try { … } catch { console.warn("(non-fatal)") }` hiding primary failures. This doc surveys the remaining instances.

## Landscape

**54 catch-only-warn occurrences** across 10 live files (excludes `.test.ts` / `_deprecated`):

| File | count | risk notes |
|---|---|---|
| `handlers/etzhayyim/index.ts` | 31 | Bootstrap / projector / agent-chat / XRPC-dispatch path. Bug 3 (mergeVertexNode) lives here |
| `handlers/pds/repo.ts` | 6 | Repo read-path fallbacks (CAR decode, etc) |
| `core.ts` | 5 | Includes hot path record INSERT catch at line 2659 |
| `handlers/register.ts` | 4 | **registerApp graph ops non-fatal — candidate Bug 4** |
| `handlers/appview/feed.ts` | 2 | Feed assembly fallbacks |
| `app.ts` | 2 | Top-level `[domain-expansion]` catch |
| `middleware/index.ts` | 1 | — |
| `handlers/oauth.ts` | 1 | — |
| `auth/verify.ts` | 1 | Layer-1 graph lookup fallthrough |
| `actor-executor-primitives.ts` | 1 | resolveAppNanoid |

Plus **3 `Promise.allSettled`** call sites (`mcp-adapter.ts`, `handlers/appview/feed.ts`, `handlers/etzhayyim/index.ts`) — these double-swallow individual task failures.

## Risk classification

### 🔴 High (hot path, failure = data loss)

| # | Loc | Pattern | Impact if fires |
|---|---|---|---|
| H1 | `core.ts:2659` | `catch (e) { console.warn("[repo-record] upsert failed (non-fatal)") }` around `vertex_repo_record` INSERT | The **sole record write path** post-MST removal. A Hyperdrive pool exhaustion / RW transient error = silently dropped record. commit row still written, so XRPC returns success to client. Firehose sees commit but record SELECT later returns empty. |
| H2 | `handlers/register.ts:440, 467, 476, 479` | 4× `registerApp graph ops failed (non-fatal)` | App-level bootstrap: `vertex_app` row creation, `DIDDocument` merge, `AgentKey` merge, agent session creation. Silent failures = the registered app works in XRPC but is invisible in graph queries. |
| H3 | `handlers/etzhayyim/index.ts: mergeVertexNode` (line 86, called from `bootstrapKnowledgeNodes` / `bootstrapGovernanceNodes`) | Bug 3 (already surfaced) | knowledge-graph + Profile bootstrap missing. |

### 🟡 Medium (optional feature, partial degradation)

| # | Loc | Pattern | Impact |
|---|---|---|---|
| M1 | `core.ts:3452, 3488` | `[murakumo] … cleanup/extraction failed (non-fatal)` | LLM-driven officer extraction downgrades to no-LLM path. Acceptable. |
| M2 | `core.ts:3509` | bare `catch { /* non-fatal */ }` | ??? needs context. |
| M3 | `handlers/pds/server.ts:270` | `[keystore] ensureSigningKey failed (non-fatal)` | New account can't sign. Would currently only matter if MST path existed — post-removal, keystore is only for did:web doc publish + Service Auth mint. |
| M4 | `handlers/etzhayyim/index.ts` (many) | bootstrap follow / tools / governance individual catches | Each sub-operation can fail independently; main bootstrap returns 200 regardless. Caller sees "registered" but subresources missing. |
| M5 | `repo/keystore.ts:163` | `syncDidDocToGraph failed (non-fatal)` | did:web `.well-known/did.json` not synced to `vertex_did_document`. Read path still works via D1 lookup. |

### 🟢 Low (genuine optional / fallback-by-design)

| # | Loc | Reason |
|---|---|---|
| L1 | `auth/verify.ts:292` | Layer 1 graph lookup designed to fall through to Layer 2 DNS resolution |
| L2 | `actor-executor-primitives.ts:279` | Site-gateway URL resolve fallback documented in comment |
| L3 | `app.ts:1207` | `[domain-expansion]` optional feature |
| L4 | allSettled in `mcp-adapter.ts` | MCP tool call per-tool isolation |

## Recommended actions

1. **H1 (core.ts:2659)** — remove the `try/catch` or replace with targeted catch for specific error classes (Hyperdrive pool exhaustion should retry, not swallow). Currently hot path silent failure mode. Audit cost: verify in RW that our canonical INSERT path doesn't error under any expected condition; if confirmed safe, remove the catch so genuine failures surface.
2. **H2 (registerApp)** — audit 4 catches. If app-registration is supposed to be atomic (app row + DID doc + key + session), convert to rethrow so caller gets 500 instead of fake 200. Or: mark `registerApp` as "best-effort bootstrap, verify via query" and document it.
3. **H3 (mergeVertexNode)** — same fix plan as advisor-flagged Bug 3: (a) generate `vertex_id` from label, (b) drop ON CONFLICT, (c) let PK upsert do the job. Follow-up task.
4. **M4 (etzhayyim/index.ts bootstrap)** — each sub-task catch: change to `Promise.allSettled` + aggregate errors into response metadata so caller can see partial-success.

## Not recommended

- Removing all silent catches en-masse. Several are genuinely optional-path by design (L-tier). Case-by-case is required.
- Changing allSettled to all. Parallel bootstrap intentionally tolerates sibling failures.

## Related

- `90-docs/260424-bsky-compat-risingwave-split.md` — MST context
- `90-docs/260420-pds-commit-seq-race-analysis.md` — seq race analysis (core.ts:2705+ block)
