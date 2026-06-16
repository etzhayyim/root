---
id: adr-2606161630-aburi-personal-tracking-exposure-observatory
title: "ADR-2606161630: aburi 炙り — personal-tracking-exposure observatory (member-side, own-data)"
status: proposed
doc_type: adr
topic: aburi-tracking-exposure
authoritative: true
last_verified: 2026-06-16
priority: 5.0
axis: architecture
weight: 0.50
priority_note: ""
authoritative_for:
  - 20-actors/aburi
  - 00-contracts/schemas/tracker-exposure-ontology.kotoba.edn
depends_on:
  - 2605192100
  - 2606082400
  - 2606071601
  - 2606082100
  - 2605302130
  - 2606112201
  - 2605312500
  - 2606101400
  - 2605181100
  - 2605231902
  - 2605312345
  - 2605215000
related:
  - 2606122400
  - 2606013800
supersedes: []
superseded_by: []
---

# ADR-2606161630: aburi 炙り — personal-tracking-exposure observatory (member-side, own-data)

**Status**: proposed
**Date**: 2026-06-16
**Deciders**: Jun Kawasaki

# Context

The founder asked, directly: *is there an actor that visualizes — when I accept the ToS and grant
permissions on Google / Facebook / X / Apple — **which** ad networks collect my data, and **how
much** each company tracks me?*

A survey of the roster found the **pieces but not the fusion**:

- **sukashi 透かし** (ADR-2606071601) datafies the **firm↔firm** programmatic ad supply chain from
  public IAB files (ads.txt / app-ads.txt / sellers.json). It is constitutionally bounded to
  firm-side supply-chain (its G1/G2 forbid per-user data modelling) — it never answers "who tracks
  **me**".
- **akashi 証** mirrors platform ad-library disclosure (what Meta/Google/X voluntarily publish) —
  advertiser-side, not the trackers behind a user's own consent.
- **himotoki 繙き** (ADR-2605302130) files DSARs for the member's own data — the *request*
  mechanism, not an exposure *map*.
- **shiori 栞** (ADR-2606082100) names addictive-design/surveillance as a cohort-scale wellbecoming
  detractor — the burden lens, not the per-member data-flow map.

No actor fused **the member's own exposure map** with **a transparent route to relieve it**.
Critically, sukashi *cannot* be extended to cover this: its charter boundary is firm-side by
construction. The charter-clean move is a **new** member-side, own-data actor.

The charter frame is the load-bearing justification. Charter §2(c) v3.1 (ADR-2606082400) puts
surveillance on a **reciprocity axis**: *monetized-OR-asymmetric* surveillance is prohibited;
*symmetric* 相互監視 is affirmed (the social form of 神の監視 — village-scale deterrence + anti-
isolation). Ad-tracking is the archetypal **asymmetric** watcher: it sees the person; the person
cannot see it. An actor that makes that one-way mirror two-way **for the watched** is not new
surveillance — it is the **reciprocity instrument**. It must, itself, hold no asymmetric power: it
operates only on the member's OWN, local-only data and builds no dossier of anyone.

# Decision

Create **aburi 炙り** (`20-actors/aburi/`, `did:web:etzhayyim.com:actor:aburi`), Tier-B, **R0
design-only**. 「炙り」= 炙り出す, to bring hidden things to light by heat (invisible ink) — the
craft-word sibling of sukashi 透かし; it炙り出す the trackers hidden behind a consent dialog.

aburi is the **member-side, own-data** inversion of the ad-tech lineage. It weaves, over the new
`tracker-exposure-ontology`, an edge-primary kotoba Datom graph:

- **nodes**: `:surface` (the consent venue — search/social/app-store/mobile-app/OS, with disclosed
  operator), `:permission` (a granted permission or ToS data-sharing clause, with DISCLOSED
  sensitivity band), `:collector` (an ad network / data broker / tracker SDK / analytics, with its
  `org.corp.*` parent shared with sukashi/kabuto and its **public catalogue provenance**
  `:collector/catalog` ∈ exodus / apple-privacy / play-data-safety / sellers-json / iab),
  `:datatype` (the kind of data that flows), `:relief` (the route that closes the exposure, bound
  to its carrier actor).
- **edges** (karma lives here, N1): `:grants` (surface→permission), `:flows-to`
  (permission→collector — the exposure edge), `:collects` (collector→datatype), `:routes-to`
  (permission→relief), `:relieves` (relief→collector).

On **read** (transient, never stored — N1/G2) it computes:

1. `exposure[collector]` = Σ inbound `:flows-to` × disclosed permission-sensitivity weight — **who
   tracks you most** (the 取-holders).
