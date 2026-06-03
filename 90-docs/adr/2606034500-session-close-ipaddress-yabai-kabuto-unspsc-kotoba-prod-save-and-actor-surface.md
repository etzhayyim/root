---
id: adr-2606034500-session-close-ipaddress-yabai-kabuto-unspsc-kotoba-prod-save-and-actor-surface
title: "ADR-2606034500: Session close — ipaddress/yabai/kabuto/UNSPSC saved to the PROD kotoba Datom log + did:web actor surface (registration · social · UNSPSC c-code resolver) live on etzhayyim.com"
status: proposed
doc_type: adr
topic: kotoba-prod-save-and-actor-surface
authoritative: true
last_verified: 2026-06-03
priority: 7.5
axis: actor-architecture
weight: 0.75
priority_note: "Documentation-only session closure. Executes ADR-2605301400 §T2/§T3 to LIVE prod: actively collects (RIR delegated-stats / crt.sh) and SAVES the ipaddress (IP/ASN), yabai (CTI/passive-DNS), kabuto (public-company), and a UNSPSC representative graph into the PRODUCTION kotoba Datom log (kotoba.etzhayyim.com), and brings the did:web actor surface live on the apex Worker (etzhayyim.com): ipaddress/yabai registered + social posts, and a getProfile synthesizer that resolves all 18,342 UNSPSC c-code actors. Subordinate to ADR-2605262130/2605312345 (kotoba canonical state), 2605231525 (no platform key), 2606013800 (apex actor profile/did surface)."
authoritative_for:
  - PROD kotoba Datom-log save of ipaddress / yabai / kabuto / UNSPSC graphs
  - kotoba transact bridges (methods/transact.py) for ipaddress / yabai / kabuto + unspsc_kotoba_transact.py
  - apex did:web actor registration of ipaddress + yabai (+ social-post path)
  - apex getProfile synthesizer for the 18,342 UNSPSC c-code actors
  - unspsc-ontology kotoba vocabulary
depends_on:
  - adr-2606031600-ipaddress-yabai-kotoba-eavt-refactor-active-collection
  - adr-2605301400-tadori-onchain-tracing-actor-and-kotoba-eavt-migration
  - adr-2606022000-kabuto-public-company-supply-chain-kg
  - adr-2605171300-open-unspsc-generative-agent-fleet
  - adr-2606013800-actor-profile-and-dynamic-did-json
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605312345-kotoba-datom-first-class-canonical-state
  - adr-2605231525-no-server-key-religious-corp-architecture
related:
  - adr-2605240100-unispsc-organism-post-sink-substrate-bridge
  - adr-2606015400-mesh-runner-serving-and-ipfs-based-did
supersedes: []
superseded_by: []
---

# ADR-2606034500: Session close — kotoba PROD save + did:web actor surface

**Status**: proposed
**Date**: 2026-06-03
**Deciders**: Jun Kawasaki

# Context

Operator request chain: *「全世界の ipaddress/dns の SecurityTrails 的収集と kotoba
datomic 保存状況は?」* → *「能動的でok, a,b を kotoba に refactor」* → *「保存を進めて
動作検証」* → *「prod」* → *「actor/social/did profile も」* → *「企業や unspsc の actor も
atproto kotoba に登録されている?」* → *「1,2 do it」*. The work moves the SecurityTrails-shaped
IP/DNS capability — and the public-company + UNSPSC actors — from design/local-EDN to the
**live production kotoba Datom log** and the **public did:web actor surface**.

# Decision

## A. ipaddress / yabai — active collection + PROD kotoba save (ADR-2605301400 §T2/§T3 → live)

- **Active collectors verified against real endpoints**: AFRINIC `delegated-stats` →
  2,734 ASNs + 1,266 CIDR ranges (`:authoritative`); a full-5-RIR sweep → 129,912 records;
  crt.sh CT-log → 27 certs. Offline-default + G7 operator-gated; no host scanning (akuma/
  aratame boundary), no adherent de-anon, no mass surveillance.
- **`methods/transact.py`** (both actors): list-form `[:db/add E A V]` datoms + schema
  install (`:db/doc` dropped — kotoba EDN reader rejects `|`); operator-JWT auth.
- **SAVED to PROD kotoba** (kotoba.etzhayyim.com, :8077): ipaddress 60 schema + **427 data
  datoms** (graph `bafyrei… qykm`); yabai schema + **163 data datoms** (graph `bafyrei…3xe`),
  **G6/G10 enforced at write** (`:access/*` encrypted, envelope CID only, no plaintext PII).
- **PROD provisioning**: the production node ran the brew `kotoba serve` (CLI reduced router,
  no `wasm-runtime`). Cut over the launchd job `com.etzhayyim.kotoba` to a release
  `kotoba-server --features wasm-runtime` binary → `wasm_executor: ready`; kotoba.etzhayyim.com
  + kotoba.gftd.ai restored. **Auth** = operator JWT whose `sub == operator_did` (keychain
  `did:key:ze2e1699…`); `require_operator_auth` verifies `sub`/`exp` only (operator trust
  boundary, no platform key — ADR-2605231525).

## B. did:web actor surface — registration + social + did-profile (ADR-2606013800)

- **Registered** `ipaddress` + `yabai` in the actor-profile SSoT + apex `INFRA_ACTORS`;
  apex Worker **deployed** (OAuth) → `did:web:etzhayyim.com:actor:{ipaddress,yabai}` resolve
  live (getProfile 200, did.json with atproto services, Universal Resolver).
