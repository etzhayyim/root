# tadori.etzhayyim.com — 辿 Authorized On-Chain Tracing + Actor-Attribution

辿 (*tadori* — "to trace / follow a thread back along its path"). Authorized,
case-anchored crypto-asset transaction tracing + actor attribution. **kotoba-EAVT-native.**
Status: 🟡 R0 scaffold (ADR-2605301400).

> **Constitutional posture (NOT amendable below Council Lv7+ for §1.12 items)**: tadori is
> **authorized-investigation-only, open-source, on-chain-monitorable, evidence-producing
> (NOT enforcement)**. Every live write requires a `case` anchor with an authorization
> reference. No case → Phase 0 dry-run only. See ADR-2605192100 §1.12 + ADR-2605192315
> (Transparent Religious Force) and ADR-2605291500 (tsukuroi propose-only pattern).

## Architecture

| 項目 | 値 |
|---|---|
| **Purpose** | address → cluster → off-chain identity / IP / DNS attribution, case-anchored |
| **Data** | **kotoba QuadStore / `kotoba-kqe` EAVT** (NOT yata SQL, NOT RisingWave) — via `@etzhayyim/sdk` only |
| **Compute** | malak LangGraph/Pregel family (`wallet_deep_inspect_pursuit`, `address_label_pursuit`) — tadori owns the durable graph, malak owns the super-steps |
| **Sources** | ipaddress.etzhayyim.com (1次 IP/WHOIS/GeoIP) + yabai (CTI/risk) + on-chain (BSC/ETH/BTC head ingest) + feature-flagged external (OFAC SDN / Tornado / Chainalysis) |
| **Inference** | Murakumo gateway only (LiteLLM 127.0.0.1:4000 / EVO-X2 / Ollama) — never vendor/commercial GPU (ADR-2605215000) |
| **PII** | person / IP / device attribution datoms written under `com.etzhayyim.encrypted.*` envelope, Signal-wrapped to case-member DIDs (ADR-2605181100) |
| **Server-key** | member-signed (case-member DID) or community-operator DID (bulk ingest); no platform private key (ADR-2605231525) |
| **Domain** | `tadori.etzhayyim.com` / DID `did:web:tadori.etzhayyim.com` |

## kotoba EAVT datom schema (`Datom[E A V T]`)

Attribute namespace `tadori/*`. Entities `E` = CIDv1/blake3; `T` = Commit-DAG time. Eight
classes: `tx`, `addr`, `cluster`, `label`, `case`, `ip-obs`, `dns-obs`, `attribution`.
Full attribute list → ADR-2605301400 §D2. Reads use the four `kotoba-kqe` arrangements:

- **EAVT** — all attributes of a tx/address (point lookup ~180 ns)
- **AEVT** — all addresses with `tadori/class = mixer`
- **AVET** — the address whose `tadori/address = 0x…`
- **VAET** — reverse edge = `correlate-ip-activity` (2-hop traversal ~748 ns), replaces
  yabai's bespoke cross-correlation SQL

### Threat-intel Datomic API bridge

`kotoba/` now contains the T3 bridge for passive threat-intel observations:

| File | Purpose |
|---|---|
| `kotoba/schema.edn` | Datomic schema for `tadori.source/*`, `tadori.obs/*`, `tadori.dns/*`, `tadori.ip/*`, and `tadori.indicator/*`. |
| `kotoba/seed.threat-intel.jsonl` | Operator-staged JSONL sample for public-archive and SecurityTrails-shaped compatibility records. |
| `kotoba/ingest_threat_intel.py` | JSONL validator + `tx_edn` generator + live `com.etzhayyim.apps.kotoba.datomic.transact` writer with optional `datomic.datoms` readback. |
| `kotoba/deploy.sh` | Dry-run/live wrapper for a running kotoba node; live runs verify readback. |

Dry-run:

```sh
20-actors/tadori/kotoba/deploy.sh
```

Live writes require a running kotoba node plus `KOTOBA_SESSION_POP` or `KOTOBA_TOKEN`.
If `KOTOBA_SESSION_POP` is supplied, the script first verifies it through
`com.etzhayyim.pds.session.verify`, then posts schema and data through
`com.etzhayyim.apps.kotoba.datomic.transact`. Live data writes require `TADORI_CASE_ID`
or per-record `case_id`; the script rejects any collection mode other than
`operator-staged-passive-archive`. `deploy.sh` runs with `--verify-readback`, so
each live run also confirms the staged source, DNS, IP, and indicator datoms via
`com.etzhayyim.apps.kotoba.datomic.datoms`.

Vendor-shaped feeds (`securitytrails-compatible`, `dnsdb-compatible`,
`recordedfuture-compatible`) are accepted only as `source_role:
feature-flagged-input`, never `system-of-record`. Tier-D sources require explicit
`--allow-tier-d` and remain non-SoR. This preserves G3/G4/G10/G11: no live DNS /
WHOIS / RDAP / DoH / probe is performed by this bridge, and all writes land only
in kotoba Datomic state.

## Migration (ADR-2605301400 §D3) — yata SQL / RisingWave → kotoba

