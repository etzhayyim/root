# Phase 3.5: atproto PDS Worker Kysely Refactoring Design

## Executive Summary

The atproto PDS Worker (primary XRPC handler) contains **~268 rawCypher/rawSql calls** distributed across:
- `pds-handlers-etzhayyim.ts`: 114 calls (complex domain logic, MERGE, profiling)
- `pds-handlers-feed.ts`: 70 calls (counts, timelines, social graphs)
- `pds-handlers-infra.ts`: 29 calls (infrastructure operations)
- `pds-handlers-repo.ts`: 24 calls (record listing, collection enumeration)
- `pds-helpers.ts`: 8 calls (validation, pre-flight checks)
- Other files: 23 calls

**Effort estimate**: 4-6 weeks (experienced Kysely+RisingWave developer)
**Risk level**: High (core PDS path, regression risk on all social graph operations)

## Cypher Pattern Categories

### 1. **Dynamic MERGE with Label Substitution** (20-30 patterns)

**Example from pds-handlers-etzhayyim.ts:553**
```cypher
MERGE (k:${nodeLabel} {label: $label})
  SET k.description = $desc, k.updated_at = $now
MERGE (a:Profile {did: $did})
MERGE (a)-[:${rel}]->(k)
```

**SQL Equivalent (RisingWave):**
- Use column-based table routing (profile → `vertex_profile`, skill → `vertex_skill`, etc.)
- Parameter-driven table name substitution (build table reference from `nodeLabel`)
- RisingWave doesn't support dynamic table names → use **IF/CASE switch or generated SQL**

**Conversion approach:**
1. Extract label → table mapping (already in graph-schema helpers)
2. Generate SQL per label using `resolveVertexTable(label)`
3. Use INSERT ... ON CONFLICT for UPSERT behavior

---

### 2. **Multi-Fallback Count Queries** (40-50 patterns)

**Example from pds-handlers-feed.ts:140-150**
```typescript
async function resolveProfileCounts(...) {
  // Try MV first, then sync MV, then base table
  const statements = [
    "SELECT count(*) AS cnt FROM mv_post_count_by_repo WHERE repo = $repo",
    "SELECT count(*) AS cnt FROM mv_post WHERE repo = $repo",
    "SELECT count(*) AS cnt FROM vertex_post WHERE repo = $repo",
  ];
  for (const stmt of statements) {
    try { return await rawCypher(stmt).exec(ctx); }
    catch { continue; }
  }
}
```

**RisingWave equivalent:**
- RisingWave MVs maintain streaming updates (< 100ms latency)
- Leverage `graphar.mv_*` for counts
- Fallback chain: async MV → sync MV (staging table) → base vertex table
- No Cypher needed; use direct SQL `SELECT count(*)` from appropriate tier

**Conversion approach:**
1. Map existing Cypher count patterns to RisingWave MV names
2. Keep fallback chain logic, replace Cypher with SQL
3. Use **Kysely query builder** for dynamic SQL generation (not string-based)

---

### 3. **Edge Traversal with CSR/CSC Tables** (60-80 patterns)

**Cypher pattern:**
```cypher
MATCH (a:Actor)-[:Follows]->(b:Actor) WHERE a.did = $did RETURN b LIMIT 10
```

**RisingWave equivalent:**
```sql
SELECT b.* FROM graphar.vertex_actor a
  JOIN graphar.edge_follows e ON a.vertex_id = e.src_vid
  JOIN graphar.vertex_actor b ON e.dst_vid = b.vertex_id
WHERE a.did = $did
LIMIT 10
```

**Challenges:**
- Incoming edges need CSC dual table (`edge_follows_by_dest`)
- Graph-schema provides dual table mappings
- Pagination requires careful OFFSET/LIMIT with ORDER BY

**Conversion approach:**
1. Extract edge direction (→ vs ←)
2. Use `resolveReverseEdgeTable()` for incoming edges
3. Build Kysely JOIN query with proper column selection
4. Handle pagination with cursor-based approach (prefer over OFFSET)

---

### 4. **Complex Multi-Hop Graph Traversals** (20-30 patterns)

**Example:**
```cypher
MATCH (a:Actor {did: $did})-[:Follows]->(b:Actor)-[:Likes]->(p:Post)
WHERE ...
RETURN p LIMIT 100
```

**RisingWave approach:**
- Split into stages or use CTEs (WITH clause)
- Prefer streaming from high-selectivity tables (actor → edge → post)
- Consider creating **RisingWave VIEW definitions** for reusable traversal patterns

**Conversion approach:**
1. Identify most common multi-hop patterns (likely 5-10 distinct traversals)
2. **Create RisingWave VIEWs** for each pattern
3. Reference views from Kysely queries (simpler, more efficient)
4. Use **query plans** to validate that pushdown is working