2. `surface_leak[surface]` = two-hop Σ `:grants` × downstream permission flow — **which platform
   exposes you most** (Google / Facebook / X / Apple…).
3. `spread[datatype]` = Σ inbound `:collects` — **what kinds of your data are most harvested**.
4. `unrouted_permissions` = permissions that leak but have no `:routes-to` — **the reciprocity
   gap**, routed to himotoki (DSAR) / kaiyaku (sever) / kurashimori (consumer opt-out) / tedai
   (on-device revoke).

**Eight constitutional gates** (full text in `manifest.jsonld`):

- **G1 OWN-DATA-ONLY** — maps the member's OWN exposure from THEIR OWN consented exports (Google
  Takeout / Apple App-Privacy / Play Data-safety / on-device permission dump); the public seed is
  REPRESENTATIVE (no real person); no record of any OTHER person, no third-party PII, no biometric,
  no raw identifier value. The himotoki/meisai pattern.
- **G2 edge-primary** — exposure lives only on `:flows-to`; integrals computed on read; no stored
  per-collector score.
- **G3 non-adjudicating** — collector catalogue membership + collector→data mappings + sensitivity
  bands are DISCLOSED facts; naming an SDK as an ad collector is a public catalogue fact, never an
  accusation of wrongdoing.
- **G4 RECIPROCITY-RESTORING** — makes the asymmetric ad-watcher visible to the watched (§2(c)
  v3.1); aburi itself never tracks/sells/profiles.
- **G5 sourcing honesty** · **G6 Murakumo-only** · **G7 outward-gated + LOCAL-ONLY personal data**
  (`data/local/` gitignored; live ingest + relief routing member-sig + operator + Council; no-
  server-key; loop does no network I/O — the meisai discipline) · **G8 no credentials / no raw
  identifiers** (the emit attr allowlist carries none, so none can be projected).

**R0 deliverables (this ADR)**: ontology + manifest + CLAUDE.md + a 47-node / 84-縁 representative
seed + pure-stdlib `analyze` / `datom_emit` / `coverage_report` (`.py` canonical + `.cljc` 1:1
ports, per the 2606160842 py→clj wave) + 14 tests green (incl. G1 no-other-person, G3
catalogued-facts-not-verdicts, G8 no-credential-attr inversions) + wasm/README. Live ingest of a
member's exports, the WASM build, and any relief routing are **R1+ / operator + Council-gated**.

# Consequences

- **The roster gap is closed**: the member can now see, from their own consents, who collects their
  data and how much, and is handed a route to opt out — the fusion sukashi/akashi/himotoki left
  open. On the seed: top trackers = The Trade Desk / Meta Audience Network / Google AdMob /
  LiveRamp; leakiest surface = Google/Android; top reciprocity gap = the ToS "share with partners"
  clause (critical-sensitivity, no opt-out route yet).
- **Charter is strengthened, not bent**: aburi operationalizes the §2(c) v3.1 reciprocity axis — it
  is the tool that restores symmetric sight against asymmetric ad-surveillance, while structurally
  unable to become an asymmetric watcher itself (own-data, local-only, no-server-key, no-credential).
- **Cross-actor wiring**: collectors map into sukashi/kabuto's `org.corp.*` id space; the
  reciprocity gap routes to himotoki/kaiyaku/kurashimori/tedai; surface-leak routes to shiori;
  collector concentration routes to kabuto/tsumugi. aburi only PROPOSES; the carriers act (G7).
- **Risk surface acknowledged**: an exposure map of a real member is sensitive. The mitigation is
  architectural — local-only (`data/local/` gitignored), structure-not-values (G8), no-server-key,
  Council-gated outward — the same discipline meisai uses for card statements. R0 ships no live
  personal data at all.

# Alternatives Considered

- **Extend sukashi with a user-side view** — rejected: sukashi's G1/G2 bound it to firm-side
  supply-chain by construction; a per-user lens would violate its own charter. Separation of
  concerns is the charter-clean choice.
- **Fold this into himotoki** — rejected: himotoki is the DSAR *request* actor; an exposure
  *observatory* is a distinct concern that *feeds* himotoki (the reciprocity gap is himotoki's
  worklist), not the same actor.
- **Live SDK-scanning / network instrumentation** (Blacklight/Exodus-style dynamic analysis) —
  deferred past R0: it implies on-device interception that must be member-run and Council-gated;
  R0 models exposure from the member's already-disclosed exports + public catalogues, no probing.
- **A public per-person tracking registry** — structurally refused (G1): aburi holds no other
  person's data and builds no dossier; that design is unrepresentable.

