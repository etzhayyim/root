---
id: 260409-unified-access-control-shannon-design
title: Unified Access Control — Shannon-Optimal RBAC/RACI/Consent/Clearance/Signal Design
status: active
doc_type: reference
topic: unified-access-control
authoritative: true
last_verified: 2026-04-09
authoritative_for:
  - read and write access control across PDS, kagami, Kotoba/Datomic, AT Protocol
  - RBAC/RACI/consent/clearance enforcement architecture
  - Signal encryption integration with access control
  - GraphAr schema security columns
related:
  - 260403-security-architecture-threat-key-consolidated
  - 260403-governance-and-compliance-consolidated
  - 260403-atproto-reference-coverage-compliance-consolidated
supersedes: []
superseded_by: []
---

# Unified Access Control — Shannon-Optimal Design

## Goal

Read と write の全経路を RBAC/RACI/consent/clearance + Signal E2E の統一モデルで制御する。現状の「write は repo owner check のみ、read は profile だけ disclosure tier」を解消し、Kotoba/Datomic/GraphAr/AT Protocol の全レイヤーで一貫した最小権限を実現する。

## Scope

- PDS XRPC handler (read + write)
- kagami Graph Worker (query execution)
- Kotoba/Datomic schema (columns, bloom, MV)
- G class (query builder security predicates)
- Signal Protocol field-level encryption
- AT Protocol OAuth scope integration

## Executive Summary

### 現状分析 (事実)

| 制御 | Write | Read |
|---|---|---|
| **auth.level** | checked | checked |
| **repo ownership** | checked (canWriteRepo) | not checked |
| **RBAC roles** | checked (admin/moderator/owner) | not checked |
| **clearance** | not checked | checked (profiles only) |
| **consent grants** | checked (grant existence, not maxSensitivity) | checked (profiles only, maxSensitivity) |
| **RACI** | not checked (populated but unused) | not checked |
| **row-level security** | none | post-filter in JS (profiles only) |
| **field-level filtering** | none | disclosure tiers (profiles only) |
| **Signal encryption** | metadata only (sensitivityOrd stored) | not enforced |
| **Kotoba/Datomic schema** | no security columns | no security columns |
| **G class** | no security predicates | no security predicates |

**Shannon 非効率**: Security metadata (sensitivityOrd, ownerHash) は `buildMergeProps()` で毎回計算し props に渡すが、Kotoba/Datomic テーブルに promoted column がなく、WHERE pushdown 不可。全 row を JS に引き上げてから filter → 帯域とメモリの浪費。

### 設計判断

5-layer unified enforcement:

```
L0: Schema (Kotoba/Datomic columns + bloom + MV)
L1: Query (G class security predicates → SQL WHERE pushdown)
L2: Post-Filter (kagami applySecurityFilter — L1 漏れの safety net)
L3: Handler (PDS disclosure tier + field redaction)
L4: Transport (Signal E2E field encrypt/decrypt)
```

Shannon 最適: L0+L1 で大半を SQL pushdown (Kotoba/Datomic で filter)。L2 は defense-in-depth。L3 は AT Protocol 互換の field projection。L4 は end-to-end confidentiality。

## Decision

### 1. Schema Evolution (L0)

#### 1.1 Vertex Base Columns 追加

`_VertexBase` mixin に 2 columns 追加:

```python
class _VertexBase:
    vertex_id = Column(String(512), primary_key=True)
    _alive = Column(Boolean)
    _seq = Column(BigInteger)
    timestamp_ms = Column(BigInteger)
    created_date = Column(Date)
    # Security columns (new)
    sensitivity_ord = Column(BigInteger)  # 0=public, 1=internal, 2=confidential, 3=restricted
    owner_did = Column(String(512))       # repo DID (denormalized for WHERE pushdown)
```

**Rationale**: `sensitivity_ord` + `owner_did` を promoted column にすることで Kotoba/Datomic bloom filter + WHERE pushdown が効く。現状は JS-derived (pds-helpers.ts:570) で SQL pushdown 不可。

#### 1.2 Edge Base Columns 追加

`_EdgeBase` mixin に同様:

```python
class _EdgeBase:
    # ... existing ...
    sensitivity_ord = Column(BigInteger)  # edge sensitivity (e.g. DM edge = 3)
    owner_did = Column(String(512))       # edge creator DID
```

#### 1.3 VertexConsent テーブル拡張

