---
id: write-only-derived-architecture
title: Write-Only Derived Architecture — AT Protocol Faithful Shannon η=100%
status: active
doc_type: adr
topic: write-only-derived-architecture
authoritative: true
last_verified: 2026-04-07
authoritative_for:
  - write-only derived architecture
  - derive rules
  - AT Protocol faithful write pattern
  - Shannon optimal app design
related:
  - news-wrpc-stream-reactive-design
supersedes: []
superseded_by: []
---

# Write-Only Derived Architecture

## Decision

**App handler は write のみ。social post / tool invoke / notification は PDS commit pipeline の derive rule で宣言的に導出する。**

## Rationale

AT Protocol の commit stream → Feed Generator / Notification / Labeler パターンは元々 Write-Only Derived Architecture。etzhayyim の explicit `postFeed()` / `invoke()` は AT Protocol に対して冗長 (η≈33%)。

## Rules

### P1: Handler = Write Only

```typescript
// ✅ correct: write only
async function cmdConfigure(sdk, payload) {
  const config = { ...parsed, createdAt: nowISO() };
  write(sdk, "configuration", config);  // single write
  return config;                         // response
}

// ❌ prohibited: explicit social post in handler
async function cmdConfigure(sdk, payload) {
  write(sdk, "configuration", config);
  postFeed(sdk, "New config!");  // redundant — derive rule handles this
  return config;
}

// ❌ prohibited: explicit invoke in handler
async function cmdLaunch(sdk, payload) {
  write(sdk, "crowdfundingRequest", req);
  invoke(did, method, params);  // redundant — derive rule handles this
  return req;
}
```

### P2: Derive Rules (kotodama.jsonld)

```jsonc
{
  "derive": {
    "social": [
      {
        "on": "com.etzhayyim.apps.{app}.{collection}",
        "when": { "field": "value" },
        "template": "text with {{field}} interpolation"
      }
    ],
    "invoke": [
      {
        "on": "com.etzhayyim.apps.{app}.{collection}",
        "when": { "status": "value" },
        "target": "did:web:{target}.etzhayyim.com",
        "method": "com.etzhayyim.apps.{target}.{method}",
        "map": { "targetField": "{{sourceField}}" }
      }
    ]
  }
}
```

PDS commit pipeline reads derive rules from kotodama.jsonld and auto-executes on commit.

### P3: Public vs Private (AT Protocol Faithful)

| Data | Storage | AT Protocol Alignment |
|---|---|---|
| Catalog, reward, campaign status | `createRecord` (Repo, public) | ✓ Repo = public |
| Pledge, payment, PII, user config | `putPreferences` (server-side) | ✓ Private = server-side |
| E2E message | `createRecord` + field encrypt | ✓ W Protocol extension |

### P4: Single Entry Point

XRPC = sole API. MCP = XRPC thin adapter (same handler). tool invoke = XRPC NSID routing.

## Implementation

PDS commit pipeline (`50-infra/cloudflare/workers/atproto/src/`) processes derive rules:

```
commit event (createRecord)
  → match derive.social rules → auto AppBskyFeedPost
  → match derive.invoke rules → auto tool dispatch
  → match derive.notify rules → auto convo notification
```