- **Social posts LIVE**: `methods/social.py` (both) compose aggregate-first, Charter §2-scanned
  status posts → `atproto.repo.write` into the prod kotoba Datom log (ipaddress 4 + yabai 2),
  federating via IPNS.
- **yoro `/profile/<did>` 405 fix**: the SPA resolved getProfile against the PDS
  (atproto.etzhayyim.com, POST-only → 405 on GET) for apex actor DIDs → every actor page
  failed. `atproto-agent.ts` now routes getProfile for `did:web:etzhayyim.com:actor:*` to the
  apex (GET 200 + CORS `*`); committed, build+deploy of the yoro SPA pending (env workspace
  could not `pnpm install`).

## C. kabuto (public companies) → PROD kotoba

- New `20-actors/kabuto/methods/transact.py` (batched) → SAVED the company graph to PROD:
  schema 107 + **1,602 data datoms** (743 companies + HQ addresses + IR contacts + supply
  edges) (graph `bafyrei…wa2i`). Resilience/transparency map, never a target-list (kabuto G2/G4).

## D. UNSPSC (18,342-agent fleet) → PROD kotoba + apex c-code resolver

- New `00-contracts/schemas/unspsc-ontology.kotoba.edn` (`:unspsc.seg/* :unspsc/*`; supersedes
  the NDJSON post-sink as the commodity system-of-record, ADR-2605240100 keeps social egress) +
  `20-actors/magatama/py/unspsc_kotoba_transact.py`. SAVED a representative set to PROD: 36
  segments + 288 commodity codes (each with `did:web:…:actor:c<code>`) = **1,853 datoms** (graph
  `bafyrei…2fay`).
- **apex getProfile synthesizer**: `resolveActorRecordTiered` gains a tier-3.5 synthesizer for
  VALIDATED `c\d{6,12}` handles (`UNISPSC_HANDLES`, 18,342-fleet) — builds a profile from the
  code + a 36-segment title table. **Deployed (Version 2e9cdc41)**; all 18,342 c-code actors
  resolve (e.g. `c10101500` → "UNSPSC 10101500 — Live Animal"); unregistered codes stay
  ProfileNotFound (set-gated); ipaddress/yabai/kabuto unaffected.

# Consequences

- **Positive**: the world IP/DNS, public-company, and UNSPSC graphs are **live in the prod
  kotoba Datom log**; the did:web actor surface (profile · did.json · social · UNSPSC c-code)
  is live on etzhayyim.com. The active collectors are real (not stubs), verified against real
  registries. The prod node now serves the full XRPC surface (`datomic.transact` + executor).
- **Honest limits**: prod graphs are bounded `:representative` seeds (no full-universe ingest;
  G7-gated); the ADR-2605301400 §T2/§T3 dual-read set-equality gates are still pending, so the
  legacy RisingWave graphs are **not yet retired** (§T4, Council Lv6+). Prod-side readback of a
  private graph needs an operator `datom:read` CACAO (Keychain seed, not extracted) — writes
  confirmed by `datom_count`/`tx_cid`; the equivalent save was read-back-verified on a public
  test node. The yoro SPA getProfile fix is committed but **not yet built/deployed** (env
  pnpm-workspace broken). UNSPSC titles are sector-derived `:representative` (segment-level in
  the synthesizer); a licensed UNSPSC dictionary ingest would tag `:authoritative`.
- **Environment caveat (process, not architecture)**: a concurrent automation rapidly switched
  the shared working tree across feature branches (reflog: continual `checkout`/`pull`),
  deleting newly-created source files mid-session. Mitigated by an **isolated `git worktree`**
  for the apex build+deploy (daemon-proof). The PROD kotoba DATA persists independently of git;
  source for the transact bridges + this ADR is committed on `feat/kanjo-financial-disclosure-actor`;
  the ipaddress/yabai substrate (ADR-2606031600) is on PR #865.

# Alternatives Considered

1. **Keep companies/UNSPSC as local EDN / NDJSON queue** — rejected: the operator asked whether
   they are "atproto/kotoba 登録"; only a live kotoba save + resolvable did satisfies that.
2. **Per-code INFRA_ACTORS entries for 18,342 UNSPSC** — rejected: unmaintainable; a validated
   pattern synthesizer + a 36-segment table resolves the whole fleet from a tiny lookup.
3. **Global yoro getProfile base swap to the apex** — rejected: would reroute auth/session/posts
   and risk login/cookies; the surgical actor-DID-only route is safe.

# References

- ADR-2606031600 — ipaddress/yabai kotoba EAVT refactor + active collection (substrate)
- ADR-2605301400 — tadori §T0–T4 migration plan (this executes §T2/§T3 to prod)
- ADR-2606022000 — kabuto public-company KG · ADR-2605171300 — Open-UNSPSC agent fleet
- ADR-2606013800 — apex actor profile + dynamic did.json · ADR-2605231525 — no platform key
- ADR-2605262130 / 2605312345 — kotoba canonical Datom-log state
- `00-contracts/schemas/{ip-network,passive-dns-cti,public-company,unspsc}-ontology.kotoba.edn`
- `20-actors/{ipaddress,yabai,kabuto}/methods/transact.py` · `20-actors/magatama/py/unspsc_kotoba_transact.py`
- `50-infra/etzhayyim-did-web/src/worker.ts` (UNSPSC c-code synthesizer; Version 2e9cdc41)