```python
class VertexConsent(_VertexBase, Base):
    # ... existing ...
    grantor_did = Column(String(512))       # who grants
    grantee_did = Column(String(512))       # who receives
    resource_pattern = Column(String(512))  # "repo:*:read", "repo:{did}:write", "collection:{nsid}:*"
    max_sensitivity = Column(BigInteger)    # 0-3
    delegatable = Column(Boolean)
    expires_at = Column(BigInteger)         # unix ms, NULL = permanent
    revoked = Column(Boolean)
```

#### 1.4 VertexCapability テーブル拡張 (RoleBinding label)

```python
# RoleBinding rows in vertex_capability:
# label = "RoleBinding"
# did = subject DID (who has the role)
# name = role name ("admin", "moderator", "owner", "reader", "writer")
# description = scope pattern ("*", "global", "did:web:xxx", "collection:com.etzhayyim.*")
# status = "active" | "revoked"
```

#### 1.5 新テーブル: VertexRaci

```python
class VertexRaci(_VertexBase, Base):
    __tablename__ = "vertex_raci"
    __graphar_labels__ = ("RaciAssignment",)
    __graphar_hash_key__ = "did"
    __graphar_buckets__ = 4
    __graphar_has_embedding__ = False
    __graphar_kind__ = "vertex"
    __table_args__ = _vertex_args("vertex_raci", "did", 4)

    rkey = Column(String(64))
    repo = Column(String(512))
    did = Column(String(512))           # subject DID
    activity = Column(String(512))      # NSID pattern (e.g. "com.etzhayyim.projector.*")
    raci_type = Column(String(1))       # "R" | "A" | "C" | "I"
    target_did = Column(String(512))    # target resource DID (optional)
    status = Column(String(64))         # "active" | "revoked"
```

#### 1.6 Bloom Filter 追加

```python
# vertex tables: bloom に sensitivity_ord, owner_did 追加
_vertex_args("vertex_actor", "did", 16,
    bloom="vertex_id,did,handle,repo,owner_did",
    colocate="social_graph")

# consent table: bloom
_vertex_args("vertex_consent", "did", 4,
    bloom="vertex_id,did,grantor_did,grantee_did")

# raci table: bloom
_vertex_args("vertex_raci", "did", 4,
    bloom="vertex_id,did,activity")
```

#### 1.7 Materialized Views

```sql
-- Consent grants aggregated by grantee (read-path acceleration)
CREATE MATERIALIZED VIEW mv_consent_by_grantee AS
SELECT grantee_did, grantor_did, max_sensitivity, resource_pattern, delegatable
FROM graphar.vertex_consent
WHERE _alive = true AND (revoked IS NULL OR revoked = false)
    AND (expires_at IS NULL OR expires_at > unix_timestamp() * 1000);

-- Active role bindings by subject DID
CREATE MATERIALIZED VIEW mv_roles_by_did AS
SELECT did, name AS role, description AS scope
FROM graphar.vertex_capability
WHERE _alive = true AND label = 'RoleBinding' AND status = 'active';

-- RACI assignments by subject DID
CREATE MATERIALIZED VIEW mv_raci_by_did AS
SELECT did, activity, raci_type, target_did
FROM graphar.vertex_raci
WHERE _alive = true AND status = 'active';
```

### 2. Query Security (L1) — G Class Extension

#### 2.1 SecurityScope Compilation

```typescript
// kagami/src/security.ts — extended
export interface SecurityScope {
  level: "public" | "authenticated" | "internal";
  did?: string;
  maxSensitivity: number;
  ownerDids: string[];           // was ownerHashes — use DID directly (promoted column)
  consentGrants: ConsentEntry[];
  rbacRoles: RBACRoleEntry[];    // new
  raciAssignments: RACIEntry[];  // new
}

export interface ConsentEntry {
  grantorDid: string;            // was grantorHash — use DID directly
  maxSensitivity: number;
  resourcePattern: string;
}

export interface RBACRoleEntry {
  role: string;
  scope: string;
}

export interface RACIEntry {
  activity: string;
  type: "R" | "A" | "C" | "I";
  targetDid?: string;
}
```

#### 2.2 compileSecurityScope (Graph → SecurityScope)