| Phase | Scope | Acceptance gate |
|---|---|---|
| **T0** (here) | scaffold + lexicons; no data moved | schema lexicons validate; boundary linter green |
| **T1** | malak Pregel output → kotoba QuadStore; RW `vertex_blockchain_tx` retired | Takahashi-case replay bit-identical kotoba vs RW |
| **T2** 🟢 substrate landed (ADR-2606031600) | ipaddress SQL graph → kotoba EAVT (`ip-network-ontology` + seed + active RIR/RDAP/rDNS ingest + analyze) | `lookup_ip`/`analyze_ip` identical from kotoba (dual-read verify pending) |
| **T3** 🟢 substrate landed (ADR-2606031600) | yabai CTI/DNS/IP-history/access-audit → kotoba EAVT (`passive-dns-cti-ontology` + seed + active crt.sh/pdns ingest + analyze; `:access/*` encrypted) | `correlate-ip-activity` set-equal; PII verified encrypted (analyze G6/G10 self-audit PASS; dual-read verify pending) |
| **T4** | retire yata Workers-RPC SQL + RW `vertex_blockchain_*` | boundary linter rejects residual `yata`/`RisingWave` import |

Each cutover is dual-write/dual-read → verify set-equality → drop legacy (one R-cycle shadow).

## Cells (6; R0 path-reserved under `40-engine/kotoba/crates/kotoba-kotodama/cells/tadori_*/`)

| Cell | Purpose | Key gate |
|---|---|---|
| `case_intake` | open/validate an authorized `caseMandate` | G3, G5 |
| `tx_trace` | wallet deep-inspect → tx/addr/cluster datoms (delegates to malak `wallet_deep_inspect_pursuit`) | G9, G11 |
| `address_label` | multi-source labeling → label datoms (delegates to malak `address_label_pursuit`) | G4, G9 |
| `attribution_join` | cross-store join addr/cluster → ip-obs/dns-obs/person (kotoba-kqe VAET); PII encrypted | G6, G10, G11 |
| `transparent_force_log` | on-chain-anchored audit datom per case action (Charter §1.12) | G5, G7 |
| `silen_tadori_review` | quarterly Council audit; structural zero-counters | G12 |

Each cell is import-time `RuntimeError` until T1 (Council Lv6+ ≥3 ratify post 2026-06-19).

## Constitutional gates (12; IMMUTABLE per ADR-2605301400 §D1)

G1 Charter Rider §2(a)-(h) scan · G2 append-only EAVT (supersededBy, no soft delete) ·
**G3 AUTHORIZED-INVESTIGATION-ONLY** (caseMandate required; no case → Phase 0 dry-run) ·
**G4 OPEN-SOURCE** (no proprietary chain-analysis as SoR) ·
**G5 ON-CHAIN-MONITORABLE** (Transparent Force audit datom) ·
**G6 PII-ENCRYPTED** (`com.etzhayyim.encrypted.*`) ·
**G7 EVIDENCE-ONLY / NO ENFORCEMENT** (enforcement via yabai + Council) ·
**G8 NO PLATFORM-HELD KEY** (ADR-2605231525) · G9 Murakumo-only (ADR-2605215000) ·
**G10 NO MASS SURVEILLANCE / NO ADHERENT DE-ANON** · G11 kotoba-only (ADR-2605262130) ·
G12 Bonsai seed-tier prune on any silenTadoriReview nonzero counter.

## Lexicons (`com.etzhayyim.tadori.*`)

`caseMandate` (authorization anchor; `transparentForceLogged` const true; `phase` 0/1) ·
`attributionFinding` (cross-store edge; `encrypted` required true for person/IP/device) ·
`traceReport` (durable malak trace result; `externalSourcesUsed` = feature-flagged inputs only) ·
`silenTadoriReview` (9 zero-counters: noncaseWrite / plaintextPii / proprietarySor /
enforcementAction / platformHeldKey / murakumoBypass / massSurveillance / adherentDeanon /
nonKotobaStore — any nonzero ⇒ halt + chigiri.disputeMediation). Schemas + manifest:
`00-contracts/lexicons/com/etzhayyim/tadori/` · `20-actors/tadori/manifest.jsonld`.

## Relationship to siblings (no duplication)

- **malak** = compute (Pregel super-steps). tadori = durable case graph + attribution surface.
- **ipaddress** = 1次 collector. tadori reads its `ip-obs`/`dns-obs` datoms post-T2.
- **yabai** = risk scoring + enforcement routing. tadori feeds it *evidence datoms*; yabai
  scores; Council authorizes enforcement. Separation of duties preserved.
- **danjo** (ADR-2605301600) = parallel kotoba-EAVT investigation sibling, **disjoint domain**:
  tadori traces on-chain crypto-asset actors (authorized-investigation, PII-encrypted, case-anchored);
  danjo cross-references the STATE's pre-published open-government records (passive-only, non-adjudicating,
  public-record-only). Shared EAVT/kotoba-kqe pattern; no data overlap, no shared cells.

## Do Not

- Do not store any tadori state in yata SQL / RisingWave / Postgres / SQLite (ADR-2605262130).
- Do not write live datoms without a `case` anchor + authorization ref (Phase 0 dry-run only).
- Do not embed proprietary chain-analysis heuristics; external paid sources are
  feature-flagged `label` inputs only, never the system of record (open-source invariant).
- Do not perform enforcement, de-anonymize etzhayyim adherents, or run untargeted/mass
  surveillance. Evidence-producing only.
- Do not route LLM classification through any non-Murakumo path (ADR-2605215000).
- Do not write person/IP/device attribution as plaintext — use `com.etzhayyim.encrypted.*`.
