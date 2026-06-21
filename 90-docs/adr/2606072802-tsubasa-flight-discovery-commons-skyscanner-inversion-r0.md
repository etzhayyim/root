---
id: adr-2606072802-tsubasa-flight-discovery-commons
renumbered_from: "2606072800"
title: "ADR-2606072802: tsubasa 翼 — flight-route/fare discovery commons (Skyscanner inversion), R0+R1"
status: proposed
doc_type: adr
topic: tsubasa-flight-commons
authoritative: true
last_verified: 2026-06-07
priority: 5.0
axis: architecture
weight: 0.50
priority_note: ""
authoritative_for:
  - 20-actors/tsubasa
depends_on:
  - 2606012100   # okaimono (external-mirror + affiliate-strip pattern)
  - 2606071600   # shukubo (Ring-2 self-book handoff pattern)
  - 2605262130   # kotoba storage substrate
related:
  - 2606041827   # watari (live aircraft POSITION — sibling, different concern)
supersedes: []
superseded_by: []
---

# ADR-2606072802: tsubasa 翼 — flight-route/fare discovery commons (Skyscanner inversion), R0+R1

**Status**: proposed
**Date**: 2026-06-07
**Deciders**: Jun Kawasaki

# Context

The 2026-06-07 app-coverage audit named eight mainstream apps. Seven now have charter-clean
inversions (uber→ainori, airbnb/hotels→shukubo, salesforce→business-manager, calendly→yotei,
drive→organizer, indeed→talent, shopify→omise). **"Flight scanner" (Skyscanner / Google Flights)
remains the one uncovered slot** — `watari 渡り` covers live aircraft POSITION (ADS-B), not fare/
schedule search or booking.

A faithful Skyscanner is a charter conflict: it monetizes via **referral/affiliate commissions**
on every onward click, **ad placement**, and **fare-watch tracking of the user**, plus
urgency dark-patterns ("price will rise!"). The underlying need — find a flight, compare options
honestly — is fine; the inversion drops the commission, the ad, the tracking, and the urgency.

# Decision

Introduce **`tsubasa 翼`** (Tier-B actor, `tsubasa.etzhayyim.com`), a **flight-route/fare
discovery commons** — an external-data-only meta-search whose every onward link is affiliate-
stripped and where the member **self-books on the airline/operator's own site** (no inflow). It
reuses okaimono's affiliate-strip and shukubo's Ring-2 self-book-handoff patterns. R0→R1 (tested).

**Charter-clean inversions / invariants (gates, see manifest.edn):**

| Skyscanner term | tsubasa dual | gate |
|---|---|---|
| affiliate/referral commission on every click | **affiliate-stripped** onward deep-link; member books on the airline's OWN site; tsubasa is never merchant-of-record, takes no inflow | G1 no-affiliate-no-inflow |
| ad placement / sponsored fares | **data-only**; no sponsored ranking / paid placement | G2 no-ads |
| "price will rise", fare-watch nudges | **honest fares only**; no urgency/scarcity; no predictive-pressure field | G3 wellbecoming-anti-dark |
| rank by referral payout | rank by **true total cost** (fare + baggage) with **CO₂ emissions surfaced**, never hidden | G4 emissions-honest |
| fare-watch tracking of the user | **no person fare-tracking / pattern-of-life**; a search is stateless w.r.t. the searcher | G5 no-person-tracking |
| vendor pipelines / LLM | Murakumo-only; kotoba-EAVT-native | G6 murakumo-only / G7 kotoba-eavt-native |

**Scope:** R1 implements honest fare search + total-cost-with-emissions comparison + affiliate-
stripped self-book handoff over a bounded `:representative` fare set. **R2** added the observatory
+ persistence layer (per-route carrier-HHI concentration → competition reading → `:opening`;
content-addressed kotoba commit-DAG; idempotent heartbeat; DID). **R3 (2026-06-21) UNLOCKS the G8
live-ingest gate** under charter bounds (see §R3 below); no real booking is ever transacted by
tsubasa (member self-books).

**Composition:** sibling of `watari` (position) — tsubasa is the *planning* layer, watari the
*live* layer; both are observational, neither is an OTA. Emissions data composes with the
Wellbecoming carbon axis used by okaimono.

# R3 — live ingest + Murakumo digest + WASM (G8 gate UNLOCK, 2026-06-21)

**Attestation.** Per the Bootstrap operational premise (root `CLAUDE.md`, 2026-06-11: *Council
attestation = GitHub Pull Request review*), the founder (sole Council member, Lv7+, 1/1
unanimity) authorized unlocking G8. The on-record attestation is **this change's PR review +
merge** — the merge commit / PR URL is the provisional value for the `COUNCIL_*` gate reference
until the on-chain multisig (Base testnet+) supersedes it.

