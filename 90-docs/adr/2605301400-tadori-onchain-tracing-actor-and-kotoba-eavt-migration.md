---
id: adr-2605301400-tadori-onchain-tracing-actor-and-kotoba-eavt-migration
title: "ADR-2605301400: 辿 (tadori) — authorized on-chain transaction-tracing + actor-attribution Tier-B actor, kotoba-EAVT-native; migrates malak pursuit + ipaddress + yabai off yata SQL / Kotoba/Datomic"
status: proposed
doc_type: adr
topic: tadori-onchain-tracing-actor
authoritative: true
last_verified: 2026-05-30
priority: 8.0
axis: actor-architecture
weight: 0.80
priority_note: "Names a new Tier-B actor (tadori) as the kotoba-native consolidation point for authorized crypto-asset transaction tracing and actor attribution, and specifies the migration of the three existing fragmented stores (malak pursuit Pregel output, ipaddress SQL graph, yabai SQL graph) onto kotoba-kqe EAVT. Subordinate to the substrate-engine charter ADR-2605262130 (no Kotoba/Datomic / no projection layer) and to the Transparent Religious Force invariant ADR-2605192100 §1.12 (authorized-investigation-only, open-source, 1 SBT = 1 vote)."
authoritative_for:
  - new Tier-B actor `tadori` (authorized on-chain tx tracing + actor attribution)
  - kotoba-kqe EAVT datom schema for tx / address / cluster / label / case / ip-observation / dns-observation / attribution / risk
  - migration of malak `wallet_deep_inspect_pursuit` + `address_label_pursuit` Pregel output off filesystem/Kotoba/Datomic onto kotoba QuadStore
  - migration of ipaddress.etzhayyim.com SQL graph off yata Workers RPC onto kotoba-kqe
  - migration of yabai.etzhayyim.com SQL graph (CTI / DNS / IP-history / access-audit) off yata Workers RPC onto kotoba-kqe
depends_on:
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
  - adr-2605231525-no-server-key-religious-corp-architecture
  - adr-2605181100-mst-encrypted-records-signal-keywrap
  - adr-2605152000-wallet-deep-inspect-and-address-label-pregels
related:
  - adr-2605131600-malak-orchestration-langgraph-pregel-langserve
  - adr-2605172000-malak-onion-frontier-ransomware-tracking
  - adr-2604251935-blockchain-vke-head-ingest
  - adr-2605291500-tsukuroi-authorized-remediation-tier-b-actor-r0
supersedes: []
superseded_by: []
notes: |
  Session 2026-05-30: user asked whether a crypto-asset-actor-tracking actor
  was designed and running on kotoba, and whether tx history / IP / DNS data
  was stored in kotoba datomic. Audit found that the capability exists but is
  (1) fragmented across three components and (2) NOT on kotoba: malak pursuit
  Pregels write filesystem + Kotoba/Datomic (ADR-2604251935 vertex_blockchain_*),
  ipaddress + yabai write "SQL graph (yata Workers RPC)". Both stores are
  prohibited by the substrate-engine charter (ADR-2605262130 strengthened the
  no-Kotoba/Datomic invariant to also cover read backends; yata SQL is a non-kotoba
  primary store). This ADR proposes the consolidation actor + the migration.
---

# Context

