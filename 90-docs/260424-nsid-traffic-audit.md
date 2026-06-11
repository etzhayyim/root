# XRPC NSID traffic audit (atproto Worker)

Date: 2026-04-24
Scope: atproto Worker (`etzhayyim-pds-2603241700`) — which NSIDs routed via handler are actually exercised in prod.
Context: post-MST removal (2026-04-24), we wanted to identify additional dead handlers to delete along the same "delete rather than fix" pattern.

## Method

1. Extract NSIDs routed by `src/handlers/**` via `method === "..."` / `case "..."` patterns → **342 routed NSIDs**.
2. Sample prod traffic via `wrangler tail` for ~3 minutes (pretty + json formats).
3. Cross-reference.

## Findings

### 1. Observed traffic (3-min window, 336 JSON events)

| NSID / event | Count | Outcome | Notes |
|---|---|---|---|
| `comAtprotoIdentityCreate` (rpcMethod) | 13 | **all `exception`** (100% failure) | Crashing on every call. Called via Worker RPC (service binding), not HTTP XRPC. Handler lives at `etzhayyim/index.ts:2476`. |
| `app.bsky.feed.getAuthorFeed` | 7 | Ok | Only 2 unique actor DIDs: `sh1n5h1x.etzhayyim.com:{boa-hancock-one-piece, rias-gremory-high-school-dxd}` — looks cron-driven (5-min cadence). |
| `/health` | 1 | Canceled | Internal healthcheck. |
| (none) | 0 | — | Zero HTTP `com.atproto.*` / `com.etzhayyim.*` write traffic |

**Result: 2 distinct NSIDs out of 342 exercised in 3 minutes.** 340 were not observed.

### 1.1 Follow-up: 60-minute sample (2026-04-24, post-wrangler-login)

Rerun with a 60-minute `wrangler tail` window, 1,232 events captured:

| Metric | 3min sample | 60min sample | Δ |
|---|---|---|---|
| Events | 33 | 1,232 | 37× |
| Distinct NSIDs | 2 | 14 | 7× |
| ok / exception / canceled | 7 / 13 / 1 | 1072 / 148 / 12 | — |

Top NSIDs by volume (60min):

```
  526  com.atproto.repo.listRecords
  369  com.atproto.repo.createRecord
  148  com.atproto.identity.create      ← 100% exception (fix 537cb4d9c59 not yet deployed)
  129  app.bsky.feed.getAuthorFeed
   11  com.atproto.repo.uploadBlob
    5  com.atproto.identity.list
    5  com.atproto.server.getServiceAuth
    4  com.etzhayyim.yoro.respondToMention
    4  com.atproto.sync.getBlob
    2  app.bsky.feed.post
    1  com.etzhayyim.apps.llm.generateImage
    1  com.etzhayyim.yoro.platformPulse
    1  com.atproto.repo.putRecord
    1  com.atproto.repo.getRecord
```

Of the 14 observed NSIDs, **4 are not in the v2 routed set of 375** (extractor gap):
`com.etzhayyim.yoro.{platformPulse, respondToMention}`, `app.bsky.feed.post`,
`com.atproto.repo.putRecord`. These are dispatched via patterns the extractor
does not yet resolve (table-based `Set.has(nsid)` dispatch, pipethrough to
AppView binding, or runtime string concat). Real routed handler count is > 375.

### 1.2 Extractor v3 — Set-based dispatch resolution (2026-04-24)

Added `new Set([...])` parsing to `70-tools/scripts/260424-nsid-extractor.py`:

- Declarations: `const XRPC_X_METHODS = new Set<string>([...]);`
- Members: string literals, NSID_* refs, `...OTHER_SET` spreads
- Usage: `SET.has(nsid)` / `.has(method)` in dispatch files → Set members become routed

v3 stats:
- 170 constant defs (96 literal/join/template + 74 Sets)
- 71 Sets fully resolved
- 55 Sets referenced from dispatch files
- **Final routed NSID count: 448** (up from 375 in v2, +73)

Resolved: `com.atproto.repo.putRecord` is in `XRPC_UPDATE_METHODS`. `com.atproto.sync.*`, `app.bsky.graph.*`, `app.bsky.feed.like/repost/threadgate`, and many more Set-dispatched NSIDs now counted correctly.

**Still not in routed set** (not extractor bugs):
- `com.etzhayyim.yoro.{platformPulse, respondToMention}` — dispatched via `pipethroughAppView()` (`dispatch.ts:334`) that forwards unknown `com.etzhayyim.yoro.*` NSIDs to `APPVIEW_SERVICE` binding. Not routed locally; routed at yoro Worker.
- `app.bsky.feed.post` — record `$type` collection, not an XRPC method. Prod URL hits are either invalid client requests or path-pattern extraction false positives.

**Sample size note**: the 60-min window got us from 342→375→448 routed (extractor improvements) and 2→14 observed. Dead-handler deletion still needs multi-day data.

60-min traffic-zero count: **365 routed NSIDs** observed zero calls. The sample
is still too short to declare any of these dead — sparse endpoints like
cohort fission, governance policy edits, admin actions, or manually-triggered
repo sync are expected at hours-to-days cadence. Conclusion is unchanged from
the 3-min audit: deletion decisions need 7-day Logpush archive or zone
Analytics permission on the CF token.

### 2. Scope limitations (don't over-conclude)

- **3 min is too short** to prove a handler is dead. User-triggered actions (identity.create, register, etc.) happen on hours/days cadence, not seconds.
- Our CF API token lacks zone-level Analytics permission (`com.cloudflare.api.account.zone.analytics.read`), so we can't query the 7-day `httpRequestsAdaptiveGroups` for URL path stats. Workers Invocations Analytics is accessible but lacks URL path dimension — only script/status/datetime.
- Some handlers (cohort ops, governance ops, admin ops) are **inherently sparse traffic** — one call per ADR-0026 fission event or per governance policy change. Absence over 3 min ≠ dead.