---

### 5. **Dynamic Label/Table Routes** (30-40 patterns)

**Example from pds-handlers-repo.ts:383**
```cypher
MATCH (r:${label}) WHERE r.repo = $repoDid RETURN ...
```

**RisingWave:**
- Each label has dedicated table (`vertex_post`, `vertex_profile`, etc.)
- No dynamic table substitution in standard SQL
- Must generate SQL or use procedure wrapper

**Conversion approach:**
1. Build **label → SQL template map** (282 lines in graph-schema helpers)
2. Use template substitution to generate concrete SQL
3. Store in **Kysely query builder** (not raw strings)
4. Example:
   ```typescript
   const table = resolveVertexTable(label); // "graphar.vertex_post"
   const query = db.selectFrom(table)
     .where("repo", "=", repoDid)
     .select("rkey", "repo", "collection");
   ```

---

## Technical Blockers & RisingWave Constraints

### 1. **No Dynamic Table Names in SQL**
RisingWave (PostgreSQL-compatible) does **not** support parameterized table names:
```sql
-- ❌ INVALID
PREPARE stmt AS SELECT * FROM $1 WHERE id = $2;

-- ✅ VALID
SELECT * FROM vertex_post WHERE id = $id;
```

**Solution:** Code generation + template tables (non-parameterized)

### 2. **Pagination: OFFSET vs Cursor-Based**

Current Cypher uses `SKIP/LIMIT` (offset-based):
```cypher
MATCH (n:Post) WHERE ... RETURN n SKIP $offset LIMIT $limit
```

RisingWave performance degrades with large OFFSET (full table scan to skip rows).

**Conversion strategy:**
- **Short-term (Phase 3): Keep OFFSET/LIMIT**, validate performance
- **Long-term (Phase 4): Migrate to cursor-based pagination** (keyset pagination using `_seq` HLC)
  - Better for large datasets
  - Consistent ordering (use `ORDER BY _seq`)

---

### 3. **CSC Reverse Tables Missing for Some Edges**

GraphAr spec requires both CSR (primary) and CSC (reverse) tables:
```
edge_follows          ← PRIMARY (src→dst)
edge_follows_by_dest  ← REVERSE (dst→src)
```

**Validation needed:**
- Audit all edge types in `models.py`
- Verify CSC dual tables exist in RisingWave
- Create missing dual tables if needed

---

### 4. **Sensitive Data Filtering (Post-Query)**

Current Cypher includes security filter at query time:
```cypher
MATCH (n:Post) WHERE ... RETURN n
-- applySecurityFilter(rows, scope) applied in-memory
```

**RisingWave approach:**
1. **Option A (Preferred):** Row-Level Security (RLS)
   - Define RLS policy in RisingWave
   - Automatic enforcement at query layer
   - Use `SET row_security = on`

2. **Option B (Fallback):** Post-query filtering
   - Fetch all rows, apply `sensitivityOrd` filter in app
   - Less efficient, but compatible with existing code

---

## Implementation Roadmap

### Phase 3.5: Design (1-2 weeks)

**Deliverables:**
1. **RisingWave VIEW definitions** for 10 most common multi-hop patterns
   - Pattern: `(Actor)-[:Follows]->(Actor)` traversal
   - Pattern: Actor profile + counts + engagement metrics
   - Pattern: Post thread + ancestors
   - etc.

2. **Kysely Migration Templates**
   - Template for COUNT queries (MV fallback chain)
   - Template for edge traversals (CSR/CSC routing)
   - Template for label-routed tables (generated SQL)
   - Template for pagination (OFFSET/LIMIT with validation)

3. **Refactoring Priority Matrix**
   - Rank 268 queries by:
     - Call frequency (hot path vs cold)
     - Complexity (simple SELECT vs complex JOIN)
     - Impact (core PDS vs optional feature)
   - Identify quick wins (10-20 simple queries, 1 week)
   - Identify critical path (50-60 core queries, 2-3 weeks)
   - Identify long-tail (remaining 150-170 queries, 1-2 weeks)

4. **Smoke Test Plan**
   - Unit tests for each template (5 scenarios each)
   - Integration tests for hot paths (feed, profile, social)
   - Performance benchmarks (P95 latency vs Cypher baseline)
   - Regression suite (10 key workflows)

### Phase 4: Implementation (3-4 weeks)

**Week 1: Quick Wins**
- Migrate 10-20 simple COUNT queries
- Migrate static table SELECT queries
- Smoke test basic functionality

**Week 2: Core PDS Paths**
- Migrate feed timeline queries
- Migrate profile queries
- Migrate social graph queries (follows, likes, reposts)
- Integrate with Kysely query builder