```typescript
export async function compileSecurityScope(
  callerDid: string,
  executeQuery: (sql: string) => Promise<Record<string, unknown>[]>,
): Promise<SecurityScope> {
  // 3 parallel queries to MVs
  const [consents, roles, racis] = await Promise.all([
    executeQuery(`SELECT grantor_did, max_sensitivity, resource_pattern, delegatable
      FROM graphar.mv_consent_by_grantee WHERE grantee_did = '${callerDid}'`),
    executeQuery(`SELECT role, scope
      FROM graphar.mv_roles_by_did WHERE did = '${callerDid}'`),
    executeQuery(`SELECT activity, raci_type, target_did
      FROM graphar.mv_raci_by_did WHERE did = '${callerDid}'`),
  ]);

  const maxClearance = roles.some(r => r.role === 'admin') ? 3
    : roles.some(r => r.role === 'moderator') ? 2
    : consents.reduce((max, c) => Math.max(max, Number(c.max_sensitivity) || 0), 0);

  return {
    level: "authenticated",
    did: callerDid,
    maxSensitivity: maxClearance,
    ownerDids: [callerDid],
    consentGrants: consents.map(c => ({
      grantorDid: String(c.grantor_did),
      maxSensitivity: Number(c.max_sensitivity) || 0,
      resourcePattern: String(c.resource_pattern),
    })),
    rbacRoles: roles.map(r => ({
      role: String(r.role),
      scope: String(r.scope),
    })),
    raciAssignments: racis.map(r => ({
      activity: String(r.activity),
      type: String(r.raci_type) as "R" | "A" | "C" | "I",
      targetDid: r.target_did ? String(r.target_did) : undefined,
    })),
  };
}
```

Cache: 5 min per DID (existing kagami SecurityScope cache).

#### 2.3 G Class — .withSecurity(scope)

```typescript
// kagami-query-builder/src/index.ts — new method
class G<TRow> {
  private securityScope?: SecurityScope;

  /**
   * Inject security predicates into the query.
   * Adds WHERE clauses for sensitivity_ord + owner_did pushdown.
   */
  withSecurity(scope: SecurityScope): this {
    if (scope.level === "internal") return this;  // bypass
    this.securityScope = scope;

    // L1: SQL pushdown — filter at Kotoba/Datomic level
    // Row visible if: sensitivity_ord <= maxSensitivity OR owner_did IN ownerDids OR consent grant
    const consentDids = scope.consentGrants
      .filter(c => c.maxSensitivity >= scope.maxSensitivity)
      .map(c => c.grantorDid);

    const allAllowedDids = [...scope.ownerDids, ...consentDids];

    if (allAllowedDids.length > 0) {
      // (sensitivity_ord <= $maxSens OR owner_did IN ($dids))
      this.whereRaw(
        `(${this.alias}.sensitivity_ord <= $pSens OR ${this.alias}.owner_did IN ($pOwners))`,
        { pSens: scope.maxSensitivity, pOwners: allAllowedDids },
      );
    } else {
      this.where("sensitivity_ord", scope.maxSensitivity, "<=");
    }

    return this;
  }
}
```

#### 2.4 G.exec(ctx) — Auto-Security

```typescript
// G.exec() automatically applies security if ctx has auth
async exec(ctx: ExecContext): Promise<TRow[]> {
  const query = this.build();
  const rows = await ctx.executeQuery(query);
  // L2: post-filter safety net (defense-in-depth)
  if (this.securityScope && this.securityScope.level !== "internal") {
    return applySecurityFilter(rows, this.securityScope) as TRow[];
  }
  return rows;
}
```

### 3. PDS Enforcement (L3)

#### 3.1 Unified canAccess() — Read + Write Gate

Replace separate `canWriteRepo()` with unified `canAccess()`:

