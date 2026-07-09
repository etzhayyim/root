---
id: adr-2607082156-iryo-karute-pds-resolution-decision
title: "ADR-2607082156: iryo hand-off boundary — resolve consentCapabilityUri/patientDid keys in-process, or keep verify-given-already-resolved-input? (OPEN, Council/owner decision requested)"
status: proposed
doc_type: adr
topic: iryo-karute-pds-resolution-decision
authoritative: true
last_verified: 2026-07-08
priority: 5.5
axis: architecture
weight: 0.55
priority_note: "3-cycle-deferred design fork on the karute -> iryo hand-off boundary (handoff.cljc): whether iryo itself should perform real PDS/did:web network resolution, or whether the existing already-resolved-input contract should remain iryo's permanent design (not just its current R0 scope). Presented as an open decision, not a recommendation — Council/owner adjudication requested."
authoritative_for:
  - the resolution question (open, not a design decision yet): should iryo.methods.handoff perform real network resolution of consentCapabilityUri / granterDid keys, or keep the verify-given-already-resolved-input boundary
depends_on:
  - adr-2605231401-karute-consent-capability-iryo-bridge
  - adr-2606074000-iryo-rezept-claims-engine-charter
related:
  - adr-2605181100-mst-encrypted-records-signal-keywrap
  - adr-2605172000-etzhayyim-kotoba-substrate
supersedes: []
superseded_by: []
---

# ADR-2607082156: iryo hand-off boundary — resolve consentCapabilityUri/patientDid keys in-process, or keep verify-given-already-resolved-input?

**Status**: proposed
**Date**: 2026-07-08
**Deciders**: Jun Kawasaki / etzhayyim Council (adjudication requested — see Decision)

# Context

## The boundary and what it currently does NOT do

