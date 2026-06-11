---
id: adr-2605203000-rw-free-write-target-options
title: "ADR-2605203000: Phase E — write-target options for RW-bound vendor actors migrating to etzhayyim"
status: active
doc_type: adr
topic: rw-free-write-target-options
authoritative: true
last_verified: 2026-05-20
priority: 7.5
axis: substrate
weight: 0.75
priority_note: "Architectural decision that unblocks 6+ vendor actors stuck in Phase E (RW direct write needs alternative substrate). Default = Option B (PDS XRPC) for actor migration. Option A (vendor RW mirror) is the carve-out per project for high-volume read-only data. Option C (IPFS + B2) for bulk-blob archival."
authoritative_for:
  - Write-target decision matrix for RW-bound vendor actors moving to etzhayyim
  - Default substrate per ADR-2605172000 (PDS XRPC + IPFS, not RW)
  - Per-project Option A/B/C decisions (ipaddress / public-malak / open-jpn-mynumber / maps / hanrei / ki / kiyo / sbom)
depends_on:
  - adr-2605172000-etzhayyim-rw-free-substrate
  - adr-2605172100-etzhayyim-payments-on-chain-only
  - adr-2605202400-gtfs-rt-vendor-mirror
related:
  - adr-2605202400-gtfs-rt-vendor-mirror
  - adr-2605202800-tsukuru-etzhayyim-business-model-change
  - adr-2605202900-tsukuru-phase2-escrow-intent-pattern
supersedes: []
superseded_by: []
---

# ADR-2605203000: Phase E — write-target options for RW-bound actors

**Status**: active
**Date**: 2026-05-20
**Deciders**: Jun Kawasaki

# Context

[ADR-2605172000](./2605172000-etzhayyim-rw-free-substrate.md) requires
etzhayyim/root apps to be **RW-free** — no Kotoba/Datomic / no Hyperdrive /
no centralized off-chain DB. Apps under `etzhayyim/root/60-apps/` MUST
write via PDS XRPC (`@etzhayyim/sdk e.write()`) + IPFS for blobs +
Base L2 anchor for tamper-evidence.

Several vendor actors are catalog-confirmed open scope (3-axes clean
per ADR-2605172400) BUT use `createKyselyDb()` for RW direct write.
Today's migration sweep (2026-05-20) deferred 6 of these to "Phase E
architecture pending":