```typescript
// pds-permissions.ts — unified access gate
export type AccessMode = "read" | "write";

export interface AccessDecision {
  allowed: boolean;
  tier: DisclosureTier;  // for reads: field filtering level
  reason: string;
}

export function canAccess(
  auth: PdsAuth,
  repo: string,
  mode: AccessMode,
  collection?: string,
  sensitivityOrd?: number,
): AccessDecision {
  const target = String(repo || "").trim();
  if (!target) return { allowed: false, tier: "t0", reason: "empty repo" };

  // 1. Internal = full access
  if (auth.level === "internal") return { allowed: true, tier: "t3", reason: "internal" };

  // 2. Owner = full access to own data
  if (isOwner(auth, target)) return { allowed: true, tier: "t3", reason: "owner" };

  // 3. RBAC check
  if (hasAdminLikeRole(auth, target)) {
    const callerDid = String(auth.userDid ?? auth.sub ?? "").trim();
    if (isBootstrapAdminDid(callerDid) && !isetzhayyimWebRepo(target)) {
      return { allowed: false, tier: "t0", reason: "bootstrap scope" };
    }
    return { allowed: true, tier: "t3", reason: "rbac" };
  }

  // 4. Consent grant check (with resource pattern + maxSensitivity)
  const grantResult = checkConsentGrant(auth, target, mode, collection, sensitivityOrd ?? 0);
  if (grantResult.allowed) return grantResult;

  // 5. RACI check (write: must be R or A; read: R, A, C, or I)
  const raciResult = checkRaci(auth, mode, collection);
  if (raciResult.allowed) return raciResult;

  // 6. For reads: public data (sensitivity_ord = 0) is readable by authenticated users
  if (mode === "read" && (sensitivityOrd ?? 0) === 0 && auth.level !== "public") {
    return { allowed: true, tier: "t1", reason: "public data" };
  }

  return { allowed: false, tier: "t0", reason: "denied" };
}

function checkConsentGrant(
  auth: PdsAuth, target: string, mode: AccessMode,
  collection?: string, sensitivityOrd: number = 0,
): AccessDecision {
  const grants = Array.isArray(auth.consentGrants) ? auth.consentGrants : [];
  for (const g of grants) {
    if (sensitivityOrdStr(g.maxSensitivity) < sensitivityOrd) continue;
    const ids = Array.isArray(g?.resourceIds) ? g.resourceIds : [];
    for (const idRaw of ids) {
      const id = String(idRaw || "").trim().toLowerCase();
      if (!id) continue;
      // Pattern matching: repo:*:read, repo:{did}:write, collection:{nsid}:*, *
      if (matchesResourcePattern(id, target, mode, collection)) {
        return { allowed: true, tier: "t3", reason: "consent" };
      }
    }
  }
  return { allowed: false, tier: "t0", reason: "no grant" };
}

function checkRaci(auth: PdsAuth, mode: AccessMode, collection?: string): AccessDecision {
  const assignments = Array.isArray(auth.raciAssignments) ? auth.raciAssignments : [];
  for (const a of assignments) {
    if (collection && !matchesActivity(a.activity, collection)) continue;
    if (mode === "write" && (a.type === "R" || a.type === "A")) {
      return { allowed: true, tier: "t3", reason: `raci:${a.type}` };
    }
    if (mode === "read") {
      return { allowed: true, tier: a.type === "I" ? "t1" : "t2", reason: `raci:${a.type}` };
    }
  }
  return { allowed: false, tier: "t0", reason: "no raci" };
}
```

#### 3.2 Write Gate: Sensitivity Enforcement

```typescript
// pds-handlers-repo.ts — createRecord/putRecord extended
// Before writing, check sensitivity:
const recordSensitivity = deriveRecordSensitivity(collection, record);
const decision = canAccess(auth, repo, "write", collection, recordSensitivity);
if (!decision.allowed) {
  return c.json({ error: "InsufficientClearance", message: decision.reason }, 403);
}
```

#### 3.3 Read Gate: Universal Disclosure

Apply disclosure to ALL read responses, not just profiles:

```typescript
// Universal field redaction based on AccessDecision.tier
function applyUniversalDisclosure(record: any, tier: DisclosureTier, collection: string): any {
  if (tier === "t0") return null;
  if (tier === "t3") return record;

  // Signal-encrypted fields: if tier < t3 and field starts with "signal:v1:", redact
  const result = { ...record };
  for (const [key, val] of Object.entries(result)) {
    if (typeof val === "string" && val.startsWith("signal:v1:")) {
      if (tier === "t1") { result[key] = "[encrypted]"; }
      // t2: show encrypted field exists but redact value
      if (tier === "t2") { result[key] = "[encrypted]"; }
    }
  }

  // Collection-specific field masks
  if (tier === "t1") {
    return pickPublicFields(result, collection);
  }
  return result;  // t2: full record minus encrypted fields
}
```

### 4. Signal Integration (L4)

#### 4.1 Encryption Decision Matrix

| sensitivity_ord | Field Type | AT Protocol Storage | Signal E2E |
|---|---|---|---|
| 0 (public) | any | plaintext repo record | no |
| 1 (internal) | PII | plaintext + clearance gate | no |
| 2 (confidential) | financial, health | `signal:v1:{ciphertext}` | yes (org key) |
| 3 (restricted) | DM, secrets | `signal:v1:{ciphertext}` | yes (pairwise key) |

#### 4.2 Write Path: Encrypt-Before-Store

```
Client → XRPC createRecord(record with plaintext fields)
  → PDS handler:
    1. canAccess(auth, repo, "write", collection, sensitivity) → allowed?
    2. If sensitivity >= 2: encrypt sensitive fields with Signal session key
       → record.field = "signal:v1:" + encrypt(plaintext, sessionKey)
    3. KAGAMI_RPC.cypher(MERGE) with sensitivity_ord + owner_did in promoted columns
  → Kotoba/Datomic: stored with sensitivity_ord, owner_did as SQL-pushdown columns
```

#### 4.3 Read Path: Filter-Then-Decrypt