`20-actors/iryo/methods/handoff.cljc` implements the receiving side of the
karute → iryo billing hand-off (ADR-2605231401 Pattern 2 "etzhayyim ↔ vendor
bridge", ADR-2606074000 G1/G2/G3/G5). karute's
`com.etzhayyim.apps.karute.requestIryoBilling` forwards a billing request
naming `ingestKaruteEncounterForBilling`; `handoff/handle-ingest` runs three
gates before accepting the intake into a `:pending` draft queue:

1. **PHI-free structural gate (G2)** — the wire request may carry only the
   exact fields karute sends (`patientDid`/`encounterDid`/`facilityDid`/
   `serviceRequestUris`/`medicationRequestUris`/`consentCapabilityUri`); every
   DID/URI must be prefix-correct and ASCII-only.
2. **Consent-capability structural gate (`capability-gate`, G1/G7)** —
   purpose/granteeDid/granterDid/revocation/expiry/scope checks against an
   **already-resolved** `com.etzhayyim.consent.capability` record the caller
   supplies, PLUS (landed this cycle) a structural self-consistency check that
   `consentCapabilityUri` parses as a well-formed
   `at://<did>/<collection>/<rkey>` AT-URI whose collection is the canonical
   `com.etzhayyim.consent.capability` NSID and whose did segment equals the
   resolved capability's `granterDid`.
3. **Ed25519 signature gate (`signature-gate`, karute/MATURITY.md #8)** —
   cryptographically verifies the capability's signature using JDK
   `java.security` (no third-party crypto dep), but is **opt-in**: it only
   runs when the caller supplies an already-resolved `granterPublicKey`
   (base64 raw 32-byte Ed25519 public key). Without it, the gate no-ops.

The consistent design pattern across all three gates is: **iryo verifies
GIVEN already-resolved inputs; it never fetches anything over the network
itself.** iryo's `handoff.cljc` performs zero network I/O of its own — the
capability record, the encounter payload (in `agent.cljc`'s
`handle-ingest-billing`), and the granter's public key are all inputs the
caller must have already resolved before invoking the cell.

Two concrete gaps remain **structurally unclosed** by this pattern (tracked
explicitly in `handoff.cljc`'s namespace docstring, not silently missing):

- **(a) Resolving `granterPublicKey` from `granterDid`.** `signature-gate`
  verifies a signature GIVEN a key; it does not obtain one. In this bridge,
  `patientDid` is a rotating pseudonym did:web
  (`iryo.methods.karte/rotating-pseudonym-did`,
  `did:web:patient.iryo.etzhayyim.com:<hash>`, monthly-rotating per
  ADR-2605181200) — not a self-describing `did:key` — so obtaining its
  verification material means an HTTPS `did:web` document fetch.
- **(b) Fetching `consentCapabilityUri`'s bytes from a real PDS.**
  `capability-gate`'s structural checks verify a self-consistency relationship
  between the URI and an already-resolved capability record; they do not
  fetch the record. The actual byte-fetch needs a PDS-resolution client.

karute carries the mirror-image gap: `karute/MATURITY.md` item 8 ("consent
capability の Ed25519 検証テスト — member-signed / server-refused") is marked
未 (not done) — the granter-side signing/verification loop is not proven
end-to-end either, so even a "resolve the key" implementation on iryo's side
would presently have no verified real-world signer to check against.

## Three prior cycles, same "scope decision," same deferral

This scope boundary — real PDS/did:web resolution vs. verify-given-input —
has now been examined across (at least) three iteration cycles of the
`iryo-karute-handoff-boundary` work (PR #2982), each one re-investigating
whether circumstances changed enough to bring it in scope, and each time
concluding "not yet, but here is what changed":

- **Cycle 3** (Ed25519 signature verification) landed `signature-gate` as
  opt-in-given-a-key, explicitly carrying forward "obtaining
  `granterPublicKey` … stays out of scope" with the concrete reason: this
  bridge's `patientDid` is a rotating pseudonym `did:web`, not a `did:key`,
  so verifying it structurally requires an HTTPS `did:web` document fetch —
  the same class of problem as (b).
- **Cycle 4** (`consentCapabilityUri` structural self-consistency)
  re-investigated **specifically because** `@etzhayyim/sdk` had, by this
  point, actually come into existence, which was the stated reason the
  question was worth re-asking rather than auto-deferring. The investigation
  found:
  - `@etzhayyim/sdk` is a re-export shim onto a **separate GitHub repository**,
    `kotoba-lang/atproto-client` (imported as `@etzhayyim/atproto-client`),
    not something internal to `etzhayyim/root`.
  - That package's `resolve-pds` / `get-record` are **already implemented**,
    not stubs.
  - Critically, the earlier "can't be tested without hitting the network"
    assumption **does not hold**: the HTTP transport (`IHttp`) is
    host-injected, so a fake/mock transport can exercise `resolve-pds` /
    `get-record` in tests with zero real network calls. This closes off "we
    can't verify this without live network I/O" as a reason to defer.
  - What remained as the actual blocker was **not testability** but two
    separate integration-cost concerns (below) — so Cycle 4 implemented only
    the network-free structural half (`parse-at-uri` + the URI/capability
    consistency check in `capability-gate`) and left the real fetch out of
    scope again, this time with the reasoning made explicit and durable in
    both `handoff.cljc`'s docstring and `20-actors/iryo/CLAUDE.md`.

**What is now settled** (do not re-litigate in a future cycle without new
information):

1. `@etzhayyim/sdk`'s PDS resolution (`resolve-pds`/`get-record`, actually
   `kotoba-lang/atproto-client` underneath) is real, non-stub, and
   host-injected-transport testable without live network I/O. "We can't test
   this" is not a valid reason to defer further investigation.

**What remains genuinely unresolved** (the actual decision this ADR raises):

2. Whether iryo *should* perform this resolution at all, independent of
   testability — see Decision below.

# Decision

This ADR does **not** pick a side. Both options below are real, defensible,
and have already been implemented-around for three cycles without a Council/
owner ruling; that absence of a ruling is itself the reason the same
scope question keeps resurfacing per-cycle instead of being closed once.
This section states the two options and their trade-offs, and asks for an
explicit decision (or an explicit "stay open" decision, if that is itself
the ruling) rather than picking one under implementation-cycle time pressure.

## Option A — Wire iryo to `@etzhayyim/sdk` / `kotoba-lang/atproto-client` and do real PDS/did:web resolution in-process

iryo would gain a new cross-repo runtime dependency (`kotoba-lang/atproto-client`,
via the `@etzhayyim/sdk` shim), add a `deps.edn`/git-dep mechanism (iryo
currently has none at all — it is pure-stdlib clj/bb with zero external
deps), and `handoff.cljc` would call `resolve-pds`/`get-record` to fetch
`consentCapabilityUri`'s bytes, and perform an HTTPS `did:web` document fetch
to obtain `granterPublicKey` for the rotating-pseudonym `patientDid`.

**Trade-offs:**

- **G3 no-server-key tension.** iryo's G3 gate is currently framed as "online
  請求(送信) operator-gated; iryo computes + drafts only." Read charitably,
  outbound READ-only resolution (fetching a public capability record / a
  public DID document) is a different class of action from the online-請求
  submission G3 actually targets — and the repo-wide substrate boundary
  table explicitly distinguishes "no-server-key bars a CUSTODIAL UNILATERAL
  signing key … READ-ONLY ops are exempt" (ADR-2606072802 clarification,
  `etzhayyim/root/CLAUDE.md` Substrate boundary table). Under that reading,
  Option A is not a G3 violation — it adds read-only network I/O, not a
  signing capability. Read strictly, however, iryo's own actor-local
  design principle so far has been narrower than the repo-wide floor:
  "iryo itself performs zero network I/O of its own" — a stronger,
  self-imposed invariant than G3 requires. Option A would be the first
  breach of that stronger self-imposed line, even though it may not breach
  the repo-wide G3 floor. Whether iryo's narrower line is itself binding
  Tier-1 policy or just an accreted implementation convention nobody has
  ruled on is exactly the open question.
- **New cross-repo dependency cost.** iryo has zero external dependencies
  today (pure-stdlib, pywasm-ready per its own design goal). Taking a
  runtime dependency on a `kotoba-lang`-org package from an
  `etzhayyim/root` actor is a new category of coupling this actor has not
  had before, and (per `20-actors/iryo/CLAUDE.md`'s own Cycle-4 investigation
  note) "iryo currently has no deps.edn / git-dep mechanism at all" — so
  Option A is not merely "add a function call," it is "stand up
  cross-repo/cross-org dependency management for this actor for the first
  time."
  This is not a new pattern for the monorepo as a whole — other actors and
  the SDK itself already depend across repos/orgs — but it would be new
  *for iryo specifically*, whose R0 charter (ADR-2606074000) explicitly
  emphasizes "self-contained, pure-stdlib" as a design property.
- **Production risk surface.** Production code performing a real HTTPS
  `did:web` fetch is a materially bigger and more failure-prone change than
  "verify a signature given a key already handed to you" — network
  failures, timeouts, revoked/rotated keys mid-flight, and PDS availability
  become iryo's problem at intake-time rather than the caller's problem
  before invocation.
- **Test strategy.** Per the Cycle-4 finding, this is genuinely
  network-free-testable via `IHttp` fake transports — the earlier
  "can't be tested" objection does not hold. Test cost is not the blocker;
  it is the two points above.
- **Implementation size (rough estimate).** Adding the dependency + wiring
  `resolve-pds`/`get-record` calls + a `did:web` document fetch + fake-transport
  test coverage for both paths is estimated at a similar order of magnitude
  to Cycles 1–4 combined (a full iteration cycle, not a small increment) —
  it touches dependency management, two distinct resolution flows (capability
  record + DID document), and their respective failure-mode handling, which
  none of the prior four cycles needed to do.
- **What it would close:** both (a) and (b) fully — iryo would no longer
  depend on a caller having pre-resolved either the capability bytes or the
  granter's public key, closing the last structural gaps in the hand-off
  boundary and making `karute/MATURITY.md` item 8 completable end-to-end
  from iryo's side (karute's own granter-signing loop would still need its
  own closure, independently).

## Option B — Keep verify-given-already-resolved-input as iryo's permanent design, not just its current scope

iryo's `handoff.cljc` continues to never perform network I/O of its own.
Real PDS/did:web resolution, if and when it is needed, happens **upstream**
of the hand-off — i.e., karute (or another caller) resolves the capability
bytes and the granter's public key before calling
`ingestKaruteEncounterForBilling`, and passes them as the already-resolved
`capability`/`granterPublicKey` inputs the boundary already accepts today.

**Trade-offs:**

- **Preserves iryo's narrower, self-imposed no-network-I/O line**, keeping
  it maximally simple, pure-stdlib, pywasm-ready, and dependency-free — a
  design property ADR-2606074000 explicitly values ("self-contained,
  pure-stdlib + pywasm-ready").
- **Symmetric with G3's spirit even under the strict reading** — no debate
  needed about whether read-only resolution counts as an exemption; the
  question simply does not arise because iryo never resolves anything
  itself.
- **Does not, by itself, close (a)/(b).** The gaps do not disappear; they
  move to whichever caller is responsible for pre-resolving inputs — most
  naturally karute, which already sits closer to the patient-facing PDS
  interactions and already has its own open item (MATURITY.md #8) for the
  granter-side signing loop. This ADR does not resolve karute's item 8;
  it only observes that Option B would make karute (or an equivalent
  upstream caller) the permanent, designed home for that resolution
  work, rather than a temporary gap.
- **Cheapest to keep as-is.** Zero new implementation cost on iryo's side;
  the existing test suite (12 cljc suites, `iryo.methods.test-handoff`: 29
  tests / 71 assertions) already exercises the verify-given-input contract
  fully.
- **Ongoing cost:** every future caller of `ingestKaruteEncounterForBilling`
  (not just karute) must independently implement capability/key resolution
  before calling iryo, which is a repeated integration burden per caller
  rather than a one-time cost inside iryo. If iryo grows more callers beyond
  karute, this cost multiplies.

## What this ADR asks the Council/owner to decide

This is not a technical unknown (Cycle 4 already resolved the testability
question); it is a **design-boundary-ownership** question:

1. Is iryo's "zero network I/O of its own" property a Tier-1-equivalent
   design invariant for this actor (i.e., something that should require an
   ADR/Council decision to cross, the way G3 no-server-key is treated
   repo-wide), or is it an incidental accretion of "we haven't needed to
   yet" that Option A can simply supersede when convenient?
2. If Option A is chosen, does the new cross-repo dependency
   (`kotoba-lang/atproto-client` via `@etzhayyim/sdk`) require the same kind
   of cross-org dependency review other `kotoba-lang` integrations have had,
   and who owns that review?
3. If Option B is chosen, is karute's MATURITY.md item 8 (granter-side
   Ed25519 signing/verification loop) the designated place this resolution
   work permanently lives, and should that item's scope be amended to say
   so explicitly (closing the ambiguity about whose job this is)?

If the investigation above surfaces a clear technical reason to prefer one
option, this ADR would state it — it does not, because the blocking factors
(G3-adjacent design-philosophy question, cross-repo dependency cost) are
governance/architecture judgment calls, not facts still to be gathered.
**No recommendation is made; this is deliberately left OPEN pending
Council/owner ruling**, consistent with this ADR's `proposed` status.

# Consequences

## If Option A is ruled

- iryo gains its first external runtime dependency and its first outbound
  network I/O path, ever. `20-actors/iryo/CLAUDE.md`'s "Build & Verify"
  section and its "self-contained, pure-stdlib" framing (ADR-2606074000)
  need updating to reflect the new dependency.
- `handoff.cljc`'s docstring's "Explicitly NOT in scope" section shrinks to
  remove both (a) and (b); its opt-in `granterPublicKey`/pre-resolved-
  `capability` contract can either be removed (become mandatory in-process
  resolution) or kept as a fallback/override path for callers that still
  want to pre-resolve (backward compatible with existing callers, notably
  the already-landed PR #2982 test suite).
- iryo's G3 gate documentation should be tightened to state explicitly why
  read-only PDS/did:web resolution does not violate it (citing the
  ADR-2606072802 read-only clarification), pre-empting the same question
  from being re-litigated by a future contributor.
- Failure-mode handling (PDS unreachable, `did:web` document 404/malformed,
  timeout) becomes iryo's problem at intake time; `handle-ingest`'s existing
  fail-closed `"needs-info"` discipline (G5) should extend to cover these
  new failure modes, not silently propagate an uncaught network exception
  (the same class of gap `parse-instant`'s introduction fixed for malformed
  instant strings this cycle).
- karute's own MATURITY.md item 8 (granter-side signing loop) remains open
  independently — Option A closes iryo's *verification* gap, not karute's
  *signing* gap. A production end-to-end proof still requires both sides
  closed.

## If Option B is ruled

- iryo remains as-is; no code changes required by this ADR.
- The "resolve capability bytes + granter public key" responsibility should
  be explicitly assigned to karute's hand-off path (or documented as an
  open requirement on any future non-karute caller of
  `ingestKaruteEncounterForBilling`), most naturally as an amendment to
  karute/MATURITY.md item 8's scope description, so the next contributor
  who looks at item 8 does not have to re-derive from `handoff.cljc`'s
  docstring where the missing resolution work is supposed to live.
- The already-resolved-input contract (`capability`/`granterPublicKey`/
  `encounter`) becomes the **permanent** public contract of
  `ingestKaruteEncounterForBilling`, not a temporary R0 scope-narrowing —
  this should be reflected by removing the "still out of scope" framing
  from `handoff.cljc`'s docstring (replacing "not yet done" language with
  "by design, callers resolve these") once ruled, so a future cycle does not
  spend a fifth iteration re-investigating the same question.

## Either way

- This ADR itself does not change any code, gate, or test. It is a decision
  record for a design fork that has been implemented-around, not resolved,
  across four implementation cycles (PR #2982) — landing this ADR converts
  an implicit, repeatedly-deferred scope boundary into an explicit decision
  point for the Council/owner to close.
- Whichever option is chosen, `20-actors/iryo/CLAUDE.md` and
  `handoff.cljc`'s docstring should be updated in the *implementing* PR
  (not this one) to state the resolution as a settled design decision
  rather than an open scope question, so a fifth cycle does not re-ask it.

# Alternatives Considered

## C. Keep the question open indefinitely / let each cycle re-decide

This is what has actually happened for three cycles. Rejected as a
permanent posture (though acceptable as a *temporary* holding pattern
until this ADR is adjudicated): re-investigating the same scope boundary
from scratch each cycle has already produced real, durable value once
(Cycle 4's discovery that `@etzhayyim/sdk`'s transport is host-injected
and testable, closing off the stale "can't test it" objection) — but that
value is now captured in this ADR and in `handoff.cljc`'s docstring, so a
fifth re-investigation would be pure repeated overhead with no new
information to surface, unless the ecosystem changes materially again
(e.g. iryo gains other callers, or `kotoba-lang/atproto-client` changes
its transport contract).

## D. karute resolves PDS/did:web keys and forwards only resolved values (Option B, generalized to "the only sanctioned pattern")

Functionally identical to Option B from iryo's perspective, but framed as a
*repo-wide* rule ("vendor-side Tier-B actors never do their own PDS/did:web
resolution; the etzhayyim-side actor always resolves and forwards") rather
than an iryo-specific choice. Considered as a stronger version of Option B.
Not adopted as a repo-wide rule in this ADR because that generalization is
out of scope for a two-actor hand-off decision — a repo-wide rule would need
its own ADR surveying more than iryo/karute (e.g. yakushi, toritate, chigiri
also cross-reference consent capabilities per `20-actors/iryo/CLAUDE.md`'s
Cross-actor section) before being adopted as binding policy. This ADR scopes
itself to the iryo/karute pair to avoid over-generalizing from one example.

## E. Split the difference — resolve `consentCapabilityUri` bytes in-process (close (b)) but keep `granterPublicKey` resolution out of scope (leave (a) open)

Considered because (b)'s PDS fetch (`resolve-pds`/`get-record`) is a single,
well-scoped call whereas (a)'s `did:web` document fetch for a
*rotating pseudonym* DID is a distinct, less-explored resolution path
(monthly rotation per ADR-2605181200 means the resolution target changes
identity over time, which the capability-fetch path does not need to
handle). Not adopted as this ADR's Decision because splitting the two
still requires taking the new cross-repo dependency (the same Option A
cost driver) while only partially closing the gap — it captures most of
Option A's cost for less than all of its benefit. Recorded here as a
possible middle path the Council may want to consider instead of a
binary A/B choice.

# References

- ADR-2605231401 [karute consent capability + iryo billing bridge](./2605231401-karute-consent-capability-iryo-bridge.md) — defines the consent capability primitive, Pattern 2 (etzhayyim ↔ vendor bridge), and the PDS-resolution step this ADR's Decision concerns
- ADR-2606074000 [iryo レセプト claims engine charter](./2606074000-iryo-rezept-claims-engine-charter.md) — iryo's R0 charter, G1–G7 gates, "self-contained, pure-stdlib" design property
- ADR-2605181100 [MST encrypted records + Signal key-wrap](./2605181100-mst-encrypted-records-signal-keywrap.md) — PHI envelope; rotating pseudonym DID origin (ADR-2605181200 referenced therein)
- ADR-2605172000 [etzhayyim kotoba substrate](./2605172000-etzhayyim-kotoba-substrate.md) — substrate client import rule (`@etzhayyim/sdk` only), relevant to Option A's dependency path
- `20-actors/iryo/methods/handoff.cljc` — the hand-off boundary implementation this ADR concerns (namespace docstring carries the same "explicitly not in scope" items this ADR formalizes as an open Council decision)
- `20-actors/iryo/CLAUDE.md` — iryo actor identity, gates (G1–G7), and the "Investigated this iteration: is `@etzhayyim/sdk` PDS resolution reachable?" note (Cycle 4 finding this ADR's Context section restates)
- `20-actors/karute/MATURITY.md` item 8 — karute's mirror-image open item (granter-side Ed25519 signing/verification loop), referenced in Decision/Consequences as the natural home for Option B's resolution work
- `etzhayyim/root/CLAUDE.md` § "Substrate boundary" — repo-wide no-server-key / read-only-exempt clarification (ADR-2606072802) cited in Option A's G3 trade-off analysis
- PR #2982 (`iryo-karute-handoff-boundary`, branch, at time of writing OPEN) — the four implementation cycles this ADR's Context section summarizes