**What unlocks.** G8 moves from *"live ingest = Council Lv7+ gated, `:representative`-only"* to
*"live ingest operator/member-ENABLED"* — but the unlock is **charter-bounded, and the bounds are
structural (in code + tests), not policy**:

1. **No paid GDS terminal.** `ingest/assert-clean-source` accepts only `:public` (free / disclosed
   fare data) or `:member-principal` (the member's OWN airline-account API credentials). A
   `:paid-terminal` (Amadeus / Sabre / Travelport opaque billed terminal) is **refused** — an
   opaque, lock-in commercial terminal scores negative on the ECL objective function (Rider
   §2(e) specialist-knowledge / §2(i) compute lock-in; the v3.5 net-effect assessment, not a
   vendor-name ban).
2. **No-server-key — what it actually gates (clarified).** The invariant (ADR-2605231525) bars a
   *custodial, unilateral signing key* on an etzhayyim-operated automated process. It is **not** a
   ban on automation, and it **exempts read-only operations** (the `// no-server-key: read-only`
   marker). Therefore:
   - **PUBLIC sources are fetched AUTONOMOUSLY by the actor itself** — `methods/fetch.cljc` does a
     read-only HTTP GET and feeds `ingest` with no key and no human in the loop, exactly like
     `kaname` (`ingest/fetch-text`), `watari`, `tsumugi`, and the organism's read-only inference.
     (The earlier "operator runs the fetch leg" framing over-gated this; corrected here.)
   - **`:member-principal` sources** (a member's OWN airline-account credentials) run in the
     **member's** runtime by consent — `fetch.cljc` refuses `:member-principal` in the autonomous
     path; the member calls `ingest` directly.
   - **Signing the actor's OWN writes** uses a **self-generated `did:key`** whose seed is sealed
     (Keychain / 1Password, CONCEALED, never committed) and **present-only** (the actor PRESENTS /
     verifies, never exfiltrates — `kaname`/`kanae` pattern), plus a **member CACAO leash**
     (`ibuki` ADR-2606111400) so an autonomous write is on-record attributed to a consenting human.
     This is the realization of "the actor makes its own key and does not expose it": *sealed +
     present-only + member-attributed*. Appending to the **local** commit-DAG needs no key at all.
     (A strictly "the actor cannot ever read its key" guarantee is a TEE/enclave or threshold-MPC
     construction — stronger, repo-future; not required for R3.)
   `methods/ingest.cljc` itself still performs no network I/O — it is the pure normalizer the
   autonomous `fetch.cljc` (or the member's fetch) feeds.
3. **G1/G3/G4/G5 unchanged + enforced at ingest.** A fetched fare bearing a
   commission/affiliate/merchant/searcher/person key is **dropped** (`:reject :forbidden-key`); a
   fare with no positive CO₂ is **dropped** (`:reject :no-co2` — emissions may never be silently
   absent); the airline link is affiliate-stripped on the way in. Per-row fail-open.
4. **No booking.** tsubasa still transacts no booking; the member self-books.

Accepted fares are `:fare/sourcing :authoritative` + `:fare/source` (cited provenance) +
`:fare/ingested-at` (caller as-of), and feed the existing analyze/heartbeat/commit-DAG pipeline
unchanged.

**Murakumo digest** (`methods/digest.cljc`): a short honest paragraph over the competition/fare
map via the **loopback** Murakumo gateway (`127.0.0.1:4000`) — the host is hardcoded loopback, so
an external LLM is unrepresentable (G6); **fail-open** to a deterministic template when Murakumo is
unreachable; read-only, no-server-key. The prompt forbids urgency / "book now" / paid-recommendation
language (G3/G1).

**WASM** (`wasm/world.wit` + `build.clj`): a compute-only Component Model scaffold (`analyze` /
`coverage` / template `digest`). It imports no `wasi:sockets`/`clocks`/`random` — the *absence* is
the guarantee (G1 no-inflow / G5 no-tracking / G6 no external call); `build.clj` (bb) fails the
build on any side-effecting import or a `commission`/`affiliate` symbol. The compiled artifact +
pinned CID are the operator step (shionome-core / rasen pattern); until then the actor runs
`service`-model on the bb methods and `did.json` carries `wasmCid: null`.

## R3+ — self-key identity + live-engine bridge + fleet + real source (2026-06-21)

Closes the remaining no-server-key items raised in review — the actor becomes a fully autonomous
fleet member.

**Self-certifying `did:key`** (`methods/identity.cljc`): the actor **GENERATES its own** Ed25519
keypair (`gen-keypair`), encodes the public half as `did:key:z6Mk…` (multicodec 0xed01 +
base58btc), and signs **present-only** (`sign`/`verify`) — the private seed is **sealed** to the
macOS Keychain / 1Password (`seal-seed!`, CONCEALED, never committed/logged) and used but never
exfiltrated. This is the code realization of *"the actor makes its own key and does not expose
it"*: sealed + present-only + (for autonomous writes) member-attributed. It is charter-clean
because custody stays off the platform and accountability stays on a consenting human (the leash
below). The strict "the actor itself can never read the seed" guarantee remains a TEE/enclave or
threshold-MPC construction (repo-future); not required here.

**Live-engine bridge** (`methods/kotoba_bridge.cljc`, kaname/ibuki pattern over tsubasa's local
ledger): each local fare-observation tx → one `…kotoba.datomic.transact` against a running node
(:8077). Host allowlist (loopback + EVO-X2) throws before I/O; a durable `:bridge/*` cursor gives
exactly-once per local tx; the prior `commit_cid` rides as `expected_parent`; **DRY-RUN by
default** (live = `TSUBASA_KOTOBA_LIVE=1`). **Auth principal = the leash**: a usable member CACAO
`:delegation` → the push PRESENTS the member-signed `cacao_b64` and the actor writes AS ITS OWN
did:key (no held key); absent/expired → **fail-open** to the node's unsigned public-DID operator
bearer (a public identifier, not a secret). Wired into `autorun --bridge` (fail-open: a dead
engine never crashes the beat).

**Fleet** (`cell.cljc` + `cells.edn`): `TsubasaHeartbeatCell` (node asher, cron `27 * * * *`,
healthz 13090) — `fire` runs one local heartbeat (no I/O; fetch + bridge stay operator/consent-
gated).

**Real public source** (`methods/openflights.cljc`): the OpenFlights ODbL public-domain
`airports.dat` / `airlines.dat` → `:authoritative` `:airport`/`:carrier` coverage rows (real
coverage off a real source — the original 'raise coverage' ask), read-only autonomous via
`fetch.cljc`. NO fares are fabricated (OpenFlights has none; fares need `:fare/co2-kg`, G4) — it
raises airport/carrier coverage only; region is best-effort with an honest `:unknown` fallback.

**74 tests / 634 assertions green** (adds identity 5/10 incl. keygen + present-only sign/verify;
bridge 7/22 incl. allowlist refusal + exactly-once + member-leash present + expired-leash fail-open;
openflights 5/12). Live engine push + member-issued CACAO + sealed-key provisioning + the OpenFlights
full-dataset pull remain the operator/consent steps (no key held here).

**Tooling = clj/bb (no shell).** Per the repo-wide rule (root `CLAUDE.md` §"Operational code =
clj/bb"), the former `run_tests.sh` / `wasm/build.sh` are replaced by `run_tests.clj` and
`wasm/build.clj`; `build.clj` shells out to the *system binaries* `wasm-tools` / `ipfs` via
`babashka.process` (allowed — invoking installed tools is not "a shell script").

**Honest limit.** R3 makes the live leg *autonomous for public sources* + *code-complete + gate-open*
overall. Public-source fetch runs with no key and no human (`fetch.cljc`, read-only); a
`:member-principal` pull needs the member's creds/runtime; the compiled WASM artifact + its pinned
CID remain the operator step. 57 tests / 590 assertions green (cwd-independent `bb run_tests.clj`),
incl. the G8-bound refusal of a paid terminal, the autonomous read-only fetch + fail-open, and the
ingest-time G1/G4/G5 rejections.

# Consequences

- Closes the last named-app coverage gap with a design that cannot become an OTA (no commission
  field is representable; booking is a self-book handoff).
- Adds one Tier-B actor; reuses proven affiliate-strip + self-book-handoff code paths.

# Alternatives Considered

1. **Extend `watari`** — rejected: watari is live-position observational (no fare/schedule/booking
   semantics); merging muddies a clean observational actor with a planning/commerce surface.
2. **Skyscanner-faithful with "non-profit" referral** — rejected: any onward commission is
   external inflow (§1.3); affiliate links are exactly what G1 strips.
3. **Fold into `kakaku`** (generic price-compare) — rejected: flights carry emissions, baggage,
   stops, and a self-book-handoff/booking-class model that the generic product comparator lacks.

# References

- ADR-2606012100 — okaimono (affiliate-strip + external-mirror pattern)
- ADR-2606071600 — shukubo (Ring-2 self-book handoff)
- ADR-2606041827 — watari (live aircraft position — sibling)
- Charter §1.3 (no external inflow), §1.13 (anti-dark-pattern Wellbecoming)