```
Client → XRPC getRecord/listRecords/search
  → PDS handler:
    1. G<TRow>.withSecurity(scope).exec(ctx) → rows (L1: SQL WHERE pushdown)
    2. applySecurityFilter(rows, scope) → rows (L2: defense-in-depth)
    3. For each row: canAccess(auth, row.repo, "read", collection, row.sensitivity_ord) → decision
    4. applyUniversalDisclosure(row, decision.tier, collection) → redacted row (L3)
    5. If tier === "t3" and Signal-encrypted fields present:
       → Client decrypts locally with Signal session key (L4)
  → Response: filtered + redacted + encrypted-if-applicable
```

### 5. AT Protocol Compatibility

#### 5.1 OAuth Scope Mapping

```
AT Protocol scope     → AccessMode + collection constraint
atproto               → read + write (all collections)
transition:generic    → read + write (all collections)
transition:chat.bsky  → read + write (chat.bsky.convo.*)
app.bsky.feed.post    → write (app.bsky.feed.post only)
```

Scope is checked BEFORE canAccess() — scope limits the maximum, canAccess() is the authorization gate.

#### 5.2 Repo Record = Public (AT Protocol Invariant)

Per root CLAUDE.md: "Repo record = always public (federable)".

- `sensitivity_ord` in Kotoba/Datomic is an **appview-level** control, not a repo-level control
- The AT Protocol repo itself remains publicly federable
- Access control is enforced at the XRPC response layer (PDS handler), not at the repo storage layer
- Signal encryption (`signal:v1:`) ensures that even if the repo record is federated, the plaintext is not exposed

### 6. Implementation Priority

| Phase | Scope | Shannon Impact |
|---|---|---|
| **P1: Schema + G class** | Add sensitivity_ord, owner_did to base; bloom; G.withSecurity() | Enables SQL pushdown (eliminates JS post-filter waste) |
| **P2: Write gate** | canAccess() for writes, sensitivity enforcement | Closes write-without-clearance gap |
| **P3: Universal read** | canAccess() for all reads (not just profiles), universal disclosure | Closes read gap on posts/messages/signals |
| **P4: RACI enforcement** | checkRaci() in canAccess(), VertexRaci table | Activates unused raciAssignments |
| **P5: Signal integration** | Encrypt-before-store, filter-then-decrypt | End-to-end confidentiality for sensitivity >= 2 |
| **P6: MVs + cache** | Consent/role/raci MVs, SecurityScope cache | Read-path performance at scale |

### 7. Shannon Information Analysis

Current entropy waste:

| Source | Bits Wasted | Fix |
|---|---|---|
| All rows fetched then JS-filtered | O(N) rows transferred, O(M) used | L1 SQL WHERE pushdown (sensitivity_ord, owner_did) |
| sensitivityOrd computed per-request | Redundant computation | L0 promoted column (stored once) |
| ownerHash computed per-request (fnv1a32) | Collision-prone hash, 32-bit | L0 owner_did column (exact DID, no collision) |
| RACI populated but never read | Dead information in PdsAuth | L3 checkRaci() activates it |
| Signal key stored but not enforced | Metadata without enforcement | L4 encrypt-before-store + read-gate |
| Disclosure tier only on profiles | Inconsistent information exposure | L3 universal disclosure |

Post-fix information flow:

```
H(security_decision) = f(sensitivity_ord, owner_did, clearance, consent, rbac, raci, signal)
```

All 7 variables contribute to every access decision. No dead variables. No redundant computation. SQL pushdown eliminates O(N-M) wasted row transfers. Signal encryption makes the information-theoretic guarantee: H(plaintext | ciphertext, no key) = H(plaintext).

## Exceptions

- `auth.level === "internal"` (service binding) bypasses all security layers — this is by design for PDS→kagami internal calls
- Kotoba/Datomic does not support native RLS — L1 (SQL WHERE) + L2 (JS post-filter) is the substitute
- `sensitivity_ord` on existing rows defaults to 0 (public) — backward compatible

## References

- `50-infra/cloudflare/workers/atproto/src/pds-permissions.ts` — current canWriteRepo
- `50-infra/cloudflare/workers/atproto/src/pds-helpers.ts:505-555` — current resolveDisclosureTier
- `_archive/30-graph/kagami-live-260414/src/security.ts` — archived SecurityScope (no callers)
- `30-graph/kagami-query-builder/src/index.ts` — G class (no security predicates)
- `30-graph/graph-schema-py/graphar_schema/models.py` — schema SSoT (no security columns on base)
- `90-docs/security/260403-security-architecture-threat-key-consolidated.md` — threat model
- `90-docs/platform/260403-governance-and-compliance-consolidated.md` — governance baseline