| Actor | Phase E reason (deferred during today's wave 1+2) |
|---|---|
| `ipaddress` | 1,152-line src/app.ts, 37 commands, 10+ createKyselyDb call sites |
| `public-malak` | 920+ tracked corpus blobs + `vertex_ads_*` RW writes |
| `open-jpn-mynumber` | 923 blob files + `corpus.sqlite3` ingestion index |
| `hanrei` | 4 createKyselyDb call sites, 2,170-line app.ts (5 tracked) |
| `ki` | shared lg/lg_organism pod (also hosts hakkou/koke/kobo/saikin) |
| `kiyo` | 10 psycopg/sync_cursor refs |
| `sbom` | 9 psycopg refs |

Plus 2 already-decided per their own ADRs (record here for cross-reference):

| Actor | Decision | Decision ADR |
|---|---|---|
| `maps` | Option A (vendor RW mirror via etzhayyim-mirror.ts shim) | ADR-2605202300 + ADR-2605202400 (GTFS-RT carve-out) |
| `tsukuru` | Option B (business model change to PDS XRPC + USDC) | ADR-2605202800 + ADR-2605202900 |

Phase E needs a clear architectural answer so the next migration agent
doesn't re-litigate per actor.

# Decision

**Three options. Default Option B for actor migration. Options A and
C are carve-outs with explicit per-actor justification.**

## Option A — vendor RW mirror

Keep `createKyselyDb()` writes vendor-side. etzhayyim-side worker is
a read-only shadow against a vendor-mirrored AT firehose or direct
PDS shadow that vendor publishes. No vendor → etzhayyim data flow on
the write path; etzhayyim consumes vendor's published events.

```
vendor app  → createKyselyDb → vendor RW
                            └→ vendor firehose
                                  └→ etzhayyim mst-projector → MST views

etzhayyim app  ← read-only e.read() ← MST views
```

Reference impl: `60-apps/etzhayyim-project-maps/appview/maps-ui-uqpel6i6/src/etzhayyim-mirror.ts` (vendor shim, fire-and-forget shadow writes).

### When to choose Option A

- High-volume ingest pipelines (>10k records/day) where PDS write
  cost is prohibitive on first migration.
- Read-mostly workloads where vendor must keep RW for other vendor
  consumers anyway (no marginal savings from rewrite).
- Data with rapid mutation cadence (GTFS-RT 5-30s update intervals).

### Cost

- etzhayyim depends on vendor RW running forever for that actor.
  Failure mode: vendor RW outage = etzhayyim degraded for that
  actor. Acceptable for non-critical actors.
- Not "true" rw-free per ADR-2605172000 spirit. Justify in per-actor
  ADR (e.g., GTFS-RT ADR-2605202400).

## Option B — PDS XRPC rewrite (DEFAULT for actor migration)

Replace `createKyselyDb().insertInto()` with `e.write({ collection,
record })` via `@etzhayyim/sdk`. All record state lives in AT PDS.
Hot reads via `e.read()`. Aggregations + fan-in views via
`mst-projector` (Phase 3 — see ADR-2605171800).

```
etzhayyim app  → e.write() → PDS createRecord → AT firehose
                                              └→ mst-projector → views

etzhayyim app  ← e.read() ← MST traversal
              ← e.read() (projector view)
```

Reference impl:
- `60-apps/etzhayyim-project-open-isco/rw-free/` (seeder + query CLI)
- `60-apps/etzhayyim-project-tsukuru/rw-free/` (full app — production
  order + escrow + manufacturer registry, 13 commands)
- This PR: `60-apps/etzhayyim-project-ipaddress/rw-free/` (initial slice)

### When to choose Option B

- **Default for actor migration.** Match the tsukuru / open-isco
  pattern.
- Small-medium write volume (<10k records/day per actor).
- Strongly-typed domain models that benefit from Lexicon validation.
- Long-term etzhayyim independence (no vendor dependency).

### Cost

- Rewrite cost: per call site, replace createKyselyDb with e.write.
  tsukuru shows ~50 LoC per command translation.
- Hot reads currently slow without mst-projector (Phase 3 dependency).
  Acceptable for Phase 2 with `e.read()` cursor pagination.
- No streaming materialized views — Phase 3 mst-projector replaces
  this affordance.

## Option C — IPFS + content-addressed blob

For bulk-blob actors where data is mostly large immutable artifacts
(>100KB per record, append-only, citation-by-CID). Pin to IPFS via
SDK `ipfsApiUrl` + record holds the CID reference.

```
etzhayyim app  → e.write({ blobs: Map<field, Blob> })
                  → SDK pins to IPFS, embeds $type=blob ref
                  → PDS createRecord with CID ref

etzhayyim app  ← e.read({ fetchBlobs: true }) ← MST + IPFS gateway
```

Reference impl: NONE yet (SDK supports the pattern; no app fully ported).

### When to choose Option C

- Bulk crawled corpus (e.g., `open-jpn-mynumber` 280MB of public gov
  PDF/Excel docs). Per-record blob >> per-record metadata.
- Archival workloads (write-once-read-rarely).
- Content where the CID IS the identifier (de-dup across actors).

### Cost

- IPFS pin budget on `50-infra/ipfs-pinner` (Pinata + Filecoin + W3S
  + Kubo). Cost scales with corpus size + replication factor.
- Read latency: IPFS gateway (200-2000ms) vs PDS direct (50-200ms).
- Eventually-consistent pin propagation across providers.

# Per-actor decisions

Recorded so subsequent migration PRs don't re-litigate:

| Actor | Decision | Rationale |
|---|---|---|
| **ipaddress** | **Option B** | Catalog A-group, IP/ASN/WHOIS/GeoIP from public RIR sources. 37 commands but data is small structured records. PDS XRPC fits. This PR ships the initial reference. |
| **public-malak** | **Option A** (Phase A in earlier ADR) | TLP CLEAR ads scraper, high-volume per-platform ingest (Meta/Google/etc.), vendor already runs RW for `malak` parent. etzhayyim shadow read. |
| **open-jpn-mynumber** | **Option C** (corpus) + **Option B** (index) | 280MB of public gov PDF/Excel = IPFS blob. `corpus.sqlite3` index = etzhayyim PDS record per gov doc with CID ref. |
| **maps** | **Option A** (GTFS-RT carve-out) | Per ADR-2605202400 — 5-30s update cadence breaks mst-projector snapshot pipeline. Vendor RW + etzhayyim-mirror shim. |
| **hanrei** | **Option B** | Legal corpus, query-heavy, structured records. Rewrite cost acceptable; matches tsukuru pattern. |
| **ki / kiyo / sbom** | **Option B** | Small actors (≤3,000 LoC each). Wave 3 batch. |
| **tsukuru** | **Option B** (business model change) | Per ADR-2605202800 — Stripe Issuing → USDC + PDS XRPC. In progress (Phase 2, 13/46 commands done). |

# Consequences

## 正の効果

- **6 deferred actors unblocked**: Each has a decision; the next
  migration PR per actor can start without re-deciding.
- **Default policy clear**: Future scans hitting `createKyselyDb` get
  Option B by default. Carve-out (A or C) requires per-actor ADR.
- **Pattern reuse**: tsukuru rw-free is the template. Subsequent
  Option-B actors copy the structure.

## 負の効果 / コスト

- **mst-projector Phase 3 dependency**: Option B reads degrade
  without indexed views. Acceptable through Phase 2 (cursor pagination
  works), but Phase 3 is hard prerequisite for production query
  patterns at scale (e.g., ipaddress.searchByAsn across 50k ASNs).
- **Per-actor rewrite cost**: 1152 LoC ipaddress + 2170 LoC hanrei +
  ki/kiyo/sbom ≈ 5,000-6,000 LoC total rewrite. Multi-month effort
  parallel to tsukuru Phase 2-6.
- **IPFS pinner production-readiness**: Option C blocked on
  `50-infra/ipfs-pinner` (Pinata/Filecoin/W3S/Kubo) reaching
  production maturity. Currently scaffold v0.0.0.

## Migration plan

This ADR is the gate. Per-actor work:

- [x] ADR-2605203000 (this) — active
- [x] ipaddress reference impl (this PR sibling)
- [ ] vendor `git rm` ipaddress (this PR sibling, vendor side)
- [ ] hanrei: Option B port (wave 3)
- [ ] ki / kiyo / sbom: Option B port (wave 3 batch)
- [ ] public-malak: Option A shim (similar to maps etzhayyim-mirror)
- [ ] open-jpn-mynumber: Option C IPFS pin + Option B index (after
  ipfs-pinner production-ready)
- [ ] tsukuru: continue Phase 2 (ADR-2605202800 timeline)
- [ ] mst-projector Phase 3: production-ready views for Option B
  hot-read paths

# Alternatives Considered

## D — wait for ipfs-pinner production-readiness, then all Option C

Hold all 6 actors until IPFS pin infrastructure matures.

却下理由: blocks too long. IPFS pinner is months away; ipaddress et al.
benefit from PDS XRPC today.

## E — accept Option A for all 6 actors (vendor RW mirror)

Just keep RW writes vendor-side forever. Etzhayyim becomes a thin
shadow.

却下理由: violates ADR-2605172000 RW-free spirit. Etzhayyim becomes
permanently coupled to vendor. Failure mode: vendor RW outage breaks
all etzhayyim open actors. Unacceptable for long-term substrate
independence.

## F — wait for SDK v0.2 (real Safe escrow + streaming) before any Option B

Defer all Option B until SDK matures.

却下理由: SDK v0.1 `e.write()` works today. Phase 2 deferred features
(escrow / streaming) are payment-specific; Option B writes do not
need them.

# References

- ADR-2605172000 — RW-free substrate (mandate)
- ADR-2605172100 — payments on-chain only (separate but related)
- ADR-2605171800 — LangGraph Pregel → PostgresSaver → MST → IPFS → L2
- ADR-2605202300 — maps consumer migration (Option A reference)
- ADR-2605202400 — GTFS-RT vendor-mirror carve-out (Option A pattern)
- ADR-2605202800 — tsukuru business model change (Option B + USDC)
- ADR-2605202900 — tsukuru Phase 2 escrow_intent (Option B pattern)
- `@etzhayyim/sdk` v0.1 — `e.write() / e.read() / e.pay()` working;
  `e.escrowOpen()` v0.2+ stub
- `60-apps/etzhayyim-project-open-isco/rw-free/` — Option B reference
  (seeder + query CLI)
- `60-apps/etzhayyim-project-tsukuru/rw-free/` — Option B reference
  (full app, 13/46 commands)
- `60-apps/etzhayyim-project-ipaddress/rw-free/` — Option B reference
  (this PR, initial slice)