**Week 3: Complex Traversals**
- Multi-hop graph queries
- Aggregate queries with GROUP BY
- Edge case handling (missing tables, null values)

**Week 4: Polish & Performance**
- Query plan validation
- Performance tuning (index usage, pushdown)
- Edge case fixes
- Pre-deployment testing

---

## Quick Start: Template-Based Conversion

### Template 1: Count Query with MV Fallback

**Before (Cypher):**
```typescript
const rows = await rawCypher(
  "MATCH (p:Post) WHERE p.repo = $repo RETURN count(*) AS cnt",
  { repo }
).exec(ctx);
```

**After (Kysely + RisingWave):**
```typescript
// Try MV first
const result = await db.selectFrom("mv_post_count_by_repo")
  .where("repo", "=", repo)
  .select("count", db.raw("coalesce(count, 0) as cnt"))
  .executeTakeFirst()
  .catch(() => null);

if (result?.cnt) return result.cnt;

// Fallback to base table
return (await db.selectFrom("vertex_post")
  .where("repo", "=", repo)
  .select(db.raw("count(*) as cnt"))
  .executeTakeFirstOrThrow()).cnt;
```

### Template 2: Edge Traversal (Outgoing)

**Before (Cypher):**
```typescript
const rows = await rawCypher(
  "MATCH (a:Actor {did: $did})-[:Follows]->(b:Actor) RETURN b.did AS did LIMIT 10",
  { did }
).exec(ctx);
```

**After (Kysely):**
```typescript
const rows = await db
  .selectFrom("vertex_actor as a")
  .innerJoin("edge_follows as e", "a.vertex_id", "e.src_vid")
  .innerJoin("vertex_actor as b", "e.dst_vid", "b.vertex_id")
  .where("a.did", "=", did)
  .select("b.did")
  .limit(10)
  .execute();
```

### Template 3: Edge Traversal (Incoming via CSC)

**Before (Cypher):**
```typescript
const rows = await rawCypher(
  "MATCH (a:Actor {did: $did})<-[:Follows]-(b:Actor) RETURN b.did AS did LIMIT 10",
  { did }
).exec(ctx);
```

**After (Kysely, using CSC dual table):**
```typescript
const rows = await db
  .selectFrom("vertex_actor as a")
  .innerJoin("edge_follows_by_dest as e", "a.vertex_id", "e.dst_vid") // CSC
  .innerJoin("vertex_actor as b", "e.src_vid", "b.vertex_id")
  .where("a.did", "=", did)
  .select("b.did")
  .limit(10)
  .execute();
```

### Template 4: Dynamic Label Route

**Before (Cypher with label substitution):**
```typescript
const label = collectionToLabel(collection); // "Post" or "Profile"
const rows = await rawCypher(
  `MATCH (r:${label}) WHERE r.repo = $repo RETURN r.rkey, r.repo`,
  { repo }
).exec(ctx);
```

**After (Kysely with label resolution):**
```typescript
const table = resolveVertexTable(label); // "graphar.vertex_post"
const rows = await db
  .selectFrom(table)
  .where("repo", "=", repo)
  .select("rkey", "repo")
  .execute();
```

---

## Risk Assessment & Mitigation

| Risk | Impact | Probability | Mitigation |
|---|---|---|---|
| **Regression on feed timeline** | Critical | Medium | Run comprehensive smoke test on hot paths before merge |
| **CSC table unavailability** | High | Low | Audit RisingWave catalog early; create missing tables in migration |
| **Performance degradation** | High | Medium | Baseline all 268 queries before/after; validate query plans |
| **Data loss on complex traversals** | Critical | Low | Unit test each template with realistic data; compare Cypher vs SQL results |
| **Migration takes >4 weeks** | Medium | Medium | Prioritize hot paths; defer cold paths to Phase 5 if needed |

---

## Success Criteria

1. ✅ All 268 rawCypher calls converted to Kysely SQL
2. ✅ No regression in PDS XRPC response times (P95 latency ≤ 100ms increase)
3. ✅ Full smoke test pass (10 key workflows)
4. ✅ RisingWave query plans validated (proper pushdown, index usage)
5. ✅ Backwards compatibility maintained (no breaking changes to PDS API)

---

## Next Steps (Post Design, Week 1 of Phase 4)

1. Generate RisingWave VIEWs (1-2 days)
2. Create 5 Kysely query builder templates (2-3 days)
3. Migrate first 10 quick-win queries (3-4 days)
4. Smoke test and baseline performance (2-3 days)
5. Proceed to Week 2 core paths

---

**Prepared**: 2026-04-12
**Reviewed**: (Pending)
**Status**: Design Phase — Ready for implementation planning