## Real finding worth fixing: identity.create 100% crash rate

`comAtprotoIdentityCreate` is failing every call in the 3-min window. Tail JSON shows `outcome: exception` but `exceptions: []` / `logs: []` — the exception body is being swallowed before reaching the tail stream. Likely caught by Hono error middleware and translated into an HTTP 500 response before reaching CF's exception channel.

Handler code is at `handlers/etzhayyim/index.ts:2476`. Needs standalone investigation — probably an auth / validation / downstream binding call failing. Since the handler returns `{did, rkey}` synchronously and `bootstrapSubDidActor` is fire-and-forget in `.catch()`, the synchronous failure is in the `writeRecordFireAndForget` / `comAtprotoRepoCreateRecord` path or earlier.

This is NOT an NSID-is-dead finding — it's a **"NSID is exercised AND broken"** finding. Route: follow up as a separate bug, not part of this audit's scope.

## Recommendations

### DO NOT do (based on this audit alone)

- Delete any of the 340 unobserved handlers. 3-min sample is evidence of low-volume prod, not evidence of death.

### DO (in priority order)

1. **Fix `com.atproto.identity.create`** as a separate task — 13 crashes/min on a core AT Protocol endpoint is prod-relevant regardless of audit.
2. **Enable CF Logpush to R2** for the PDS Worker with a 24-48h window, filter by XRPC path, then repeat this audit with meaningful statistics. Setup cost: one-time config, ~$0/mo at current traffic.
3. **Request zone Analytics API permission** on the CF API token so future audits can query `httpRequestsAdaptiveGroups` directly (GraphQL, free, instant).
4. Only after (2) or (3): build a sorted NSID × 7d-count table and consider deletion of truly 0-count handlers, weighted by the handler's implementation cost vs maintenance burden.

## Alternative signal: dead handler via code shape

Without traffic data, code-level signals for likely-dead handlers:
- Handler returns a hardcoded error / stub response (e.g. we just did this to `com.etzhayyim.admin.repoBackfillMst`: 410 Gone).
- Handler writes to a vertex_* table with 0 rows in prod (we know 555/934 are 0-row).
- Handler references a removed constant / deprecated ENV var.
- Handler has no corresponding lexicon file anymore.

These are all false-positive-prone. Manual review recommended.

## Out of scope

- Handlers in other Workers (yoro, auth, vault, etc) — audit each separately.
- WebSocket endpoints (`subscribeRepos`) — require connection-count stats, not call-count.
- Internal Worker-to-Worker RPC (service binding calls) — these are visible via `rpcMethod` field (e.g. `comAtprotoIdentityCreate`) but our sample didn't hit most.

## Appendix: explicit diff (3-min window, 2026-04-24)

Observed NSIDs (both HTTP path extraction + camelCase RPC decode):

```
app.bsky.feed.getAuthorFeed
com.atproto.identity.create
```

Extractor gap noted: literal `case "..."` pattern matched 342 handlers,
but `case NSID_ID_CREATE:` (constant ref) was missed — so the real
routed count is higher. `com.atproto.identity.create` in particular
falls in this gap. Resolving NSID_* constants → strings would raise
the denominator. See `handlers/etzhayyim/index.ts:590` for the constant,
routed at line 2476.

**Resolved 2026-04-24** via `70-tools/scripts/260424-nsid-extractor.py`:

- Resolves all `const NSID_X = "..." | [NS, "..."].join(".") | \`${NS}.x\``
  definitions (96 constants, all fully chained).
- Unions with direct `case "..."` / `method === "..."` usages.
- Filters to valid NSID shape (≥ 3 dotted segments).

Result: **375 routed NSIDs** (up from 342 literal-only). Same 2 observed
in the 3-min window → **373 handlers with 0 traffic** in the sample.
The 33-NSID delta (375 − 342) are all constant-referenced handlers
that the v1 extractor missed, including `com.atproto.identity.create`.

0-traffic handlers by namespace prefix (from the 342 literal-case set):

| Prefix | 0-traffic count |
|---|---|
| app.bsky.graph | 25 |
| com.atproto.server | 24 |
| com.etzhayyim.projector | 23 |
| com.etzhayyim.apps | 23 |
| app.bsky.feed | 22 |
| chat.bsky.convo | 17 |
| app.bsky.unspecced | 17 |
| com.atproto.admin | 16 |
| com.etzhayyim.rtc | 15 |
| com.atproto.sync | 14 |
| com.etzhayyim.governance | 13 |
| com.etzhayyim.signal | 12 |
| com.atproto.identity | 10 |
| app.bsky.notification | 10 |
| com.atproto.repo | 9 |
| app.bsky.contact | 8 |
| com.etzhayyim.pds | 8 |
| com.atproto.temp | 7 |
| com.etzhayyim.cohort | 7 |
| tools.ozone.moderation | 6 |
| app.bsky.actor | 6 |
| tools.ozone.{set,team,safelink,communication,verification,setting,server} | 19 |
| chat.bsky.{moderation,actor} | 5 |
| app.bsky.{draft,bookmark,video,ageassurance,labeler} | 14 |
| com.etzhayyim.{stream,convo,identity,murakumo,kagami,agent,admin} | 11 |

Full list: `/tmp/traffic-zero.txt` (ephemeral, not committed — regenerate
via `grep + comm -23` against a fresh tail).

## Related

- `90-docs/260424-bsky-compat-kotoba-split.md` — MST context (`com.atproto.sync.*` already known dead externally)
- `90-docs/260424-silent-catch-audit.md` — silent catch patterns that mask failed invocations