# Implementation update (2026-06-16) — A/B/C legs landed

The initial R0 shipped the analyzer + ontology + representative seed. This update lands the three
legs that move it from "analyzer over a public seed" toward "real own-data, on the live log,
publishable":

- **(A) live kotoba transact bridge** — `methods/kotoba_bridge.py` (the ibuki kotoba_bridge
  pattern): pushes the member's local exposure commit-DAG to the live engine at
  `:8077/xrpc/com.etzhayyim.apps.kotoba.datomic.transact`, one tx per `datomic.transact`, oldest
  first; exactly-once `:aburi-bridge/*` cursor, `expected_parent` commit-DAG chaining,
  `:aburi.tx/*` provenance, fleet host-allowlist (ADR-2605215000), **no-server-key** (unsigned
  operator bearer keyed by a PUBLIC DID env var; the network leg is INJECTED so the loop is a pure
  function). **Dry-run by default**; a live push requires `ABURI_KOTOBA_LIVE=1` + member-sig +
  operator + Council (the member's exposure leaving the device is an outward act, G7).
- **(B) real acquisition (ingest)** — `methods/ingest.py` + `methods/autorun.py`: parses the
  member's OWN consented exports — **iOS App Privacy Report** (per-app data access + the ad/tracker
  DOMAINS each app contacted → catalogued collectors), **Google Play Data-safety** (data shared
  "for Advertising or marketing" → ad collectors), **Google Takeout Ads-settings** (ad-
  personalization + activity controls), **on-device permission dump** — into the same
  tracker-exposure graph the analyzer reads. The local heartbeat dedups by intake content CID and
  appends one content-addressed tx per new export (resume-safe, byte-identical). **G8 guard**
  `raise`s on credential-shaped keys and raw-identifier values (IDFA/GAID/IMEI/email/PAN/UUID);
  only exposure STRUCTURE is projected (the datom_emit attr allowlist). Exports live under
  `data/local/` (gitignored, G7); the loop does no network I/O.
- **(C) publish (etzhayyim.com resolvability)** — registered in the three homes
  (`actor-profile-seed.kotoba.edn` SSoT, `infra-actors.ts` tier-3 fallback, static
  `50-infra/etzhayyim-did-web/public/actor/aburi/{did.json,profile.json}`) + a **build-ready WASM
  component** (`wasm/` world.wit + app.py exporting `analyze`/`datoms`/`coverage`, offline python
  sanity green). `verificationMethod` empty (no-server-key). All driven by **bb** (the repo standard
  — no `.sh`): `bb aburi:build-wasm` (impl `tools/build.clj`), `bb aburi:publish --pin --deploy --kv`
  (impl `tools/publish.clj`). The `componentize-py` build, IPFS pin, KV/kotoba ingest, and Worker
  deploy are the **operator steps**. `wasmCid` stays **null** by design: componentize-py is **not
  byte-reproducible** (verified — two builds gave `bafybeibzwi…` then `bafybeia66s…`), and the apex
  `/ipfs` gateway re-verifies bytes against the CID, so the operator records the **pinned** CID at
  `bb aburi:publish --pin` time rather than committing a CID that no fresh build reproduces.

**Honest boundary**: the live transact, the WASM build/deploy, and ingest of a member's REAL
exports are all operator/Council-gated outward acts — they are *runnable code with offline tests*,
not executed here. The new I/O legs are `.py` (the established boundary for I/O-coupled code,
ADR-2606131800); `.cljc` byte-parity ports of ingest/autorun/bridge (the meisai pattern) are the
R1 follow-up. **Test count: 31 python (analyze 11 / coverage 3 / ingest 9 / bridge 8) + 14 cljc
(1369 assertions) green.**

# References

- ADR-2606071601 (sukashi — firm-side ad-tech supply-chain observatory)
- ADR-2606082100 (shiori — wellbecoming detractor observatory)
- ADR-2606082400 (Charter Rider v3.1 — §2(c) reciprocity axis: asymmetric surveillance prohibited / 相互監視 affirmed)
- ADR-2605302130 (himotoki — DSAR / own-data) · ADR-2606112201 (kaiyaku — sever) · ADR-2605312500 (kurashimori — consumer opt-out) · ADR-2606101400 (tedai — on-device revoke)
- ADR-2606122400 (meisai — member-own local-only ingestion pattern)
- ADR-2605312345 (kotoba Datom = first-class canonical state) · ADR-2605215000 (Murakumo-only inference)
- ADR-2606160842 (py→clj actor port wave — `.py` canonical + `.cljc` 1:1)