A 2026-05-30 audit (user question: "暗号資産取引 actor の追跡を行う actor は設計されて
kotoba で動いている? 取引履歴 / ipaddress / dns 履歴は kotoba datomic に保存されている?")
established the current state honestly:

1. **The tracing capability exists but is fragmented across three components**, none
   of which is a single coherent "crypto-asset actor tracking" actor:
   - **malak pursuit Pregel family** (ADR-2605152000 `wallet_deep_inspect_pursuit` +
     `address_label_pursuit`; ADR-2605172000 onion/ransomware tracking) — fetches
     paginated BSC tx history, classifies wallets (cex_cold / dex_router / bridge_pool
     / mixer / whale_eoa), labels counterparties from K sources (local DB / BscScan /
     ABI / OFAC SDN / Tornado list / Chainalysis OSI / LLM). **Case-anchored**
     (`case:takahashi-hiroyuki-20260512`) — i.e. authorized fraud-investigation, not
     mass surveillance.
   - **ipaddress.etzhayyim.com** — 1次ソース IP / ASN / WHOIS / GeoIP / reverse-DNS
     collection (RIR feeds, on-demand IP entities).
   - **yabai.etzhayyim.com** — AML / sanctions / CTI risk scoring + the actual
     temporal history: `DnsRecord` (passive DNS first_seen/last_seen),
     `IpLocationHistory` / `IpHostingHistory`, `IntelAccessLog` / `IntelSession` /
     `IntelDevice` (access audit with accessor_ip + device fingerprint).

2. **None of it runs on kotoba.** Storage today:
   - malak Pregel output → filesystem (`persist_fs`) + Kotoba/Datomic tables
     `vertex_blockchain_block` / `vertex_blockchain_tx` (ADR-2604251935).
   - ipaddress + yabai → "SQL graph (yata Workers RPC)".

3. **Both stores are now prohibited.** ADR-2605262130 (kotoba substrate-engine charter)
   made `kotoba-kqe` arrangements the **only** authorized hot-path read engine over
   content-addressed blocks, removed the projection layer entirely (D7), and
   strengthened the no-Kotoba/Datomic invariant to cover **read backends** as well as
   primary write stores (D-row 4, D-row 12). yata Workers-RPC SQL graph is a non-kotoba
   primary store and falls under the same RW-free invariant (ADR-2605172000). So the
   honest answer to the user was: **the data is NOT in kotoba datomic; it is in
   Kotoba/Datomic + yata SQL, which the current charter prohibits.**

4. **Constitutional posture of a tracing actor.** A crypto-tracing / forensic actor
   touches third-party data (addresses, IPs, attribution). Under the Transparent
   Religious Force invariant (ADR-2605192100 §1.12 + ADR-2605192315) any investigatory
   force etzhayyim operates must be (a) **open-source**, (b) **fully on-chain
   monitorable**, and (c) authorized under **1 SBT = 1 vote**. The existing malak design
   already encodes this implicitly via the **case-anchor** model (every observation is
   tied to an authorized case, default Phase 0 dry-run, Phase 1 live-write gated). This
   ADR makes that posture explicit and constitutional for the consolidated actor, in the
   same "authorized + propose/evidence-only" spirit as 繕い tsukuroi (ADR-2605291500).

# Decision

Create a new Tier-B actor **辿 (tadori)** — *"to trace / follow a thread back along its
path"* — as the **kotoba-EAVT-native consolidation point** for authorized crypto-asset
transaction tracing and actor attribution, and migrate the three fragmented stores onto
`kotoba-kqe`. tadori is a sibling of malak (which remains the LangGraph/Pregel *compute*
engine); tadori owns the *durable case graph + attribution surface* in kotoba.

## D1. Actor identity, charter posture, and prohibitions

- **Name**: 辿 tadori. Domain `tadori.etzhayyim.com`. DID `did:web:tadori.etzhayyim.com`.
- **Purpose**: authorized, case-anchored on-chain transaction tracing + actor
  attribution (address → cluster → off-chain identity / IP / DNS), with every datom
  written to kotoba and readable over `kotoba-kqe`.
- **Constitutional gates (NOT amendable below Council Lv7+ for §1.12 items)**:
  - **Authorized-investigation-only.** Every write MUST be anchored to a `case`
    entity carrying an authorization reference (fraud-victim recovery, AML/CTI duty,
    sanctioned-entity tracing, or Council-authorized Transparent Force action). No
    case-anchor → no live write (Phase 0 dry-run only). Mirrors malak ADR-2605152000
    `link_back: requires live_write=True AND case-anchor non-empty`.
  - **Open-source.** tadori code + heuristics + label sources are public (Apache 2.0 +
    Charter Rider v2.0). No proprietary chain-analysis algorithm is embedded; external
    paid sources (Chainalysis/Elliptic) are **feature-flagged data inputs only**, never
    a dependency of the open path (ADR-2605152000 Alt-3).
  - **On-chain monitorable.** Every case action emits an on-chain-anchored audit datom
    (Transparent Force log, ADR-2605192315). No covert tracing.
  - **PII confidentiality.** Any datom that attributes an on-chain entity to a natural
    person, an IP, or a device fingerprint is written under the
    `com.etzhayyim.encrypted.*` envelope (ADR-2605181100), Signal-wrapped to the
    authorized case-member DIDs only. Public datoms (on-chain tx, public address labels)
    stay plaintext.
  - **Prohibited.** Mass / untargeted surveillance; selling or ad-monetizing intel
    (Substrate boundary + Charter Rider §2); de-anonymizing etzhayyim adherents;
    offensive use. tadori is **evidence-producing, not enforcement** — enforcement
    actions route through yabai (risk) + Council, not tadori.
- **Inference.** Any LLM verdict path (e.g. last-resort address classification) routes
  through the Murakumo gateway only (LiteLLM 127.0.0.1:4000 / EVO-X2 / Ollama), never a
  vendor or commercial-GPU path (ADR-2605215000). The Chainalysis-OSI "LLM label" source
  in malak `label_one` is re-pointed at Murakumo or disabled.
- **Server-key.** tadori writes are member-signed (case-member DID) or community-operator
  DID for bulk ingest (RIR feeds / firehose); the tadori Worker/pod holds no platform
  private key (ADR-2605231525). Read-only firehose subscribe + IPFS pin are allowed.

## D2. kotoba-kqe EAVT datom schema (`Datom[CID/T]`)

All state is `Datom[E A V T]` per the kotoba formula `KOTOBA ≝ Datom[CID/T] × EAVT[KSE
Topic] × Pregel[BSP] × Datalog[Δ]` (ADR-2605262130). Entities `E` are CIDv1/blake3
content addresses; `T` is the kotoba Commit-DAG transaction time. Attribute namespace:
`tadori/*`. Eight entity classes:

| Entity class | Key attributes (`A`) | Source today → migrates from |
|---|---|---|
| `tx` (on-chain transaction) | `tadori/chain`, `tadori/tx-hash`, `tadori/from`, `tadori/to`, `tadori/value`, `tadori/token`, `tadori/block`, `tadori/ts` | Kotoba/Datomic `vertex_blockchain_tx` (ADR-2604251935) + malak `pages[*]` |
| `addr` (address) | `tadori/chain`, `tadori/address`, `tadori/checksum-valid`, `tadori/is-contract`, `tadori/verified`, `tadori/balance-usd`, `tadori/tx-count` | malak `fetch_address_meta` / `counterparties` |
| `cluster` (attribution cluster) | `tadori/heuristic` (common-input / change / temporal), `tadori/member` (multi-valued → addr), `tadori/class` (cex_cold / cex_hot / dex_router / bridge_pool / mixer / whale_eoa / unknown_eoa), `tadori/confidence` | malak `classify` verdict |
| `label` (address label) | `tadori/subject` (→ addr), `tadori/source` (local-db / bscscan / abi / ofac-sdn / tornado / chainalysis / murakumo-llm), `tadori/class`, `tadori/confidence` | malak `address_label_pursuit.labels[*]` |
| `case` (investigation anchor) | `tadori/case-id`, `tadori/narrative`, `tadori/authorization-ref`, `tadori/phase` (0 dry-run / 1 live), `tadori/opened-ts` | malak `case:*` anchor |
| `ip-obs` (IP observation) | `tadori/ip`, `tadori/first-seen`, `tadori/last-seen`, `tadori/asn`, `tadori/geo-country`, `tadori/geo-city`, `tadori/is-proxy`, `tadori/is-datacenter`, `tadori/ptr` | ipaddress `IPAddress`/`Geolocation`/`ReverseDns`/`WhoisSnapshot`; yabai `IpLocationHistory`/`IpHostingHistory` |
| `dns-obs` (passive-DNS observation) | `tadori/domain`, `tadori/type` (A/AAAA/MX/NS/TXT/CNAME), `tadori/value`, `tadori/ttl`, `tadori/first-seen`, `tadori/last-seen` | yabai `DnsRecord`; ipaddress `reverse_dns` |
| `attribution` (edge) | `tadori/subject` (→ addr/cluster), `tadori/object` (→ ip-obs / dns-obs / person / org), `tadori/evidence` (multi-valued → tx/label/ip-obs CIDs), `tadori/confidence`, `tadori/encrypted` (bool — PII path) | NEW (cross-store join that no single store does today) |

Edges are themselves datoms (`attribution`) or VAET-indexed value references, so the four
`kotoba-kqe` arrangements serve the traversals the three SQL graphs serve today:

- **EAVT** — "all attributes of this tx/address" (point lookup, ~180 ns).
- **AEVT** — "all addresses with `tadori/class = mixer`" (column scan).
- **AVET** — "the address whose `tadori/address = 0x06f3…`" (unique-value lookup).
- **VAET** — reverse edge: "everything attributing TO this ip-obs" = `correlate-ip-activity`
  (yabai's cross-correlation, now a native 2-hop traversal ~748 ns).

This means yabai's `correlate-ip-activity` / `correlate-accessor-activity` and ipaddress's
graph edges become **kotoba-kqe Datalog rules**, not bespoke SQL — no separate projection
(D7 of ADR-2605262130).

## D3. Migration — yata SQL / Kotoba/Datomic → kotoba-kqe (5 phases)

Aligned to ADR-2605262130's phase numbering (its **Phase 2** is the `kotoba-kqe` Quad
read+write cutover). Default Phase 0 dry-run is preserved throughout (malak contract).

| Phase | Scope | Cutover | Acceptance gate |
|---|---|---|---|
| **T0** (this ADR, R0) | Scaffold `20-actors/tadori/` (CLAUDE.md + manifest + cells + lex) + the EAVT schema above as `00-contracts/lexicons/com/etzhayyim/tadori/*.json`. No data moved. | none | schema lexicons validate; substrate-boundary linter green |
| **T1** | **malak Pregel output** → kotoba QuadStore. `wallet_deep_inspect_pursuit` / `address_label_pursuit` `emit_pegel`/`persist_fs` steps additionally write `tx`/`addr`/`cluster`/`label`/`case` datoms via `@etzhayyim/sdk` (`kotoba-graph`). Kotoba/Datomic `vertex_blockchain_tx` becomes a read-shadow, then retired. | dual-write → verify → drop RW | round-trip: a Takahashi-case replay produces bit-identical classifications reading from kotoba vs RW |
| **T2** | **ipaddress SQL graph** → `kotoba-kqe`. `IPAddress`/`IPRange`/`ASN`/`WhoisSnapshot`/`Geolocation`/`ReverseDns` become `ip-obs`/`dns-obs` datoms. ipaddress `G()` reads re-point to `kotoba-kqe` arrangements. | dual-read → cut | `lookup_ip` / `analyze_ip` return identical enrichment from kotoba |
| **T3** | **yabai SQL graph** → `kotoba-kqe`. `DnsRecord`/`IpLocationHistory`/`IpHostingHistory`/`IntelAccessLog`/`IntelSession`/`IntelDevice` → `dns-obs`/`ip-obs` + (access-audit) `com.etzhayyim.encrypted.*` envelope. `correlate-ip-activity` → Datalog rule over VAET. | dual-read → cut | `correlate-ip-activity` output set-equal under kotoba; access-audit PII verified encrypted |
| **T4** | Retire yata Workers-RPC SQL graph + Kotoba/Datomic `vertex_blockchain_*` for these three actors. Remove projection markers. | git rm + archive marker | substrate-boundary linter rejects any residual `yata`/`Kotoba/Datomic` import in tadori/ipaddress/yabai |

Each cutover is **dual-write/dual-read → verify set-equality → drop legacy**, never a
big-bang. The migration touches *which engine stores the datom*, not the wire semantics
of the malak case model or the encrypted envelope.

## D4. Relationship to malak / ipaddress / yabai (no duplication)

- **malak** keeps the LangGraph/Pregel *compute* (fetch, paginate, classify, label). Its
  terminal `persist_fs`/`emit_pegel` steps now target tadori's kotoba QuadStore instead
  of filesystem + RW. malak ADRs 2605131600 / 2605152000 / 2605172000 are **related**,
  not superseded.
- **ipaddress** keeps being the 1次ソース *collector* (RIR / WHOIS / GeoIP). Its storage
  backend moves to kotoba (T2). The DID hierarchy + agent model are unchanged.
- **yabai** keeps being the *risk-scoring + enforcement-routing* actor. Its CTI graph
  storage moves to kotoba (T3). tadori produces *evidence datoms*; yabai consumes them
  for scoring; Council authorizes enforcement. Separation of duties preserved.
- **tadori** is the new layer that does the **cross-store attribution join** (address →
  cluster → ip-obs → dns-obs → person) that no single store performs today, expressed as
  `kotoba-kqe` Datalog rules over the unified EAVT.

# Consequences

## Positive
- Single honest answer going forward: tx history / IP / DNS **are** in kotoba datomic
  (EAVT), once T1–T3 land. Removes the RW + yata-SQL charter violation.
- Cross-store attribution (the actual "track the actor behind the wallet" capability)
  becomes a 2-hop VAET traversal instead of bespoke per-store SQL + manual joins.
- Constitutional posture (authorized-only, open-source, on-chain-logged, PII-encrypted)
  is explicit and linter-enforceable, matching §1.12 + the tsukuroi propose-only pattern.
- malak / ipaddress / yabai keep their distinct roles; no actor is collapsed or duplicated.

## Negative / risks
- Three concurrent dual-write windows (T1–T3) carry the usual divergence risk; mitigated
  by set-equality acceptance gates per phase.
- `kotoba-kqe` must meet the access-audit + passive-DNS write throughput yabai sees today;
  ADR-2605262130 reports 252K–390K quad/s insert which should cover it, but T3 must
  benchmark the `IntelAccessLog` hot path explicitly before cutover.
- Encrypting attribution PII (D1) means those datoms are opaque to plaintext `kotoba-kqe`
  arrangements — correlation over PII runs inside the authorized-member decryption
  boundary, not as an open Datalog rule. This is the intended privacy cost.

## Migration / rollback
- Each phase keeps the legacy store as a read-shadow for one R-cycle (~30 days) before
  `git rm`, matching the tonbo retire-window pattern (ADR-2605262130 D-row 12).
- T0 (this ADR) moves no data; it is reversible by deleting the scaffold.

# Alternatives Considered

## Alt-1: Fold tracing into malak; no new actor
Rejected. malak is the *compute* engine (LangGraph/Pregel, ephemeral super-steps). The
durable case graph + attribution surface + PII boundary is a distinct, long-lived concern
with a different constitutional posture (authorized-investigation gate, encrypted PII).
Conflating them muddies malak's reusable case-agnostic Pregels (the same reason
ADR-2605152000 Alt-2 kept the Pregels case-agnostic).

## Alt-2: Migrate the three stores to kotoba but add no consolidation actor
Rejected as half the user's ask. It fixes the charter violation (data in kotoba) but
leaves the cross-store attribution join unowned — the actual "track the actor" capability
stays a manual, per-investigation effort. The VAET-native join is the point.

## Alt-3: Keep yata SQL / Kotoba/Datomic for "analytics only"
Rejected — directly prohibited by ADR-2605262130 D7 + D-row 4/12 (RW and SQL side stores
banned as read backends, not just primary stores). `kotoba-kqe` arrangements are the only
authorized hot-path read engine.

## Alt-4: Use a commercial chain-analysis platform (Chainalysis Reactor / Elliptic) as the store of record
Rejected on the same grounds as ADR-2605152000 Alt-3 (cost, per-call billing) **plus** the
Transparent Force open-source invariant (§1.12): the store of record and the heuristics
must be open. Commercial sources remain optional, feature-flagged *inputs* to a `label`
datom, never the system of record.

# References
- ADR-2605262130 (kotoba substrate-engine charter — EAVT, no RW, no projection layer, D7)
- ADR-2605192100 §1.12 + ADR-2605192315 (Transparent Religious Force — open-source + on-chain + 1 SBT = 1 vote)
- ADR-2605152000 (malak `wallet_deep_inspect_pursuit` + `address_label_pursuit` Pregels)
- ADR-2605172000 (malak onion/ransomware tracking)
- ADR-2605131600 (malak LangGraph + Pregel + LangServe orchestration)
- ADR-2604251935 (blockchain VKE head ingest — Kotoba/Datomic `vertex_blockchain_*`, migration source)
- ADR-2605215000 (Murakumo-only inference invariant)
- ADR-2605231525 (server-side signing capability — no platform private key)
- ADR-2605181100 (confidential records `com.etzhayyim.encrypted.*` envelope)
- ADR-2605291500 (tsukuroi — authorized propose-only Tier-B actor pattern)
- `20-actors/ipaddress/CLAUDE.md` (1次ソース IP/ASN/WHOIS/GeoIP collector — T2 migration target)
- `20-actors/yabai/CLAUDE.md` (CTI risk + DNS/IP-history + access-audit — T3 migration target)
